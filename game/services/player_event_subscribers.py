# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 L3 玩家事件订阅方注册（v181 L3-P2 field 试点）

把 combat._handle_victory 壳 L2034-2118 的玩家级手动接线段（公会每日/升级/任务/
周常/野王/塔卫/成就）收敛为 player_event_bus 订阅方。注册序 = 原行序（回填顺序
对照表见 docs/REFACTOR_v181_L3_P0_task.md §5/§6，零文案变化）。

本模块被命令层 fire 点显式 import 一次触发注册（不做 import 魔法）。handler 均为
薄壳：逻辑 1:1 调原函数/原内联段（services/quests_flow、core/wild_king、
services/tower_progress、services/weekly_progress、core/stat_bonus、core/achievements）。
kind 分支（field/instance/worldboss）留待 P3 收编 instance/worldboss 时按语义决策
（任何击杀都算数）扩展——P2 仅 field fire，instance/worldboss 手动段尚未动。
"""

from __future__ import annotations

from .. import db
from ..content_rules.gameplay import check_player_level_up
from .. import content as C
from ..core.achievements import check_achievements
from ..core.stat_bonus import stat_bonus
from ..core.wild_king import wild_king_on_kill
from ..services.guild import guild_kill_progress
from ..services.player_event_bus import register
from ..services.quests_flow import quest_kill_progress
from ..services.tower_progress import tower_guard_on_kill
from ..services.weekly_progress import weekly_bump_kill

_registered = False


# ---------------------------------------------------------------------------
# 订阅方 1：公会每日击杀任务（每场胜利 +1）——原 combat L2034-2055 内联段
# ---------------------------------------------------------------------------
def _sub_guild_daily(ctx):
    g = db.guild_get_by_member(ctx["qq_id"])
    if not g:
        return []
    lines, _rewarded = guild_kill_progress(ctx["group_id"], ctx["qq_id"], g)
    return lines


# ---------------------------------------------------------------------------
# 订阅方 2：升级（title_bonus 注入 + check_player_level_up）——原 combat L2056-2063
# 经验落库后重读 player（v105 M18 P2：rule_fire 彩蛋金币已在库）→ 注入 stat_bonus
# → 升级检查 → 升级时写回 db 字段并重绑 ctx["player"]（后续订阅方拿最新 dict）。
# 🔴 kind 守卫：仅 field 升级——副本战斗内不做升级检查（_instance_kill_reward
# docstring：check_player_level_up 回满 hp 会破坏连续战斗节奏，经验攒到出副本统一
# 结算）；世界Boss 参与奖励现状也不升级。任务达标发奖内部的升级（settle_daily_quest
# 单点）不在此列——那属发奖机制，全局一致。
# ---------------------------------------------------------------------------
def _sub_levelup(ctx):
    if ctx.get("kind") != "field":
        return []
    player = db.get_player(ctx["group_id"], ctx["qq_id"]) or {}
    player["_title_bonus"] = stat_bonus(ctx["group_id"], ctx["qq_id"], player)
    lv_logs, player2 = check_player_level_up(ctx["group_id"], ctx["qq_id"], player)
    if not lv_logs:
        return []
    ctx["player"] = player2
    db.update_player(ctx["group_id"], ctx["qq_id"],
                     level=player2["level"], exp=player2["exp"],
                     hp=player2["hp"], mp=player2["mp"],
                     max_hp=player2["max_hp"], max_mp=player2["max_mp"],
                     skills=player2["skills"],
                     attr_pts=player2.get("attr_pts", 0),
                     skill_points=player2.get("skill_points", 0),
                     learned_skills=player2.get("learned_skills", []))
    return lv_logs


# ---------------------------------------------------------------------------
# 订阅方 3：任务（主线/每日/支线）+ 周常——原 combat L2064-2075 quest 循环
# （_update_quests 壳 = quest_kill_progress + weekly_bump_kill 每只怪）
# 全 kind 推（语义决策 09-09：任何击杀都算数；quest_kill_progress 内部按怪属性/名
# 匹配，instance/worldboss 的怪名字对得上就推——取代副本 _instance_main_kill_progress）
# ---------------------------------------------------------------------------
def _sub_quests(ctx):
    lines = []
    for k in ctx.get("killed") or []:
        lines += (quest_kill_progress(ctx["group_id"], ctx["qq_id"], k) or [])
        lines += (weekly_bump_kill(ctx["group_id"], ctx["qq_id"], k) or [])
    return lines


# ---------------------------------------------------------------------------
# 订阅方 4：野王击杀（主怪 id b_guard_ 前缀）——原 combat L2076-2089
# 返回行组 + side_effects 广播（命令层 fire 点负责 _broadcast）
# ---------------------------------------------------------------------------
def _sub_wild_king(ctx):
    monster = ctx.get("monster") or {}
    if not (monster and str(monster.get("id", "")).startswith("b_guard_")):
        return []
    _wk_lines = wild_king_on_kill(ctx["group_id"], ctx["qq_id"], monster)
    if _wk_lines:
        ctx["side_effects"].append({"type": "broadcast", "text": "\n".join(_wk_lines)})
    return _wk_lines


# ---------------------------------------------------------------------------
# 订阅方 5：塔卫击杀（主怪 id tower_ 前缀）——原 combat L2090-2099
# ---------------------------------------------------------------------------
def _sub_tower_guard(ctx):
    monster = ctx.get("monster") or {}
    if not (monster and str(monster.get("id", "")).startswith("tower_")):
        return []
    return tower_guard_on_kill(ctx["group_id"], ctx["qq_id"], monster)


# ---------------------------------------------------------------------------
# 订阅方 6：成就（按 kind 组装 extra）——field 原 combat L2100-2118 / instance 原
# _instance_victory L3187(inst_id+flawless) / worldboss 原 _worldboss_act L2432
# kind 分支只此一处（P0 任务书 §9）：场景决定 extra，解锁判定全局一致。
# ---------------------------------------------------------------------------
def _ach_lines(achs) -> list:
    lines = []
    for a in achs or []:
        rw_txt = f"\n      🎁 {a['_reward_txt']}" if a.get("_reward_txt") else ""
        lines.append(f"🏆 成就解锁：{a['name']}！({a['desc']}){rw_txt}")
    return lines


def _sub_achievements(ctx):
    kind = ctx.get("kind", "field")
    if kind == "instance":
        meta = ctx.get("meta") or {}
        extra = {"inst_id": meta.get("inst_id")}
        if meta.get("flawless"):
            extra["flawless"] = True
        return _ach_lines(check_achievements(ctx["group_id"], ctx["qq_id"],
                                             ctx.get("player"), extra))
    if kind == "worldboss":
        return _ach_lines(check_achievements(ctx["group_id"], ctx["qq_id"],
                                             ctx.get("player"), {"worldboss": 1}))
    # field：v87 隐藏怪击杀累计（成就·传说猎人）
    monster = ctx.get("monster") or {}
    hm_defeated = set()
    try:
        _hm_st = db.get_event_state(f"hm_defeated_{ctx['group_id']}_{ctx['qq_id']}")
        if _hm_st:
            hm_defeated = set(_hm_st.split(",")) if _hm_st else set()
        if monster.get("id") in C.HIDDEN_MONSTERS:
            hm_defeated.add(monster["id"])
            db.set_event_state(f"hm_defeated_{ctx['group_id']}_{ctx['qq_id']}", ",".join(sorted(hm_defeated)))
    except Exception:
        pass
    return _ach_lines(check_achievements(ctx["group_id"], ctx["qq_id"], ctx.get("player"),
                                         {"defeated_hidden_monsters": hm_defeated}))


def ensure_registered() -> None:
    """注册 6 个 field 订阅方（幂等：模块只注册一次）。

    命令层 fire 点显式调用本函数（或 import 本模块触发底部调用）。
    """
    global _registered
    if _registered:
        return
    # 注册序 = 原壳行序（回填顺序对照表 §5/§6）：
    # guild(无空行) → levelup → quests+weekly → wild_king → tower_guard → achievements
    register("battle_victory", _sub_guild_daily, blank_line=False)
    register("battle_victory", _sub_levelup, blank_line=True)
    register("battle_victory", _sub_quests, blank_line=True)
    register("battle_victory", _sub_wild_king, blank_line=True)
    register("battle_victory", _sub_tower_guard, blank_line=True)
    register("battle_victory", _sub_achievements, blank_line=True)
    _registered = True


ensure_registered()
