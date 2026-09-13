# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - instance（组队副本）—— B11-L1 **薄壳**（2026-09-14）

实现正文（`InstanceCmds` 的 65 个方法 + 模块常量 + `_inst_map_id`）已逐字搬进内容包
`content/instance_cmds.py`（类 `InstanceImpl`）。本文件只剩四件事：

    命令注册（**真** `@declared`，注册副作用留宿主）· 取玩家（包内方法自己取）· 调包（一行转发）· 渲染

`class InstanceCmds(_IC.InstanceImpl, InstanceRouterCmds, CommandBase)` 的 MRO 与重构前逐位等价：
私有助手（`_instance_battle_for` / `_instance_map_view` / `consume_monster` /
`_instance_current_members` / …）由 `InstanceImpl` 继承提供，宿主其它模块（combat/world/…
与 `instance_router`）和测试里 `self._instance_xxx(...)` 的调用点**零改动**。

★ 文案接线登记（`_DOMAIN_TEXT_KEYS`）：`tests/test_texts_table.py:81 WIRED` 的「声明 ↔ 调用点」
AST 对账按宿主文件做，而本文件原有的 `instance.*` 文案**真实调用点已随实现搬进包内**
（`content/instance_cmds.py` 的 `T.text/T.static`）。下表逐条登记该域全部 key，保证
「表里没有死文案」仍成立；**根修法** = 把 WIRED 那行指到包内实现（`INSTANCE_SRC` →
`framework/games/orlandia/content/instance_cmds.py`，属测试域，本线未动）→ 主 agent 收口清单。
本线自带的**同口径对拍**（宿主壳 + 包内实现并集，含槽位双向核对）见
`overnight/w1213_b11l1_gate.py`。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import content as C
from .. import db
from ..content_rules.gameplay import resolve_drop
from ..content_rules.panel import player_final_stats
from ..core.constants import ACT_TICK  # v167.3 护盾剩余刻数折算（1 刻 = ACT_TICK 秒）——N10 前由 battle re-export 改为 core 权威单源
from ..core import texts as T  # v185：文案表（唯一真源 game/data/text_specs.json）
from ..commands.base import CommandBase, no_prof_waiting, require_player
from .instance_router import InstanceRouterCmds  # v181.N5b4-5a R1：saintess_engine 副本行动路由

# 包加载口（本进程唯一）：包根进 sys.path → `content` 命名空间包
from .. import bootstrap as _bootstrap                                        # noqa: E402

_bootstrap.package_apply()

from content import instance_cmds as _IC                                      # noqa: E402

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

