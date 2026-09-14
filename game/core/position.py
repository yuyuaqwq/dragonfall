# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - position（★ B13-L7 起 = 薄壳）

逻辑真源已进内容包：`content/position.py`（**逐字端口**；真源 = 本文件旧版 140 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入宿主句柄：`data`（`MAP_BY_ID` / `SUBAREAS`）+ `core.worlds`（副本大陆实例
     `get_instance_world` —— **B13-L2 那条线在搬**，本线不许直接 import 别线在搬的模块：
     会瞬时 `ImportError`）→ **按完整模块名注入自己那棵树**（plan §8-R2）
  3. 同名单 re-export（5 个符号）

消费点零改动：`game/core/__init__.py:126-129`（`C.Position / C.cur_map_obj / C.cur_subareas /
C.player_position / C.position_to_db`）、`tests/test_v141_instance_world.py:228`
（`C.Position.from_player(...)`）。

★ 为什么 `MAP_BY_ID` / `SUBAREAS` **没有**切包内 maps/subareas 域（实测依据，见包内头注）：
  `MAP_BY_ID` 无同名域、且值 = MAPS 条目**含装配期注入的 `subareas` 键**（`_assembly.py:137`），
  而包内 `worlds` 域有意剔除该键（宿主 15+ 处消费点读 `map["subareas"]`）；`SUBAREAS` 虽有等价
  域，但本模块把**行对象本身**抛给调用方（对象身份/就地改写语义不可保证）→ 缺口登记给 B14。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import position as _pkg                         # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]
_pkg.bind_host(**{
    "data": _pkg.lazy_module(_HERE_PKG + ".data"),
    "core.worlds": _pkg.lazy_module(_HERE_PKG + ".core.worlds"),   # 待 B13-L2 落地后切包内直取
})

# ---- 同名单 re-export（真源符号名一字不变）----
Position = _pkg.Position
cur_map_obj = _pkg.cur_map_obj
cur_subareas = _pkg.cur_subareas
player_position = _pkg.player_position
position_to_db = _pkg.position_to_db
