# -*- coding: utf-8 -*-
"""宿主存储工厂（P5A：`game/store/store_factory.py` 迁移 / 改名进 `host/`）——

「宿主零逻辑」边界：本文件只有「**库路径怎么来**」与「**存档半边怎么取**」，
**零 SQL、零业务分支**（表结构与 CRUD 全在包内 —— B17 已归包）。

四类注入句柄（`inject`）的宿主落点
----------------------------------
| 键 | 宿主值 | 包内落点（由包侧 `bind_host` 扇出） |
|---|---|---|
| `db_path` | 本模块 `DB_PATH`（环境变量 `GWEN_GAME_DB` 优先，否则插件根 `game_data.db`） | 存档层注入面（建引擎 `Database`） |
| `clock` | 本模块 `clock()`（stdlib `time.time`） | 存档层 / 计时 |
| `log` | `host.log_setup.LOG`（= AstrBot `astrbot` logger 本体） | 日志唯一取用口 |
| `tlog` | `host.tlog_setup`（模块：`enable/disable/enabled/tlog/emit`） | 流水唯一取用口 |
| `attach_tlog` | `host.tlog_setup.attach_tlog`（**平台件**：把战斗挂到流水采集半边） | 接口表第 11 行冻结注入名 |
| `grant_reward` | 本模块 `grant_reward`（**能力口**，调用时才解析实现） | 发奖扇出 |

存档半边（`HostStore`）
----------------------
引擎契约把「读档 / 落档」交给适配器（`load_player` / `save_player`），而**权威玩家档是
落库的那一行**（包内 `content/persistence` 的 `get_player`：JSON 解码 / 惰性体力恢复 /
惰性升级 / 漏档兜底）。宿主因此不去重写一份 SQL（那会变成第二个真源、且与包的 hydration
逐字对齐不可能），而是经**引擎包契约**取包内存档半边：

    package.optional_submodule("persistence") → get_player(group_id, uid) / update_player(...)

取不到 → **抛**（fail-closed：拒绝静默空跑）。这是宿主侧唯一一条「读玩家档」的路。
"""
from __future__ import annotations

import json
import os
import sys
import time as _time

#: 插件根（`host/store_factory.py` → `host/` → 插件根）
PLUGIN_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

#: 库路径（四层优先：显式入参 > `GWEN_GAME_DB` > 插件配置 `config.json` 的 `db_path` > 旧路径默认）
#  ★ 归属：**库路径是宿主的平台职责**（宿主=平台件属主：库路径 / 单进程锁 / 存档半边取用口）。
#    **包（framework/games/<pkg>）只管玩法，不该知道文件系统路径** —— 换包 / 换数据集要能随便换。
#  ★ 2026-09-15 重启冒烟抓到：本行曾写成 `<插件根>/game_data.db`（少了 `game/` 一层）⇒ 终态宿主
#    另起了一个空库，而**生产库（794KB，玩家数据）在 `<插件根>/game/game_data.db`** ⇒ 表现是
#    「你还没有角色！」。137 个测试文件全绿 + 六条判据全过都照不出来 —— 只有真启动才暴露。
_LEGACY_DB_REL = os.path.join("game", "game_data.db")
DEFAULT_DB_PATH = os.path.join(PLUGIN_ROOT, _LEGACY_DB_REL)


def _cfg_db_path():
    """插件配置 `config.json` 的 `db_path`（相对路径按插件根解析）。取不到 → `None`。"""
    try:
        with open(os.path.join(PLUGIN_ROOT, "config.json"), encoding="utf-8") as fh:
            raw = str((json.load(fh) or {}).get("db_path") or "").strip()
    except (OSError, ValueError):
        return None
    if not raw:
        return None
    return raw if os.path.isabs(raw) else os.path.normpath(os.path.join(PLUGIN_ROOT, raw))


DB_PATH = (
    os.environ.get("GWEN_GAME_DB")
    or _cfg_db_path()
    or DEFAULT_DB_PATH
)


def db_path() -> str:
    """库路径句柄（包侧存档层要的那一个）。"""
    return DB_PATH


def clock() -> float:
    """时钟句柄（stdlib `time.time`，与旧工厂逐字相同）。"""
    return _time.time()


def _noop(*_a, **_k):
    return None


def flush_log(msg):
    """日志 sink 句柄：默认静默；宿主 logger 在册时记 DEBUG（与旧工厂逐字相同）。"""
    log_setup = sys.modules.get("data.plugins.dragonfall.host.log_setup") or \
        sys.modules.get("host.log_setup")
    getattr(getattr(log_setup, "LOG", None), "debug", _noop)(msg)


#: 发奖半边名（引擎包契约的**半边名**，不是包内模块路径字面量）
REWARD_HALF = "reward"


def _package_reward():
    """包内发奖真源（按**半边名** `reward` 经引擎包契约取）—— 取不到 → **抛**（fail-closed）。

    ★ P5F 前置⑦（去壳）：原实现 `from ..game import reward as _reward` 走待删壳
    `game/reward.py`（它是包内 `content/reward.py` 的别名壳，拿到的是同一只实现函数）。
    终态 `game/**` 删除后该 import 直接 ImportError ⇒ 改为按半边名向已绑定的引擎包取，
    宿主里**不出现任何包内模块路径字面量**（与 `host/tlog_setup.attach_tlog` 同口径）。
    """
    pkg = STORE.package
    if pkg is None:
        raise RuntimeError(
            "host.store_factory.grant_reward：引擎包未绑定（装配处应先 `bind_store(pkg)`）"
            "——拒绝静默取不到发奖实现")
    mod = pkg.optional_submodule(REWARD_HALF)
    fn = getattr(mod, "grant_reward", None) if mod is not None else None
    if not callable(fn):
        raise RuntimeError(
            "host.store_factory.grant_reward：包内半边 %r 取不到 grant_reward ——拒绝静默空跑"
            % (REWARD_HALF,))
    return fn


