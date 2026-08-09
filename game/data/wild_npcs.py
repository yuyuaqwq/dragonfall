# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - wild_npcs.py（18 章野外NPC与时间季节系统，2026-08-06）

- WILD_NPCS：28 个野外 NPC（满足出现条件 → 偶遇；随机性 chance/roam/cycle/unlock 可选）
- HIDDEN_NPCS：10 个隐藏 NPC（解锁条件 + 高随机性，隐藏任务链 H3-H12 后续落地）

条件字段（AND）：
  time: ["morning","day","evening","night"]  时间段（清晨05-08/白天08-18/黄昏18-20/夜晚20-05）
  season: ["spring","summer","autumn","winter"]  季节（春3-5/夏6-8/秋9-11/冬12-2）
  weather: "rain"/"storm"/"snow"/"fog"  天气（None=不限；晴/多云不写）
  min_level / max_level  玩家等级区间（防错过）
  quest_done: [qid]  完成过任务
  quest_active: [qid]  任务进行中
  flag: "xxx"  玩家对话 flag
  item: "mat_xxx"  持有道具
  day_of_week: [0..6]  星期（周一=0）
随机性字段：
  chance: 0.0-1.0  满足基础条件后概率出现（每 30 分钟独立判定）
  roam: [map_id,...]  每天随机出现在其中一个地图（日期哈希，全服一致）
  cycle: N  每 N 天出现一次（date.toordinal() % N == 0）
  unlock: "flag:xxx"/"item:xxx"/"quest:qid"  解锁后才可能遇到
