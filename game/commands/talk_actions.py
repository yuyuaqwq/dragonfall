# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 - talk_actions.py（v101.23d B 级：对话动作注册表）

与 core/dialogue_conds.py 的 CONDITIONS 注册表对称：加新对话动作 =
register 一个函数（~5 行），_apply_talk_action 零改动，纯内容扩展不动引擎。

动作函数签名：
    fn(world, group_id, qq_id, player, npc_id, action) -> list[通知行]
    world = Main 实例（Mixin 方法可用），action = 选项里的动作 dict

注意：注册顺序 = 执行顺序（dict 保序），与 v101.23d 之前的 if 链顺序一致；
一个选项可带多个动作键（如 set_flag + quest_take），全部执行。

v113：新增异步动作支持（hidden_evolve 等需要 await async generator 的动作）——
异步动作函数用 async def 声明，world._apply_talk_action 会检测并 await。
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


def check_action_keys(action):
    """消费端防御：action 中未注册的动作键（set(action) - set(ACTIONS)）告警。

    v124.3（审计）：此前 _apply_talk_action 对未知 action 键静默忽略（qest_take
    笔误无告警），与 check_need 的未知 need 键防御不对称。现与
    core/dialogue.py check_need（v104 M21 P1）对齐：
      生产环境 → astrbot 日志 warn 并放行（防数据笔误静默失效）；
      测试环境（GWEN_GAME_DB 含 "test" / GWEN_TEST_MODE=1）→ 直接 raise 让单测抓笔误。
    _apply_talk_action_async / _apply_talk_action 入口调用。"""
    if not action:
        return
    unknown = set(action) - set(ACTIONS)
    if not unknown:
        return
    import logging
    import os
    _db = os.environ.get("GWEN_GAME_DB", "")
    _msg = (f"[dragonfall] 对话动作未注册键 action{unknown}："
            f"数据笔误？已按'无动作'放行，请检查 dialogues.py")
    _test = ("test" in os.path.basename(_db).lower()
             or os.environ.get("GWEN_TEST_MODE") == "1")
    if _test:
        raise ValueError(_msg)
    logging.getLogger("astrbot").warning(_msg)


# ================= 动作实现 =================

# 注册顺序 = 执行顺序。apprentice_check 必须最先注册：它是条件型动作（闸门），
# 判定失败/副业位满时设置 world._talk_route，消费端据此中断后续动作链——
# 与 v101.23d 前 talk_choice 特判"失败路径零动作执行（consume_item 不扣料）"一致。


