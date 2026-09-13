# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - exploration（『探索进度』）—— B8.2 **薄壳**

命令层只做四件事：**注册 / 解析参数 / 取玩家 / 调包 / 拼文案**。聚合逻辑与表全归内容包。

真源与包内的分工（B8.2 线2，2026-09-13）
========================================
    区域聚合（曾经 `game/core/exploration.py:96 region_progress` / `:137 overall_progress`）
        → 包内 `content/exploration.py`（`region_progress(visited)` / `overall_progress(visited)`），
          数据 = `content/data/exploration.json`（628 个探索点：`地图id:子区域id` → region/hidden/order
          + 首访材料池 `_config`）—— 导出见 `scripts/export_domains/collection_exploration.py` ②
    到访状态（宿主存储） 仍在本文件：`db.get_visited_subareas(qq_id)` → 键集合交给包
        （包内不读宿主 DB：与 `content/bridge.py` 同款替身接口）
    渲染文案             全在本文件（一个字都没动）

包加载口 = `game.bootstrap.package_apply()`（**本进程唯一**，幂等；失败大声抛，不静默降级）。
"""
from ._platform import AstrMessageEvent

from ._declared import declared

from .. import db
from .base import CommandBase, require_player

SEP = "━━━━━━━━━━━━━━"

_EX = None


def _ex():
    """包内 `content.exploration`（探索进度聚合）。

    惰性 import（模块级 import 包内模块会赶在 `package_apply()` 之前 —— 那时包根还没进 `sys.path`）。
    """
    global _EX
    if _EX is None:
        import importlib

        from .. import bootstrap
        bootstrap.package_apply()                       # 幂等；失败抛（不静默留空表）
        _EX = importlib.import_module("content.exploration")
    return _EX


class ExplorationCmds(CommandBase):
    """v115 探索见闻：『探索进度』指令"""

    @declared("explore_progress")
    @require_player()
    async def explore_progress(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)

        ex = _ex()
        visited = db.get_visited_subareas(qq_id)        # 宿主到访表（键 = "地图:子区域"）
        regions = ex.region_progress(visited)
        overall = ex.overall_progress(visited)

        lines = [
            "🗺️ 探索进度",
            SEP,
        ]
        for r in regions:
            total = r["total"]
            visited_n = r["visited"]
            if total <= 0:
                continue
            pct = int(round(visited_n * 100.0 / total))
            if pct >= 100:
                mark = "🟢"
            elif pct >= 50:
                mark = "🟡"
            else:
                mark = "⚪"
            row = f"{mark} {r['region']}   {visited_n}/{total}"
            if r["hidden_total"] > 0:
                row += f"（隐藏 {r['hidden_found']}/{r['hidden_total']}）"
            lines.append(row)

        lines.append(SEP)
        lines.append(
            f"全大陆探索度 {overall['pct']}%（{overall['visited']}/{overall['total']}）"
        )
        lines.append(self._tip("explore"))

        yield event.plain_result("\n".join(lines))
