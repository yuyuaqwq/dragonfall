# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - world（world）★ B18-L1 终态：**一行转发**

36 条世界命令的**守卫 / 取参 / 分支业务 / 面板行序 / 渲染全在包内**（`content/cmds_world.py`
登记进 `content/commands.py::COMMANDS`；文案走包内 `content/texts.py`）。本模块只剩三件事：

  ① **注册**：`@declared("<key>")`（正则/desc 来自宿主声明表 `game/data/command_specs.json`）
  ② **转发**：`_BRIDGE.run(self, "<key>", event)` —— 桥到引擎 host 契约（造 `Env` → 守卫
     → 包内 handler → 一条成品文本）
  ③ **私有方法桩**：非命令的 `_xxx` 一行委托（其它 Mixin/测试按 MRO 直调，名字集合与改造前逐名相同）

宿主里**零** 文案调用点（`grep -c 'T\.text\|T\.static' game/commands/world.py` = 0）
—— 每日任务域 `daily.*` 的渲染点随 `quest_view` 一起进包（`tests/test_texts_table.py` 的 WIRED
表已按「周常」先例补上包内文件）。

★ **故意留在宿主**的一处实现（宿主源码级门禁要求，不是遗漏）
  · `_instance_gate_block` —— `tests/test_v185_instance_admission.py:1131` 要求本文件源码出现
    `instance_gate.walk_admission`（徒步进图三档判定；非命令、无文案调用点）。

