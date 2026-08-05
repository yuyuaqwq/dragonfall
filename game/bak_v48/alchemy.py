# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - alchemy.py（从旧 pyc 恢复，v48 转换前）"""

ALCHEMY_RECIPES = {
    "治疗药水": {
        "cost": {
            "狼皮": 2,
            "妖精之尘": 1
        },
        "product": {
            "i_treatment_potion": 1
        },
        "desc": "用兽皮与妖精之尘炼制的恢复药水"
    },
    "超级治疗药水": {
        "cost": {
            "圣光羽毛": 2,
            "火焰核心": 1
        },
        "product": {
            "i_super_treatment": 1
        },
        "desc": "高级恢复药水"
    },
    "魔力药水": {
        "cost": {
            "妖精之尘": 2,
            "蜘蛛毒囊": 1
        },
        "product": {
            "i_mana_potion": 1
        },
        "desc": "恢复魔力"
    },
    "超级魔力药水": {
        "cost": {
            "雪之精华": 2,
            "灵魂碎片": 1
        },
        "product": {
            "i_super_mana": 1
        },
        "desc": "高级魔力恢复"
    },
    "强化石": {
        "cost": {
            "熔岩石": 2,
            "深渊精钢": 1
        },
        "product": {
            "mat_强化石": 1
        },
        "desc": "强化装备的必备材料"
    },
    "精炼强化石": {
        "cost": {
            "强化石": 2,
            "火焰核心": 1
        },
        "product": {
            "mat_精炼强化石": 1
        },
        "desc": "高品质强化材料，强化成功率更高"
    },
    "回城卷轴": {
        "cost": {
            "鬼魂精华": 1,
            "妖精之尘": 1
        },
        "product": {
            "i_scroll_escape": 1
        },
        "desc": "瞬间回到维拉镇"
    },
    "幸运护符": {
        "cost": {
            "兽人獠牙": 2,
            "暗影碎片": 1
        },
        "product": {
            "mat_幸运护符": 1
        },
        "desc": "提升打怪掉落率"
    }
}
