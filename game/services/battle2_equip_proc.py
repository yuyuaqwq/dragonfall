# -*- coding: utf-8 -*-
"""battle2 装备特效/词条装配层（game/services/battle2_equip_proc.py，N9）。

battle2 包外（引擎零知识——引擎不 import 本模块，本模块 import 引擎/数据）。
职责：把玩家装备的 weapon_effect / affix 数据 → actor["triggers"] 声明
（N8 事件总线消费），使装备特效在 battle2 战斗中生效。

架构（docs/REFACTOR_v181P4_N9_migration.md §2）：
- 效果源 = actor["triggers"] = {事件: [效果 dict]}，效果 dict 两种形态：
  ① 纯动词（引擎原生能力）：shield/buff/state_add/control/heal/...
  ② 族扩展动作（复杂机制，ACTION_HANDLERS 扩展注册）：type="we_xxx"
- 事件映射：旧 proc 事件集 → battle2 19 事件（hit→attack_hit+skill_hit 展开等）
- 数值权威：weapon_effect_data.WEAPON_EFFECT_DATA + 装备行 we_data 覆盖层
  （读表零默认值铁律：缺字段 = 无此行为）

N9 批次：第一批 = battle_start 起手类纯动词 key（proc_shield 起手 2 +
proc_buff 起手 6），验证「读表 → 事件映射 → triggers 装配 → 引擎 fire」管线。
后续批按 docs/REFACTOR_v181P4_N9_migration.md §3 铺开。
"""
from __future__ import annotations

from typing import Optional

# ============================================================
# 旧事件集 → battle2 19 事件映射
# ============================================================

# 旧 weapon proc 事件集（weapon_effects._WE_KEY_EVENTS 的 key）
_EVENT_MAP = {
    "battle_start": ("battle_start",),
    "hit": ("attack_hit", "skill_hit"),   # 普攻+技能通用命中
    "skill_hit": ("skill_hit",),
    "skill_cast": ("act_cast",),
    "taken": ("on_taken",),
    "heal": ("on_heal",),
    "turn_start": ("turn_start",),
    "threshold": ("threshold",),
    "crit": ("crit",),
    "kill": ("on_kill",),
    # N9A-2：旧 enemy_act（敌方行动后）→ 通用 act_done 广播（全员触发，效果侧
    # 自己 if 敌我判断——randuin/ice_vein 敌对判断在 we_act_done_slow 扩展动作内）
    "enemy_act": ("act_done",),
    # 以下旧时机 battle2 无 1:1 点位，第一批不迁（后续批次/上层处理）：
    # taken_after / turn_end / passive / dot_taken
}

# 每个旧事件映射后的 battle2 事件（返回 tuple）
def map_event(old_ev: str) -> tuple:
    """旧事件 → battle2 事件展开；不在表 = 假定已是 battle2 原生事件名，同名直通
    （dmg_calc/taken_calc/battle_start 等装配层可直接用 battle2 事件名）。"""
    return _EVENT_MAP.get(old_ev, (old_ev,))


# ============================================================
# 数据表读取（数值权威）
# ============================================================

_WE_TABLE = None


def _we_data() -> dict:
    global _WE_TABLE
    if _WE_TABLE is None:
        try:
            from game.data import weapon_effect_data as W
            _WE_TABLE = getattr(W, "WEAPON_EFFECT_DATA", {})
        except Exception:
            _WE_TABLE = {}
    return _WE_TABLE


def _we_config(key: str, actor: Optional[dict] = None) -> dict:
    """key 的生效参数：数据表权威 + 装备行 we_data 覆盖（同旧 effect_data 语义）。"""
    cfg = dict((_we_data() or {}).get(key) or {})
    if actor:
        for item in (actor.get("equipment") or {}).values():
            if not isinstance(item, dict):
                continue
            if item.get("weapon_effect") == key and isinstance(item.get("we_data"), dict):
                cfg.update(item["we_data"])
    return cfg


def equipped_weapon_keys(actor: dict) -> list:
    """actor 已装备的 weapon_effect key 列表（各槽位，去重保序）。"""
    out = []
    for item in (actor.get("equipment") or {}).values():
        if not isinstance(item, dict):
            continue
        we = item.get("weapon_effect")
        if we and we not in out:
            out.append(we)
    return out


# ============================================================
# affix 词条装配（N9.7：AFFIXES 76 → 分档）
# ============================================================
# 分档结论（docs/REFACTOR_v181P4_N9_7_affix_migration.md）：
# - A1 stat 型 26：装备生成时已折算进 item.stats → battle2 面板自动含，装配层跳过
# - B 事件型：trigger 映射 battle2 事件 → 翻译成效果声明（此文件翻译器）
# - 资源型/职业机制 ~37：上层职业模块缺口清单（此文件不装，静默跳过）
# tier 语义（旧 _affix_effs）：effect.tiers[装备品质] 覆盖主数值键（如能量上限
# full_pack purple 10/orange 20）；装配时按 item.quality 取档。

_AFFIX_TABLE = None


def _affix_data() -> dict:
    """AFFIXES 表（数值权威，惰性读）。"""
    global _AFFIX_TABLE
    if _AFFIX_TABLE is None:
        try:
            from game.data import affixes as _A
            _AFFIX_TABLE = getattr(_A, "AFFIXES", {})
        except Exception:
            _AFFIX_TABLE = {}
    return _AFFIX_TABLE


