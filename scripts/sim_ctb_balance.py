# -*- coding: utf-8 -*-
"""CTB（Charge Time Battle）数值模拟与常量标定 —— Agent D 第四阶段。

直接 from game.battle import Battle / from game import engine as E（不依赖 astrbot）。
对比新旧机制胜率基线，并做 BASE_DELAY / SPD_CT_CAP 敏感性 + 极端配速测试。

口径说明：
- 玩家构造复用 tests 的 make_player 字段（class_name/level/attributes/equipment/
  learned_skills/skill_levels...）。
- 与真实流程一致：Battle("monster", enemy, player=player) —— __init__ 据此初始化
  p_ct = -spd（快者先手）。
- 技能简化：与旧 sim 一致 —— p["mp"]>=6 时用『猛击』(mp4)，否则普攻；仅此口径简化。
- 确定性：random.seed 固定。
"""
import sys, random, statistics
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

from game.content_rules.panel import player_final_stats
from game.core.stats import monster_stats, equip_stats
from game import battle as BT  # 模块级常量读写（BASE_DELAY/SPD_CT_CAP）
from game.battle import Battle

random.seed(42)


# ---------------- 玩家 / 敌方构造 ----------------

def make_player(class_name, level, attributes, equipment, learned_skills):
    return {
        "qq_id": "test", "class_name": class_name, "level": level,
        "attributes": attributes, "equipment": equipment,
        "learned_skills": learned_skills,
        "skill_levels": {s: min(2, level) for s in learned_skills},
        "hp": 9999, "mp": 9999, "class_tier": 0, "evolve_path": 0,
    }


def make_enemy(st, name="怪", role="dps", skills=()):
    return {
        "name": name, "role": role, "hp": st["hp"], "max_hp": st["hp"],
        "atk": st["atk"], "def": st["def"], "matk": st["matk"], "mdef": st["mdef"],
        "spd": st["spd"], "skills": list(skills),
    }


def equip_set(lv, quality, enhance=0):
    eq = {}
    names = {"weapon": "铁剑", "helm": "皮帽", "armor": "皮甲", "legs": "皮裤",
             "boots": "皮靴", "ring": "铜戒", "necklace": "骨链"}
    for slot in ("weapon", "helm", "armor", "legs", "boots", "ring", "necklace"):
        eq[slot] = {"name": names[slot], "stats": equip_stats(slot, lv, quality), "enhance": enhance}
    return eq


def player_sheet(p):
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    return st


# ---------------- 单场战斗 ----------------

def run_one_battle(p, enemy, use_skill=True, spd_override=None, enemy_spd_override=None):
    """跑一场完整战斗，返回 (result, rounds, maxhp - hp_lost)。"""
    b = Battle("monster", dict(enemy), player=p)
    if enemy_spd_override is not None:
        for u in b.enemies:
            u["spd"] = float(enemy_spd_override)
            u["ct"] = -float(enemy_spd_override)
    pp = dict(p)
    st = player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    pp["max_hp"] = st["max_hp"]; pp["max_mp"] = st["max_mp"]
    pp["hp"] = st["max_hp"]; pp["mp"] = st["max_mp"]

    if spd_override is not None:
        # 速度敏感性：用真实 stats 但注入目标 spd（保留伤害/防御的合理性）
        _orig = Battle._player_stats

        def _inject(self, player):
            d = _orig(self, player)
            d = dict(d); d["spd"] = float(spd_override)
            return d
        b._player_stats = _inject.__get__(b, Battle)

    while True:
        done = False
        # 与旧 sim 口径一致：仅在已学技能时用技能，否则普攻（否则未学技能会被 O118
        # 拦截持续返回 done=False，造成死循环）
        if use_skill and pp.get("learned_skills") and pp["mp"] >= 6:
            logs, done = b.actor_turn("skill", "猛击", pp)
        else:
            logs, done = b.actor_turn("attack", None, pp)
        if done:
            break
        if b.round > 800:  # 兜底保护，防御极端配速解析不一导致的死循环
            break
    dmg = st["max_hp"] - pp["hp"]
    return b.result, b.round, max(0, dmg)


