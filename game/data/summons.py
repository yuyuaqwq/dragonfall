# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - summons.py (v107 召唤物系统)

召唤物模板：属性按玩家实时属性比例缩放（召唤物永远跟玩家强度走，不过时），
生成时吃 summon_power 强化（隐藏职业暗影祭司/星语线专属属性）。

字段说明：
- atk_ratio/hp_ratio/def_ratio：相对玩家 atk/max_hp/def 的比例
- dmg_type：召唤物自动攻击的伤害类型（phys/magi/true，v107 四层架构）
- limit：同类型并存上限（亡灵骷髅海可叠 3，植物藤蔓守卫 2）
- bodyguard：挡刀概率（敌人攻击时由召唤物承受的概率）

v113 调整：游侠攻线改为自然系「林语者」后，召唤下放基础职业——
兽群流（幼狼→狼王→影狼进化链）随隐藏线收敛删除，新增植物召唤（数量流）：
藤蔓守卫（基础攻线召唤）→ 古树守卫（T3 强化召唤）。
"""
SUMMONS = {
    # 暗影祭司·骷髅海（数量流：可叠 3，自动攻击 + 高挡刀）
    "skeleton": {
        "name": "骷髅兵", "icon": "💀",
        "atk_ratio": 0.50, "hp_ratio": 0.35, "def_ratio": 0.40,
        "dmg_type": "phys", "limit": 3, "bodyguard": 0.40,
        "rank": 1, "reach": 1,   # v27b：肉盾/近战召唤物 → 前排 rank1，近战 reach1
    },
    # 林语者·藤蔓守卫（基础攻线召唤，数量流：可叠 2，自动攻击 + 挡刀）
    "vine_guard": {
        "name": "藤蔓守卫", "icon": "🌿",
        "atk_ratio": 0.45, "hp_ratio": 0.30, "def_ratio": 0.35,
        "dmg_type": "phys", "limit": 2, "bodyguard": 0.35,
        "rank": 1, "reach": 1,   # v27b：肉盾/近战召唤物 → 前排 rank1，近战 reach1
    },
    # 万木之灵·古树守卫（T3 强化召唤，单只重装，挡刀率高）
    "treant": {
        "name": "古树守卫", "icon": "🌳",
        "atk_ratio": 0.75, "hp_ratio": 0.55, "def_ratio": 0.60,
        "dmg_type": "phys", "limit": 1, "bodyguard": 0.50,
        "rank": 1, "reach": 1,   # v27b：重装/近战召唤物 → 前排 rank1，近战 reach1
    },
}
