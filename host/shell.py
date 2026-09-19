# -*- coding: utf-8 -*-
"""QQ 宿主平台壳（`HostShell`）—— 引擎**通用半边** + 本平台的**真平台面**。

它是什么
--------
引擎 host 契约把「一条消息 → 引擎 `Env` → 包内 handler」打通；包内 handler 的**实现体**
仍需要一个「平台能力面」对象（包内一律经 `env.state["shell"]` 取它）。本文件是那只壳在
**QQ 宿主**上的落点：只写 QQ 专有的那一层。

| 面 | 来源 |
|---|---|
| 分页 / 页码 / 文本剥离 / 提示抽取 / handler 路由 / `_run_shortcut` | 引擎 `saintess_engine.command.base.CommandBase` |
| 取件管道（`bind_package` / `_sub` / `__getattr__` 按名解析）· 包内内容半边转发 · 环境位（GM 白名单 / 停服位） | 引擎 `saintess_engine.host.shell.ShellBase` |
| 渲染（句子） | **包内**（经 `ShellBase._sub` 取半边）—— 宿主零句子 |
| 平台动作：广播 / 通知 / 停服投递 / 身份映射 / 窥探投递 | **本文件** + `host/_platform.py` + `host/adapter_qq.py` |

零包知识口径（本文件为何一个包内模块字面量都没有）
--------------------------------------------------
plan §6⑨ ① 要求宿主里不出现包名 / `content.*`：包对象由装配处（`main.py` / 测试驱动口）经
配置给出，包内半边一律按**半边名**向 `Package.optional_submodule(name)` 取（引擎公开 API，
名字是契约里的半边名，不是模块路径）。

历史来源（逐条可查，不重写语义）
--------------------------------
`game/commands/base.py`（`CommandBase` 平台钩子 / `_maint_gate` / `_GameCmdFilter`）·
`game/commands/{player,world,combat,misc,social,gm,instance,instance_router}.py` 里**平台专有**的
少量方法（平台例外 5 条）。
★ 2026-09-20（T7 第 2 轮 · 编辑器试玩脱宿主）：通用那一半（取件管道 / 包内转发 / 环境位）
搬进引擎 `ShellBase` —— 试玩侧与 QQ 侧**同继承一份**，不再各抄一份（漂移源实测：试玩侧手搓壳
缺 `_bag_view`）。本文件随即只剩真平台面 8 个。
"""
from __future__ import annotations

import logging
import os
import re

from saintess_engine.host.shell import ShellBase, store_half   # noqa: F401（store_half 再导出：装配处取件口）
from saintess_engine.session import SessionAdapter

from . import _identity as _host_identity

LOG = logging.getLogger("astrbot")

# ============================================================
# 平台配置常量（`gm_窥探` 投递面）—— **流程实现已在包内** `content/cmds_gm.py::gm_spy`
# ------------------------------------------------------------
# 窥探的实录解析 / 拆角色卡 / 多卡投递流程在包内；壳侧只留 `gm_spy` 一条转发 + 本组
# **平台配置常量**，经 `_spy_ops()` 交给包内（与 `_identity_ops()` 同款「平台能力口」口径）。
# ============================================================
#: 窥探投递目标（运营号；环境变量可覆盖，换号不改代码）
GM_OWNER_QQ = (os.environ.get("GWEN_GM_QQ") or "1454832774").split(",")[0].strip()
#: 鱼鱼所在游戏群（`--群` 变体投递目标）
OWNER_GROUP = os.environ.get("GWEN_GM_GROUP") or "1095961596"
#: AstrBot 平台 id（**不是**适配器 type；用 aiocqhttp 前缀发送会返回 False 静默不发）
PLATFORM_PREFIX = "onebot_v11_qq"
#: playtest 交互实录目录（`playtest_spy_round{N}.md`，导出脚本轮末生成）
SPY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


