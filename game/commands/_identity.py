# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - _identity：平台身份映射（openid ↔ QQ 号）

背景（2026-09-07 鱼鱼拍板换官方 bot）：
  AstrBot 从 NapCat(OneBot v11，事件带真实 QQ 号) 切到 QQ 官方 API(botpy，
  事件只带腾讯 openid：member_openid/user_openid/group_openid)。
  dragonfall 玩家表/公会/市场等全部以 QQ 号为主键 —— 直接换平台会让所有老玩家
  变成"新 openid 陌生人"（注册新号、等级全丢）。

本模块是"中转映射层"：把官方 bot 的 openid 翻译回玩家原本的 QQ 号。
- 入向（事件 → 玩家）：命令层 _uid() 拿到的 sender 若是 openid → 查表换 QQ 号
- 出向（GM/主动投递 → 会话）：GM_OWNER_QQ 等 QQ 号 → 查表换 openid 作 session

认领流程（防冒领，需验证码）：
  玩家在官方 bot 下发『绑定身份 <QQ号> <验证串>』；验证串由老 bot 渠道/管理员
  私下告知（或 GM 用 gm_加身份 <openid> <QQ号> 直接绑定）。
"""

import re
import time

from ..store import connection as _conn

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
    with _conn._lock:
        conn = _conn._connect()
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
    with _conn._lock:
        conn = _conn._connect()
        try:
            conn.execute("DELETE FROM identity_map WHERE openid=?", (str(openid).strip(),))
            conn.commit()
        finally:
            conn.close()


def openid_to_qq(openid: str) -> str | None:
    """openid → QQ 号；未绑定返回 None。"""
    if not is_openid(openid):
        return None
    with _conn._lock:
        conn = _conn._connect()
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
    with _conn._lock:
        conn = _conn._connect()
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
    """命令层统一入口：raw 若是已绑定 openid → 返回对应 QQ 号，否则原样返回。"""
    if not raw:
        return raw
    mapped = openid_to_qq(raw)
    return mapped if mapped else raw


def query_all(limit: int = 100) -> list[dict]:
    """列出全部映射（GM 查看用）。返回 [dict(openid, qq_id, platform)]。"""
    with _conn._lock:
        conn = _conn._connect()
        try:
            rows = conn.execute(
                "SELECT openid, qq_id, platform FROM identity_map "
                "ORDER BY bind_time DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
