# -*- coding: utf-8 -*-
"""怪物·战斗数据线（B7）域插件 —— `monster_mods` / `item_templates` / `potion_effects` /
`wild_king` / `stats`。

契约见同目录 `README.md`：暴露 `DOMAINS = {域: derive_<域>}`，宿主
`scripts/export_game_package.py` 运行期并进 `DERIVERS`（**不改那 2,900 行宿主文件**）。
派生函数**只读真源**、只返回内存表；落盘（UTF-8/LF/indent=2/原子替换）与
排序（外层键字典序）都由宿主做 → 本文件对同一真源两次派生逐字节相同。

⚠️ 导入顺序铁律（两处踩过）：`game.core.*` 单独先 import 会炸
`ImportError: cannot import name 'build_index' from partially initialized module 'game.core.index'`
——`game/core/__init__.py:45` → `core/index.py:5` → `game.data._INDEXES`，
而 `game/data/__init__.py:242` 又 `from . import _assembly`、`_assembly.py:9` 反手 import
`..core.index`。所以**每个 core 派生函数先 `import_game_data(...)` 整包加载 `game.data`**，
再 import `game.core.<mod>`（见 `_core_module()`）。

================================================================================
各域证据（2026-09-13 本机实测；行号 = 当时的真源文件）
================================================================================

monster_mods —— `game/data/monster_mods.py:15 MONSTER_MODS`（1824 行文件里**唯一**的模块级表）
    140 条（键 = 怪物 id；实测前缀 `m_*` 29 / `e_*` 81 / `b_*` 30），条目**原样**进 JSON。
    字段出现次数（140 条上的直方图）：desc 140（**每条都有**）、hp_mult 97、atk_mult 93、
    spd_mult 37、matk_mult 37、mech 31、phases 27、ai 21、on_interrupt 19、opening 17、
    def_mult 13、element_weak 9、triggers 8、on_minion_died 7、chains 5、immune_dots 5、
    dodge 3、block 3、target_policy 3、dmg_taken_mult 2、phys_reduce 1、on_taken 1。
    全部条目 dict、全部 JSON 原生叶类型（0 tuple / 0 非 str 键）。
    消费端（导出只搬运，不改语义）：
        `game/core/drops.py:400`      `mod = C.MONSTER_MODS.get(mid, {})` → 六维乘区（:402-405）、
                                      rank/reach 覆盖（:420-421）、mech/desc/ai/on_taken/
                                      element_immune/element_weak/immune_dots/dmg_taken_mult/
                                      class_name/equipment/…（:447-481，整条白名单透传）
        `game/commands/boss_script.py:28`  Boss 剧本基准（副本侧由 instances 覆盖）
        `game/commands/instance_battle.py:134`  `target_policy`（仇恨选敌）
        `game/commands/combat.py:503`     图鉴展示 `desc`
    引用闭合（本批只列，不展开）：条目的 `skills`/`phases[].add_skills`/`chains[].seq` 里
    90 个技能 id **90/90 落 monsters 域**（`ms_*` 怪物技能表）；140 个条目键 **140/140 落
    monster_roster 域**（怪物名册）—— 两处零悬空（见报告 §4）。

item_templates —— `game/core/item_templates.py:28 META`（`@register(...)` 装饰器 :37-43 与
    :446 / :606 两处直写共同填充；真源是**道具模板注册表**：`TEMPLATES` = 函数、`META` = 元数据）
    99 条（键 = 模板名，如 `heal` / `battle_start_resource` / `bait_glow`），条目**原样** =
    `{"battle_ok": bool}`（实测 64 true / 35 false）。导入期断言 `set(TEMPLATES) == set(META)`
    （同一装饰器两处写、`:600-607` 鱼饵循环同样两处写）—— 不等即源侧注册路径变了，拒绝导出。
    消费端（真源读取点只有一处）：`game/commands/economy.py:5823`
    `meta = IT.META.get(tpl_name, {"battle_ok": False})` → :5863 副本战斗内、:5912 普通战斗内
    两道 `if not meta["battle_ok"]`（战斗内可用性闸门）。
    ⚠️ 本域**只搬 META**（模板可用性元数据）。真源里另有 `_BAIT_INFO`（:578，3 条
    `{物品 effect 名 → [名, tip]}`）、`_BUFF_KEYS`（:356，56 条 special 别名）、
    `_V130_ITEM_EFFECTS`（:413，23 个效果名）、`_PURIFY_DEBUFF_KEYS`（:752，8 个状态名）
    四张词表 —— 都是**效果名/状态名词汇**，指向 effects / items 域，本批未展开（报告 §4）。

potion_effects —— `game/core/potion_effects.py:51 DEFAULTS`（= `:36-49 _scan_defaults()`
    扫 `game/data/items.py` 的 `effect_data` 构建；`_EFFECT_KIND` :29-33 把 3 个物品
    effect 名折到注册键）。本批**只导数据表**（`DEFAULTS` 原样），不导逻辑：
    55 条（键 = 效果名），条目 = `effect_data` 原样（如 `{"pct": 0.5}`）。
    注册表 `POTION_EFFECTS`（36 个 handler，`:16` + 末尾 `vuln`）是**逻辑**，已由
    `games/orlandia/content/effects/potion_effects.py` 逐字端口（该包内文件 :103-123 自己
    从 `content/data/items.json` 重算同一张 DEFAULTS —— 包内单源，不 import 宿主）→
    本域 JSON 是这张表的**编辑器侧视图**（口径 = 扫描 + 别名折叠，见报告 §4）。
    实测：36 个 handler 全部在 DEFAULTS 里（0 缺）；DEFAULTS 另有 19 个键**无 handler**
    （`anchor`/`mail`/`reforge`/… —— 非战斗道具，走 item_templates 路径），原样保留不筛。
    引用闭合（报告 §4）：4 条（`restore_resource`/`resource_amp`/`restore_resource_full`/
    `battle_start_resource`）的 `key` = `"rage"` **落 effect_rules 域**（85 条里命中）；
    `summon.tid = "ember_wisp"` 的召唤模板表、`apply_mark.mark = "fire"` 的元素词汇
    都**尚未进包** = 空引用。

wild_king —— `game/data/wild_king_data.py:62 WILD_KINGS`（注意：父任务行号的
    `game/core/wild_king.py`（622 行）是**纯逻辑**（21 个函数：时段哈希/刷新/开箱），
    数据表在 data 侧这份 215 行文件里。）
    8 条（键 = 野王 id，`b_guard_*`），条目**原样**（name/icon/map/lv/hp_base/atk_mult/
    skills/drops/chest_tier/desc 十字段，实测字段并集 = 这 10 个）。
    消费端：`game/core/wild_king.py:124 _build_king`（构造野王怪物）、:224（按图选池）、
    :258/:476（击杀结算 + 宝箱奖励）。
    引用闭合：`map` 8/8 落 maps 域；`chest_tier` 8/8 落本文件的 `WILD_KING_CHEST_TIERS`
    （3 档 low/mid/high，未进包）；`skills` 12 个里 10 个落 monsters 域、2 个悬空
    （`ms_an_ying_zhua` / `ms_han_bing_zhu_fu`）；`drops` 15 个字面量是**物品中文名**
    （非 id）→ 按 `items` 域 `name` 反查 **15/15 命中**（按名引用，见报告 §4）。
    未进包的域级配置（无对应域声明）：`WILD_KING_MAPS`（:130 = 8 图）、`WILD_KING_PERIODS`
    （:26 = 4 时段）、`WILD_KING_CHEST_TIERS`（:145 = 3 档）、9 个数值常量（:34-47 全服上限 3 /
    存活 5400s / 专属 900s / 每时段 1 / 每日 2 / 保底 3 时段 / 加刷 2 只 / 刷新点 02,08,14,20）。

stats —— `game/core/stats.py:218 _EXP_TABLE`（v169.1 成长模型：5 级锚点指数插值全表写死，
    `:242 exp_to_next` 查表 O(1)）。
    100 条（键 = 等级 1..100），条目 = `{"level": <源表键>, "exp_to_next": <源表值原样>}`。
    条目里的 `level` 与键 `lv_<n>` **都是导出器注入的键口径**（源表键是 int —— JSON 对象键
    必须 str，且包内 `propertyNames` 是 `^[a-z][a-z0-9_]*$`，故用 `lv_` 前缀）；
    `exp_to_next` 是源表值**一个字未改**。
    消费端：`game/content_rules/gameplay.py:83-84`（升级循环）、`game/commands/player.py:572`、
    `game/commands/combat.py:739`（经验条）。
    ⚠️ stats.py 其余全是公式（`hp_stage_mult`/`monster_stats`/`equip_stats`/`monster_exp`…），
    其数值表**不在本文件**：`game/data/stat_templates.py`（HP/ATK/BOSS 段乘区）、
    `game/data/formula_skeleton.py`（公式骨架）、`game/data/equipment.py`（分系表）、
    `game/data/base_growth.py` —— 那几份是「战斗数值表」的真正大头，**本批未导**（报告 §5）；
    `_EQUIP_VALUE_WEIGHT`（:203，`{"hp":0.1,"mp":0.1}`）是 2 条定价权重，形状与等级行不同，
    未混进本表（报告 §5）。
"""
from _helpers import import_game_data, import_game_core, sort_table, as_table

