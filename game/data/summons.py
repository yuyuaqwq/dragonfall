# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - summons.py (v107 召唤物系统)

召唤物模板：属性按玩家实时属性比例缩放（召唤物永远跟玩家强度走，不过时），
生成时吃 summon_power 强化（隐藏职业亡灵术士/兽王专属属性）。

字段说明：
- atk_ratio/hp_ratio/def_ratio：相对玩家 atk/max_hp/def 的比例
- dmg_type：召唤物自动攻击的伤害类型（phys/magi/true，v107 四层架构）
- limit：同类型并存上限（亡灵骷髅海可叠 3，兽王单宠 1）
- bodyguard：挡刀概率（敌人攻击时由召唤物承受的概率）
"""
SUMMONS = {
    # 亡灵术士·骷髅海（数量流：可叠 3，自动攻击 + 高挡刀）
    "skeleton": {
        "name": "骷髅兵", "icon": "💀",
        "atk_ratio": 0.55, "hp_ratio": 0.35, "def_ratio": 0.40,
        "dmg_type": "phys", "limit": 3, "bodyguard": 0.40,
    },
    # 兽王·单宠进化（质量流：1 宠，宠强人弱；形态随技能等级进化）
    "wolf_cub": {
        "name": "幼狼", "icon": "🐺",
        "atk_ratio": 0.65, "hp_ratio": 0.40, "def_ratio": 0.45,
        "dmg_type": "phys", "limit": 1, "bodyguard": 0.50,
    },
    "wolf_king": {
        "name": "狼王", "icon": "🐺",
        "atk_ratio": 0.80, "hp_ratio": 0.50, "def_ratio": 0.55,
        "dmg_type": "phys", "limit": 1, "bodyguard": 0.55,
    },
    "shadow_wolf": {
        "name": "影狼", "icon": "🐺",
        "atk_ratio": 1.00, "hp_ratio": 0.60, "def_ratio": 0.65,
        "dmg_type": "true", "limit": 1, "bodyguard": 0.60,
    },
}