def simulate(p, enemy, rounds=400, use_skill=True, spd_override=None, enemy_spd_override=None):
    """跑多次，返回 {win_rate, avg_round, avg_dmg, max_round}。"""
    wins = 0; rnds = []; dmgs = []
    for _ in range(rounds):
        res, r, d = run_one_battle(dict(p), enemy, use_skill, spd_override, enemy_spd_override)
        if res == "victory":
            wins += 1; rnds.append(r); dmgs.append(d)
    return {
        "win_rate": wins / rounds,
        "avg_round": (statistics.mean(rnds) if rnds else 0),
        "max_round": (max(rnds) if rnds else 0),
        "avg_dmg": (statistics.mean(dmgs) if dmgs else 0),
        "n": rounds,
    }


# ---------------- 行动频次/连动统计（极端配速） ----------------

def action_statistics(player_spd, enemy_spd, player_actions=100):
    """在敌方高血量下打 player_actions 次玩家行动，统计：
    - 双方行动次数分布（players_vs_enemies）
    - 单次玩家行动后敌方连动的最大次数（是否触顶 8）
    - 引擎是否因硬上限被截断（连动==8 的次数）
    构造：玩家 spd 注入，敌方 spd 注入；用够肉的属性避免过早结束。
    """
    st_p = player_final_stats("cls_zhan_shi", 60, {}, 0, {"str": 100, "agi": 0, "int": 0, "vit": 40})
    p = make_player("cls_zhan_shi", 60, {"str": 100, "agi": 0, "int": 0, "vit": 40}, {}, ["sk_meng_ji"])
    # 敌方给超高血量，让战斗持续 100 次玩家行动
    en = make_enemy({"hp": 10_000_000, "atk": 5, "def": 30, "matk": 5, "mdef": 30,
                     "spd": enemy_spd}, role="dps", skills=[])
    pp = dict(p)
    pp["max_hp"] = st_p["max_hp"]; pp["max_mp"] = st_p["max_mp"]
    pp["hp"] = st_p["max_hp"]; pp["mp"] = st_p["max_mp"]

    b = Battle("monster", dict(en), player=pp)
    for u in b.enemies:
        u["spd"] = float(enemy_spd); u["ct"] = -float(enemy_spd)
    _orig = Battle._player_stats

    def _inj(self, player):
        d = dict(_orig(self, player)); d["spd"] = float(player_spd)
        return d
    b._player_stats = _inj.__get__(b, Battle)

    # 埋点：统计敌方行动
    stat = {"e_total": 0, "cur_chain": 0, "max_chain": 0, "cap_hits": 0}
    real_after = Battle._after_actor_ct

    def _after(self, side, unit=None, player=None):
        if side == "e":
            stat["cur_chain"] += 1
            stat["e_total"] += 1
            if stat["cur_chain"] > stat["max_chain"]:
                stat["max_chain"] = stat["cur_chain"]
            if stat["cur_chain"] >= 8:
                stat["cap_hits"] += 1
        else:
            stat["cur_chain"] = 0
        return real_after(self, side, unit, player)
    Battle._after_actor_ct = _after

    p_acts = 0
    while p_acts < player_actions:
        logs, done = b.actor_turn("attack", None, pp)
        p_acts += 1
        if done or b.result is not None:
            break

    Battle._after_actor_ct = real_after
    return {
        "player_actions_taken": p_acts,
        "player_turn_count": p_acts,
        "enemy_actions": stat["e_total"],
        "action_ratio_p:e": (p_acts, stat["e_total"]),
        "max_enemy_chain_per_pturn": stat["max_chain"],
        "cap8_hits": stat["cap_hits"],
    }


