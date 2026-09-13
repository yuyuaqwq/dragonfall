# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - hidden_cond.py（★ B13-L3 起 = 薄壳）

实现真源已进内容包：`content/hidden_cond.py`（`ENV_KEYWORDS` / `CONDITIONS` / `register` /
`HiddenCtx` / `envs_of` / 6 个条件函数 / `check_cond` **逐字全搬，零改动面** ——
是 B13 线3 六个模块里唯一「一搬就完事」的一个）。本文件只剩三件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **同名单 re-export**：
     · `tests/test_v98_03_registry.py:37`（`HC.ENV_KEYWORDS` / `HC.register` / `HC.envs_of` /
       `HC.check_cond` —— 要求**同一批对象**：本文件与包内共享同一个 `ENV_KEYWORDS` / `CONDITIONS` ✅）
     · `content/combat_cmds.py:915`（B10 线5 产物）仍经宿主薄壳解析
       `_host_attrs("core.hidden_cond", "envs_of", "check_cond", "HiddenCtx")` —— 名字面一致即可
       （**待收口**：该调用点可改为 `from .hidden_cond import …`，见报告「未做与缺口」）
  3. `__getattr__` / `__dir__` 兜底（6 个 `_c_*` 条件函数不逐个列）

改造前 86 行 → 现在 35 行。等价证据：`overnight/w1213_b13l3_snap.py`（E4–E9：关键词表 /
6 图位图 / 全 cond × 上下文矩阵 / 未知 cond 按 any / 注册即生效 + 可撤销）
· `overnight/W-B13-L3-events-dialogue.md`。
"""
from .. import bootstrap as _bootstrap                          # noqa: F401

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等）

from content import hidden_cond as _IMPL                        # noqa: E402  包内唯一实现

# ---- 同名单 re-export（真源符号名一字不变；两张表是**同一个对象**）----
ENV_KEYWORDS = _IMPL.ENV_KEYWORDS
CONDITIONS = _IMPL.CONDITIONS
register = _IMPL.register
HiddenCtx = _IMPL.HiddenCtx
envs_of = _IMPL.envs_of
check_cond = _IMPL.check_cond


def __getattr__(name):
    """未列名兜底：转发包内实现（6 个 `_c_*` 条件函数）。"""
    if name.startswith("__"):
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    return getattr(_IMPL, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_IMPL)))
