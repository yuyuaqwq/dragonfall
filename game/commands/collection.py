# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - collection（冒险者收藏册）★ B18 终态：**一行转发**

『收藏册 [套名]』/『收藏册 领取 [套名]』的**总览 / 明细 / 满套领取（含宝箱入包）全在包内**
（`content/cmds_collection.py` 登记进 `content/commands.py::COMMANDS`）。本模块只剩注册
（`@declared("collection")`）+ 一行转发（`_BRIDGE.run(self, "collection", event)`）。

包内数据口：读表 + 收藏判定 = `content/collection.py`；背包/图鉴读写 = 包内存档层
`content/persistence`（B17 归包，与宿主 `db.*` 同一批函数）；显示名索引 = 包内 `content/index.py`。
宿主里没有任何渲染代码。形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；
行为逐字节不变，证据 = `overnight/W-B18-样板.md`。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from ..commands.base import CommandBase


class CollectionCmds(CommandBase):
    """收藏册：冒险者收藏集展示/满套领奖（★ B18 终态：注册 + 一行转发）"""

    @declared("collection")
    async def collection(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "collection", event))
