# -*- coding: utf-8 -*-
import json
import time
from .connection import _connect, _lock
from .. import content as C

"""《剑与魔法》存储层 - players"""


def record_player_group(qq_id, group_id):
    """记录玩家在某个群注册/活跃过（广播目标筛选）"""
    if not group_id or group_id == "private":
        return
    with _lock:
        conn = _connect()
        try:
            now = int(time.time())
            conn.execute(
                "INSERT INTO player_groups (qq_id, group_id, first_seen, last_active) VALUES (?,?,?,?) "
                "ON CONFLICT(qq_id, group_id) DO UPDATE SET last_active=excluded.last_active",
                (qq_id, group_id, now, now),
            )
            conn.commit()
        finally:
            conn.close()

def get_player_groups():
    """返回所有有玩家注册/活跃过的群号列表（广播目标）"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT DISTINCT group_id FROM player_groups WHERE group_id != 'private'"
            ).fetchall()
            return [r["group_id"] for r in rows]
        finally:
            conn.close()

def get_group_players(group_id):
    """返回在指定群注册/活跃过的玩家 {qq_id: player}（玩家数据全局，此处按群筛选）"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT p.* FROM players p JOIN player_groups g ON p.qq_id=g.qq_id "
                "WHERE g.group_id=? ORDER BY p.level DESC",
                (group_id,),
            ).fetchall()
            out = {}
            for r in rows:
                p = dict(r)
                p["equipment"] = json.loads(p["equipment"] or "{}")
                p["skills"] = json.loads(p["skills"] or "[]")
                p["attributes"] = json.loads(p.get("attributes") or '{"str":0,"agi":0,"int":0,"vit":0}')
                p["learned_skills"] = json.loads(p.get("learned_skills") or "[]")
                out[p["qq_id"]] = p
            return out
        finally:
            conn.close()


def create_player(group_id, qq_id, name, class_name, base_stats, max_hp, max_mp, race="human"):
    with _lock:
        conn = _connect()
        try:
            now = int(time.time())
            conn.execute(
                "INSERT INTO players (qq_id, name, class_name, level, exp, gold, hp, mp, max_hp, max_mp, cur_map, class_tier, attr_pts, attributes, created_at, last_active, race) "
                "VALUES (?,?,?,1,0,50,?,?,?,?,'oak_town',0,9,'{\"str\":0,\"agi\":0,\"int\":0,\"vit\":0}',?,?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET name=excluded.name, class_name=excluded.class_name, last_active=excluded.last_active, race=excluded.race",
                (qq_id, name, class_name, max_hp, max_mp, max_hp, max_mp, now, now, race),
            )
            conn.commit()
        finally:
            conn.close()
    record_player_group(qq_id, group_id)

def get_player(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM players WHERE qq_id=?", (qq_id,)
            ).fetchone()
            if not row:
                return None
            p = dict(row)
            p["equipment"] = json.loads(p["equipment"] or "{}")
            p["skills"] = json.loads(p["skills"] or "[]")
            p["attributes"] = json.loads(p.get("attributes") or '{"str":0,"agi":0,"int":0,"vit":0}')
            p["learned_skills"] = json.loads(p.get("learned_skills") or "[]")
            # v46：learned_skills 存档为技能 ID，读入内存转回技能名（battle 层用名字查定义）
            p["learned_skills"] = [C.display("skills", s) if s else s for s in p["learned_skills"]]
            p["shortcuts"] = json.loads(p.get("shortcuts") or "{}")
            p["skill_levels"] = json.loads(p.get("skill_levels") or "{}")
            # v46：skill_levels 键名同样转回技能名
            p["skill_levels"] = {C.display("skills", k) if k else k: v for k, v in p["skill_levels"].items()}
            p["mounts"] = json.loads(p.get("mounts") or "{}")
            p["learned_blueprints"] = json.loads(p.get("learned_blueprints") or "[]")
            # v81 导师进修：apprentices 已拜师副业列表（JSON 数组）
            p["apprentices"] = json.loads(p.get("apprentices") or "[]")
            p["hidden_class_unlock"] = json.loads(p.get("hidden_class_unlock") or "[]")
            return p
        finally:
            conn.close()

