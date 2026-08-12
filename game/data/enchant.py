# -*- coding: utf-8 -*-
from .runes import RUNES, RUNE_EFFECT_NAMES
"""《剑与魔法》数据层 - enchant.py(v48 ENCHANT_SLOTS 品质英文 ID)"""
ENCHANT_SLOTS = {
    "blue": 1,
    "purple": 2,
    "orange": 2
}

ENCHANT_RECIPES = {
    "atk": {
        "label": "攻击",
        "mats": [
            "核心",
            "獠牙",
            "爪",
            "之刃",
            "权杖",
            "战刃",
            "剑"
        ],
        "ratio": 0.18,
        "cost": 500
    },
    "matk": {
        "label": "魔攻",
        "mats": [
            "法珠",
            "法杖",
            "结晶",
            "经卷",
            "法球",
            "沉木",  # M14 P1 死材料消费点: mat_chen_mu（沉船墓地采集，策划 13:437 附魔材料）
        ],
        "ratio": 0.18,
        "cost": 500
    },
    "def": {
        "label": "防御",
        "mats": [
            "皮",
            "甲",
            "壳",
            "盾牌",
            "铠"
        ],
        "ratio": 0.18,
        "cost": 400
    },
    "mdef": {
        "label": "魔防",
        "mats": [
            "徽章",
            "羽毛",
            "护符",
            "圣印",
            "之羽"
        ],
        "ratio": 0.18,
        "cost": 400
    },
    "hp": {
        "label": "生命",
        "mats": [
            "精华",
            "血肉",
            "腐肉",
            "之心",
            "粘液",
            "之泪"
        ],
        "ratio": 0.2,
        "cost": 350
    },
    "spd": {
        "label": "速度",
        "mats": [
            "羽",
            "翼",
            "翎羽",
            "蹄",
            "蝙蝠翼",  # M14 P1 死材料消费点: mat_bian_fu_yi（黑森林/黄昏岭道采集，策划 13:107 附魔材料）
        ],
        "ratio": 0.16,
        "cost": 450
    },
    "crit": {
        "label": "暴击",
        "mats": [
            "碎片",
            "之尘",
            "图腾",
            "棱镜"
        ],
        "ratio": 0.02,
        "cost": 800
    }
}

ENCHANT_CRIT_CHANCE = 0.05

ENCHANT_MAX_VALUE = {
    "crit": 0.04,
    "dodge": 0.03
}

ENCHANT_STONES = RUNES

ENCHANT_EFFECT_NAMES = RUNE_EFFECT_NAMES
