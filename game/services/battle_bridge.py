# -*- coding: utf-8 -*-
"""v181.P4 N5b 数据桥（saintess_engine 命令层适配）—— **B2-W2 薄壳指向**

位置：game/services/（saintess_engine 包外——鱼鱼红线：saintess_engine 引擎零改动、零旧数据知识，
本桥是"命令层侧的翻译层"，把命令层手里的旧数据形态（player dict / 怪组 / pet）
翻译成 saintess_engine 的 sides actors）。

真源（**唯一实现**）= 内容包 `content/bridge.py`（构造半边 D3 批搬入 + 回写半边 B9-L8 批搬入，
两向同处一个模块；逐函数对拍证据 `overnight/_b10_l4_recon.py`）。本文件**不再**逐个手写转发
（B2-W2：那是"再抄一份转发实现"），改为**机械指向**：

    `game.services.battle_bridge.<名>`  →  包内 `content.bridge.<同名>`（**同一对象**）

宿主侧只保留两类**真·宿主专属件**（平台件，接口表已冻结「不搬」）：

  ① `_EventStateView` / `_es_arg` / `_default_db`：把宿主 `db` 的 `get/set/delete_event_state`
     三动词适配成包内第三参要的 `event_state` dict 协议；**`db=None` 时回落宿主 db**
     （包内 `_as_event_state(None)` 是「无 event_state」，两者**不等价** ⇒ 这两个包装函数
      必须留在宿主、签名不许变：`prepare_player_for_battle(player, title_bonus=None, db=None)` /
      `apply_player_battle_start(player, actor, db=None)`）；
  ② `attach_tlog`：读 `game/tlog_setup` 流水开关 + `game/services/battle_tlog` 采集 sink
     （`content/bridge.py:544-567` 明确「包内不搬 sink」，只留「取宿主实现并调用」的一层口）。

其余 8 个名字（`player_to_actor` / `monster_to_actor` / `enemies_to_actors` / `build_sides` /
`_battle_boons_to_effects` / `apply_battle_loadout` / `_seed_battle_keys` / `sync_player_from_actor`）
＋ 3 个模块级常量（`_PLAYER_PASSTHROUGH` / `_BACK_SYNC_SCALARS` / `_BACK_SYNC_BAGS`）由模块级
`__getattr__` 转发（PEP 562），`from ..services.battle_bridge import sync_player_from_actor` 这类
调用点零改动，且拿到的是**包内同一对象**（身份更严格，不再是宿主壳的一层委托）。
"""
from __future__ import annotations

from typing import Optional

from .. import bootstrap as _bootstrap                       # noqa: E402

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import bridge as _pkg                           # noqa: E402  包内唯一实现


# ============================================================
# 宿主专属件 ①：db → 包内 `event_state` 协议替身
# ============================================================

class _EventStateView(dict):
    """宿主 db → 包内 `event_state` 协议替身（只用到 get / 赋值 / pop 三动词）。

    包内 `prepare_player_for_battle(player, title_bonus, event_state)` 的第三参是**普通 dict**
    （等价宿主 event_state 存储）。本类把宿主 db 的三动词接上：

        view.get(k)                 → db.get_event_state(k)
        view[k] = v                 → db.set_event_state(k, v)
        view.pop(k, default)        → db.delete_event_state(k)（键不存在则返回 default）

    `dict` 子类**只为**满足包内 `isinstance(event_state, dict)` 守卫 —— 键值**不落本对象**
    （`__setitem__` 已改道 db），故本对象不持有第二份状态。
    ⚠️ 契约：包内对 `event_state` 只用上述三动词；若包内改用 `setdefault` / `in` / 迭代，
       会落到 dict 自己的空存储上（静默偏差）→ 改包内那侧时必须同步改这里。
    """

    __slots__ = ("_db",)

    def __init__(self, db):
        super().__init__()
        self._db = db

    def get(self, key, default=None):
        v = self._db.get_event_state(key)
        return default if v is None else v

    def __setitem__(self, key, value):
        self._db.set_event_state(key, value)

    def pop(self, key, default=None):
        v = self._db.get_event_state(key)
        if v is None:
            return default
        self._db.delete_event_state(key)
        return v


def _default_db():
    """延迟取宿主存储层（避免顶部循环 import）。★ 宿主专属件（不进包）。"""
    from .. import db as _db
    return _db


def _es_arg(db):
    """宿主第三参 `db` → 包内 `event_state` 替身（`db or _default_db()`，与旧实现一字同款）。"""
    return _EventStateView(db or _default_db())


def prepare_player_for_battle(player: dict, title_bonus: Optional[dict] = None,
                              db=None) -> dict:
    """开战仪式（player dict 侧，build_sides 前调用）—— 实现见包内 `content/bridge`。

    签名 / 语义 / 返回（原地补全后同一引用）一字不变；第三参 `db` 仍走 `_EventStateView`
    （**不能用包内缺省**：包内 `None` = 无 event_state，宿主 `None` = 回落宿主 db，两者不等价）。
    """
    return _pkg.prepare_player_for_battle(player, title_bonus, _es_arg(db))


def apply_player_battle_start(player: dict, actor: dict, db=None) -> dict:
    """把旧 Battle.__init__ 的玩家侧开战仪式结果应用到 actor（第三参同上，走 `_EventStateView`）。"""
    return _pkg.apply_player_battle_start(player, actor, _es_arg(db))


# ============================================================
# 宿主专属件 ②：流水挂载（读 game/tlog_setup 开关 + 采集 sink；不进包）
# ============================================================

def attach_tlog(b, *, btype: str = "monster", player=None, enemies=None, seed=None):
    """给一场战斗挂**流水采集**（可拔插：未启用流水时**零行为**，直接返回 `b`）。

    开关在 `game/tlog_setup.py`（`DRAGONFALL_TLOG=1` 或显式 `enable()`）；
    采集器与回放见 `game/services/battle_tlog.py`，设计见 `docs/REFACTOR_tlog_landing.md`。
    调用点：开战处一行（`combat._open_battle` 等）；异常一律吞掉 —— 流水不该影响开战。

    ⚠️ 本函数**不委托包内**：它读宿主流水开关与 sink（`game.tlog_setup` / `battle_tlog`），
    属宿主侧契约（包内 `content/bridge.py` 头注「未搬」清单第 1 项）。
    """
    try:
        from ..tlog_setup import tlog as _tlog
        tl = _tlog()
        if tl is None:
            return b
        from .battle_tlog import BattleTLog
        BattleTLog(tl).attach(b, btype=btype, seed=seed, player=player, enemies=enemies)
    except Exception:                                         # noqa: BLE001
        pass
    return b


# ============================================================
# 机械指向（PEP 562）：其余名字 = 包内同一对象
# ============================================================

_FORWARDS = (
    "player_to_actor", "monster_to_actor", "enemies_to_actors", "build_sides",
    "_battle_boons_to_effects", "apply_battle_loadout", "_seed_battle_keys",
    "sync_player_from_actor",
    # 模块级常量（真源 §B10-L4：双源收口后宿主不再持有第二份）
    "_PLAYER_PASSTHROUGH", "_BACK_SYNC_SCALARS", "_BACK_SYNC_BAGS",
)


def __getattr__(name):
    """PEP 562：按名指向包内实现（同一对象 —— 不再是宿主侧的一层委托）。"""
    if name in _FORWARDS:
        return getattr(_pkg, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
