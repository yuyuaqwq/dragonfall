# -*- coding: utf-8 -*-
"""生活·养成线（B5）域插件 —— `craft` / `alchemy` / `cooking` 三个域的真源 → 包 JSON。

契约见 `scripts/export_domains/README.md`：本文件只**读真源、返回内存表**，落盘由宿主
（`scripts/export_game_package.py`：UTF-8 / LF / indent=2 / 原子替换 + `sort_table` 外层键字典序）统一做。
**不许 import `export_game_package`**（宿主会扫本目录 → 循环导入）。公用小工具走 `_helpers.py`。

================================================================================
域 1：`craft` 锻造配方 —— 426 条（表键 = 配方 id `rec_*`）
================================================================================
真源（2026-09-13 实测）：
    `game/data/craft.py:9   CRAFT_RECIPES`          426 条，**巨型字典字面量**（4600+ 行）
    `game/data/craft.py:4635 CRAFT_RECIPE_ALIASES`  3 条：`{配方 id → [旧世界玩家输入别名…]}`
                                                    （v48 约定常驻；`game/core/craft.py:40` 反查）
消费者（游戏侧；导出只搬运不改语义）：
    `game/data/_assembly.py:181`   `build_index("recipes", CRAFT_RECIPES, prefix="rec_", name_field="name")`
                                   → `_INDEXES["recipes"]` 的 `name_to_id` / `id_to_name`
    `game/data/__init__.py:71`      re-export `CRAFT_RECIPES` / `CRAFT_RECIPE_ALIASES`
    `game/core/craft.py:4,13,38,40` 核心合成逻辑：按名取配方 + 别名反查
    `game/commands/economy.py`      3100+ 行的锻造/图纸/获取链命令面（:1745 起按名取配方，
                                   :2064 `rec.get("blueprint") == bp_disp`，:2132/:2194 遍历全表）

映射口径（**本域只做一件事：把配方表原样搬进包**）
    * 一条 = 一个配方，键 = 配方 id；条目**原样**（不改类型、不补默认值、不动字段顺序、不展开引用串）。
      实测字段 census（426 条）：`name/desc/slot/quality/roster_id/mats/gold` 全 426 条有；
      `blueprint` 261 条；`weapon_type` 128 条。叶类型全 JSON 原生（str/int/dict），无 tuple/None。
    * **唯一注入**：`CRAFT_RECIPE_ALIASES`（3 条，值不是 dict、无法自己成一个域）折进它所指的那条
      配方，字段名 `aliases`（`[字符串…]`）。守卫三条：①别名键必须命中 `CRAFT_RECIPES`（否则源侧
      出现了悬空别名 → `raise`）；②源条目里已有 `aliases` 键 → `raise`（注入不许覆盖源真值）；
      ③值必须是非空字符串列表。实测 3/3 命中、0 同名冲突。
    * 空/坏表 → `raise`（空表在编辑器里 = 「0 条」且不报错，是本项目最怕的静默失效）。

留作引用、不展开（见报告 §缺口）
    产物  `roster_id`      → `equip_roster` 域 key（实测 413 个互异值 **100% 命中**；426/426 条
                             配方名 == 名册那条的 `name`，即「配方名 = 装备名」是恒等式）
    材料  `mats`           → 物品 id（实测 137 个互异 `mat_*` 值 **100% 落 items 域**；值是数量 int）
    图纸  `blueprint`      → **显示名字符串**（不是 id）：`name + "图纸"` 对 261/261 条恒成立；
                             按名在 items 域只命中 16 条（items 域共 19 条带 `blueprint_for`）
    槽位/品质 `slot`/`quality`/`weapon_type` → 内容侧词汇（7 / 5 / 8 个取值，落 schema enum，
                             与 `EQUIP_SLOTS` / `QUALITY` / `WEAPON_TYPES` 同表）
    gold 有 1 条为 0（源侧合法值，不补默认）

================================================================================
域 2：`alchemy` 炼金配方 —— 91 条（表键 = 配方 id `al_*`）
================================================================================
真源：`game/data/alchemy.py:3 ALCHEMY_RECIPES`（808 行文件的唯一顶层表；实测 91 条）
消费者：`game/data/_assembly.py:187` `build_index("alchemy", ALCHEMY_RECIPES, prefix="al_", name_field="name")`；
    `game/commands/economy.py:758,804,812`（炼金列表 / 净化分支 / 配方详情）、`:2097` 按 key 先查
    `COOKING_RECIPES` 再查 `ALCHEMY_RECIPES`（两个域共用一个"配方 id"入口，所以两条线必须同批进包）
映射：条目**原样**。字段 census：`cost/product/min_lv/desc/name` 全 91 条；`purify` 6 条（全是 `true`）；
    `blueprint` 2 条。`cost`/`product` 是 `{物品 id: 数量}`（实测 cost 77 个互异值 = 74 `mat_*` + 3 `i_*`；
    product 82 个 = 74 `i_*` + 7 `mat_*` + 1 `it_*`；**两向 100% 落 items 域**）。`min_lv` 实测 1~9。

================================================================================
域 3：`cooking` 烹饪配方 —— 59 条（表键 = 配方 id `cook_*`）
================================================================================
真源：`game/data/cooking.py:9 COOKING_RECIPES`（13 章 2.3 烹饪表 v2.0；实测 59 条）
消费者：`game/data/_assembly.py:188` `build_index("cooking", COOKING_RECIPES, prefix="cook_", name_field="name")`；
    `game/commands/economy.py:923,960-974`（烹饪列表按**插入序**编号 —— 所以导出后外层键按字典序排
    是**包侧**的展示约定，源侧插入序不在本域表达，见报告）；`:2097` 同 alchemy。
映射：条目**原样**。字段 census：`name/desc/min_lv/cost/product` 全 59 条；`blueprint` 3 条。
    `cost` 49 个互异值全 `mat_*`、`product` 53 个（48 `i_*` + 5 `it_*`）—— **100% 落 items 域**。`min_lv` 实测 1~8。

================================================================================
通用纪律（三域一致）
================================================================================
    * 读的是 **import 之后的运行时表**（`game.data.<mod>`），不是源码字面量 —— 与 items/npcs 域同一纪律。
    * 每个域 `raise` 而不是静默降级：表不存在 / 非 dict / 空 / 条目非 dict / 核心字段形状变了。
    * 返回前 `sort_table` 一次（幂等；宿主还会再排一次，结果相同）。
"""

