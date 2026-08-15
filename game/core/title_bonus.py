# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - title_bonus.py（v105 M01#11）

副业大师称号/成就称号的属性加成汇总，独立于命令层：
- commands/base.py:_title_bonus 与 store/players.py 惰性升级共用同一实现，
  避免 get_player 读档升级重算 max_hp 时缺称号加成（存档上限 < 面板计算值，
  升级回满血只回到旧上限，面板长期"生命 861/891"不满）。
- 逻辑与 base.py 旧实现逐行等价（TITLES 加成 + 成就加成 + M18 同名去重）。
- player 参数：已加载玩家 dict 时传入，避免重复读档（get_player 持锁调用必须传）。
"""
from .. import content as C


def _visited_maps(group_id, qq_id):
    """已探索地图 id 列表（独立直连，不占用 store 锁）。"""
    import sqlite3
    from .. import db
    try:
        conn = sqlite3.connect(db.DB_PATH)
        rows = conn.execute("SELECT map_id FROM visited WHERE qq_id=?", (qq_id,)).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []


def _has_enhanced(group_id, qq_id, level):
    """背包中是否有强化 ≥level 的装备（独立直连，不占用 store 锁）。"""
    import json
    import sqlite3
    from .. import db
    try:
        conn = sqlite3.connect(db.DB_PATH)
        rows = conn.execute(
            "SELECT item_data FROM inventory WHERE qq_id=?", (qq_id,)).fetchall()
        conn.close()
        for r in rows:
            try:
                d = json.loads(r[0] or "{}")
                if d.get("enhance", 0) >= level:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def title_bonus(group_id, qq_id, player=None) -> dict:
    """称号属性加成汇总（Lv.10 称号 bonus 叠加 + 阶段九成就称号 bonus）。

    与 commands/base.py:_title_bonus 同逻辑；失败静默返回 {}（与旧实现一致）。
    """
    bonus = {}
    try:
        from .. import db
        from .title_conds import TitleCtx, CONDITIONS, check_pro_title
        if player is None:
            player = db.get_player(group_id, qq_id) or {}
        stats = db.get_stats(group_id, qq_id) or {}
        rep = db.get_reputation(group_id, qq_id)
        quests = db.get_quests(group_id, qq_id)
        ctx = TitleCtx(group_id, qq_id, player, stats, rep, quests, hooks={
            "has_enhanced": _has_enhanced,
            "visited_maps": _visited_maps,
        })
        earned = []
        for t in C.TITLES:
            tid = t["id"]
            fn = CONDITIONS.get(tid)
            if fn is not None:
                ok = fn(ctx)
            elif tid.startswith("pro_"):
                ok = check_pro_title(tid, ctx)
            else:
                ok = False  # 未知称号 id：不获得（数据错误时安全降级）
            earned.append(ok)
        for i, t in enumerate(C.TITLES):
            if earned[i] and t.get("bonus"):
                for k, v in t["bonus"].items():
                    bonus[k] = bonus.get(k, 0) + v
        # 阶段九：成就称号 bonus（14 章 3.3，达成即生效）
        # M18 修复：跳过与 TITLES 同名且带 bonus 的成就（副业 Lv.10 大师称号已由上方
        # TITLES 段累加，成就侧 ach_pro_*10 为同一称号的重复数据 → 跳过避免双倍发放）
        title_bonus_names = {t["name"] for t in C.TITLES if t.get("bonus")}
        try:
            unlocked_achs = {r["ach_key"] for r in db.get_achievements("", qq_id)}
        except Exception:
            unlocked_achs = set()
        for a in C.ACHIEVEMENTS:
            if a.get("bonus") and a["id"] in unlocked_achs and a.get("name") not in title_bonus_names:
                for k, v in a["bonus"].items():
                    if k == "prof_exp_mult":
                        continue  # v104.2 M13：全知全能副业经验倍率由 add_prof_exp 结算，非面板属性
                    if k != "atk" or v != 0:  # 占位字段跳过
                        bonus[k] = bonus.get(k, 0) + v
    except Exception:
        import logging
        logging.getLogger("astrbot").warning("[dragonfall] title_bonus 计算异常，称号加成降级为空", exc_info=True)
        pass
    return bonus
