# -*- coding: utf-8 -*-
"""v134.7 验证：停服时『意见』放行；其他指令直接无视（不回复维护提示，静默 stop）。

宿主侧冒烟（`_maint_gate` = **平台门控面**），故留宿主。

★ T8（测试单源化）适配：
  · `conftest` / 内容侧夹具的**唯一真源 = 包仓那份 tests**（部署面
    `<plugin>/framework/games/*/tests`）⇒ 从这里取，宿主侧不再自留副本；
  · 平台名面（`data.plugins.<pkg>`）的 qqbot 根 + shim 目录走 `tests/_host_layout.py` 发现；
  · 删掉原先硬编码的三条 `C:\\Users\\yuyu\\qqbot\\...` —— 那是**另一棵树**（真仓），
    读到它 = 假绿（实测：旧写法下本冒烟跑的是真仓，不是 T8 副本）。
"""
import sys, os, asyncio
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from _host_layout import PLUGIN_DIR, QQBOT_DIR, SHIM_DIR, PKG_TESTS_DIRS  # noqa: E402

# 逐个 insert(0) ⇒ 列表**靠后**的排在 sys.path 越前：包仓那份 tests 最前（conftest 真源）。
for _p in ([os.path.join(PLUGIN_DIR, "framework"), PLUGIN_DIR, QQBOT_DIR, SHIM_DIR]
           + list(PKG_TESTS_DIRS)):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)
_PRIVATE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".private_dbs", "smoke_v1347_maint.db")
os.makedirs(os.path.dirname(_PRIVATE_DB), exist_ok=True)
os.environ["GWEN_GAME_DB"] = _PRIVATE_DB
os.environ["GWEN_TEST_MODE"] = "1"
from conftest import db, clean_db, Main, FakeEvent, run, make_player

async def _go():
    m = Main()
    G, Q = "g1", "u1"
    clean_db()
    make_player(G, Q, "测试玩家", "法师")

    # 停服
    db.set_event_state("server_maintenance", "1")
    db.set_event_state("server_maintenance_msg", "例行维护")
    print("=== 停服状态 ===")

    # ① 意见（应放行 → gate 不 stop，无输出，事件继续传播）
    ev = FakeEvent(G, Q, "意见 希望能出坐骑系统")
    out = await m._maint_gate(ev)
    print("① 意见 gate 放行:", "✅" if not ev._stopped else "❌ 被拦", "| 输出:", out)

    # ② 地图（应被拦且静默 → stop 且无任何输出）
    ev2 = FakeEvent(G, Q, "地图")
    out2 = await m._maint_gate(ev2)
    print("② 地图 gate 静默拦截:", "✅" if ev2._stopped and not out2 else f"❌ stop={ev2._stopped} out={out2}")

    # ③ 探索（应被拦且静默）
    ev3 = FakeEvent(G, Q, "探索")
    out3 = await m._maint_gate(ev3)
    print("③ 探索 gate 静默拦截:", "✅" if ev3._stopped and not out3 else f"❌ stop={ev3._stopped} out={out3}")

    # ④ 意见内容空（也应放行，进 feedback 提示格式）
    ev4 = FakeEvent(G, Q, "意见")
    out4 = await m._maint_gate(ev4)
    print("④ 空意见 gate 放行:", "✅" if not ev4._stopped else "❌ 被拦")

    # ⑤ 恢复开服
    db.set_event_state("server_maintenance", "0")
    ev5 = FakeEvent(G, Q, "地图")
    out5 = await m._maint_gate(ev5)
    print("⑤ 开服后 地图 gate 放行:", "✅" if not ev5._stopped else "❌ 被拦")

    # ⑥ 意见 走完整链路（停服时 feedback_cmd 能真正写入）
    db.set_event_state("server_maintenance", "1")
    r6 = await run(m.feedback_cmd, FakeEvent(G, Q, "意见 停服了也能提意见吗"))
    print("⑥ 停服中 意见完整链路:", "✅" if "收到" in r6[0] or "感谢" in r6[0] else f"❌ {r6}")

asyncio.run(_go())
