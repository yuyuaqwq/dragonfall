# -*- coding: utf-8 -*-
"""《剑与魔法》命令层 - talk_actions.py（v101.23d B 级：对话动作注册表）

与 core/dialogue_conds.py 的 CONDITIONS 注册表对称：加新对话动作 =
register 一个函数（~5 行），_apply_talk_action 零改动，纯内容扩展不动引擎。

动作函数签名：
    fn(world, group_id, qq_id, player, npc_id, action) -> list[通知行]
    world = Main 实例（Mixin 方法可用），action = 选项里的动作 dict

注意：注册顺序 = 执行顺序（dict 保序），与 v101.23d 之前的 if 链顺序一致；
一个选项可带多个动作键（如 set_flag + quest_take），全部执行。
"""
from .. import content as C  # noqa: F401
from .. import db
from .. import engine as E  # noqa: F401

ACTIONS = {}


def register(key):
    """动作注册装饰器。"""
    def deco(fn):
        ACTIONS[key] = fn
        return fn
    return deco


# ================= 动作实现 =================


@register("set_flag")
def action_set_flag(world, group_id, qq_id, player, npc_id, action):
    db.set_talk_flag(group_id, qq_id, npc_id, action["set_flag"])
    return []


@register("give_gold")
def action_give_gold(world, group_id, qq_id, player, npc_id, action):
    gold = int(action["give_gold"])
    db.update_player(group_id, qq_id, gold=(player.get("gold", 0) or 0) + gold)
    return [f"💰 获得金币 ×{gold}"]


@register("give_exp")
def action_give_exp(world, group_id, qq_id, player, npc_id, action):
    exp = int(action["give_exp"])
    db.update_player(group_id, qq_id, exp=(player.get("exp", 0) or 0) + exp)
    return [f"✨ 获得经验 +{exp}"]


@register("give_item")
def action_give_item(world, group_id, qq_id, player, npc_id, action):
    # #260: 拜师动作同时带 unlock_prof 时，副业位满则不发材料（此前 give_item 先于
    # unlock_prof 执行，拦截后材料照发、与解锁不同步）
    skip_give = False
    _up = action.get("unlock_prof")
    if _up:
        _okp, _ = world._prof_active_check(group_id, qq_id, _up)
        skip_give = not _okp
    if skip_give:
        return []
    item = action["give_item"]
    key = item.get("key", "")
    count = int(item.get("count", 1))
    if not key:
        return []
    db.add_item(group_id, qq_id, key, {}, count)
    return [f"🎒 获得 {key} ×{count}"]


@register("open_shop")
def action_open_shop(world, group_id, qq_id, player, npc_id, action):
    if not action.get("open_shop"):
        return []
    return ["🏪 输入『商店』可以买东西"]


@register("hint")
def action_hint(world, group_id, qq_id, player, npc_id, action):
    if not action.get("hint"):
        return []
    return [action["hint"]]


@register("quest_take")
def action_quest_take(world, group_id, qq_id, player, npc_id, action):
    # 主线：pending → 接取；ready → 交付领奖（_take_main_quest 自动分流）
    if not action.get("quest_take"):
        return []
    npc = C.NPCS.get(npc_id) or C.ALL_WILD.get(npc_id) or {}
    if not npc:
        return []
    return world._take_main_quest(group_id, qq_id, npc_id, npc)


@register("side_take")
def action_side_take(world, group_id, qq_id, player, npc_id, action):
    # 支线：交付该 NPC 名下第一个可交支线
    if not action.get("side_take"):
        return []
    quests = db.get_quests(group_id, qq_id)
    lines = []
    for sid, sq in list((quests.get("side") or {}).items()):
        sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
        if not sqd or sqd.get("giver") != npc_id:
            continue
        if sq.get("status") == "done":  # v95.12：已交付支线不再提示/交付
            continue
        obj = sqd.get("objective", {})
        if obj.get("collect"):
            if db.count_item(group_id, qq_id, obj["collect"]) >= obj.get("count", 1):
                lines += world._complete_side_quest(group_id, qq_id, sid)
                break
        elif sq.get("status") == "ready":
            lines += world._complete_side_quest(group_id, qq_id, sid)
            break
    return lines


