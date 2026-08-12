# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - food_effects.py（v101.28e：料理效果注册表）

v101.28c 词条料理借用装备词条机制（affix 字段 + _equip_affix_ids 合并），
鱼鱼拍板（2026-08-12）：食物效果独立成体系，不复用装备词条——
- 数据字段 affix → food_effect
- 触发：p_food_effects 列表 + 本文件三个注册表（HIT/TAKEN/TURN_START）
- 行为与 v101.28c 对齐（数值已在 28c 平衡），但实现完全独立，
  后续食物可自由扩展装备没有的专属效果（加 id + 注册函数即可）

注册表：
- FOOD_HIT_EFFECTS          攻击命中效果 fn(battle, player, dmg, logs)
- FOOD_TAKEN_EFFECTS        受击效果 fn(battle, player, ctx, logs)（ctx 同 affix TAKEN）
- FOOD_TURN_START_EFFECTS   回合开始效果 fn(battle, player, logs)

伤害倍率类（execute/precise/龙语印记层数）由 battle._affix_dmg_mult 的
p_food_effects 分支消费；护盾类（shield）由 _do_use_item 特判走 _add_shield。
"""
import random


def register(registry, key):
    """注册装饰器。"""
    def deco(fn):
        registry[key] = fn
        return fn
    return deco


FOOD_HIT_EFFECTS = {}
FOOD_TAKEN_EFFECTS = {}
FOOD_TURN_START_EFFECTS = {}


# ================= 1. 攻击命中效果（_food_on_hit） =================

@register(FOOD_HIT_EFFECTS, "lifesteal")
def _f_h_lifesteal(battle, player, dmg, logs):
    """蛇羹：每次攻击回复伤害 8% 生命"""
    if dmg > 0:
        heal = int(dmg * 0.08)
        player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
        logs.append(f"🩸 吸血：回复 {heal} 点生命！")


@register(FOOD_HIT_EFFECTS, "bleed")
def _f_h_bleed(battle, player, dmg, logs):
    """烬火辣椒：20% 使目标流血（每回合 5% 生命，3 回合）"""
    if random.random() < 0.20:
        battle.e_buffs["bleed"] = max(battle.e_buffs.get("bleed", 0), 3)
        logs.append("🩸 流血！敌人伤口裂开，将持续失血！")


@register(FOOD_HIT_EFFECTS, "armor_break")
def _f_h_armor_break(battle, player, dmg, logs):
    """蘑菇汤：25% 降低目标防御 15%（2 回合）"""
    if random.random() < 0.25:
        battle.e_buffs["def_down"] = max(battle.e_buffs.get("def_down", 0), 2)
        battle.e_buffs["_armor_break_pct"] = 0.15
        logs.append("🛡️ 破甲！敌人防御下降 15%！")


@register(FOOD_HIT_EFFECTS, "combo")
def _f_h_combo(battle, player, dmg, logs):
    """鹰蛋：15% 追加一次 50% 伤害"""
    if random.random() < 0.15:
        cd = int(dmg * 0.50)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - cd)
        logs.append(f"⚡ 连击！追加 {cd} 点伤害！")


@register(FOOD_HIT_EFFECTS, "dragon_tongue")
def _f_h_dragon_tongue(battle, player, dmg, logs):
    """龙蛋煎饼：攻击叠龙语印记（每层 +2% 伤害，上限 5）"""
    battle.mech_stacks["dragon_mark"] = min(5, int(battle.mech_stacks.get("dragon_mark", 0) or 0) + 1)
    logs.append(f"🐉 龙语印记叠加！({battle.mech_stacks['dragon_mark']} 层，每层＋2% 伤害)")


@register(FOOD_HIT_EFFECTS, "element_fire")
def _f_h_element_fire(battle, player, dmg, logs):
    """灰烬烤饼：攻击附加 5% 火属性伤害"""
    ed = max(1, int(dmg * 0.05))
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - ed)
    logs.append(f"🔥 火焰附加 {ed} 点伤害！")


@register(FOOD_HIT_EFFECTS, "element_ice")
def _f_h_element_ice(battle, player, dmg, logs):
    """冰霜浆果：攻击附加 5% 冰属性伤害 + 减速"""
    ed = max(1, int(dmg * 0.05))
    battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - ed)
    logs.append(f"❄️ 冰霜附加 {ed} 点伤害！")
    battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), 2)
    logs.append("❄️ 减速！")


@register(FOOD_HIT_EFFECTS, "pierce")
def _f_h_pierce(battle, player, dmg, logs):
    """雪狼肉排：20% 无视防御追加伤害（60% 攻击）"""
    if random.random() < 0.20:
        from ..engine import calc_damage
        pst = battle._player_stats(player)
        pd = calc_damage(int(pst.get("atk", 0) * 0.6), 0)
        if pd > 0:
            battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - pd)
            logs.append(f"🏹 贯穿！无视防御 {pd} 点伤害！")


@register(FOOD_HIT_EFFECTS, "charge")
def _f_h_charge(battle, player, dmg, logs):
    """皇家烤肉：10% 造成 150% 伤害（追加 50%）"""
    if random.random() < 0.10:
        cd = int(dmg * 0.50)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - cd)
        logs.append(f"💪 蓄力爆发！追加 {cd} 点伤害！")


@register(FOOD_HIT_EFFECTS, "static")
def _f_h_static(battle, player, dmg, logs):
    """雷雨藤烤串（v102.3）：静电麻痹——攻击 20% 令敌方减速（2 回合）"""
    if random.random() < 0.20 and battle.enemy.get("hp", 0) > 0:
        battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), 2)
        logs.append(f"⚡ 静电麻痹！【{battle.enemy.get('name', '敌人')}】速度下降！")


# ================= 2. 受击效果（_food_on_taken） =================

@register(FOOD_TAKEN_EFFECTS, "counter")
def _f_t_counter(battle, player, ctx, logs):
    """狼肉干：20% 反击 60% 伤害"""
    if random.random() < 0.20 and battle.enemy.get("hp", 0) > 0:
        from ..engine import calc_damage
        pst2 = battle._player_stats(player)
        est2 = battle._enemy_stats()
        cd = calc_damage(int(pst2.get("atk", 0) * 0.6), est2.get("def", 0))
        if cd > 0:
            battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - cd)
            logs.append(f"⚔️ 反击！对【{battle.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")


@register(FOOD_TAKEN_EFFECTS, "thorns")
def _f_t_thorns(battle, player, ctx, logs):
    """鹿奶干酪：10% 反弹 30% 伤害（基于原始 dmg）"""
    if random.random() < 0.10 and battle.enemy.get("hp", 0) > 0:
        rd = int(ctx["dmg"] * 0.30)
        battle.enemy["hp"] = max(0, battle.enemy.get("hp", 0) - rd)
        logs.append(f"🌵 反伤！反弹 {rd} 点伤害！")


@register(FOOD_TAKEN_EFFECTS, "aurora_guard")
def _f_t_aurora_guard(battle, player, ctx, logs):
    """极光花蜜（v102.3）：极光庇护——本场战斗受击伤害 -15%（稳定减伤，改 ctx['out']）"""
    if ctx.get("out", 0) > 0:
        reduced = int(ctx["out"] * 0.15)
        ctx["out"] = max(1, ctx["out"] - reduced)
        logs.append(f"✨ 极光庇护！伤害减免 {reduced} 点！")


# ================= 3. 回合开始效果（_food_turn_start） =================

@register(FOOD_TURN_START_EFFECTS, "regen")
def _f_ts_regen(battle, player, logs):
    """树蜜糖：每回合回复 1% 生命"""
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * 0.01)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌿 回春生效，回复 {heal} 点生命！")


@register(FOOD_TURN_START_EFFECTS, "meditate")
def _f_ts_meditate(battle, player, logs):
    """月光饼：每回合回复 1% 魔力"""
    if player.get("mp", 0) < player.get("max_mp", 1):
        heal = int(player.get("max_mp", player.get("mp", 1)) * 0.01)
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
        logs.append(f"🧘 冥想生效，回复 {heal} 点魔力！")


@register(FOOD_TURN_START_EFFECTS, "dawn_crown")
def _f_ts_dawn_crown(battle, player, logs):
    """御膳汤：每回合回复 2% 生命"""
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * 0.02)
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🌅 晨曦祝福生效，回复 {heal} 点生命！")


# ================= 效果显示名（吃下播报/物品详情用） =================
FOOD_EFFECT_NAMES = {
    "lifesteal": "吸血", "shield": "护盾", "bleed": "流血", "counter": "反击",
    "armor_break": "破甲", "dragon_tongue": "龙语印记", "combo": "连击",
    "element_ice": "元素·冰", "regen": "回春", "meditate": "冥想",
    "thorns": "反伤", "precise": "精准", "execute": "处决", "pierce": "贯穿",
    "element_fire": "元素·火", "charge": "蓄力", "dawn_crown": "晨曦祝福",
    # v102.3 生活技能差异化新效果
    "aurora_guard": "极光庇护", "static": "静电麻痹",
}
