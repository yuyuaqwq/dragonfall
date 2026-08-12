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
    """成就点(普通 1 / 隐藏 2)。

    ⚠️ 14 章四「成就等级体系（青铜→传奇）」待后续版本，未实装：当前只算点数，
    无等级划分/等级称号/等级加成。（v105 M18 P2 标注，见 AUDIT_FINDINGS_v104 P2-8）
    """
    from .. import content as C
    from .. import db
    try:
        rows = db.get_achievements("", qq_id)
        unlocked = {r["ach_key"] for r in rows}
    except Exception:
        return 0
    return sum(2 if a.get("cat") == "隐藏" else 1 for a in C.ACHIEVEMENTS if a["id"] in unlocked)


def check_achievements(group_id, qq_id, player=None, extra=None) -> list:
    """通用成就判定：事件后调用。返回本次新解锁的成就(dict)列表。

    v101.22（鱼鱼拍板）：解锁不再自动发奖励——改为待领取(claimed=0)，
    玩家用『成就 领取』手动领。奖励数值同步下调(新手期 500→100)。
    返回的成就 dict 带 _reward_txt 供调用方提示。
    """
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
                    db.set_achievement(group_id, qq_id, a["id"], 1, 0)  # claimed=0 待领取
                except Exception:
                    continue
                unlocked.add(a["id"])
                rw = a.get("reward") or {}
                if rw.get("exp") or rw.get("gold"):
                    parts = []
                    if rw.get("exp"):
                        parts.append(f"经验+{rw['exp']}")
                    if rw.get("gold"):
                        parts.append(f"金币+{rw['gold']}")
                    a = dict(a)
                    a["_reward_txt"] = "、".join(parts) + "（『成就 领取』领取）"
                else:
                    a = dict(a)
                    a["_reward_txt"] = ""
                new_ones.append(a)
        return new_ones
    except Exception:
        return []


def claim_achievement_rewards(group_id, qq_id) -> tuple:
    """领取全部待领取的成就奖励(经验/金币)。返回 (lines, err) 供命令输出。

    v101.22：成就解锁后奖励待领取，玩家手动『成就 领取』时统一发放，
    发放走 check_player_level_up 正常结算升级。未解锁/无奖励成就忽略。
    """
    from .. import content as C
    from .. import db
    from ..engine import check_player_level_up
    try:
        rows = db.get_achievements(group_id, qq_id) or []
        pending = [r for r in rows if not r.get("claimed")]
        if not pending:
            return [], "没有待领取的成就奖励～"
        # 过滤出真正带奖励的待领成就
        claimable = []
        for r in pending:
            a = next((x for x in C.ACHIEVEMENTS if x["id"] == r["ach_key"]), None)
            # v105.xx P0 修复：原 `if a and X or Y` 优先级错误——a=None（如 inst_clear_* 记录
            # 不在 C.ACHIEVEMENTS 中）时 `or` 右侧仍求值 a.get() → AttributeError 崩溃。
            # 显式括号：a 为 None 时短路，不进入。
            if a and (((a.get("reward") or {}).get("exp", 0)) or ((a.get("reward") or {}).get("gold", 0))):
                claimable.append(a)
        if not claimable:
            # 没有奖励的成就直接标记已领取，避免永久挂起
            for r in pending:
                try:
                    db.set_achievement(group_id, qq_id, r["ach_key"], r.get("progress", 1), 1)
                except Exception:
                    pass
            return [], "没有待领取的成就奖励～"
        player = db.get_player(group_id, qq_id)
        if not player:
            return [], "请先注册角色～"
        player = dict(player)
        player["_title_bonus"] = _title_bonus_plain(group_id, qq_id)
        exp_gain = sum((a.get("reward") or {}).get("exp", 0) for a in claimable)
        gold_gain = sum((a.get("reward") or {}).get("gold", 0) for a in claimable)
        player["exp"] = player.get("exp", 0) + exp_gain
        player["gold"] = player.get("gold", 0) + gold_gain
        lv_logs, player = check_player_level_up(group_id, qq_id, player)
        db.update_player(group_id, qq_id,
                         exp=player["exp"], gold=player["gold"], level=player["level"],
                         hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"],
                         skills=player["skills"], attr_pts=player.get("attr_pts", 0),
                         skill_points=player.get("skill_points", 0),
                         learned_skills=player.get("learned_skills", []))
        for a in claimable:
            db.set_achievement(group_id, qq_id, a["id"], 1, 1)
        lines = [f"🎁 成就奖励领取！经验 +{exp_gain}" + (f" 金币 +{gold_gain}" if gold_gain else "")]
        for a in claimable:
            lines.append(f"🏅 {a['name']}")
        lines.append("")
        lines += lv_logs
        return lines, ""
    except Exception as e:
        import logging
        logging.getLogger("astrbot").warning(f"[dragonfall] 成就领取失败: {e}")
        return [], "领取失败，稍后再试试～"


def _title_bonus_plain(group_id, qq_id):
    """轻量版称号加成计算（避免 import 环）。仅用于领取时的属性快照。"""
    from .. import content as C
    from .. import db
    try:
        base = {"hp": 0, "atk": 0, "def": 0, "matk": 0, "mdef": 0, "spd": 0, "crit": 0.0}
        rows = db.get_achievements("", qq_id) or []
        unlocked = {r["ach_key"] for r in rows}
        for a in C.ACHIEVEMENTS:
            if a.get("bonus") and a["id"] in unlocked:
                for k, v in a["bonus"].items():
                    base[k] = base.get(k, 0) + v
        return base
    except Exception:
        return {}