# ---- 文案接线登记（实现已搬包内；真实调用点在 content/instance_cmds.py）----
_DOMAIN_TEXT_KEYS = (
    "instance.i_am_leader",
    "instance.日志_击杀_宠物升级",
    "instance.日志_击杀_宠物经验",
    "instance.日志_击杀_拾取材料",
    "instance.日志_击杀_经验",
    "instance.日志_列表_入口",
    "instance.日志_列表_轮流提示",
    "instance.日志_列表_钥匙",
    "instance.日志_列表_首领",
    "instance.日志_地图_Boss房",
    "instance.日志_地图_可调查",
    "instance.日志_地图_怪剩余",
    "instance.日志_地图_怪肃清",
    "instance.日志_地图_房间标题",
    "instance.日志_地图_无出口",
    "instance.日志_地图_资源池",
    "instance.日志_墙砖提示",
    "instance.日志_失败_全灭",
    "instance.日志_失败_回城",
    "instance.日志_层_Boss在前",
    "instance.日志_层_场景标题",
    "instance.日志_层_宝箱",
    "instance.日志_层_敌人列表",
    "instance.日志_层_无敌",
    "instance.日志_层_暗门气息",
    "instance.日志_层_环顾",
    "instance.日志_层_肃清_剩调查",
    "instance.日志_层_肃清_无调查",
    "instance.日志_层_隐藏房间",
    "instance.日志_战利品堆提示",
    "instance.日志_搜刮_拾取",
    "instance.日志_搜刮_空",
    "instance.日志_搜刮_金币",
    "instance.日志_组队无坦克",
    "instance.日志_组队无治疗",
    "instance.日志_组队无输出",
    "instance.日志_行动序_我",
    "instance.日志_行动序_敌",
    "instance.日志_调查痕迹",
    "instance.日志_轮到行动",
    "instance.日志_通关_专属装备",
    "instance.日志_通关_停留搜刮",
    "instance.日志_通关_再挑战",
    "instance.日志_通关_击败",
    "instance.日志_通关_图纸",
    "instance.日志_通关_图纸已学",
    "instance.日志_通关_墙砖",
    "instance.日志_通关_奖励",
    "instance.日志_通关_宝石",
    "instance.日志_通关_宠物升级",
    "instance.日志_通关_宠物经验",
    "instance.日志_通关_战利品堆",
    "instance.日志_通关_材料",
    "instance.日志_通关_珍藏装备",
    "instance.日志_通关_离开提示",
    "instance.日志_通关_调查痕迹提示",
    "instance.日志_通关_阵亡",
    "instance.日志_通关_首功图纸",
    "instance.日志_通关_首功图纸已学",
    "instance.日志_面板_减伤",
    "instance.日志_面板_增益",
    "instance.日志_面板_护盾",
    "instance.日志_面板_护盾_剩刻",
    "instance.日志_面板_敌增益_剩刻",
    "instance.日志_面板_敌增益_叠层",
    "instance.日志_面板_敌增益行",
    "instance.日志_面板_选敌提示",
    "instance.面板_不在副本",
    "instance.面板_不在副本_简",
    "instance.面板_列表_人数",
    "instance.面板_列表_人数区间",
    "instance.面板_列表_单人",
    "instance.面板_列表_标题",
    "instance.面板_列表_行",
    "instance.面板_加入_参战",
    "instance.面板_加入_已在战斗",
    "instance.面板_加入_播报",
    "instance.面板_加入_无角色",
    "instance.面板_地图_层标题",
    "instance.面板_地图命令_战斗中",
    "instance.面板_宝箱_图纸",
    "instance.面板_宝箱_宠物蛋",
    "instance.面板_宝箱_开启",
    "instance.面板_宝箱_材料",
    "instance.面板_宝箱_符文",
    "instance.面板_宝箱_装备",
    "instance.面板_层行",
    "instance.面板_开本_单人挑战",
    "instance.面板_开本_地图_引导",
    "instance.面板_开本_地图_标题",
    "instance.面板_开本_找不到",
    "instance.面板_开本_提示",
    "instance.面板_开本_标题",
    "instance.面板_开本_队伍构成",
    "instance.面板_恢复进度",
    "instance.面板_探索_POI开头",
    "instance.面板_探索_小心开头",
    "instance.面板_探索_已肃清",
    "instance.面板_探索_已通关",
    "instance.面板_探索_无事",
    "instance.面板_探索_未发现",
    "instance.面板_探索_遇怪",
    "instance.面板_撤退_已弹过",
    "instance.面板_撤退_已放弃",
    "instance.面板_撤退_战斗中",
    "instance.面板_撤退_战斗中_boss",
    "instance.面板_撤退_无待确认",
    "instance.面板_撤退_确认",
    "instance.面板_撤退_确认过期",
    "instance.面板_暗格_开门",
    "instance.面板_暗格_死墙",
    "instance.面板_深入_已通关",
    "instance.面板_深入_房间模式",
    "instance.面板_深入_无分层",
    "instance.面板_深入_未清_先打完",
    "instance.面板_深入_未清_探索",
    "instance.面板_深入_末层",
    "instance.面板_状态_标题",
    "instance.面板_离开_完成",
    "instance.面板_离开_战斗中",
    "instance.面板_移动_非队长",
    "instance.面板_继续深入",
    "instance.面板_行动序",
    "instance.面板_调查_已处理",
    "instance.面板_调查_已搜刮空",
    "instance.面板_调查_战斗中",
    "instance.面板_调查_未命中",
    "instance.面板_调查_格式",
    "instance.面板_调查点_图纸",
    "instance.面板_调查点_开头",
    "instance.面板_调查点_收藏",
    "instance.面板_调查点_材料",
    "instance.面板_调查点_空",
    "instance.面板_调查点_蓝符",
    "instance.面板_调查点_零碎",
    "instance.面板_过期_24h",
    "instance.面板_通关超时离开",

)


class InstanceCmds(_IC.InstanceImpl, InstanceRouterCmds, CommandBase):
    """副本命令薄壳（B11-L1）：注册 + 取玩家 + 一行转发；实现全在包内 `content/instance_cmds.py`。"""

    @declared("join_battle")
    @require_player()
    @no_prof_waiting()
    async def join_battle(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.join_battle(self, event):
            yield _r

    @declared("instance_cmd")
    @require_player()
    @no_prof_waiting()
    async def instance_cmd(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_cmd(self, event):
            yield _r

    @declared("instance_advance")
    @require_player()
    @no_prof_waiting()
    async def instance_advance(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_advance(self, event):
            yield _r

    @declared("instance_map_view_cmd")
    @require_player()
    @no_prof_waiting()
    async def instance_map_view_cmd(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_map_view_cmd(self, event):
            yield _r

    @declared("instance_investigate")
    @require_player()
    @no_prof_waiting()
    async def instance_investigate(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_investigate(self, event):
            yield _r

    @declared("instance_retreat")
    @require_player()
    @no_prof_waiting()
    async def instance_retreat(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_retreat(self, event):
            yield _r

    @declared("instance_retreat_confirm")
    @require_player()
    @no_prof_waiting()
    async def instance_retreat_confirm(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_retreat_confirm(self, event):
            yield _r

    @declared("instance_leave")
    @require_player()
    @no_prof_waiting()
    async def instance_leave(self, event: AstrMessageEvent):
        async for _r in _IC.InstanceImpl.instance_leave(self, event):
            yield _r
