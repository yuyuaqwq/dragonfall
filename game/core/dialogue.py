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


def check_need(need, ctx: dict) -> bool:
    """判断选项条件是否满足。ctx = {player, quests, flags}

    v98.3：条件判定全数据化 → core/dialogue_conds.py CONDITIONS 注册表。
    need 支持的键（quest_done/quest_active/quest_pending/quest_ready/side_ready/
    main_done/level/flag/quest_any_active/apprentice/not_apprentice/is_novice/
    not_novice/class_any/class_tier/evolve_ready）见该文件；
    加新条件类型 = register 一个函数（~5 行），本文件零改动。
    """
    if not need:
        return True
    from .dialogue_conds import CONDITIONS
    for k, v in need.items():
        fn = CONDITIONS.get(k)
        if fn is None:
            continue  # 未知条件放行（向后兼容，旧数据不崩）
        if not fn(ctx, v):
            return False
    return True


def visible_options(dlg, node, ctx: dict) -> list:
    """过滤出当前可见的选项(need 不满足的隐藏)"""
    return [opt for opt in node.get("options", []) if check_need(opt.get("need"), ctx)]


def node_text(node, ctx: dict) -> str:
    """节点台词：支持条件变体 texts=[{need, text}, ...]，取第一个满足 need 的；
    否则用默认 text。v101.23：让 NPC 台词随主线进度切换（镇长做完史莱姆不再念史莱姆）。"""
    for variant in node.get("texts") or []:
        if check_need(variant.get("need"), ctx):
            return variant["text"]
    return node.get("text", "……")


def is_end(node_id: str) -> bool:
    """__end__ 是结束对话的哨兵节点"""
    return node_id == "__end__"
