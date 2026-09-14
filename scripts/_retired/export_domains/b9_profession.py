# -*- coding: utf-8 -*-
"""生活副业线（B9 L4）域插件 —— `fishing_spots` / `fishing_pool` / `gather_pools` /
`gather_cond_pools` / `mining_deep_pools` 五个域的真源 → 包 JSON。

契约见 `scripts/export_domains/README.md`：本文件只**读真源、返回内存表**，落盘由宿主
（`scripts/export_game_package.py`：UTF-8 / LF / indent=2 / 原子替换 + `sort_table` 外层键字典序）统一做。
**不许 import `export_game_package`**（宿主会扫本目录 → 循环导入）。公用小工具走 `_helpers.py`。

为什么是这五个域（B9 L4 的面）
------------------------------
本线搬的是**生活副业服务层**（`game/services/profession.py` + `quests.py` → 包内
`content/profession.py` / `content/profession_quests.py`）。这些逻辑直接消费的**生活副业数据表**里，
`game/data/fishing.py` 的钓点/鱼种池与 `game/data/gather_pools.py` 的三张池表**尚未进包**
（B9 派工单里的「未进包候选：fishing / gather / gather_pools」）→ 本文件把它们单向导出。
（注：`FISH_QUALITY_WEIGHTS` / `FISH_EXP` / `FISH_COLLECT` 与 `prof_config.py` 的配置常量
**不是条目形状**（int 键表 / 常量），本批未进包 —— 见报告 §缺口。）

顺序不变式（**渲染逐字等价的关键**）
------------------------------------
五张源表里，**遍历顺序参与随机数消费**的有三处：
  * `FISH_POOL` 是 list，`core/fishing.py:_roll_fish_legacy` 按插入序做累计权重抽样；
  * `GATHER_COND_POOLS` 是 dict（地图 → 条目表），`gather_cond_roll` 按**插入序**把命中材料
    extend 进 `hit` 列表，再 `random.choice(hit)` —— 顺序变了，同 seed 的结果就变；
  * `GATHER_MAP_POOLS` / `MINING_DEEP_POOLS` 经 `data/_assembly` 折进 `DROP_POOLS`（同样按插入序）。
而导出契约 `sort_table` 把**外层键排成字典序** → 源顺序在域文件里没处存。故本插件给每条注入
`seq` = 源插入序（1 基）；包侧若要按源序还原，按 `seq` 排即可（与 `derive_weekly_quests` 同款）。
注入守卫：源条目/源值里已有 `seq` 字段 → `raise`（注入不许覆盖源真值）。

通用纪律
--------
    * 读的是 **import 之后的运行时表**（`game.data.<mod>`），不是源码字面量。
    * 坏形状 `raise` 而不是静默降级（空表 = 编辑器显示「0 条」且不报错，是本项目最怕的静默失效）。
    * 返回前 `sort_table` 一次（幂等；宿主还会再排一次，结果相同）。
"""

from _helpers import import_game_data, sort_table, as_table  # noqa: F401

# 真源位置（写进报错文案，便于定位「形状变了」时是哪个文件哪张表）
FISHING_SPOTS_SRC = "game/data/fishing.py:9 FISHING_SPOTS"
FISH_POOL_SRC = "game/data/fishing.py:91 FISH_POOL"
GATHER_POOLS_SRC = "game/data/gather_pools.py:8 GATHER_MAP_POOLS"
GATHER_COND_SRC = "game/data/gather_pools.py:109 GATHER_COND_POOLS"
MINING_DEEP_SRC = "game/data/gather_pools.py:127 MINING_DEEP_POOLS"

# 品质五档（真源 `game/data/stats.py QUALITY` 的键；与装备品质同一枚举）
QUALITY_CODES = ("white", "green", "blue", "purple", "orange")
# 季节码（真源 `game/data/time_weather.py`：season / season_boost 取值）
SEASON_CODES = ("spring", "summer", "autumn", "winter")
# 限定采集条件词（= 真源 `game/services/profession.py:_GATHER_COND_CHECKERS` 的键集，
# 运行期 fail-closed 校验的就是这几个；导出期同口径静态拦一道）
COND_TOKENS = ("night", "morning", "winter", "rain")