# core 模块的整包预热锚点：任何 `game.data.*` 导入都会执行 `game/data/__init__.py`
# （含 `_assembly`）→ 之后 `import game.core.<mod>` 不再踩 core/index ↔ data 的循环导入。
_CORE_PRIME_MOD = "monster_mods"


def _core_module(mod_name: str, src_root: str = None):
    """import 游戏仓 `game/core/<mod>.py`（先整包加载 `game.data`，见文件头铁律）。"""
    import_game_data(_CORE_PRIME_MOD, src_root)
    return import_game_core(mod_name, src_root)


def _table_of(mod, attr: str, where: str, src_root: str = None) -> dict:
    """取真源表并拒绝空表 —— 静默空表在编辑器侧 = 「0 条」且不报错（本项目最怕的故障）。"""
    tbl = as_table(getattr(mod, attr, None), where)
    if not tbl:
        raise ValueError(f"{where} 是空表 —— 源形状变了/表被删，拒绝导出")
    return tbl


# =============================================================================
# monster_mods
# =============================================================================
def derive_monster_mods(src_root: str = None) -> dict:
    """怪物个体改造表 → `{怪物 id: 修正条目}`（140 条，条目原样，不注入任何字段）。

    真源 `game/data/monster_mods.py:15 MONSTER_MODS`（import 后的运行时表 = 唯一表，
    文件里无 `MONSTER_MODS.update(...)` 之类的二次写入路径 —— 与 items 域那种「读字面量会
    拿到未覆盖旧值」的坑不同）。
    映射口径：键 = 怪物 id 原样（不再拆 `m_/e_/b_` 三张表 —— 源侧本来就是一张表）；
    条目字段原样（含 `desc` 140/140 必有、`phases`/`ai`/`on_interrupt`/`element_weak` 等
    嵌套形状），**不补默认值、不展开技能 id、不改字段顺序**。
    实测：140 条全 dict、0 非 JSON 原生叶类型；条目键 140/140 落 monster_roster 域、
    引用技能 90/90 落 monsters 域（报告 §4）。
    """
    mod = import_game_data("monster_mods", src_root)
    table = _table_of(mod, "MONSTER_MODS", "game/data/monster_mods.py:15 MONSTER_MODS", src_root)
    for mid, ent in table.items():
        if not isinstance(ent, dict):
            raise ValueError(
                f"monster_mods：{mid!r} 不是 dict（{type(ent).__name__}）—— 源形状变了，拒绝导出"
            )
        if not ent:
            raise ValueError(f"monster_mods：{mid!r} 是空条目 —— 空修正表会让该怪退回公式值，拒绝导出")
    return sort_table(table)


