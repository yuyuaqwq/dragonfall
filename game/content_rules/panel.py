# -*- coding: utf-8 -*-
"""内容侧玩家面板公式 —— **宿主薄壳**（B12B13-TAIL 线 1，2026-09-14）。

实现已归内容包：`content/panel.py`（= 本文件旧版的**逐字端口**；包内 `content/apply.py`
`install_engine()` 挂到引擎 `config.panel_fn` 的就是它）。本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败**大声抛**，不静默留空 hook）
  2. 同名单 re-export —— **公开/私有名与签名逐字保留**：`commands/base.py`（`STAT_NAMES`）、
     `commands/economy.py`（`STAT_NAMES` / `_set_info` / `player_final_stats` / `race_stats`）、
     `services/party.py`、`services/battle_settlement.py`、`tests/numeric_sim.py`、
     `tests/test_v136_class_discount.py` 等**全按名引用**（一个都不能少）。
  3. **残留名兼容面**（旧版 `import` 带进来的模块面：`C` / `K_PASSIVE` / `PLAYER_BASE_GROWTH` /
     `TIER_GROWTH` / `BRANCH_BONUS` / `BRANCH_BONUS_BY_CLASS` / `skill_info` / `skill_learn_cost`）
     —— 逐名保持（`overnight/b12b13_L1_surface.py` 公开面冻结比对判据：**丢名报红**）。

真源 = 本文件旧版 584 行（`tests` 侧无源码级断言；证据见 `overnight/W-B12B13-L1.md`：
109 例快照 before/after 逐字节相同 + `test_texts_table` / 命令矩阵 / 数值门禁）。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                       # 包根进 sys.path（失败抛，不静默）
from .. import content as C  # noqa: E402,F401   （原文 `from .. import content as C` 的残留名）
from .skills import skill_info  # noqa: E402,F401  （原文 `from .skills import skill_info`）
from content.panel import (  # noqa: E402,F401
    BRANCH_BONUS,
    BRANCH_BONUS_BY_CLASS,
    K_PASSIVE,
    PLAYER_BASE_GROWTH,
    STAT_NAMES,
    TIER_GROWTH,
    _PASSIVE_STAT_APPLY,
    _set_info,
    active_sets,
    apply_passive_to_stats,
    has_set,
    is_passive_learned,
    passive_skills_learned,
    player_base_stats,
    player_final_stats,
    player_passive_stats,
    player_stats_detail,
    race_name,
    race_stats,
    set_bonus_2,
    set_bonus_4,
    skill_learn_cost,
    skill_learn_cost_for,
)
