# -*- coding: utf-8 -*-
import json
import time
from .connection import _connect, _lock
from .. import content as C

"""《剑与魔法》存储层 - world"""


def bump_fishing(group_id, qq_id, n=1):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO fishing (qq_id, total) VALUES (?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET total=total+?",
                (qq_id, n, n),
            )
            conn.commit()
        finally:
            conn.close()

def get_fishing_total(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT total FROM fishing WHERE qq_id=?", (qq_id,)
            ).fetchone()
            return row["total"] if row else 0
        finally:
            conn.close()


def bump_bestiary(group_id, qq_id, monster, n=1):
    """v46：怪物名/ID 统一存怪物 ID（monster 参数兼容名字或 m_xxx id）"""
    mon_id = C.resolve("monsters", monster)
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO bestiary (qq_id, monster, kills) VALUES (?,?,?) "
                "ON CONFLICT(qq_id, monster) DO UPDATE SET kills=kills+?",
                (qq_id, mon_id, n, n),
            )
            conn.commit()
        finally:
            conn.close()

def get_bestiary(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT monster, kills FROM bestiary WHERE qq_id=? ORDER BY kills DESC",
                (qq_id,),
            ).fetchall()
            out = []
            for r in rows:
                out.append({"monster": r["monster"],
                            "name": C.display("monsters", r["monster"]),
                            "kills": r["kills"]})
            return out
        finally:
            conn.close()


def add_visited(group_id, qq_id, map_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO visited (qq_id, map_id) VALUES (?,?)",
                (qq_id, map_id),
            )
            conn.commit()
        finally:
            conn.close()

def get_visited_count(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM visited WHERE qq_id=?",
                (qq_id,),
            ).fetchone()
            return row["c"] if row else 0
        finally:
            conn.close()


def get_world_event(include_expired: bool = False):
    """返回当前活动事件（未过期），无则 None；include_expired=True 时返回最近一条（含过期）"""
    with _lock:
        conn = _connect()
        try:
            now = int(time.time())
            if include_expired:
                row = conn.execute(
                    "SELECT * FROM world_event ORDER BY id DESC LIMIT 1"
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM world_event WHERE ends_at > ? ORDER BY id DESC LIMIT 1", (now,)
                ).fetchone()
            if not row:
                return None
            e = dict(row)
            e["data"] = json.loads(e.get("data") or "{}")
            return e
        finally:
            conn.close()

def save_world_event(etype, ends_at, data: dict):
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM world_event")
            conn.execute(
                "INSERT INTO world_event (etype, starts_at, ends_at, data) VALUES (?,?,?,?)",
                (etype, int(time.time()), int(ends_at), json.dumps(data, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()

def clear_world_event():
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM world_event")
            conn.commit()
        finally:
            conn.close()

def get_event_state(key: str):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT value FROM event_state WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None
        finally:
            conn.close()

def set_event_state(key: str, value):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO event_state (key, value) VALUES (?,?)",
                (key, str(value)),
            )
            conn.commit()
        finally:
            conn.close()

def delete_event_state(key: str):
    """删除事件状态（v62 注销确认用）"""
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM event_state WHERE key=?", (key,))
            conn.commit()
        finally:
            conn.close()


# ---------- v65 NPC 多轮对话状态 ----------
# 会话状态（当前正在跟谁聊、聊到哪个节点）：event_state key = talk_{gid}_{qid}
# 对话 flag（聊过什么/彩蛋解锁，跨会话持久）：event_state key = talkflags_{gid}_{qid}

def talk_state_key(group_id, qq_id):
    return f"talk_{group_id}_{qq_id}"

def talk_flags_key(group_id, qq_id):
    return f"talkflags_{group_id}_{qq_id}"

def get_talk_state(group_id, qq_id):
    """返回当前对话会话 {"npc": id, "node": id} 或 None"""
    raw = get_event_state(talk_state_key(group_id, qq_id))
    if not raw:
        return None
    try:
        import json
        return json.loads(raw)
    except (ValueError, TypeError):
        return None

def set_talk_state(group_id, qq_id, npc_id, node_id):
    """保存对话会话"""
    import json
    set_event_state(talk_state_key(group_id, qq_id),
                    json.dumps({"npc": npc_id, "node": node_id}, ensure_ascii=False))

def clear_talk_state(group_id, qq_id):
    """结束对话（删除会话，flag 保留）"""
    delete_event_state(talk_state_key(group_id, qq_id))

def get_talk_flags(group_id, qq_id, npc_id):
    """该 NPC 已设置的对话 flag 列表"""
    raw = get_event_state(talk_flags_key(group_id, qq_id))
    if not raw:
        return []
    try:
        import json
        data = json.loads(raw)
        return list(data.get(npc_id, []))
    except (ValueError, TypeError):
        return []

def set_talk_flag(group_id, qq_id, npc_id, flag):
    """给该 NPC 设置对话 flag（幂等）"""
    import json
    key = talk_flags_key(group_id, qq_id)
    raw = get_event_state(key)
    data = {}
    if raw:
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            data = {}
    lst = list(data.get(npc_id, []))
    if flag not in lst:
        lst.append(flag)
    data[npc_id] = lst
    set_event_state(key, json.dumps(data, ensure_ascii=False))


