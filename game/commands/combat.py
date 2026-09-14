# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - combat（combat）—— B10 L5 薄壳 · **B2-W2 机械指向**

由 main.py 拆分而来，作为 Mixin 被 Main 继承。真源（实现本体）**全在内容包**
`content/combat_cmds.py`（74 个方法逐字搬过去，见那边的头注；15 条命令的守卫/取参/守卫声明
在 `content/cmds_combat.py` + `content/guards.py`，B18 L3c 起命令整块进包）。

本文件现在只剩**两类**东西（B2-W2：把 59 个**逐个手写**的委托桩换成**类级机械指向**，
不再抄一遍转发实现；本波不删壳，删壳归 B4）：

  · **命令入口**（15 个）：`@declared("<key>")` + 两行转发（`_BRIDGE.run_async`）——
    名字/装饰器/注册序与改造前逐行相同（`@declared` 是宿主侧的**注册**动作：正则来自
    `game/data/command_specs.json`，框架注册表 + `_registry` 都从它派生）。
  · **类级机械指向**：59 个非命令私有方法经 `CombatCmds.__getattr__` 按名单转发到包内同名
    模块级函数（`fn(self, …)` 绑定；唯一例外 `_buff_left_ticks` 是 `@staticmethod`）。
    执行 `self._<名>(...)` 的调用方（本文件、其它 Mixin、测试）**零改动**：
    名字集合与改造前**逐名相同** → Main 的 MRO 解析结果不变。
    类级常量表（`_MECH_CN` / `_EFFECT_CN` / `_P_BUFF_NAMES` / `_E_BUFF_NAMES` / `_STACK_NAMES` /
    `_ENEMY_MECH_STACKS` / `_DEBUFF_NAMES` / `_RAIN_WINDOW` / `_EXPLORE_RECENT_*` /
    `_DF139_CLASS_FORMS` / `_FINISHER139_OPTIONS` / `_ARCANE_FIELD_OPTIONS`）**改由基类提供**：
    `class CombatCmds(_CC.CombatCmds, CommandBase)` —— `_CC.CombatCmds` 是包内**类入口等价面**
    （B2-C1 逐表值/类型/dict 键序对拍全等，`out/evidence/combatcmds_tables.txt`），
    包内实现体经 `self._X` 读到的仍是**同一份值**（单源，不复制）。

★ 一处**故意留在宿主**（不是遗漏）：`from ..core.wild_king import (` 模块级 import ——
  包内 `explore`/`wild_king_chest` 经**本模块属性**动态解析野王四函数；
  `tests/test_v1307_zone_risk.py:65` 与 `tests/test_v1308_lv_jitter.py:70` 会 monkeypatch
  `game.commands.combat.explore_king` 屏蔽野王（绑死 = 测试假红）。
  宿主替身注入照旧：`_CC.bind_host(db=db, content=C, **{"commands.combat": 本模块})`。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from .. import content as C
from .. import db
from ..commands.base import CommandBase, no_prof_waiting, require_player, require_battle

# v140 波2：野王体系（探索命中/结算/摸宝箱）—— 包内实现经本模块属性动态解析（测试 monkeypatch 面）
from ..core.wild_king import (
    explore_king, build_king_monster, open_chest,
    wild_king_summary,
)
# v181 P4-1 试点：每日元数据键 + 达标结算单点已收敛至 services.quests（兼容再导出：原顶层名照旧）
from ..services.quests import DAILY_META_KEYS, settle_daily_quest  # noqa: F401

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）
from content import combat_cmds as _CC                        # noqa: E402

import functools as _functools                                # noqa: E402
import sys as _sys                                           # noqa: E402
_CC.bind_host(db=db, content=C,
              **{"commands.combat": _sys.modules[__name__]})  # 宿主替身注入（正文 `db.`/`C.` 不改）

# ---- 搬迁再导出（模块级名字集合与改造前逐名相同；消费者零改动）----
# game/commands/instance.py:1484 / :1495
pet_battle_status_note = _CC.pet_battle_status_note
resource_stack_text = _CC.resource_stack_text
# tests/test_v104_explore_map.py:42
WORLD_BOSS_DROPS = _CC.WORLD_BOSS_DROPS
# 其余原顶层名（无外部消费者，保名字集合一致）
RESOURCE_STACK_CN = _CC.RESOURCE_STACK_CN
WORLD_BOSS_DOT_INTERVAL = _CC.WORLD_BOSS_DOT_INTERVAL
_curve_vals = _CC._curve_vals
_fmt_mult = _CC._fmt_mult
_res_display_name = _CC._res_display_name
_battle_locks = _CC._battle_locks


