# -*- coding: utf-8 -*-
"""v101.30 阶段三验证：强化段位经验 + 精炼强化石/强化石接入"""
import sys, os, io, asyncio, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from tests.conftest import C, db, clean_db, Main, FakeEvent, run

m = Main(None)

async def cmd(name, msg, gid="g1", qid="w1"):
    ev = FakeEvent(gid, qid, msg)
    results = await run(getattr(m, name), ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    await cmd("register", "注册 战士 测试强化 男")
    db.update_player("g1", "w1", cur_map="oak_town", cur_subarea="oak_town_3",
                     gold=999999, apprentices=["enhance"],
                     stamina=100, level=20)
    db.add_item("g1", "w1", "eq_test1", {"name": "试炼剑", "slot": "weapon", "quality": "white",
                                         "lv": 10, "enhance": 0, "stats": {"atk": 10}, "price": 50})
    # 每日任务已领，防止经验干扰
    db.set_event_state(f"prof_daily_g1_w1_{time.strftime('%Y-%m-%d')}", "enhance|强化装备|1|50|1|1")

    # 1. +0->+1 成功给 1 经验
    out = await cmd("enhance", "强化 试炼剑")
    profs = db.get_professions("g1", "w1")
    print("1) out:", out[:200])
    print("1) +0->+1:", "强化成功" in out, "| enhance lv/exp:", profs["enhance"]["lv"], profs["enhance"]["exp"])
    assert profs["enhance"]["exp"] == 1, f"期望 1 exp, 实际 {profs['enhance']['exp']}"

    # 2. 装备已 +1，继续强化会要求 Lv.2（被拦）
    out = await cmd("enhance", "强化 试炼剑")
    print("2) +1->+2 拦截:", "需要强化副业 Lv.2" in out)

    # 3. 副业升到 Lv.2 再强化 +1->+2 成功给 2 exp
    db.add_prof_exp("g1", "w1", "enhance", 19)
    out = await cmd("enhance", "强化 试炼剑")
    profs = db.get_professions("g1", "w1")
    print("3) +1->+2:", "强化成功" in out, "| enhance lv/exp:", profs["enhance"]["lv"], profs["enhance"]["exp"])
    assert profs["enhance"]["exp"] == 2, f"期望 2 exp, 实际 {profs['enhance']['exp']}"

    # 4. 精炼强化石：+2->+3 需 Lv.3；带精炼强化石 +25% -> 105% 必成且消耗
    db.add_prof_exp("g1", "w1", "enhance", 40)  # -> Lv.3
    db.add_item("g1", "w1", "i_stone_refine", {"name": "精炼强化石", "type": "矿石", "price": 800})
    out = await cmd("enhance", "强化 试炼剑")
    have = db.count_item("g1", "w1", "i_stone_refine")
    print("4) +2->+3 精炼强化石:", "强化成功" in out, "| 剩余:", have, "| 提示:", "成功率提升" in out)
    assert have == 0, "精炼强化石应被消耗"
    assert "成功率提升" in out, "应提示精炼强化石生效"
    profs = db.get_professions("g1", "w1")
    print("   exp now:", profs["enhance"]["exp"], "(2+40->Lv3 剩2, +3=5)")

    # 5. 强化石失败保护：装备提 +4，Lv.5 强化 +4->+5（50%），带强化石
    items = db.get_inventory("g1", "w1")
    for it in items:
        if it["data"].get("name") == "试炼剑":
            it["data"]["enhance"] = 4
            db.remove_item("g1", "w1", it["key"])
            db.add_item("g1", "w1", it["key"], it["data"], 1)
            break
    db.add_prof_exp("g1", "w1", "enhance", 400)  # 升到 Lv.5+
    db.add_item("g1", "w1", "i_stone_upgrade", {"name": "强化石", "type": "矿石", "price": 400})
    out = await cmd("enhance", "强化 试炼剑")
    have2 = db.count_item("g1", "w1", "i_stone_upgrade")
    print("5) +4->+5:", "强化成功" in out or "强化失败" in out, "| 强化石剩余:", have2,
          "| 保护触发:", "保住了等级" in out)
    # 成功: 不消耗(剩1)；失败: 保护消耗(剩0) 且提示保级
    if "强化成功" in out:
        assert have2 == 1, "成功不应消耗强化石"
    else:
        assert have2 == 0 and "保住了等级" in out, f"失败应触发保护: {out[:150]}"

    print("\n✅ 阶段三验证全部通过")

asyncio.run(main())
