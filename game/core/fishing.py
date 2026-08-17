# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - fishing.py（16 章品质垂钓 v2.0）

roll 流程：垂钓等级查五档权重表（中间等级线性插值）→ 过滤钓点禁出档位 → 选档位
→ 档位内按品种权重选（过滤品种限定水域）。
"""
import random

from ..data.fishing import (
    FISHING_SPOTS,
    FISH_POOL,
    FISH_QUALITY_WEIGHTS,
    FISH_COLLECT,
)
from ..data import FISH_QUALITY_ORDER  # v101.25i6 别名：= QUALITY_ORDER
from .time_weather import current_season  # v116 季节限定：垂钓随季节变化


def _quality_weights(prof_lv: int) -> list:
    """垂钓等级 → 五档权重(Lv.1/3/5/7/9 查表，中间等级线性插值)。"""
    lv = max(1, min(9, int(prof_lv)))
    keys = sorted(FISH_QUALITY_WEIGHTS)
    if lv <= keys[0]:
        return list(FISH_QUALITY_WEIGHTS[keys[0]])
    if lv >= keys[-1]:
        return list(FISH_QUALITY_WEIGHTS[keys[-1]])
    for a, b in zip(keys, keys[1:]):
        if a <= lv <= b:
            wa = FISH_QUALITY_WEIGHTS[a]
            wb = FISH_QUALITY_WEIGHTS[b]
            t = (lv - a) / (b - a)
            return [wa[i] + (wb[i] - wa[i]) * t for i in range(len(wa))]
    return list(FISH_QUALITY_WEIGHTS[keys[0]])


def roll_fish(prof_lv: int = 1, spot_id: str | None = None, bait: str | None = None):
    """垂钓结果：返回 FISH_POOL 中的一项。

    prof_lv: 垂钓副业等级（1-9）
    spot_id: 钓点地图 ID（FISHING_SPOTS 的 key）；钓点禁出档位权重清零，
             品种限定水域（spots 字段）不满足时跳过。
    bait: v102.3 鱼饵加成（glow=紫橙×2 / dough=绿蓝×1.5 / blood=稀有鱼种×3）
    v116 季节限定：season 硬限定鱼的季节不匹配时跳过；season_boost 偏好的季节权重 ×1.5。
           若某档位在当前季节被硬限定过滤空，则放宽为「不限定季节」重试，避免钓空。
    """
    spot = FISHING_SPOTS.get(spot_id) if spot_id else None
    ban = set(spot.get("ban_quality", [])) if spot else set()
    weights = _quality_weights(prof_lv)
    for i, q in enumerate(FISH_QUALITY_ORDER):
        if q in ban:
            weights[i] = 0.0
    # v102.3 鱼饵品质加权（在禁出档位清零之后应用，ban 优先）
    if bait == "glow":
        for i, q in enumerate(FISH_QUALITY_ORDER):
            if q in ("purple", "orange"):
                weights[i] *= 2.0
    elif bait == "dough":
        for i, q in enumerate(FISH_QUALITY_ORDER):
            if q in ("green", "blue"):
                weights[i] *= 1.5
    quality = random.choices(FISH_QUALITY_ORDER, weights=weights, k=1)[0]

    # v116 当前季节（spring/summer/autumn/winter，与 time_weather.current_season 对齐）
    season = current_season()

    def _spots_ok(f):
        return not f.get("spots") or (spot_id and spot_id in f["spots"])

    def _season_ok(f):
        # 硬限定鱼仅当季节匹配才产出；无 season 字段 = 全年可钓
        return not f.get("season") or f["season"] == season

    # 第一步：档位 + 水域 + 季节 三重过滤（季节限定生效）
    pool = [f for f in FISH_POOL
            if f["quality"] == quality and _spots_ok(f) and _season_ok(f)]
    if not pool:
        # 兜底一：本档位在当前季节被限定鱼占满 → 放宽季节限制（仍守水域，避免越界钓点）
        pool = [f for f in FISH_POOL if f["quality"] == quality and _spots_ok(f)]
    if not pool:
        # 防御性兜底二：再退全品质池（原有逻辑，如新钓点蓝档无全水域品种）
        pool = [f for f in FISH_POOL if f["quality"] == quality]
    # v102.3 血饵：稀有鱼种（权重 ≤ 15）品种权重 ×3
    # v104 M15 修复：原阈值 <5 高于 FISH_POOL 实际最低权重(10)，血饵永不生效（20 万竿采样零效果）；
    # 改为 ≤15 覆盖盲鱼/云棉/深渊珍珠/彩虹露珠/风暴贝/鲸须草等稀有鱼种
    if bait == "blood":
        pool_w = [f.get("weight", 1) * (3 if f.get("weight", 1) <= 15 else 1) for f in pool]
    else:
        pool_w = [f.get("weight", 1) for f in pool]
    # v116 季节偏好：season_boost 匹配当前季节的鱼权重 ×1.5（非限定，仅概率上升）
    pool_w = [w * 1.5 if f.get("season_boost") == season else w
              for f, w in zip(pool, pool_w)]
    pick = random.choices(pool, weights=pool_w, k=1)[0]
    # v116 季节感输出标记：命中限定/偏好鱼时，在浅拷贝上附加季节前缀供展示层读取
    # （不直接在共享 FISH_POOL 上写字段，避免污染数据）
    if pick.get("season") == season or pick.get("season_boost") == season:
        pick = dict(pick)
        pick["_season_prefix"] = {"spring": "🌸限定", "summer": "☀️限定",
                                  "autumn": "🍂限定", "winter": "❄️限定"}[season]
    return pick

def roll_fish_size_weight(fish: dict):
    """v126.1 鱼获随机波动：百分位均匀分布在品种 size_range/weight_range 区间内插值。

    返回 {"size": float(cm), "weight": float(kg)}（保留 1 位小数）；品种未配区间
    （老数据/测试桩）返回 None，调用方跳过入明细——出售按 1.0 原价，行为与旧版一致。
    v126.4 审计 P2：重量精度按量级自适应——低于 0.1kg 的品种（珍珠类 0.01-0.05kg）
    原 round(weight,1) 几乎 100% 舍入成 0.0（播报 0.0kg + 加权系数恒 0.5 失效），
    现 <0.1kg 保留 3 位小数（0.045），≥0.1kg 保留 1 位。
    """
    sr = fish.get("size_range")
    wr = fish.get("weight_range")
    if not sr or not wr or len(sr) < 2 or len(wr) < 2:
        return None
    size = sr[0] + (sr[1] - sr[0]) * random.random()
    weight = wr[0] + (wr[1] - wr[0]) * random.random()
    if weight < 0.1:
        return {"size": round(size, 1), "weight": round(weight, 3)}
    return {"size": round(size, 1), "weight": round(weight, 1)}

def roll_collect_fish(spot_id: str | None = None, is_night: bool = False):
    """彩蛋收藏鱼判定（16 章 4.x）：五档之外独立判定。

    概率升序判定（最稀有优先），命中即返回，最多 1 条。
    spot_id: 钓点地图 ID；is_night: 当前是否为夜晚（18 章时间系统）。
    """
    for cf in sorted(FISH_COLLECT, key=lambda x: x["chance"]):
        if cf.get("spots") and (spot_id not in cf["spots"]):
            continue
        if cf.get("time") == "night" and not is_night:
            continue
        if random.random() < cf["chance"]:
            return cf
    return None
