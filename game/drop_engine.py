# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - drop_engine.py（掉落统一引擎 v174 → v184 收口）

掉落只有一条入口 `roll()`，池数据在 `game/data/drop_pools.py`（纯数据 `DROP_POOLS`），
分层抽象（鱼鱼 2026-09-04 拍板）——四类池 + 专属策略：

    weighted     带权条目抽取（采集/挖掘/通用材料/小怪材料）
    fish         垂钓（质量档→品种；季节/水域/鱼饵过滤）—— 内容专属，注册进引擎实例
    table        多层概率表（副本Boss/野王宝箱/垂钓惊喜 —— 各 roll 独立判定）
    table_choice 互斥档（暗格宝箱/战利品堆 —— 一次 roll 只进一档）
    fixed        固定掉落（精英专属/必掉清单）

v184（路线图 #7「内容侧·池」）：池 / 策略注册表 / 展开 / 审计的**形状**已搬进引擎
`saintess_engine.loot`（引擎零知识）。本文件从此只剩**内容侧那一半**：

  · 池数据源      `_get_pools()` → `DROP_POOLS`（惰性：import 期不拉数据，时机与 v174 同）
  · 引用解析      `_resolve_item_ref`（`equip:`/`gold:`/`gold_pct:`/`petegg:`/`rune:`… 是本游戏词汇）
  · 专属策略      `_roll_fish`（季节/水域/鱼饵/血饵是这款游戏的内容，不是形状）
  · 对外四入口    `roll()` / `expand_pool()` / `audit_all()` / `audit_pretty()`
                  —— **名字、签名、返回结构一字不变**（调用方零改动）
  · 旧名字保留    `POOL_STRATEGIES`（只读转发到引擎实例的策略表）
                  `_SimpleCtx`（= 引擎 `SimpleCtx`，instance.py / fishing.py / wild_king.py 在用）

档位（品质）表唯一真相源：`game/core/quality_tiers.py` —— 本文件不再内联副本。
随机源：标准库 `random` **模块本体**（不是新实例），随机流与 v174 逐格对齐。

条目引用统一带前缀：
    mat_xxx/物品ID  → 普通物品
    equip:eq_xxx    → 名册装备（generate_roster_equip）
    equip_drop:role → 通用装备掉落（roll_drop_equip，boss/elite）
    equip_drop_mix  → 混合装备（60% boss / 40% elite 双池）
    bp              → 图纸（等级就近 roll_blueprint）
    gem             → 幸运宝石（roll_gem_drop）
    gold:[a,b]      → 金币区间        gold_pct:n → ctx.gold_base × n%（下限 10）
    rune / rune:q   → 符文（蓝紫随机 / 指定品质）
    item:ID         → 带 count 的普通物品
    petegg:pet_xxx  → 宠物蛋
    special:xxx     → 扩展点（调用方注入的 hook，防特殊语义硬编码）

