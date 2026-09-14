# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - instance（组队副本）—— B11-L1 起**薄壳**，B18-L10 终态（2026-09-14）

8 条副本命令的**守卫声明 / 调包 / 回话**全在包内
（`content/cmds_instance.py` 登记进 `content/commands.py::COMMANDS`）。本文件只剩三件事：

    ① **注册**：`@declared("<key>")`（真注册，正则来自声明表 `game/data/command_specs.json`）
    ② **转发**：`async for _r in _BRIDGE.run_async(self, "<key>", event): yield _r`
       —— 桥到引擎 host 契约（造 `Env` → 声明守卫 → 包内 handler → 逐段回话）
    ③ **包内实现注入 + 再导出**：`content/instance_cmds.py` 的宿主面注入
       （`_IC.bind_host(...)`，必须先于用包内实现）+ 模块常量 / 纯函数的再导出
       （既有 import 点零变化：tests 直接 import 这些名字）

★ B18-L10（2026-09-14）**这 8 条进引擎通道**：原先宿主壳是
  `async for _r in _CMDS.forward(self, "<key>", event): yield _r` —— 那只是**宿主内部**的
  转发口（`content/cmds_instance.py::forward` 是 B18-L5 搬进包的宿主转发口），**不是引擎通道**：
  编辑器试玩（B20）与换包实证（P6）跑不到这 8 条。本线把守卫声明与调包搬进包内本模块的
  `@_declare` 处理器，宿主每条命令只剩 `@declared("<key>")` + 两行 `run_async` 转发。

★ **8 条全部是「两行 `run_async`」**（没有一条走同步 `_BRIDGE.run`）：实现体
  `content/instance_cmds.py::InstanceImpl.<key>` 8/8 都是 **async generator**（AST 实测带
  `yield`；每条命令按分支 `yield event.plain_result(...)`，多分支合计 37 个 yield 点），
  旧壳正是 `async for _r in _CMDS.forward(self, key, event): yield _r` —— 只能 `async for`
  迭代。故包内用 `_declare` 登记 `async def`（照 B18-L3c 战斗族 / B18-L9 经济族先例），
  宿主两行逐条 `yield`：与旧壳的消息切分逐字节相同（含守卫拦截回话）。
  `forward` / `COMMAND_KEYS` **保留**（宿主其它调用点/工具可能还用；B18-L10 起宿主不再调它）。

★ **守卫随声明进包**：原先宿主装饰器 `@require_player()` + `@no_prof_waiting()` 一并搬进包内
  处理器声明（`guards=("hook:player", "hook:no_prof_waiting")`，顺序 = `command_specs.json`
  这 8 条的 `guards` = 宿主装饰器施加顺序）。判定与文案都在包侧 `content/guards.py`
  （`player` 的提示逐字 = `base.REGISTER_HINT`；`no_prof_waiting` 与宿主再导出同源），
  故拦截回话一字不差。宿主里 `grep -c 'T\\.text\\|T\\.static' game/commands/instance.py` = 0。

`class InstanceCmds(_IC.InstanceImpl, InstanceRouterCmds, CommandBase)` 的 MRO 与重构前逐位等价：
私有助手（`_instance_battle_for` / `_instance_map_view` / `consume_monster` /
`_instance_current_members` / …）由 `InstanceImpl` 继承提供，宿主其它模块（combat/world/…
与 `instance_router`）和测试里 `self._instance_xxx(...)` 的调用点**零改动**。

★ 文案接线（**真源在包内**）：本域 `instance.*` 文案的 `T.text/T.static` 调用点全在包内
实现（`content/instance_cmds.py` = B11-L1 搬入的实现体）。**B18-L5 已把「根修法」做完**：
`tests/test_texts_table.py::WIRED` 的「副本日志」域扫描根改为
`[game/commands/instance.py, framework/.../content/instance_cmds.py]` **双侧**（与「周常 /
补给箱 / 副本战斗日志」同款口径）→ B11-L1 的 key 字面量兜底（`_DOMAIN_TEXT_KEYS`）**已删**
（那时 WIRED 只扫宿主才需要它）。本线自带的同口径对拍（命令清单 / 声明视图 / 门禁扫描根 /
槽位双向核对）见 `overnight/b18l5_checks.py`（44/44）。

