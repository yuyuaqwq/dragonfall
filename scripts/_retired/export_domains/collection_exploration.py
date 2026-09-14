# -*- coding: utf-8 -*-
"""B8.2 线2 域插件 —— 收藏册 + 探索（两个域，一个文件独占一路，多路并行零冲突）。

契约见 `scripts/export_domains/README.md`：本文件只做「真源 → 内存表」的单向搬运
（条目原样进 JSON：不补默认值、不改类型、不展开引用字符串），落盘/比对/清单全在宿主。

两个域的真源（都读 **import 之后的运行时表**，不是源码字面量）
================================================================

① `collection_books` —— 冒险者收藏册（5 套 / 42 条目）
    真源：`game/data/collection_book.py:20 COLLECTION_BOOKS`
    形状：**列表** `[{id, name, desc, entries:[{key,name,hint}], reward}]`
          → 落包为**表**（键 = 册 id），与包内既有「源侧 list → 包侧 dict」的域同法
          （`achievements` / `title_conds` / `equip_roster` 都是这么落的）。
    ⚠️ 列表序是**内容**：总览按源列表序逐册渲染（`commands/collection.py` 直接 `for b in books`），
      而包侧表按键字典序落盘会**丢列表序**（实测源序 book_fish/book_ore/book_trophy/book_food/
      book_relic ≠ 键字典序 book_fish/book_food/book_ore/book_relic/book_trophy）
      → 导出期注入 `order`（0 起，= 源列表下标），消费端（`content/collection.py`）按它还原源序。
      注入先例：`subareas` 域注入 `map`（world_explore.py），同为「把结构信息摊平进条目」。
    实测（2026-09-13，游戏仓 master 真跑）：
        5 册 / 42 条目（8+8+10+8+8）；册 id 全局唯一；条目 key 册内唯一且**跨册 0 重复**
        （42/42 全局唯一）→ 判定口径（一个 key 只属一册）成立。
        条目字段恒为 {key,name,hint} 三个非空 str（42/42）；
        reward 恒有 {chest,title,bonus}（5/5）：chest 是 items 域键（5/5 命中 ITEMS）、
        bonus 是非空 {属性: 正整数}、title 是非空 str。
    未导出（本域不碰）：模块级只有 `COLLECTION_BOOKS` 一张表（文件头另无别的常量）；
        `reward.title` 的**称号闭合**不在本域（见报告遗留项：5 个称号名在 titles 域
        `TITLES`(68) / `title_conds`(50) 里都查无 —— 源文件头声称「对应 TITLES 条目」，
        实测未登记；本域只导出原样字符串，不替它造名册条目）。

② `exploration` —— 探索点位表（628 点）
    真源：`game/core/exploration.py` —— **该文件没有可搬运的「一张行表」**：
        · 模块级静态表**只有** `:23 _FIRST_VISIT_MAT_POOL`（5 个材料中文名，隐藏房间首访随机池）；
        · `region_progress():96` / `overall_progress():137` 是**对 `MAPS × SUBAREAS` 的运行时聚合**
          （逻辑，不是数据）；`record_visit():39` 是副作用流程（写 db + 发奖），属宿主。
        → 本域把「探索点」这一层**投影**成表（键 = `地图id:子区域id`，**与宿主
          `visited_subareas` 表 / `db.get_visited_subareas()` 的键空间逐字相同**）；
          聚合逻辑改用**包内模块承载**：`content/exploration.py`
          （`region_progress(visited)` / `overall_progress(visited)`，逐字搬自真源那两个函数，
           唯一接口替换 = 到访集合由调用方传，包内不读宿主 DB）。
    ⚠️ **未导出 `_FIRST_VISIT_MAT_POOL`（有意，不是漏）**：它是该文件唯一的模块级静态表，
      但 ① 消费端仍是宿主 `record_visit()`（B8.2 本路命令不用它，未接线）；
      ② 框架门禁 `tests/test_item_field_coverage.py` 要求「一个域的**所有行同形状**」
         （schema 的 `required` 必须在每条数据里都成立）→ 塞一条保留配置行（先例 `shop` 的
         `wild_trade`）会让本域多出一种形状，破「一条 = 一个探索点」的契约、也让 schema 只能
         退化成「无 required」。故本域只导点表，材料池留宿主侧，登记在报告遗留项。
    条目形状（实测 628 条全量）：`{map, region, hidden, order}`
        map     str   所在图 id（= 键的 `:` 前半，摊平）
        region  str   所在图的 `region` 字段（= `region_progress` 的聚合键；实测 10 个境全非空）
        hidden  bool  子区域 `hidden` 标记（真源 `_is_hidden()` = `bool(sa.get("hidden"))`）
        order   int   全局序号（MAPS 顺序 × 子区域顺序；= `region_progress` 的遍历序）
    为什么 `order` 必须进来：`region_progress` 的**返回序 = MAPS 里 region 的首次出现序**
      （实测 `南境·绿野` 首、`北境·烬原` 末，**不是**字典序）——表落盘会丢序，不注入就必然
      漂「域的展示顺序」（命令层逐行渲染，顺序错=输出不等价）。
    与已进包域的关系（**不重复造表**）：
        · `subareas` 域一行 = 一个子区域（id/name/desc/lv/npcs/monsters/… + 注入 `map`）；
          本域一行 = 一个**探索点**（只有地址/境/隐藏/序四个字段）——只取「进度骨架」这一投影，
          子区域的 name/desc/lv/内容字段一个都不进本域。
        · `worlds` 域一行 = 一张图的世界级元数据（含 `region`）；本域不设「图」行，
          region 只是逐点摊平的聚合键（与 worlds 域字段交集仅 `region` 的取值）。
        · `pois` 域键**同为** `地图id:子区域id`（同地址形式）：pois 域一行 = 该点上的**交互点**
          （内容），本域一行 = 该点**是不是探索点 / 何时算到访**（进度）——键同、语义不同。
    形状门禁（任一不成立 → raise，拒绝导出）：
        · MAPS 非空 list、SUBAREAS 非空 dict，两者图 id 集合相等（悬空/缺图 = 源形状变了）；
        · 每个子区域 id 非空 str、图内唯一；键（地图:子区域）全局唯一；
        · 导出的点表非空（空表 = 静默空域，编辑器会显示 0 条而不报错）。

实测（2026-09-13，游戏仓 master 真跑）
=====================================
  * collection_books 5 条（42 条目 = 8+8+10+8+8，与文件头声明一致）
  * exploration 628 点（121 图 / 578 非隐藏 + 50 隐藏；10 个境，region 全非空）
"""

