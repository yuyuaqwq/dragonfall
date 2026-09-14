# -*- coding: utf-8 -*-
"""B9-L7「域补口」线域插件 —— `trial_floors`（修炼塔塔表）+ `game_config`（配置/常量归口）。

契约见同目录 `README.md`：本文件只**读真源、返回内存表**，落盘（UTF-8 / LF / indent=2 / 原子替换）
与排序（外层键字典序）由宿主 `scripts/export_game_package.py` 统一做；**不许 import
`export_game_package`**（宿主会扫本目录 → 循环导入），公用小工具走 `_helpers.py`。
派生函数必须定义在 `DOMAINS = {` **之前**。

================================================================================
域 1：`trial_floors` —— 修炼塔 30 层（键 = floor，int → JSON 字符串键）
================================================================================
真源：`game/data/trial_tower.py:112 TRIAL_FLOORS`（**生成式**：`:113` 的 for + `:122` 的 append
在 import 期把 `_FLOOR_NAMES/_GUARD_NAMES/_EXP/_GOLD/_floor_lv/_hp_mult/_atk_mult` 拼成成品表）。
导出的是**成品表**（import 之后的运行时值），不是那些生成器函数/私有中间表（见域 2 的判定）。

* 键 = `str(floor)`（`^[0-9]+$`，与包内 `enhance_table` 同一口径 —— JSON 只有字符串键）；
  条目**原样** 11 字段：`floor/name/guard/lv/role/skills/hp_mult/atk_mult/reward_exp/reward_gold/desc`。
  消费端（`content/config.py:trial_floors()`）把键还原成 int 并**按 floor 排回源顺序**
  （源表是 list，域是 dict；JSON 外层键是字典序 → 不还原顺序 = 玩家看到的层序漂移）。
* 条目里的 `floor` 字段（源侧本就有的 int）是**权威**：导出期断言 `键后缀 == 条目["floor"]`。
* 三条常量（`TRIAL_DAILY_LIMIT=3` / `TRIAL_MIN_LV=70` / `TRIAL_MAX_FLOOR=30`）**不是条目形状**
  → 归口到域 2 `game_config` 的 `trial_tower` 组（与 `weekly_quests` 的 WEEKLY_PICK 同款处理）。
* 空表 / 层号断号 / 重号 → `raise`（编辑器 0 条不报错 = 本项目最怕的静默失效）。
* ⚠️ 未导入（源里存在但**不是数据**，见报告判定表）：`_floor_lv` / `_hp_mult` / `_atk_mult`
  三个生成函数与 `_EXP` / `_GOLD` / `_ROLES` / `_FLOOR_NAMES` / `_FLOOR_DESC` / `_GUARD_NAMES`
  六张私有中间表 —— 它们是「**怎么生成**这张表」的代码，不是玩家可见数据；成品已进本域，
  重复导它们 = 同一语义两份（BRIEF §6 禁）。

================================================================================
域 2：`game_config` —— 配置/常量归口（一条 = 一个源模块的常量组）
================================================================================
`game/data/` 下 20 个「配置/常量」模块逐个判定（判定表见 overnight/B9-L7-domains.md §2）。
**能进本域的判据**（BRIEF：换游戏要不要重写 + 是不是纯数据）：
  ① 纯数据（零函数体 / 零 IO / 零 import 期依赖外部状态）；
  ② 换一个游戏必须重写（经济价、签到、强化阶梯、房产、采集点、流派表…）；
  ③ JSON 可达（叶类型 str/int/float/bool/None；dict 键 str 或 int；list/tuple → JSON array）。
**不进的判据**：函数（公式骨架的执行器）/ 派生索引 / 私有中间表 / 已属别域的同一张表。

条目模型：**外层键 = 真源模块名**（`^[a-z][a-z0-9_]*$`），条目 = `{源常量名: 值原样}`。
键**一律用源侧常量名原文**（UPPER_SNAKE）—— 改名 = 语义漂移，消费端按同名取
（包内 `content/config.py`）。值**一字不改**：不补默认值、不改类型、不展开引用串。

「每个模块级常量都有家」硬闸（本域的核心价值：不给常量留野地）
--------------------------------------------------------------------------------
显式组：模块的**全部**公开模块级常量 = `members` ∪ `owned_elsewhere`，多一个就 `raise`
（`game/data` 里新增常量却没归口 → 导出报红，而不是悄悄漏出包）。`owned_elsewhere` 是
「这张表已在别的域 / 是派生索引 / 真源删不掉但无消费」的白名单，每项**带理由**。
自动组（battle_config / battle_rules，表多且是纯字面量字典）：模块**不许有模块级
import / for / if**（AST 断言，防「导入进来的名字被当成表」），成员 = 全部公开非 callable
常量 − `exclude`（带理由），并断言条数下界。

已被别的域占用的表（**不在本域重复**，防双源）
- `battle_config.TIER_GROWTH` / `BRANCH_BONUS` / `BRANCH_BONUS_BY_CLASS` → `panel_rules` 域
- `base_growth.PLAYER_BASE_GROWTH`（整模块）→ `panel_rules` 域（`base_growth` 段）
- `enhance.ENHANCE_TABLE` → `enhance_table` 域
- `battle_rules.EFFECT_RULES` → `effect_rules` 域；`battle_rules.PASSIVE_PROC` → `passive_proc` 域
- `weekly_quests.WEEKLY_QUESTS` → `weekly_quests` 域；`trial_tower.TRIAL_FLOORS` → `trial_floors` 域

本轮明确不导（写进报告「未做与缺口」，不是漏）
- `battle_config` 里 **4 张 tuple 键表**：`BRANCH_RESOURCE_OVERRIDE`（键 = `(职业 id, 档位)`）、
  `ELEMENT_REACTIONS` / `REACTION_TABLE`（键 = `(元素, 印记)`）、`MECH_CFG`（内层
  `element.reactions` 同型）—— JSON 键只能是字符串，落成 `"('ice', 'fire_mark')"` 后还原要
  `ast.literal_eval`；「tuple 键怎么编码 + 消费端怎么还原」是**一条口径决定**（如 `ice+fire_mark`
  + 包内 split 还原），本轮不擅自发明（见报告「未做与缺口」）。
- `mounts.MOUNT_BY_KEY`：`{m["key"]: m for m in MOUNT_POOL}` 的**派生索引**（可由 MOUNT_POOL 重建）。
- `battle_config.mech_cfg()` / `battle_rules._dot_period()` / `prof_config.price_band()` /
  `prof_config.gather_map_min_lv()`：函数（逻辑，留宿主模块）。
"""
from _helpers import import_game_data, sort_table