def equipped_affix_ids(actor: dict) -> list:
    """actor 已装备的全部 affix id（各槽位 affixes 列表，去重保序）。"""
    out = []
    for item in (actor.get("equipment") or {}).values():
        if not isinstance(item, dict):
            continue
        for aid in (item.get("affixes") or []):
            if aid and aid not in out:
                out.append(aid)
    return out


def _tier_value(eff: dict, quality: str):
    """effect.tiers[quality] 取档覆盖（旧 _affix_effs 语义）；无 tiers → None。"""
    tiers = eff.get("tiers")
    if not isinstance(tiers, dict):
        return None
    return tiers.get(quality or "")


def _affix_effect_final(aid: str, actor: dict) -> dict:
    """词条 effect + tier 覆盖（读 AFFIXES 表；未找到 = {} → 缺字段无行为）。"""
    info = (_affix_data() or {}).get(aid) or {}
    eff = dict(info.get("effect") or {})
    tiers = eff.get("tiers")
    if isinstance(tiers, dict):
        # 找该词条所在装备的品质（同名词条多件品质不同 → 取最高档）
        tv = None
        for item in (actor.get("equipment") or {}).values():
            if isinstance(item, dict) and aid in (item.get("affixes") or []):
                q = item.get("quality", "")
                if q in tiers:
                    cand = tiers[q]
                    if tv is None or (isinstance(cand, (int, float))
                                      and cand > tv):
                        tv = cand
        eff.pop("tiers", None)
        if tv is not None:
            # 主数值键 = 排除辅助键（cond/on/desc）外的第一个数值键
            for k, v in eff.items():
                if isinstance(v, (int, float)) and k not in ("cond",):
                    eff[k] = tv
                    break
    return eff


# ============================================================
# affix → 效果声明翻译器（按 aid 注册；chance 数据表权威）
# ============================================================

# 已支持 affix key 清单 → 翻译器（函数签名 (aid, actor, eff) -> {old_event: [效果]})
_AFFIX_TRANSLATORS: dict = {}


def _register_affix(aid: str):
    """affix 翻译器注册装饰器。"""
    def deco(fn):
        _AFFIX_TRANSLATORS[aid] = fn
        return fn
    return deco


def _affix_chance_of(aid: str) -> float:
    """词条触发概率（AFFIXES 表 chance；缺省 None = 恒触发——旧语义）。"""
    return (_affix_data() or {}).get(aid, {}).get("chance")


def _affix_hit_ev(eff: dict) -> str:
    """词条命中挂点：数据表自定义事件（如 soul_devourer skill_hit）缺省 hit
    （装配层 map_event 展开 attack_hit+skill_hit）。"""
    return eff.get("event") or "hit"


@_register_affix("shield")
def _af_shield(aid, actor, eff):
    """护盾：battle_start 10% maxhp 盾（3 刻）。（无 chance → 纯动词可直接走）"""
    return {"battle_start": [{"type": "shield", "key": "affix_shield",
                              "pct": float(eff.get("shield_hp_pct") or 0.10),
                              "turns": int(eff.get("turns") or 3), "on": "caster"}]}


@_register_affix("regen")
def _af_regen(aid, actor, eff):
    """回春：turn_start 回 1% 最大生命。"""
    return {"turn_start": [{"type": "heal", "pct": float(eff.get("pct") or 0.01),
                            "on": "caster"}]}


@_register_affix("meditate")
def _af_meditate(aid, actor, eff):
    """冥想：turn_start 回 1% 最大生命（法师词条，同 regen 语义）。"""
    return {"turn_start": [{"type": "heal", "pct": float(eff.get("pct") or 0.01),
                            "on": "caster"}]}


# ============ N9.7b on_hit 族（带 chance/附加伤害 → 扩展动作层） ============

@_register_affix("bleed")
def _af_bleed(aid, actor, eff):
    """流血：20% 使目标流血（每刻 dot_pct 生命，3 刻）。"""
    return {"hit": [{"type": "we_affix_dot", "key": aid, "aid": aid,
                     "state_key": "affix_bleed", "chance": _affix_chance_of(aid),
                     "stacks": eff.get("stacks") or 3}]}


@_register_affix("armor_break")
def _af_armor_break(aid, actor, eff):
    """破甲：25% 降低目标防御 15%（2 刻）。"""
    return {"hit": [{"type": "we_affix_defdown", "key": aid, "aid": aid,
                     "chance": _affix_chance_of(aid),
                     "pct": eff.get("pct") or 0.15,
                     "turns": eff.get("turns") or 2}]}


@_register_affix("element_fire")
def _af_element_fire(aid, actor, eff):
    """元素附加·火：5% 属性伤害（恒触发）。"""
    return {"hit": [{"type": "we_affix_element", "key": aid, "aid": aid,
                     "element": eff.get("element") or "fire",
                     "pct": eff.get("pct") or 0.05, "name": "火焰附加"}]}


@_register_affix("element_ice")
def _af_element_ice(aid, actor, eff):
    """元素附加·冰：5% 属性伤害 + 减速。"""
    return {"hit": [{"type": "we_affix_element", "key": aid, "aid": aid,
                     "element": eff.get("element") or "ice",
                     "pct": eff.get("pct") or 0.05, "name": "冰霜附加",
                     "slow": eff.get("slow") or 0.10,
                     "slow_turns": eff.get("slow_turns") or 2}]}


