# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - quests_flow（★ B9 L5 起 = 薄壳）

逻辑真源已进内容包：`content/quests_flow.py`（逐字端口，真源 = 本文件旧版 831 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()` = 本进程唯一包加载口，幂等；失败大声抛）
  2. 注入宿主替身：
       `db`                     —— 存储层（真源 `from .. import db`）
       `c`                      —— 内容聚合层 `game.content`（**只喂未进包的符号**：
                                   TITLES / FACTIONS / AREA_FACTION / resolve("materials")）
       `level_up`               —— `content_rules.gameplay.check_player_level_up`（升级结算）
       `stat_bonus_fn`          —— `core.stat_bonus.stat_bonus`（外部面板增幅聚合）
       `grant_reward_fn`        —— `reward.grant_reward`（奖励发放）
       `quests_svc`             —— `services.quests`（每日委托：bump_daily_progress /
                                   settle_daily_quest / DAILY_META_KEYS）
  3. **同名单 re-export** —— 保持模块路径与符号名不变，命令层 / 战斗层 / 订阅方 / 测试零改动：
       命令层       `game/commands/world.py`（15 处 `qf.*`）+ `commands/combat.py` 击杀推进
       订阅方       `game/services/player_event_subscribers.py:25`（`quest_kill_progress`）
       聚合导出     `game/services/__init__.py:19`（17 个名字，逐字沿用）
       测试         `tests/test_commands_world.py:16` / `tests/test_v104_quests.py:21`

宿主注入的必要性：包内模块**不 import 宿主**（方向只有 内容 → 引擎）；它按 `bind_host(...)`
或「已加载的宿主模块」解析这些口，见包内模块 docstring 的替身接口表与逐符号归属表。
"""

from __future__ import annotations

import importlib

from .. import bootstrap as _bootstrap
from .. import content as _host_content
from .. import db as _db
from ..content_rules.gameplay import check_player_level_up as _level_up
from ..core.stat_bonus import stat_bonus as _stat_bonus
from ..reward import grant_reward as _grant_reward
from . import quests as _quests_svc

_bootstrap.package_apply()                          # 包加载口（失败抛，不静默）
_pkg = importlib.import_module("content.quests_flow")

_pkg.bind_host(db=_db, c=_host_content, level_up=_level_up,
               stat_bonus_fn=_stat_bonus, grant_reward_fn=_grant_reward,
               quests_svc=_quests_svc)              # 宿主替身注入（幂等）

# ---- 同名单 re-export（逐字沿用真源符号名）----
obj_text = _pkg.obj_text
sq_unlocked = _pkg.sq_unlocked
sq_stats_met = _pkg.sq_stats_met
available_quest_list = _pkg.available_quest_list
update_explore_quests = _pkg.update_explore_quests
take_main_quest = _pkg.take_main_quest
quest_reputation = _pkg.quest_reputation
deliver_hint = _pkg.deliver_hint
side_available_list = _pkg.side_available_list
offer_side_quest = _pkg.offer_side_quest
offer_side_quests = _pkg.offer_side_quests
grant_quest_rewards = _pkg.grant_quest_rewards
complete_side_quest = _pkg.complete_side_quest
talk_quest_progress = _pkg.talk_quest_progress
update_use_quests = _pkg.update_use_quests
branch_wait_sid = _pkg.branch_wait_sid
quest_kill_progress = _pkg.quest_kill_progress

# 顺序声明（真源 `SIDE_QUESTS` 插入序）—— 供导出/审计脚本对账用，透传不另存一份
SIDE_QUEST_ORDER = _pkg.SIDE_QUEST_ORDER