SEQ_FIELD = "seq"
DROPS_FIELD = "drops"


# ─────────────────────────────────────────────────────────── 通用守卫
def _require_table(obj, where: str, dom: str) -> dict:
    """真源表必须是非空 dict —— 空表会让编辑器显示「0 条」且不报错（最怕的静默失效）。"""
    tbl = as_table(obj, where)
    if not tbl:
        raise ValueError(f"{dom}：{where} 是空表 —— 源形状变了/表被删，拒绝导出")
    return tbl


def _require_list(obj, where: str, dom: str) -> list:
    if not isinstance(obj, list) or not obj:
        raise ValueError(f"{dom}：{where} 不是非空 list（{type(obj).__name__}）—— 拒绝导出")
    return obj


def _require_str(val, what: str, dom: str, allow_empty: bool = False) -> str:
    if not isinstance(val, str) or (not allow_empty and not val.strip()):
        raise ValueError(f"{dom}：{what} 不是{'字符串' if allow_empty else '非空字符串'}（{val!r}）—— 拒绝导出")
    return val


def _require_int(val, what: str, dom: str, minimum=None, maximum=None) -> int:
    if isinstance(val, bool) or not isinstance(val, int):
        raise ValueError(f"{dom}：{what} 不是 int（{val!r}）—— 拒绝导出")
    if minimum is not None and val < minimum:
        raise ValueError(f"{dom}：{what} = {val} 低于下限 {minimum} —— 拒绝导出")
    if maximum is not None and val > maximum:
        raise ValueError(f"{dom}：{what} = {val} 高于上限 {maximum} —— 拒绝导出")
    return val


def _no_field(ent, key, field: str, where: str, dom: str) -> None:
    """注入字段的守卫：源条目里已有同名键 → raise（注入不许覆盖源真值）。"""
    if isinstance(ent, dict) and field in ent:
        raise ValueError(f"{dom}：{where}[{key!r}] 已含字段 {field!r} —— 注入会覆盖源真值，拒绝导出")


def _require_seq_source(tbl: dict, where: str, dom: str) -> None:
    """源表的键序可复现性前提：外层键必须全为非空字符串（`seq` 按插入序注入）。"""
    for k in tbl:
        if not isinstance(k, str) or not k:
            raise ValueError(f"{dom}：{where} 的键 {k!r} 不是非空字符串 —— 拒绝导出")


def _fold_pairs(pairs, key, where: str, dom: str) -> list:
    """`[(id, 权重), …]` → `[[id, 权重], …]`（JSON 化；顺带守卫 id/权重形状）。"""
    out = []
    for el in _require_list(pairs, f"{where}[{key!r}]", dom):
        if not isinstance(el, (list, tuple)) or len(el) != 2:
            raise ValueError(f"{dom}：{where}[{key!r}] 的元素 {el!r} 不是 (id, 权重) 二元组 —— 拒绝导出")
        mid, w = el
        _require_str(mid, f"{where}[{key!r}] 的材料 id", dom)
        _require_int(w, f"{where}[{key!r}][{mid!r}] 权重", dom, minimum=1)
        out.append([mid, w])
    return out


def _fold_cond(pairs, key, where: str, dom: str) -> list:
    """`[(id, 权重, 条件串), …]` → `[[id, 权重, 条件串], …]`；条件词逐 token 必须在 COND_TOKENS 里。"""
    out = []
    for el in _require_list(pairs, f"{where}[{key!r}]", dom):
        if not isinstance(el, (list, tuple)) or len(el) != 3:
            raise ValueError(f"{dom}：{where}[{key!r}] 的元素 {el!r} 不是 (id, 权重, 条件) 三元组 —— 拒绝导出")
        mid, w, cond = el
        _require_str(mid, f"{where}[{key!r}] 的材料 id", dom)
        _require_int(w, f"{where}[{key!r}][{mid!r}] 权重", dom, minimum=1)
        _require_str(cond, f"{where}[{key!r}][{mid!r}] 条件串", dom)
        for tok in str(cond).split("+"):
            if tok not in COND_TOKENS:
                raise ValueError(
                    f"{dom}：{where}[{key!r}][{mid!r}] 的条件词 {tok!r} 不在注册表 {COND_TOKENS} —— "
                    f"运行期 `_GATHER_COND_CHECKERS` 会 fail-closed（本条永不命中），拒绝导出")
        out.append([mid, w, cond])
    return out


