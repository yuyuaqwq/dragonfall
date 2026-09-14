# -*- coding: utf-8 -*-
"""内容侧玩法规则（元素反应 / 叠层 / 升级结算 / 掉落名解析）—— **宿主薄壳**（B12B13-TAIL 线 1）。

实现已归内容包：`content/gameplay_rules.py`（= 本文件旧版的**逐字端口**，只动「取件口」；
`overnight/b12b13_L1_verbatim.py` 逐行证明 137/137 行相同）。本文件只做两件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败**大声抛**）
  2. 同名单 re-export —— `commands/instance.py`、`services/battle_settlement.py`、
     `services/quests.py` / `quests_flow.py`、`reward.py`、`store/players.py`、
     `tests/test_v140_commands.py` 全按名引用（`check_player_level_up` / `resolve_drop` …）。

真源 = 本文件旧版 158 行（证据见 `overnight/W-B12B13-L1.md`：升级结算整库 dump +
章节礼包落库 + 掉落解析 109 例快照 before/after 逐字节相同）。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                       # 包根进 sys.path（失败抛，不静默）
from .. import content as C  # noqa: E402,F401   （原文 `from .. import content as C` 的残留名）
from content.gameplay_rules import (  # noqa: E402,F401
    ELEMENT_CN,
    ELEMENT_MARKS,
    ELEMENT_OPTIONS,
    MECH_CFG,
    _sk_table,
    check_player_level_up,
    element_mark_apply,
    element_reaction,
    mech_stack_gain,
    player_base_stats,
    player_final_stats,
    resolve_drop,
)
