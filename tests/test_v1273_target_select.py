# -*- coding: utf-8 -*-
"""v127.3 战斗选敌体系测试：站位编号 + 『技能 <槽位> <编号>』指定目标。

覆盖：
1. formation_view 编号显示（敌方 a1/a2、A1层/A2层；我方 b1、B1层）
2. 多怪战斗『技能1 2』纯数字 → 打敌方第 2 号（修复鱼鱼抓包 bug）
3. 『技能1 a2』→ 打敌方第 2 号
4. 越界编号 a9 → 明确提示 + 自动选择（不再静默）
5. 名字前缀目标兼容保留
6. 治疗 b1 → 友方第 1 个目标（allies）
7. 单怪战斗指定编号 → 恒打唯一目标
"""
import os
import sys

os.environ["GWEN_GAME_DB"] = os.path.abspath("test_v1273.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import formation as FM  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def make_battle(mon_defs, player=None):
    """造多怪战斗：mon_defs=[(mid, 中文名, role, lv, skills, drops), ...]"""
    mons = []
    for md in mon_defs:
        m = C.build_monster(md, {"id": "oak_plain", "name": "橡木平原", "area": "新手区"})
        mons.append(m)
    b = BT.Battle("monster", None, {}, player=player or {},
                  enemies=mons)
    return b


def test_formation_view_numbers():
    print("【1. 站位图编号显示】")
    m1 = {"uid": "e1", "name": "野狼", "icon": "🐺", "hp": 100, "max_hp": 100, "rank": 1, "reach": 1}
    m2 = {"uid": "e2", "name": "黑熊", "icon": "🐻", "hp": 150, "max_hp": 150, "rank": 1, "reach": 1}
    m3 = {"uid": "e3", "name": "巨蟒", "icon": "🐍", "hp": 200, "max_hp": 200, "rank": 2, "reach": 2}
    rows = FM.formation_view([m1, m2, m3], side="enemy")
    txt = "\n".join(rows)
    print("   ", txt.replace("\n", " | "))
    check("敌方层标记 A1层/A2层", "A1层" in txt and "A2层" in txt, txt)
    check("敌方目标编号 a1/a2/a3", "a1" in txt and "a2" in txt and "a3" in txt, txt)
    ally = [{"uid": "p", "name": "你(战士)", "icon": "🛡️", "hp": 150, "max_hp": 150, "rank": 2, "reach": 1}]
    arows = FM.formation_view(ally, side="ally")
    atxt = "\n".join(arows)
    check("我方层标记 B2层", "B2层" in atxt, atxt)
    check("我方目标编号 b1", "b1" in atxt, atxt)
    # numbered_units 顺序：rank 升序 + 原序
    numed = FM.numbered_units([m1, m2, m3])
    check("编号顺序 1=e1 2=e2 3=e3", [u["uid"] for _, u in numed] == ["e1", "e2", "e3"], str([u["uid"] for _, u in numed]))


def test_numeric_target_second():
    import random as _r
    _r.seed(11)
    print("【2. 『技能1 2』纯数字 → 打敌方第 2 号（bug 修复）】")
    mon_defs = [
        ("m_slime", "史莱姆A", "dps", 1, ["撞击"], []),
        ("m_slime", "史莱姆B", "dps", 1, ["撞击"], []),
        ("m_slime", "史莱姆C", "dps", 1, ["撞击"], []),
    ]
    player = {"class_name": "cls_zhan_shi", "level": 5, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}, "learned_skills": ["猛击"], "class_tier": 0,
              "evolve_path": 0, "race": "human", "reach": 1, "name": "测试"}
    b = make_battle(mon_defs, player)
    # 战士技能：猛击
    skill_name = "猛击"
    logs, ended = b.player_turn("skill", skill_name, player, target="2")
    out = "\n".join(logs)
    # 目标 = 第 2 个敌方（史莱姆B）
    check("打到史莱姆B", "史莱姆B" in out, out[:300])
    check("史莱姆B 掉血", b.enemies[1]["hp"] < b.enemies[1]["max_hp"], f"hp={b.enemies[1]['hp']}")
    check("史莱姆A 未掉血", b.enemies[0]["hp"] == b.enemies[0]["max_hp"], f"hp={b.enemies[0]['hp']}")


def test_a_prefixed_target():
    import random as _r
    _r.seed(13)
    print("【3. 『技能1 a2』→ 打敌方第 2 号】")
    mon_defs = [
        ("m_slime", "史莱姆A", "dps", 1, ["撞击"], []),
        ("m_slime", "史莱姆B", "dps", 1, ["撞击"], []),
    ]
    player = {"class_name": "cls_zhan_shi", "level": 5, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}, "learned_skills": ["猛击"], "class_tier": 0,
              "evolve_path": 0, "race": "human", "reach": 1, "name": "测试"}
    b = make_battle(mon_defs, player)
    logs, ended = b.player_turn("skill", "猛击", player, target="a2")
    out = "\n".join(logs)
    check("打到史莱姆B", "史莱姆B" in out, out[:300])
    check("史莱姆B 掉血", b.enemies[1]["hp"] < b.enemies[1]["max_hp"], f"hp={b.enemies[1]['hp']}")