def _load(mod_name: str, src_root: str = None):
    return import_game_data(mod_name, src_root) if src_root else import_game_data(mod_name)


# ─────────────────────────────────────────────────────────── 域 1：fishing_spots
def derive_fishing_spots(src_root: str = None) -> dict:
    """`fishing_spots` 域：`FISHING_SPOTS` 原样导出（11 条，键 = 地图 id）。**无注入**。

    真源：`game/data/fishing.py:9 FISHING_SPOTS`（16 章品质垂钓体系 v2.0；v104 M15 补 `subarea`）。
    条目字段（实测 11/11 齐）：`name` / `min_lv`（1~9）/ `ban_quality`（禁出档位，取值 ∈ QUALITY，
    实测只用 `orange` / `purple` / 空表）/ `subarea`（子区域 id，指向 subareas 域）/ `desc`。
    消费者：`game/core/fishing.py:roll_fish`（按 `min_lv` 与 `ban_quality` 过滤）、
        `game/services/profession.py`（钓点 id 进事件 data）、命令层垂钓面板。
    留作引用、不展开：`subarea` → subareas 域（导出期不校验闭合，见报告 §缺口）。
    """
    mod = _load("fishing", src_root)
    spots = _require_table(getattr(mod, "FISHING_SPOTS", None), FISHING_SPOTS_SRC, "fishing_spots")
    _require_seq_source(spots, FISHING_SPOTS_SRC, "fishing_spots")
    for k, ent in spots.items():
        if not isinstance(ent, dict):
            raise ValueError(f"fishing_spots：{FISHING_SPOTS_SRC}[{k!r}] 不是 dict（{type(ent).__name__}）")
        _require_str(ent.get("name"), f"{FISHING_SPOTS_SRC}[{k!r}].name", "fishing_spots")
        _require_str(ent.get("desc"), f"{FISHING_SPOTS_SRC}[{k!r}].desc", "fishing_spots")
        _require_str(ent.get("subarea"), f"{FISHING_SPOTS_SRC}[{k!r}].subarea", "fishing_spots")
        _require_int(ent.get("min_lv"), f"{FISHING_SPOTS_SRC}[{k!r}].min_lv", "fishing_spots", minimum=1)
        ban = ent.get("ban_quality")
        if not isinstance(ban, list):
            raise ValueError(f"fishing_spots：{FISHING_SPOTS_SRC}[{k!r}].ban_quality 不是 list")
        for q in ban:
            if q not in QUALITY_CODES:
                raise ValueError(f"fishing_spots：{FISHING_SPOTS_SRC}[{k!r}].ban_quality 含未知品质 {q!r}")
    return sort_table({k: dict(v) for k, v in spots.items()})


