# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - maps（★ B13-L7 起 = 薄壳）

逻辑真源已进内容包：`content/maps.py`（**逐字端口**；真源 = 本文件旧版 229 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身（`data` / `db`）——**按完整模块名注入自己那棵树**（同进程并存
     `game.*` 与 `data.plugins.dragonfall.game.*` 两套模块树，plan §8-R2）
  3. **同名单 re-export**（13 个符号，名字/签名一字不变；`game/core/__init__.py:53/:106-112`
     与 `game/data/_assembly.py:90` 的 import 点零改动）

★ 时机不变式：`_build_monster_locs()` 仍在**本模块 import 期**调用一次（原实现的位置）。
   实测这条不能省：本模块在 `game/data/_assembly.py:9`（`..core.index`）→ `game/core/__init__.py:53`
   这一链上被 import，而网状房间 `EXTRA_SUBAREAS` 的并入在 `_assembly.py:97` —— 所以
   `MONSTER_LOCS` 是**并入前**的 SUBAREAS 算出来的（实测 343 条，≠ 用最终 628 条现算：
   2 个怪缺失、174 个怪的地点列表不同）。换源/换时机 = 改行为，见包内头注「未切包内的读点」。

★ 两个**故意留宿主**的装配钩子（不是遗漏）：`_build_ency` / `build_monster_locs` 的输入输出
   全走宿主 `data` 句柄 —— `MAPS` 迭代序不可逆（域外层键是字典序）+ 装配时机敏感 +
   `ENCY_*`/`MONSTER_LOCS` 无同名域（`editor/domains.json` 无此名）。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import maps as _M                               # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]                    # "game" / "data.plugins.dragonfall.game"
_M.bind_host(data=_M.lazy_host_module(_HERE_PKG + ".data"),
             db=_M.lazy_host_module(_HERE_PKG + ".db"))

# ---- 同名单 re-export（真源符号名一字不变）----
_build_ency = _M.build_ency
_build_monster_locs = _M.build_monster_locs
map_space = _M.map_space
map_center = _M.map_center
map_route = _M.map_route
subarea_links = _M.subarea_links
map_exit_subarea = _M.map_exit_subarea
map_entry_subarea = _M.map_entry_subarea
subarea_depth = _M.subarea_depth
is_hidden_room = _M.is_hidden_room
reveal_met = _M.reveal_met
reveal_progress = _M.reveal_progress
bump_explore_count = _M.bump_explore_count

_build_monster_locs()        # 与原实现同一时机（本模块 import 期填充宿主 MONSTER_LOCS）