# =============================================================================
# item_templates
# =============================================================================
def derive_item_templates(src_root: str = None) -> dict:
    """道具模板注册表的**元数据表** → `{模板名: {"battle_ok": bool}}`（99 条，条目原样）。

    真源 `game/core/item_templates.py:28 META`：`register(name, battle_ok)` 装饰器（:37-43）
    与 :446（`special` 族批量）/ :606（鱼饵循环）两处直写共同填充。
    映射口径：键 = 模板名（= 真源 `TEMPLATES` 的键 = `items.py` 条目 `effect` 字段的取值）；
    条目**原样**（实测只有一个字段 `battle_ok`，64 true / 35 false），不注入、不补默认值。
    导入期一致性断言：`set(TEMPLATES) == set(META)`（不等 = 注册路径改了 → 拒绝导出）；
    另断言每条都带 `battle_ok`（消费端 `economy.py:5823/5863/5912` 直接取该键做战斗内闸门）。
    ⚠️ 只搬 META：真源的四张词表 `_BAIT_INFO`/`_BUFF_KEYS`/`_V130_ITEM_EFFECTS`/
    `_PURIFY_DEBUFF_KEYS` 是效果名/状态名词汇（指向 effects/items 域），未展开（报告 §4）。
    """
    mod = _core_module("item_templates", src_root)
    meta = _table_of(mod, "META", "game/core/item_templates.py:28 META", src_root)
    tpls = as_table(getattr(mod, "TEMPLATES", None), "game/core/item_templates.py:27 TEMPLATES")
    if not tpls:
        raise ValueError("item_templates：game/core/item_templates.py:27 TEMPLATES 是空表 —— 拒绝导出")
    if set(tpls) != set(meta):
        only_t = sorted(set(tpls) - set(meta))
        only_m = sorted(set(meta) - set(tpls))
        raise ValueError(
            f"item_templates：TEMPLATES 与 META 键不一致（只在 TEMPLATES：{only_t[:5]}；"
            f"只在 META：{only_m[:5]}）—— 注册路径（:41 / :446 / :606）改了，拒绝导出"
        )
    for name, ent in meta.items():
        if not isinstance(ent, dict) or "battle_ok" not in ent:
            raise ValueError(
                f"item_templates：{name!r} 的 META 不是带 battle_ok 的 dict（{ent!r}）—— "
                f"消费端 economy.py:5823 靠它判战斗内可用，源形状变了，拒绝导出"
            )
    return sort_table(meta)


