# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年存储层 - fishing_catches：鱼篓明细表（v126.1 鱼获随机波动）

每次钓获一行（qq_id + fish_key + size/weight/ts），出售/交任务扣鱼时按 FIFO
（ts, rowid）消费——背包保持堆叠（mat_×N），重量信息只存本表。
fish_key 与背包 mat_ ID 一致（_key_to_id 归一化，兼容中文名/ID 两种入参）。
"""
import time

from .connection import _connect, _lock
from .inventory import _key_to_id


def log_fish_catch(qq_id, fish_key, size, weight):
    """钓获入明细（每次一条），返回 True。"""
    fish_key = _key_to_id(fish_key)
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO fish_catches (qq_id, fish_key, size, weight, ts) VALUES (?,?,?,?,?)",
                (qq_id, fish_key, float(size), float(weight), int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()
    return True


def peek_fish_catches(qq_id, fish_key, n):
    """FIFO 前 n 条明细（只读不删），返回 [{"size":…, "weight":…, "ts":…}, …]。"""
    fish_key = _key_to_id(fish_key)
    n = int(n)
    if n <= 0:
        return []
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT size, weight, ts FROM fish_catches"
                " WHERE qq_id=? AND fish_key=? ORDER BY ts, rowid LIMIT ?",
                (qq_id, fish_key, n),
            ).fetchall()
            return [{"size": r["size"], "weight": r["weight"], "ts": r["ts"]} for r in rows]
        finally:
            conn.close()


def consume_fish_catches(qq_id, fish_key, n):
    """删除最早 n 条明细（FIFO；无明细静默）。返回实际删除条数。"""
    fish_key = _key_to_id(fish_key)
    n = int(n)
    if n <= 0:
        return 0
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT rowid FROM fish_catches"
                " WHERE qq_id=? AND fish_key=? ORDER BY ts, rowid LIMIT ?",
                (qq_id, fish_key, n),
            ).fetchall()
            if rows:
                conn.executemany(
                    "DELETE FROM fish_catches WHERE rowid=?",
                    [(r["rowid"],) for r in rows],
                )
                conn.commit()
            return len(rows)
        finally:
            conn.close()
