# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 服务层 - player_event_bus（L3 玩家级事件总线，v181 L3-P1）

战斗之外、玩家账号级的领域事件同步总线（DDD 领域事件语义，非 QFramework EventSystem）：
一次战斗胜利/失败/击杀是「已经发生的事实」，发布时订阅方按注册顺序反应并回填结算文案。
战斗引擎（saintess_engine）零游戏知识、不 import 本文件；fire 入口收拢在命令层/结算层编排点。

设计文档：docs/DESIGN_v181_L3_player_event_bus.md（权威思想）
字段级任务书：docs/REFACTOR_v181_L3_P0_task.md（ctx schema/订阅注册表/行序对照，P0 侦察修订）

三层事件全景：
- L1 战斗内效果总线 saintess_engine/effect_triggers.py fire() 23 时机（actor 级，N8 已落地）
- L2 战斗级观察者 battle.on_event 注入钩子（N5b4-5E/5c 已落地）
- L3 本文件：玩家级（任务/成就/公会/野王/塔卫），一次战斗只几类事件

总线规则（北极星对齐，全部为显式决策）：
- EVENTS 起步全集固定元组；register 未知事件 raise ValueError（防拼写静默失效）；
  fire 未知事件 log warning 后不 raise（返回当前行收集器；ctx 未预置 lines 时即 []）。
- 订阅方按注册顺序执行；段间空行规则由 blank_line 参数统一实现（对齐原手写
  `if lines: lines.append("")` 语义）：blank=True 且上一行非空才补一个 ""。
- 异常订阅不阻断（log + continue，对齐各命令层 try/except 宽容铁律）；
  返回 None 与 [] 等价（无行=跳过）。
- ctx 是唯一上下文（见 P0 任务书 §4）：订阅方可原地改 dict（ctx["player"] 重绑等），
  总线不解释 ctx["side_effects"]（非文案副作用，fire 返回后由命令层消费）。
- 显式 import 触发注册（game/services/player_event_subscribers.py），不做 import 魔法。

【骨架归属（2026-09-11，M3）】总线的**机制**（注册表 / 注册序执行 / 段落空行 /
未知事件策略 / 异常容忍）来自框架 `saintess_engine.events.EventBus`；本文件只留
**本游戏的内容**：事件集 `EVENTS`、对外 API 名、日志器。
"""

from __future__ import annotations

import logging

from saintess_engine.events import EventBus

_log = logging.getLogger("astrbot")

# 起步全集（**本游戏的事件名**；框架不预设任何事件名）
# 扩展靠 data/声明不靠加 if——但事件本体先枚举，防止拼写漂移
EVENTS = ("battle_victory", "battle_defeat", "monster_killed")

# 总线实例。策略与改造前的手写实现逐条一致（正是框架的默认值）：
#   register 未知事件 → raise；fire 未知事件 → warn 后返回行收集器；订阅方异常 → 跳过
_bus = EventBus(EVENTS, logger=_log)


def register(event: str, subscriber, blank_line: bool = True) -> None:
    """注册订阅方。

    subscriber(ctx: dict) -> list[str] | None：接收 ctx，返回要回填进结算日志的行组
    （不含段落分隔空行——由 blank_line 统一处理）。返回 None/[] = 本段无行。
    同事件重复注册 = 追加（各模块 import 一次天然单次，不查重）。
    """
    _bus.on(event, subscriber, blank_line=blank_line)


def fire(event: str, ctx: dict) -> list:
    """发布事件：按注册顺序执行订阅方，收集回填行（含 blank 空行），返回行列表。

    ctx 至少含 P0 任务书 §4 固定字段（event 自动补，其余由 fire 点构造）；
    ctx.setdefault("lines", []) 作为行收集器（若调用方预置内容则在其后追加）。
    订阅方抛异常：log warning + 跳过该订阅方（不阻断后续，容错铁律）。
    """
    return _bus.fire(event, ctx)


def clear_registry() -> None:
    """清空全部订阅（仅测试用）。生产代码不得调用。"""
    _bus.clear()