def find_player_by_name(name: str):
    """按名字查找玩家（玩家跨群共用，只按名字查）。返回 {qq_id, name} 或 None"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT qq_id, name FROM players WHERE name=?", (name,)
            ).fetchone()
            if not row:
                return None
            return {"qq_id": row["qq_id"], "name": row["name"]}
        finally:
            conn.close()

def update_player(group_id, qq_id, **fields):
    """通用更新。fields: hp/mp/exp/gold/level/cur_map/equipment/skills/name/max_hp/max_mp"""
    if not fields:
        return
    with _lock:
        conn = _connect()
        try:
            sets = []
            vals = []
            for k, v in fields.items():
                if k in ("equipment", "skills", "learned_skills", "shortcuts", "skill_levels", "mounts", "learned_blueprints", "apprentices", "hidden_class_unlock"):
                    # v46：技能名列表/技能等级表 写入时转 ID（存档只存 ID）
                    if k in ("learned_skills", "skills") and isinstance(v, list):
                        v = [C.resolve("skills", s) if s else s for s in v]
                    elif k == "skill_levels" and isinstance(v, dict):
                        v = {C.resolve("skills", kk) if kk else kk: vv for kk, vv in v.items()}
                    v = json.dumps(v, ensure_ascii=False)
                sets.append(f"{k}=?")
                vals.append(v)
            vals += [int(time.time()), qq_id]
            conn.execute(
                f"UPDATE players SET {', '.join(sets)}, last_active=? WHERE qq_id=?",
                vals,
            )
            conn.commit()
        finally:
            conn.close()
    record_player_group(qq_id, group_id)

def top_players(group_id, limit=10):
    """全服强者榜（跨群）：玩家数据全局，排行不按群过滤。group_id 仅作兼容参数"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT p.name, p.class_name, p.level, p.exp FROM players p "
                "ORDER BY p.level DESC, p.exp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def all_players(group_id):
    """返回全部玩家（全局）——group_id 仅作兼容参数"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute("SELECT * FROM players ORDER BY level DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def get_portals(qq_id) -> list:
    """已激活的祭坛地图 id 列表"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT portals FROM players WHERE qq_id=?", (qq_id,)).fetchone()
            if not row or not row["portals"]:
                return []
            try:
                return json.loads(row["portals"])
            except (ValueError, TypeError):
                return []
        finally:
            conn.close()

def add_portal(qq_id, map_id):
    """激活一座祭坛（幂等）"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT portals FROM players WHERE qq_id=?", (qq_id,)).fetchone()
            lst = []
            if row and row["portals"]:
                try:
                    lst = json.loads(row["portals"])
                except (ValueError, TypeError):
                    lst = []
            if map_id not in lst:
                lst.append(map_id)
                conn.execute("UPDATE players SET portals=? WHERE qq_id=?", (json.dumps(lst), qq_id))
                conn.commit()
                return True
            return False
        finally:
            conn.close()


def get_skill_bar(qq_id) -> list:
    """技能栏 6 槽（技能 ID 列表，空槽为 None）；旧档技能名自动转 ID"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT skill_bar FROM players WHERE qq_id=?", (qq_id,)).fetchone()
            if not row or not row["skill_bar"]:
                return []
            try:
                bar = json.loads(row["skill_bar"])
                if not isinstance(bar, list):
                    return []
                # v46：旧档技能名 → 技能 ID，再统一转回名字（内存层用名字）
                return [C.display("skills", C.resolve("skills", s)) if s else None for s in bar]
            except (ValueError, TypeError):
                return []
        finally:
            conn.close()

def set_skill_bar(qq_id, bar: list):
    """保存技能栏（自动补齐 6 槽）；v46 统一存技能 ID"""
    padded = list(bar) + [None] * max(0, 6 - len(bar))
    padded = padded[:6]
    # v46：技能名 → ID
    padded = [C.resolve("skills", s) if s else None for s in padded]
    with _lock:
        conn = _connect()
        try:
            conn.execute("UPDATE players SET skill_bar=? WHERE qq_id=?", (json.dumps(padded), qq_id))
            conn.commit()
        finally:
            conn.close()


def delete_player(qq_id):
    """注销角色：删除玩家主记录 + 全部关联数据（v62 群友想切职业）。

    清理表：inventory / quests / battle_state / achievements / stats /
    reputation / signin / fishing / bestiary / visited / player_groups /
    professions / pets / market(卖出) / party(队长或队员) / guild_members /
    feedback(保留历史意见，仅清空 qq 归属标记由 create 重建)。
    返回是否删除成功（False = 该 qq 无角色）。
    """
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT qq_id FROM players WHERE qq_id=?", (qq_id,)).fetchone()
            if not row:
                return False
            for tbl in ("inventory", "quests", "battle_state", "achievements", "stats",
                        "reputation", "signin", "fishing", "bestiary", "visited",
                        "player_groups", "professions", "pets"):
                conn.execute(f"DELETE FROM {tbl} WHERE qq_id=?", (qq_id,))
            # 市场：下架该玩家挂的单
            conn.execute("DELETE FROM market WHERE seller=?", (qq_id,))
            # 队伍：删掉该玩家所在行（队长行也删，队自动散）
            conn.execute("DELETE FROM party WHERE member=?", (qq_id,))
            conn.execute("DELETE FROM party WHERE leader=?", (qq_id,))
            # 公会：退出公会；若为会长则解散公会
            g = conn.execute("SELECT gid FROM guild_members WHERE qq_id=?", (qq_id,)).fetchone()
            if g:
                gid = g["gid"]
                conn.execute("DELETE FROM guild_members WHERE qq_id=?", (qq_id,))
                remain = conn.execute("SELECT COUNT(*) AS c FROM guild_members WHERE gid=?", (gid,)).fetchone()["c"]
                if remain == 0:
                    conn.execute("DELETE FROM guilds WHERE gid=?", (gid,))
            # 玩家主记录最后删（外键约束兜底顺序无关，SQLite 默认无外键）
            conn.execute("DELETE FROM players WHERE qq_id=?", (qq_id,))
            conn.commit()
            return True
        finally:
            conn.close()


