# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - exploration（『探索进度』）★ B18 终态：**一行转发**

『探索进度』的**守卫 / 取参 / 区域聚合 / 面板行序 / 渲染全在包内**
（`content/cmds_explore.py` 登记进 `content/commands.py::COMMANDS`；聚合走包内
`content/exploration.py`，到访状态走包内存档层 `content/persistence/world.py`）。

本模块只剩两件事：
  ① **注册**：`@declared("explore_progress")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "explore_progress", event)` —— 桥到引擎 host 契约
     （造 `Env` → 守卫 → 包内 handler → 一条成品文本）

宿主的 `db.get_visited_subareas` 唯一读点（B8.2 线2 版）已随业务进包；宿主侧**无文案调用点**。
形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，
证据 = `overnight/W-B18-L6.md` 的 34 场景快照（sha256 改前 = 改后）。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from .base import CommandBase


class ExplorationCmds(CommandBase):
    """v115 探索见闻：『探索进度』指令（★ B18 终态：注册 + 一行转发）"""

    @declared("explore_progress")
    async def explore_progress(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "explore_progress", event))
