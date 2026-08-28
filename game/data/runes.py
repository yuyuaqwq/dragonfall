# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - runes.py(v48 key=effect ID)"""
RUNES = {
    "rn_brutal": {
        "quality": "purple",
        "effect": "brutal",
        "lvl": {
            1: 0.3,
            2: 0.5,
            3: 0.8
        },
        "desc": "暴击伤害＋{v}%",
        "cost": 1500,
        "icon": "💢",
        "name": "残忍"
    },
    "rn_armor_pierce": {
        "quality": "purple",
        "effect": "armor_pierce",
        "lvl": {
            1: 0.2,
            2: 0.3,
            3: 0.4
        },
        "desc": "攻击无视 {v}% 防御",
        "cost": 1500,
        "icon": "🗡️",
        "name": "破甲"
    },
    "rn_burn": {
        "quality": "blue",
        "effect": "burn",
        "lvl": {
            1: 1,
            2: 2,
            3: 3
        },
        "desc": "攻击附带灼烧 {v} 层",
        "cost": 800,
        "icon": "🔥",
        "name": "灼热"
    },
    "rn_freeze": {
        "quality": "blue",
        "effect": "freeze",
        "lvl": {
            1: 0.1,
            2: 0.15,
            3: 0.2
        },
        "desc": "攻击 {v}% 概率冻结敌人",
        "cost": 900,
        "icon": "❄️",
        "name": "冰霜"
    },
    "rn_chain": {
        "quality": "orange",
        "effect": "chain",
        "lvl": {
            1: [
                0.1,
                0.7
            ],
            2: [
                0.15,
                1.0
            ],
            3: [
                0.2,
                1.4
            ]
        },
        "desc": "攻击 {v1}% 概率雷击 {v2}% 伤害",
        "cost": 2200,
        "icon": "⚡",
        "name": "连锁"
    },
    "rn_weaken": {
        "quality": "blue",
        "effect": "weaken",
        "lvl": {
            1: 0.1,
            2: 0.15,
            3: 0.2
        },
        "desc": "攻击使敌人攻击－{v}%(3回合)",
        "cost": 900,
        "icon": "😵",
        "name": "虚弱"
    },
    "rn_magic_break": {
        "quality": "purple",
        "effect": "magic_break",
        "lvl": {
            1: 0.1,
            2: 0.15,
            3: 0.2
        },
        "desc": "魔法伤害＋{v}%",
        "cost": 1400,
        "icon": "🔮",
        "name": "破魔"
    },
    "rn_lifesteal": {
        "quality": "purple",
        "effect": "lifesteal",
        "lvl": {
            1: 0.05,
            2: 0.08,
            3: 0.12
        },
        "desc": "造成伤害的 {v}% 回复生命",
        "cost": 1200,
        "icon": "🩸",
        "name": "吸血"
    },
    "rn_regen": {
        "quality": "purple",
        "effect": "regen",
        "lvl": {
            1: 0.01,
            2: 0.02,
            3: 0.03
        },
        "desc": "每回合回复 {v}% 生命",
        "cost": 2000,
        "icon": "✨",
        "name": "治愈"
    },
    "rn_barrier": {
        "quality": "orange",
        "effect": "barrier",
        "lvl": {
            1: [
                0.15,
                0.08
            ],
            2: [
                0.25,
                0.1
            ],
            3: [
                0.35,
                0.15
            ]
        },
        "desc": "受击 {v1}% 概率获得 {v2}% 护盾",
        "cost": 2500,
        "icon": "🛡️",
        "name": "壁垒"
    },
    "rn_thorns": {
        "quality": "purple",
        "effect": "thorns",
        "lvl": {
            1: 0.1,
            2: 0.15,
            3: 0.2
        },
        "desc": "受击反弹 {v}% 伤害",
        "cost": 1600,
        "icon": "🌵",
        "name": "荆棘"
    },
    "rn_swift": {
        "quality": "blue",
        "effect": "swift",
        "lvl": {
            1: 0.08,
            2: 0.12,
            3: 0.18
        },
        "desc": "速度＋{v}%",
        "cost": 800,
        "icon": "💨",
        "name": "疾风"
    },
    "rn_ironwall": {
        "quality": "blue",
        "effect": "ironwall",
        "lvl": {
            1: 0.08,
            2: 0.12,
            3: 0.18
        },
        "desc": "防御＋{v}%",
        "cost": 850,
        "icon": "🏰",
        "name": "铁壁"
    },
    "rn_mana_flow": {
        "quality": "blue",
        "effect": "mana_flow",
        "lvl": {
            1: 0.1,
            2: 0.15,
            3: 0.25
        },
        "desc": "MP 消耗－{v}%",
        "cost": 950,
        "icon": "🌀",
        "name": "聚能"
    },
    "rn_scavenger": {
        "quality": "blue",
        "effect": "scavenger",
        "lvl": {
            1: 0.15,
            2: 0.25,
            3: 0.4
        },
        "desc": "金币掉落＋{v}%",
        "cost": 1000,
        "icon": "💰",
        "name": "拾荒"
    },
    "rn_exp_bless": {
        "quality": "blue",
        "effect": "exp_bless",
        "lvl": {
            1: 0.1,
            2: 0.15,
            3: 0.25
        },
        "desc": "经验获取＋{v}%",
        "cost": 1000,
        "icon": "📖",
        "name": "睿智"
    }
}

