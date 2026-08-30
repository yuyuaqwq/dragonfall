# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - worlds.py（v141 大陆隔离）

大陆（world）抽象：
- 主大陆 "mainland" = 全游戏静态地图共享（MAP_BY_ID）
- 副本大陆 "inst:<uuid>" = 开本时动态创建/销毁的独立大陆实例
  克隆副本地图为独立地图集，副本进度（rooms/resources_pool/队伍快照）
  挂在大陆实例上，不再挂在队长个人 battle_state 行。

存储：
- 内存态 instance_worlds（运行时读写快）
- 落库 event_state key = "instance_world_{world_id}"（重启防丢，
  惰性重建——首次访问时从 DB 恢复）

设计目标（docs/CONTINENT_ISOLATION_v141.md §2.3/§2.4）：
- 队伍问题从根消失（退队卡图/队长退队僵尸/撤退覆盖进度）
- 多队伍同本天然隔离（各自 inst:<uuid>）
"""
from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional

# 运行时内存态：world_id -> {
#   "name": 副本名,
#   "inst_id": 副本配置 id（inst_goblin_camp）,
#   "maps": {map_id: map_def},      # 克隆的副本图
#   "subareas": {map_id: [sa...]},  # 克隆的子区域
#   "created_at": ts,
#   "leader": qq_id,                # 仅展示/带队，不承载状态
#   "members": [qq_id...],          # 进本快照（展示用）
#   "rooms": {...},                 # 怪池/资源池（v137 副本地图化）
#   "resources_pool": {...},        # 奖励总量
#   "st": {...},                    # 副本战斗状态快照（迁移自 battle_state）
#   "retreated": bool,              # 撤退保留进度标记
# }
instance_worlds: Dict[str, dict] = {}

EVENT_STATE_PREFIX = "instance_world_"


# ============================================================
# 内存态访问
# ============================================================


def get_instance_world(world_id: str) -> Optional[dict]:
    """获取大陆实例。内存没有则尝试从 DB 惰性恢复。"""
    if world_id not in instance_worlds:
        _restore_from_db(world_id)
    return instance_worlds.get(world_id)


def _restore_from_db(world_id: str) -> None:
    """重启后从 event_state 恢复大陆实例（惰性：首次访问才加载）。"""
    try:
        from ..store.world import get_event_state
        raw = get_event_state(f"{EVENT_STATE_PREFIX}{world_id}")
        if raw:
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, dict):
                instance_worlds[world_id] = data
    except Exception:
        # DB 不可用/损坏 → 当作不存在，调用方自行兜底
        instance_worlds.pop(world_id, None)


# ============================================================
# 创建 / 销毁
# ============================================================


def create_instance_world(
    inst_id: str,
    members: List[int],
    boss: dict,
    now: Optional[int] = None,
    leader: Optional[int] = None,
    st: Optional[dict] = None,
    rooms: Optional[dict] = None,
    resources_pool: Optional[dict] = None,
) -> str:
    """开本：克隆副本地图为独立大陆。返回 world_id 'inst:<uuid>'。

    参数：
    - inst_id: 副本配置 id（inst_goblin_camp）
    - members: 进本成员 qq_id 列表
    - boss: 构建好的 Boss dict（血量已按人数缩放）
    - now: 当前时间戳（缺省取 time.time()）
    - leader: 队长 qq_id（缺省取 members[0]；仅展示，不承载状态）
    - st: 副本战斗状态快照（_instance_build_state 产物）
    - rooms / resources_pool: v137 副本地图化怪池/资源池
    """
    from ..data import MAP_BY_ID, SUBAREAS, INSTANCES
    world_id = f"inst:{uuid.uuid4().hex[:12]}"
    map_id = inst_id[5:] if str(inst_id).startswith("inst_") else inst_id
    inst = INSTANCES.get(inst_id, {})
    _now = int(now if now is not None else time.time())
    _leader = str(leader if leader is not None else members[0])

    instance_worlds[world_id] = {
        "name": inst.get("name", map_id),
        "inst_id": inst_id,
        "maps": {map_id: deepcopy(MAP_BY_ID.get(map_id, {}))},
        "subareas": {map_id: deepcopy(SUBAREAS.get(map_id, []))},
        "created_at": _now,
        "leader": _leader,
        "members": [str(m) for m in members],
        "rooms": rooms or {},
        "resources_pool": resources_pool or {},
        "st": st,
        "retreated": False,
    }
    _persist(world_id)
    return world_id


def destroy_instance_world(world_id: str) -> None:
    """退本/通关/失败/过期：销毁大陆实例。"""
    instance_worlds.pop(world_id, None)
    try:
        from ..store.world import delete_event_state
        delete_event_state(f"{EVENT_STATE_PREFIX}{world_id}")
    except Exception:
        pass


def _persist(world_id: str) -> None:
    """落库 event_state（重启防丢）。只落非战斗核心字段（st 也落，可恢复）。"""
    data = instance_worlds.get(world_id)
    if data is None:
        return
    try:
        from ..store.world import set_event_state
        set_event_state(f"{EVENT_STATE_PREFIX}{world_id}", json.dumps(data, ensure_ascii=False, default=str))
    except Exception:
        pass


def update_instance_world(world_id: str, **fields) -> None:
    """更新大陆实例字段（房间/资源池/队伍快照等）并落库。"""
    data = instance_worlds.get(world_id)
    if data is None:
        return
    for k, v in fields.items():
        data[k] = v
    _persist(world_id)


def set_instance_st(world_id: str, st: Optional[dict]) -> None:
    """设置副本战斗状态快照（迁移自 battle_state 存队长 → 存大陆）。"""
    update_instance_world(world_id, st=st)


def get_instance_st(world_id: str) -> Optional[dict]:
    """取副本战斗状态快照。"""
    data = get_instance_world(world_id)
    return (data or {}).get("st")


def list_instance_worlds() -> List[str]:
    """列出全部存活大陆实例 world_id（监控/清理用）。"""
    return list(instance_worlds.keys())


def cleanup_stale_instances(max_age_sec: int = 24 * 3600) -> int:
    """惰性回收过期大陆实例（24h 无活动）。返回清理数量。

    过期判定：created_at 距今超过 max_age_sec。调用方（命令层）在
    任意副本入口检查本副本的 world_id 是否过期。
    """
    now = int(time.time())
    stale = []
    for wid, data in instance_worlds.items():
        created = int(data.get("created_at", 0) or 0)
        if created and now - created > max_age_sec:
            stale.append(wid)
    for wid in stale:
        destroy_instance_world(wid)
    return len(stale)


def resolve_map_for(world_id: str, map_id: str) -> Optional[dict]:
    """按世界解析地图（纯函数，供不持有 Position 的场景）。"""
    if world_id and world_id.startswith("inst:"):
        data = get_instance_world(world_id)
        if data is None:
            return None
        return data.get("maps", {}).get(map_id)
    from ..data import MAP_BY_ID
    return MAP_BY_ID.get(map_id)
