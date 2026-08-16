# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - title_conds.py（v98.3：称号获得条件注册表）

消灭 commands/economy.py _earned_titles() 里的 if-elif 硬编码：
称号数据只声明 id，判定统一走本模块注册表。

扩展方式：
- 加称号：data/titles.py 加一条 dict（id 唯一）+ 本文件 register 一个条件函数
- 函数签名：fn(ctx) -> bool
- ctx 为 TitleCtx（group_id/qq_id/player/stats/rep/quests/hooks）
"""
import re

CONDITIONS = {}


def register(tid):
    """条件注册装饰器。"""
    def deco(fn):
        CONDITIONS[tid] = fn
        return fn
    return deco


class TitleCtx:
    """称号条件判定上下文。hooks 注入命令层专属能力（has_enhanced/visited_maps）。"""

    def __init__(self, group_id, qq_id, player, stats, rep, quests, hooks=None):
        self.group_id = group_id
        self.qq_id = qq_id
        self.player = player or {}
        self.stats = stats or {}
        self.rep = rep or {}
        self.quests = quests or {}
        self.hooks = hooks or {}

    def _db(self):
        from .. import db
        return db

    def hook(self, name, *args, **kwargs):
        fn = self.hooks.get(name)
        if fn:
            return fn(*args, **kwargs)
        return None


# ================= 条件实现 =================

@register("novice")
def _t_novice(ctx):
    return True


@register("lv10")
def _t_lv10(ctx):
    return ctx.player.get("level", 0) >= 10


@register("lv20")
def _t_lv20(ctx):
    return ctx.player.get("level", 0) >= 20


@register("lv30")
def _t_lv30(ctx):
    return ctx.player.get("level", 0) >= 30


@register("kill10")
def _t_kill10(ctx):
    return ctx.stats.get("kills", 0) >= 10


@register("kill100")
def _t_kill100(ctx):
    return ctx.stats.get("kills", 0) >= 100


@register("kill500")
def _t_kill500(ctx):
    return ctx.stats.get("kills", 0) >= 500


@register("elite5")
def _t_elite5(ctx):
    return ctx.stats.get("elite_kills", 0) >= 5


@register("boss1")
def _t_boss1(ctx):
    return ctx.stats.get("boss_kills", 0) >= 1


@register("boss3")
def _t_boss3(ctx):
    return ctx.stats.get("boss_kills", 0) >= 3


@register("rep_honor")
def _t_rep_honor(ctx):
    from .. import content as C
    return any(C.faction_reputation_tier(v) in ("崇敬", "崇拜") for v in ctx.rep.values())


@register("rep_legend")
def _t_rep_legend(ctx):
    from .. import content as C
    return any(C.faction_reputation_tier(v) == "崇拜" for v in ctx.rep.values())


@register("quest10")
def _t_quest10(ctx):
    return len(ctx.quests.get("completed_main", [])) >= 10


@register("wealthy")
def _t_wealthy(ctx):
    return ctx.player.get("gold", 0) >= 5000


@register("explorer")
def _t_explorer(ctx):
    return ctx._db().get_visited_count(ctx.group_id, ctx.qq_id) >= 10


@register("fish10")
def _t_fish10(ctx):
    return ctx._db().get_fishing_total(ctx.group_id, ctx.qq_id) >= 10


@register("enhance5")
def _t_enhance5(ctx):
    return bool(ctx.hook("has_enhanced", ctx.group_id, ctx.qq_id, 5))


@register("enhance9")
def _t_enhance9(ctx):
    return bool(ctx.hook("has_enhanced", ctx.group_id, ctx.qq_id, 9))


@register("hidden")
def _t_hidden(ctx):
    # v124 修复：mithril_hall 已删除（v104 P2 清理死条目）→ 改判真实隐藏区域，
    # 与成就 ach_mythril（hidden_area≥1，achievement_conds.py 已修复）同语义：
    # 到访任一隐藏区域即达成（lost_library / ember_corridor，或 hidden=True 地图）
    from .. import content as C
    visited = ctx.hook("visited_maps", ctx.group_id, ctx.qq_id) or []
    hidden = set(getattr(C, "HIDDEN_MAP_UNLOCK", None) or {})
    for m in (C.MAPS or []):
        if m.get("hidden") or m.get("type") == "隐藏区域":
            hidden.add(m["id"])
    if not hidden:
        return False
    return any(v in hidden for v in visited)


@register("final")
def _t_final(ctx):
    return ctx.quests.get("main_quest") is None and len(ctx.quests.get("completed_main", [])) >= 10


@register("fish_king")
def _t_fish_king(ctx):
    return ctx._db().get_fish_king(ctx.group_id, ctx.qq_id) >= 1


@register("pvp_hero")
def _t_pvp_hero(ctx):
    # 数据源：荣誉商店兑换勋章（26 章 3.3，combat.py _honor_buy 写
    # event_state key = f"honor_{reward['title_id']}_{qq}"，honor_shop.py
    # 第 1 件商品 title_id="medal" → 键 honor_medal_{qq}，与本行读取键一致）
    return int(ctx._db().get_event_state(f"honor_medal_{ctx.qq_id}") or 0) >= 1


# ================= v124 剧情线称号（side 完成判定）=================
def _side_done(ctx, sid):
    """支线完成 = quests.side[sid].status == done"""
    return (ctx.quests.get("side") or {}).get(sid, {}).get("status") == "done"


def _has_flag(ctx, flag):
    """任意 NPC flag 桶含指定 flag（扫描全桶，同 wild.py unlock_met flag: 先例）"""
    from .. import content as _C
    db = ctx._db()
    for nid in list(_C.NPCS.keys()) + list(_C.ALL_WILD.keys()) + list(_C.HIDDEN_NPCS.keys()):
        if flag in db.get_talk_flags(ctx.group_id, ctx.qq_id, nid):
            return True
    return False


@register("north_benefactor")
def _t_north_benefactor(ctx):
    return _side_done(ctx, "s18") and _has_flag(ctx, "s18_branch_light")


@register("nightwalker")
def _t_nightwalker(ctx):
    return _side_done(ctx, "s18") and _has_flag(ctx, "s18_branch_dark")


@register("guifan_seal")
def _t_guifan_seal(ctx):
    return _side_done(ctx, "s27")


@register("dragon_warden")
def _t_dragon_warden(ctx):
    return _side_done(ctx, "s33")


@register("gourmet")
def _t_gourmet(ctx):
    return _side_done(ctx, "s56")


@register("herb_friend")
def _t_herb_friend(ctx):
    return _side_done(ctx, "s60")


@register("treasure_hunter")
def _t_treasure_hunter(ctx):
    return _side_done(ctx, "s64")


@register("furry_friend")
def _t_furry_friend(ctx):
    return _side_done(ctx, "s69")


@register("merchant_friend")
def _t_merchant_friend(ctx):
    return _side_done(ctx, "s74")


@register("just_enforcer")
def _t_just_enforcer(ctx):
    return _side_done(ctx, "s78") and _has_flag(ctx, "s78_branch_justice")


@register("shadow_friend")
def _t_shadow_friend(ctx):
    return _side_done(ctx, "s78") and _has_flag(ctx, "s78_branch_mercy")


@register("dusk_detective")
def _t_dusk_detective(ctx):
    return _side_done(ctx, "s79")


@register("peacemaker")
def _t_peacemaker(ctx):
    return _side_done(ctx, "s84")


@register("guide")
def _t_guide(ctx):
    return _side_done(ctx, "s89")


@register("night_rain")
def _t_night_rain(ctx):
    return _side_done(ctx, "hq5_3")


@register("goose_messenger")
def _t_goose_messenger(ctx):
    return _side_done(ctx, "hq7_3")


@register("forge_son")
def _t_forge_son(ctx):
    return _side_done(ctx, "hq8_4")


@register("graveyard_warden")
def _t_graveyard_warden(ctx):
    return _side_done(ctx, "hq6_3")


@register("fishing_legend")
def _t_fishing_legend(ctx):
    return _side_done(ctx, "s95")


@register("late_messenger")
def _t_late_messenger(ctx):
    return _side_done(ctx, "s100")


@register("season_gardener")
def _t_season_gardener(ctx):
    return _side_done(ctx, "s106")


def check_pro_title(tid: str, ctx) -> bool:
    """副业称号：pro_<prof><lv>（如 pro_gather3）→ 副业等级达标。"""
    m = re.match(r"^pro_([a-z]+)(\d+)$", tid)
    if not m:
        return False
    prof_key, need_lv = m.group(1), int(m.group(2))
    if prof_key in ("gather", "mining", "fishing", "alchemy", "craft", "cooking"):
        return ctx._db().get_prof_level(ctx.group_id, ctx.qq_id, prof_key) >= need_lv
    return False
