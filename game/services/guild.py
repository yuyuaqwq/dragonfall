# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - guild（公会域，v181 P4-6）

公会创建/加入/退出/解散/签到/任务/捐献/排行/任命/免职的编排逻辑
（策划 11 章 + v105 M18 + v116 职位体系 + v104R3 P1-3 规则原样随迁）：
由 social.py 『创建公会』『加入公会』『退出公会』『解散公会』『公会』『公会签到』
『公会任务』『公会捐献』『公会排行』『公会任命』『公会免职』命令层消费——
命令层只留解析 + 文案壳（含 _tip 随机提示等 I/O），业务判定与落库收敛到本文件。

- v116 职位体系：guild_members.role 四档（leader/vice_leader/elite/member），
  任命『副会长』需公会 Lv.3（GUILD_CONFIG.vice_leader_level），精英无门槛。
- 捐献：上交 3 份材料（GUILD_CONFIG.donate_items），每日一次，进度用
  event_state（key=guild_donate:{gid}:{qq_id}）单独记录，不与击杀任务共用。
- v104R3 P1-3：捐献材料排除任务道具（mat_ 前缀的隐藏线/主线交付物误捐断链）。
- 公会任务：讨伐（击杀自动推进，kill_task=5）由 combat 击杀结算侧消费
  （guild_kill_progress，跨天重置；达标发奖与 social.guild_task 面板同源）。