@_register_affix("element_thunder")
def _af_element_thunder(aid, actor, eff):
    """元素附加·雷：5% 属性伤害 + chance 20% 小爆。"""
    return {"hit": [{"type": "we_affix_element", "key": aid, "aid": aid,
                     "element": eff.get("element") or "thunder",
                     "pct": eff.get("pct") or 0.05, "name": "雷光附加",
                     "chance": _affix_chance_of(aid),
                     "thunder_bonus": eff.get("thunder_bonus") or 0.20}]}


@_register_affix("combo")
def _af_combo(aid, actor, eff):
    """连击：15% 追加一次 50% 伤害（本击 dmg × extra_atk）。"""
    return {"hit": [{"type": "we_affix_bonus", "key": aid, "aid": aid,
                     "mode": "dmg_pct", "chance": _affix_chance_of(aid),
                     "pct": eff.get("extra_atk") or 0.50,
                     "tag": "⚡", "name": "连击"}]}


@_register_affix("charge")
def _af_charge(aid, actor, eff):
    """蓄力：10% 追加 50% 伤害（本击 dmg × dmg_pct）。"""
    return {"hit": [{"type": "we_affix_bonus", "key": aid, "aid": aid,
                     "mode": "dmg_pct", "chance": _affix_chance_of(aid),
                     "pct": eff.get("dmg_pct") or 0.50,
                     "tag": "💪", "name": "蓄力爆发"}]}


@_register_affix("pierce")
def _af_pierce(aid, actor, eff):
    """贯穿：20% 无视防御追加伤害（玩家 atk × atk_pct 真伤）。"""
    return {"hit": [{"type": "we_affix_bonus", "key": aid, "aid": aid,
                     "mode": "atk_true", "chance": _affix_chance_of(aid),
                     "atk_pct": eff.get("atk_pct") or 0.60,
                     "tag": "🏹", "name": "贯穿"}]}


# ============ N9.7c on_taken 族 + dmg_reduce ============

@_register_affix("counter")
def _af_counter(aid, actor, eff):
    """反击：受击 20% 反击攻击方 atk×60%（on_taken，攻击方在 ctx.source）。"""
    return {"on_taken": [{"type": "we_affix_counter", "key": aid, "aid": aid,
                          "chance": _affix_chance_of(aid),
                          "atk_pct": eff.get("pct") or 0.60}]}


@_register_affix("tenacity_cc")
def _af_tenacity_cc(aid, actor, eff):
    """坚韧：受击 20% 免疫/清除自身负面 + 回 3% maxhp。"""
    return {"on_taken": [{"type": "we_affix_tenacity", "key": aid, "aid": aid,
                          "chance": _affix_chance_of(aid),
                          "heal_pct": eff.get("heal_pct") or 0.03}]}


@_register_affix("dmg_reduce")
def _af_dmg_reduce(aid, actor, eff):
    """全减伤（常驻 3%）：taken_calc 乘区 ×（1-0.03）。stat trigger 但实际是
    受击减伤（旧 TAKEN_EFFECTS reduce 段），装配成 taken_calc 乘区。"""
    return {"taken_calc": [{"type": "we_taken_mult_cond", "key": aid, "cond": "always",
                            "mult": 1.0 - float(eff.get("dmg_reduce") or 0.03),
                            "tag": "🛡️减伤"}]}


# ============ N9.7d 条件乘区（passive → dmg_calc 钩子） ============

@_register_affix("execute")
def _af_execute(aid, actor, eff):
    """处决：目标生命 <30% ×1.3（dmg_calc hp_target_lt）。"""
    return {"dmg_calc": [{"type": "we_dmg_mult_cond", "key": aid,
                          "cond": "hp_target_lt",
                          "threshold": eff.get("execute_threshold") or 0.30,
                          "mult": eff.get("dmg_mult") or 1.30,
                          "tag": eff.get("tag") or "💀处决"}]}


@_register_affix("hunt")
def _af_hunt(aid, actor, eff):
    """追猎：目标带猎印 ×1.2（dmg_calc enemy_marked）。"""
    return {"dmg_calc": [{"type": "we_dmg_mult_cond", "key": aid,
                          "cond": "enemy_marked",
                          "mult": eff.get("dmg_mult") or 1.20,
                          "tag": eff.get("tag") or "🎯追猎"}]}


@_register_affix("break_magic")
def _af_break_magic(aid, actor, eff):
    """破魔：目标为法系 ×1.25（dmg_calc role_caster）。"""
    return {"dmg_calc": [{"type": "we_dmg_mult_cond", "key": aid,
                          "cond": "role_caster",
                          "mult": eff.get("dmg_mult") or 1.25,
                          "tag": eff.get("tag") or "🔮破魔"}]}


@_register_affix("dragon_aw")
def _af_dragon_aw(aid, actor, eff):
    """龙威：目标名含龙 ×1.25（dmg_calc name_contains）。"""
    return {"dmg_calc": [{"type": "we_dmg_mult_cond", "key": aid,
                          "cond": "name_contains",
                          "keywords": eff.get("enemy_contains") or ["龙"],
                          "mult": eff.get("dmg_mult") or 1.25,
                          "tag": eff.get("tag") or "🐉龙威"}]}


