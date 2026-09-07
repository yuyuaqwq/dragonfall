# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - travel.py（v181 P4-8 TravelService：move 纯逻辑段服务化）

world.py 『前往/移动』（move 命令 ~583 行）是 async generator 长流程——只抽段不整体搬
（方案 §P4-8 / v3.4 铁律：yield 流程留命令层壳）。本文件收纳 move 区的**同步纯逻辑段**，
逐行 copy 零变化（v98 铁律：文案逐字符等价），函数体一律去 self/_ 前缀、签名加所需参数：

  - 子区域寻址：visible_sas（= world._visible_sas，v115 隐藏房过滤）／
    conn_target（= world._conn_target，v87.5 连接项两字段解析）／
    conn_subarea_name（= world._conn_subarea_name，v87.16 落点显示名）／
    subarea_hidden_block（move 内 v115 隐藏房未揭示拦截文案）
  - 出口校验：move_blocked_msg（= world._move_blocked_msg，城镇街道链/线性必经提示）／
    leave_map_block_msg（move 内 v87.14 出图必经出口子区域引导文案，跨图三段同源）
  - 目标地图寻址：resolve_map_target（move 地图名/ID/旧区域别名/区域名 → 入口，v104 P1 口径）
  - 等级提示：level_warn（move 内 v87 建议等级行，纯格式化）
  - 体力经济：stamina_tired_line（move 体力 0 走不动提示段）／
    move_stamina_cost（v101.13 坐骑 stamina_reduce 概率免费骰：返回 0/1）
  - 撞怪档位：travel_ambush（= world._travel_ambush——普通图/副本两分支、diff 档位
    0.30/0.18/0.08 + v130.7 越级线性提升 + lv_jitter=1；撞怪档位双轨
    core/constants.MOVE_ENCOUNTER_CHANCE 收敛**先搬后统一**，本批不统一）
  - 方碑/隐藏图路由：hidden_map_block（move 内 v87 隐藏图等级/物品/主线封印三档拦截）、
    landing_subarea（跨图落点 = map_entry_subarea，want_sa 覆盖）、
    portal_arrive_note（到达含未激活方碑提示行）

依赖红线（services 全局铁律）：只 import game.data（C 聚合）/ game.core / game.store(db)；
禁止 import game.commands.*。db 一律函数体内惰性 import（防 data/_assembly 加载期循环）。

⚠️ 边界（本批不碰）：
  - _instance_dungeon_move / _instance_move_route（async 副本移动流）留 instance.py 壳；
  - _subarea_arrive / _map_nav_body / _map_blocks / _map_scene / _map_facilities
    （到达/面板展示模板）留 world.py 壳（展示域，面板与移动同源铁律）；
  - _main_kill_target_on_map 属 combat 域（combat.explore/move 共用），travel_ambush 以
    hook 参数接收（group_id/qq_id 空 = 无上下文跳过副本撞怪分支，等价原语义）；
  - db.update_player / _spend_stamina 等副作用落库动作留命令层壳（service 只算不写）；
  - portal_view / portal_activate / portal_travel（async 命令）不在本批范围。
