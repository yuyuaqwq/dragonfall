# -*- coding: utf-8 -*-
"""B6 域插件 —— 商店·经济 + 任务·成就线（一条线 6 个域，一个文件，多路并行零冲突）。

契约见 `scripts/export_domains/README.md`：本文件只做「真源 → 内存表」的**单向搬运**
（条目原样进 JSON，不补默认值、不改类型、不展开引用字符串），落盘/比对/清单全在宿主。
六个域的真源（**读的是 import 之后的运行时表**，不是源码字面量）：

    shop              game/data/shop.py:13/22/83/232/293/417 六张表合表  → 89 条
    smith_stock       game/core/smith_stock.py:44-82 的四组静态配置   →  4 条
    shop_stock        game/data/shop_limit.py:39 SHOP_LIMIT          → 35 条
    achievements      game/data/achievements.py:25 ACHIEVEMENTS      → 119 条
    achievement_conds game/core/achievement_conds.py:22 COND_CHECKS  → 44 条
    title_conds       game/core/title_conds.py:14 CONDITIONS + data/titles.py:3 TITLES → 50 条

**引用不展开**：`item:xxx` / `mat_xxx` / `eq_xxx` / 武器名 一律按源侧字符串原样保留
（items / equip_roster / skills / classes 域已进包，闭合由包侧编辑器自己查，本插件不解析）。

⚠️ import 顺序铁律（`derive_panel_rules` 的教训，2026-09-13 实测复现）：
**先 `import_game_data` 再 `import_game_core`**，否则 `import game.core.X` 会先跑尚未完成的
`game/core/__init__.py` → `ImportError: cannot import name … from partially initialized module`。
"""
from _helpers import import_game_data, import_game_core, sort_table, as_table

# 野外行商货单（`SHOP_WILD_TRADE`）没有店铺归属 —— 用这个保留键落一条（全表唯一非店铺键）
WILD_TRADE_KEY = "wild_trade"
# B14-3：荣誉商店（`game/data/honor_shop.py:11 HONOR_SHOP`）没有店铺归属 —— 第二个保留键
HONOR_SHOP_KEY = "honor_shop"

# 商品 key 前缀（`data/shop_limit.py:12-16` 的四类来源；`_validate()` 也按这四个前缀自检）
_LIMIT_PREFIXES = ("item", "mat", "equip", "weapon")