def affix_triggers_for_key(aid: str, actor: dict) -> dict:
    """单个 affix → {old_event: [效果 dict]}（未支持 key → {}）。"""
    fn = _AFFIX_TRANSLATORS.get(aid)
    if fn is None:
        return {}
    eff = _affix_effect_final(aid, actor)
    if not eff and aid not in _AFFIX_TRANSLATORS:
        return {}
    return fn(aid, actor, eff)


# ============================================================
# key → 效果声明翻译（第一批：纯动词 battle_start 起手类）
# ============================================================
# 返回 {old_event(字符串): [效果 dict]}（装配时 map_event 把旧事件展开成 battle2 事件）

def _translate_shield_start(key: str, wd: dict) -> dict:
    """proc_shield battle_start 起手盾：盾值 = shield_hp_pct×maxhp / shield_pct×maxhp /
    base+per_lv×lv（sentinel 型后续批），turns 由数据给。"""
    turns = int(wd.get("turns") or 3)
    eff = {"type": "shield", "key": wd.get("shield_key") or ("we_" + key),
           "turns": turns, "on": "caster"}
    if wd.get("base") is not None or wd.get("per_lv") is not None:
        # 固定值形态（value 按 level 由装配时算不了 level 依赖——走 pct 或交给扩展动作）
        return {}  # 第一批不含该形态（sentinel/deeprock 属 taken 概率盾，后续批）
    if wd.get("shield_pct") is not None:
        eff["pct"] = float(wd["shield_pct"])
    else:
        eff["pct"] = float(wd.get("shield_hp_pct") or 0.10)
    return {"battle_start": [eff]}


def _translate_buff_start(key: str, wd: dict) -> dict:
    """proc_buff battle_start 起手 buff：spd_pct → buff 动词（spd mul 1+pct，turns 数据给）。"""
    if wd.get("spd_pct") is None:
        return {}
    eff = {"type": "buff", "key": wd.get("buff_key") or key,
           "stat": "spd", "op": "mul", "mult": 1.0 + float(wd["spd_pct"]),
           "turns": int(wd.get("turns") or 3), "on": "caster"}
    return {"battle_start": [eff]}


def _translate_shield_abyss(key: str, wd: dict) -> dict:
    """abyss_barrier：深渊屏障 = battle_start 永久最大生命加成（we_abyss 扩展动作）。"""
    eff = {"type": "we_abyss", "key": key}
    if wd.get("max_hp_pct") is not None:
        eff["max_hp_pct"] = wd["max_hp_pct"]
    if wd.get("log") is not None:
        eff["log"] = wd["log"]
    return {"battle_start": [eff]}


def _translate_regen_turn_start(key: str, wd: dict) -> dict:
    """proc_aux regen 型：每刻（turn_start）回复。guard_regen = 已损生命%；
    dawn_regen/undying_band = 最大生命%（heal 动词 missing_pct/pct，N9.4 引擎扩展）。"""
    pct = float(wd.get("pct") or 0.02)
    if key == "guard_regen":
        eff = {"type": "heal", "missing_pct": pct, "on": "caster"}
    else:
        eff = {"type": "heal", "pct": pct, "on": "caster"}
    return {"turn_start": [eff]}


def _translate_stack_hit(key: str, wd: dict) -> dict:
    """proc_stack 纯叠层型（wind_mark）：每次命中 +1 层（cap/stat_scale 由 STATE_EFFECTS
    声明，面板折算读 state；命中 = 普攻+技能双事件展开）。"""
    eff = {"type": "state_add", "key": key, "amount": 1, "on": "caster"}
    return {"hit": [eff]}


def _translate_we(key: str, wd: dict, action: str, old_ev: str, fields: tuple) -> dict:
    """通用族扩展动作翻译：type=action + key + 指定字段透传，挂 old_ev 事件。"""
    eff = {"type": action, "key": key}
    for f in fields:
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {old_ev: [eff]}


def _translate_dot_hit(key: str, wd: dict) -> dict:
    """proc_dot 命中挂 DOT：族扩展动作 we_dot（chance 概率 + 挂 state dot 层）。
    smith/rong/blood = hit 双事件；ember_burn = skill_hit。"""
    ev = "skill_hit" if key == "ember_burn" else "hit"
    eff = {"type": "we_dot", "key": key}
    for f in ("dot_key", "chance", "turns"):
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {ev: [eff]}


def _translate_reflect_taken(key: str, wd: dict) -> dict:
    """proc_reflect 受击反弹：族扩展动作 we_reflect（on_taken；攻击者=caster 反弹对象）。
    参数全带（chance/reflect_pct/heal_pct/heal_down/max_hp_pct/burn_stack——缺省执行器兜底无此段）。"""
    eff = {"type": "we_reflect", "key": key}
    for f in ("chance", "reflect_pct", "heal_pct", "heal_down", "max_hp_pct", "burn_stack"):
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {"taken": [eff]}


def _translate_buff_hit_self(key: str, wd: dict, old_ev: str) -> dict:
    """通用：事件后自身 buff（属性提升——buff 动词 stat/op/mult 快照）。"""
    stat = wd.get("stat") or "spd"
    op = wd.get("op") or "mul"
    mult = float(wd.get("spd_pct") or 0)
    if mult <= 0:
        return {}
    eff = {"type": "buff", "key": wd.get("buff_key") or key, "stat": stat, "op": op,
           "mult": 1.0 + mult, "turns": int(wd.get("turns") or 3), "on": "caster"}
    return {old_ev: [eff]}