# ─────────────────────────────────────────────────────────── 域 2：fishing_pool
def derive_fishing_pool(src_root: str = None) -> dict:
    """`fishing_pool` 域：`FISH_POOL`（list，30 条）→ 表（键 = 鱼名）。**唯一注入 = `seq`**。

    真源：`game/data/fishing.py:91 FISH_POOL`（白/绿/蓝/紫/橙五档 + 鱼王/宝物/垃圾特殊 type；
    v126.6 扩容）。字段（实测 30/30 齐）：`name` / `quality` / `type` / `price` / `spots`
    （`None` = 全水域 / 列表 = 限定钓点）/ `weight`（10~60）/ `size_range` / `weight_range` / `desc`；
    `season` 4 条（硬限定）/ `season_boost` 5 条（偏好 ×1.5）。
    ⚠️ 源是 **list**，插入序参与累计权重抽样（`_roll_fish_legacy`）→ 注入 `seq`（1 基）保序。
    守卫：名字唯一（重名会让键碰撞静默丢鱼）；`spots` 非 None 时必须是非空字符串列表；
    `size_range` / `weight_range` 必须是二元数值区间且 low ≤ high；`quality` ∈ QUALITY、
    `season`/`season_boost` ∈ 季节码。
    """
    mod = _load("fishing", src_root)
    pool = _require_list(getattr(mod, "FISH_POOL", None), FISH_POOL_SRC, "fishing_pool")
    out: dict = {}
    for i, ent in enumerate(pool, 1):
        if not isinstance(ent, dict):
            raise ValueError(f"fishing_pool：{FISH_POOL_SRC}[{i}] 不是 dict（{type(ent).__name__}）")
        name = _require_str(ent.get("name"), f"{FISH_POOL_SRC}[{i}].name", "fishing_pool")
        if name in out:
            raise ValueError(f"fishing_pool：{FISH_POOL_SRC} 出现重名 {name!r}（键 = 鱼名，重名会静默丢鱼）")
        _no_field(ent, name, SEQ_FIELD, FISH_POOL_SRC, "fishing_pool")
        _require_str(ent.get("desc"), f"{FISH_POOL_SRC}[{i}].desc", "fishing_pool")
        _require_str(ent.get("type"), f"{FISH_POOL_SRC}[{i}].type", "fishing_pool")
        q = ent.get("quality")
        if q not in QUALITY_CODES:
            raise ValueError(f"fishing_pool：{FISH_POOL_SRC}[{i}].quality = {q!r} 不在 {QUALITY_CODES}")
        _require_int(ent.get("weight"), f"{FISH_POOL_SRC}[{i}].weight", "fishing_pool", minimum=1)
        _require_int(ent.get("price"), f"{FISH_POOL_SRC}[{i}].price", "fishing_pool", minimum=0)
        for f in ("size_range", "weight_range"):
            rng = ent.get(f)
            if not isinstance(rng, list) or len(rng) != 2 or any(
                    isinstance(x, bool) or not isinstance(x, (int, float)) for x in rng):
                raise ValueError(f"fishing_pool：{FISH_POOL_SRC}[{i}].{f} 不是二元数值区间（{rng!r}）")
            if rng[0] > rng[1]:
                raise ValueError(f"fishing_pool：{FISH_POOL_SRC}[{i}].{f} 的 low > high（{rng!r}）")
        spots = ent.get("spots")
        if spots is not None:
            if not isinstance(spots, list) or not spots:
                raise ValueError(f"fishing_pool：{FISH_POOL_SRC}[{i}].spots 既非 None 也非非空列表（{spots!r}）")
            for sp in spots:
                _require_str(sp, f"{FISH_POOL_SRC}[{i}].spots 元素", "fishing_pool")
        for f in ("season", "season_boost"):
            if f in ent and ent[f] not in SEASON_CODES:
                raise ValueError(f"fishing_pool：{FISH_POOL_SRC}[{i}].{f} = {ent[f]!r} 不在 {SEASON_CODES}")
        entry = dict(ent)                      # 字段顺序原样
        entry[SEQ_FIELD] = i                   # 唯一注入：源插入序
        out[name] = entry
    return sort_table(out)


# ─────────────────────────────────────────────────────────── 域 3：gather_pools
def derive_gather_pools(src_root: str = None) -> dict:
    """`gather_pools` 域：`GATHER_MAP_POOLS`（68 条，地图 → 材料权重表）→ 每条一个对象。

    真源：`game/data/gather_pools.py:8 GATHER_MAP_POOLS`（v95.23 首批 7 池 + v97.2 全野外地图专属池；
    格式 `{地图 id: [(材料 id, 权重), …]}`）。
    唯一注入（两个）：`drops` = `[[材料 id, 权重], …]`（源是 tuple 列表，JSON 只能是数组）、
        `seq` = 源插入序（1 基；折进 `DROP_POOLS` 时按插入序）。
    守卫：值必须是非空 list（源形状变了就报）、材料 id 非空串、权重 ≥1、条目不重名（键唯一天然成立）。
    留作引用、不展开：材料 id → items 域（导出期不校验闭合，见报告 §缺口）。
    """
    mod = _load("gather_pools", src_root)
    tbl = _require_table(getattr(mod, "GATHER_MAP_POOLS", None), GATHER_POOLS_SRC, "gather_pools")
    _require_seq_source(tbl, GATHER_POOLS_SRC, "gather_pools")
    out: dict = {}
    for i, (mid, pairs) in enumerate(tbl.items(), 1):
        out[mid] = {DROPS_FIELD: _fold_pairs(pairs, mid, GATHER_POOLS_SRC, "gather_pools"),
                    SEQ_FIELD: i}
    return sort_table(out)