def extreme_duel(p_spd, e_spd, rounds=400):
    """极端配速胜负检验：3:1/5:1 用真实血量对打，看战斗是否失衡（<10% 或 >95%）。"""
    # 战士用高级别 + 敏捷打造高 spd 玩家；敌方用同等级怪但注入敌 spd
    agi = int((p_spd - 20) / 0.8)  # spd ≈ base(战士60级=45) + agi*0.8 → 造 p_spd
    lv = 60
    attrs = {"str": 50, "agi": max(0, agi), "int": 0, "vit": 30}
    # 注意 make_player(class_name, level, attributes, equipment, learned_skills)
    p = make_player("cls_zhan_shi", lv, attrs, {}, ["sk_meng_ji"])
    st = player_final_stats(p["class_name"], lv, {}, 0, attrs)
    base_e = monster_stats(lv, "dps")
    en = make_enemy(base_e, role="dps", skills=["ms_pi_kan"])
    # 用 spd_override 精确注入玩家 spd（面板 built 值随 agi 可能有偏差，保证比例可控）
    return simulate(p, en, rounds=rounds, use_skill=True,
                    spd_override=float(p_spd), enemy_spd_override=float(e_spd))


def enemy_cap8_test():
    """验证敌方连动硬上限 8：敌方 spd300 vs 玩家 spd5 → 单次玩家回合敌方应被截停在 8 连动。"""
    st_p = player_final_stats("cls_zhan_shi", 30, {}, 0, {"str": 60, "agi": 0, "int": 0, "vit": 40})
    p = make_player("cls_zhan_shi", 30, {"str": 60, "agi": 0, "int": 0, "vit": 40}, {}, [])
    en = {"name": "fast", "role": "dps", "hp": 2000, "max_hp": 2000, "atk": 5, "def": 5,
          "matk": 5, "mdef": 5, "spd": 300, "skills": []}
    pp = dict(p)
    pp["max_hp"] = st_p["max_hp"]; pp["max_mp"] = st_p["max_mp"]; pp["hp"] = st_p["max_hp"]; pp["mp"] = st_p["max_mp"]
    b = Battle("monster", dict(en), player=pp)
    for u in b.enemies:
        u["spd"] = 300; u["hp"] = 2000; u["max_hp"] = 2000
    _orig = Battle._player_stats

    def _inj(self, ply):
        d = dict(_orig(self, ply)); d["spd"] = 5; return d
    b._player_stats = _inj.__get__(b, Battle)
    cnt = {"e": 0, "chain": 0, "max": 0, "p": 0}
    real = Battle._after_actor_ct

    def _after(self, side, unit=None, player=None):
        if side == "e":
            cnt["e"] += 1; cnt["chain"] += 1
            cnt["max"] = max(cnt["max"], cnt["chain"])
        else:
            cnt["p"] += 1; cnt["chain"] = 0
        return real(self, side, unit, player)
    Battle._after_actor_ct = _after
    b.actor_turn("attack", None, pp)
    Battle._after_actor_ct = real
    return {"enemy_in_1pturn": cnt["e"], "max_chain": cnt["max"], "p_turns": cnt["p"]}


def fmt_res(r):
    return f"胜率{r['win_rate']*100:.0f}% | 平均{r['avg_round']:.1f}回合(max {int(r['max_round'])}) | 胜局掉血{r['avg_dmg']:.0f}"


# ================= 1. 胜率基线验证（复刻旧 sim 场景，400 场） =================
print("=" * 86)
print("【1. 胜率基线验证】CTB 新引擎 400 场 vs 旧 sim（v61 进度条 / v57 引擎）记录")
print("=" * 86)

E_4 = monster_stats(4, "elite")
e4 = make_enemy(E_4, name="山贼头目", role="elite", skills=["ms_pi_kan", "ms_nu_hou"])

