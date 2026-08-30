# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - position.py（v141 大陆隔离）

玩家位置结构体：world_id + map_id + subarea_id 三元组，取代散落的裸字符串
cur_map / cur_subarea 约定。主大陆 = "mainland"，副本 = "inst:<uuid>"。

设计目标（docs/CONTINENT_ISOLATION_v141.md §2.1）：
- 位置 = 唯一真相源，新增字段/行为只在 Position 一处加
- 所有地图解析走 resolve_map() 唯一入口（主大陆 → MAP_BY_ID；副本 → 克隆大陆）
- 旧存档 world_id 缺省 = "mainland" → 零迁移成本
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .worlds import InstanceWorld


class Position:
    """玩家位置。大陆 id + 地图 id + 子区域 id 三元组。"""

    __slots__ = ("world_id", "map_id", "subarea_id")

    def __init__(self, world_id: str, map_id: str, subarea_id: str = ""):
        self.world_id = world_id or "mainland"
        self.map_id = map_id
        self.subarea_id = subarea_id

    # ---- 构造 ----

    @classmethod
    def from_player(cls, player: dict) -> "Position":
        """从玩家存档解析位置。world_id 缺省 = 主大陆（兼容旧存档）。"""
        w = player.get("world_id") or "mainland"
        return cls(w, player.get("cur_map", "") or "", player.get("cur_subarea", "") or "")

    @classmethod
    def from_db(cls, world_id: Optional[str], map_id: str, subarea_id: str = "") -> "Position":
        """从数据库行/字段构造。world_id 缺省 = 主大陆。"""
        return cls(world_id or "mainland", map_id or "", subarea_id or "")

    # ---- 序列化 ----

    def key(self) -> str:
        """落库键：'mainland:goblin_camp:goblin_camp_1'"""
        return f"{self.world_id}:{self.map_id}:{self.subarea_id}"

    def to_db(self) -> tuple:
        """(cur_map, cur_subarea, world_id) —— 兼容 update_player 调用"""
        return self.map_id, self.subarea_id, self.world_id

    # ---- 判定 ----

    def is_instance(self) -> bool:
        """是否在副本大陆实例里。"""
        return self.world_id.startswith("inst:")

    def is_mainland(self) -> bool:
        """是否在主大陆。"""
        return self.world_id == "mainland"

    # ---- 解析 ----

    def resolve_map(self) -> Optional[dict]:
        """按世界解析地图 dict——唯一入口，替换全游戏 C.MAP_BY_ID.get(map_id)。

        主大陆 → 全局 MAP_BY_ID；副本实例 → instance_worlds[world_id].maps。
        找不到返回 None（调用方自行兜底，与原 C.MAP_BY_ID.get 语义一致）。
        """
        if self.is_instance():
            from .worlds import get_instance_world
            inst = get_instance_world(self.world_id)
            if inst is None:
                return None
            return inst.get("maps", {}).get(self.map_id)
        from ..data import MAP_BY_ID
        return MAP_BY_ID.get(self.map_id)

    def resolve_subareas(self) -> list:
        """当前地图的子区域列表（按世界解析）。"""
        if self.is_instance():
            from .worlds import get_instance_world
            inst = get_instance_world(self.world_id)
            if inst is None:
                return []
            return inst.get("subareas", {}).get(self.map_id, [])
        from ..data import SUBAREAS
        return SUBAREAS.get(self.map_id, [])

    # ---- 复制 ----

    def with_map(self, map_id: str, subarea_id: str = "") -> "Position":
        """同世界换地图（用于移动落点）。"""
        return Position(self.world_id, map_id, subarea_id or self.subarea_id)

    def with_subarea(self, subarea_id: str) -> "Position":
        """同世界同地图换子区域。"""
        return Position(self.world_id, self.map_id, subarea_id)

    def as_mainland(self) -> "Position":
        """回到主大陆（位置字段保留，world_id 重置）。"""
        return Position("mainland", self.map_id, self.subarea_id)

    # ---- 展示 ----

    def __repr__(self):
        return f"<Position {self.world_id}:{self.map_id}:{self.subarea_id}>"


# ============================================================
# 适配层（v141 Phase 1：零行为变更）
# ------------------------------------------------------------
# 命令层新增代码统一走以下入口；旧代码不动（读到的还是主大陆结果，
# 因为默认 world=mainland）。热路径替换在 Phase 2 逐步进行。
# ============================================================


def cur_map_obj(player: dict) -> Optional[dict]:
    """按玩家位置解析当前地图 dict（唯一入口）。"""
    return Position.from_player(player).resolve_map()


def cur_subareas(player: dict) -> list:
    """当前地图的子区域列表（按世界解析）。"""
    return Position.from_player(player).resolve_subareas()


def player_position(player: dict) -> Position:
    """快捷：从玩家存档取 Position（适配层统一入口）。"""
    return Position.from_player(player)


def position_to_db(pos: Position) -> dict:
    """把 Position 转成 update_player 字段 dict（Phase 3 用）。"""
    return {
        "cur_map": pos.map_id,
        "cur_subarea": pos.subarea_id,
        "world_id": pos.world_id,
    }
