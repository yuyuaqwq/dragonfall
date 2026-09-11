# -*- coding: utf-8 -*-
"""v179 通用 tick 效果框架（tick_effects.py）

把战斗引擎里所有"周期/持续"效果（回血/充能/毒/宠物/召唤物/食物HOT/药水/词条
turn_start/武器特效/boss 定时/状态机维护）统一成**效果条目**模型：

    {uid, kind, actor, interval, next_at, expire_at, data, source}

- battle 维护一个 tick_effects 条目池（list）
- 一个通用 tick 调度器（battle._process_tick_effects）到点弹到期条目
- 按 kind 查 TICK_HANDLERS 注册表分发到具体处理函数
- 加新周期效果 = 注册 handler + add_tick_effect，**零引擎改动**

数据驱动铁律（鱼鱼 2026-09-06 拍板）：
- 不再 per-效果造事件类型 / 改 _process_until 分支
- 周期效果统一走本框架；一次性行动事件（enemy_act/cast_done）保留事件队列原样

效果源注册（仿 affix/food/weapon 现有 register 模式）：
    @register_handler("regen_heal")
    def handle_regen_heal(battle, eff, logs): ...
"""
import time  # noqa: F401  兼容（星尘套读真实时钟由 handler 自行 import）

# ============================================================
# 注册表
# ============================================================
TICK_HANDLERS: dict = {}


def register_handler(kind: str):
    """装饰器：注册一个 tick 效果处理函数。签名 (battle, eff, logs) -> list/logs。"""
    def deco(fn):
        TICK_HANDLERS[kind] = fn
        return fn
    return deco


def make_effect(kind: str, actor: dict, interval: float, now: float,
                data: dict | None = None, expire_at: float | None = None,
                uid: str | None = None, source: str = "") -> dict:
    """构造一个 tick 效果条目。

    kind      效果类型（查 TICK_HANDLERS）
    actor     作用对象 dict（玩家 or 怪——一视同仁，actor-agnostic）
    interval  周期（秒）；<=0 = 一次性（触发即移除）
    now       当前战斗时刻（用于算 next_at）
    data      效果参数（数值/来源等，数据驱动）
    expire_at 到期绝对时刻（None=永久直到显式移除）
    source    来源（set_chen_guang/food/potion/skill_pet…，用于排查）
    """
    return {
        "uid": uid or f"{kind}_{int(time.time() * 1000)}_{id(actor) % 10000}",
        "kind": kind,
        "actor": actor,
        "interval": float(interval),
        "next_at": float(now) + max(float(interval), 0.001) if interval > 0 else float(now),
        "expire_at": expire_at,
        "data": data or {},
        "source": source,
    }
