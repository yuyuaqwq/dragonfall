# -*- coding: utf-8 -*-
"""v181.P2C-C7 标记族语义门禁（行为零变化单体断言 + battle 消费点探针）。

覆盖（探针 test_p2cc7_marks_probe.py 之外的代表场景硬断言）：
1. 族路由：9 key → _WE_EXEC_KEYS 精确路由（proc_next_atk_mark 5 + proc_retort_mark 4）
2. trinity_rhythm skill_hit → eff.we_trinity=0.30 + we_trinity_thunder=0.15
3. mountain_break skill_hit → eff.we_mountain=0.25；oath_blade → eff.we_oath=0.25
4. novice_spark_followup skill_cast → stacks.novice_spark=True（日志原文案）
5. dusk_blade kill → 每场 1 次：buffs.stealth + eff.we_dusk_dmg=0.30；二次 kill 不再置
6. gargoyle/titan/ranger taken → eff.we_retort=max（30%/40%/20%）
7. guardian_will taken 命中 seed → e_buffs.mon_atk_down=1 + _weaken_val=0.25（原文案日志）
8. oath_blade/dusk_blade passive 消费 mult+tag 并清标（battle ctx 无 attack 键——旧语义保真）
9. trinity/mountain/retort passive：ctx.attack 门 battle 恒不传 → 空转不清标（旧语义保真）
10. battle 消费点：_skill_finalize_damage basic 消费 novice_spark 标记清（读表 stack_key）
11. battle 消费点：_decay_buff_table 对 we_oath/stealth 一次性键不衰减（we_oath 保留）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import (
    WEAPON_EFFECTS, proc as we_proc, effect_data, _we_family, _WE_EXEC_KEYS,
)

NEXT_KEYS = ["trinity_rhythm", "mountain_break", "oath_blade", "novice_spark_followup", "dusk_blade"]
RETORT_KEYS = ["gargoyle_retort", "titan_retort", "ranger_retort", "guardian_will"]

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, class_name="战士"):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
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
    for k in NEXT_KEYS:
        check(f"{k} family=proc_next_atk_mark 且进路由", _we_family(k) == "proc_next_atk_mark"
              and k in _WE_EXEC_KEYS and _WE_EXEC_KEYS[k] == "proc_next_atk_mark",
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    for k in RETORT_KEYS:
        check(f"{k} family=proc_retort_mark 且进路由", _we_family(k) == "proc_retort_mark"
              and k in _WE_EXEC_KEYS and _WE_EXEC_KEYS[k] == "proc_retort_mark",
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    # v181.P2C-C10：guard_regen/dawn_regen 已迁 proc_aux 收尾族
    for k in ("guard_regen", "dawn_regen"):
        check(f"C10 {k} 进 proc_aux 路由", _WE_EXEC_KEYS.get(k) == "proc_aux",
              f"route={_WE_EXEC_KEYS.get(k)}")

def test_skill_hit_marks():
    print("【2. skill_hit 置标（三相/破岳/咒誓）】")
    for key, ek, ev in (("trinity_rhythm", "we_trinity", 0.30), ("mountain_break", "we_mountain", 0.25),
                        ("oath_blade", "we_oath", 0.25)):
        b, p = battle_for(key)
        we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": False, "skill": "测试", "kind": "物理"}, [])
        check(f"{key} 置 {ek}={ev}", abs(float((p.get("eff") or {}).get(ek, 0)) - ev) < 1e-9,
              str(p.get("eff")))
    b, p = battle_for("trinity_rhythm")
    we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": False}, [])
    check("trinity 附雷标 we_trinity_thunder=0.15",
          abs(float((p.get("eff") or {}).get("we_trinity_thunder", 0)) - 0.15) < 1e-9, str(p.get("eff")))

def test_novice_spark():
    print("【3. 星火 skill_cast 置 stacks.novice_spark】")
    b, p = battle_for("novice_spark_followup")
    logs = []
    we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "物理"}, logs)
    check("stacks.novice_spark=True", b._p_stacks().get("novice_spark") is True, str(b._p_stacks()))
    check("日志原文案", any("星火" in l for l in logs), str(logs))
    # 表 stack_key 权威（读表 == 硬编码键）
    check("表 stack_key=novice_spark", effect_data(b, p, "novice_spark_followup").get("stack_key") == "novice_spark", "")

def test_dusk_blade_kill():
    print("【4. 暮裂潜行 kill（每场 1 次）】")
    b, p = battle_for("dusk_blade")
    logs = []
    we_proc(b, p, "kill", {}, logs)
    check("潜行 buffs.stealth + we_dusk_dmg=0.30",
          b._p_buffs_bag().get("stealth") == 1
          and abs(float((p.get("eff") or {}).get("we_dusk_dmg", 0)) - 0.30) < 1e-9,
          f"buffs={b._p_buffs_bag()} eff={p.get('eff')}")
    check("we_dusk_used 置位", bool((p.get("eff") or {}).get("we_dusk_used")), str(p.get("eff")))
    check("日志原文案", any("暮裂潜行" in l for l in logs), str(logs))
    # 二次 kill 不再置（每场 1 次——标记保持原值）
    we_proc(b, p, "kill", {}, [])
    check("二次 kill 不重置", abs(float((p.get("eff") or {}).get("we_dusk_dmg", 0)) - 0.30) < 1e-9
          and b._p_buffs_bag().get("stealth") == 1, str(p.get("eff")))

def test_retort_taken():
    print("【5. taken 置 we_retort（反击三件 max）】")
    for key, exp in (("gargoyle_retort", 0.30), ("titan_retort", 0.40), ("ranger_retort", 0.20)):
        b, p = battle_for(key)
        we_proc(b, p, "taken", {"dmg": 100}, [])
        check(f"{key} we_retort={exp}", abs(float((p.get("eff") or {}).get("we_retort", 0)) - exp) < 1e-9,
              str(p.get("eff")))

def test_guardian_will_hit():
    print("【6. 卫士信念 taken（命中 seed）】")
    sd = hit = None
    for sd in range(1, 400):
        random.seed(sd)
        b, p = battle_for("guardian_will")
        logs = []
        we_proc(b, p, "taken", {"dmg": 100}, logs)
        if (b.enemy.get("buffs") or {}).get("mon_atk_down"):
            hit = True
            check("guardian_will 命中 seed 触发弱化",
                  b.enemy["buffs"].get("mon_atk_down") == 1
                  and abs(float(b.enemy["buffs"].get("_weaken_val", 0)) - 0.25) < 1e-9,
                  f"eb={b.enemy['buffs']}")
            check("卫士信念日志原文案", any("卫士信念" in l for l in logs), str(logs))
            break
    check("guardian_will 可命中", hit, f"sd={sd}")

def test_passive_consume_old_semantics():
    print("【7. passive 消费（旧语义保真：attack 门 / 无条件）】")
    # oath/dusk：battle ctx 无 attack 键也消费（无 attack 门）——与旧 handler 逐字一致
    # ⚠️ 旧 handler mult = ctx.mult × 标记原值（0.25/0.30 原样乘，非 1+值——tag 文案 x1.25 系历史
    # 文案与数值不一致，逐字保真）——探针被动 diff OLD==NEW 已锁定
    for key, mk, mult in (("oath_blade", "we_oath", 0.25), ("dusk_blade", "we_dusk_dmg", 0.30)):
        b, p = battle_for(key)
        p.setdefault("eff", {})[mk] = mult
        ctx = {"mult": 1.0, "tags": []}  # 模拟 battle passive 挂点 ctx（无 attack 键）
        we_proc(b, p, "passive", ctx, [])
        check(f"{key} passive 消费 mult=原值×标记", abs(ctx["mult"] - mult) < 1e-9
              and bool(ctx["tags"]), f"mult={ctx['mult']} tags={ctx['tags']}")
        check(f"{key} 消费后清标", mk not in (p.get("eff") or {}), str(p.get("eff")))
    # trinity/mountain/retort：ctx.attack 门（battle 恒不传 → 空转不清标）
    for key, mk, in (("trinity_rhythm", "we_trinity"), ("mountain_break", "we_mountain")):
        b, p = battle_for(key)
        p.setdefault("eff", {})[mk] = 0.30 if key == "trinity_rhythm" else 0.25
        ctx = {"mult": 1.0, "tags": []}  # battle 真实 ctx 无 attack 键
        we_proc(b, p, "passive", ctx, [])
        check(f"{key} passive 无 attack 键空转不清标", ctx["mult"] == 1.0 and not ctx["tags"]
              and mk in (p.get("eff") or {}), f"mult={ctx['mult']} eff={p.get('eff')}")
    b, p = battle_for("titan_retort")
    p.setdefault("eff", {})["we_retort"] = 0.40
    ctx = {"mult": 1.0, "tags": []}
    we_proc(b, p, "passive", ctx, [])
    check("retort passive 无 attack 键空转不清标", ctx["mult"] == 1.0 and not ctx["tags"]
          and abs(float((p.get("eff") or {}).get("we_retort", 0)) - 0.40) < 1e-9,
          f"mult={ctx['mult']} eff={p.get('eff')}")

def test_battle_consume_spark():
    print("【8. battle _skill_finalize_damage 消费星火（basic 技，读表 stack_key）】")
    # 直接调用 _skill_finalize_damage 前的内部路径较深——用 _player_attack 全链验证
    # （novice_spark_followup 技能后置标 → 普攻命中消费清除；test_v140_novice 同款断言）
    p = mk_player(["novice_spark_followup"], atk=100)
    b = BT.Battle("monster", mk_enemy(hp=1000000), player=p)
    we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "物理"}, [])
    check("星火标记挂上", b._p_stacks().get("novice_spark") is True, str(b._p_stacks()))
    logs = b._player_attack(b._player_stats(p), p)
    check("普攻消费并清除星火标记", not b._p_stacks().get("novice_spark"), str(b._p_stacks()))
    check("星火增伤日志", any("星火" in l for l in logs), str(logs[-3:]))

def test_battle_decay_we_oath():
    print("【9. battle _decay_buff_table 保留一次性标记（we_oath/stealth）】")
    b, p = battle_for("oath_blade")
    b._p_buffs_bag()["we_oath"] = 1  # 一次性标记（buff 表内，攻击消费语义）
    b._p_buffs_bag()["stealth"] = 1
    b._p_buffs_bag()["gale_step"] = 100.0  # 计时 buff 对照组（未到期保留，不参与递减断言）
    b._now = 5.0
    b._decay_buff_table(b._p_buffs_bag(), True)
    check("we_oath 不按时刻衰减", b._p_buffs_bag().get("we_oath") == 1, str(b._p_buffs_bag()))
    check("stealth 不按时刻衰减", b._p_buffs_bag().get("stealth") == 1, str(b._p_buffs_bag()))
    # 计时 buff 到期对照组：gale_step int 刻值 1 → _now=5 到期删除（decay 语义仍在）
    b2, p2 = battle_for("oath_blade")
    b2._p_buffs_bag()["gale_step"] = 1
    b2._now = 5.0
    b2._decay_buff_table(b2._p_buffs_bag(), True)
    check("gale_step 计时对照组到期清除", "gale_step" not in b2._p_buffs_bag(), str(b2._p_buffs_bag()))

if __name__ == "__main__":
    test_routing()
    test_skill_hit_marks()
    test_novice_spark()
    test_dusk_blade_kill()
    test_retort_taken()
    test_guardian_will_hit()
    test_passive_consume_old_semantics()
    test_battle_consume_spark()
    test_battle_decay_we_oath()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
