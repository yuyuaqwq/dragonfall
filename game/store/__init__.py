# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年存储层 —— SQLite Repository（唯一碰 DB 的层）

按领域拆分：
- connection: 连接/锁/建表
- players:    玩家/群归属/传送点/技能栏
- inventory:  背包物品
- quests:     任务
- battle_state: 战斗状态
- stats:      统计/成就
- social:     声望/签到/市场/组队/公会/宠物
- world:      图鉴/到访/世界事件/垂钓
- feedback:   意见箱

聚合导出全部函数，保持 `db.xxx` 调用兼容。
"""
from .connection import (  # noqa: F401
    DB_PATH, C_MAP_IDS, _connect, _lock, init_db, atomic,
)
# B-RPH 聚合门收口：players/quests/stats/professions/feedback/props_use 六个委托薄壳已删；
# 真源直取包内存档层（`content/persistence/__init__.py` 同名聚合）。
# ★ `battle_state` 保留：tests/test_battle_n5b4_pvp.py:390 直取宿主模块
#   `game.store.battle_state` 的 `_lock`/`_connect` → 消费者含 tests，归 D 组，本批不动。
from content.persistence import (  # noqa: F401
    # players
    record_player_group, get_player_groups, get_group_players,
    create_player, get_player, find_player_by_name, update_player,
    top_players, all_players, get_portals, add_portal,
    get_skill_bar, set_skill_bar, delete_player,
    # quests
    get_quests, save_quests, expire_daily,
    # stats
    init_stats, bump_stats, get_stats, set_achievement, get_achievements,
    # professions
    get_professions, get_prof_level, add_prof_exp, prof_top,
    bump_fish_king, get_fish_king, PROF_FIELDS,
    MAX_ACTIVE_PROFS, get_activated_profs, activate_prof, forget_prof,
    # feedback
    add_feedback, get_feedback,
    # props_use
    get_props_use, mark_props_use, props_use_claim_atomic,
)
from .inventory import (  # noqa: F401
    _key_to_id, add_item, get_inventory, count_item, remove_item,
    update_item_data, sell_item_atomic,
    # v168 冒险手册：曾拥有物品
    record_possessed, record_possessed_conn,
    get_possessed, get_possessed_rows, count_possessed,
)
from .battle_state import save_battle, get_battle, get_battle_raw, clear_battle  # noqa: F401
from .social import (  # noqa: F401
    add_reputation, get_reputation, get_signin, save_signin, signin_claim,
    market_list, market_add, market_remove,
    market_list_by_seller, market_get, market_sync_stall, market_remove_by_seller,
    market_buy_atomic, market_stall_sell_atomic, market_exchange_atomic,
    party_create, party_add, party_members, party_leave,
    guild_create, guild_get_by_leader, guild_get_by_member,
    guild_get_by_name, guild_members, guild_join, guild_leave,
    guild_add_exp, guild_set_sign, guild_get_sign,
    guild_set_task, guild_get_task, guild_top,
    pet_get, pet_create, pet_update, pet_delete,
    pet_decay_satiety, pet_dex_get, pet_dex_add,
)
from .world import (  # noqa: F401
    bump_fishing, get_fishing_total, bump_bestiary, get_bestiary,
    add_visited, get_visited_count, get_world_event, save_world_event,
    clear_world_event, get_event_state, set_event_state, delete_event_state,
    get_talk_state, set_talk_state, clear_talk_state, talk_state_key,
    get_talk_flags, set_talk_flag, get_boss_dmg_mult,
    cleanup_stale_event_state,
    home_storage_deposit_atomic, home_storage_take_atomic,
    # v115 探索见闻：子区域级到访
    add_visited_subarea, get_visited_subareas, count_visited_subareas,
    # v168 冒险手册：子区域到访明细（含首访时间）
    get_visited_subareas_rows,
)