# =============================================================================
# potion_effects
# =============================================================================
def derive_potion_effects(src_root: str = None) -> dict:
    """药水效果**默认数值表** → `{效果名: effect_data}`（55 条，条目原样）。

    真源 `game/core/potion_effects.py:51 DEFAULTS`（= `:36-49 _scan_defaults()` 扫
    `game/data/items.py` 的 `effect_data` 构建，`:29-33 _EFFECT_KIND` 把 3 个物品 effect 名
    （`armor_break_pot`/`rock_shield`/`holy_shield`）折到注册键
    （`def_down`/`shield_small`/`shield_big`）。items.py 是数值的单一权威 → 本表是它的**派生视图**。
    映射口径：键 = 效果名；条目 = `effect_data` **原样**（如 `{"pct": 0.5}` / `{"key": "rage",
    "amount": 3}`），不补默认值、不筛条目。
    **只导数据表**：注册表 `POTION_EFFECTS`（36 个 handler）是逻辑，已由
    `games/orlandia/content/effects/potion_effects.py` 逐字端口（该文件 :103-123 自己从
    `content/data/items.json` 重算同一张表）→ 本 JSON 给编辑器看的是「同一口径的静态视图」。
    实测：36 handler **全部**在 DEFAULTS 里；DEFAULTS 多出 19 个无 handler 的键
    （`anchor`/`bag_expand`/`mail`/`reforge`/… 非战斗道具）**原样保留** —— 删它们 = 导出器
    替真源决定「哪些效果值得看」，那是另一件事。
    引用闭合：`key="rage"` 落 effect_rules 域（85 条里命中）；`summon.tid`（召唤模板表）、
    `apply_mark.mark="fire"`（元素词汇）**未进包** = 空引用（报告 §4）。
    """
    mod = _core_module("potion_effects", src_root)
    defaults = _table_of(mod, "DEFAULTS", "game/core/potion_effects.py:51 DEFAULTS", src_root)
    for kind, ent in defaults.items():
        if not isinstance(ent, dict):
            raise ValueError(
                f"potion_effects：{kind!r} 不是 dict（{type(ent).__name__}）—— 源形状变了，拒绝导出"
            )
    return sort_table(defaults)