依赖红线：可 import data/core/store/db/engine/battle/reward；禁止 import commands/*。
db 等依赖一律函数体内惰性 import（防 data/_assembly 加载期循环，core 样板同款铁律）。
"""
import datetime


def _today():
    return datetime.date.today().isoformat()


def _is_leader(g, qq_id):
    return str(g.get("leader")) == str(qq_id)


def guild_create_check(player):
    """创建公会前置校验（纯读）：返回 (ok, err)。已入会/等级/金币门槛在调用方查完再进。

    注意：『已在一个公会』校验依赖 db.guild_get_by_member(qq_id)，由命令层先查后调
    （本函数收 player 快照避免重复读）。返回 ok=False 时 err 为可直接 yield 的拒绝文案。
    """
    from .. import content as C
    cfg = C.GUILD_CONFIG
    if player["level"] < cfg["create_level"]:
        return False, f"创建公会需要 {cfg['create_level']} 级！你才 {player['level']} 级，先去冒险吧～"
    if player["gold"] < cfg["create_cost"]:
        return False, f"创建公会需要 {cfg['create_cost']} 金币！你只有 {player['gold']} 金币。"
    return True, None


def guild_create(group_id, qq_id, player, name):
    """创建公会：扣金币 → 建会。返回 (ok, gid, err)。

    - guild_create 重名返回 None → err='已存在' 文案。
    - 成功后扣 create_cost 金币（v105 M18 P2：成就判定由命令层在成功后做）。
    """
    from .. import db
    from .. import content as C
    cfg = C.GUILD_CONFIG
    gid = db.guild_create(name, qq_id, desc=f"{player['name']} 创立的公会")
    if not gid:
        return False, None, f"公会『{name}』已存在！换个名字吧～"
    db.update_player(group_id, qq_id, gold=player["gold"] - cfg["create_cost"])
    return True, gid, None


def guild_join(group_id, qq_id, name):
    """加入公会：按名查会 → 入会。返回 (ok, g, err)。成功 g=公会 dict（命令层取 g['name'] 拼文案）。"""
    from .. import db
    g = db.guild_get_by_name(name)
    if not g:
        return False, None, f"找不到公会『{name}』！输入『公会排行』看看有哪些公会～"
    db.guild_join(g["gid"], qq_id)
    return True, g, None


def guild_leave_check(g, qq_id):
    """退出公会前置守卫：会长不能直接退会（须解散）。返回 (blocked, msg)。"""
    if _is_leader(g, qq_id):
        # v105 M18 P2：全仓无『转让会长』命令，提示只指向真实命令，避免误导
        return True, "你是会长！会长不能直接退会，请『解散公会』（公会随之解散）～"
    return False, None


def guild_leave(g, qq_id):
    """退出公会（db.guild_leave：leader 离开即解散，由 store 原语处理）。"""
    from .. import db
    db.guild_leave(g["gid"], qq_id)


def guild_disband(g, qq_id):
    """解散公会（leader 离开即解散）。"""
    from .. import db
    db.guild_leave(g["gid"], qq_id)  # leader 离开即解散


def guild_sign(group_id, qq_id, g):
    """公会签到（每日一次）：写签到日期 → 公会经验/个人贡献/金币。

    返回 (ok, lines, err)。ok=False 时 err=拒绝文案（今日已签/无公会由调用方先查）。
    数值全部来自 C.GUILD_CONFIG（sign_exp/sign_contribute/sign_gold）。
    """
    from .. import db
    from .. import content as C
    cfg = C.GUILD_CONFIG
    today = _today()
    if db.guild_get_sign(g["gid"], qq_id) == today:
        return False, None, "今天已经公会签过到啦！明天再来～"
    db.guild_set_sign(g["gid"], qq_id, today)
    db.guild_add_exp(g["gid"], cfg["sign_exp"], member_qq=qq_id, contribute=cfg["sign_contribute"])
    player = db.get_player(group_id, qq_id)
    db.update_player(group_id, qq_id, gold=(player or {}).get("gold", 0) + cfg["sign_gold"])
    return True, [
        f"📅 【公会签到】在【{g['name']}】报到！\n"
        f"🏰 公会经验 +{cfg['sign_exp']} ｜ 个人贡献 +{cfg['sign_contribute']}\n"
        f"💰 金币 +{cfg['sign_gold']}"
    ], None


def guild_task_view(group_id, qq_id, g):
    """公会任务面板（击杀型，跨天重置）：返回 (ok, lines, err)。

    击杀自动推进由 combat 侧调 guild_kill_progress；此处仅读当前进度。
    """
    from .. import db
    from .. import content as C
    need = C.GUILD_CONFIG["kill_task"]
    tdate, tprog = db.guild_get_task(g["gid"], qq_id)
    if tdate != _today():
        tdate, tprog = _today(), 0
    if tprog >= need:
        return False, None, "今天的公会任务已完成！明天再来～"
    return True, [
        f"🎯 【公会任务】击杀 {need} 只怪物(当前 {tprog}/{need})\n"
        f"💡 击杀会自动结算奖励！"
    ], None


def guild_donate_inventory(group_id, qq_id):
    """公会捐献可上交材料清单（v46 材料统一 mat_ 前缀；v104R3 P1-3 排除任务道具）。"""
    from .. import db
    return [it for it in db.get_inventory(group_id, qq_id)
            if it["key"].startswith("mat_") and it["data"].get("type") != "任务道具"]


def guild_donate_total(mats):
    return sum(it["count"] for it in mats)


def guild_donate(group_id, qq_id, g):
    """公会捐献（每日一次，event_state 记日期）：够料则扣料 → 公会经验/贡献/金币。

    返回 (ok, lines, err, need, total)：ok=False 时 err=拒绝/不足文案（含 need/total 供面板）。
    扣料顺序：从背包靠前的材料开始扣（与旧命令层逐项 remove_item 等价）。
    """
    from .. import db
    from .. import content as C
    cfg = C.GUILD_CONFIG
    need = cfg["donate_items"]
    key = f"guild_donate:{g['gid']}:{qq_id}"
    if db.get_event_state(key) == _today():
        return False, None, "今天的公会捐献已完成！明天再来～", need, None
    mats = guild_donate_inventory(group_id, qq_id)
    total = guild_donate_total(mats)
    if total < need:
        return False, None, f"🎯 【公会捐献】需要上交 {need} 份材料(当前 {total}/{need})！\n", need, total
    remain = need
    for it in mats:
        if remain <= 0:
            break
        take = min(it["count"], remain)
        db.remove_item(group_id, qq_id, it["key"], take)
        remain -= take
    db.guild_add_exp(g["gid"], cfg["task_exp"], member_qq=qq_id, contribute=cfg["task_contribute"])
    player = db.get_player(group_id, qq_id)
    db.update_player(group_id, qq_id, gold=(player or {}).get("gold", 0) + cfg["task_gold"])
    db.set_event_state(key, _today())
    return True, [
        f"🎁 【公会捐献完成】上交 {need} 份材料，为公会贡献力量！\n"
        f"🏰 公会经验 +{cfg['task_exp']} ｜ 个人贡献 +{cfg['task_contribute']}\n"
        f"💰 金币 +{cfg['task_gold']}"
    ], None, need, total


def guild_rank_lines():
    """公会排行榜行（db.guild_top(10)）。无公会时返回 []（命令层给空榜文案）。"""
    from .. import db
    tops = db.guild_top(10)
    if not tops:
        return []
    lines = ["🏆 【公会排行榜】", "━━━━━━━━━━━━"]
    for i, g in enumerate(tops, 1):
        lines.append(f"{i}. {g['icon']} {g['name']} Lv.{g['level']}({g['members']}人)")
    return lines


# ---- 职位体系（v116：任命/免职 role 校验）----

ROLE_MAP = {"副会长": "vice_leader", "精英": "elite"}
APPOINTABLE_ROLES = ("vice_leader", "elite")  # 与 data/guild.GUILD_APPOINTABLE 同源


def guild_appoint_check_role(role_arg):
    """职位词 → role key；不支持返回 None（命令层给『可任命职位』文案）。"""
    return ROLE_MAP.get(role_arg)


def guild_appoint_level_ok(g, role):
    """任命等级门槛：副会长需公会 Lv.3（GUILD_CONFIG.vice_leader_level），精英无门槛。

    返回 (ok, err)：ok=False 时 err 为可直接 yield 的文案（含门槛值与当前公会等级）。
    """
    from .. import content as C
    cfg = C.GUILD_CONFIG
    if role == "vice_leader" and g["level"] < cfg.get("vice_leader_level", 3):
        return False, f"任命副会长需要公会 Lv.{cfg.get('vice_leader_level', 3)}！本公会才 Lv.{g['level']}～"
    return True, None


def guild_find_member(g, target_name):
    """按玩家名查公会成员。返回 (member, target, err)：

    - 查无此玩家 → err='没找到玩家' 文案；
    - 玩家不在本公会 → err='不在本公会' 文案（member=None, target 有值）。
    """
    from .. import db
    from ..store.social import guild_get_member
    target = db.find_player_by_name(target_name)
    if not target:
        return None, None, f"没找到玩家『{target_name}』！"
    tm = guild_get_member(g["gid"], target["qq_id"])
    if not tm:
        return None, target, f"『{target['name']}』不在本公会里～"
    return tm, target, None


def guild_appoint(g, target, role):
    """执行任命（写 role）。返回 (label, icon)（命令层拼晋升文案）。"""
    from ..store.social import guild_set_role
    from ..data import guild as _G
    guild_set_role(g["gid"], target["qq_id"], role)
    return _G.GUILD_ROLES[role]


def guild_demote(g, target):
    """执行免职（降回 member）。"""
    from ..store.social import guild_set_role
    guild_set_role(g["gid"], target["qq_id"], "member")


# ---- 公会任务击杀推进（combat 击杀结算侧消费；跨天重置 v43）----


def guild_kill_progress(group_id, qq_id, g, lines=None):
    """击杀推进公会任务：跨天重置 → +1 → 达标发奖（公会经验/贡献/金币）。

    返回 (changed_lines, rewarded)：changed_lines 为击杀侧要追加的战斗结算行
    （进度行或完成行），rewarded=True 表示本次击杀达成任务并已发奖。
    无公会成员资格（g=None）返回 ([], False)。v43：跨天重置而非跳过。
    """
    from .. import db
    from .. import content as C
    cfg = C.GUILD_CONFIG
    tdate, tprog = db.guild_get_task(g["gid"], qq_id)
    if tdate != _today():
        tprog = 0  # 新的一天/新成员：重置进度
    if tprog < cfg["kill_task"]:
        tprog += 1
        db.guild_set_task(g["gid"], qq_id, _today(), tprog)
        if tprog >= cfg["kill_task"]:
            db.guild_add_exp(g["gid"], cfg["task_exp"], member_qq=qq_id, contribute=cfg["task_contribute"])
            # v105 M18 P2：先刷新 player 再写金币——player dict 在战斗结算中段刷新后，
            # _rule_fire("battle_win")（Boss 巢穴私藏金币等 loot_gold 彩蛋）可能已落库加金币，
            # 直接用旧 dict 值覆盖会丢掉同场彩蛋金币
            player = db.get_player(group_id, qq_id)
            db.update_player(group_id, qq_id, gold=(player or {}).get("gold", 0) + cfg["task_gold"])
            return [f"🎯 【公会任务完成】击杀 {cfg['kill_task']} 只达成！公会经验 +{cfg['task_exp']} 贡献 +{cfg['task_contribute']} 金币 +{cfg['task_gold']}"], True
        return [f"🎯 公会任务进度 {tprog}/{cfg['kill_task']}"], False
    return [], False
