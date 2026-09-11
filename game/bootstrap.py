# -*- coding: utf-8 -*-
"""内容侧引擎装配 —— 把《奥兰迪亚》内容注入 battle2 引擎（S1 断链 + S5 公式拆分）。

背景：docs/ENGINE_CONTENT_SPLIT_PLAN.md §3.2 —— 引擎（framework/battle2/）历史上
有 15 条「引擎 → 内容」反向 import 边。S1 全部改为**内容 → 引擎**方向的注入：

    mount_engine_hooks()   注入数值公式/面板/技能查询/kind 常量（幂等）
    load_engine_config()   完整装配 = hook + 规则表（EFFECT_ACTIONS/EFFECT_RULES）
                           —— 即旧 `battle2.config.load_game_defaults()` 的实体

S5（§6.4 / §7.5）：`game/engine.py` 一拆为二后，公式/面板/技能查询的落点变为
    - `framework/battle2/formulas.py`   引擎侧纯数值公式（零内容 import）
    - `game/content_rules/skills.py`   技能表读取（PLAYER_SKILLS/…/SKILL_UP）
    - `game/content_rules/panel.py`    玩家面板公式（CLASSES/RACES/SETS/PCT_CAPS）
本模块负责把「公式参数表 + 内容查询函数」挂到引擎 config 的 S5 注入面
（`formula_skeleton_fn` / `skill_flat_fn` / `skill_up_fn` / `skill_level_of_fn`），
使 formulas.py 不必认识任何游戏表。

旧名/旧位置 `battle2.config.load_game_defaults()` 保留为兼容 shim，
委托回本模块（52 个测试调用点，见 §8-R7）。

装配时机：`game/content.py` 末尾 / `game/__init__.py` import bootstrap 时登记，
凡 import 内容者即完成 hook 装配，行为与 S1 前（引擎直接 import 内容函数/表）等价；
规则表仍只在显式 load_game_defaults() 时装载（保持旧语义）。

阶段说明：本文件最终迁 `content/bootstrap.py`（§6.3 / §7 S7）；S1 先落
`game/bootstrap.py`，S6 内容层重组时随内容一起搬。
"""
from __future__ import annotations

from battle2 import config as _b2cfg


# ------------------------------------------------------------
# 惰性取件（防装配期循环 import —— 装配发生在内容包 import 期间）
# ------------------------------------------------------------

def _formulas():
    """引擎侧纯数值公式模块（S5 落点：framework/battle2/formulas.py）。"""
    from battle2 import formulas as _f
    return _f


def _panel():
    """内容侧玩家面板公式（S5 落点：game/content_rules/panel.py）。"""
    from .content_rules import panel as _p
    return _p


def _skills():
    """内容侧技能表读取（S5 落点：game/content_rules/skills.py）。"""
    from .content_rules import skills as _s
    return _s


# ------------------------------------------------------------
# S5 注入面供体（引擎 formulas.py 的表读点）
# ------------------------------------------------------------

def _skeleton():
    """公式骨架参数表（活读 data/formula_skeleton.py，与 S5 前引擎全局同对象）。"""
    try:
        from .data.formula_skeleton import FORMULA_SKELETON
        return FORMULA_SKELETON
    except Exception:
        return {}


def _skill_flat():
    """技能基础值常量表（活读 data/skill_up.py，与 S5 前函数体内 import 同语义）。"""
    try:
        from .data.skill_up import (SKILL_FLAT_BASE, SKILL_FLAT_PER_PLAYER_LV,
                                    SKILL_FLAT_PER_SKILL_LV)
        return {
            "SKILL_FLAT_BASE": SKILL_FLAT_BASE,
            "SKILL_FLAT_PER_PLAYER_LV": SKILL_FLAT_PER_PLAYER_LV,
            "SKILL_FLAT_PER_SKILL_LV": SKILL_FLAT_PER_SKILL_LV,
        }
    except Exception:
        return {}


def _skill_up(info):
    """技能升级配置查询（内容侧 SKILL_UP；S5 前在 game/engine.py `_skill_up`）。"""
    return _skills()._skill_up(info)


def _skill_level_of(player, skill_name):
    """技能等级查询（内容侧技能 id resolve；S5 前在 game/engine.py `skill_level_of`）。"""
    return _skills().skill_level_of(player, skill_name)


# ------------------------------------------------------------
# 基础装配件（S1）
# ------------------------------------------------------------

def _basic_skill_of(class_name):
    """职业 basic_skill 配置（S1 前在 battle2/actions.resolve_basic_skill 内直读表）。"""
    try:
        from . import content as _C
        cid = _C.resolve("classes", class_name or "")
        bs = (_C.CLASSES.get(cid, {}) or {}).get("basic_skill") or {}
        return bs if isinstance(bs, dict) else None
    except Exception:
        return None


