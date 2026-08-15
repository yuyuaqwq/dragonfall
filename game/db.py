# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年存储层 —— 薄聚合层（重构后）

实际实现已拆至 game/store/（Repository 分层）。
本文件保留 `from .game import db` / `db.xxx` 兼容路径。
"""
from .store import *  # noqa: F401,F403
from .store import DB_PATH, C_MAP_IDS, _connect, _lock, init_db  # noqa: F401
