# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层（game/services，v181 P4 命令层抽 services）

与 game/core/ 对等（ARCHITECTURE.md v47 蓝图预留的"服务层"位置）：
- 每域一文件（quests/shop/crafting/…）、纯函数模块、零类零装饰器
- 依赖方向：可 import data/core/store/db/engine/battle/reward 及同级 services；
  禁止 import commands/*（防环 + 命令依赖方向约束）
- db 等依赖一律函数体内惰性 import（防 data/_assembly 加载期循环）
"""
from .quests import (  # noqa: F401
    DAILY_LIMIT, DAILY_META_KEYS, DAILY_REPEAT_FACTORS,
    daily_repeat_pct, daily_need,
    settle_daily_quest, bump_daily_progress,
    daily_pool, draw_daily,
)
from .auction import (  # noqa: F401
    settle_auction, settle_expired_auction, save_auction_state,
)
