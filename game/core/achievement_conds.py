# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - achievement_conds.py（v99.5：成就条件注册表）

消灭 core/achievements.py cond_met() 的 41 种类型 if 硬编码：
成就数据只声明 cond={"type": ..., "value": ...}，判定统一走本模块注册表。

扩展方式：
- 加成就条件类型：register 一个函数（~5 行），之后成就数据直接可用
- 函数签名：fn(player, stats, profs, extra, cond) -> bool
  player 玩家 dict / stats 统计 dict / profs 副业 dict / extra 事件上下文 / cond 条件 dict
- 未知 type / 异常 → False（与旧 if 链兜底一致，由调用方 cond_met 统一 try/except）

约定：
- db 访问在函数内延迟 import（防 core→content→core 循环）
- 原代码"受限返回 False"的类型（faction/event_all/goblin_trade）原样保留
- quest_done/main_done 原代码引用了未定义变量（NameError→False 的历史行为），
  注册表保持同款代码，行为零变化
"""
COND_CHECKS = {}


def register(key):
    """条件注册装饰器。"""
    def deco(fn):
        COND_CHECKS[key] = fn
        return fn
    return deco


def _value(cond):
    return cond.get("value", 0)


# ================= 角色成长类 =================

@register("registered")
def _c_registered(player, stats, profs, extra, cond):
    """已注册角色"""
    return bool(player)


@register("level")
def _c_level(player, stats, profs, extra, cond):
    """达到等级"""
    return player.get("level", 0) >= _value(cond)


@register("evolve")
def _c_evolve(player, stats, profs, extra, cond):
    """转职阶数"""
    return player.get("evolve_path", 0) >= _value(cond)


@register("learned")
def _c_learned(player, stats, profs, extra, cond):
    """学习技能数"""
    return len(player.get("learned_skills", []) or []) >= _value(cond)


@register("learned_all")
def _c_learned_all(player, stats, profs, extra, cond):
    """学完全职业技能"""
    from .. import content as C
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


@register("skill_has")
def _c_skill_has(player, stats, profs, extra, cond):
    """习得指定关键词技能"""
    from .. import content as C
    learned = [C.display("skills", s) for s in (player.get("learned_skills", []) or []) if s]
    return any(cond.get("keyword", "") in s for s in learned)


@register("hidden_class")
def _c_hidden_class(player, stats, profs, extra, cond):
    """解锁隐藏职业"""
    return cond.get("key") in (player or {}).get("hidden_class_unlock", [])


@register("hidden_class_lv")
def _c_hidden_class_lv(player, stats, profs, extra, cond):
    """隐藏职业达到等级"""
    return (player or {}).get("class_name") == cond.get("key") and (player or {}).get("level", 0) >= cond.get("value", 0)


# ================= 战斗统计类 =================

@register("kills")
def _c_kills(player, stats, profs, extra, cond):
    """击杀数（no_death 时要求零死亡）"""
    if cond.get("no_death"):
        return stats.get("kills", 0) >= _value(cond) and stats.get("deaths", 0) == 0
    return stats.get("kills", 0) >= _value(cond)


@register("elite")
def _c_elite(player, stats, profs, extra, cond):
    """精英击杀数"""
    return stats.get("elite_kills", 0) >= _value(cond)


@register("boss")
def _c_boss(player, stats, profs, extra, cond):
    """Boss 击杀数"""
    return stats.get("boss_kills", 0) >= _value(cond)


@register("kills_type")
def _c_kills_type(player, stats, profs, extra, cond):
    """指定怪物类型击杀"""
    from .achievements import _bestiary_kills  # 延迟引用（运行时 achievements 已加载）
    kws = cond.get("keywords") or [cond["keyword"]]
    return any(_bestiary_kills(player["qq_id"], kw) >= _value(cond) for kw in kws)


# ================= 副业/养成类 =================

@register("prof_lv")
def _c_prof_lv(player, stats, profs, extra, cond):
    """副业等级"""
    p = (profs or {}).get(cond["key"], {})
    return int(p.get("lv", 0) or 0) >= _value(cond)


@register("prof_any10")
def _c_prof_any10(player, stats, profs, extra, cond):
    """任意副业 10 级"""
    return any(int(p.get("lv", 0) or 0) >= 10 for p in (profs or {}).values())


@register("prof_count")
def _c_prof_count(player, stats, profs, extra, cond):
    """副业次数统计"""
    return stats.get(cond["key"], 0) >= _value(cond)


@register("apprentice")
def _c_apprentice(player, stats, profs, extra, cond):
    """收徒数"""
    return len(player.get("apprentices", []) or []) >= _value(cond)


@register("set_has")
def _c_set_has(player, stats, profs, extra, cond):
    """装备套装收集数"""
    eqs = (player or {}).get("equipment", {}) or {}
    cnt = 0
    for _slot, _eq in eqs.items():
        if isinstance(_eq, dict) and _eq.get("set") == cond.get("key"):
            cnt += 1
    return cnt >= cond.get("value", 4)


# ================= 地图/副本类 =================

@register("visited")
def _c_visited(player, stats, profs, extra, cond):
    """到访区域数"""
    from .. import db
    try:
        return db.get_visited_count("", player["qq_id"]) >= _value(cond)
    except Exception:
        return stats.get("visited_areas", 0) >= _value(cond)


@register("hidden_area")
def _c_hidden_area(player, stats, profs, extra, cond):
    """隐藏区域数（并入到访计数，数据源受限）"""
    from .. import db
    try:
        return db.get_visited_count("", player["qq_id"]) >= _value(cond)
    except Exception:
        return stats.get("visited_areas", 0) >= _value(cond)


@register("inst_clear")
def _c_inst_clear(player, stats, profs, extra, cond):
    """副本通关数"""
    return stats.get("inst_clears", 0) >= _value(cond)


@register("inst_id")
def _c_inst_id(player, stats, profs, extra, cond):
    """通关指定副本"""
    return bool(extra.get("inst_ids", set()) and cond.get("inst") in extra["inst_ids"])


@register("inst_all8")
def _c_inst_all8(player, stats, profs, extra, cond):
    """通关全部 8 副本"""
    return len(extra.get("inst_ids", set()) or set()) >= 8


@register("flawless")
def _c_flawless(player, stats, profs, extra, cond):
    """无伤通关（extra）"""
    return bool(extra.get("flawless"))


# ================= 图鉴/收集类 =================

@register("bestiary")
def _c_bestiary(player, stats, profs, extra, cond):
    """图鉴收集数"""
    from .. import db
    return len(db.get_bestiary("", player["qq_id"])) >= _value(cond)


@register("bestiary_all")
def _c_bestiary_all(player, stats, profs, extra, cond):
    """图鉴全收集"""
    from .. import db
    from .achievements import _monster_total  # 延迟引用（运行时 achievements 已加载）
    return len(db.get_bestiary("", player["qq_id"])) >= _monster_total()


@register("item_has")
def _c_item_has(player, stats, profs, extra, cond):
    """持有指定物品（v100.3b 修复：原代码引用未定义 group_id → NameError→False 恒 False）
    key 为装备 id（如 eq_starfall_sword）或物品名；背包与已装备槽位双查。"""
    gid = extra.get("_group_id")
    if not gid:
        return False  # 无群上下文时保持旧行为（恒 False）
    from .. import db
    from ..data.equip_roster import EQUIP_ROSTER
    key = cond.get("key")
    name = EQUIP_ROSTER.get(key, {}).get("name", key)
    if db.count_item(gid, player["qq_id"], name) > 0:
        return True
    for slot, item in (player.get("equipment") or {}).items():
        if item and item.get("name") == name:
            return True
    return False


@register("hidden_monsters_all")
def _c_hidden_monsters_all(player, stats, profs, extra, cond):
    """击败全部隐藏怪物"""
    hm = extra.get("defeated_hidden_monsters") or set()
    from ..data.hidden_monsters import HIDDEN_MONSTERS
    return len(hm & set(HIDDEN_MONSTERS.keys())) >= len(HIDDEN_MONSTERS)


# ================= 社交/公会类 =================

@register("party")
def _c_party(player, stats, profs, extra, cond):
    """组队次数"""
    return stats.get("party_count", 0) >= _value(cond)


@register("guild")
def _c_guild(player, stats, profs, extra, cond):
    """加入公会"""
    from .. import db
    return bool(db.guild_get_by_member(player["qq_id"]))


@register("guild_lv")
def _c_guild_lv(player, stats, profs, extra, cond):
    """公会等级"""
    from .. import db
    g = db.guild_get_by_member(player["qq_id"])
    return bool(g) and int(g.get("level", 0) or 0) >= _value(cond)


@register("faction")
def _c_faction(player, stats, profs, extra, cond):
    return False  # 国战延迟（11 章）


@register("faction_top")
def _c_faction_top(player, stats, profs, extra, cond):
    return False  # 国战延迟（11 章）


@register("faction_rank1")
def _c_faction_rank1(player, stats, profs, extra, cond):
    return False  # 国战延迟（11 章）


# ================= 世界事件/活动类 =================

@register("world_event")
def _c_world_event(player, stats, profs, extra, cond):
    """参与世界事件数"""
    return stats.get("world_events", 0) >= _value(cond)


@register("event_all")
def _c_event_all(player, stats, profs, extra, cond):
    return False  # 世界事件全触发记录受限


@register("fish_king")
def _c_fish_king(player, stats, profs, extra, cond):
    """钓到鱼王（extra）"""
    return bool(extra.get("fish_king"))


@register("collect_fish")
def _c_collect_fish(player, stats, profs, extra, cond):
    """钓到指定鱼（extra）"""
    return extra.get("collect_fish") == cond.get("key")


@register("wish_met")
def _c_wish_met(player, stats, profs, extra, cond):
    """许愿实现（extra）"""
    return bool(extra.get("wish_met"))


@register("worldboss")
def _c_worldboss(player, stats, profs, extra, cond):
    """参与世界 Boss（extra）"""
    return bool(extra.get("worldboss"))


@register("goblin_trade")
def _c_goblin_trade(player, stats, profs, extra, cond):
    return False  # 地精商人交易记录受限


# ================= 任务/剧情类 =================

@register("quest_done")
def _c_quest_done(player, stats, profs, extra, cond):
    """已完成隐藏任务（v100.3b 修复：原代码引用未定义 group_id → NameError→False 恒 False）
    优先走 extra 显式上下文；否则查 quests.side[key].status == \"done\"。"""
    if extra.get("quest_done") == cond.get("key"):
        return True
    gid = extra.get("_group_id")
    if not gid:
        return False  # 无群上下文时保持旧行为（恒 False）
    from .. import db
    q = db.get_quests(gid, player["qq_id"])
    return bool(q and q.get("side", {}).get(cond.get("key"), {}).get("status") == "done")


@register("main_done")
def _c_main_done(player, stats, profs, extra, cond):
    """主线完成"""
    from .. import db
    q = db.get_quests(player["qq_id"])
    return bool(q and q.get("completed_main"))


@register("flag")
def _c_flag(player, stats, profs, extra, cond):
    """剧情标记（extra.flags）"""
    flags = extra.get("flags") or {}
    return bool(flags.get(cond.get("flag")))
