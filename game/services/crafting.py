# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - crafting.py（★ B12 L5 起 = 薄壳）

逻辑真源已进内容包：`content/crafting.py`（逐字端口，真源 = 本文件旧版 86 行；
生成器 `overnight/w1213_l5_gen.py` 可重算出包内正文）。本文件只做三件事：

  1. 装配序保证：先引宿主 `content`（`bootstrap.load_engine_config` 口径：**先引 game.content，
     再加载包**；原真源模块级 `from .. import content as C` 的等价位置）
  2. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  3. **同名单 re-export** —— 保持模块路径与符号名不变：
       `game/services/__init__.py:33`（5 个名字）
       `game/commands/economy.py:28`（`from ..services import crafting as _craft_svc`
         → `content/economy_host.py` 的 `_craft_svc` 键 → 包内 `content/economy_cmds.py`
         的 enhance 命令调用 `compute_enhance_rate` / `enhance_fail_floor` / 三个石料常量）
       `tests/test_services_crafting.py`

**本模块零宿主面**（无 `bind_host`、无宿主表读取）：真源唯一的读点 `C.ENHANCE_FAIL_DROP`
已按 I1 切到包内常量域读口 `content/config.py`（`rules/game_config.json` 的 `enhance` 组，
int 键已还原），见包内模块头注。逐字节等价证据：`overnight/w1213_l5_snap.py`
（20 例 · 私有库全表 dump · sha256 对拍，含 `compute_enhance_rate` 12 组叠加组合与
`enhance_fail_floor` 全等级档）；读口等值证据：`overnight/w1213_l5_check.py`【⑤】。
"""

from __future__ import annotations

from .. import bootstrap as _bootstrap
from .. import content as _host_content  # noqa: F401  （装配序；见头注第 1 条）

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
from content import crafting as _pkg                # noqa: E402

# ---- 同名单 re-export（逐字沿用真源符号名）----
ENHANCE_STONE_REFINE = _pkg.ENHANCE_STONE_REFINE
ENHANCE_STONE_BLESSED = _pkg.ENHANCE_STONE_BLESSED
ENHANCE_STONE_PROTECT = _pkg.ENHANCE_STONE_PROTECT
compute_enhance_rate = _pkg.compute_enhance_rate
enhance_fail_floor = _pkg.enhance_fail_floor
