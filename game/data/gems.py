# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - gems.py（v136 原石系统）
原石=怪猎护石式随机属性+伊甸属性绑定；5层×2小级=10级阶梯，合成3同级→1上级。
纯数据零逻辑（掉落概率等由 core 层消费）。
"""
# 层 → 名称/数值/合成关系（v136 定稿）
GEM_TIERS = {
    1: {"name": "碎裂", "mult": 0.01},    # 碎裂I
    2: {"name": "碎裂", "mult": 0.015},   # 碎裂II
    3: {"name": "普通", "mult": 0.02},
    4: {"name": "普通", "mult": 0.025},
    5: {"name": "无瑕", "mult": 0.03},
    6: {"name": "无瑕", "mult": 0.035},
    7: {"name": "完美", "mult": 0.04},
    8: {"name": "完美", "mult": 0.045},
    9: {"name": "传说", "mult": 0.05},
    10: {"name": "传说", "mult": 0.06},
}
GEM_TIER_NAMES = {1: "碎裂I", 2: "碎裂II", 3: "普通I", 4: "普通II", 5: "无瑕I", 6: "无瑕II", 7: "完美I", 8: "完美II", 9: "传说I", 10: "传说II"}
# 属性池 23 种（v136 定稿）：面板7 + 百分比14 + 成长2
GEM_STATS = ["hp","mp","atk","def","matk","mdef","spd","crit","dodge","precise","pene_phys","pene_magi","tenacity","luck","cdr","block","lifesteal","thorns","crit_dmg","heal_power","shield_power","exp_bonus","gold_bonus"]
# 孔位表（品质→孔数/孔位级/可插层数）
GEM_SOCKETS = {
    "white": {"count": 0, "tier": "", "min_tier": 0, "max_tier": 0},
    "green": {"count": 0, "tier": "", "min_tier": 0, "max_tier": 0},
    "blue":  {"count": 1, "tier": "S1", "min_tier": 1, "max_tier": 2},   # 碎裂-普通(1-2层)
    "purple":{"count": 2, "tier": "S2", "min_tier": 2, "max_tier": 4},  # 普通-无瑕(2-4层)
    "orange":{"count": 3, "tier": "S3", "min_tier": 3, "max_tier": 10},  # 无瑕-传说(3-10层)，传说可插终盘孔
}
# 打孔费用/副业门槛（v136 定稿）
GEM_DRILL = {
    "blue":  {"cost": 500, "craft_lv": 1},
    "purple":{"cost": 1500, "craft_lv": 3},
    "orange":{"cost": 4000, "craft_lv": 5},
}
# 拆卸费用：原石 500×层数 金；符文 1000×等级 金（放 runes.py 或共用）
GEM_REMOVE_COST = 500   # 原石拆卸 500×层数
RUNE_REMOVE_COST = 1000  # 符文拆卸 1000×等级
# 传说级特效池（仅传说II/传说I触发，机制向）
GEM_LEGENDARY_EFFECTS = ["暴击连击", "击杀回血", "受击反伤", "开局加速"]

# ============ v136 原石掉落配置（掉落表/胜利结算消费；护石式随机追求） ============
# v136 Phase 2 定稿：掉率按一天刷几个反推——普通怪 2% / 精英 5% / 野外 Boss 15% / 副本 Boss 20%。
# 命中才给 1 颗随机原石（不掉 999 上限，与材料/图纸同逻辑）。
GEM_DROP_RATE = {
    "normal": 0.02,
    "elite": 0.05,
    "field_boss": 0.15,
    "instance_boss": 0.20,
}
# 各档层数范围（v136 定稿：普通 1-6 碎裂~无瑕，精英 2-8，Boss 3-10 可出传说）
GEM_DROP_TIER = {
    "normal": (1, 6),
    "elite": (2, 8),
    "field_boss": (3, 10),
    "instance_boss": (3, 10),
}
# Boss 专属原石固定属性倾向（v136 定稿：怪物名 → 固定属性；未收录 Boss 走随机属性池）
# 裂鬃=破甲倾向（pene_phys）/ 深海龙王·敖澜=法穿倾向（pene_magi）/ 灰烬使者=暴击倾向（crit）
GEM_BOSS_FIXED = {
    "裂鬃": "pene_phys",
    "野猪王·裂鬃": "pene_phys",
    "深海龙王·敖澜": "pene_magi",
    "灰烬使者": "crit",
}
