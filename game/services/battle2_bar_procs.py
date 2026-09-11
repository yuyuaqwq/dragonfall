# -*- coding: utf-8 -*-
"""saintess_engine 挂敌身条装配层 battle2_bar_procs（v181 破绽接线 + 时间化）。

背景：`core/battle_bars.py` 的通用挂敌身条（enemy_bar）容器在 v181.N10 重构后
失去消费方——旧 `battle.py` 的 `_skill_hit_settle` / `_turn_start` 两个消费端随文件
删除，`bar_gain` 全库零调用方，破绽条打不出去（容器/配置/条件全活，只断在消费链）。
本模块把消费链接回 saintess_engine 的事件总线（`effect_triggers.fire`）。

通用动词（引擎零知识：动作名是动词，bar key / 技能字段名全由声明参数给出）：
- `bar_gain`          skill_hit 命中后按技能数据字段注入积蓄（`params["field"]`，如
                      `shaken_gain`）；满阈值 → `bar_trigger` → 落地 `trigger_effect`
- `bar_time_settle`   time_advance 时钟推进：把宿主身上所有条按 dt 结息（免疫到期 +
                      连续衰减）→ 触发检查。读点永远拿到当刻值
                      （宿主首次挂条时自安装订阅——只有真挂过条的单位才跑，零噪音）
- `bar_phase_preserve` phase 阶段转换：宿主所有条保留配置比例积蓄（`phase_preserve_pct`，
                      进度遗产不清零）——事件由上层剧本导演广播，比例全在配置里
- `passive_reflect_bar` on_taken 受击反制（反震）：反弹 `reflect_pct` 伤害 + 反推攻击者条
                      （量 = 被动自身推条字段，装配器经 `BAR_INJECT_FIELDS` 解析）

数据来源：
- 注入字段映射 = `data/battle2_rules.BAR_INJECT_FIELDS`（技能字段 → bar key；`per_hit`
  = 字段值是「每段」量，按技能 hits 合并注入，v153 §六「多段 +N/段」）
- 条数值/阈值/衰减/免疫 = `data/battle_config.ENEMY_BAR_CFG[key]`
- 条容器 = `actor.effects[BAR_STATE_PREFIX + key]`（val/threshold/trigger_count/
  immune_until/_at；V 系列统一单容器，见 core/battle_bars）

控制落地：`trigger_effect == "skip_turn"` → 宿主 `effects` 挂 `mode=skip`
（saintess_engine 统一控制消费点 `Battle.act` 消费，消费即清）——`expire=None` 表示
「下一动生效」而非墙钟刻数，慢速单位也不会白漏（对齐旧引擎 skip_turn 语义）。
"""
from __future__ import annotations

from saintess_engine.effects import register_action


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
    from saintess_engine.support.battle_bars import _state_prefix
    pfx = _state_prefix()
    out = []
    for k, v in (host.get("effects") or {}).items():
        if isinstance(k, str) and k.startswith(pfx) and isinstance(v, dict):
            out.append(k[len(pfx):])
    return out


def _ensure_tick(host: dict) -> None:
    """自安装订阅（首次挂条时；重复调用幂等）：

    - `time_advance` → `bar_time_settle`：时钟推进按 dt 结息（谁挂过条谁才订阅，零噪音）
    - `phase`        → `bar_phase_preserve`：阶段转换保留部分积蓄（进度遗产，配置定比例）
    """
    trig = host.setdefault("triggers", {})
    lst = trig.setdefault("time_advance", [])
    if not any(isinstance(e, dict) and e.get("action") == "bar_time_settle" for e in lst):
        lst.append({"action": "bar_time_settle"})
    lph = trig.setdefault("phase", [])
    if not any(isinstance(e, dict) and e.get("action") == "bar_phase_preserve" for e in lph):
        lph.append({"action": "bar_phase_preserve"})


def _settle(battle, host: dict, key: str, logs: list) -> bool:
    """阈值检查 → 触发 → 落地 trigger_effect。返回是否触发。"""
    from saintess_engine.support.battle_bars import bar_def, bar_should_trigger, bar_trigger
    now = _now_of(battle)
    if not host or not key or not bar_should_trigger(host, key, now):
        return False
    if not bar_trigger(host, key, logs, now):
        return False
    bd = bar_def(key) or {}
    if (bd.get("trigger_effect") or "") == "skip_turn":
        # 控制跳过：effects 容器 mode=skip（saintess_engine 统一控制消费点消费后自清）；
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
    from saintess_engine.support.battle_bars import bar_gain
    bar_gain(host, key, amount, logs, now=_now_of(battle))
    _ensure_tick(host)
    _settle(battle, host, key, logs)