def _monster_skill(key):
    """怪物技能表查询（S1 前在 battle2/battle._index_one_actor 内直读 C.MONSTER_SKILLS）。"""
    try:
        from . import content as _C
        return (_C.MONSTER_SKILLS or {}).get(key)
    except Exception:
        return None


def _kinds() -> dict:
    """kind 语义常量（S1 前写死在 battle2/actions.py:22-26）。"""
    from battle2.support.skill_kinds import K_PHYS, K_MAGI, K_TRUE, K_HEAL, K_BUFF
    return {"phys": K_PHYS, "magi": K_MAGI, "true": K_TRUE, "heal": K_HEAL, "buff": K_BUFF}


def _basic_fallback() -> dict:
    """普攻兜底配置（S1 前写死在 battle2/actions.py:42 的 {"name": "攻击", …}）。"""
    return {"name": "攻击", "kind": _kinds()["phys"], "exprs": ["atk*1.0"]}


def _mech_cfg(name):
    """机制配置表读取（S3 前在 core/battle_bars._battle_cfg 内经 importlib 直读）。

    活读（每次取 data.battle_config.MECH_CFG[name]）：与 S3 前直读语义一致，
    tests/数值仿真对 MECH_CFG 的运行期改动可见。
    """
    try:
        from .data.battle_config import MECH_CFG
        return MECH_CFG.get(name, {}) or {}
    except Exception:
        return {}


def _bar_prefix():
    """挂敌身条键前缀（S3 前在 core/battle_bars._state_prefix 内经 importlib 直读）。"""
    try:
        from .data.battle2_rules import BAR_STATE_PREFIX
        return BAR_STATE_PREFIX or "bar:"
    except Exception:
        return "bar:"


def mount_engine_hooks() -> None:
    """把本游戏的内容函数/常量注入引擎 config hook 面（幂等；内容侧入口）。"""
    _b2cfg.mount(
        formulas=_formulas(),                                # 数值公式（引擎侧纯公式模块，S5 落点）
        panel_fn=lambda *a, **k: _panel().player_final_stats(*a, **k),  # 玩家职业面板
        skill_lookup=_skills(),                              # .skill_info / .skill_by_key
        monster_skill_fn=_monster_skill,                     # 怪物技能表
        basic_skill_fn=_basic_skill_of,                      # 职业普攻配置
        kinds=_kinds(),                                      # kind 语义常量
        basic_fallback=_basic_fallback(),                    # 普攻兜底配置
        mech_cfg_fn=_mech_cfg,                               # 机制配置表（battle_bars）
        bar_prefix_fn=_bar_prefix,                           # 挂敌身条键前缀（battle_bars）
        # ---- S5：formulas.py 的表读点（引擎零内容 import）----
        formula_skeleton_fn=_skeleton,                       # 公式骨架参数表
        skill_flat_fn=_skill_flat,                           # 技能基础值常量表
        skill_up_fn=_skill_up,                               # 技能升级配置（SKILL_UP）
        skill_level_of_fn=_skill_level_of,                   # 技能等级查询
    )


def load_engine_config() -> None:
    """完整装配（旧 battle2.config.load_game_defaults 的实体）。

    = mount_engine_hooks()（hook 面）+ load_game_rules(battle2_rules)（规则表）。

    ⚠️ 装载顺序（§8-R1 导入环）：**先引内容包**，再取 battle2_rules。若先
    `from .data import ...`，data→core 的半初始化链会中途拉进 content，
    content 的 `from .data import *` / `from .core import *` 拿到残缺命名空间
    （star-import 命中半成品模块）→ 静默缺符号。先引 content 则顺序与 S1 前一致
    （content 先于 data 装载，环在 content.py 内部安全闭合）。
    """
    from . import content  # noqa: F401  (必须先于 game.data —— 见 docstring)
    from .data import battle2_rules
    mount_engine_hooks()
    _b2cfg.load_game_rules(battle2_rules)


def _lazy_mount() -> None:
    """引擎侧 hook 惰性装配器：首次访问未装配 hook 时调用。

    先把内容包引进来（内容 → 引擎方向），再做 hook 装配。
    """
    from . import content  # noqa: F401  (内容自举)
    mount_engine_hooks()


def install() -> None:
    """包 import 期登记（轻量：不 import 内容/引擎）。

    只登记「hook 惰性装配器」：引擎首次访问未装配 hook 时回调本包完成装配。
    （S8 拆仓后不再登记「默认配置装载器」——引擎侧已删除 `load_game_defaults`
    这类游戏概念 API；配置装配的入口在内容侧：
    `game.content_rules.apply.ensure_engine_configured()`。）
    """
    _b2cfg.register_hook_provider(_lazy_mount)


# 内容侧登记（game/__init__.py 调用 install()；此处兜底再登记一次，幂等）
install()
