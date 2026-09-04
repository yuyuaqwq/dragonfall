# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - drop_engine.py（掉落系统统一引擎 v174）

把全游戏散落的掉落池收敛为单一数据表 DROP_POOLS + 统一抽取入口 roll() + 审计 audit_all()。

设计（分层抽象，鱼鱼 2026-09-04 拍板）：
- 统一入口：roll(pool_key, ctx) —— 任何池子都走这里
- 统一数据：DROP_POOLS（game/data/drop_pools.py，纯数据）
- 四种子策略：
    weighted    带权条目抽取（采集/挖掘/通用材料/小怪材料）
    fish        垂钓（质量档→品种；季节/水域/鱼饵过滤）
    table       多层概率表（副本Boss/野王宝箱/垂钓惊喜——各 roll 独立判定）
    fixed       固定掉落（精英专属/必掉清单）

条目引用统一带前缀：
    mat_xxx/物品ID  → 普通物品
    equip:eq_xxx    → 名册装备（generate_roster_equip）
    bp              → 图纸（等级就近 roll_blueprint）
    gem             → 幸运宝石（roll_gem_drop）
    gold:[a,b]      → 金币区间
    rune            → 符文（稀有）
    item:ID         → 带 count 的普通物品
    special:xxx     → 扩展点（调用方注入的 hook，防特殊语义硬编码）