# =============================================================================
# shop —— 商店配货（game/data/shop.py 六张表合表）
# =============================================================================
def derive_shop(src_root: str = None) -> dict:
    """商店域（`shop`）→ 一条 = 一个店铺（表键 = 店铺 id）。

    ================================ 真源是六张表 ================================
        game/data/shop.py:22   `SHOP_SUBAREA_ITEMS`    58 个**子区域店铺**的专属货单（物品 id 列表）
        game/data/shop.py:83   `SHOP_WEAPONS`          24 个**城镇**的武器货架（[名, 类型, 等级, 品质]）
        game/data/shop.py:232  `SHOP_SMITH_MATERIALS`   6 个城镇的锻造材料货单
        game/data/shop.py:293  `SHOP_EQUIP`             6 个城镇的名册装备货单（EQUIP_ROSTER id）
        game/data/shop.py:417  `SUBAREA_KIND`          64 个子区域的**设施类别**（smith/herb/tavern/
                                                      cook/general/misc/enhance）
        game/data/shop.py:13   `SHOP_WILD_TRADE`        6 件野外行商存货（**无店铺键**，见下）

    映射口径（**合表，不改一词**）
    ---------------------------------------------------
      · 键 = 上述 5 张 keyed 表的**并集**（实测 88 个）+ 1 个保留键 `wild_trade` = 89 条。
        两张不同粒度的键在游戏侧本来就各查各的：子区域店铺查 `SHOP_SUBAREA_ITEMS`/`SUBAREA_KIND`，
        城镇店（武器/材料/装备货架）查 `SHOP_WEAPONS`/`SHOP_SMITH_MATERIALS`/`SHOP_EQUIP`。
        **不折成一层**（折了就得发明「哪层优先」的规则），字段出现即「这张表有这个键」：
            子区域店 → `items` + `kind`（实测 58 条）/ 只有 `kind` 的 6 条
            城镇店   → `weapons` / `materials` / `equip` 的任意组合（实测 17/5/1/1 四种组合）
      · 缺字段不是「空」：源表没这个键 → 条目里**没有**这个字段（不补 `[]` / 不补 `null`）。
      · 值**原样**：`items`/`materials`/`equip` 是 id/名引用串列表，`weapons` 是四元列表
        （`[名, 武器类型英文ID, 等级, 品质]`），`kind` 是设施类别字符串 —— 一个都不展开。
      · `wild_trade`（`{"items": [...]}`）：`SHOP_WILD_TRADE` 没有店键（消费点 `commands/economy.py`
        的 trade 型野外 NPC 分支），给它是为了**不丢源数据**；它是全表唯一的非店铺条目。

    消费者在游戏侧：`economy.py` 的 shop 面板 / buy 分支（`C.SHOP_SUBAREA_ITEMS` / `C.SHOP_WEAPONS`
    / `C.SHOP_SMITH_MATERIALS` / `C.SHOP_EQUIP` / `C.SUBAREA_KIND` / `C.SHOP_WILD_TRADE`）。

    自检（拒绝导出坏表）：五张表必须是非空 dict、键是非空字符串、`SHOP_WILD_TRADE` 是非空字符串
    列表；保留键 `wild_trade` 不许与任何店铺 id 撞名。
    """
    mod = import_game_data("shop", src_root)
    tbl = {}
    for name in ("SHOP_SUBAREA_ITEMS", "SHOP_WEAPONS", "SHOP_SMITH_MATERIALS",
                 "SHOP_EQUIP", "SUBAREA_KIND"):
        t = as_table(getattr(mod, name, None), f"shop.{name}")
        bad = [k for k in t if not isinstance(k, str) or not k]
        if bad:
            raise ValueError(f"shop.{name}：有非字符串/空键 {bad[:3]} —— 拒绝导出")
        tbl[name] = t
    wild = getattr(mod, "SHOP_WILD_TRADE", None)
    if not isinstance(wild, (list, tuple)) or not wild or not all(isinstance(x, str) and x for x in wild):
        raise ValueError("shop：game/data/shop.py:13 SHOP_WILD_TRADE 不是非空字符串列表 —— 拒绝导出")

    keys = set()
    for t in tbl.values():
        keys |= set(t)
    if WILD_TRADE_KEY in keys:
        raise ValueError(f"shop：店铺 id 与保留键 {WILD_TRADE_KEY!r} 撞名 —— 拒绝导出（会覆盖行商货单）")

    out = {}
    for k in sorted(keys):
        e = {}
        if k in tbl["SHOP_SUBAREA_ITEMS"]:
            e["items"] = tbl["SHOP_SUBAREA_ITEMS"][k]
        if k in tbl["SHOP_WEAPONS"]:
            e["weapons"] = tbl["SHOP_WEAPONS"][k]
        if k in tbl["SHOP_SMITH_MATERIALS"]:
            e["materials"] = tbl["SHOP_SMITH_MATERIALS"][k]
        if k in tbl["SHOP_EQUIP"]:
            e["equip"] = tbl["SHOP_EQUIP"][k]
        if k in tbl["SUBAREA_KIND"]:
            e["kind"] = tbl["SUBAREA_KIND"][k]
        out[k] = e
    out[WILD_TRADE_KEY] = {"items": list(wild)}

    # B14-3（2026-09-14）：`HONOR_SHOP`（荣誉商店 6 件，`game/data/honor_shop.py:11`）进本域 ——
    # 它就是一个「商店」（键 = 商品编号 1..6，值 = {name, cost, desc, reward}），真源在**另一个
    # 模块**（honor_shop.py 只有这一张表），故按本域既有的「保留键」先例再落一行。
    # ⚠ 本域 `$defs.shop` **不写 required** 且 `additionalProperties: true` ⇒ 新行能过条目校验；
    #   行内用 `ranks` 装编号表（**不能叫 `items`**：`$defs.shop.items` 声明的是字符串数组）。
    # ⚠ int 键陷阱：编号源侧是 int 1..6（消费点 `combat_cmds._honor_buy(..., int(num))` 用
    #   `HONOR_SHOP.get(num)` 取）→ 包内读口必须还原 int，否则兑换恒报「没有第 N 件商品」。
    honor = import_game_data("honor_shop", src_root)
    ranks = as_table(getattr(honor, "HONOR_SHOP", None), "honor_shop.HONOR_SHOP")
    if not ranks:
        raise ValueError("shop：game/data/honor_shop.py:11 HONOR_SHOP 是空表 —— 拒绝导出")
    for num, ent in ranks.items():
        if not isinstance(ent, dict) or not isinstance(ent.get("name"), str) or not ent["name"]:
            raise ValueError(f"shop：HONOR_SHOP[{num!r}] 不是含非空 name 的 dict（{ent!r}）"
                             " —— 源形状变了，拒绝导出")
    if HONOR_SHOP_KEY in out:
        raise ValueError(f"shop：保留键 {HONOR_SHOP_KEY!r} 与店铺 id 撞名 —— 拒绝导出")
    out[HONOR_SHOP_KEY] = {"ranks": dict(ranks)}
    return sort_table(out)


