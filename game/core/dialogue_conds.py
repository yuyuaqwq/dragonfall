# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - dialogue_conds.py ★ B13-L3 起 = 薄壳

实现真源已进内容包：`content/dialogue_conds.py`（`CONDITIONS` / `register` / `_quest_state` /
18 个条件函数逐字端口；两处宿主取件改造见那边头注）。本文件只剩三件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **同名单 re-export**：`tests/test_v98_03_registry.py:34`
     （`from ...game.core import dialogue_conds as DC` → `DC.register` / `DC.CONDITIONS`）零改动
  3. `__getattr__` / `__dir__` 兜底（18 个 `_c_*` 条件函数不逐个列）

★ 注意：`content/dialogue.py`（同线）现在**直接** `from .dialogue_conds import CONDITIONS`
  （包内直取），不再经本薄壳 —— 本文件的存在只为宿主侧 import 面（测试 / 工具）。
  **注册表是同一个 dict 对象**：本文件写 `DC.register(...)` 与包内实现共享生效
  （`tests/test_v98_03_registry.py:40-46` 注册即生效断言照旧）。

★ 宿主替身注入：**不需要**（本线实现零宿主依赖：主线表走包内 `quests` 域、`CLASS_NOVICE`
  走 `content/tables.py`）。

改造前 210 行 → 现在 33 行。等价证据：`overnight/w1213_b13l3_snap.py`（E1–E3 + D3/D3b 真值矩阵）
· `overnight/W-B13-L3-events-dialogue.md`。
"""
from .. import bootstrap as _bootstrap                          # noqa: F401

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等）

from content import dialogue_conds as _IMPL                     # noqa: E402  包内唯一实现

# ---- 同名单 re-export（真源符号名一字不变；`CONDITIONS` 是同一个字典对象）----
CONDITIONS = _IMPL.CONDITIONS
register = _IMPL.register
_quest_state = _IMPL._quest_state

# 包内实现里**不外露**的私有工具名（真源本模块也没有这些名字）
_HANDLES = frozenset(("CLASS_NOVICE", "_read_domain", "_main_quests", "_MAIN_QUESTS", "_HERE"))


def __getattr__(name):
    """未列名兜底：转发包内实现（18 个 `_c_*` 条件函数）；私有工具名不外露。"""
    if name in _HANDLES or name.startswith("__"):
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    return getattr(_IMPL, name)


def __dir__():
    return sorted((set(globals()) | set(dir(_IMPL))) - set(_HANDLES))
