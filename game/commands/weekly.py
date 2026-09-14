# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - weekly（v169.2 周常悬赏 Lv50+）★ B18 终态：**一行转发**

『周常』『周常列表』的**守卫 / 取参 / 分支业务 / 面板行序 / 渲染全在包内**
（`content/cmds_weekly.py` 登记进 `content/commands.py::COMMANDS`；文案走包内 `content/texts.py`）。
本模块只剩两件事：

  ① **注册**：`@declared("<key>")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "<key>", event)` —— 桥到引擎 host 契约（造 `Env` → 守卫
     → 包内 handler → 一条成品文本）

宿主里**没有**任何文案调用点（句子与槽位全在包内 → 宿主零游戏文案）。
形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 = `overnight/W-B18-样板.md`。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from ..commands.base import CommandBase


class WeeklyCmds(CommandBase):
    """周常悬赏：本周悬赏板查看/自动发布 + 悬赏池列表分页（★ B18 终态：注册 + 一行转发）"""

    @declared("weekly_cmd")
    async def weekly_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "weekly_cmd", event))

    @declared("weekly_list")
    async def weekly_list(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "weekly_list", event))
