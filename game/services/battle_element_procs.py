# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - battle_element_procs.py（★ B10 线 L2 起 = **薄壳**）

实现正文（印记反应 / 克制 / 元素流转 + 两轴装配入口）**唯一真源已归内容包**：

    <pkg>/content/mech/element_procs.py   （P4/D2 + D2b 逐字端口；真源 = 本文件旧版 341 行）
    对拍：只差 3 处 —— ① `_reactions()` 的表 import（`..data.battle_config` → `.element_data`）
          ② 包内新增 `__all__` + 头注 ③ `apply_element_procs` 的 skill_info import 换包内同源物；
          其余函数体 / 数值 / `logs.append` 文案 / 注释**逐字相同**

本文件只做两件事，**零实现**（无控制流、无数值、无文案字面量）：

  1. 加载内容包 —— `game.bootstrap.package_apply()`（幂等；失败大声抛）
  2. **同名单 re-export** —— 路径与符号名不变；包内装饰器在 import 时注册
     （`import 即注册` 语义不变）

宿主侧活消费者（实测 `git grep`）：`tests/test_v181_element_and_field.py:44`
（`EP.apply_element_procs(p)`）+ `tests/test_v181_batch_b_resist_data.py:193`
（`from game.services.battle_element_procs import COUNTER_RULES`）—— 两者都零改动。
逐字节对拍证据：`overnight/B10-L2-team-element-tlog.md`（改前 ≡ 改后：sha256 + 字节数）。
"""
from __future__ import annotations

from .. import bootstrap as _BST

_BST.package_apply()                                          # 唯一包加载口
from content.mech.element_procs import (                      # noqa: E402  包内唯一真源
    ELEMENT_MARKS, COUNTER_RULES,
    _info, _element_of, _mark_of, _reactions, _reaction_of,
    elem_reaction, _apply_freeze, elem_counter, class_element_switch, elem_conv_apply,
    apply_element_procs,
)
# 旧宿主模块级名保真（引擎既有动词的 import，非本模块实现）
from saintess_engine.battle.effects import register_action    # noqa: E402,F401
