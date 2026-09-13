# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 `stats`（B13-L6 **薄壳**）。

真源（实现本体，逐字搬）已进内容包：`content/stats.py`。
本文件只剩三件事：**加载包**（幂等；失败大声抛）+ **同名单 re-export**（符号名/签名一字不变）
+ 数量：全名单再导出（含 17 张数据表名 + 私有 `_stage_mult` / `_boss_atk_stage` / `_EXP_TABLE`）。

消费者（顶层/函数内）9 处，全部零改动：
  · `game/commands/economy.py:25` `ARMOR_FAMILY_ALIAS, equip_value`
  · `game/core/__init__.py:50` `monster_stats, equip_stats, equip_value, exp_to_next, monster_exp, monster_gold`
  · `game/core/drops.py:3` · `game/core/affix.py:25/137` · `game/core/enchant.py:3` · `game/core/smith_stock.py:22`
  · 测试：`tests/test_core_engine.py:9` · `test_numeric_monster_curve.py:26`（含 `_stage_mult`/`_boss_atk_stage`）
    · `test_numeric_economy_toolkit.py:62`（`S.MONSTER_GOLD_BASE`）· `test_numeric_instance_reward.py:26`
  · 工具：`scripts/economy_lib/core.py:24` · `scripts/numeric_lib/gear.py:18` · `scripts/export_domains/monster_combat.py:262`（`mod._EXP_TABLE`）

逐字节等价证据：`overnight/w1213_l6_snap.py`（改前/改后同 sha256 + 字节数）；
差异面自检：`overnight/w1213_l6_diff.py`（只列「宿主取件」差异行）；本线报告 `overnight/W-B13-L6-stats-rules.md`。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap                       # noqa: E402 包加载口（本进程唯一；幂等）

_bootstrap.package_apply()                                   # 失败抛，不静默留一个空实现
from content import stats as _pkg  # noqa: E402                 # ← 唯一实现

# ---------------------------------------------------------------- 同名单 re-export（真源 29 名）
EQUIP_SLOT_BASE = _pkg.EQUIP_SLOT_BASE
EQUIP_SLOT_SCALING = _pkg.EQUIP_SLOT_SCALING
MONSTER_EXP_BASE = _pkg.MONSTER_EXP_BASE
MONSTER_GOLD_BASE = _pkg.MONSTER_GOLD_BASE
MONSTER_ROLE_BASE = _pkg.MONSTER_ROLE_BASE
MONSTER_ROLE_GROWTH = _pkg.MONSTER_ROLE_GROWTH
QUALITY = _pkg.QUALITY
NORMAL_HP_STAGE_MULT = _pkg.NORMAL_HP_STAGE_MULT
BOSS_ATK_STAGE_MULT = _pkg.BOSS_ATK_STAGE_MULT
INSTANCE_BOSS_ATK_STAGE_MULT = _pkg.INSTANCE_BOSS_ATK_STAGE_MULT
HP_STAGE_MULT = _pkg.HP_STAGE_MULT
ATK_STAGE_MULT = _pkg.ATK_STAGE_MULT
MONSTER_ROLE_MODS = _pkg.MONSTER_ROLE_MODS
FORMULA_SKELETON = _pkg.FORMULA_SKELETON
WEAPON_DIST = _pkg.WEAPON_DIST
ARMOR_FAMILY = _pkg.ARMOR_FAMILY
ARMOR_FAMILY_ALIAS = _pkg.ARMOR_FAMILY_ALIAS
hp_stage_mult = _pkg.hp_stage_mult
atk_stage_mult = _pkg.atk_stage_mult
_boss_atk_stage = _pkg._boss_atk_stage
_stage_mult = _pkg._stage_mult
monster_stats = _pkg.monster_stats
equip_stats = _pkg.equip_stats
_EQUIP_VALUE_WEIGHT = _pkg._EQUIP_VALUE_WEIGHT
equip_value = _pkg.equip_value
_EXP_TABLE = _pkg._EXP_TABLE
exp_to_next = _pkg.exp_to_next
monster_exp = _pkg.monster_exp
monster_gold = _pkg.monster_gold

__all__ = []  # 真源同款占位（防误读；core/stats 均经 core/__init__ 聚合）
