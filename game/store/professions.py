# -*- coding: utf-8 -*-
"""《剑与魔法》存储层 - professions：副业等级与经验

副业（采集/采矿/钓鱼/炼金/打造/烹饪）独立成长线：
- 每条副业 Lv.1~10，经验按 20*当前等级 升级（Lv1→2 需 20，Lv2→3 需 40……）
- add_prof_exp 自动处理升级与封顶（Lv.10 满级不再累积）
"""
from .connection import _connect, _lock

PROF_FIELDS = {
    "gather": "采集",
    "mining": "采矿",
    "fishing": "钓鱼",
    "alchemy": "炼金",
    "craft": "打造",
    "cooking": "烹饪",
}


def _ensure_prof_row(conn, qq_id):
    conn.execute(
        "INSERT OR IGNORE INTO professions (qq_id) VALUES (?)", (qq_id,)
    )


def get_professions(group_id, qq_id):
    """返回全部副业等级/经验 dict：{key: {"lv": n, "exp": n, "name": 中文}}"""
    with _lock:
        conn = _connect()
        try:
            _ensure_prof_row(conn, qq_id)
            conn.commit()
            row = conn.execute(
                "SELECT * FROM professions WHERE qq_id=?", (qq_id,)
            ).fetchone()
            d = dict(row) if row else {}
        finally:
            conn.close()
    out = {}
    for key, name in PROF_FIELDS.items():
        out[key] = {
            "name": name,
            "lv": d.get(f"{key}_lv", 1),
            "exp": d.get(f"{key}_exp", 0),
        }
    return out


def get_prof_level(group_id, qq_id, key):
    return get_professions(group_id, qq_id)[key]["lv"]


def add_prof_exp(group_id, qq_id, key, exp=1):
    """给副业加经验，自动升级。返回 (level, leveled_up)"""
    with _lock:
        conn = _connect()
        try:
            _ensure_prof_row(conn, qq_id)
            conn.commit()
            row = conn.execute(
                f"SELECT {key}_lv AS lv, {key}_exp AS exp FROM professions WHERE qq_id=?",
                (qq_id,),
            ).fetchone()
            lv = row["lv"] if row else 1
            cur = row["exp"] if row else 0
            if lv >= 10:
                return lv, False
            cur += exp
            leveled = False
            while lv < 10 and cur >= lv * 20:
                cur -= lv * 20
                lv += 1
                leveled = True
            if lv >= 10:
                cur = 0
            conn.execute(
                f"UPDATE professions SET {key}_lv=?, {key}_exp=? WHERE qq_id=?",
                (lv, cur, qq_id),
            )
            conn.commit()
            return lv, leveled
        finally:
            conn.close()


def prof_top(group_id, limit=10):
    """副业总分排行（6 条副业等级之和）"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT qq_id, gather_lv+mining_lv+fishing_lv+alchemy_lv+craft_lv+cooking_lv AS total "
                "FROM professions ORDER BY total DESC, qq_id LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def bump_fish_king(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            _ensure_prof_row(conn, qq_id)
            conn.execute(
                "UPDATE professions SET fish_king=fish_king+1 WHERE qq_id=?",
                (qq_id,),
            )
            conn.commit()
        finally:
            conn.close()


def get_fish_king(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            _ensure_prof_row(conn, qq_id)
            row = conn.execute(
                "SELECT fish_king FROM professions WHERE qq_id=?", (qq_id,)
            ).fetchone()
            return row["fish_king"] if row else 0
        finally:
            conn.close()
