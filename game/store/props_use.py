# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年存储层 - props_use（场景元素每日彩蛋使用记录，v87.12）

阶段四：专属元素带小效果（锻造台→材料、药柜→药草、壁炉→回血），
每日 1 次防刷。记录粒度 = 玩家 × 元素实例 key（"地图:子区域:prop_id"），
每个元素每天独立 1 次。value = 日期字符串 "YYYY-MM-DD"。
"""
import json

from .connection import _connect, _lock, atomic


def get_props_use(qq_id):
    """返回该玩家的 {元素key: 日期} 使用记录(无则 {})。
    v105 M23 P3-8：记录按 qq_id 全局（玩家数据全局化），原 group_id 参数完全未用，已移除。"""
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


def mark_props_use(qq_id, key, date):
    """记录该元素今天已使用。"""
    used = get_props_use(qq_id)
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


def props_use_claim_atomic(qq_id, key, date):
    """F1 P1-4：原子认领每日元素使用（防并发双请求重复生效）。

    单事务内 读 used→判是否已用→写回；返回 True 表示本次是本玩家第一个把该元素
    记为今天已用（调用方据此发放奖励），False 表示今天已被拿走（并发后手/重复调用）。
    """
    with atomic() as conn:
        row = conn.execute(
            "SELECT used FROM props_use WHERE qq_id=?", (qq_id,)
        ).fetchone()
        used = {}
        if row and row["used"]:
            try:
                used = json.loads(row["used"] or "{}")
                if not isinstance(used, dict):
                    used = {}
            except (ValueError, TypeError):
                used = {}
        if used.get(key) == date:
            return False
        used[key] = date
        conn.execute(
            "INSERT INTO props_use (qq_id, used) VALUES (?,?) "
            "ON CONFLICT(qq_id) DO UPDATE SET used=excluded.used",
            (qq_id, json.dumps(used, ensure_ascii=False)),
        )
        return True
