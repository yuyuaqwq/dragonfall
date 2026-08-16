# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - potion_effects.py（v125.1 审计 P2-1：药水效果注册表）

消灭 battle.py _apply_potion_special 的 15 分支 if/elif 硬编码链：
- POTION_EFFECTS: {效果名: 函数}，仿 event_templates @register 模式
- handler 签名 fn(battle, player, value) -> str|None（返回日志行；None = 不追加日志）
- value 为 items.py 药水条目 effect_data dict（如 {"pct": 0.5}）；
  当前战斗分发链（special: payload 由 core/item_templates.py 生成，未携带物品数据）
  传 None 时回退 DEFAULTS——DEFAULTS 由 items.py effect_data 扫描构建（数据层单一权威）。

扩展方式（新增药水效果 = 注册函数 + 数据）：
1. items.py 药水条目加 effect + effect_data（数值字段按效果语义：pct=百分比/turns=回合数）
2. 本文件 register 一个新 handler（~10 行），数值全部读 value/DEFAULTS，禁止写死
"""

POTION_EFFECTS = {}


def register(name):
    """效果注册装饰器。"""
    def deco(fn):
        POTION_EFFECTS[name] = fn
        return fn
    return deco


# effect → 注册表 kind 别名（与 core/item_templates.py _BUFF_KEYS special 映射同口径；
# 3 个物品 effect 名 ≠ 注册表键名，扫描默认值时需对齐）
_EFFECT_KIND = {
    "armor_break_pot": "def_down",
    "rock_shield": "shield_small",
    "holy_shield": "shield_big",
}


def _scan_defaults():
    """从 items.py 药水 effect_data 扫描各效果默认数值（items.py = 数值单一权威）。
    同 effect 多物品共用一套数值（数据约定一致），首个命中为准。"""
    from ..data.items import ITEMS  # 延迟导入（core 聚合链惯例）
    out = {}
    for _d in ITEMS.values():
        ed = _d.get("effect_data")
        if not isinstance(ed, dict) or not ed:
            continue
        kind = _EFFECT_KIND.get(_d.get("effect"), _d.get("effect"))
        if kind and kind not in out:
            out[kind] = ed
    return out


DEFAULTS = _scan_defaults()


def _resolve(value, kind):
    """value（物品级 effect_data）缺省回退 DEFAULTS[kind]。"""
    if isinstance(value, dict) and value:
        return value
    return DEFAULTS.get(kind, {}) or {}


# ================= 效果实现 =================

@register("next_atk_up")
def eff_next_atk_up(battle, player, value):
    """狂怒药剂/月露精华/彩虹药剂/黑羽箭：下一次攻击 +50%（一次性，普攻/技能消费）。"""
    v = _resolve(value, "next_atk_up")
    pct = float(v.get("pct", 0.5))
    battle.p_buffs["next_atk_up"] = int(v.get("turns", 1))
    return f"⚔️ 你蓄势待发！下一次攻击+{int(pct * 100)}%！"


@register("heal_up")
def eff_heal_up(battle, player, value):
    """圣光药剂：治疗技能效果 +20%（3 回合）。"""
    v = _resolve(value, "heal_up")
    pct = float(v.get("pct", 0.2))
    battle.p_buffs["heal_up"] = int(v.get("turns", 3))
    return f"✨ 治疗增幅！治疗技能效果+{int(pct * 100)}%！(3 回合)"


@register("magic_resist")
def eff_magic_resist(battle, player, value):
    """龙鳞药剂/深渊药剂：受到魔法伤害 －15%（3 回合）。"""
    v = _resolve(value, "magic_resist")
    pct = float(v.get("pct", 0.15))
    battle.p_buffs["magic_resist"] = int(v.get("turns", 3))
    return f"🛡️ 魔鳞护体！受到魔法伤害－{int(pct * 100)}%！(3 回合)"


@register("thorns_pot")
def eff_thorns_pot(battle, player, value):
    """荆棘药剂：受击反弹 30% 伤害（3 回合）。"""
    v = _resolve(value, "thorns_pot")
    pct = float(v.get("pct", 0.30))
    battle.p_buffs["thorns_pot"] = int(v.get("turns", 3))
    return f"🌵 荆棘附体！受击反弹 {int(pct * 100)}% 伤害！(3 回合)"


@register("dodge_pot")
def eff_dodge_pot(battle, player, value):
    """影步药剂：15% 概率闪避攻击（3 回合，乘算并入闪避结算）。"""
    v = _resolve(value, "dodge_pot")
    pct = float(v.get("pct", 0.15))
    battle.p_buffs["dodge_pot"] = int(v.get("turns", 3))
    return f"💨 身法飘忽！{int(pct * 100)}% 概率闪避攻击！(3 回合)"


@register("cc_immune")
def eff_cc_immune(battle, player, value):
    """不动药剂：免疫眩晕/冻结/减速（3 回合）。"""
    v = _resolve(value, "cc_immune")
    battle.p_buffs["cc_immune"] = int(v.get("turns", 3))
    return "🗿 不动如山！免疫眩晕/冻结/减速！(3 回合)"


@register("execute_pot")
def eff_execute_pot(battle, player, value):
    """死神药剂：对生命<30% 的敌人 +30% 伤害（3 回合）。"""
    v = _resolve(value, "execute_pot")
    pct = float(v.get("pct", 0.30))
    th = float(v.get("hp_threshold", 0.30))
    battle.p_buffs["execute_pot"] = int(v.get("turns", 3))
    return f"💀 死神凝视！对生命<{int(th * 100)}%的敌人+{int(pct * 100)}%伤害！(3 回合)"


@register("def_down")
def eff_def_down(battle, player, value):
    """破甲药剂：敌人防御下降 15%（2 回合，_armor_break_pct 供防御结算）。"""
    v = _resolve(value, "def_down")
    pct = float(v.get("pct", 0.15))
    turns = int(v.get("turns", 2))
    battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), turns)
    battle.e_buffs["_armor_break_pct"] = pct
    return f"🛡️ 破甲！敌人防御下降 {int(pct * 100)}%！({turns} 回合)"


@register("pene_pot")
def eff_pene_pot(battle, player, value):
    """穿甲药剂：物穿 +15%（3 回合，与属性乘算）。"""
    v = _resolve(value, "pene_pot")
    pct = float(v.get("pct", 0.15))
    battle.p_buffs["pene_pot"] = int(v.get("turns", 3))
    return f"🗡️ 穿甲附刃！物穿 +{int(pct * 100)}%！(3 回合)"


@register("pene_magi_pot")
def eff_pene_magi_pot(battle, player, value):
    """破法药剂：法穿 +15%（3 回合，与属性乘算）。"""
    v = _resolve(value, "pene_magi_pot")
    pct = float(v.get("pct", 0.15))
    battle.p_buffs["pene_magi_pot"] = int(v.get("turns", 3))
    return f"🔮 破法附魔！法穿 +{int(pct * 100)}%！(3 回合)"


@register("lifesteal_pot")
def eff_lifesteal_pot(battle, player, value):
    """嗜血药剂：吸血 +15%（3 回合，乘算并入 _settle_lifesteal）。"""
    v = _resolve(value, "lifesteal_pot")
    pct = float(v.get("pct", 0.15))
    battle.p_buffs["lifesteal_pot"] = int(v.get("turns", 3))
    return f"🩸 嗜血药剂！吸血 +{int(pct * 100)}%！(3 回合)"


@register("crit_dmg_pot")
def eff_crit_dmg_pot(battle, player, value):
    """狂暴药剂：暴击伤害 +25%（3 回合，乘算并入暴击结算）。"""
    v = _resolve(value, "crit_dmg_pot")
    pct = float(v.get("pct", 0.25))
    battle.p_buffs["crit_dmg_pot"] = int(v.get("turns", 3))
    return f"💥 狂暴药剂！暴击伤害 +{int(pct * 100)}%！(3 回合)"


@register("block_pot")
def eff_block_pot(battle, player, value):
    """岩壁药剂：格挡 +15%（3 回合，乘算并入受击格挡）。"""
    v = _resolve(value, "block_pot")
    pct = float(v.get("pct", 0.15))
    battle.p_buffs["block_pot"] = int(v.get("turns", 3))
    return f"🛡️ 岩壁药剂！格挡 +{int(pct * 100)}%！(3 回合)"


@register("shield_small")
def eff_shield_small(battle, player, value):
    """岩盾药剂：获得 max_hp × 10% 护盾（3 回合）。"""
    v = _resolve(value, "shield_small")
    pct = float(v.get("pct", 0.10))
    gain = int(player.get("max_hp", 100) * pct)
    battle._add_shield("potion", gain, int(v.get("turns", 3)))
    return f"🛡️ 岩盾护体！获得 {gain} 点护盾！(3 回合)"


@register("shield_big")
def eff_shield_big(battle, player, value):
    """圣盾药剂：获得 max_hp × 15% 护盾（3 回合）。"""
    v = _resolve(value, "shield_big")
    pct = float(v.get("pct", 0.15))
    gain = int(player.get("max_hp", 100) * pct)
    battle._add_shield("potion", gain, int(v.get("turns", 3)))
    return f"🛡️ 圣盾护体！获得 {gain} 点护盾！(3 回合)"
