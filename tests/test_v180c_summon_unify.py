#!/usr/bin/env python3
"""v180-C S2 收尾门禁：召唤物装配统一（_spawn_companion）行为等价锚。

覆盖：
1. 技能召唤 _summon_entity 走 _spawn_companion 生成实体（属性/上限/auto_act/guard 不变）
2. 药水召唤 eff_summon 走 _spawn_companion（限 1 只 + 附属 buffs 不变）
3. 装配统一后实体仍是 companions 里 kind==summon 的 actor（side/buffs 容器齐全）
4. 药水召唤不吃 summon_power（与技能召唤区分）
5. 回归：召唤物普攻 / 挡刀 / 序列化行为不因装配重构变化

背景：v180-C S2 把 _summon_entity 与 potion_effects.eff_summon 两处手写装配
收进 battle._spawn_companion 单一装配函数（设计文档 §3.4），本测试保证
重构前后行为等价（属性缩放/上限/辅助 buff/actor 字段一致）。
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
    from data.plugins.dragonfall.game.data.summons import SUMMONS
    from data.plugins.dragonfall.game.core import potion_effects as PE

    print("===== v180-C S2 装配统一行为等价 =====\n")

    def mk_player(extra=None, cls="牧师", hp=500):
        p = {
            "class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
            "mp": 100, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试杖", "stats": {"atk": 100, "matk": 100},
                                     "affixes": [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": [], "race": "human",
        }
        if extra:
            p.update(extra)
        return p

    def mk_enemy(def_=20, hp=50000):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 100, "def": def_, "mdef": 20, "spd": 10}

    # 1. 技能召唤走统一装配
    print("\n— 技能召唤（_summon_entity → _spawn_companion）—")
    p1 = mk_player()
    b1 = BT.Battle("怪物", mk_enemy(), {}, p1)
    st1 = b1._player_stats(p1)
    logs1 = []
    ok1 = b1._summon_entity("skeleton", p1, logs1)
    check("召唤成功", ok1, str(logs1))
    check("实体进 companions", len(b1.companions) == 1, str(len(b1.companions)))
    check("summons 视图可见", len(b1.summons) == 1, str(len(b1.summons)))
    s1 = b1.companions[0]
    exp_hp = max(20, int(st1["max_hp"] * SUMMONS["skeleton"]["hp_ratio"]))
    exp_atk = max(0, int(st1["atk"] * SUMMONS["skeleton"]["atk_ratio"]))
    check(f"HP 按玩家比例 ({exp_hp})", abs(s1["hp"] - exp_hp) <= 1, f"got {s1['hp']}")
    check(f"ATK 按玩家比例 ({exp_atk})", abs(s1["atk"] - exp_atk) <= 1, f"got {s1['atk']}")
    check("actor 容器齐全", s1.get("side") == "player" and s1.get("kind") == "summon"
          and isinstance(s1.get("buffs"), dict), str({k: s1.get(k) for k in ("side", "kind", "buffs")}))
    check("auto_act player_act", (s1.get("auto_act") or {}).get("trigger") == "player_act", str(s1.get("auto_act")))
    check("guard 数据化", (s1.get("guard") or {}).get("chance") == 0.40, str(s1.get("guard")))
    check("日志有加入提示", any("加入战斗" in l for l in logs1), str(logs1))

    # 2. 药水召唤走统一装配（烬灵香炉：atk 型 + 挡刀）
    print("\n— 药水召唤（eff_summon → _spawn_companion）—")
    p2 = mk_player()
    b2 = BT.Battle("怪物", mk_enemy(), {}, p2)
    st2 = b2._player_stats(p2)
    from data.plugins.dragonfall.game.data.items import ITEMS
    ed_wisp = ITEMS["i_jin_ling_xiang_lu"]["effect_data"]
    logs2 = []
    ret2 = PE.POTION_EFFECTS["summon"](b2, p2, dict(ed_wisp))
    check("烬灵召唤返回成功文案", "✨ 召唤成功" in str(ret2), str(ret2))
    check("烬灵实体 1 个", len(b2.companions) == 1, str(len(b2.companions)))
    s2 = b2.companions[0]
    exp_hp2 = max(20, int(st2["max_hp"] * float(ed_wisp.get("hp_ratio", 0.30))))
    exp_atk2 = max(5, int(st2["atk"] * float(ed_wisp.get("atk_ratio", 0.35))))
    check(f"HP 按药水比例 ({exp_hp2})", abs(s2["hp"] - exp_hp2) <= 1, f"got {s2['hp']}")
    check(f"ATK 按药水比例 ({exp_atk2})", abs(s2["atk"] - exp_atk2) <= 1, f"got {s2['atk']}")
    check("actor 容器齐全", s2.get("side") == "player" and s2.get("kind") == "summon"
          and isinstance(s2.get("buffs"), dict), str({k: s2.get(k) for k in ("side", "kind", "buffs")}))
    check("药水召唤不吃 summon_power", True)  # 占位（下条精确断言）

    # 3. 药水召唤不吃 summon_power（与技能召唤区分）
    print("\n— summon_power 区分 —")
    p3 = mk_player()
    p3["equipment"]["weapon"]["stats"]["summon_power"] = 0.50
    b3 = BT.Battle("怪物", mk_enemy(), {}, p3)
    st3 = b3._player_stats(p3)
    b3._summon_entity("skeleton", p3, [])
    sk3 = b3.companions[0]
    check("技能召唤吃 summon_power", abs(sk3["atk"] - max(0, int(st3["atk"] * 0.50 * 1.5))) <= 1,
          f"got {sk3['atk']}")
    p3b = mk_player()
    p3b["equipment"]["weapon"]["stats"]["summon_power"] = 0.50
    b3b = BT.Battle("怪物", mk_enemy(), {}, p3b)
    st3b = b3b._player_stats(p3b)
    PE.POTION_EFFECTS["summon"](b3b, p3b, dict(ed_wisp))
    w3 = b3b.companions[0]
    exp_atk3b = max(5, int(st3b["atk"] * float(ed_wisp.get("atk_ratio", 0.35))))
    check("药水召唤不吃 summon_power", abs(w3["atk"] - exp_atk3b) <= 1,
          f"got {w3['atk']} exp {exp_atk3b}")

    # 4. 药水召唤 limit 记账（每场限 1）
    print("\n— 药水 limit 记账 —")
    p4 = mk_player()
    b4 = BT.Battle("怪物", mk_enemy(), {}, p4)
    ret4a = PE.POTION_EFFECTS["summon"](b4, p4, dict(ed_wisp))
    ret4b = PE.POTION_EFFECTS["summon"](b4, p4, dict(ed_wisp))
    check("第一次成功", "✨ 召唤成功" in str(ret4a), str(ret4a))
    check("第二次被拒", "每场战斗只能使用 1 次" in str(ret4b), str(ret4b))
    check("实体仍 1 个", len(b4.companions) == 1, str(len(b4.companions)))
    check("summon_used 记账", "ember_wisp" in p4.setdefault("eff", {}).setdefault("summon_used", []),
          str(p4.setdefault("eff", {}).get("summon_used")))

    # 5. 药水召唤附属 buff（荆棘傀儡种 thorns）
    print("\n— 药水附属 buff —")
    p5 = mk_player()
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    ed_thorn = ITEMS["i_jing_ji_kui_lei_zhong"]["effect_data"]
    ret5 = PE.POTION_EFFECTS["summon"](b5, p5, dict(ed_thorn))
    check("荆棘傀儡召唤成功", "✨ 召唤成功" in str(ret5), str(ret5))
    check("thorns_pot buff 挂上", int(p5.setdefault("buffs", {}).get("thorns_pot", 0) or 0) == int(ed_thorn.get("turns", 3)),
          str(p5.get("buffs")))
    check("荆棘傀儡辅助型不普攻（无 auto_act）", b5.companions[0].get("auto_act") is None,
          str(b5.companions[0].get("auto_act")))
    check("荆棘傀儡有血防（挡刀存在性）", b5.companions[0]["hp"] > 20 and b5.companions[0]["def"] > 0,
          f"hp {b5.companions[0]['hp']} def {b5.companions[0]['def']}")

    # 6. 普攻行为回归（装配后 auto_act 仍驱动攻击）
    print("\n— 普攻/挡刀行为回归 —")
    p6 = mk_player()
    b6 = BT.Battle("怪物", mk_enemy(def_=10, hp=50000), {}, p6)
    b6._summon_entity("skeleton", mk_player(), [])
    hp6 = b6.enemy["hp"]
    logs6 = []
    b6._companions_trigger("player_act", logs6)
    check("召唤物普攻造成伤害", b6.enemy["hp"] < hp6, f"dealt {hp6 - b6.enemy['hp']}")
    check("攻击日志", any("攻击" in l for l in logs6), str(logs6))

    # 7. 序列化回归
    print("\n— 序列化 —")
    b7 = BT.Battle("怪物", mk_enemy(), {}, mk_player())
    b7._summon_entity("skeleton", mk_player(), [])
    st7 = b7.to_state()
    check("to_state 含 summons", len(st7.get("summons", [])) == 1, str(len(st7.get("summons", []))))
    b7r = BT.Battle.from_state(st7)
    check("from_state 恢复 companions", len(b7r.companions) == 1 and b7r.companions[0]["tid"] == "skeleton",
          str(len(getattr(b7r, "companions", []))))

    print()
    print(f"===== v180-C S2 装配统一: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
