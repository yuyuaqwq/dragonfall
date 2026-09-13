# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - instance_run.py —— **B11-L2 薄壳**（副本运行态适配层）

真源（唯一实现）已进包：`framework/games/orlandia/content/flow/instance_run.py`
（名单 `Roster` / 进度 `Progress` / 剩余池 / 资源预算 / 清战斗视图，五种形状的唯一来源）。

本文件只剩一件事：**宿主独有的取数入口** —— `current_members(group_id, st)` 的「当前队伍」
来自 `db.party_members(group_id, leader)`（组队是平台/DB 语义，留宿主）；`members ∩ 队伍`
的过滤本体在包内 `current_members(st, party)`。其余名字（函数 + 池名/预算名/清空键常量）
一律从包内**再导出**，名字/签名与改造前逐字一致：

    roster_of / write_roster / alive_of / set_alive / living_members / living_players /
    sort_members_by / stages_progress / write_stages_progress / stage_count / is_last_stage /
    stage_name / pending_left / pending_take / stage_advance / rooms_progress /
    write_rooms_progress / monsters_left / take_monster / poi_left / take_poi /
    mark_boss_room_done / spend_gold / spend_mat / spend_equip / clear_battle_view /
    clear_pet_hits / _stage_index + POOL_UNITS / POOL_MONSTERS / POOL_POIS /
    BUDGET_GOLD / BUDGET_MATS / BUDGET_EQUIP / BATTLE_VIEW_KEYS

存档红线不变：`st` 的键名/类型/缺失语义一律不动（本文件是「读 → 构造视图 → 写回」的取数端）。
调用点零改动：`commands/instance.py`、`commands/instance_router.py`、`core/poi_effects.py`、测试
（`tests/test_v185_instance_run.py` 用 `IR.current_members(GID, st)` / `IR.living_players(st)` 等）。
"""
from __future__ import annotations

from saintess_engine.run import Progress, Roster                 # 与改造前同名单（类型面）

from .. import bootstrap as _BST

_BST.package_apply()                                      # 本进程唯一包加载口（幂等；失败抛）
from content.flow import instance_run as _G           # noqa: E402  包内实现（唯一真源）


# ======================================================================
# 一、宿主独有：队伍取数入口（组队 = 平台/DB 语义，留宿主；过滤本体在包内）
# ======================================================================


def current_members(group_id: str, st: dict) -> list:
    """当前仍在队伍中的副本成员（宿主侧取数：`db.party_members`；`members ∩ 队伍` 在包内）。"""
    from .. import db
    return _G.current_members(st, db.party_members(group_id, st.get("leader")))


# ======================================================================
# 二、包内实现再导出（名字/签名/返回与改造前逐字一致）
# ======================================================================
roster_of = _G.roster_of
write_roster = _G.write_roster
alive_of = _G.alive_of
set_alive = _G.set_alive
living_members = _G.living_members
living_players = _G.living_players
sort_members_by = _G.sort_members_by

_stage_index = _G._stage_index
stages_progress = _G.stages_progress
write_stages_progress = _G.write_stages_progress
stage_count = _G.stage_count
is_last_stage = _G.is_last_stage
stage_name = _G.stage_name
pending_left = _G.pending_left
pending_take = _G.pending_take
stage_advance = _G.stage_advance

rooms_progress = _G.rooms_progress
write_rooms_progress = _G.write_rooms_progress
monsters_left = _G.monsters_left
take_monster = _G.take_monster
poi_left = _G.poi_left
take_poi = _G.take_poi
mark_boss_room_done = _G.mark_boss_room_done
spend_gold = _G.spend_gold
spend_mat = _G.spend_mat
spend_equip = _G.spend_equip

clear_battle_view = _G.clear_battle_view
clear_pet_hits = _G.clear_pet_hits

# 池名 / 预算名 / 清空键（内容侧字符串；引擎不解释它们）
POOL_UNITS = _G.POOL_UNITS
POOL_MONSTERS = _G.POOL_MONSTERS
POOL_POIS = _G.POOL_POIS
BUDGET_GOLD = _G.BUDGET_GOLD
BUDGET_MATS = _G.BUDGET_MATS
BUDGET_EQUIP = _G.BUDGET_EQUIP
BATTLE_VIEW_KEYS = _G.BATTLE_VIEW_KEYS
