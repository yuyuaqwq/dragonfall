# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - weekly_quests.py（v169.2 周常悬赏 Lv50+）

成长模型（v169.1）经验需求放大 10-25 倍后，S4(51-70)/S5(71-100) 需要新的高频经验源。
周常悬赏 = 每周刷新一次的击杀型悬赏，Lv50+ 解锁，自动结算（击杀达标即发奖），
无接取/交付环节——比每日任务更高的单笔奖励 + 一周时间窗，作为中后期主线外的经验主轴。

表结构（与 quests.py DAILY_QUESTS 同构，额外带 band / min_lv）：
    name       任务名（西幻悬赏命名）
    desc       描述（击杀目标）
    objective  目标（单键：kill_any / kill_elite / kill_boss，值 = 达标数）
    reward_exp 经验奖励（新成长曲线：Lv55 单条 ≈ 150-250k / Lv80+ 单条 ≈ 400-700k，
                = exp_to_next 的 50-80%；exp_to_next: Lv55≈309k / Lv80≈902k）
    reward_gold 金币奖励（经验 1/4 ~ 1/5 量级）
    min_lv     最低可抽等级（等级带下限：50 / 70）
    band       等级带标识（仅策划/调试用，不做逻辑判定）
    flavor     悬赏委托文案（西幻风委托板口吻，供面板润色）
"""
# v169.2：两档等级带（Lv50-69 中坚进阶 / Lv70-100 终局），各 6 条，共 12 条。
#   每条按该带代表等级核对 exp_to_next 占比：band1 Lv55≈309k、band2 Lv80≈902k。
#   数值按"每周做满 3 条 ≈ 单级需求 70-100%"校准（每天 1-2 条击杀向，7 天时间窗很宽裕）。
WEEKLY_QUESTS = [
    # ============================================================
    # 一、进阶悬赏池 Lv.50-69（占 Lv55 需求 309k 的 ~50-80%：150-250k）
    # ============================================================
    {
        "name": "边境肃清令",
        "desc": "击败 30 只任意怪物",
        "objective": {"kill_any": 30},
        "reward_exp": 155000,
        "reward_gold": 38000,
        "min_lv": 50,
        "band": "Lv50-69",
        "flavor": "边境哨站的狼烟已起，兽群在防线外越聚越多。斩断它们，让长夜重新安静下来。",
    },
    {
        "name": "深林猎手悬赏",
        "desc": "击败 40 只任意怪物",
        "objective": {"kill_any": 40},
        "reward_exp": 175000,
        "reward_gold": 44000,
        "min_lv": 50,
        "band": "Lv50-69",
        "flavor": "古树隘口的护林人说，月下的猎手从未失手。你愿意接过这张悬赏吗？",
    },
    {
        "name": "剿灭魔裔",
        "desc": "击败 5 只精英怪物",
        "objective": {"kill_elite": 5},
        "reward_exp": 190000,
        "reward_gold": 48000,
        "min_lv": 50,
        "band": "Lv50-69",
        "flavor": "魔裔的血脉在幽暗处悄然滋长，行会开出了高价——为每一只倒下的精英魔物。",
    },
    {
        "name": "破阵斩将",
        "desc": "击败 6 只精英怪物",
        "objective": {"kill_elite": 6},
        "reward_exp": 210000,
        "reward_gold": 53000,
        "min_lv": 50,
        "band": "Lv50-69",
        "flavor": "敌阵的将旗立在风中，六面战旗，六颗头颅。行会的委托从不仁慈。",
    },
    {
        "name": "讨伐区域首领",
        "desc": "击败 2 个区域 Boss",
        "objective": {"kill_boss": 2},
        "reward_exp": 230000,
        "reward_gold": 58000,
        "min_lv": 50,
        "band": "Lv50-69",
        "flavor": "领主盘踞一方，令四方商旅绕道。王庭悬赏其首级，赏金已封存于冒险者行会。",
    },
    {
        "name": "诛灭祸乱之源",
        "desc": "击败 3 个区域 Boss",
        "objective": {"kill_boss": 3},
        "reward_exp": 250000,
        "reward_gold": 64000,
        "min_lv": 50,
        "band": "Lv50-69",
        "flavor": "三处祸乱的源头在同一周被点燃——预言说，斩断它们的人将名扬奥兰迪亚。",
    },
    # ============================================================
    # 二、终局悬赏池 Lv.70-100（占 Lv80 需求 902k 的 ~45-75%：400-700k）
    # ============================================================
    {
        "name": "龙脊清扫令",
        "desc": "击败 35 只任意怪物",
        "objective": {"kill_any": 35},
        "reward_exp": 400000,
        "reward_gold": 100000,
        "min_lv": 70,
        "band": "Lv70-100",
        "flavor": "龙脊山脉的裂隙里涌出源源不断的野兽，清扫它们，为屠龙者开路。",
    },
    {
        "name": "深渊行者试炼",
        "desc": "击败 45 只任意怪物",
        "objective": {"kill_any": 45},
        "reward_exp": 450000,
        "reward_gold": 115000,
        "min_lv": 70,
        "band": "Lv70-100",
        "flavor": "深渊行者从不回头。行会要的只是数字——四十五次挥剑，或四十五次奇迹。",
    },
    {
        "name": "精英猎杀令",
        "desc": "击败 6 只精英怪物",
        "objective": {"kill_elite": 6},
        "reward_exp": 520000,
        "reward_gold": 130000,
        "min_lv": 70,
        "band": "Lv70-100",
        "flavor": "精英魔物的爪牙已撕裂三道防线。行会重金悬赏它们的头颅，每一颗都作数。",
    },
    {
        "name": "霜烬双境镇魔",
        "desc": "击败 8 只精英怪物",
        "objective": {"kill_elite": 8},
        "reward_exp": 580000,
        "reward_gold": 145000,
        "min_lv": 70,
        "band": "Lv70-100",
        "flavor": "霜原与烬山，一冷一热两条战线同时告急。镇魔者需要在两境之间奔走。",
    },
    {
        "name": "古龙讨伐状",
        "desc": "击败 2 个区域 Boss",
        "objective": {"kill_boss": 2},
        "reward_exp": 630000,
        "reward_gold": 160000,
        "min_lv": 70,
        "band": "Lv70-100",
        "flavor": "古龙的鳞片在龙陨谷堆积成山。讨伐状上只有一句话：带回它们的咆哮。",
    },
    {
        "name": "终焉王座攻略",
        "desc": "击败 3 个区域 Boss",
        "objective": {"kill_boss": 3},
        "reward_exp": 700000,
        "reward_gold": 180000,
        "min_lv": 70,
        "band": "Lv70-100",
        "flavor": "三座王座悬于虚空之上。攻略它们的人，将触碰到这片大陆真正的顶点。",
    },
]

# 每周抽取条数（参考每日 2 条 → 周常给 3 条，7 天时间窗内每天清一清即可做满）
WEEKLY_PICK = 3

# 周常悬赏可接最低等级（Lv50+ 解锁；与 quests.py 高阶池 min_lv=50 对齐）
WEEKLY_MIN_LV = 50
