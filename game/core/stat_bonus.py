# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - stat_bonus.py（v105 M01#11，N5b4-4 泛化正名）

**外部面板数值增幅聚合器**（鱼鱼 2026-09-08 拍板：新增纯数值增幅系统不改战斗引擎）。

来源（全部是"纯 flat 数值"，加进面板）：
- 副业大师称号/成就称号（TITLES/ACHIEVEMENTS bonus）
- 收藏册满套 bonus（v174）
- 【未来新增来源：挂件/时装/符文等——只在这个函数加一路，引擎/battle2/命令层零改动】

⚠️ 边界：机制型效果（触发/条件/事件）不走这里——走 battle2 装配层
（actor.triggers + 事件总线，N9/N9A 通用通道）。本聚合器只产 flat 数值 dict
（如 {"atk": 15, "spd": 10}），由命令层开战时塞进 actor["stat_bonus"]。

命名迁移：v105 原名 title_bonus（只聚合称号）；v174 并入收藏册后语义已是
"外部增幅"，N5b4-4 正名 stat_bonus。命令层 _title_bonus 方法名与
engine.player_final_stats 的 title_bonus 位置参数保留（旧引擎冻结区，N10 删旧收敛）。

独立于命令层：commands/base.py:_title_bonus 与 store/players.py 惰性升级共用
同一实现，避免 get_player 读档升级重算 max_hp 时缺称号加成（存档上限 < 面板
计算值，升级回满血只回到旧上限，面板长期"生命 861/891"不满）。
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


def stat_bonus(group_id, qq_id, player=None) -> dict:
    """外部面板数值增幅聚合（称号加成 + 成就称号 + 收藏册满套；未来纯数值来源加这里）。

    与 commands/base.py 旧 _title_bonus 同逻辑（TITLES 加成 + 成就加成 +
    M18 同名去重 + v174 收藏册）；失败静默返回 {}（与旧实现一致）。
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
        # v174 收藏册满套 bonus 实装（此前数据登记但从不生效，死数据）：
        # 集齐 = 册条目 key/name 命中「曾拥有 possessed」或「图鉴击杀怪名」（与 collection.py
        # _book_progress 同口径，但读 possessed 而非当前背包——卖掉/用掉仍算收集过）
        _book_bonus = _collection_completed_bonus(qq_id, player)
        for k, v in _book_bonus.items():
            bonus[k] = bonus.get(k, 0) + v
    except Exception:
        import logging
        logging.getLogger("astrbot").warning("[dragonfall] title_bonus 计算异常，称号加成降级为空", exc_info=True)
        pass
    return bonus


def _collection_completed_bonus(qq_id: str, player: dict) -> dict:
    """收藏册已集齐册的永久属性汇总（v174 实装）。

    读 possessed（曾拥有 key）+ ITEMS/MATERIALS 名映射 + bestiary（击杀图鉴怪 key/名）
    判断条目收集；集齐册的 reward.bonus 累加。失败安全返回 {}（不影响其他加成）。
    """
    bonus = {}
    try:
        from .. import content as _C
        from .. import db
        books = list(getattr(_C, "COLLECTION_BOOKS", None) or [])
        if not books:
            return bonus
        poss = set()
        # 曾拥有物品 key（possessed 表）
        try:
            poss |= set(db.get_possessed(qq_id) or set())
        except Exception:
            pass
        # key → 显示名映射（收藏册条目常用中文名，把曾拥有 key 的中文名也纳入）
        try:
            for _ik in list(poss):
                if _ik in _C.ITEMS:
                    poss.add(str(_C.ITEMS[_ik].get("name", "")))
                elif _ik in _C.MATERIALS:
                    poss.add(str(_C.MATERIALS[_ik].get("name", "")))
        except Exception:
            pass
        # 图鉴击杀怪名（key + display 名）
        try:
            for r in db.get_bestiary("", qq_id) or []:
                _mk = str(r.get("monster") or "")
                poss.add(_mk)
                try:
                    poss.add(str(_C.display("monsters", _mk)))
                except Exception:
                    pass
        except Exception:
            pass
        for b in books:
            entries = b.get("entries") or []
            if not entries:
                continue
            got = sum(1 for e in entries
                      if (e.get("key") and str(e["key"]) in poss)
                      or (e.get("name") and str(e["name"]) in poss))
            if got == len(entries) and b.get("reward", {}).get("bonus"):
                for k, v in b["reward"]["bonus"].items():
                    bonus[k] = bonus.get(k, 0) + float(v)
    except Exception:
        pass
    return bonus