@register_action("bar_time_settle")
def bar_time_settle_act(battle, caster, target, params, logs):
    """time_advance：宿主自身所有条结算到当刻（免疫到期 + 连续衰减）+ 触发检查。"""
    host = params.get("_owner") or _host_of(caster, target, params)
    if not isinstance(host, dict):
        return
    from saintess_engine.support.battle_bars import bar_settle
    now = _now_of(battle)
    for key in _bar_keys_of(host):
        bar_settle(host, key, now, logs)
        _settle(battle, host, key, logs)


@register_action("bar_phase_preserve")
def bar_phase_preserve_act(battle, caster, target, params, logs):
    """phase：宿主阶段转换 → 所有条保留配置比例积蓄（进度遗产；阶段不清零）。

    比例 = `ENEMY_BAR_CFG[key].phase_preserve_pct`（缺省 50%）——动作零数值，
    只是「阶段转换」这个通用时机的条侧消费端（事件由上层剧本导演广播）。
    """
    host = params.get("_owner") or _host_of(caster, target, params)
    if not isinstance(host, dict):
        return
    from saintess_engine.support.battle_bars import bar_def, bar_preserve, bar_state
    for key in _bar_keys_of(host):
        before = float((bar_state(host, key) or {}).get("val", 0.0) or 0.0)
        if before <= 0:
            continue
        bar_preserve(host, key)
        after = float((bar_state(host, key) or {}).get("val", 0.0) or 0.0)
        bd = bar_def(key) or {}
        pct = int(round(float(bd.get("phase_preserve_pct", 0.5) or 0.5) * 100))
        logs.append(f"💢【{host.get('name', '目标')}】阶段更迭："
                    f"{bd.get('name', key)}积蓄保留 {pct}%（{int(before)} → {int(after)}）")


@register_action("passive_reflect_bar")
def passive_reflect_bar_act(battle, caster, target, params, logs):
    """on_taken：受击反制（反震）——反弹 `reflect_pct` 伤害 + 反推攻击者条。

    - 反制者 = `params["_owner"]`（被动持有者 = 受击者；on_taken 主体过滤已保证）
    - 攻击者 = `_fire_ctx["source"]`；反弹基数 = `_fire_ctx["dmg"]`；
      无来源（DOT/环境伤）不反制（对齐 we_reflect 口径）
    - 反推条 = `params["key"]/["gain"]`（装配器按被动 `bar_field` 解析的技能字段量）
      → bar_gain + 触发检查（与命中注入同一条消费链）
    """
    from saintess_engine.actors import actor_alive
    from saintess_engine.support.battle_bars import bar_gain
    deflector = params.get("_owner") or target
    if not isinstance(deflector, dict) or not actor_alive(deflector):
        return
    ctx = getattr(battle, "_fire_ctx", None) or {}
    attacker = ctx.get("source")
    if not isinstance(attacker, dict) or not actor_alive(attacker):
        return
    pct = float(params.get("reflect_pct", 0) or 0)
    if pct > 0:
        rd = max(1, int(int(ctx.get("dmg", 0) or 0) * pct))
        from saintess_engine.landing import deal_damage
        deal_damage(battle, deflector, attacker, rd, logs)
        logs.append(f"🪨 反震：反弹 {rd} 点伤害！")
    key = params.get("key")
    gain = int(params.get("gain", 0) or 0)
    if key and gain > 0:
        now = _now_of(battle)
        bar_gain(attacker, key, gain, logs, now=now)
        _ensure_tick(attacker)
        _settle(battle, attacker, key, logs)


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
    from ..content_rules.skills import skill_info
    trig = actor.setdefault("triggers", {})
    for field, spec in (BAR_INJECT_FIELDS or {}).items():
        key = (spec or {}).get("key") if isinstance(spec, dict) else ""
        if not key:
            continue
        per_hit = bool((spec or {}).get("per_hit")) if isinstance(spec, dict) else False
        found = False
        for s in names:
            try:
                info = skill_info(cn, s)
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