"""
import random

from .. import content as C


# ============ 模块常量（world.py 原样随迁，值逐字符同源） ============
# v130.7 意见#28 越级风险增强：比玩家高 5 级起，撞怪概率随等级差线性提升
# （0.30 + (diff-5)*0.05；低 10 级 = 0.55，低 11 级+ = 0.60 封顶）
AMBUSH_HIGH_MIN = 0.30
AMBUSH_HIGH_STEP = 0.05
AMBUSH_HIGH_CAP = 0.60
AMBUSH_MID = 0.18    # 同级/略低（diff 0..4）
AMBUSH_LOW = 0.08    # 玩家等级 > 地图（diff -4..-1）


# ============ 子区域寻址（v86/v87.14/v115） ============

def visible_sas(player: dict, cur_map: dict, group_id: str, qq_id: str) -> list:
    """v115 当前位置地图中**可见**的子区域列表（供面板/移动统一使用）。

    隐藏房间（A 提供 is_hidden_room）未揭示（C.reveal_met）→ 不可见（不列出）。
    若 A 尚未装好网状/hidden 接口，用 getattr 兜底：is_hidden_room 缺失时全部可见。
    """
    sas = cur_map.get("subareas") or []
    map_id = cur_map.get("id", "")
    is_hidden = getattr(C, "is_hidden_room", None)
    reveal_met = getattr(C, "reveal_met", None)
    visible = []
    for sa in sas:
        sa_id = sa.get("id", "")
        if is_hidden is None or reveal_met is None:
            visible.append(sa)
            continue
        try:
            if is_hidden(map_id, sa_id) and not reveal_met(sa.get("reveal"), group_id, qq_id, map_id):
                continue  # 隐藏未揭示 → 跳过
        except Exception:
            pass
        visible.append(sa)
    return visible


def conn_target(conn) -> tuple:
    """解析可前往连接项 → (目标地图 dict, 指定子区域 id 或 None)
    v87.5 支持两字段配置：'map_id' 或 ('map_id', 'subarea_id')"""
    if isinstance(conn, tuple):
        return C.MAP_BY_ID[conn[0]], conn[1]
    return C.MAP_BY_ID[conn], None


def conn_subarea_name(nm: dict, want_sa) -> str:
    """目标地图的落点子区域显示名(默认入口子区域，可指定)

    v87.16：无指定时用 map_entry_subarea（进城落点=出口/入口），不再是首个子区域
    """
    sas = nm.get("subareas") or []
    if not sas:
        return ""
    if want_sa:
        for s in sas:
            if s["id"] == want_sa:
                return f" · {s['name']}"
        return ""
    # v87.16：跨图落点 = 城镇出口（镇郊）/ 野外入口，显示与实际到达一致
    entry_id = C.map_entry_subarea(nm.get("id", ""))
    if entry_id:
        for s in sas:
            if s["id"] == entry_id:
                return f" · {s['name']}"
    return f" · {sas[0]['name']}"


def subarea_hidden_block(group_id, qq_id, map_id: str, sa: dict) -> str:
    """v115：隐藏未揭示房间不能直接前往（提示需先探索揭开）。

    返回拦截文案（含探索进度 txt，'' 表示无）或 None（可通行）。
    is_hidden/reveal_met 接口缺失时 getattr 兜底放行（同 world 原分支）。
    """
    _is_hidden_fn = getattr(C, "is_hidden_room", None)
    _reveal_met_fn = getattr(C, "reveal_met", None)
    if _is_hidden_fn is not None and _reveal_met_fn is not None:
        try:
            if _is_hidden_fn(map_id, sa["id"]) and not _reveal_met_fn(sa.get("reveal"), group_id, qq_id, map_id):
                _reveal_pr = getattr(C, "reveal_progress", None)
                _progress_txt = ""
                if _reveal_pr is not None:
                    try:
                        _ck, _nk = _reveal_pr(group_id, qq_id, map_id)
                        if _nk is not None:
                            _progress_txt = f"（还差 {_nk - _ck} 次探索）"
                    except Exception:
                        pass
                return f"🔒 这里似乎被什么遮挡着……（在本图继续『探索』可揭开它的面纱）{_progress_txt}"
        except Exception:
            pass
    return None


def resolve_map_target(dest: str):
    """目标地图寻址：地图名/ID 精确 → 旧区域别名 → 区域名（area_name）→ 区域入口。

    v86/v104 P1 口径（与『前往』原 else 分支逐行等价）：返回 dict 或 None。
    """
    for m in C.MAPS:
        if dest in (m["name"], m["id"]):
            return m
    if dest in C.LEGACY_MAP_ALIAS:
        return C.MAP_BY_ID.get(C.LEGACY_MAP_ALIAS[dest])
    # 区域名 → 区域入口
    for m in C.MAPS:
        if dest in m.get("area_name", ""):
            return m
    return None


def move_blocked_msg(cur_map: dict, player: dict, target_sa: dict) -> str:
    """v87.14 同图内不可直达时的提示(城镇星形 / 野外线性)。"""
    cur_sa_id = player.get("cur_subarea") or ""
    cur_name = cur_sa_id
    tgt_name = target_sa.get("name", target_sa.get("id", "？"))
    sas = cur_map.get("subareas") or []
    for s in sas:
        if s["id"] == cur_sa_id:
            cur_name = s["name"]
            break
    center = sas[0] if sas else {}
    if center.get("type") == C.SUB_TYPE_TOWN:
        # v87.16 街道链：在广场想去链上目标（东大街/镇郊）时提示必经之路
        if cur_sa_id == center.get("id", ""):
            chain = [s for s in sas if s.get("type") in (C.SUB_TYPE_STREET, C.SUB_TYPE_GATE)]
            # v95.12 防御：目标就是链首（无街道时链首=出口自身）不拦截，避免"先经过自己"
            if (any(s["id"] == target_sa.get("id") for s in chain)
                    and chain and chain[0]["id"] != target_sa.get("id")):
                first = chain[0]["name"] if chain else center.get("name", "广场")
                return (f"🧭 你身处【{cur_name}】，不能直接去【{tgt_name}】——"
                        f"路只有一条，需要先经过{first}。")
        # v95.12：非广场城镇子区域按空间连接提示必经路线（街道/出口链），
        # 不要一律"回广场"——镇郊去广场要先经过东大街，提示必须与真实路径一致
        links = C.subarea_links(cur_map.get("id", ""), cur_sa_id)
        link_names = [next((s["name"] for s in sas if s["id"] == lid), lid) for lid in links]
        return (f"🧭 你身处【{cur_name}】，不能直接去【{tgt_name}】——"
                f"路只有一条，需要先经过{'、'.join(link_names)}。")
    links = C.subarea_links(cur_map.get("id", ""), cur_sa_id)
    link_names = [next((s["name"] for s in sas if s["id"] == lid), lid) for lid in links]
    return (f"🧭 你身处【{cur_name}】，不能直接去【{tgt_name}】——"
            f"路只有一条，需要先经过{'、'.join(link_names)}。")


def leave_map_block_msg(cur_map: dict, player: dict) -> str:
    """v87.14 出图必须在该图出口子区域（城镇=城门，野外=入口）。

    未在出口 → 返回引导提示（同 move 跨图两段原文案）；已在出口/无出口 → ''。
    """
    exit_sa_id = C.map_exit_subarea(cur_map.get("id", ""))
    if exit_sa_id and player.get("cur_subarea") != exit_sa_id:
        sas = cur_map.get("subareas") or []
        _exit_name = next((s["name"] for s in sas if s["id"] == exit_sa_id), "出口")
        _cur_sa_name = next((s["name"] for s in sas if s["id"] == player.get("cur_subarea")),
                            player.get("cur_subarea", ""))
        return (f"🧭 你身处【{_cur_sa_name}】，还不能离开{cur_map.get('name', '此地')}——"
                f"需要先到{_exit_name}(『前往 {_exit_name}』)才能出城/出图。")
    return ""


# ============ 等级提示 / 体力经济（v94 / v101.13 坐骑概率免费） ============

def level_warn(player: dict, target: dict) -> str:
    """v87 跨图建议等级提示行（玩家低于目标图等级时）。"""
    if player["level"] < target["lv"]:
        return (f"\n⚠️ 建议等级 Lv.{target['lv']}，你才 Lv.{player['level']}，小心行事！")
    return ""


def stamina_max(player: dict) -> int:
    """体力上限：100 + 等级×2（base._stamina_max 同式，服务层自算版）"""
    return 100 + (player.get("level") or 1) * 2


def stamina_tired_line(player: dict) -> str:
    """体力 0 走不动提示段（move 跨图扣 1 前置拦截，原 4 行文案逐字符随迁）。"""
    return (
        f"⚡ 你太累了，走不动了！(体力 {int(player.get('stamina') or 0)}/{stamina_max(player)})\n"
        "💡 恢复体力：野外营地『休息』/ 吃食物 / 旅店『住宿』，或等体力自然恢复(每1分钟+1)\n"
        "💡 也可以『传送』(已激活的方碑)或使用『回城卷轴』脱身～\n"
        "💡 新手建议：野外活动前先在城镇『商店』买点食物（烤肉串等），体力 0 才不会困在野外～"
    )


def move_stamina_cost(player: dict) -> int:
    """跨图移动体力扣费：v101.13 坐骑 stamina_reduce 概率免费（返回 0/1）。

    等价于原 move 段 `0 if random.random() < float(mount_effects...stamina_reduce) else 1`——
    单次 random 消耗位置与次序完全一致（L3 seed 等价）。
    """
    if random.random() < float(C.mount_effects(player).get("stamina_reduce", 0) or 0):
        return 0
    return 1


# ============ 撞怪档位（v49 意见#4 / v130.7 / v130.8 → v132 ±1） ============

def travel_ambush(player: dict, target_map: dict, group_id=None, qq_id=None,
                  main_kill_hook=None):
    """移动撞怪判定：返回撞到的怪物 dict 或 None。

    生物趋避利害：
    - 玩家等级 ≥ 地图等级+5：威慑低等级生物，不撞怪
    - 玩家等级 ≤ 地图等级-5：闯入强者地盘，30% 概率撞怪
    - 同级/略低：8~18% 概率
    城镇区域不撞怪（安全区）。'城镇外郊' 类型数据不存在，v102.1 清理。

    main_kill_hook：命令层注入 _main_kill_target_on_map（combat 域只读判定）。
    缺省 None 或 group_id/qq_id 空 = 无群上下文 → 维持原语义跳过副本撞怪分支。
    """
    mtype = target_map.get("type", C.MAP_TYPE_FIELD)
    if mtype == C.MAP_TYPE_TOWN:
        return None
    # v95.23 #247：副本区域不参与移动撞怪——副本 Boss 在入口子区域 monsters 池里，
    # 撞怪会绕过『副本 <名字>』开本流程的等级/人数校验，低等级玩家进副本入口被 Boss 秒杀。
    # 副本入口应显示地图信息，引导玩家走开本流程（'副本' 命令有完整校验）。
    # v105 M19 P0：主线击杀目标只挂副本时放行——撞怪池仅保留主线目标怪
    # （走下方统一概率判定，Boss 按等级差概率撞，不绕过任何校验之外的新增风险面）。
    if mtype == C.MAP_TYPE_INSTANCE:
        # v105 M19 P0：主线击杀目标只挂副本时放行——撞怪池仅保留主线目标怪
        # （走下方统一概率判定；group_id/qq_id 为空=既有测试直调场景，维持原跳过）
        _main_ent = None
        if group_id and qq_id and main_kill_hook is not None:
            _main_ent = main_kill_hook(group_id, qq_id, target_map)
        if not _main_ent:
            return None
        monsters = [_main_ent]
        diff = target_map.get("lv", 1) - player["level"]
        if diff <= -5:
            return None
        if diff >= 5:
            chance = AMBUSH_HIGH_MIN
        elif diff >= 0:
            chance = AMBUSH_MID
        else:
            chance = AMBUSH_LOW
        if random.random() >= chance:
            return None
        return C.build_monster(random.choice(monsters), target_map, lv_jitter=1)
    # v87.6 内容下沉子区域：优先取落点入口子区域的怪；入口无怪才找最近有怪子区域
    # （M22 P3：原逻辑取"首个有怪子区域"，入口无怪时会抽到深处高等级怪，玩家刚进图就被深处怪秒）
    _sas = target_map.get("subareas") or []
    _entry_id = C.map_entry_subarea(target_map.get("id", ""))
    monsters = []
    for sa in _sas:
        if sa["id"] == _entry_id and sa.get("monsters"):
            monsters = sa["monsters"]
            break
    if not monsters:
        # 入口无怪：线性图按列表顺序扫描即离入口由近及远
        for sa in _sas:
            if sa.get("monsters"):
                monsters = sa["monsters"]
                break
    if not monsters:
        return None
    diff = target_map.get("lv", 1) - player["level"]
    if diff <= -5:
        return None
    # v130.7 意见#28 越级风险增强：比玩家高 5 级起，撞怪概率随等级差线性提升
    # （0.30 + (diff-5)*0.05；低 10 级 = 0.55，低 11 级+ = 0.60 封顶）
    if diff >= 5:
        chance = min(AMBUSH_HIGH_CAP, AMBUSH_HIGH_MIN + (diff - 5) * AMBUSH_HIGH_STEP)
    elif diff >= 0:
        chance = AMBUSH_MID
    else:
        chance = AMBUSH_LOW
    if random.random() >= chance:
        return None
    # v101.25c 移动撞怪也带等级波动（普通怪 ±1，精英/Boss 固定）
    # v130.8 意见#32：±1 感知弱 → 增强为 ±2；v132 鱼鱼拍板改回 ±1（面板明示 Lv.X±1）
    return C.build_monster(random.choice(monsters), target_map, lv_jitter=1)


# ============ 隐藏图 / 方碑路由（v87 / v115） ============

def hidden_map_block(group_id, qq_id, player: dict, target: dict):
    """隐藏图准入校验 → 命中返回拦截文案（str）；放行返回 None。

    v87：等级门槛 + 物品信物（H6 泛黄书页×3 / H7 烬火信标）+ 主线完成封印。
    三条提示逐字符等价于 move 原分支（文案含引导语，随迁不动）。
    """
    from .. import db  # 惰性导入
    if not target.get("hidden"):
        return None
    unlock = C.HIDDEN_MAP_UNLOCK.get(target["id"], {})
    if player["level"] < unlock.get("level", 99):
        return "前方被无形的屏障阻挡……这里需要更强大的实力！(等级不足)"
    # v87：物品型准入（H6 泛黄书页×3 / H7 烬火信标）
    item_req = unlock.get("item")
    if item_req:
        lack = [f"{name}×{need}" for name, need in item_req.items()
                if db.count_item(group_id, qq_id, name) < need]
        if lack:
            return (
                "入口被古老的力量封锁，似乎需要信物才能进入……\n"
                f"🔒 缺少：{'、'.join(lack)}\n"
                "💡 失落图书馆：集齐 3 张泛黄书页(探索彩蛋/圣堂地窖精英/符文石)\n"
                "💡 灰烬回廊：找到老守墓人·灰须领取烬火信标"
            )
    quests = db.get_quests(group_id, qq_id)
    if unlock.get("quest") not in quests.get("completed_main", []):
        return "地图的入口被古老魔法封印，似乎只有完成主线任务才能解开……"
    return None


def landing_subarea(target: dict, want_sa):
    """跨图移动落点子区域：v86 城镇=出口（entry_subarea），野外=入口；want_sa 覆盖。

    返回子区域 dict 或 None（无 subareas 且无 want_sa 命中时——命令层按 None 兜底，
    等价原 first_sa 语义：落库 cur_subarea=''、展示回退 target desc）。
    """
    target_sas = target.get("subareas") or []
    first_sa = None
    entry_sa_id = C.map_entry_subarea(target["id"])
    for _s in target_sas:
        if _s["id"] == entry_sa_id:
            first_sa = _s
            break
    if first_sa is None and target_sas:
        first_sa = target_sas[0]
    if want_sa:
        for _s in target_sas:
            if _s["id"] == want_sa:
                first_sa = _s
                break
    return first_sa


def portal_arrive_note(group_id, qq_id, target: dict) -> str:
    """到达图含未激活方碑 → 提示行（'' 表示无提示；v13 旅者方碑引导）。"""
    from .. import db  # 惰性导入
    tid = target.get("id", "")
    if tid in C.PORTALS and tid not in db.get_portals(qq_id):
        p = C.PORTALS[tid]
        return f"\n\n🌌 一座{p['icon']}{p['name']}矗立在此！『激活』可解锁传送点～"
    return ""
