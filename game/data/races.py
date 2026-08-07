# -*- coding: utf-8 -*-
"""《奥兰迪亚：余烬纪年》数据层 - races.py（阶段九：种族系统，08 章）

6 种族 × 2 正 + 1 负天赋（有得有失，净强度≈不变）。
天赋字段语义（按消费端分组）：
- stat 型（engine.player_race_stats 结算，进面板/战斗属性）：
    hp_mult      最大生命倍率（月缺 0.95 / 坚韧体魄 1.08）
    growth_mult  全属性成长倍率（凡人之躯 0.98，只影响基础成长）
    spd_mult     先手/速度倍率（磐石步履 0.95）
    crit_add     暴击率加点（月之优雅 +0.08）
- 战斗型（battle.py 结算）：
    phys_reduce   受物理伤害 -x（石肤 0.10）
    magic_reduce  受魔法伤害 -x（龙鳞 0.10；鲁莽之心 -0.05 为负=增伤）
    heal_received 接受治疗 +x（圣光亲和 0.10；孤傲之血 -0.10）
    berserk_hp    残血（HP 低于该比例）攻击 +x（无畏 0.30 → +20%）
    timid_hp      残血（HP 低于该比例）攻击 -x（怯战 0.30 → -10%）
    first_hit     每场战斗首次攻击 +x（龙之吐息 0.15）
- 命令层（economy/player/combat 结算）：
    learn_discount 学习技能消耗技能点 -x（多才多艺 0.08）
    craft_bonus    锻造成功率 +x（熔炉之心 0.10）
    gold_bonus     金币掉落 +x（幸运儿 0.15）
    item_effect    消耗品效果 +x（灵巧双手 0.10）
    explore_item   探索获得物品概率 +x（森林之友 0.10）
"""
RACES = {
    "human": {
        "name": "人类", "icon": "🧑",
        "desc": "均衡·多面手。没有天赋就是最好的天赋——什么都能学。",
        "race_neg": True,
        "talents": {
            "heal_received": 0.10,     # 圣光亲和：受疗 +10%
            "learn_discount": 0.08,    # 多才多艺：学习技能点 -8%
            "growth_mult": 0.98,       # 🔻 凡人之躯：全属性成长 -2%
        },
        "talent_names": {"heal_received": "圣光亲和", "learn_discount": "多才多艺", "growth_mult": "凡人之躯"},
    },
    "elf": {
        "name": "银月精灵", "icon": "🧝",
        "desc": "敏捷·魔法。月光照过的箭矢，永远比风更快。",
        "race_neg": True,
        "talents": {
            "crit_add": 0.08,          # 月之优雅：暴击 +8%
            "explore_item": 0.10,      # 森林之友：探索物品 +10%
            "hp_mult": 0.95,           # 🔻 月缺：最大 HP -5%
        },
        "talent_names": {"crit_add": "月之优雅", "explore_item": "森林之友", "hp_mult": "月缺"},
    },
    "dwarf": {
        "name": "矮人", "icon": "⛏️",
        "desc": "力量·体质。岩石般的脊梁，比岩石更硬的脾气。",
        "race_neg": True,
        "talents": {
            "phys_reduce": 0.10,       # 石肤：受物理伤害 -10%
            "craft_bonus": 0.10,       # 熔炉之心：锻造成功率 +10%
            "spd_mult": 0.95,          # 🔻 磐石步履：先手 -5%
        },
        "talent_names": {"phys_reduce": "石肤", "craft_bonus": "熔炉之心", "spd_mult": "磐石步履"},
    },
    "orc": {
        "name": "兽人", "icon": "👹",
        "desc": "力量·耐力。活着就是战斗，战斗就是荣耀。",
        "race_neg": True,
        "talents": {
            "berserk_hp": 0.30,        # 无畏：HP<30% 攻击 +20%
            "hp_mult": 1.08,           # 坚韧体魄：最大 HP +8%
            "magic_reduce": -0.05,     # 🔻 鲁莽之心：受魔法伤害 +5%
        },
        "talent_names": {"berserk_hp": "无畏", "hp_mult": "坚韧体魄", "magic_reduce": "鲁莽之心"},
    },
    "halfling": {
        "name": "半身人", "icon": "🍀",
        "desc": "敏捷·幸运。锅里有热汤，兜里有金币，就是最富足的人。",
        "race_neg": True,
        "talents": {
            "gold_bonus": 0.15,        # 幸运儿：金币掉落 +15%
            "item_effect": 0.10,       # 灵巧双手：消耗品效果 +10%
            "timid_hp": 0.30,          # 🔻 怯战：HP<30% 攻击 -10%
        },
        "talent_names": {"gold_bonus": "幸运儿", "item_effect": "灵巧双手", "timid_hp": "怯战"},
    },
    "dragonborn": {
        "name": "龙裔", "icon": "🐉",
        "desc": "力量·魔法抗性。龙骨山脉记得一切，我们记得。",
        "race_neg": True,
        "talents": {
            "magic_reduce": 0.10,      # 龙鳞：受魔法伤害 -10%
            "first_hit": 0.15,         # 龙之吐息：每场首击 +15%
            "heal_received": -0.10,    # 🔻 孤傲之血：受疗 -10%
        },
        "talent_names": {"magic_reduce": "龙鳞", "first_hit": "龙之吐息", "heal_received": "孤傲之血"},
    },
}
