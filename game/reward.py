# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - reward.py（统一奖励发放器）—— ★ B12B13-TAIL 线3 **薄壳**（2026-09-14）

实现正文（225 行 = `grant_reward` / `grant_items_batch` / 五个发放子过程）已**逐字搬进内容包**
`content/reward.py`（发奖**规则**属内容；**实际落库**走注入的 `db` 句柄）。本文件只剩四件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **注入宿主取件（七个活源 thunk）** —— 真源那七处本来就是**函数内惰性 import 宿主**
     （只有 `LOG` 在模块级），薄壳把 import 点搬进 thunk，经 `bind_host(...)` 挂进包内实现；
     **取件时机与真源一一对应**（`tlog` 埋点仍在 `grant_reward` 的 try 内、`db` 仍在发奖时问一次）：

        `_db()`          ← `from . import db`
        `_content()`     ← `def _c(): import game.content as C`
        `_log()`         ← 模块级 `from .log_setup import LOG`（日志门面留宿主 = 平台适配）
        `_tlog()`        ← `from . import tlog_setup as _tlog`（埋点唯一入口，留宿主）
        `_levelup()`     ← `from .content_rules.gameplay import check_player_level_up`
        `_stat_bonus()`  ← `from .core.stat_bonus import stat_bonus`
        `_key_to_id_fn()`← `from .store.inventory import _key_to_id`

     七个 thunk 都**每次调用问一次** → 打桩 / 替换宿主模块属性照旧可见（与真源同款）。
  3. **模块别名**（`sys.modules[__name__] = 包内模块`）—— 与 `game/core/fishing.py` 同款。
     引用链零改动，全宿主调用点**一行未改**：
       `game/commands/talk_actions.py:42` · `game/commands/weekly.py:27-28` ·
       `game/services/quests_flow.py:36` · `game/services/weekly_progress.py:21`（`from ..reward import grant_reward`）
       `content/{achievements,commands,quests_flow,talk_actions}.py` · `content/flow/weekly_progress.py`
       （`_host_attr("reward", "grant_items_batch")` / `_resolve_host("reward")`）
       测试：`tests/test_numeric_reward_unify.py:51` · `tests/test_v182_behavior_tlog.py:48/76`
       （`from game.reward import grant_reward` —— 别名后拿到的是同一只实现函数）。
  4. **源码探针**：`tests/test_v182_behavior_tlog.py:59` 按**本文件源码**查掉落埋点
     `emit("drop.grant"`（防被误删）—— 探针字面量留在本文件，并在 import 期断言「它确实长在
     包内实现里」：指针指向的实现若漂移，直接 import 失败（比「扫到壳上一句注释就过」强）。

⚠️ 本文件**刻意不含**任何真源正文里的大写模块级常量名（`RULES` 之类）以外的旧实现细节 ——
   旧正文只在包内一份（无第二真源）。
"""
import inspect as _inspect
import sys as _sys

from . import bootstrap as _bootstrap

_bootstrap.package_apply()                          # 包加载口（幂等；失败大声抛，不静默）
from content import reward as _impl                 # noqa: E402  包内实现（唯一真源）


# ============================================================
# 宿主取件：七个活源（真源 import 点逐条对应；调用时才解析）
# ============================================================

def _db():
    """真源 `from . import db`（存储层；实际落库走这个句柄）。"""
    from . import db as _m
    return _m


def _content():
    """真源 `def _c(): import game.content as C`（绝对导入，防循环/半初始化）。"""
    import game.content as _C
    return _C


def _log():
    """真源模块级 `from .log_setup import LOG`（日志门面 = 平台适配，留宿主）。"""
    from .log_setup import LOG
    return LOG


def _tlog():
    """真源 `grant_reward` 的 try 内 `from . import tlog_setup as _tlog`（埋点唯一入口，留宿主）。"""
    from . import tlog_setup as _m
    return _m


def _levelup():
    """真源 `from .content_rules.gameplay import check_player_level_up`（升级结算）。"""
    from .content_rules.gameplay import check_player_level_up
    return check_player_level_up


def _stat_bonus():
    """真源 `from .core.stat_bonus import stat_bonus`（属性加成）。"""
    from .core.stat_bonus import stat_bonus
    return stat_bonus


def _key_to_id_fn():
    """真源 `_grant_items` 内 `from .store.inventory import _key_to_id`。"""
    from .store.inventory import _key_to_id
    return _key_to_id


_impl.bind_host(db=_db, content=_content, log=_log, tlog=_tlog,
                levelup=_levelup, stat_bonus=_stat_bonus, key_to_id=_key_to_id_fn)

# ============================================================
# 源码探针（tests/test_v182_behavior_tlog.py:59）
# ============================================================

_SRC_PROBES = ('emit("drop.grant"',)                # noqa: F841  埋点字面量指针（防被误删）
try:
    _IMPL_SRC = _inspect.getsource(_impl)
except OSError as _exc:                             # pragma: no cover
    raise RuntimeError("reward 薄壳：取不到包内实现源码，埋点指针无法核验（%r）" % (_exc,))
for _needle in _SRC_PROBES:
    if _needle not in _IMPL_SRC:
        raise RuntimeError("reward 薄壳：包内实现已漂移（源码里查不到 %r）" % (_needle,))

# ============================================================
# 模块别名：壳与实现同体（引用链 / 同一性全部照旧）
# ============================================================

_sys.modules[__name__] = _impl
