# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - sets.py(v48 全 key 转 ID)"""
SET_THEMES = {
    "blue": [
        "寒霜",
        "烈焰",
        "雷霆",
        "秘银"
    ],
    "purple": [
        "龙鳞",
        "月影",
        "黑沼",
        "圣徽"
    ],
    "orange": [
        "白银骑士",
        "黑铁佣兵",
        "晨光教会",
        "旅人公会"
    ]
}

SET_CHANCE = {
    "blue": 0.35,
    "purple": 0.45,
    "orange": 0.55
}

# 改名映射：旧套名 → 新套名（key 保留中文，用于旧档迁移推导）
SETS = {
    "set_han_shuang": {
        "quality": "blue",
        "icon": "❄️",
        "bonus_2": {
            "spd": 0.15
        },
        "bonus_4": {
            "effect": "frost", "chance": 0.3, "params": {"type": "proc_slow", "chance": 0.30, "slow_pct": 0.15, "slow_turns": 2, "tag": "❄️", "name": "寒霜之力"},
            "desc": "攻击 30% 概率使敌人减速 2 回合"
        },
        "name": "寒霜"
    },
    "set_lie_yan": {
        "quality": "blue",
        "icon": "🔥",
        "bonus_2": {
            "atk": 0.12
        },
        "bonus_4": {
            "effect": "burn", "chance": 0.3, "params": {"type": "proc_burn", "chance": 0.30, "burn_pct": 0.05, "burn_turns": 2, "max_stacks": 5, "tag": "🔥", "name": "烈焰之力"},
            "desc": "攻击 30% 概率灼烧敌人(2 回合每回合 5% 生命)"
        },
        "name": "烈焰"
    },
    "set_lei_ting": {
        "quality": "blue",
        "icon": "⚡",
        "bonus_2": {
            "crit": 0.05
        },
        "bonus_4": {"effect": "lei_ting_chain", "chance": 0.25, "params": {"type": "proc_flat_dmg", "chance": 0.25, "stat": "matk", "pct": 0.50, "pct_alt": 0.75, "cond_thunder_mark": True, "edef": "mdef", "dmg_type": "magic", "tag": "⚡", "name": "连环雷"}, "desc": "攻击命中 25% 概率追加 50% 魔攻雷击（带雷印记时 75%）"},
        "name": "雷霆"
    },
    "set_mi_yin": {
        "quality": "blue",
        "icon": "🛡️",
        "bonus_2": {
            "def": 0.15
        },
        "bonus_4": {
            "effect": "mdef_up_set", "stats": {"mdef": 0.20},
            "desc": "魔防＋20%"
        },
        "name": "秘银"
    },
    "set_long_lin": {
        "quality": "purple",
        "icon": "🐉",
        "bonus_2": {
            "def": 0.2,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "reflect",
            "desc": "被攻击时 25% 概率反弹 25% 伤害"
        },
        "name": "龙鳞"
    },
    "set_yue_ying": {
        "quality": "purple",
        "icon": "✨",
        "bonus_2": {
            "matk": 0.18,
            "pene_magi": 0.05  # v106.1 月影法穿：法系穿透
        },
        "bonus_4": {
            "effect": "crit_up_set", "stats": {"crit": 0.08},
            "desc": "暴击率＋8%"
        },
        "name": "月影"
    },
    "set_hei_zhao": {
        "quality": "purple",
        "icon": "🌑",
        "bonus_2": {
            "atk": 0.18,
            "pene_phys": 0.05  # v106.1 黑沼穿甲：暗杀者破甲
        },
        "bonus_4": {"effect": "hei_zhao_erode", "chance": 0.3, "params": {"type": "proc_erode", "chance": 0.30, "max_stacks": 2, "pct": 1, "tag": "🌑", "name": "暗蚀"}, "desc": "攻击 30% 概率附加暗蚀（2 回合每回合 1% 敌方最大生命暗伤），伤害全额转化自身生命"},
        "name": "黑沼"
    },
    "set_sheng_hui": {
        "quality": "purple",
        "icon": "☀️",
        "bonus_2": {
            "mdef": 0.2,
            "hp": 0.1,
            "abyss_res": 0.05,   # v106.1 圣徽庇护：深渊抗性
            "heal_power": 0.05   # v106.2 圣徽圣愈：治疗强度
        },
        "bonus_4": {"effect": "holy_halo_shield", "params": {"type": "taken_shield_convert", "shield_pct": 0.10, "once_per_round": True, "tag": "✨", "name": "圣辉护盾"}, "desc": "被攻击命中后将本次伤害 10% 转化为护盾（每回合最多 1 次）"},
        "name": "圣徽"
    },
    "set_bai_yin_qi_shi": {
        "quality": "orange",
        "icon": "👑",
        "bonus_2": {
            "atk": 0.2
        },
        "bonus_4": {"effect": "silver_knight_lance", "chance": 0.3, "params": {"type": "proc_armor_break", "chance": 0.30, "break_pct": 0.15, "break_turns": 2, "bonus_atk_pct": 0.30, "tag": "🐎", "name": "白银冲锋"}, "desc": "攻击命中 30% 概率破甲 15%（2 回合）；目标已破甲则追加 30% 攻击力冲锋"},
        "name": "白银骑士"
    },
    "set_hei_tie_yong_bing": {
        "quality": "orange",
        "icon": "💀",
        "bonus_2": {
            "crit": 0.1,
            "atk": 0.1
        },
        "bonus_4": {"effect": "iron_execute_rampage", "chance": 0.3, "params": {"type": "proc_flat_dmg", "chance": 0.30, "stat": "atk", "pct": 0.50, "cond_hp_lt": 0.40, "tag": "💀", "name": "黑铁斩杀"}, "desc": "对生命低于 40% 的敌人，攻击命中 30% 概率追加一次 50% 攻击力的斩杀"},
        "name": "黑铁佣兵"
    },
    "set_chen_guang_jiao_hui": {
        "quality": "orange",
        "icon": "⏳",
        "bonus_2": {
            "hp": 0.25,
            "heal_power": 0.05  # v106.2 晨光圣愈：治疗强度
        },
        "bonus_4": {
            "effect": "regen_strong",
            "desc": "每回合开始回复 8% 生命"
        },
        "name": "晨光教会"
    },
    "set_lv_ren_gong_hui": {
        "quality": "orange",
        "icon": "🎲",
        "bonus_2": {
            "spd": 0.2,
            "dodge": 0.05,
            "cdr": 0.05  # v106.1 旅人经验：冷却缩减
        },
        "bonus_4": {"effect": "travel_mark", "chance": 0.3, "params": {"type": "proc_mark", "chance": 0.30, "max_mark": 5, "mark_desc": "每层 +20% 伤害", "tag": "🎒", "name": "旅人标记"}, "desc": "攻击命中 30% 概率给敌人挂 1 层旅人标记（每层 +20% 伤害，上限 5）"},
        "name": "旅人公会"
    },
    "set_tie_pi": {
        "quality": "blue",
        "icon": "🛡️",
        "bonus_2": {"def": 0.18, "atk": 0.08},
        "bonus_4": {"effect": "tie_pi_bulwark", "chance": 0.2, "params": {"type": "taken_shield", "chance": 0.20, "shield_pct": 0.05, "shield_turns": 1, "shield_key": "tie_pi_bulwark", "tag": "🛡️", "name": "铁皮护体"}, "desc": "受击 20% 概率获得 5% 最大生命护盾（1 回合）"},
        "name": "铁皮"
    },
    "set_jing_tie": {
        "quality": "blue",
        "icon": "🛡️",
        "bonus_2": {"atk": 0.18, "def": 0.08},
        "bonus_4": {"effect": "jing_tie_refine", "chance": 0.5, "params": {"type": "proc_armor_stack", "chance": 0.50, "max_stacks": 3, "break_pct": 0.05, "break_turns": 2, "tag": "⚒️", "name": "精淬"}, "desc": "攻击命中 50% 概率叠 1 层精淬（敌方防御 -5%/层，上限 3 层）"},
        "name": "精铁"
    },
    "set_qi_shi": {
        "quality": "purple",
        "icon": "🛡️",
        "bonus_2": {"atk": 0.2, "def": 0.08},
        "bonus_4": {"effect": "qi_shi_charge", "chance": 0.18, "params": {"type": "proc_flat_dmg", "chance": 0.18, "stat": "atk", "pct": 1.00, "once_per_round": True, "tag": "🐎", "name": "骑士冲锋"}, "desc": "攻击命中 18% 概率追加 100% 攻击力冲锋（每回合最多 1 次）"},
        "name": "骑士"
    },
    "set_shou_wang": {
        "quality": "purple",
        "icon": "🛡️",
        "bonus_2": {"def": 0.2, "hp": 0.08},
        "bonus_4": {"effect": "shou_wang_ward", "chance": 0.25, "desc": "受击 25% 概率本次受击伤害 -50%"},
        "name": "守望"
    },
    "set_li_ming": {
        "quality": "orange",
        "icon": "🛡️",
        "bonus_2": {"atk": 0.18, "def": 0.12},
        "bonus_4": {"effect": "li_ming_dawnbreak", "chance": 0.3, "params": {"type": "proc_anti_heal", "chance": 0.30, "break_pct": 0.15, "break_turns": 2, "anti_heal_pct": 0.30, "tag": "🌅", "name": "黎明破晓"}, "desc": "攻击命中 30% 概率破甲 15%（2 回合）；破甲期间目标受疗效果 -30%"},
        "name": "黎明"
    },
    "set_xue_tu": {
        "quality": "blue",
        "icon": "🔮",
        "bonus_2": {"matk": 0.15, "cdr": 0.05},
        "bonus_4": {"effect": "xue_tu_spark", "chance": 0.4, "params": {"type": "proc_mark", "chance": 0.40, "max_mark": 3, "mark_key": "element_marks", "tag": "⚡", "name": "蓄雷"}, "desc": "攻击命中 40% 概率叠 1 层雷印记（上限 3）"},
        "name": "学徒"
    },
    "set_fu_wen": {
        "quality": "blue",
        "icon": "🔮",
        "bonus_2": {"matk": 0.18, "crit": 0.03},
        "bonus_4": {"effect": "fu_wen_glyph_bolt", "chance": 0.3, "params": {"type": "proc_flat_dmg", "chance": 0.30, "stat": "matk", "pct": 0.45, "pct_alt": 0.75, "cond_thunder_ge2": True, "consume_thunder": True, "edef": "mdef", "dmg_type": "magic", "tag": "📜", "name": "符文雷刻"}, "desc": "攻击命中 30% 概率追加 45% 魔攻雷击（雷印记 ≥2 消耗 1 层额外 +30%）"},
        "name": "符文"
    },
    "set_mi_fa": {
        "quality": "purple",
        "icon": "🔮",
        "bonus_2": {"matk": 0.15, "crit": 0.05},
        "bonus_4": {"effect": "mi_fa_arcane_bolt", "chance": 0.2, "params": {"type": "proc_flat_dmg", "chance": 0.20, "stat": "matk", "pct": 0.80, "edef": "mdef", "dmg_type": "magic", "tag": "✨", "name": "秘术重雷"}, "desc": "攻击命中 20% 概率追加 80% 魔攻秘法雷击（吃暴击）"},
        "name": "秘法"
    },
    "set_xing_jie": {
        "quality": "purple",
        "icon": "🔮",
        "bonus_2": {"matk": 0.18, "pene_magi": 0.03},
        "bonus_4": {"effect": "xing_jie_starfall", "chance": 0.15, "params": {"type": "proc_flat_dmg", "chance": 0.15, "stat": "matk", "pct": 0.80, "edef": "mdef", "dmg_type": "magic", "tag": "☄️", "name": "星坠"}, "desc": "攻击命中 15% 概率追加 80% 魔攻星雷并溅射全体 40% 魔攻"},
        "name": "星界"
    },
    "set_xing_chen": {
        "quality": "orange",
        "icon": "🔮",
        "bonus_2": {"matk": 0.2, "crit": 0.04},
        "bonus_4": {"effect": "xing_chen_starstrike", "chance": 0.25, "params": {"type": "proc_flat_dmg", "chance": 0.25, "stat": "matk", "pct": 0.75, "edef": "mdef", "dmg_type": "magic", "tag": "🌟", "name": "星辰轰击", "cond_thunder_full": True}, "desc": "攻击命中 25% 概率追加 75% 魔攻星雷（雷印记满 3 必触发）"},
        "name": "星辰"
    },
    "set_lie_shou": {
        "quality": "blue",
        "icon": "🏹",
        "bonus_2": {"spd": 0.15, "pene_phys": 0.04},
        "bonus_4": {"effect": "hunter_mark_bonus", "chance": 0.4, "params": {"type": "proc_mark_or_dmg", "chance": 0.40, "max_mark": 5, "dmg_pct": 0.15, "tag": "🏹", "name": "猎手印记"}, "desc": "攻击命中 40%：标记目标伤害 +15%，否则叠 1 层标记"},
        "name": "猎手"
    },
    "set_feng_xing": {
        "quality": "blue",
        "icon": "🏹",
        "bonus_2": {"spd": 0.18, "dodge": 0.03},
        "bonus_4": {"effect": "gale_double", "chance": 0.25, "params": {"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.50, "tag": "🌪️", "name": "风行连射"}, "desc": "攻击命中 25% 概率追加一次 50% 攻击力的连射"},
        "name": "风行"
    },
    "set_an_ye": {
        "quality": "purple",
        "icon": "🏹",
        "bonus_2": {"crit": 0.06, "dodge": 0.04},
        "bonus_4": {"stats": {"precise": 0.05, "dodge": 0.05}, "desc": "精准 +5%、闪避 +5%（暗夜潜行精准）"},
        "name": "暗夜"
    },
    "set_ying_yan": {
        "quality": "purple",
        "icon": "🏹",
        "bonus_2": {"crit": 0.07, "pene_phys": 0.03},
        "bonus_4": {"effect": "eagle_vision", "chance": 0.35, "params": {"type": "proc_buff", "chance": 0.35, "buff_key": "eagle_vision", "buff_val": True, "tag": "🦅", "name": "鹰眼锐视"}, "desc": "攻击命中 35% 概率下一次攻击暴击伤害 +30%"},
        "name": "鹰眼"
    },
    "set_cang_qiong": {
        "quality": "orange",
        "icon": "🏹",
        "bonus_2": {"spd": 0.15, "crit": 0.06},
        "bonus_4": {"effect": "sky_chain", "chance": 0.25, "params": {"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.60, "pct_alt": 0.75, "cond_mark": True, "tag": "☄️", "name": "苍穹连星"}, "desc": "攻击命中 25% 概率追加 60% 攻击力的箭雨（标记目标 75%）"},
        "name": "苍穹"
    },
    "set_bu_yi": {
        "quality": "blue",
        "icon": "☀️",
        "bonus_2": {"mdef": 0.16, "hp": 0.12},
        "bonus_4": {"effect": "cloth_regen_battle", "chance": 0.3, "params": {"type": "proc_heal_hp", "chance": 0.30, "heal_pct": 0.08, "tag": "☀️", "name": "布衣愈合"}, "desc": "攻击命中 30% 概率回复 8% 最大生命"},
        "name": "布衣"
    },
    "set_zhu_fu": {
        "quality": "blue",
        "icon": "☀️",
        "bonus_2": {"mdef": 0.18, "hp": 0.1, "heal_power": 0.03},
        "bonus_4": {"effect": "bless_chant_mp", "chance": 0.35, "params": {"type": "proc_heal_mp", "chance": 0.35, "heal_pct": 0.05, "tag": "🎵", "name": "祝福咏叹"}, "desc": "攻击命中 35% 概率回复 5% 最大魔力"},
        "name": "祝福"
    },
    "set_sheng_tang": {
        "quality": "purple",
        "icon": "☀️",
        "bonus_2": {"mdef": 0.2, "hp": 0.1},
        "bonus_4": {"effect": "holy_field_heal", "params": {"type": "turn_heal_cond", "heal_low_pct": 0.06, "heal_high_pct": 0.03, "cond_hp_lt": 0.50, "tag": "✨", "name": "圣辉疗愈"}, "desc": "每回合开始：生命低于 50% 回复 6%，否则回复 3%"},
        "name": "圣堂"
    },
    "set_shen_pan": {
        "quality": "purple",
        "icon": "☀️",
        "bonus_2": {"mdef": 0.18, "hp": 0.1, "tenacity": 0.03},
        "bonus_4": {"effect": "judge_purify_heal", "chance": 0.25, "params": {"type": "proc_purify_heal", "chance": 0.25, "heal_pct": 0.04, "tag": "⚖️", "name": "审判净化"}, "desc": "攻击命中 25% 概率净化自身 1 个负面效果并回复 4% 最大生命"},
        "name": "审判"
    },
    "set_shen_en": {
        "quality": "orange",
        "icon": "☀️",
        "bonus_2": {"mdef": 0.18, "hp": 0.12, "heal_power": 0.05},
        "bonus_4": {"effect": "divine_grace_burst", "params": {"type": "turn_heal_cond", "heal_pct": 0.05, "low_extra_pct": 0.15, "low_hp_lt": 0.30, "per_battle": True, "tag": "☀️", "name": "神恩爆发"}, "desc": "每回合开始回复 5% 生命；生命首次低于 30% 时额外回复 15%（每场 1 次）"},
        "name": "神恩"
    },
    "set_qing_ying": {
        "quality": "blue",
        "icon": "🗡️",
        "bonus_2": {"crit": 0.08, "atk": 0.1},
        "bonus_4": {"effect": "shadow_combo_double", "chance": 0.25, "params": {"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.40, "tag": "🗡️", "name": "轻影连刺"}, "desc": "攻击命中 25% 概率追加一次 40% 攻击力的连刺"},
        "name": "轻影"
    },
    "set_ye_xing": {
        "quality": "blue",
        "icon": "🗡️",
        "bonus_2": {"crit": 0.1, "atk": 0.08},
        "bonus_4": {"effect": "night_backstab", "chance": 0.2, "params": {"type": "proc_execute", "stat": "atk", "pct": 0.25, "hp_full": True, "chance": 0.20, "pct2": 0.05, "hp_pct_dmg": True, "tag": "🌙", "name": "夜行背刺"}, "desc": "对满血敌人伤害 +25%；否则 20% 概率附加 5% 最大生命真伤"},
        "name": "夜行"
    },
    "set_yin_ying": {
        "quality": "purple",
        "icon": "🗡️",
        "bonus_2": {"crit": 0.08, "atk": 0.1, "pene_phys": 0.03},
        "bonus_4": {"effect": "shadow_etch_vuln", "chance": 0.3, "params": {"type": "proc_mark", "chance": 0.30, "max_mark": 5, "mark_desc": "每层 +15% 受伤害", "tag": "🌒", "name": "阴影蚀刻"}, "desc": "攻击命中 30% 概率叠 1 层阴影蚀刻（每层 +15% 受伤害，上限 5）"},
        "name": "阴影"
    },
    "set_huan_ying": {
        "quality": "purple",
        "icon": "🗡️",
        "bonus_2": {"crit": 0.06, "atk": 0.12},
        "bonus_4": {"effect": "phantom_echo", "chance": 0.15, "params": {"type": "proc_flat_dmg", "chance": 0.20, "stat": "atk", "pct": 0.60, "pct_alt": 0.35, "cond_crit": True, "tag": "👻", "name": "幻影分身"}, "desc": "攻击命中 15% 概率追加 60% 攻击力的幻影斩（暴击时 30%）"},
        "name": "幻影"
    },
    "set_wu_ye": {
        "quality": "orange",
        "icon": "🗡️",
        "bonus_2": {"crit": 0.1, "atk": 0.12},
        "bonus_4": {"effect": "midnight_assassinate", "chance": 0.35, "params": {"type": "proc_execute", "chance": 0.35, "stat": "atk", "pct": 0.40, "hp_lt": 0.30, "true_dmg": True, "tag": "🗡️", "name": "午夜暗杀"}, "desc": "对生命低于 30% 的敌人，攻击命中 35% 概率追加 40% 攻击力真伤处决"},
        "name": "午夜"
    },
    "set_xing_zhe": {
        "quality": "blue",
        "icon": "🥋",
        "bonus_2": {"atk": 0.1, "lifesteal": 0.02, "hp": 0.08},
        "bonus_4": {"effect": "xing_zhe_hunt", "chance": 0.4, "params": {"type": "proc_lifesteal", "chance": 0.40, "lifesteal_pct": 0.12, "tag": "🩸", "name": "猎血"}, "desc": "攻击 40% 概率吸血 12% 伤害"},
        "name": "行者"
    },
    "set_tie_shou": {
        "quality": "blue",
        "icon": "🥋",
        "bonus_2": {"hp": 0.15, "def": 0.08},
        "bonus_4": {"effect": "tie_shou_blood", "chance": 0.3, "desc": "受击 30% 概率回复 3% 最大生命"},
        "name": "石拳"
    },
    "set_hu_xiao": {
        "quality": "purple",
        "icon": "🥋",
        "bonus_2": {"hp": 0.12, "mdef": 0.1},
        "bonus_4": {"effect": "hu_xiao_barrier", "params": {"type": "turn_shield", "shield_pct": 0.03, "shield_turns": 1, "tag": "🧱", "name": "壁立千仞"}, "desc": "每回合开始获得 3% 最大生命的护盾（1 回合）"},
        "name": "壁槌"
    },
    "set_pan_shi": {
        "quality": "purple",
        "icon": "🥋",
        "bonus_2": {"def": 0.15, "hp": 0.1},
        "bonus_4": {"effect": "pan_shi_steady", "params": {"type": "taken_dmg_reduce_flat", "reduce_pct": 0.05, "tag": "⛰️", "name": "磐石不动"}, "desc": "受击时伤害 -5%（磐石不动）"},
        "name": "磐石"
    },
    "set_anvil_guard": {
        "quality": "orange",
        "icon": "🥋",
        "bonus_2": {"def": 0.12, "hp": 0.15, "block": 0.04},
        "bonus_4": {"effect": "anvil_parry", "chance": 0.2, "params": {"type": "taken_immune", "chance": 0.20, "per_battle": 3, "tag": "🛡️", "name": "铁壁格挡"}, "desc": "受击 20% 概率完全免疫本次伤害（每场最多 3 次）"},
        "name": "铁砧拳套"
    },
    # ================= v130.2c 资源联动套装（12 套，效果定义已自 affixes.py V130 段迁入（v130.2d）；战斗侧消费见 battle.py SET_EFFECT_CONSUMED） =================
    # bonus_2 为 effect 型（非属性 dict）——引擎 set_bonus_2 按非 STAT 键静默跳过，
    # 战斗侧消费由引擎 agent 按 desc/effect 接入（见主报告数据结构约定）。
    # line 字段：非运行字段，策划说明（12 套统一）。
    "set_xue_shi_zhan_tuan": {  # 战士·通用基础（散件配套）
        "quality": "purple", "icon": "⚔️", "name": "血誓战团", "line": "战士·通用基础",
        "bonus_2": {"effect": "res_gain", "res": "rage", "value": 1, "on": "on_taken",
                    "desc": "受击回怒 +1"},
    },
    "set_yu_jin_jun_tuan_hui_zhang": {  # 战士·攻线
        "quality": "purple", "icon": "🔥", "name": "余烬军团徽章", "line": "战士·攻线",
        "bonus_2": {},
        "bonus_4": {"effect": "full_rage_pursuit", "power": 0.50, "rage_cost_reduce": 1,
                    "desc": "满怒时 普攻二段追击 威力 30% → 50%；满怒大招 怒气消耗 -1 (最低消耗 1)"},
    },
    "set_yuan_su_shi_tu": {  # 法师·基础/转职通用（传说套装，团本/世界 Boss 掉落）
        "quality": "orange", "icon": "✨", "name": "元素使徒", "line": "法师·基础/转职通用",
        "bonus_2": {"effect": "res_max", "res": "element", "value": 1,
                    "desc": "元素亲和充能条 上限 +1 (5 → 6)"},
        "bonus_4": {"effect": "ultimate_cost_reduce", "res": "element", "value": 1,
                    "desc": "全耗奥义(元素湮灭) 充能消耗 -1 (-5 → -4，保留残点走轴)"},
    },
    "set_shi_zhi_ling_zhu": {  # 法师·时律线（v151：原隐藏线时咒→时律线）
        "quality": "orange", "icon": "⏳", "name": "时之领主", "line": "法师·时律线",
        "bonus_2": {"effect": "cdr_set", "on": "time_freeze", "value": -1,
                    "desc": "时停领域 冷却时间 -1"},
    },
    "set_xun_lin_zhang_pi_feng": {  # 游侠·散件配套
        "quality": "purple", "icon": "🍃", "name": "巡林长披风", "line": "游侠·散件配套",
        "bonus_2": {"effect": "crit_on_marked", "crit": 0.05,
                    "desc": "命中带标记目标时 暴击率 +5%"},
    },
    "set_lie_shou_yuan_zheng_dui_hui_ji": {  # 游侠·攻线
        "quality": "purple", "icon": "🏹", "name": "猎首远征队徽记", "line": "游侠·攻线",
        "bonus_2": {},
        "bonus_4": {"effect": "res_cost_reduce", "res": "energy", "value": 0.10, "on": "finisher_marked",
                    "min_cost": 50,
                    "desc": "对带标记敌人释放 50/100 档终结技时 精力消耗 -10%"},
    },
    "set_sheng_dian_ri_mian": {  # 牧师·平稳/爆发流
        "quality": "purple", "icon": "🌞", "name": "圣典·日冕", "line": "牧师·平稳/爆发流",
        "bonus_2": {"effect": "heal_team_on_miracle_t2plus", "hp": 30, "miracle_min": 5,
                    "desc": "施放耗 5 点以上信仰的神迹技时 全体队友额外恢复 30 体力"},
        "bonus_4": {"effect": "first_hit_immune", "cond": "faith_full", "per_battle": 1, "params": {"type": "taken_immune_cond", "cond": "faith_full", "per_battle": 1, "tag": "☀️", "name": "圣典日冕"},
                    "desc": "满信仰状态下 首次受击免伤 (每战 1 次)"},
    },
    "set_an_ye_sheng_dian": {  # 牧师·幽祷线（v151：原暗影神谕悼咏→幽祷召唤流）
        "quality": "purple", "icon": "🌙", "name": "暗夜圣典", "line": "牧师·幽祷(召唤流)",
        "bonus_2": {"effect": "summon_heal", "value": 0.05,
                    "desc": "场上亡灵≥1 时 每回合全队回复 5% 生命"},
        "bonus_4": {"effect": "summon_dmg", "value": 0.20,
                    "desc": "场上亡灵≥1 时 召唤物伤害 +20%"},
    },
    "set_sheng_hui_shi_yue": {  # 牧师·新手保底
        "quality": "blue", "icon": "🛡️", "name": "圣徽·誓约", "line": "牧师·新手保底",
        "bonus_2": {"effect": "res_gain", "res": "faith", "value": 1, "on": "on_taken",
                    "desc": "受击回信仰 +1"},
        "bonus_4": {"effect": "res_gain", "res": "faith", "value": 1, "on": "on_heal",
                    "desc": "治疗回信仰 +1"},
    },
    "set_ye_mu_he_qi_ying_sha": {  # 刺客·轻甲/武器 5 件套
        "quality": "purple", "icon": "🗡️", "name": "夜幕合契·影纱", "line": "刺客·轻甲/武器 5 件套",
        "bonus_2": {"effect": "battle_start_cp", "value": 1,
                    "desc": "战斗开始时 +1 连击点"},
        "bonus_4": {"effect": "finisher_crit", "crit": 0.15,
                    "desc": "终结技暴击率 +15%"},
        "bonus_5": {"effect": "combo_finisher_per_layer", "per_layer": 0.08, "base": 0.05,
                    "max_layers": 8,
                    "desc": "攻线连段每层终结技增伤 5% → 8% (上限 +64%)"},
    },
    "set_xu_shi_yong_dong": {  # 拳师·通用
        "quality": "purple", "icon": "🌊", "name": "蓄势涌动", "line": "拳师·通用",
        "bonus_2": {"effect": "battle_start_res", "res": "chi", "value": 2,
                    "desc": "进入战斗时 2 气 (开局即进连段中段)"},
    },
    "set_shi_bu_ke_dang": {  # 拳师·通用
        "quality": "purple", "icon": "⛰️", "name": "势不可挡", "line": "拳师·通用",
        "bonus_2": {},
        "bonus_4": {"effect": "chi_skill_phys", "value": 0.15,
                    "desc": "气力技(耗气) 物理伤害 +15%"},
    },
}

CLASS_SET_STAGES = [
    {
        "lv": 10,
        "label": "Ⅰ",
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "quality": "blue"
    },
    {
        "lv": 30,
        "label": "Ⅱ",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "quality": "blue"
    },
    {
        "lv": 50,
        "label": "Ⅲ",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "quality": "purple"
    },
    {
        "lv": 70,
        "label": "Ⅳ",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "quality": "purple"
    },
    {
        "lv": 90,
        "label": "Ⅴ",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "quality": "orange"
    }
]

CLASS_SET_THEMES = {
    "cls_zhan_shi": {
        "stages": [
            "铁皮",
            "精铁",
            "骑士",
            "守望",
            "黎明"
        ],
        "weapons": [
            "铁皮长剑",
            "精铁长剑",
            "骑士长剑",
            "守望者之剑",
            "黎明圣剑"
        ],
        "parts": [
            "头盔",
            "胸甲",
            "护腿",
            "战靴"
        ],
        "icon": "🛡️",
        "wtype": "剑",
        "bonus_2": {
            "atk": 0.15,
            "def": 0.12
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3, "params": {"type": "proc_armor_break", "chance": 0.30, "break_pct": 0.15, "break_turns": 2, "tag": "⚔️", "name": "破甲之力"},
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "战士"
    },
    "cls_fa_shi": {
        "stages": [
            "学徒",
            "符文",
            "秘法",
            "星界",
            "星辰"
        ],
        "weapons": [
            "见习法杖",
            "符文法杖",
            "秘法法杖",
            "星界法杖",
            "星辰法杖"
        ],
        "parts": [
            "法帽",
            "长袍",
            "护腿",
            "法靴"
        ],
        "icon": "🔮",
        "wtype": "法杖",
        "bonus_2": {
            "matk": 0.18,
            "crit": 0.04
        },
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "params": {"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.60, "tag": "⚡", "name": "雷霆一击"},
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "法师"
    },
    "cls_you_xia": {
        "stages": [
            "猎手",
            "风行",
            "暗夜",
            "鹰眼",
            "苍穹"
        ],
        "weapons": [
            "猎手短弓",
            "猎手长弓",
            "风行长弓",
            "鹰眼之弓",
            "苍穹之弓"
        ],
        "parts": [
            "皮帽",
            "皮甲",
            "护腿",
            "长靴"
        ],
        "icon": "🏹",
        "wtype": "弓",
        "bonus_2": {
            "spd": 0.18,
            "crit": 0.05
        },
        "bonus_4": {
            "effect": "dodge_set", "stats": {"dodge": 0.10},
            "desc": "闪避率＋10%"
        },
        "name": "游侠"
    },
    "cls_mu_shi": {
        "stages": [
            "布衣",
            "祝福",
            "圣堂",
            "审判",
            "神恩"
        ],
        "weapons": [
            "布衣权杖",
            "祝福权杖",
            "圣堂权杖",
            "审判之杖",
            "神恩权杖"
        ],
        "parts": [
            "圣冠",
            "法衣",
            "护腿",
            "圣靴"
        ],
        "icon": "☀️",
        "wtype": "权杖",
        "bonus_2": {
            "mdef": 0.18,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "牧师"
    },
    "cls_ci_ke": {
        "stages": [
            "轻影",
            "夜行",
            "阴影",
            "幻影",
            "午夜"
        ],
        "weapons": [
            "轻影匕首",
            "夜行匕首",
            "阴影匕首",
            "幻影之匕",
            "午夜之刃"
        ],
        "parts": [
            "面巾",
            "皮衣",
            "护腿",
            "轻靴"
        ],
        "icon": "🗡️",
        "wtype": "匕首",
        "bonus_2": {
            "crit": 0.08,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0, "params": {"type": "proc_execute", "chance": 1.0, "hp_lt": 0.30, "dmg_pct": 0.25, "pct_of_dmg": True, "tag": "💀", "name": "灭世之力"},
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "刺客"
    },
    "cls_wu_seng": {
        "stages": [
            "行者",
            "石拳",
            "壁槌",
            "磐石",
            "磐岩"
        ],
        "weapons": [
            "行者拳套",
            "石拳拳套",
            "壁槌拳套",
            "磐石拳套",
            "磐岩拳套"
        ],
        "parts": [
            "束发带",
            "武斗袍",
            "护腿",
            "布靴"
        ],
        "icon": "🥋",
        "wtype": "拳套",
        "bonus_2": {
            "atk": 0.12,
            "hp": 0.15
        },
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3, "params": {"type": "proc_lifesteal", "chance": 0.30, "lifesteal_pct": 0.15, "tag": "🌑", "name": "深渊之力"},
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "拳师"
    },
}