# =============================================================================
# wild_king
# =============================================================================
def derive_wild_king(src_root: str = None) -> dict:
    """野王数据表 → `{野王 id: 王定义}`（8 条，条目原样，不注入字段）。

    真源 `game/data/wild_king_data.py:62 WILD_KINGS`（父任务给的 `game/core/wild_king.py`
    是纯逻辑：时段哈希 `_day_hash` / 刷新 `wild_king_tick` / 击杀 `wild_king_on_kill` /
    开箱 `open_chest` 共 21 个函数，模块级只有两个 event_state 键名常量）。
    映射口径：键 = 野王 id（`b_guard_*`）；条目十字段原样（name/icon/map/lv/hp_base/atk_mult/
    skills/drops/chest_tier/desc），不改类型、不补默认值。
    实测：8 条全 dict；`map` 8/8 落 maps 域；`chest_tier` 8/8 落 `WILD_KING_CHEST_TIERS`；
    `skills` 12 个里 10 落 monsters 域、2 悬空；`drops` 15 个字面量是**物品中文名**（非 id），
    按 items 域 `name` 反查 15/15 命中。
    未进包（无对应域声明）：`WILD_KING_MAPS`（8 图）/`WILD_KING_PERIODS`（4 时段）/
    `WILD_KING_CHEST_TIERS`（3 档）/9 个数值常量 —— 见报告 §4。
    """
    mod = import_game_data("wild_king_data", src_root)
    table = _table_of(mod, "WILD_KINGS", "game/data/wild_king_data.py:62 WILD_KINGS", src_root)
    for kid, ent in table.items():
        if not isinstance(ent, dict) or "name" not in ent:
            raise ValueError(
                f"wild_king：{kid!r} 不是带 name 的 dict（{ent!r}）—— 源形状变了，拒绝导出"
            )
    return sort_table(table)


# =============================================================================
# stats
# =============================================================================
def derive_stats(src_root: str = None) -> dict:
    """升级经验表 → `{lv_<等级>: {"level": <等级>, "exp_to_next": <经验>}}`（100 条）。

    真源 `game/core/stats.py:218 _EXP_TABLE`（v169.1：5 级锚点指数插值全表写死，
    `:242 exp_to_next` 查表 O(1)，超出 100 级才走 `FORMULA_SKELETON["exp_fallback"]` 兜底）。
    注入的键口径（**源里没有这两层，是导出器加的**，逐字记录在此）：
        `lv_<n>`  —— JSON 对象键必须 str（源表键是 int），且包内 `propertyNames` 是
                     `^[a-z][a-z0-9_]*$` → 用 `lv_` 前缀，n = 源表键原样
        `level`   —— 源表键（int）复制进条目，供编辑器列显示与排序
        `exp_to_next` —— 源表值**原样**（int），一个字未改
    实测：100 条（1..100 连续、无缺口），值全 int（无 bool/float 混入），
    取值区间 2600（Lv.1）… 1607650（Lv.100）。
    ⚠️ 本域只含这一张 stats.py 自有的**数据表**；stats.py 其余是公式，其数值表在
    `game/data/stat_templates.py` / `formula_skeleton.py` / `equipment.py` / `base_growth.py`
    （未导，报告 §5）；`_EQUIP_VALUE_WEIGHT`（:203，2 条定价权重）形状不同，未混进本表。
    """
    mod = _core_module("stats", src_root)
    exp = _table_of(mod, "_EXP_TABLE", "game/core/stats.py:218 _EXP_TABLE", src_root)
    out: dict = {}
    for lv, need in exp.items():
        if isinstance(lv, bool) or not isinstance(lv, int):
            raise ValueError(f"stats：等级键 {lv!r} 不是 int —— 源形状变了，拒绝导出")
        if isinstance(need, bool) or not isinstance(need, int):
            raise ValueError(
                f"stats：Lv.{lv} 的经验值 {need!r} 不是 int —— 源形状变了，拒绝导出"
            )
        out[f"lv_{lv}"] = {"level": lv, "exp_to_next": need}
    if len(out) != len(exp):
        raise ValueError("stats：等级键去重后条目数变了（`lv_` 前缀冲突）—— 拒绝导出")
    # 外层键字典序（与宿主 `sort_table` 同一口径；`lv_1` / `lv_10` / `lv_100` … 逐字面序）
    return sort_table(out)


DOMAINS = {
    "monster_mods": derive_monster_mods,
    "item_templates": derive_item_templates,
    "potion_effects": derive_potion_effects,
    "wild_king": derive_wild_king,
    "stats": derive_stats,
}