class CombatCmds(_CC.CombatCmds, CommandBase):
    """命令层薄壳（B2-W2 机械指向）：15 个 `@declared` 命令入口 + 一个按名转发口。

    实现（74 个方法）全在包内 `content/combat_cmds.py`；类级常量表来自基类
    `_CC.CombatCmds`（包内等价面，逐表对拍相等）。
    """

    @declared("explore")
    async def explore(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::explore`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "explore", event):
            yield _r


    @declared("wild_king_chest")
    async def wild_king_chest(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::wild_king_chest`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "wild_king_chest", event):
            yield _r


    @declared("wish")
    async def wish(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::wish`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "wish", event):
            yield _r


    @declared("trader_confirm")
    async def trader_confirm(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::trader_confirm`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "trader_confirm", event):
            yield _r


    @declared("revive_confirm")
    async def revive_confirm(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::revive_confirm`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "revive_confirm", event):
            yield _r


    @declared("attack")
    async def attack(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::attack`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "attack", event):
            yield _r


    @declared("skill")
    async def skill(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::skill`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "skill", event):
            yield _r


    @declared("defend")
    async def defend(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::defend`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "defend", event):
            yield _r


    @declared("flee")
    async def flee(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::flee`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "flee", event):
            yield _r


    @declared("hunt_boss")
    async def hunt_boss(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::hunt_boss`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "hunt_boss", event):
            yield _r


    @declared("honor_shop")
    async def honor_shop(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::honor_shop`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "honor_shop", event):
            yield _r


    @declared("battle_prefs_form")
    async def battle_prefs_form(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::battle_prefs_form`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "battle_prefs_form", event):
            yield _r


    @declared("battle_prefs_finisher")
    async def battle_prefs_finisher(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::battle_prefs_finisher`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "battle_prefs_finisher", event):
            yield _r


    @declared("battle_prefs_arcane_field")
    async def battle_prefs_arcane_field(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::battle_prefs_arcane_field`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "battle_prefs_arcane_field", event):
            yield _r


    @declared("battle_prefs_view")
    async def battle_prefs_view(self, event: AstrMessageEvent):
        # 守卫 / 取参 / 业务 / 回话全在包内 `content/cmds_combat.py::battle_prefs_view`（B18 L3c）
        async for _r in _BRIDGE.run_async(self, "battle_prefs_view", event):
            yield _r


    # ---- 机械指向（类级 `__getattr__` = 模块级 PEP 562 的类等价物）----------------
    _FORWARDS = frozenset(["_b_enemy", "_main_kill_target_on_map", "_in_battle", "_lock_battle", "_unlock_battle", "_open_battle", "_restore_battle", "_sync_battle_player", "_mount_explore_bonus", "_roll_hidden_monster", "_roll_find_quest_events", "_rain_boost", "_handle_explore_event", "_recent_explore_events", "_remember_explore_event", "_poi_daily_used", "_handle_poi", "_skill_panel", "_branch_skills_for", "_player_skill_table", "_skill_tag", "_skill_range_label", "_skill_list_gains", "_skill_gains_curve", "_skill_list_page", "_buff_left_ticks", "_status_line", "_resource_line", "_player_unit_for_formation", "_battle_formation_panel", "_battle_footer", "_handle_victory", "_next_step_hint", "_nearest_town", "_handle_defeat", "_grant_worldboss_drop", "_worldboss_act", "_parse_target_qq", "_red_until", "_is_redname", "_get_honor", "_pvp_meta_qqs", "_pvp_snapshot", "_pvp_handle_timeout", "_set_pvp_cd", "_pvp_cd_left", "_honor_buy", "_pvp_start", "_pvp_act", "_pvp_finish"])

    _STATIC_FORWARDS = frozenset(["_buff_left_ticks"])

    def __getattr__(self, name):
        """按名单把非命令私有方法转发到包内同名函数（**包内唯一实现**；本类不再抄一份）。"""
        if name in CombatCmds._FORWARDS:
            fn = getattr(_CC, name)
            if name in CombatCmds._STATIC_FORWARDS:
                return lambda *a, **kw: fn(*a, **kw)
            return _functools.partial(fn, self)
        raise AttributeError("CombatCmds has no attribute %r" % (name,))
