# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - quests_flow（主线/支线任务状态机域，v181 P4-2）

主线（接取/交付/结局变体）与支线（接取/推进/分支交付/发奖）状态机规则原样随迁：
由 world.py 『接取/任务/放弃/交付任务』命令层 + combat.py 击杀推进 + economy.py use
推进 + talk_actions.py 对话动作 + instance.py 副本击杀 共同消费——命令层只留
解析/守卫/面板壳（async yield 流留命令层，v3.4 铁律），业务判定与落库收敛到本文件。

- 主线状态机：pending（未接）→ active（进行）→ ready（可交）→ 交付领奖推进 next
  （_take_main_quest：collect 实时数包置 ready/交付扣料、talk/explore 接取即达成、
  min_level 硬门槛、suggest_lv 软提示、q10_5 结局变体按对话 flag 分支）
- 支线状态机：接取（_offer_side_quest(s) 同源可接清单 side_available_list——
  unlock 链式前置/require_stats 计数门槛/min_level/require_race/board 过滤）、
  推进（combat/economy/explore 击杀·use·探索收敛 update_explore_quests/
  update_use_quests）、交付（collect 扣包 + branch 分支选项覆盖奖励 + deliver_text +
  quest_deliver 行为彩蛋 hooks）
- 发奖：grant_quest_rewards 三处共用（explore 自动完成/主线交付/支线交付）——
  reward_item 列表随机/eq: 名册、reward_pet/reward_mount、title 称号播报、
  unlock_class 隐藏职业解锁、exp/gold 结算升级（title_bonus 走 core 单点）
- 击杀型主/支线进度由 combat._update_quests 消费（v105 M19 P2 前缀精确匹配规则见 combat）
- _deliver_hint/_tip/_rule_fire 面板 I/O：deliver_hint 纯数据判定随迁；_tip/_rule_fire
  命令层能力经 complete_side_quest(hooks=...) 注入，缺省空实现（service 直测不依赖命令层）

