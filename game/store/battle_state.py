# -*- coding: utf-8 -*-
import json
import time
from .connection import _connect, _lock

"""《剑与魔法》存储层 - battle_state"""
# v104 M02 P2：普通战斗 24h 无活动自动回收（battle_state 永久残留泄漏；PVP 另有 5 分钟超时在 combat.py）
BATTLE_STALE_SEC = 24 * 3600


def save_battle(group_id, qq_id, state: dict):
    """保存完整战斗上下文（v9：含 type/round/buffs/enemy 等）


    兼容旧调用：若传入的是裸怪物 dict，自动包装为 v9 状态。
    v94.1：续存时自动继承旧 state 的 stamina_charged 标记（b.to_state() 不含该字段，
    否则战斗内第二击会重复扣体力）。
    """
    if "type" not in state:
        state = {
            "type": "monster", "round": 0,
            "enemy": state, "p_buffs": {}, "e_buffs": {},
            "p_defending": False, "e_defending": False,
        }
    with _lock:
        conn = _connect()
        try:
            enemy = state.get("enemy") or {}
            old = conn.execute(
                "SELECT state FROM battle_state WHERE qq_id=?", (qq_id,)
            ).fetchone()
            if old and state.get("stamina_charged") is None:
                try:
                    old_state = json.loads(old["state"])
                    if old_state.get("stamina_charged"):
                        state["stamina_charged"] = True
                except (ValueError, TypeError):
                    pass
            conn.execute(
                "INSERT INTO battle_state (qq_id, monster, state, updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET monster=excluded.monster, state=excluded.state, updated_at=excluded.updated_at",
                (qq_id, enemy.get("name", ""), json.dumps(state, ensure_ascii=False), int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()

def get_battle(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT monster, state, updated_at FROM battle_state WHERE qq_id=?",
                (qq_id,),
            ).fetchone()
            if not row:
                return None
            # v104 M02 P2：超 24h 无活动的战斗记录回收（普通战斗此前永久保留；
            # 表无 created_at 列，用 updated_at 判定更合理——战斗长时间无操作即视为废弃）
            updated = row["updated_at"] or 0
            if updated and time.time() - updated > BATTLE_STALE_SEC:
                conn.execute("DELETE FROM battle_state WHERE qq_id=?", (qq_id,))
                conn.commit()
                return None
            state = json.loads(row["state"])
            # 兼容 v9 之前的旧数据（state 字段直接是裸怪物 dict）
            if "type" not in state:
                state = {
                    "type": "monster", "round": 0,
                    "enemy": state, "p_buffs": {}, "e_buffs": {},
                    "p_defending": False, "e_defending": False,
                }
            return {"state": state, "monster": state.get("enemy", {}), "name": row["monster"], "updated_at": row["updated_at"]}
        finally:
            conn.close()

def clear_battle(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "DELETE FROM battle_state WHERE qq_id=?", (qq_id,)
            )
            conn.commit()
        finally:
            conn.close()


