# -*- coding: utf-8 -*-
"""宿主壳 → **引擎 host 契约**的桥接层（B18 样板定形，2026-09-14）。属**平台适配**。

一条 AstrBot 命令事件 → 造引擎 `Env` → 跑声明里的守卫 → 调包内 handler → 文本段拼成一条消息。

```python
class WeeklyCmds(CommandBase):
    @declared("weekly_cmd")
    async def weekly_cmd(self, event):
        yield event.plain_result(_BRIDGE.run(self, "weekly_cmd", event))    # 宿主壳只剩这一行
```

零游戏知识（本模块的验收线）
----------------------------
不含任何**命令名 / 文案 key / 职业名 / 文案句子**：命令表、守卫文案、渲染全部来自包
（`content/commands.py::COMMANDS` · `content/guards.py::GUARDS` · `content/texts.py`）。
所以 P2 之后本模块可**整体提升进引擎**（作为「AstrBot 适配器示例」），宿主只剩 `main.py`
的装配 + 三函数适配器。

包面取件 = 引擎包契约（不是宿主自己认包）
------------------------------------------
`load_package()`（`saintess_engine.host`）拿 `Package` 对象 → `command_handlers()` /
`guard_hooks()` / `resolve_handler()`。包根来自宿主唯一包加载口 `bootstrap.package_apply()`
的返回模块（P5 改为「配置给」后本文件不必改：照样只吃「包根」这一个输入）。

`env.state["shell"] = <宿主壳对象>`
-----------------------------------
过渡期的**可选能力口**（`tower` 的 `_open_tower_battle` 在「开战装配」搬包前需要它，
与 B18a 的 `ctx.cap("<名字>")` 同源）；包内只 `getattr` 取可选方法，缺 → 走默认分支。
P2 后由引擎 `Host` 的能力口取代（届时本键可删）。
"""
from __future__ import annotations

import os
import random
import sys
import time

from saintess_engine.host import BUILTIN_GUARDS, Env, load_package, run_guards

from .. import db as _db

#: 插件根（`game/commands/_host_bridge.py` → 上两级）—— 两套 import 形态共用的落点
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_PKG = None                                   # 引擎包对象（幂等；本进程唯一）
_IDENTITY_KEYS = ("group_id", "qq_id", "uid")   # 「谁是玩家」那几列由落库函数自己带
#: handler 引用解析不到时的明确回话（`run` / `run_async` 共用；不静默吞）
_UNRESOLVED = "【%s】包内处理器未解析：%r（检查 content/commands.py 的 handler）"


def _host_inject() -> dict:
    """宿主注入面（P5A）—— 包在 `game.json` 声明了 `bind`，**给了 inject 才允许加载**
    （引擎 `Package.apply_bind`：声明了却不给 → `PackageError`，拒绝静默空跑）。

    值 = 宿主平台件（`host/store_factory.inject_handles()`：库路径 / 时钟 / 日志与流水 sink /
    发奖）。宿主**不解释**包怎么用这些对象，只按契约交出去；旧路径（`_host_bridge`）与新路径
    （`main.py::EngineChannel`）因此共用**同一份**注入口径。

    ⚠️ 本仓并存两套 import 形态（`data.plugins.dragonfall.game.*` 与顶层 `game.*`，见 plan §8-R2）
    ⇒ 按 `__package__` 推同前缀的 `host` 包名，**不写死包名**、不依赖相对点数。
    """
    import importlib
    if __package__:
        prefix = __package__[:-len("commands")].rstrip(".") if __package__.endswith(
            ".commands") else "game"
        name = prefix.rsplit(".", 1)[0] + ".host.store_factory" if "." in prefix else "host.store_factory"
    else:
        name = "host.store_factory"
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    return importlib.import_module(name).inject_handles()


def package():
    """引擎包对象（幂等）——宿主壳只经它读包面（不自己认包内模块名）。"""
    global _PKG
    if _PKG is None:
        from .. import bootstrap as _bootstrap
        apply_mod = _bootstrap.package_apply()          # 幂等；失败大声抛（不静默降级）
        root = os.path.dirname(os.path.dirname(os.path.abspath(apply_mod.__file__)))
        _PKG = load_package(root, inject=_host_inject())   # ★ inject 由宿主给（包声明了 bind）
    return _PKG