def _translate_next_atk_mark(key: str, wd: dict) -> dict:
    """proc_next_atk_mark：命中后给自身挂「下次出手强化」buff（引擎 N7.3 hit 子键
    天然支持：出手时消费 dmg_mult）。mountain/oath = skill_hit；spark = skill_cast。
    （dusk 的 stealth 段后续扩展动作补；trinity 走 _translate_trinity 含附雷段）"""
    old_ev = "skill_cast" if key == "novice_spark_followup" else "skill_hit"
    pct = float(wd.get("atk_pct") or 0)
    if pct <= 0:
        return {}
    eff = {"type": "buff", "key": wd.get("mark_key") or ("we_" + key),
           "turns": 999, "hit": {"dmg_mult": 1.0 + pct}, "on": "caster"}
    return {old_ev: [eff]}


def _translate_trinity(key: str, wd: dict) -> dict:
    """proc_next_atk_mark trinity_rhythm（奔雷大剑）：技能后下一次出手 +30% 伤害
    **并附带 atk×thunder_pct 雷属性伤害**（N9.8 补 thunder 段）。

    - atk_pct 段：buff hit 子键 dmg_mult（引擎 N7.3 出手消费，同族通用）；
    - thunder 段：buff hit 子键 bonus_atk_pct —— 引擎 _consume_hit_buffs 返回
      附伤参数 → actions 主伤害落地后按 atk×pct 追一段独立伤害（走 landing
      统一收口）。数值全读 wd 表（零硬编码）；无 thunder_pct → 纯 atk 段
      （读表零默认值：缺字段 = 无此行为）。
    """
    pct = float(wd.get("atk_pct") or 0)
    if pct <= 0:
        return {}
    hit = {"dmg_mult": 1.0 + pct}
    tp = float(wd.get("thunder_pct") or 0)
    if tp > 0:
        hit["bonus_atk_pct"] = tp
        hit["bonus_tag"] = wd.get("bonus_tag") or "⚡"
    eff = {"type": "buff", "key": wd.get("mark_key") or ("we_" + key),
           "turns": 999, "hit": hit, "on": "caster"}
    return {"skill_hit": [eff]}


def _translate_retort_mark(key: str, wd: dict) -> dict:
    """proc_retort_mark：受击后自身挂「下次出手强化」buff（反击势能，同 hit 子键消费）。
    gargoyle/titan/ranger 共用 we_retort 键（同源刷新，各取 next_atk_pct）。"""
    pct = float(wd.get("next_atk_pct") or 0)
    if pct <= 0:
        return {}
    eff = {"type": "buff", "key": wd.get("mark_key") or "we_retort",
           "turns": 999, "hit": {"dmg_mult": 1.0 + pct}, "on": "caster"}
    return {"taken": [eff]}


def _translate_shield_taken_cd(key: str, wd: dict) -> dict:
    """proc_shield taken 概率盾（sentinel/deeprock）：族扩展动作 we_shield_taken
    （chance + cd 判定 → 上盾）。base+per_lv×lv / shield_pct×maxhp。"""
    eff = {"type": "we_shield_taken", "key": key}
    for f in ("chance", "base", "per_lv", "shield_pct", "turns", "cd", "shield_key", "cd_key"):
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {"taken": [eff]}


def _translate_shield_cond(key: str, wd: dict, old_ev: str) -> dict:
    """proc_shield 条件型：族扩展动作 we_shield_cond。
    threshold 低保盾（bedrock/gargoyle/firmament）挂 on_taken（受击后自查 hp 阈值）；
    heal 溢出（echo_bless/atonement）挂 heal；crit 盾（endless_radiance）挂 crit。"""
    eff = {"type": "we_shield_cond", "key": key}
    for f in ("threshold", "shield_hp_pct", "heal_pct", "turns", "per_battle",
              "overflow_pct", "cap_hp_pct", "shield_key", "used_key", "active_key",
              "cd_key", "cd", "shield_turns"):
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {old_ev: [eff]}


def _translate_control(key: str, wd: dict, old_ev: str) -> dict:
    """proc_control 敌方控制：we_control 扩展动作。字段全带（mode/chance/cd/限次/
    slow/freeze 参数——执行器按 mode 分派，缺省无此段）。"""
    eff = {"type": "we_control", "key": key}
    for f in ("mode", "chance", "slow_turns", "slow_pct", "freeze_turns", "heal_down",
              "cd", "cd_key", "used_key", "max_per_battle", "threshold", "turns", "source", "log"):
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {old_ev: [eff]}


def _translate_death_dance(key: str, wd: dict) -> dict:
    """proc_special death_dance 缓伤池：on_taken 收池（dmg×pool_pct）+ turn_start 结算
    （pay = pool×pay_pct 扣血）。池存 actor.ext.we_proc[pool_key]（扩展动作自管）。
    battle_start 惰性建键由执行器 .get 天然缺省 0，无需事件。"""
    pool_key = wd.get("pool_key") or "we_death_pool"
    return {
        "on_taken": [{"type": "we_death_pool_add", "key": key, "pool_key": pool_key,
                      "pool_pct": float(wd.get("pool_pct") or 0.35)}],
        "turn_start": [{"type": "we_death_pool_pay", "key": key, "pool_key": pool_key,
                        "pay_pct": float(wd.get("pay_pct") or 0.10)}],
    }


