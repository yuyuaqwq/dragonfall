# -*- coding: utf-8 -*-
"""B14-3「缺口 46 名」收口线域插件 —— 6 个新域（**表组**形状）。

契约见同目录 `README.md`：只读真源、返回内存表；落盘/排序/清单由宿主
`scripts/export_game_package.py` 统一做；**不许 import 宿主导出器**（循环导入），公用小工具走
`_helpers.py`。派生函数必须定义在 `DOMAINS = {` **之前**。

本文件为什么是「表组」形状（顶层键 = 真源常量名，值 = 该常量**原样**）
--------------------------------------------------------------------
这 6 个宿主模块（`equipment` / `factions` / `enchant` / `poi_pools` / `quest_add_v140` / `gems`）
包内**没有对应域**（B14-2 各线的报告逐名登记为「无域可依」，例：`content/catalog_items.py:50`、
`content/catalog_core.py:83`）。而它们的内容**不是「一条 = 一个实体」**，是「一张张常量表」：
一张品质表 / 一张阵营表 / 一张配方表 / 一张池子…… 硬按实体域的形状导出＝要么给每张表硬造实体
字段（造数据），要么把 `required` 放水（B14-3_BRIEF §2.4 禁）。

⇒ 沿用包内**已有的同型域**（`game_config`「一条 = 一个源模块的常量组」`b9_l7_domains.py:30`、
`guild`「4 张表打包成 1 条」`schemas/guild.schema.json`、`smith_stock`/`panel_rules`）：
**一条 = 一张源表**（外层键 = 源常量名原样，值 = 该表的值原样）。

只加不改：本文件是**新文件**，不改任何既有域的派生函数（并行 9 条线零冲突）。
每个域都带「源侧断言」—— 表被删/空表/形状变了 → `raise`，绝不静默产空表
（空表在编辑器里 = 显示 0 条且不报错，是本项目最怕的故障）。

未导（写在这里防后人「顺手补上」）
----------------------------------
* `equipment.py` 其余 6 个常量（`WEAPON_NAME_SUFFIX`/`EQUIP_NAME_PREFIX`/`EQUIP_PREFIX_FLAVOR`/
  `EQUIP_NAME_SUFFIX`/`AFFIX_COUNT`/`AFFIX_FALLBACK`）：**包内无读点**（宿主侧的 51 处 data-import
  已由 B14 收口线把这几张表 dump 进 `content/catalog_rules.py` 字面量）→ 仍不进域（要进是同一个域加一行）。
  （2026-09-14 收口：原清单里的 `WEAPON_TYPES`/`QUALITY_CN`/`WT_CN`/`WEAPON_DIST`/`ARMOR_FAMILY`/
  `ARMOR_FAMILY_ALIAS` 6 个**已补进域** —— 它们是 `content/index.py` 索引表与 `content/stats.py`
  模块级取件的真读点。）
* `factions.py` 的营地族（`FACTION_SHOP`/`FACTION_CAMPS`/`FACTION_CAMP_*`）：同理，非本轮缺口名。
* `gems.py` 的掉落族（`GEM_BASE_NAME`/`GEM_ITEM_TYPE`/`GEM_STATS`/`GEM_REMOVE_COST`/`GEM_DROP_RATE`/
  `GEM_DROP_TIER`/`GEM_BOSS_FIXED`）：同理。
* `poi_pools.py` 全 3 个常量都进了（无未导项）。
* `quest_add_v140.py` 的 `QUEST_ADD`/`QUEST_MAT`（`npc_story.py:189` 已判定「不在 quests 域」的
  奖励补丁行/材料补丁行）与 `SUPPLY_BOX`：非本轮缺口名（包内无读点）→ 不进域，登记在报告「未做」。
"""
from _helpers import import_game_data, sort_table

# =============================================================================
# 通用：表组派生（一条 = 一张源表）
# =============================================================================
def _mod(name: str, src_root):
    return import_game_data(name, src_root) if src_root else import_game_data(name)


