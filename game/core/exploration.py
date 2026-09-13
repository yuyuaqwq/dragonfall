# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - exploration（★ B13-L7 起 = 薄壳）

逻辑真源已进内容包：`content/exploration.py`（**逐字端口**；真源 = 本文件旧版 174 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入宿主句柄：`db`（存储层）+ `content`（`MATERIALS` / `resolve` / `display` ——
     材料表**未进包**，BRIEF §5 无同名域）→ 按完整模块名注入自己那棵树（plan §8-R2）
  3. 同名单 re-export + **两个取数适配器**

★ 两个取数适配器（薄壳真的在做「取数据」）：真源的 `region_progress(qq_id)` /
  `overall_progress(qq_id)` 内部自己读 `db.get_visited_subareas(qq_id)`；包内那份（B8.2 已定）
  签名是 `(visited)`（包内不读宿主 DB）——所以薄壳保持**对外签名一字不变**（调用方
  `C.region_progress(qq_id)` 零改动），把「读 visited」这一步留在宿主：

      region_progress(qq_id)  →  _pkg.region_progress(db.get_visited_subareas(qq_id))
      overall_progress(qq_id) →  _pkg.overall_progress(db.get_visited_subareas(qq_id))

消费点零改动：`game/core/__init__.py:116-119`（含协作契约名
`exploration_record_visit`）、`tests/test_v104_commands_system.py:185`
（`C.exploration_record_visit("g1","q4","oak_town","oak_town_2")`）。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import exploration as _pkg                      # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]
_pkg.bind_host(db=_pkg.lazy_host_module(_HERE_PKG + ".db"),
               content=_pkg.lazy_host_module(_HERE_PKG + ".content"))

# ---- 同名单 re-export（真源符号名一字不变）----
record_visit = _pkg.record_visit
exploration_record_visit = _pkg.record_visit        # v115 协作契约名（G 调用 C.exploration_record_visit）
_FIRST_VISIT_MAT_POOL = _pkg._FIRST_VISIT_MAT_POOL
C_resolve_material = _pkg.C_resolve_material
C_display_material = _pkg.C_display_material
C_material_price = _pkg.C_material_price


def _visited(qq_id):
    """真源 `db.get_visited_subareas(qq_id)`（函数内惰性取件，防循环导入）。"""
    from .. import db
    return db.get_visited_subareas(qq_id)


def region_progress(qq_id):
    """『探索进度』按地图 region 聚合（真源签名不变；visited 由本层读出）。"""
    return _pkg.region_progress(_visited(qq_id))


def overall_progress(qq_id):
    """全大陆探索度（真源签名不变；visited 由本层读出）。"""
    return _pkg.overall_progress(_visited(qq_id))