# =============================================================================
# smith_stock —— 铁匠铺货架（game/core/smith_stock.py 的静态配置面）
# =============================================================================
def derive_smith_stock(src_root: str = None) -> dict:
    """铁匠货架域（`smith_stock`）→ 一条 = 一组**静态配置**（共 4 组）。

    为什么是「配置组」而不是「城镇货架行」：`game/core/smith_stock.py` 是**程序性模块**，
    货架内容由 `roll_stock():137` 在运行期随机生成（等级窗口 ±5 + 品质权重抽 + 6h 补货 +
    惰性落 `event_state`）——**没有可静态导出的货架行**。模块里能当内容编辑的静态真源
    只有下面这几组，风格与同批 `panel_rules`（一条 = 一组常量）一致。

        game/core/smith_stock.py:44  `QUALITY_WEIGHTS`     品质抽取权重（白20/绿25/蓝35/紫15/橙5）
        game/core/smith_stock.py:46  `STOCK_COUNT`         每城货架件数 = 8（2 武器+3 防具+2 饰品+1 随机）
        game/core/smith_stock.py:47  `STOCK_WINDOW`        城镇等级 ±N 窗口 = 5
        game/core/smith_stock.py:48  `RESTOCK_HOURS`       售罄补货周期（小时）= 6
        game/core/smith_stock.py:51  `_QTY_BY_QUALITY`     品质 → 每件份数（实测只配紫/橙 = 1，其余走 2~3）
        game/core/smith_stock.py:54  `SMITH_NPC_NAMES`     城镇地图 id → 铁匠 NPC 名（实测 9 城，作品署名用）
        game/core/smith_stock.py:70  `_SMITH_TOWN_LEVELS`  城镇地图 id → 推荐等级（实测 11 城）

    映射口径
    --------
      · 4 条：`quality_weights`（原样 dict）/ `npc_names`（原样 dict）/ `town_levels`（原样 dict）
        / `shelf_rules`（把三个标量 + `_QTY_BY_QUALITY` 并成一组，标量必须包一层 ——
        导出器要求每条都是对象）。
      · 值**原样**：不把 `_SMITH_TOWN_LEVELS` 展开成 `town_level()` 的运行期结果、不补缺省件数。
        （实测 11 城全部命中该表 → `town_level()` 对它们与表值逐一相同；不在表里的城镇才走
        `MAP_BY_ID`/子区域怪物等级兜底，那是代码路径，本域不导。）
      · `npc_names` ⊆ `town_levels`（9/9 命中，导出期断言）—— 有的城镇有等级窗口无署名铁匠。

    消费者在游戏侧：`get_smith_stock():281` / `buy_stock_item():371` / `smith_stock_price():366`；
    面板与商店由 `commands/economy.py:24 from ..core import smith_stock as _ss` 调。

    ⚠️ 本函数第一行**必须先 `import_game_data("shop")`**：本模块在 `game/core/` 下，直接
    `import game.core.smith_stock` 会先跑尚未完成的 `game/core/__init__.py` →
    `game/core/index.py:5 from ..data import _INDEXES` → `_assembly.py:9 from ..core.index import
    build_index` = **循环导入 ImportError**（2026-09-13 实测复现，与 `derive_panel_rules` 同一坑）。
    先导 `game.data`（装配期会把 `game.core.*` 链路走完）再导 core 才通。
    """
    import_game_data("shop", src_root)                       # ★ 见上：data 必须先进来
    mod = import_game_core("smith_stock", src_root)
    qw = as_table(getattr(mod, "QUALITY_WEIGHTS", None), "smith_stock.QUALITY_WEIGHTS")
    qty = as_table(getattr(mod, "_QTY_BY_QUALITY", None), "smith_stock._QTY_BY_QUALITY")
    npc = as_table(getattr(mod, "SMITH_NPC_NAMES", None), "smith_stock.SMITH_NPC_NAMES")
    lvl = as_table(getattr(mod, "_SMITH_TOWN_LEVELS", None), "smith_stock._SMITH_TOWN_LEVELS")
    if not set(qty) <= set(qw):
        raise ValueError(f"smith_stock：_QTY_BY_QUALITY 的档位 {sorted(set(qty) - set(qw))} "
                         f"不在 QUALITY_WEIGHTS 里 —— 源形状变了，拒绝导出")
    if not set(npc) <= set(lvl):
        raise ValueError(f"smith_stock：SMITH_NPC_NAMES 的城镇 {sorted(set(npc) - set(lvl))} "
                         f"不在 _SMITH_TOWN_LEVELS 里 —— 源形状变了，拒绝导出")
    rules = {}
    for name, attr in (("stock_count", "STOCK_COUNT"), ("stock_window", "STOCK_WINDOW"),
                       ("restock_hours", "RESTOCK_HOURS")):
        v = getattr(mod, attr, None)
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise ValueError(f"smith_stock：{attr} 不是正整数（得到 {v!r}）—— 拒绝导出")
        rules[name] = v
    rules["qty_by_quality"] = dict(qty)
    rules["quality_weights"] = dict(qw)
    return sort_table({
        "quality_weights": dict(qw),
        "shelf_rules": rules,
        "npc_names": dict(npc),
        "town_levels": dict(lvl),
    })


