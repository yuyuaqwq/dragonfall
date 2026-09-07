# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层（game/services，v181 P4 命令层抽 services）

与 game/core/ 对等（ARCHITECTURE.md v47 蓝图预留的"服务层"位置）：
- 每域一文件（party/guild/quests/shop/crafting/…）、纯函数模块、零类零装饰器
- 依赖方向：可 import data/core/store/db/engine/battle/reward 及同级 services；
  禁止 import commands/*（防环 + 命令依赖方向约束）
- db 等依赖一律函数体内惰性 import（防 data/_assembly 加载期循环）

P4-6（wt_p4s11）：party.py（组队域）+ guild.py（公会域）——social.py
party 区（L435-589）+ guild 区（L590-1000）编排逻辑服务化，命令层只留解析+文案壳。
（P4-1 quests.py 在 wt_p41 分支，合并后由主 agent 统一聚合。）
"""
from .party import (  # noqa: F401
    resolve_party_target, party_in_battle, target_in_battle,
    party_view_lines, party_join, party_leave_check,
    party_leave_inst_member, party_leave_execute,
)
from .guild import (  # noqa: F401
    guild_create_check, guild_create, guild_join,
    guild_leave_check, guild_leave, guild_disband,
    guild_sign, guild_task_view, guild_donate,
    guild_donate_inventory, guild_donate_total,
    guild_rank_lines, guild_appoint_check_role,
    guild_appoint_level_ok, guild_find_member,
    guild_appoint, guild_demote, guild_kill_progress,
)
