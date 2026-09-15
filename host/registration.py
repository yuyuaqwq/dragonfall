# -*- coding: utf-8 -*-
"""宿主侧「声明 → AstrBot 注册」驱动（R3）—— **注册动作的唯一落点**。

为什么要有这个文件（P5C 报的结构性卡点 A）
------------------------------------------
删掉宿主 `game/commands/**` 之后，`import ...main` 照样通过，但 AstrBot 注册表里本插件的
指令 handler **194 → 0** —— 玩家所有消息掉进 LLM 兜底，机器人**静默哑掉**。根因是注册动作
本身长在待删树里（`game/commands/_declared.py` 的 `@declared` 装饰器）。本文件把注册动作
收进宿主：**声明表仍是包内唯一真源**（引擎 `Package.command_declarations()`），宿主只负责
「把每条声明接成平台 handler」。

职责边界（零包知识）
--------------------
* 不读任何包内文件路径、不出现包名 / 包内模块路径 / 待删壳模块名；包只以引擎 `Package`
  对象进来（`command_declarations()` / `command_handlers()` / `resolve_handler()`）。
* 平台面只经本包的 `host/_platform.py`（`register_regex` / `register_custom_filter` 会
  双注册进 AstrBot 注册表）。
* 「一条声明怎么执行」不在本文件：由装配处（`main.py`）经 `bind_dispatcher()` 注入
  `(key, event) -> list[str]`（引擎 host 通道）。默认 handler factory 只做「取段 → 按旧壳
  的消息切分口径投递」。

一条声明的 handler 形状（与旧壳注册**可观察行为一致**）
-------------------------------------------------------
旧路径（`game/commands/**`，待删）每条命令两种桥之一：

* **同步族**（包内处理器是普通函数）：`yield event.plain_result(_BRIDGE.run(...))`
  —— 多段 `"\\n".join` 成**一条**回话；
* **异步族**（包内处理器是 `async def`）：`async for _r in _BRIDGE.run_async(...): yield _r`
  —— **逐段**回话。

P5B/本批当次实测（`out/_probe/probe_framing.log`）：194 条声明里 189 条被旧壳源码分类，
「旧壳选哪只桥」与「包内 handler 是不是 coroutine」**0 处不一致**；剩下 5 条正是平台例外
（`_maint_gate` + 4 条转发型），由本驱动显式处理。故默认 factory 用同一条规则推切分口径，
不抄任何 key 名单。

fail-closed
-----------
声明表为空 / 声明缺正则 / 正则非法 / 没装 dispatcher → **抛**（`RegistrationError`）。
绝不允许「配了不生效」这种最难查的静默坏态（本文件的存在理由）。
"""
from __future__ import annotations

import inspect
import logging
import re

from saintess_engine.command import CommandSpec

from . import _platform
#: 平台例外（包内有声明、宿主实现）——键名真源 = 适配器（同一处定义，别抄第二份）
from .adapter_qq import GATE_KEY, PLATFORM_ROUTES

LOG = logging.getLogger("astrbot")

__all__ = [
    "RegistrationError", "bind_dispatcher", "register_from_declarations",
    "reset_plugin_handlers", "declaration_count", "declaration_patterns",
    "static_handlers", "is_game_command",
]


class RegistrationError(RuntimeError):
    """注册不可能正确完成（声明表空 / 正则非法 / 没装 dispatcher）——拒绝静默降级。"""


# ============================================================
# 执行面：装配处注入的 dispatcher（引擎 host 通道）
# ============================================================
_DISPATCHER = None
#: 最近一次注册用到的声明正则池 `[(key, 合并正则), …]`（`is_game_command` 用；注册时刷新）
_PATTERNS = []


def bind_dispatcher(fn) -> None:
    """装配处登记「跑一条声明」的驱动口（`main.py` 的引擎通道）。

    `fn(key, event)` → 该条声明的回话段（`list[str]`；平台 gate 无回话 = `[]`）。
    不给 dispatcher 就调 `register_from_declarations` → 抛（见 `RegistrationError`）。
    """
    global _DISPATCHER
    if not callable(fn):
        raise RegistrationError("bind_dispatcher 只收可调用对象，收到 %r" % (fn,))
    _DISPATCHER = fn


def _dispatcher():
    if _DISPATCHER is None:
        raise RegistrationError(
            "注册驱动没有执行面：装配处必须先 bind_dispatcher(fn)（引擎 host 通道）——"
            "否则注册出来的 handler 是空壳，玩家消息会静默掉进 LLM 兜底")
    return _DISPATCHER


# ============================================================
# 包声明 → 声明项
# ============================================================
def _declarations(pkg) -> dict:
    """包内声明表（引擎 `Package.command_declarations()`）；空 → 抛（fail-closed）。"""
    if pkg is None:
        raise RegistrationError("register_from_declarations 需要一个引擎 Package（收到 None）")
    decls = pkg.command_declarations() or {}
    if not isinstance(decls, dict) or not decls:
        raise RegistrationError(
            "包内声明表为空（引擎 Package.command_declarations() 返回 %r）——"
            "拒绝注册 0 条 handler（那等于把机器人静默弄哑）" % (type(decls).__name__,))
    return decls