from _helpers import import_game_data, import_game_core, sort_table, as_table  # noqa: F401
# `import_game_core` 本批三域没用到（三张真源表都在 game/data/）—— 保留导入是为了本线后续域
# （props / runes / skill_up / job_guide 里有读 game/core/ 取派生口径的）不必再动 import 行。

# 真源位置（写进报错文案，便于定位「形状变了」时是哪个文件哪张表）
CRAFT_SRC = "game/data/craft.py:9 CRAFT_RECIPES"
CRAFT_ALIAS_SRC = "game/data/craft.py:4635 CRAFT_RECIPE_ALIASES"
ALCHEMY_SRC = "game/data/alchemy.py:3 ALCHEMY_RECIPES"
COOKING_SRC = "game/data/cooking.py:9 COOKING_RECIPES"

ALIAS_FIELD = "aliases"          # craft 注入字段（唯一注入）


# ─────────────────────────────────────────────────────────── 通用守卫
def _require_table(obj, where: str, dom: str) -> dict:
    """真源表必须是非空 dict —— 空表会让编辑器显示「0 条」且不报错（本项目最怕的静默失效）。"""
    tbl = as_table(obj, where)
    if not tbl:
        raise ValueError(f"{dom}：{where} 是空表 —— 源形状变了/表被删，拒绝导出"
                         f"（空表 = 编辑器显示 0 条且不报错）")
    return tbl


def _require_entry(ent, key, where: str, dom: str) -> dict:
    """条目必须是 dict（非 dict 的条目在编辑器里没法按字段编辑）。"""
    if not isinstance(ent, dict):
        raise ValueError(f"{dom}：{where}[{key!r}] 不是 dict（{type(ent).__name__}）—— 源形状变了，拒绝导出")
    return ent


def _load(mod_name: str, src_root: str = None):
    """`game/data/<mod>` 模块 —— `src_root` 省略时走 `_helpers` 的默认仓根。"""
    return import_game_data(mod_name, src_root) if src_root else import_game_data(mod_name)


def _require_field(ent, key, field: str, types, where: str, dom: str, nonempty: bool = True):
    """核心字段存在且类型对 —— 少了它消费者（炼金/烹饪面板、build_index）会当场炸。

    `bool` 不算 `int`（Python 里 `isinstance(True, int)` 为真，但真源里数量/等级绝不接受布尔）。
    """
    if field not in ent:
        raise ValueError(f"{dom}：{where}[{key!r}] 缺字段 {field!r} —— 源形状变了，拒绝导出")
    val = ent[field]
    ok = isinstance(val, types)
    if ok and types is int and isinstance(val, bool):
        ok = False
    if not ok:
        raise ValueError(f"{dom}：{where}[{key!r}].{field} 类型不对（{type(val).__name__}）—— 拒绝导出")
    if nonempty and types is str and not val.strip():
        raise ValueError(f"{dom}：{where}[{key!r}].{field} 是空串 —— 拒绝导出")
    return val


def _require_core(tbl: dict, where: str, dom: str) -> None:
    """三域共用的核心字段守卫：键为非空 str + 条目是 dict + `name` 为非空 str
    （`name` 是 `build_index(..., name_field="name")` 的索引字段，丢了它按名找就废）。"""
    for k, ent in tbl.items():
        if not isinstance(k, str) or not k:
            raise ValueError(f"{dom}：{where} 的键 {k!r} 不是非空字符串 —— 拒绝导出")
        _require_entry(ent, k, where, dom)
        _require_field(ent, k, "name", str, where, dom)


