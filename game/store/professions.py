# -*- coding: utf-8 -*-
"""《剑与魔法》存储层 - professions：副业等级与经验

副业（采集/挖掘/垂钓/炼金/锻造/烹饪）独立成长线：
- 每条副业 Lv.1~10，经验按 20*当前等级 升级（Lv1→2 需 20，Lv2→3 需 40……）
- add_prof_exp 自动处理升级与封顶（Lv.10 满级不再累积）
"""
from .connection import _connect, _lock
from .. import content as C
import json  # v67 activated 列 JSON 序列化

PROF_FIELDS = {
    "gather": "采集",
    "mining": "挖掘",
    "fishing": "垂钓",
    "alchemy": "炼金",
    "craft": "锻造",
    "cooking": "烹饪",
    "enhance": "强化",
    "enchant": "附魔",
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
    if key not in PROF_FIELDS:  # B2 加固（2026-08-10）：动态列名前白名单校验
        raise ValueError(f"add_prof_exp 非法副业: {key}（不在 PROF_FIELDS）")
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
            while lv < 10 and cur >= lv * C.PROF_EXP_BASE:
                cur -= lv * C.PROF_EXP_BASE
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
    """副业总分排行(8 条副业等级之和，v101.28i 补 enhance/enchant)

    v104 修复：按群过滤（JOIN player_groups，口径同 get_group_players）——
    群 A 排行不再串入群 B 玩家；私聊(无群)退化为全服排行。
    """
    with _lock:
        conn = _connect()
        try:
            _sum = ("gather_lv+mining_lv+fishing_lv+alchemy_lv+craft_lv"
                    "+cooking_lv+enhance_lv+enchant_lv AS total")
            if group_id and group_id != "private":
                rows = conn.execute(
                    "SELECT pr.qq_id, pr." + _sum + " "
                    "FROM professions pr JOIN player_groups g ON pr.qq_id=g.qq_id "
                    "WHERE g.group_id=? ORDER BY total DESC, pr.qq_id LIMIT ?",
                    (group_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT qq_id, " + _sum + " "
                    "FROM professions ORDER BY total DESC, qq_id LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


# ---------- v67 双副业上限 ----------

MAX_ACTIVE_PROFS = 2


def get_activated_profs(group_id, qq_id):
    """已激活的副业 key 列表(v67：每人最多发展 2 条)"""
    with _lock:
        conn = _connect()
        try:
            _ensure_prof_row(conn, qq_id)
            conn.commit()
            row = conn.execute(
                "SELECT activated FROM professions WHERE qq_id=?", (qq_id,)
            ).fetchone()
            raw = (row["activated"] if row else "") or "[]"
            try:
                import json
                lst = json.loads(raw)
                return [k for k in lst if k in PROF_FIELDS] if isinstance(lst, list) else []
            except (ValueError, TypeError):
                return []
        finally:
            conn.close()


def activate_prof(group_id, qq_id, key):
    """激活副业(幂等)。返回 True=本次新激活；False=已在激活列表或非法 key"""
    if key not in PROF_FIELDS:
        return False
    lst = get_activated_profs(group_id, qq_id)
    if key in lst:
        return False
    lst.append(key)
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE professions SET activated=? WHERE qq_id=?",
                (json.dumps(lst, ensure_ascii=False), qq_id),
            )
            conn.commit()
        finally:
            conn.close()
    return True


def forget_prof(group_id, qq_id, key):
    """遗忘副业：移除激活 + 等级/经验清零 + 清学徒资格(拜师记录)。

    v104 P0 修复：遗忘后必须同时从 players.apprentices 移除该副业——
    否则再激活免拜师，且 附魔 Lv.1 被 Lv.2 门槛拦截、唯一经验来源被堵，
    永久卡 Lv.1 死锁。8 副业全路径生效（enhance/enchant 同表逻辑）。
    返回旧等级
    """
    if key not in PROF_FIELDS:  # B2 加固（2026-08-10）：动态列名前白名单校验
        return None
    lst = get_activated_profs(group_id, qq_id)
    if key not in lst:
        return None
    lst.remove(key)
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                f"SELECT {key}_lv AS lv FROM professions WHERE qq_id=?", (qq_id,)
            ).fetchone()
            old_lv = row["lv"] if row else 1
            conn.execute(
                f"UPDATE professions SET activated=?, {key}_lv=1, {key}_exp=0 WHERE qq_id=?",
                (json.dumps(lst, ensure_ascii=False), qq_id),
            )
            # v104 P0：同步清 players.apprentices 里的拜师资格（防附魔遗忘死锁）
            try:
                prow = conn.execute(
                    "SELECT apprentices FROM players WHERE qq_id=?", (qq_id,)
                ).fetchone()
                appr = []
                if prow and prow["apprentices"]:
                    try:
                        appr = json.loads(prow["apprentices"])
                    except (ValueError, TypeError):
                        appr = []
                if key in appr:
                    appr.remove(key)
                    conn.execute(
                        "UPDATE players SET apprentices=? WHERE qq_id=?",
                        (json.dumps(appr, ensure_ascii=False), qq_id),
                    )
            except Exception:
                pass  # 玩家表/列异常不阻断遗忘主流程（等级清零已生效）
            conn.commit()
            return old_lv
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
