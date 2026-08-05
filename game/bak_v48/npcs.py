# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - npcs.py"""
NPCS = {
    # ---- 远境城（圣光王国）----
    'npc_holy_king': {'name': '远境国王·罗兰', 'title': '远境王国国王', 'map': 'holy_city_square', 'icon': '👑', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's14', 'dialogue': '远境城的大门永远为勇士敞开。城外的光耀狼最近格外凶悍，替王国清除它们，圣光会铭记你的功绩。'},
    'npc_holy_innkeeper': {'name': '圣辉旅店·晨曦', 'title': '旅店老板', 'map': 'holy_city_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '远道而来的冒险者，晨曦旅店为你备好了最柔软的床铺与圣光祝福。'},
    # ---- 银月城（精灵王国）----
    'npc_elf_royal': {'name': '精灵王·艾瑞斯', 'title': '精灵王', 'map': 'elf_city_square', 'icon': '👑', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's15', 'dialogue': '银月城的月光见证过精灵千年的荣光。月影豹在城门徘徊，威胁着精灵子民的安全。'},
    'npc_elf_innkeeper': {'name': '银月旅店·月光', 'title': '旅店老板', 'map': 'elf_city_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '在月光旅店小憩吧，生命之树的祝福会抚平你的伤口。'},
    # ---- 龙喉堡（龙裔王国）----
    'npc_dragon_king': {'name': '古龙·奥瑞斯', 'title': '古龙之王', 'map': 'dragon_city_square', 'icon': '👑', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's16', 'dialogue': '龙喉堡的火焰为真正的勇士燃烧。最近有龙裔战士被深渊蛊惑，替龙族清除叛徒！'},
    'npc_dragon_innkeeper': {'name': '龙喉旅店·熔炉', 'title': '旅店老板', 'map': 'dragon_city_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '喝一杯熔炉烈酒，在龙鳞暖床上歇息。明天的战斗还长着呢。'},
    # ---- 虚空前哨 ----
    'npc_void_general': {'name': '远征军团长·艾德里克', 'title': '人类联军团长', 'map': 'void_city_square', 'icon': '⚔️', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's17', 'dialogue': '前哨的每一寸土地都是用战士的血换来的。废墟爪牙在大门外集结，替我挡下这波攻势！'},
    'npc_void_innkeeper': {'name': '前哨军需官·凯特', 'title': '军需官', 'map': 'void_city_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '物资紧缺，但勇士的补给绝不能断。好好休息，前线的炮火不等人。'},
    # ---- 悲怆营地 ----
    'npc_exile_leader': {'name': '流亡者首领·玛尔', 'title': '流亡者首领', 'map': 'exile_camp_square', 'icon': '🔥', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's18', 'dialogue': '我们失去了家园，但没失去希望。黑袍修士在营地外游荡，替我们守住这最后的火光。'},
    'npc_exile_innkeeper': {'name': '营火医者·洛琳', 'title': '随军牧师', 'map': 'exile_camp_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '营火旁没有陌生人。来，让我为你包扎伤口，愿圣光庇护你。'},
    # ---- 铁壁城 ----
    'npc_iron_marshal': {'name': '铁壁元帅·钢盾', 'title': '联军元帅', 'map': 'iron_city_square', 'icon': '🛡️', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's19', 'dialogue': '铁壁城是人类最后的壁垒。枯骨魔兵正在城下集结，去挫一挫他们的锐气！'},
    'npc_iron_innkeeper': {'name': '铁壁旅店·钢炉', 'title': '旅店老板', 'map': 'iron_city_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '城里的铁匠铺炉火不熄，旅店的汤锅也永远滚烫。吃饱喝足，明天还要守城。'},
    # ---- 旧王城 ----
    'npc_divine_archon': {'name': '旧王城执政官·塞拉芬', 'title': '失落王城执政官', 'map': 'divine_city_square', 'icon': '👁️', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 's20', 'dialogue': '旧王城见证了众神的黄昏。古王战灵被暗影侵蚀，正在袭击朝圣者——净化它们。'},
    'npc_divine_innkeeper': {'name': '天穹旅店·星辉', 'title': '旅店老板', 'map': 'divine_city_square', 'icon': '🏨', 'funcs': ['heal'], 'dialogue': '星辉旅店在云端营业了千年，你是第一位凡间客人。请随意歇息。'},
    # ---- 维拉镇 ----
    "npc_mayor": {
        "name": "镇长·阿尔文", "title": "维拉镇镇长", "map": "vila_square",
        "icon": "🧔", "funcs": ["quest", "ency"], "quest_id": "q1",
        "dialogue": "年轻人，你来得正是时候。最近镇子外围的野狗越来越猖狂，商队都不敢进城了。帮我解决这个麻烦，镇子不会亏待你的。",
        "dialogue_done": "是你啊，维斯特兰的传说！如今商队络绎不绝，镇子夜不闭户，全靠你当初的恩情。镇上的孩子们都在传唱你的故事呢。",
    },
    "npc_blacksmith": {
        "name": "铁匠·托尔", "title": "铁匠铺老板", "map": "vila_street",
        "icon": "🔨", "funcs": ["shop"],
        "dialogue": "嘿，冒险者！我这儿的家伙什都是上好的货。买把趁手的武器再上路吧！",
    },
    "npc_bartender": {
        "name": "老板·老杰克", "title": "酒馆老板", "map": "vila_tavern",
        "icon": "🍺", "funcs": ["lore"],
        "dialogue": "欢迎光临醉熊酒馆！要听故事还是喝一杯？听说翡翠森林最近来了头远古圣鹿，不少人盯着呢。",
    },
    "npc_bounty": {
        "name": "赏金猎人·卡珊德拉", "title": "赏金猎人", "map": "vila_tavern",
        "icon": "🗡️", "funcs": ["daily"],
        "dialogue": "小子，想赚点外快？每天都有悬赏任务，干完来我这儿领赏金。",
    },
    "npc_innkeeper": {
        "name": "老板娘·玛丽", "title": "旅店老板娘", "map": "vila_inn",
        "icon": "🏨", "funcs": ["heal"],
        "dialogue": "累了吧？在星夜旅店歇一晚，保你明天生龙活虎！",
    },
    "npc_bard": {
        "name": "吟游诗人·莉莉", "title": "吟游诗人", "map": "vila_square",
        "icon": "🎻", "funcs": ["lore"],
        "dialogue": "你听说了吗？矮人那边石拳丘陵的矿洞被地精占了，听说深处出了个‘隧洞之王’……",
    },
    # ---- 翡翠森林 ----
    "npc_druid": {
        "name": "德鲁伊·艾露", "title": "翡翠森林守护者", "map": "emerald_heart",
        "icon": "🌿", "funcs": ["quest"], "quest_id": "q2",
        "dialogue": "外来者，森林在哭泣。远古圣鹿被黑暗侵蚀了心智，只有击败它才能让森林重归平静。",
    },
    # ---- 石拳丘陵 ----
    "npc_dwarf_elder": {
        "name": "长老·铁砧", "title": "矮人长老", "map": "stonefist_camp",
        "icon": "⛏️", "funcs": ["quest", "shop"], "quest_id": "q3",
        "dialogue": "地精那群小崽子霸占了我们的矿洞！勇士，帮我们把矿洞夺回来，矮人的友谊和商店都给你！",
    },
    # ---- 赤脊荒原 ----
    "npc_orc_prisoner": {
        "name": "俘虏·血牙", "title": "被俘的兽人", "map": "redridge_camp",
        "icon": "⛓️", "funcs": ["quest"], "quest_id": "q5",
        "dialogue": "勇士……帮我逃出酋长的营地，兽人欠你一个人情。酋长太残暴了，部落需要新的首领……",
    },
    # ---- 黑石城废墟 ----
    "npc_ghost_knight": {
        "name": "亡魂·赛德里克", "title": "旧王国骑士", "map": "blackrock_keep",
        "icon": "👻", "funcs": ["quest", "heal"], "quest_id": "q6",
        "dialogue": "吾乃旧王国骑士赛德里克……巫妖宰相篡夺了王座。勇士，替我复仇，吾将指引你圣光之路……",
    },
    # ---- 风暴之巅 ----
    "npc_sky_hermit": {
        "name": "隐士·云渡", "title": "风暴之巅的隐士", "map": "stormpeak_peak",
        "icon": "🧙", "funcs": ["quest", "lore"], "quest_id": "q9",
        "dialogue": "哦？居然有人能走到这里。你可知秘银遗迹的传说？那才是强者真正的试炼……",
    },
    'npc_holy_cardinal': {'name': '远境大主教·菲奥娜', 'title': '远境大教堂大主教', 'map': 'holy_altar', 'icon': '🕊️', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 'q11', 'dialogue': '圣光在上……天使长竟然堕落了。年轻人，祭坛的光芒正在熄灭，只有你能阻止这场浩劫。'},
    'npc_elf_sage': {'name': '精灵贤者·塞琳', 'title': '精灵王庭贤者', 'map': 'elf_courtyard', 'icon': '🧝', 'funcs': ['quest', 'shop', 'lore'], 'quest_id': 'q13', 'dialogue': '月之泉水已经浑浊……女王被暗影蒙蔽了双眼。请救救精灵王庭，救救我们的女王。'},
    'npc_dragon_elder': {'name': '龙裔贤者·岩语', 'title': '龙族贤者', 'map': 'dragon_nest', 'icon': '🐉', 'funcs': ['quest', 'shop', 'lore'], 'quest_id': 'q15', 'dialogue': '龙血在沸腾，古老的意志正在苏醒。龙王知道些什么——他眼中的混沌之火，不属于任何龙族。'},
    'npc_void_prophet': {'name': '裂隙先知·弥撒', 'title': '裂隙谷地的先知', 'map': 'void_corridor', 'icon': '🔮', 'funcs': ['quest', 'shop', 'lore'], 'quest_id': 'q17', 'dialogue': '你击败的魔王，不过是深渊的先锋。裂隙的心脏还在跳动——真正的敌人，就在裂隙的最深处。'},
    'npc_fallen_priest': {'name': '堕落祭司·格雷', 'title': '教团叛逃者', 'map': 'temple_aisle', 'icon': '🕯️', 'funcs': ['quest', 'heal'], 'quest_id': 'q19', 'dialogue': '我曾是教团的祭司……直到我看见他们在祭坛上召唤的东西。那不是神，那是深渊本身。'},
    'npc_annih_spy': {'name': '前线斥候·铁牙', 'title': '联军前线斥候', 'map': 'annih_field', 'icon': '🐺', 'funcs': ['quest', 'shop'], 'quest_id': 'q21', 'dialogue': '亡灵大军马上就要总攻了！我们的人正在集结，但你得先挫一挫他们的锐气！'},
    'npc_star_warden': {'name': '古国守望者·阿尔法', 'title': '失落王城守望者', 'map': 'divine_hall', 'icon': '⭐', 'funcs': ['quest', 'shop', 'heal'], 'quest_id': 'q23', 'dialogue': '古老的预言已经应验：王国倾覆之前，将最后的希望托付给远道而来的冒险者。去吧，推开那扇门。'},
    'npc_last_god': {'name': '古国贤者·艾瑟', 'title': '最后的王家学者', 'map': 'panth_court', 'icon': '👁️', 'funcs': ['quest', 'lore'], 'quest_id': 'q27', 'dialogue': '我是旧王朝最后幸存的一位学者。巫王……不，他是第一次战争之前的古老意志。凡人，终结这一切吧。'},
}