def test_out_of_range_target():
    import random as _r
    _r.seed(17)
    print("【4. 越界编号 a9 → 明确提示 + 自动选择】")
    mon_defs = [
        ("m_slime", "史莱姆A", "dps", 1, ["撞击"], []),
        ("m_slime", "史莱姆B", "dps", 1, ["撞击"], []),
    ]
    player = {"class_name": "cls_zhan_shi", "level": 5, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}, "learned_skills": ["猛击"], "class_tier": 0,
              "evolve_path": 0, "race": "human", "reach": 1, "name": "测试"}
    b = make_battle(mon_defs, player)
    logs, ended = b.player_turn("skill", "猛击", player, target="a9")
    out = "\n".join(logs)
    check("提示未找到目标", "没有找到目标" in out, out[:300])
    check("自动选择仍出手", "猛击" in out or "史莱姆" in out, out[:300])


def test_name_prefix_target():
    print("【5. 名字前缀目标兼容保留】")
    mon_defs = [
        ("m_slime", "史莱姆A", "dps", 1, ["撞击"], []),
        ("m_slime", "史莱姆B", "dps", 1, ["撞击"], []),
    ]
    player = {"class_name": "cls_zhan_shi", "level": 5, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}, "learned_skills": ["猛击"], "class_tier": 0,
              "evolve_path": 0, "race": "human", "reach": 1, "name": "测试"}
    b = make_battle(mon_defs, player)
    import random as _r
    _r.seed(55)
    logs, ended = b.player_turn("skill", "猛击", player, target="史莱姆B")
    out = "\n".join(logs)
    # 名字命中 B（可能暴击秒杀后日志不含名，以 B 掉血 + A 未动为准）
    check("按名字打到史莱姆B", b.enemies[1]["hp"] < b.enemies[1]["max_hp"], f"B hp={b.enemies[1]['hp']} out={out[:60]}")
    check("史莱姆A 未掉血", b.enemies[0]["hp"] == b.enemies[0]["max_hp"], f"A hp={b.enemies[0]['hp']}")


def test_heal_b_target():
    print("【6. 治疗 b1 → 友方第 1 个目标】")
    player = {"class_name": "cls_mu_shi", "level": 5, "mp": 200, "max_mp": 200,
              "equipment": {}, "attributes": {}, "learned_skills": ["治愈术"], "class_tier": 0,
              "evolve_path": 0, "race": "human", "reach": 1, "name": "测试", "hp": 50, "max_hp": 200}
    mon = C.build_monster(("m_slime", "史莱姆", "dps", 1, ["撞击"], []),
                          {"id": "oak_plain", "name": "橡木平原", "area": "新手区"})
    ally2 = {"uid": "ally2", "name": "队友乙", "icon": "🧙", "hp": 30, "max_hp": 100, "rank": 1, "reach": 2}
    b = BT.Battle("monster", None, {}, player=player, enemies=[mon], allies=[ally2])
    # 治疗技能：治疗术（牧师基础）—— 需要技能存在
    import random
    random.seed(7)
    logs, ended = b.player_turn("skill", "治愈术", player, target="b1")
    out = "\n".join(logs)
    check("b1 指定队友乙被治疗", "队友乙" in out and "治愈" in out, out[:300])
    check("队友乙血量上升", ally2["hp"] > 30, f"hp={ally2['hp']}")


def test_single_monster_target():
    import random as _r
    _r.seed(19)
    print("【7. 单怪战斗指定编号 → 恒打唯一目标】")
    mon = C.build_monster(("m_slime", "史莱姆", "dps", 1, ["撞击"], []),
                          {"id": "oak_plain", "name": "橡木平原", "area": "新手区"})
    player = {"class_name": "cls_zhan_shi", "level": 5, "mp": 100, "max_mp": 100,
              "equipment": {}, "attributes": {}, "learned_skills": ["猛击"], "class_tier": 0,
              "evolve_path": 0, "race": "human", "reach": 1, "name": "测试"}
    b = BT.Battle("monster", None, {}, player=player, enemies=[mon])
    logs, ended = b.player_turn("skill", "猛击", player, target="a9")
    out = "\n".join(logs)
    check("单怪仍打唯一目标", "史莱姆" in out and b.enemies[0]["hp"] < b.enemies[0]["max_hp"], out[:300])


def main():
    clean_db()
    test_formation_view_numbers()
    test_numeric_target_second()
    test_a_prefixed_target()
    test_out_of_range_target()
    test_name_prefix_target()
    test_heal_b_target()
    test_single_monster_target()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)