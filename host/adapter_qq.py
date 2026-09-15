# -*- coding: utf-8 -*-
"""QQ 平台适配器（P5A ★ 契约实现）—— 三函数 + 可选钩子 + 平台 gate。

契约本体（`docs/engine-wiki/reference/host-api.md`）
---------------------------------------------------
```python
recv() -> ctx | None                     ① 取一条消息；None = 没有新消息（循环自旋）
load_player(uid) -> dict | None          ② 读档；None = 新玩家
save_player(uid, data) -> None           ② 写档：一条消息一次（改完必存）
say(to, text) -> None                    ③ 回话：to={"uid","group_id"}；text 已渲染
```
`ctx` 七字段（多给忽略）：`uid` · `text` · `group_id` · `is_group` · `at[]` · `ts` · `raw`

可选钩子（不给也能跑）：`clock()` · `rng()` · `on_tlog(record)` · `load_blob`/`save_blob` ·
`on_event(name, payload)` · `should_stop()`。

接缝纪律（不可谈判）
--------------------
包内**只拿普通 dict 进来、只交普通 dict 出去**；序列化 / 并发锁 / 落库 / 迁移全在适配器侧
（→ `host/store_factory.py` 的存档口）。适配器**零游戏知识**：不认识任何指令名 / 文案 / 表名。

平台例外（§11.3 五条：`_maint_gate` · `gm_play` · `gm_spy` · `shortcut_trigger` · `page_flip`）
----------------------------------------------------------------------------------------------
这五条**不是包的职责**（包内既无处理器也不应有），终态由适配器实现：

* `_maint_gate` → **适配器 gate**：每条消息路由**之前**跑一次（停服拦截 + 惰性刷新；
  被拦 = `stop_event` → 本次不再路由、不产出回话）；
* 其余四条 → **平台命令派发**：命中包内**声明**（含不可见声明；包内没有处理器）时，由适配器
  交给宿主壳的**平台实现**执行；平台实现内部的「转发另一条指令」经宿主壳 `_run_shortcut`
  改走**引擎通道**（`Host.handle`）—— 见 `main.py::EngineShell`。

运行期取事件队列
----------------
真 QQ 接入时由 AstrBot handler `push(event)` 后取；测试 / loopback 由驱动方
`push(external_event)`。`run_sync()` 给「引擎是同步的、包内一部分 handler 是 async」这一
现实提供**唯一**的落地方式（引擎侧不改；编辑器试玩通道同款先例）。
"""
from __future__ import annotations

import asyncio
import collections
import random
import re
import time

from . import _identity
from . import store_factory as _sf

#: 平台 @ 标记（`[At:123]` / `[At:全体成员]`；`<at id=...>` 备用）
_AT_RE = re.compile(r"\[At:([^\]]*)\]\s*|<at[^>]*>")
#: 平台投递前缀（AstrBot 平台 id，不是适配器 type —— v101.28q 实测教训）
PLATFORM_PREFIX = "onebot_v11_qq"

#: 平台例外命令（包内**声明**、宿主**实现**；终态由适配器负责）
PLATFORM_KEYS = ("_maint_gate", "gm_play", "gm_spy", "shortcut_trigger", "page_flip")
#: 其中「需要路由到平台实现」的四条（`_maint_gate` 是每条消息的 gate，不参与路由）
PLATFORM_ROUTES = ("gm_play", "gm_spy", "shortcut_trigger", "page_flip")
#: 停服 gate 的声明 key（每条消息路由**之前**跑一次；不参与命令路由）
GATE_KEY = "_maint_gate"


# ============================================================
# 同步/异步桥（引擎 host 是同步的；包内战斗族 handler 与平台命令是 async）
# ============================================================
_LOOP = asyncio.new_event_loop()


