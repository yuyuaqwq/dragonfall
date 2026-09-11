# -*- coding: utf-8 -*-
"""元素机制装配层 battle_element_procs（2026-09-11）。

## 背景：元素机制有两根轴，此前**都没接线**

权威口径 = `docs/CLASS_MECHANICS_v153.md`：
- **§2 印记反应轴**（:385-388）：火印+冰印=蒸发 / 雷印+火印=超载 / 冰印+雷印=冻结 /
  雷印满 3 层=感电。配置表 `battle_config.ELEMENT_REACTIONS` **早已存在**，
  但 `content_rules.gameplay.element_reaction()` **全仓零调用方**（只在退役旧引擎测试里出现过）
  → 反应从未发生。
- **§9.1 克制轴**（:1170-1178）：三角循环 火→冰→雷→火，克制命中伤害 ×1.25
  （火克冰解冻 / 冰克雷打断 / 雷克火对灼烧 +25%）。**配置表根本不存在** → 也没接线。

§1178 明示两轴关系：「**两套独立加成，可叠加但都进"条件倍率"预算**——
即 `裸eps × 克制 × 反应 ≤ 条件后上限`」。

## 本模块做什么

| 动作 | 事件 | 用途 |
|---|---|---|
| `elem_reaction` | `dmg_calc` | 印记反应轴：技能元素 × 目标印记 → 反应乘区（+ 清印 / AOE / 冻结 / 感电连击） |
| `elem_counter` | `dmg_calc` | 克制轴：三角循环 ×1.25（含解冻 / 打断） |
| `element_main_switch` | 技能施放 | 元素流转：切换主系（`cur_element`） |

装配：`apply_element_procs(actor)` —— 学了带 `element` 的技能才挂（学什么挂什么，零噪音）。

## 修正的两处配置缺陷（2026-09-11 取证）

1. `ELEMENT_REACTIONS` 里冻结写作 `("water", "ice_mark")` —— 游戏里**没有 water 元素**
   （三系 = fire/ice/thunder，§9.1 表）；按 §2「冰印 + 雷印 = 冻结」应为 `("thunder", "ice_mark")`。
   原样保留会让「冻结」永远不触发（水系技能不存在）。
2. 感电（`("thunder","thunder_mark")`）按 §2 需要**雷印满 3 层**，配置里没有层数门槛
   → 新增 `min_layers` 字段（缺省 = 1 层即可，保持其它反应行为不变）。
"""
from __future__ import annotations

from saintess_engine.battle.effects import register_action

# 印记 key（元素 → 印记）
ELEMENT_MARKS = {"fire": "fire_mark", "ice": "ice_mark", "thunder": "thunder_mark"}


def _info(params) -> dict:
    """技能数据（`_do_buff` 经 params["info"] 注入）——本模块数值唯一来源。

    注：本模块自持一份（`battle_team_procs` 里那个是私有 helper，跨模块直接引用会让
    动作在异常里静默失败——2026-09-11 实测踩到，故各自持有）。
    """
    i = params.get("info") if isinstance(params, dict) else None
    return i if isinstance(i, dict) else {}

# 克制轴（§9.1 三角循环：火 → 冰 → 雷 → 火）
#   火克冰：对**冰冻**目标 +25%，并解冻
#   冰克雷：对**雷印**目标 +25%，并打断
#   雷克火：对**灼烧**目标 +25%
COUNTER_RULES = {
    "fire":    {"victim_state": "freeze",       "mult": 1.25, "name": "破冰",
                "cleanse": "freeze",  "note": "解冻"},
    "ice":     {"victim_mark": "thunder_mark",  "mult": 1.25, "name": "冰封雷",
                "interrupt": True, "note": "打断"},
    "thunder": {"victim_state": "burn",         "mult": 1.25, "name": "雷引燃",
                "note": "灼烧目标增伤"},
}


# ============================================================
# 数据读取
# ============================================================

def _element_of(info: dict, actor: dict) -> str:
    """本次技能的伤害元素。

    技能自带 `element` 优先；缺省时若技能声明 `element_from_main` → 用**主系**
    （元素流转切换的那个，实现 §427「影响下次挂印系别」的语义）。
    """
    if not isinstance(info, dict):
        return ""
    el = str(info.get("element") or "")
    if el:
        return el
    if info.get("element_from_main"):
        return str((actor or {}).get("cur_element") or "")
    return ""


def _mark_of(target: dict, mark_key: str) -> int:
    e = (target or {}).get("effects") or {}
    entry = e.get(mark_key)
    if not isinstance(entry, dict):
        return 0
    try:
        return int(float(entry.get("stacks", 0) or 0))
    except Exception:
        return 0


def _reactions() -> dict:
    """反应表（内容侧配置；缺省空表 = 无反应，不崩）。"""
    try:
        from ..data.battle_config import ELEMENT_REACTIONS
        return ELEMENT_REACTIONS or {}
    except Exception:
        return {}


