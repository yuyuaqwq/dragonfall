# -*- coding: utf-8 -*-
"""T5 意见#6『采集后没有东西』复现/验证脚本（workspace/feedback_fix/verify_T5.py）

链路：采集指令 → 等待轮(set_timed prof_wait) → 到点 _prof_delayed_push 结算入包。
复现目标：延迟推送失败（进程重启/异常被吞）后，任意指令的 _maint_gate → refresh_timed
物理删除过期事件 → 结算数据永久丢失 → 背包无物、无提示（= 玩家反馈『采集后没有东西』）。

运行：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe workspace/feedback_fix/verify_T5.py
"""
import os
import sys
import json
import time

PLUGIN = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
TESTDIR = os.path.join(PLUGIN, "tests")
for p in (TESTDIR, os.path.dirname(PLUGIN), os.path.dirname(os.path.dirname(PLUGIN))):
    if p not in sys.path:
        sys.path.insert(0, p)

# 独立私有临时库（绝不触碰生产库）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_T5.db")
os.environ["GWEN_GAME_DB"] = _DB
os.environ["GWEN_TEST_MODE"] = "1"

from conftest import C, db, clean_db, Main, FakeEvent, run  # noqa: E402
from data.plugins.dragonfall.game.core import timed_events as _te  # noqa: E402

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

def expire_event_now(gid, qid):
    """模拟『到点但延迟推送未结算』（进程重启/推送失败）：把引擎事件 expire 改为过去。

    真实场景里 set_timed 写入 data.finish == expire（同一时刻），重启间隔后两者都在过去；
    这里必须同时改 data.finish（_prof_wait_compat 以 data.finish 为准判到期）。"""
    raw = db.get_event_state(_te._PLAYER_KEY.format(qq_id=qid))
    assert raw, "无引擎事件可过期"
    d = json.loads(raw)
    if "prof_wait" in d:
        past = int(time.time()) - 5
        d["prof_wait"]["expire"] = past
        if isinstance(d["prof_wait"].get("data"), dict):
            d["prof_wait"]["data"]["finish"] = past
        db.set_event_state(_te._PLAYER_KEY.format(qq_id=qid), json.dumps(d, ensure_ascii=False))

def bag_mats(gid, qid):
    out = {}
    for it in db.get_inventory(gid, qid):
        k = it["key"]
        if k.startswith("mat_"):
            out[k] = it["count"]
    return out

async def new_gather_player(m, gid, qid):
    clean_db()
    await cmd(m, "register", gid, qid, "注册 战士 旅人 男")
    db.update_player(gid, qid, level=20, gold=5000, cur_map="oak_plain", stamina=9999,
                     apprentices=["gather"])

