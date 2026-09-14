# -*- coding: utf-8 -*-
"""内容侧技能表读取 —— **宿主薄壳**（B12B13-TAIL 线 1，2026-09-14）。

实现已归内容包：`content/skills.py`（= 本文件旧版的**逐字端口**；包内 `content/apply.py`
`install_engine()` 把 `skill_up` / `skill_level_of` 挂到引擎 hook 面的就是它）。本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败**大声抛**）
  2. 同名单 re-export —— **公开/私有名与签名逐字保留**：`commands/instance_router.py`、
     `store/players.py`、`services/class_mech_proc.py`、`tests/test_commands_skills.py`、
     `tests/test_v112_smoke_regression.py` 等**全按名引用**；`C` / `skill_max_level` 是旧版
     `import` 带进来的残留名（保持面不丢）。
  3. `__getattr__`（PEP 562）：本模块**不**再抄一份惰性缓存（`_SKILL_KEY_INDEX` /
     `_SKILL_UP_NAME_INDEX` —— 由实现侧 `global` 改写，抄一份就是第二份真源）；按名转发到包内那份。

真源 = 本文件旧版 220 行（证据见 `overnight/W-B12B13-L1.md`）。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                       # 包根进 sys.path（失败抛，不静默）
from .. import content as C  # noqa: E402,F401   （原文 `from .. import content as C` 的残留名）
from content import skills as _impl  # noqa: E402
from content.skills import (  # noqa: E402,F401
    _br_table,
    _build_skill_key_index,
    _sk_table,
    _skill_up,
    _skill_up_name_index,
    branch_path_index,
    branch_skill_owner,
    is_skill_learned,
    skill_by_key,
    skill_info,
    skill_level_of,
    skill_max_level,
    skill_owner_cls,
    skill_upgrade_cost,
    skills_for_level,
)


def __getattr__(name):
    """PEP 562：未列名的符号（含会被实现侧改写的惰性缓存）按名转发 —— 不留第二份。"""
    return getattr(_impl, name)
