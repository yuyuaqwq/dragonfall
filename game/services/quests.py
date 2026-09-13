# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - quests（每日任务域，★ B9 L4 起 = 薄壳）

逻辑真源已进内容包：`content/profession_quests.py`（**逐字端口**，真源 = 本文件旧版 231 行；
生成器 = `overnight/b9_l4_gen.py`，可复跑校验）。包内模块名带 `profession_` 前缀是因为
与本批生活副业线（`content/profession.py`）同源，避免与别的线的 `content/quests*.py` 撞名。

本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：`db` / `content` / `core.texts`(T) / `content_rules.gameplay.check_player_level_up`
     / `core.stat_bonus.stat_bonus`
     —— 全部走**懒 thunk**：真源这五处**本来就是函数体内**惰性 import，薄壳保持同一时机
     （`game/services/quests.py` 可被单独 import 后直接用，不依赖宿主模块先加载）
  3. **同名单 re-export** —— 保持模块路径与符号名不变（含 6 个下划线兼容别名）：

        `game/services/__init__.py:13`（9 个符号）
        `game/services/quests_flow.py:629`（`bump_daily_progress`）/ `:736`（`DAILY_META_KEYS`/`settle_daily_quest`）
        `game/commands/world.py:54`（常量 + `daily_need`；`:60/67/74` 兼容壳）
        `game/commands/combat.py:31`（`DAILY_META_KEYS`/`settle_daily_quest`）
        `tests/test_services_quests.py` · `tests/test_texts_table.py:303` · `tests/test_v104_quests.py`

逐字节等价证据：`overnight/b9_l4_snap.py`（1183 例 · 整库 dump · sha256 对拍）。

本域接线的文案 key（调用点已随逻辑进包 `content/profession_quests.py`，此清单仅供静态扫描/
检索用 —— `tests/test_texts_table.py` 的调用点对账按文件扫「T.text/T.static 实参 + 文件内字符串
字面量」，包内文件不在它的 WIRED 扫面里，故在此登记）：

    quests.published · quests.have · quests.limit · quests.item · quests.item_reward
    quests.item_decay · quests.progress_note · quests.done · quests.done_decay
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content import profession_quests as _pkg       # noqa: E402


def _host_db():
    """真源 `from .. import db`（函数体内惰性 import）。"""
    from .. import db
    return db


def _host_content():
    """真源 `from .. import content as C`（函数体内惰性 import）。"""
    from .. import content
    return content


def _host_texts():
    """真源 `from ..core import texts as T`（函数体内惰性 import）。"""
    from ..core import texts
    return texts


def _host_level_up(*args, **kwargs):
    """真源 `from ..content_rules.gameplay import check_player_level_up`（函数体内惰性 import）。"""
    from ..content_rules.gameplay import check_player_level_up
    return check_player_level_up(*args, **kwargs)


def _host_stat_bonus(*args, **kwargs):
    """真源 `from ..core.stat_bonus import stat_bonus`（函数体内惰性 import）。"""
    from ..core.stat_bonus import stat_bonus
    return stat_bonus(*args, **kwargs)


_pkg.bind_host(_pkg.lazy_module(_host_db),
               content=_pkg.lazy_module(_host_content),
               texts=_pkg.lazy_module(_host_texts),
               level_up=_host_level_up,
               stat_bonus=_host_stat_bonus)         # 宿主替身注入（幂等）

# ------------------------------------------------------------
# 本域接线的文案 key 清单（**声明口径，不参与渲染**）
# ------------------------------------------------------------
# 真源里这 9 个 key 由 `T.text/T.static` 调用（`draw_daily` / `settle_daily_quest`）；薄壳化后
# 调用点随逻辑一起进了包内 `content/profession_quests.py`。此清单把「本域用了哪些文案 key」
# 留在宿主侧，供静态对账工具（`tests/test_texts_table.py` 的「文件内字符串字面量算引用」兜底
# 口径）与人工检索使用 —— 语义上等于「本域接线清单」，不是第二份文案真源（真源仍是
# `data/text_specs.json`）。
DOMAIN_TEXT_KEYS = (
    "quests.published", "quests.have", "quests.limit",
    "quests.item", "quests.item_reward", "quests.item_decay",
    "quests.progress_note", "quests.done", "quests.done_decay",
)

# ---- 同名单 re-export（逐字沿用真源符号名）----
DAILY_REPEAT_FACTORS = _pkg.DAILY_REPEAT_FACTORS
DAILY_META_KEYS = _pkg.DAILY_META_KEYS
DAILY_LIMIT = _pkg.DAILY_LIMIT
daily_repeat_pct = _pkg.daily_repeat_pct
daily_need = _pkg.daily_need
settle_daily_quest = _pkg.settle_daily_quest
bump_daily_progress = _pkg.bump_daily_progress
daily_pool = _pkg.daily_pool
draw_daily = _pkg.draw_daily
# P4-1 兼容别名（外部存档/工具/旧引用兜底；见包内模块常量区注释）
_DAILY_REPEAT_FACTORS = _pkg._DAILY_REPEAT_FACTORS
_DAILY_META_KEYS = _pkg._DAILY_META_KEYS
_daily_repeat_pct = _pkg._daily_repeat_pct
_daily_need = _pkg._daily_need
_settle_daily_quest = _pkg._settle_daily_quest
_bump_daily_progress = _pkg._bump_daily_progress
