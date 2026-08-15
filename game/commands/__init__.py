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
from .instance import InstanceCmds  # noqa: F401
from .gm import GmCmds  # noqa: F401
from .exploration import ExplorationCmds  # noqa: F401

__all__ = [
    "CommandBase", "PlayerCmds", "WorldCmds", "CombatCmds",
    "EconomyCmds", "SocialCmds", "MiscCmds", "InstanceCmds", "GmCmds",
    "ExplorationCmds",
]
