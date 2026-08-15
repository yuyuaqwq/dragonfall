# -*- coding: utf-8 -*-
"""v97.7 临时验证：战斗内使用道具（模板引擎重构后行为对齐）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, E, BT, Main, FakeEvent, run, clean_db

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人 男")
    db.update_player("g1", "w1", cur_map="oak_plain", level=5, gold=999999)
    # v95.19：战斗内 max_hp/max_mp 由引擎实时重算（换装备一致），预设必须用引擎值
    p0 = db.get_player("g1", "w1")
    db.update_player("g1", "w1", hp=p0["max_hp"], mp=p0["max_mp"])
    ok = fail = 0
    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond: ok += 1; print(f"  ✅ {name}")
        else: fail += 1; print(f"  ❌ {name} {detail}")

    # 造一场战斗（test_v94 现成 state 模式：手写怪物 dict）
    import random
    random.seed(42)
    mon = {"name": "测试怪", "hp": 999999, "max_hp": 999999, "def": 50, "mdef": 40,
           "spd": 5, "atk": 30, "matk": 30, "crit": 0.0, "dodge": 0.0,
           "is_boss": False, "is_elite": False, "skills": [], "exp": 10, "gold": 10}
    db.save_battle("g1", "w1", {"type": "monster", "round": 0, "enemy": mon,
                                "p_buffs": {}, "e_buffs": {}, "p_defending": False,
                                "e_defending": False})

    # 1. 战斗内治疗药水
    hp_before = db.get_player("g1", "w1")["hp"]
    db.add_item("g1", "w1", "pot_test1", {"name": "治疗药水(中)", "type": "消耗品",
                "stackable": True, "heal": 0.4, "price": 30})
    out = await cmd(m, "use", "g1", "w1", "使用 治疗药水(中)")
    p = db.get_player("g1", "w1")
    check("战斗内治疗回血", p["hp"] > hp_before, f"hp={p['hp']} out={out[:80]}")
    check("战斗内治疗提示恢复", "恢复" in out, out[:120])

    # 2. 战斗内 buff 药水
    db.add_item("g1", "w1", "pot_test2", {"name": "力量药剂", "type": "消耗品",
                "stackable": True, "effect": "buff_atk", "price": 100})
    out = await cmd(m, "use", "g1", "w1", "使用 力量药剂")
    bt = db.get_battle("g1", "w1")
    check("战斗内buff挂p_buffs", (bt["state"].get("p_buffs") or {}).get("atk_up", 0) >= 2,
          str(bt["state"].get("p_buffs")))  # 3 回合 buff，本回合结束衰减 1
    check("战斗内buff日志", "大幅提升" in out, out[:120])

    # 3. 战斗内 mana 药水（只回蓝不回血）
    p = db.get_player("g1", "w1")
    p_mp0 = p["mp"]
    p_hp0 = p["hp"]
    db.update_player("g1", "w1", mp=max(0, p_mp0 - 50))  # 先扣蓝再喝
    db.add_item("g1", "w1", "pot_test3", {"name": "魔法药水(中)", "type": "消耗品",
                "stackable": True, "mana": 0.4, "price": 30})
    out = await cmd(m, "use", "g1", "w1", "使用 魔法药水(中)")
    p = db.get_player("g1", "w1")
    check("战斗内mana回蓝", p["mp"] > p_mp0 - 50, f"mp={p['mp']} vs {p_mp0 - 50}")
    # v121 CTB：mana 药水本身不加血；旧 v61"速度优势回合敌方不行动"使本断言成立，
    # CTB 下玩家行动后敌方按 ct 正常行动（怪 spd 5 开局排第 2 位），hp 减少来自怪攻击。
    check("战斗内mana不回血", p["hp"] <= p_hp0, f"hp={p['hp']} vs {p_hp0}")

    # 4. 战斗中卷轴拦截
    db.add_item("g1", "w1", "pot_test4", {"name": "传送卷轴", "type": "消耗品",
                "stackable": True, "effect": "return_vila", "price": 500})
    out = await cmd(m, "use", "g1", "w1", "使用 传送卷轴")
    check("战斗内卷轴拦截", "战斗中只能使用" in out, out[:120])

    # 5. 战斗中食物（heal+stamina 复合）
    db.add_item("g1", "w1", "pot_test5", {"name": "黑面包", "type": "消耗品",
                "stackable": True, "heal": 0.3, "stamina": 20, "price": 5})
    out = await cmd(m, "use", "g1", "w1", "使用 黑面包")
    check("战斗内食物可用", "体力" in out or "恢复" in out, out[:150])

    # 6. 战斗外 buff 药水提示
    db.update_player("g1", "w1", cur_map="oak_town")
    db.clear_battle("g1", "w1")  # 结束战斗
    db.add_item("g1", "w1", "pot_test6", {"name": "力量药剂", "type": "消耗品",
                "stackable": True, "effect": "buff_atk", "price": 100})
    out = await cmd(m, "use", "g1", "w1", "使用 力量药剂")
    check("战斗外buff提示战斗中用", "战斗" in out, out[:120])
    # 物品还在（没被扣）
    has = any(it["key"] == "pot_test6" for it in db.get_inventory("g1", "w1"))
    check("战斗外buff不扣物品", has, "")

    print(f"\n结果: {ok} 通过, {fail} 失败")
    return fail == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