@register("side_offer")
def action_side_offer(world, group_id, qq_id, player, npc_id, action):
    # v95r65 #288：支线接取入口（有对话树 NPC 的『有活儿要交给我吗』选项）。
    # 走 _offer_side_quests 接该 NPC 名下未接支线（已过滤告示板委托 #295）
    if not action.get("side_offer"):
        return []
    npc = C.NPCS.get(npc_id) or C.ALL_WILD.get(npc_id) or {}
    if not npc:
        return []
    return world._offer_side_quests(group_id, qq_id, npc_id, npc)


@register("consume_item")
def action_consume_item(world, group_id, qq_id, player, npc_id, action):
    ci = action["consume_item"]
    key = ci.get("item", "")
    count = int(ci.get("count", 1))
    if not key:
        return []
    db.remove_item(group_id, qq_id, key, count)
    return [f"🎒 交出 {key} ×{count}"]


@register("unlock_prof")
def action_unlock_prof(world, group_id, qq_id, player, npc_id, action):
    prof = action["unlock_prof"]
    appr = list(player.get("apprentices", []))
    if prof in appr:
        return [f"你已经拜过{db.PROF_FIELDS.get(prof, prof)}的导师了。"]
    ok, act_msg = world._prof_active_check(group_id, qq_id, prof)
    if not ok:
        return [act_msg]
    appr.append(prof)
    db.update_player(group_id, qq_id, apprentices=appr)
    # 入门礼：副业经验（unlock_prof 配套 give_prof_exp 时由命令层统一给）
    exp = action.get("give_prof_exp")
    lines = []
    if exp:
        lv, _ = db.add_prof_exp(group_id, qq_id, prof, int(exp))
        lines.append(f"🎓 拜师成功！解锁副业「{db.PROF_FIELDS.get(prof, prof)}」(副业经验 +{exp})")
    else:
        lines.append(f"🎓 拜师成功！解锁副业「{db.PROF_FIELDS.get(prof, prof)}」")
    lines.append("💡 『副业』查看你的生活职业面板")
    return lines


@register("unlock_class")
def action_unlock_class(world, group_id, qq_id, player, npc_id, action):
    # 行会就职：见习冒险者 → 基础职业（属性按新职业重算 + 初始技能）
    new_cls = action["unlock_class"]
    return world._do_join_class(group_id, qq_id, player, new_cls)


@register("tutor_skill")
def action_tutor_skill(world, group_id, qq_id, player, npc_id, action):
    # 导师进阶技能教学：等级门槛 + 金币学费 → 直接学会（不耗技能点）
    ts = action["tutor_skill"]
    sk_id = ts.get("skill", "")
    cost = int(ts.get("cost", 0))
    need_lv = int(ts.get("need_lv", 1))
    info = E.skill_info(player.get("class_name", ""), sk_id)
    if not info:
        return ["这位导师似乎还没准备好教你……"]
    if player.get("level", 0) < need_lv:
        return [f"导师摇摇头：这套本事要 Lv.{need_lv} 才学得动，你才 Lv.{player.get('level', 1)}，先练练基本功。"]
    if (player.get("gold", 0) or 0) < cost:
        return [f"导师伸出三根手指：学费 {cost} 金币，少一个子儿都不行。(你现在有 {player.get('gold', 0)} 金币)"]
    learned = list(player.get("learned_skills", []))
    sname = info.get("name", sk_id)
    if C.resolve("skills", sname) in [C.resolve("skills", s) for s in learned if s]:
        return [f"『{sname}』你已经学会了，再多练练吧。"]
    db.update_player(group_id, qq_id, gold=(player.get("gold", 0) or 0) - cost,
                     learned_skills=learned + [sname])
    return [
        f"💰 支付学费 {cost} 金币",
        f"✨ 导师悉心传授，你学会了进阶技能『{sname}』！",
        f"「{info['desc']}」",
        "💡 记得『设置技能 <槽位> <技能名>』放入技能栏～",
    ]


@register("evolve_class")
def action_evolve_class(world, group_id, qq_id, player, npc_id, action):
    # 导师转职：Lv.30/60/90 找对应职业导师对话转职
    ev = action["evolve_class"]
    next_tier = int(ev.get("tier", 1))
    path = int(ev.get("path", 1))
    return world._do_evolve_via_npc(group_id, qq_id, player, next_tier, path)
