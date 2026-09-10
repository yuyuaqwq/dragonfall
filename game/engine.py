# -*- coding: utf-8 -*-
"""兼容 shim（S5）：`game/engine.py` 已一拆为二（docs/ENGINE_CONTENT_SPLIT_PLAN.md §6.4 / §7.5）。

本体迁往：
  - 引擎侧通用公式 → `game/battle2/formulas.py`（零游戏知识；表读走 config 注入面）
  - 内容侧表读     → `game/content_rules/skills.py`   （PLAYER_SKILLS/BRANCH_SKILLS/TUTOR_SKILLS/SKILL_UP）
                    `game/content_rules/panel.py`    （CLASSES/RACES/SETS/PCT_CAPS 面板公式）
                    `game/content_rules/gameplay.py` （元素反应/机制叠层/升级结算/掉落解析）

本模块**只做 re-export，不含任何实现**：`from game import engine as E` /
`from .. import engine as E`（67 个文件 / 79 条语句）保持可用，数值与行为零变化。

S9 收口（§7-S9）时删。
"""
import random  # noqa: F401  （保留旧模块命名空间，dir() 对齐 S5 前）

from . import content as C  # noqa: F401  （旧 `E.C` 消费点：tests/test_commands_skills.py）
from .core.skill_kinds import K_PASSIVE  # noqa: F401
from .data.base_growth import PLAYER_BASE_GROWTH  # noqa: F401
from .data.battle_config import (  # noqa: F401
    BRANCH_BONUS,
    BRANCH_BONUS_BY_CLASS,
    ELEMENT_REACTIONS,
    MECH_CFG,
    MECH_STACK_MAX,
    TIER_GROWTH,
)
from .data.formula_skeleton import FORMULA_SKELETON  # noqa: F401

# ---- 引擎侧通用公式（game/battle2/formulas.py）----
from .battle2.formulas import (  # noqa: F401
    SKILL_MAX_LEVEL,
    calc_damage,
    resolve_formula,
    skill_buff_turns,
    skill_cond_mult,
    skill_expr_preview,
    skill_flat_value,
    skill_formula_expr,
    skill_formula_expr_for_seg,
    skill_learn_cost,
    skill_lifesteal_pct,
    skill_max_level,
    skill_mech_val,
    skill_mp_pay_of,
    skill_power_mult,
)

# ---- 内容侧技能表读取（game/content_rules/skills.py）----
from .content_rules.skills import (  # noqa: F401
    _br_table,
    _build_skill_key_index,
    _sk_table,
    _skill_up,
    _skill_up_name_index,
    branch_path_index,
    branch_skill_owner,
    is_skill_learned,
    skill_by_key,
    skill_info,
    skill_level_of,
    skill_owner_cls,
    skill_upgrade_cost,
    skills_for_level,
)

# ---- 内容侧玩家面板（game/content_rules/panel.py）----
from .content_rules.panel import (  # noqa: F401
    STAT_NAMES,
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
    skill_learn_cost_for,
)

# ---- 内容侧战斗/成长辅助（game/content_rules/gameplay.py）----
from .content_rules.gameplay import (  # noqa: F401
    ELEMENT_CN,
    ELEMENT_MARKS,
    ELEMENT_OPTIONS,
    check_player_level_up,
    element_mark_apply,
    element_reaction,
    mech_stack_gain,
    resolve_drop,
)


def __getattr__(name: str):
    """两个懒构建缓存的**活读**转发（`_SKILL_KEY_INDEX` / `_SKILL_UP_NAME_INDEX`）。

    它们是 `content_rules/skills` 的模块级可变缓存（首次查询时填充）——
    re-export 会快照成 None，故改为按需转发，与 S5 前「同名全局」语义一致。
    """
    if name in ("_SKILL_KEY_INDEX", "_SKILL_UP_NAME_INDEX"):
        from .content_rules import skills as _skills
        return getattr(_skills, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
