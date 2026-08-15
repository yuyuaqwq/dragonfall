# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - factions.py（阶段四重写，2026-08-06）

07 章三·声望系统：7 势力（冒险者行会/圣光王国/圣光教会/银月精灵/矮人铁砧/北境诸部/龙裔）
AREA_FACTION：新世界 area → 势力（击杀/找NPC 加声望）
CHRONICLES：01 章世界观传说（核心反转：蚀夜是守护者，教会篡改历史）
"""
FACTIONS = {
    "guild":   {"name": "冒险者行会",   "icon": "⚔️", "desc": "铁牌到传奇，冒险者的家。完成任务/委托提升，解锁高级委托与隐藏任务。"},
    "kingdom": {"name": "圣光王国",     "icon": "🏰", "desc": "晨曦城的王权，人类王国的秩序。主线/支线提升，声望商店解锁王都军需。"},
    "church":  {"name": "圣光教会",     "icon": "⛪", "desc": "表面圣光的守望者，暗中维持封印的真相。主线后期解锁教会专属商品。"},
    "elves":   {"name": "银月精灵",     "icon": "🌿", "desc": "银月林海的古老精灵，月神的后裔。西境支线提升，精灵商店与月系图纸。"},
    "dwarves": {"name": "矮人铁砧",     "icon": "⛏️", "desc": "铁砧要塞的锻匠，大地与符文的大师。北境支线提升，声望商店解锁锻造补给。"},
    "north":   {"name": "北境诸部",     "icon": "❄️", "desc": "霜原上的部落联盟，苦寒之地的人类。北境任务提升，北境商店与酒馆情报。"},
    "dragons": {"name": "龙裔",         "icon": "🐉", "desc": "龙脊山脉的半龙之民，守护古龙血脉。东境试炼提升，龙语传承图纸。"},
}

FACTION_ORDER = ["guild", "kingdom", "church", "elves", "dwarves", "north", "dragons"]

REPUTATION_TIERS = [
    (0,    "陌生"),
    (100,  "友好"),
    (300,  "尊敬"),
    (700,  "崇敬"),
    (1500, "崇拜"),
]

# v105 M18 P2-7 声望消费侧：势力声望商店（07 章三·声望系统 desc 承诺的"商店折扣/专属商品"最小落地）
# 按声望等级解锁专属商品（声望只作门槛，金币购买）：声望不足 → 提示所需等级。
#   item  = 物品 ID（C.ITEMS / C.MATERIALS 均有定义）
#   tier  = 解锁所需声望阈值（对照 REPUTATION_TIERS：100 友好 / 300 尊敬 / 700 崇敬 / 1500 崇拜）
#   price = 商店售价（金币；缺省用物品原价）
# 命令入口：『声望商店』（game/commands/world.py rep_shop），高级委托/隐藏任务解锁随 11 章阵营体系后续扩展。
FACTION_SHOP = {
    "guild": [  # 冒险者行会：高级药水 + 行会传送特权
        {"item": "i_treat_l", "tier": 100},
        {"item": "i_mana_l", "tier": 100},
        {"item": "i_scroll_teleport", "tier": 300, "price": 400},
    ],
    "kingdom": [  # 圣光王国：王都军需
        {"item": "i_treat_l", "tier": 100},
        {"item": "i_holy_water", "tier": 300},
        {"item": "i_holy_charm", "tier": 300},
    ],
    "church": [  # 圣光教会：圣堂恩赐
        {"item": "i_holy_water", "tier": 100},
        {"item": "i_holy_potion", "tier": 300},
        {"item": "i_scroll_purify", "tier": 700},
    ],
    "elves": [  # 银月精灵：月系珍品
        {"item": "i_elf_fruit", "tier": 100},
        {"item": "i_mana_l", "tier": 300},
        {"item": "i_moon_dew", "tier": 700},
    ],
    "dwarves": [  # 矮人铁砧：锻造补给
        {"item": "i_dwarf_liquor", "tier": 100},
        {"item": "i_stone_upgrade", "tier": 300},
        {"item": "i_stone_refine", "tier": 700},
    ],
    "north": [  # 北境诸部：霜原补给
        {"item": "i_meat_skewer", "tier": 100},
        {"item": "i_treat_l", "tier": 300},
        {"item": "i_scroll_escape", "tier": 300},
    ],
    "dragons": [  # 龙裔：龙血传承
        {"item": "i_dragon_scale_potion", "tier": 300},
        {"item": "i_life_elixir", "tier": 1500},
    ],
}

# ================= v116：阵营国战最小闭环（11 章策划案二·最小可行版）=================
# 借鉴：11_国战与公会 §二。Lv.20 起可选四大阵营；每日收集型阵营任务 + 贡献；
# 贡献可在阵营商店兑换物资。周结算/据点/Boss 国战线随二期扩展（设计：主agent 报告附图）。
# 四阵营名/图标风格对齐上方七势力中文名。*注意*：四阵营为玩家「可选入籍」阵营，
# 与上方七势力的「声望（唯一且并行）」体系相互独立，互不影响。
FACTION_CAMPS = {
    "holy":   {"name": "圣辉王国",   "icon": "⚜️", "desc": "晨曦余晖下的骑士王国，恪守秩序与圣光的誓言。",
               "buff_text": "特性加成（二期规划）：王国要塞血量上限 +5%"},
    "dragon": {"name": "龙裔部落",   "icon": "🐉", "desc": "龙脊山脉的守序战士，血脉中流淌着古龙之魂。",
               "buff_text": "特性加成（二期规划）：部落战士攻击 +5%"},
    "elf":    {"name": "精灵议会",   "icon": "🌿", "desc": "银月林海的贤者议会，与自然和月辉同呼吸。",
               "buff_text": "特性加成（二期规划）：议会贤者魔力 +5%"},
    "shadow": {"name": "幽影教团",   "icon": "🌙", "desc": "蛰伏于月影之下的隐秘教团，垂涎知识与暗影之力。",
               "buff_text": "特性加成（二期规划）：教团刺客速度 +5%"},
}

# 阵营开放等级门槛（与任务书 §二 一致：Lv.20 开放选阵营）
FACTION_CAMP_OPEN_LV = 20

# 每日阵营任务可在同一天交付/完成的上限（防刷；跨天重置）。
# 例：2 → 玩家每天最多完成 2 个阵营任务并各拿一次贡献。
FACTION_CAMP_DAILY_LIMIT = 2

# 阵营切换冷却（秒）。缺省 7 天 = 604800 秒；设为 0 则允许随时切换。
FACTION_CAMP_SWITCH_COOLDOWN = 7 * 24 * 3600

# 阵营商店：item=物品 ID（C.ITEMS / C.MATERIALS）/ cost=所需阵营贡献 / name=商品名。
# 语义与上方 FACTION_SHOP（声望门槛+金币）区分：阵营商店为「贡献交换」，不花金币。
# 贡献由每日阵营任务积累（FACTION_CAMP_DAILY_TASKS），四阵营共用同一档商品池，
# 二级区分：军需/材料各有代表，前两件低门槛(药水)、后两件高档(强化石/卷轴)。
FACTION_CAMP_SHOP = [
    {"item": "i_treat_l",        "cost": 30,  "name": "治疗药水(大)"},
    {"item": "i_mana_l",         "cost": 30,  "name": "魔法药水(大)"},
    {"item": "i_stone_upgrade",  "cost": 60,  "name": "强化石"},
    {"item": "i_str_potion",     "cost": 80,  "name": "力量药剂"},
    {"item": "i_scroll_teleport","cost": 120, "name": "传送卷轴"},
]

# 每日阵营任务池（收集型·玩家主动『阵营任务 交付』闭环，全部在命令层完成，
# 不依赖 combat.py 击杀挂钩）。每个模板：item=交付材料 ID / count=需交数量 /
# reward=完成一次获得的阵营贡献。击杀型/Boss 讨伐型模板列入注释（标注待 combat 挂钩，不实际发放）。
# item 材料需 Lv.20 及以上玩家可较易获得：兔毛/丘陵狼皮（野外采集）、蜂蜜/风干肉（采集）、
# 萤火虫（采集）、夜枭羽毛（夜间采集）。击杀型/Boss 型（待 combat 挂钩二期）：
#   {"kind":"kill",  "monster":"森林狼", "count":15, "reward":20}
#   {"kind":"boss",  "monster":"野猪王·裂鬃", "count":1, "reward":40}
FACTION_CAMP_DAILY_TASKS = [
    {"kind": "collect", "item": "mat_tu_mao",          "count": 5,  "name": "献上兔毛",     "reward": 20},
    {"kind": "collect", "item": "mat_qiu_ling_lang_pi", "count": 4,  "name": "献上丘陵狼皮", "reward": 25},
    {"kind": "collect", "item": "mat_feng_mi",          "count": 3,  "name": "献上蜂蜜",     "reward": 20},
    {"kind": "collect", "item": "mat_ying_huo_chong",   "count": 5,  "name": "献上萤火虫",   "reward": 20},
]

AREA_FACTION = {
    # 南境（圣光王国腹地）
    "oak": "kingdom", "white_deer": "kingdom", "emerald": "kingdom",
    "misty": "kingdom", "goblin": "kingdom", "hill": "kingdom",
    "ironharbor": "kingdom", "seacave": "kingdom", "silver": "kingdom",
    "windmill": "kingdom", "deerfort": "kingdom", "maple": "kingdom",
    # 中域（圣光王国 + 教会）
    "dawn": "kingdom", "gold": "kingdom", "abbey": "church",
    "oldtomb": "kingdom", "border": "kingdom", "silverriver": "kingdom",
    "crypt": "church", "knight": "kingdom", "kingroad": "kingdom",
    "holytrial": "church", "ironshield": "kingdom", "oldbattle": "kingdom",
    # 西境（银月精灵）
    "moongate": "elves", "silverwood": "elves", "starlake": "elves",
    "mooncourt": "elves", "elvenruins": "elves", "ancienttree": "elves",
    "starsong": "elves", "moonglade": "elves", "emeraldvalley": "elves",
    "moontemple": "elves", "windvale": "elves", "moonshadow": "elves",
    # 北境（北境诸部 + 矮人铁砧）
    "frosthorn": "north", "frostfield": "north", "anvilfort": "dwarves",
    "forgevalley": "dwarves", "blackforest": "north", "cinder": "north",
    "ashtemple": "north", "abyssgate": "north", "frostfang": "north",
    "coldridge": "north", "winterlake": "north", "frostthrone": "north",
    "aurora": "north", "permafrost": "north", "frostwhisper": "north",
    # 东境（龙裔）
    "dragonpass": "dragons", "dragonridge": "dragons", "dragonroost": "dragons",
    "ancientbattle": "dragons", "dragontomb": "dragons", "dragonkin": "dragons",
    "bonewild": "dragons", "stormcliff": "dragons", "stormthrone": "dragons",
    "redridge": "dragons", "dragonsfall": "dragons",
    # 翡翠海群岛（自由商路，王国势力）
    "jade": "kingdom", "shell": "kingdom", "coral": "kingdom",
    "sunset": "kingdom", "stormstrait": "kingdom", "mermaid": "kingdom",
    "sunkenship": "kingdom", "siren": "kingdom",
    # 无尽海（自由海域）
    "nameless": "kingdom", "pearl": "kingdom", "misttrench": "kingdom",
    "whale": "kingdom", "shipwreck": "kingdom", "stormsea": "kingdom",
    "seagod": "kingdom", "deepdragon": "kingdom",
    # 幽暗地域（中立地下世界，不归属七势力）
    # 风翼群岛（龙裔传承地）
    "windcity": "dragons", "cloudsea": "dragons", "stormplateau": "dragons",
    "eyeofstorm": "dragons", "rainbow": "dragons", "starlight": "dragons",
    "cloudsanctum": "dragons",
}

CHRONICLES = [
    {"title": "创世与圣光", "text": "传说父神以圣光划开混沌，群山、森林、大海应声而生。他留下六个孩子看守世界的伤口——蚀夜，便是那个守在深渊裂隙旁的守夜人。"},
    {"title": "三百年前的圣战(教会版本)", "text": "教会记载：魔王蚀夜自北方霜原的裂口而出，率恶魔军团席卷大陆。英雄王艾德里克·晨星集结百族联军，在烬山以圣剑『黎明之光』将其封印。"},
    {"title": "被掩埋的真相", "text": "蚀夜并非恶魔——它是上古守护者，一直在镇压深渊裂隙。三百年前裂隙突然扩大，蚀夜拼尽全力抵抗，却被人类误认作入侵的魔王。英雄王真正做的，是加固了它的封印。"},
    {"title": "圣光容器的代价", "text": "封印每百年需要重新灌注圣光。历代圣女都被『献祭』以维持封印——这就是教会圣女庭的真面目：活祭培养所。现任圣女艾莉丝发现了真相，在冒险者行会帮助下出逃。"},
    {"title": "圣女失踪", "text": "第 37 代圣女艾莉丝不愿再当祭品，留下圣徽悄然离开王都。封印因此加速衰弱，深渊裂隙开始重新扩张——魔物蠢蠢欲动，教会高层却在隐瞒真相。"},
    {"title": "英雄王的遗物", "text": "传说英雄王艾德里克战死在烬山，黎明之光随他一同失落。但老冒险者说：那柄圣剑没有断——它只是被藏进了只有真正的守护者才能找到的地方。"},
    {"title": "铁砧的誓言", "text": "矮人铁砧会议三百年来从不过问王都内政，只守着一条铁律：封印若崩，铁砧必先焚。矮人工匠们至今还在锻造『能终结一切封印』的武器。"},
    {"title": "银月之泪", "text": "银月精灵相信，月神陨落时留下的月之泪拥有净化诅咒的力量。历代精灵女王以生命守护它——三百年前圣战时，它曾让濒死的英雄王多撑了七天。"},
    {"title": "龙裔的守望", "text": "龙裔是古龙与人的混血，世代守护龙脊山脉的古龙血脉。他们记得第一次深渊战争——族中长者说：魔王不过是个传令兵，真正的深渊意志远比远古更古老。"},
    {"title": "北境的歌谣", "text": "霜原的部落民谣唱着：『雪会掩埋尸体，但掩不住真相』。三百年前的圣战，烬山脚下曾有过一支没被记载的军队——他们看到的，和教会写下的，不是同一场战争。"},
    {"title": "铁港城的传闻", "text": "自由城邦铁港城的酒馆里，老水手们流传着一个说法：封印的裂隙不止烬山一处。深渊的触角，早已从海底、地底和云海深处悄悄蔓延。"},
    {"title": "深渊的低语", "text": "靠近深渊裂隙的冒险者都做过同一个梦：黑暗中有声音在问——『守夜人，你还在吗？』那是蚀夜的声音。它被困在封印里，已经三百年了。"},
]
