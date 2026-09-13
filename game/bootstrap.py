# -*- coding: utf-8 -*-
"""内容侧引擎装配 —— 把《奥兰迪亚》内容注入 saintess_engine 引擎（S1 断链 + S5 公式拆分）。

背景：docs/ENGINE_CONTENT_SPLIT_PLAN.md §3.2 —— 引擎（framework/saintess_engine/）历史上
有 15 条「引擎 → 内容」反向 import 边。S1 全部改为**内容 → 引擎**方向的注入：

    mount_engine_hooks()   注入数值公式/面板/技能查询/kind 常量（幂等）
    load_engine_config()   完整装配 = hook + 规则表（EFFECT_ACTIONS/EFFECT_RULES）
                           —— 即旧 `saintess_engine.config.load_game_defaults()` 的实体

S5（§6.4 / §7.5）：`game/engine.py` 一拆为二后，公式/面板/技能查询的落点变为
    - `framework/saintess_engine/formulas.py`   引擎侧纯数值公式（零内容 import）
    - `game/content_rules/skills.py`   技能表读取（PLAYER_SKILLS/…/SKILL_UP）
    - `game/content_rules/panel.py`    玩家面板公式（CLASSES/RACES/SETS/PCT_CAPS）
本模块负责把「公式参数表 + 内容查询函数」挂到引擎 config 的 S5 注入面
（`formula_skeleton_fn` / `skill_flat_fn` / `skill_up_fn` / `skill_level_of_fn`），
使 formulas.py 不必认识任何游戏表。

旧名/旧位置 `saintess_engine.config.load_game_defaults()` 保留为兼容 shim，
委托回本模块（52 个测试调用点，见 §8-R7）。

装配时机：`game/content.py` 末尾 / `game/__init__.py` import bootstrap 时登记，
凡 import 内容者即完成 hook 装配，行为与 S1 前（引擎直接 import 内容函数/表）等价；
规则表仍只在显式 load_game_defaults() 时装载（保持旧语义）。

阶段说明：本文件最终迁 `content/bootstrap.py`（§6.3 / §7 S7）；S1 先落
`game/bootstrap.py`，S6 内容层重组时随内容一起搬。
"""
from __future__ import annotations

from saintess_engine import config as _b2cfg


# ------------------------------------------------------------
# 惰性取件（防装配期循环 import —— 装配发生在内容包 import 期间）
# ------------------------------------------------------------

def _formulas():
    """引擎侧纯数值公式模块（S5 落点：framework/saintess_engine/formulas.py）。"""
    from saintess_engine import formulas as _f
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
    """职业 basic_skill 配置（S1 前在 saintess_engine/actions.resolve_basic_skill 内直读表）。"""
    try:
        from . import content as _C
        cid = _C.resolve("classes", class_name or "")
        bs = (_C.CLASSES.get(cid, {}) or {}).get("basic_skill") or {}
        return bs if isinstance(bs, dict) else None
    except Exception:
        return None


def _monster_skill(key):
    """怪物技能表查询（S1 前在 saintess_engine/battle._index_one_actor 内直读 C.MONSTER_SKILLS）。"""
    try:
        from . import content as _C
        return (_C.MONSTER_SKILLS or {}).get(key)
    except Exception:
        return None


def _kinds() -> dict:
    """kind 语义常量（S1 前写死在 saintess_engine/actions.py:22-26）。"""
    # P4 下沉（2026-09-13）：中文 kind 词表真源 = game/data/kinds.py（原 saintess_engine/kinds/）
    from .data.kinds import K_PHYS, K_MAGI, K_TRUE, K_HEAL, K_BUFF
    return {"phys": K_PHYS, "magi": K_MAGI, "true": K_TRUE, "heal": K_HEAL, "buff": K_BUFF}


def _basic_fallback() -> dict:
    """普攻兜底配置（S1 前写死在 saintess_engine/actions.py:42 的 {"name": "攻击", …}）。"""
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
        from .data.battle_rules import BAR_STATE_PREFIX
        return BAR_STATE_PREFIX or "bar:"
    except Exception:
        return "bar:"


# ============================================================
# ★ B8 切消费端（2026-09-13）：hook 面 / 规则表 / 开战装配的真源**已全部归内容包**
#   （`<plugin>/framework/games/orlandia/` —— 与 `game/__init__.py` 插进 sys.path 的 framework 根
#    是同一个 submodule，即「引擎 + 包」同源，不额外复制一份）。
#   本文件从「自己取件挂 hook」改成「加载包 + 调包自己的 install_engine()」；
#   上面那些 `_formulas()/_panel()/_skills()/_kinds()/…` 取件器随本次收口退役
#   （B8 退役批：宿主副本移出仓，见 overnight/B8_*.md）。
# ============================================================

import os as _os

_PKG_DIR = _os.path.normpath(_os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "framework", "games", "orlandia"))

_PKG_APPLY = None      # 包内 `content.apply` 模块（本进程唯一加载口缓存）


def package_apply():
    """加载内容包（幂等）并返回包内 `content.apply` 模块 —— **本进程唯一的包加载口**。

    走引擎的包加载器 `saintess_engine.package.load`：包根进 sys.path → `content` 成命名空间包
    → `import content.apply`（包内相对导入因此可用）→ 调它的 `install_engine()`。
    失败 → **抛**（不静默降级：hook 面空着 = 引擎 `strict=False` 下数值全 0 的「静默零放」，
    比报错难查得多）。
    """
    global _PKG_APPLY
    if _PKG_APPLY is None:
        from saintess_engine import package as _pkg_loader
        info = _pkg_loader.load(_PKG_DIR)
        if not (info.get("ok") and info.get("installed")):
            raise RuntimeError("内容包加载失败：%s" % (info.get("errors"),))
        _PKG_APPLY = info["apply"]
    return _PKG_APPLY


def mount_engine_hooks() -> None:
    """把内容函数/常量注入引擎 config hook 面（幂等；内容侧入口）。

    ★ B8：真源 = 内容包 —— 本函数 = 「加载包」。`package.load` 内部即调
    `content/apply.install_engine()`，由**包自己** mount 13 个 hook 名 + 注册惰性装配器。
    """
    package_apply()


def load_engine_config() -> None:
    """完整装配（= hook 面 + 规则表）。

    ★ B8：规则表那一步也在包里（`content/mech/params.py` 的 `EFFECT_RULES` / `EFFECT_ACTIONS`，
    由包内 `install_engine()` 走 `config.load_game_rules(P)` 装载）→ 本函数委托包加载。

    ⚠️ 装载顺序（§8-R1 导入环）：**先引 `game.content`**，再加载包。
    若先 `from .data import ...`，data→core 的半初始化链会中途拉进 content，
    content 的 `from .data import *` / `from .core import *` 拿到残缺命名空间
    （star-import 命中半成品模块）→ 静默缺符号，甚至反向成环报
    `ImportError: cannot import name 'build_index' from partially initialized module`。
    （B8 第一版把这一行删了 → 实测 `test_v181_batch_b_resist_data` 当场红，已复原。）
    """
    from . import content  # noqa: F401  (必须先于 game.data —— 见 docstring)
    package_apply()


def install() -> None:
    """包 import 期登记（幂等）。

    ★ B8：登记动作也归包 —— `install_engine()` 自己 `register_hook_provider`。本函数只负责
    「把包加载起来」；加载失败**大声抛**（不静默留一个没装配的引擎）。
    """
    package_apply()


# 内容侧登记（game/__init__.py 调用 install()；此处兜底再调一次，幂等）
install()