逐格一致由 `tests/test_v184_loot_pools.py` 证明（旧实现原文冻结 + 全池定种子对跑）。
审计的**判定与措辞**都在 `_resolvable(ref, pool)`（引擎只提供四态回调契约）。
⚠️ 与 v174 的 7 处**有意差异**（池数据均未使用）逐条登记在该门禁 §7：`gold:` 子引用带 `n`、
带前缀子池引用、裸名册 id 当条目 ref、`fixed` 空 entries 审计、`table_choice` 的 rolls 审计、
`table` 池 roll 行的 `fallback`、**引擎自己那两条结构消息的措辞**（D7：判定不变，措辞更直白；
引用类措辞仍由本文件 `_resolvable` 逐字保留旧说法）。
"""
import random
import sys
from collections.abc import Mapping
from typing import Any

from saintess_engine.loot import LootTable, SimpleCtx

# ============================================================
# 基础工具
# ============================================================

def _randint(a: int, b: int) -> int:
    return random.randint(a, b)


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
    if ref.startswith("gold_pct:"):
        # gold_pct:30 = ctx.gold_base × 30%（战利品堆金币=通关奖金×30%）
        pct = float(ref.split(":", 1)[1])
        base = int(getattr(ctx, "gold_base", 0) or 0)
        return {"type": "gold", "count": max(10, int(base * pct / 100.0))}
    if ref.startswith("rune:"):
        # rune:blue / rune:purple（指定品质符文）；rune = 蓝紫混合
        q = ref.split(":", 1)[1] if ":" in ref else None
        pool = [k for k, r in C.RUNES.items()
                if (r.get("quality") or "") == q] if q else \
               [k for k, r in C.RUNES.items() if (r.get("quality") or "") in ("blue", "purple")]
        if not pool:
            return None
        rk = random.choice(pool)
        r_def = C.RUNES[rk]
        rune_data = C.rune_item(r_def["effect"], random.randint(1, 2))
        return {"type": "rune", "data": rune_data} if rune_data else None
    if ref == "equip_drop_mix":
        # 混合装备：60% boss 池 / 40% elite 池；所选池 None → 换另一池；仍 None → None
        # （暗格宝箱语义：40% 装备档永不空开——双池都失败由调用方兜底材料）
        lv = int(getattr(ctx, "monster_lv", None) or getattr(ctx, "player_level", 1) or 1)
        first_role = "boss" if random.random() < 0.60 else "elite"
        second_role = "elite" if first_role == "boss" else "boss"
        eq = C.roll_drop_equip(lv, first_role)
        if eq is None:
            eq = C.roll_drop_equip(lv, second_role)
        if eq:
            return {"type": "equip", "data": eq}
        return None
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
    if ref.startswith("petegg:"):
        # 宠物蛋：petegg:pet_xxx（C.make_pet_egg 构造）
        pet_id = ref.split(":", 1)[1]
        try:
            egg = C.make_pet_egg(pet_id)
            return {"type": "petegg", "data": egg} if egg else None
        except Exception:
            return None
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


# ============================================================
# 内容侧词汇表（引擎零知识：认得出什么前缀、什么算内联引用，由这里声明）
# ============================================================

# 内联引用前缀：审计时"这些 ref 由 resolver 直接解析，不查池、不判断链"。
# ⚠️ 与 v174 audit_all 的白名单逐项一致，唯 **不含 `equip:`** —— 名册引用要**查名册**，
#    而引擎的 inline_prefixes 是"命中即跳过"，装不下这条判定；故 equip: 交给 resolvable 判。
_INLINE_PREFIXES = ("gold:", "gold_pct:", "item:", "special:", "equip_drop:", "petegg:", "rune:")

# 精确值特殊引用（不会断链）：图纸 / 幸运宝石 / 符文 / 混合装备
_SPECIAL_REFS = ("bp", "gem", "rune", "equip_drop_mix")

# 子池 key 可能带的前缀（v174 的 expand_pool / 审计里对 'weighted:xxx' / 'fixed:xxx' 的处理）
_POOL_KEY_PREFIXES = ("weighted:", "fixed:")

# `table` 池**展开**时的内联引用白名单：**逐字保留 v174 行为**。
# v174 的 expand_pool 对 table 池只外列 equip:/item:/gold: 三种，比审计白名单窄
# （gold_pct:/equip_drop:/petegg:/rune: 不外列）——两者本来就不是一个集合；
# 用引擎默认展开会认全部 inline_prefixes，`loot_pile:*` 会凭空多出 'gold_pct:30'，
# 故这里按旧白名单展开（对外行为一字不变）。
_EXPAND_INLINE_PREFIXES = ("equip:", "item:", "gold:")


def _get_pools() -> dict:
    """池数据源（B14 收口）：**包内** `content/catalog_rules.DROP_POOLS`
    （= `content/data/drop_pools.json`，596 池，与原 `game/data/drop_pools.py` 逐条同源；
    删 `game/data` 后本模块仍可用）。

    ⚠️ 一处**刻意的兼容**：宿主数据层若**已被本项目加载**（`<本模块所属树>.data.drop_pools`
    在 `sys.modules` 里 —— 只有宿主侧代码自己 import 过它才会在），则优先读它的 `DROP_POOLS`
    属性。理由：`tests/test_v184_loot_pools.py:1082 _with_pools()` 直接替换
    `_DP.DROP_POOLS` 造合成池，**打桩要对本实现可见**（打桩语义 = 行为的一部分；
    同款理由见 `content/events.py::_src` 的注释）。
    数据层被删后该分支自然消失（`sys.modules` 里没有它）→ 走包内域，值同。
    两路都不拉数据到 import 期（取数时机与 v174 同）。
    """
    _host = None
    if __package__:
        _host = sys.modules.get(__package__ + ".data.drop_pools")
    _host = _host or sys.modules.get("game.data.drop_pools")
    if _host is not None and hasattr(_host, "DROP_POOLS"):
        return _host.DROP_POOLS
    from content.catalog_rules import DROP_POOLS as _PKG_POOLS      # noqa: PLC0415
    return _PKG_POOLS


class _LazyPools(Mapping):
    """惰性池视图：每次访问才去取 `DROP_POOLS`（保持 v174 的取数时机，import 期不拉数据）。"""

    def __getitem__(self, key):
        return _get_pools()[key]

    def __iter__(self):
        return iter(_get_pools())

    def __len__(self):
        return len(_get_pools())


# ============================================================
# 内容专属策略：fish（垂钓）
# ============================================================

def _fish_tiers():
    """垂钓档位表（唯一真相源 `game/core/quality_tiers.py`）。

    为什么在这里 import：`game.core` 包的 `__init__` 会拉 index → data 装配链，数据层
    装配完成前 import 会撞循环 —— 与本文件 `import game.content as C` 同一手法（函数内延迟导入）。
    首次访问时先确保**本树**数据层装配（幂等），再取档位表。
    """
    try:
        from .core.quality_tiers import FISH_TIERS
    except ImportError:                      # 本树数据层尚未装配 → 先拉一次（幂等）
        from . import data as _data          # noqa: F401
        from .core.quality_tiers import FISH_TIERS
    return FISH_TIERS


def _roll_fish(pool: dict, ctx: Any, table) -> list[dict]:
    """垂钓（内容专属策略，签名 = 引擎策略契约 `fn(pool, ctx, table)`）。

    先按钓点禁档/鱼饵/等级定质量档，再从该档品种按权重摸 1 条。

    pool.spot_cfg: {min_lv, ban_quality, subarea}
    pool.quality_weights: {钓点等级: [白绿蓝紫橙五档权重]}（缺省全局 FISH_QUALITY_WEIGHTS）
    pool.entries: [{"item": mat_id, "name":..., "quality":..., "w":..., "spots":...,
                    "season":..., "season_boost":..., "size_range":..., "weight_range":..., ...}]

    ⚠️ 两处抽档**仍是 `random.choices`**（经 `table.rng`，即标准库 random 模块本体）：
    权重行是**浮点**（等级插值），引擎 `pick_weighted` 会对权重做 `int()` 截断 → 改概率分布。
    权重**行**已收口到 `FISH_TIERS.weights_at()`（与旧 `_quality_weights_inline` 位级一致）。
    """
    FISH_TIERS = _fish_tiers()
    FISH_QUALITY_ORDER = FISH_TIERS.order
    rng = table.rng
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

    # v184：权重行问 TierTable.weights_at()（旧 _quality_weights_inline 内联副本已删）
    weights = list(FISH_TIERS.weights_at(prof_lv))
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
    quality = rng.choices(FISH_QUALITY_ORDER, weights=weights, k=1)[0]

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
    pick = rng.choices(pool_by_q, weights=pool_w, k=1)[0]
    # 构造鱼条目返回（与旧 fishing.roll_fish 同形态：含 name/quality/type/price/size_range...）
    fish = dict(pick)
    fish["name"] = fish.get("name") or fish.get("item")
    return [{"type": "fish", "data": fish}]


def _expand_table(pool: dict, table) -> list:
    """`table` 池的展开：递归子池 + 内联引用原样外列（`_EXPAND_INLINE_PREFIXES` 白名单）。

    为什么不用引擎默认展开：引擎 `_expand_rolls` 认**全部** `inline_prefixes`，
    见 `_EXPAND_INLINE_PREFIXES` 的说明 —— 这里要的是 v174 的窄白名单。
    """
    out = []
    for rc in pool.get("rolls") or []:
        sub = rc.get("pool", "")
        if table.pools.get(sub) is not None:      # 旧语义：池表原样 key（不剥前缀）
            out.extend(table.expand(sub))
        elif isinstance(sub, str) and sub.startswith(_EXPAND_INLINE_PREFIXES):
            out.append(sub)
    return out


# ============================================================
# 引擎实例（池 + 引用解析 + 策略绑定）
# ============================================================

_TABLE = LootTable(
    _LazyPools(),                       # 惰性池视图（不 import 期拉 DROP_POOLS）
    resolver=_resolve_item_ref,         # 内容侧解析器（引擎只调它，不认识前缀）
    strategies={
        # 内容专属策略：uses/needs_weights/expand 是给审计与展开看的**元数据**
        "fish": {"fn": _roll_fish, "uses": "entries", "needs_weights": True, "expand": None,
                 "doc": "垂钓：质量档 → 品种（季节/水域/鱼饵），权重行问 TierTable"},
        # table 展开按 v174 窄白名单（见 _EXPAND_INLINE_PREFIXES）
        "table": {"expand": _expand_table},
        # table_choice 的 v174 展开走 entries 带权展开（暗格宝箱没有 entries → []）
        "table_choice": {"expand": None},
    },
    inline_prefixes=_INLINE_PREFIXES,
    pool_key_prefixes=_POOL_KEY_PREFIXES,
    special_refs=_SPECIAL_REFS,
    rng=random,                         # ★ 标准库模块本体：随机流与 v174 逐格对齐
)


class _StrategyMap(Mapping):
    """`POOL_STRATEGIES` 的只读转发（v184）。

    旧名字保留（有人 import 它），但**不是第二份真相源**：策略表活在 `_TABLE` 里，
    这里只是一层视图 —— `POOL_STRATEGIES[name]` → 引擎实例注册的策略函数。
    """

    def __init__(self, table: LootTable):
        self._table = table

    def __getitem__(self, name):
        spec = self._table._strategies.get(name)
        if spec is None:
            raise KeyError(name)
        return spec["fn"]

    def __iter__(self):
        return iter(self._table._strategies)

    def __len__(self):
        return len(self._table._strategies)


POOL_STRATEGIES = _StrategyMap(_TABLE)


# 旧名字保留：instance.py / fishing.py / wild_king.py 都在用 `_SimpleCtx(...)`。
# 语义与 v174 逐字相同（引擎 SimpleCtx = 同一份实现：缺属性 → None，hooks 恒为 dict）。
_SimpleCtx = SimpleCtx


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
    # 旧语义：只认 `DROP_POOLS` 里的原样 key（不剥 weighted:/fixed: 前缀），空池也当"没有"
    if not _get_pools().get(pool_key):
        return []
    return _TABLE.roll(pool_key, ctx, **kw)


def expand_pool(pool_key: str) -> list:
    """返回池的带权展开候选 ID 列表（weighted 池按权重展开；fixed 池返回全部）。

    用途：命令层需要"候选池 + 自己多次 choice"的旧语义时（如采集按副业等级选 N 份），
    数据源统一走 DROP_POOLS。池不存在返回 []（调用方走兜底）。
    """
    if not _get_pools().get(pool_key):
        return []
    return _TABLE.expand(pool_key)


# ============================================================
# 全量审计
# ============================================================

def _resolvable(ref, pool) -> object:
    """引擎审计的**引用判定 + 措辞**（内容侧词汇表）—— `audit_all` 的"什么算断链、怎么说"都在这里。

    返回值四态（引擎 `LootTable.audit(resolvable=…)` 契约）：

      * `True`  —— 解得开
      * `False` —— 断链（引擎给通用措辞）
      * `str`   —— 断链，且**这句就是措辞**（本游戏用自己的说法：物品缺失 / 名册缺失 / 子池缺失）
      * `None`  —— 这条引用内容侧自己管，不判

    v184 之前这段判定散在 `audit_all` 里的两套分支（条目 ref / roll 子池 ref，措辞各一套），
    这里按池的策略元数据 `uses` 归一（`_TABLE.strategy_of(pool)["uses"]`）：
      `uses=entries` → 「物品缺失 / equip 名册缺失 / 引用无法解析」
      `uses=rolls`   → 「table 子池缺失 / table 子池未知」
    裸名册 id（`eq_xxx`）两条都认（INSTANCE_BOSS_EQUIP_DROP 老数据就是裸名册 id）；
    真实池数据里条目 ref 无裸名册 id（0/1435），见门禁 §7 登记。
    """
    import game.content as C  # noqa: E402
    if not isinstance(ref, str):
        return False
    uses = _TABLE.strategy_of(pool or {}).get("uses", "entries")
    if ref.startswith(_POOL_KEY_PREFIXES):
        key = ref.split(":", 1)[1]
        pools = _get_pools()
        if key in pools or any(k.endswith(key) for k in pools):
            return True
        return f"table 子池缺失: {ref}"
    if ref.startswith("equip:"):
        rid = ref.split(":", 1)[1]
        return True if rid in C.EQUIP_ROSTER else f"equip 名册缺失: {rid}"
    if ref in C.ITEMS or ref in C.EQUIP_ROSTER:
        return True
    if uses == "rolls":
        return f"table 子池未知: {ref}"
    if ref.startswith("mat_"):
        return f"物品缺失: {ref}"
    return f"引用无法解析: {ref}"


def audit_all() -> dict:
    """全量审计：断链/空池/权重/等级匹配/重复。

    返回 {"issues": [...], "pool_count": N, "entry_count": M}
    每个 issue: (级别, 池key, 描述)

    v184：判定**与措辞**都交给引擎 `LootTable.audit(resolvable=_resolvable)` ——
    本游戏的说法（物品缺失 / 名册缺失 / 子池缺失）由 `_resolvable` 直接给出，
    不再需要"事后把引擎文案改写回旧文案"那种字符串兼容壳；本函数只剔掉引擎多出的 `ok` 键，
    返回的三个键一字不变。
    """
    rep = _TABLE.audit(resolvable=_resolvable)
    return {
        "issues": list(rep["issues"]),
        "pool_count": rep["pool_count"],
        "entry_count": rep["entry_count"],
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