def run_sync(awaitable):
    """把一个协程 / async generator 跑到完成，返回结果（`list` 或值）。

    * 本线程没有运行中的 loop，且私有 loop 空闲 → 直接 `run_until_complete`（零额外线程）；
    * 否则（已在 loop 里 / 私有 loop 正忙，例如 async handler 里再转发指令）→ 交给临时线程
      自带的新 loop 跑，避免「This event loop is already running」。
    """
    try:
        asyncio.get_running_loop()
        busy = True
    except RuntimeError:
        busy = _LOOP.is_running()
    if busy:
        return _run_in_thread(awaitable)
    return _LOOP.run_until_complete(_drive(awaitable))


async def _drive(awaitable):
    """协程 → 结果；async generator → 收成 list（逐段 yield 语义）。"""
    if hasattr(awaitable, "__anext__"):
        out = []
        async for item in awaitable:
            out.append(item)
        return out
    if hasattr(awaitable, "__await__"):
        return await awaitable
    return awaitable


def _run_in_thread(awaitable):
    import threading

    box = {}

    def _worker():
        loop = asyncio.new_event_loop()
        try:
            box["value"] = loop.run_until_complete(_drive(awaitable))
        except BaseException as exc:                             # noqa: BLE001
            box["error"] = exc
        finally:
            loop.close()

    t = threading.Thread(target=_worker, daemon=True, name="engine-channel-await")
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box.get("value")


