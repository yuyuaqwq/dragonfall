# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - reward.py（统一奖励发放器 v174）

把全游戏散落的"确定奖励发放"收敛为单一入口 grant_reward()：
- 任务 / 成就 / 收藏 / 对话NPC / 签到 / 周常 / 爬塔 的奖励统一走这里
- 消灭各来源重复的「加 exp(含升级结算) → 加金币 → 物品入包 → 文案」代码

统一奖励格式（REWARD dict，字段均可选）：
    exp    : int            经验（自动触发升级结算）
    gold   : int            金币
    items  : [{"item": key, "n": count}]   物品/材料（key 兼容 ID/中文名）
    equips : [{"rid": rid}] 名册装备（也可用 items 里 "eq:rid" 前缀）
    pets   : ["pet_id"]     宠物蛋（make_pet_egg）
    mounts : ["mount_id"]   坐骑缰绳（make_mount_rein）
    title  : str            称号（titles.py id 或中文名，授予播报）
    bonus  : {stat: val}    永久属性加成（写 players 表 title_bonus 键）
    buff   : {stat, mult, left}  限时 buff（event_state 写 poi_buff_ 语义）

注意：本模块只发「奖励动作」，不含触发条件（任务提交/成就判定/对话节点由调用方保留）。
有特有副作用的来源（任务解锁职业 unlock_class、对话 set_flag 等）由调用方在 grant 前后自理。
"""
import uuid


def _c():
    """惰性引 content，防模块加载期循环 import"""
    import game.content as C
    return C


def _grant_items(group_id, qq_id, items, lines, db):
    """物品/材料/装备入包。items: [{item, n}]。返回 (成功, 失败计数)。"""
    from game.store.inventory import _key_to_id  # noqa: E402
    fail = 0
    for it in items or []:
        try:
            key = it.get("item") or it.get("key")
            n = int(it.get("n") or it.get("count") or 1)
            if not key:
                continue
            # eq: 前缀 = 名册装备
            if isinstance(key, str) and key.startswith("eq:"):
                rid = key[3:]
                _rids = _c().EQUIP_ROSTER_BY_NAME.get(rid, [rid]) if rid not in _c().EQUIP_ROSTER else [rid]
                _rid = _rids[0]
                if _rid not in _c().EQUIP_ROSTER:
                    print(f"[dragonfall][reward] 装备奖励名册缺失: {rid}")
                    fail += 1
                    continue
                eq = _c().generate_roster_equip(_rid)
                db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", eq)
                lines.append(f"  🎁 获得装备：{eq.get('name', rid)}")
                continue
            # 普通物品/材料
            kid = _key_to_id(key) if _key_to_id else key
            _idata = _c().ITEMS.get(kid) or _c().MATERIALS.get(kid)
            if _idata is None:
                print(f"[dragonfall][reward] 物品奖励缺失: {key}（未收录），已跳过")
                fail += 1
                continue
            db.add_item(group_id, qq_id, kid, _idata, count=n)
            lines.append(f"  🎒 {_idata.get('name', key)} ×{n}")
        except Exception as e:
            import logging
            logging.getLogger("astrbot").warning(f"[dragonfall][reward] 物品发放失败 {it}: {e}")
            fail += 1
    return fail


def _grant_pets(group_id, qq_id, pets, lines, db):
    for pid in pets or []:
        try:
            egg = _c().make_pet_egg(pid)
            if not egg:
                continue
            db.add_item(group_id, qq_id, f"petegg_{pid}", egg)
            lines.append(f"  🥚 获得道具：{egg['name']}！『使用 宠物蛋』孵化！")
        except Exception:
            pass


def _grant_mounts(group_id, qq_id, mounts, lines, db):
    for mid in mounts or []:
        try:
            rein = _c().make_mount_rein(mid)
            if not rein:
                continue
            db.add_item(group_id, qq_id, f"mountrein_{mid}", rein)
            lines.append(f"  🐾 获得道具：{rein['name']}！『使用 缰绳』驯服坐骑！")
        except Exception:
            pass


def _grant_title(group_id, qq_id, title, lines):
    """称号授予：titles.py 按 id/中文名匹配，播报解锁（条件系统自动判定拥有）。"""
    if not title:
        return
    _C = _c()
    tinfo = next((t for t in _C.TITLES if t.get("id") == title), None)
    if not tinfo:
        tinfo = next((t for t in _C.TITLES if t.get("name") == title), None)
    if tinfo:
        lines.append(f"  🏅 获得称号：「{tinfo.get('name', title)}」！")
    else:
        print(f"[dragonfall][reward] 称号 id 缺失：{title}（titles.py 未登记），已跳过")


def _grant_bonus(group_id, qq_id, bonus, lines, db):
    """永久属性加成（收藏册满套 bonus）。

    注意：游戏内永久属性走 title_bonus() 动态计算（读 TITLES/ACHIEVEMENTS 已解锁项），
    **不落 players 表字段**。收藏册满套 bonus 的实装 = 让 title_bonus() 认识"收藏册已集齐"，
    由 title_bonus 模块动态给，这里不做存储。若数据里 bonus 到达这里，说明调用方用了
    grant 的直接 bonus 语义——仅播报（属性由 title_bonus 动态源保证），不重复落库。
    """
    if not bonus:
        return
    parts = []
    _CN = {"atk": "攻击", "def": "防御", "matk": "魔攻", "mdef": "魔防",
           "spd": "速度", "hp": "生命", "mp": "魔力", "crit": "暴击", "dodge": "闪避"}
    for k, v in (bonus or {}).items():
        parts.append(f"{_CN.get(k, k)}+{v}")
    if parts:
        lines.append(f"  ✨ 永久属性：{'、'.join(parts)}（已自动生效）")


def grant_items_batch(group_id, qq_id, items_dict, lines=None) -> tuple:
    """批量物品发放辅助（成就等多条奖励合并物品时用）。

    items_dict: {item_key: count}（成就 reward.items 原生形态，兼容中文名）
    lines: 可选文案列表（追加物品行）
    返回 (lines, 是否全部成功)。物品缺失静默跳过不阻塞。
    """
    from game import db  # noqa: E402
    if lines is None:
        lines = []
    items = [{"item": k, "n": v} for k, v in (items_dict or {}).items()]
    _fail = _grant_items(group_id, qq_id, items, lines, db)
    return lines, _fail == 0


def grant_reward(reward: dict, group_id, qq_id, *, player=None, lines=None) -> list:
    """统一奖励发放入口。

    reward: REWARD dict（见模块 docstring）。None/空 dict → 返回空文案。
    player: 可选，传入可省一次 DB 读（调用方已有 player 时）。
    lines: 可选，已有文案列表时追加（否则新建）。
    返回文案行列表（含升级结算日志）。

    用法：
        from game.core.reward import grant_reward
        lines = grant_reward({"exp": 100, "gold": 50, "items": [...]}, gid, qid)
    """
    from game import db  # noqa: E402
    from game.engine import check_player_level_up  # noqa: E402
    from game.core.title_bonus import title_bonus  # noqa: E402
    if lines is None:
        lines = []
    if not reward:
        return lines
    _C = _c()
    reward = dict(reward)  # 防污染原数据
    # ── 经验/金币（含升级结算）──────────────────────────────
    exp = int(reward.get("exp") or 0)
    gold = int(reward.get("gold") or 0)
    if exp or gold:
        if player is None:
            player = db.get_player(group_id, qq_id)
        if player:
            player = dict(player)
            player["qq_id"] = player.get("qq_id") or qq_id
            player["_title_bonus"] = title_bonus(group_id, qq_id, player)
            if exp:
                player["exp"] = player.get("exp", 0) + exp
            if gold:
                player["gold"] = player.get("gold", 0) + gold
            lv_logs, player = check_player_level_up(group_id, qq_id, player)
            db.update_player(group_id, qq_id,
                             exp=player["exp"], gold=player["gold"], level=player["level"],
                             hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"],
                             skills=player["skills"], attr_pts=player.get("attr_pts", 0),
                             skill_points=player.get("skill_points", 0),
                             learned_skills=player.get("learned_skills", []))
            parts = []
            if exp:
                parts.append(f"经验 +{exp}")
            if gold:
                parts.append(f"金币 +{gold}")
            if parts:
                lines.append(f"🎁 获得{'、'.join(parts)}")
            lines += lv_logs
    # ── 物品/材料/装备 ──────────────────────────────────────
    items = reward.get("items") or []
    # 兼容旧 items: {key: count} dict 形态
    if isinstance(items, dict):
        items = [{"item": k, "n": v} for k, v in items.items()]
    _grant_items(group_id, qq_id, items, lines, db)
    # 兼容旧 reward_item（任务单值/列表）——由调用方转成 items 传入，此处不处理
    # ── 名册装备 ────────────────────────────────────────────
    for eq in reward.get("equips") or []:
        rid = eq.get("rid") if isinstance(eq, dict) else eq
        try:
            equip = _C.generate_roster_equip(rid)
            db.add_item(group_id, qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip)
            lines.append(f"  🎁 获得装备：{equip.get('name', rid)}")
        except Exception:
            print(f"[dragonfall][reward] 装备奖励名册缺失: {rid}，已跳过")
    # ── 宠物蛋 / 坐骑缰绳 ───────────────────────────────────
    _grant_pets(group_id, qq_id, reward.get("pets"), lines, db)
    _grant_mounts(group_id, qq_id, reward.get("mounts"), lines, db)
    # ── 称号 / 永久属性 ─────────────────────────────────────
    _grant_title(group_id, qq_id, reward.get("title"), lines)
    _grant_bonus(group_id, qq_id, reward.get("bonus"), lines, db)
    return lines
