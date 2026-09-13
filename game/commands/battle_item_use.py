# -*- coding: utf-8 -*-
"""saintess_engine 战斗内道具翻译器（**命令层薄壳**）。

把旧引擎道具 payload（item_templates 模板产物，引擎无关中间语言）翻译成
saintess_engine actor 效果。核心不变式：效果全部落到 saintess_engine actor
（hp/mp/buffs/hot/shields/food_effects），只调 saintess_engine 动词
（landing.heal_actor / effects.apply_effects / actor 容器直写），
引擎零道具名词。

★ B8.2 线4（2026-09-13）：翻译实现已归内容包
------------------------------------------
包内实现（唯一真源）：`<pkg>/content/mech/item_use.py`
（真源逐字搬入 + 五处 import 换包内同源物；对照表见该文件头）

本文件只做 **再导出**（宿主调用点/测试口径一字不变）：

    translate(battle, actor, payload[, target]) -> (logs, cast) | None
    can_translate(payload) -> bool
    make_override() -> callable(battle, action, actor, skill_name, target)

宿主调用点（改动前后同一批）：
  · `economy.use()` 副本/野外战斗内分支 —— `can_translate`（机制型缺口 → 不扣道具）
    + `make_override`（from_state 后注入 action_override）
  · `instance_battle.build_battle/_attach_instance_hooks`（开战/恢复后注入；本路同批薄壳化）
  · 测试 `tests/test_battle_item_use.py` / `test_battle_n10_b7_food.py` /
    `test_v101_28_food_hot.py`（均 `from game.commands.battle_item_use import translate`）

包加载口 = `from .. import bootstrap; bootstrap.package_apply()`（唯一，幂等）。
本文件**零实现**（无控制流、无数值、无文案字面量）。
"""
from __future__ import annotations

from .. import bootstrap as _BST

_BST.package_apply()                                      # 唯一包加载口（包根进 sys.path + install_engine）
from content.mech.item_use import (                       # noqa: E402  包内实现（翻译唯一真源）
    can_translate, make_override, translate,
)

__all__ = ["translate", "can_translate", "make_override"]
