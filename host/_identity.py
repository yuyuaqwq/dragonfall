# -*- coding: utf-8 -*-
"""宿主平台身份映射（P5A：`game/commands/_identity.py` 的**平台面**实现）—— openid ⇄ QQ 号。

为什么不是「alias 到包内实现」
------------------------------
旧壳（`game/commands/_identity.py`）是 `sys.modules[__name__] = content._identity`（指向**包内**
实现）。宿主 `host/**` 是**零包知识**面（不 import 任何包内模块；当次实测的 grep 口径与结果见
`out/W-P5A.md` §⑥），所以本文件把同一份**平台映射**（正则 / SQL / 返回形状逐字相同）实现在
宿主侧，落在**同一只库的同一张表** `identity_map` 上（表由存档半边建，DDL 在包内；宿主只读写）。

取件口 = `host/store_factory`（库路径 + 连接 + 单进程锁的宿主落点）：
    · `store_factory.STORE.connect()` = 存档半边的连接（与包内 `handles.connect` **同一只**）
    · `store_factory.STORE.lock()`    = 同一个 RLock（`with lock:` 与旧壳逐语义相同）

与包内 `content/_identity.py` 的关系（如实登记，不静默）：两边是**同一张表的两个读写口**
（同一个 `identity_map`、同一个 openid 正则），行为一致；重复的是 SQL 文本而非数据。
终态可由「宿主把身份映射当能力口注入包」收敛（见 out/W-P5A.md「未做项/缺口」）。
"""
from __future__ import annotations

import re
import time

from . import store_factory as _sf

# 腾讯 openid 形如：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx（32 位十六进制，部分带 -）
# QQ 号：5-11 位纯数字
_OPENID_RE = re.compile(r"^[0-9a-fA-F]{24,40}$|^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_QQ_RE = re.compile(r"^\d{5,11}$")


def is_openid(s: str) -> bool:
    """判断字符串是不是腾讯 openid（区别于 QQ 号）。"""
    if not s:
        return False
    s = str(s).strip()
    return bool(_OPENID_RE.match(s))


def is_qq_id(s: str) -> bool:
    return bool(_QQ_RE.match(str(s).strip()))


def bind(openid: str, qq_id: str, platform: str = "qq_official") -> None:
    """绑定 openid ↔ qq_id。已存在则覆盖。"""
    openid = str(openid).strip()
    qq_id = str(qq_id).strip()
    store = _sf.store()
    with store.lock():
        conn = store.connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO identity_map(openid, qq_id, platform, bind_time) "
                "VALUES(?,?,?,?)",
                (openid, qq_id, platform, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()


def unbind_openid(openid: str) -> None:
    store = _sf.store()
    with store.lock():
        conn = store.connect()
        try:
            conn.execute("DELETE FROM identity_map WHERE openid=?", (str(openid).strip(),))
            conn.commit()
        finally:
            conn.close()


def openid_to_qq(openid: str) -> str | None:
    """openid → QQ 号；未绑定返回 None（**非 openid 形状直接返回 None，不碰库**）。"""
    if not is_openid(openid):
        return None
    store = _sf.store()
    with store.lock():
        conn = store.connect()
        try:
            row = conn.execute(
                "SELECT qq_id FROM identity_map WHERE openid=?", (openid.strip(),)
            ).fetchone()
            return str(row[0]) if row else None
        finally:
            conn.close()


def qq_to_openid(qq_id: str, platform: str = "qq_official") -> str | None:
    """QQ 号 → openid（出向投递用）；未绑定返回 None。"""
    qq_id = str(qq_id).strip()
    store = _sf.store()
    with store.lock():
        conn = store.connect()
        try:
            row = conn.execute(
                "SELECT openid FROM identity_map WHERE qq_id=? AND platform=? "
                "ORDER BY bind_time DESC LIMIT 1",
                (qq_id, platform),
            ).fetchone()
            return str(row[0]) if row else None
        finally:
            conn.close()


def resolve_uid(raw: str) -> str:
    """平台标识 → 玩家账号 id：raw 若是已绑定 openid → 返回对应 QQ 号，否则原样返回。"""
    if not raw:
        return raw
    mapped = openid_to_qq(raw)
    return mapped if mapped else raw


def query_all(limit: int = 100) -> list[dict]:
    """列出全部映射（GM 查看用）。返回 [dict(openid, qq_id, platform)]。"""
    store = _sf.store()
    with store.lock():
        conn = store.connect()
        try:
            rows = conn.execute(
                "SELECT openid, qq_id, platform FROM identity_map "
                "ORDER BY bind_time DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
