# -*- coding: utf-8 -*-
"""battle2 挂敌身条装配层 battle2_bar_procs（v181 破绽接线）。

背景：`core/battle_bars.py` 的通用挂敌身条（enemy_bar）容器在 v181.N10 重构后
失去消费方——旧 `battle.py` 的 `_skill_hit_settle` / `_turn_start` 两个消费端随文件
删除，`bar_gain` 全库零调用方，破绽条打不出去（容器/配置/条件全活，只断在消费链）。
本模块把消费链接回 battle2 的事件总线（`effect_triggers.fire`）。

两个通用动词（引擎零知识：动作名是动词，bar key / 技能字段名全由声明参数给出）：
- `bar_gain`  skill_hit 命中后按技能数据字段注入积蓄（`params["field"]`，如
              `shaken_gain`）；满阈值 → `bar_trigger` → 落地 `trigger_effect`
- `bar_tick`  宿主自身 turn_start：免疫期递减 + 自然衰减 + 触发检查；
              首次注入时自安装到宿主 `triggers["turn_start"]`（只有真正挂过条的
              单位才跑，零噪音）

数据来源：
- 注入字段映射 = `data/battle2_rules.BAR_INJECT_FIELDS`（技能字段 → bar key；`per_hit`
  = 字段值是「每段」量，按技能 hits 合并注入，v153 §六「多段 +N/段」）
- 条数值/阈值/衰减 = `data/battle_config.ENEMY_BAR_CFG[key]`
- 条容器 = `core/battle_bars`（val/threshold/trigger_count/immune_turns）

控制落地：`trigger_effect == "skip_turn"` → 宿主 `effects` 挂 `mode=skip`
（battle2 统一控制消费点 `Battle.act` 消费，消费即清）——`expire=None` 表示
「下一动生效」而非墙钟刻数，慢速单位也不会白漏（对齐旧引擎 skip_turn 语义）。
"""
from __future__ import annotations

from ..battle2.effects import register_action


def _host_of(caster, target, params) -> dict | None:
    """条宿主：命中目标优先（skill_hit）；无 target 取声明者（turn_start 自 tick）。

    turn_start 事件的 ctx 无 target，fire 会把声明者注入 params["_owner"]。
    """
    if isinstance(target, dict):
        return target
    own = params.get("_owner")
    if isinstance(own, dict):
        return own
    return caster if isinstance(caster, dict) else None


def _ensure_tick(host: dict, key: str) -> None:
    """自安装 turn_start tick 触发器（首次挂条时；重复调用幂等）。"""
    lst = host.setdefault("triggers", {}).setdefault("turn_start", [])
    for e in lst:
        if isinstance(e, dict) and e.get("action") == "bar_tick" and e.get("key") == key:
            return
    lst.append({"action": "bar_tick", "key": key})


def _settle(battle, host: dict, key: str, logs: list) -> bool:
    """阈值检查 → 触发 → 落地 trigger_effect。返回是否触发。"""
    from ..core.battle_bars import bar_def, bar_should_trigger, bar_trigger
    if not host or not key or not bar_should_trigger(host, key):
        return False
    if not bar_trigger(host, key, logs):
        return False
    bd = bar_def(key) or {}
    if (bd.get("trigger_effect") or "") == "skip_turn":
        # 控制跳过：effects 容器 mode=skip（battle2 统一控制消费点消费后自清）；
        # expire=None = 无墙钟到期 → 由「下一动」消费
        host.setdefault("effects", {})[f"bar_skip:{key}"] = {
            "mode": "skip", "expire": None}
        logs.append(f"💢 【{host.get('name', '目标')}】被破绽震慑，无法行动！")
    return True


@register_action("bar_gain")
def bar_gain_act(battle, caster, target, params, logs):
    """命中注入积蓄。

    amount 显式给则用；否则读事件技能字段 `params["field"]`（如 shaken_gain）——
    无字段/非正数 = 无此行为（静默跳过）。
    """
    key = params.get("key")
    if not key:
        return
    host = _host_of(caster, target, params)
    if not host:
        return
    amount = params.get("amount")
    if amount is None:
        field = params.get("field")
        if not field:
            return
        info = (getattr(battle, "_fire_ctx", None) or {}).get("info") or {}
        amount = info.get(field)
        # per_hit：字段值 = 每段量（v153 §六「多段 +3~+5/段」）→ 按本次施放段数合并
        # （skill_hit 每次施放只 fire 一次，段循环在 fire 之前——等价旧引擎逐段 settle）
        if params.get("per_hit"):
            try:
                amount = int(amount or 0) * int(info.get("hits") or info.get("multi") or 1)
            except Exception:
                pass
    try:
        amount = int(amount or 0)
    except Exception:
        return
    if amount <= 0:
        return
    from ..core.battle_bars import bar_gain
    bar_gain(host, key, amount, logs)
    _ensure_tick(host, key)
    _settle(battle, host, key, logs)


@register_action("bar_tick")
def bar_tick_act(battle, caster, target, params, logs):
    """宿主自身回合开始：免疫期递减 + 自然衰减 + 触发检查。"""
    key = params.get("key")
    if not key:
        return
    host = _host_of(caster, target, params)
    if not host:
        return
    from ..core.battle_bars import bar_tick
    if bar_tick(host, key, logs):
        _settle(battle, host, key, logs)


def apply_bar_procs(actor: dict) -> None:
    """装配：扫 actor 已学技能 → 命中 BAR_INJECT_FIELDS 字段则挂 skill_hit 注入。

    学什么挂什么，零噪音（未学推条技能的单位不挂，不产生空转触发器）。

    ⚠️ 顺序契约：注入条目 **insert(0)** 排 skill_hit 首位——被动族同一事件的后置段
    （如破绽·极 passive_bar_extend 延长免疫窗口）依赖「本次命中先推条并触发」，
    排在注入之后才能读到触发后的免疫窗口（旧 battle.py `_skill_hit_settle` 同序）。
    """
    cn = actor.get("class_name") or ""
    names = actor.get("learned_skills") or []
    if not cn or not names:
        return
    try:
        from ..data.battle2_rules import BAR_INJECT_FIELDS
    except Exception:
        return
    from .. import engine as E
    trig = actor.setdefault("triggers", {})
    for field, spec in (BAR_INJECT_FIELDS or {}).items():
        key = (spec or {}).get("key") if isinstance(spec, dict) else ""
        if not key:
            continue
        per_hit = bool((spec or {}).get("per_hit")) if isinstance(spec, dict) else False
        found = False
        for s in names:
            try:
                info = E.skill_info(cn, s)
            except Exception:
                info = None
            if info and info.get(field):
                found = True
                break
        if not found:
            continue
        lst = trig.setdefault("skill_hit", [])
        if not any(isinstance(e, dict) and e.get("action") == "bar_gain"
                   and e.get("key") == key for e in lst):
            entry = {"action": "bar_gain", "key": key, "field": field}
            if per_hit:
                entry["per_hit"] = True
            lst.insert(0, entry)
