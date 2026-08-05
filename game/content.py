# -*- coding: utf-8 -*-
"""《剑与魔法》内容库 —— 薄聚合层（重构后）

数据层 → game/data/（纯静态表）
核心层 → game/core/（生成逻辑）
本文件保留 `import game.content as C` 兼容路径，全部符号聚合自上下两层。
"""
import random  # noqa: F401

from .data import *  # noqa: F401,F403
from .core import *  # noqa: F401,F403
from .data import _INDEXES  # noqa: F401
from .core import pinyin_id, build_index, resolve, display  # noqa: F401
