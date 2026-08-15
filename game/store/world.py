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
    """v46：怪物名/ID 统一存怪物 ID(monster 参数兼容名字或 m_xxx id)"""
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


# ==================== v115 探索见闻：子区域级到访 visited_subareas ====================
# 与 visited 表（地图级）同构但按"地图:子区域"粒度记录；group_id 仅作兼容保留（同 add_visited）。

def add_visited_subarea(group_id, qq_id, map_id, sa_id):
    """记录子区域到访（INSERT OR IGNORE：幂等，不重复计数）。"""
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO visited_subareas (qq_id, map_id, sa_id, first_at) VALUES (?,?,?,?)",
                (qq_id, map_id, sa_id, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()

def get_visited_subareas(qq_id) -> set:
    """返回该玩家已到访问的子区域集合 {"map_id:sa_id", ...}。"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT map_id, sa_id FROM visited_subareas WHERE qq_id=?",
                (qq_id,),
            ).fetchall()
            return {f"{r['map_id']}:{r['sa_id']}" for r in rows}
        finally:
            conn.close()

def count_visited_subareas(qq_id) -> int:
    """子区域到访总数（全大陆 visited_subareas 记录条数）。"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM visited_subareas WHERE qq_id=?",
                (qq_id,),
            ).fetchone()
            return row["c"] if row else 0
        finally:
            conn.close()


def get_world_event(include_expired: bool = False):
    """返回当前活动事件(未过期)，无则 None；include_expired=True 时返回最近一条(含过期)"""
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
    """删除事件状态(v62 注销确认用)"""
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
    """结束对话(删除会话，flag 保留)"""
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
    """给该 NPC 设置对话 flag(幂等)"""
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

def get_boss_dmg_mult(qq_id) -> float:
    """世界 Boss 伤害倍率（gm_伤害 设置，默认 1.0）。"""
    try:
        return float(get_event_state(f"boss_dmg_{qq_id}") or 1)
    except (ValueError, TypeError):
        return 1.0


# v104 M24 P2-5：流失玩家残留 event_state 键的全局过期清理。
# 键内嵌 qq_id 的后缀键（每日运势/对话会话/移动模式/物品查看模式/Boss 伤害倍率）
# 只随注销路径清理，流失玩家（>N 天未活跃）的键永久残留 → 启动时统一清扫。
# 注意：talkflags_（跨会话彩蛋解锁，持久保留）、prof_daily_（按天键，短生命周期）等
# 不在清理名单内；无玩家关联的键（deed_owner_ 等）也不动。
_EVENT_STATE_PLAYER_PREFIXES = (
    "daily_fortune_",  # daily_fortune_{gid}_{qid}
    "talk_",           # talk_{gid}_{qid}（talkflags_ 不以 "talk_" 开头，天然豁免）
    "boss_dmg_",       # boss_dmg_{qid}
    "move_mode:",      # move_mode:{qid}
    "item_view_mode:", # item_view_mode:{qid}
)

def _event_state_key_qq(key: str):
    """从上述五类后缀键中提取内嵌 qq_id；无法识别返回 None。"""
    if key.startswith("move_mode:") or key.startswith("item_view_mode:"):
        return key.split(":", 1)[1]
    if key.startswith("boss_dmg_"):
        return key.split("_", 2)[2]
    if key.startswith("daily_fortune_"):
        return key.split("_", 3)[3]
    if key.startswith("talk_"):
        return key.split("_", 2)[2]
    return None

def cleanup_stale_event_state(max_age_days: int = 30) -> int:
    """清理 >max_age_days 天未活跃玩家的五类残留 event_state 键。
    幂等；返回删除的键数（0 = 无可清理/无表）。"""
    cutoff = int(time.time()) - max_age_days * 86400
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT qq_id FROM players WHERE last_active < ?", (cutoff,)
            ).fetchall()
            if not rows:
                return 0
            inactive = {r["qq_id"] for r in rows}
            keys = [
                r["key"] for r in conn.execute("SELECT key FROM event_state").fetchall()
                if r["key"].startswith(_EVENT_STATE_PLAYER_PREFIXES)
            ]
            doomed = [k for k in keys if _event_state_key_qq(k) in inactive]
            if doomed:
                conn.executemany("DELETE FROM event_state WHERE key=?", [(k,) for k in doomed])
                conn.commit()
            return len(doomed)
        finally:
            conn.close()