# ─────────────────────────────────────────────────────────── 域 1：craft
def derive_craft(src_root: str = None) -> dict:
    """`craft` 域：`CRAFT_RECIPES`（426 条）+ `CRAFT_RECIPE_ALIASES`（3 条，注入 `aliases`）。

    条目**原样**进 JSON（不补默认值 / 不改类型 / 不展开 `roster_id`·`mats`·`blueprint` 等引用字符串），
    唯一例外是 `aliases` 注入（见文件头 docstring「唯一注入」）。
    """
    mod = _load("craft", src_root)
    recipes = _require_table(getattr(mod, "CRAFT_RECIPES", None), CRAFT_SRC, "craft")
    aliases = _require_table(getattr(mod, "CRAFT_RECIPE_ALIASES", None), CRAFT_ALIAS_SRC, "craft")

    _require_core(recipes, CRAFT_SRC, "craft")
    # 核心字段形状（426/426 实测有）：slot/quality/roster_id 非空 str，lv/gold int，mats 非空 dict[str,int]
    for k, ent in recipes.items():
        for f in ("slot", "quality", "roster_id", "desc"):
            _require_field(ent, k, f, str, CRAFT_SRC, "craft")
        for f in ("lv", "gold"):
            _require_field(ent, k, f, int, CRAFT_SRC, "craft")
        mats = _require_field(ent, k, "mats", dict, CRAFT_SRC, "craft")
        if not mats:
            raise ValueError(f"craft：{CRAFT_SRC}[{k!r}].mats 是空 dict —— 无材料配方不该出现在本表，拒绝导出")
        for mid, cnt in mats.items():
            if not isinstance(mid, str) or not mid:
                raise ValueError(f"craft：{CRAFT_SRC}[{k!r}].mats 的键 {mid!r} 不是非空字符串 —— 拒绝导出")
            if not isinstance(cnt, int) or isinstance(cnt, bool):
                raise ValueError(f"craft：{CRAFT_SRC}[{k!r}].mats[{mid!r}] 不是 int（{cnt!r}）—— 拒绝导出")

    # 别名：只允许折进真实存在的配方，且不许覆盖源条目已有同名键
    injected: dict = {}
    for rid, names in aliases.items():
        if rid not in recipes:
            raise ValueError(f"craft：{CRAFT_ALIAS_SRC}[{rid!r}] 指不到任何配方（悬空别名）—— "
                             f"源侧要么补配方要么删别名，拒绝导出")
        if ALIAS_FIELD in recipes[rid]:
            raise ValueError(f"craft：源条目 {rid!r} 已含字段 {ALIAS_FIELD!r} —— 注入会覆盖源真值，拒绝导出")
        if not isinstance(names, list) or not names or not all(isinstance(x, str) and x for x in names):
            raise ValueError(f"craft：{CRAFT_ALIAS_SRC}[{rid!r}] 不是非空字符串列表（{names!r}）—— 拒绝导出")
        injected[rid] = list(names)

    out: dict = {}
    for rid, ent in recipes.items():
        entry = dict(ent)                       # 字段顺序原样
        if rid in injected:
            entry[ALIAS_FIELD] = injected[rid]
        out[rid] = entry
    return sort_table(out)


# ─────────────────────────────────────────────────────────── 域 2：alchemy
def derive_alchemy(src_root: str = None) -> dict:
    """`alchemy` 域：`ALCHEMY_RECIPES` 原样导出（91 条）。`cost`/`product` 是 `{物品 id: 数量}` 引用串。"""
    mod = _load("alchemy", src_root)
    recs = _require_table(getattr(mod, "ALCHEMY_RECIPES", None), ALCHEMY_SRC, "alchemy")
    _require_core(recs, ALCHEMY_SRC, "alchemy")
    for k, ent in recs.items():
        _require_field(ent, k, "min_lv", int, ALCHEMY_SRC, "alchemy")
        _require_field(ent, k, "desc", str, ALCHEMY_SRC, "alchemy")
        for side in ("cost", "product"):
            side_d = _require_field(ent, k, side, dict, ALCHEMY_SRC, "alchemy")
            if not side_d:
                raise ValueError(f"alchemy：{ALCHEMY_SRC}[{k!r}].{side} 是空 dict —— 拒绝导出")
            for iid, cnt in side_d.items():
                if not isinstance(iid, str) or not iid:
                    raise ValueError(f"alchemy：{ALCHEMY_SRC}[{k!r}].{side} 的键 {iid!r} 不是非空字符串")
                if not isinstance(cnt, int) or isinstance(cnt, bool):
                    raise ValueError(f"alchemy：{ALCHEMY_SRC}[{k!r}].{side}[{iid!r}] 不是 int（{cnt!r}）")
    return sort_table({k: dict(v) for k, v in recs.items()})


