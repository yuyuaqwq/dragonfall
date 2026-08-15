# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - guild.py"""
GUILD_CONFIG = {
    "create_cost": 1000,       # 创建公会金币（策划 11 章 3.1：1000 金币）
    "create_level": 30,        # 创建公会等级要求（策划 11 章 3.1：Lv.30）
    "sign_exp": 20,            # 公会签到：公会经验
    "sign_contribute": 10,     # 公会签到：个人贡献
    "sign_gold": 50,           # 公会签到：个人金币
    "task_exp": 40,            # 公会任务：公会经验
    "task_contribute": 20,     # 公会任务：个人贡献
    "task_gold": 100,          # 公会任务：个人金币
    "kill_task": 5,            # 公会任务击杀数
    "donate_items": 3,         # 公会捐献：上交材料份数（策划 11 章 4 种任务：讨伐/捐献/金币/副本 → 简化落地：讨伐＋捐献）
    "exp_bonus_per_level": 0.01,  # 每级公会经验加成
    "max_bonus": 0.20,         # 公会经验加成上限
    # v116 公会成长纵深：职位体系任命门槛（公会等级）
    "vice_leader_level": 3,    # 任命『副会长』需公会 Lv.3
    "elite_level": 1,          # 任命『精英』需公会 Lv.1（即无门槛）
}

# v116 公会职位体系：guild_members.role 四档（leader/vice_leader/elite/member）
# 结构：{role: (职位名, 展示图标)}
GUILD_ROLES = {
    "leader": ("会长", "👑"),
    "vice_leader": ("副会长", "🛡️"),
    "elite": ("精英", "⭐"),
    "member": ("成员", "⚔️"),
}
# 会长可任命的目标职位（不含成员——成员是默认降级，用『免职』或直接任为精英? 设计只任命提升）
GUILD_APPOINTABLE = ("vice_leader", "elite")

# v116 公会商店：用公会积分（guild_members.contribute）兑换。
# 结构：{编号: {name, cost(积分), min_level(公会等级门槛), daily_limit(每日限购,0不限制),
#              item_key(背包 key), item_data(物品 dict)}}
GUILD_SHOP_ITEMS = {
    1: {
        "name": "淬火石",
        "cost": 30, "min_level": 1, "daily_limit": 10,
        "item_key": "gs_qch_stone",
        "item_data": {"name": "淬火石", "type": "材料", "stackable": True,
                      "price": 15, "desc": "公会商店出品的强化石，用于装备强化"},
        "msg": "⚒️ 强化石到手！『强化』给装备升个级吧～",
    },
    2: {
        "name": "图纸残页",
        "cost": 50, "min_level": 2, "daily_limit": 5,
        "item_key": "gs_tu_zhi_pian",
        "item_data": {"name": "图纸残页", "type": "材料", "stackable": True,
                      "price": 10, "desc": "残缺的锻造图纸，s24/s25 等支线交付物"},
        "msg": "📜 图纸残页到手，凑齐做些支线吧～",
    },
    3: {
        "name": "力量药剂",
        "cost": 80, "min_level": 2, "daily_limit": 3,
        "item_key": "gs_str_potion",
        "item_data": {"name": "力量药剂", "type": "消耗品", "stackable": True,
                      "price": 100, "effect": "buff_atk", "desc": "战斗中使用，3 回合攻击 + 30%"},
        "msg": "💊 『使用 力量药剂』3 回合攻击 + 30%！",
    },
    4: {
        "name": "彩虹露",
        "cost": 120, "min_level": 3, "daily_limit": 3,
        "item_key": "gs_cai_hong_lu",
        "item_data": {"name": "彩虹露", "type": "材料", "stackable": True,
                      "price": 60, "desc": "炼金/锻造的进阶材料，稀有掉落可遇不可求"},
        "msg": "🌈 稀有材料彩虹露入包！去炼金或锻造看看～",
    },
    5: {
        "name": "高级强化石",
        "cost": 200, "min_level": 4, "daily_limit": 2,
        "item_key": "gs_gao_ji_stone",
        "item_data": {"name": "高级强化石", "type": "材料", "stackable": True,
                      "price": 400, "desc": "高纯度强化矿石，高级锻造/强化基石"},
        "msg": "⚙️ 高级强化石到手，这可是高级装备的基石！",
    },
    6: {
        "name": "藏宝图碎片",
        "cost": 160, "min_level": 3, "daily_limit": 0,
        "item_key": "gs_treasure_shard",
        "item_data": {"name": "藏宝图碎片", "type": "材料", "stackable": True,
                      "price": 80, "desc": "拼凑起来也许能找到意外之财"},
        "msg": "🗺️ 藏宝图碎片到手，集齐也许有大发现！",
    },
}

# v116 公会技能：学习消耗公会积分 + 公会等级门槛；每级递增，最高 5 级。
# 结构：{key: {name, desc(每级效果说明), max_level, level_costs[每级积分], level_guild_lv[每级公会门槛]}}
# 战斗加成挂接延后（见 commands/social.py guild_skill_view 注释）——本轮仅数据 + 展示。
GUILD_SKILLS = {
    "atk": {
        "name": "攻击强化",
        "desc": "全员攻击力 +2%",
        "max_level": 5,
        "level_costs": [0, 60, 120, 200, 300],      # level_costs[i] = 学到 i 级的积分（1 级起）; 0 占位
        "level_guild_lv": [0, 1, 2, 3, 4],          # 学第 i 级需公会等级
    },
    "def": {
        "name": "防御强化",
        "desc": "全员防御 +2%",
        "max_level": 5,
        "level_costs": [0, 60, 120, 200, 300],
        "level_guild_lv": [0, 1, 2, 3, 4],
    },
    "exp": {
        "name": "经验强化",
        "desc": "全员打怪经验 +2%",
        "max_level": 5,
        "level_costs": [0, 80, 160, 260, 400],
        "level_guild_lv": [0, 1, 3, 4, 5],
    },
}