RUNE_CONFLICTS = [
    [
        "burn",
        "freeze"
    ],
    [
        "barrier",
        "thorns"
    ],
    [
        "scavenger",
        "exp_bless"
    ]
]

RUNE_DROP = {
    "blue": 0.018,
    "purple": 0.008,
    "orange": 0.0025
}

RUNE_EFFECT_NAMES = {
    "brutal": "残忍",
    "armor_pierce": "破甲",
    "burn": "灼热",
    "lifesteal": "吸血",
    "freeze": "冰霜",
    "swift": "疾风",
    "barrier": "壁垒",
    "regen": "治愈",
    "chain": "连锁",
    "weaken": "虚弱",
    "thorns": "荆棘",
    "scavenger": "拾荒",
    "exp_bless": "睿智",
    "ironwall": "铁壁",
    "mana_flow": "聚能",
    "magic_break": "破魔"
}

RUNE_LEVEL_ROMAN = {
    1: "I",
    2: "II",
    3: "III"
}

# ============ v136 符文制作（Phase 3：掉落 → 掉落+可制作） ============
# 消耗规则：品质决定素材/碎片/金币
#   blue   → 怪物素材×2 + 符文碎片×3 + 制作费  cost//2 金
#   purple → 怪物素材×3 + 符文碎片×4 + 制作费  cost//2 金
#   orange → 怪物素材×4 + 符文碎片×6 + 制作费  cost//2 金
# 素材 key 用「怪物掉落主材」：裂鬃獠牙(野猪王·裂鬃)/巨魔獠牙/兽人獠牙（龙脉路线核心素材）
# 素材池（可扩展）：裂鬃獠牙/巨魔獠牙/兽人獠牙/灰影狼牙/狼王牙
RUNE_CRAFT = {
    "rn_brutal":      {"mat": "mat_lie_zong_liao_ya", "count": 3},
    "rn_armor_pierce": {"mat": "mat_lie_zong_liao_ya", "count": 3},
    "rn_magic_break":  {"mat": "mat_lie_zong_liao_ya", "count": 3},
    "rn_lifesteal":    {"mat": "mat_lie_zong_liao_ya", "count": 3},
    "rn_regen":        {"mat": "mat_lie_zong_liao_ya", "count": 3},
    "rn_thorns":       {"mat": "mat_lie_zong_liao_ya", "count": 3},
    "rn_burn":         {"mat": "mat_ju_mo_liao_ya", "count": 2},
    "rn_freeze":       {"mat": "mat_ju_mo_liao_ya", "count": 2},
    "rn_weaken":       {"mat": "mat_ju_mo_liao_ya", "count": 2},
    "rn_swift":        {"mat": "mat_ju_mo_liao_ya", "count": 2},
    "rn_ironwall":     {"mat": "mat_ju_mo_liao_ya", "count": 2},
    "rn_mana_flow":    {"mat": "mat_ju_mo_liao_ya", "count": 2},
    "rn_scavenger":    {"mat": "mat_shou_ren_liao_ya", "count": 2},
    "rn_exp_bless":    {"mat": "mat_shou_ren_liao_ya", "count": 2},
    "rn_chain":        {"mat": "mat_shou_ren_liao_ya", "count": 4},
    "rn_barrier":      {"mat": "mat_shou_ren_liao_ya", "count": 4},
}
# 制作碎片消耗（品质 → 符文碎片数量）
RUNE_CRAFT_SHARDS = {"blue": 3, "purple": 4, "orange": 6}
# 符文碎片材料 key（items.py 已定义 mat_fu_wen_sui_pian，名字『符文碎片』，price 100）
RUNE_SHARD_KEY = "mat_fu_wen_sui_pian"