# ─────────────────────────────────────────────────────────── 域 3：cooking
def derive_cooking(src_root: str = None) -> dict:
    """`cooking` 域：`COOKING_RECIPES` 原样导出（59 条）。`cost`/`product` 是 `{物品 id: 数量}` 引用串。"""
    mod = _load("cooking", src_root)
    recs = _require_table(getattr(mod, "COOKING_RECIPES", None), COOKING_SRC, "cooking")
    _require_core(recs, COOKING_SRC, "cooking")
    for k, ent in recs.items():
        _require_field(ent, k, "min_lv", int, COOKING_SRC, "cooking")
        _require_field(ent, k, "desc", str, COOKING_SRC, "cooking")
        for side in ("cost", "product"):
            side_d = _require_field(ent, k, side, dict, COOKING_SRC, "cooking")
            if not side_d:
                raise ValueError(f"cooking：{COOKING_SRC}[{k!r}].{side} 是空 dict —— 拒绝导出")
            for iid, cnt in side_d.items():
                if not isinstance(iid, str) or not iid:
                    raise ValueError(f"cooking：{COOKING_SRC}[{k!r}].{side} 的键 {iid!r} 不是非空字符串")
                if not isinstance(cnt, int) or isinstance(cnt, bool):
                    raise ValueError(f"cooking：{COOKING_SRC}[{k!r}].{side}[{iid!r}] 不是 int（{cnt!r}）")
    return sort_table({k: dict(v) for k, v in recs.items()})


# =============================================================================
# 第二批（同日）：`props` / `runes` / `skill_up` / `job_guide`
# -----------------------------------------------------------------------------
# 三个小域 + 一个中等域，与第一批同一纪律：读运行时表、条目原样、坏形状就 raise。
# 每个域的「唯一注入」在函数 docstring 里点名（props.mounts / runes.craft+conflicts /
# job_guide.aliases+extra_resources）；skill_up 无注入。
# =============================================================================
PROPS_SRC = "game/data/props.py:12 PROPS"
SUBAREA_PROPS_SRC = "game/data/props.py:606 SUBAREA_PROPS"
RUNES_SRC = "game/data/runes.py:3 RUNES"
RUNE_CRAFT_SRC = "game/data/runes.py:285 RUNE_CRAFT"
RUNE_CONFLICTS_SRC = "game/data/runes.py:232 RUNE_CONFLICTS"
SKILL_UP_SRC = "game/data/skill_up.py:22 SKILL_UP"
JOB_GUIDE_SRC = "game/data/job_guide.py:172 JOB_GUIDE（= _build_guide() 的产物，:133-169）"
JOB_ALIASES_SRC = "game/data/job_guide.py:180-189 JOB_ALIASES"
EXTRA_RESOURCES_SRC = "game/data/job_guide.py:58 EXTRA_RESOURCES"
EXTRA_RESOURCE_GUIDE_SRC = "game/data/job_guide.py:99 EXTRA_RESOURCE_GUIDE"


def _require_no_field(ent: dict, key, field: str, where: str, dom: str) -> None:
    """注入字段的守卫：源条目里已有同名键 → raise（注入不许覆盖源真值）。"""
    if field in ent:
        raise ValueError(f"{dom}：{where}[{key!r}] 已含字段 {field!r} —— 注入会覆盖源真值，拒绝导出")


def _join_where(where, dom: str, src: str) -> tuple:
    """`"地图id:子区域id"` 拆成两段并各自非空（引用闭合由报告/审计脚本核，导出期只保形状）。"""
    if not isinstance(where, str) or ":" not in where:
        raise ValueError(f"{dom}：{src} 的键 {where!r} 不是「地图id:子区域id」形状 —— 拒绝导出")
    a, b = where.split(":", 1)
    if not a or not b:
        raise ValueError(f"{dom}：{src} 的键 {where!r} 有空的半段 —— 拒绝导出")
    return a, b