形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 =
`out/b18l10_snap.py` 的 74 场景快照（sha256 改前 = 改后，含逐表 DB dump）+ 3 硬门禁
+ 10 副本定向 + 数值门禁。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import content as C
from .. import db
from ..content_rules.gameplay import resolve_drop
from ..content_rules.panel import player_final_stats
from ..core.constants import ACT_TICK  # v167.3 护盾剩余刻数折算（1 刻 = ACT_TICK 秒）——N10 前由 battle re-export 改为 core 权威单源
from ..core import texts as T  # v185：文案表（唯一真源 game/data/text_specs.json）
from ..commands.base import CommandBase
from . import _host_bridge as _BRIDGE
from .instance_router import InstanceRouterCmds  # v181.N5b4-5a R1：saintess_engine 副本行动路由

# 包加载口（本进程唯一）：包根进 sys.path → `content` 命名空间包
from .. import bootstrap as _bootstrap                                        # noqa: E402

_bootstrap.package_apply()

from content import instance_cmds as _IC                                      # noqa: E402
from content import cmds_instance as _CMDS                                    # noqa: E402,F401  B18-L10：8 条命令登记进包内表

# 宿主面注入（**必须先于用包内实现**；包内模块级只读包内域文件，不读宿主面）
_IC.bind_host(C=C, db=db, T=T, player_final_stats=player_final_stats,
              resolve_drop=resolve_drop, ACT_TICK=ACT_TICK,
              AstrMessageEvent=AstrMessageEvent)

# ---- 再导出：模块常量 / 纯函数（既有 import 点零变化：tests 直接 import 这些名字）----
INSTANCE_TIMEOUT = _IC.INSTANCE_TIMEOUT                                       # noqa: F401
INVESTIGATE_DAILY_LIMIT = _IC.INVESTIGATE_DAILY_LIMIT                         # noqa: F401
INVESTIGATE_BP_CHANCE = _IC.INVESTIGATE_BP_CHANCE                             # noqa: F401
INVESTIGATE_RUNE_CHANCE = _IC.INVESTIGATE_RUNE_CHANCE                         # noqa: F401
INVESTIGATE_COLLECT_CHANCE = _IC.INVESTIGATE_COLLECT_CHANCE                   # noqa: F401
_inst_map_id = _IC._inst_map_id                                              # noqa: F401

# ---- 文案接线（**真源在包内，宿主不再登记**）----------------------------------------
# 本域 `instance.*` 文案的 `T.text/T.static` 调用点全在包内实现
# （`content/instance_cmds.py` = B11-L1 搬入的实现体；`content/cmds_instance_router.py`
#  = B18-L5 搬入的路由）。`tests/test_texts_table.py::WIRED` 的「副本日志 / 副本结算」
# 两域已同批扩到「宿主 + 包内」双侧扫描（与「周常 / 补给箱 / 副本战斗日志」同款口径），
# 故此处**不再需要** B11-L1 的 key 字面量登记（那套是当时 WIRED 只扫宿主时的兜底）。
# B18-L10 只搬「壳」（守卫声明 + 调包），文案调用点**一个没动**（实现体逐字未改）。


class InstanceCmds(_IC.InstanceImpl, InstanceRouterCmds, CommandBase):
    """副本命令薄壳（B11-L1 起，B18-L10 终态）：注册 + 两行转发；守卫/调包/回话全在包内
    `content/cmds_instance.py`。"""

    @declared("join_battle")
    async def join_battle(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::join_battle`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "join_battle", event):
            yield _r

    @declared("instance_cmd")
    async def instance_cmd(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_cmd`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_cmd", event):
            yield _r

    @declared("instance_advance")
    async def instance_advance(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_advance`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_advance", event):
            yield _r

    @declared("instance_map_view_cmd")
    async def instance_map_view_cmd(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_map_view_cmd`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_map_view_cmd", event):
            yield _r

    @declared("instance_investigate")
    async def instance_investigate(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_investigate`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_investigate", event):
            yield _r

    @declared("instance_retreat")
    async def instance_retreat(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_retreat`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_retreat", event):
            yield _r

    @declared("instance_retreat_confirm")
    async def instance_retreat_confirm(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_retreat_confirm`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_retreat_confirm", event):
            yield _r

    @declared("instance_leave")
    async def instance_leave(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_instance.py::instance_leave`（B18 L10）
        async for _r in _BRIDGE.run_async(self, "instance_leave", event):
            yield _r
