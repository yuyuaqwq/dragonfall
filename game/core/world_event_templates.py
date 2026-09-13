# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - world_event_templates.py（★ B13-L3 起 = 薄壳）

实现真源已进内容包：`content/world_event_templates.py`（`DISPLAYS` 6 个展示函数 +
`INITIALIZERS` 2 个初始化函数 + `register` / `register_init` 逐字端口；搬的边界 / 正文改动面
/ 缺口全写在那边的头注里）。本文件只剩三件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **同名单 re-export**：`game/commands/social.py:776/:810` 的
     `from ..core.world_event_templates import INITIALIZERS / DISPLAYS` 零改动
  3. `__getattr__` / `__dir__` 兜底

★ 宿主替身注入：**不需要**（`content` 聚合层由包内按 `sys.modules` 惰性解析；
  core 模块级 `from .. import content` 会撞 §8-R1 导入环，故本文件不 import 它）。

改造前 121 行 → 现在 37 行。等价证据：`overnight/w1213_b13l3_snap.py`（B1–B8 共 11 例）
· `overnight/W-B13-L3-events-dialogue.md`。
"""
from .. import bootstrap as _bootstrap                          # noqa: F401

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等）

from content import world_event_templates as _IMPL              # noqa: E402  包内唯一实现

# ---- 同名单 re-export（真源符号名一字不变；字典 / 装饰器是**同一个对象**）----
DISPLAYS = _IMPL.DISPLAYS
register = _IMPL.register
INITIALIZERS = _IMPL.INITIALIZERS
register_init = _IMPL.register_init

# 包内实现里**不外露**的宿主替身 / 私有工具名
_HANDLES = frozenset(("C", "bind_host", "_INJECTED", "_HOST_PKG", "_HOST_PKG_FALLBACK",
                      "_host_module", "_HostMod"))


def __getattr__(name):
    """未列名兜底：转发包内实现（`_d_*` / `_i_*`），宿主替身名一律不外露。"""
    if name in _HANDLES or name.startswith("__"):
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    return getattr(_IMPL, name)


def __dir__():
    return sorted((set(globals()) | set(dir(_IMPL))) - set(_HANDLES))
