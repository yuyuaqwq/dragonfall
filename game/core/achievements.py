# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - achievements.py（阶段九：成就系统，14 章）

- cond_met(player, stats, profs, extra, cond)：单条条件判定
- check_achievements(group_id, qq_id)：遍历 97 成就，满足且未解锁 → 解锁 + 发奖励
- achievement_titles(qq_id)：已解锁成就的称号名列表（与 titles.py TITLES 合并成称号总表）
- achievement_points(qq_id)：成就点计算（普通 1 / 隐藏 2）

⚠️ 本模块在 core 聚合链内，禁止顶层 import content/engine（循环导入），一律函数内延迟导入。
数据源：players（level/evolve_path/learned_skills/apprentices/gold）、
stats 表（kills/elite/boss/visited_areas/inst_clears/party_count/副业次数/world_events）、
professions 表（副业等级）、quests（completed_main）、bestiary（击杀/图鉴）、
achievements 表（已解锁 + inst_clear_* 记录）。
"""


def _bestiary_kills(qq_id, keyword) -> int:
    """bestiary 按怪物名关键词统计击杀数"""
    from .. import content as C
    from .. import db
    try:
        rows = db.get_bestiary("", qq_id)
    except Exception:
        return 0
    total = 0
    for r in rows:
        name = C.display("monsters", r["monster"])
        if keyword in (name or ""):
            total += int(r.get("kills", 0) or 0)
    return total


def _monster_total() -> int:
    """地图怪物去重总数(图鉴全解锁判定)"""
    from .. import content as C
    from .. import db
    try:
        ids = set()
        for mid, m in C.MAP_BY_ID.items():
            for mon in (m.get("monsters") or []):
                if isinstance(mon, dict):
                    ids.add(mon.get("id") or mon.get("name"))
                else:
                    ids.add(mon)
        return max(len(ids), 100)
    except Exception:
        return 150


def cond_met(player: dict, stats: dict, profs: dict, extra: dict, cond: dict, group_id: str = None) -> bool:
    """成就条件判定。extra 携带事件上下文(inst_id/flawless/worldboss/flags 等)
    v99.5：判定逻辑数据化 → core/achievement_conds.py COND_CHECKS 注册表
    （41 种条件类型；未知 type / 异常 → False，与旧 if 链兜底一致）
    v100.3b：新增可选 group_id —— 非 None 时注入 extra['_group_id'] 副本，
    供 quest_done/item_has 查询任务/背包（原代码引用未定义 group_id → 恒 False 的历史 bug）"""
    try:
        from .achievement_conds import COND_CHECKS
        fn = COND_CHECKS.get(cond.get("type"))
        if fn is None:
            return False
        if group_id is not None and extra.get("_group_id") is None:
            extra = dict(extra)
            extra["_group_id"] = group_id
        return fn(player, stats, profs, extra, cond)
    except Exception:
        return False


def achievement_titles(qq_id) -> list:
    """已解锁成就的称号名列表(14 章：达成成就自动获得称号)"""
    from .. import content as C
    from .. import db
    try:
        rows = db.get_achievements("", qq_id)
        unlocked = {r["ach_key"] for r in rows}
    except Exception:
        return []
    return [a["title"] for a in C.ACHIEVEMENTS if a["id"] in unlocked and a.get("title")]


def achievement_points(qq_id) -> int:
    """成就点(普通 1 / 隐藏 2)"""
    from .. import content as C
    from .. import db
    try:
        rows = db.get_achievements("", qq_id)
        unlocked = {r["ach_key"] for r in rows}
    except Exception:
        return 0
    return sum(2 if a.get("cat") == "隐藏" else 1 for a in C.ACHIEVEMENTS if a["id"] in unlocked)


def check_achievements(group_id, qq_id, player=None, extra=None) -> list:
    """通用成就判定：事件后调用。返回本次新解锁的成就(dict)列表。"""
    from .. import content as C
    from .. import db
    try:
        if player is None:
            player = db.get_player(group_id, qq_id)
        if not player:
            return []
        player["qq_id"] = player.get("qq_id") or qq_id
        stats = db.get_stats(group_id, qq_id) or {}
        profs = db.get_professions(group_id, qq_id) or {}
        extra = extra or {}
        unlocked = set()
        try:
            rows = db.get_achievements("", qq_id)
            unlocked = {r["ach_key"] for r in rows}
        except Exception:
            pass
        # 已通关副本集合（inst_clear_* 记录）
        inst_ids = set()
        for aid in unlocked:
            if str(aid).startswith("inst_clear_"):
                inst_ids.add(str(aid)[len("inst_clear_"):])
        if extra.get("inst_id"):
            inst_ids.add(extra["inst_id"])
        extra["inst_ids"] = inst_ids
        new_ones = []
        for a in C.ACHIEVEMENTS:
            if a["id"] in unlocked:
                continue
            if cond_met(player, stats, profs, extra, a["cond"], group_id):
                try:
                    db.set_achievement(group_id, qq_id, a["id"], 1, 1)
                except Exception:
                    continue
                unlocked.add(a["id"])
                new_ones.append(a)
                # 奖励发放（经验/金币）
                rw = a.get("reward") or {}
                if rw.get("exp"):
                    db.update_player(group_id, qq_id, exp=player.get("exp", 0) + rw["exp"])
                    player["exp"] = player.get("exp", 0) + rw["exp"]
                if rw.get("gold"):
                    db.update_player(group_id, qq_id, gold=player.get("gold", 0) + rw["gold"])
                    player["gold"] = player.get("gold", 0) + rw["gold"]
        return new_ones
    except Exception:
        return []
