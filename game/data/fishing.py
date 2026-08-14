# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - fishing.py（16 章品质垂钓体系 v2.0，2026-08-06 重写）

品质五档统一枚举（与装备品质一致）：white 普通 / green 优良 / blue 稀有 / purple 史诗 / orange 传说。
- 稀有度由垂钓等级查 FISH_QUALITY_WEIGHTS 表（Lv.1→Lv.9，中间等级线性插值，见 core/fishing.py）
- 渔获品种 key 一律 mat_ ID（v48 ID 规范），禁止动态中文 key
- 钓点差异化：FISHING_SPOTS 的 ban_quality 禁出档位 + 品种 spots 限定水域
"""
FISHING_SPOTS = {
    # v104 M15 修复：补 subarea 字段（v87.17 子区域绑定原为死代码——11 钓点全无绑定，任意子区域可钓）。
    # 子区域 id 均取自 data/subareas.py 实际定义（测试 test_commands_fishing 已按同款落点设置）。
    "oak_plain": {
        "name": "橡木溪流", "min_lv": 1, "ban_quality": ["purple", "orange"],
        "subarea": "oak_plain_3",  # 溪边草地（浅溪从草地间流过）
        "desc": "新手区，白绿为主",
    },
    "starlake": {
        "name": "星语湖", "min_lv": 1, "ban_quality": ["purple", "orange"],
        "subarea": "starlake_1",  # 湖畔
        "desc": "湖珍珠(附魔)/鲛人泪的传说水域",
    },
    "harbor_docks": {
        "name": "铁港码头", "min_lv": 3, "ban_quality": [],
        "subarea": "harbor_docks_1",  # 码头栈桥
        "desc": "深水鱼王栖息地，全档位",
    },
    "gold_plain": {
        "name": "银铃河", "min_lv": 5, "ban_quality": ["orange"],
        "subarea": "gold_plain_1",  # 平原边缘（河流沿岸）
        "desc": "银鳞鱼群聚，稀有+",
    },
    "misty_swamp": {
        "name": "迷雾沼泽", "min_lv": 4, "ban_quality": ["orange"],
        "subarea": "misty_swamp_1",  # 沼泽边缘（渔人蹲守的岸边）
        "desc": "神秘鳞片/鲛人泪，紫·宝箱",
    },
    "frost_horn": {
        "name": "霜原冰湖", "min_lv": 6, "ban_quality": ["orange"],
        "subarea": "frost_horn_gate",  # 霜角堡城门（冰湖在堡外霜原一侧）
        "desc": "深海水晶/龙涎香",
    },
    "mist_trench": {
        "name": "迷雾海沟", "min_lv": 6, "ban_quality": ["orange"],
        "subarea": "mist_trench_1",  # 海沟口
        "desc": "海藻/珍珠贝，蓝·稀有为主",
    },
    "whale_domain": {
        "name": "龙鲸海域", "min_lv": 7, "ban_quality": ["purple", "orange"],
        "subarea": "whale_domain_1",  # 海域边缘（幼年龙鲸出没处）
        "desc": "鲸须草摇曳的外海，绿蓝为主",
    },
    "storm_sea": {
        "name": "风暴之海", "min_lv": 8, "ban_quality": ["orange"],
        "subarea": "storm_sea_1",  # 海缘
        "desc": "雷晶砂/风暴贝",
    },
    "deep_lake": {
        "name": "深渊湖", "min_lv": 7, "ban_quality": ["orange"],
        "subarea": "deep_lake_1",  # 湖岸（渔人点灯垂钓处）
        "desc": "盲鱼/深渊珍珠，地底特色",
    },
    "rainbow_cloud": {
        "name": "彩虹云谷", "min_lv": 9, "ban_quality": ["orange"],
        "subarea": "rainbow_cloud_1",  # 云谷口（彩虹桥横亘入口）
        "desc": "云棉/彩虹露珠，天空特色",
    },
}

# 品质档位顺序：v101.25i6 统一引用 QUALITY_ORDER（见 data/__init__.py 别名）
# 品质五档权重表：垂钓等级 Lv.1/3/5/7/9 查表（16 章 2.2，总和=100）
# 中间等级（2/4/6/8）由 core/fishing.py 线性插值。
# 单调性：白递减、绿/蓝/紫/橙递增（等级越高成长越高）。
FISH_QUALITY_WEIGHTS = {
    1: [84.25, 13, 2.5, 0.2, 0.05],
    3: [76.3, 18, 5, 0.6, 0.1],
    5: [65, 23, 10, 1.8, 0.2],
    7: [52.05, 26, 17, 4.5, 0.45],
    9: [41, 29, 20, 9, 1.0],
}

# 品质中文名：v101.25i6 统一走 QUALITY[q]["name"]（白档不显示 ✦ 标记）
# 垂钓经验：白 1 / 绿 1 / 蓝 2 / 紫 3 / 橙 5（16 章 2.6）
FISH_EXP = {"white": 1, "green": 1, "blue": 2, "purple": 3, "orange": 5}

# 渔获品种池（16 章 2.3 + 2.4 特色列，按品质档位组织）
# spots: None = 全部水域；列表 = 仅限这些钓点产出（FISHING_SPOTS 的 map_id）
FISH_POOL = [
    # ---- 白·普通 ----
    {"name": "银鳞鱼", "quality": "white", "type": "鱼", "price": 6, "spots": None,
     "weight": 55, "desc": "常见的淡水鱼，肉质鲜美"},
    {"name": "水草", "quality": "white", "type": "垃圾", "price": 1, "spots": None,
     "weight": 25, "desc": "缠成一团的水草，什么也没有"},
    {"name": "破旧的靴子", "quality": "white", "type": "垃圾", "price": 1, "spots": None,
     "weight": 20, "desc": "不知道谁扔进水里的，毫无用处"},
    # ---- 绿·优良 ----
    {"name": "金鲤", "quality": "green", "type": "鱼", "price": 12, "spots": None,
     "weight": 40, "desc": "鳞片泛着金光的鲤鱼，酒楼抢着收"},
    {"name": "帝王鲑", "quality": "green", "type": "鱼", "price": 22, "spots": None,
     "weight": 25, "desc": "罕见的大鱼，据说吃了能增强体质"},
    {"name": "海藻", "quality": "green", "type": "材料", "price": 15,
     "spots": ["mist_trench", "whale_domain", "storm_sea"],
     "weight": 20, "desc": "墨绿色的海藻，炼金师会感兴趣"},
    {"name": "鲸须草", "quality": "green", "type": "材料", "price": 20,
     "spots": ["whale_domain", "storm_sea"],
     "weight": 15, "desc": "龙鲸身上落下的须草，柔韧异常"},
    {"name": "云棉", "quality": "green", "type": "材料", "price": 22,
     "spots": ["rainbow_cloud"],
     "weight": 10, "desc": "云朵凝成的棉絮，轻盈温暖"},
    {"name": "盲鱼", "quality": "green", "type": "鱼", "price": 9,
     "spots": ["deep_lake"],
     "weight": 10, "desc": "地下湖的盲眼鱼，肉质细腻"},
    # ---- 蓝·稀有 ----
    {"name": "月光鱼", "quality": "blue", "type": "鱼", "price": 27, "spots": None,
     "weight": 20, "desc": "月光下泛着银蓝光泽的鱼，稀有"},
    {"name": "湖珍珠", "quality": "blue", "type": "材料", "price": 40,
     "spots": ["starlake", "harbor_docks", "gold_plain", "misty_swamp"],
     "weight": 35, "desc": "贝中孕育的珍宝，附魔师抢着收"},
    {"name": "鲛人泪", "quality": "blue", "type": "材料", "price": 120,
     "spots": ["starlake", "misty_swamp"],
     "weight": 25, "desc": "鲛人落下的泪珠，炼金术的珍品"},
    {"name": "神秘鳞片", "quality": "blue", "type": "材料", "price": 30,
     "spots": ["misty_swamp", "harbor_docks", "frost_horn"],
     "weight": 25, "desc": "不知名生物留下的鳞片，铁匠会感兴趣"},
    # v104 M15 修复：夜光鲛无产出源（设计 13 章 line 134「垂钓(深夜/沼泽钓点)」）
    {"name": "夜光鲛", "quality": "blue", "type": "材料", "price": 35,
     "spots": ["misty_swamp"],
     "weight": 15, "desc": "深夜出没于沼泽的鲛鱼，鳞片泛着幽幽荧光，炼金师视若珍宝"},
    {"name": "珍珠贝", "quality": "blue", "type": "材料", "price": 35,
     "spots": ["mist_trench", "whale_domain"],
     "weight": 20, "desc": "海沟里的珍珠贝，偶尔藏着珍宝"},
    {"name": "深渊珍珠", "quality": "blue", "type": "材料", "price": 45,
     "spots": ["deep_lake"],
     "weight": 15, "desc": "地底深处孕育的暗色珍珠"},
    {"name": "彩虹露珠", "quality": "blue", "type": "材料", "price": 50,
     "spots": ["rainbow_cloud"],
     "weight": 15, "desc": "凝结在云端的露珠，映着七色光"},
    {"name": "风暴贝", "quality": "blue", "type": "材料", "price": 40,
     "spots": ["storm_sea"],
     "weight": 15, "desc": "风暴中生长的贝类，壳上有雷纹"},
    # ---- 紫·史诗 ----
    {"name": "陈旧的宝箱", "quality": "purple", "type": "宝物", "price": 0, "spots": None,
     "weight": 30, "desc": "水底的宝箱！打开看看有什么好东西"},
    {"name": "深海水晶", "quality": "purple", "type": "材料", "price": 250,
     "spots": ["harbor_docks", "frost_horn"],
     "weight": 35, "desc": "深海凝结的水晶，锻造珍品"},
    {"name": "龙涎香", "quality": "purple", "type": "材料", "price": 180,
     "spots": ["harbor_docks", "frost_horn"],
     "weight": 25, "desc": "龙涎凝成的香料，炼金珍品"},
    {"name": "雷晶砂", "quality": "purple", "type": "材料", "price": 80,
     "spots": ["storm_sea"],
     "weight": 20, "desc": "雷暴淬炼过的晶砂，滋滋作响"},
    # ---- 橙·传说 ----
    {"name": "鱼王·翡翠巨龙", "quality": "orange", "type": "鱼王", "price": 245,
     "spots": ["harbor_docks"],
     "weight": 60, "desc": "传说沉眠在深水中的鱼王！全服为之震动"},
    {"name": "古代鱼骨", "quality": "orange", "type": "材料", "price": 200,
     "spots": ["harbor_docks"],
     "weight": 40, "desc": "上古巨兽的遗骨，蕴含神秘力量"},
]

# v83 16 章 4.x：超稀有收藏鱼（彩蛋，独立于五档权重，纯收藏）
# chance 固定不随垂钓等级提升；spots=None 任意钓点；time="night" 仅夜晚
# 判定：core/fishing.py roll_collect_fish（概率升序，高稀有优先，最多 1 条）
FISH_COLLECT = [
    {"id": "mat_rainbow_kite", "name": "虹彩龙鲤", "chance": 0.0005, "spots": None,
     "desc": "传说中只在彩虹映照深潭时现身的龙鲤，鳞片流光溢彩。"},
    {"id": "mat_moon_jelly", "name": "月华水母", "chance": 0.0003, "spots": None,
     "time": "night",
     "desc": "月光下才会浮起的透明水母，触须如月华般柔软。"},
    {"id": "mat_star_remnant", "name": "星骸遗鳞", "chance": 0.0002,
     "spots": ["mist_trench", "whale_domain", "storm_sea"],
     "desc": "据说来自坠入海底的星辰，鳞片还带着星空的微光。"},
]
