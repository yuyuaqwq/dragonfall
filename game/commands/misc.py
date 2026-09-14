# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - misc（misc）★ B18-L1 终态：**一行转发**

『帮助』『游戏提示』『签到』『成就』『意见』的**守卫 / 取参 / 分支业务 / 面板行序 / 渲染全在包内**
（`content/cmds_misc.py` 登记进 `content/commands.py::COMMANDS`；文案走包内 `content/texts.py`）。
本模块只剩两件事：

  ① **注册**：`@declared("<key>")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "<key>", event)` —— 桥到引擎 host 契约（造 `Env` → 守卫
     → 包内 handler → 一条成品文本）

宿主里**零** 文案调用点（`grep -c 'T\.text\|T\.static' game/commands/misc.py` = 0）。
宿主侧**故意保留**两处（都是宿主侧真源，非遗漏）：

  · `CMD_HELP*` 十一份面板类属性 —— `tests/test_v104_commands_system.py:268-274` 直读
    `MiscCmds.CMD_HELP*`（值 = 包内 `content.misc_cmds.CMD_HELP*` 同一对象）；
  · `_notify_hermes` —— Hermes webhook 推送 = **宿主集成**（非游戏内容；v36 起默认停用），
    包内 `content/cmds_misc.py` 经 `env.state["shell"]` 取它。

形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 = `overnight/W-B18-L1.md`。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from ..commands.base import CommandBase
from ..log_setup import LOG

# 包加载口 = `game.bootstrap.package_apply()`（本进程唯一，幂等；失败大声抛，不静默降级）
from .. import bootstrap as _bootstrap          # noqa: E402

_bootstrap.package_apply()
from content import misc_cmds as _M             # noqa: E402


class MiscCmds(CommandBase):
    """签到/成就/意见/帮助（★ B18-L1 终态：注册 + 一行转发）"""

    # 帮助面板 11 份：真源在包内（`_M.HELP_PANELS`）；类属性照旧保留 ——
    # `tests/test_v104_commands_system.py:268-274` 直接读 `MiscCmds.CMD_HELP*` 做帮助补全断言
    CMD_HELP = _M.CMD_HELP
    CMD_HELP_CHAR = _M.CMD_HELP_CHAR
    CMD_HELP_ADV = _M.CMD_HELP_ADV
    CMD_HELP_BATTLE = _M.CMD_HELP_BATTLE
    CMD_HELP_SKILL = _M.CMD_HELP_SKILL
    CMD_HELP_PROF = _M.CMD_HELP_PROF
    CMD_HELP_ITEM = _M.CMD_HELP_ITEM
    CMD_HELP_INSTANCE = _M.CMD_HELP_INSTANCE
    CMD_HELP_SOCIAL = _M.CMD_HELP_SOCIAL
    CMD_HELP_WORLD = _M.CMD_HELP_WORLD
    CMD_HELP_OTHER = _M.CMD_HELP_OTHER


    # ---------- 宿主集成（非游戏内容）：Hermes webhook 推送 ----------
    async def _notify_hermes(self, group_id, qq_id, content, msg_type):
        """把玩家消息主动推送给 Hermes（webhook 触发格温本体处理）
        v36: webhook 桥已停用（改为 cron 汇总报告给鱼鱼），默认不通知。
        如后续需要可设环境变量 HERMES_WEBHOOK_URL 重新启用。"""
        import os
        if not os.environ.get("HERMES_WEBHOOK_URL"):
            return
        try:
            import aiohttp
            import hashlib
            import hmac
            import json as _json
            webhook_url = os.environ.get(
                "HERMES_WEBHOOK_URL",
                "http://localhost:8644/webhooks/dragonfall-bridge",
            )
            # v105 M24 P2-9：secret 不再内置明文默认值（曾泄漏在源码），强制由环境变量提供；
            # 未配置时跳过签名（webhook 桥默认停用，需 HERMES_WEBHOOK_URL 才启用）
            secret = os.environ.get("HERMES_WEBHOOK_SECRET")
            payload = _json.dumps(
                {
                    "group_id": str(group_id),
                    "qq_id": str(qq_id),
                    "content": content,
                    "msg_type": msg_type,
                },
                ensure_ascii=False,
            ).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if secret:
                sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
                headers["X-Webhook-Signature"] = sig
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, data=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    LOG.debug(
                        f"[dragonfall] 通知 Hermes: {resp.status}"
                    )
        except Exception as e:
            LOG.warning(f"[dragonfall] 通知 Hermes 失败(不影响主流程): {e}")


    @declared("help_cmd")
    async def help_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "help_cmd", event))

    @declared("game_tip")
    async def game_tip(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "game_tip", event))

    @declared("signin")
    async def signin(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "signin", event))

    @declared("achievements")
    async def achievements(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "achievements", event))

    @declared("feedback_cmd")
    async def feedback_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "feedback_cmd", event))