# =============================================================================
# 域 1：trial_floors
# =============================================================================
FLOORS_SRC = "game/data/trial_tower.py:112 TRIAL_FLOORS"
FLOOR_FIELDS = ("floor", "name", "guard", "lv", "role", "skills", "hp_mult", "atk_mult",
                "reward_exp", "reward_gold", "desc")
FLOOR_ROLES = ("dps", "caster", "speedster", "tank", "healer")


def _mod_key(path_or_name: str) -> str:
    """`game/data/weekly_quests.py` / `weekly_quests` → `weekly_quests`（import 用的模块名）。"""
    name = str(path_or_name).replace("\\", "/").rsplit("/", 1)[-1]
    return name[:-3] if name.endswith(".py") else name


def _mod(mod_name: str, src_root: str = None):
    """import `game/data/<mod>.py`（`src_root=None` 时用 `_helpers.REPO_ROOT` 默认 —— 不能把
    `None` 传进 `sys.path.insert`，那样会 TypeError）。"""
    name = _mod_key(mod_name)
    return import_game_data(name, src_root) if src_root else import_game_data(name)


def _json_safe(obj, where: str, path: str = "") -> None:
    """递归断言「JSON 可达」：叶类型原生、dict 键 str/int（**非 tuple**）。

    为什么在这里炸：tuple 键落盘后不可逆（`content/config.py` 无法可靠还原），
    叶类型脏值会让编辑器渲染出 `"<object at 0x…>"` 而不报错。
    """
    p = f"{path}" or "<root>"
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


