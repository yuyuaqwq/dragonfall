# -*- coding: utf-8 -*-
import json
import sqlite3
import time
from .connection import _connect, _lock

"""《剑与魔法》存储层 - social"""


def add_reputation(group_id, qq_id, faction, points):
    """增加势力声望"""
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO reputation (qq_id, faction, points) VALUES (?,?,?) "
                "ON CONFLICT(qq_id, faction) DO UPDATE SET points=points+?",
                (qq_id, faction, points, points),
            )
            conn.commit()
        finally:
            conn.close()

def get_reputation(group_id, qq_id):
    """返回 {faction: points}"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT faction, points FROM reputation WHERE qq_id=?",
                (qq_id,),
            ).fetchall()
            return {r["faction"]: r["points"] for r in rows}
        finally:
            conn.close()


def get_signin(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM signin WHERE qq_id=?", (qq_id,)
            ).fetchone()
            if not row:
                return {"last_date": "", "streak": 0, "total": 0}
            return dict(row)
        finally:
            conn.close()

def save_signin(group_id, qq_id, last_date, streak, total):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO signin (qq_id, last_date, streak, total) VALUES (?,?,?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET last_date=excluded.last_date, streak=excluded.streak, total=excluded.total",
                (qq_id, last_date, streak, total),
            )
            conn.commit()
        finally:
            conn.close()


def market_list(group_id):
    """查看市场列表（全局市场：所有群互通）"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM market ORDER BY id DESC", ()
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["item_data"] = json.loads(d["item_data"] or "{}")
                out.append(d)
            return out
        finally:
            conn.close()