def _reaction_of(element: str, target: dict) -> dict:
    """印记反应判定：任一印记命中即返回反应 dict（含反应名/倍率/清印/额外效果）。

    对齐旧 `element_reaction()` 的遍历语义；另加 `min_layers` 门槛（感电需雷印 ≥3）。
    """
    if not element:
        return {}
    for mark_key in ELEMENT_MARKS.values():
        n = _mark_of(target, mark_key)
        if n <= 0:
            continue
        r = (_reactions() or {}).get((element, mark_key))
        if not r:
            continue
        try:
            need = int(r.get("min_layers", 1) or 1)
        except Exception:
            need = 1
        if n >= need:
            return r
    return {}


# ============================================================
# 动作：印记反应轴
# ============================================================

@register_action("elem_reaction")
def elem_reaction(battle, caster, target, params, logs):
    """`dmg_calc`：技能元素 × 目标印记 → 反应（乘区 + 清印 + 额外效果）。

    反应数值全部来自 `ELEMENT_REACTIONS`（内容侧配置），引擎零知识。
    """
    ctx = getattr(battle, "_fire_ctx", None)
    if not isinstance(ctx, dict):
        return
    actor = ctx.get("actor") or caster
    tgt = ctx.get("target") or target
    if not isinstance(tgt, dict):
        return
    element = _element_of(ctx.get("info") or {}, actor)
    if not element:
        return
    r = _reaction_of(element, tgt)
    if not r:
        return
    mult = 1.0
    try:
        mult = float(r.get("mult", 1.0) or 1.0)
    except Exception:
        mult = 1.0
    if mult != 1.0:
        ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
    name = r.get("name") or "元素反应"
    logs.append(f"💥 元素反应【{name}】" + (f" 伤害 ×{mult:g}" if mult != 1.0 else ""))
    # 清印（反应消耗印记）
    if r.get("clear"):
        ef = tgt.setdefault("effects", {})
        for mk in ELEMENT_MARKS.values():
            if _mark_of(tgt, mk) > 0:
                ef.pop(mk, None)
    # 额外效果：AOE / 冻结 / 感电连击
    extra = str(r.get("extra") or "")
    if extra == "freeze":
        _apply_freeze(battle, tgt, logs)
    elif extra == "chain":
        ef = tgt.setdefault("effects", {})
        old = ef.get("elem_chain") or {}
        n = int(old.get("stacks", 0) or 0) + 1 if isinstance(old, dict) else 1
        ef["elem_chain"] = {"stacks": n, "expire": None}
        logs.append(f"⚡ 感电：连击 +1（累计 {n}）")


def _apply_freeze(battle, tgt: dict, logs) -> None:
    """反应附带冻结：写控制态（mode=skip，1.5 刻 → 取整 2 刻）。"""
    try:
        from saintess_engine.battle import now_of
        now = float(now_of(battle) or 0)
    except Exception:
        now = float(getattr(battle, "_now", 0) or 0)
    ef = tgt.setdefault("effects", {})
    old = ef.get("freeze") or {}
    old_exp = float(old.get("expire", 0) or 0) if isinstance(old, dict) else 0.0
    ef["freeze"] = {"expire": max(old_exp, now + 2), "mode": "skip", "stacks": 1}
    logs.append(f"❄️ 【{tgt.get('name', '目标')}】被冻结 2 刻！")


# ============================================================
# 动作：克制轴
# ============================================================

@register_action("elem_counter")
def elem_counter(battle, caster, target, params, logs):
    """`dmg_calc`：克制轴（§9.1 三角循环，命中克制 → ×1.25 + 附带效果）。"""
    ctx = getattr(battle, "_fire_ctx", None)
    if not isinstance(ctx, dict):
        return
    actor = ctx.get("actor") or caster
    tgt = ctx.get("target") or target
    if not isinstance(tgt, dict):
        return
    element = _element_of(ctx.get("info") or {}, actor)
    rule = COUNTER_RULES.get(element)
    if not rule:
        return
    # 判定目标是否处于被克状态
    victim_state = rule.get("victim_state")
    victim_mark = rule.get("victim_mark")
    hit = False
    if victim_state:
        e = (tgt.get("effects") or {}).get(str(victim_state))
        hit = isinstance(e, dict)
    elif victim_mark:
        hit = _mark_of(tgt, str(victim_mark)) > 0
    if not hit:
        return
    mult = float(rule.get("mult", 1.25) or 1.25)
    ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * mult
    logs.append(f"✦ 元素克制【{rule.get('name')}】：伤害 ×{mult:g}（{rule.get('note', '')}）")
    # 附带：解冻 / 打断
    if rule.get("cleanse"):
        ef = tgt.setdefault("effects", {})
        if isinstance(ef.get(rule["cleanse"]), dict):
            ef.pop(rule["cleanse"], None)
            logs.append("🌡️ 冰层消融（解冻）")
    if rule.get("interrupt"):
        try:
            from saintess_engine.battle.effects import apply_effects
            apply_effects(battle, actor, tgt, [{"type": "interrupt"}], logs)
        except Exception:
            pass


