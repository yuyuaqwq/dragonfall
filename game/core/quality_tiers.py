# -*- coding: utf-8 -*-
"""品质档位阶梯（v184 搬形状）—— 全项目**唯一**一份档位表。

v184 之前，「品质五档」的顺序/倍率/颜色/中文名 + 各处的权重表在**四处各自维护**：
装备（`data/equipment.QUALITY`）、垂钓（`data/fishing.FISH_QUALITY_WEIGHTS` 与它那份内联副本）、
锻造货架（`core/smith_stock.QUALITY_WEIGHTS`）、签到（`SIGNIN_CONFIG.week_quality_weights`），
外加坐骑/宠物又各抄一遍顺序。现在**顺序与取值只有一份**，全部经 `saintess_engine.loot.TierTable`
读取 —— 引擎不认识「品质」二字，它只按档位算。

用法::

    from ..core.quality_tiers import QUALITY_TIERS, FISH_TIERS, quality_of, quality_up
    QUALITY_TIERS.order                       # ('white','green','blue','purple','orange')
    QUALITY_TIERS.info_of("blue")["mult"]     # 1.55
    QUALITY_TIERS.next_tier("blue")           # 'purple'（封顶）
    QUALITY_TIERS.upgrade("blue", chance=0.05)  # 概率升档
    QUALITY_TIERS.resolve("蓝")               # 'blue'（玩家输入别名 → 档位 key）
    FISH_TIERS.weights_at(4)                  # 垂钓等级 → 五档权重（相邻两档线性插值，clamp 1..9）
    FISH_TIERS.pick(level=4, exclude=("orange",))   # 按权重抽一档
"""
from saintess_engine.loot import TierTable

from ..data import (FISH_QUALITY_WEIGHTS, QUALITY, QUALITY_CN, QUALITY_ORDER)

# 装备/通用品质档位（顺序 = QUALITY_ORDER；每档信息 = QUALITY[key]，含倍率/颜色/中文名）
QUALITY_TIERS = TierTable(QUALITY_ORDER, info=QUALITY, aliases=QUALITY_CN)

# 垂钓档位（顺序同 QUALITY_ORDER；权重表按钓点等级，内容侧策略把等级夹在 1..9）
FISH_TIERS = TierTable(QUALITY_ORDER, info=QUALITY, aliases=QUALITY_CN,
                       weights_by_level=FISH_QUALITY_WEIGHTS, clamp=(1, 9))


def quality_of(word):
    """玩家输入 → 档位 key（先当 key，再查中文别名）；认不出 → None。"""
    return QUALITY_TIERS.resolve(word)


def quality_up(quality, *, chance=1.0, steps=1, rng=None):
    """概率升档（封顶）；未知档位 → None。`chance` 与 `rng` 由调用方给（可复现）。"""
    return QUALITY_TIERS.upgrade(quality, chance=chance, steps=steps, rng=rng)
