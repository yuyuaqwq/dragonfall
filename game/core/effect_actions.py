# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - effect_actions.py（v180-D P2：共享效果动作）

效果系统统一（鱼鱼 2026-09-06 拍板）——把"效果动作"（成功触发后做什么）
抽成共享函数，来源域（装备词条 affix / 食物 food）各自保留触发判断，但动作
只此一份，不再 affix/food 复制粘贴。

铁律：
- 本文件函数只做"动作"，不判来源、不查来源数据表
- 数值由调用方传入（affix 读 AFFIXES 表、food 从声明读）——动作不存数值
- 返回 None（改 battle/player 状态 + 追加 logs）
"""
import random as _random


def action_regen_hp(battle, player, logs, *, pct=0.01, label="回春"):
    """回复 玩家 max_hp × pct 生命（原 affix regen / food 树蜜糖）。"""
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * float(pct))
        battle._heal_actor(player, heal, logs)  # v180E 统一落地
        logs.append(f"🌿 {label}生效，回复 {heal} 点生命！")


def action_regen_mp(battle, player, logs, *, pct=0.01, label="冥想"):
    """回复 玩家 max_mp × pct 魔力（原 affix meditate / food 月光饼）。"""
    if player.get("mp", 0) < player.get("max_mp", 1):
        heal = int(player.get("max_mp", player.get("mp", 1)) * float(pct))
        player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + heal)
        logs.append(f"🧘 {label}生效，回复 {heal} 点魔力！")


def action_dot(battle, logs, *, key="bleed", stacks=3, max_n=None, label="流血"):
    """目标级持续伤害：叠 debuffs[key] 层（原 affix bleed / food 烬火辣椒）。

    stacks=每次触发叠层数（兼上限，除非 max_n 指定）；max_n=None 用 stacks。
    """
    deb = battle.enemy.setdefault("debuffs", {})
    cur = deb.get(key) or {"n": 0, "mult": 1.0}
    cap = int(max_n if max_n is not None else stacks)
    cur["n"] = min(cap, int(cur.get("n", 0) or 0) + int(stacks))
    deb[key] = cur
    logs.append(f"🩸 {label}！敌人伤口裂开，将持续失血！")


def action_def_down(battle, logs, *, turns=2, pct=0.15, label="破甲"):
    """敌方防御削减：def_down 刻数 + _armor_break_pct（原 affix armor_break / food 蘑菇汤）。"""
    battle.e_buffs["def_down"] = max(int(battle.e_buffs.get("def_down", 0) or 0), int(turns))
    battle.e_buffs["_armor_break_pct"] = float(pct)
    logs.append(f"🛡️ {label}！敌人防御下降 {int(pct * 100)}%！")


def action_mark(battle, player, logs, *, key="dragon_mark", max_n=5, label="龙语印记",
                mark_pct=None):
    """玩家叠印记层（原 affix dragon_tongue / food 龙蛋煎饼）。

    mark_pct 仅供文案；层数上限 max_n。
    """
    player.setdefault('stacks', {})[key] = min(int(max_n), int(player.setdefault('stacks', {}).get(key, 0) or 0) + 1)
    logs.append(f"🐉 {label}叠加！({player.setdefault('stacks', {})[key]} 层"
                + (f"，每层＋{int(mark_pct * 100)}% 伤害)" if mark_pct else ")"))


# ============================================================
# 追加伤害类（combo/charge/element/pierce 共用底座）
# ============================================================
def _bonus_dmg_apply(battle, player, cd, logs, tag, name):
    """追加伤害落地：Boss 护盾过滤 → 主结算（v104 M02 P1-5 统一）。

    food 侧原实现有此过滤、affix 侧漏了（词条 combo/charge 附加伤害绕过 Boss
    护盾 = bug）——统一收口到本动作后两侧一致。
    """
    if cd <= 0:
        return 0
    try:
        cd = battle._boss_dmg_filter(cd, player, logs)
    except Exception:
        pass
    battle._deal_damage(cd, logs)
    logs.append(f"{tag} {name}！追加 {cd} 点伤害！")
    return cd


def action_bonus_pct(battle, player, dmg, logs, *, pct=0.50, tag="⚡", name="连击"):
    """按本次伤害 dmg × pct 追加一次伤害（原 affix combo/charge / food 鹰蛋/皇家烤肉）。

    combo(连击)与 charge(蓄力爆发)动作同构，仅文案/标签不同——统一本动作。
    """
    if dmg <= 0:
        return 0
    cd = int(dmg * float(pct))
    return _bonus_dmg_apply(battle, player, cd, logs, tag, name)


def action_element_dmg(battle, player, dmg, logs, *, pct=0.05, tag="🔥", name="火焰附加",
                       slow_turns=0, label="减速"):
    """攻击附加 dmg × pct 元素伤害（原 affix/food element_fire / element_ice）。

    slow_turns>0 时额外挂敌方减速（冰）。
    """
    if dmg <= 0:
        return 0
    ed = max(1, int(dmg * float(pct)))
    _bonus_dmg_apply(battle, player, ed, logs, tag, name)
    if slow_turns > 0:
        battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), int(slow_turns))
        logs.append(f"❄️ {label}！")
    return ed


def action_pierce_dmg(battle, player, logs, *, atk_pct=0.60, tag="🏹", name="贯穿"):
    """无视防御追加伤害（原 affix/food pierce）。

    按玩家 atk × atk_pct 计算，防御=0 直伤（无视防御语义）。
    """
    from ..engine import calc_damage
    pst = battle._player_stats(player)
    pd = calc_damage(int(pst.get("atk", 0) * float(atk_pct)), 0)
    if pd <= 0:
        return 0
    return _bonus_dmg_apply(battle, player, pd, logs, tag, name)


def action_counter(battle, player, logs, *, atk_pct=0.60, tag="⚔️", name="反击"):
    """受击反击：按玩家 atk × atk_pct 反打敌方（原 affix/food counter）。

    触发条件（敌方存活/概率）由来源 handler 判定；此处只做反击动作。
    """
    if not battle.enemy.get("hp", 0) or battle.enemy.get("hp", 0) <= 0:
        return 0
    from ..engine import calc_damage
    pst = battle._player_stats(player)
    est = battle._enemy_stats()
    cd = calc_damage(int(pst.get("atk", 0) * float(atk_pct)), est.get("def", 0))
    if cd <= 0:
        return 0
    try:
        cd = battle._boss_dmg_filter(cd, player, logs)
    except Exception:
        pass
    battle._deal_damage(cd, logs)
    logs.append(f"{tag} {name}！对【{battle.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")
    return cd


def action_lifesteal(battle, player, dmg, logs, *, heal_pct=0.08, label="吸血"):
    """攻击吸血：回复 dmg × heal_pct 生命（原 food lifesteal / 词条吸血通用）。"""
    if dmg <= 0:
        return 0
    heal = max(1, int(dmg * float(heal_pct)))
    battle._heal_actor(player, heal, logs)  # v180E 统一落地
    logs.append(f"🩸 {label}：回复 {heal} 点生命！")
    return heal