@register("apprentice_check")
def action_apprentice_check(world, group_id, qq_id, player, npc_id, action):
    """v81 导师进修：考验判定（检查背包材料）——由 talk_choice 主循环特判迁入注册表。

    条件型动作：判定结果经 world._talk_route / world._talk_tail 通道传出，
    _apply_talk_action_async 返回路由，talk_choice 主循环只做通用分发：
      _talk_route = "__end__" → 副业位满直接结束对话（#101.29，不再渲染 fail 节点）
      _talk_route = "fail"    → 材料不足，走选项 fail_next
      通过（不设 route）     → 成功提示放 _talk_tail，待全部动作行之后追加
                                 （与旧特判 notices.append("✅…") 的输出顺序一致）
    交互行为（选项显示/失败提示/通过流程）与 v101.23d 前内联特判完全一致。
    """
    check = action["apprentice_check"]
    # #255: 副业位满时考验提前拦截——遍历对话树找 unlock_prof 目标副业，
    # 位满则材料也不收，避免玩家交完材料才被拦白跑
    # #417: 遍历层级 bug——dlg 顶层是 {start, nodes}，必须遍历 nodes 子表
    prof_target = None
    dlg = C.get_dialogue(npc_id)
    for _nid, _node in ((dlg.get("nodes") or {}).items()):
        if not isinstance(_node, dict):
            continue  # 对话树部分节点为纯字符串（跳转别名）
        for _o in (_node.get("options") or []):
            _ua = (_o.get("action") or {}).get("unlock_prof")
            if _ua:
                prof_target = _ua
                break
        if prof_target:
            break
    _npc = C.NPCS.get(npc_id) or C.ALL_WILD.get(npc_id) or {}
    _name = _npc.get("name", npc_id)
    if prof_target:
        _okp, _msgp = world._prof_active_check(group_id, qq_id, prof_target)
        if not _okp:
            # v101.29：副业位满拦截直接结束对话（不再渲染 fail 节点）——旧代码跳
            # fail_next 会渲染"材料凑不齐"类台词，与"副业位满先不收材料"的拦截
            # 归因矛盾（小红实测梅尔文交付被抓包）
            world._talk_route = "__end__"
            return [_msgp + "（这次考验先不收材料，腾出副业位再来吧）"]
    have = db.count_item(group_id, qq_id, check.get("item", ""))
    need = int(check.get("count", 1))
    if have >= need:
        world._talk_tail = [f"✅ {_name}满意地点了点头。"]
        return []
    world._talk_route = "fail"
    return [f"{_name}摇头：还差 {need - have} 份{check.get('item', '材料')}，备齐了再来。"]


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
    # v105 M21 P2：补升级结算——此前只写 exp 不触发 check_player_level_up，
    # 数据一旦使用会跳过升级（潜在雷）；与成就奖励领取同源结算（achievements.py:195-203）
    exp = int(action["give_exp"])
    p = dict(player)
    p["exp"] = (p.get("exp", 0) or 0) + exp
    lv_logs, p = E.check_player_level_up(group_id, qq_id, p)
    db.update_player(group_id, qq_id,
                     exp=p["exp"], level=p["level"], hp=p["hp"], mp=p["mp"],
                     max_hp=p["max_hp"], max_mp=p["max_mp"], skills=p["skills"],
                     attr_pts=p.get("attr_pts", 0), skill_points=p.get("skill_points", 0),
                     learned_skills=p.get("learned_skills", []))
    lines = [f"✨ 获得经验 +{exp}"]
    lines += lv_logs
    return lines


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
    # v105 M11 P2：赠礼补全物品 data（此前空 {} → get_inventory 名字兜底只认 mat_ 前缀，
    # i_stone_upgrade 等直接显示英文 key，克拉拉入门礼强化石在背包显示为 i_stone_upgrade）
    data = {"name": key, "type": "材料", "stackable": True}
    try:
        mid = C.resolve("materials", key)
        if mid in C.MATERIALS:
            m = C.MATERIALS[mid]
            data = {"name": m.get("name", key), "type": m.get("type", "材料"),
                    "stackable": True, "price": m.get("price", 0), "desc": m.get("desc", "")}
    except Exception:
        pass
    db.add_item(group_id, qq_id, key, data, count)
    return [f"🎒 获得 {data['name']} ×{count}"]


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
    # 支线：交付该 NPC 名下所有可交支线（v104 M20 P2：原只交第一条即 break，
    # 玛莎同挂 s1 与 s_board_cat 时寻猫 ready 需重复进对话；现循环交付全部可交）
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
            # v104 M20 P2：收集门槛统一 collect_count 优先（与 world.py 面板/交付一致；
            # 复合目标如魔剑士试炼 collect_count=2/count=3，旧口径 count=3 会拒收背包 2/3 的玩家）
            if db.count_item(group_id, qq_id, obj["collect"]) >= obj.get("collect_count", obj.get("count", 1)):
                lines += world._complete_side_quest(group_id, qq_id, sid)
                # 交付后标记本地快照，防同一轮重复交付（_complete_side_quest 已重读 DB 保存）
                sq["status"] = "done"
        elif sq.get("status") == "ready":
            lines += world._complete_side_quest(group_id, qq_id, sid)
            sq["status"] = "done"
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


@register("give_prof_exp")
def action_give_prof_exp(world, group_id, qq_id, player, npc_id, action):
    """unlock_prof 的配套参数键（拜师礼副业经验，实际由 unlock_prof 动作消费）。

    v124.3（审计）：注册为 no-op 仅为让 ACTIONS 覆盖数据中全部动作键，
    防 check_action_keys 未知键告警误报（拜师选项均带此键）。"""
    return []