"""
import random
from typing import Any


# ============================================================
# 基础工具
# ============================================================

def _randint(a: int, b: int) -> int:
    return random.randint(a, b)


def _weighted_pick(entries: list[dict]) -> dict | None:
    """从 [{"w": int, ...}, ...] 按权重抽一个；空列表/全 0 返回 None。"""
    if not entries:
        return None
    total = sum(int(e.get("w", 1) or 0) for e in entries)
    if total <= 0:
        return None
    roll = random.random() * total
    acc = 0.0
    for e in entries:
        acc += int(e.get("w", 1) or 0)
        if roll < acc:
            return e
    return entries[-1]


def _resolve_item_ref(ref: str, ctx: Any) -> dict | None:
    """把条目引用解析为实物。返回统一产出 dict 或 None（池空/失败优雅跳过）。

    产出 dict 形态：{"type": "item"/"equip"/"bp"/"gem"/"gold"/"rune", "name":..., "data":..., "count":...}
    """
    import game.content as C  # noqa: E402  绝对导入，防循环/半初始化

    if ref == "bp":
        bp = C.roll_blueprint(max(1, int(getattr(ctx, "player_level", 1) or 1)))
        return {"type": "bp", "data": bp} if bp else None
    if ref == "gem":
        mon = {"lv": getattr(ctx, "monster_lv", None) or getattr(ctx, "player_level", 30),
               "is_boss": True, "map_area": "field"}
        gem = C.roll_gem_drop(mon)
        return {"type": "gem", "data": gem} if gem else None
    if ref == "rune":
        # 稀有符文：蓝/紫品质随机（v168 语义：随机取蓝/紫符文 1 级）
        pool = [k for k, r in C.RUNES.items() if (r.get("quality") or "") in ("blue", "purple")]
        if not pool:
            return None
        rk = random.choice(pool)
        r_def = C.RUNES[rk]
        rune_data = C.rune_item(r_def["effect"], random.randint(1, 2))
        return {"type": "rune", "data": rune_data} if rune_data else None
    if ref.startswith("gold:"):
        # gold:300:600
        parts = ref.split(":")
        a, b = int(parts[1]), int(parts[2]) if len(parts) > 2 else int(parts[1])
        return {"type": "gold", "count": _randint(a, b)}
    if ref.startswith("equip:"):
        rid = ref.split(":", 1)[1]
        try:
            eq = C.generate_roster_equip(rid)
            return {"type": "equip", "data": eq}
        except Exception:
            return None
    if ref.startswith("equip_drop:"):
        # 通用装备掉落（随机）：equip_drop:elite / equip_drop:boss（走 roll_drop_equip 白名单+等级就近）
        role = ref.split(":", 1)[1]
        lv = int(getattr(ctx, "monster_lv", None) or getattr(ctx, "player_level", 1) or 1)
        eq = C.roll_drop_equip(lv, role)
        if eq:
            return {"type": "equip", "data": eq}
        # 兜底：随机生成同品质装备（与旧逻辑 generate_equip 一致）
        if role == "boss":
            slot = random.choice(["weapon", "helm", "armor", "legs", "boots", "ring", "necklace"])
            eq = C.generate_equip(slot, lv + random.randint(-3, 3), "orange")
        elif role == "elite":
            slot = random.choice(["weapon", "helm", "armor", "legs", "boots", "ring", "necklace"])
            eq = C.generate_equip(slot, lv + random.randint(-3, 3), "purple")
        return {"type": "equip", "data": eq} if eq else None
    if ref.startswith("item:"):
        iid = ref.split(":", 1)[1]
        return {"type": "item", "item_id": iid}
    if ref.startswith("special:"):
        hook = ref.split(":", 1)[1]
        if hasattr(ctx, "hooks") and hook in (ctx.hooks or {}):
            try:
                return ctx.hooks[hook](ctx)
            except Exception:
                return None
        return None
    # 普通物品 ID
    return {"type": "item", "item_id": ref}


def _resolve_pool(pool_key: str, pools: dict | None = None) -> dict | None:
    """解析池 key（含内联引用 'weighted:xxx' / 'fixed:xxx' 需在 DROP_POOLS 查）。"""
    if pools is None:
        from game.data.drop_pools import DROP_POOLS  # noqa: E402
        pools = DROP_POOLS
    return pools.get(pool_key)


# ============================================================
# 四种子策略
# ============================================================

def _roll_weighted(pool: dict, ctx: Any) -> list[dict]:
    """带权抽取：默认抽 1（qty 由 ctx 指定）。支持 'count' 指定本池份数。"""
    qty = int(getattr(ctx, "qty", 1) or 1)
    # 过滤：min_lv / max_lv（ctx.player_level 或 monster_lv）
    entries = pool.get("entries", [])
    lv = int(getattr(ctx, "player_level", 0) or getattr(ctx, "monster_lv", 0) or 0)
    cand = []
    for e in entries:
        min_lv = e.get("min_lv")
        max_lv = e.get("max_lv")
        if min_lv and lv and lv < int(min_lv):
            continue
        if max_lv and lv and lv > int(max_lv):
            continue
        cand.append(e)
    # fallback：主池空/权重 0 → 兜底（price_band 由 ctx 提供函数）
    if not cand:
        fb = pool.get("fallback")
        if fb and hasattr(ctx, "fallback_roll"):
            try:
                return ctx.fallback_roll(pool, fb, ctx) or []
            except Exception:
                return []
        return []
    out = []
    for _ in range(qty):
        pick = _weighted_pick(cand)
        if pick:
            r = _resolve_item_ref(pick["item"], ctx)
            if r:
                r["count"] = r.get("count", 1) * int(pick.get("n", 1) or 1)
                out.append(r)
    return out


def _quality_weights_inline(prof_lv: int, weights_table: dict) -> list:
    """垂钓等级 → 五档权重（内联实现，等价 core/fishing._quality_weights，防循环 import）。"""
    lv = max(1, min(9, int(prof_lv)))
    keys = sorted(weights_table)
    if lv <= keys[0]:
        return list(weights_table[keys[0]])
    if lv >= keys[-1]:
        return list(weights_table[keys[-1]])
    for a, b in zip(keys, keys[1:]):
        if a <= lv <= b:
            wa = weights_table[a]
            wb = weights_table[b]
            t = (lv - a) / (b - a)
            return [wa[i] + (wb[i] - wa[i]) * t for i in range(len(wa))]
    return list(weights_table[keys[0]])


def _roll_fish(pool: dict, ctx: Any) -> list[dict]:
    """垂钓：先按钓点禁档/鱼饵/等级定质量档，再从该档品种按权重摸 1 条。

    pool.spot_cfg: {min_lv, ban_quality, subarea}
    pool.quality_weights: {钓点等级: [白绿蓝紫橙五档权重]}（缺省全局 FISH_QUALITY_WEIGHTS）
    pool.entries: [{"item": mat_id, "name":..., "quality":..., "w":..., "spots":...,
                    "season":..., "season_boost":..., "size_range":..., "weight_range":..., ...}]
    """
    import game.content as C  # noqa: E402
    FISH_QUALITY_ORDER = C.FISH_QUALITY_ORDER
    FISH_QUALITY_WEIGHTS = C.FISH_QUALITY_WEIGHTS
    spot_cfg = pool.get("spot_cfg") or {}
    ban = set(spot_cfg.get("ban_quality", []))
    prof_lv = int(getattr(ctx, "prof_lv", 1) or 1)
    bait = getattr(ctx, "bait", None)
    spot_id = getattr(ctx, "map_id", None)
    season = getattr(ctx, "season", None)
    if not season:
        # 内联季节计算（等价 core.time_weather.current_season，纯 datetime 防循环 import）
        try:
            import datetime
            _m = datetime.datetime.now().month
            season = {3: "spring", 4: "spring", 5: "spring",
                      6: "summer", 7: "summer", 8: "summer",
                      9: "autumn", 10: "autumn", 11: "autumn",
                      12: "winter", 1: "winter", 2: "winter"}.get(_m, "spring")
        except Exception:
            season = None

    weights = list(_quality_weights_inline(prof_lv, FISH_QUALITY_WEIGHTS))
    for i, q in enumerate(FISH_QUALITY_ORDER):
        if q in ban:
            weights[i] = 0.0
    if bait == "glow":
        for i, q in enumerate(FISH_QUALITY_ORDER):
            if q in ("purple", "orange"):
                weights[i] *= 2.0
    elif bait == "dough":
        for i, q in enumerate(FISH_QUALITY_ORDER):
            if q in ("green", "blue"):
                weights[i] *= 1.5
    quality = random.choices(FISH_QUALITY_ORDER, weights=weights, k=1)[0]

    def _spots_ok(f):
        sp = f.get("spots")
        return not sp or (spot_id and spot_id in sp)

    def _season_ok(f):
        return not f.get("season") or f.get("season") == season

    entries = pool.get("entries", [])
    pool_by_q = [f for f in entries if f.get("quality") == quality and _spots_ok(f) and _season_ok(f)]
    if not pool_by_q:
        pool_by_q = [f for f in entries if f.get("quality") == quality and _spots_ok(f)]
    if not pool_by_q:
        pool_by_q = [f for f in entries if f.get("quality") == quality]
    if not pool_by_q:
        return []
    # 血饵稀有 ×3
    if bait == "blood":
        pool_w = [int(f.get("w", 1)) * (3 if int(f.get("w", 1)) <= 15 else 1) for f in pool_by_q]
    else:
        pool_w = [int(f.get("w", 1)) for f in pool_by_q]
    # 季节偏好 ×1.5
    if season:
        pool_w = [w * 1.5 if f.get("season_boost") == season else w
                  for f, w in zip(pool_by_q, pool_w)]
    pick = random.choices(pool_by_q, weights=pool_w, k=1)[0]
    # 构造鱼条目返回（与旧 fishing.roll_fish 同形态：含 name/quality/type/price/size_range...）
    fish = dict(pick)
    fish["name"] = fish.get("name") or fish.get("item")
    return [{"type": "fish", "data": fish}]


def _roll_table(pool: dict, ctx: Any) -> list[dict]:
    """多层概率表：每个 roll 独立判定（副本Boss/野王宝箱/垂钓惊喜）。

    pool.rolls: [{"pool": 子池key/内联引用/"gold:a:b"/特殊, "chance": 0-1, "n": [a,b]|int, ...}]
    """
    out = []
    for roll_cfg in pool.get("rolls", []):
        chance = float(roll_cfg.get("chance", 1.0))
        if chance < 1.0 and random.random() >= chance:
            continue
        sub = roll_cfg.get("pool", "")
        if sub.startswith("gold:"):
            r = _resolve_item_ref(sub, ctx)
            if r:
                out.append(r)
            continue
        # n 数量（[a,b] 区间或 int）
        n = roll_cfg.get("n")
        if isinstance(n, (list, tuple)) and len(n) >= 2:
            qty = _randint(int(n[0]), int(n[1]))
        elif isinstance(n, int):
            qty = n
        else:
            qty = 1
        # 子池抽取
        sub_ctx = _sub_ctx(ctx, qty)
        if sub and sub in (_get_pools()):
            sub_pool = _get_pools()[sub]
            out.extend(POOL_STRATEGIES.get(sub_pool.get("type"), _roll_weighted)(sub_pool, sub_ctx))
        elif sub:
            r = _resolve_item_ref(sub, ctx)
            if r:
                r["count"] = r.get("count", 1) * qty
                out.append(r)
    return out


def _roll_fixed(pool: dict, ctx: Any) -> list[dict]:
    """固定掉落：entries 全给（必掉清单）。"""
    out = []
    for e in pool.get("entries", []):
        r = _resolve_item_ref(e["item"], ctx)
        if r:
            r["count"] = r.get("count", 1) * int(e.get("n", 1) or 1)
            out.append(r)
    return out


POOL_STRATEGIES = {
    "weighted": _roll_weighted,
    "fish": _roll_fish,
    "table": _roll_table,
    "fixed": _roll_fixed,
}


def _sub_ctx(ctx: Any, qty: int) -> Any:
    """子池抽取上下文（复制一份改 qty，避免污染原 ctx）。"""
    try:
        import copy
        c = copy.copy(ctx)
        c.qty = qty
        return c
    except Exception:
        return ctx


def _get_pools() -> dict:
    from game.data.drop_pools import DROP_POOLS  # noqa: E402
    return DROP_POOLS


# ============================================================
# 统一入口
# ============================================================

def roll(pool_key: str, ctx: Any = None, **kw) -> list[dict]:
    """任何池子唯一抽取入口。

    用法：
      roll("gather:oak_plain", ctx)                     # ctx 带 map_id/player_level/...
      roll("gather:oak_plain", ctx, qty=2)
      roll("chest:wild_low", ctx)
    返回产出 dict 列表；池不存在/抽空返回 []（优雅跳过，不抛错）。
    """
    pools = _get_pools()
    pool = pools.get(pool_key)
    if not pool:
        return []
    if ctx is None:
        ctx = _SimpleCtx(**kw)
    elif kw:
        for k, v in kw.items():
            setattr(ctx, k, v)
    strategy = POOL_STRATEGIES.get(pool.get("type", "weighted"), _roll_weighted)
    try:
        return strategy(pool, ctx) or []
    except Exception:
        return []


def expand_pool(pool_key: str) -> list:
    """返回池的带权展开候选 ID 列表（weighted 池按权重展开；fixed 池返回全部）。

    用途：命令层需要"候选池 + 自己多次 choice"的旧语义时（如采集按副业等级选 N 份），
    数据源统一走 DROP_POOLS。池不存在返回 []（调用方走兜底）。
    """
    pools = _get_pools()
    pool = pools.get(pool_key)
    if not pool:
        return []
    ptype = pool.get("type", "weighted")
    if ptype == "fixed":
        return [e.get("item", "") for e in pool.get("entries", []) if e.get("item")]
    if ptype == "table":
        out = []
        for rc in pool.get("rolls") or []:
            sub = rc.get("pool", "")
            if sub in pools:
                out.extend(expand_pool(sub))
            elif sub.startswith(("equip:", "item:", "gold:")):
                out.append(sub)
        return out
    # weighted / fish：按权重展开（等价旧实现 [m for m,_w in pool for _ in range(_w)]）
    entries = pool.get("entries", [])
    out = []
    for e in entries:
        w = int(e.get("w", 1) or 1)
        it = e.get("item", "")
        if not it:
            continue
        # 展开上限保护：w 异常巨大（>1000）时按 1 处理（防内存爆炸）
        w = min(w, 1000)
        out.extend([it] * w)
    return out


class _SimpleCtx:
    """极简上下文：无 Attr 报错，属性缺失返回 None/0。"""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.hooks = kw.get("hooks") or {}

    def __getattr__(self, name):
        return None


# ============================================================
# 全量审计
# ============================================================

def audit_all() -> dict:
    """全量审计：断链/空池/权重/等级匹配/重复。

    返回 {"issues": [...], "pool_count": N, "entry_count": M}
    每个 issue: (级别, 池key, 描述)
    """
    import game.content as C  # noqa: E402
    pools = _get_pools()
    issues = []

    # 有效引用集合
    valid_ids = set(C.ITEMS.keys())
    valid_rids = set(C.EQUIP_ROSTER.keys())
    special_refs = {"bp", "gem", "rune"}
    for pool_key, pool in pools.items():
        ptype = pool.get("type", "weighted")
        entries = pool.get("entries") or []
        for e in entries:
            ref = e.get("item", "")
            if not ref:
                issues.append(("断链", pool_key, f"条目无 item: {e}"))
                continue
            if ref in special_refs or ref.startswith(("gold:", "item:", "special:", "equip_drop:")):
                continue
            if ref.startswith("equip:"):
                rid = ref.split(":", 1)[1]
                if rid not in valid_rids:
                    issues.append(("断链", pool_key, f"equip 名册缺失: {rid}"))
            elif ref.startswith("mat_") or ref in valid_ids:
                if ref not in valid_ids:
                    issues.append(("断链", pool_key, f"物品缺失: {ref}"))
            elif ref not in valid_ids:
                issues.append(("断链", pool_key, f"引用无法解析: {ref}"))
        # 空池检查
        if ptype in ("weighted", "fish") and not entries:
            issues.append(("空池", pool_key, "entries 为空"))
        # 权重和（weighted/fish）
        if ptype in ("weighted", "fish"):
            total = sum(int(e.get("w", 1) or 0) for e in entries)
            if total <= 0:
                issues.append(("空池", pool_key, "权重和 ≤ 0"))
        # table 的 rolls 引用检查
        if ptype == "table":
            for rc in pool.get("rolls") or []:
                sub = rc.get("pool", "")
                if sub.startswith("weighted:") or sub.startswith("fixed:"):
                    key = sub.split(":", 1)[1]
                    # 内联引用直接指向 DROP_POOLS 中的 key（允许前缀）
                    if key not in pools and not any(k.endswith(key) for k in pools):
                        issues.append(("断链", pool_key, f"table 子池缺失: {sub}"))
                elif sub.startswith(("gold:", "item:", "special:", "equip:", "equip_drop:")):
                    pass  # 内联直接解析
                elif sub not in pools and sub not in special_refs and sub not in C.EQUIP_ROSTER:
                    issues.append(("断链", pool_key, f"table 子池未知: {sub}"))
    return {
        "issues": issues,
        "pool_count": len(pools),
        "entry_count": sum(len((p.get("entries") or [])) for p in pools.values()),
    }


def audit_pretty() -> str:
    """人类可读审计报告。"""
    rep = audit_all()
    lines = [f"DROP_POOLS 审计: {rep['pool_count']} 池 / {rep['entry_count']} 条目"]
    if not rep["issues"]:
        lines.append("✅ 0 问题")
    else:
        for lvl, key, msg in rep["issues"]:
            lines.append(f"  ⚠️ [{lvl}] {key}: {msg}")
    return "\n".join(lines)