# ============================================================
# 装配
# ============================================================
# ============================================================
# 动作：元素流转（主系切换 + 下次挂印转换）
# ============================================================

@register_action("class_element_switch")
def class_element_switch(battle, caster, target, params, logs):
    """元素流转（§427，lv62）：**切换当前主系**，并让**下一次**元素技能的挂印/元素
    改按主系走（实现 desc「影响下次挂印系别」）。

    - 主系落 `actor["cur_element"]`（随存档；展示/后续判定可读）。
    - 一次性转换标记 `actor["_elem_conv"] = 主系`：下一次带元素系别的技能施放时，
      由 `elem_conv_apply`（act_cast）改写该技能的 `element` 与挂印 `mech`，
      然后清标记（**只影响一次**，不会永久改变职业元素）。
    - 数值全从技能数据/主系来，模块内零写死。
    """
    src = caster if isinstance(caster, dict) else target
    if src is None:
        return
    info = _info(params)
    cycle = params.get("cycle") or info.get("element_cycle") or ["fire", "ice", "thunder"]
    if not isinstance(cycle, (list, tuple)) or not cycle:
        return
    cycle = list(cycle)
    cur = src.get("cur_element")
    nxt = cycle[(cycle.index(cur) + 1) % len(cycle)] if cur in cycle else cycle[0]
    src["cur_element"] = nxt
    src["_elem_conv"] = nxt          # 一次性：下次挂印按主系
    logs.append(f"🌀 元素流转：主系切换为【{nxt}】，下次挂印随主系")


@register_action("elem_conv_apply")
def elem_conv_apply(battle, caster, target, params, logs):
    """`act_cast`：若存在一次性转换标记 → 把本次技能的 `element` 与挂印 `mech`
    改写为主系，然后清标记。无标记 = 零行为。"""
    actor = (getattr(battle, "_fire_ctx", None) or {}).get("actor") or caster
    if not isinstance(actor, dict):
        return
    conv = actor.pop("_elem_conv", None)
    if not conv:
        return
    ctx = getattr(battle, "_fire_ctx", None) or {}
    info = ctx.get("info")
    if not isinstance(info, dict):
        return
    mark = ELEMENT_MARKS.get(str(conv))
    if not mark:
        return
    info["element"] = str(conv)
    # 挂印类技能（mech 是元素印）→ 换成主系的印
    if str(info.get("mech") or "") in ELEMENT_MARKS.values():
        info["mech"] = mark
    logs.append(f"🌀 元素转化：本次技能转为【{conv}】系")


def apply_element_procs(actor: dict) -> None:
    """学了带 `element` / `element_from_main` / `element_switch` 的技能才挂元素机制。

    挂载点：
    - `dmg_calc` → `elem_reaction` + `elem_counter`（两轴乘区）
    - `act_cast` → `elem_conv_apply`（元素转化的挂印改写，仅在学了元素流转时挂）
    幂等：重复装配只留一条。
    """
    if not isinstance(actor, dict):
        return
    cn = actor.get("class_name") or ""
    names = actor.get("learned_skills") or []
    if not cn or not names:
        return
    from ..content_rules.skills import skill_info
    has_elem = has_switch = False
    for s in names:
        try:
            info = skill_info(cn, s)
        except Exception:
            info = None
        if not isinstance(info, dict):
            continue
        if info.get("element") or info.get("element_from_main"):
            has_elem = True
        if str(info.get("effect") or "") == "element_switch":
            has_switch = True
        if has_elem and has_switch:
            break
    if not has_elem and not has_switch:
        return
    trig = actor.setdefault("triggers", {})
    if has_elem:
        lst = trig.setdefault("dmg_calc", [])
        # 顺序铁律：**克制先判、反应后算**——反应会清印（`clear: True`），
        #   若反应先跑，克制判定（读目标印记/状态）就会因印记已被清而失效
        #   （实测：冰打火印+雷印目标，反应先清雷印 → 冰克雷不触发）。
        for act in ("elem_counter", "elem_reaction"):
            if not any(isinstance(e, dict) and e.get("action") == act for e in lst):
                lst.append({"action": act})
    # 元素转化订阅：不仅学「元素流转」要挂——元素转化标记也可能来自其它来源
    #   （装备/消耗品/后续机制），`elem_conv_apply` 无标记时零行为，故零成本常挂。
    if has_elem or has_switch:
        lst2 = trig.setdefault("act_cast", [])
        if not any(isinstance(e, dict) and e.get("action") == "elem_conv_apply" for e in lst2):
            lst2.append({"action": "elem_conv_apply"})
