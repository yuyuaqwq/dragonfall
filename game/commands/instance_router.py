# -*- coding: utf-8 -*-
"""v181.N5b4-5a R1：副本战斗行动命令层 Router（saintess_engine 原生重写）—— ★ **B18-L5 薄壳**

实现正文已**整块进包**：`framework/games/orlandia/content/cmds_instance_router.py`
（`class InstanceRouterImpl`，类体 458 行逐字搬自本文件旧正文；只改「宿主取件」那一层）。
本文件只剩三件事：

    ① **包加载口**（本进程唯一，幂等）——`bootstrap.package_apply()`
    ② **再导出**：`InstanceRouterCmds`（类名沿用旧名，`tests/test_battle_n5b4_instance_router.py`
       等既存 import 点零改动）+ 模块常量 `INSTANCE_TIMEOUT`
    ③ **文案接线**：真源在包内（本文件零 `T.text/T.static`；门禁扫描根双侧，见文末注）

调用协议与搬包前**逐字一致**（`InstanceCmds` 的 MRO 组合不变：`InstanceImpl` + 本类 + `CommandBase`）：

    async for _r in self._instance_router(event, group_id, qq_id, player, st,
                                          action, skill_name, target):
        yield _r

`self` 侧玩法壳方法（`_instance_defeat` / `_instance_victory` / `_instance_kill_reward` /
`_instance_save` / `_instance_battle_footer` / `_instance_current_members` / `_instance_map_view` /
`_instance_elite_scale` / `_find_skill_cfg` / `_unlock_battle` / `_player` …）由宿主
`class InstanceCmds` 提供 —— 本类只作为 mixin 被组合，行为逐位等价。

宿主里**零 `T.text/T.static` 调用点**（B18 §3 验收线：`grep -c "T\\.text\\|T\\.static"` → 0）。
"""
from __future__ import annotations

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 本进程唯一包加载口（幂等；失败抛）

from content import cmds_instance_router as _IRI               # noqa: E402  包内实现（唯一真源）

# ---- 再导出（名字/签名与搬包前逐字一致：调用方零改动）----
InstanceRouterCmds = _IRI.InstanceRouterImpl                   # noqa: F401
INSTANCE_TIMEOUT = _IRI.INSTANCE_TIMEOUT                       # noqa: F401

# ---- 文案接线（**真源在包内，宿主不再登记**）----------------------------------------
# 本文件已零 `T.text/T.static` 调用点（渲染随实现整块进包）；
# `tests/test_texts_table.py::WIRED` 的「副本结算」域已同批扩到
# `[game/commands/instance_router.py, framework/.../content/cmds_instance_router.py]`
# 双侧扫描（与「周常 / 补给箱」同款口径），「声明 ↔ 调用点」双向对账仍成立。