def _translate_act_done_slow(key: str, wd: dict) -> dict:
    """proc_control spd_down_stack（randuin/ice_vein）：敌对 actor 行动完成 → 给它
    叠减速层。挂 enemy_act → act_done（全员广播）；敌我判断在扩展动作
    we_act_done_slow 内（hostile_sides 查 owner vs acted）。
    ⚠️ state key 用效果 key（randuin_weary/ice_vein）而非数据表 stack_key
    （_randuin_stack/_ice_vein_stack——那是旧 e_buffs 内部键）——battle2 的
    STATE_EFFECTS 面板折算/层 cap 以注册 key 为权威。"""
    eff = {"type": "we_act_done_slow", "key": key, "stack_key": key,
           "max_stack": wd.get("max_stack"),
           "spd_down_pct": wd.get("spd_down_pct")}
    return {"enemy_act": [eff]}


def _translate_extra_dmg(key: str, wd: dict) -> dict:
    """proc_extra_dmg 命中追击：we_extra_dmg 扩展动作。事件 = 数据表注册事件
    （skill_hit 4：afterglow/spellblade/annihilation/endless_blade；其余 hit）。"""
    ev = "skill_hit" if key in ("afterglow_splash", "spellblade_echo",
                                "annihilation_echo", "endless_blade") else "hit"
    eff = {"type": "we_extra_dmg", "key": key}
    for f in ("mode", "chance", "atk_pct", "pene_pct", "guarantee", "count",
              "lost_hp_pct", "cap_pct", "cur_hp_pct", "heal_pct", "stack_key",
              "used_key", "log"):
        if wd.get(f) is not None:
            eff[f] = wd[f]
    return {ev: [eff]}


def _translate_dusk_blade(key: str, wd: dict) -> dict:
    """proc_next_atk_mark dusk_blade（kill）：击杀后潜行（必暴）+ 下次攻击 +30%。"""
    effs = []
    spd_pct = float(wd.get("next_atk_pct") or 0)
    if spd_pct > 0:
        effs.append({"type": "buff", "key": wd.get("mark_key") or "we_dusk",
                     "turns": 999, "hit": {"dmg_mult": 1.0 + spd_pct}, "on": "caster"})
    effs.append({"type": "buff", "key": wd.get("buff_key") or "stealth",
                 "turns": 999, "hit": {"guaranteed_crit": True}, "on": "caster"})
    return {"kill": effs}


def _cond_mult(old_ev: str, cond: str, threshold: float, mult: float, tag: str = "") -> dict:
    """条件乘区翻译（dmg_calc/taken_calc → we_*_mult_cond 扩展动作）。"""
    return {old_ev: [{"type": "we_dmg_mult_cond", "cond": cond, "threshold": threshold,
                      "mult": mult, "tag": tag}]}


def _star_slayer(wd: dict) -> dict:
    """弑星：目标 hp>70% ×1.15（dmg_calc）+ 暴伤 +30% 面板（battle_start buff）。"""
    out = {"dmg_calc": [{"type": "we_dmg_mult_cond", "cond": "hp_target_gt",
                         "threshold": float(wd.get("threshold") or 0.70),
                         "mult": float(wd.get("dmg_mult") or 1.15), "tag": "⭐弑星"}]}
    cd = float(wd.get("crit_dmg") or 0)
    if cd > 0:
        out["battle_start"] = [{"type": "buff", "key": "we_star_slayer_cd",
                                "stat": "crit_dmg", "op": "add", "mult": cd,
                                "turns": 999, "on": "caster"}]
    return out


def _arcane_firmament(wd: dict) -> dict:
    """奥术苍穹：魔攻 +15% 面板（battle_start buff）+ 魔法技 ×1.1（dmg_calc kind_magic）。"""
    return {
        "battle_start": [{"type": "buff", "key": "we_arcane_matk", "stat": "matk",
                          "op": "mul", "mult": 1.0 + float(wd.get("matk_pct") or 0.15),
                          "turns": 999, "on": "caster"}],
        "dmg_calc": [{"type": "we_dmg_mult_cond", "cond": "kind_magic",
                      "mult": 1.0 + float(wd.get("skill_dmg_pct") or 0.10), "tag": "✨奥术苍穹"}],
    }


def _stack_pair(key: str, wd: dict, prod_old_ev: str) -> dict:
    """叠层放大器翻译：生产事件 → we_stack_prod；dmg_calc → we_amp_consume。"""
    return {
        prod_old_ev: [{"type": "we_stack_prod", "key": key,
                       "stack_key": wd.get("stack_key") or key,
                       "need": wd.get("need"), "charge_key": wd.get("charge_key"),
                       "charge_pct": wd.get("charge_pct")}],
        "dmg_calc": [{"type": "we_amp_consume", "key": key,
                      "stack_key": wd.get("stack_key") or key,
                      "per_pct": wd.get("per_pct") or wd.get("dmg_pct_per"),
                      "charge_key": wd.get("charge_key")}],
    }


# 第一批支持 key 清单（key → 翻译器）
# proc_heal amp 被动常驻 4 key（不走 triggers——装配 state heal_amp_pct）
_HEAL_AMP_KEYS = ("vital_band", "holy_radiance_mail", "echo_band", "novice_regen_heal")

