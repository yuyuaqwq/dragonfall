# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - race_talent_display.py（v98.3：种族天赋展示格式化注册表）

消灭 commands/player.py races() 里的 if-elif 硬编码：
天赋数据只声明 key → 值，展示文案统一走本模块注册表。

扩展方式：
- 加天赋类型：data/races.py 加字段 + 本文件 register 一个格式化函数（~5 行）
- 函数签名：fn(v, name) -> str（name 为天赋显示名，来自 races talent_names）
"""
DISPLAY = {}


def register(key):
    """展示格式化注册装饰器。"""
    def deco(fn):
        DISPLAY[key] = fn
        return fn
    return deco


def format_talent(k, v, name):
    """返回天赋展示文本；未知 key 返回 None（不显示，与原 elif 链无 else 一致）。

    v105 P3(M01)：未知 key 打告警日志（原静默缺失）——races.py 新增天赋忘记
    注册展示文案时日志可见，防无声缺失。
    """
    fn = DISPLAY.get(k)
    if fn is None:
        import logging
        logging.getLogger("astrbot").warning(
            f"[dragonfall] 种族天赋无展示注册: {k}（data/races.py 新增天赋需在 "
            "race_talent_display.py 注册 format 函数）"
        )
        return None
    return fn(v, name)


# ================= 格式化实现（文案与原实现逐字一致） =================

@register("hp_mult")
def _d_hp_mult(v, name):
    pct = int((v - 1) * 100)
    # v113.6 描述补全：明确"最大生命"（此前只有 ±% 看不出是血量）
    return f"{'🔻' if v < 1 else ''}{name} 最大生命{pct:+d}%"


@register("growth_mult")
def _d_growth_mult(v, name):
    pct = int((v - 1) * 100)
    # v113.6 描述补全：明确"全属性成长"
    return f"{'🔻' if v < 1 else ''}{name} 全属性成长{pct:+d}%"


@register("spd_mult")
def _d_spd_mult(v, name):
    pct = int((v - 1) * 100)
    # v113.6 描述补全：明确"先手速度"
    return f"{'🔻' if v < 1 else ''}{name} 先手速度{pct:+d}%"


@register("crit_add")
def _d_crit_add(v, name):
    return f"{name} 暴击+{int(v*100)}%"


@register("phys_reduce")
def _d_phys_reduce(v, name):
    if v > 0:
        # v113.6 描述补全：明确"受物理伤害"
        return f"{name} 受物理伤害-{int(v*100)}%"
    return f"🔻{name} 受物理伤害+{int(-v*100)}%"


@register("magic_reduce")
def _d_magic_reduce(v, name):
    if v > 0:
        # v113.6 描述补全：明确"受魔法伤害"
        return f"{name} 受魔法伤害-{int(v*100)}%"
    return f"🔻{name} 受魔法伤害+{int(-v*100)}%"


@register("heal_received")
def _d_heal_received(v, name):
    if v > 0:
        return f"{name} 受疗+{int(v*100)}%"
    return f"🔻{name} 受疗{int(v*100)}%"


@register("berserk_hp")
def _d_berserk_hp(v, name):
    # v105 P3(M01)：倍率取自 battle.RACE_BERSERK_MULT（原硬编码 +20%，调 battle 倍率会文案失配）
    from ..battle import RACE_BERSERK_MULT
    pct = round((RACE_BERSERK_MULT - 1) * 100)
    return f"{name} 残血攻＋{pct}%"


@register("timid_hp")
def _d_timid_hp(v, name):
    # v105 P3(M01)：倍率取自 battle.RACE_TIMID_MULT（原硬编码 -10%，调 battle 倍率会文案失配）
    from ..battle import RACE_TIMID_MULT
    pct = round((1 - RACE_TIMID_MULT) * 100)
    return f"🔻{name} 残血攻－{pct}%"


@register("first_hit")
def _d_first_hit(v, name):
    return f"{name} 首击+{int(v*100)}%"


@register("learn_discount")
def _d_learn_discount(v, name):
    return f"{name} 学习-{int(v*100)}%"


@register("gold_bonus")
def _d_gold_bonus(v, name):
    return f"{name} 金币+{int(v*100)}%"


# v110 审计修复：补 v106.2/3 新增 5 条正面天赋的展示注册（此前缺注册 →
# format_talent 返 None → 『种族』命令静默不显示，仅 stderr 告警）
@register("exp_bonus")
def _d_exp_bonus(v, name):
    return f"{name} 经验+{int(v*100)}%"


@register("crit_dmg")
def _d_crit_dmg(v, name):
    return f"{name} 暴伤+{int(v*100)}%"


@register("block")
def _d_block(v, name):
    return f"{name} 格挡+{int(v*100)}%"


@register("lifesteal")
def _d_lifesteal(v, name):
    return f"{name} 吸血+{int(v*100)}%"


@register("luck")
def _d_luck(v, name):
    return f"{name} 幸运+{int(v*100)}%"


@register("item_effect")
def _d_item_effect(v, name):
    return f"{name} 消耗品+{int(v*100)}%"


@register("craft_bonus")
def _d_craft_bonus(v, name):
    return f"{name} 锻造经验+{int(v*100)}%"


@register("explore_item")
def _d_explore_item(v, name):
    return f"{name} 探索物品+{int(v*100)}%"
