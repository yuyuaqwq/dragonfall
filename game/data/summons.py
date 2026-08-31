# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - summons.py (v107 召唤物系统)

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
    # 暗影祭司·骷髅海（v151 隐藏职业删除：骷髅召唤随暗影神谕移除，模板保留兼容旧档）
    "skeleton": {
        "name": "骷髅兵", "icon": "💀",
        "atk_ratio": 0.50, "hp_ratio": 0.35, "def_ratio": 0.40,
        "dmg_type": "phys", "limit": 3, "bodyguard": 0.40,
        "rank": 1, "reach": 1,   # v27b：肉盾/近战召唤物 → 前排 rank1，近战 reach1
    },
    # v151 林语者·藤蔓守卫：纯挡刀（ATK 0，替队友吸收 1 次单体后消失，吃 AOE）
    "vine_guard": {
        "name": "藤蔓守卫", "icon": "🌿",
        "atk_ratio": 0.0, "hp_ratio": 0.25, "def_ratio": 0.35,
        "dmg_type": "phys", "limit": 2, "bodyguard": 1.0,
        "absorb_once": True,  # v151：纯挡刀，吸收 1 次单体后消失
        "eats_aoe": True,     # v151：吃 AOE
        "rank": 1, "reach": 1,
    },
    # v151 万木之灵·古树守卫：重装单只，挡刀 + 全队攻击 +30% 光环，吃 AOE
    "treant": {
        "name": "古树守卫", "icon": "🌳",
        "atk_ratio": 0.30, "hp_ratio": 0.50, "def_ratio": 0.60,
        "dmg_type": "phys", "limit": 1, "bodyguard": 0.50,
        "aura_atk_all": 0.30,  # v151：全队攻击 +30% 光环（常驻）
        "eats_aoe": True,      # v151：吃 AOE
        "rank": 1, "reach": 1,
    },
}