import sys

from _helpers import import_game_data, sort_table, as_table


def _game_data(src_root):
    """import 游戏仓 `game.data` **包本身** —— 返回**装配后**的包命名空间。

    与 world_explore.py 的同名助手同因：`game/data/_assembly.py:94-97` 在**包 import 期**
    把三张 `EXTRA_SUBAREAS`（网状房间，id 自 `_4` 起）就地 extend 进 `SUBAREAS`
    —— 只看 `subareas.py` 源码字面量会**少 79 个房间**（628 → 549）。
    走 `import_game_data()` 时 Python 会先执行 `game.data.__init__`（= 跑装配），
    因此 import 之后 `sys.modules["game.data"]` 就是组装完的同一份命名空间。
    """
    import_game_data("collection_book", src_root)   # 触发 game.data.__init__ → _assembly 装配
    return sys.modules["game.data"]


# =============================================================================
# ① collection_books —— 冒险者收藏册（5 套 / 42 条目）
# =============================================================================
def derive_collection_books(src_root: str = None) -> dict:
    """收藏册域：读 `COLLECTION_BOOKS`（**列表**），一条 = 一册（键 = 册 id）。

    详见本文件头 ①：条目 = 源 dict **原样** + 注入 `order`（源列表下标，还原渲染序）。
    形状门禁（任一不成立 → raise，拒绝导出）：
        * 表是非空 list；每册是 dict，`id`/`name`/`desc` 非空 str，`id` 全局唯一；
        * `entries` 是非空 list，每条恒为 {key,name,hint} 三个**非空 str**（不补字段、不省略）；
        * 条目 key **册内唯一**（重复 → 该册进度恒多算一条，静默误差）；
        * `reward` 是非空 dict，`chest` 命中 items 域（引用闭合）、`title` 非空 str、
          `bonus` 是非空 {str: 正整数}（v174 实装：满套动态永久属性）。
    """
    ns = _game_data(src_root)
    books = getattr(ns, "COLLECTION_BOOKS", None)
    if not isinstance(books, (list, tuple)) or not books:
        raise ValueError("game.data.COLLECTION_BOOKS 不是非空列表 —— 源形状变了，拒绝导出")
    items = getattr(ns, "ITEMS", None)
    if not isinstance(items, dict) or not items:
        raise ValueError("game.data.ITEMS 不是非空 dict（reward.chest 的闭合证据）—— 拒绝导出")

    out: dict = {}
    for idx, b in enumerate(books):
        if not isinstance(b, dict):
            raise ValueError(f"COLLECTION_BOOKS[{idx}] 不是 dict（得到 {type(b).__name__}）—— 拒绝导出")
        bid = b.get("id")
        if not isinstance(bid, str) or not bid:
            raise ValueError(f"COLLECTION_BOOKS[{idx}] 缺非空 str `id`（得到 {bid!r}）—— 拒绝导出")
        if bid in out:
            raise ValueError(f"收藏册 id 重复：{bid!r} —— 外层键会丢一册，拒绝导出")
        for f in ("name", "desc"):
            v = b.get(f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"COLLECTION_BOOKS[{bid!r}] 的 `{f}` 不是非空 str（得到 {v!r}）")
        entries = b.get("entries")
        if not isinstance(entries, (list, tuple)) or not entries:
            raise ValueError(f"COLLECTION_BOOKS[{bid!r}].entries 不是非空列表 —— 拒绝导出")
        seen = set()
        for e in entries:
            if not isinstance(e, dict):
                raise ValueError(f"COLLECTION_BOOKS[{bid!r}] 里有非 dict 条目：{e!r}")
            if sorted(e) != ["hint", "key", "name"]:
                raise ValueError(
                    f"COLLECTION_BOOKS[{bid!r}] 的条目字段集变了：{sorted(e)} —— "
                    f"（消费端按 key/name/hint 三字段读）拒绝导出")
            for f in ("key", "name", "hint"):
                v = e.get(f)
                if not isinstance(v, str) or not v:
                    raise ValueError(f"COLLECTION_BOOKS[{bid!r}] 条目 `{f}` 不是非空 str（{v!r}）")
            if e["key"] in seen:
                raise ValueError(f"COLLECTION_BOOKS[{bid!r}] 条目 key 重复：{e['key']!r}"
                                 f" —— 进度会多算一条，拒绝导出")
            seen.add(e["key"])
        rw = b.get("reward")
        if not isinstance(rw, dict) or not rw:
            raise ValueError(f"COLLECTION_BOOKS[{bid!r}].reward 不是非空 dict —— 拒绝导出")
        for f in ("chest", "title"):
            v = rw.get(f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"COLLECTION_BOOKS[{bid!r}].reward.{f} 不是非空 str（{v!r}）")
        if rw["chest"] not in items:
            raise ValueError(f"COLLECTION_BOOKS[{bid!r}].reward.chest = {rw['chest']!r} "
                             f"在 items 域里查无 —— 满套宝箱发不出去，拒绝导出")
        bonus = rw.get("bonus")
        if not isinstance(bonus, dict) or not bonus:
            raise ValueError(f"COLLECTION_BOOKS[{bid!r}].reward.bonus 不是非空 dict —— 拒绝导出")
        for k, v in bonus.items():
            if not isinstance(k, str) or not k or not isinstance(v, int) or isinstance(v, bool) or v <= 0:
                raise ValueError(f"COLLECTION_BOOKS[{bid!r}].reward.bonus[{k!r}] = {v!r} "
                                 f"不是正整数 —— 永久属性消费点靠它，拒绝导出")
        entry = dict(b)          # 浅拷贝：不与被装配期改写过的源对象别名
        entry["order"] = idx     # 导出期注入（源里没有）：还原源列表序
        out[bid] = entry
    return sort_table(out)


