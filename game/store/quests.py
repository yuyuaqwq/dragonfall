# -*- coding: utf-8 -*-
import json
from .connection import _connect, _lock

"""《剑与魔法》存储层 - quests"""


def get_quests(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM quests WHERE qq_id=?", (qq_id,)
            ).fetchone()
            if not row:
                return {"main_quest": "q1", "main_status": "pending", "main_progress": {}, "daily": {}, "completed_main": [], "side": {}}
            q = dict(row)
            q["main_progress"] = json.loads(q["main_progress"] or "{}")
            q["daily"] = json.loads(q["daily"] or "{}")
            q["completed_main"] = json.loads(q["completed_main"] or "[]")
            q["main_status"] = q.get("main_status") or "pending"
            q["side"] = json.loads(q["side"] or "{}")
            return q
        finally:
            conn.close()

def save_quests(group_id, qq_id, quest_data):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO quests (qq_id, main_quest, main_status, main_progress, daily, completed_main, side) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET main_quest=excluded.main_quest, main_status=excluded.main_status, main_progress=excluded.main_progress, daily=excluded.daily, completed_main=excluded.completed_main, side=excluded.side",
                (
                    qq_id,
                    quest_data.get("main_quest"),
                    quest_data.get("main_status"),
                    json.dumps(quest_data.get("main_progress", {}), ensure_ascii=False),
                    json.dumps(quest_data.get("daily", {}), ensure_ascii=False),
                    json.dumps(quest_data.get("completed_main", []), ensure_ascii=False),
                    json.dumps(quest_data.get("side", {}), ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()


