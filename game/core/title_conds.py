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
    db = ctx._db()
    visited = ctx.hook("visited_maps", ctx.group_id, ctx.qq_id) or []
    return db.get_visited_count(ctx.group_id, ctx.qq_id) >= 10 and "mithril_hall" in visited


@register("final")
def _t_final(ctx):
    return ctx.quests.get("main_quest") is None and len(ctx.quests.get("completed_main", [])) >= 10


@register("fish_king")
def _t_fish_king(ctx):
    return ctx._db().get_fish_king(ctx.group_id, ctx.qq_id) >= 1


@register("pvp_hero")
def _t_pvp_hero(ctx):
    return int(ctx._db().get_event_state(f"honor_medal_{ctx.qq_id}") or 0) >= 1


def check_pro_title(tid: str, ctx) -> bool:
    """副业称号：pro_<prof><lv>（如 pro_gather3）→ 副业等级达标。"""
    m = re.match(r"^pro_([a-z]+)(\d+)$", tid)
    if not m:
        return False
    prof_key, need_lv = m.group(1), int(m.group(2))
    if prof_key in ("gather", "mining", "fishing", "alchemy", "craft", "cooking"):
        return ctx._db().get_prof_level(ctx.group_id, ctx.qq_id, prof_key) >= need_lv
    return False
