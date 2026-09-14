# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - event_menu（v140 波3.7 地图随机事件菜单）★ B18 终态：**一行转发**

『今日事件』总览（今日奇遇/世界事件/彩蛋线索三栏）+ 『事件 <地图名>』单图深查 +
『领取补给箱』（SUPPLY_BOX 3 档限额）的**守卫 / 取参 / 分支业务 / 面板行序 / 渲染全在包内**
（`content/cmds_event.py` 登记进 `content/commands.py::COMMANDS`；读表 = 包内
`content/event_menu.py` + `content/catalog_rules.py` + `content/catalog_b143.py`；
发物/限额 = 包内存档层 `content/persistence/`）。

本模块只剩两件事：
  ① **注册**：`@declared("event_menu")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "event_menu", event)` —— 桥到引擎 host 契约
     （造 `Env` → 守卫 → 包内 handler → 一条成品文本）

`supply.*` 7 条文案的调用点随渲染进包（`content/cmds_event.py`）—— 文案表门禁
（`tests/test_texts_table.py` 的 `WIRED["补给箱"]`）已把宿主与本文件两侧一起扫 → 41/41 不变。
形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，
证据 = `overnight/W-B18-L6.md` 的 34 场景快照（sha256 改前 = 改后）。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from ..commands.base import CommandBase


class EventMenuCmds(CommandBase):
    """今日事件：地图随机事件总览 / 单图深查 / 每日补给箱（★ B18 终态：注册 + 一行转发）"""

    @declared("event_menu")
    async def event_menu(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "event_menu", event))
