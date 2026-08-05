# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - classes.py（v48 key 转 ID）"""
CLASSES = {
    "cls_zhan_shi": {
        "desc": "身穿重甲、手持巨剑的钢铁壁垒，正面硬刚一切敌人。",
        "icon": "🛡️",
        "role": "坦克",
        "evolve": [
            "狂战士(30)"
        ],
        "evolve_branches": {
            1: [
                "狂战士",
                "圣骑士"
            ]
        },
        "base": {
            "hp": 150,
            "mp": 40,
            "atk": 18,
            "def": 14,
            "matk": 6,
            "mdef": 10,
            "spd": 10,
            "crit": 0.05,
            "dodge": 0.03
        },
        "growth": {
            "hp": 22,
            "mp": 3,
            "atk": 3.2,
            "def": 2.6,
            "matk": 0.5,
            "mdef": 1.2,
            "spd": 0.6
        },
        "weapon_type": "sword",
        "name": "战士"
    },
    "cls_fa_shi": {
        "desc": "掌控元素之力的施法者，输出爆炸但身板脆弱。",
        "icon": "🔥",
        "role": "输出",
        "evolve": [
            "元素大师(30)"
        ],
        "evolve_branches": {
            1: [
                "元素大师",
                "冰霜贤者"
            ]
        },
        "base": {
            "hp": 90,
            "mp": 120,
            "atk": 8,
            "def": 7,
            "matk": 22,
            "mdef": 14,
            "spd": 12,
            "crit": 0.08,
            "dodge": 0.05
        },
        "growth": {
            "hp": 10,
            "mp": 10,
            "atk": 0.8,
            "def": 1.0,
            "matk": 3.8,
            "mdef": 1.8,
            "spd": 0.8
        },
        "weapon_type": "staff",
        "name": "法师"
    },
    "cls_you_xia": {
        "desc": "敏捷的弓箭手，箭无虚发，暴击与闪避的艺术家。",
        "icon": "🏹",
        "role": "输出",
        "evolve": [
            "猎魔人(30)"
        ],
        "evolve_branches": {
            1: [
                "猎魔人",
                "风行者"
            ]
        },
        "base": {
            "hp": 110,
            "mp": 60,
            "atk": 15,
            "def": 10,
            "matk": 8,
            "mdef": 9,
            "spd": 16,
            "crit": 0.15,
            "dodge": 0.12
        },
        "growth": {
            "hp": 14,
            "mp": 5,
            "atk": 2.6,
            "def": 1.6,
            "matk": 0.8,
            "mdef": 1.0,
            "spd": 1.8
        },
        "weapon_type": "bow",
        "name": "游侠"
    },
    "cls_mu_shi": {
        "desc": "信仰圣光的神职者，能打能奶，队伍的灵魂。",
        "icon": "✨",
        "role": "治疗",
        "evolve": [
            "圣武士(30)"
        ],
        "evolve_branches": {
            1: [
                "圣武士",
                "神谕者"
            ]
        },
        "base": {
            "hp": 100,
            "mp": 110,
            "atk": 10,
            "def": 11,
            "matk": 16,
            "mdef": 16,
            "spd": 11,
            "crit": 0.06,
            "dodge": 0.06
        },
        "growth": {
            "hp": 12,
            "mp": 9,
            "atk": 1.2,
            "def": 1.8,
            "matk": 2.6,
            "mdef": 2.4,
            "spd": 0.7
        },
        "weapon_type": "mace",
        "name": "牧师"
    },
    "cls_ci_ke": {
        "desc": "暗影中的利刃，出手必见血，暴击与闪避的极致。",
        "icon": "🗡️",
        "role": "输出",
        "evolve": [
            "影舞者(30)"
        ],
        "evolve_branches": {
            1: [
                "影舞者",
                "毒刃者"
            ]
        },
        "base": {
            "hp": 95,
            "mp": 70,
            "atk": 17,
            "def": 9,
            "matk": 7,
            "mdef": 8,
            "spd": 19,
            "crit": 0.2,
            "dodge": 0.18
        },
        "growth": {
            "hp": 12,
            "mp": 5,
            "atk": 3.0,
            "def": 1.3,
            "matk": 0.6,
            "mdef": 0.9,
            "spd": 2.2
        },
        "weapon_type": "dagger",
        "name": "刺客"
    },
    "cls_wu_seng": {
        "desc": "以拳入道的修行者，拳拳到肉，连击与反击的行家。",
        "icon": "🥊",
        "role": "辅助",
        "evolve": [
            "拳师(30)"
        ],
        "evolve_branches": {
            1: [
                "拳师",
                "金刚罗汉"
            ]
        },
        "base": {
            "hp": 135,
            "mp": 55,
            "atk": 15,
            "def": 12,
            "matk": 6,
            "mdef": 11,
            "spd": 14,
            "crit": 0.1,
            "dodge": 0.12
        },
        "growth": {
            "hp": 18,
            "mp": 4,
            "atk": 2.8,
            "def": 2.0,
            "matk": 0.5,
            "mdef": 1.6,
            "spd": 1.4
        },
        "weapon_type": "fist",
        "name": "武僧"
    }
}
