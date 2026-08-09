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
    """主线状态判断：quests dict + qid + 期望状态"""
    if not quests:
        return False
    if status == "done":
        return qid in (quests.get("completed_main") or [])
    if quests.get("main_quest") != qid:
        return False
    cur = quests.get("main_status", "pending")
    if status == "active":
        return cur in ("active", "ready")
    if status == "pending":
        return cur == "pending"
    return False


def check_need(need, ctx: dict) -> bool:
    """判断选项条件是否满足。ctx = {player, quests, flags}

    need 支持的键（全部满足才通过）：
      quest_done / quest_active / quest_pending : 主线状态
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
    for k, v in need.items():
        if k in ("quest_done", "quest_active", "quest_pending"):
            if not _quest_state(quests, v, k.replace("quest_", "")):
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
        elif k == "apprentice":
            if v not in apprentices:
                return False
        elif k == "not_apprentice":
            if v in apprentices:
                return False
    return True


def visible_options(dlg, node, ctx: dict) -> list:
    """过滤出当前可见的选项(need 不满足的隐藏)"""
    return [opt for opt in node.get("options", []) if check_need(opt.get("need"), ctx)]


def is_end(node_id: str) -> bool:
    """__end__ 是结束对话的哨兵节点"""
    return node_id == "__end__"
