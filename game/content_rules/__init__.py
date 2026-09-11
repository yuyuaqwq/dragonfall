# -*- coding: utf-8 -*-
"""内容规则包（S5：自 `game/engine.py` 拆出的内容侧表读，docs/ENGINE_CONTENT_SPLIT_PLAN.md §6.4）。

顶层目录（非 `game/content/`）——避开后续 S6「内容层重组」的路径冲突（plan §7.5）。

  - skills.py   读 PLAYER_SKILLS / BRANCH_SKILLS / TUTOR_SKILLS / SKILL_UP 的技能查询
  - panel.py    读 C.CLASSES / C.RACES / C.SETS / PCT_CAPS 的玩家面板公式
  - gameplay.py 元素反应 / 机制叠层 / 升级结算 / 掉落名解析

判据：**凡读游戏表或职业名 → 内容侧**；引擎（framework/saintess_engine/）不得 import 本包，
需要数值时经 `saintess_engine.config` 注入 hook 取（game/bootstrap.py 装配）。

旧路径 `game.engine.*` 保留 shim re-export（S9 收口时删）。
"""
