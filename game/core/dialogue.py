# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - dialogue（多轮对话引擎）

纯逻辑，不碰 DB/QQ。数据在 data/dialogues.py。

命令层（world.py）负责：
- 读写会话状态（event_state）
- 执行选项动作（涉及 DB 的副作用：给金币/物品/设 flag）

动作 action 是声明式的，命令层用 apply_talk_action 统一落地，
core 只负责判断与筛选，保证引擎可单测、可复用。
"""
import re
from .. import content as C
from ..log_setup import LOG


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
    quest_any_active/apprentice/not_apprentice/is_novice/not_novice/class_any/
    evolve_ready）见该文件；
    v113 增补：race_is/hidden_unlocked/hidden_current/not_hidden_current/side_available。
    加新条件类型 = register 一个函数（~5 行），本文件零改动。
    """
    if not need:
        return True
    from .dialogue_conds import CONDITIONS
    for k, v in need.items():
        fn = CONDITIONS.get(k)
        if fn is None:
            # v104 M21 P1：未注册条件键 → 生产放行但告警（防数据笔误静默变永远可见）；
            # 测试环境（GWEN_GAME_DB 指向 test 库）直接 raise，让单测抓出笔误
            import os
            _db = os.environ.get("GWEN_GAME_DB", "")
            _msg = (f"[dragonfall] 对话条件未注册键 need[{k!r}]={v!r}："
                    f"数据笔误？已按'永远可见'放行，请检查 dialogues.py")
            # v110.5 X3：显式判定测试环境——既看私有库名含 "test"（旧约定兼容），
            # 也认 GWEN_TEST_MODE=1（本轮私有库名不含 "test" 时测试行为漂移的根因）。
            _test = ("test" in os.path.basename(_db).lower()
                     or os.environ.get("GWEN_TEST_MODE") == "1")
            if _test:
                raise ValueError(_msg)
            LOG.warning(_msg)
            continue  # 未知条件放行（向后兼容，旧数据不崩）
        if not fn(ctx, v):
            return False
    return True


def visible_options(dlg, node, ctx: dict) -> list:
    """过滤出当前可见的选项(need 不满足的隐藏)

    v127.6 side_menu 动态菜单：选项带非空 'side_menu' 键时，调用命令层注入的
    ctx['side_menu_expand'](opt) 回调，将该选项展开成一组动态子选项
    （每个子选项自带 text/next/action，如『接『支线名』(目标)』）；
    未注入回调、need 不满足、或展开为空 → 该选项整体不出现
    （无活儿可接时不显示菜单）。core 层保持纯逻辑、零 DB，回调由命令层注入。
    """
    out = []
    for opt in node.get("options", []):
        if opt.get("side_menu") is not None:
            if not check_need(opt.get("need"), ctx):
                continue
            expand = ctx.get("side_menu_expand")
            subs = expand(opt) if expand else []
            if subs:
                out.extend(subs)
            continue  # 未注入回调/展开为空 → 跳过该选项
        if check_need(opt.get("need"), ctx):
            out.append(opt)
    return out


_STORY_PREFIX = re.compile(r"^[^：:]{1,20}[：:]\s*")


def _story_to_line(raw: str) -> str:
    """任务 story/ending 文本 → NPC 台词（v101.23d A 级：text_from 自动生成）

    格式多为『NPC名：台词』或『NPC名：『台词』』（少数叙事型『老约翰交给玩家一封信：『…』』）。
    规则：剥 NPC 名前缀 → 取 『』/“” 引号内 → 都没有就原样降级（叙事型也能念）。
    """
    if not raw:
        return ""
    body = _STORY_PREFIX.sub("", raw.strip())
    m = re.match(r"^[“『](.+)[”』]$", body.strip())
    return m.group(1) if m else body


def node_text(node, ctx: dict) -> str:
    """节点台词：texts 条件变体优先（need 满足的第一个），否则默认 text；
    v101.23d：text_from 支持——节点写 {"text_from": "story"} 时，无变体匹配则
    从『当前主线任务』的 story 字段自动生成接取台词（giver 校验，防串台）。
    多任务 NPC 加新任务 = 纯数据，quest_talk 台词自动跟任务走，不用手写变体。"""
    for variant in node.get("texts") or []:
        if check_need(variant.get("need"), ctx):
            return variant["text"]
    src = node.get("text_from")
    if src in ("story",):
        quests = ctx.get("quests") or {}
        mid = quests.get("main_quest")
        if mid:
            from ..data import MAIN_QUESTS
            mq = next((q for q in MAIN_QUESTS if q["id"] == mid), None)
            if mq and (not mq.get("giver") or mq.get("giver") == ctx.get("npc_id")):
                auto = _story_to_line(mq.get("story", ""))
                if auto:
                    return auto
    return node.get("text", "……")


def is_end(node_id: str) -> bool:
    """__end__ 是结束对话的哨兵节点"""
    return node_id == "__end__"
