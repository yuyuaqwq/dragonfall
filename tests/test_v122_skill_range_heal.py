# -*- coding: utf-8 -*-
"""v122 技能范围显示 + 治疗自选队友 回归测试。

鱼鱼拍板（2026-08-16）：奶妈技能必须能自选己方目标，同时技能要有范围配置，
范围显示进技能列表。

1. 范围标签映射：_skill_range_label single/front/all/rankN/aoe 推导/默认单体
2. 技能列表显示范围标签（<单体>/<全体> 等）
3. 副本治疗指定队友：队友 hp+、施法者 hp 不变、日志含队友名
4. 副本治疗无指定 → 奶自己（旧行为不变）
5. 指定不存在的队友 → 拦截：不扣 MP、队友 hp 不变、日志提示
6. 单人战斗（无 allies）治疗带目标 token → 忽略目标奶自己
7. 攻击技能目标解析不受影响（非治疗技能 target 走敌人路径）

环境铁律：私有库 test_v122_skill_range_heal.db（绝不碰生产库）。
"""
import os
import sys

os.environ["GWEN_GAME_DB"] = os.path.abspath("test_v122_skill_range_heal.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.commands.combat import CombatCmds  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_priest(hp=400, mp=100, name="牧师"):
    return {
        "class_name": "cls_mu_shi", "level": 30, "hp": hp, "max_hp": 1000,
        "mp": mp, "max_mp": 100, "name": name, "reach": 3,
        "equipment": {"weapon": {"name": "测试法杖", "stats": {"matk": 200, "atk": 50},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"int": 20, "str": 5},
        "learned_skills": ["治愈术"],
    }


def mk_enemy(hp=500):
    return {"uid": "e1", "name": "测试史莱姆", "hp": hp, "max_hp": 500,
            "rank": 1, "reach": 1, "atk": 30, "def": 10, "matk": 0,
            "mdef": 5, "spd": 5, "lv": 8}


# ---------------- 1. 范围标签映射 ----------------
def test_range_label():
    print("【1. 范围标签映射】")
    cc = CombatCmds()
    cases = [
        ({}, ""),                              # 单体不显示标签（v122c 鱼鱼拍板）
        ({"range": "single"}, ""),
        ({"range": "front"}, "群体"),
        ({"range": "all"}, "群体"),
        ({"range": "rank2"}, "群体"),
        ({"aoe": "front"}, "群体"),
        ({"aoe": "all"}, "群体"),
        ({"aoe": "rank3"}, "群体"),
        ({"aoe": "all", "range": "front"}, "群体"),   # range/aoe 任一非 single → 群体
        ({"range": "weird"}, "群体"),                  # 未知值按群体（非 single）
        ({"team": "heal_all"}, "群体"),                # 团队广播 → 群体
        ({"team": "taunt"}, ""),                       # 嘲讽是单体目标，不显示
    ]
    for info, expect in cases:
        got = cc._skill_range_label(info)
        check(f"range={info} → {expect}", got == expect, f"实际 {got}")


# ---------------- 2. 技能列表范围标签 ----------------
def test_skill_list_range():
    print("【2. 技能列表显示范围标签】")
    from data.plugins.dragonfall.main import Main
    m = Main(None)
    p = mk_priest()
    # 牧师技能表含治愈术（单体）、圣光术（单体）、大治疗术（全体 heal_all，若已学/可见）
    out = m._skill_list_page(p, 1)
    check("技能列表不含 <单体> 标签", "<单体>" not in out, out[:200])
    check("技能列表含 <治疗>", "<治疗>" in out, out[:200])
    check("技能列表消耗行含 射程：", "射程：" in out, out[:300])
    # 大治疗术（team heal_all）→ <群体>
    info = E.skill_info("cls_mu_shi", "大治疗术")
    if info:
        cc = CombatCmds()
        check("大治疗术范围标签 <群体>", cc._skill_range_label(info) == "群体",
              cc._skill_range_label(info))
    else:
        print("  ⚠️ 大治疗术不存在，跳过群体标签断言")


# ---------------- 3. 治疗指定队友 ----------------
def test_heal_target_ally():
    print("【3. 副本治疗指定队友】")
    clean_db()
    ally1 = {"uid": "q1", "name": "阿瓦隆", "hp": 300, "max_hp": 1000}
    ally2 = {"uid": "q2", "name": "艾琳", "hp": 800, "max_hp": 1000}
    priest = mk_priest(hp=400)
    enemy = mk_enemy()
    b = BT.Battle("monster", enemy, player=priest, enemies=[enemy],
                  allies=[ally1, ally2])
    logs, ended = b.player_turn("skill", "治愈术", priest, enemy_act=False, target="阿瓦隆")
    text = "\n".join(logs)
    check("指定队友血量增加", ally1["hp"] > 300, f"实际 {ally1['hp']}")
    check("施法者血量不变", priest["hp"] == 400, f"实际 {priest['hp']}")
    check("日志含队友名", "治愈了 阿瓦隆" in text, text[:200])
    check("未误报治愈自己", "治愈了你" not in text, text[:200])
    check("施法者 MP 已扣", priest["mp"] < 100, f"实际 {priest['mp']}")


# ---------------- 4. 无指定 → 奶自己 ----------------
def test_heal_self_default():
    print("【4. 副本治疗无指定 → 奶自己】")
    clean_db()
    ally1 = {"uid": "q1", "name": "阿瓦隆", "hp": 300, "max_hp": 1000}
    priest = mk_priest(hp=400)
    enemy = mk_enemy()
    b = BT.Battle("monster", enemy, player=priest, enemies=[enemy],
                  allies=[ally1])
    logs, ended = b.player_turn("skill", "治愈术", priest, enemy_act=False, target=None)
    text = "\n".join(logs)
    check("无指定奶自己", priest["hp"] > 400, f"实际 {priest['hp']}")
    check("队友血量不变", ally1["hp"] == 300, f"实际 {ally1['hp']}")
    check("日志含治愈自己", "治愈了你" in text, text[:200])


# ---------------- 5. 指定不存在的队友 → 拦截 ----------------
def test_heal_target_missing():
    print("【5. 指定不存在队友 → 拦截不扣资源】")
    clean_db()
    ally1 = {"uid": "q1", "name": "阿瓦隆", "hp": 300, "max_hp": 1000}
    priest = mk_priest(hp=400)
    enemy = mk_enemy()
    b = BT.Battle("monster", enemy, player=priest, enemies=[enemy],
                  allies=[ally1])
    logs, ended = b.player_turn("skill", "治愈术", priest, enemy_act=False, target="不存在")
    text = "\n".join(logs)
    check("日志提示队伍里没有", "队伍里没有" in text, text[:200])
    check("MP 未扣", priest["mp"] == 100, f"实际 {priest['mp']}")
    check("施法者血量不变", priest["hp"] == 400, f"实际 {priest['hp']}")
    check("队友血量不变", ally1["hp"] == 300, f"实际 {ally1['hp']}")
    check("未进入结束状态", ended is False, str(ended))


# ---------------- 6. 单人战斗带目标 → 忽略奶自己 ----------------
def test_heal_solo_target_ignored():
    print("【6. 单人战斗带目标 token → 忽略奶自己】")
    clean_db()
    priest = mk_priest(hp=400)
    enemy = mk_enemy()
    b = BT.Battle("monster", enemy, player=priest, enemies=[enemy])  # 无 allies
    logs, ended = b.player_turn("skill", "治愈术", priest, enemy_act=False, target="随便")
    text = "\n".join(logs)
    check("单人带目标仍奶自己", priest["hp"] > 400, f"实际 {priest['hp']}")
    check("日志含治愈自己", "治愈了你" in text, text[:200])


# ---------------- 7. 非治疗技能 target 走敌人路径 ----------------
def test_damage_skill_target_enemy():
    print("【7. 非治疗技能 target 走敌人路径】")
    clean_db()
    ally1 = {"uid": "q1", "name": "阿瓦隆", "hp": 300, "max_hp": 1000}
    # 战士：裂地斩（单体伤害）指定敌人 e2（后排 rank2，战士 reach 1 打不到 → 射程拒绝）
    from data.plugins.dragonfall.game.commands.combat import CombatCmds
    warrior = {
        "class_name": "cls_zhan_shi", "level": 30, "hp": 800, "max_hp": 800,
        "mp": 100, "max_mp": 100, "name": "战士", "reach": 1,
        "equipment": {"weapon": {"name": "测试剑", "stats": {"atk": 200, "matk": 20},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 20, "int": 5},
        "learned_skills": ["裂地斩"],
    }
    e1 = {"uid": "e1", "name": "前排怪", "hp": 500, "max_hp": 500, "rank": 1, "reach": 1,
          "atk": 10, "def": 10, "matk": 0, "mdef": 5, "spd": 5, "lv": 8}
    e2 = {"uid": "e2", "name": "后排怪", "hp": 500, "max_hp": 500, "rank": 2, "reach": 1,
          "atk": 10, "def": 10, "matk": 0, "mdef": 5, "spd": 5, "lv": 8}
    b = BT.Battle("monster", e1, player=warrior, enemies=[e1, e2], allies=[ally1])
    b.resources = {"rage": 10}  # 裂地斩消耗 3 怒气
    logs, ended = b.player_turn("skill", "裂地斩", warrior, enemy_act=False, target="后排怪")
    text = "\n".join(logs)
    # 战士 reach=1 打不到 rank2 → 射程拒绝（v2 既有行为，v122 不破坏）
    check("非治疗技能目标解析走敌人射程", "攻击范围之外" in text or e2["hp"] < 500, text[:200])


async def main():
    test_range_label()
    test_skill_list_range()
    test_heal_target_ally()
    test_heal_self_default()
    test_heal_target_missing()
    test_heal_solo_target_ignored()
    test_damage_skill_target_enemy()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    import asyncio
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