# ============================================================
# 适配器
# ============================================================
class QQAdapter:
    """AstrBot / QQ 平台的契约实现（三函数 + 钩子 + 平台 gate / 平台命令派发）。"""

    def __init__(self, *, store=None, shell=None, context=None, id_key="uid",
                 sink=None, seed=None, name="qq"):
        self.store = store if store is not None else _sf.store()
        self.shell = shell                 # 宿主壳（`env.state["shell"]`；平台命令实现处）
        self.context = context             # 平台发送面（AstrBot context / 测试记录器）
        self.id_key = str(id_key or "uid")
        self.name = name
        self.seed = seed
        self._sink = sink                  # 回话出口覆盖（loopback / 测试用）
        self._inbox = collections.deque()  # 平台事件队列（`push` → `recv`）
        self._cur = None                   # 当前 ctx（load/save/say 的上下文）
        self._collectors = []              # `say` 收集栈（收集模式；对拍 / loopback）
        self._pkg = None                   # 引擎 Package（声明表 / 存档半边的来源）
        self._host = None
        self._blobs: dict = {}
        self._tlogs: list = []
        self._events: list = []
        self._stop = False

    # ---------- 装配 ----------
    def attach(self, *, pkg=None, host=None, shell=None, context=None) -> "QQAdapter":
        if pkg is not None:
            self._pkg = pkg
        if host is not None:
            self._host = host
        if shell is not None:
            self.shell = shell
        if context is not None:
            self.context = context
        return self

    # ---------- 回话收集（loopback / 对拍：把 `say` 收成 list）----------
    def collecting(self, out: list):
        """上下文管理器：期间 `say()` 的段进 `out`（可嵌套）。"""
        return _Collector(self, out)

    # ============================================================
    # ① recv：平台事件 → ctx 七字段
    # ============================================================
    def push(self, event) -> None:
        """把一条平台事件放进队列（AstrBot handler / 测试驱动调用）。"""
        self._inbox.append(event)

    def recv(self):
        """取一条消息；`None` = 没有新消息（引擎 `serve_forever` 自旋）。"""
        if not self._inbox:
            return None
        event = self._inbox.popleft()
        ctx = self.to_ctx(event)
        self.begin(ctx)
        return ctx

    def to_ctx(self, event, text=None) -> dict:
        """平台事件 → ctx 七字段（@ 标记 / 群私聊 / 时间戳都在这吸收）。

        `text` 显式给出时（快捷转发/翻页重建的指令文本）原样使用；否则从事件消息里
        **剥掉 @ 标记**（id 落 `at`）后 strip。
        """
        raw_msg = event.get_message_str() or ""
        at = [m for m in _AT_RE.findall(raw_msg) if m]
        if text is None:
            text = _AT_RE.sub("", raw_msg).strip()
        gid = event.get_group_id()
        group_id = str(gid) if gid else "private"
        sender = event.get_sender_id() or "unknown"
        return {
            "uid": str(_identity.resolve_uid(str(sender)) or sender),
            "text": str(text),
            "group_id": group_id,
            "is_group": bool(gid),
            "at": at,
            "ts": float(self.clock()),
            "raw": event,
        }

    def begin(self, ctx: dict) -> None:
        """声明「当前正在处理哪条消息」（`load_player`/`save_player` 的群上下文）。"""
        self._cur = ctx or {}

    def current(self) -> dict:
        return self._cur or {}

    # ============================================================
    # ② load_player / save_player（形状 = 普通 dict）
    # ============================================================
    def load_player(self, uid):
        group_id = str((self._cur or {}).get("group_id") or "private")
        return self.store.load_player(group_id, str(uid))

    def save_player(self, uid, data) -> None:
        group_id = str((self._cur or {}).get("group_id") or "private")
        if not isinstance(data, dict):
            raise TypeError("save_player 只收普通 dict（包内接缝纪律）")
        self.store.save_player(group_id, str(uid), data)

    # ============================================================
    # ③ say（text 已渲染）
    # ============================================================
    def say(self, to, text) -> None:
        """回话出口（`text` 已渲染）。

        空串段 = 包内**排版空行**（`raw("")`）：**收集面保真**（对拍 / loopback 需要它），
        **平台面不空发**（不往群里丢空消息）。二者语义差异写在这里，不留隐式行为。
        """
        text = "" if text is None else str(text)
        if self._collectors:
            self._collectors[-1].append(text)
            return
        if not text:
            return
        if self._sink is not None:
            self._sink(to, text)
            return
        if self.context is None:
            raise RuntimeError(
                "适配器 say()：没有回话出口（既无收集器 / sink，也没有平台 context）——拒绝静默丢消息")
        from ._platform import MessageChain           # 平台面（宿主自己的类型）
        group_id = (to or {}).get("group_id")
        if group_id:
            target = "%s:GroupMessage:%s" % (PLATFORM_PREFIX, group_id)
        else:
            openid = _identity.qq_to_openid(str((to or {}).get("uid") or ""))
            target = "%s:FriendMessage:%s" % (PLATFORM_PREFIX, openid or (to or {}).get("uid"))
        run_sync(self.context.send_message(target, MessageChain().message(text)))

    # ============================================================
    # 可选钩子（契约 §二）
    # ============================================================
    def clock(self) -> float:
        return time.time()

    def rng(self):
        return random.Random(self.seed)

    def on_tlog(self, record: dict) -> None:
        """流水出口（宿主侧落点 = `host.tlog_setup`；未启用 → 零行为）。"""
        self._tlogs.append(dict(record or {}))
        from . import tlog_setup as _tlog
        kind = str((record or {}).get("kind") or "")
        if not kind:
            return
        fields = {k: v for k, v in (record or {}).items() if k != "kind"}
        _tlog.emit(kind, actor=str(fields.pop("actor", "") or ""), **fields)

    def load_blob(self, key):
        """额外持久化（组队 / 世界状态这类）。本包未使用 → 进程内 dict（契约缺省口径）。"""
        return self._blobs.get(key)

    def save_blob(self, key, value) -> None:
        self._blobs[key] = value

    def on_event(self, name, payload) -> None:
        self._events.append((str(name), payload))

    def should_stop(self) -> bool:
        return bool(self._stop)

    def stop(self) -> None:
        self._stop = True

    # ============================================================
    # 平台例外五条（适配器职责）
    # ============================================================
    def declarations(self) -> dict:
        """包内指令**声明**表（`content/data/commands.json`；引擎契约面）。"""
        if self._pkg is None:
            raise RuntimeError("适配器未绑定引擎 Package（`attach(pkg=…)`）——拒绝静默无声明可路由")
        return self._pkg.command_declarations() or {}

    def route_plan(self, text: str):
        """适配器路由判定：**引擎可见路由之外的那一半**（§11.3「不可见声明是适配器职责」）。

        排序口径与引擎**同源**（`host.commands.hits` = `priority` 降序、同值按注册序，唯一实现），
        所以「谁胜出」在两条通道里是同一件事。三种结论：

        * `("platform", spec)` —— 胜出者是**平台例外**四条之一（`gm_play` / `gm_spy` /
          `shortcut_trigger` / `page_flip`）：包内没有也不应有处理器 → 适配器派发；
          ⚠️ 只有**胜出**才派发（例：`1` 被 `npc_quick_dialog`（priority 100）压过 → 仍走引擎）。
        * `("invoke", spec)` —— 胜出者是**不可见声明**（GM 族等）：引擎的可见路由不认它
          （`declared_hit(visible_only=True)`），但玩家发得出来 → 适配器按同一声明交回
          **包内处理器**（`Host.invoke`）。
        * `None` —— 可见且非例外 → 原样交给引擎 `Host.handle`（包含 `_maint_gate` 这类
          全匹配 gate：它已由 `gate()` 处理，这里不是"路由不到的兜底"）。
        """
        if not (text or "").strip() or self._host is None:
            return None
        for spec in self._host.commands.hits(text):    # 含不可见；priority 降序、同值按注册序
            key = str(getattr(spec, "key", "") or "")
            if key == GATE_KEY:
                continue                               # gate 已由 `gate()` 消费（不是命令）
            if key in PLATFORM_ROUTES:
                return ("platform", spec)
            if not getattr(spec, "visible", True):
                return ("invoke", spec)
            return None                                # 可见且非例外 → 引擎可见路由
        return None

    def gate(self, ctx: dict) -> bool:
        """平台 gate（`_maint_gate`）：每条消息路由**之前**跑一次。

        返回 True = 本次消息被拦（`stop_event` 语义：不再路由、不产出回话）。
        实现在宿主壳上（`game/commands/base.py::_maint_gate`：停服拦截 + 惰性刷新），
        本批**复用不重写**；P5C 随壳迁进 `host/**`。
        """
        event = (ctx or {}).get("raw")
        if event is None or self.shell is None:
            return False
        run_sync(self.shell._maint_gate(event))
        return bool(getattr(event, "_stopped", False) or getattr(event, "stopped", False))

    def platform_replies(self, key: str, ctx: dict) -> list:
        """平台例外命令 → **宿主壳实现**（`gm_play` / `gm_spy` / `shortcut_trigger` / `page_flip`）。

        它们进不了引擎的包内处理器表（包内没有、也不应有处理器）；内部「转发另一条指令」
        经宿主壳 `_run_shortcut` 改走**引擎通道**（`main.py::EngineShell` 覆盖）。
        """
        event = (ctx or {}).get("raw")
        if event is None or self.shell is None:
            raise RuntimeError("平台命令 %r 缺平台事件 / 宿主壳 ——拒绝静默空跑" % key)
        fn = getattr(self.shell, key, None)
        if not callable(fn):
            raise RuntimeError("平台命令 %r 在宿主壳上无实现（%r）" % (key, type(self.shell).__name__))
        out = run_sync(fn(event))
        if out is None:
            return []
        if isinstance(out, str):
            return [out] if out else []
        return [str(x) for x in out if x is not None]


class _Collector:
    """`say` 收集上下文（`with adapter.collecting(out): …`）。"""

    def __init__(self, adapter: QQAdapter, out: list):
        self.adapter = adapter
        self.out = out

    def __enter__(self):
        self.adapter._collectors.append(self.out)
        return self.out

    def __exit__(self, *exc):
        self.adapter._collectors.pop()
        return False
