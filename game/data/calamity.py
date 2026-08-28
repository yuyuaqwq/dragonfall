# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - calamity.py（v136 怪异炼成，怪猎曙光怪异化）

消耗稀有素材（Boss 怨念物/高难副本材料）随机强化装备属性。
- 武器：随机 +攻击/魔攻/暴击/暴伤（可能 -其他，取舍）
- 防具：随机 +防御/魔防（生存向）
- 每件限 3 次（calamity_count 字段，0-3）
- 炼成走机制向/小数值（≤5%），红线：炼成+强化+升级+原石+词条叠加 ≤ 40%

与强化/升级差异化：强化=赌（数值，掉级）｜升级=养（稳定保底）｜炼成=刷（随机强化，取舍，限3次）
"""
CALAMITY_MAX = 3                  # 每件限 3 次
CALAMITY_COST = {
    "gold": 2000,
    "mats": {"mat_yu_jin_he_xin": 1},   # 余烬核心（Boss 稀有素材，v136 新增）
}
# 可随机强化的属性池（面板向小数值）
CALAMITY_STATS = ["atk", "matk", "def", "mdef", "crit", "crit_dmg"]
# 每次随机加成：+3%（90% 正面）/ -1%（10% 负面取舍）
CALAMITY_BONUS = 0.03
CALAMITY_MALUS = 0.01
# 正面概率（90% 加属性，10% 减属性——取舍感）
CALAMITY_POSITIVE_CHANCE = 0.90