def derive_trial_floors(src_root: str = None) -> dict:
    """`trial_floors` 域：`TRIAL_FLOORS`（30 条）→ `{str(floor): 条目原样}`。

    与 `enhance_table` 同款：int 键显式 `str()`，消费端（`content/config.py`）还原 int。
    """
    mod = _mod("trial_tower", src_root)
    floors = getattr(mod, "TRIAL_FLOORS", None)
    if not isinstance(floors, list):
        raise TypeError(f"trial_floors：{FLOORS_SRC} 应为 list（得到 {type(floors).__name__}）"
                        f" —— 源形状变了")
    if not floors:
        raise ValueError(f"trial_floors：{FLOORS_SRC} 是空表 —— 拒绝导出"
                         f"（空表 = 编辑器显示 0 条且不报错）")

    out: dict = {}
    for i, ent in enumerate(floors, 1):
        if not isinstance(ent, dict):
            raise ValueError(f"trial_floors：{FLOORS_SRC}[{i - 1}] 不是 dict"
                             f"（{type(ent).__name__}）—— 拒绝导出")
        miss = [f for f in FLOOR_FIELDS if f not in ent]
        if miss:
            raise ValueError(f"trial_floors：{FLOORS_SRC}[{i - 1}] 缺字段 {miss} —— 拒绝导出")
        floor = ent.get("floor")
        if isinstance(floor, bool) or not isinstance(floor, int):
            raise ValueError(f"trial_floors：{FLOORS_SRC}[{i - 1}].floor 不是 int（{floor!r}）")
        if floor != i:
            raise ValueError(f"trial_floors：源表第 {i} 条的 floor={floor} —— 表序与层号不一致"
                             f"（键 = floor，错位会静默改层序），拒绝导出")
        if floor in out:
            raise ValueError(f"trial_floors：层号重复 {floor}（键 = floor，重号会吞一条）")
        for f in ("name", "guard", "desc"):
            v = ent.get(f)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"trial_floors：第 {floor} 层的 {f} 不是非空字符串（{v!r}）")
        role = ent.get("role")
        if role not in FLOOR_ROLES:
            raise ValueError(f"trial_floors：第 {floor} 层的 role={role!r} 不在 {list(FLOOR_ROLES)}"
                             f"（塔卫走 monster_stats 角色模板，未知 role = 数值兜底）")
        lv = ent.get("lv")
        if isinstance(lv, bool) or not isinstance(lv, int) or not (1 <= lv <= 200):
            raise ValueError(f"trial_floors：第 {floor} 层的 lv={lv!r} 不是 1..200 的 int")
        skills = ent.get("skills")
        if not isinstance(skills, list) or not skills or not all(isinstance(s, str) and s for s in skills):
            raise ValueError(f"trial_floors：第 {floor} 层的 skills 不是非空字符串列表（{skills!r}）")
        for f in ("hp_mult", "atk_mult"):
            v = ent.get(f)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                raise ValueError(f"trial_floors：第 {floor} 层的 {f}={v!r} 不是正数")
        for f in ("reward_exp", "reward_gold"):
            v = ent.get(f)
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise ValueError(f"trial_floors：第 {floor} 层的 {f}={v!r} 不是正 int")
        out[str(floor)] = dict(ent)                      # 字段顺序原样

    # 自证：键必须恰好是 1..N 连续整数（防上面循环被改动后静默错位/断号）
    keys = sorted(int(k) for k in out)
    if keys != list(range(1, len(out) + 1)):
        raise ValueError(f"trial_floors：层号不是 1..{len(out)} 连续整数（{keys}）—— 拒绝导出")
    return sort_table(out)


