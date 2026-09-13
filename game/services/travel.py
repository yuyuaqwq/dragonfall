# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - travel.py（★ B9 L5 起 = 薄壳）

逻辑真源已进内容包：`content/travel.py`（逐字端口，真源 = 本文件旧版 374 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：
       `db`  —— 存储层（真源 函数体内 `from .. import db # 惰性导入`）
       `c`   —— 内容聚合层 `game.content`（**只喂未进包的符号**：地图几何 `map_entry_subarea` /
               `map_center` / `map_route` / `subarea_links`、类型常量 `MAP_TYPE_*`、
               常量表 `LEGACY_MAP_ALIAS` / `HIDDEN_MAP_UNLOCK`、隐藏房判定 `is_hidden_room` /
               `reveal_met` / `reveal_progress`、生成器 `build_monster` / `mount_effects`）
       理由逐条见包内模块 docstring 的「逐符号归属表」——地图几何与隐藏房判定读的是**运行时态**
       `SUBAREAS`（副本大陆克隆会就地增补房间），包内是按静态域文件重建 ⇒ 这两类**必须**走宿主。
  3. **同名单 re-export** —— 保持模块路径与符号名不变，`commands/world.py` 的 14 个调用点
     与 `game/services/__init__.py:64` 的 20 个聚合名零改动。

包内自带的域数据（本批新增 / 复用）：
    `content/data/portals.json`  ← 本线新域 `portals`（真源 `game/data/portals.py:4 PORTALS`，11 条）
                                   导出器 `scripts/export_domains/b9_quests_travel.py:derive_portals`
    `content/data/{worlds,subareas,maps}.json` → 包内重建宿主 `MAPS`/`MAP_BY_ID`
                                   （逐条 deep-equal 121/121，见 `overnight/_b9l5_maps_probe.py`）
"""

from __future__ import annotations

import importlib

from .. import bootstrap as _bootstrap
from .. import content as _host_content
from .. import db as _db

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
_pkg = importlib.import_module("content.travel")

_pkg.bind_host(db=_db, c=_host_content)             # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
AMBUSH_HIGH_MIN = _pkg.AMBUSH_HIGH_MIN
AMBUSH_HIGH_STEP = _pkg.AMBUSH_HIGH_STEP
AMBUSH_HIGH_CAP = _pkg.AMBUSH_HIGH_CAP
AMBUSH_MID = _pkg.AMBUSH_MID
AMBUSH_LOW = _pkg.AMBUSH_LOW

visible_sas = _pkg.visible_sas
conn_target = _pkg.conn_target
conn_subarea_name = _pkg.conn_subarea_name
subarea_hidden_block = _pkg.subarea_hidden_block
resolve_map_target = _pkg.resolve_map_target
move_blocked_msg = _pkg.move_blocked_msg
leave_map_block_msg = _pkg.leave_map_block_msg
level_warn = _pkg.level_warn
stamina_max = _pkg.stamina_max
stamina_tired_line = _pkg.stamina_tired_line
move_stamina_cost = _pkg.move_stamina_cost
travel_ambush = _pkg.travel_ambush
hidden_map_block = _pkg.hidden_map_block
landing_subarea = _pkg.landing_subarea
portal_arrive_note = _pkg.portal_arrive_note
