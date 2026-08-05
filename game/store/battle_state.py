# -*- coding: utf-8 -*-
import json
import time
from .connection import _connect, _lock

"""《剑与魔法》存储层 - battle_state"""
def save_battle(group_id, qq_id, state: dict):
    """保存完整战斗上下文（v9：含 type/round/buffs/enemy 等）


    兼容旧调用：若传入的是裸怪物 dict，自动包装为 v9 状态。
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