def derive_props(src_root: str = None) -> dict:
    """`props` 域：`PROPS`（59 条）原样 + 把 `SUBAREA_PROPS` 折成每条 prop 的 `mounts`。

    真源：
        `game/data/props.py:12  PROPS`          59 条：`{name, icon, desc, texts[2], effect}`
        `game/data/props.py:606 SUBAREA_PROPS`  315 个挂载点 → 621 条挂载（key = `"地图id:子区域id"`，
                                                元素是 prop id 字符串（用默认名）或 `(prop_id, 专属名)` 元组）
    唯一注入：`mounts` = `[{"where": "地图:子区域", "name": 专属名?}]`（源里是"按地点列 prop"，
        折成"每条 prop 列地点"；`name` 只在元组形式上有 —— 字符串形式**不补默认值**，键直接不写）。
        守卫：① prop id 必须命中 `PROPS`；② 源条目已有 `mounts` 键 → raise；③ `where` 必须是
        "x:y" 两段非空。实测 621 条挂载 0 悬空、57/59 条 prop 被挂过（`rock_formation` /
        `wishing_well` 两条**从未挂载** → 没有 `mounts` 键）。
    留作引用、不展开：`mounts.where` 的「地图id」→ maps 域、「子区域id」→ subareas 域
        （实测 315 个挂载点 315/315 两段都命中）；`effect.pool` 的元素 → items 域；
        `effect` 实测三形态：`None` 46 条 / 字符串 2 条（`wish` / `refresh`）/ 字典 11 条
        （`{type: heal|material, daily, pct?|pool?, found_text}`）。
    """
    mod = _load("props", src_root)
    props = _require_table(getattr(mod, "PROPS", None), PROPS_SRC, "props")
    subarea_props = _require_table(getattr(mod, "SUBAREA_PROPS", None), SUBAREA_PROPS_SRC, "props")

    mounts: dict = {}
    n_mounts = 0
    for where, lst in subarea_props.items():
        _join_where(where, "props", SUBAREA_PROPS_SRC)
        if not isinstance(lst, list) or not lst:
            raise ValueError(f"props：{SUBAREA_PROPS_SRC}[{where!r}] 不是非空列表 —— 拒绝导出")
        for el in lst:
            if isinstance(el, tuple):
                if len(el) != 2 or not all(isinstance(x, str) and x for x in el):
                    raise ValueError(f"props：{SUBAREA_PROPS_SRC}[{where!r}] 的元组 {el!r} 形状不对 —— 拒绝导出")
                pid, label = el
            elif isinstance(el, str) and el:
                pid, label = el, None
            else:
                raise ValueError(f"props：{SUBAREA_PROPS_SRC}[{where!r}] 的元素 {el!r} 不是 prop id/元组 —— 拒绝导出")
            if pid not in props:
                raise ValueError(f"props：{SUBAREA_PROPS_SRC}[{where!r}] 引用 {pid!r} 不在 PROPS 里（悬空挂载）—— 拒绝导出")
            item = {"where": where}
            if label is not None:
                item["name"] = label
            mounts.setdefault(pid, []).append(item)
            n_mounts += 1

    if not n_mounts:
        raise ValueError(f"props：{SUBAREA_PROPS_SRC} 一条挂载都没有 —— 源形状变了，拒绝导出"
                         "（空挂载表 = 所有 prop 都不出现在任何子区域，编辑器看不出异常）")

    out: dict = {}
    for pid, ent in props.items():
        _require_entry(ent, pid, PROPS_SRC, "props")
        _require_field(ent, pid, "name", str, PROPS_SRC, "props")
        _require_field(ent, pid, "icon", str, PROPS_SRC, "props")
        _require_field(ent, pid, "desc", str, PROPS_SRC, "props")
        texts = _require_field(ent, pid, "texts", list, PROPS_SRC, "props")
        if not texts or not all(isinstance(t, str) for t in texts):
            raise ValueError(f"props：{PROPS_SRC}[{pid!r}].texts 不是非空字符串列表 —— 拒绝导出")
        _require_no_field(ent, pid, "mounts", PROPS_SRC, "props")
        entry = dict(ent)
        if pid in mounts:
            entry["mounts"] = mounts[pid]
        out[pid] = entry
    return sort_table(out)