def declaration_count(pkg) -> int:
    """包内声明条数（= 期望注册条数）。"""
    return len(_declarations(pkg))


def _spec_of(key: str, raw) -> CommandSpec:
    """一条原始声明 → `CommandSpec`（引擎形状；缺正则 → 抛）。"""
    if isinstance(raw, CommandSpec):
        spec = raw
    else:
        data = dict(raw) if isinstance(raw, dict) else {"patterns": (raw,)}
        data.setdefault("key", key)
        spec = CommandSpec.from_dict(data)
    if not spec.patterns:
        raise RegistrationError("声明 %r 没有正则（patterns 为空）——拒绝注册空壳 handler" % key)
    return spec


def _compile(spec: CommandSpec):
    pat = spec.combined()
    try:
        re.compile(pat)
    except re.error as exc:
        raise RegistrationError("声明 %r 的正则非法：%s（%r）" % (spec.key, exc, pat)) from exc
    return pat


# ============================================================
# 消息切分口径（同步族 / 异步族）
# ============================================================
def _unwrap_handler(fn):
    """取回 `register()` 包住的真实现（包内 `content/commands.py::register` 约定）。

    包内命令表把 handler 包成 `(lambda env, _fn=fn: render_panel(_fn(env), env))`，
    真实现藏在 lambda 默认参数里 —— 判断「是不是协程」必须拆到那一层。
    """
    seen = 0
    while (callable(fn) and getattr(fn, "__name__", "") == "<lambda>"
           and fn.__defaults__ and seen < 3):
        nxt = fn.__defaults__[0]
        if not callable(nxt):
            break
        fn = nxt
        seen += 1
    return fn


def _async_family(pkg, key: str) -> bool:
    """该声明在旧壳里属于异步族吗（= 包内处理器是 coroutine）。"""
    try:
        entry = dict((pkg.command_handlers() or {}).get(key) or {})
    except Exception:                                            # noqa: BLE001
        return False
    fn = _unwrap_handler(pkg.resolve_handler(entry.get("handler")))
    return bool(fn) and inspect.iscoroutinefunction(fn)


def _make_handler(key: str, spec: CommandSpec, *, async_family: bool):
    """默认 handler factory：一条声明 → AstrBot handler（可观察行为照旧壳）。"""
    if key == GATE_KEY:
        async def _gate(self, event):                            # noqa: ANN001
            _dispatcher()(key, event)                            # 平台 gate：无回话（dispatcher 同步）
        _gate.__name__ = key
        _gate.__doc__ = spec.desc or ""
        return _gate

    async def _handler(self, event):                             # noqa: ANN001
        segments = _dispatcher()(key, event) or []
        if isinstance(segments, str):
            segments = [segments]
        if async_family:
            for seg in segments:                                 # 旧壳异步族：逐段
                yield seg
        else:
            yield event.plain_result("\n".join(str(s) for s in segments))

    _handler.__name__ = key
    _handler.__doc__ = spec.desc or ""
    return _handler


# ============================================================
# 注册表接管（幂等 + 单注册者）
# ============================================================
def _registries() -> list:
    """所有「指令 handler 注册表」：AstrBot 真表（分发真源）+ 本包平台面表。"""
    out = []
    try:
        from astrbot.core.star.star_handler import star_handlers_registry as _reg
    except Exception:                                            # noqa: BLE001
        _reg = None
    if _reg is not None:
        out.append(_reg)
    if _platform.star_handlers_registry is not _reg:
        out.append(_platform.star_handlers_registry)
    return out


def _plugin_prefix(module_path: str) -> str:
    text = str(module_path or "")
    if "." not in text:
        return text
    return text.rsplit(".", 1)[0] + "."


def reset_plugin_handlers(module_path: str) -> int:
    """注销**本插件**已注册的指令 handler（幂等取代表；返回清理条数）。

    为什么需要它：本批是「过渡态」——`game/commands/**` 的 `@declared` 装饰器仍在
    import 期注册 194 条旧 handler。AstrBot 会**激活所有 filter 命中的 handler**，
    两份并存 = 每条消息跑两遍（或旧的那份因 `star_map` 查不到而被跳过并刷警告）。
    故注册驱动在注册前先做「接管」：本插件名下旧 handler 一律清掉，保证**同一时刻只有
    一套、且是新驱动那套**。删壳（P5C）之后这里命中 0 条，行为不变。
    """
    prefix = _plugin_prefix(module_path)
    exact = str(module_path or "")
    if not prefix:
        raise RegistrationError("reset_plugin_handlers 需要一个模块路径（收到 %r）" % (module_path,))
    removed = 0
    for reg in _registries():
        handlers = getattr(reg, "_handlers", None)
        if handlers is None:
            continue
        def _mine(md):
            path = str(getattr(md, "handler_module_path", "") or "")
            return path == exact or path.startswith(prefix)
        keep = [md for md in handlers if not _mine(md)]
        removed += len(handlers) - len(keep)
        handlers[:] = keep
        # 真 AstrBot 还有 full_name → metadata 的索引表，一并清掉（否则残留旧引用）
        index = getattr(reg, "star_handlers_map", None)
        if isinstance(index, dict):
            for full in [k for k, md in index.items() if _mine(md)]:
                index.pop(full, None)
    return removed


