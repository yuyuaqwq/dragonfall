# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年命令层 —— 按领域拆分的 Command Mixin

Main(star.Star) 继承全部 Mixin，实现命令路由。
"""
from .base import CommandBase  # noqa: F401
from .player import PlayerCmds  # noqa: F401
from .world import WorldCmds  # noqa: F401
from .combat import CombatCmds  # noqa: F401
from .economy import EconomyCmds  # noqa: F401
from .social import SocialCmds  # noqa: F401
from .misc import MiscCmds  # noqa: F401
from .collection import CollectionCmds  # noqa: F401  (v140 波2 『收藏册』命令)
from .weekly import WeeklyCmds  # noqa: F401  (v169.2 『周常/周常列表』命令)
from .tower import TowerCmds  # noqa: F401  (v169.2 『爬塔』命令)
from .event_menu import EventMenuCmds  # noqa: F401  (v140 波3.7 『今日事件/事件』命令)
from .job_guide import JobGuideCmds  # noqa: F401  (v130.2g 『职业』速查指令)
from .instance import InstanceCmds  # noqa: F401
from .gm import GmCmds  # noqa: F401
from .exploration import ExplorationCmds  # noqa: F401

__all__ = [
    "CommandBase", "PlayerCmds", "WorldCmds", "CombatCmds",
    "EconomyCmds", "SocialCmds", "MiscCmds", "JobGuideCmds", "InstanceCmds", "GmCmds",
    "ExplorationCmds", "CollectionCmds", "WeeklyCmds", "TowerCmds", "EventMenuCmds",
]
