# -*- coding: utf-8 -*-
from .connection import _connect, _lock

"""奥兰迪亚·余烬纪年存储层 - feedback"""


def add_feedback(qq_id, group_id, content):
    """记录一条玩家意见，返回意见编号"""
    from datetime import datetime
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "INSERT INTO feedback (qq_id, group_id, content, created_at, status) VALUES (?,?,?,?, 'new')",
                (qq_id, group_id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

def get_feedback(status=None, limit=50):
    """查询意见；status=None 查全部，'new' 只查未处理"""
    with _lock:
        conn = _connect()
        try:
            if status:
                rows = conn.execute(
                    "SELECT id, qq_id, group_id, content, reply, created_at, status FROM feedback WHERE status=? ORDER BY id DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, qq_id, group_id, content, reply, created_at, status FROM feedback ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return rows
        finally:
            conn.close()