# =============================================================================
# shop_stock —— 商店限购/共享库存（真源在 data/shop_limit.py）
# =============================================================================
def derive_shop_stock(src_root: str = None) -> dict:
    """商店库存域（`shop_stock`）→ 一条 = 一个商品的限购配置（共 35 条）。

    真源 = **数据层** `game/data/shop_limit.py:39 SHOP_LIMIT`（v166 鱼鱼拍板的两层限购配置）。
    `game/core/shop_stock.py`（228 行）是**纯消费/状态机**（`check_and_consume():150` /
    `limit_label():213` / `stock_state():85`，惰性补货 + `event_state` 读改写），
    模块内**零静态数据** —— 所以本域导的是那张配置表，键空间与机制一致：
        `item:{iid}`   → SHOP_SUBAREA_ITEMS 消耗品/杂物（i_ 前缀）
        `mat:{mid}`    → SHOP_SMITH_MATERIALS 锻造材料（mat_ 前缀）
        `equip:{rid}`  → SHOP_EQUIP 名册装备（eq_ 前缀）
        `weapon:{名}`  → SHOP_WEAPONS 武器（按名；**当前数据 0 条**，源侧声明未用）

    映射口径
    --------
      · 键 = 源表键原样（**带前缀**，前缀就是商品来源）；值 = 源配置 dict 原样
        （实测字段只有 `stock` / `per_day` / `restock_hours` 三种，35/35 条都有；
        `restock_at` / `max_buy_once` 源侧在文件头声明但**当前数据未出现** → 不补）。
      · 不在本表的商品 = 不限购（这是源侧语义「缺省 = 不限量」，不是本域的空值填充）。
      · `data/shop_limit.py:90 _validate()` 在 **import 期**已自检（前缀/字段类型/`HH:MM` 格式），
        这里只再核「前缀合法 + 值是非空 dict」两道，防 import 被跳过。

    消费者在游戏侧：`commands/economy.py:25 as _sshop`（买前 `check_and_consume`、面板 `limit_label`）。
    """
    mod = import_game_data("shop_limit", src_root)
    lim = as_table(getattr(mod, "SHOP_LIMIT", None), "shop_limit.SHOP_LIMIT")
    out = {}
    for key, cfg in lim.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"shop_stock：非字符串/空键 {key!r} —— 拒绝导出")
        if ":" not in key or key.split(":", 1)[0] not in _LIMIT_PREFIXES:
            raise ValueError(f"shop_stock：{key!r} 的前缀不在 {_LIMIT_PREFIXES} —— 拒绝导出")
        if not isinstance(cfg, dict) or not cfg:
            raise ValueError(f"shop_stock：{key!r} 的配置不是非空 dict（得到 {cfg!r}）—— 拒绝导出")
        out[key] = dict(cfg)
    return sort_table(out)


