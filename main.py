# -*- coding: utf-8 -*-
"""《剑与魔法》AstrBot 插件主入口 —— 薄装配层（重构后）

命令处理器已按领域拆至 game/commands/（Mixin 模式）：
  PlayerCmds / WorldCmds / CombatCmds / EconomyCmds / SocialCmds / MiscCmds
本文件只保留：插件生命周期 + 后台任务 + Mixin 装配。
"""
import threading
import logging

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.message_event_result import MessageChain

from .game import db
from .game.commands import (
    PlayerCmds, WorldCmds, CombatCmds, EconomyCmds, SocialCmds, MiscCmds,
    InstanceCmds,
)


def _fix_handler_module_paths():
    """修复 Mixin 重构后 handler 模块路径问题。

    AstrBot 通过 handler.handler_module_path 在 star_map 中查找插件实例，
    而 Mixin 拆分后 handler 注册为 game.commands.* 子模块路径，与
    Main 类所在的 main 模块不匹配，导致全部指令 handler 被过滤、
    消息全部落入 LLM 回复。

    这里在插件加载完成后，把本插件所有 handler 的模块路径统一改写到
    main 模块（__name__），保证 star_map 能正确关联到 Main 实例。
    """
    try:
        from astrbot.core.star.star_handler import star_handlers_registry

        pkg = __name__.rsplit(".", 1)[0]  # plugins.dragonfall
        for h in star_handlers_registry._handlers:
            if h.handler_module_path and h.handler_module_path.startswith(pkg + "."):
                h.handler_module_path = __name__
    except Exception:
        logging.getLogger(__name__).exception("fix handler module paths failed")


_fix_handler_module_paths()

class Main(
    star.Star,
    PlayerCmds,
    WorldCmds,
    CombatCmds,
    EconomyCmds,
    SocialCmds,
    MiscCmds,
    InstanceCmds,
):
    """《剑与魔法》西幻文字RPG——在QQ群里冒险吧！"""

    def __init__(self, context: star.Context) -> None:
        self.context = context
        db.init_db()
        # v36: 广播任务已停用（意见改为 cron 汇总报告给鱼鱼，不回复玩家）