依赖红线：可 import data/core/store/db/engine/battle/reward/sibling services；
禁止 import commands/*。db 等依赖一律函数体内惰性 import（core 样板铁律）。
"""

def obj_text(obj):
    from .. import content as C
    if obj.get("kill"):
        return f"击败 {obj['kill']} ×{obj['count']}"
    if obj.get("collect"):
        # v125.1 P2：s64 等 collect_count 无 count 的复合目标不再 KeyError
        return f"收集 {obj['collect']} ×{obj.get('collect_count') or obj.get('count', 1)}"
    if obj.get("explore"):
        return f"前往 {C.MAP_BY_ID.get(obj['explore'], {}).get('name', '？')}"
    if obj.get("find"):
        # v97.1 告示委托：在指定地图探索概率找到目标
        return f"在 {C.MAP_BY_ID.get(obj.get('map', ''), {}).get('name', '？')} 寻找 {obj['find']}(探索有概率遇到)"
    if obj.get("use"):
        # v124 use 目标：使用指定物品达成
        return f"使用 {obj['use']}"
    if obj.get("talk"):
        npc = C.NPCS.get(obj["talk"], {})
        return f"与 {npc.get('name', '？')} 交谈"
    return "？"


def sq_unlocked(quests, sq):
    """v124 链式支线：unlock 前置解锁检查。unlock 支持单条或列表（全部满足）。
    格式：{"side": "s5"} 或 {"main": "q2_3"}（兼容 {"type":"side","id":"s5"} 写法）。
    无 unlock=天然解锁。"""
    u = sq.get("unlock")
    if not u:
        return True
    us = u if isinstance(u, list) else [u]
    for x in us:
        if not isinstance(x, dict):
            continue
        _typ = x.get("type") or ("side" if x.get("side") else "main" if x.get("main") else None)
        _tid = x.get("id") or x.get("side") or x.get("main") or ""
        if _typ == "side":
            # 支线完成 = side dict 中该任务 status==done
            _sq = (quests.get("side") or {}).get(_tid) or {}
            if _sq.get("status") != "done":
                return False
        elif _typ == "main":
            _cm = quests.get("completed_main") or []
            if _tid not in _cm and quests.get("main_quest") != _tid:
                return False
    return True

def sq_stats_met(player, sq):
    """v124 隐藏线/副业线：require_stats 动作计数门槛。达标才可接取。
    stats 表以 qq_id 为主键，group_id 参数为兼容占位。"""
    from .. import db
    rs = sq.get("require_stats")
    if not rs:
        return True
    _qq = player.get("qq_id") or player.get("id", "")
    if not _qq:
        return False
    _st = db.get_stats("", _qq) or {}
    for k, v in rs.items():
        if int(_st.get(k, 0) or 0) < int(v):
            return False
    return True

def available_quest_list(player, quests, mq) -> list:
    """当前地图可接取任务列表（v123d 抽出，供『接取』无参渲染与『接取 <序号>』映射共用）。

    返回 [{"name": 任务名, "line": 渲染行（不含 📜 前缀）}, ...]——主线 pending 在前，
    支线按 C.SIDE_QUESTS 顺序；告示委托（board）不在此列（须去告示板指名接取）。
    """
    from .. import content as C
    available = []
    if mq and quests.get("main_status") == "pending":
        giver = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
        if giver.get("map") == player["cur_map"]:
            available.append({
                "name": mq["name"],
                "line": f"主线『{mq['name']}』（{giver.get('name', '？')}发布）",
            })
    for sq in C.SIDE_QUESTS:
        if sq["id"] in (quests.get("side") or {}):
            continue
        # v124 链式支线：unlock 前置未满足不出现在可接列表
        if not sq_unlocked(quests, sq):
            continue
        # v124 隐藏线：require_stats 计数门槛未达不出现在可接列表
        if not sq_stats_met(player, sq):
            continue
        # v104 M20 P2：告示委托（board: true）只在告示板子区域指名接取，
        # 列入普通列表会误导玩家（点名接取被 world.py 告示板拦截逻辑挡下）
        if sq.get("board"):
            continue
        npc = C.NPCS.get(sq["giver"]) or C.ALL_WILD.get(sq["giver"]) or {}
        if npc.get("map") == player["cur_map"]:
            # v104 M19：接取列表显示支线等级门槛
            _lv = f"Lv.{sq['min_level']}+ " if sq.get("min_level") else ""
            available.append({
                "name": sq["name"],
                "line": f"支线『{sq['name']}』{_lv}（{npc.get('name', '？')}发布）",
            })
    return available


# v116 §3.4：放弃进行中的支线/每日任务（释放接取位）。主线不可放弃。

def update_explore_quests(group_id, qq_id, map_id):
    """到达子区域时检查 explore 型任务(主线和支线)"""
    from .. import content as C
    from .. import db
    lines = []
    quests = db.get_quests(group_id, qq_id)
    changed = False
    # 主线 explore（v105：仅已接取(active)时触发——pending 未接取到达目标图不得自动完成+发奖）
    main_id = quests.get("main_quest")
    if main_id and quests.get("main_status") == "active":
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
        if mq and mq["objective"].get("explore") == map_id:
            # v124.3：奖励统一走 _grant_quest_rewards（exp/gold/升级 + reward_item 全格式
            # + reward_pet/reward_mount/unlock_class）——此前 explore 自动完成只有
            # reward_item 单值，reward_pet 配了也静默不发
            grant_quest_rewards(group_id, qq_id, mq, lines)
            completed = list(quests.get("completed_main", []))
            completed.append(main_id)
            quests["completed_main"] = completed
            quests["main_quest"] = mq["next"]
            # v105 M19 P1：explore 自动完成必须重置 main_status=pending（与 _take_main_quest
            # 交付分支一致）——此前遗留 "active" 导致任务面板显示"进行中"而非"未接取"、
            # 对话树 quest_pending 接取入口不亮（q1_5 完成后 q1_6 需 3-4 轮对话才兜底接取）
            quests["main_status"] = "pending"
            quests["main_progress"] = {}
            changed = True
            lines.append(f"📜 主线『{mq['name']}』达成！奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
            # v105 M19 P2：explore 自动完成补发声望（奖励本体已并入 _grant_quest_rewards）
            _rep = quest_reputation(group_id, qq_id, mq["giver"])
            if _rep:
                lines.append(f"  {_rep}")
            if mq["next"]:
                nq = next((q for q in C.MAIN_QUESTS if q["id"] == mq["next"]), None)
                if nq:
                    lines.append(f"📜 新主线：『{nq['name']}』{nq['desc']}")
            else:
                lines.append("🎊 恭喜！你完成了全部主线任务，成为奥兰迪亚的传说！")
    # 支线 explore
    side = dict(quests.get("side", {}))
    for sid, sq in list(side.items()):
        if sq.get("status") == "active":
            sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
            if sqd and sqd["objective"].get("explore") == map_id:
                sq["status"] = "ready"
                changed = True
                _g = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {_g.get('name', '？')} {deliver_hint(sqd['giver'])}吧～")
    if changed:
        quests["side"] = side
        db.save_quests(group_id, qq_id, quests)
    return lines

def take_main_quest(group_id, qq_id, npc_id, npc):
    """从 NPC 接主线任务；返回通知行列表"""
    from .. import content as C
    from .. import db
    lines = []
    player = db.get_player(group_id, qq_id)
    quests = db.get_quests(group_id, qq_id)
    main_id = quests.get("main_quest")
    if not main_id:
        lines.append("🎊 主线任务已全部完成，你已是奥兰迪亚的传说！")
        return lines
    mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
    # 存档容错：main_quest 指向已不存在的任务（旧存档/主线数据变更）→ 重置回主线起点
    if not mq and main_id:
        quests["main_quest"] = "q1_1"
        quests["main_status"] = "pending"
        quests["main_progress"] = {}
        main_id = "q1_1"
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
    if not mq or mq["giver"] != npc_id:
        # 不是这个 NPC 的任务
        need_npc = C.NPCS.get(mq["giver"], {}).get("name", "？") if mq else "？"
        lines.append(f"【{npc['name']}】我现在没有任务交给你。镇长/各地首领或许有安排……")
        if mq:
            lines.append(f"📜 当前主线『{mq['name']}』由 {need_npc} 发布。")
        return lines
    st = quests.get("main_status", "pending")
    # v105 P0：collect 型主线（q5_5 圣光百合）——背包材料足够即置 ready
    # （对齐支线逻辑 talk_actions.py:111-113 实时数背包；交付时再扣材料）
    # 放在状态分发前：pending 接取时材料已齐 → 直接可交付；active 回来找 NPC → 置 ready
    obj0 = mq["objective"]
    if obj0.get("collect") and st != "ready" and db.count_item(group_id, qq_id, obj0["collect"]) >= obj0.get("count", 1):
        quests["main_status"] = "ready"
        quests["main_progress"] = {obj0["collect"]: obj0.get("count", 1)}
        db.save_quests(group_id, qq_id, quests)
        st = "ready"
    if st == "pending":
        # v169.1：主线 min_level 硬门槛（高经验主线防跨级接取；suggest_lv 仅软提示保留）
        if mq.get("min_level") and player["level"] < mq["min_level"]:
            return lines + [f"🛡️ 『{mq['name']}』需要 Lv.{mq['min_level']} 才能接取！（你当前 Lv.{player['level']}）先去提升实力吧～"]
        quests["main_status"] = "active"
        quests["main_progress"] = {}
        # talk 型任务：与发布 NPC 交谈即达成目标（对话即完成）
        obj = mq["objective"]
        if obj.get("talk") and obj["talk"] == npc_id:
            quests["main_status"] = "ready"
            quests["main_progress"] = {obj["talk"]: 1}
        # v105 P2：explore 型主线接取时已在目标地图 → 直接置 ready（免出图重进）
        if obj.get("explore") and player.get("cur_map") == obj["explore"]:
            quests["main_status"] = "ready"
            quests["main_progress"] = {obj["explore"]: 1}
        db.save_quests(group_id, qq_id, quests)
        lines.append(f"📜 【接取任务】『{mq['name']}』")
        if mq.get("story"):
            lines.append(f"  📖 {mq['story']}")
        lines.append(f"  🎯 目标：{obj_text(mq['objective'])}")
        lines.append(f"  奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
        # v95.25 #138：主线等级建议（软提示，不拦截接取）——suggest_lv 在 quests.py 数据里
        if mq.get("suggest_lv") and player["level"] < mq["suggest_lv"]:
            lines.append(f"  ⚠️ 建议等级 Lv.{mq['suggest_lv']}，你才 Lv.{player['level']}——可以先练练级再挑战！")
        if quests["main_status"] == "ready":
            lines.append("  ✨ 交谈完成！再与这位 NPC 对话即可交付任务。")
    elif st == "ready":
        # 交任务领奖
        obj = mq.get("objective") or {}
        # v105 P0：collect 型主线交付时扣材料（先复核背包，材料被消耗则回到进行中）
        if obj.get("collect"):
            need = obj.get("count", 1)
            if db.count_item(group_id, qq_id, obj["collect"]) < need:
                quests["main_status"] = "active"
                quests["main_progress"] = {}
                db.save_quests(group_id, qq_id, quests)
                lines.append(f"📜 交付『{mq['name']}』需要 {obj['collect']} ×{need}，你背包里不够了，先去凑齐吧～")
                return lines
            db.remove_item(group_id, qq_id, obj["collect"], need)
            # v126.2：鱼获个体属性在 item_data.tags，remove_item 自动截断，无需额外同步
            lines.append(f"🎒 交出 {obj['collect']} ×{need}")
        # v124.3：奖励统一走 _grant_quest_rewards（exp/gold/升级 + reward_item 全格式
        # + reward_pet/reward_mount/unlock_class）——此前主线交付只支持 reward_item
        # 单值 + reward_pet，eq:/list 随机/坐骑/隐藏职业配了不发
        grant_quest_rewards(group_id, qq_id, mq, lines)
        completed = list(quests.get("completed_main", []))
        completed.append(main_id)
        quests["completed_main"] = completed
        quests["main_quest"] = mq["next"]
        quests["main_status"] = "pending"
        quests["main_progress"] = {}
        db.save_quests(group_id, qq_id, quests)
        lines.append(f"✅ 【任务完成】『{mq['name']}』！")
        if mq.get("ending"):
            # v105 M19 P1：主线抉择结局变体——q10_5 等任务按对话树选择的 flag 输出不同结尾
            _ending = mq["ending"]
            _endings = mq.get("endings") or {}
            if _endings:
                try:
                    _flags = db.get_talk_flags(group_id, qq_id, mq["giver"]) or []
                except Exception:
                    _flags = []
                for _fk, _fv in _endings.items():
                    if _fk in _flags:
                        _ending = _fv
                        break
            lines.append(f"  📖 {_ending}")
        lines.append(f"  奖励：经验 +{mq['reward_exp']} 金币 +{mq['reward_gold']}")
        rep_line = quest_reputation(group_id, qq_id, mq["giver"])
        if rep_line:
            lines.append(f"  {rep_line}")
        if mq["next"]:
            nq = next((q for q in C.MAIN_QUESTS if q["id"] == mq["next"]), None)
            if nq:
                lines.append(f"📜 新主线：『{nq['name']}』{nq['desc']}")
                lines.append(f"  🎯 去找 {C.NPCS[nq['giver']]['name']} 接取新任务")
        else:
            lines.append("🎊 恭喜！你完成了全部主线任务，成为奥兰迪亚的传说！")
    else:
        lines.append(f"📜 你已接取『{mq['name']}』：{mq['desc']}")
    return lines

def quest_reputation(group_id, qq_id, npc_id):
    """完成任务时给对应势力加声望，返回提示行(如有)"""
    from .. import content as C
    from .. import db
    npc = C.NPCS.get(npc_id)
    if not npc:
        return ""
    m = C.MAP_BY_ID.get(npc["map"], {})
    area_key = m.get("area", npc["map"])
    faction = C.AREA_FACTION.get(area_key)
    if not faction:
        return ""
    db.add_reputation(group_id, qq_id, faction, 10)
    return f"🏛️ {C.FACTIONS[faction]['icon']} 声望＋10"

def deliver_hint(npc_id):
    """交付方式提示（v95.16 #75）：有对话树 NPC 走对话交付，无对话树 NPC 用『交付任务』"""
    from .. import content as C
    if C.DIALOGUES.get(npc_id):
        return "对话交付"
    return "『交付任务』交付"

def side_available_list(group_id, qq_id, npc_id, npc) -> list:
    """v127.6：该 NPC 名下当前"可接"的支线清单（对话菜单/预告/全接三处同源过滤）。

    过滤条件与旧 _offer_side_quests 全部一致：giver == npc_id、非告示板委托(board)、
    未接取（不在 side）、_sq_unlocked 链式前置、_sq_stats_met 计数门槛、
    min_level 等级门槛、require_race 种族限制。每项返回
    {sid, name, desc, objective_text, reward_exp, reward_gold}，按 SIDE_QUESTS 定义顺序
    （保证对话菜单序号稳定）。npc 参数保留以与 _offer_side_quests 签名一致（此处未用到）。
    """
    from .. import content as C
    from .. import db
    player = db.get_player(group_id, qq_id) or {}
    quests = db.get_quests(group_id, qq_id)
    side = quests.get("side", {}) or {}
    out = []
    for sq in C.SIDE_QUESTS:
        if sq["giver"] != npc_id:
            continue
        if sq.get("board"):  # v95r65 #295：告示板委托只能在告示板接取，NPC 不自动发
            continue
        if sq["id"] in side:
            continue
        # v124 链式支线：unlock 前置未满足不自动发（如剧情线第二步等第一步完成）
        if not sq_unlocked(quests, sq):
            continue
        # v124 隐藏线/副业线：require_stats 计数门槛未达不自动发（如 H7 需垂钓 10 次）
        if not sq_stats_met(player, sq):
            continue
        # v101.30d #O52：支线等级门槛（min_level 字段）——等级不够不算可接
        if sq.get("min_level") and (player.get("level") or 0) < sq["min_level"]:
            continue
        # v113 种族限制：require_race 指定血脉（隐藏线试炼）——非该种族不算可接
        if sq.get("require_race"):
            _cur = player.get("race") or "human"
            if _cur != sq["require_race"]:
                continue
        out.append({
            "sid": sq["id"],
            "name": sq["name"],
            "desc": sq.get("desc", ""),
            "objective_text": obj_text(sq.get("objective") or {}),
            "reward_exp": sq.get("reward_exp", 0),
            "reward_gold": sq.get("reward_gold", 0),
        })
    return out

def offer_side_quest(group_id, qq_id, npc_id, sid) -> list:
    """v127.6：单条支线接取（对话 side_menu 子选项 action: side_take_one）。

    校验 sid 必须在 _side_available_list 当前可接清单内才接（防越权/已接/等级不足），
    否则返回 [] 不落地。返回该任务的接取通知行列表。
    """
    from .. import content as C
    from .. import db
    item = next((a for a in side_available_list(group_id, qq_id, npc_id, None)
                 if a["sid"] == sid), None)
    if not item:
        return []
    sq = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
    if not sq:
        return []
    quests = db.get_quests(group_id, qq_id)
    side = dict(quests.get("side", {}))
    side[sid] = {"status": "active", "progress": {}}
    quests["side"] = side
    db.save_quests(group_id, qq_id, quests)
    return [
        f"📜 【支线】『{sq['name']}』{sq['desc']}",
        f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}",
        f"  🎯 目标：{item['objective_text']}",
    ]

def offer_side_quests(group_id, qq_id, npc_id, npc):
    """NPC 有未接的支线任务时自动接取，返回通知行列表

    v127.6 重构：可接清单统一走 _side_available_list（与对话 side_menu 菜单/预告同源过滤），
    逐条复用 _offer_side_quest 接取；不可接（min_level/require_race 被过滤掉）的
    原拒绝提示按 SIDE_QUESTS 顺序保留，全接+完成提示行为不变（旧 side_offer action 兼容，
    单支线 NPC 无感）。
    """
    from .. import content as C
    from .. import db
    player = db.get_player(group_id, qq_id) or {}
    lines = []
    quests = db.get_quests(group_id, qq_id)
    side = dict(quests.get("side", {}))
    available = side_available_list(group_id, qq_id, npc_id, npc)
    av_ids = {a["sid"] for a in available}
    changed = False
    for sq in C.SIDE_QUESTS:
        if sq["giver"] != npc_id or sq.get("board"):
            continue
        if sq["id"] in side:
            continue
        if sq["id"] in av_ids:
            side[sq["id"]] = {"status": "active", "progress": {}}
            changed = True
            lines.append(f"📜 【支线】『{sq['name']}』{sq['desc']}")
            lines.append(f"  奖励：经验 +{sq['reward_exp']} 金币 +{sq['reward_gold']}")
            lines.append(f"  🎯 目标：{obj_text(sq['objective'])}")
            continue
        # 不可接但符合其余条件的拒绝提示（与原始行为文案一致）
        if not sq_unlocked(quests, sq):
            continue
        if not sq_stats_met(player, sq):
            continue
        # v101.30d #O52：支线等级门槛——等级不够不自动接
        if sq.get("min_level") and (player.get("level") or 0) < sq["min_level"]:
            lines.append(
                f"🛡️ {npc.get('name', '对方')}打量了你一眼：这活得有 Lv.{sq['min_level']}+ 的本事，你再去练练吧。"
            )
            continue
        # v113 种族限制：require_race 指定血脉——非该种族导师直接拒绝
        if sq.get("require_race"):
            _rr = sq["require_race"]
            _cur = player.get("race") or "human"
            if _cur != _rr:
                _rcn = (C.RACES.get(_rr) or {}).get("name", "对应血脉")
                lines.append(
                    f"⛔ {npc.get('name', '对方')}凝视着你，缓缓摇头：『这份传承只属于{_rcn}的血脉。"
                    f"你体内流淌的{(C.RACES.get(_cur) or {}).get('name', '血脉')}之血，与它无缘。』"
                )
                continue
    if changed:
        quests["side"] = side
        db.save_quests(group_id, qq_id, quests)
    # v95.4：该 NPC 有已完成支线 → 提示交付入口（反馈：可交任务找不到交付方式）
    # v95.15 #73：代词按 NPC 性别（迷路骑士等男性 NPC 用"他"）
    # v95.16 #75：按是否有对话树区分交付引导（无对话树 NPC 的『对话』没有交付选项）
    _ta = "她" if npc.get("gender") == "女" else "他"
    for sid, sq in list(quests.get("side", {}).items()):
        sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
        if sqd and sqd["giver"] == npc_id and sq.get("status") == "ready":
            if C.DIALOGUES.get(npc_id):
                lines.append(f"✅ 『{sqd['name']}』已完成！与{_ta}对话即可交付～")
            else:
                lines.append(f"✅ 『{sqd['name']}』已完成！输入『交付任务』即可交付～")
            break
    return lines

# v104 M24 P2-2：『交任务』无命中（策划案 23 章:182 主指令）→ 补别名

def grant_quest_rewards(group_id, qq_id, qdef, lines):
    """v124.3 统一任务奖励发放（主线 explore 自动完成 / 主线交付 / 支线交付三处共用）。

    基准：支线 _complete_side_quest 原实现（v104 M20 + v124 全奖励类型）——
    reward_exp/reward_gold 入角色并结算升级；reward_item 支持单值 / 列表随机 /
    eq: 装备名册；reward_pet 宠物蛋 / reward_mount 坐骑缰绳入包；unlock_class
    解锁隐藏职业。声望 / 分支 flag / 每日计数等任务特有处理不入此函数，调用方各自保留。
    返回结算后的 player（调用方后续需要时使用，如 _complete_side_quest 的 _rule_fire）。"""
    from .. import content as C
    from .. import db
    from ..content_rules.gameplay import check_player_level_up
    from ..core.stat_bonus import stat_bonus
    import random
    player = db.get_player(group_id, qq_id)
    player["exp"] += qdef.get("reward_exp", 0)
    player["gold"] += qdef.get("reward_gold", 0)
    player["_title_bonus"] = stat_bonus(group_id, qq_id, player)
    lv_logs, player = check_player_level_up(group_id, qq_id, player)
    db.update_player(group_id, qq_id, exp=player["exp"], gold=player["gold"], level=player["level"], hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"], max_mp=player["max_mp"], skills=player["skills"], attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0), learned_skills=player.get("learned_skills", []))
    if lv_logs:
        if lines:
            lines.append("")
        lines += lv_logs
    # v104 M20 P1：列表型奖励（如 s17 随机符文）→ 随机抽一个发放
    # v174 统一抽象：item/eq/pet/mount/title 发放走 game.reward.grant_reward
    # （只传物品类，exp/gold 已在上方原逻辑结算且要 return 更新后 player）
    ri = qdef.get("reward_item")
    _reward_items = []
    if ri:
        if isinstance(ri, list):
            ri = random.choice(ri)
        # eq: 前缀保留（grant_reward 支持 eq:rid 按名册名解析）
        _reward_items.append({"item": ri, "n": 1})
    _rew = {}
    if _reward_items:
        _rew["items"] = _reward_items
    rp = qdef.get("reward_pet")
    if rp:
        _rew["pets"] = [rp] if isinstance(rp, str) else list(rp)
    rm = qdef.get("reward_mount")
    if rm:
        _rew["mounts"] = [rm] if isinstance(rm, str) else list(rm)
    _tid = qdef.get("title")
    if _tid:
        _rew["title"] = _tid
    if _rew:
        try:
            from ..reward import grant_reward
            grant_reward(_rew, group_id, qq_id, player=player, lines=lines)
        except Exception:
            pass
    # v87 隐藏职业：交任务解锁（unlock_class 写入 hidden_class_unlock）
    uc = qdef.get("unlock_class")
    if uc:
        player_now = db.get_player(group_id, qq_id)
        unlocks = list(player_now.get("hidden_class_unlock", []) or [])
        if uc not in unlocks:
            unlocks.append(uc)
            db.update_player(group_id, qq_id, hidden_class_unlock=unlocks)
            lines.append(f"  ⚔️ 传承达成！隐藏职业「{C.CLASSES.get(uc, {}).get('name', uc)}」已解锁！")
            # v112：档位门槛统一读 CLASSES["tier_levels"]（缺省 T1=40），删除 60/30 特例
            _need = (C.CLASSES.get(uc, {}).get("tier_levels") or {1: 40, 2: 60, 3: 90})[1]
            _cname = C.CLASSES.get(uc, {}).get("name", uc)
            lines.append(f"  💡 达到 {_need} 级后输入『转职 {_cname}』接受传承！")
    # v140 波3.6：任务奖励称号（title 字段 = titles.py id 或中文名；称号系统条件判定自动拥有，
    # 这里仅播报解锁——条件满足即生效，不满足也不阻塞任务完成）
    _tid = qdef.get("title")
    if _tid:
        _tinfo = next((t for t in C.TITLES if t.get("id") == _tid), None)
        if not _tinfo:
            # 兼容支线旧字段用中文名（如 "北境的恩人" → north_benefactor）
            _tinfo = next((t for t in C.TITLES if t.get("name") == _tid), None)
        if _tinfo:
            lines.append(f"  🏅 获得称号：「{_tinfo.get('name', _tid)}」！")
        else:
            print(f"[dragonfall][v140] 任务『{qdef.get('name', '')}』称号 id 缺失：{_tid}（titles.py 未登记），已跳过")
    return player

def complete_side_quest(group_id, qq_id, sid, branch_choice=None, hooks=None):
    """交支线任务，返回通知行列表
    v124：支持 branch 分支交付（第一次输出选项并置 branch_wait，玩家回复数字后执行）+
    deliver_text 交付剧情文本。

    hooks：命令层注入 {"tip": callable(cat)->str, "rule_fire": callable(trigger,...)->str}
    （_tip/_rule_fire 是命令层 I/O 面板能力，P4-2 按 §5.2 以 hooks 回调接入）；
    缺省（None）时 _tip 返回空串、_rule_fire 返回空串——service 直测不依赖命令层。"""
    from .. import content as C
    from .. import db
    _tip = (hooks or {}).get("tip")
    _rule_fire = (hooks or {}).get("rule_fire")
    lines = []
    quests = db.get_quests(group_id, qq_id)
    sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
    if not sqd:
        return ["未知支线任务。"]
    sq = quests.get("side", {}).get(sid)
    if not sq:
        return ["这个任务还没完成呢。"]
    obj = sqd["objective"]
    # 收集型：实时检查背包材料（不依赖 ready 状态）
    if obj.get("collect"):
        # v87 复合目标：kill+collect（魔剑士试炼），collect_count 独立于 kill count
        need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 不再 KeyError
        _ckey = C.resolve("materials", obj["collect"])
        have = db.count_item(group_id, qq_id, _ckey)
        if have < need:
            return [f"材料不够！需要 {obj['collect']} ×{need}，你只有 {have} 个。"]
        # v87 复合目标：同时存在 kill 目标时，击杀进度也要满足
        if obj.get("kill"):
            kp = (sq.get("progress") or {}).get(obj["kill"], 0)
            if kp < obj["count"]:
                return [f"还要击败 {obj['kill']} ×{obj['count'] - kp}(当前 {kp}/{obj['count']})！"]
    elif sq.get("status") != "ready":
        return ["这个任务还没完成呢。"]
    # v124 分支任务：第一次交付输出选项，等待玩家回复数字
    br = sqd.get("branch")
    if br and not branch_choice:
        opts = br.get("options") or []
        if sq.get("branch_wait"):
            return [f"{br.get('prompt', '')}\n{_tip('quest_branch')}\n" + "\n".join(
                f"  {o.get('key', str(i + 1))}. {o.get('label', '')}" for i, o in enumerate(opts))]
        quests["side"][sid] = {**sq, "status": "ready", "branch_wait": True}
        db.save_quests(group_id, qq_id, quests)
        _o = [f"  {o.get('key', str(i + 1))}. {o.get('label', '')}" for i, o in enumerate(opts)]
        return [f"{br.get('prompt', '')}\n{_tip('quest_branch')}\n" + "\n".join(_o)]
    # v124 分支选择执行
    if br and branch_choice:
        opts = br.get("options") or []
        chosen = None
        if isinstance(branch_choice, str):
            for o in opts:
                if branch_choice in (o.get("key"), o.get("label")):
                    chosen = o
                    break
        if chosen is None:
            return [f"没有这个选项～{br.get('prompt', '')}\n{_tip('quest_branch')}\n" + "\n".join(
                f"  {o.get('key', str(i + 1))}. {o.get('label', '')}" for i, o in enumerate(opts))]
        # 用分支选项覆盖奖励（顶层 reward 为 0 时以选项为准）
        lines.append(f"  📖 {chosen.get('text', '')}")
        sqd = {**sqd,
               "reward_exp": chosen.get("reward_exp", sqd.get("reward_exp", 0)),
               "reward_gold": chosen.get("reward_gold", sqd.get("reward_gold", 0)),
               "reward_item": chosen.get("reward_item", sqd.get("reward_item"))}
        # v124 分支 flag：写入 giver NPC 的 flag 桶（称号/后续任务判定用）
        _cf = chosen.get("flag")
        if _cf:
            db.set_talk_flag(group_id, qq_id, sqd.get("giver", ""), _cf)
    # 收集类：扣除材料
    if obj.get("collect"):
        need = obj.get("collect_count") or obj.get("count", 1)  # v125.1 P2：s64 等 collect_count 无 count 不再 KeyError
        for _ in range(need):
            db.remove_item(group_id, qq_id, _ckey)
        # v126.2：鱼获个体属性在 item_data.tags，remove_item 自动截断，无需额外同步
    # v124 交付剧情文本（无分支时）
    dt = sqd.get("deliver_text")
    if dt and not br:
        lines.append(f"  📖 {dt}")
    # v124.3：奖励统一走 _grant_quest_rewards（exp/gold/升级 + reward_item 全格式 +
    # reward_pet/reward_mount/unlock_class）——逻辑与支线原实现完全一致（列表随机 /
    # eq: 名册 / items→materials 顺序），返回结算后 player 供下方 _rule_fire 使用
    player = grant_quest_rewards(group_id, qq_id, sqd, lines)
    # v95.12：交付后保留条目标记 done（无 completed_side 列），防止 _offer_side_quests 自动重接
    quests["side"][sid] = {"status": "done"}
    db.save_quests(group_id, qq_id, quests)
    # v104 M20：行会委托每日（complete_side）——支线交付完成 +1，达标发奖
    from .quests import bump_daily_progress as _bump_daily_progress
    _bump_daily_progress(group_id, qq_id, "complete_side", lines)
    lines.append(f"✅ 【支线完成】『{sqd['name']}』！")
    lines.append(f"  奖励：经验 +{sqd['reward_exp']} 金币 +{sqd['reward_gold']}")
    rep_line = quest_reputation(group_id, qq_id, sqd["giver"])
    if rep_line:
        lines.append(f"  {rep_line}")
    # v97.5 行为彩蛋规则：任务交付后
    _rule_txt = _rule_fire("quest_deliver", group_id, qq_id, player,
                           C.MAP_BY_ID.get(player.get("cur_map"), {}))
    if _rule_txt:
        lines.append(f"  {_rule_txt}")
    return lines

def talk_quest_progress(group_id, qq_id, npc_id) -> list:
    """v95.11：talk 型主线与目标 NPC 对话即达成（active 空进度遗留态 → ready）。
    覆盖 v95.9 对话化之前接取、或接取瞬间未置 ready 的存量档，返回通知行。
    v105 P0/P2：collect 型主线对话时实时数背包（材料足够 → ready）；
    explore 型主线已在目标地图 → ready（免出图重进）。"""
    from .. import content as C
    from .. import db
    quests = db.get_quests(group_id, qq_id)
    if quests.get("main_status") != "active":
        return []
    mid = quests.get("main_quest")
    if not mid:
        return []
    mq = next((q for q in C.MAIN_QUESTS if q["id"] == mid), None)
    if not mq:
        return []
    obj = mq.get("objective", {})
    if obj.get("talk") == npc_id:
        quests["main_status"] = "ready"
        quests["main_progress"] = {npc_id: 1}
        db.save_quests(group_id, qq_id, quests)
        return ["✨ 交谈完成！再与这位 NPC 对话即可交付任务。"]
    if obj.get("collect") and mq.get("giver") == npc_id:
        need = obj.get("count", 1)
        if db.count_item(group_id, qq_id, obj["collect"]) >= need:
            quests["main_status"] = "ready"
            quests["main_progress"] = {obj["collect"]: need}
            db.save_quests(group_id, qq_id, quests)
            return [f"✨ 材料已齐（{obj['collect']} ×{need}）！再与这位 NPC 对话即可交付任务。"]
    if obj.get("explore") and mq.get("giver") == npc_id:
        player = db.get_player(group_id, qq_id)
        if player.get("cur_map") == obj["explore"]:
            quests["main_status"] = "ready"
            quests["main_progress"] = {obj["explore"]: 1}
            db.save_quests(group_id, qq_id, quests)
            return ["✨ 目标地点已到达！再与这位 NPC 对话即可交付任务。"]
    return []

# ---------------- v95.23 职业就职 / 导师转职 ----------------

def update_use_quests(group_id, qq_id, item_name):
    """v124 use 目标支线：使用指定物品后支线置 ready（如 递麦酒/用月鳞/交信物）。
    v124.2 防跨图白嫖：objective.map 或任务自身 map 配置时，须玩家当前地图一致才推进；
    objective 无 map 且任务无 map 的保持原行为（不校验直接推进）。"""
    from .. import content as C
    from .. import db
    if not item_name:
        return ""
    quests = db.get_quests(group_id, qq_id)
    side = quests.get("side") or {}
    lines = []
    changed = False
    for sid, sq in list(side.items()):
        if sq.get("status") != "active":
            continue
        sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
        if not sqd:
            continue
        obj = sqd.get("objective") or {}
        if obj.get("use") and obj["use"] == item_name:
            _need_map = obj.get("map") or sqd.get("map")
            if _need_map:
                _pm = db.get_player(group_id, qq_id) or {}
                if _pm.get("cur_map") != _need_map:
                    continue
            side[sid] = {"status": "ready", "progress": {"use": item_name}}
            changed = True
            giver = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
            lines.append(f"✨ 『{sqd['name']}』目标达成！回去找 {giver.get('name', '发布人')} 交付吧～")
    if changed:
        quests["side"] = side
        db.save_quests(group_id, qq_id, quests)
    return "\n".join(lines)

def branch_wait_sid(group_id, qq_id):
    """v124：查找处于分支等待状态的支线 sid（ready + branch_wait）。"""
    from .. import db
    quests = db.get_quests(group_id, qq_id)
    for sid, sq in (quests.get("side") or {}).items():
        if sq.get("status") == "ready" and sq.get("branch_wait"):
            return sid
    return None

def quest_kill_progress(group_id, qq_id, monster):
    """战斗后更新任务进度（主线/支线/每日击杀型），返回通知行——combat._update_quests 击杀段原样随迁。

    v181 P4-2：combat._update_quests 的 quest 段（主线/支线 kill/kill_any + 每日 kill_any/elite/boss）
    收敛本函数，combat 只留调用壳；周常悬赏 weekly_bump_kill 属 weekly 域不随迁（调用方自行追加）。
    匹配规则 v105 M19 P2 前缀精确（== 或 「目标·」开头）；每日结算走 services.quests.settle_daily_quest
    （P4-1 试点已收敛单点）。kill_any 支线用 progress.any（v95.13 防卡死）。
    """
    from .. import content as C
    from .. import db
    from ..services.quests import DAILY_META_KEYS, settle_daily_quest
    lines = []
    quests = db.get_quests(group_id, qq_id)
    changed = False
    # 主线（仅处理已接且进行中的任务；击杀达到目标则变为可交状态）
    main_id = quests.get("main_quest")
    if main_id:
        mq = next((q for q in C.MAIN_QUESTS if q["id"] == main_id), None)
        if mq and quests.get("main_status") == "active":
            prog = dict(quests.get("main_progress", {}))
            obj = mq["objective"]
            if obj.get("kill") and (monster["name"] == obj["kill"] or monster["name"].startswith(obj["kill"] + "·")):
                # v95.7 #33：精英/头目变体名包含目标怪名（如『野猪』←『野猪·首领』）也计入任务进度
                # v105 M19 P2：进度 key 统一记 obj['kill']（此前记 monster['name']，杀精英变体时
                # 计数入账但面板按 obj['kill'] 读 → 显示 0/N；现精英击杀也计入基础怪 key）
                # v104 M20 P2：in 后缀包含误伤面过大（『野猪』命中巨型野猪/风车野猪/铁甲野猪/
                # 岛野猪，『霜巨魔』顶 3 只霜巨魔王），改前缀精确：== 或 「目标·」开头，仅命中
                # 同名怪与「·」后缀精英/Boss 变体
                prog[obj["kill"]] = prog.get(obj["kill"], 0) + 1
                quests["main_progress"] = prog
                changed = True
                if prog.get(obj["kill"], 0) >= obj["count"]:
                    quests["main_status"] = "ready"
                    _g = C.NPCS.get(mq["giver"]) or C.ALL_WILD.get(mq["giver"]) or {}
                    lines.append(f"📜 主线『{mq['name']}』目标达成！回去找 {_g.get('name', '？')} {deliver_hint(mq['giver'])}吧～")
                else:
                    lines.append(f"📜 主线『{mq['name']}』：{prog[obj['kill']]}/{obj['count']}")
    # 每日
    # v94：先清跨天任务（daily 里 _date 不是今天 → 清空），避免旧任务残留
    if db.expire_daily(quests):
        changed = True
    daily = dict(quests.get("daily", {}))
    # v125.1 P0 修复：跳过全部元数据键（_date/_completed/_repeat）——原只跳过 _date，
    # _completed(int)/_repeat(dict) 被 dq["objective"] 下标 → TypeError 每日首战必崩
    for dkey, dq in list(daily.items()):
        if dkey in DAILY_META_KEYS:  # 跨天/计数元数据，不是任务
            continue
        dobj = dq["objective"]
        prog = dq.get("progress", 0)
        if dobj.get("kill_any"):
            prog += 1
        elif dobj.get("kill_elite") and monster.get("is_elite"):
            prog += 1
        elif dobj.get("kill_boss") and monster.get("is_boss"):
            prog += 1
        dq["progress"] = prog
        changed = True
        if prog >= dobj.get("kill_any", dobj.get("kill_elite", dobj.get("kill_boss", 99))):
            # v125.1 P2：发奖结算统一走 settle_daily_quest（与 world 非击杀 bump 同单点；
            # 击杀型每日在此接线，防刷上限/衰减对击杀型同样生效）
            settle_daily_quest(group_id, qq_id, daily, dq, lines)
            del daily[dkey]
    # 无条件写回：即使全部完成（daily 为空）也要清空 quests，否则任务残留会无限重复发奖励
    quests["daily"] = daily
    # 支线（击杀型）
    side = dict(quests.get("side", {}))
    for sid, sq in list(side.items()):
        if sq.get("status") != "active":
            continue
        sqd = next((q for q in C.SIDE_QUESTS if q["id"] == sid), None)
        if not sqd:
            continue
        obj = sqd["objective"]
        if obj.get("kill_any"):
            # v95.13 修复：kill_any 支线（护送商货等）此前无计数分支，任务永久卡死
            prog = dict(sq.get("progress", {}))
            prog["any"] = prog.get("any", 0) + 1
            sq["progress"] = prog
            changed = True
            if prog["any"] >= obj["kill_any"]:
                sq["status"] = "ready"
                _g = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {_g.get('name', '？')} {deliver_hint(sqd['giver'])}吧～")
            else:
                lines.append(f"📜 支线『{sqd['name']}』：{prog['any']}/{obj['kill_any']}")
        elif obj.get("kill") and (monster["name"] == obj["kill"] or monster["name"].startswith(obj["kill"] + "·")):
            # v105 M19 P2：进度 key 统一记 obj['kill']（与主线一致、与面板/交付校验读取一致）
            # v104 补测发现：支线此前只精确 ==（杀精英变体不推进），现与主线同款前缀精确匹配
            # v104 M20 P2：in 后缀包含误伤面过大（『盗贼』命中盗贼头目·黑鸦、『霜巨魔』顶 3 只
            # 霜巨魔王、『月狼』命中月狼王·银鬃），改前缀精确：== 或 「目标·」开头
            prog = dict(sq.get("progress", {}))
            # v105 M19 P2：进度 key 统一记 obj['kill']（与主线一致、与面板/交付校验读取一致）
            prog[obj["kill"]] = prog.get(obj["kill"], 0) + 1
            sq["progress"] = prog
            changed = True
            if prog.get(obj["kill"], 0) >= obj["count"]:
                sq["status"] = "ready"
                _g = C.NPCS.get(sqd["giver"]) or C.ALL_WILD.get(sqd["giver"]) or {}
                lines.append(f"📜 支线『{sqd['name']}』目标达成！回去找 {_g.get('name', '？')} {deliver_hint(sqd['giver'])}吧～")
            else:
                lines.append(f"📜 支线『{sqd['name']}』：{prog[obj['kill']]}/{obj['count']}")
    if side:
        quests["side"] = side
    if changed:
        db.save_quests(group_id, qq_id, quests)
    return lines