# =============================================================================
# achievements —— 成就表（game/data/achievements.py）
# =============================================================================
def derive_achievements(src_root: str = None) -> dict:
    """成就域（`achievements`）→ 一条 = 一个成就（表键 = 成就 id，实测 119 条）。

    真源 = `game/data/achievements.py:25 ACHIEVEMENTS`（**一张 list，全量 119 条**，无二次 update）。
    条目字段（实测并集）：`id` / `cat` / `name` / `title` / `desc` / `cond` / `points` /
    `reward` / `bonus` —— **原样进 JSON**：不补缺省（`bonus` 只有一部分条目有、`reward` 的
    `exp` 同理），`cond` 一个都不解释（`cond.type` 是 `achievement_conds` 域的键空间，
    判定实现在 `game/core/achievement_conds.py` 注册表）。

    实测分布（2026-09-13，供对照）：cat 6 值（战斗/成长/探索/社交/副业/隐藏）；
    points 1 或 2（隐藏成就 = 2）；cond 字段 8 种（type 119 / value 95 / key 47 /
    keyword 3 / keywords 2 / flag 3 / inst 1 / no_death 1）；reward 字段 2 种（exp / items）。

    消费者在游戏侧：`commands/social.py` 成就面板、`core/achievements.py`（`cond_met()` 走注册表
    + `claim_achievement_rewards` 发奖，物品 key 是 `mat_`/`i_` 稳定 ID → items 域）。
    """
    mod = import_game_data("achievements", src_root)
    raw = getattr(mod, "ACHIEVEMENTS", None)
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("achievements：game/data/achievements.py:25 ACHIEVEMENTS 不是非空序列 —— 拒绝导出")
    out = {}
    for a in raw:
        if not isinstance(a, dict):
            raise ValueError(f"achievements：条目不是对象（得到 {type(a).__name__}）—— 拒绝导出")
        aid = a.get("id")
        if not isinstance(aid, str) or not aid:
            raise ValueError(f"achievements：条目缺字符串 id（得到 {aid!r}）—— 拒绝导出")
        if aid in out:
            raise ValueError(f"achievements：id {aid!r} 重复 —— 拒绝导出（会静默丢一条）")
        cond = a.get("cond")
        if not isinstance(cond, dict) or not isinstance(cond.get("type"), str) or not cond["type"]:
            raise ValueError(f"achievements：{aid} 的 cond 不是带 type 的对象（得到 {cond!r}）"
                             f" —— 判定入口变了，拒绝导出")
        out[aid] = dict(a)
    return sort_table(out)


