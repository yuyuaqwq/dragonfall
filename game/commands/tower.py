# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - tower（v169.2 修炼爬塔 Lv70+）★ B18 终态：**一行转发**

『爬塔』的**等级门槛 / 战斗中拦截 / 目标层解析 / 每日上限 / 同层幂等 / 塔卫构造 / 开战面板渲染
全在包内**（`content/cmds_tower.py` 登记进 `content/commands.py::COMMANDS`）。本模块只剩注册
（`@declared("tower_cmd")`）+ 一行转发（`_BRIDGE.run(self, "tower_cmd", event)`）。

宿主侧只剩两件「必须认识活人世界」的事（包内经 `env.state["shell"]` 取可选能力）：
  · `_open_tower_battle`（`Battle` + `battle_bridge` 装配序列 + `db.save_battle` + 单进程锁 +
    阵型面板）—— 返回「插到第 4 行后的串」，无/抛错 → `None`（与真源 try/except 同效）；
  · `_in_any_battle`（战斗中拦截判定）。
两者都是宿主壳对象上的方法，桥接层只做透传（零游戏知识）。形状真源 =
`overnight/B18_TERMINAL_SHAPE.md` §1.3；行为逐字节不变，证据 = `overnight/W-B18-样板.md`。
"""
from ._platform import AstrMessageEvent

from . import _host_bridge as _BRIDGE
from ._declared import declared

from .. import db
from ..commands.base import CommandBase


class TowerCmds(CommandBase):
    """修炼爬塔：Lv70+ 单人守关挑战（★ B18 终态：注册 + 一行转发）"""

    @declared("tower_cmd")
    async def tower_cmd(self, event: AstrMessageEvent):
        yield event.plain_result(_BRIDGE.run(self, "tower_cmd", event))

    # ---------------- 宿主能力（包内经 env.state["shell"] 调用）----------------
    def _open_tower_battle(self, group_id, qq_id, player, guard):
        """开战装配（本线不搬）：装配序列 + 落库 + 单进程锁 + 阵型面板；
        返回「插到第 4 行后的串」，无阵型面板/面板抛错 → None（真源 try/except 同效）。"""
        from ..services import battle_bridge as BR
        tb = self._title_bonus(group_id, qq_id)
        BR.prepare_player_for_battle(player, tb, db)
        _sides = BR.build_sides(player=player, enemies=[guard])
        for _a in _sides.get("player", []):
            # 装备词条 + 职业机制 + 外部增幅容器（序列收敛于 BR.apply_battle_loadout）
            BR.apply_battle_loadout(_a, tb)
        from saintess_engine import Battle as B2
        b = B2("monster", sides=_sides, title_bonus=tb, pet=db.pet_get(qq_id))
        db.save_battle(group_id, qq_id, b.to_state())
        _lock = getattr(self, "_lock_battle", None)
        if _lock:
            try:
                _lock(group_id, qq_id)
            except Exception:
                pass
        try:
            _fp = getattr(self, "_battle_formation_panel", None)
            if _fp:
                return _fp(player, b) + "\n"
        except Exception:
            pass
        return None
