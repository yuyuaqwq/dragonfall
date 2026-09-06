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
    craft_bonus    锻造经验 +x（熔炉之心 0.10，向上取整至少 +1）
    gold_bonus     金币掉落 +x（幸运儿 0.15）
    item_effect    消耗品效果 +x（灵巧双手 0.10）
    explore_item   探索获得物品概率 +x（森林之友 0.10）

v181.D 种族机制数据下沉（P1-D，battle.py 后门清除）：
- RACE_ATTACK_MULT：种族残血攻/首击倍率表（原 battle.py 模块级 RACE_BERSERK_MULT=1.20 /
  RACE_TIMID_MULT=0.90 硬编码；展示侧 race_talent_display 曾从 battle 反向 import，现一并改读本表）
- RACES[race].talents 新增展示用键（battle._race_attack_mult 只读 talent 值 + 本表数值/标签，
  不再内联任何数值）：
    berserk_tag   无畏残血攻标签（"🔥无畏"）
    timid_tag     怯战残血攻标签（"😰怯战"）
    first_hit_tag 龙之吐息首击标签（"🐲龙之吐息x{mult}"，mult 由 battle 按 1+first_hit 现算，
                  展示名与引擎标签同源本表）
- UNDEAD_KEYWORDS：亡灵系关键词单源（原 battle.py 模块常量，注释自认与 achievements.py
  ach_undead100 cond.keywords 双处同步——现统一由本文件声明，battle._undead_count 读本表）
