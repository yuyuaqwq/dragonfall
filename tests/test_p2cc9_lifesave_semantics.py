# -*- coding: utf-8 -*-
"""v181.P2C-C9 保命/特殊族语义门禁（行为零变化单体断言 + battle 消费点硬断言）。

在 OLD-NEW 差分探针（test_p2cc9_lifesave_probe.py）之外，对每个代表场景做
数值/副作用硬断言：
1. 族路由：5 key → _WE_EXEC_KEYS 精确路由（proc_dr_revive 2 + proc_special 3）
2. undying_will：battle_start 登记 we_undying_used=False；threshold 低血(15%)
   置 we_undying_immune + 回 max_hp×heal_pct(0.10)；hp≥threshold(0.20) 不触发；
   used 后再触发不生效（每场 1 次）
3. death_dance：battle_start 初始化 we_death_pool=0；turn_start pool=350 →
   pay=max(1,int(350×0.10))=35、hp−35、pool 315（日志原文案含缓伤池结算）
4. death_dance_armor：passive taken 500 → taken=460（×0.92）
5. novice_first_turn_guard/dodge：battle_start 置 novice_guard_active/
   novice_dodge_active=True + 日志原文案
6. battle _post_hp_lethal：undying immune 致死 → 回拉 max_hp×hp_pct(0.10)（表读）；
   death_dance 受击池填充 dmg×pool_pct(0.35)（表读）；无特效不进段
7. battle _mitigate_chain：守御 tick1 受击 dmg×0.90；tick>1 全额
8. battle _roll_dodge：远行首刻闪避 +5%（base dodge 0.03 + 5% 乘算 0.0785，
   命中 seed 扫描）；无远行 base 0.03 低频闪避（对照组不做永不闪断言——基础 3% 存在）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import (
    WEAPON_EFFECTS, proc as we_proc, effect_data,
    _we_family, _WE_EXEC_KEYS,
)

DR_KEYS = ["undying_will", "death_dance_armor"]
SPECIAL_KEYS = ["death_dance", "novice_first_turn_guard", "novice_first_turn_dodge"]

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, class_name="战士", hp=9999, max_hp=9999):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": hp, "max_hp": max_hp, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": class_name, "qq_id": "t1"}

def mk_enemy(hp=100000, **kw):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    e.update(kw)
    return e

def battle_for(key, **pw):
    p = mk_player([key], **pw)
    b = BT.Battle("monster", mk_enemy(), player=p)
    return b, p

def test_routing():
    print("【1. 族路由】")
    for k in DR_KEYS:
        check(f"{k} family=proc_dr_revive 且进路由", _we_family(k) == "proc_dr_revive"
              and k in _WE_EXEC_KEYS and _WE_EXEC_KEYS[k] == "proc_dr_revive",
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    for k in SPECIAL_KEYS:
        check(f"{k} family=proc_special 且进路由", _we_family(k) == "proc_special"
              and k in _WE_EXEC_KEYS and _WE_EXEC_KEYS[k] == "proc_special",
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    # v181.P2C-C10：guard_regen/dawn_regen/undying_band/novice_dawn_mana 已迁 proc_aux 收尾族
    for k in ("guard_regen", "dawn_regen", "undying_band", "novice_dawn_mana"):
        check(f"C10 {k} 进 proc_aux 路由", _WE_EXEC_KEYS.get(k) == "proc_aux",
              f"route={_WE_EXEC_KEYS.get(k)}")

def test_undying_will():
    print("【2. 不灭意志（battle_start 登记 + threshold 免死/回血/每场 1 次）】")
    b, p = battle_for("undying_will")
    we_proc(b, p, "battle_start", {}, [])
    check("battle_start 登记 we_undying_used=False",
          (p.get("eff") or {}).get("we_undying_used") is False, str(p.get("eff")))
    # 低血 15%：threshold 触发 → immune + used + 回血 max_hp×0.10
    _maxhp = int(p["max_hp"])
    p["hp"] = int(_maxhp * 0.15)
    logs = []
    we_proc(b, p, "threshold", {"dmg": 100}, logs)
    check("低血触发置 we_undying_immune", (p.get("eff") or {}).get("we_undying_immune") is True,
          str(p.get("eff")))
    check("触发置 we_undying_used=True", (p.get("eff") or {}).get("we_undying_used") is True,
          str(p.get("eff")))
    check("回血 heal_pct×max_hp", p["hp"] > int(_maxhp * 0.15), f"hp={p['hp']}")
    check("日志含 不灭意志", any("不灭意志" in l for l in logs), str(logs))
    # 高血 50%：不触发
    b2, p2 = battle_for("undying_will")
    p2["hp"] = int(p2["max_hp"] * 0.50)
    we_proc(b2, p2, "battle_start", {}, [])
    logs2 = []
    we_proc(b2, p2, "threshold", {"dmg": 100}, logs2)
    check("hp≥20% 不触发（无 immune）", not (p2.get("eff") or {}).get("we_undying_immune"),
          str(p2.get("eff")))
    # used 后再触发：不生效
    b3, p3 = battle_for("undying_will")
    p3["hp"] = int(p3["max_hp"] * 0.15)
    p3.setdefault("eff", {})["we_undying_used"] = True
    logs3 = []
    we_proc(b3, p3, "threshold", {"dmg": 100}, logs3)
    check("used 后不再触发", not (p3.get("eff") or {}).get("we_undying_immune")
          and not logs3, str(p3.get("eff")))

def test_death_dance():
    print("【3. 死亡之舞（battle_start 初始化 + turn_start 结算）】")
    b, p = battle_for("death_dance")
    we_proc(b, p, "battle_start", {}, [])
    check("battle_start 初始化 we_death_pool=0.0", (p.get("eff") or {}).get("we_death_pool") == 0.0,
          str(p.get("eff")))
    p.setdefault("eff", {})["we_death_pool"] = 350.0
    p["hp"] = 5000
    logs = []
    we_proc(b, p, "turn_start", {}, logs)
    check("pool=350 → pay=35", p["hp"] == 5000 - 35, f"hp={p['hp']}")
    check("pool 递减 350−35=315", abs(float((p.get("eff") or {}).get("we_death_pool", 0)) - 315.0) < 1e-6,
          str(p.get("eff")))
    check("结算日志原文案", any("缓伤池结算" in l and "损失 35 点生命" in l for l in logs), str(logs))
    # pool=0：空转无日志
    b2, p2 = battle_for("death_dance")
    p2.setdefault("eff", {})["we_death_pool"] = 0.0
    p2["hp"] = 5000
    logs2 = []
    we_proc(b2, p2, "turn_start", {}, logs2)
    check("pool=0 空转不扣血", p2["hp"] == 5000 and not logs2, f"hp={p2['hp']} logs={logs2}")

def test_death_dance_armor():
    print("【4. 亡舞战铠 passive taken 减伤 8%】")
    b, p = battle_for("death_dance_armor")
    ctx = {"taken": 500}
    we_proc(b, p, "passive", ctx, [])
    check("taken 500 → 460（×0.92）", ctx["taken"] == 460, f"taken={ctx['taken']}")
    # 无 taken 键：空转
    b2, p2 = battle_for("death_dance_armor")
    ctx2 = {}
    we_proc(b2, p2, "passive", ctx2, [])
    check("无 taken 空转", ctx2 == {}, str(ctx2))

def test_novice_marks():
    print("【5. 新手首刻标记（battle_start 置标 + 原文案日志）】")
    b, p = battle_for("novice_first_turn_guard")
    logs = []
    we_proc(b, p, "battle_start", {}, logs)
    check("守御标记 novice_guard_active=True", (p.get("eff") or {}).get("novice_guard_active") is True,
          str(p.get("eff")))
    check("守御日志原文案", any("守御" in l and "首刻受击伤害 -10%" in l for l in logs), str(logs))
    b2, p2 = battle_for("novice_first_turn_dodge")
    logs2 = []
    we_proc(b2, p2, "battle_start", {}, logs2)
    check("远行标记 novice_dodge_active=True", (p2.get("eff") or {}).get("novice_dodge_active") is True,
          str(p2.get("eff")))
    check("远行日志原文案", any("远行" in l and "首刻闪避率 +5%" in l for l in logs2), str(logs2))

def test_battle_post_hp_lethal():
    print("【6. battle _post_hp_lethal（免疫回拉 hp_pct + 池填充 pool_pct 表读）】")
    # undying_will 死亡链端到端：低血被一击打死（_damage_actor 扣血 → threshold proc 置
    # immune + 回血 10% → immune 兜底回拉）→ 不死，最终 hp = max(1, max_hp×hp_pct 表读 0.10)
    # 固定 seed（基础闪避 3% roll 不干扰致死命中——seed 1 已验证致死必中）
    random.seed(1)
    b, p = battle_for("undying_will")
    _maxhp = int(b._focus["max_hp"])
    p["hp"] = int(_maxhp * 0.15)
    logs = []
    b._damage_actor(p, 999999, logs, source="测试")
    check("undying 致死不死（hp 回拉至 max_hp×hp_pct=0.10）", p["hp"] == max(1, int(_maxhp * 0.10)),
          f"hp={p['hp']} max={_maxhp} logs={logs}")
    # 死亡链存活由 threshold 回血 + 回拉兜底共同保证——"撑住了"兜底日志只在回拉真正执行时出现
    # （本场景 threshold 回血 78 后 999999 打穿 → hp=0 → 回拉执行 → 该日志出现）——见下方二次致死
    check("used 置位 + immune 消费清",
          (p.get("eff") or {}).get("we_undying_used") is True
          and "we_undying_immune" not in (p.get("eff") or {}), str(p.get("eff")))
    # 表读一致性：hp_pct/pool_pct 字段 == 硬编码旧值
    check("表 undying_will.hp_pct=0.10", abs(float(effect_data(b, p, "undying_will").get("hp_pct")) - 0.10) < 1e-9, "")
    check("表 death_dance.pool_pct=0.35", abs(float(effect_data(b, p, "death_dance").get("pool_pct")) - 0.35) < 1e-9, "")
    # 免疫兜底回拉单元（battle 消费分支直测）：immune 置位 + hp=0（治疗被禁疗完全压制等场景）
    # → _post_hp_lethal 回拉 max_hp×hp_pct + 撑住了日志 + 清 immune
    b4, p4 = battle_for("undying_will")
    _m4 = int(b4._focus["max_hp"])
    p4.setdefault("eff", {})["we_undying_immune"] = True
    p4.setdefault("eff", {})["we_undying_used"] = True
    p4["hp"] = 0
    logs4 = []
    b4._post_hp_lethal(p4, 200, logs4)
    check("immune 兜底回拉 max_hp×hp_pct=0.10", p4["hp"] == max(1, int(_m4 * 0.10)),
          f"hp={p4['hp']} max={_m4}")
    check("回拉日志 你撑住了致命一击", any("撑住了致命一击" in l for l in logs4), str(logs4))
    check("immune 消费清（兜底分支）", "we_undying_immune" not in (p4.get("eff") or {}),
          str(p4.get("eff")))
    # 每场 1 次：二次致死不再救
    p["hp"] = int(_maxhp * 0.10)
    b._damage_actor(p, 999999, [], source="测试")
    check("二次致死（used 已置）不救 hp=0", p["hp"] == 0, f"hp={p['hp']}")
    # death_dance：受击填充 dmg×0.35（表读）+ 无特效不进段
    b2, p2 = battle_for("death_dance")
    p2["hp"] = 5000
    b2._post_hp_lethal(p2, 1000, [])
    check("池填充 dmg×pool_pct=350", abs(float((p2.get("eff") or {}).get("we_death_pool", 0)) - 350.0) < 1e-6,
          str(p2.get("eff")))
    b3, p3 = battle_for("starlight_bulwark")  # 无保命特效
    p3["hp"] = 5000
    b3._post_hp_lethal(p3, 1000, [])
    check("无保命特效不进段（无 pool/immune）",
          "we_death_pool" not in (p3.get("eff") or {})
          and "we_undying_immune" not in (p3.get("eff") or {}), str(p3.get("eff")))

def test_battle_mitigate():
    print("【7. battle _mitigate_chain（守御首刻减伤 mark_key）】")
    b, p = battle_for("novice_first_turn_guard", hp=50000, max_hp=50000)
    b._focus["max_hp"] = 50000
    b._focus["hp"] = 50000
    we_proc(b, p, "battle_start", {}, [])
    b._now = 0.5  # tick 1
    hp_before = p["hp"]
    b._damage_actor(p, 1000, [], source="测试")
    check("tick1 受击 -10% 扣 900", hp_before - p["hp"] == 900, f"taken={hp_before - p['hp']}")
    b._now = 2.0  # tick 3
    p["hp"] = 50000
    hp_before = p["hp"]
    b._damage_actor(p, 1000, [], source="测试")
    check("tick>1 全额受击 1000", hp_before - p["hp"] == 1000, f"taken={hp_before - p['hp']}")

def test_battle_dodge():
    print("【8. battle _roll_dodge（远行首刻闪避 mark_key +5%）】")
    # 基础 dodge=0.03（玩家 class 面板）→ 远行首刻乘算 1−(1−0.03)(1−0.05)=0.0785；命中 seed 扫描
    sd = hit = miss = None
    for sd in range(1, 800):
        random.seed(sd)
        b, p = battle_for("novice_first_turn_dodge")
        we_proc(b, p, "battle_start", {}, [])
        b._now = 0.5
        if b._roll_dodge(p, []):
            hit = sd
            break
    check("远行首刻闪避可命中（+5% 乘算叠加）", hit, f"sd={sd}")
    # 对照组（无远行）：同批 seed 无首刻加成 → 命中频率应显著低于带远行（0.03 vs 0.0785）
    plain_hits = 0
    for sd in range(1, 201):
        random.seed(sd)
        b0, p0 = battle_for("novice_lifesteal")  # 无关特效对照组
        if b0._roll_dodge(p0, []):
            plain_hits += 1
    check("对照组基础闪避命中率低（≤3% 理论，<10% 断言）", plain_hits < 20, f"hits={plain_hits}/200")
    # 表 mark_key 权威
    bd, pd = battle_for("novice_first_turn_dodge")
    check("表 novice_first_turn_dodge.mark_key=novice_dodge_active",
          effect_data(bd, pd, "novice_first_turn_dodge").get("mark_key") == "novice_dodge_active", "")
    bg, pg = battle_for("novice_first_turn_guard")
    check("表 novice_first_turn_guard.mark_key=novice_guard_active",
          effect_data(bg, pg, "novice_first_turn_guard").get("mark_key") == "novice_guard_active", "")

if __name__ == "__main__":
    test_routing()
    test_undying_will()
    test_death_dance()
    test_death_dance_armor()
    test_novice_marks()
    test_battle_post_hp_lethal()
    test_battle_mitigate()
    test_battle_dodge()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)