def derive_runes(src_root: str = None) -> dict:
    """`runes` 域：`RUNES`（16 条）原样 + 注入 `craft`（`RUNE_CRAFT`）+ `conflicts`（`RUNE_CONFLICTS` 折叠）。

    真源：`game/data/runes.py:3 RUNES`（16 条：`quality/effect/lvl/cost/icon/name/desc`）、
        `:285 RUNE_CRAFT`（16 条 `{mat, count}`，与 RUNES 键**一一对应**）、
        `:232 RUNE_CONFLICTS`（3 对互斥 effect：burn/freeze、barrier/thorns、scavenger/exp_bless）。
    唯一注入（两个）：
        `craft`      = `RUNE_CRAFT[rid]` 原样（`{mat: 物品 id, count: 数量}`；**不是 craft 域的引用**）
        `conflicts`  = 该符文的 effect 在 `RUNE_CONFLICTS` 里的对手 effect 列表（排序；
                       实测只有 6 个 effect 有对手 → 10 条符文无此键）。折叠是无损的：
                       对手表可反推回那 3 对。
    注意（JSON 化，不是本函数改的）：`lvl` 的键在真源是 **int** 1/2/3，JSON 对象键只能是字符串 →
        落盘后是 `"1"/"2"/"3"`（宿主 `json_clean` 的 JSON 往返所致，与 16/16 单域一致）。
    留作引用/未进包：`effect`（16 个取值）在 `effect_rules` 域**解析不到 14 个**（符文效果是引擎侧另一套词汇）；
        `craft.mat` → items 域（3 个互异值 100% 命中）；`RUNE_SHARD_KEY`（`mat_fu_wen_sui_pian`，命中 items）、
        `RUNE_DROP` / `RUNE_CRAFT_SHARDS` / `RUNE_LEVEL_ROMAN` 是引擎侧常量表（非条目形状，未进包）；
        `RUNE_EFFECT_NAMES`（16 条 effect→中文名）与各符文 `name` **实测 16/16 逐条相等**（冗余展示表，未进包）。
    """
    mod = _load("runes", src_root)
    runes = _require_table(getattr(mod, "RUNES", None), RUNES_SRC, "runes")
    craft = _require_table(getattr(mod, "RUNE_CRAFT", None), RUNE_CRAFT_SRC, "runes")
    conflicts = getattr(mod, "RUNE_CONFLICTS", None)
    if not isinstance(conflicts, list) or not conflicts:
        raise ValueError(f"runes：{RUNE_CONFLICTS_SRC} 不是非空列表 —— 源形状变了，拒绝导出")

    miss = sorted(k for k in craft if k not in runes)
    if miss:
        raise ValueError(f"runes：{RUNE_CRAFT_SRC} 有 {len(miss)} 条不在 RUNES 里（例 {miss[:3]}）—— 拒绝导出")
    partner: dict = {}
    for pair in conflicts:
        if not isinstance(pair, list) or len(pair) < 2 or not all(isinstance(x, str) and x for x in pair):
            raise ValueError(f"runes：{RUNE_CONFLICTS_SRC} 的 {pair!r} 不是 ≥2 个非空字符串 —— 拒绝导出")
        for e in pair:
            for o in pair:
                if o != e:
                    partner.setdefault(e, set()).add(o)

    for rid, ent in runes.items():
        _require_entry(ent, rid, RUNES_SRC, "runes")
        for f in ("name", "icon", "desc", "effect", "quality"):
            _require_field(ent, rid, f, str, RUNES_SRC, "runes")
        _require_field(ent, rid, "cost", int, RUNES_SRC, "runes")
        lvl = _require_field(ent, rid, "lvl", dict, RUNES_SRC, "runes")
        if not lvl:
            raise ValueError(f"runes：{RUNES_SRC}[{rid!r}].lvl 是空 dict —— 拒绝导出")
        for k, v in lvl.items():
            if not isinstance(k, int) or isinstance(k, bool):
                raise ValueError(f"runes：{RUNES_SRC}[{rid!r}].lvl 的键 {k!r} 不是 int —— 拒绝导出")
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                if not (isinstance(v, list) and v and all(
                        not isinstance(x, bool) and isinstance(x, (int, float)) for x in v)):
                    raise ValueError(f"runes：{RUNES_SRC}[{rid!r}].lvl[{k!r}] 不是数值/数值列表（{v!r}）")
        for f in ("craft", "conflicts"):
            _require_no_field(ent, rid, f, RUNES_SRC, "runes")

    out: dict = {}
    for rid, ent in runes.items():
        entry = dict(ent)
        entry["craft"] = dict(craft[rid])
        ps = partner.get(ent["effect"])
        if ps:
            entry["conflicts"] = sorted(ps)
        out[rid] = entry
    return sort_table(out)


def derive_skill_up(src_root: str = None) -> dict:
    """`skill_up` 域：`SKILL_UP` 原样导出（305 条，键 = 技能稳定 id）。**无注入**。

    真源：`game/data/skill_up.py:22 SKILL_UP`（由 `scripts/gen_skill_up_p0bc.py` 生成；
        v181 P0B-C 把键从「技能中文名」改成稳定 id：基础/导师技 = 现存 `sk_id`（67 条），
        分支技 = 生成的 `sk_br_*` id（238 条））。字段实测只有三个：`name`(305)、`max`(305)、
        `p`(165) —— 文件头声明的 `c` / `m` / `l` 在当前数据里**一条都没有**（schema 备位）。
    未进包（同一次搬运没处放）：`SKILL_FLAT_BASE=12` / `SKILL_FLAT_PER_PLAYER_LV=1` /
        `SKILL_FLAT_PER_SKILL_LV=2` 三个常量（引擎 `skill_flat_value` 与 numeric_lib 共用的口径）。
    引用（不展开、且**本域不声明 ref**）：305 个键按 **name** 100% 命中包内 `skills` 域；
        按 **id** 只 67/305 命中 —— 因为包内 skills 域的 238 条分支技用的是**显示名**做键
        （实测 238/238 键 == 该条目 name），而 skill_up 用的是 `sk_br_*` 稳定 id
        （源侧 v181 键空间分叉，归口要等 skills 域那一路，见报告 §缺口）。
    """
    mod = _load("skill_up", src_root)
    table = _require_table(getattr(mod, "SKILL_UP", None), SKILL_UP_SRC, "skill_up")
    _require_core(table, SKILL_UP_SRC, "skill_up")
    for k, ent in table.items():
        _require_field(ent, k, "max", int, SKILL_UP_SRC, "skill_up")
        if not (isinstance(ent["max"], int) and not isinstance(ent["max"], bool) and ent["max"] >= 1):
            raise ValueError(f"skill_up：{SKILL_UP_SRC}[{k!r}].max 不是 ≥1 的 int（{ent['max']!r}）—— 拒绝导出")
        if "p" in ent:
            _require_field(ent, k, "p", int, SKILL_UP_SRC, "skill_up")
    return sort_table({k: dict(v) for k, v in table.items()})


