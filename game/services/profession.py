# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - profession.py（★ B9 L4 起 = 薄壳）

逻辑真源已进内容包：`content/profession.py`（**逐字端口**，真源 = 本文件旧版 958 行；
生成器 = `overnight/b9_l4_gen.py`，可复跑校验）。

本文件只做四件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：`db`（存储层）· `content`（读表口 C）· `core.timed_events`（倒计时引擎）
     · `log_setup`（日志门面）· `drop_engine.expand_pool`（产出池展开）
     —— 全部走**懒 thunk**：与真源的 import 时机一致（真源 db / drop_engine 都是函数体内惰性 import）
  3. **保留模块级副作用**（真源就在模块顶层，行为必须逐字保持）：
       · `validate_gather_cond()` —— v125.2 启动校验 fail-fast（数据拼错 → import 期即抛）
       · `_te.register_timed("prof_wait", duration_sec=None, on_expire=prof_wait_expire_cb)`
         —— 回调体在包里，注册时机/注册者仍是本宿主模块（`_te._timers._spec("prof_wait")` 内容不变）
  4. **同名单 re-export** —— 保持模块路径与符号名不变（`game/services/__init__.py` 的聚合导出、
     `game/commands/economy.py` 的转发壳、各测试零改动）：

        `game/services/__init__.py:54`（29 个符号）
        `game/commands/economy.py:28`（`_prof_svc.*` 转发壳 + `_prof_wait_expire_cb` 兼容指针）

宿主注入的必要性：包内模块**不 import 宿主**（方向只有 内容 → 引擎）；它按 `bind_host(...)`
或「已加载的宿主模块」解析存储层/读表口，见包内模块 docstring 的替身接口表。

⚠️ **本文件是 `prof_wait` 引擎注册（`on_expire` 数据保全回调）与 v125.2 启动校验的当前唯一落点**：
包内模块**没有** import 期副作用（包在 `package_apply()` 里被加载，那时宿主 `content`/`timed_events`
未必就绪）。收口若要退役本薄壳，**必须先把下面两行迁到新落点**（否则 `prof_wait` 到点不再触发
`on_expire` → 旧轮结算数据静默丢失，且启动校验消失）。

逐字节等价证据：`overnight/b9_l4_snap.py`（1183 例 · 整库 dump · sha256 对拍）。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap
from .. import content as _C
from ..core import timed_events as _te
from ..log_setup import LOG as _LOG

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content import profession as _pkg              # noqa: E402


def _host_db():
    """宿主存储层（真源 `from .. import db`，**函数体内**惰性 import → 保持时机）。"""
    from .. import db
    return db


def _host_expand_pool(*args, **kwargs):
    """宿主产出池展开（真源 `from ..drop_engine import expand_pool`，函数体内惰性 import）。"""
    from ..drop_engine import expand_pool
    return expand_pool(*args, **kwargs)


_pkg.bind_host(_pkg.lazy_module(_host_db), content=_C, timed=_te, log=_LOG,
               expand_pool=_host_expand_pool)        # 宿主替身注入（幂等）

_pkg.validate_gather_cond()                          # v125.2 启动校验（原模块顶层自带，fail-fast）
_te.register_timed("prof_wait", duration_sec=None,
                   on_expire=_pkg.prof_wait_expire_cb)   # 引擎注册（原模块顶层自带）

# ---- 同名单 re-export（逐字沿用真源符号名）----
MINING_FATIGUE_THRESHOLD = _pkg.MINING_FATIGUE_THRESHOLD
MINING_FATIGUE_RECOVER = _pkg.MINING_FATIGUE_RECOVER
# v125.2 限定采集条件词注册表（命令层 `game/commands/economy.py:599` 模块级取用同一 dict 对象）
_GATHER_COND_CHECKERS = _pkg._GATHER_COND_CHECKERS
FISHING_SURPRISE_TRIGGER = _pkg.FISHING_SURPRISE_TRIGGER
FISHING_SURPRISE_BP = _pkg.FISHING_SURPRISE_BP
FISHING_SURPRISE_EQ = _pkg.FISHING_SURPRISE_EQ
FISHING_SURPRISE_RUNE = _pkg.FISHING_SURPRISE_RUNE
FISHING_SURPRISE_GEM = _pkg.FISHING_SURPRISE_GEM
validate_gather_cond = _pkg.validate_gather_cond
prof_wait_expire_cb = _pkg.prof_wait_expire_cb
gather_roll = _pkg.gather_roll
gather_cond_roll = _pkg.gather_cond_roll
prof_wait_key = _pkg.prof_wait_key
prof_wait_ev_name = _pkg.prof_wait_ev_name
prof_wait_compat = _pkg.prof_wait_compat
prof_wait_residual = _pkg.prof_wait_residual
prof_wait_state = _pkg.prof_wait_state
prof_wait_clear = _pkg.prof_wait_clear
prof_wait_duration = _pkg.prof_wait_duration
prof_wait_begin = _pkg.prof_wait_begin
prof_delayed_push = _pkg.prof_delayed_push
prof_settle = _pkg.prof_settle
prof_wait_flow = _pkg.prof_wait_flow
settle_fishing = _pkg.settle_fishing
fishing_surprise_fn = _pkg.fishing_surprise_fn
collect_bonus_line = _pkg.collect_bonus_line
settle_gather = _pkg.settle_gather
mining_fatigue_state = _pkg.mining_fatigue_state
mining_fatigue_tick = _pkg.mining_fatigue_tick
mining_fatigued = _pkg.mining_fatigued
settle_mining = _pkg.settle_mining
