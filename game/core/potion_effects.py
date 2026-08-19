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


# ================= v130.2 资源联动消耗品（7 类新 effect handler） =================
# 消费端：items.py 尾部 19 件资源联动消耗品（i_rage_draught ~ i_surging_brew）。
# handler 签名统一 fn(battle, player, value)：battle=Battle 实例、player=玩家 dict、
# value=物品级 effect_data（由 item_templates 注入 special payload；旧特殊药水无数据 → None 走 DEFAULTS）。
# 资源值/回合类效果挂 p_buffs + p_eff{battle}（持久数据），引擎侧触发点消费。
# 职业校验统一走 battle._branch_keys（B1 分支级 resource_override，v130.2）。


def _item_res_def(key: str) -> dict:
    """按资源 key 查核心资源定义（副资源 resonance/echo 亦按 key 注册）。"""
    from .. import engine as E
    return E.core_resource_def_by_key(key) or {}


def _res_mine(battle, player, key: str) -> bool:
    """玩家职业/转职分支是否持有该资源位（如时之沙仅时咒法师、怒气仅战士）。"""
    return bool(key) and key in battle._branch_keys(player)


@register("restore_resource")
def eff_restore_resource(battle, player, value):
    """v130.2 回资源类消耗品：立即回复核心资源。
    effect_data {key, amount, cooldown?, once_per_battle?, next_heal_pct?}
    支持：cooldown（叠加冷却，圣辉药剂 2 回合）/ once_per_battle（瞬步结晶每场限 1 次）/
    next_heal_pct（信仰结晶：下个治疗增强，_skill_heal 消费一次）。
    职业不符（如非时咒法师用时之沙漏）→ 无效无消耗。"""
    v = _resolve(value, "restore_resource")
    key = v.get("key", "")
    amount = int(v.get("amount", 0) or 0)
    if not key or amount <= 0:
        return "🧪 药剂效果配置异常，没有生效！"
    if not _res_mine(battle, player, key):
        return "🧪 这瓶药剂对你的职业没有效果！"
    # once_per_battle：每场限 1 次（战斗内资源 key 作标记，key 唯一性保证不重复）
    once = bool(v.get("once_per_battle"))
    if once:
        _used = battle.p_eff.setdefault("once_restore", [])
        if key in _used:
            return "⏳ 这瓶药剂每场战斗只能使用 1 次，已经用过了！"
    # cooldown：叠加冷却（同资源位独占）
    cd = int(v.get("cooldown", 0) or 0)
    _cdk = "item_cd_" + key
    if cd > 0 and int(battle.cooldown.get(_cdk, 0) or 0) > 0:
        return f"⏳ 药剂还在冷却中(剩余 {int(battle.cooldown.get(_cdk, 0) or 0)} 回合)！"
    rd = _item_res_def(key)
    new = battle._res_gain(player, key, amount)
    if once:
        battle.p_eff.setdefault("once_restore", []).append(key)
    if cd > 0:
        battle.cooldown[_cdk] = cd
    msg = f"⚡ 你使用药剂，{rd.get('name', key)} +{amount}({new}/{rd.get('max', '?')})！"
    nh = v.get("next_heal_pct")
    if nh:
        pn = float(nh)
        battle.p_eff["next_heal_up"] = pn
        msg += f" 下一次治疗技能效果 +{int(pn * 100)}%！"
    return msg


@register("restore_resource_full")
def eff_restore_resource_full(battle, player, value):
    """v130.2 熔核之心：立即充满核心资源 + 战损代价（penalty_pct% 全减伤，penalty_turns 回合）。
    effect_data {key, penalty_pct, penalty_turns}——全减伤负值 = 受击 +X%（battle.py reduce_all 槽消费）。"""
    v = _resolve(value, "restore_resource_full")
    key = v.get("key", "")
    if not _res_mine(battle, player, key):
        return "🧪 这份物资对你的职业没有效果！"
    rd = _item_res_def(key)
    cap = int(rd.get("max", 0))
    battle._res_gain(player, key, cap)  # 充满到 max（_res_gain 自带封顶）
    penalty = float(v.get("penalty_pct", 0.0) or 0)
    turns = max(1, int(v.get("penalty_turns", v.get("turns", 2)) or 2))
    if penalty > 0:
        # 战损交易：全减伤 -penalty%（负值 reduce_all → _damage_player 受击 +X%）
        battle.p_buffs["reduce_all"] = -penalty
        battle._reduce_all_left = turns
        return (f"🔥 熔核之心爆发！{rd.get('name', key)}充满({cap}/{cap})！"
                f"代价：{turns} 回合内 全减伤 -{int(penalty * 100)}%（受损加重）")
    return f"🔥 {rd.get('name', key)} 瞬间充满！({cap}/{cap})"