_START_TRANSLATORS = {
    # proc_shield battle_start 起手盾
    "starlight_bulwark": _translate_shield_start,
    "eclipse_crown": _translate_shield_start,
    # proc_buff battle_start 起手速度 buff
    "gale_step": _translate_buff_start,
    "swift_boots": _translate_buff_start,
    "deadman_stride": _translate_buff_start,
    "temple_stride": _translate_buff_start,
    "void_stride": _translate_buff_start,
    # 深渊屏障（单独形态：max_hp_pct 起手盾）
    "abyss_barrier": _translate_shield_abyss,
    # proc_aux regen 型（每刻回复）
    "guard_regen": _translate_regen_turn_start,
    "dawn_regen": _translate_regen_turn_start,
    "undying_band": _translate_regen_turn_start,
    # proc_stack 纯叠层型（命中叠层 + state_effects 面板折算）
    "wind_mark": _translate_stack_hit,
    # proc_dot 命中挂 DOT（族扩展动作）
    "smith_blaze_wound": _translate_dot_hit,
    "rong_lu_yu_wen": _translate_dot_hit,
    "ember_burn": _translate_dot_hit,
    "blood_trace": _translate_dot_hit,
    # proc_reflect 受击反弹（族扩展动作）
    "thorn_armor": _translate_reflect_taken,
    "retribution_ring": _translate_reflect_taken,
    "iron_echo": _translate_reflect_taken,
    "dragon_spine_mail": _translate_reflect_taken,
    "ember_bulwark": _translate_reflect_taken,
    # proc_buff hit 型（自身速度 buff）
    "novice_wind_spd": lambda k, wd: _translate_buff_hit_self(k, wd, "hit"),
    # proc_next_atk_mark（下次出手强化 buff，引擎 hit 子键消费）
    "mountain_break": _translate_next_atk_mark,
    "oath_blade": _translate_next_atk_mark,
    "novice_spark_followup": _translate_next_atk_mark,
    "dusk_blade": _translate_dusk_blade,
    "trinity_rhythm": _translate_trinity,   # atk_pct + thunder_pct 双段（N9.8 收口）
    # proc_retort_mark（受击反击势能）
    "gargoyle_retort": _translate_retort_mark,
    "titan_retort": _translate_retort_mark,
    "ranger_retort": _translate_retort_mark,
    "guardian_will": lambda k, wd: _translate_we(k, wd, "we_guardian_will", "taken",
                                                 ("chance", "weaken", "debuff_key", "turns")),
    # proc_shield taken 概率盾（族扩展动作带 cd）
    "sentinel_aegis": _translate_shield_taken_cd,
    "deeprock_aegis": _translate_shield_taken_cd,
    # proc_shield 条件盾（threshold 低保 / heal 溢出 / crit）
    "bedrock_crown": lambda k, wd: _translate_shield_cond(k, wd, "taken"),
    "firmament_crown": lambda k, wd: _translate_shield_cond(k, wd, "taken"),
    "gargoyle_heart": lambda k, wd: _translate_shield_cond(k, wd, "taken"),
    "echo_bless": lambda k, wd: _translate_shield_cond(k, wd, "heal"),
    "atonement_shield": lambda k, wd: _translate_shield_cond(k, wd, "heal"),
    "endless_radiance": lambda k, wd: _translate_shield_cond(k, wd, "crit"),
    # proc_extra_dmg 命中追击（族扩展动作多 mode）
    "afterglow_splash": _translate_extra_dmg,
    "spellblade_echo": _translate_extra_dmg,
    "annihilation_echo": _translate_extra_dmg,
    "wind_split": _translate_extra_dmg,
    "phantom_barrage": _translate_extra_dmg,
    "endless_blade": _translate_extra_dmg,
    "hunter_open": _translate_extra_dmg,
    "siren_fang": _translate_extra_dmg,
    "star_pierce": _translate_extra_dmg,
    "soul_eater": _translate_extra_dmg,
    "novice_lifesteal": _translate_extra_dmg,
    # proc_control 敌方控制（randuin_weary/ice_vein 依赖 enemy_act 事件暂缺）
    "frost_ring": lambda k, wd: _translate_control(k, wd, "hit"),
    "holy_judgment_field": lambda k, wd: _translate_control(k, wd, "hit"),
    "everfrost_domain": lambda k, wd: _translate_control(k, wd, "skill_hit"),
    "everfrost_scepter": lambda k, wd: _translate_control(k, wd, "skill_hit"),
    "frost_crown": lambda k, wd: _translate_control(k, wd, "taken"),
    "holy_word_bind": lambda k, wd: _translate_control(k, wd, "heal"),
    "time_freeze": lambda k, wd: _translate_control(k, wd, "taken"),
    # proc_aux novice_dawn_mana（施法首次回蓝——we_mana_once 扩展动作）
    "novice_dawn_mana": lambda k, wd: _translate_we(k, wd, "we_mana_once", "skill_cast",
                                                    ("mp", "log")),
    # proc_dr_revive undying_will（battle_start 挂濒死保护层——landing 致死保底）
    "undying_will": lambda k, wd: {
        "battle_start": [{"type": "state_add", "key": "death_guard", "amount": 1,
                          "on": "caster", "log": wd.get("log")}],
    },
    # proc_passive_mult 条件乘区（dmg_calc/taken_calc 通道）
    "twilight_execute": lambda k, wd: _cond_mult("dmg_calc", "hp_target_lt",
                                                 float(wd.get("threshold") or 0.40),
                                                 float(wd.get("dmg_mult") or 1.25), "🌆暮光处决"),
    "star_slayer_edge": lambda k, wd: _star_slayer(wd),
    "arcane_firmament": lambda k, wd: _arcane_firmament(wd),
    # proc_dr_revive death_dance_armor（受击减伤 8%——taken_calc 通道；复活段缺口）
    "death_dance_armor": lambda k, wd: {
        "taken_calc": [{"type": "we_taken_mult_cond", "key": k, "cond": "always",
                        "mult": 1.0 - float(wd.get("taken_reduce_pct") or 0.08)}],
    },
    # proc_special 首刻守御（taken_calc first_turn 一次）
    "novice_first_turn_guard": lambda k, wd: {
        "taken_calc": [{"type": "we_taken_mult_cond", "key": k, "cond": "first_turn",
                        "mult": 1.0 - float(wd.get("reduce_pct") or 0.10),
                        "used_key": wd.get("mark_key") or "novice_guard_used"}],
    },
    # proc_stack 叠层放大器（生产事件 + dmg_calc 消费）
    "rune_amp": lambda k, wd: _stack_pair(k, wd, "skill_cast"),
    "sage_amp": lambda k, wd: _stack_pair(k, wd, "skill_cast"),
    "eternal_codex": lambda k, wd: _stack_pair(k, wd, "skill_cast"),
    "time_staff": lambda k, wd: _stack_pair(k, wd, "turn_start"),
    "thunder_weave": lambda k, wd: _stack_pair(k, wd, "hit"),
    # proc_control 敌方控制（randuin_weary/ice_vein = act_done 叠减速层）
    "randuin_weary": _translate_act_done_slow,
    "ice_vein": _translate_act_done_slow,
    # proc_special death_dance 缓伤池（受击收池 + 每刻结算）
    "death_dance": _translate_death_dance,
}


