# -*- coding: utf-8 -*-
"""《剑与魔法》存储层 —— SQLite Repository（唯一碰 DB 的层）

按领域拆分：
- connection: 连接/锁/建表
- players:    玩家/群归属/传送点/技能栏
- inventory:  背包物品
- quests:     任务
- battle_state: 战斗状态
- stats:      统计/成就
- social:     声望/签到/市场/组队/公会/宠物
- world:      图鉴/到访/世界事件/钓鱼
- feedback:   意见箱

聚合导出全部函数，保持 `db.xxx` 调用兼容。
"""
from .connection import (  # noqa: F401
    DB_PATH, C_MAP_IDS, _connect, _lock, init_db,
)
from .players import (  # noqa: F401
    record_player_group, get_player_groups, get_group_players,
    create_player, get_player, find_player_by_name, update_player,
    top_players, all_players, get_portals, add_portal,
    get_skill_bar, set_skill_bar, delete_player,
)
from .inventory import (  # noqa: F401
    _key_to_id, add_item, get_inventory, count_item, remove_item,
)
from .quests import get_quests, save_quests  # noqa: F401
from .battle_state import save_battle, get_battle, clear_battle  # noqa: F401
from .stats import (  # noqa: F401
    init_stats, bump_stats, get_stats, set_achievement, get_achievements,
)
from .professions import (  # noqa: F401
    get_professions, get_prof_level, add_prof_exp, prof_top,
    bump_fish_king, get_fish_king, PROF_FIELDS,
)
from .social import (  # noqa: F401
    add_reputation, get_reputation, get_signin, save_signin,
    market_list, market_add, market_remove,
    party_create, party_add, party_members, party_leave,
    guild_create, guild_get_by_leader, guild_get_by_member, guild_get,
    guild_get_by_name, guild_members, guild_join, guild_leave, guild_kick,
    guild_count, guild_add_exp, guild_set_sign, guild_get_sign,
    guild_set_task, guild_get_task, guild_top,
    pet_get, pet_create, pet_update, pet_delete,
)
from .world import (  # noqa: F401
    bump_fishing, get_fishing_total, bump_bestiary, get_bestiary,
    add_visited, get_visited_count, get_world_event, save_world_event,
    clear_world_event, get_event_state, set_event_state, delete_event_state,
)
from .feedback import (  # noqa: F401
    add_feedback, get_feedback, mark_feedback_done,
    ensure_feedback_reply_col, get_feedback_with_reply, mark_feedback_broadcast,
)
