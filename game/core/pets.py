# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - pets（★ B13-L7 起 = 薄壳）

真源 `game/core/pets.py`（9 行）**本身没有实现** —— 它是一行 re-export：
    `from ..data.pets import PET_POOL, PET_EGG_ROLL, PET_MAX_LEVEL, make_pet_egg, …`
所以本文件（薄壳）+ 包内 `content/pets.py`（同名读口）合起来 = 把「re-export 面」搬进包：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入宿主句柄：`data.pets`（宿主 `game/data/pets.py` —— 数据层真源，B14 迁；
     包内 `content/data/pets.json` 是它的导出投影）→ 按完整模块名注入自己那棵树
  3. `__getattr__` **惰性同名转发**（PEP 562）：11 个名字一个字不改，取值时解析
     （不在 import 期解析，避免 `core/__init__` 早于 `game.data.pets` 加载时炸）

消费点零改动：`game/core/__init__.py:114`（9 个符号的 `from .pets import …`）。

缺口：`pets` 的**实现**仍在宿主 `game/data/pets.py`（数据层，B14 随表一起迁进
`content/pets.py`；届时改成读 `content/data/pets.json`）。本线不抄一份 = 不留双源。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import pets as _pkg                             # noqa: E402
from content.pets import lazy_module as _lazy_module  # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]
_pkg.bind_host(pets=_lazy_module(_HERE_PKG + ".data.pets"))


def __getattr__(name):
    """惰性同名转发（真源符号名一字不变）——`from .pets import make_pet_egg` 照旧可用。"""
    return getattr(_pkg, name)


# 真源 re-export 的 11 个名字（供静态检查/文档用；取值仍走上面的惰性转发）
__all__ = [
    "PET_POOL", "PET_EGG_ROLL", "PET_MAX_LEVEL",
    "make_pet_egg", "pet_exp_need", "pet_exp_mult", "pet_skill_label",
    "pet_quality_label", "pet_line", "pet_exp_bonus", "pct_str",
]