# ============================================================
# ★ 主入口：声明 → 平台注册
# ============================================================
def register_from_declarations(pkg, *, handler_factory=None, module_path=None) -> int:
    """遍历包内声明表，逐条注册 AstrBot 正则 handler。**返回注册条数**。

    参数
    ----
    pkg              引擎 `Package`（声明真源 = `pkg.command_declarations()`）
    handler_factory  `(key, spec) -> callable(self, event)`；缺省 = 本文件默认口径
                     （引擎 host 通道 + 旧壳消息切分）
    module_path      本插件主模块路径（AstrBot `star_map` 按它精确关联插件实例）。
                     给了 → 写进每个 handler 的 `__module__`，注册表里就是可绑定的。

    失败绝不静默：声明表空 / 正则非法 / 缺 dispatcher → `RegistrationError`。
    """
    decls = _declarations(pkg)
    factory = handler_factory
    if factory is None:
        _dispatcher()                                            # 没执行面就别注册
        factory = lambda key, spec: _make_handler(              # noqa: E731
            key, spec,
            # 平台例外四条在旧壳里都是 async generator（逐段 yield）；其余按包内处理器是否协程
            async_family=(key in PLATFORM_ROUTES) or _async_family(pkg, key))

    global _PATTERNS, _GAME_CMD_PATTERNS
    _PATTERNS = [(k, _spec_of(k, v).combined()) for k, v in decls.items()]
    _GAME_CMD_PATTERNS = None                                    # 声明变了 → 旧正则池作废

    count = 0
    for key, raw in decls.items():
        spec = _spec_of(key, raw)
        pattern = _compile(spec)
        handler = factory(key, spec)
        if not callable(handler):
            raise RegistrationError("handler_factory 对 %r 返回了不可调用对象：%r" % (key, handler))
        if module_path:
            handler.__module__ = str(module_path)
        if key == GATE_KEY:
            # 停服 gate：声明正则（匹配所有消息）+ 「是不是游戏指令」自定义过滤（AND 语义）
            _platform.register_custom_filter(_platform._GameCmdFilter, priority=spec.priority)(handler)
            _platform.register_regex(pattern, priority=spec.priority)(handler)
        else:
            _platform.register_regex(pattern, priority=spec.priority)(handler)
        count += 1
    LOG.info("注册驱动：%d 条声明 → AstrBot handler（module_path=%s）", count, module_path)
    return count


# ============================================================
# 派生面：平台 filter / 静态表 / 「是不是游戏指令」
# ============================================================
def declaration_patterns(pkg) -> list:
    """`[合并正则, …]`（每条声明一条）——**「怎样算一条游戏指令」的唯一池子**。"""
    specs = [_spec_of(k, v) for k, v in _declarations(pkg).items()]
    return [s.combined() for s in specs]


def static_handlers(pkg) -> list:
    """`[(已编译正则, key), …]` —— 引擎 `CommandBase._find_handler` 的静态兜底表。"""
    out = []
    for key, raw in _declarations(pkg).items():
        spec = _spec_of(key, raw)
        for pat in spec.patterns:
            try:
                out.append((re.compile(pat), key))
            except re.error:
                continue
    return out


_GAME_CMD_PATTERNS = None


def _game_cmd_patterns() -> list:
    """懒编译的「游戏指令正则」池（注册时刷新 ⇒ 改声明表要重新注册）。

    平台 gate 的声明正则（全可选、匹配一切）**不参与**判定 —— 它消费不了任何字符，
    拿它判「是不是游戏指令」会把所有消息都算成指令（v134.1 的既有口径）。
    """
    global _GAME_CMD_PATTERNS
    if _GAME_CMD_PATTERNS is None:
        compiled = []
        for key, pat in _PATTERNS or ():
            if key == GATE_KEY:
                continue
            try:
                compiled.append(re.compile(pat))
            except re.error:
                continue
        _GAME_CMD_PATTERNS = compiled
    return _GAME_CMD_PATTERNS


def is_game_command(msg: str) -> bool:
    """消息是否为本插件能处理的游戏指令（AstrBot RateLimitStage 的判定口）。

    逐条 `re.match`（与注册 filter 的 `search` 语义同池），要求**至少消费 1 字符**
    （排除 `_maint_gate` 那种全可选 pattern）；纯数字/全角数字（快捷绑定 / 赶路序号）
    也算游戏指令。声明池为空（未注册）→ False（fail-safe：不误伤普通聊天）。
    """
    if not msg:
        return False
    if re.match(r"^[0-9０-９]+\s*$", msg):
        return True
    for rx in _game_cmd_patterns():
        try:
            m = rx.match(msg)
        except re.error:
            continue
        if m and m.end() > 0:
            return True
    return False