@register("unlock_class")
def action_unlock_class(world, group_id, qq_id, player, npc_id, action):
    # 行会就职：见习冒险者 → 基础职业（属性按新职业重算 + 初始技能）
    new_cls = action["unlock_class"]
    return world._do_join_class(group_id, qq_id, player, new_cls)


@register("tutor_skill")
def action_tutor_skill(world, group_id, qq_id, player, npc_id, action):
    # 导师进阶技能教学：等级门槛 + 金币学费 → 直接学会（不耗技能点）
    # v104 R3 P1-5 修复：对话树写死的 need_lv 可被绕过（实测 Lv.6 学 45 级三连射），
    # 改以 E.skill_info 真实 lv + branch_skill_owner 转职校验（与 player.py _skill_learn_msg 同源）
    ts = action["tutor_skill"]
    sk_id = ts.get("skill", "")
    cost = int(ts.get("cost", 0))
    info = E.skill_info(player.get("class_name", ""), sk_id)
    if not info:
        return ["这位导师似乎还没准备好教你……"]
    need_lv = int(info.get("lv", ts.get("need_lv", 1)))
    if player.get("level", 0) < need_lv:
        return [f"导师摇摇头：这套本事要 Lv.{need_lv} 才学得动，你才 Lv.{player.get('level', 1)}，先练练基本功。"]
    # v26 分支专属技能门槛：必须先转职到对应分支（与技能点学习同源）
    owner = E.branch_skill_owner(player.get("class_name", ""), sk_id)
    if owner:
        need_tier, bname = owner
        my_tier = player.get("class_tier", 0)
        my_path = player.get("evolve_path", 0)
        if my_tier < need_tier or not my_path:
            return [f"导师摇摇头：『{info.get('name', sk_id)}』是 {bname} 的专属技能，需要先转职为 {bname} 才能学习！(Lv.30/60/90 可转职)"]
        branches = C.CLASSES[player["class_name"]].get("evolve_branches", {}).get(need_tier, [])
        # v112：多分支索引通用化（攻/守 path=1/2；隐藏流派 path=1/2/3）
        idx = max(0, int(my_path or 0) - 1)
        my_branch = branches[idx] if idx < len(branches) else ""
        if my_branch != bname:
            return [f"导师摇摇头：『{info.get('name', sk_id)}』是 {bname} 的专属技能，你走的是 {my_branch} 路线，学不了～"]
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


@register("hidden_evolve")
async def action_hidden_evolve(world, group_id, qq_id, player, npc_id, action):
    # v113 血脉传承：隐藏线导师对话『接受传承』——复用 _evolve_hidden_generic（异步 generator）
    # 种族校验由对话树 need（race_is）前置 + _evolve_hidden_generic 内 src_race 双保险
    # tier 语义：>0 显式指定档位；0/缺省 = 按等级修为继承（40→T1 / 60→T2 / 90→T3）
    ev = action["hidden_evolve"]
    cls_id = ev.get("cls", "")
    tier = int(ev.get("tier", 0) or 0)
    path = int(ev.get("path", 1))
    if tier <= 0:
        # 修为继承：与『转职 别名』同源——当前阶 +1 起，逐档看等级门槛
        _tlv = world._hidden_tier_levels(cls_id)
        _cur = player.get("class_tier", 0)
        _tgt = _cur + 1
        while _tgt <= 3 and player["level"] >= _tlv.get(_tgt, 99999):
            _tgt += 1
        _tgt -= 1
        if _tgt <= _cur:
            _tgt = _cur + 1  # 下一阶都不够 → 交给 generic 报等级不足
        tier = _tgt

    class _Sink:
        """收集 _evolve_hidden_generic 的 plain_result 文本（event 只用于输出）"""
        def __init__(self):
            self.lines = []
        def plain_result(self, text):
            self.lines.append(text)
            return text

    sink = _Sink()
    async for _ in world._evolve_hidden_generic(sink, group_id, qq_id, player, cls_id, tier, path):
        pass
    return sink.lines