def _save_player(group_id, qq_id, player: dict) -> None:
    """`env.save()` 的落地：整档回写（一条消息一次）。字段非法 → `update_player` 当场抛
    （fail-closed：宁可报错，不静默写坏档）。"""
    fields = {k: v for k, v in (player or {}).items() if k not in _IDENTITY_KEYS}
    if fields:
        _db.update_player(group_id, qq_id, **fields)


def _guard_hint(hooks: dict, name: str, env: Env):
    """内置守卫的拦截文案 —— 取**包侧** `content/guards.py::GUARDS[name]`（文案属内容）。"""
    fn = hooks.get(name) if isinstance(hooks, dict) else None
    if not callable(fn):
        return None
    return fn(env, env.player) or None


def _prepare(host_shell, key: str, event):
    """造 `Env` + 跑声明守卫 —— `run`（同步命令）与 `run_async`（战斗族异步命令）**共用**。

    返回 `(pkg, entry, env, blocked)`：`blocked` 非空 = 守卫拦截回话（调用方直接回话，不再调 handler）。
    行为逐字 = 改造前 `run` 的前半段（`hooks` 只取一次，值相同）。
    """
    pkg = package()
    group_id, qq_id = host_shell._uid(event)
    player = host_shell._player(group_id, qq_id)
    entry = dict(pkg.command_handlers().get(key) or {})
    env = Env(
        key=str(key or ""),
        uid=str(qq_id),
        group_id=str(group_id),
        text=(event.get_message_str() or "").strip(),
        raw=event,                                     # 平台事件原样透传（包内禁解释）
        player=player if isinstance(player, dict) else {},
        clock=time.time,
        rng=random,
        texts=None,                                    # 渲染在包内 `content/texts.py`（宿主 SPEC_PATH 已注入）
        state={"shell": host_shell},                   # 过渡期可选能力口（见模块头注）
    )
    env.save = lambda: _save_player(group_id, qq_id, env.player)
    # 守卫：声明在包（`COMMANDS[key]["guards"]`）—— 判定与**文案**都取包侧
    # （`hook:<名>` → `content/guards.py::GUARDS`）。引擎内置名（player/battle）只做兜底转发：
    # 判定照旧，拦截文案仍取包侧同名钩子（宿主里不留任何游戏文案）。
    hooks = pkg.guard_hooks()
    builtin = {name: (lambda e, _n=name: _guard_hint(hooks, _n, e)) for name in BUILTIN_GUARDS}
    blocked = run_guards(entry.get("guards") or (), env, builtin=builtin, hooks=hooks)
    return pkg, entry, env, blocked


def run(host_shell, key: str, event) -> str:
    """把一条宿主命令事件桥到引擎 host 契约，返回**一条**已渲染消息（宿主直接 plain_result）。"""
    pkg, entry, env, blocked = _prepare(host_shell, key, event)
    if blocked:
        return blocked                                 # 守卫拦截（文案来自包侧）
    fn = pkg.resolve_handler(entry.get("handler"))
    if fn is None:                                     # 坏引用 → 明确回话（不静默吞）
        return _UNRESOLVED % (key, entry.get("handler"))
    out = fn(env)
    return "\n".join(str(x) for x in (out or ()) if x is not None)


async def run_async(host_shell, key: str, event):
    """**逐段回话**的桥（B18 L3c 战斗族：处理器是 `async def fn(env) -> list[str]`）。

    与 `run` 同一套 `Env` / 守卫 / handler 解析（`_prepare`）；差别只有两点：

      · `fn(env)` 若返回 awaitable → `await`（战斗族实现体是 async generator，命令体 async）；
      · 返回的 `list[str]` **逐元素 yield**（一条 = 一条消息）—— 对齐改造前
        `async for _r in _CC.<cmd>(...): yield _r` 的逐条语义，**不做 `"\\n".join` 合并**
        （分支/异常提示的行序与消息切分逐字节保留）。

    宿主壳用法（每条命令两行）：:

        @declared("attack")
        async def attack(self, event):
            async for _r in _BRIDGE.run_async(self, "attack", event):
                yield _r
    """
    pkg, entry, env, blocked = _prepare(host_shell, key, event)
    if blocked:
        yield blocked                                  # 守卫拦截（文案来自包侧）
        return
    fn = pkg.resolve_handler(entry.get("handler"))
    if fn is None:                                     # 坏引用 → 明确回话（不静默吞）
        yield _UNRESOLVED % (key, entry.get("handler"))
        return
    out = fn(env)
    if hasattr(out, "__await__"):                      # async handler（战斗族）
        out = await out
    for x in (out or ()):
        if x is not None:
            yield str(x)