def derive_job_guide(src_root: str = None) -> dict:
    """`job_guide` 域：`JOB_GUIDE`（7 条，键 = 职业 id）原样 + 注入 `aliases` + `extra_resources`。

    真源：`game/data/job_guide.py:133-169 _build_guide()` → `:172 JOB_GUIDE`（7 职业 × 20 字段；
        副产物 `BASE_ORDER` / `HIDDEN_ORDER` / `HIDDEN_SUCCESSORS` 实测 7/0/{} —— 本轮无隐藏职业）。
    唯一注入（两个）：
        `aliases`          = `JOB_ALIASES`（:180-189，44 个名字 → 职业 id）**按职业反向折叠**成名字列表
        `extra_resources`  = `EXTRA_RESOURCES`（:58，`{cls_mu_shi: [resonance, echo]}`）+ 其展示元数据
                             `EXTRA_RESOURCE_GUIDE`（:99）→ `[{key, name, max, desc}]`（实测只有牧师一条）
    留作引用/未进包：`resource_key` 6 个（rage/element/energy/faith/cp/chi）**100% 命中 effect_rules 域**；
        `extra_resources[].key`（resonance/echo）**不在 effect_rules**（歌者专属，引擎批次 2 才启用）；
        `position` 每句都是该职业 `classes` 域 `desc` 的子串（源侧测试强校验）；
        `BRANCH_KEY_DISPLAY`（:29，武僧→淬势者）已体现在 `tiers` 的取值里，不单独进包。
    """
    mod = _load("job_guide", src_root)
    guide = _require_table(getattr(mod, "JOB_GUIDE", None), JOB_GUIDE_SRC, "job_guide")
    aliases = _require_table(getattr(mod, "JOB_ALIASES", None), JOB_ALIASES_SRC, "job_guide")
    extra = _require_table(getattr(mod, "EXTRA_RESOURCES", None), EXTRA_RESOURCES_SRC, "job_guide")
    extra_g = getattr(mod, "EXTRA_RESOURCE_GUIDE", None)
    if not isinstance(extra_g, dict) or not extra_g:
        raise ValueError(f"job_guide：{EXTRA_RESOURCE_GUIDE_SRC} 不是非空 dict —— 源形状变了，拒绝导出")

    by_cid: dict = {}
    for nm, cid in aliases.items():
        if not isinstance(nm, str) or not nm or not isinstance(cid, str) or not cid:
            raise ValueError(f"job_guide：{JOB_ALIASES_SRC} 的 {nm!r}→{cid!r} 不是两个非空字符串 —— 拒绝导出")
        if cid not in guide:
            raise ValueError(f"job_guide：{JOB_ALIASES_SRC} 的别名 {nm!r} 指向不存在的职业 {cid!r} —— 拒绝导出")
        by_cid.setdefault(cid, []).append(nm)

    ex_by_cid: dict = {}
    for cid, keys in extra.items():
        if cid not in guide:
            raise ValueError(f"job_guide：{EXTRA_RESOURCES_SRC} 的键 {cid!r} 不在 JOB_GUIDE 里 —— 拒绝导出")
        if not isinstance(keys, list) or not keys:
            raise ValueError(f"job_guide：{EXTRA_RESOURCES_SRC}[{cid!r}] 不是非空列表 —— 拒绝导出")
        items_ = []
        for k in keys:
            if not isinstance(k, str) or k not in extra_g:
                raise ValueError(f"job_guide：{EXTRA_RESOURCES_SRC}[{cid!r}] 引用 {k!r} 不在 "
                                 f"{EXTRA_RESOURCE_GUIDE_SRC} 里 —— 拒绝导出")
            meta = extra_g[k]
            if not isinstance(meta, dict) or not isinstance(meta.get("name"), str):
                raise ValueError(f"job_guide：{EXTRA_RESOURCE_GUIDE_SRC}[{k!r}] 形状不对（{meta!r}）—— 拒绝导出")
            items_.append({**meta, "key": k})
        ex_by_cid[cid] = items_

    for cid, ent in guide.items():
        _require_entry(ent, cid, JOB_GUIDE_SRC, "job_guide")
        for f in ("cls_id", "name", "desc", "position"):
            _require_field(ent, cid, f, str, JOB_GUIDE_SRC, "job_guide")
        if ent["cls_id"] != cid:
            raise ValueError(f"job_guide：{JOB_GUIDE_SRC}[{cid!r}].cls_id = {ent['cls_id']!r} 与键不一致 —— 拒绝导出")
        for f in ("aliases", "extra_resources"):
            _require_no_field(ent, cid, f, JOB_GUIDE_SRC, "job_guide")

    out: dict = {}
    for cid, ent in guide.items():
        entry = dict(ent)
        if cid in by_cid:
            entry["aliases"] = sorted(by_cid[cid])
        if cid in ex_by_cid:
            entry["extra_resources"] = ex_by_cid[cid]
        out[cid] = entry
    return sort_table(out)



