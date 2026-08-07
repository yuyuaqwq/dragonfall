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
    """地图怪物去重总数（图鉴全解锁判定）"""
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


def cond_met(player: dict, stats: dict, profs: dict, extra: dict, cond: dict) -> bool:
    """成就条件判定。extra 携带事件上下文（inst_id/flawless/worldboss/flags 等）"""
    from .. import content as C
    from .. import db
    t = cond.get("type")
    value = cond.get("value", 0)
    try:
        if t == "registered":
            return bool(player)
        if t == "level":
            return player.get("level", 0) >= value
        if t == "kills":
            if cond.get("no_death"):
                return stats.get("kills", 0) >= value and stats.get("deaths", 0) == 0
            return stats.get("kills", 0) >= value
        if t == "elite":
            return stats.get("elite_kills", 0) >= value
        if t == "boss":
            return stats.get("boss_kills", 0) >= value
        if t == "kills_type":
            kws = cond.get("keywords") or [cond["keyword"]]
            return any(_bestiary_kills(player["qq_id"], kw) >= value for kw in kws)
        if t == "evolve":
            return player.get("evolve_path", 0) >= value
        if t == "learned":
            return len(player.get("learned_skills", []) or []) >= value
        if t == "learned_all":
            total = 0
            cls = player.get("class_name", "")
            t1 = C.PLAYER_SKILLS.get(cls, {})
            if isinstance(t1, dict) and "skills" in t1:
                total += len(t1["skills"])
            bt = C.BRANCH_SKILLS.get(cls, {})
            if isinstance(bt, dict) and "branches" in bt:
                for tier in bt["branches"].values():
                    for skills in tier.values():
                        total += len(skills)
            return total > 0 and len(player.get("learned_skills", []) or []) >= total
        if t == "prof_lv":
            p = (profs or {}).get(cond["key"], {})
            return int(p.get("lv", 0) or 0) >= value
        if t == "prof_any10":
            return any(int(p.get("lv", 0) or 0) >= 10 for p in (profs or {}).values())
        if t == "prof_count":
            return stats.get(cond["key"], 0) >= value
        if t == "apprentice":
            return len(player.get("apprentices", []) or []) >= value
        if t == "visited":
            try:
                return db.get_visited_count("", player["qq_id"]) >= value
            except Exception:
                return stats.get("visited_areas", 0) >= value
        if t == "hidden_area":
            try:
                return db.get_visited_count("", player["qq_id"]) >= value  # 隐藏区域并入到访计数（数据源受限）
            except Exception:
                return stats.get("visited_areas", 0) >= value
        if t == "inst_clear":
            return stats.get("inst_clears", 0) >= value
        if t == "inst_id":
            return bool(extra.get("inst_ids", set()) and cond.get("inst") in extra["inst_ids"])
        if t == "inst_all8":
            return len(extra.get("inst_ids", set()) or set()) >= 8
        if t == "flawless":
            return bool(extra.get("flawless"))
        if t == "worldboss":
            return bool(extra.get("worldboss"))
        if t == "bestiary":
            return len(db.get_bestiary("", player["qq_id"])) >= value
        if t == "bestiary_all":
            return len(db.get_bestiary("", player["qq_id"])) >= _monster_total()
        if t == "party":
            return stats.get("party_count", 0) >= value
        if t == "guild":
            return bool(db.guild_get_by_member(player["qq_id"]))
        if t == "guild_lv":
            g = db.guild_get_by_member(player["qq_id"])
            return bool(g) and int(g.get("level", 0) or 0) >= value
        if t in ("faction", "faction_top", "faction_rank1"):
            return False  # 国战延迟（11 章）
        if t == "world_event":
            return stats.get("world_events", 0) >= value
        if t == "event_all":
            return False  # 世界事件全触发记录受限
        if t == "fish_king":
            return bool(extra.get("fish_king"))
        if t == "collect_fish":
            return extra.get("collect_fish") == cond.get("key")
        if t == "wish_met":
            return bool(extra.get("wish_met"))
        if t == "hidden_class":
            return cond.get("key") in (player or {}).get("hidden_class_unlock", [])
        if t == "hidden_class_lv":
            return (player or {}).get("class_name") == cond.get("key") and (player or {}).get("level", 0) >= cond.get("value", 0)



        if t == "main_done":
            q = db.get_quests(player["qq_id"])
            return bool(q and q.get("completed_main"))
        if t == "flag":
            flags = extra.get("flags") or {}
            return bool(flags.get(cond.get("flag")))
        if t == "goblin_trade":
            return False  # 地精商人交易记录受限
        if t == "skill_has":
            learned = [C.display("skills", s) for s in (player.get("learned_skills", []) or []) if s]
            return any(cond.get("keyword", "") in s for s in learned)
    except Exception:
        return False
    return False


def achievement_titles(qq_id) -> list:
    """已解锁成就的称号名列表（14 章：达成成就自动获得称号）"""
    from .. import content as C
    from .. import db
    try:
        rows = db.get_achievements("", qq_id)
        unlocked = {r["ach_key"] for r in rows}
    except Exception:
        return []
    return [a["title"] for a in C.ACHIEVEMENTS if a["id"] in unlocked and a.get("title")]


def achievement_points(qq_id) -> int:
    """成就点（普通 1 / 隐藏 2）"""
    from .. import content as C
    from .. import db
    try:
        rows = db.get_achievements("", qq_id)
        unlocked = {r["ach_key"] for r in rows}
    except Exception:
        return 0
    return sum(2 if a.get("cat") == "隐藏" else 1 for a in C.ACHIEVEMENTS if a["id"] in unlocked)


def check_achievements(group_id, qq_id, player=None, extra=None) -> list:
    """通用成就判定：事件后调用。返回本次新解锁的成就（dict）列表。"""
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
            if cond_met(player, stats, profs, extra, a["cond"]):
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
