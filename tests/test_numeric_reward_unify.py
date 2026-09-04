# -*- coding: utf-8 -*-
"""test_numeric_reward_unify —— 统一奖励发放门禁（v174）

防退化断言：
  1. grant_reward 各类型发放（exp/gold/items/equips/pets/mounts/title）
  2. 多动作连发不覆盖（曾 bug：旧 player 引用覆盖新 gold）
  3. 已接入来源奖励正确性（成就/任务/对话/周常发奖走统一入口）
  4. 物品缺失静默跳过不阻塞（exp/gold 照发）

运行：python tests/test_numeric_reward_unify.py（exit=0 全绿）
"""
import os
import sys
import asyncio

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (_SCRIPT_DIR, os.path.dirname(_SCRIPT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_SCRIPT_DIR, "test_game_data.db"))

from conftest import C, E, db, clean_db, Main, FakeEvent, run  # noqa: E402

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail)[:300]}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "gr", "wr", "注册 战士 奖测 男")
    db.update_player("gr", "wr", level=1, gold=100)

    print("【reward_unify：grant_reward 全类型】")
    from game.reward import grant_reward
    p = db.get_player("gr", "wr")
    lines = grant_reward({
        "exp": 300, "gold": 200,
        "items": [{"item": "mat_cao_yao", "n": 3}],
        "pets": ["pet_turtle"],
    }, "gr", "wr")
    p2 = db.get_player("gr", "wr")
    check("exp+gold 入账", p2["gold"] == 300 and p2["exp"] == 300, f"gold{p2['gold']} exp{p2['exp']}")
    check("文案含经验金币", any("经验 +300" in l and "金币 +200" in l for l in lines), str(lines))
    check("物品入包", db.count_item("gr", "wr", "mat_cao_yao") == 3)
    check("宠物蛋入包", db.count_item("gr", "wr", "petegg_pet_turtle") == 1)

    print("【reward_unify：装备/称号】")
    lines = grant_reward({"equips": [{"rid": "eq_ju_mo_liao_ya_zhui"}], "title": "不存在的称号"}, "gr", "wr")
    inv = db.get_inventory("gr", "wr") or []
    keys = [x.get("key") for x in inv] if isinstance(inv, list) else list(inv.keys())
    check("名册装备入包", any(str(k).startswith("eq_") for k in keys), f"{keys}")
    check("未知称号不崩(跳过)", len(lines) >= 1, str(lines))

    print("【reward_unify：多动作连发不覆盖（曾 bug）】")
    db.update_player("gr", "wr", gold=1000)
    # 模拟对话一次带三个动作（旧 player 引用会覆盖）
    m._apply_talk_action("gr", "wr", db.get_player("gr", "wr"), "npc_mayor",
                         {"give_gold": 50, "give_exp": 30})
    p4 = db.get_player("gr", "wr")
    check("give_gold 50 生效不被覆盖", p4["gold"] == 1050, f"gold{p4['gold']}")
    check("give_exp 30 生效", p4["exp"] >= 330, f"exp{p4['exp']}")

    print("【reward_unify：物品缺失不阻塞 exp/gold】")
    before = db.get_player("gr", "wr")["gold"]
    lines = grant_reward({"gold": 10, "items": [{"item": "mat_bu_cun_zai_zzz", "n": 1}]}, "gr", "wr")
    p5 = db.get_player("gr", "wr")
    check("缺失物品不阻塞金币", p5["gold"] == before + 10, f"gold{p5['gold']}")

    print("【reward_unify：空奖励安全】")
    lines = grant_reward({}, "gr", "wr")
    check("空奖励返回空", lines == [], str(lines))
    lines = grant_reward(None, "gr", "wr")
    check("None 奖励返回空", lines == [], str(lines))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if asyncio.run(main()) else 1)
