# -*- coding: utf-8 -*-
"""v116.1 Boss 条件触发反制 + 三阶段剧本化

验证（怪物行动 AI §二 条件行动子集 / BOSS 战编排 §一）：
  1. player_low 低血追击：玩家 HP<30% 触发文案 + 本回合攻击加成（+25%）
  2. pv_broken 反扑：玩家本回合用过技能 → 反击演出 + 追加一次攻击
  3. phase_open 开场技：首回合必放（once），演出 + 增益 buff
  4. phase 剧本化：进入新阶段换招表追加技能 + 演出回合(_phase_skip_act) + 演出文案
  5. phase 阈值预告：接近下一阶段阈值(+3%)提前输出预警

独立运行：python tests/test_v116_boss_trigger_phase.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, clean_db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_boss(mech, hp=1000, max_hp=1000, atk=50, name="测试Boss", scripts=None):
    return {
        "id": "b_test", "name": name, "lv": 40, "role": "boss",
        "hp": hp, "max_hp": max_hp, "atk": atk, "def": 10, "matk": atk, "mdef": 10,
        "spd": 5, "exp": 100, "gold": 50, "skills": ["ms_an_ying_dan"],
        "drops": [], "map": "测试", "map_area": "test",
        "is_boss": True, "is_elite": False, "mech": mech, "mod": "测试",
        "scripts": scripts or {},
    }


def mk_player(hp=5000, max_hp=5000):
    return {
        "class_name": "cls_zhan_shi", "level": 40, "equipment": {},
        "class_tier": 0, "attributes": {"str": 0, "agi": 0, "int": 0, "vit": 0},
        "evolve_path": 0, "hp": hp, "max_hp": max_hp, "mp": 200, "max_mp": 200,
        "learned_skills": [], "name": "测试",
    }


def test_low_hp_chase():
    print("【1. player_low 低血追击】")
    # hp=1 相对 max_hp 极低，即便 __init__ 重算 max_hp 也保证 ratio 极低触发
    b = BT.Battle("monster", mk_boss("player_low"), {}, player=mk_player(hp=1, max_hp=5000))
    b.round = 3
    logs = []
    b._boss_mech(logs)
    check("低血触发文案【盯上了重伤的你】", any("盯上了重伤的你" in x for x in logs), str(logs))
    check("本回合追击标记 _low_hp_active", b.enemy.get("_low_hp_active") is True, "")
    est = b._enemy_stats()
    check("低血攻击加成 +25%", est["atk"] == int(50 * 1.25), f"{est['atk']}")
    # 玩家满血不触发
    b2 = BT.Battle("monster", mk_boss("player_low"), {}, player=mk_player(hp=5000, max_hp=5000))
    b2.round = 3
    logs2 = []
    b2._boss_mech(logs2)
    check("满血不触发低血追击", not b2.enemy.get("_low_hp_active") and logs2 == [], str(logs2))


def test_pv_broken_counter():
    print("【2. pv_broken 大招后反扑】")
    b = BT.Battle("monster", mk_boss("pv_broken"), {}, player=mk_player())
    b.round = 3
    b._player_recent_skill = True  # 玩家本回合用过技能
    logs = []
    b._boss_mech(logs)
    check("反扑演出文案【愤怒反扑】", any("愤怒反扑" in x for x in logs), str(logs))
    check("反扑标记 _pv_broken_active", b.enemy.get("_pv_broken_active") is True, "")
    est = b._enemy_stats()
    check("反扑攻击加成 +30%", est["atk"] == int(50 * 1.30), f"{est['atk']}")
    # 玩家未用技能不触发
    b2 = BT.Battle("monster", mk_boss("pv_broken"), {}, player=mk_player())
    b2.round = 3
    b2._player_recent_skill = False
    logs2 = []
    b2._boss_mech(logs2)
    check("未用技能不触发反扑", not b2.enemy.get("_pv_broken_active") and logs2 == [], str(logs2))
    # 全流程：_enemy_turn 反扑额外追加一次攻击
    b3 = BT.Battle("monster", mk_boss("pv_broken"), {}, player=mk_player())
    b3.round = 3
    b3._player_recent_skill = True
    logs3, dmg3 = b3._enemy_turn(mk_player())
    check("反扑回合产生伤害", dmg3 > 0, f"dmg={dmg3}")


def test_opening_roar():
    print("【3. phase_open 开场技】")
    scripts = {"opening": {"name": "深渊咆哮", "effect": "atk_up", "power": 2}}
    b = BT.Battle("monster", mk_boss("phase_open", scripts=scripts), {}, player=mk_player())
    b.round = 1
    logs = []
    b._boss_mech(logs)
    check("开场演出【深渊咆哮】", any("深渊咆哮" in x for x in logs), str(logs))
    check("开场增益 mon_atk_up", b.e_buffs.get("mon_atk_up", 0) >= 2, str(b.e_buffs))
    check("开场 once（_open_played）", b.enemy.get("_open_played") is True, "")
    # 非首回合不再触发
    b2 = BT.Battle("monster", mk_boss("phase_open", scripts=scripts), {}, player=mk_player())
    b2.round = 2
    logs2 = []
    b2._boss_mech(logs2)
    check("非首回合不再放开场技", not b2.enemy.get("_open_played") and not any("深渊咆哮" in x for x in logs2), str(logs2))


def test_phase_scripted():
    print("【4. phase 三阶段剧本化：换招 + 演出回合】")
    scripts = {
        "phases": [
            {"min": 60, "add_skills": ["ms_zhao_huan_e_mo"],
             "script": {"name": "深渊之躯浮现", "icon": "🌑"}},
            {"min": 30, "add_skills": ["ms_shen_yuan_zhi_nu"],
             "script": {"name": "魔核迸裂", "icon": "💀"}},
        ],
    }
    e = mk_boss("phase", hp=400, max_hp=1000, atk=50, scripts=scripts)
    b = BT.Battle("monster", e, {}, player=mk_player())
    b.round = 3
    logs = []
    b._boss_mech(logs)
    check("血量40%进入第2阶段", b.enemy.get("phase_count") == 1, str(b.enemy.get("phase_count")))
    check("阶段换招追加技能", "ms_zhao_huan_e_mo" in b.enemy["skills"], str(b.enemy["skills"]))
    check("演出文案【深渊之躯浮现】", any("深渊之躯浮现" in x for x in logs), str(logs))
    check("演出回合不行动(_phase_skip_act)", getattr(b, "_phase_skip_act", False) is True, "")
    # 演出回合在 _enemy_turn 里直接跳过行动
    b2 = BT.Battle("monster", mk_boss("phase", hp=400, max_hp=1000, scripts=scripts), {}, player=mk_player())
    b2.round = 3
    logs2, dmg2 = b2._enemy_turn(mk_player())
    check("演出回合 _enemy_turn 不行动(dmg=0)", dmg2 == 0 and any("蜕变" in x for x in logs2),
          f"dmg={dmg2} logs={str(logs2)}")
    # 阶段攻击 +20% 仍有
    est = b._enemy_stats()
    check("阶段攻击仍 +20%", est["atk"] == int(50 * 1.20), f"{est['atk']}")


def test_phase_threshold_warn():
    print("【5. phase 阈值预告】")
    e = mk_boss("phase", hp=260, max_hp=1000, scripts={
        "phases": [{"min": 60, "add_skills": []}, {"min": 30, "add_skills": []}],
    })
    e["phase_count"] = 1  # 已在阶段2，下一阈值 25%，当前 26%（25%~28% 内）
    b = BT.Battle("monster", e, {}, player=mk_player())
    b.round = 5
    logs = []
    b._boss_mech(logs)
    check("阈值预告【气息开始紊乱】", any("气息开始紊乱" in x for x in logs), str(logs))
    # 远离阈值不警告
    e2 = mk_boss("phase", hp=500, max_hp=1000, scripts={"phases": []})
    e2["phase_count"] = 1
    b2 = BT.Battle("monster", e2, {}, player=mk_player())
    b2.round = 5
    logs2 = []
    b2._boss_mech(logs2)
    check("远离阈值不预告", not any("气息开始紊乱" in x for x in logs2), str(logs2))


def test_data_config_resolution():
    print("【6. 数据配置按 id 解析示范】")
    # b_moro（wild）配置携带时，_boss_cfg 应能从 MONSTER_MODS 读到 opening/phases
    src = C.MONSTER_MODS.get("b_moro", {})
    check("b_moro mech 含 phase_open", "phase_open" in (src.get("mech") or ""), str(src.get("mech")))
    check("b_moro 配置 opening", bool(src.get("opening")), str(src.get("opening")))
    check("b_moro 配置 phases", len(src.get("phases") or []) == 2, str(src.get("phases")))
    inst = C.INSTANCES.get("inst_abyss_gate", {})
    check("inst_abyss_gate 配置 phases", len(inst.get("phases") or []) == 2, "")
    # _boss_cfg 按 enemy id 解析
    e = mk_boss("phase")
    e["id"] = "b_moro"
    b = BT.Battle("monster", e, {}, player=mk_player())
    cfg = b._boss_cfg(e)
    check("_boss_cfg 读取 b_moro opening", cfg.get("opening", {}).get("name") == "深渊咆哮", str(cfg.get("opening")))
    check("_boss_cfg 读取 b_moro phases", len(cfg.get("phases") or []) == 2, "")


async def main():
    clean_db()
    test_low_hp_chase()
    test_pv_broken_counter()
    test_opening_roar()
    test_phase_scripted()
    test_phase_threshold_warn()
    test_data_config_resolution()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
