# -*- coding: utf-8 -*-
"""v130.4 批量使用固化测试（玩家意见 #11：使用物品支持批量）

覆盖：
  ① 『使用 <名>*<数量>』星号格式批量（扣减+回血+汇总行）
  ② 『使用 <名> <数量>』空格格式批量
  ③ 数量超过持有 → 显式报错不钳制
  ④ 数量 0/负 → 显式报错
  ⑤ 数量格式错（*abc）→ 显式报错
  ⑥ 战斗中批量 → 拒绝（回合制一次 1 个）
  ⑦ 满血拦截：单次使用不扣道具（回归）、批量中途满血停止并提示
  ⑧ 无数量单次使用行为不回归（不显示汇总行）

运行：python tests/test_v1304_use_batch.py（exit=0 全绿）
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1304_use_batch.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, FakeEvent, clean_db, make_player  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402
from data.plugins.dragonfall.game.commands._registry import COMMAND_REGEX  # noqa: E402

passed = failed = 0
G, Q = 1095961596, "gm_t1304"
POT = "测试药水"


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"✅ {name}")
    else:
        failed += 1
        print(f"❌ {name} {detail}")


async def _cmd(m, cmd):
    """注册表分发，Main 多继承环境（MRO 坑必须实测）"""
    ev = FakeEvent(G, Q, cmd)
    for key, pat in COMMAND_REGEX.items():
        if re.match(pat, cmd):
            fn = getattr(m, key, None)
            if fn:
                out = []
                async for r in fn(ev):
                    out.append(r)
                if out and isinstance(out[0], tuple):
                    return out[0][1]
                return str(out[0]) if out else ""
            return ""
    return ""


def _seal(gid, qid, count=5, hp=50):
    """落库玩家+测试药水（heal=20 固定值）"""
    make_player(gid, qid, "批量测试", "战士", level=3)
    from data.plugins.dragonfall.game import db
    db.update_player(gid, qid, hp=hp)
    db.add_item(gid, qid, "test_pot", {"name": POT, "type": "药剂", "heal": 20}, count=count)


def _held(gid, qid):
    from data.plugins.dragonfall.game import db
    items = db.get_inventory(gid, qid)
    for it in items:
        if it["data"]["name"] == POT:
            return it["count"]
    return 0


async def main():
    from data.plugins.dragonfall.game import db
    m = Main()

    # ---- ① 星号批量 3 个 ----
    clean_db()
    _seal(G, Q, count=5, hp=50)
    r = await _cmd(m, f"使用 {POT}*3")
    check("① 星号批量回血文本", "恢复 20 点生命" in r and "已使用 3 个" in r, r[:120])
    check("① 扣减 3 个", _held(G, Q) == 2, f"持有={_held(G, Q)}")
    p = db.get_player(G, Q)
    check("① HP 50→100（封顶）", p["hp"] == 100, f"hp={p['hp']}")

    # ---- ② 空格格式批量 2 个 ----
    clean_db()
    _seal(G, Q, count=5, hp=50)
    p = db.get_player(G, Q)
    db.update_player(G, Q, hp=50)
    r = await _cmd(m, f"使用 {POT} 2")
    check("② 空格格式批量", "已使用 2 个" in r, r[:120])
    check("② 扣减 2 个", _held(G, Q) == 3, f"持有={_held(G, Q)}")

    # ---- ③ 超持有显式报错 ----
    clean_db()
    _seal(G, Q, count=5)
    r = await _cmd(m, f"使用 {POT}*99")
    check("③ 超持有报错", "你只有 5 个" in r, r[:120])
    check("③ 不扣减", _held(G, Q) == 5, f"持有={_held(G, Q)}")

    # ---- ④ 0/负数量报错 ----
    clean_db()
    _seal(G, Q, count=5)
    r = await _cmd(m, f"使用 {POT}*0")
    check("④ 数量 0 报错", "数量至少 1 个" in r, r[:120])
    r = await _cmd(m, f"使用 {POT} -1")
    check("④ 数量负报错", "数量至少 1 个" in r, r[:120])
    check("④ 不扣减", _held(G, Q) == 5, f"持有={_held(G, Q)}")

    # ---- ⑤ 格式错 ----
    clean_db()
    _seal(G, Q, count=5)
    r = await _cmd(m, f"使用 {POT}*abc")
    check("⑤ 格式错报错", "数量格式不对" in r, r[:120])

    # ---- ⑥ 战斗中批量拒绝 ----
    clean_db()
    _seal(G, Q, count=5, hp=50)
    db.save_battle(G, Q, {"type": "normal", "round": 0, "enemy": {"name": "测试狼"}, "p_buffs": {}, "e_buffs": {}, "p_defending": False, "e_defending": False})
    r = await _cmd(m, f"使用 {POT}*2")
    check("⑥ 战斗中批量拒绝", "战斗中一次只能使用 1 个道具" in r, r[:120])
    check("⑥ 拒绝不扣减", _held(G, Q) == 5, f"持有={_held(G, Q)}")
    db.clear_battle(G, Q)

    # ---- ⑦ 满血拦截 ----
    clean_db()
    _seal(G, Q, count=5, hp=100)
    r = await _cmd(m, f"使用 {POT}")
    check("⑦ 满血单次拦截不扣", "用不着" in r and _held(G, Q) == 5, r[:120])
    # 批量中途满血：hp=90，heal 20 → 第 1 个满 100，第 2 个拦截
    clean_db()
    _seal(G, Q, count=5, hp=90)
    r = await _cmd(m, f"使用 {POT}*2")
    check("⑦ 批量中途满血停止", "已使用 1/2 个" in r, r[:120])
    check("⑦ 只扣 1 个", _held(G, Q) == 4, f"持有={_held(G, Q)}")

    # ---- ⑧ 单次使用不回归 ----
    clean_db()
    _seal(G, Q, count=5, hp=50)
    r = await _cmd(m, f"使用 {POT}")
    check("⑧ 单次无汇总行", "已使用" not in r, r[:120])
    check("⑧ 单次扣 1 个", _held(G, Q) == 4, f"持有={_held(G, Q)}")
    p = db.get_player(G, Q)
    check("⑧ 单次回血 70", p["hp"] == 70, f"hp={p['hp']}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


os_asy = __import__("asyncio")
os_asy.run(main())