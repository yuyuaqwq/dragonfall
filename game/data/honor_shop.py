# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - honor_shop.py（v99.4：荣誉商店数据化）

原定义在 commands/combat.py 类内（v84 荣誉商店），v99.4 下沉：
- 加商品 = 数据加一行（reward 声明发什么），零代码
- reward.type:
  - "title"  → 发放称号标记（title_id 存 event_state: honor_{title_id}_{qid}=1）
  - "item"   → 发放物品（item_prefix 为背包 id 前缀，item 为物品 dict）
- 展示文案 msg 保持与旧实现逐字一致（行为零变化）
"""
HONOR_SHOP = {
    1: {
        "name": "荣誉勋章", "cost": 300,
        "desc": "PVP 强者称号(攻击＋10)，兑换后在『称号 装备 荣誉勋章』佩戴",
        "reward": {
            "type": "title", "title_id": "medal", "label": "荣誉勋章",
            "msg": "👑 『称号 装备 荣誉勋章』即可佩戴(攻击＋10)！",
        },
    },
    2: {
        "name": "决斗者披风", "cost": 500,
        "desc": "外观装备(纯展示，穿上很帅)",
        "reward": {
            "type": "item", "item_prefix": "cape_",
            "item": {"name": "决斗者披风", "type": "外观", "stackable": False,
                     "price": 0, "desc": "荣誉商店出品的外观披风(纯展示)"},
            "msg": "🦸 穿上它你就是全场最靓的仔～『背包』查看",
        },
    },
    3: {
        "name": "荣誉药剂", "cost": 100,
        "desc": "使用后恢复 50% 生命与魔力",
        "reward": {
            "type": "item", "item_prefix": "pot_",
            "item": {"name": "荣誉药剂", "type": "消耗品", "stackable": True,
                     "price": 0, "heal": 0.5, "mana": 0.5,
                     "desc": "使用后恢复 50% 生命与魔力"},
            "msg": "💊 『使用 荣誉药剂』恢复 50% 血蓝",
        },
    },
    4: {
        "name": "红名清除券", "cost": 800,
        "desc": "使用后立即消除红名状态",
        "reward": {
            "type": "item", "item_prefix": "clearr_",
            "item": {"name": "红名清除券", "type": "消耗品", "stackable": True,
                     "price": 0, "effect": "clear_red",
                     "desc": "使用后立即消除红名状态"},
            "msg": "🎫 『使用 红名清除券』立即洗白～",
        },
    },
}
