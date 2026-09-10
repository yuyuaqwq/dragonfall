# -*- coding: utf-8 -*-
"""battle2 挂敌身条装配层 battle2_bar_procs（v181 破绽接线 + 时间化）。

背景：`core/battle_bars.py` 的通用挂敌身条（enemy_bar）容器在 v181.N10 重构后
失去消费方——旧 `battle.py` 的 `_skill_hit_settle` / `_turn_start` 两个消费端随文件
删除，`bar_gain` 全库零调用方，破绽条打不出去（容器/配置/条件全活，只断在消费链）。
本模块把消费链接回 battle2 的事件总线（`effect_triggers.fire`）。

三个通用动词（引擎零知识：动作名是动词，bar key / 技能字段名全由声明参数给出）：
- `bar_gain`        skill_hit 命中后按技能数据字段注入积蓄（`params["field"]`，如
                    `shaken_gain`）；满阈值 → `bar_trigger` → 落地 `trigger_effect`
- `bar_time_settle` time_advance 时钟推进：把宿主身上所有条按 dt 结息（免疫到期 +
                    连续衰减）→ 触发检查。读点永远拿到当刻值
                    （宿主首次挂条时自安装订阅——只有真挂过条的单位才跑，零噪音）

数据来源：
- 注入字段映射 = `data/battle2_rules.BAR_INJECT_FIELDS`（技能字段 → bar key；`per_hit`
  = 字段值是「每段」量，按技能 hits 合并注入，v153 §六「多段 +N/段」）
- 条数值/阈值/衰减/免疫 = `data/battle_config.ENEMY_BAR_CFG[key]`
- 条容器 = `actor.effects[BAR_STATE_PREFIX + key]`（val/threshold/trigger_count/
  immune_until/_at；V 系列统一单容器，见 core/battle_bars）

控制落地：`trigger_effect == "skip_turn"` → 宿主 `effects` 挂 `mode=skip`
（battle2 统一控制消费点 `Battle.act` 消费，消费即清）——`expire=None` 表示
「下一动生效」而非墙钟刻数，慢速单位也不会白漏（对齐旧引擎 skip_turn 语义）。
"""
from __future__ import annotations

from ..battle2.effects import register_action


def _now_of(battle) -> float:
    return float(getattr(battle, "_now", 0.0) or 0.0)


def _host_of(caster, target, params) -> dict | None:
    """条宿主：命中目标优先（skill_hit）；无 target 取声明者（时钟事件自结算）。"""
    if isinstance(target, dict):
        return target
    own = params.get("_owner")
    if isinstance(own, dict):
        return own
    return caster if isinstance(caster, dict) else None


def _bar_keys_of(host: dict) -> list:
    """宿主身上所有条键（effects 里带前缀的条目 → 去前缀 bar key）。"""
    from ..core.battle_bars import _state_prefix
    pfx = _state_prefix()
    out = []
    for k, v in (host.get("effects") or {}).items():
        if isinstance(k, str) and k.startswith(pfx) and isinstance(v, dict):
            out.append(k[len(pfx):])
    return out


def _ensure_tick(host: dict) -> None:
    """自安装 time_advance 结算订阅（首次挂条时；重复调用幂等）。"""
    lst = host.setdefault("triggers", {}).setdefault("time_advance", [])
    for e in lst:
        if isinstance(e, dict) and e.get("action") == "bar_time_settle":
            return
    lst.append({"action": "bar_time_settle"})


def _settle(battle, host: dict, key: str, logs: list) -> bool:
    """阈值检查 → 触发 → 落地 trigger_effect。返回是否触发。"""
    from ..core.battle_bars import bar_def, bar_should_trigger, bar_trigger
    now = _now_of(battle)
    if not host or not key or not bar_should_trigger(host, key, now):
        return False
    if not bar_trigger(host, key, logs, now):
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
    bar_gain(host, key, amount, logs, now=_now_of(battle))
    _ensure_tick(host)
    _settle(battle, host, key, logs)


@register_action("bar_time_settle")
def bar_time_settle_act(battle, caster, target, params, logs):
    """time_advance：宿主自身所有条结算到当刻（免疫到期 + 连续衰减）+ 触发检查。"""
    host = params.get("_owner") or _host_of(caster, target, params)
    if not isinstance(host, dict):
        return
    from ..core.battle_bars import bar_settle
    now = _now_of(battle)
    for key in _bar_keys_of(host):
        bar_settle(host, key, now, logs)
        _settle(battle, host, key, logs)


def apply_bar_procs(actor: dict) -> None:
    """装配：扫 actor 已学技能 → 命中 BAR_INJECT_FIELDS 字段则挂 skill_hit 注入。

    学什么挂什么，零噪音（未学推条技能的单位不挂，不产生空转触发器）。

    ⚠️ 顺序契约：注入条目 **insert(0)** 排 skill_hit 首位——被动族同一事件的后置段
    （如破绽·极 passive_bar_extend 延长免疫窗口）依赖「本次命中先推条并触发」，
    排在注入之后才能读到触发后的免疫状态（旧 battle.py `_skill_hit_settle` 同序）。
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