# =============================================================================
# achievement_conds —— 成就条件类型注册表（game/core/achievement_conds.py）
# =============================================================================
def derive_achievement_conds(src_root: str = None) -> dict:
    """成就条件域（`achievement_conds`）→ 一条 = 一个条件类型（表键 = `cond.type`，实测 47 条）。

    真源 = `game/core/achievement_conds.py:22 COND_CHECKS`（`register()` 装饰器注册的运行时表，
    v99.5 起消灭 `core/achievements.py cond_met()` 的 41 种 type 硬编码；函数签名
    `fn(player, stats, profs, extra, cond) -> bool`）。条目字段：
        `cond_type`  条件类型（= 表键，便于编辑器按字段渲染）
        `doc`        该条件函数的 docstring 原文（**47/47 都有**；源侧含版本沿革/坑位注）
        `fields`     **实测**：`ACHIEVEMENTS`（achievements 域同一份真源）里 cond 用到的键集
                     （如 ["key","value"]），按字典序 —— 零用的类型是 `[]`（实测 3 条）
        `used_by`    用了这个类型的成就条数（实测合计 119 = 成就总数）

    映射口径：注册表按注册顺序读（`COND_CHECKS` 是 dict），外层键仍字典序（宿主/`sort_table` 保证幂等）；
    `doc` **原样**（含换行的多段注不裁剪成一行）。**不解释也不展开** `cond` 的取值。

    实测闭合（导出期断言）：`ACHIEVEMENTS` 里出现的每个 `cond.type` 都必须已注册（实测用到的
    44 个类型全在表内）；注册了却没成就用的 3 个类型（`hidden_class` / `hidden_class_lv` /
    `skill_has`）照导（`used_by=0`）。

    判定入口在游戏侧：`core/achievements.py cond_met()` → `COND_CHECKS[type](player, stats, profs, extra, cond)`。
    """
    amod = import_game_data("achievements", src_root)        # ★ data 先于 core（防 core↔data 环）
    cmod = import_game_core("achievement_conds", src_root)
    reg = as_table(getattr(cmod, "COND_CHECKS", None), "achievement_conds.COND_CHECKS")
    rows = getattr(amod, "ACHIEVEMENTS", None)
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("achievement_conds：读不到 ACHIEVEMENTS（事实取证源）—— 拒绝导出")
    used, count = {}, {}
    for a in rows:
        ctype = (a.get("cond") or {}).get("type") if isinstance(a, dict) else None
        if not isinstance(ctype, str) or not ctype:
            raise ValueError(f"achievement_conds：成就 {a!r} 的 cond.type 缺失 —— 拒绝导出")
        count[ctype] = count.get(ctype, 0) + 1
        used.setdefault(ctype, set()).update(k for k in a["cond"] if isinstance(k, str))
    unreg = sorted(set(count) - set(reg))
    if unreg:
        raise ValueError(f"achievement_conds：这些 cond.type 在成就数据里出现但**没有注册实现**："
                         f"{unreg} —— 那些成就恒 False，拒绝导出（先修条件注册表）")
    out = {}
    for ctype, fn in reg.items():
        if not isinstance(ctype, str) or not ctype or not callable(fn):
            raise ValueError(f"achievement_conds：注册项 {ctype!r} 形状不对 —— 拒绝导出")
        out[ctype] = {
            "cond_type": ctype,
            "doc": (fn.__doc__ or "").strip(),
            "fields": sorted(used.get(ctype, ())),
            "used_by": count.get(ctype, 0),
        }
    return sort_table(out)


