# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - refine.py（v172 装备重锻，怪猎派生树）

同系列旧武器 + 稀有素材 + 金钱 → 同系列高阶武器，继承强化/升级等级（投资不沉没）。
派生树：同一基础武器可派生多个方向（玩家做选择）。

首批每系列 1 条重锻链（v136 定稿，后续扩展）：
- 弯刀(Lv14 蓝) → 血誓战剑(Lv36 紫)      铁港→血誓 系列（新手第一把重锻武器）
- 血誓战剑(Lv36 紫) → 余烬军团战剑(Lv55 紫)  血誓→余烬军团 系列
- 日冕权杖(Lv56 紫) → 夜祷权杖(Lv66 紫)  圣典·日冕→暗夜圣典 系列（牧师武器重锻）

inherit: "full"=完整继承强化/升级等级；"half"=折半向下取整（v136 定稿）
mats: 稀有素材（重锻消耗，额外加 Boss 怨念物/稀有矿）
"""
REFINE_RECIPES = {
    # 旧装备(装备名) → 新装备(配方 key) + 消耗 + 继承
    "弯刀": {
        "target": "rec_xue_shi_zhan_jian",
        "mats": {
            "mat_tie_kuang_shi": 4,   # 铁矿石
            "mat_xue_shi_zhi_yuan": 1,  # 血誓之源（Boss 稀有素材，v136 新增）
        },
        "gold": 800,
        "inherit": "half",   # 新手重锻折半继承，避免白嫖高强化
        "desc": "铁港弯刀淬入血誓之源，剑脊烙上团徽——血誓战剑（继承一半强化/升级）",
    },
    "血誓战剑": {
        "target": "rec_yu_jin_jun_tuan_jian",
        "mats": {
            "mat_sheng_dian_tie_kuai": 3,  # 圣殿铁块
            "mat_yu_jin_he_xin": 1,        # 余烬核心（Boss 稀有素材，v136 新增）
        },
        "gold": 1500,
        "inherit": "half",
        "desc": "血誓战剑熔入余烬核心，剑锋燃起烽火——余烬军团战剑（继承一半强化/升级）",
    },
    "日冕权杖": {
        "target": "rec_ye_dao_quan_zhang",
        "mats": {
            "mat_sheng_guang_jie_jing": 3,  # 圣光结晶
            "mat_ye_dao_zhi_xin": 1,        # 夜祷之心（Boss 稀有素材，v136 新增）
        },
        "gold": 1800,
        "inherit": "half",
        "desc": "日冕权杖浸入夜色，杖首光芒转为幽蓝——夜祷权杖（继承一半强化/升级）",
    },
}
