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
    p = mk_player("cls_dragon_oath", ["龙息", "龙息之怒"])
    b = BT.Battle("怪物", mk_enemy(def_=5000, hp=50000), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "龙息")
    dealt = hp0 - b.enemy["hp"]
    check("龙息真伤无视 def=5000", dealt > 100, f"dealt {dealt}")
    check("龙息附灼烧", any("灼烧" in l for l in logs), str(logs[:2]))

    # 2. 暗影祭司：召唤骷髅
    print("\n— 暗影祭司 —")
    p = mk_player("cls_hymn", ["召唤骷髅", "骷髅海"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "召唤骷髅")
    check("召唤骷髅生成", len(b.summons) == 1, str(b.summons))
    logs2 = cast(b, p, "骷髅海")
    check("骷髅海再召唤", len(b.summons) == 2, str(len(b.summons)))
    check("骷髅海带攻击buff", b.p_buffs.get("atk_up", 0) > 0, str(b.p_buffs))

    # 3. 植物召唤（v113 兽群进化链已删，召唤下放基础游侠攻线·林语者）
    print("\n— 林语者：植物召唤 —")
    p = mk_player("cls_you_xia", ["召唤藤蔓守卫", "召唤古树守卫"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "召唤藤蔓守卫")
    check("召唤藤蔓守卫", b.summons[0]["tid"] == "vine_guard", str([s.get("tid") for s in b.summons]))
    cast(b, p, "召唤古树守卫")
    check("再召古树守卫", any(s["tid"] == "treant" for s in b.summons),
          str([s.get("tid") for s in b.summons]))

    # 4. 暮影行者（暗杀流）：幽影连刺多段（v113 收割流派已下放基础刺客）
    print("\n— 暮影行者（暗杀流）—")
    p = mk_player("cls_shadow_blade", ["幽影袭", "幽影连刺", "幽影刃"])
    b = BT.Battle("怪物", mk_enemy(hp=50000), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "幽影连刺")
    check("幽影连刺多段输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")
    logs2 = cast(b, p, "幽影连刺")
    check("幽影连刺日志", any("幽影连刺" in l for l in logs + logs2),
          str([l for l in logs + logs2 if "幽影连刺" in l]))

    # 5. 虚空爆破（v113 从时咒线虚空流下放基础法师攻线）：吸MP
    print("\n— 法师·虚空爆破（吸蓝）—")
    p = mk_player("cls_fa_shi", ["虚空爆破"], mp=20)
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "虚空爆破")
    check("虚空爆破回蓝", p["mp"] > 20, f"mp {p['mp']}")
    check("虚空汲取日志", any("虚空汲取" in l for l in logs), str([l for l in logs if "虚空汲取" in l]))

    # 6. 游侠·林语者（v113 自然毒藤下放基础攻线）：毒→爆
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

    # 7. 龙裔誓约（龙血流）：龙焰吐息真伤（v113 本线只留龙血流派）
    print("\n— 龙裔誓约（龙血流）—")
    p = mk_player("cls_dragon_oath", ["龙息", "龙鳞", "龙威", "龙焰吐息"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "龙焰吐息")
    check("龙焰吐息真伤", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")
    check("龙焰吐息附灼烧", any("灼烧" in l for l in logs), str([l for l in logs if "灼烧" in l]))
    logs_c = cast(b, p, "龙鳞")
    check("龙鳞防御增益", any("龙鳞" in l for l in logs_c), str([l for l in logs_c if "龙鳞" in l]))

    # 8. 苦修士：气连击
    print("\n— 苦修士 —")
    p = mk_player("cls_wu_sheng", ["裂岩冲", "气力连打", "气爆"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    logs = cast(b, p, "裂岩冲")
    check("裂岩冲攒气", b.mech_stacks.get("chi", 0) >= 1, str(b.mech_stacks))
    hp0 = b.enemy["hp"]
    logs2 = cast(b, p, "气爆")
    check("气爆输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    # 9. 奥秘守线（基础法师）：飞弹→脉冲
    print("\n— 奥秘守线 —")
    p = mk_player("cls_fa_shi", ["奥术飞弹", "奥术脉冲"])
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    cast(b, p, "奥术飞弹")
    cast(b, p, "奥术飞弹")
    check("奥术印记叠加", b.mech_stacks.get("arcane", 0) >= 2, str(b.mech_stacks.get("arcane")))
    hp0 = b.enemy["hp"]
    logs = cast(b, p, "奥术脉冲")
    check("奥术脉冲输出", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    # 10. 星语者（原占星者，cls_wild_hunter 不变）：命运之轮多段
    print("\n— 星语者 —")
    p = mk_player("cls_wild_hunter", ["星陨", "命运之轮"])
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
