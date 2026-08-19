# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - wild_npcs.py（18 章野外NPC与时间季节系统，2026-08-06）

- WILD_NPCS：32 个野外 NPC（满足出现条件 → 偶遇；随机性 chance/roam/cycle/unlock 可选）
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
        "duration": 60,  # v127.5 限时NPC：在场分钟数（缺省 60）
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
        # v105 M21 P2：teach 空转修复——有对话树但树内无教学选项（world.py 对带树
        # 的 teach NPC 只提示"或许能指点你一二"），删死 func 与树内纯指点台词一致
        "funcs": ["info"],
        "dialogue": "(头也不抬)……这里不是观光的林子。你是迷路了，还是专程来找我的？",
    },
    "w_lost_knight": {
        "name": "迷路的骑士", "icon": "🛡️", "map": "emerald_forest",
        "condition": {"weather": "rain"},
        "desc": "北方来的骑士，迷路了",
        # v105 M21 P1-5：无任务 giver → 删 quest 死 func（台词为问路，非任务承诺）
        "funcs": [],
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
        # v124.3（审计）：解锁链数据化——交谈授予隐藏 NPC 解锁 flag
        # （world.py _grant_wild_unlock_flags 读此字段；新增解锁型 NPC 无需改代码）
        "unlock_flags": {"flag": "heard_owl_song",
                         "notice": "🦉 巴尔的故事里传来一声夜枭的长啼——那声音，仿佛来自白鹿林的深处……"},
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
        # v105 M21 P1-5：无任务 giver → 删 quest 死 func（保留 lore）
        "funcs": ["lore"],
        "dialogue": "……生者？多少年了，终于又有人踏进这片焦土。",
        # v124.3（审计）：解锁链数据化（见 w_lore_master 注释）
        "unlock_flags": {"flag": "soothed_five_ghosts",
                         "notice": "👻 老兵之魂的执念渐渐平息——古战场深处，仿佛传来一声悠长的叹息……"},
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
        # v124.3（审计）：解锁链数据化（见 w_lore_master 注释）
        "unlock_flags": {"flag": "heard_timeless_tale",
                         "notice": "⏳ 弦歌拨动琴弦，唱起一位不属于任何时代的旅人——『时光旅人』的传说……"},
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
        # v105 M21 P1-5：无任务 giver → 删 quest 死 func
        "funcs": [],
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
        # v105 M21 P1-5：无任务 giver → 删 quest 死 func，台词同步（删任务承诺）
        "funcs": [],
        "dialogue": "你见过腐牙兽人吗？它们……它们把我弟弟抓走了。这些年来，我一直在北境找它们的踪迹。",
    },
    "w_pilgrim": {
        "name": "老朝圣者·灰袍", "icon": "🧎", "map": "cinder_mountain",
        "condition": {"time": ["day"]},
        "desc": "替爷爷来看英雄王的世界",
        # v105 M21 P1-5：无任务 giver → 删 quest 死 func，台词同步（删任务承诺）
        "funcs": [],
        "dialogue": "爷爷说，烬山上有英雄王留下的光……我老了，走不动了，只能望着那座山叹气。",
    },
    # ---- 2.5 东境·龙脊（Lv.80-100）----
    "w_dragon_whisper": {
        "name": "龙语者·古尔", "icon": "🐉", "map": "dragon_ridge",
        "condition": {"time": ["evening"]},
        "desc": "能与龙对话的人",
        "funcs": ["info", "teach", "quest"],
        "dialogue": "龙说，黄昏是它们最清醒的时候。你想听龙在说什么吗？",
        # v112 D6：教习技能表下沉数据（原 world.py _TEACH_SKILL_MAP，职业 → 传授技能）
        "teach_hint": "龙语者·古尔侧耳倾听片刻，缓缓开口：",
        "teach_skills": {
            "cls_zhan_shi": "战争践踏", "cls_fa_shi": "元素爆发", "cls_you_xia": "林语印记",
            "cls_mu_shi": "圣光惩击", "cls_ci_ke": "淬毒", "cls_wu_seng": "破晓之拳",
            "cls_dragon_oath": "龙息", "cls_chronomancer": "时滞术", "cls_wild_hunter": "星陨",
            "cls_hymn": "战歌", "cls_shadow_blade": "幽影袭", "cls_wu_sheng": "裂岩冲",
        },
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
        # v105 M21 P1-5：无任务 giver → 删 quest 死 func（保留 lore），台词同步（删任务承诺）
        "funcs": ["lore"],
        "dialogue": "亡魂们还在重演那场战争……我日复一日地记录他们的故事，可永远记不完。",
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
        "teach_hint": "上古守卫者的石瞳亮起微光，低沉的声音在你心中响起：",
        "teach_skills": {
            "cls_zhan_shi": "铁壁之心", "cls_fa_shi": "元素护盾", "cls_you_xia": "风行步",
            "cls_mu_shi": "神圣坚韧", "cls_ci_ke": "影袭", "cls_wu_seng": "磐石体",
            "cls_dragon_oath": "龙鳞", "cls_chronomancer": "时间裂隙", "cls_wild_hunter": "占卜",
            "cls_hymn": "英雄叙事诗", "cls_shadow_blade": "暗影步", "cls_wu_sheng": "势蓄连打",
        },
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
    # ---- v118 支线设计稿新增野外 NPC（01-21 稿，2026-08-16 落地）----
    "npc_dock_coroner": {
        "name": "验尸人·艾德娜", "icon": "🕯️", "map": "harbor_docks",
        "condition": {"time": ["day", "evening"]},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "铁港码头验尸人，前圣女庭杂役修女",
        "funcs": ["quest", "lore"],
        "dialogue": "尸体不说话，但尸体不撒谎——这是我在圣女庭扫地八年，学到的唯一一件事。说吧，你捞上来什么了？",
    },
    "npc_seal_jonah": {
        "name": "守印修士·约拿", "icon": "📿", "map": "white_abbey",
        "condition": {},
        "desc": "白石修道院地下封印室看守，能听见封印状态的人",
        "funcs": ["quest", "lore"],
        "dialogue": "潮声会认路……哦，是布鲁姆的拓片。坐吧，孩子。你看，这扇门闩，三百年前插得好好的。可有人把它往回抽。",
    },
    "npc_abyss_witness": {
        # 设计稿 03 名「暗语者·默」与既有 npc_abyssaltar_whisperer（深渊祭坛守坛修士）重名，
        # 按 NPC 命名铁律改用设计稿头衔「深渊见证者」规避（同 09 稿 老橡→老栎 先例）
        "name": "深渊见证者·默", "icon": "✒️", "map": "abyss_altar",
        "condition": {},
        "desc": "深渊裂隙的记忆具象，只记录不插手",
        "funcs": ["lore", "quest"],
        "dialogue": "（在地上写字）别说话。这里的声音够多了。",
    },
    "npc_captain_ghost_edmund": {
        "name": "船长亡灵·埃德蒙", "icon": "⚓", "map": "shipwreck_graveyard",
        "condition": {"time": ["night"]},
        "desc": "十二年前沉没的归帆号船长之魂",
        "funcs": ["quest", "lore"],
        "dialogue": "这封信……帮我送到珍珠城，交给我女儿伊莲。她认得我的字。",
    },
    "npc_retired_collector_heron": {
        "name": "隐退收藏家·苍鹭", "icon": "🦢", "map": "starlake",
        "condition": {"time": ["day", "evening"]},
        "desc": "星语湖畔的隐退收藏家，黎明王冠的守冠人",
        "funcs": ["quest", "lore"],
        "dialogue": "收藏的最高境界，不是把东西留在手里，而是知道它该去哪里。",
    },
    "npc_elven_ranger_yuelu": {
        "name": "巡林者·月露", "icon": "🏹", "map": "silverwood",
        "condition": {"time": ["day", "evening"]},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "银月王庭外巡林者，长老银歌的关门弟子",
        "funcs": ["quest", "lore"],
        "dialogue": "……银尾？是银尾吗？银歌长老等了三百年的银尾。",
    },
    "npc_dusk_shadow": {
        "name": "赤鳞龙王·暮影", "icon": "🐉", "map": "dragonsfall_valley",
        "condition": {},
        "desc": "千年前陨落的赤鳞龙王之魂，龙陨谷守望者",
        "funcs": ["quest", "lore"],
        "dialogue": "谷里的龙骨，是我的责任，也是我的牢笼。",
    },
    "npc_scalenote": {
        "name": "龙裔先祖·瓦罗·鳞歌", "icon": "⚔️", "map": "ancient_battlefield",
        "condition": {"time": ["night"]}, "unlock": "quest:s22",
        "desc": "百族战争时期战死的龙裔战将英魂",
        "funcs": ["lore"],
        "dialogue": "三百年了……终于有人用我们的语言，叫我们回家。",
    },
    "npc_hunter_birch": {
        "name": "猎手·白桦", "icon": "🏹", "map": "black_forest",
        "condition": {"time": ["day", "evening"]}, "unlock": "quest:s18",
        "desc": "被腐牙兽人掳走的年轻猎户，铁弓的弟弟",
        "funcs": ["quest"],
        "dialogue": "恩人！我左手使不上弓了，但我哥教我用右手——冬天结束前，我再猎一头雪狼，给你做双新靴子！",
    },
    "npc_fang_shaman": {
        "name": "腐牙萨满·嚎骨", "icon": "🦴", "map": "black_forest",
        "condition": {"time": ["night"]}, "unlock": "quest:s18",
        "desc": "腐牙部落的转化萨满，以腐牙之血制造\"兄弟\"",
        "funcs": [],
        "dialogue": "北境的肉，最香了——尤其是猎户的肉，筋骨硬，养得出好'兄弟'！",
    },
    "npc_forest_keeper_moss": {
        "name": "守林人·苔衣", "icon": "🪵", "map": "black_forest",
        "condition": {"time": ["day"]},
        "desc": "黑森林林缘守林人小屋的独居老人",
        "funcs": ["quest", "lore"],
        "dialogue": "腐牙兽人总来扒我的柴垛、偷我的存粮。老头子打不动了，替我把它们赶远些，柴垛保住了，我分你一半过冬的柴火。",
    },
    "npc_leafwhisper": {
        "name": "巡林人·叶语", "icon": "🍃", "map": "white_deer_forest",
        "condition": {"time": ["night"]}, "unlock": "quest_done:s104",
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "银月精灵巡林人·树语者，永恒花的寻访者",
        "funcs": ["quest", "lore"],
        "dialogue": "花比人长情，也比人守诺。",
    },
    "npc_starlake_elder": {
        "name": "老人·罗根", "icon": "🧓", "map": "starlake",
        "condition": {"time": ["day", "evening"]},
        "desc": "每年月圆之夜来星语湖守约的退休马帮老人",
        "funcs": ["quest", "lore"],
        "dialogue": "五十七年前，我和一个精灵姑娘约好，月亮最圆的时候，在这湖边见。我迟到了——马队在山里误了半个月。",
    },
    "npc_brook_whisper": {
        "name": "守湖人·溪语", "icon": "💧", "map": "silverwood",
        "roam": ["silverwood", "starlake"],
        "condition": {"time": ["day", "evening"]},
        "gender": "女",  # v95 #141：代词跟随 NPC 性别
        "desc": "星语湖守湖人·水之祭司，月之母的信徒",
        "funcs": ["quest", "lore"],
        "dialogue": "三百年了，还有人带着它回来。……灯还亮着，说明它还没熄。可它在哪里，被什么绊住了——我不知道。",
    },
    "npc_fisher_buoy": {
        "name": "老渔翁·浮标", "icon": "🎣", "map": "silver_river",
        "condition": {"time": ["day", "evening"]},
        "desc": "银铃河渡口的老渔翁，一辈子等银铃鲤的人",
        "funcs": ["quest", "lore"],
        "dialogue": "鱼不信谎话，河不骗老实人。老头子钓了五十年，河说什么，我就信什么。",
    },
}