# ─────────────────────────────────────────────────────────── 域 4：gather_cond_pools
def derive_gather_cond_pools(src_root: str = None) -> dict:
    """`gather_cond_pools` 域：`GATHER_COND_POOLS`（8 条，时机限定采集物）。

    真源：`game/data/gather_pools.py:109 GATHER_COND_POOLS`（v102.3；格式 `{地图 id: [(材料, 权重, 条件)]}`，
    条件串用 `+` 组合，如 `winter+night`）。
    唯一注入（两个）：`drops` = `[[材料 id, 权重, 条件串], …]`、`seq` = 源插入序（1 基）。
    **静态门禁**：条件词逐 token 必须在 `COND_TOKENS`（= 运行期 `_GATHER_COND_CHECKERS` 的键集）里 ——
    运行期对未知词是 fail-closed（本条永不命中 + 告警），导出期直接拒绝，双重防线。
    ⚠️ 本表的**插入序参与随机消费**（`gather_cond_roll` 按插入序 extend `hit` 后 `random.choice`）
    → 包侧消费时必须按 `seq` 还原源序，否则同 seed 结果漂移（渲染逐字等价的红线）。
    """
    mod = _load("gather_pools", src_root)
    tbl = _require_table(getattr(mod, "GATHER_COND_POOLS", None), GATHER_COND_SRC, "gather_cond_pools")
    _require_seq_source(tbl, GATHER_COND_SRC, "gather_cond_pools")
    out: dict = {}
    for i, (mid, pairs) in enumerate(tbl.items(), 1):
        out[mid] = {DROPS_FIELD: _fold_cond(pairs, mid, GATHER_COND_SRC, "gather_cond_pools"),
                    SEQ_FIELD: i}
    return sort_table(out)


# ─────────────────────────────────────────────────────────── 域 5：mining_deep_pools
def derive_mining_deep_pools(src_root: str = None) -> dict:
    """`mining_deep_pools` 域：`MINING_DEEP_POOLS`（9 条，矿洞类地图专属深矿）。

    真源：`game/data/gather_pools.py:127 MINING_DEEP_POOLS`（v102.3 深矿池；v173 重排 ——
    删 deep_tunnel/sea_cave 死条，星铁链迁矮人长廊）。
    唯一注入（两个）：`drops` = `[[材料 id, 权重], …]`、`seq` = 源插入序（1 基）。
    消费者：`game/services/profession.py:settle_mining`（`drop_engine.expand_pool("mine:{地图}")`
    的数据源之一）+ `data/_assembly` 折进 `DROP_POOLS`。
    """
    mod = _load("gather_pools", src_root)
    tbl = _require_table(getattr(mod, "MINING_DEEP_POOLS", None), MINING_DEEP_SRC, "mining_deep_pools")
    _require_seq_source(tbl, MINING_DEEP_SRC, "mining_deep_pools")
    out: dict = {}
    for i, (mid, pairs) in enumerate(tbl.items(), 1):
        out[mid] = {DROPS_FIELD: _fold_pairs(pairs, mid, MINING_DEEP_SRC, "mining_deep_pools"),
                    SEQ_FIELD: i}
    return sort_table(out)


DOMAINS = {
    "fishing_spots": derive_fishing_spots,
    "fishing_pool": derive_fishing_pool,
    "gather_pools": derive_gather_pools,
    "gather_cond_pools": derive_gather_cond_pools,
    "mining_deep_pools": derive_mining_deep_pools,
}