def market_add(group_id, seller, item_key, item_data, price):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO market (group_id, seller, item_key, item_data, price, listed_at) VALUES (?,?,?,?,?,?)",
                (group_id, seller, item_key, json.dumps(item_data, ensure_ascii=False), price, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()

def market_remove(mid):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM market WHERE id=?", (mid,)).fetchone()
            conn.execute("DELETE FROM market WHERE id=?", (mid,))
            conn.commit()
            if row:
                d = dict(row)
                d["item_data"] = json.loads(d["item_data"] or "{}")
                return d
            return None
        finally:
            conn.close()


def party_create(group_id, leader, member):
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM party WHERE group_id=? AND leader=?", (group_id, leader))
            conn.execute("DELETE FROM party WHERE group_id=? AND member=?", (group_id, leader))
            conn.execute(
                "INSERT INTO party (group_id, leader, member, created_at) VALUES (?,?,?,?)",
                (group_id, leader, leader, int(time.time())),
            )
            if member != leader:
                conn.execute(
                    "INSERT INTO party (group_id, leader, member, created_at) VALUES (?,?,?,?)",
                    (group_id, leader, member, int(time.time())),
                )
                conn.execute("DELETE FROM party WHERE group_id=? AND member=? AND leader!=?", (group_id, member, leader))
            conn.commit()
        finally:
            conn.close()

def party_add(group_id, leader, new_member, max_size=4):
    """队长拉新人入队（v53 组队扩至 4 人，支持 4 人副本）。成功返回 True；非队长/已在队/满员返回 False"""
    with _lock:
        conn = _connect()
        try:
            # 校验 leader 是队长（存在自指行）
            row = conn.execute(
                "SELECT 1 FROM party WHERE group_id=? AND leader=? AND member=?",
                (group_id, leader, leader),
            ).fetchone()
            if not row:
                return False
            # 已在队
            dup = conn.execute(
                "SELECT 1 FROM party WHERE group_id=? AND leader=? AND member=?",
                (group_id, leader, new_member),
            ).fetchone()
            if dup:
                return False
            # 人数上限
            cnt = conn.execute(
                "SELECT COUNT(*) AS c FROM party WHERE group_id=? AND leader=?",
                (group_id, leader),
            ).fetchone()["c"]
            if cnt >= max_size:
                return False
            # 清掉 new_member 可能所在的旧队伍
            conn.execute("DELETE FROM party WHERE group_id=? AND member=? AND leader!=?", (group_id, new_member, leader))
            conn.execute("DELETE FROM party WHERE group_id=? AND leader=?", (group_id, new_member))
            conn.execute(
                "INSERT INTO party (group_id, leader, member, created_at) VALUES (?,?,?,?)",
                (group_id, leader, new_member, int(time.time())),
            )
            conn.commit()
            return True
        finally:
            conn.close()

def party_members(group_id, qq_id):
    """返回玩家所在队伍的成员列表（含自己），无队返回 []"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT leader FROM party WHERE group_id=? AND member=?", (group_id, qq_id)
            ).fetchone()
            if not row:
                return []
            leader = row["leader"]
            rows = conn.execute(
                "SELECT member FROM party WHERE group_id=? AND leader=?", (group_id, leader)
            ).fetchall()
            return [r["member"] for r in rows]
        finally:
            conn.close()

def party_leave(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT leader FROM party WHERE group_id=? AND member=?", (group_id, qq_id)
            ).fetchone()
            if not row:
                return False
            leader = row["leader"]
            conn.execute("DELETE FROM party WHERE group_id=? AND member=?", (group_id, qq_id))
            conn.commit()
            if leader == qq_id:
                conn.execute("DELETE FROM party WHERE group_id=? AND leader=?", (group_id, qq_id))
                conn.commit()
            return True
        finally:
            conn.close()


def guild_create(name, leader, icon="🏰", desc=""):
    """创建公会；重名返回 None"""
    with _lock:
        conn = _connect()
        try:
            now = int(time.time())
            cur = conn.execute(
                "INSERT INTO guilds (name, leader, icon, desc, level, exp, created_at) VALUES (?,?,?,?,1,0,?)",
                (name, leader, icon, desc, now),
            )
            gid = cur.lastrowid
            conn.execute(
                "INSERT INTO guild_members (gid, qq_id, role, joined_at, contribute) VALUES (?,?,?,?,0)",
                (gid, leader, "leader", now),
            )
            conn.commit()
            return gid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

def guild_get_by_leader(qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT g.* FROM guilds g JOIN guild_members gm ON g.gid=gm.gid "
                "WHERE gm.qq_id=? AND gm.role='leader'", (qq_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

def guild_get_by_member(qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT g.* FROM guilds g JOIN guild_members gm ON g.gid=gm.gid "
                "WHERE gm.qq_id=?", (qq_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

def guild_get(gid):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM guilds WHERE gid=?", (gid,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

def guild_get_by_name(name):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM guilds WHERE name=?", (name,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

def guild_members(gid):
    """返回 (gid, qq_id, role, joined_at, contribute) 列表，按贡献排序"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM guild_members WHERE gid=? ORDER BY role='leader' DESC, contribute DESC",
                (gid,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def guild_join(gid, qq_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO guild_members (gid, qq_id, role, joined_at, contribute) VALUES (?,?,?,?,0)",
                (gid, qq_id, "member", int(time.time())),
            )
            conn.commit()
            return True
        finally:
            conn.close()

def guild_leave(gid, qq_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM guild_members WHERE gid=? AND qq_id=?", (gid, qq_id))
            conn.commit()
            # 若成员为会长 → 解散公会
            g = conn.execute("SELECT * FROM guilds WHERE gid=? AND leader=?", (gid, qq_id)).fetchone()
            if g:
                conn.execute("DELETE FROM guild_members WHERE gid=?", (gid,))
                conn.execute("DELETE FROM guilds WHERE gid=?", (gid,))
                conn.commit()
                return "disbanded"
            return "left"
        finally:
            conn.close()

def guild_kick(gid, leader, qq_id):
    """会长踢人；返回 True 成功"""
    with _lock:
        conn = _connect()
        try:
            g = conn.execute("SELECT * FROM guilds WHERE gid=? AND leader=?", (gid, leader)).fetchone()
            if not g:
                return False
            conn.execute("DELETE FROM guild_members WHERE gid=? AND qq_id=? AND role!='leader'", (gid, qq_id))
            conn.commit()
            return True
        finally:
            conn.close()

def guild_count(gid):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM guild_members WHERE gid=?", (gid,)).fetchone()
            return row["c"] if row else 0
        finally:
            conn.close()

def guild_add_exp(gid, exp, member_qq=None, contribute=0):
    """公会获得经验（可附带成员贡献）"""
    with _lock:
        conn = _connect()
        try:
            conn.execute("UPDATE guilds SET exp=exp+? WHERE gid=?", (exp, gid))
            if member_qq:
                conn.execute(
                    "UPDATE guild_members SET contribute=contribute+? WHERE gid=? AND qq_id=?",
                    (contribute, gid, member_qq),
                )
            conn.commit()
            # 升级判定：lv*300 经验升一级
            g = conn.execute("SELECT * FROM guilds WHERE gid=?", (gid,)).fetchone()
            if g:
                while g["exp"] >= g["level"] * 300:
                    conn.execute("UPDATE guilds SET exp=exp-?, level=level+1 WHERE gid=?", (g["level"] * 300, gid))
                    conn.commit()
                    g = conn.execute("SELECT * FROM guilds WHERE gid=?", (gid,)).fetchone()
            return True
        finally:
            conn.close()

def guild_set_sign(gid, qq_id, date):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE guild_members SET sign_date=? WHERE gid=? AND qq_id=?", (date, gid, qq_id)
            )
            conn.commit()
        finally:
            conn.close()

def guild_get_sign(gid, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT sign_date FROM guild_members WHERE gid=? AND qq_id=?", (gid, qq_id)
            ).fetchone()
            return row["sign_date"] if row else ""
        finally:
            conn.close()

def guild_set_task(gid, qq_id, date, progress):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE guild_members SET task_date=?, task_progress=? WHERE gid=? AND qq_id=?",
                (date, progress, gid, qq_id),
            )
            conn.commit()
        finally:
            conn.close()

def guild_get_task(gid, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT task_date, task_progress FROM guild_members WHERE gid=? AND qq_id=?",
                (gid, qq_id),
            ).fetchone()
            return (row["task_date"], row["task_progress"]) if row else ("", 0)
        finally:
            conn.close()

def guild_top(limit=10):
    """公会排行榜：按等级/人数"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT g.gid, g.name, g.level, g.icon, COUNT(gm.qq_id) AS members "
                "FROM guilds g LEFT JOIN guild_members gm ON g.gid=gm.gid "
                "GROUP BY g.gid ORDER BY g.level DESC, members DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def pet_get(qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM pets WHERE qq_id=?", (qq_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

def pet_create(qq_id, pet_key, name):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO pets (qq_id, pet_key, name, level, exp, satiety, bond) VALUES (?,?,?,1,0,100,0)",
                (qq_id, pet_key, name),
            )
            conn.commit()
        finally:
            conn.close()

def pet_update(qq_id, **fields):
    with _lock:
        conn = _connect()
        try:
            sets = ", ".join(f"{k}=?" for k in fields)
            conn.execute(
                f"UPDATE pets SET {sets} WHERE qq_id=?", (*fields.values(), qq_id)
            )
            conn.commit()
        finally:
            conn.close()

def pet_delete(qq_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM pets WHERE qq_id=?", (qq_id,))
            conn.commit()
        finally:
            conn.close()


