# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `constants`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/constants.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：全名单再导出（除 `ACT_TICK`，见下）。

消费者（顶层/函数内）多处零改动：`game/core/__init__.py:8`（43 名）· `game/commands/instance.py:34`（ACT_TICK）·
  `game/core/enchant.py:5` · `game/core/maps.py:4` · `game/store/players.py:93` · `game/content_rules/panel.py` ·
  `scripts/export_game_package.py:684/:2511`（读运行时属性 `SUB_TYPE_*` / `PCT_STATS` / `PCT_CAPS` / `PENE_PCT_STATS`：
  取的是**值**，走再导出语义不变；静态行号口径见该文件注释，行号变了但它只读属性）

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import constants as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 74 名）
START_MAP = _pkg.START_MAP
START_SUBAREA = _pkg.START_SUBAREA
DEFAULT_GOLD = _pkg.DEFAULT_GOLD
DEFAULT_ATTR_PTS = _pkg.DEFAULT_ATTR_PTS
DEFAULT_STAMINA = _pkg.DEFAULT_STAMINA
FLEE_CHANCE = _pkg.FLEE_CHANCE
FLEE_LEVEL_STEP = _pkg.FLEE_LEVEL_STEP
FLEE_SPD_STEP = _pkg.FLEE_SPD_STEP
FLEE_MIN = _pkg.FLEE_MIN
FLEE_MAX = _pkg.FLEE_MAX
MON_SKILL_CHANCE = _pkg.MON_SKILL_CHANCE
MON_SKILL_CRIT = _pkg.MON_SKILL_CRIT
SHIELD_COUNTER_CHANCE = _pkg.SHIELD_COUNTER_CHANCE
REFLECT_CHANCE = _pkg.REFLECT_CHANCE
ENCOUNTER_EVENT_CHANCE = _pkg.ENCOUNTER_EVENT_CHANCE
SA_BOSS_CHANCE = _pkg.SA_BOSS_CHANCE
ENCOUNTER_LOW_CHANCE = _pkg.ENCOUNTER_LOW_CHANCE
FISH_RARE_CHANCE = _pkg.FISH_RARE_CHANCE
PET_EGG_ORANGE_CHANCE = _pkg.PET_EGG_ORANGE_CHANCE
RARE_MAT_CHANCE = _pkg.RARE_MAT_CHANCE
PROF5_BONUS_CHANCE = _pkg.PROF5_BONUS_CHANCE
INST_EVENT_CHANCE = _pkg.INST_EVENT_CHANCE
MOVE_ENCOUNTER_CHANCE = _pkg.MOVE_ENCOUNTER_CHANCE
STARFALL_STUN_CHANCE = _pkg.STARFALL_STUN_CHANCE
BOSS_BP_DROP_CHANCE = _pkg.BOSS_BP_DROP_CHANCE
TRADER_DEAL_CHANCE = _pkg.TRADER_DEAL_CHANCE
CHEST_BP_CHANCE = _pkg.CHEST_BP_CHANCE
INSTANCE_BP_CHANCE = _pkg.INSTANCE_BP_CHANCE
ELITE_EQ_DROP_CHANCE = _pkg.ELITE_EQ_DROP_CHANCE
RECIPE_LV_TIERS = _pkg.RECIPE_LV_TIERS
MAP_TYPE_TOWN = _pkg.MAP_TYPE_TOWN
MAP_TYPE_FIELD = _pkg.MAP_TYPE_FIELD
MAP_TYPE_INSTANCE = _pkg.MAP_TYPE_INSTANCE
MAP_TYPE_HIDDEN = _pkg.MAP_TYPE_HIDDEN
SUB_TYPE_TOWN = _pkg.SUB_TYPE_TOWN
SUB_TYPE_STREET = _pkg.SUB_TYPE_STREET
SUB_TYPE_GATE = _pkg.SUB_TYPE_GATE
ITEM_TYPE_PET_EGG = _pkg.ITEM_TYPE_PET_EGG
ITEM_TYPE_MOUNT = _pkg.ITEM_TYPE_MOUNT
MATERIAL_KIND_TYPES = _pkg.MATERIAL_KIND_TYPES
CLASS_NOVICE = _pkg.CLASS_NOVICE
PCT_STATS = _pkg.PCT_STATS
PCT_CAPS = _pkg.PCT_CAPS
OPTIONAL_STATS = _pkg.OPTIONAL_STATS
PENE_PCT_STATS = _pkg.PENE_PCT_STATS
EVOLVE_LEVELS = _pkg.EVOLVE_LEVELS
EVOLVE_FEES = _pkg.EVOLVE_FEES
RESET_SKILL_COST = _pkg.RESET_SKILL_COST
DEFAULT_MAX_MP = _pkg.DEFAULT_MAX_MP
PVP_TIMEOUT_SEC = _pkg.PVP_TIMEOUT_SEC
GUILD_EXP_BASE = _pkg.GUILD_EXP_BASE
PROF_EXP_BASE = _pkg.PROF_EXP_BASE
STAMINA_RECOVER_INTERVAL = _pkg.STAMINA_RECOVER_INTERVAL
SKILL_PMULT_CAP = _pkg.SKILL_PMULT_CAP
BUFF_TURNS = _pkg.BUFF_TURNS
DEBUFF_TURNS = _pkg.DEBUFF_TURNS
BASE_DELAY = _pkg.BASE_DELAY
SPD_CT_CAP = _pkg.SPD_CT_CAP
SPD_REF = _pkg.SPD_REF
CAST_ATK = _pkg.CAST_ATK
CAST_SKILL = _pkg.CAST_SKILL
CAST_ITEM = _pkg.CAST_ITEM
CAST_FOOD = _pkg.CAST_FOOD
CAST_DEFEND = _pkg.CAST_DEFEND
CAST_FLEE = _pkg.CAST_FLEE
CAST_PET_SKILL = _pkg.CAST_PET_SKILL
DOT_THRESHOLD_MULT = _pkg.DOT_THRESHOLD_MULT
DOT_THRESHOLD_CAP = _pkg.DOT_THRESHOLD_CAP
DOT_MAX_TRIGGER = _pkg.DOT_MAX_TRIGGER
DOT_PRESERVE_PCT = _pkg.DOT_PRESERVE_PCT
DOT_PRESERVE_THRESHOLD_BONUS = _pkg.DOT_PRESERVE_THRESHOLD_BONUS
DOT_SATURATE_MULT = _pkg.DOT_SATURATE_MULT
prof_exp_need = _pkg.prof_exp_need

# ---------------------------------------------------------------- 门禁锚点（唯一留在宿主的字面量）
# `tests/test_package_mech_ports.py:256` 的 TABLES 用 AST **静态读本文件模块级字面量**，
# 与包内 `content/mech/we_data.py:22 ACT_TICK` 逐值对拍 → 本文件必须是字面量（改再导出会报「取不到」）。
# 该门禁本身就是这两份的漂移守卫；数值权威 = 策划案仓 32_数值设计.md。
ACT_TICK = 1.0        # 1 刻 = 1.0 时刻 = 1 游戏秒（鱼鱼拍板对齐秒）
