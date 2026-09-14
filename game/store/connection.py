# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年存储层 - connection：**委托薄壳 + 句柄转发**（B17 存档层归包）。

实现（DDL 四段 / 老库补列 / 地图 id 集合 / 连接骨架）已归内容包：
  · 表结构 + 迁移器 + `C_MAP_IDS` → `content/persistence/schema.py`
  · 连接/锁/事务/时钟/日志 sink 注入面 → `content/persistence/handles.py`
本文件只剩两件事：把工厂注入的句柄**原名转发**出来（`with store.connection._lock:` 等调用点不动），
外加「库路径 `DB_PATH`」这一条部署面。**零 SQL、零业务分支**。

落在包外的 1 个私有名：`_C_MAP_IDS_CACHE`（模块私有可变缓存，全仓 0 处外部读取 —— 见 W-B17.md §7）。
"""
import os  # noqa: F401    （旧模块级面保留）
from saintess_engine.store import Database, ensure_columns  # noqa: F401

from .store_factory import DB_PATH  # noqa: F401    （工厂已在此完成句柄注入）
from content.persistence import handles as _h
from content.persistence.handles import (  # noqa: F401
    C, atomic, init_db, _connect,
)
from content.persistence.schema import (  # noqa: F401
    _map_ids, C_MAP_IDS, _ensure_legacy_columns,
    _SQL_CORE_TABLES, _SQL_SOCIAL_TABLES, _SQL_PROF_TABLES, _SQL_IDENTITY_TABLES,
)

_db = _h.get_db()      # 引擎连接骨架（与包内实现**同一个对象**）
_lock = _h.lock()      # 真 RLock（`with db._lock:` 的消费端语义不变）
del _h                 # 薄壳不留多余模块名（`dir(store.connection)` 面 = 改造前面 -`_C_MAP_IDS_CACHE`）
