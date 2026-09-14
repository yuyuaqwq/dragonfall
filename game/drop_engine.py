# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - drop_engine.py（掉落统一引擎）—— ★ B12B13-TAIL 线3 **薄壳**（2026-09-14）

实现正文（v184 收口版 **495 行** = 池数据源 / 引用解析 / 专属策略 / 四入口 / 全量审计）已
**逐字搬进内容包** `content/loot.py`（正文 `def _randint` → EOF，除「宿主取件 4 行 + fish 守卫 1 行」
外一行未改；白名单门禁 `overnight/d3_loot_verify.py` A1 节，行为证据 `overnight/W-B12B13-L3.md`）。
本文件只剩四件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **注入宿主取件（三个「活源」thunk）** —— 真源里这三处本来就是**函数内惰性 import 宿主**，
     薄壳把那几行原文一字搬进 thunk，经 `install_*_source()` 挂进包内实现（取数时机不变）：

        `_host_pools_source()`   ← 真源 `_get_pools()`（:188-208）：本树 `data.drop_pools`
                                     已在 `sys.modules`（测试打桩 `_DP.DROP_POOLS`）则优先读它，
                                     否则落包内门面 `content.catalog_rules.DROP_POOLS`
        `_host_content_api()`    ← 真源函数内 `import game.content as C`（:67 / :445）
        `_host_quality_tiers()`  ← 真源 `_fish_tiers()`（:228-240）：先确保**本树**数据层装配
                                     （幂等），再取 `game/core/quality_tiers.FISH_TIERS`

     三个 thunk 都是**每次调用问一次**（= 真源「函数内 import」的时机）：`sys.modules` 里的
     桩、模块属性被换掉、档位表被替换，**全部照旧可见**（打桩语义 = 行为的一部分）。

  3. **模块别名**（`sys.modules[__name__] = 包内模块`）—— 与 `game/core/fishing.py` 同款。
     必要性（两条，都是测试依赖，不是形式）：
       · `tests/test_texts_table.py:1170` 直接 `_IL_DE.roll = lambda *a, **k: []` 打桩
         （补丁打在**模块对象**上）；别名后壳与实现是**同一个模块对象** → 补丁必然命中实现。
       · `tests/test_v184_loot_pools.py` 取 `DE._SimpleCtx` / `DE._TABLE` / `DE._roll_fish` /
         `DE.POOL_STRATEGIES`，并断言 `POOL_STRATEGIES["fish"] is DE._roll_fish`、
         `DE._SimpleCtx is EngineSimpleCtx` —— 别名是**同一对象**，同一性断言一字不改照样成立。
     引用链零改动：`game/services/profession.py:53`（`from ..drop_engine import expand_pool`）、
     `content/{fishing,instance_cmds,wild_king,profession}.py` 的 `_host_attr("drop_engine", …)`。

  4. **源码探针**：`tests/test_v184_loot_pools.py §6` 按源码查「旧实现已删 / 新接线到位」+
     AST 逐行比 —— 薄壳化后该门禁按「**壳 + 包内实现**」两侧拼接扫（与
     `tests/test_v184_loot_tiers.py:313 _src()` / `test_v135_bp_drop.py:197` 同款口径，
     判据只加强不削弱）；本文件因此**刻意不含**任何旧实现字面量（旧内联档位权重表函数名 /
     旧策略表的 `{` 字面量写法 —— 逐个拆开写，免得自己把自己扫红）。

⚠️ 本文件**不含** `TierTable` 的构造字面 —— `tests/test_v184_loot_tiers.py:671` 扫 `<插件>/game/**`
   要求全仓只有一处建档位表（唯一真相源 = 包内 `content/quality_tiers.py`）。
"""
import sys as _sys

from . import bootstrap as _bootstrap

_bootstrap.package_apply()                          # 包加载口（幂等；失败大声抛，不静默）
from content import loot as _impl                   # noqa: E402  包内实现（唯一真源）


# ============================================================
# ① 宿主取件：池数据源（真源 `_get_pools()` :188-208 原文搬运）
# ============================================================

def _host_pools_source():
    """等价真源 `_get_pools()`：宿主数据层若**已被本项目加载**则优先读它的 `DROP_POOLS`
    （`tests/test_v184_loot_pools.py:1089 _with_pools()` 直接替换 `_DP.DROP_POOLS` 造合成池
    —— 打桩要对实现可见），否则落包内门面。两路都不拉数据到 import 期（取数时机与 v174 同）。
    """
    _host = None
    if __package__:
        _host = _sys.modules.get(__package__ + ".data.drop_pools")
    _host = _host or _sys.modules.get("game.data.drop_pools")
    if _host is not None and hasattr(_host, "DROP_POOLS"):
        return _host.DROP_POOLS
    from content.catalog_rules import DROP_POOLS as _PKG_POOLS      # noqa: PLC0415
    return _PKG_POOLS


# ============================================================
# ② 宿主取件：内容 API（真源 `import game.content as C` 原文搬运）
# ============================================================

def _host_content_api():
    """等价真源函数内 `import game.content as C`（绝对导入，防循环/半初始化）。"""
    import game.content as C                                     # noqa: PLC0415
    return C


# ============================================================
# ③ 宿主取件：垂钓档位表（真源 `_fish_tiers()` :228-240 原文搬运）
# ============================================================

def _host_quality_tiers():
    """等价真源 `_fish_tiers()`：先确保**本树**数据层装配（幂等），再取档位表。"""
    try:
        from .core.quality_tiers import FISH_TIERS
    except ImportError:                          # 本树数据层尚未装配 → 先拉一次（幂等）
        from . import data as _data              # noqa: F401,PLC0415
        from .core.quality_tiers import FISH_TIERS
    return FISH_TIERS


# 挂进包内实现（幂等；三个活源都覆盖式安装 —— 与本树对应的那份宿主取件）
_impl.install_pools_source(_host_pools_source)
_impl.install_content_api_source(_host_content_api)
_impl.install_quality_tiers_source(_host_quality_tiers)

# ============================================================
# 模块别名：壳与实现同体（打桩 / 同一性断言 / 引用链全部照旧）
# ============================================================

_sys.modules[__name__] = _impl
