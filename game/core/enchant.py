# -*- coding: utf-8 -*-
"""game/core/enchant.py —— B13-L1 **薄壳**（2026-09-14）

真源（**唯一实现**）已搬进内容包：`framework/games/orlandia/content/enchant.py`
（搬的边界 / 正文改动面 / 缺口全写在那边的头注里）。本文件只剩三件事：

  · **包加载口**：`bootstrap.package_apply()`（本进程唯一；幂等）
  · **全量再导出**：名字集合与改造前**逐名相同** → `game/core/__init__.py` 的
    `from .enchant import …`、别线模块的 `from .enchant import …`、测试的模块属性访问**零改动**
  · `__getattr__` / `__dir__` 兜底：未列名也转发包内实现

★ 一条**必须保留的行为细节**（不是巧合，是测试依赖）：`random` 之类的模块对象再导出后仍是
  **同一只 stdlib 模块对象**（包内 `import random` 的那只）——
  `tests/test_v136_gem_drops.py:67` 用 `mock.patch.object(game.core.gems.random, "random", …)`
  打宿主模块属性来钉随机序列，同一对象才让打点照旧命中包内实现。

改造前 46 行 → 现在 66 行（`enchant_value` / `enchant_match_material` 名字不变）。
"""
import sys                                             # noqa: F401（class_sets 的 _tree_mod 用）

from .. import bootstrap as _bootstrap                  # noqa: F401  本进程唯一包加载口（幂等）

_bootstrap.package_apply()

from content import enchant as _IMPL                      # noqa: E402  包内唯一实现


def _re_export():
    """把包内实现的名字（**同一个对象**：函数 / 字典 / 类 / 模块）挂到本模块。"""
    for _n in [n for n in dir(_IMPL) if not n.startswith("__")]:
        globals()[_n] = getattr(_IMPL, _n)


_re_export()
del _re_export


# 改造前**从 `..data` 导入**、因而挂在本模块上的表名（`from ..data import X` 的 X）——
# 常量表已随实现搬进包内，这些名字在本壳上用「惰性回退」补齐（读得到、写不到壳上）：
_LEGACY_DATA_NAMES = frozenset(["ENCHANT_RECIPES", "ENCHANT_MAX_VALUE"])
# 改造前**从别处宿主模块导入**的模块级名字（`from ..<mod> import X` 的 X）→ (宿主模块, 属性)
_LEGACY_HOST_NAMES = {"equip_stats": ("core.stats", "equip_stats")}


def _tree_mod(name):
    """**本棵树**的宿主子模块（只看 `sys.modules`，**绝不主动 import** ——
    防 `game.data → _assembly → core.<mod> → game.data` 的 EAGER 环）。"""
    root = (__package__ or "").rsplit(".core", 1)[0]
    return sys.modules.get("%s.%s" % (root, name)) if name else sys.modules.get(root)


def __getattr__(name):
    """未列名兜底：先转发包内实现；再回退到宿主 `data` 的同名表（= 改造前的导入名）。"""
    try:
        return getattr(_IMPL, name)
    except AttributeError:
        if name in _LEGACY_DATA_NAMES:
            return getattr(_tree_mod("data") or _IMPL._host_module("data"), name)
        if name in _LEGACY_HOST_NAMES:
            _m, _a = _LEGACY_HOST_NAMES[name]
            return getattr(_IMPL._host_module(_m), _a)
        raise


def __dir__():
    return sorted(set(globals()) | set(dir(_IMPL)))
