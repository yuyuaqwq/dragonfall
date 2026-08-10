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


def market_list(group_id, map_id=None):
    """查看市场列表（全局市场：所有群互通）。

    map_id=None → 群市场寄售（map_id 为空）；map_id=具体地图 → 该地图摆摊。
    """
    with _lock:
        conn = _connect()
        try:
            if map_id is None:
                rows = conn.execute(
                    "SELECT * FROM market WHERE map_id IS NULL OR map_id='' ORDER BY id DESC", ()
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM market WHERE map_id=? ORDER BY id DESC", (map_id,)
                ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["item_data"] = json.loads(d["item_data"] or "{}")
                out.append(d)
            return out
        finally:
            conn.close()

def market_add(group_id, seller, item_key, item_data, price, map_id=None):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO market (group_id, seller, item_key, item_data, price, listed_at, map_id) VALUES (?,?,?,?,?,?,?)",
                (group_id, seller, item_key, json.dumps(item_data, ensure_ascii=False), price, int(time.time()), map_id or ""),
            )
            conn.commit()
        finally:
            conn.close()

def market_list_by_seller(group_id, seller):
    """某玩家的全部寄售/摆摊条目"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM market WHERE seller=? ORDER BY id DESC", (seller,)
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["item_data"] = json.loads(d["item_data"] or "{}")
                out.append(d)
            return out
        finally:
            conn.close()

def market_get(mid):
    """按编号查单条(群市场/摆摊通用)，返回 dict 或 None"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM market WHERE id=?", (mid,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["item_data"] = json.loads(d["item_data"] or "{}")
            return d
        finally:
            conn.close()

def market_sync_stall(seller, cur_map):
    """摆摊惰性跟随：把该卖家所有摊位条目 map_id 同步到当前位置"""
    if not cur_map:
        return
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE market SET map_id=? WHERE seller=? AND map_id IS NOT NULL AND map_id!=''",
                (cur_map, seller),
            )
            conn.commit()
        finally:
            conn.close()

def market_remove_by_seller(group_id, seller):
    """收摊：删除该玩家的全部摆摊条目，返回物品列表(供退回背包)"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM market WHERE seller=? AND map_id IS NOT NULL AND map_id!=''", (seller,)
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["item_data"] = json.loads(d["item_data"] or "{}")
                out.append(d)
            conn.execute(
                "DELETE FROM market WHERE seller=? AND map_id IS NOT NULL AND map_id!=''", (seller,)
            )
            conn.commit()
            return out
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
    """队长拉新人入队(v53 组队扩至 4 人，支持 4 人副本)。成功返回 True；非队长/已在队/满员返回 False"""
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
    """返回玩家所在队伍的成员列表(含自己)，无队返回 []"""
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

def guild_add_exp(gid, exp, member_qq=None, contribute=0):
    """公会获得经验(可附带成员贡献)"""
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
                "INSERT OR REPLACE INTO pets (qq_id, pet_key, name, level, exp, satiety, bond, last_sat_time) VALUES (?,?,?,1,0,100,0,?)",
                (qq_id, pet_key, name, int(time.time())),
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

def pet_decay_satiety(pet, now=None):
    """按时间自然衰减饱食度：每小时 -1（上限 100，下限 0）。
    返回更新后的 pet dict（内存副本），不写库；调用方决定是否持久化。"""
    if not pet:
        return pet
    now = int(now or time.time())
    last = int(pet.get("last_sat_time") or 0)
    if last <= 0:
        pet = dict(pet)
        pet["last_sat_time"] = now
        return pet
    hours = (now - last) // 3600
    if hours > 0:
        pet = dict(pet)
        pet["satiety"] = max(0, int(pet["satiety"]) - hours)
        pet["last_sat_time"] = now
    return pet

# ---------------- 宠物图鉴（24 章） ----------------
def pet_dex_get(qq_id):
    """图鉴收集记录：返回 {pet_key: hatched_count}"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT pet_key, hatched FROM pet_dex WHERE qq_id=?", (qq_id,)
            ).fetchall()
            return {r[0]: r[1] for r in rows}
        finally:
            conn.close()

def pet_dex_add(qq_id, pet_key):
    """孵化记录：图鉴＋1(INSERT OR REPLACE 语义为计数累加需先查)"""
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "SELECT hatched FROM pet_dex WHERE qq_id=? AND pet_key=?", (qq_id, pet_key)
            ).fetchone()
            n = (cur[0] + 1) if cur else 1
            conn.execute(
                "INSERT OR REPLACE INTO pet_dex (qq_id, pet_key, hatched) VALUES (?,?,?)",
                (qq_id, pet_key, n),
            )
            conn.commit()
            return n
        finally:
            conn.close()