lv2_elite_scenarios = [
    ("A 现状(全力量str12,裸奔)", {"str": 12, "agi": 0, "int": 0, "vit": 0}, {}, True),
    ("B 现状+白装Lv2",           {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white"), True),
    ("C 现状+绿装Lv2",           {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "green"), True),
    ("D 现状+蓝装Lv2",           {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "blue"), True),
    ("E 均衡(str6vit6)+白装",    {"str": 6, "agi": 0, "int": 0, "vit": 6}, equip_set(2, "white"), True),
    ("F 肉装(vit12)+白装",       {"str": 0, "agi": 0, "int": 0, "vit": 12}, equip_set(2, "white"), True),
    ("G 现状+白装(普攻无技能)",  {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white"), False),
]
print("场景: 2级战士 vs 4级精英(山贼头目)   —— 旧 sim(sim_lv2_vs_elite4/v57_balance)基线: A=2%, B~G=94~100")
for name, attrs, eq, use_skill in lv2_elite_scenarios:
    p = make_player("cls_zhan_shi", 2, attrs, eq, ["sk_meng_ji"] if name != "G" else ["sk_meng_ji"])
    r = simulate(p, e4, rounds=400, use_skill=use_skill)
    st = player_sheet(p)
    print(f"  {name}: 玩家{st['max_hp']}血/{st['atk']}攻/{st['def']}防/{st['spd']}速"
          f"  → {fmt_res(r)}")

# 新手期普通怪（复刻 sim_v57_normal）
print("\n场景: 新手期普通怪（复刻 sim_v57_normal）")
norm_scen = [
    ("1级战士(初始9点str9)", 1, {"str": 9, "agi": 0, "int": 0, "vit": 0}, 1, "dps"),
    ("1级战士 vs 2级怪",     1, {"str": 9, "agi": 0, "int": 0, "vit": 0}, 2, "dps"),
    ("2级战士 vs 2级怪",     2, {"str": 12, "agi": 0, "int": 0, "vit": 0}, 2, "dps"),
    ("2级战士 vs 3级怪",     2, {"str": 12, "agi": 0, "int": 0, "vit": 0}, 3, "dps"),
    ("3级战士 vs 3级怪",     3, {"str": 15, "agi": 0, "int": 0, "vit": 0}, 3, "dps"),
    ("2级战士 vs 3级坦克",   2, {"str": 12, "agi": 0, "int": 0, "vit": 0}, 3, "tank"),
]
for name, plv, attrs, mlv, role in norm_scen:
    p = make_player("cls_zhan_shi", plv, attrs, {}, ["sk_meng_ji"] if plv >= 2 else [])
    en = make_enemy(monster_stats(mlv, role), name=role, role=role)
    r = simulate(p, en, rounds=400)
    st = player_sheet(p)
    flag = "😴轻松" if r["win_rate"] == 1 and r["avg_dmg"] < st["max_hp"] * 0.4 else (
        "⚠️有压力" if r["win_rate"] == 1 else "❌打不过")
    print(f"  {name}: 玩家{st['spd']}速 vs 怪spd{monster_stats(mlv, role)['spd']}"
          f" → {r['win_rate']*100:.0f}% 掉血{r['avg_dmg']:.0f}/{st['max_hp']}"
          f"({r['avg_dmg']/st['max_hp']*100:.0f}%) {flag}")


# ================= 2. BASE_DELAY 敏感性 =================
print("\n" + "=" * 86)
print("【2. BASE_DELAY 敏感性】100 / 60 / 150（用 G 白装普攻 + B 白装技能两场景，400 场）")
print("=" * 86)
base_cases = [
    ("B 白装+技能",  {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white"), True),
    ("G 白装+普攻",  {"str": 12, "agi": 0, "int": 0, "vit": 0}, equip_set(2, "white"), False),
]
for delay in (100.0, 60.0, 150.0):
    BT.BASE_DELAY = float(delay)  # 模块级全局（_ct_cost 读模块全局；Battle.BASE_DELAY 类属性无效）
    for name, attrs, eq, usk in base_cases:
        p = make_player("cls_zhan_shi", 2, attrs, eq, ["sk_meng_ji"])
        r = simulate(p, e4, rounds=400, use_skill=usk)
        print(f"  BASE_DELAY={delay:<4} | {name}: {fmt_res(r)}")
BT.BASE_DELAY = 100.0


# ================= 3. SPD_CT_CAP 敏感性 =================
print("\n" + "=" * 86)
print("【3. SPD_CT_CAP 敏感性】无cap / 80 / 60（极端配速: 玩家spd100 vs 怪spd20，行动比理想5:1）")
print("=" * 86)
for cap in ("none", 80.0, 60.0):
    if cap == "none":
        # 真正的"无 cap"：直接覆盖 _ct_cost，绕过 min(spd, cap)（设 cap=None 会被
        # _ct_cost 的 except 兜底成 eff=0 → 双方 cost 都=BASE_DELAY，反而退化为 1:1）
        _orig_ct = Battle._ct_cost
        Battle._ct_cost = lambda self, spd: 100.0 / max(1.0, float(spd or 0))
    else:
        BT.SPD_CT_CAP = cap
    ac = action_statistics(100, 20, player_actions=100)
    ratio = ac["action_ratio_p:e"]
    eff_ratio = ratio[0] / ratio[1] if ratio[1] else float('inf')
    print(f"  cap={'无cap' if cap == 'none' else cap:<3} | 行动比 玩家:敌 = {ratio[0]}:{ratio[1]}"
          f" (实际比值 {eff_ratio:.2f}) | 敌方连动最大{ac['max_enemy_chain_per_pturn']} 次"
          f"(触顶8×{ac['cap8_hits']})")
    if cap == "none":
        Battle._ct_cost = _orig_ct
BT.SPD_CT_CAP = 80.0


# ================= 4. 极端配速测试 =================
print("\n" + "=" * 86)
print("【4. 极端配速测试】3:1 / 5:1 对抗：行动比分布、敌方连动上限、战斗是否失衡")
print("=" * 86)
for ratio, pspd, espd in ((3, 60, 20), (5, 100, 20)):
    ac = action_statistics(pspd, espd, player_actions=100)
    ratio_s = ac["action_ratio_p:e"]
    eff = ratio_s[0] / ratio_s[1] if ratio_s[1] else float('inf')
    print(f"  配速 {ratio}:1 (玩家{pspd} vs 怪{espd}): 玩家行动量{ac['player_actions_taken']}"
          f" → 双方行动 {ratio_s[0]}:{ratio_s[1]} (实测比值 {eff:.2f}) | "
          f"敌方连动最大 {ac['max_enemy_chain_per_pturn']} 次 (触顶8×{ac['cap8_hits']})")

print("\n  真实血量对打（400 场，验证胜负导向）：")
for ratio, pspd, espd in ((3, 60, 20), (5, 100, 20)):
    r = extreme_duel(pspd, espd, rounds=400)
    flag = ""
    if r["win_rate"] > 0.95:
        flag = " 🔥失衡(>95%)"
    elif r["win_rate"] < 0.10:
        flag = " ❄️失衡(<10%)"
    print(f"    配速 {ratio}:1 (玩家{pspd} vs 怪{espd}) → {fmt_res(r)}{flag}")

print("\n  敌方硬上限 8 触发验证（敌方 spd300 vs 玩家 spd5 → 单次玩家回合内敌方应被截停为 8 连动）：")
for _ in range(3):
    ac = enemy_cap8_test()
    print(f"    单玩家回合敌方行动 {ac['enemy_in_1pturn']} 次 | 连动最大 {ac['max_chain']} | p_turns={ac['p_turns']}")

# ================= 5. 结论 =================
print("\n" + "=" * 86)
print("【结论】")
print("  当前 battle.py 常量: BASE_DELAY=100.0, SPD_CT_CAP=80.0")
print("  (详见 scripts/sim_ctb_balance.md)")

# 恢复默认（脚本进程内不影响部署；真实改动在 battle.py 顶部）
BT.BASE_DELAY = 100.0
BT.SPD_CT_CAP = 80.0
print("  默认常量已恢复（进程内）。")
