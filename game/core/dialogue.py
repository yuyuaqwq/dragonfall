# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - dialogue（多轮对话引擎）

纯逻辑，不碰 DB/QQ。数据在 data/dialogues.py。

命令层（world.py）负责：
- 读写会话状态（event_state）
- 执行选项动作（涉及 DB 的副作用：给金币/物品/设 flag）

动作 action 是声明式的，命令层用 apply_talk_action 统一落地，
core 只负责判断与筛选，保证引擎可单测、可复用。
"""
from .. import content as C


def get_dialogue(npc_id: str):
    """返回 NPC 的对话树(dict)或 None(未配置多轮对话 → 走旧单轮逻辑)"""
    dlg = C.DIALOGUES.get(npc_id)
    return dlg if dlg else None


def dialogue_node(dlg, node_id: str):
    """取对话树中的节点；不存在回退到 start 节点"""
    nodes = dlg.get("nodes", {})
    if node_id in nodes:
        return nodes[node_id]
    return nodes.get(dlg.get("start"), {})


def _quest_state(quests, qid: str, status) -> bool:
    """主线状态判断：quests dict + qid + 期望状态
    qid 为空字符串 → 按"当前主线"动态判断（对话树通用接取/交付选项用）"""
    if not quests:
        return False
    if status == "done":
        return qid in (quests.get("completed_main") or [])
    target = quests.get("main_quest") if not qid else qid
    if not target:
        return False  # 主线全完成/未设置时，无"当前主线"可言
    if quests.get("main_quest") != target:
        return False
    cur = quests.get("main_status", "pending")
    if status == "active":
        return cur in ("active", "ready")
    if status == "pending":
        return cur == "pending"
    if status == "ready":
        return cur == "ready"
    return False


def check_need(need, ctx: dict) -> bool:
    """判断选项条件是否满足。ctx = {player, quests, flags}

    need 支持的键（全部满足才通过）：
      quest_done / quest_active / quest_pending / quest_ready : 主线状态（qid 为空=当前主线动态判断）
      side_ready  : 该 NPC 名下有待交付的支线（v95.9 对话交付）
      main_done   : 全部主线完成
      level       : 等级下限
      flag        : 该 NPC 对话 flag 已设置
      apprentice      : 已拜师该副业（19 章第八章导师进修）
      not_apprentice  : 未拜师该副业（拜师选项只在未拜师时显示）
    """
    if not need:
        return True
    player = ctx.get("player") or {}
    quests = ctx.get("quests") or {}
    flags = ctx.get("flags") or []
    apprentices = ctx.get("apprentices") or []
    npc_id = ctx.get("npc_id") or ""
    for k, v in need.items():
        if k in ("quest_done", "quest_active", "quest_pending", "quest_ready"):
            if not _quest_state(quests, v, k.replace("quest_", "")):
                return False
        elif k == "side_ready" and v:
            # v95.9：该 NPC 名下有待交付支线（击杀/探索型 ready，收集型材料齐）
            side = quests.get("side") or {}
            if not side:
                return False
            ok = False
            for sid, sq in side.items():
                sqd = next((q for q in (ctx.get("side_quests") or []) if q["id"] == sid), None)
                if not sqd or sqd.get("giver") != npc_id:
                    continue
                if sq.get("status") == "done":  # v95.12：已交付支线不重复提示
                    continue
                obj = sqd.get("objective", {})
                if obj.get("collect"):
                    have = ctx.get("item_counts") or {}
                    if have.get(obj["collect"], 0) >= obj.get("count", 1):
                        ok = True
                        break
                elif sq.get("status") == "ready":
                    ok = True
                    break
            if not ok:
                return False
        elif k == "main_done" and v:
            if quests.get("main_quest") or not (quests.get("completed_main") or []):
                return False
        elif k == "level":
            if int(player.get("level", 0) or 0) < int(v):
                return False
        elif k == "flag":
            if v not in flags:
                return False
        elif k == "quest_any_active":
            # v95.4：当前存在任意进行中主线（对话树指引用）
            if not quests.get("main_quest"):
                return False
        elif k == "apprentice":
            if v not in apprentices:
                return False
        elif k == "not_apprentice":
            if v in apprentices:
                return False
        elif k == "is_novice":
            # v95.23：仅见习冒险者可见（行会就职选项）
            if player.get("class_name") != "cls_novice":
                return False
        elif k == "not_novice":
            # v95.23：已就职（非见习）才可见
            if player.get("class_name") == "cls_novice":
                return False
        elif k == "class_any":
            # v95.23：玩家职业在列表中才可见（导师对话按职业过滤）
            if player.get("class_name") not in v:
                return False
        elif k == "class_tier":
            # v95.23：转职阶数匹配
            if player.get("class_tier", 0) != int(v):
                return False
        elif k == "evolve_ready":
            # v95.23：到达转职等级门槛（{tier: 目标阶, level: 需要等级}）
            if player.get("class_tier", 0) != int(v.get("tier", 0)):
                return False
            if int(player.get("level", 0) or 0) < int(v.get("level", 0)):
                return False
    return True


def visible_options(dlg, node, ctx: dict) -> list:
    """过滤出当前可见的选项(need 不满足的隐藏)"""
    return [opt for opt in node.get("options", []) if check_need(opt.get("need"), ctx)]


def is_end(node_id: str) -> bool:
    """__end__ 是结束对话的哨兵节点"""
    return node_id == "__end__"
