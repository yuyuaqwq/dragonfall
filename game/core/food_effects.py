# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - food_effects.py（v101.28e：料理效果注册表）

v101.28c 词条料理借用装备词条机制（affix 字段 + _equip_affix_ids 合并），
鱼鱼拍板（2026-08-12）：食物效果独立成体系，不复用装备词条——
- 数据字段 affix → food_effect
- 触发：p_food_effects 列表 + 本文件三个注册表（HIT/TAKEN/TURN_START）
- 行为与 v101.28c 对齐（数值已在 28c 平衡），但实现完全独立，
  后续食物可自由扩展装备没有的专属效果（加 id + 注册函数即可）

注册表：
- FOOD_HIT_EFFECTS          攻击命中效果 fn(battle, player, dmg, logs)
- FOOD_TAKEN_EFFECTS        受击效果 fn(battle, player, ctx, logs)（ctx 同 affix TAKEN）
- FOOD_TURN_START_EFFECTS   刻开始效果 fn(battle, player, logs)

伤害倍率类（execute/precise/龙语印记层数）由 battle._affix_dmg_mult 的
p_food_effects 分支消费；护盾类（shield）由 _do_use_item 特判走 _add_shield。

v180-D P2（2026-09-06 鱼鱼拍板效果系统统一）：与装备词条同语义的效果（bleed/
armor_break/combo/charge/element_fire/element_ice/pierce/counter/regen/meditate）
动作收敛到 core/effect_actions.py 共享执行器——本文件只保留"触发判断 + 数值"，
不再复制动作实现。效果动作 = 唯一一份代码，任何来源可复用。
"""
import random

# v180F 清2b：数值权威下沉 game/data/food_effect_data.py（原 handler 全部硬编码）
from ..data.food_effect_data import FOOD_EFFECT_PARAMS as _FPARAMS


def _fp(key, field, default=0.0):
    """读食物效果参数（数据驱动铁律：数值权威在 food_effect_data.py）。"""
    try:
        return (_FPARAMS.get(key) or {}).get(field, default)
    except Exception:
        return default


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
        from .effect_actions import action_lifesteal
        action_lifesteal(battle, player, dmg, logs, heal_pct=float(_fp("lifesteal", "pct", 0.08)), label="吸血")


@register(FOOD_HIT_EFFECTS, "bleed")
def _f_h_bleed(battle, player, dmg, logs):
    """烬火辣椒：20% 使目标流血（每刻 5% 生命，3 刻）"""
    if random.random() < float(_fp("bleed", "chance", 0.20)):
        from .effect_actions import action_dot
        action_dot(battle, logs, key="bleed", stacks=int(_fp("bleed", "stacks", 3)), max_n=int(_fp("bleed", "max_n", 3)), target=battle.enemy)  # 烬火辣椒 3 层


@register(FOOD_HIT_EFFECTS, "armor_break")
def _f_h_armor_break(battle, player, dmg, logs):
    """蘑菇汤：25% 降低目标防御 15%（2 刻）"""
    if random.random() < float(_fp("armor_break", "chance", 0.25)):
        from .effect_actions import action_def_down
        action_def_down(battle, logs, turns=int(_fp("armor_break", "turns", 2)), pct=float(_fp("armor_break", "pct", 0.15)), target=battle.enemy)


@register(FOOD_HIT_EFFECTS, "combo")
def _f_h_combo(battle, player, dmg, logs):
    """鹰蛋：15% 追加一次 50% 伤害"""
    if random.random() < float(_fp("combo", "chance", 0.15)):
        from .effect_actions import action_bonus_pct
        action_bonus_pct(battle, player, dmg, logs, pct=float(_fp("combo", "pct", 0.50)), tag="⚡", name="连击", target=battle.enemy)


@register(FOOD_HIT_EFFECTS, "dragon_tongue")
def _f_h_dragon_tongue(battle, player, dmg, logs):
    """龙蛋煎饼：攻击叠龙语印记（每层 +2% 伤害，上限 5）"""
    from .effect_actions import action_mark
    action_mark(battle, player, logs, key="dragon_mark", max_n=int(_fp("dragon_tongue", "max_n", 5)), mark_pct=float(_fp("dragon_tongue", "pct", 0.02)))


@register(FOOD_HIT_EFFECTS, "element_fire")
def _f_h_element_fire(battle, player, dmg, logs):
    """灰烬烤饼：攻击附加 5% 火属性伤害"""
    from .effect_actions import action_element_dmg
    action_element_dmg(battle, player, dmg, logs, pct=float(_fp("element_fire", "pct", 0.05)), tag="🔥", name="火焰附加", target=battle.enemy)


@register(FOOD_HIT_EFFECTS, "element_ice")
def _f_h_element_ice(battle, player, dmg, logs):
    """冰霜浆果：攻击附加 5% 冰属性伤害 + 减速"""
    from .effect_actions import action_element_dmg
    action_element_dmg(battle, player, dmg, logs, pct=float(_fp("element_ice", "pct", 0.05)), tag="❄️", name="冰霜附加",
                       slow_turns=int(_fp("element_ice", "slow_turns", 2)), target=battle.enemy)


@register(FOOD_HIT_EFFECTS, "pierce")
def _f_h_pierce(battle, player, dmg, logs):
    """雪狼肉排：20% 无视防御追加伤害（60% 攻击）"""
    if random.random() < float(_fp("pierce", "chance", 0.20)):
        from .effect_actions import action_pierce_dmg
        action_pierce_dmg(battle, player, logs, atk_pct=float(_fp("pierce", "atk_pct", 0.60)), target=battle.enemy)


@register(FOOD_HIT_EFFECTS, "charge")
def _f_h_charge(battle, player, dmg, logs):
    """皇家烤肉：10% 造成 150% 伤害（追加 50%）"""
    if random.random() < float(_fp("charge", "chance", 0.10)):
        from .effect_actions import action_bonus_pct
        action_bonus_pct(battle, player, dmg, logs, pct=float(_fp("charge", "pct", 0.50)), tag="💪", name="蓄力爆发", target=battle.enemy)


@register(FOOD_HIT_EFFECTS, "static")
def _f_h_static(battle, player, dmg, logs):
    """雷雨藤烤串（v102.3）：静电麻痹——攻击 20% 令敌方减速（2 刻）"""
    if random.random() < float(_fp("static", "chance", 0.20)) and battle.enemy.get("hp", 0) > 0:
        battle._actor_buffs(battle._hit_tgt())["spd_down"] = max(battle._actor_buffs(battle._hit_tgt()).get("spd_down", 0), int(_fp("static", "turns", 2)))
        logs.append(f"⚡ 静电麻痹！【{battle.enemy.get('name', '敌人')}】速度下降！")


# ================= 2. 受击效果（_food_on_taken） =================

@register(FOOD_TAKEN_EFFECTS, "counter")
def _f_t_counter(battle, player, ctx, logs):
    """狼肉干：20% 反击 60% 伤害"""
    if random.random() < float(_fp("counter", "chance", 0.20)) and battle.enemy.get("hp", 0) > 0:
        from .effect_actions import action_counter
        action_counter(battle, player, logs, atk_pct=float(_fp("counter", "atk_pct", 0.60)), target=battle.enemy)


@register(FOOD_TAKEN_EFFECTS, "thorns")
def _f_t_thorns(battle, player, ctx, logs):
    """鹿奶干酪：10% 反弹 30% 伤害（基于原始 dmg）"""
    if random.random() < float(_fp("thorns", "chance", 0.10)) and battle.enemy.get("hp", 0) > 0:
        rd = int(ctx["dmg"] * float(_fp("thorns", "pct", 0.30)))
        rd = battle._boss_dmg_filter(rd, player, logs)  # v104 M02 P1-5：反伤走主结算路径
        battle._deal_damage(rd, logs)
        logs.append(f"🌵 反伤！反弹 {rd} 点伤害！")


@register(FOOD_TAKEN_EFFECTS, "aurora_guard")
def _f_t_aurora_guard(battle, player, ctx, logs):
    """极光花蜜（v102.3）：极光庇护——本场战斗受击伤害 -15%（稳定减伤，改 ctx['out']）"""
    if ctx.get("out", 0) > 0:
        reduced = int(ctx["out"] * float(_fp("aurora_guard", "pct", 0.15)))
        ctx["out"] = max(1, ctx["out"] - reduced)
        logs.append(f"✨ 极光庇护！伤害减免 {reduced} 点！")


# ================= 3. 刻开始效果（_food_turn_start） =================

@register(FOOD_TURN_START_EFFECTS, "regen")
def _f_ts_regen(battle, player, logs):
    """树蜜糖：每刻回复 1% 生命"""
    from .effect_actions import action_regen_hp
    action_regen_hp(battle, player, logs, pct=float(_fp("regen", "pct", 0.01)), label="回春")


@register(FOOD_TURN_START_EFFECTS, "meditate")
def _f_ts_meditate(battle, player, logs):
    """月光饼：每刻回复 1% 魔力"""
    from .effect_actions import action_regen_mp
    action_regen_mp(battle, player, logs, pct=float(_fp("meditate", "pct", 0.01)), label="冥想")


@register(FOOD_TURN_START_EFFECTS, "dawn_crown")
def _f_ts_dawn_crown(battle, player, logs):
    """御膳汤：每刻回复 2% 生命"""
    from .effect_actions import action_regen_hp
    action_regen_hp(battle, player, logs, pct=float(_fp("dawn_crown", "pct", 0.02)), label="晨曦祝福")


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