"""
WILD_NPCS = {
    # ---- 2.1 南境·绿野（Lv.1-30）----
    "w_old_trader": {
        "name": "游商·老马", "icon": "🧭", "map": "oak_plain",
        "condition": {"time": ["day"]},
        "desc": "走南闯北的行商，消息灵通",
        "funcs": ["trade", "info"],
        "dialogue": "赶路呢？要不要看看货？都是走南闯北淘来的好东西。",
    },
    "w_forest_girl": {
        "name": "采药女·小荨", "icon": "🌿", "map": "white_deer_forest",
        "condition": {"time": ["morning", "day"]},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "采药为生，知道草药的秘密",
        "funcs": ["trade", "quest"],
        "dialogue": "这片林子的草药我闭着眼都能找到……你也要采药？",
    },
    "w_sage_ryder": {
        "name": "隐士·莱德", "icon": "🗡️", "map": "white_deer_forest",
        "condition": {"time": ["evening", "night"], "season": ["summer", "autumn"]},
        "desc": "退役剑客，隐居避世",
        "funcs": ["teach", "info"],
        "dialogue": "(头也不抬)……这里不是观光的林子。你是迷路了，还是专程来找我的？",
    },
    "w_lost_knight": {
        "name": "迷路的骑士", "icon": "🛡️", "map": "emerald_forest",
        "condition": {"weather": "rain"},
        "desc": "北方来的骑士，迷路了",
        "funcs": ["quest"],
        "dialogue": "这位旅人！请问白鹿城往哪个方向走？这该死的雨把路标都冲没了。",
    },
    "w_gravekeeper": {
        "name": "守墓老人", "icon": "🕯️", "map": "misty_swamp",
        "condition": {"time": ["night"]},
        "desc": "守着沼泽深处的无名墓",
        "funcs": ["lore", "info"],
        "dialogue": "深更半夜来沼泽……胆子不小。坐下吧，听老头子讲讲这墓里埋的是谁。",
    },
    "w_fisherman": {
        "name": "夜钓翁·老竿", "icon": "🎣", "map": "harbor_docks",
        "condition": {"time": ["night"]},
        "desc": "只在夜里钓鱼，知道深海秘密",
        "funcs": ["info", "trade"],
        "dialogue": "夜里的鱼才会上钩。小子，看你像个会钓鱼的，来陪老头子坐会儿？",
    },
    # ---- 2.2 中域·圣光之心（Lv.25-55）----
    "w_paladin_exile": {
        "name": "流浪圣骑士·奥利", "icon": "⚔️", "map": "gold_plain",
        "condition": {"time": ["evening"]},
        "desc": "被教会除名的圣骑士",
        "funcs": ["quest", "info"],
        "dialogue": "……圣光抛弃了我，但我没有抛弃圣光。年轻人，你相信誓言吗？",
    },
    "w_lore_master": {
        "name": "说书人·巴尔", "icon": "📜", "map": "silver_river",
        "condition": {"time": ["night"]},
        "desc": "知道所有民间传说",
        "funcs": ["lore", "info"],
        "dialogue": "夜里的河最会讲故事。来，给你说一段连国王都不知道的往事……",
    },
    "w_grave_digger": {
        "name": "盗墓贼·鼠仔", "icon": "🪦", "map": "old_battlefield",
        "condition": {"time": ["night"]},
        "desc": "偷挖古墓，胆子小",
        "funcs": ["trade", "quest"],
        "dialogue": "嘘！小声点！……你、你也是来捞外快的？",
    },
    "w_temple_hermit": {
        "name": "圣堂隐修者", "icon": "📖", "map": "white_abbey",
        "condition": {"season": ["winter"]},
        "desc": "苦修者，见过圣女",
        "funcs": ["lore"],
        "dialogue": "冬日的风最清醒。年轻人，你想听一个关于圣女的故事吗？",
    },
    "w_war_ghost": {
        "name": "老兵之魂", "icon": "👻", "map": "old_battlefield",
        "condition": {"time": ["night"], "weather": "fog"},
        "desc": "百族战争的老兵亡灵",
        "funcs": ["lore", "quest"],
        "dialogue": "……生者？多少年了，终于又有人踏进这片焦土。",
    },
    # ---- 2.3 西境·银月林海（Lv.45-75）----
    "w_elf_wanderer": {
        "name": "流浪精灵·薇拉", "icon": "🏹", "map": "silverwood",
        "condition": {"time": ["night"], "weather": "sunny"},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "被逐出王庭的精灵",
        "funcs": ["quest", "info"],
        "dialogue": "月亮的眼睛看着我，你也看见了吗？王庭不承认我，但月亮认得我。",
    },
    "w_druid_old": {
        "name": "老德鲁伊·橡心", "icon": "🌳", "map": "ancient_tree",
        "condition": {"season": ["spring"]},
        "desc": "与古树对话的人",
        "funcs": ["info", "trade"],
        "dialogue": "春天来了，树在说话。你听——它们说：又一个旅人路过，带着迷茫。",
    },
    "w_bard_roaming": {
        "name": "流浪诗人·弦歌", "icon": "🎵", "map": "moon_gate",
        "condition": {"time": ["day", "evening"]}, "cycle": 3,
        "desc": "收集歌谣的吟游诗人",
        "funcs": ["lore"],
        "dialogue": "我把路上听来的歌都收在琴里……你想听哪一段？",
    },
    "w_silent_hunter": {
        "name": "沉默猎人", "icon": "🐺", "map": "windvale",
        "condition": {"time": ["evening", "night"]},
        "desc": "猎影豹的老猎人",
        "funcs": ["trade", "info"],
        "dialogue": "……(沉默地整理箭袋，半天才开口)影豹的皮，要趁热剥。",
    },
    "w_elf_poet": {
        "name": "精灵诗人·夜歌", "icon": "🌙", "map": "starlake",
        "condition": {"time": ["night"], "weather": "sunny"},
        "desc": "为湖心亭写诗的精灵诗人",
        "funcs": ["quest"],
        "dialogue": "湖心亭的月色是最好的墨。可惜……我一个人写不出两行诗。",
    },
    # ---- 2.4 北境·霜原（Lv.60-95）----
    "w_frost_shaman": {
        "name": "霜语萨满·冰牙", "icon": "❄️", "map": "permafrost_field",
        "condition": {"time": ["night"], "season": ["winter"]},
        "desc": "与冰灵沟通的萨满",
        "funcs": ["trade", "info"],
        "dialogue": "冰灵在风里低语……你听懂了，就留下来；听不懂，就快走吧。",
    },
    "w_trapper": {
        "name": "老猎人·灰狼", "icon": "🪓", "map": "black_forest",
        "condition": {"time": ["day"]},
        "desc": "猎腐牙兽人的独行猎人",
        "funcs": ["quest", "trade"],
        "dialogue": "腐牙兽人又在林子里转悠了……小子，帮我个忙，我请你喝最烈的酒。",
    },
    "w_abyss_watcher": {
        "name": "深渊守望者", "icon": "🔮", "map": "cinder_mountain",
        "condition": {"time": ["night"]},
        "desc": "守着封印裂缝的老修士",
        "funcs": ["lore"],
        "dialogue": "裂缝在低语……它说封印要松了。你……你是来帮忙的，还是来围观的？",
    },
    "w_snow_traveler": {
        "name": "雪夜旅人", "icon": "🧣", "map": "frost_field",
        "condition": {"weather": "snow"},
        "desc": "在暴雪中赶路的旅人",
        "funcs": ["info", "trade"],
        "dialogue": "这么大的雪还能遇上人，缘分。来，分你一杯热酒——顺便，我告诉你一个秘密。",
    },
    "w_volcano_hermit": {
        "name": "火山隐者", "icon": "🌋", "map": "forge_valley",
        "condition": {"season": ["summer"]},
        "desc": "研究熔岩的学者",
        "funcs": ["trade", "info"],
        "dialogue": "熔岩的脉搏比任何钟表都准……夏天它跳得最快，就像现在。",
    },
    "w_north_hunter": {
        "name": "北境猎手·铁弓", "icon": "🏹", "map": "black_forest",
        "condition": {"time": ["day"]},
        "desc": "弟弟被腐牙兽人掳走的猎人",
        "funcs": ["quest"],
        "dialogue": "你见过腐牙兽人吗？它们……它们把我弟弟抓走了。帮帮我，求你。",
    },
    "w_pilgrim": {
        "name": "老朝圣者·灰袍", "icon": "🧎", "map": "cinder_mountain",
        "condition": {"time": ["day"]},
        "desc": "替爷爷来看英雄王的世界",
        "funcs": ["quest"],
        "dialogue": "爷爷说，烬山上有英雄王留下的光……我老了，走不动了，你替我去看看好吗？",
    },
    # ---- 2.5 东境·龙脊（Lv.80-100）----
    "w_dragon_whisper": {
        "name": "龙语者·古尔", "icon": "🐉", "map": "dragon_ridge",
        "condition": {"time": ["evening"]},
        "desc": "能与龙对话的人",
        "funcs": ["info", "teach", "quest"],
        "dialogue": "龙说，黄昏是它们最清醒的时候。你想听龙在说什么吗？",
    },
    "w_bone_collector": {
        "name": "拾骨人·白骸", "icon": "🦴", "map": "bone_wild",
        "condition": {"time": ["night"]},
        "desc": "收集龙骨的研究者",
        "funcs": ["trade", "info"],
        "dialogue": "每根龙骨都是一段史诗……这块，是八百年前那场战争的遗物。",
    },
    "w_war_scholar": {
        "name": "亡灵学者·骨语", "icon": "📚", "map": "ancient_battlefield",
        "condition": {"time": ["night"]},
        "desc": "研究百族战争亡魂的学者",
        "funcs": ["quest", "lore"],
        "dialogue": "亡魂们还在重演那场战争……你愿意帮我记录他们的故事吗？",
    },
    "w_storm_chaser": {
        "name": "追风者·岚", "icon": "🌪️", "map": "storm_cliff",
        "condition": {"weather": "storm"},
        "desc": "追逐风暴的疯子",
        "funcs": ["info", "quest"],
        "dialogue": "风暴就是最壮丽的诗！别躲，站上来，感受它！",
    },
    "w_ancient_guardian": {
        "name": "上古守卫者", "icon": "🗿", "map": "dragonsfall_valley",
        "condition": {"time": ["day", "evening"]}, "cycle": 7,
        "desc": "守护龙冢的神秘存在",
        "funcs": ["lore", "teach"],
        "dialogue": "……(石像般的守卫者缓缓开口)第七日，又一位旅人踏足龙冢。",
    },
    # ---- 2.6 外域·无尽海（Lv.55-78）----
    "w_lighthouse_old": {
        "name": "灯塔老人·光柄", "icon": "🗼", "map": "nameless_harbor",
        "condition": {"weather": "storm"},
        "desc": "守灯塔的老人",
        "funcs": ["quest", "info"],
        "dialogue": "暴风雨来了……灯不能灭。年轻人，帮我守住这盏灯，就是守住整片海。",
    },
    "w_pearl_diver": {
        "name": "采珠女·明珠", "icon": "🫧", "map": "pearl_city",
        "condition": {"time": ["morning"]},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "潜海采珠的姑娘",
        "funcs": ["trade", "info"],
        "dialogue": "清晨的海最平静，珍珠也最亮。要不要看看今天的收成？",
    },
    "w_shipwreck_ghost": {
        "name": "沉船幽灵·船长", "icon": "⚓", "map": "shipwreck_graveyard",
        "condition": {"time": ["night"]},
        "desc": "沉船船长的亡灵",
        "funcs": ["quest", "lore"],
        "dialogue": "……我还能听到海浪拍打船板的声音。这封信，你能帮我送回家乡吗？",
    },
    "w_whale_whisper": {
        "name": "鲸语者·潮", "icon": "🐳", "map": "whale_domain",
        "condition": {"season": ["summer"]},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "能与龙鲸沟通的少女",
        "funcs": ["info", "trade"],
        "dialogue": "龙鲸说，夏天它们会游到最温暖的海域……你想听听它们的歌吗？",
    },
}

# 隐藏 NPC（18 章 5.5.1：解锁条件 + 高随机性；隐藏任务链 H3-H12 数据落地后续阶段）
HIDDEN_NPCS = {
    "h_owl": {
        "name": "夜枭·啼月", "icon": "🦉", "map": "white_deer_forest",
        "condition": {"time": ["night"]}, "chance": 0.15,
        "unlock": "flag:heard_owl_song",
        "desc": "月下的影子，唱着无人听过的歌",
        "funcs": ["lore"],
        "dialogue": "……人类，你为何在夜里游荡？",
    },
    "h_mystery_merchant": {
        "name": "神秘商人·无面", "icon": "🎭", "map": None,
        "condition": {}, "chance": None,
        "roam": ["oak_town", "white_deer", "harbor_docks", "pearl_city", "dawn_city"],
        "day_of_week": [5],
        "unlock": None,
        "desc": "不露脸的商人，拿秘密换货物",
        "funcs": ["trade"],
        "dialogue": "想要好东西？拿秘密来换。",
    },
    "h_grave_king": {
        "name": "墓王·静语", "icon": "💀", "map": "old_battlefield",
        "condition": {"time": ["night"], "weather": "fog"}, "cycle": 3,
        "unlock": "flag:soothed_five_ghosts",
        "desc": "亡者之王，静默如坟",
        "funcs": ["lore", "teach"],
        "dialogue": "……你安抚了我的子民。为此，本王许你一个愿望。",
    },
    "h_moon_wolf_king": {
        "name": "月狼王·白夜", "icon": "🐺", "map": "silverwood",
        "condition": {"time": ["night"], "weather": "sunny"}, "chance": 0.10,
        "unlock": "quest:s12",
        "desc": "月夜之王，白如初雪",
        "funcs": ["lore", "teach"],
        "dialogue": "月亮的子民，为何闯入我的领地？",
    },
    "h_ancient_druid": {
        "name": "远古德鲁伊·橡语", "icon": "🌲", "map": "ancient_tree",
        "condition": {"season": ["spring"]}, "cycle": 7,
        "unlock": "quest:s15",
        "desc": "与千年古树同寿的存在",
        "funcs": ["info", "teach"],
        "dialogue": "树记得千年的事……你要听哪一段？",
    },
    "h_ice_spirit": {
        "name": "冰灵·霜歌", "icon": "🧊", "map": "permafrost_field",
        "condition": {"time": ["night"], "season": ["winter"]}, "chance": 0.12,
        "unlock": "quest:s34",
        "desc": "冰封之心的歌唱者",
        "funcs": ["lore", "trade"],
        "dialogue": "……你的心跳声，比冰原的风还吵。",
    },
    "h_sea_dragon_king": {
        "name": "海龙·潮汐", "icon": "🌊", "map": "whale_domain",
        "condition": {"season": ["summer"]}, "cycle": 5,
        "unlock": "quest:s28",
        "desc": "掌管潮汐的海之君王",
        "funcs": ["lore", "teach"],
        "dialogue": "潮汐由我而起……人类，你为何而来？",
    },
    "h_abyss_whisper": {
        "name": "深渊低语者", "icon": "🌑", "map": "abyss_altar",
        "condition": {"time": ["night"]}, "chance": 0.08,
        "unlock": "flag:saw_the_rift",
        "desc": "裂缝中的声音，不是人也不是魔",
        "funcs": ["lore"],
        "dialogue": "……你看见了裂缝。现在，你还能假装什么都没发生吗？",
    },
    "h_storm_herald": {
        "name": "风暴先知·雷音", "icon": "⚡", "map": "storm_plateau",
        "condition": {"weather": "storm"}, "chance": 0.10,
        "unlock": "quest:q12_6",
        "desc": "在雷暴中聆听神谕的先知",
        "funcs": ["info", "teach"],
        "dialogue": "雷霆是神的语言……你听懂了，就留下；听不懂，就逃。",
    },
    "h_timeless": {
        "name": "时光旅人·刹那", "icon": "⏳", "map": None,
        "condition": {}, "cycle": 1,
        "roam": ["starlight_terrace", "silverwood", "permafrost_field", "dragon_ridge", "pearl_city"],
        "unlock": "item:time_shard",
        "desc": "不属于任何时代的人",
        "funcs": ["lore", "teach"],
        "dialogue": "……你来早了，也来晚了。时间对我而言，只是另一条路。",
    },
    # ---- v87 03 章附章：隐藏线专属 NPC +3 ----
    "h_gravekeeper": {
        "name": "老守墓人·灰须", "icon": "🪦", "map": "cinder_mountain",
        "condition": {"time": ["night"]}, "chance": 0.20,
        "unlock": None,
        "desc": "守着烬山墓园的独臂老人",
        "funcs": ["quest", "lore"],
        "dialogue": "圣战结束那天，活下来的只有我爷爷和一把烧红的剑。那剑……还在烬山深处等着它的主人。",
        "quest": "s_hidden_ember",  # 隐藏任务 H3·烬火的余温
    },
    "h_librarian": {
        "name": "图书管理员·贝拉", "icon": "📖", "map": "dawn_cathedral",
        "condition": {}, "chance": 0.25,
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "unlock": "quest_done:inst_secret_crypt",  # 击败圣堂地窖 Boss 后出现（主线副本通关标记）
        "desc": "教会图书馆幸存的书记官",
        "funcs": ["quest", "trade"],
        "dialogue": "他们把真相锁进了地窖最深处。三百年了……我守着这些书，就是在等一个能读完它们的人。",
        "quest": "s_hidden_library",  # 隐藏任务 H4·失落的图书馆
    },
    "h_night_trader": {
        "name": "夜行者商人", "icon": "🌙", "map": None,
        "condition": {"time": ["night"]}, "chance": 0.05,
        "roam": ["oak_town", "white_deer", "ironharbor", "dawn_city", "moon_court", "frost_horn"],
        "unlock": None,
        "desc": "只在夜里出没的神秘商人",
        "funcs": ["trade"],
        "dialogue": "识货人？夜晚的货物，只卖给识货人。",
    },
}