# =============================================================================
# 域 2：game_config
# =============================================================================
# 显式组：模块 → (真源模块名, 成员常量元组, {别的归属/排除: 理由})
# 「全部公开模块级常量 = 成员 ∪ owned_elsewhere」，多一个就 raise（见文件头「硬闸」）。
EXPLICIT_GROUPS = (
    ("weekly_quests", "game/data/weekly_quests.py", ("WEEKLY_PICK", "WEEKLY_MIN_LV"),
     {"WEEKLY_QUESTS": "weekly_quests 域（周常悬赏池表，不是常量）"}),
    ("trial_tower", "game/data/trial_tower.py",
     ("TRIAL_DAILY_LIMIT", "TRIAL_MIN_LV", "TRIAL_MAX_FLOOR"),
     {"TRIAL_FLOORS": "trial_floors 域（30 层塔表，不是常量）"}),
    ("econ_config", "game/data/econ_config.py", ("ECON_CONFIG",), {}),
    ("signin_config", "game/data/signin_config.py", ("SIGNIN_CONFIG",), {}),
    ("enhance", "game/data/enhance.py",
     ("MAX_ENHANCE", "ENHANCE_FAIL_DROP", "ENHANCE_SMITH_MAPS"),
     {"ENHANCE_TABLE": "enhance_table 域（强化阶梯表，面板与引擎共读）"}),
    ("upgrade", "game/data/upgrade.py",
     ("UPGRADE_TABLE", "MAX_UPGRADE", "UPGRADE_STONE", "UPGRADE_STAMINA", "UPGRADE_MATERIAL_CN"),
     {}),
    ("calamity", "game/data/calamity.py",
     ("CALAMITY_MAX", "CALAMITY_COST", "CALAMITY_STATS", "CALAMITY_BONUS", "CALAMITY_MALUS",
      "CALAMITY_POSITIVE_CHANCE"), {}),
    ("refine", "game/data/refine.py", ("REFINE_RECIPES",), {}),
    ("housing", "game/data/housing.py",
     ("PROPERTIES", "HOUSE_LEVELS", "HOUSE_MAX_LEVEL", "HOUSE_REFUND"), {}),
    ("gather", "game/data/gather.py", ("CAMP_SPOTS", "MINE_SPOTS"), {}),
    ("gather_pools", "game/data/gather_pools.py",
     ("GATHER_MAP_POOLS", "GATHER_COND_POOLS", "MINING_DEEP_POOLS"), {}),
    ("item_tag_display", "game/data/item_tag_display.py", ("ITEM_TAG_DISPLAY",), {}),
    ("prof_config", "game/data/prof_config.py",
     ("PROF_TUTORS", "PROF_WAIT_BASE", "DAILY_PROF_TASKS", "BAG_FILTER_TYPES", "PROF_STAMINA_COST",
      "PROF_WAIT_DECAY", "PROF_WAIT_FLOOR", "MINING_KEYWORDS", "PAWN_RATES", "ENCHANT_SLOT_UNLOCK",
      "RUNE_LEVEL_GATE", "DAILY_PROF_EXP", "PRICE_BAND", "RARE_MATERIAL_PRICE", "GATHER_MAP_MIN_LV"),
     {}),
    ("formula_skeleton", "game/data/formula_skeleton.py", ("FORMULA_SKELETON",), {}),
    ("stat_templates", "game/data/stat_templates.py",
     ("MONSTER_ROLE_BASE", "MONSTER_ROLE_GROWTH", "MONSTER_EXP_BASE", "FIELD_TIER_MULT",
      "NORMAL_HP_STAGE_MULT", "BOSS_ATK_STAGE_MULT", "INSTANCE_BOSS_ATK_STAGE_MULT",
      "HP_STAGE_MULT", "ATK_STAGE_MULT", "MONSTER_GOLD_BASE", "MONSTER_ROLE_MODS",
      "EQUIP_SLOT_BASE", "EQUIP_SLOT_SCALING"), {}),
    ("builds", "game/data/builds.py", ("BUILDS",), {}),
    ("mounts", "game/data/mounts.py", ("MOUNT_POOL", "MOUNT_DROP_ELITE", "MOUNT_DROP_BOSS"),
     {"MOUNT_BY_KEY": "派生索引（{m['key']: m for m in MOUNT_POOL}），可由 MOUNT_POOL 重建"}),
    ("summons", "game/data/summons.py", ("SUMMONS",), {}),
    ("rules", "game/data/rules.py", ("RULES",), {}),
    ("base_growth", "game/data/base_growth.py", (),
     {"PLAYER_BASE_GROWTH": "panel_rules 域（成长结构声明，面板读它）"}),
    # -------------------------------------------------------------------------
    # B14-3（2026-09-14）「缺口 46 名」收口 —— 新增 9 组常量归口。
    # 判据：这些常量所属的宿主模块**已有实体域**（pets/maps/runes/affixes/fishing/pois/…），
    # 但实体域的 primary def 有实体必填字段（例：`pets` 要 key/name/quality/focus/skill_type/…，
    # `maps` 要 name/nodes，`runes` 要 name）⇒ 常量行塞不进去（硬塞 = 或硬造数据、或放水 required）。
    # 按本域既有设计（「一条 = 一个源模块的常量组」，不给常量留野地）+ B9「常量模块归 L7」口径，
    # 落这里；`owned_elsewhere` 逐项注明那些常量各自的真域。
    # 未建域的那几个模块（equipment/factions/enchant/poi_pools/quest_add_v140/gems）本轮
    # **单开新域**（`scripts/export_domains/b14_3_gaps.py`），不在本域重复（防双源）。
    # -------------------------------------------------------------------------
    ("pets", "game/data/pets.py", ("PET_MAX_LEVEL", "PET_SKILL_UNLOCK_LV"),
     {"PET_POOL": "pets 域（品种池 16 条，一条 = 一个品种）",
      "PET_EGG_ROLL": "pets 域导出期并入条目字段 `egg_roll`（蛋掉落规则，按品种 id 连接）",
      "PET_EXP_GRADE": "pets 域同族的成长档表（消费口径 = 品种经验曲线），本轮未导出（非缺口名）"}),
    ("maps", "game/data/maps.py",
     ("MAP_CONNECTIONS", "LEGACY_MAP_ALIAS", "HIDDEN_MAP_UNLOCK"),
     {"MAPS": "maps 域（121 图，只取 name 做显示名）+ worlds 域（地图级元数据）",
      "MAP_BY_ID": "派生索引（{m['id']: m for m in MAPS}），可由 maps/worlds 域重建",
      "ENCY_MAP_MONSTERS": "源里是**空 dict**，装配期由 `game/core/maps` 填充的运行期索引（非数据）",
      "ENCY_MONSTER_MAP": "同上（源里空 dict，运行期建索引）",
      "MONSTER_LOCS": "同上（源里空 dict，`core/maps:_build_monster_locs` 运行期填充）",
      "ENCY_MATERIAL_SOURCE": "同上（源里空 dict，运行期建索引）"}),
    ("world", "game/data/world.py", ("WORLD_EVENT_POOL", "AUCTION_POOL", "WORLD_BOSS_POOL"), {}),
    ("runes", "game/data/runes.py",
     ("RUNE_CRAFT_SHARDS", "RUNE_DROP", "RUNE_LEVEL_ROMAN"),
     {"RUNES": "runes 域（16 条符文）", "RUNE_CRAFT": "runes 域导出期注入条目字段 `craft`",
      "RUNE_CONFLICTS": "runes 域导出期折成条目字段 `conflicts`",
      "RUNE_EFFECT_NAMES": "与 runes 域各条 `name` 逐条相等的**冗余展示表**（零新信息，不导）",
      "RUNE_SHARD_KEY": "物品 id 常量（`mat_fu_wen_sui_pian`）→ items 域按 id 引用，不在本域"}),
    ("affixes", "game/data/affixes.py", ("AFFIX_AFFINITY_CN", "AFFIX_POOL_BY_QUALITY"),
     {"AFFIXES": "affixes 域（76 条词条）", "LEGENDARY_EFFECTS": "legendary_effects 域（93 条）",
      "SERIES_FIXED_AFFIX": "套装固定词条表（外层键是中文装备名）—— 本轮无域，登记为缺口",
      "AFFIX_KIND": "词条大类显示名（attack/defense → 武器/防具），非缺口名",
      "AFFIX_AFFINITY_POOLS": "锻造倾向池（与 AFFIX_AFFINITY_CN 同族的池表），非缺口名"}),
    ("fishing", "game/data/fishing.py", ("FISH_COLLECT", "FISH_EXP"),
     {"FISHING_SPOTS": "fishing_spots 域（11 钓点）", "FISH_POOL": "fishing_pool 域（鱼种池）",
      "FISH_QUALITY_WEIGHTS": "品质权重表（非缺口名，无 `C.<名>` 读点）"}),
    ("pois", "game/data/pois.py", ("POIS",),
     {"SUBAREA_POIS": "pois 域（457 条 = 子区域落点，键 `map:subarea`）",
      "NOTE_POOL": "纸条池（`POIS` 的配套池），非缺口名",
      "RUNE_POOL": "符文石池，非缺口名", "SIGHT_POOL": "风景池，非缺口名"}),
    ("hidden_monsters", "game/data/hidden_monsters.py", ("HIDDEN_MONSTERS",), {}),
    ("instance_investigation", "game/data/instance_investigation.py",
     ("INVESTIGATE_COLLECT_SAMPLES",),
     {"INVESTIGATION_POINTS": "instance_investigation 域（22 本 / 90 个调查点）",
      "INVESTIGATE_BP_CHANCE": "图纸残页概率常量（非缺口名）",
      "INVESTIGATE_RUNE_CHANCE": "蓝符概率常量（非缺口名）",
      "INVESTIGATE_COLLECT_CHANCE": "收藏概率常量（非缺口名）",
      "INVESTIGATION_COUNT": "派生计数（= 90，`sum(len(v) for v in INVESTIGATION_POINTS.values())`）",
      "INVESTIGATION_INST_COUNT": "派生计数（= 22，`len(INVESTIGATION_POINTS)`）"}),
)

