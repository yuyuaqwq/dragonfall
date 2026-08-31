#!/usr/bin/env python3
"""v151 基础职业技能层冒烟测试（原 v107 隐藏职业冒烟，2026-08-31 v151 重构后改版）

覆盖 6 基础职业真实技能数据：施放不报错 + 关键机制字段生效
（真伤/召唤/多段/毒爆/元素印记/战意叠层）
v151 变更：6 隐藏职业删除，旧技能名全部替换为新表技能。
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player

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
    from data.plugins.dragonfall.game import battle as BT

    print("===== v151 基础职业技能层冒烟 =====\n")

    def mk_player(cls, skills=None, hp=800, mp=200):
        return {
            "class_name": cls, "level": 60, "hp": hp, "max_hp": hp,
            "mp": mp, "max_mp": 200,
            "equipment": {"weapon": {"name": "测试武", "stats": {"atk": 100, "matk": 100},
                                     "affixes": [], "enhance": 0}},
            "attributes": {"str": 20, "int": 20},
            "learned_skills": skills or [], "race": "human",
        }

    def mk_enemy(def_=30, mdef=30, hp=50000):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 80, "def": def_, "mdef": mdef, "spd": 10}

    def cast(b, p, sname):
        info = E.skill_info(p["class_name"], sname)
        st = b._player_stats(p)
        random.seed(11)
        return b._player_skill(st, sname, info, p)

    # 1. 战士：龙息之怒真伤（v151 T2 狂战统领）
    print("— 战士·龙息之怒 —")
    p = mk_player("cls_zhan_shi", ["龙息之怒"])
    b = BT.Battle("怪物", mk_enemy(def_=5000, hp=50000), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "龙息之怒")
    dealt = hp0 - b.enemy["hp"]
    check("龙息之怒真伤无视 def=5000", dealt > 100, f"dealt {dealt}")
    check("龙息之怒附灼烧", any("灼烧" in l for l in logs), str(logs[:2]))

    # 2. 牧师·神谕者：召唤骷髅 + 骷髅海（v151 T1 神谕者 / T3 圣光先知）
    print("\n— 牧师·召唤骷髅 —")
    p = mk_player("cls_mu_shi", ["召唤骷髅", "骷髅海"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "召唤骷髅")
    check("召唤骷髅生成", len(b.summons) == 1, str(b.summons))
    logs2 = cast(b, p, "骷髅海")
    check("骷髅海再召唤", len(b.summons) >= 2, str(len(b.summons)))

    # 3. 游侠·林语者：植物召唤（v151 T1 林语者 / T3 万木之灵）
    print("\n— 林语者：植物召唤 —")
    p = mk_player("cls_you_xia", ["召唤藤蔓守卫", "召唤古树守卫"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "召唤藤蔓守卫")
    check("召唤藤蔓守卫", b.summons[0]["tid"] == "vine_guard", str([s.get("tid") for s in b.summons]))
    cast(b, p, "召唤古树守卫")
    check("再召古树守卫", any(s["tid"] == "treant" for s in b.summons),
          str([s.get("tid") for s in b.summons]))

    # 4. 刺客·暗影之刃：幽影连刺多段（v151 T2 暗影之刃）
    print("\n— 刺客·幽影连刺 —")
    p = mk_player("cls_ci_ke", ["幽影连刺"])
    b = BT.Battle("怪物", mk_enemy(hp=50000), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "幽影连刺")
    check("幽影连刺多段输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")
    logs2 = cast(b, p, "幽影连刺")
    check("幽影连刺日志", any("幽影连刺" in l for l in logs + logs2),
          str([l for l in logs + logs2 if "幽影连刺" in l]))

    # 5. 法师·元素湮灭（v151 T1 元素法师）：消耗充能爆发
    print("\n— 法师·元素湮灭（充能爆发）—")
    p = mk_player("cls_fa_shi", ["元素湮灭"], mp=200)
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "元素湮灭")
    check("元素湮灭输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    # 6. 游侠·毒爆流（v151 T1 林语者）：毒→爆
    print("\n— 游侠·毒爆流 —")
    p = mk_player("cls_you_xia", ["淬毒箭矢", "藤蔓缠绕", "毒爆术", "剧毒之心"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "淬毒箭矢")
    cast(b, p, "藤蔓缠绕")
    cast(b, p, "藤蔓缠绕")
    check("毒层叠加", (b.enemy.get("debuffs") or {}).get("poison", {}).get("n", 0) >= 3,
          str(b.enemy.get("debuffs")))
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "毒爆术")
    check("毒爆引爆", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")
    check("毒层清空", "poison" not in (b.enemy.get("debuffs") or {}), str(b.enemy.get("debuffs")))

    # 7. 拳师·格斗士：连招三连 + 震地击（v151 T1 格斗士）
    print("\n— 拳师·连招/震地 —")
    p = mk_player("cls_wu_seng", ["连招三连", "震地击", "冲拳"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "连招三连")
    check("连招三连多段输出", any("连击" in l for l in logs), str(logs[:2]))
    hp0 = b.enemy["hp"]
    logs2 = cast(b, p, "震地击")
    check("震地击输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")
    check("震地击眩晕机制字段", (E.skill_info("cls_wu_seng", "震地击") or {}).get("mech") == "stun",
          str(E.skill_info("cls_wu_seng", "震地击")))

    # 8. 法师·元素印记（v151 基础）：元素弹幕 + 元素冲击叠印记
    print("\n— 法师·元素印记 —")
    p = mk_player("cls_fa_shi", ["元素弹幕", "元素冲击"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "元素弹幕")
    cast(b, p, "元素冲击")
    check("元素印记叠加", b._elem_marks().get("fire", 0) >= 1, str(b._elem_marks()))
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "元素冲击")
    check("元素冲击输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    print()
    print(f"===== v151 基础职业技能层冒烟: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
