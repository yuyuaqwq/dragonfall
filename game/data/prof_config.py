# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - prof_config.py（v98.1：副业配置数据下沉）

原 hardcode 在 commands/economy.py 类属性，数据下沉后：
- 加副业 = 在此文件加配置，零代码改动
- 导师与 data/npcs.py 的对话 unlock_prof 对应；改导师/城市只改这里
"""
# 副业导师映射：副业 key → (导师名, 所在城)。副业必须先找导师拜师（对话 unlock_prof）才解锁
PROF_TUTORS = {
    "gather": ("草药师·艾琳", "橡木镇"),
    "mining": ("矿工长·巴尔金", "铁港城"),
    "fishing": ("老渔夫·马库斯", "铁港城"),
    "cooking": ("大厨·罗莎", "白鹿城"),
    "alchemy": ("炼金术士·梅尔文", "晨曦城"),
    "craft": ("铁匠大师·奥格", "铁港城"),
    "enhance": ("强化师·克拉拉", "白鹿城"),
    "enchant": ("符文大师·吉姆利", "铁砧要塞"),
}

# 等待型副业基准等待（秒）随机范围：fish/gather 45~75，mining 65~115
# 副业等级每级 -5%（上限 -50%），保底 10 秒
PROF_WAIT_BASE = {
    "fishing": (45, 75, "垂钓"),
    "gather": (45, 75, "采集"),
    "mining": (65, 115, "挖掘"),
}

# 每日副业任务：副业 key → (任务名, 需要次数, 奖励金币)
# v101.30: 奖励统一 50 金币 + 50 副业经验（见 economy.py _daily_prof_bump；经验是主奖励，
#           金币为成本零头补贴——旧版强化 1 次成本 50 金却只奖 40 金，制造型任务全负收益）
DAILY_PROF_TASKS = {
    "gather": ("采集", 5, 50),
    "mining": ("挖掘", 3, 50),
    "fishing": ("垂钓", 5, 50),
    "alchemy": ("炼金合成", 2, 50),
    "craft": ("锻造装备", 1, 50),
    "cooking": ("烹饪料理", 2, 50),
    "enhance": ("强化装备", 1, 50),
    "enchant": ("附魔装备", 1, 50),
}

# 背包过滤类型（『背包 材料』等）
BAG_FILTER_TYPES = ["装备", "材料", "消耗品", "符文", "宠物蛋", "坐骑", "图纸", "鱼"]

# 副业体力消耗（commands/economy.py 各副业命令 _spend_stamina 数据源；等待型 5 / 制造型 10）
PROF_STAMINA_COST = {
    "gather": 5, "mining": 5, "fishing": 5, "cooking": 5,
    "alchemy": 10, "craft": 10, "enhance": 10, "enchant": 10,
}

# 等待型副业：等级每级等待衰减比例 / 保底等待秒数（economy._prof_wait_duration 数据源）
PROF_WAIT_DECAY = 0.05
PROF_WAIT_FLOOR = 10

# 挖掘矿石类材料名关键词（economy._settle_mining 数据源；原 _ORE_KW 迁移）
MINING_KEYWORDS = ["矿石", "秘银", "精钢", "结晶", "核心", "碎片", "石", "精华"]

# 回收率表：物品类型 → 出售回收率（economy._pawn_rate 数据源）
PAWN_RATES = {
    "equip": 1.0,        # 装备→铁匠/工坊（原价）
    "pet_mount": 0.5,    # 宠物蛋/坐骑缰绳
    "consumable": 0.85,  # 非材料消耗品（药水/食物/卷轴/炼金/烹饪产物）
    "mat_smith": 0.9,    # 材料→铁匠铺（矿石/木材/兽材/宝石）
    "mat_alchemy": 0.9,  # 材料→炼金铺（草药/精华）
    "mat_shop": 0.8,     # 材料→商店（食材/织物/杂物）
}
