# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - equipment.py（v48 品质/武器类型英文 ID）"""
EQUIP_SLOTS = {
    "weapon": "武器",
    "helm": "头盔",
    "armor": "胸甲",
    "legs": "护腿",
    "boots": "靴子",
    "ring": "戒指",
    "necklace": "项链"
}

QUALITY = {
    "white": {
        "mult": 1.0,
        "color": "⚪",
        "name": "普通"
    },
    "green": {
        "mult": 1.3,
        "color": "🟢",
        "name": "优秀"
    },
    "blue": {
        "mult": 1.6,
        "color": "🔵",
        "name": "稀有"
    },
    "purple": {
        "mult": 1.8,
        "color": "🟣",
        "name": "史诗"
    },
    "orange": {
        "mult": 2.0,
        "color": "🟠",
        "name": "传说"
    }
}

QUALITY_ORDER = [
    "white",
    "green",
    "blue",
    "purple",
    "orange"
]

WEAPON_TYPES = {
    "sword": [
        "战士"
    ],
    "staff": [
        "法师"
    ],
    "bow": [
        "游侠"
    ],
    "mace": [
        "牧师"
    ],
    "dagger": [
        "刺客"
    ],
    "fist": [
        "武僧"
    ],
    "spear": [
        "战士"
    ],
    "shield": [
        "战士"
    ]
}

WEAPON_NAME_SUFFIX = {
    "sword": [
        "大剑",
        "之刃",
        "战刃",
        "长剑"
    ],
    "staff": [
        "法杖",
        "之杖",
        "魔杖",
        "秘杖"
    ],
    "bow": [
        "长弓",
        "之弓",
        "猎弓",
        "战弓"
    ],
    "mace": [
        "权杖",
        "圣杖",
        "之杖",
        "法杖"
    ],
    "dagger": [
        "匕首",
        "短刃",
        "之匕",
        "毒刃"
    ],
    "fist": [
        "拳套",
        "之拳",
        "铁拳",
        "爪套"
    ],
    "spear": [
        "之枪",
        "长枪",
        "战枪",
        "骑枪"
    ],
    "shield": [
        "之盾",
        "盾牌",
        "重盾",
        "圆盾"
    ]
}

WEAPON_FLAVOR = {
    "sword": {
        "crit": 0.02,
        "desc": "剑类武器：攻守均衡，暴击 +2%"
    },
    "staff": {
        "matk": 0.08,
        "desc": "法杖：魔攻额外 +8%"
    },
    "bow": {
        "spd_fix": 4,
        "crit": 0.02,
        "desc": "长弓：速度 +4、暴击 +2%"
    },
    "mace": {
        "matk": 0.08,
        "hp_fix": 60,
        "desc": "权杖：魔攻 +8%、生命 +60"
    },
    "dagger": {
        "crit": 0.05,
        "desc": "匕首：暴击额外 +5%"
    },
    "fist": {
        "atk": 0.08,
        "desc": "拳套：攻击额外 +8%"
    },
    "spear": {
        "atk": 0.08,
        "crit": 0.01,
        "desc": "长枪：攻击额外 +8%、暴击 +1%"
    },
    "shield": {
        "def": 0.08,
        "hp_fix": 30,
        "desc": "盾牌：防御额外 +8%、生命 +30"
    }
}

EQUIP_NAME_PREFIX = {
    "white": [
        "陈旧",
        "磨损",
        "普通",
        "粗制"
    ],
    "green": [
        "精良",
        "坚韧",
        "锋利",
        "强固"
    ],
    "blue": [
        "稀有",
        "附魔",
        "寒霜",
        "烈焰",
        "雷霆",
        "秘银"
    ],
    "purple": [
        "史诗",
        "龙鳞",
        "星辉",
        "深渊",
        "圣光",
        "虚空"
    ],
    "orange": [
        "传说",
        "王室",
        "精工",
        "古制",
        "传承",
        "王权"
    ]
}

# v58 装备前缀属性倾向：前缀名 → 额外属性（名字风格真实影响手感）
# 值：固定加成 {属性: 数值}；crit/dodge 为小数概率
EQUIP_PREFIX_FLAVOR = {
    "寒霜": {"matk": 3, "spd": 1},
    "烈焰": {"atk": 3},
    "雷霆": {"crit": 0.015},
    "秘银": {"def": 3, "mdef": 2},
    "龙鳞": {"hp": 25, "def": 2},
    "星辉": {"spd": 3, "crit": 0.01},
    "深渊": {"atk": 2, "matk": 2},
    "圣光": {"mdef": 3, "hp": 15},
    "虚空": {"atk": 3, "hp": -10},
    "王室": {"def": 4, "mdef": 2},
    "精工": {"atk": 2, "crit": 0.01},
    "古制": {"hp": 30, "def": 2},
    "传承": {"matk": 3, "mp": 20},
    "王权": {"atk": 3, "def": 2, "hp": 10},
    "附魔": {"matk": 2, "spd": 1},
    "坚韧": {"def": 1, "hp": 8},
    "锋利": {"atk": 2, "crit": 0.005},
    "强固": {"def": 2, "hp": 5},
    "精良": {"hp": 6},
    "陈旧": {"hp": -4},
    "磨损": {"def": -1},
    "粗制": {"atk": -1},
}

EQUIP_NAME_SUFFIX = {
    "weapon": [
        "大剑",
        "之刃",
        "战刃",
        "法杖",
        "之杖",
        "长弓",
        "之弓",
        "权杖",
        "圣杖",
        "匕首",
        "短刃",
        "拳套",
        "之拳"
    ],
    "helm": [
        "头盔",
        "之冠",
        "战盔"
    ],
    "armor": [
        "胸甲",
        "战甲",
        "护甲"
    ],
    "legs": [
        "护腿",
        "战裙",
        "胫甲"
    ],
    "boots": [
        "之靴",
        "战靴",
        "皮靴"
    ],
    "ring": [
        "之戒",
        "指环",
        "戒指"
    ],
    "necklace": [
        "项链",
        "护符",
        "吊坠"
    ]
}

AFFIX_COUNT = {
    "white": 0,
    "green": 1,
    "blue": 2,
    "purple": 3,
    "orange": [
        3,
        4
    ]
}

AFFIX_RATIO = {
    "green": 0.25,
    "blue": 0.25,
    "purple": 0.3,
    "orange": 0.3
}

AFFIX_POOL = [
    "atk",
    "def",
    "matk",
    "mdef",
    "hp",
    "mp",
    "spd",
    "crit",
    "dodge"
]

AFFIX_FALLBACK = {
    "atk": [
        2,
        1.5
    ],
    "def": [
        1.5,
        1.0
    ],
    "matk": [
        2,
        1.5
    ],
    "mdef": [
        1.5,
        1.0
    ],
    "hp": [
        6,
        4
    ],
    "mp": [
        4,
        2.5
    ],
    "spd": [
        1,
        0.8
    ]
}

# 品质颜色档位中文名 → 英文 ID（v48：玩家输入"蓝"→ blue 查询用）
QUALITY_CN = {
    "white": "白", "green": "绿", "blue": "蓝", "purple": "紫", "orange": "橙",
}

# 武器类型英文 ID → 中文名（v48：显示用）
WT_CN = {
    "sword": "剑", "staff": "法杖", "bow": "弓",
    "mace": "权杖", "dagger": "匕首", "fist": "拳套",
    "spear": "枪", "shield": "盾",
}