# 自动组：模块 → (真源模块名, {排除: 理由}, 条数下界)
# 只对「表多且全是字面量字典」的模块用；AST 断言它们没有模块级 import/for/if（见 _discover）。
AUTO_GROUPS = (
    ("battle_config", "game/data/battle_config.py",
     {"TIER_GROWTH": "panel_rules 域", "BRANCH_BONUS": "panel_rules 域",
      "BRANCH_BONUS_BY_CLASS": "panel_rules 域",
      # 下面 4 张表的外层/内层键是 **tuple**（元素反应对 / (职业,档位)）—— JSON 键只能是字符串，
      # 落成 "('ice', 'fire_mark')" 这种不可逆形式（还原要 ast.literal_eval），本轮不导。
      "BRANCH_RESOURCE_OVERRIDE": "键 = tuple(职业 id, 档位) —— JSON 不可逆",
      "ELEMENT_REACTIONS": "键 = tuple(元素, 印记) —— JSON 不可逆",
      "REACTION_TABLE": "键 = tuple(元素, 印记) —— JSON 不可逆",
      "MECH_CFG": "内含 element.reactions 的 tuple 键（元素反应对）—— JSON 不可逆"},
     39),
    ("battle_rules", "game/data/battle_rules.py",
     {"EFFECT_RULES": "effect_rules 域", "PASSIVE_PROC": "passive_proc 域",
      # 顶层 `from .battle_config import (...)` 的 5 个名字：**家在 game_config.battle_config 组**，
      # 不在本组重复（导进来只是为了 `_dot_period` 公式生成，不是 battle_rules 自有表）。
      "DOT_DEFS": "game_config.battle_config 组（顶层 import 进来的）",
      "DOT_BOSS_PCT_MULT": "game_config.battle_config 组（顶层 import 进来的）",
      "DOT_PCT_CAP": "game_config.battle_config 组（顶层 import 进来的）",
      "DOT_BLEED_DOUBLE_HP_PCT": "game_config.battle_config 组（顶层 import 进来的）",
      "DOT_RESIST_CAP": "game_config.battle_config 组（顶层 import 进来的）"},
     4),
)


