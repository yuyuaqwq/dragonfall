# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层（game/services，v181 P4 命令层抽 services）

ARCHITECTURE.md v47 蓝图：data ← core ← store ← services ← commands ← main。
services 可 import：game.data / game.core（含 C 聚合）/ game.store / game.reward /
同级 services；禁止 import：game.commands.*（任何文件、任何符号——防环）。

每个文件是一个纯函数模块（零类零装饰器零 async generator yield），命令层只留
解析+守卫+壳。本包聚合导出（与 store/__init__.py 同款）。

⚠️ db 只在函数体内惰性 import（防 data/_assembly 加载期被 import 时循环——core 样板铁律）。
"""
from .quests import (  # noqa: F401
    DAILY_LIMIT, DAILY_META_KEYS, DAILY_REPEAT_FACTORS,
    daily_repeat_pct, daily_need,
    settle_daily_quest, bump_daily_progress,
    daily_pool, draw_daily,
)
from .quests_flow import (  # noqa: F401
    obj_text, sq_unlocked, sq_stats_met, available_quest_list,
    update_explore_quests, take_main_quest, quest_reputation, deliver_hint,
    side_available_list, offer_side_quest, offer_side_quests,
    grant_quest_rewards, complete_side_quest, talk_quest_progress,
    update_use_quests, branch_wait_sid, quest_kill_progress,
)
from .shop import (  # noqa: F401
    SHOP_EQUIP_PRICE_MULT,
    req_label, equip_price, equip_roster, buy_weapon,
    cur_subarea, is_smith_shop, pawn_rate, is_quest_item,
    fish_weight_max, sell_one, apprentice_protect_mats,
    buy_index_dispatch, buy_weapon_fn, limit_buy_guard, limit_label,
)
from .crafting import (  # noqa: F401
    ENHANCE_STONE_REFINE, ENHANCE_STONE_BLESSED, ENHANCE_STONE_PROTECT,
    compute_enhance_rate, enhance_fail_floor,
)
from .auction import (  # noqa: F401
    settle_auction, settle_expired_auction, save_auction_state,
)
from .party import (  # noqa: F401
    resolve_party_target, party_in_battle, target_in_battle, party_view_lines,
    party_join, party_leave_check, party_leave_inst_member, party_leave_execute,
)
from .guild import (  # noqa: F401
    guild_create_check, guild_create, guild_join, guild_leave_check,
    guild_leave, guild_disband, guild_sign, guild_task_view,
    guild_donate_inventory, guild_donate_total, guild_donate,
    guild_rank_lines, guild_appoint_check_role, guild_appoint_level_ok,
    guild_find_member, guild_appoint, guild_demote, guild_kill_progress,
)
from .profession import (  # noqa: F401
    MINING_FATIGUE_THRESHOLD, MINING_FATIGUE_RECOVER,
    FISHING_SURPRISE_TRIGGER, FISHING_SURPRISE_BP, FISHING_SURPRISE_EQ,
    FISHING_SURPRISE_RUNE, FISHING_SURPRISE_GEM,
    validate_gather_cond,
    prof_wait_expire_cb, gather_roll, gather_cond_roll,
    prof_wait_key, prof_wait_ev_name, prof_wait_compat, prof_wait_residual,
    prof_wait_state, prof_wait_clear, prof_wait_duration, prof_wait_begin,
    prof_settle, prof_wait_flow,
    settle_fishing, fishing_surprise_fn, collect_bonus_line,
    settle_gather, mining_fatigue_state, mining_fatigue_tick, mining_fatigued,
    settle_mining,
)
from .travel import (  # noqa: F401
    AMBUSH_HIGH_MIN, AMBUSH_HIGH_STEP, AMBUSH_HIGH_CAP, AMBUSH_MID, AMBUSH_LOW,
    visible_sas, conn_target, conn_subarea_name, subarea_hidden_block,
    resolve_map_target, move_blocked_msg, leave_map_block_msg, level_warn,
    stamina_max, stamina_tired_line, move_stamina_cost, travel_ambush,
    hidden_map_block, landing_subarea, portal_arrive_note,
)