"""
RACES = {
    "human": {
        "name": "人类", "icon": "🧑",
        "desc": "均衡·多面手。没有天赋就是最好的天赋——什么都能学。",
        "talents": {
            # v134.1 人类天赋重做（鱼鱼拍板 2026-08-28，三次迭代）：
            #   ① 旧 learn_discount 0.08（技能点-8%）取整后每技能仅省 1 点，体感≈0
            #   ② 改学习-1/升级-1 → 鱼鱼说"每次学习都-1太离谱了，削一下"
            #   ③ 最终：首次升级某技能返还 1 技能点（first_upgrade_refund=1，player.skill_upgrade 特判）
            #      副业亲和保留：副业经验 +10%（professions.add_prof_exp 特判）
            "first_upgrade_refund": 1,      # 博学者：首次升级技能返还 1 技能点（每技能一次）
            "prof_bonus": 0.10,             # v134.1 副业亲和：副业经验 +10%（professions.add_prof_exp 特判）
            "exp_bonus": 0.05,              # v106.2 勤学：战斗经验 +5%（替换原受疗+10%，贴合多面手成长设定）
            "growth_mult": 0.98,            # 🔻 凡人之躯：全属性成长 -2%
        },
        "talent_names": {"first_upgrade_refund": "博学者", "prof_bonus": "副业亲和", "exp_bonus": "勤学", "growth_mult": "凡人之躯"},
    },
    "elf": {
        "name": "银月精灵", "icon": "🧝",
        "desc": "敏捷·魔法。月光照过的箭矢，永远比风更快。",
        "talents": {
            "crit_add": 0.08,          # 月之优雅：暴击 +8%
            "crit_dmg": 0.10,          # v106.3 月华利刃：暴击伤害 +10%（月光既准且狠）
            "explore_item": 0.10,      # 森林之友：探索物品 +10%
            "hp_mult": 0.95,           # 🔻 月缺：最大 HP -5%
        },
        "talent_names": {"crit_add": "月之优雅", "crit_dmg": "月华利刃", "explore_item": "森林之友", "hp_mult": "月缺"},
    },
    "dwarf": {
        "name": "矮人", "icon": "⛏️",
        "desc": "力量·体质。岩石般的脊梁，比岩石更硬的脾气。",
        "talents": {
            "phys_reduce": 0.10,       # 石肤：受物理伤害 -10%
            "block": 0.05,             # v106.3 岩壁格挡：格挡率 +5%（铁壁血统，配合石肤双防）
            "craft_bonus": 0.10,       # 熔炉之心：锻造经验 +10%（向上取整，基础 1 点 → 2 点）
            "spd_mult": 0.95,          # 🔻 磐石步履：先手 -5%
        },
        "talent_names": {"phys_reduce": "石肤", "block": "岩壁格挡", "craft_bonus": "熔炉之心", "spd_mult": "磐石步履"},
    },
    "orc": {
        "name": "兽人", "icon": "👹",
        "desc": "力量·耐力。活着就是战斗，战斗就是荣耀。",
        "talents": {
            "berserk_hp": 0.30,        # 无畏：HP<30% 攻击 +20%
            "berserk_tag": "🔥无畏",   # v181.D 引擎结算标签（原 battle.py 内联 → 本表）
            "lifesteal": 0.05,         # v106.3 嗜血本能：吸血 +5%（战血即食粮）
            "hp_mult": 1.08,           # 坚韧体魄：最大 HP +8%
            "magic_reduce": -0.05,     # 🔻 鲁莽之心：受魔法伤害 +5%
        },
        "talent_names": {"berserk_hp": "无畏", "lifesteal": "嗜血本能", "hp_mult": "坚韧体魄", "magic_reduce": "鲁莽之心"},
    },
    "halfling": {
        "name": "半身人", "icon": "🍀",
        "desc": "敏捷·幸运。锅里有热汤，兜里有金币，就是最富足的人。",
        "talents": {
            "luck": 0.10,              # v106.2 幸运儿：掉落收益 +10%（替换原金币+15%，幸运覆盖面更广）
            "item_effect": 0.10,       # 灵巧双手：消耗品效果 +10%
            "timid_hp": 0.30,          # 🔻 怯战：HP<30% 攻击 -10%
            "timid_tag": "😰怯战",     # v181.D 引擎结算标签（原 battle.py 内联 → 本表）
        },
        "talent_names": {"luck": "幸运儿", "item_effect": "灵巧双手", "timid_hp": "怯战"},
    },
    "dragonborn": {
        "name": "龙裔", "icon": "🐉",
        "desc": "力量·魔法抗性。龙骨山脉记得一切，我们记得。",
        "talents": {
            "magic_reduce": 0.10,      # 龙鳞：受魔法伤害 -10%
            "first_hit": 0.15,         # 龙之吐息：每场首击 +15%
            "first_hit_tag": "🐲龙之吐息x{mult}",   # v181.D 引擎结算标签（原 battle.py 内联 → 本表；{mult} 由引擎按 1+first_hit 现算）
            "heal_received": -0.10,    # 🔻 孤傲之血：受疗 -10%
        },
        "talent_names": {"magic_reduce": "龙鳞", "first_hit": "龙之吐息", "heal_received": "孤傲之血"},
    },
}

# v181.D 种族残血攻/首击倍率表（原 battle.py L57-58 RACE_BERSERK_MULT/RACE_TIMID_MULT 硬编码，
# 展示侧 core/race_talent_display.py 亦从 battle 反向 import —— 现统一下沉本文件单源）。
# 行为零变化：1.20 / 0.90 原样迁移；battle._race_attack_mult 与展示侧均只读本表。
RACE_ATTACK_MULT = {
    "berserk": 1.20,   # 无畏：HP 低于 berserk_hp 阈值时攻击 ×1.20（展示文案 +20%）
    "timid": 0.90,     # 怯战：HP 低于 timid_hp 阈值时攻击 ×0.90（展示文案 -10%）
}

# v181.D 亡灵系关键词单源（原 battle.py L62 UNDEAD_KEYWORDS 模块常量；注释自认与
# achievements.py ach_undead100 cond.keywords 双处同步——改词需同步两处）。
# 消费端：battle._undead_count 敌方名匹配（引擎只读本表，不再内联）。
UNDEAD_KEYWORDS = ("亡灵", "骷髅", "僵尸", "幽灵")