# ================================================================================
# 域 8：`food_effects` 食物战斗效果数值权威表 —— 19 条（B8 批，2026-09-13）
# ================================================================================

FOOD_SRC = "game/data/food_effect_data.py:21 FOOD_EFFECT_PARAMS"
NAMES_SRC = "game/data/food_effect_data.py:50 FOOD_EFFECT_NAMES"


def derive_food_effects(src_root: str = None) -> dict:
    """`food_effects` 域：`FOOD_EFFECT_PARAMS`（19 条）原样导出（零注入、不筛、不补默认值）。

    真源：`game/data/food_effect_data.py:21 FOOD_EFFECT_PARAMS` —— v180F「清2b 食物效果数值权威表」，
        把此前散在 `game/core/food_effects.py` 与 `battle.py` 里的 17 个 handler 数值收口成一张表。

    消费者（游戏侧，导出只搬运不改语义）：
        `game/services/battle_food_proc.py:36 _food_params()`  战斗内食物效果装配（读表零默认值：
            `_fp(key, field, default=0.0)` —— 缺字段 = 无此行为，不复制硬编码）
        `game/core/food_effects.py`                             战斗外 / 图鉴展示
        `game/commands/battle_item_use.py:170`                  `foodfx:aid,...` 翻译入口（吃料理唯一入口）

    映射口径（**本域只做一件事：把表原样搬进包**）
        * 一条 = 一个效果键（`lifesteal` / `bleed` / `regen` / …），条目**原样**：不改类型、
          不补默认值、不动字段顺序、不展开引用串。
        * 字段 census（19 条实测，**按条目实算不是并集**）：数值字段按效果语义取用 ——
          `pct` / `chance` / `mult` / `atk_pct` / `hp_ratio` / `turns` / `slow_turns` /
          `stacks` / `max_n`（并集 9 个），叶类型全 JSON 原生（str/float/int，无 tuple/None）。
          源里的 `label` **只有 1/19 条有**（`lifesteal`，值 `"吸血"`）—— 展示名的**主表**是
          `FOOD_EFFECT_NAMES`（19 条，键集与参数表完全一致）→ 本函数把它作为 `name` 注入。
        * 空/坏表 → `raise`（空表在编辑器里 = 「0 条」且不报错，本项目最怕的静默失效）。

    留作引用、不展开：无 —— 本表自足（`name` 是展示名，不是跨域引用串）。
    """
    mod = _load("food_effect_data", src_root)
    tbl = _require_table(getattr(mod, "FOOD_EFFECT_PARAMS", None), FOOD_SRC, "food_effects")
    names = _require_table(getattr(mod, "FOOD_EFFECT_NAMES", None), NAMES_SRC, "food_effects")
    out = {}
    for key, ent in tbl.items():
        entry = dict(_require_entry(ent, key, FOOD_SRC, "food_effects"))
        # 唯一注入：展示名（`FOOD_EFFECT_NAMES`，与参数表 **19/19 键集完全一致**，实测 0 缺 0 多）。
        # 守卫三条：①缺该键 → raise（源侧出现只加数值没给展示名的效果 = 编辑器里没中文名）
        #          ②源条目已有 name → raise（不许覆盖源真值）
        #          ③展示名必须是非空字符串
        if key not in names:
            raise ValueError(f"food_effects：{key!r} 在 {NAMES_SRC} 里没有展示名 —— 拒绝导出")
        if "name" in entry:
            raise ValueError(f"food_effects：{key!r} 源条目已有 name 字段 —— 注入不许覆盖源真值")
        nm = names[key]
        if not isinstance(nm, str) or not nm.strip():
            raise ValueError(f"food_effects：{key!r} 的展示名不是非空字符串（{nm!r}）")
        entry["name"] = nm
        out[key] = entry
    return sort_table(out)


DOMAINS = {
    "craft": derive_craft,
    "alchemy": derive_alchemy,
    "cooking": derive_cooking,
    "props": derive_props,
    "runes": derive_runes,
    "skill_up": derive_skill_up,
    "job_guide": derive_job_guide,
    "food_effects": derive_food_effects,
}
