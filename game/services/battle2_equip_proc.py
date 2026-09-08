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
    # 以下旧时机 battle2 无 1:1 点位，第一批不迁（后续批次/上层处理）：
    # taken_after / turn_end / enemy_act / passive / dot_taken
}

# 每个旧事件映射后的 battle2 事件（返回 tuple）
def map_event(old_ev: str) -> tuple:
    return _EVENT_MAP.get(old_ev, ())


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
    """abyss_barrier：深渊屏障 = 起手 max_hp_pct 护盾（无 turns 字段 → 3 刻）。"""
    eff = {"type": "shield", "key": "we_abyss", "pct": float(wd.get("max_hp_pct") or 0.08),
           "turns": int(wd.get("turns") or 3), "on": "caster"}
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
    （trinity 的 thunder_pct 附加雷伤段 / dusk 的 stealth 段后续扩展动作补）"""
    old_ev = "skill_cast" if key == "novice_spark_followup" else "skill_hit"
    pct = float(wd.get("atk_pct") or 0)
    if pct <= 0:
        return {}
    eff = {"type": "buff", "key": wd.get("mark_key") or ("we_" + key),
           "turns": 999, "hit": {"dmg_mult": 1.0 + pct}, "on": "caster"}
    return {old_ev: [eff]}


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


# 第一批支持 key 清单（key → 翻译器）
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
    "trinity_rhythm": _translate_next_atk_mark,   # atk_pct 段（thunder_pct 附雷段后续补）
    # proc_retort_mark（受击反击势能）
    "gargoyle_retort": _translate_retort_mark,
    "titan_retort": _translate_retort_mark,
    "ranger_retort": _translate_retort_mark,
    "guardian_will": lambda k, wd: _translate_we(k, wd, "we_guardian_will", "taken",
                                                 ("chance", "weaken", "debuff_key", "turns")),
    # proc_shield taken 概率盾（族扩展动作带 cd）
    "sentinel_aegis": _translate_shield_taken_cd,
    "deeprock_aegis": _translate_shield_taken_cd,
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


def apply_to_actor(actor: dict) -> None:
    """把装备特效装配进 actor["triggers"]（幂等合并；命令层开战前调用）。"""
    if not actor:
        return
    install_ext_actions()  # 保证族扩展动作已注册（triggers 可能引用 we_xxx）
    merged = weapon_triggers(actor)
    tr = actor.setdefault("triggers", {})
    for ev, effs in merged.items():
        tr.setdefault(ev, []).extend(effs)
