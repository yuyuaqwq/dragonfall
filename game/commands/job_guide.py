# -*- coding: utf-8 -*-
"""命令层 - job_guide（v130.2g 『职业』/『职业 <名称>』职业速查）★ B18 终态：**一行转发**

落地玩家意见 #1（zerc）「增加查看职业信息的功能」：
- 『职业』：12 职业速查一览（基础六 + 隐藏六分组，名称 + 定位一句话）
- 『职业 <名称>』：单职业详情（基础名/档位路线/核心资源机制/转职条件/隐藏线解锁方式）

**解析与渲染全在包内**（`content/cmds_job.py` 登记进 `content/commands.py::COMMANDS`；
数据 = 包内门面 `content/tables.py` 的 job_guide 域 + `resolve("job_guide", …)`）。
本模块只剩两件事：
  ① **注册**：`@declared("job_guide")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "job_guide", event)` —— 桥到引擎 host 契约
     （造 `Env` → 守卫 → 包内 handler → 一条成品文本）

纯信息查询：不 require_player（注册前可查，与『种族』『图鉴』同款）—— 声明里也不给 guards。
形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，
证据 = `overnight/W-B18-L6.md` 的 34 场景快照（sha256 改前 = 改后）。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared
from ..commands.base import CommandBase


class JobGuideCmds(CommandBase):
    """『职业』速查：12 职业一览 + 单职业详情（玩家意见 #1，★ B18 终态：注册 + 一行转发）"""

    @declared("job_guide")
    async def job_guide(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "job_guide", event))
