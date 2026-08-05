# -*- coding: utf-8 -*-
from .connection import _connect, _lock

"""《剑与魔法》存储层 - stats"""


def init_stats(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO stats (qq_id) VALUES (?)", (qq_id,)
            )
            conn.commit()
        finally:
            conn.close()

def bump_stats(group_id, qq_id, **fields):
    with _lock:
        conn = _connect()
        try:
            sets = ", ".join(f"{k}={k}+?" for k in fields)
            conn.execute(
                f"UPDATE stats SET {sets} WHERE qq_id=?",
                (*fields.values(), qq_id),
            )
            conn.commit()
        finally:
            conn.close()

def get_stats(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM stats WHERE qq_id=?", (qq_id,)
            ).fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

def set_achievement(group_id, qq_id, ach_key, progress, claimed=0):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO achievements (qq_id, ach_key, progress, claimed) VALUES (?,?,?,?) "
                "ON CONFLICT(qq_id, ach_key) DO UPDATE SET progress=excluded.progress, claimed=excluded.claimed",
                (qq_id, ach_key, progress, claimed),
            )
            conn.commit()
        finally:
            conn.close()

def get_achievements(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM achievements WHERE qq_id=?", (qq_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