def _json_safe(obj, where: str, path: str = "") -> None:
    """递归断言「JSON 可达」（叶类型原生、dict 键 str/int 非 tuple）。

    tuple 键落盘后不可逆；叶类型脏值会让编辑器渲染出 `"<object at 0x…>"` 而不报错。
    """
    p = path or "<root>"
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, bool) or not isinstance(k, (str, int)):
                raise ValueError(f"{where}：{p} 的键 {k!r} 不是 str/int（{type(k).__name__}）"
                                 f" —— JSON 不可逆，拒绝导出")
            _json_safe(v, where, f"{p}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _json_safe(v, where, f"{p}[{i}]")
    elif isinstance(obj, (str, int, float)) or obj is None:
        return
    else:
        raise ValueError(f"{where}：{p} 是 {type(obj).__name__} —— 不是 JSON 原生叶类型，拒绝导出")


def _group(domain: str, mod_name: str, rows: tuple, src_line: str, src_root) -> dict:
    """`{源模块名: {源常量名: 值原样}}` —— 一条 = 一个源模块的常量组（与 `game_config` 同型）。

    为什么外层还要包一层模块名（本来「一条 = 一张表」更直白）：宿主导出器的
    `export()` 有一条硬闸「**域表的外层值必须全是 dict**」（不是 dict 直接 raise）——
    而本文件的池子/序表/礼包表的值是 **list**（`QUALITY_ORDER`/`WISH_POOL`/`CHAPTER_PACK`/…），
    直接当外层行会被拒。包一层「模块 → 常量组」后：外层值恒为 dict、成员值**原样**（不包装、不改型），
    且与 `game_config`（`b9_l7_domains.py:30`「一条 = 一个源模块的常量组」）逐字同型。
    空值判定与 `game_config` 同款：dict/list/tuple/str 为空 → raise（空表 = 编辑器 0 条不报错）。
    """
    mod = _mod(mod_name, src_root)
    group: dict = {}
    for name in rows:
        if not hasattr(mod, name):
            raise ValueError(f"{domain}：{src_line} 的 {mod_name}.{name} 不存在 —— 源形状变了，拒绝导出")
        v = getattr(mod, name)
        if isinstance(v, (dict, list, tuple, str)) and not v:
            raise ValueError(f"{domain}：{mod_name}.{name} 是空值（{type(v).__name__}）—— 拒绝导出"
                             f"（空表 = 编辑器显示 0 条且不报错）")
        if isinstance(v, bool) or v is None:
            raise ValueError(f"{domain}：{mod_name}.{name} 是 {v!r} —— 不是表值，拒绝导出")
        _json_safe(v, f"{domain}.{mod_name}.{name}")
        group[name] = v
    return sort_table({mod_name: sort_table(group)})


# =============================================================================
# ① equipment —— 品质 / 装备槽 / 武器手感 / 品质序（game/data/equipment.py）
# =============================================================================
def derive_equipment(src_root: str = None) -> dict:
    """`equipment` 域：10 张常量表（**引用最多的缺口**：`QUALITY` 67 处 / `EQUIP_SLOTS` 38 处）。

        game/data/equipment.py:13  `QUALITY`       {品质档: {mult, color, name}}  —— 5 档
        game/data/equipment.py:3   `EQUIP_SLOTS`   {槽位 id: 中文名}               —— 7 槽
        game/data/equipment.py:127 `WEAPON_FLAVOR` {武器类型: {crit, desc}}        —— 8 型
        game/data/equipment.py:41  `QUALITY_ORDER` [品质档…]（**升序**，5 档）
        ── B14 收口追加 6 键（2026-09-14）：删宿主 `game/data` 的最后几处宿主兜底 ──
        `QUALITY_CN`(330) `WT_CN`(325) `WEAPON_TYPES`(49)  → `content/index.py` 的 `quality` /
          `weapon_types` 两张索引表（W1 实测：不补则删表后 `C.display('weapon_types','sword')`
          由「剑」退化成 `sword`）
        `WEAPON_DIST` / `ARMOR_FAMILY` / `ARMOR_FAMILY_ALIAS` → `content/stats.py:103-105`
          （P2F-2 v156 装备分系表下沉；是 `content/stats.py` 模块级取件，删表即 import 崩）

    ⚠ 消费口径（导出**不改**，只登记）：`QUALITY[档]["mult"]` 是装备价与强化的品质乘区、
    `["color"]` 是面板前缀字形；`QUALITY_ORDER` 是图鉴/统计的品质**迭代序**（顺序=行为）；
    `WEAPON_FLAVOR[型]["crit"]` 是武器暴击加成。键一律是内容侧词汇（字符串），无 int 键陷阱。
    """
    return _group("equipment", "equipment",
                  ("QUALITY", "EQUIP_SLOTS", "WEAPON_FLAVOR", "QUALITY_ORDER",
                   "QUALITY_CN", "WT_CN", "WEAPON_TYPES",
                   "WEAPON_DIST", "ARMOR_FAMILY", "ARMOR_FAMILY_ALIAS"),
                  "game/data/equipment.py", src_root)


# =============================================================================
# ② factions —— 阵营 / 序 / 地图归属 / 编年史 / 声望档（game/data/factions.py）
# =============================================================================
def derive_factions(src_root: str = None) -> dict:
    """`factions` 域：5 张表。

        :8   `FACTIONS`        {阵营 id: {name, icon, desc}}  —— 7 阵营
        :18  `FACTION_ORDER`   [阵营 id…]（面板枚举序 = **行为**：`world_cmds` 按它做编号映射）
        :123 `AREA_FACTION`    {区域 key: 阵营 id}             —— 85 个区域
        :165 `CHRONICLES`      [{title, text}]                 —— 12 篇
        :20  `REPUTATION_TIERS`[[下限, 档名]…]                 —— 5 档

    ⚠ `REPUTATION_TIERS` 源侧是 **tuple 的 list**，JSON 落成 array 的 array →
    消费端 `for _t, _n in C.REPUTATION_TIERS` 的**按序解包语义不变**（判等 tuple 的地方要自己转）。
    """
    return _group("factions", "factions",
                  ("FACTIONS", "FACTION_ORDER", "AREA_FACTION", "CHRONICLES", "REPUTATION_TIERS"),
                  "game/data/factions.py", src_root)


# =============================================================================
# ③ enchant —— 附魔配方 / 槽位数 / 暴击率（game/data/enchant.py）
# =============================================================================
def derive_enchant(src_root: str = None) -> dict:
    """`enchant` 域：3 个常量。

        :9   `ENCHANT_RECIPES`    {属性 key: {label, mats: [材料名…], ratio, cost}} —— 7 条
        :3   `ENCHANT_SLOTS`      {品质档: 槽位数}                                  —— 3 档
        :134 `ENCHANT_CRIT_CHANCE` 0.05（附魔「大师之作」概率；副业 10 级走 0.10，见消费点）

    ⚠ `ENCHANT_RECIPES[k]["mats"]` 是**材料名关键词**（不是物品 id），消费点是「名字包含匹配」，
    导出**不展开、不校验闭合**（展开＝在包里长出第二份物品表）。
    """
    return _group("enchant", "enchant",
                  ("ENCHANT_RECIPES", "ENCHANT_SLOTS", "ENCHANT_CRIT_CHANCE"),
                  "game/data/enchant.py", src_root)


# =============================================================================
# ④ poi_pools —— 交互点材料池（game/data/poi_pools.py）
# =============================================================================
def derive_poi_pools(src_root: str = None) -> dict:
    """`poi_pools` 域：3 个材料名池（`content/effects/poi_effects.py` 与 `content/combat_cmds.py` 消费）。

        :10 `WISH_POOL`          [材料名…] —— 6 个（许愿池）
        :15 `CAMPFIRE_FOOD_POOL` [材料名…] —— 4 个（篝火料理）
        :18 `HERB_POOL`          [材料名…] —— 5 个（草药丛，v101.4 数据化）

    池内是**中文材料名**（不是 id）：消费端按名查物品域 → 导出不翻译（翻译 = 第二份 id 空间）。
    """
    return _group("poi_pools", "poi_pools",
                  ("WISH_POOL", "CAMPFIRE_FOOD_POOL", "HERB_POOL"),
                  "game/data/poi_pools.py", src_root)


# =============================================================================
# ⑤ chapters —— 章节补给礼包（game/data/quest_add_v140.py）
# =============================================================================
def derive_chapters(src_root: str = None) -> dict:
    """`chapters` 域：1 张表（`CHAPTER_PACK`）。

        game/data/quest_add_v140.py:106 `CHAPTER_PACK` [{lv, name, items: [物品名…]}…] —— 10 条

    为什么单开域而不并进 `quests`：`quests` 域的 primary def 是「一条 = 一个任务」
    （`required=[source,name,desc,objective,reward_exp,reward_gold]`），而本表是
    「一条 = 一个等级的补给包」（`lv/name/items`），**形状不同** ⇒ 并进去只能硬造任务字段或放水
    required（B14-3_BRIEF §2.4 禁）。消费点 `content/gameplay.py`（升级结算发章节礼包）。
    """
    return _group("chapters", "quest_add_v140", ("CHAPTER_PACK",),
                  "game/data/quest_add_v140.py:106", src_root)


# =============================================================================
# ⑥ gems —— 宝石阶位 / 名称 / 孔位 / 打孔 / 传说特效 / 符文拆卸价（game/data/gems.py）
# =============================================================================
def derive_gems(src_root: str = None) -> dict:
    """`gems` 域：6 个常量（BRIEF §1(a) 的 6 名里 5 个是宝石，`RUNE_REMOVE_COST` 按源文件同族归此）。

        :7  `GEM_TIERS`            {阶位(1..10): {name, mult}}      —— 10 阶
        :19 `GEM_TIER_NAMES`       {阶位(1..10): 全名}              —— 10 条
        :25 `GEM_SOCKETS`          {品质档: {count, tier, min_tier, max_tier}} —— 5 档
        :33 `GEM_DRILL`            {品质档: {cost, craft_lv}}       —— 3 档
        :42 `GEM_LEGENDARY_EFFECTS` [传说特效名…]                   —— 4 条
        :40 `RUNE_REMOVE_COST`     1000（符文拆卸单价；与 `GEM_REMOVE_COST` 同在源文件）

    ⚠⚠ **int 键陷阱（本域最重要的坑）**：`GEM_TIERS` / `GEM_TIER_NAMES` 的键源侧是 **int 1..10**，
    JSON 只有字符串键 → 包内读口**必须还原 int**，否则：`C.GEM_TIERS.get(tier)`（tier 是 int）
    恒 miss = 宝石详情数值静默归零；`sorted(C.GEM_TIERS)` 变成 `"1","10","2"…` = 阶位显示乱序；
    `GEM_TIER_NAMES.get(tier + 1)` = 合成链断（永远显示「已是最高阶」）。
    还原责任在**包内读口**（`content/catalog_items.py`，与 `content/config.py:int_keys()` 同款），
    导出侧只按源形状搬运（`lvl` 这类 int 键的先例见 `runes.schema.json` 的同一登记）。
    """
    return _group("gems", "gems",
                  ("GEM_TIERS", "GEM_TIER_NAMES", "GEM_SOCKETS", "GEM_DRILL",
                   "GEM_LEGENDARY_EFFECTS", "RUNE_REMOVE_COST"),
                  "game/data/gems.py", src_root)


DOMAINS = {
    "equipment": derive_equipment,
    "factions": derive_factions,
    "enchant": derive_enchant,
    "poi_pools": derive_poi_pools,
    "chapters": derive_chapters,
    "gems": derive_gems,
}
