#!/usr/bin/env python3
"""v107 隐藏职业技能层冒烟测试（2026-08-13 鱼鱼拍板）

覆盖 11 职业真实技能数据：施放不报错 + 关键机制字段生效
（真伤/召唤/进化/斩杀被动/血魔法/吸MP/毒爆/护盾/奥术爆发/连击/多段）
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

    print("===== v107 隐藏职业技能层冒烟 =====\n")

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

    # 1. 龙血战士：龙息真伤
    print("— 龙血战士 —")
    p = mk_player("cls_dragon_warrior", ["龙息", "龙息之怒"])
    b = BT.Battle("怪物", mk_enemy(def_=5000, hp=50000), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "龙息")
    dealt = hp0 - b.enemy["hp"]
    check("龙息真伤无视 def=5000", dealt > 100, f"dealt {dealt}")
    check("龙息附灼烧", any("灼烧" in l for l in logs), str(logs[:2]))

    # 2. 亡灵术士：召唤骷髅
    print("\n— 亡灵术士 —")
    p = mk_player("cls_necromancer", ["召唤骷髅", "骷髅海"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "召唤骷髅")
    check("召唤骷髅生成", len(b.summons) == 1, str(b.summons))
    logs2 = cast(b, p, "骷髅海")
    check("骷髅海再召唤", len(b.summons) == 2, str(len(b.summons)))
    check("骷髅海带攻击buff", b.p_buffs.get("atk_up", 0) > 0, str(b.p_buffs))

    # 3. 兽王：进化链
    print("\n— 兽王 —")
    p = mk_player("cls_beast_king", ["驯兽召唤", "狼群指令", "野性呼唤"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "驯兽召唤")
    check("驯兽召唤幼狼", b.summons[0]["tid"] == "wolf_cub")
    cast(b, p, "狼群指令")
    check("狼群指令→狼王", b.summons[0]["tid"] == "wolf_king")
    cast(b, p, "野性呼唤")
    check("野性呼唤→影狼真伤", b.summons[0]["tid"] == "shadow_wolf" and b.summons[0]["dmg_type"] == "true")

    # 4. 影武者：斩杀被动
    print("\n— 影武者 —")
    p = mk_player("cls_shadow_blade", ["影袭", "残血追猎", "收割"])
    b = BT.Battle("怪物", mk_enemy(hp=50000), {}, p)
    b.enemy["hp"] = 8000  # 16% 血
    logs = cast(b, p, "影袭")
    check("残血影袭斩杀加成", any("斩杀" in l for l in logs), str([l for l in logs if "斩杀" in l]))
    b2 = BT.Battle("怪物", mk_enemy(hp=50000), {}, p)
    logs2 = cast(b2, p, "收割")
    check("收割低血条件生效", any("收割" in l for l in logs2), str([l for l in logs2 if "收割" in l]))

    # 5. 血法师：血之契约
    print("\n— 血法师 —")
    p = mk_player("cls_blood_mage", ["血之契约", "猩红汲取", "血爆"], hp=800)
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    hp0 = p["hp"]
    logs = cast(b, p, "血之契约")
    check("血之契约扣血", p["hp"] < hp0, f"{hp0}→{p['hp']}")
    check("血祭标签", any("血祭" in l for l in logs), str([l for l in logs if "血祭" in l]))
    # 猩红汲取吸血
    b2 = BT.Battle("怪物", mk_enemy(), {}, p)
    p["hp"] = 100
    logs2 = cast(b2, p, "猩红汲取")
    check("猩红汲取回血", p["hp"] > 100, f"hp {p['hp']}")

    # 6. 虚空行者：吸MP
    print("\n— 虚空行者 —")
    p = mk_player("cls_void_walker", ["虚空箭", "虚空爆破"], mp=20)
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "虚空箭")
    check("虚空箭回蓝", p["mp"] > 20, f"mp {p['mp']}")
    check("虚空汲取日志", any("虚空汲取" in l for l in logs), str(logs))

    # 7. 丛林猎手：毒→爆
    print("\n— 丛林猎手 —")
    p = mk_player("cls_jungle_hunter", ["毒箭", "藤蔓缠绕", "毒爆", "剧毒之心"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "毒箭")
    cast(b, p, "藤蔓缠绕")
    cast(b, p, "藤蔓缠绕")
    check("毒层叠加", b.mech_stacks.get("poison", 0) >= 3, str(b.mech_stacks.get("poison")))
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "毒爆")
    check("毒爆引爆", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")
    check("毒层清空", b.mech_stacks.get("poison", 0) == 0, str(b.mech_stacks.get("poison")))

    # 8. 圣殿骑士：圣盾
    print("\n— 圣殿骑士 —")
    p = mk_player("cls_templar", ["圣盾", "圣光审判"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "圣盾")
    check("圣盾获得", len(b.p_shields) > 0, str(b.p_shields))
    logs2 = cast(b, p, "圣光审判")
    check("圣光审判输出", any("伤害" in l for l in logs2), str(logs2))

    # 9. 武圣：气连击
    print("\n— 武圣 —")
    p = mk_player("cls_wu_sheng", ["铁山靠", "气劲连打", "气爆"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "铁山靠")
    check("铁山靠攒气", b.mech_stacks.get("chi", 0) >= 1, str(b.mech_stacks))
    hp0 = b.enemy["hp"]
    logs2 = cast(b, p, "气爆")
    check("气爆输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    # 10. 奥术师：飞弹→脉冲
    print("\n— 奥术师 —")
    p = mk_player("cls_arcanist", ["奥术飞弹", "奥术脉冲"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "奥术飞弹")
    cast(b, p, "奥术飞弹")
    check("奥术印记叠加", b.mech_stacks.get("arcane", 0) >= 2, str(b.mech_stacks.get("arcane")))
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "奥术脉冲")
    check("奥术脉冲输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    # 11. 占星者：命运之轮多段
    print("\n— 占星者 —")
    p = mk_player("cls_astrologer", ["星陨", "命运之轮"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "命运之轮")
    dealt = hp0 - b.enemy["hp"]
    check("命运之轮多段输出", dealt > 150, f"dealt {dealt}")
    check("命运之轮连击日志", any("连击" in l for l in logs), str(logs))

    print()
    print(f"===== v107 隐藏职业技能层冒烟: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
