# -*- coding: utf-8 -*-
from .connection import _connect, _lock

"""《剑与魔法》存储层 - feedback"""


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
                    "SELECT id, qq_id, group_id, content, created_at, status FROM feedback WHERE status=? ORDER BY id DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, qq_id, group_id, content, created_at, status FROM feedback ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return rows
        finally:
            conn.close()

def mark_feedback_done(feedback_id):
    """把意见标记为已处理"""
    with _lock:
        conn = _connect()
        try:
            conn.execute("UPDATE feedback SET status='done' WHERE id=?", (feedback_id,))
            conn.commit()
        finally:
            conn.close()

def ensure_feedback_reply_col():
    """兼容迁移：旧 feedback 表补 reply 列"""
    with _lock:
        conn = _connect()
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()]
            if "reply" not in cols:
                conn.execute("ALTER TABLE feedback ADD COLUMN reply TEXT DEFAULT ''")
                conn.commit()
        finally:
            conn.close()

def get_feedback_with_reply(status="replied", limit=10):
    """查询已回复待广播的意见(reply 非空)"""
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT id, qq_id, group_id, content, reply FROM feedback "
                "WHERE reply != '' AND status='replied' ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
            return rows
        finally:
            conn.close()

def mark_feedback_broadcast(feedback_id):
    """意见已广播到群，状态改为 done"""
    with _lock:
        conn = _connect()
        try:
            conn.execute("UPDATE feedback SET status='done' WHERE id=?", (feedback_id,))
            conn.commit()
        finally:
            conn.close()

