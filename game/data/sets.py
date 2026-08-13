# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - sets.py(v48 全 key 转 ID)"""
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
            "effect": "frost", "chance": 0.3,
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
            "effect": "burn", "chance": 0.3,
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
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "雷霆"
    },
    "set_mi_yin": {
        "quality": "blue",
        "icon": "🛡️",
        "bonus_2": {
            "def": 0.15
        },
        "bonus_4": {
            "effect": "mdef_up_set",
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
            "effect": "crit_up_set",
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
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
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
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "圣徽"
    },
    "set_bai_yin_qi_shi": {
        "quality": "orange",
        "icon": "👑",
        "bonus_2": {
            "atk": 0.2
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3,
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "白银骑士"
    },
    "set_hei_tie_yong_bing": {
        "quality": "orange",
        "icon": "💀",
        "bonus_2": {
            "crit": 0.1,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
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
        "bonus_4": {
            "effect": "dodge_set",
            "desc": "闪避率＋10%"
        },
        "name": "旅人公会"
    },
    "set_tie_pi": {
        "quality": "blue",
        "icon": "🛡️",
        "bonus_2": {
            "atk": 0.15,
            "def": 0.12
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3,
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "铁皮"
    },
    "set_jing_tie": {
        "quality": "blue",
        "icon": "🛡️",
        "bonus_2": {
            "atk": 0.15,
            "def": 0.12
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3,
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "精铁"
    },
    "set_qi_shi": {
        "quality": "purple",
        "icon": "🛡️",
        "bonus_2": {
            "atk": 0.15,
            "def": 0.12
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3,
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "骑士"
    },
    "set_shou_wang": {
        "quality": "purple",
        "icon": "🛡️",
        "bonus_2": {
            "atk": 0.15,
            "def": 0.12
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3,
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "守望"
    },
    "set_li_ming": {
        "quality": "orange",
        "icon": "🛡️",
        "bonus_2": {
            "atk": 0.15,
            "def": 0.12
        },
        "bonus_4": {
            "effect": "pierce", "chance": 0.3,
            "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"
        },
        "name": "黎明"
    },
    "set_xue_tu": {
        "quality": "blue",
        "icon": "🔮",
        "bonus_2": {
            "matk": 0.18,
            "crit": 0.04
        },
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "学徒"
    },
    "set_fu_wen": {
        "quality": "blue",
        "icon": "🔮",
        "bonus_2": {
            "matk": 0.18,
            "crit": 0.04
        },
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "符文"
    },
    "set_mi_fa": {
        "quality": "purple",
        "icon": "🔮",
        "bonus_2": {
            "matk": 0.18,
            "crit": 0.04
        },
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "秘法"
    },
    "set_xing_jie": {
        "quality": "purple",
        "icon": "🔮",
        "bonus_2": {
            "matk": 0.18,
            "crit": 0.04
        },
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "星界"
    },
    "set_xing_chen": {
        "quality": "orange",
        "icon": "🔮",
        "bonus_2": {
            "matk": 0.18,
            "crit": 0.04
        },
        "bonus_4": {
            "effect": "thunder", "chance": 0.25,
            "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"
        },
        "name": "星辰"
    },
    "set_lie_shou": {
        "quality": "blue",
        "icon": "🏹",
        "bonus_2": {
            "spd": 0.18,
            "crit": 0.05
        },
        "bonus_4": {
            "effect": "dodge_set",
            "desc": "闪避率＋10%"
        },
        "name": "猎手"
    },
    "set_feng_xing": {
        "quality": "blue",
        "icon": "🏹",
        "bonus_2": {
            "spd": 0.18,
            "crit": 0.05
        },
        "bonus_4": {
            "effect": "dodge_set",
            "desc": "闪避率＋10%"
        },
        "name": "风行"
    },
    "set_an_ye": {
        "quality": "purple",
        "icon": "🏹",
        "bonus_2": {
            "spd": 0.18,
            "crit": 0.05
        },
        "bonus_4": {
            "effect": "dodge_set",
            "desc": "闪避率＋10%"
        },
        "name": "暗夜"
    },
    "set_ying_yan": {
        "quality": "purple",
        "icon": "🏹",
        "bonus_2": {
            "spd": 0.18,
            "crit": 0.05
        },
        "bonus_4": {
            "effect": "dodge_set",
            "desc": "闪避率＋10%"
        },
        "name": "鹰眼"
    },
    "set_cang_qiong": {
        "quality": "orange",
        "icon": "🏹",
        "bonus_2": {
            "spd": 0.18,
            "crit": 0.05
        },
        "bonus_4": {
            "effect": "dodge_set",
            "desc": "闪避率＋10%"
        },
        "name": "苍穹"
    },
    "set_bu_yi": {
        "quality": "blue",
        "icon": "☀️",
        "bonus_2": {
            "mdef": 0.18,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "布衣"
    },
    "set_zhu_fu": {
        "quality": "blue",
        "icon": "☀️",
        "bonus_2": {
            "mdef": 0.18,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "祝福"
    },
    "set_sheng_tang": {
        "quality": "purple",
        "icon": "☀️",
        "bonus_2": {
            "mdef": 0.18,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "圣堂"
    },
    "set_shen_pan": {
        "quality": "purple",
        "icon": "☀️",
        "bonus_2": {
            "mdef": 0.18,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "审判"
    },
    "set_shen_en": {
        "quality": "orange",
        "icon": "☀️",
        "bonus_2": {
            "mdef": 0.18,
            "hp": 0.1
        },
        "bonus_4": {
            "effect": "regen",
            "desc": "每回合开始回复 5% 生命"
        },
        "name": "神恩"
    },
    "set_qing_ying": {
        "quality": "blue",
        "icon": "🗡️",
        "bonus_2": {
            "crit": 0.08,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "轻影"
    },
    "set_ye_xing": {
        "quality": "blue",
        "icon": "🗡️",
        "bonus_2": {
            "crit": 0.08,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "夜行"
    },
    "set_yin_ying": {
        "quality": "purple",
        "icon": "🗡️",
        "bonus_2": {
            "crit": 0.08,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "阴影"
    },
    "set_huan_ying": {
        "quality": "purple",
        "icon": "🗡️",
        "bonus_2": {
            "crit": 0.08,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "幻影"
    },
    "set_wu_ye": {
        "quality": "orange",
        "icon": "🗡️",
        "bonus_2": {
            "crit": 0.08,
            "atk": 0.1
        },
        "bonus_4": {
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "午夜"
    },
    "set_xing_zhe": {
        "quality": "blue",
        "icon": "🥋",
        "bonus_2": {
            "atk": 0.12,
            "hp": 0.15
        },
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "行者"
    },
    "set_tie_shou": {
        "quality": "blue",
        "icon": "🥋",
        "bonus_2": {
            "atk": 0.12,
            "hp": 0.15
        },
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "铁手"
    },
    "set_hu_xiao": {
        "quality": "purple",
        "icon": "🥋",
        "bonus_2": {
            "atk": 0.12,
            "hp": 0.15
        },
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "虎啸"
    },
    "set_pan_shi": {
        "quality": "purple",
        "icon": "🥋",
        "bonus_2": {
            "atk": 0.12,
            "hp": 0.15
        },
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "磐石"
    },
    "set_jin_shen": {
        "quality": "orange",
        "icon": "🥋",
        "bonus_2": {
            "atk": 0.12,
            "hp": 0.15
        },
        "bonus_4": {
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "金身"
    }
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
            "effect": "pierce", "chance": 0.3,
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
            "effect": "dodge_set",
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
            "effect": "execute", "chance": 1.0,
            "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"
        },
        "name": "刺客"
    },
    "cls_wu_seng": {
        "stages": [
            "行者",
            "铁手",
            "虎啸",
            "磐石",
            "金身"
        ],
        "weapons": [
            "行者拳套",
            "铁手拳套",
            "虎啸拳套",
            "磐石拳套",
            "金身拳套"
        ],
        "parts": [
            "头带",
            "僧袍",
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
            "effect": "lifesteal_set", "chance": 0.3,
            "desc": "攻击 30% 概率吸血 15% 伤害"
        },
        "name": "拳师"
    },
}