def _public_names(mod, where: str) -> dict:
    """模块级公开非 callable 常量 `{名: 值}`（`_私有` / 函数 / 类 一律不算）。"""
    import __future__
    out: dict = {}
    for n in dir(mod):
        if n.startswith("_"):
            continue
        v = getattr(mod, n)
        if callable(v) or isinstance(v, type) or isinstance(v, __future__._Feature):
            continue                       # `from __future__ import annotations` 会在运行期绑定一个
                                           # `_Feature` 对象，不是模块的数据常量
        out[n] = v
    if not out:
        raise ValueError(f"{where}：读不到任何模块级公开常量 —— 源形状变了，拒绝导出")
    return out


def _assert_literal_module(mod_name: str, src_root: str, where: str) -> set:
    """自动组铁律：模块顶层不许有 for / if / while / with / try（import 期拼装 = 自动发现不安全）。

    **返回**顶层 import 进来的公开名字集：调用方必须逐个交代（callable/类/模块 无害；
    数据值 = 会被 `dir()` 扫描当成表 → 必须显式写进 `exclude` 并注明家在哪个模块/组）。

    `game/data/battle_config.py` 顶层只有字面量赋值（+ 1 个 def）；
    `battle_rules.py` 顶层有 `from .battle_config import (DOT_DEFS, DOT_BOSS_PCT_MULT, …)`
    —— 那 5 个名字**是 battle_config 的表**，正是这条闸要拦的重复面。
    """
    import ast
    import os
    from _helpers import REPO_ROOT
    root = src_root or REPO_ROOT
    path = os.path.join(root, "game", "data", f"{_mod_key(mod_name)}.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    bad = [type(n).__name__ for n in tree.body
           if isinstance(n, (ast.For, ast.AsyncFor, ast.While, ast.If, ast.With, ast.Try))]
    if bad:
        raise ValueError(f"{where}：{path} 顶层出现 {bad} —— 自动发现不再安全"
                         f"（拼装/条件导入来的名字会被当成表），请改成显式组并人工判定")
    imported: set = set()
    for n in tree.body:
        if isinstance(n, ast.Import):
            imported |= {a.asname or a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            if n.module == "__future__":
                continue                       # `from __future__ import annotations` 只影响编译期
            imported |= {a.asname or a.name for a in n.names}
    return {n for n in imported if not n.startswith("_")}


def derive_game_config(src_root: str = None) -> dict:
    """`game_config` 域：一条 = 一个源模块的常量组，`{模块名: {源常量名: 值}}`。

    「每个模块级常量都有家」硬闸见文件头；值为真源**原样**（`json_clean` 在宿主导出侧
    统一把 tuple 落成 array —— 包内消费端若按序解包/索引不受影响，判等 tuple 的地方要注意）。
    """
    out: dict = {}
    group_src: dict = {}

    # ---- 显式组 ----
    for key, mod_name, members, elsewhere in EXPLICIT_GROUPS:
        mod = _mod(mod_name, src_root)
        found = _public_names(mod, f"game_config.{key}（{mod_name}）")
        unknown = sorted(set(found) - set(members) - set(elsewhere))
        if unknown:
            raise ValueError(
                f"game_config.{key}：{mod_name} 有未归口的模块级常量 {unknown} —— "
                f"新常量必须有家（进 members，或写进 owned_elsewhere 并给理由），拒绝导出")
        for n in members:
            if n not in found:
                raise ValueError(f"game_config.{key}：{mod_name} 缺常量 {n} —— 源形状变了，拒绝导出")
            v = found[n]
            if isinstance(v, (dict, list, tuple, str)) and not v:
                raise ValueError(f"game_config.{key}.{n}：空值（{type(v).__name__}）—— 拒绝导出")
            _json_safe(v, f"game_config.{key}.{n}")
        grp = {n: found[n] for n in members}
        if not grp:
            continue                      # 纯「owned_elsewhere」模块（base_growth）→ 不建空条目
        out[key] = grp
        group_src[key] = mod_name

    # ---- 自动组 ----
    for key, mod_name, exclude, min_n in AUTO_GROUPS:
        imported = _assert_literal_module(mod_name, src_root, f"game_config.{key}")
        mod = _mod(mod_name, src_root)
        found = _public_names(mod, f"game_config.{key}（{mod_name}）")
        for n in sorted(imported & set(found)):
            v = getattr(mod, n)
            if callable(v) or isinstance(v, type) or type(v).__name__ == "module":
                continue                       # 函数/类/模块：`dir()` 扫描本来就跳过，无害
            if n not in exclude:
                raise ValueError(
                    f"game_config.{key}：{mod_name} 顶层 import 进来的 **数据名** {n}"
                    f"（{type(v).__name__}）会被当成表 —— 请显式写进 exclude 并注明它的家在哪个组")
        for n, why in exclude.items():
            if n not in found:
                raise ValueError(f"game_config.{key}：排除名单里的 {n} 在 {mod_name} 里不存在"
                                 f"（排除理由：{why}）—— 排除名单过时了，拒绝导出")
        members = {n: v for n, v in found.items() if n not in exclude}
        if len(members) < min_n:
            raise ValueError(f"game_config.{key}：只剩 {len(members)} 张表（下界 {min_n}）"
                             f" —— 源表被删/形状变了，拒绝导出")
        for n, v in members.items():
            _json_safe(v, f"game_config.{key}.{n}")
        out[key] = members
        group_src[key] = mod_name

    # 自证：组名 = 目录名（消费端/报告按组名定位真源；漂了就说明有人改了键口径）
    for key, mod_name in group_src.items():
        if mod_name.rsplit("/", 1)[-1] != f"{key}.py":
            raise ValueError(f"game_config：组名 {key!r} 与真源模块 {mod_name!r} 不一致"
                             f" —— 键口径是「模块名」，拒绝导出")
    return sort_table(out)


DOMAINS = {
    "trial_floors": derive_trial_floors,
    "game_config": derive_game_config,
}