class HostShell(ShellBase):
    """QQ 宿主壳：`env.state["shell"]`（装配处注入）；通用半边见 `ShellBase`。"""

    logger_name = "astrbot"

    def __init__(self, *, pkg=None, store=None, context=None, session=None,
                 events=None, finder=None):
        super().__init__(
            pkg=pkg, store=store, context=context, events=events, finder=finder,
            session=session or SessionAdapter(
                private_fallback="private", unknown_fallback="unknown",
                resolve_uid=lambda raw: _host_identity.resolve_uid(raw)))

    # ============================================================
    # 平台动作（广播 / 通知）—— 有 context 才真发，否则落记录
    # ============================================================
    async def _broadcast(self, text, exclude_group=None):
        groups = self._store.get_player_groups()
        if not groups:
            return
        for gid in groups:
            if exclude_group and str(gid) == str(exclude_group):
                continue
            await self._deliver(str(gid), str(text))

    async def _notify_hermes(self, group_id, qq_id, content, msg_type):
        await self._deliver(str(group_id), str(content))

    async def _deliver(self, group_id, text):
        self._events.append({"action": "say", "group_id": group_id, "text": text})
        if self.context is None:
            return
        try:
            from ._platform import MessageChain
            await self.context.send_message(
                "onebot_v11_qq:GroupMessage:%s" % group_id, MessageChain().message(text))
        except Exception as exc:                                 # noqa: BLE001
            LOG.warning("[dragonfall] 广播到群 %s 失败: %s", group_id, exc)

    # ============================================================
    # 平台能力口（包内 `_cap(shell, …)` 探测）
    # ============================================================
    def _identity_ops(self):
        """平台身份映射面（openid ⇄ QQ）——包内 GM 身份表的宿主能力口。"""
        return _host_identity

    def _spy_ops(self):
        """窥探投递平台面（实录目录 / 合并转发类型 / 投递目标 / 宿主日志）。

        包内 `content/cmds_gm.py::gm_spy` 经此取平台件（与 `_identity_ops()` 同款能力口）；
        壳侧不留流程实现。
        """
        from . import _platform as _pf
        return {"dir": SPY_DIR, "prefix": PLATFORM_PREFIX,
                "owner_qq": GM_OWNER_QQ, "owner_group": OWNER_GROUP,
                "Node": _pf.Node, "Plain": _pf.Plain,
                "Nodes": _pf.Nodes, "MessageChain": _pf.MessageChain,
                "log": LOG}

    # ============================================================
    # 平台例外 5 条（包内有声明、无处理器）
    # ============================================================
    async def _maint_gate(self, event):
        """停服 gate（逐字 = 原 `game/commands/base.py::_maint_gate`）。"""
        group_id, qq_id = self._uid(event)
        try:
            self._sub("timed_events").refresh_timed(group_id, qq_id)
        except Exception:                                        # noqa: BLE001
            LOG.warning("[timed_events] _maint_gate 刷新失败（不影响指令主流程）", exc_info=True)
        try:
            self._sub("wild_king").wild_king_tick()
        except Exception:                                        # noqa: BLE001
            pass
        try:
            self._sub("worlds").cleanup_stale_instances(24 * 3600)
        except Exception:                                        # noqa: BLE001
            pass
        if self._is_gm(qq_id):
            return None
        if self._server_down():
            text = (event.get_message_str() or "").strip()
            if re.match(r"^(?:\[At:[^\]]+\]\s*)?意见", text):
                return None
            event.stop_event()
            return None
        return None

    async def gm_play(self, event):
        """`gm_play <指令>`（平台例外）：转发包内实现。"""
        group_id, qq_id = self._uid(event)
        async for r in self._sub("cmds_gm").gm_play(self, event, group_id, qq_id):
            yield r

    async def gm_spy(self, event):
        """`gm_窥探`（平台例外）：转发包内实现。"""
        group_id, qq_id = self._uid(event)
        async for r in self._sub("cmds_gm").gm_spy(self, event, group_id, qq_id):
            yield r