# 隐藏 NPC（18 章 5.5.1：解锁条件 + 高随机性；隐藏任务链 H3-H12 数据落地后续阶段）
HIDDEN_NPCS = {
    "h_owl": {
        "name": "夜枭·啼月", "icon": "🦉", "map": "white_deer_forest",
        "condition": {"time": ["night"]}, "chance": 0.15,
        # v104 P1（M21）：设置点=与 说书人·巴尔(w_lore_master, 银月河畔) 交谈（world.py find_npc 授予）
        "unlock": "flag:heard_owl_song",
        "desc": "月下的影子，唱着无人听过的歌",
        "funcs": ["lore"],
        "dialogue": "……人类，你为何在夜里游荡？",
    },
    "h_mystery_merchant": {
        "name": "神秘商人·无面", "icon": "🎭", "map": None,
        # v104 M20 P1：day_of_week 必须放 condition 内——引擎只读 condition.day_of_week
        # （wild.py base_conditions_met），顶层字段不生效导致「每周六出现」约束失效
        "condition": {"day_of_week": [5]}, "chance": None,
        "roam": ["oak_town", "white_deer", "harbor_docks", "pearl_city", "dawn_city"],
        "unlock": None,
        "desc": "不露脸的商人，拿秘密换货物",
        "funcs": ["trade"],
        "dialogue": "想要好东西？拿秘密来换。",
    },
    "h_grave_king": {
        "name": "墓王·静语", "icon": "💀", "map": "old_battlefield",
        "condition": {"time": ["night"], "weather": "fog"}, "cycle": 3,
        # v104 P1（M21）：设置点=与 老兵之魂(w_war_ghost, 旧战场夜雾) 交谈安抚亡魂（world.py find_npc 授予）
        "unlock": "flag:soothed_five_ghosts",
        "desc": "亡者之王，静默如坟",
        "funcs": ["lore", "teach"],
        "dialogue": "……你安抚了我的子民。为此，本王许你一个愿望。",
        "teach_hint": "墓王·静语睁开灰白的眼眸，亡者的低语在你耳畔回响：",
        "teach_skills": {
            "cls_zhan_shi": "无畏冲击", "cls_fa_shi": "冰霜新星", "cls_you_xia": "狩猎终章",
            "cls_mu_shi": "圣光驱散", "cls_ci_ke": "暗影处刑", "cls_wu_seng": "连招三连",
            "cls_dragon_oath": "龙威", "cls_chronomancer": "凝时锁", "cls_wild_hunter": "命运之轮",
            "cls_hymn": "哀歌", "cls_shadow_blade": "幽影连刺", "cls_wu_sheng": "蓄劲连打",
        },
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
        # v104 M20 P2/P3：设计条件「主线第 10 章后 + flag:saw_the_rift」（03 章 5.5.1）。
        # 原 unlock=flag:saw_the_rift 仅来自全图探索彩蛋 night_visitor（权重 10/249 ×
        # EXPLORE_EGG_CHANCE 0.005 ≈ 0.02%/次，近乎锁死）；unlock 引擎仅支持单条件，
        # 取主线门槛为准：第 10 章最终章 q10_6 完成后解锁（night_visitor 彩蛋 flag 保留，
        # 作为叙事伏笔不再阻塞解锁）
        "unlock": "quest_done:q10_6",
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
        # v104 P1（M21）：原 unlock=item:time_shard 物品不存在→永久锁死；改 flag，
        # 设置点=与 流浪诗人·弦歌(w_bard_roaming, 月之门) 交谈（world.py find_npc 授予）
        "unlock": "flag:heard_timeless_tale",
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
        "unlock": "quest_done:q11_3",  # v104 P1（M21）：主线第11章『奥古斯都的真面目』通关后出现
        # （原 quest_done:inst_secret_crypt 是副本 id 非任务 id，quests 完成记录从不写入→永久锁死；
        #   副本通关的 battle_state 临时标记已被 core/wild.py unlock_met 兼容）
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
    # ---- v118 18 稿隐藏任务链 H5-H8 新增隐藏 NPC（2026-08-16 落地）----
    # 注：设计稿 condition 为 weather rain/storm 双值，引擎 weather 仅支持单值字符串（wild.py
    # base_conditions_met 直接比较），取 rain 为准（雨 15% 概率最高）；storm 由实现端 H5 任务触发兜底。
    "w_night_merchant": {
        "name": "神秘商人·鸦羽", "icon": "🌂", "map": "harbor_docks",
        "condition": {"time": ["night"], "weather": "rain", "min_level": 20}, "chance": 1.0,
        "unlock": None,
        "desc": "雨夜码头灯塔残基下的撑伞商人",
        "funcs": ["shop", "lore", "trade"],  # v124 P1：补 trade——_wild_trader_here 只认 trade 行商（鸦羽货摊分支）
        "dialogue": "雨夜的路，从来不是给人走的。可你来了第二次——看来你也是走夜路的人。",
        "quest": "h5",  # 隐藏任务 H5·雨夜的来客
    },
    "npc_gravedigger": {
        "name": "守墓人·灰杖", "icon": "🪦", "map": "white_abbey",
        "condition": {"time": ["day", "evening"]}, "chance": 0.30,
        "unlock": None,
        "desc": "白石修道院墓园的独眼守墓人",
        "funcs": ["quest", "lore"],
        "dialogue": "墓园里的花，我只种白的。白花在夜里看得见——亡魂认得回家的路。",
        "quest": "h6",  # 隐藏任务 H6·墓园的低语
    },
    "npc_letter_bird": {
        "name": "候鸟·翎信", "icon": "🐦", "map": "starlake",
        "condition": {"time": ["day", "evening"]}, "chance": 0.30,
        "unlock": "quest:h7",
        "desc": "星语湖畔颈挂旧铜管的灰羽候鸟，传了三百年信的邮差",
        "funcs": ["quest", "lore"],
        "dialogue": "（它落在你竿边，歪着头看你，铜管里露出一角油纸——那眼神不像鸟，倒像一位等了三百年的邮差。）",
        "unlock": "stats:fish_count:10",  # H7 触发：星语湖垂钓 10 次后出现（wild.py unlock_met 支持 stats:key:min）
        "quest": "hq7_1",  # 隐藏任务 H7·候鸟的信
    },
}