# =============================================================================
# title_conds —— 称号条件（game/core/title_conds.py + data/titles.py 合表）
# =============================================================================
def derive_title_conds(src_root: str = None) -> dict:
    """称号条件域（`title_conds`）→ 一条 = 一个**有注册条件判定**的称号（51→实测 50 条）。

    ================================ 真源是两张表 ================================
        game/core/title_conds.py:14 `CONDITIONS`  v98.3 起消灭 `commands/economy.py
                                                 _earned_titles()` 的 if-elif 硬编码；
                                                 `register(tid)` 注册 50 个判定函数
                                                 `fn(ctx) -> bool`（ctx = TitleCtx:25）
        game/data/titles.py:3       `TITLES`     称号名册 68 条（id/name/desc/bonus/effect）

    映射口径（**合表**，与 npcs 三表合表同法）
    ---------------------------------------------------
      · 键 = `CONDITIONS` 的注册键（称号 id）→ 50 条；条目 = **`TITLES` 里那条原样**
        （实测字段 `id` / `name` / `desc`，部分条目另有 `bonus`（属性加成）/`effect`
        （资源向消费点注册名）—— 有就有、没有就没有，不补）。
      · 注入 `doc`：**仅当**该称号的判定函数带 docstring（实测 7/50 有 —— 其余 43 条的
        判定函数源侧零文档 → 条目里**没有** `doc` 字段，不补空串）。
      · 源侧闭合（导出期断言）：注册了判定的称号 id 必须在 `TITLES` 里找得到（实测 50/50）。
      · **本域不含**另外 18 个称号（副业档 `pro_gather3/6/10` 等 6×3）：它们**没有**条件函数
        （由副业等级/任务奖励路径授予），要导得另起「称号名册」域 —— 见报告 §4。

    消费者在游戏侧：`commands/economy.py` 称号面板/`_earned_titles` 走注册表；
    `core/title_bonus.py` 消费 `TITLES` 的 `bonus`。
    """
    tmod = import_game_data("titles", src_root)               # ★ data 先于 core（防 core↔data 环）
    cmod = import_game_core("title_conds", src_root)
    rows = getattr(tmod, "TITLES", None)
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("title_conds：game/data/titles.py:3 TITLES 不是非空序列 —— 拒绝导出")
    by_id = {}
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError(f"title_conds：TITLES 条目不是对象（得到 {type(r).__name__}）—— 拒绝导出")
        tid = r.get("id")
        if not isinstance(tid, str) or not tid:
            raise ValueError(f"title_conds：TITLES 条目缺字符串 id（得到 {tid!r}）—— 拒绝导出")
        if tid in by_id:
            raise ValueError(f"title_conds：TITLES 里 id {tid!r} 重复 —— 拒绝导出")
        by_id[tid] = r
    reg = as_table(getattr(cmod, "CONDITIONS", None), "title_conds.CONDITIONS")
    missing = sorted(set(reg) - set(by_id))
    if missing:
        raise ValueError(f"title_conds：这些称号注册了条件判定但 titles.py 里查不到：{missing[:5]}"
                         f" —— 名册与判定表对不上，拒绝导出")
    out = {}
    for tid, fn in reg.items():
        if not isinstance(tid, str) or not tid or not callable(fn):
            raise ValueError(f"title_conds：注册项 {tid!r} 形状不对 —— 拒绝导出")
        e = dict(by_id[tid])
        doc = (fn.__doc__ or "").strip()
        if doc:
            e["doc"] = doc
        out[tid] = e
    return sort_table(out)


DOMAINS = {
    "shop": derive_shop,
    "smith_stock": derive_smith_stock,
    "shop_stock": derive_shop_stock,
    "achievements": derive_achievements,
    "achievement_conds": derive_achievement_conds,
    "title_conds": derive_title_conds,
}
