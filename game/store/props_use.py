# -*- coding: utf-8 -*-
"""《剑与魔法》存储层 - props_use（场景元素每日彩蛋使用记录，v87.12）

阶段四：专属元素带小效果（锻造台→材料、药柜→药草、壁炉→回血），
每日 1 次防刷。记录粒度 = 玩家 × 元素实例 key（"地图:子区域:prop_id"），
每个元素每天独立 1 次。value = 日期字符串 "YYYY-MM-DD"。
"""
import json

from .connection import _connect, _lock


def get_props_use(group_id, qq_id):
    """返回该玩家的 {元素key: 日期} 使用记录（无则 {}）。"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT used FROM props_use WHERE qq_id=?", (qq_id,)
            ).fetchone()
            if not row:
                return {}
            return json.loads(row["used"] or "{}")
        finally:
            conn.close()


def mark_props_use(group_id, qq_id, key, date):
    """记录该元素今天已使用。"""
    used = get_props_use(group_id, qq_id)
    used[key] = date
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO props_use (qq_id, used) VALUES (?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET used=excluded.used",
                (qq_id, json.dumps(used, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()
