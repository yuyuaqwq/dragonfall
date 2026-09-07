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
from .shop import (  # noqa: F401
    SHOP_EQUIP_PRICE_MULT,
    req_label, equip_price, equip_roster, buy_weapon,
    cur_subarea, is_smith_shop, pawn_rate, is_quest_item,
    fish_weight_max, sell_one, apprentice_protect_mats,
    buy_index_dispatch, buy_weapon_fn, limit_buy_guard, limit_label,
)
from .auction import (  # noqa: F401
    settle_auction, settle_expired_auction, save_auction_state,
)
