# -*- coding: utf-8 -*-
"""v181.P2C-C8 proc_passive_mult + proc_stack 语义门禁（行为零变化单体断言）。

在 OLD-NEW 差分探针（test_p2cc8_passive_stack_probe.py）之外，对每个代表场景做
数值/副作用硬断言：
1. twilight_execute：敌 hp<40% mult=×1.25（低血 30/100 触发）
2. star_slayer_edge：敌 hp>70% mult=×1.15；hp 中段（40%-70%）不触发
3. arcane_firmament：battle_start 置 eff.we_arcane_firmament + 日志；魔法技 mult ×1.10，物理不乘
4. combo_end：攻线刺客 hit 置 we_combo_end；is_crit passive 消费 crit_dmg +0.4 并清标
5. rune_amp：skill_cast 叠 3 层 → passive mult = 1+0.02×3=1.06，消费后 stacks.rune_amp=0
6. sage_amp：2 次 skill_cast → eff.we_sage_charge；passive mult ×1.25 后清
7. eternal_codex：5 层 passive mult = 1+0.015×5=1.075（不清层）
8. time_staff：turn_start 叠层 + 半血回血；passive 每层 ×1.015
9. thunder_weave：5 次 hit 满层 → eff.we_thunder_charge；passive mult ×1.20 后清
10. wind_mark / novice_hunt_combo：叠层写槽（面板消费点在 battle，C6 收）
11. 未迁移 key（trinity_rhythm family=proc_next_atk_mark）不进白名单 → 仍走旧 handler
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

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, class_name="战士", evolve_path=0):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": class_name, "evolve_path": evolve_path, "qq_id": "t1"}

def mk_enemy(hp=100000, max_hp=None, **kw):
    mh = hp if max_hp is None else max_hp
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": mh,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    e.update(kw)
    return e

def battle_for(key, enemy_hp=100000, enemy_max_hp=None, **pw):
    p = mk_player([key], **pw)
    b = BT.Battle("monster", mk_enemy(hp=enemy_hp, max_hp=enemy_max_hp), player=p)
    return b, p

def test_twilight():
    print("【1. 暮光处决（低血 ×1.25）】")
    b, p = battle_for("twilight_execute", enemy_hp=30, enemy_max_hp=100)
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b, p, "passive", ctx, [])
    check("低血 30/100 mult=1.25", abs(ctx["mult"] - 1.25) < 1e-9, f"mult={ctx['mult']}")
    check("tags 暮光处决", ctx["tags"] == ["🌆暮光处决"], str(ctx["tags"]))
    b2, p2 = battle_for("twilight_execute", enemy_hp=50, enemy_max_hp=100)
    ctx2 = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b2, p2, "passive", ctx2, [])
    check("高血 50% 不触发", ctx2["mult"] == 1.0 and not ctx2["tags"], f"mult={ctx2['mult']}")

def test_star():
    print("【2. 弑星（高血 ×1.15）】")
    b, p = battle_for("star_slayer_edge", enemy_hp=90, enemy_max_hp=100)
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b, p, "passive", ctx, [])
    check("高血 90/100 mult=1.15", abs(ctx["mult"] - 1.15) < 1e-9, f"mult={ctx['mult']}")
    b2, p2 = battle_for("star_slayer_edge", enemy_hp=50, enemy_max_hp=100)
    ctx2 = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b2, p2, "passive", ctx2, [])
    check("中血 50% 不触发", ctx2["mult"] == 1.0 and not ctx2["tags"], f"mult={ctx2['mult']}")

def test_arcane():
    print("【3. 奥术苍穹（魔法技 ×1.10 + battle_start 置标）】")
    b, p = battle_for("arcane_firmament")
    we_proc(b, p, "battle_start", {}, [])
    check("battle_start 置 eff.we_arcane_firmament", bool((p.get("eff") or {}).get("we_arcane_firmament")),
          str(p.get("eff")))
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "魔法"}
    we_proc(b, p, "passive", ctx, [])
    check("魔法技 mult=1.10", abs(ctx["mult"] - 1.10) < 1e-9, f"mult={ctx['mult']}")
    check("tags 奥术苍穹", ctx["tags"] == ["✨奥术苍穹"], str(ctx["tags"]))
    ctx2 = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b, p, "passive", ctx2, [])
    check("物理技不触发", ctx2["mult"] == 1.0 and not ctx2["tags"], f"mult={ctx2['mult']}")

def test_combo_end():
    print("【4. 连击终点（hit 置标 → passive 暴伤 +0.4 消费）】")
    b, p = battle_for("combo_end", class_name="cls_ci_ke", evolve_path=1)
    # 攻线刺客连段活跃：直接 _combo_add 到 3（置标判定用 _combo_active 布尔，不查 ≥3）
    for _ in range(3):
        b._combo_add(p)
    we_proc(b, p, "hit", {"dmg": 100, "is_crit": False}, [])
    check("hit 置 eff.we_combo_end=0.4", abs(float((p.get("eff") or {}).get("we_combo_end", 0)) - 0.4) < 1e-9,
          str(p.get("eff")))
    ctx = {"mult": 1.0, "tags": [], "is_crit": True, "kind": "物理"}
    we_proc(b, p, "passive", ctx, [])
    check("is_crit 消费 crit_dmg +0.4", abs(ctx.get("crit_dmg", 0) - 0.4) < 1e-9, f"crit_dmg={ctx.get('crit_dmg')}")
    check("消费后清标", "we_combo_end" not in (p.get("eff") or {}), str(p.get("eff")))
    # 非暴击不消费（未清标）
    b2, p2 = battle_for("combo_end", class_name="cls_ci_ke", evolve_path=1)
    for _ in range(3):
        b2._combo_add(p2)
    we_proc(b2, p2, "hit", {"dmg": 100}, [])
    ctx2 = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b2, p2, "passive", ctx2, [])
    check("非暴不消费且不清标", "we_combo_end" in (p2.get("eff") or {}),
          f"eff={p2.get('eff')} ctx={ctx2}")

def test_rune():
    print("【5. 铭文增幅（3 层 ×1.06 消费清 0）】")
    b, p = battle_for("rune_amp")
    for _ in range(3):
        we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "魔法"}, [])
    check("叠 3 层", int((p.get("stacks") or {}).get("rune_amp", 0)) == 3, str(p.get("stacks")))
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "魔法"}
    we_proc(b, p, "passive", ctx, [])
    check("3 层 mult=1.06", abs(ctx["mult"] - 1.06) < 1e-9, f"mult={ctx['mult']}")
    check("消费后清 0", int((p.get("stacks") or {}).get("rune_amp", 0)) == 0, str(p.get("stacks")))

def test_sage():
    print("【6. 秘典增幅（2 次 → charge ×1.25）】")
    b, p = battle_for("sage_amp")
    we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "魔法"}, [])
    we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "魔法"}, [])
    check("2 次置 eff.we_sage_charge", abs(float((p.get("eff") or {}).get("we_sage_charge", 0)) - 0.25) < 1e-9,
          str(p.get("eff")))
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "魔法"}
    we_proc(b, p, "passive", ctx, [])
    # 旧 handler 语义 = ctx.mult × charge（charge_pct=0.25 原样乘，非 (1+0.25)）——保持零变化
    check("charge mult=0.25（旧语义逐字保持）", abs(ctx["mult"] - 0.25) < 1e-9, f"mult={ctx['mult']}")
    check("消费后清", "we_sage_charge" not in (p.get("eff") or {}), str(p.get("eff")))

def test_eternal():
    print("【7. 永恒契约（5 层 ×1.075 不清层）】")
    b, p = battle_for("eternal_codex")
    for _ in range(5):
        we_proc(b, p, "skill_cast", {"skill": "测试", "kind": "魔法"}, [])
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "魔法"}
    we_proc(b, p, "passive", ctx, [])
    check("5 层 mult=1.075", abs(ctx["mult"] - 1.075) < 1e-9, f"mult={ctx['mult']}")
    check("不清层（仍 5 层）", int((p.get("stacks") or {}).get("eternal_codex", 0)) == 5,
          str(p.get("stacks")))

def test_time_staff():
    print("【8. 岁月流转（叠层 + 回血；passive 每层 ×1.015）】")
    b, p = battle_for("time_staff")
    p["hp"] = int(p["max_hp"] * 0.5)
    hp0 = p["hp"]
    we_proc(b, p, "turn_start", {}, [])
    check("叠层 1 且回血", int((p.get("stacks") or {}).get("time_staff", 0)) == 1 and p["hp"] > hp0,
          f"stacks={p.get('stacks')} hp={p['hp']} hp0={hp0}")
    p.setdefault("stacks", {})["time_staff"] = 6
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"}
    we_proc(b, p, "passive", ctx, [])
    expect = 1 + 0.015 * 6
    check("6 层 mult=1.09", abs(ctx["mult"] - expect) < 1e-9, f"mult={ctx['mult']} expect={expect}")

def test_thunder():
    print("【9. 雷纹连打（满层 charge ×1.20）】")
    b, p = battle_for("thunder_weave")
    for _ in range(5):
        we_proc(b, p, "hit", {"dmg": 100}, [])
    check("满层置 eff.we_thunder_charge", abs(float((p.get("eff") or {}).get("we_thunder_charge", 0)) - 0.20) < 1e-9,
          f"eff={p.get('eff')} stacks={p.get('stacks')}")
    ctx = {"mult": 1.0, "tags": [], "is_crit": False, "kind": "魔法"}
    we_proc(b, p, "passive", ctx, [])
    # 旧 handler 语义 = ctx.mult × charge（charge_pct=0.20 原样乘，非 (1+0.20)）——保持零变化
    check("charge mult=0.20（旧语义逐字保持）", abs(ctx["mult"] - 0.20) < 1e-9, f"mult={ctx['mult']}")
    check("消费后清", "we_thunder_charge" not in (p.get("eff") or {}), str(p.get("eff")))

def test_wind_hunt():
    print("【10. 风痕 / 猎影叠层写槽】")
    b, p = battle_for("wind_mark")
    for _ in range(3):
        we_proc(b, p, "hit", {"dmg": 100}, [])
    check("风痕 3 层", int((p.get("stacks") or {}).get("wind_mark", 0)) == 3, str(p.get("stacks")))
    b2, p2 = battle_for("novice_hunt_combo")
    we_proc(b2, p2, "hit", {"dmg": 100, "is_crit": True}, [])
    we_proc(b2, p2, "hit", {"dmg": 100, "is_crit": True}, [])
    check("猎影 2 层", int((p2.get("stacks") or {}).get("novice_combo", 0)) == 2, str(p2.get("stacks")))

def test_unmigrated_old_path():
    print("【11. 未迁移 key 走旧 handler（安全阀）】")
    # trinity_rhythm family=proc_next_atk_mark（C7 收）不在 C8 白名单
    check("trinity_rhythm family=proc_next_atk_mark", _we_family("trinity_rhythm") == "proc_next_atk_mark"
          and "trinity_rhythm" not in _WE_EXEC_KEYS, f"fam={_we_family('trinity_rhythm')}")
    b, p = battle_for("trinity_rhythm")
    we_proc(b, p, "skill_hit", {"dmg": 100, "is_crit": False, "skill": "测试", "kind": "物理"}, [])
    check("trinity skill_hit 旧 handler 置 we_trinity", abs(float((p.get("eff") or {}).get("we_trinity", 0)) - 0.30) < 1e-9,
          str(p.get("eff")))

if __name__ == "__main__":
    test_twilight()
    test_star()
    test_arcane()
    test_combo_end()
    test_rune()
    test_sage()
    test_eternal()
    test_time_staff()
    test_thunder()
    test_wind_hunt()
    test_unmigrated_old_path()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