# =============================================================================
# ② exploration —— 探索点位表（628 点 + 保留键 _config）
# =============================================================================
def derive_exploration(src_root: str = None) -> dict:
    """探索域：读 `MAPS × SUBAREAS`，一条 = 一个探索点（键 = `地图id:子区域id`）。

    详见本文件头 ②（含「为什么必须注入 order」「未导出首访材料池的理由」与三个已进包域的边界）。
    形状门禁（任一不成立 → raise，拒绝导出）：
        * MAPS 非空 list、每图 id 非空 str 且唯一、`region` 是 str（允许空串 —— 真源
          `_m.get("region") or ""` 也是空串聚合，不替它编值）；
        * SUBAREAS 非空 dict；两者的图 id 集合**必须相等**（缺一边 = 悬空/漏图）；
        * 每图的行是 list（真源 `if not sas: continue` 只跳过空图 —— 本域等价：空图无点）；
        * 点键（地图:子区域）全局唯一；子区域 id 非空 str 且图内唯一；
        * 导出的点表非空（空表 = 静默空域，编辑器只显示「0 条」不报错 —— 最难查的那种）。
    """
    ns = _game_data(src_root)
    maps = getattr(ns, "MAPS", None)
    subareas = as_table(getattr(ns, "SUBAREAS", None), "game.data.SUBAREAS")
    if not isinstance(maps, list) or not maps:
        raise ValueError("game.data.MAPS 不是非空 list —— 源形状变了，拒绝导出")

    map_ids = []
    regions = {}
    for m in maps:
        if not isinstance(m, dict):
            raise ValueError(f"MAPS 里有非 dict 条目：{m!r} —— 拒绝导出")
        mid = m.get("id")
        if not isinstance(mid, str) or not mid:
            raise ValueError(f"MAPS 条目缺 id（或不是非空 str）：{m!r}")
        if mid in map_ids:
            raise ValueError(f"图 id 重复：{mid!r} —— 拒绝导出")
        region = m.get("region") or ""
        if not isinstance(region, str):
            raise ValueError(f"MAPS[{mid!r}].region 不是 str（得到 {region!r}）—— 聚合键会漂，拒绝导出")
        map_ids.append(mid)
        regions[mid] = region

    if set(subareas) != set(map_ids):
        raise ValueError(
            f"SUBAREAS 与 MAPS 的图 id 集合不相等："
            f"只在这边 {sorted(set(subareas) - set(map_ids))[:10]} / "
            f"只在那边 {sorted(set(map_ids) - set(subareas))[:10]} —— 源形状变了，拒绝导出")

    out: dict = {}
    order = 0
    for mid in map_ids:
        sas = subareas.get(mid) or []
        if not isinstance(sas, list):
            raise ValueError(f"SUBAREAS[{mid!r}] 不是 list（得到 {type(sas).__name__}）—— 拒绝导出")
        region = regions[mid]
        seen = set()
        for sa in sas:
            if not isinstance(sa, dict):
                raise ValueError(f"SUBAREAS[{mid!r}] 里有非 dict 子区域：{sa!r}")
            sid = sa.get("id")
            if not isinstance(sid, str) or not sid:
                raise ValueError(f"SUBAREAS[{mid!r}] 里有缺 id 的子区域：{sa!r}")
            if sid in seen:
                raise ValueError(f"SUBAREAS[{mid!r}] 子区域 id 重复：{sid!r} —— 拒绝导出")
            seen.add(sid)
            key = f"{mid}:{sid}"
            if key in out:
                raise ValueError(f"探索点键重复：{key!r} —— 外层键会丢一点，拒绝导出")
            out[key] = {
                "map": mid,
                "region": region,
                "hidden": bool(sa.get("hidden")),
                "order": order,
            }
            order += 1
    if not out:
        raise ValueError("导出的探索点是空表（MAPS × SUBAREAS 一个点都没有）—— 拒绝导出")
    return sort_table(out)


DOMAINS = {
    "collection_books": derive_collection_books,
    "exploration": derive_exploration,
}