def grant_reward(*args, **kwargs):
    """发奖**能力口**（宿主侧句柄）—— 调用时才解析实现（避免 import 期成环 / 半初始化）。

    真源 = 包内半边 `reward`（`content/reward.py::grant_reward`）。解析不到 → **抛**（fail-closed）。
    """
    fn = _REWARD_IMPL[0]
    if fn is None:
        fn = _REWARD_IMPL[0] = _package_reward()
    return fn(*args, **kwargs)


#: 显式绑定的发奖实现（可选；测试 / 终态可先 `bind_reward(fn)` 再跑）
_REWARD_IMPL: list = [None]


def bind_reward(fn) -> None:
    """显式绑定发奖实现（可选；不给则 `grant_reward` 向引擎包按半边名 `reward` 取）。"""
    _REWARD_IMPL[0] = fn


def inject_handles(*, log=None, tlog=None, grant_reward_fn=None) -> dict:
    """宿主注入面（引擎 `inject`）：**四类句柄 + 发奖 + 流水挂载平台件**，键名以包侧 `bind_host(**inject)` 认的为准。"""
    from . import log_setup as _log_setup
    from . import tlog_setup as _tlog_setup
    return {
        "db_path": DB_PATH,
        "clock": _time.time,
        "log": log if log is not None else _log_setup.LOG,
        "tlog": tlog if tlog is not None else _tlog_setup,
        # ★ R5 缺口③：`attach_tlog` 平台件的终态落点 = `host/tlog_setup.py`（`host/**` 属主）；
        #   这里把它摆进宿主注入面，包内 `content.combat_cmds` / `content.bridge` 经
        #   `content.facade.bind_host` 扇出取到（接口表第 11 行冻结注入名）。
        "attach_tlog": _tlog_setup.attach_tlog,
        "grant_reward": grant_reward_fn if grant_reward_fn is not None else grant_reward,
    }


# ============================================================
# 存档半边取用口
# ============================================================
_IDENTITY_KEYS = ("group_id", "qq_id", "uid")   # 「谁是玩家」那几列由落库函数自己带


class HostStore:
    """宿主侧存档口（经引擎包契约取包内**存档半边**；不重写 SQL）。

    `half` 命名 = 包契约的「可选半边」口径（引擎 `Package.optional_submodule`）。宿主的
    `load_player/save_player` 两函数只做「取玩家档 / 交回玩家档」，形状是**普通 dict**
    （接缝纪律：不给包任何 ORM 对象 / 连接句柄）。
    """

    #: 存档半边名（包内 `content/<name>/` 或 `content/<name>.py`）
    HALF = "persistence"

    def __init__(self) -> None:
        self._pkg = None
        self._half = None

    # ---------- 装配 ----------
    def attach(self, package) -> "HostStore":
        """绑定引擎 `Package`（`boot()` 之后调一次；幂等）。"""
        self._pkg = package
        self._half = None
        return self

    @property
    def package(self):
        """当前绑定的引擎 `Package`（未绑定 → `None`）。

        ★ R5 缺口③：`host/tlog_setup.attach_tlog` 要按**半边名**取包内采集半边
        （`pkg.optional_submodule("tlog_collect")`）——宿主里不出现包名字面量，故需要一个
        公开的包取件口（`bind_store` 的对称面）。
        """
        return self._pkg

    def half(self):
        if self._half is None:
            mod = self._pkg.optional_submodule(self.HALF) if self._pkg is not None else None
            missing = [n for n in ("get_player", "update_player", "init_db", "lock", "connect")
                       if not callable(getattr(mod, n, None))]
            if mod is None or missing:
                raise RuntimeError(
                    "存档半边 content/%s 取不到（缺 %s）——宿主拒绝静默空跑；"
                    "请检查包是否声明了 bind 且宿主给的 db_path 已生效" % (self.HALF, missing))
            self._half = mod
        return self._half

    # ---------- 建表 / 连接 / 锁 ----------
    def init(self):
        """建表 + 迁移（幂等；`Main` 旧路径的 `db.init_db()` 同义）。"""
        return self.half().init_db()

    def lock(self):
        """单进程锁（= 包内引擎 `Database.lock` 的同一只 RLock）。"""
        return self.half().lock()

    def connect(self):
        """新连接（调用方负责关闭；一般配合 `with store.lock():`）。"""
        return self.half().connect()

    # ---------- 三函数里的 ②：读档 / 落档 ----------
    def load_player(self, group_id, uid):
        """读档（普通 dict | None）；`None` = 新玩家。"""
        return self.half().get_player(group_id, uid)

    def save_player(self, group_id, uid, data: dict) -> None:
        """落档（一条消息一次）：整档回写，剔掉身份列；非法字段 → 包内 `update_player` 当场抛。"""
        fields = {k: v for k, v in (data or {}).items() if k not in _IDENTITY_KEYS}
        if fields:
            self.half().update_player(group_id, uid, **fields)


#: 进程唯一存档口（`_identity` 的连接/锁取件也走它 —— 同一个库、同一只锁）
STORE = HostStore()


def store() -> HostStore:
    return STORE


def bind_store(package) -> HostStore:
    """把引擎 `Package` 交给存档口（宿主装配处调一次）。"""
    return STORE.attach(package)