async def scenario():
    m = Main(None)
    print("== Part 1: 采集池数据完整性（材料 ID 必须全部存在于 MATERIALS）==")
    bad = []
    for mid, w in [(x[0], x[1]) for pl in C.GATHER_MAP_POOLS.values() for x in pl]:
        if mid not in C.MATERIALS:
            bad.append((mid, "MAP"))
        if not (isinstance(w, int) and w > 0):
            bad.append((mid, f"权重{w}"))
    for mid, w, cond in [x for pl in C.GATHER_COND_POOLS.values() for x in pl]:
        if mid not in C.MATERIALS:
            bad.append((mid, "COND"))
        if not (isinstance(w, int) and w > 0):
            bad.append((mid, f"权重{w}"))
    check("采集池/条件池全部材料 ID 有效且权重>0", not bad, str(bad[:10]))
    # 全地图 _gather_roll 冒烟（含未配置地图的价格带兜底）
    import random
    inst = m
    rolls = []
    for mid in C.MAP_BY_ID:
        try:
            with __import__("unittest").mock.patch("random.random", return_value=0.99), \
                 __import__("unittest").mock.patch("random.randint", return_value=1):
                rolls.extend(inst._gather_roll(1, 1, mid))
        except Exception as e:
            rolls.append(("EXC", mid, repr(e)))
    bad2 = [r for r in rolls if not isinstance(r, tuple)]
    check("全地图 _gather_roll 无异常且恒有产出", len(rolls) == (len(C.MAP_BY_ID)) and not bad2,
          str([r for r in rolls if isinstance(r, tuple)][:5]))

    print("== Part 2A: 正常主路径（延迟推送结算）==")
    await new_gather_player(m, "gA", "qA")
    out = await cmd(m, "gather", "gA", "qA", "采集")
    check("采集开轮提示", "开始采集" in out, out[:200])
    before = bag_mats("gA", "qA")
    # 正常路径：直接结算（模拟 push 到点）
    st = m._prof_wait_residual("gA", "qA")
    text = m._prof_settle("gA", "qA", st)
    after = bag_mats("gA", "qA")
    diff = sum(after.values()) - sum(before.values())
    check("正常结算：背包 +1~2 份材料（_gather_roll 数量 1~2）", 1 <= diff <= 2, f"{before}→{after}")
    check("正常结算：提示语含物品名", text and "采到了" in text, (text or "")[:120])

    print("== Part 2B: 修复注记——到点未结算 + 任意指令 refresh ===")
    # 修复前行为：refresh_timed 物理删除事件 → residual=None、背包空（复现『采集后没有东西』，
    # 第一轮运行实录见 audit_T5.md）。修复后：on_expire 把数据保全到遗留键，residual 可读。
    await new_gather_player(m, "gB", "qB")
    out = await cmd(m, "gather", "gB", "qB", "采集")
    check("采集开轮提示", "开始采集" in out, out[:200])
    before = bag_mats("gB", "qB")
    expire_event_now("gB", "qB")          # 模拟重启/推送失败：事件已到点但从未结算
    # 玩家发任意指令（如『背包』）→ _maint_gate 先 refresh_timed
    n = _te.refresh_timed("gB", "qB")
    check("refresh_timed 清掉引擎过期事件", n == 1, f"n={n}")
    after = bag_mats("gB", "qB")
    res = m._prof_wait_residual("gB", "qB")
    check("修复后：结算数据不再被物理删除（on_expire 保全，residual 可读）", res is not None, str(res))
    check("修复后：刷新本身不入包（待下条副业指令惰性结算）",
          sum(after.values()) == sum(before.values()), f"{before}→{after}")

    print("== Part 2C: 对照——到点未结算后玩家下一个指令仍是『采集』（现行唯一幸存路径）==")
    await new_gather_player(m, "gC", "qC")
    out = await cmd(m, "gather", "gC", "qC", "采集")
    before = bag_mats("gC", "qC")
    expire_event_now("gC", "qC")
    out2 = await cmd(m, "gather", "gC", "qC", "采集")  # 再次采集 → _prof_wait_flow 先读 residual
    after = bag_mats("gC", "qC")
    diff = sum(after.values()) - sum(before.values())
    check("再采集：旧轮结算文本带出", "采到了" in out2, out2[:200])
    check("再采集：背包 +1~2（旧轮产出不丢）", 1 <= diff <= 2, f"{before}→{after}")

    print("== Part 2D: 修复后——到点未结算 + 任意指令 refresh + 再采集 ===")
    await new_gather_player(m, "gD", "qD")
    out = await cmd(m, "gather", "gD", "qD", "采集")
    before = bag_mats("gD", "qD")
    expire_event_now("gD", "qD")          # 模拟重启/推送失败
    n = _te.refresh_timed("gD", "qD")     # 任意指令触发的 refresh（on_expire 保全数据）
    check("refresh_timed 清掉引擎过期事件", n == 1, f"n={n}")
    res = m._prof_wait_residual("gD", "qD")
    check("on_expire 把结算数据保全到遗留键（residual 可读）", res is not None, str(res))
    out2 = await cmd(m, "gather", "gD", "qD", "采集")  # 下一条副业指令 → 惰性结算旧轮
    after = bag_mats("gD", "qD")
    diff = sum(after.values()) - sum(before.values())
    check("修复后：旧轮产出入包（1~2 份）", 1 <= diff <= 2, f"{before}→{after}")
    check("修复后：旧轮提示语带出（采集=有东西）", "采到了" in out2, out2[:200])
    check("修复后：无双结算（结算后遗留键已清空）",
          db.get_event_state(m._prof_wait_key("gD", "qD")) in ("", None),
          str(db.get_event_state(m._prof_wait_key("gD", "qD"))))

import asyncio
asyncio.run(scenario())
print(f"\n结果: passed={passed} failed={failed}")
sys.exit(1 if failed else 0)