形状真源 = `overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 = `overnight/W-B18-L1.md`
（174 项三分支快照 sha256 改前 = 改后）。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import db
from .. import content as C

from . import _host_bridge as _BRIDGE
from ..commands.base import CommandBase

# ============ v181 P4-1：每日任务域规则实现收敛在 game/services/quests.py（兼容导出照旧） ============
from ..services.quests import (  # noqa: F401  （P4-1 兼容导出：原 world.py 顶层常量名）
    DAILY_LIMIT, DAILY_REPEAT_FACTORS as _DAILY_REPEAT_FACTORS,
    DAILY_META_KEYS as _DAILY_META_KEYS, daily_need,
)


def _settle_daily_quest(inst, group_id, qq_id, daily, dq, lines=None):
    """（P4-1 兼容壳：转调 game/services/quests.settle_daily_quest——world/combat 命令层
    调用点已全部改走 services 直调；本壳仅供外部存档/工具兜底）"""
    from ..services.quests import settle_daily_quest as _settle_impl
    _settle_impl(group_id, qq_id, daily, dq, lines)


def _bump_daily_progress(group_id, qq_id, obj_key, lines=None):
    """（P4-1 兼容壳：转调 game/services/quests.bump_daily_progress——供存档/工具兜底）"""
    from ..services.quests import bump_daily_progress as _bump_impl
    return _bump_impl(group_id, qq_id, obj_key, lines)


def _daily_pool(player, dq):
    """（P4-1 兼容壳：转调 game/services/quests.daily_pool——『每日』抽取已改 services 直调）"""
    from ..services.quests import daily_pool as _pool_impl
    return _pool_impl(player, dq)


from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）
from content import world_cmds as _WC                        # noqa: E402

_WC.bind_host(db=db, content=C)                              # 宿主替身注入（桩正文 `db.`/`C.` 不改）
# v104 M23 修复：许愿井彩蛋概率（唯一定义点已随实现搬进包内 `content/world_cmds.py`；本行兼容再导出）
WISH_WELL_EGG_CHANCE = _WC.WISH_WELL_EGG_CHANCE


class WorldCmds(CommandBase):
    """命令层（★ B18-L1 终态）：注册 + 一行转发；守卫/取参/业务/渲染全在包内 `content/cmds_world.py`。"""



    _HURRY_ALIAS = {
        "npc": "npc",
        "怪物": "monster", "怪": "monster", "monster": "monster",
        "场景": "scene", "scene": "scene", "景物": "scene",
        "设施": "facility", "facility": "facility", "商店": "facility",
    }

    def _map_facilities(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_facilities`（B9 线2 薄壳）。"""
        return _WC._map_facilities(self, *args, **kwargs)

    def _map_scene(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_scene`（B9 线2 薄壳）。"""
        return _WC._map_scene(self, *args, **kwargs)

    def _visible_sas(self, *args, **kwargs):
        """委托包内 `content/world_cmds._visible_sas`（B9 线2 薄壳）。"""
        return _WC._visible_sas(self, *args, **kwargs)

    @staticmethod
    def _conn_target(*args, **kwargs):
        """委托包内 `content/world_cmds._conn_target`（B9 线2 薄壳）。"""
        return _WC._conn_target(*args, **kwargs)

    @staticmethod
    def _conn_subarea_name(*args, **kwargs):
        """委托包内 `content/world_cmds._conn_subarea_name`（B9 线2 薄壳）。"""
        return _WC._conn_subarea_name(*args, **kwargs)

    def _home_map_id(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_map_id`（B9 线2 薄壳）。"""
        return _WC._home_map_id(self, *args, **kwargs)

    @declared("deed_view")
    async def deed_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "deed_view", event))

    @declared("deed_buy")
    async def deed_buy(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "deed_buy", event))

    @declared("deed_sell")
    async def deed_sell(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "deed_sell", event))

    def _deed_upgrade(self, *args, **kwargs):
        """委托包内 `content/world_cmds._deed_upgrade`（B9 线2 薄壳）。"""
        return _WC._deed_upgrade(self, *args, **kwargs)

    @declared("go_home")
    async def go_home(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "go_home", event))

    @declared("go_out")
    async def go_out(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "go_out", event))

    @declared("visit_home")
    async def visit_home(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "visit_home", event))

    def _home_storage_key(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_storage_key`（B9 线2 薄壳）。"""
        return _WC._home_storage_key(self, *args, **kwargs)

    def _home_storage_load(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_storage_load`（B9 线2 薄壳）。"""
        return _WC._home_storage_load(self, *args, **kwargs)

    def _home_storage_save(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_storage_save`（B9 线2 薄壳）。"""
        return _WC._home_storage_save(self, *args, **kwargs)

    @declared("home_storage")
    async def home_storage(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "home_storage", event))

    @declared("home_storage_take")
    async def home_storage_take(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "home_storage_take", event))

    @declared("map_view")
    async def map_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "map_view", event))

    @declared("region_view")
    async def region_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "region_view", event))

    def _map_blocks(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_blocks`（B9 线2 薄壳）。"""
        return _WC._map_blocks(self, *args, **kwargs)

    def _map_nav_body(self, *args, **kwargs):
        """委托包内 `content/world_cmds._map_nav_body`（B9 线2 薄壳）。"""
        return _WC._map_nav_body(self, *args, **kwargs)

    @declared("location_view")
    async def location_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "location_view", event))

    def _hurry_type(self, *args, **kwargs):
        """委托包内 `content/world_cmds._hurry_type`（B9 线2 薄壳）。"""
        return _WC._hurry_type(self, *args, **kwargs)

    def _hurry_section(self, *args, **kwargs):
        """委托包内 `content/world_cmds._hurry_section`（B9 线2 薄壳）。"""
        return _WC._hurry_section(self, *args, **kwargs)

    def _hurry_panel(self, *args, **kwargs):
        """委托包内 `content/world_cmds._hurry_panel`（B9 线2 薄壳）。"""
        return _WC._hurry_panel(self, *args, **kwargs)

    @declared("hurry_view")
    async def hurry_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "hurry_view", event))

    def _move_blocked_msg(self, *args, **kwargs):
        """委托包内 `content/world_cmds._move_blocked_msg`（B9 线2 薄壳）。"""
        return _WC._move_blocked_msg(self, *args, **kwargs)

    @declared("back_cmd")
    async def back_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "back_cmd", event))

    @declared("ask_way")
    async def ask_way(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "ask_way", event))

    def _instance_gate_block(self, player: dict, group_id: str, qq_id: str, target: dict) -> str:
        """q1-B 副本图门禁：徒步『前往/移动』不可直接进入副本图（type=副本）。

        否则终局副本旁路：ash_temple/abyss_gate 等副本图经 MAP_CONNECTIONS 连通可徒步
        到达，玩家走进即自动完成 explore 主线目标（q9_3/q10_3 目标 ash_temple，
        q12_3 目标 abyss_gate），绕过『副本 <名字>』开本流程的钥匙/等级/人数校验。
        准入判定有三档（任一满足即放行，返回值空串）：
          - 玩家正持有 active 且 explore 目标为本图的**主线或支线任务**（任务内进入不受影响）；
          - 背包持有该副本 key_item（如 ash_temple→烬火令，abyss_gate→深渊钥匙）；
          - 已通关该副本（inst_clear_* 首通记录，与 instance.py 免钥匙同口径）。

        v141 审计 #9：钥匙三路匹配 + 通关豁免抽到 core/instance_gate.py
        （find_instance_key_item / instance_cleared_qq），此处只做任务放行层 + 调用公共函数。
        设计语义：**徒步进图不扣钥匙**（只校验持有，钥匙由『副本 <名字>』开本时才扣），
        任务/钥匙两路放行；开本才扣（见 instance.py _instance_start 同款公共函数调用）。

        v185：三档判定收敛成 core/instance_gate.walk_admission（`mode='any'`，任一命中即
        放行；全不通过时链级 reason = 原文案），本方法只负责取数与渲染 `v.reason`。

        命中时返回拦截文案；非副本图直接放行。『副本 <名字>』开本入口不经过本方法，不受影响。
        """
        if target.get("type") != C.MAP_TYPE_INSTANCE:
            return ""
        from ..core import instance_gate
        kid = target.get("id", "")
        mid = f"inst_{kid}"
        inst = C.INSTANCES.get(mid)
        # 1) 任务内进入：active 主线或支线 explore 目标 == 本副本图 → 放行
        quests = db.get_quests(group_id, qq_id)
        quest_open = False
        if quests.get("main_status") == "active":
            mq = next((q for q in C.MAIN_QUESTS if q["id"] == quests.get("main_quest")), None)
            if mq and mq["objective"].get("explore") == kid:
                quest_open = True
        if not quest_open:
            side = quests.get("side") or {}
            quest_open = any(sq.get("status") == "active"
                             and next((q for q in C.SIDE_QUESTS if q["id"] == sid), {}).get("objective", {}).get("explore") == kid
                             for sid, sq in side.items())
        # 2) 持有钥匙（与 instance.py 开本钥匙判定同源，抽公共 core/instance_gate.py）
        # 3) 已通关副本 → 免钥匙放行（与 instance.py 同口径）
        # ★ D2（v185 本轮登记的有意差异）：这一档原先查 `inst_clear_<地图id>`（kid），
        #   而真实通关写入的是 `inst_clear_<inst键>`（instance.py 通关结算 / instance_router 读档）
        #   ⇒ 线上**不可达**（实测：写真实键仍被拦、写地图 id 形式反而放行）。
        #   现改为查 inst 键（mid），与 instance.py 免钥匙真正同口径；不保留旧键兼容（一套口径）。
        key_item = (inst or {}).get("key_item")
        ctx = {
            "inst_name": (inst or {}).get("name") or C.MAP_BY_ID.get(kid, {}).get("name", "副本"),
            "tip": self._tip("instance"),
            "quest_open": quest_open,
            "key_held": bool(key_item) and instance_gate.find_instance_key_item(
                group_id, qq_id, key_item) is not None,
            "cleared": instance_gate.instance_cleared_qq(group_id, qq_id, mid),
        }
        v = instance_gate.walk_admission(ctx).check(ctx)
        return "" if v.ok else v.reason

    @declared("move")
    async def move(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "move", event))

    def _subarea_arrive(self, *args, **kwargs):
        """委托包内 `content/world_cmds._subarea_arrive`（B9 线2 薄壳）。"""
        return _WC._subarea_arrive(self, *args, **kwargs)

    def _instance_dungeon_move(self, *args, **kwargs):
        """委托包内 `content/world_cmds._instance_dungeon_move`（B9 线2 薄壳）。"""
        return _WC._instance_dungeon_move(self, *args, **kwargs)

    def _travel_ambush(self, *args, **kwargs):
        """委托包内 `content/world_cmds._travel_ambush`（B9 线2 薄壳）。"""
        return _WC._travel_ambush(self, *args, **kwargs)

    @declared("portal_view")
    async def portal_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "portal_view", event))

    @declared("portal_activate")
    async def portal_activate(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "portal_activate", event))

    @declared("portal_travel")
    async def portal_travel(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "portal_travel", event))

    def _update_explore_quests(self, *args, **kwargs):
        """委托包内 `content/world_cmds._update_explore_quests`（B9 线2 薄壳）。"""
        return _WC._update_explore_quests(self, *args, **kwargs)

    @declared("quest_view")
    async def quest_view(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "quest_view", event))

    @declared("quest_accept")
    async def quest_accept(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "quest_accept", event))

    def _sq_unlocked(self, *args, **kwargs):
        """委托包内 `content/world_cmds._sq_unlocked`（B9 线2 薄壳）。"""
        return _WC._sq_unlocked(self, *args, **kwargs)

    def _sq_stats_met(self, *args, **kwargs):
        """委托包内 `content/world_cmds._sq_stats_met`（B9 线2 薄壳）。"""
        return _WC._sq_stats_met(self, *args, **kwargs)

    def _available_quest_list(self, *args, **kwargs):
        """委托包内 `content/world_cmds._available_quest_list`（B9 线2 薄壳）。"""
        return _WC._available_quest_list(self, *args, **kwargs)

    @declared("quest_abandon")
    async def quest_abandon(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "quest_abandon", event))

    @declared("daily")
    async def daily(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "daily", event))

    def _daily_pool(self, *args, **kwargs):
        """委托包内 `content/world_cmds._daily_pool`（B9 线2 薄壳）。"""
        return _WC._daily_pool(self, *args, **kwargs)

    def _bump_daily_progress(self, *args, **kwargs):
        """委托包内 `content/world_cmds._bump_daily_progress`（B9 线2 薄壳）。"""
        return _WC._bump_daily_progress(self, *args, **kwargs)

    def _home_view(self, *args, **kwargs):
        """委托包内 `content/world_cmds._home_view`（B9 线2 薄壳）。"""
        return _WC._home_view(self, *args, **kwargs)

    def _current_npcs(self, *args, **kwargs):
        """委托包内 `content/world_cmds._current_npcs`（B9 线2 薄壳）。"""
        return _WC._current_npcs(self, *args, **kwargs)

    def _present_wild_hints(self, *args, **kwargs):
        """委托包内 `content/world_cmds._present_wild_hints`（B9 线2 薄壳）。"""
        return _WC._present_wild_hints(self, *args, **kwargs)

    def _start_talk_list(self, *args, **kwargs):
        """委托包内 `content/world_cmds._start_talk_list`（B9 线2 薄壳）。"""
        return _WC._start_talk_list(self, *args, **kwargs)

    def _find_npc_in_map(self, *args, **kwargs):
        """委托包内 `content/world_cmds._find_npc_in_map`（B9 线2 薄壳）。"""
        return _WC._find_npc_in_map(self, *args, **kwargs)

    def _town_npc_absent_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._town_npc_absent_hint`（B9 线2 薄壳）。"""
        return _WC._town_npc_absent_hint(self, *args, **kwargs)

    def _player_map_name(self, *args, **kwargs):
        """委托包内 `content/world_cmds._player_map_name`（B9 线2 薄壳）。"""
        return _WC._player_map_name(self, *args, **kwargs)

    def _subarea_name(self, *args, **kwargs):
        """委托包内 `content/world_cmds._subarea_name`（B9 线2 薄壳）。"""
        return _WC._subarea_name(self, *args, **kwargs)

    def _find_wild_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds._find_wild_npc`（B9 线2 薄壳）。"""
        return _WC._find_wild_npc(self, *args, **kwargs)

    def _wild_unseen_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._wild_unseen_hint`（B9 线2 薄壳）。"""
        return _WC._wild_unseen_hint(self, *args, **kwargs)

    def _npc_direction_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._npc_direction_hint`（B9 线2 薄壳）。"""
        return _WC._npc_direction_hint(self, *args, **kwargs)

    def _npc_dialogue(self, *args, **kwargs):
        """委托包内 `content/world_cmds._npc_dialogue`（B9 线2 薄壳）。"""
        return _WC._npc_dialogue(self, *args, **kwargs)

    def _take_main_quest(self, *args, **kwargs):
        """委托包内 `content/world_cmds._take_main_quest`（B9 线2 薄壳）。"""
        return _WC._take_main_quest(self, *args, **kwargs)

    def _obj_text(self, *args, **kwargs):
        """委托包内 `content/world_cmds._obj_text`（B9 线2 薄壳）。"""
        return _WC._obj_text(self, *args, **kwargs)

    def _obj_text_lines(self, *args, **kwargs):
        """委托包内 `content/world_cmds._obj_text_lines`（B9 线2 薄壳）。"""
        return _WC._obj_text_lines(self, *args, **kwargs)

    def _quest_reputation(self, *args, **kwargs):
        """委托包内 `content/world_cmds._quest_reputation`（B9 线2 薄壳）。"""
        return _WC._quest_reputation(self, *args, **kwargs)

    def _wild_cond_label(self, *args, **kwargs):
        """委托包内 `content/world_cmds._wild_cond_label`（B9 线2 薄壳）。"""
        return _WC._wild_cond_label(self, *args, **kwargs)

    @declared("time_cmd")
    async def time_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "time_cmd", event))

    @declared("wild_notes")
    async def wild_notes(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "wild_notes", event))

    @declared("npc_quick_dialog", priority=100)
    async def npc_quick_dialog(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "npc_quick_dialog", event))

    def find_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds.find_npc`（B9 线2 薄壳）。"""
        return _WC.find_npc(self, *args, **kwargs)

    def _grant_wild_unlock_flags(self, *args, **kwargs):
        """委托包内 `content/world_cmds._grant_wild_unlock_flags`（B9 线2 薄壳）。"""
        return _WC._grant_wild_unlock_flags(self, *args, **kwargs)

    def _teach_by_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds._teach_by_npc`（B9 线2 薄壳）。"""
        return _WC._teach_by_npc(self, *args, **kwargs)

    @declared("interact_prop")
    async def interact_prop(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "interact_prop", event))

    def _talk_active(self, *args, **kwargs):
        """委托包内 `content/world_cmds._talk_active`（B9 线2 薄壳）。"""
        return _WC._talk_active(self, *args, **kwargs)

    def _talk_ctx(self, *args, **kwargs):
        """委托包内 `content/world_cmds._talk_ctx`（B9 线2 薄壳）。"""
        return _WC._talk_ctx(self, *args, **kwargs)

    def _side_menu_expand(self, *args, **kwargs):
        """委托包内 `content/world_cmds._side_menu_expand`（B9 线2 薄壳）。"""
        return _WC._side_menu_expand(self, *args, **kwargs)

    def _render_talk_node(self, *args, **kwargs):
        """委托包内 `content/world_cmds._render_talk_node`（B9 线2 薄壳）。"""
        return _WC._render_talk_node(self, *args, **kwargs)

    def _branch_wait_sid(self, *args, **kwargs):
        """委托包内 `content/world_cmds._branch_wait_sid`（B9 线2 薄壳）。"""
        return _WC._branch_wait_sid(self, *args, **kwargs)

    def _weapon_pick_active(self, *args, **kwargs):
        """委托包内 `content/world_cmds._weapon_pick_active`（B9 线2 薄壳）。"""
        return _WC._weapon_pick_active(self, *args, **kwargs)

    def _weapon_pick_choose(self, *args, **kwargs):
        """委托包内 `content/world_cmds._weapon_pick_choose`（B9 线2 薄壳）。"""
        return _WC._weapon_pick_choose(self, *args, **kwargs)

    def _remove_one_by_name(self, *args, **kwargs):
        """委托包内 `content/world_cmds._remove_one_by_name`（B9 线2 薄壳）。"""
        return _WC._remove_one_by_name(self, *args, **kwargs)

    def _update_use_quests(self, *args, **kwargs):
        """委托包内 `content/world_cmds._update_use_quests`（B9 线2 薄壳）。"""
        return _WC._update_use_quests(self, *args, **kwargs)

    def _talk_quest_progress(self, *args, **kwargs):
        """委托包内 `content/world_cmds._talk_quest_progress`（B9 线2 薄壳）。"""
        return _WC._talk_quest_progress(self, *args, **kwargs)

    def _do_join_class(self, *args, **kwargs):
        """委托包内 `content/world_cmds._do_join_class`（B9 线2 薄壳）。"""
        return _WC._do_join_class(self, *args, **kwargs)

    def _do_evolve_via_npc(self, *args, **kwargs):
        """委托包内 `content/world_cmds._do_evolve_via_npc`（B9 线2 薄壳）。"""
        return _WC._do_evolve_via_npc(self, *args, **kwargs)

    def _apply_talk_action_async(self, *args, **kwargs):
        """委托包内 `content/world_cmds._apply_talk_action_async`（B9 线2 薄壳）。"""
        return _WC._apply_talk_action_async(self, *args, **kwargs)

    def _apply_talk_action(self, *args, **kwargs):
        """委托包内 `content/world_cmds._apply_talk_action`（B9 线2 薄壳）。"""
        return _WC._apply_talk_action(self, *args, **kwargs)

    @declared("talk_choice")
    async def talk_choice(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "talk_choice", event))

    def _deliver_hint(self, *args, **kwargs):
        """委托包内 `content/world_cmds._deliver_hint`（B9 线2 薄壳）。"""
        return _WC._deliver_hint(self, *args, **kwargs)

    def _side_available_list(self, *args, **kwargs):
        """委托包内 `content/world_cmds._side_available_list`（B9 线2 薄壳）。"""
        return _WC._side_available_list(self, *args, **kwargs)

    def _offer_side_quest(self, *args, **kwargs):
        """委托包内 `content/world_cmds._offer_side_quest`（B9 线2 薄壳）。"""
        return _WC._offer_side_quest(self, *args, **kwargs)

    def _offer_side_quests(self, *args, **kwargs):
        """委托包内 `content/world_cmds._offer_side_quests`（B9 线2 薄壳）。"""
        return _WC._offer_side_quests(self, *args, **kwargs)

    @declared("turn_in")
    async def turn_in(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "turn_in", event))

    def _grant_quest_rewards(self, *args, **kwargs):
        """委托包内 `content/world_cmds._grant_quest_rewards`（B9 线2 薄壳）。"""
        return _WC._grant_quest_rewards(self, *args, **kwargs)

    def _complete_side_quest(self, *args, **kwargs):
        """委托包内 `content/world_cmds._complete_side_quest`（B9 线2 薄壳）。"""
        return _WC._complete_side_quest(self, *args, **kwargs)

    @declared("rest_camp")
    async def rest_camp(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "rest_camp", event))

    @declared("rest")
    async def rest(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "rest", event))

    @declared("reputation")
    async def reputation(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "reputation", event))

    @declared("rep_shop")
    async def rep_shop(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "rep_shop", event))

    def _camp_ctx(self, *args, **kwargs):
        """委托包内 `content/world_cmds._camp_ctx`（B9 线2 薄壳）。"""
        return _WC._camp_ctx(self, *args, **kwargs)

    def _camp_save(self, *args, **kwargs):
        """委托包内 `content/world_cmds._camp_save`（B9 线2 薄壳）。"""
        return _WC._camp_save(self, *args, **kwargs)

    @declared("camp_join")
    async def camp_join(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "camp_join", event))

    @declared("camp_task")
    async def camp_task(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "camp_task", event))

    @declared("camp_shop")
    async def camp_shop(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "camp_shop", event))

    @declared("camp_rank")
    async def camp_rank(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "camp_rank", event))

    @declared("chronicle")
    async def chronicle(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "chronicle", event))