def triggers_for_key(key: str, actor: Optional[dict] = None) -> dict:
    """单个 weapon key → {old_event: [效果 dict]}（未支持 key → {}）。"""
    if key not in _START_TRANSLATORS:
        return {}
    wd = _we_config(key, actor)
    fn = _START_TRANSLATORS[key]
    return fn(key, wd)


# ============================================================
# 装配入口
# ============================================================

_EXT_LOADED = False


def install_ext_actions() -> None:
    """注册族扩展动作（形态 2）——import 时 register_action 装饰器即注册，幂等。"""
    global _EXT_LOADED
    if _EXT_LOADED:
        return
    _EXT_LOADED = True
    from game.services import battle2_we_procs as _WEP
    _WEP.ensure_registered()


def weapon_triggers(actor: dict) -> dict:
    """actor 全部已装备武器特效 → {battle2事件: [效果 dict]}。

    内部先把 key 翻译成 {old_event: [效果]}，再把 old_event 映射展开到
    battle2 事件（hit → attack_hit + skill_hit 双事件注册）。
    """
    out: dict = {}
    for key in equipped_weapon_keys(actor):
        raw = triggers_for_key(key, actor)
        if not raw:
            continue  # 未支持 key：静默跳过（范围外）
        for old_ev, effs in raw.items():
            for b2_ev in map_event(old_ev):
                out.setdefault(b2_ev, []).extend(list(effs))
    return out


def affix_triggers(actor: dict) -> dict:
    """actor 全部已装备词条（事件型）→ {battle2事件: [效果 dict]}。

    - stat 型词条（生成时已折算进 item.stats）不产生 triggers（面板自动含）
    - 资源型/职业机制词条：翻译器未注册 → 静默跳过（上层职业模块缺口清单）
    - 事件型走翻译器 + 事件映射展开（hit → attack_hit + skill_hit）
    """
    out: dict = {}
    for aid in equipped_affix_ids(actor):
        raw = affix_triggers_for_key(aid, actor)
        if not raw:
            continue
        for old_ev, effs in raw.items():
            for b2_ev in map_event(old_ev):
                out.setdefault(b2_ev, []).extend(list(effs))
    return out


def apply_to_actor(actor: dict) -> None:
    """把装备特效+词条装配进 actor（幂等；命令层开战前调用）：
    1. 事件型效果 → actor["triggers"]（武器特效 + 词条事件型合并）
    2. 被动常驻型（proc_heal amp：受疗增幅）→ actor.state.heal_amp_pct（landing 折算）"""
    if not actor:
        return
    install_ext_actions()
    # 1) 事件型（武器特效 + affix 词条）
    merged = weapon_triggers(actor)
    try:
        _afx = affix_triggers(actor)
        for ev, effs in _afx.items():
            merged.setdefault(ev, []).extend(effs)
    except Exception:
        pass  # 词条装配异常不阻断武器装配（容错）
    tr = actor.setdefault("triggers", {})
    for ev, effs in merged.items():
        tr.setdefault(ev, []).extend(effs)
    # 2) 被动常驻：heal amp（vital_band 等 proc_heal amp 4 key）
    amp = 0.0
    for key in equipped_weapon_keys(actor):
        wd = _we_config(key, actor)
        if (wd.get("family") == "proc_heal" and wd.get("heal_pct") is not None
                and key in _HEAL_AMP_KEYS):
            pct = float(wd.get("heal_pct") or 0)
            if pct > 0:
                amp = 1.0 - (1.0 - amp) * (1.0 - pct)  # 多件叠乘转加和
    if amp > 0:
        st = actor.setdefault("state", {})
        st["heal_amp_pct"] = max(float(st.get("heal_amp_pct", 0) or 0), amp)