@register("resource_amp")
def eff_resource_amp(battle, player, value):
    """v130.2 资源增幅：特定触发下每次额外 +amount 资源（持续 turns 回合或 hits 次出手）。
    effect_data {key, amount, turns/hits, trigger}
    trigger ∈ {on_hit 受击 / 出手命中(hits 制) / on_heal 治疗 / regen 自然回复}，
    引擎侧触发点消费（battle.py _amp_resource 各站点；战斗外待用经 _init_resources 挂载）。
    沸血战血 turns+on_hit(受击)、影袭药水 hits+on_hit(出手命中)、迅捷之核 turns+regen、
    香薰圣烛 turns+on_heal（战斗外点燃 → 战前待用队列）。"""
    v = _resolve(value, "resource_amp")
    key = v.get("key", "")
    amount = int(v.get("amount", 0) or 0)
    trigger = v.get("trigger", "")
    turns = int(v.get("turns", 0) or 0)
    hits = int(v.get("hits", 0) or 0)
    if not key or amount <= 0 or not trigger:
        return "🧪 药剂效果配置异常，没有生效！"
    if not _res_mine(battle, player, key):
        return "🧪 这瓶药剂对你的职业没有效果！"
    amps = battle.p_eff.setdefault("amps", {})
    prev = amps.get(key) or {}
    amps[key] = {
        "key": key, "amount": amount, "trigger": trigger,
        "turns_left": max(int(prev.get("turns_left", 0) or 0), turns),
        "hits_left": max(int(prev.get("hits_left", 0) or 0), hits),
    }
    rd = _item_res_def(key)
    _tcn = {"on_hit": "受击/出手", "on_heal": "治疗", "regen": "自然回复"}.get(trigger, trigger)
    if hits:
        return f"⚡ 接下来 {hits} 次出手命中时 {rd.get('name', key)} +{amount}！"
    return f"⚡ {turns} 回合内（{_tcn}触发）{rd.get('name', key)} +{amount}！"


@register("mana_cost_down")
def eff_mana_cost_down(battle, player, value):
    """v130.2 元素亲和药剂：技能魔力消耗 ×(1-pct) 持续 turns 回合（基础法师纯蓝减耗）。
    effect_data {pct, turns}——p_buffs 回合计数 + p_eff 存 pct，battle.py 技能耗蓝结算消费。"""
    v = _resolve(value, "mana_cost_down")
    pct = float(v.get("pct", 0.0) or 0)
    turns = int(v.get("turns", 3) or 3)
    if pct <= 0:
        return "🧪 药剂效果配置异常，没有生效！"
    battle.p_buffs["mana_cost_down"] = max(int(battle.p_buffs.get("mana_cost_down", 0) or 0), turns)
    battle.p_eff["mana_cost_down"] = pct
    return f"🔮 元素亲和！技能魔力消耗 -{int(pct * 100)}%！({turns} 回合)"


@register("buff_phys_next")
def eff_buff_phys_next(battle, player, value):
    """v130.2 引气精华：下一次物理/气力技 伤害 +pct%（一次性，物理技能伤害结算消费）。
    effect_data {pct}——p_buffs 一次性标记 + p_eff 存 pct（同 next_atk_up 豁免回合递减）。"""
    v = _resolve(value, "buff_phys_next")
    pct = float(v.get("pct", 0.0) or 0)
    if pct <= 0:
        return "🧪 药剂效果配置异常，没有生效！"
    battle.p_buffs["buff_phys_next"] = 1
    battle.p_eff["buff_phys_next"] = pct
    return f"🥊 引气入体！下一次物理/气力技伤害 +{int(pct * 100)}%！"


@register("full_tension")
def eff_full_tension(battle, player, value):
    """v130.2 满弦烈酒：立即进入满弦状态 turns 回合（精力≥80 阈值视为已满足）。
    effect_data {turns}——守线·风行者系专属（风行者/疾风射手/疾风猎手），其余职业无效。
    p_buffs[\"full_tension\"] 供 _energy_high_crit 满弦判定短路。"""
    v = _resolve(value, "full_tension")
    turns = int(v.get("turns", 1) or 1)
    if not battle._is_branch_of(player, "风行者", "疾风射手", "疾风猎手"):
        return "🏹 满弦是守线·风行者专属状态，这瓶烈酒没有生效！"
    battle.p_buffs["full_tension"] = max(int(battle.p_buffs.get("full_tension", 0) or 0), turns)
    return f"🏹 满弦烈酒入喉，弓弦绷满！进入满弦状态 {turns} 回合！"


@register("battle_start_resource")
def eff_battle_start_resource(battle, player, value):
    """v130.2 战前资源预充（战前猛火餐/夜枭茶/澎湃烈酒）：战斗开始时预充资源。
    effect_data {key, amount, buff?{kind, pct, turns}}
    大宗走战前待用队列（item_templates 战斗外使用 → event_state prebattle_{qq_id} ，
    _init_resources 战斗初始化段注入）；此处为战斗内兜底分发（战斗中饮用按同口径立即预充）。"""
    v = _resolve(value, "battle_start_resource")
    key = v.get("key", "")
    amount = int(v.get("amount", 0) or 0)
    if not key or amount < 0:
        return "🧪 效果配置异常，没有生效！"
    if not _res_mine(battle, player, key):
        return "🧪 这杯饮品对你的职业没有效果！"
    msgs = []
    if amount > 0:
        rd = _item_res_def(key)
        new = battle._res_gain(player, key, amount)
        msgs.append(f"{rd.get('name', key)} +{amount}({new}/{rd.get('max', '?')})")
    bf = v.get("buff")
    if isinstance(bf, dict) and bf.get("kind") == "phys_up":
        _pct = float(bf.get("pct", 0.05) or 0)
        _t = int(bf.get("turns", 3) or 3)
        battle.p_buffs["phys_up"] = max(int(battle.p_buffs.get("phys_up", 0) or 0), _t)
        battle.p_eff["phys_up"] = max(float(battle.p_eff.get("phys_up", 0) or 0), _pct)
        msgs.append(f"物理伤害 +{int(_pct * 100)}%({_t} 回合)")
    if not msgs:
        return "🧪 效果未触发！"
    return "⚡ 战前准备生效！" + "、".join(msgs) + "！"
