# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - cooking.py：烹饪副业（13 章 2.3 烹饪表 v2.0，2026-08-06 重写）

副业联动：垂钓（鱼）+ 采集（药材）→ 烹饪 → 战斗外恢复/持续 buff。
- 成本 key 一律 mat_ ID（v48 ID 规范，禁止 fish_ 中文动态 key）
- 持续 buff 型料理（银鳞鱼汤/狼肉煲/龙息炖锅/精灵果酱）随 19 章食物 buff 系统落地，
  本表只收当前可即时生效的配方（战斗外回复）
"""
COOKING_RECIPES = {
    "cook_slime_jelly": {
        "name": "史莱姆果冻",
        "desc": "史莱姆黏液熬成的果冻，滑嫩爽口",
        "min_lv": 1,
        "cost": {"mat_shi_lai_mu_nian_ye": 3},
        "product": {"it_slime_jelly": 1},
    },
    "cook_skewer": {
        "name": "烤肉串(自制)",
        "desc": "新鲜兽肉串烤，滋滋冒油",
        "min_lv": 1,
        "cost": {"mat_shou_rou": 2},
        "product": {"it_cook_skewer": 1},
    },
    "cook_gold_feast": {
        "name": "金鲤盛宴",
        "desc": "金鲤红烧一锅端，富贵人家才吃得起",
        "min_lv": 2,
        "cost": {"mat_jin_li": 2},
        "product": {"it_gold_feast": 1},
    },
    # ---- v101.28i 词条料理接入烹饪（13 件，2026-08-11）：材料成本≈卖价40~90%，
    #      烬火辣椒/蘑菇汤/冰霜浆果/树蜜糖 因材料倒挂保留商店渠道 ----
    "cook_snake_soup": {
        "name": "蛇羹",
        "desc": "蛇皮慢火熬成的鲜羹，沼泽风味",
        "min_lv": 1,
        "cost": {"mat_she_pi": 3},
        "product": {"i_snake_soup": 1},
    },
    "cook_wolf_jerky": {
        "name": "狼肉干",
        "desc": "狼皮风干熏制的野外干粮，耐放顶饿",
        "min_lv": 1,
        "cost": {"mat_lang_pi": 2},
        "product": {"i_wolf_jerky": 1},
    },
    "cook_eagle_egg": {
        "name": "鹰蛋",
        "desc": "悬崖巢穴里捡来的蛋，煎烤皆宜",
        "min_lv": 1,
        "cost": {"mat_hai_ou_yu_mao": 1, "mat_jiang_guo": 1},
        "product": {"i_eagle_egg": 1},
    },
    "cook_ash_pancake": {
        "name": "灰烬烤饼",
        "desc": "炭火烤制的粗粮饼，带着烟火气",
        "min_lv": 1,
        "cost": {"mat_mian_fen": 2, "mat_jiang_guo": 2},
        "product": {"i_ash_pancake": 1},
    },
    "cook_sacred_bread": {
        "name": "圣餐面包",
        "desc": "以圣水揉面烤成的素面包，圣堂赐福",
        "min_lv": 2,
        "cost": {"mat_mian_fen": 2, "mat_sheng_shui": 1},
        "product": {"i_sacred_bread": 1},
    },
    "cook_deer_cheese": {
        "name": "鹿奶干酪",
        "desc": "溪鹿乳发酵压制的干酪，奶香浓郁",
        "min_lv": 2,
        "cost": {"mat_xi_lu_pi": 1, "mat_jiang_guo": 1},
        "product": {"i_deer_cheese": 1},
    },
    "cook_pirate_stew": {
        "name": "海盗炖鱼",
        "desc": "整条银鳞鱼下锅炖煮，无名港私房菜",
        "min_lv": 2,
        "cost": {"mat_yin_lin_yu": 2},
        "product": {"i_pirate_stew": 1},
    },
    "cook_moon_cake": {
        "name": "月光饼",
        "desc": "月鹿角磨粉入馅的甜饼，月色下的点心",
        "min_lv": 3,
        "cost": {"mat_yue_lu_jiao": 1, "mat_jiang_guo": 1},
        "product": {"i_moon_cake": 1},
    },
    "cook_seafood_chowder": {
        "name": "海鲜浓汤",
        "desc": "蟹肉鱼鲜一锅烩，码头工人的最爱",
        "min_lv": 3,
        "cost": {"mat_xie_ke": 1, "mat_yin_lin_yu": 1},
        "product": {"i_seafood_chowder": 1},
    },
    "cook_snowwolf_steak": {
        "name": "雪狼肉排",
        "desc": "雪狼里脊厚切煎排，霜原猎手的骄傲",
        "min_lv": 4,
        "cost": {"mat_xue_lang_pi": 1},
        "product": {"i_snowwolf_steak": 1},
    },
    "cook_royal_roast": {
        "name": "皇家烤肉",
        "desc": "精选兽肉配麦酒腌制，王都御膳风味",
        "min_lv": 4,
        "cost": {"mat_shou_rou": 2, "mat_mai_jiu": 1},
        "product": {"i_royal_roast": 1},
    },
    "cook_royal_soup": {
        "name": "御膳汤",
        "desc": "鹿角兽肉小火慢煨，王都名厨的看家汤",
        "min_lv": 5,
        "cost": {"mat_shou_rou": 1, "mat_yue_lu_jiao": 1, "mat_jiang_guo": 1},
        "product": {"i_royal_soup": 1},
    },
    "cook_dragon_egg_pancake": {
        "name": "龙蛋煎饼",
        "desc": "幼龙鳞入面糊的珍馐，龙脊盛宴压轴",
        "min_lv": 7,
        "cost": {"mat_you_long_lin": 1, "mat_mian_fen": 2, "mat_jiang_guo": 1},
        "product": {"i_dragon_egg_pancake": 1},
    },
    # ---- v102.3 生活技能差异化：稀有食谱（限定材料链：采集→烹饪） ----
    "cook_night_mushroom_soup": {
        "name": "夜雾菇浓汤",
        "desc": "月光下采的夜雾菇慢火煨成，汤面浮着微光",
        "min_lv": 3,
        "cost": {"mat_night_mushroom": 2},
        "product": {"i_night_mushroom_soup": 1},
    },
    "cook_moon_tea": {
        "name": "月光草茶",
        "desc": "月光草焙干冲泡，茶汤清冽回甘，饮后神清气爽",
        "min_lv": 3,
        "cost": {"mat_yue_guang_cao": 2},
        "product": {"i_moon_tea": 1},
    },
    "cook_aurora_honey": {
        "name": "极光花蜜",
        "desc": "极光花浸蜜封存，琥珀色的蜜里流转着极光",
        "min_lv": 5,
        "cost": {"mat_aurora_flower": 1, "mat_mian_fen": 1},
        "product": {"i_aurora_honey": 1},
    },
    "cook_dragon_blood_hotpot": {
        "name": "龙血火锅",
        "desc": "龙血草打底的猛火火锅，辣得人热血沸腾",
        "min_lv": 5,
        "cost": {"mat_long_xue_cao": 1, "mat_shou_rou": 3},
        "product": {"i_dragon_blood_hotpot": 1},
    },
    "cook_thunder_skewer": {
        "name": "雷雨藤烤串",
        "desc": "雷雨藤缠着兽肉烤得滋滋作响，入口有酥麻电光",
        "min_lv": 4,
        "cost": {"mat_thunder_vine": 2},
        "product": {"i_thunder_skewer": 1},
    },
    # ---- v101.30 阶段四：高级钓点材料消费点（垂钓独占 → 烹饪） ----
    "cook_storm_chowder": {
        "name": "风暴贝汤",
        "desc": "风暴贝熬的鲜汤，喝下后每场战斗回复 8% 生命(持续 3 场)",
        "min_lv": 4,
        "cost": {"mat_feng_bao_bei": 2},
        "product": {"i_storm_chowder": 1},
    },
    # ---- v104 R3 M15 P2-2：夜光鲛消费点落地（13 章 line 134「烹饪/炼金」用途；迷雾沼泽钓点独占材料→烹饪）----
    "cook_glow_shark_soup": {
        "name": "夜光鲛汤",
        "desc": "夜光鲛熬成的鲜汤，汤面泛着幽幽荧光，喝下后每场战斗回复 8% 生命(持续 3 场)",
        "min_lv": 4,
        "cost": {"mat_ye_guang_jiao": 2},
        "product": {"i_glow_shark_soup": 1},
    },
    # ---- v104 M15 鱼饵配方落地（v102.3 规划 3 条：烹饪 2 条，炼金 1 条见 alchemy.py）----
    "cook_dough_bait": {
        "name": "面团鱼饵",
        "desc": "揉得松软的麦粉饵团，下次垂钓绿/蓝档品质权重提升(仅 1 次)",
        "min_lv": 1,
        # v104R3 M16 P2-5：成本 6/20=0.30 低于 40% 下限 → 面粉×3+浆果×1=14/20=0.70
        "cost": {"mat_mian_fen": 3, "mat_jiang_guo": 1},
        "product": {"it_dough_bait": 1},
    },
    "cook_blood_bait": {
        "name": "血饵",
        "desc": "浸透兽血的饵团，凶猛的掠食鱼最爱的味道，下次垂钓稀有鱼种概率提升(仅 1 次)",
        "min_lv": 2,
        "cost": {"mat_shou_xue": 2},
        "product": {"it_blood_bait": 1},
    },
    # ================= v117 副本材料联动·方案 C 烹饪部分（6-8 条，2026-08） =================
    # 把 18 种完全闲置的副本掉落材料接进烹饪（本厨娘覆盖其中 8 种：
    #   龙语传承/风暴之核/永冻之核/赫尔加的祭器/幽灵船票/灰矮人徽记/石炉之锤/烬核），
    # 其余（克罗的罗盘/圣光圣徽/地底龙鳞/蓝歌之冠/要塞残片/试炼徽记/马尔库斯的法冠/
    #   黑渊之眼/龙宫珠/云怒之核）留给锻造/附魔/炼金 agent 覆盖，避免重复。
    # 防刷金铁律：产物售价 ≤ 材料成本合计 ×0.9（每条下方列算式）。
    # ---- v117 R1：龙语传承(200,橙)→龙蛋煎饼(90) ----
    #    成本 200×1+3×2=206；90 ≤ 206×0.9=185.4 ✓
    "cook_v117_dragon_relic_pancake": {
        "name": "龙语余温煎饼",
        "desc": "以龙语传承的古老残页点着面糊，烙出的煎饼泛着微黄的暖光，龙脊秘传",
        "min_lv": 7,
        "cost": {"mat_long_yu_chuan_cheng": 1, "mat_mian_fen": 2},
        "product": {"i_dragon_egg_pancake": 1},
    },
    # ---- v117 R2：风暴之核(230,橙)→风暴贝汤(100) ----
    #    成本 230×1+40×1=270；100 ≤ 270×0.9=243 ✓
    "cook_v117_storm_eye_chowder": {
        "name": "风暴之眼贝汤",
        "desc": "风暴之核碾粉入汤，风暴贝在汤中翻滚如惊雷，喝下浑身燥热(雷暴)待发",
        "min_lv": 8,
        "cost": {"mat_feng_bao_zhi_he": 1, "mat_feng_bao_bei": 1},
        "product": {"i_storm_chowder": 1},
    },
    # ---- v117 R3：永冻之核(180,橙)→雪狼肉排(40) ----
    #    成本 180×1=180；40 ≤ 180×0.9=162 ✓（永冻之核为霜原珍材，属价值消耗 sink）
    "cook_v117_permafrost_steak": {
        "name": "永冻冰原肉排",
        "desc": "永冻之核的寒气腌制雪狼里脊，切片沁凉，煎出外焦内冻的霜原奇味",
        "min_lv": 7,
        "cost": {"mat_yong_dong_zhi_he": 1},
        "product": {"i_snowwolf_steak": 1},
    },
    # ---- v117 R4：赫尔加的祭器(60,橙位冰系)→皇家烤肉(55) ----
    #    成本 60×1+15×1=75；55 ≤ 75×0.9=67.5 ✓
    "cook_v117_helga_royal_roast": {
        "name": "祭器御前烤宴",
        "desc": "以赫尔加的祭器剔下的兽肉，佐麦酒腌烤，王都御膳级焦香酥脆",
        "min_lv": 6,
        "cost": {"mat_he_er_jia_de_ji_qi": 1, "mat_mai_jiu": 1},
        "product": {"i_royal_roast": 1},
    },
    # ---- v117 R5：幽灵船票(120,紫)→海盗炖鱼(32) ----
    #    成本 120×1+6×2=132；32 ≤ 132×0.9=118.8 ✓（锈蚀船票指路的无名港鬼船私房）
    "cook_v117_ghost_ship_stew": {
        "name": "幽灵船宴炖鱼",
        "desc": "凭幽灵船票走入雾中，借鬼火煨出的银鳞鱼羹，葬身之台的最后风味",
        "min_lv": 5,
        "cost": {"mat_you_ling_chuan_piao": 1, "mat_yin_lin_yu": 2},
        "product": {"i_pirate_stew": 1},
    },
    # ---- v117 R6：石炉之锤(35)+灰矮人徽记(35)→石酿麦酒(18) ----
    #    成本 35×2=70；18 ≤ 70×0.9=63 ✓（矮人石窖：铁锤敲出佳酿）
    "cook_v117_dwarf_stone_ale": {
        "name": "石炉矮人麦酒",
        "desc": "石炉之锤震碎麦芽，灰矮人徽记为印，窖藏出的麦酒带一丝铁锈石香",
        "min_lv": 4,
        "cost": {"mat_shi_lu_zhi_chui": 1, "mat_hui_ai_ren_hui_ji": 1},
        "product": {"i_stone_ale": 1},
    },
    # ---- v117 R7：烬核(60,橙位火系)→灰烬烤饼(24) ----
    #    成本 60×1+3×1=63；24 ≤ 63×0.9=56.7 ✓（烬核余温烘饼，灰烬城炭火风味）
    "cook_v117_ember_ash_pancake": {
        "name": "烬核熔香烤饼",
        "desc": "烬核捏碎揉进面里，靠余温烘成的粗粮饼，带着熔岩深处的焦香",
        "min_lv": 6,
        "cost": {"mat_jin_he": 1, "mat_mian_fen": 1},
        "product": {"i_ash_pancake": 1},
    },
}

