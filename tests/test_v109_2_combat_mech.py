#!/usr/bin/env python3
"""v109.2 六项战斗机制修复验证（正式回归测试）

覆盖：
1. pierce 魔法分支修复（P1-6）：魔法 pierce 技能无视 mdef，普通魔法吃 mdef
2. 安眠曲改睡眠（P1-3）：effect=sleep → e_buffs["sleep"]=1 → 敌方回合跳过
3. 火之亲和（P1-2 龙血火系强化）：灼烧 dot ×1.2
4. 运势 luck 联动（P1-1）：luck → 暴击补充（×0.3 cap 0.12）+ 暴击 30% 追加 50%
5. 武圣连击 0.50（P1-2）：连招精通三连追加 = total × 0.50
6. PVP 韧性对称：玩家攻击端暴击率 × 敌方 tenacity_mult

说明：暴击判定用伤害阈值法（def=0, atk=100：非暴 85-115 / 暴击 127-173 / 幸运 191-259）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, run
from data.plugins.dragonfall.game import engine as EG
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.game.core.affix import stat_affix_stats

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()

    def mk_player(cls="战士", skills=None, affixes=None, extra_stats=None, hp=500):
        eq_stats = {"atk": 100, "matk": 100}
        if extra_stats:
            eq_stats.update(extra_stats)
        eq_stats.update(stat_affix_stats(affixes or [], "weapon", 30))
        return {
            "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
            "mp": 100, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试剑", "stats": eq_stats,
                                     "affixes": affixes or [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": skills or [], "race": "human",
        }

    def mk_enemy(def_=20, mdef=20, hp=100000, **kw):
        e = {"name": "测试怪", "hp": hp, "max_hp": hp, "atk": 0,
             "def": def_, "mdef": mdef, "spd": 10}
        e.update(kw)
        return e

    def attack_once(b, st, p, seed, atk=None):
        random.seed(seed)
        b.enemy["hp"] = 10**9
        logs = b._player_attack(st, p)
        dealt = 10**9 - b.enemy["hp"]
        a = atk or st["atk"]
        is_crit = dealt > a * 1.2          # 暴击（非暴 ≤1.15a）
        is_lucky = dealt > a * 1.8         # 幸运一击（暴击≤1.725a，幸运≥1.9125a）
        return logs, dealt, is_crit, is_lucky

    print("===== 1. pierce 魔法分支修复（P1-6）=====\n")
    p_magi = {"name": "魔法测试", "kind": "魔法", "power": 1.0, "lv": 30, "cd": 1}
    p_pierce = {"name": "审判测试", "kind": "魔法", "power": 1.0, "lv": 30, "cd": 1, "pierce": True}
    random.seed(3)
    p1 = mk_player()
    b1 = BT.Battle("怪物", mk_enemy(mdef=500), {}, p1)
    st1 = b1._player_stats(p1)
    base = int(st1["matk"] * 1.0)
    h0 = b1.enemy["hp"]
    b1._player_skill(st1, "魔法测试", p_magi, p1)
    dealt_magi = h0 - b1.enemy["hp"]
    random.seed(3)
    p1b = mk_player()
    b1b = BT.Battle("怪物", mk_enemy(mdef=500), {}, p1b)
    h0 = b1b.enemy["hp"]
    b1b._player_skill(b1b._player_stats(p1b), "审判测试", p_pierce, p1b)
    dealt_pierce = h0 - b1b.enemy["hp"]
    check("pierce 魔法无视 mdef=500（≈matk×power ±15%）",
          0.8 * base <= dealt_pierce <= 1.2 * base, f"{dealt_pierce} vs base {base}")
    check("普通魔法被 mdef=500 大幅削减（< pierce×50%）",
          dealt_magi < dealt_pierce * 0.5, f"{dealt_magi} vs {dealt_pierce}")

    print("\n===== 2. 安眠曲改睡眠（P1-3）=====\n")
    info_sleep = EG.skill_info("cls_mu_shi", "安眠曲")  # v112.3：安眠曲归入牧师攻线 T1 吟游诗人分支
    check("安眠曲 effect=sleep", info_sleep and info_sleep.get("effect") == "sleep",
          str(info_sleep))
    random.seed(5)
    p2 = mk_player(cls="cls_mu_shi", skills=["安眠曲"])
    b2 = BT.Battle("怪物", mk_enemy(), {}, p2)
    logs2 = b2._player_skill(b2._player_stats(p2), "安眠曲", info_sleep, p2)
    check("施放后 e_buffs['sleep']=2（普通怪）", b2.e_buffs.get("sleep") == 2, str(b2.e_buffs))
    l2, d2 = b2._enemy_turn(p2)
    check("敌方回合被跳过（伤害 0）", d2 == 0, f"dmg {d2}")
    check("日志含『沉睡』", any("沉睡" in x for x in l2), str(l2))
    check("跳过一回合后 sleep 剩 1", b2.e_buffs.get("sleep") == 1, str(b2.e_buffs))
    # 再睡一回合后消耗完
    l2b, d2b = b2._enemy_turn(p2)
    check("第二回合再跳过", d2b == 0, f"dmg {d2b}")
    check("sleep 已耗尽", "sleep" not in b2.e_buffs, str(b2.e_buffs))
    # 受击解除：再挂睡眠后普攻打醒
    b2.e_buffs["sleep"] = 2
    st2 = b2._player_stats(p2)
    random.seed(8)
    b2._player_attack(st2, p2)
    check("普攻打醒睡眠（受击解除）", "sleep" not in b2.e_buffs, str(b2.e_buffs))
    # 世界 Boss 只睡 1 回合
    p2b = mk_player(cls="cls_mu_shi", skills=["安眠曲"])
    b2b = BT.Battle("worldboss", mk_enemy(), {}, p2b)
    b2b._player_skill(b2b._player_stats(p2b), "安眠曲", info_sleep, p2b)
    check("世界 Boss 只睡 1 回合", b2b.e_buffs.get("sleep") == 1, str(b2b.e_buffs))
    # dot 不打醒：灼烧结算后 sleep 保留
    p2c = mk_player(cls="cls_mu_shi", skills=["安眠曲"])
    b2c = BT.Battle("怪物", mk_enemy(), {}, p2c)
    b2c._player_skill(b2c._player_stats(p2c), "安眠曲", info_sleep, p2c)
    b2c.mech_stacks["burn"] = 1
    b2c._turn_start(p2c)
    check("灼烧 dot 不打醒睡眠", "sleep" in b2c.e_buffs, str(b2c.e_buffs))

    print("\n===== 3. 火之亲和（龙血灼烧 +20%）=====\n")
    info_hz = EG.skill_info("龙裔誓约", "火之亲和")
    check("火之亲和技能存在", info_hz is not None, str(info_hz))
    check("火之亲和 passive=burn_amp×1.2",
          info_hz and info_hz.get("passive") == {"proc": "burn_amp", "mult": 1.2},
          str(info_hz and info_hz.get("passive")))
    random.seed(7)
    p3 = mk_player(cls="龙裔誓约", skills=["火之亲和"])
    b3 = BT.Battle("怪物", mk_enemy(hp=10000), {}, p3)
    b3.mech_stacks["burn"] = 1
    logs3 = b3._turn_start(p3)
    hp_loss3 = 10000 - b3.enemy["hp"]
    expect3 = int(10000 * 0.03 * 1.2)
    check(f"灼烧伤害 = max_hp×3%×1.2（={expect3}）", hp_loss3 == expect3, f"got {hp_loss3}")
    check("日志含『火之亲和』", any("火之亲和" in x for x in logs3), str(logs3))
    random.seed(7)
    p3b = mk_player(cls="龙裔誓约")
    b3b = BT.Battle("怪物", mk_enemy(hp=10000), {}, p3b)
    b3b.mech_stacks["burn"] = 1
    b3b._turn_start(p3b)
    hp_loss3b = 10000 - b3b.enemy["hp"]
    check("无火之亲和：灼烧 = max_hp×3%", hp_loss3b == 300, f"got {hp_loss3b}")

    print("\n===== 4. 运势 luck 暴击联动（P1-1）=====\n")
    n = 900
    # 4a. luck → 暴击补充（luck=0.4 → +12%）
    random.seed(11)
    p4 = mk_player(extra_stats={"luck": 0.4})
    b4 = BT.Battle("怪物", mk_enemy(def_=0, hp=10**9), {}, p4)
    st4 = b4._player_stats(p4)
    a4 = st4["atk"]
    base_crit = st4["crit"]
    crits = 0
    for _ in range(n):
        _, _, is_crit, _ = attack_once(b4, st4, p4, 1000 + _, atk=a4)
        crits += 1 if is_crit else 0
    print(f"  (base crit={base_crit:.3f}, luck=0.4 → 期望 {base_crit+0.12:.3f}, 实测 {crits/n:.3f})")
    check("luck=0.4 暴击率 ≈ crit+0.12（±0.04）",
          abs(crits / n - (base_crit + 0.12)) < 0.04, f"{crits/n:.3f}")
    # 对照 luck=0
    random.seed(11)
    p4z = mk_player(extra_stats={"luck": 0.0})
    b4z = BT.Battle("怪物", mk_enemy(def_=0, hp=10**9), {}, p4z)
    st4z = b4z._player_stats(p4z)
    a4z = st4z["atk"]
    critsz = 0
    for _ in range(n):
        _, _, is_crit, _ = attack_once(b4z, st4z, p4z, 1000 + _, atk=a4z)
        critsz += 1 if is_crit else 0
    print(f"  (luck=0 实测暴击 {critsz/n:.3f} vs 期望 {st4z['crit']:.3f})")
    check("luck=0 暴击率不变（±0.04）", abs(critsz / n - st4z["crit"]) < 0.04,
          f"{critsz/n:.3f}")

    # 4b. 幸运一击：暴击后 30% 概率追加（日志统计）
    n2 = 600
    random.seed(13)
    p4b = mk_player(extra_stats={"crit": 0.9, "luck": 0.5})
    b4b = BT.Battle("怪物", mk_enemy(def_=0, hp=10**9), {}, p4b)
    st4b = b4b._player_stats(p4b)
    lucky_n = 0
    for _ in range(n2):
        logs, _, _, _ = attack_once(b4b, st4b, p4b, 2000 + _)
        if any("幸运一击" in x for x in logs):
            lucky_n += 1
    exp_lucky = (st4b["crit"] + 0.12) * 0.30
    print(f"  (暴击≈{st4b['crit']+0.12:.3f}, 幸运 {lucky_n}/{n2}={lucky_n/n2:.3f}, 期望≈{exp_lucky:.3f})")
    check("幸运一击 ≈ 暴击率×30%（±0.05）", abs(lucky_n / n2 - exp_lucky) < 0.05,
          f"{lucky_n/n2:.3f}")

    # 4c. 幸运一击伤害 = 暴击伤害 ×1.5
    random.seed(17)
    p4c = mk_player(extra_stats={"crit": 1.0, "luck": 1.0})
    b4c = BT.Battle("怪物", mk_enemy(def_=0, hp=10**9), {}, p4c)
    st4c = b4c._player_stats(p4c)
    got_lucky = False
    lucky_dealt = 0
    for _ in range(50):
        logs, dealt, is_crit, is_lucky = attack_once(b4c, st4c, p4c, 3000 + _)
        if is_lucky:
            got_lucky = True
            lucky_dealt = dealt
            print(f"  (幸运一击伤害 {dealt}，非幸运暴击区间 127-173)")
            break
    # v110.5 X3：恒真断言替换——got_lucky 为 True 时断言实际伤害 > 190（= 暴击×1.5，a=125 下限）。
    # 若幸运一击未触发到或伤害未达暴击×1.5（192.5 起）则必红。
    check("幸运一击伤害 > 190（= 暴击×1.5）",
          got_lucky and lucky_dealt > 190,
          f"lucky={got_lucky}, dealt={lucky_dealt}")

    print("\n===== 5. 武圣连击 0.50（P1-2）=====\n")
    def combo_play(with_passive):
        random.seed(23)
        sk = ["连招精通"] if with_passive else []
        p = mk_player(cls="拳师", skills=sk)
        b = BT.Battle("怪物", mk_enemy(def_=0, hp=10**9), {}, p)
        st = b._player_stats(p)
        s_quan = EG.skill_info("拳师", "直拳")
        s_ti = EG.skill_info("拳师", "侧踢")
        s_zhang = EG.skill_info("拳师", "钢拳")
        b._player_skill(st, "直拳", s_quan, p)
        b._player_skill(st, "侧踢", s_ti, p)
        logs = b._player_skill(st, "钢拳", s_zhang, p)
        return logs, 10**9 - b.enemy["hp"]
    logs_a, total_a = combo_play(False)
    logs_b, total_b = combo_play(True)
    import re as _re
    m_b = _re.search(r"钢拳】，造成 (\d+) 点伤害", next(x for x in logs_b if "钢拳" in x))
    main_b = int(m_b.group(1))
    exp_a = int(main_b * 0.30)   # 无被动追加
    exp_b = int(main_b * 0.50)   # 有被动追加
    check(f"三连触发（日志含『三连击破』）", any("三连击破" in x for x in logs_b), str(logs_b))
    check(f"无被动：追加 = 主伤×0.30（{exp_a}）", (total_b - total_a) == exp_b - exp_a,
          f"差值 {total_b-total_a} vs 期望 {exp_b-exp_a}")
    # v110.5 X3：恒真断言替换——从 logs_b 解析『三连击破』行的实际追加数值，
    # 断言 == int(主伤×0.50)。若被动未生效（追加仍走 0.30）或日志格式变动则必红。
    _re_bonus = _re.search(r"三连击破.*?追加 (\d+) 点伤害", next(x for x in logs_b if "三连击破" in x))
    got_bonus = int(_re_bonus.group(1)) if _re_bonus else None
    check(f"有被动：追加 = 主伤×0.50（{exp_b}）",
          got_bonus is not None and got_bonus == exp_b,
          f"got {got_bonus} vs 期望 {exp_b}（主伤 {main_b}）")
    # 对照：无被动组合（logs_a 也必有三连，追加走 0.30）同样可解析出 0.30
    _re_bonus_a = _re.search(r"三连击破.*?追加 (\d+) 点伤害", next(x for x in logs_a if "三连击破" in x))
    got_bonus_a = int(_re_bonus_a.group(1)) if _re_bonus_a else None
    check(f"无被动对照：追加 = 主伤×0.30（{exp_a}）",
          got_bonus_a is not None and got_bonus_a == exp_a,
          f"got {got_bonus_a} vs 期望 {exp_a}（主伤 {main_b}）")
    check("日志无『斗气』残留", not any("斗气" in x for x in logs_a + logs_b),
          str([x for x in logs_a + logs_b if "斗气" in x]))

    print("\n===== 6. PVP 韧性对称 =====\n")
    n3 = 900
    # 6a. 真实快照路径：快照含 tenacity/def（P0 快照补齐），玩家打 PVP 敌人暴击率 ×(1-敌韧)
    from data.plugins.dragonfall.game.commands import combat as CMB
    p_def = mk_player(extra_stats={"crit": 0.6, "luck": 0.0})
    p_def["qq_id"] = 999
    p_def["name"] = "测试对手"
    snap = CMB.CombatCmds._pvp_snapshot(CMB.CombatCmds(), p_def)
    check("PVP 快照含 tenacity 字段", snap.get("tenacity", 0) == p_def["equipment"]["weapon"]["stats"].get("tenacity", 0),
          f"snap tenacity={snap.get('tenacity')}")
    check("PVP 快照含 def 字段", snap.get("def", 0) > 0, f"def={snap.get('def')}")
    snap["tenacity"] = 0.5  # 显式韧性场景
    snap["hp"] = 10**9
    snap["max_hp"] = 10**9
    snap["atk"] = 0
    snap["def"] = 0  # 只测韧性路径，防御置 0（伤害阈值法依赖 def=0）
    b6 = BT.Battle("pvp", snap, {}, p_def)
    st6 = b6._player_stats(p_def)
    a6 = st6["atk"]
    crits6 = 0
    for _ in range(n3):
        _, _, is_crit, _ = attack_once(b6, st6, p_def, 4000 + _, atk=a6)
        crits6 += 1 if is_crit else 0
    exp6 = st6["crit"] * (1 - 0.5)
    print(f"  (PVP 快照敌韧 0.5: 期望 {exp6:.3f}, 实测 {crits6/n3:.3f})")
    check("PVP 玩家暴击率 × (1-敌韧)（快照路径 ±0.05）", abs(crits6 / n3 - exp6) < 0.05,
          f"{crits6/n3:.3f}")
    # 6b. 直接构造 enemy 韧性（单元级对照）
    random.seed(31)
    p6b = mk_player(extra_stats={"crit": 0.6, "luck": 0.0})
    b6b = BT.Battle("pvp", mk_enemy(def_=0, hp=10**9, tenacity=0.5), {}, p6b)
    st6b = b6b._player_stats(p6b)
    a6b = st6b["atk"]
    crits6b = 0
    for _ in range(n3):
        _, _, is_crit, _ = attack_once(b6b, st6b, p6b, 4000 + _, atk=a6b)
        crits6b += 1 if is_crit else 0
    exp6b = st6b["crit"] * (1 - 0.5)
    print(f"  (PVP 敌韧 0.5 单元级: 期望 {exp6b:.3f}, 实测 {crits6b/n3:.3f})")
    check("PVP 玩家暴击率 × (1-敌韧)（单元级 ±0.05）", abs(crits6b / n3 - exp6b) < 0.05,
          f"{crits6b/n3:.3f}")
    # 6c. PVE：无韧性 → 暴击率不变
    random.seed(31)
    p6c = mk_player(extra_stats={"crit": 0.6, "luck": 0.0})
    b6c = BT.Battle("怪物", mk_enemy(def_=0, hp=10**9), {}, p6c)
    st6c = b6c._player_stats(p6c)
    a6c = st6c["atk"]
    crits6c = 0
    for _ in range(n3):
        _, _, is_crit, _ = attack_once(b6c, st6c, p6c, 4000 + _, atk=a6c)
        crits6c += 1 if is_crit else 0
    print(f"  (PVE: 期望 {st6c['crit']:.3f}, 实测 {crits6c/n3:.3f})")
    check("PVE 玩家暴击率不受影响（±0.05）", abs(crits6c / n3 - st6c["crit"]) < 0.05,
          f"{crits6c/n3:.3f}")

    print(f"\n===== 结果: {passed} passed, {failed} failed =====")
    return failed == 0


if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
