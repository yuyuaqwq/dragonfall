# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - exploration（v115 探索进度指令）

『探索进度』：按地图 region 聚合展示每域子区域探索进度 + 全大陆探索度。
由 Main 继承本 Mixin 使用；核心计算在 game/core/exploration.py（region_progress/overall_progress）。
"""
from ._platform import AstrMessageEvent, filter

from .. import content as C
from .. import db
from .base import CommandBase, require_player

SEP = "━━━━━━━━━━━━━━"


class ExplorationCmds(CommandBase):
    """v115 探索见闻：『探索进度』指令"""

    @filter.regex(r"^(?:\[At:\d+\]\s*)?探索进度(?:[\s\S]*)$")
    @require_player()
    async def explore_progress(self, event: AstrMessageEvent):
        group_id, qq_id = self._uid(event)

        regions = C.region_progress(qq_id)
        overall = C.overall_progress(qq_id)

        lines = [
            "🗺️ 探索进度",
            SEP,
        ]
        for r in regions:
            total = r["total"]
            visited = r["visited"]
            if total <= 0:
                continue
            pct = int(round(visited * 100.0 / total))
            if pct >= 100:
                mark = "🟢"
            elif pct >= 50:
                mark = "🟡"
            else:
                mark = "⚪"
            row = f"{mark} {r['region']}   {visited}/{total}"
            if r["hidden_total"] > 0:
                row += f"（隐藏 {r['hidden_found']}/{r['hidden_total']}）"
            lines.append(row)

        lines.append(SEP)
        lines.append(
            f"全大陆探索度 {overall['pct']}%（{overall['visited']}/{overall['total']}）"
        )
        lines.append(self._tip("explore"))

        yield event.plain_result("\n".join(lines))
