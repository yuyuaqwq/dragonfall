# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - events.py（v97.3：模板化重写）

探索随机事件（遇怪之前判定）。v97.3 起事件 = 模板 + 参数 + 文案：
- `template`：core/event_templates.py 注册的模板名（loot_gold/loot_materials/...）
- `params`：模板参数（数值/材料池/文案模板）
- 执行统一走 core.event_templates.execute_event_template，combat.py 不再 if-elif

扩展：加新事件 = 复制一条 dict 改 id/weight/template/params/texts，零代码。
"""
EXPLORE_EVENTS = [
    {"id": "treasure", "weight": 18, "name": "闪闪发光的宝箱",
     "desc": "树丛里藏着一个落了灰的宝箱，锁扣上刻着冒险者行会的旧徽记！",
     "template": "loot_gold_mats",
     "params": {"min": 15, "max": 50, "scale_lv": 2,
                "blueprint_chance": 0.7, "explore_item_bonus": True,
                "header": "🎁 【宝箱】你在{name}的草丛里发现一个宝箱！\n💰 获得 {gold} 金币！{mat_line}{bp_line}",
                "mat_line": "", "bp_line": "\n📜 还翻出一张图纸：{bp}！"}},
    {"id": "merchant", "weight": 1, "name": "流浪商人",
     "desc": "一个行色匆匆的商队掉队者拦住你，想低价出手几件压箱底的好货。",
     "template": "merchant", "params": {}},
    {"id": "spring", "weight": 14, "name": "神秘泉水",
     "desc": "一汪冒着微光的泉水，喝下后感觉浑身的疲惫都被涤荡干净了。",
     "template": "heal_full",
     "params": {"header": "💧 【神秘泉水】你发现一汪泛着微光的泉水，饮下后浑身舒畅！\n❤️ 生命全满！💙 魔力全满！"}},
    {"id": "trap", "weight": 10, "name": "隐蔽的陷阱",
     "desc": "脚下突然一空，你踩进了猎人的捕兽坑！",
     "template": "damage",
     "params": {"pct": 0.15, "min": 5,
                "header": "🕳️ 【陷阱】脚下突然一空，你掉进了猎人废弃的陷阱！\n你摔伤了，损失 {dmg} 点生命(当前 ❤️ {hp}/{max_hp})"}},
    {"id": "omen", "weight": 8, "name": "古老的遗迹",
     "desc": "废墟的残垣上刻着陌生的符文，像是某位守护者留下的警示。",
     "template": "exp_gain",
     "params": {"min": 15, "scale_lv": 3,
                "header": "🏛️ 【古老遗迹】你在废墟中发现一段古老符文，隐约蕴含着知识的力量！\n✨ 经验 +{exp}"}},
    {"id": "herb", "weight": 12, "name": "草药丛",
     "desc": "一片长势喜人的野生草药，炼金师会为它们出个好价钱。",
     "template": "loot_materials",
     "params": {"mats": ["草药", "林语之叶", "谷地露水", "浆果"], "n": 1,
                "header": "🌿 【草药丛】你发现一片野生草药，采摘了一些！\n🎒 获得材料：{mats}！{extra}",
                "bp_line": ""}},
    {"id": "windfall", "weight": 10, "name": "意外之财",
     "desc": "地上散落着几枚金币，像是某位粗心商人翻车时掉的。",
     "template": "loot_gold",
     "params": {"min": 10, "max": 40, "scale_lv": 1,
                "header": "💰 【意外之财】你在地上发现几枚散落的金币，大概是某位粗心商人的损失！\n获得 {gold} 金币！"}},
    {"id": "wandering", "weight": 8, "name": "迷路的旅人",
     "desc": "一位迷路的旅人向你求助，想用随身物品换取指路。",
     "template": "wandering", "params": {}},
    # v87 02 章 7.6：常规事件扩容 8 → 12
    {"id": "lost_camp", "weight": 9, "name": "废弃营地",
     "desc": "一处被遗弃的营地，篝火余烬尚温，帐篷里似乎还有前人留下的物资。",
     "template": "loot_materials",
     "params": {"mats": ["狼皮", "兽肉", "铁矿石", "野猪牙", "魔法粉尘"], "n": 2,
                "blueprint_chance": 0.15,
                "header": "🏕️ 【废弃营地】你翻找着前人的遗物——篝火余烬还带着温度。\n🎒 获得材料：{mats}！{extra}",
                "bp_line": "\n📜 帐篷角落里还压着一张图纸：{bp}！"}},
    {"id": "meteor", "weight": 5, "name": "陨石坑",
     "desc": "地面凹陷着一个冒着热气的陨石坑，坑底嵌着一块奇异的金属。",
     "template": "combo",
     "params": {"steps": [
         {"template": "loot_materials",
          "params": {"mats": ["铁矿石", "秘银", "精铁", "星辉石"], "n": 1,
                     "header": "☄️ 【陨石坑】坑底嵌着一块奇异的金属，你费了番力气把它撬了出来。\n🎒 获得矿石：{mats}！{extra}",
                     "bp_line": ""}},
         {"template": "exp_gain",
          "params": {"min": 20, "scale_lv": 2, "header": "✨ 经验 +{exp}"}},
     ]}},
    {"id": "animal", "weight": 9, "name": "迷路的小动物",
     "desc": "一只小动物从灌木丛探出头来，好奇地打量着你。",
     "template": "loot_materials",
     "params": {"mats": ["兽肉", "狼皮", "兔毛", "兔皮"], "n": 1,
                "header": "🐿️ 【迷路的小动物】你喂了它一点干粮，小家伙蹭了蹭你的手，留下一份谢礼跑了。\n🎒 获得：{mats}！{extra}",
                "bp_line": ""}},
    {"id": "rain", "weight": 7, "name": "突如其来的雨",
     "desc": "天空骤然阴沉，豆大的雨点砸了下来。",
     "template": "set_state",
     "params": {"key": "rain_{gid}_{qid}",
                "value": "ts",
                "header": "🌧️ 【突如其来的雨】豆大的雨点砸下来，你躲进树荫避雨。\n雨后的空气格外清新——你感到一阵清明(接下来 30 分钟探索遇怪率小幅提升)。"}},
]

# v83 02 章 7.5：探索彩蛋事件（独立于常规权重，总概率 EXPLORE_EGG_CHANCE）
# 命中后按权重分配：流星 60 / 宝匣 30 / 访客 10 → 实际 0.30%/0.15%/0.05%
EXPLORE_EGG_CHANCE = 0.005
EXPLORE_EGG_EVENTS = [
    {"id": "shooting_star", "weight": 60, "name": "流星许愿",
     "desc": "一道流星划过夜空！",
     "template": "set_state",
     "params": {"key": "wish_{gid}_{qid}", "value": "wish_ts",
                "header": "🌠 【流星许愿】一道流星拖着长尾划过{name}的夜空！\n你赶紧闭上眼睛许愿——流星似乎回应了你！\n━━━━━━━━━━━━\n💡 快决定吧：『许愿 经验』『许愿 金币』『许愿 材料』"}},
    {"id": "mystery_chest", "weight": 30, "name": "神秘宝匣",
     "desc": "埋藏千年的宝匣。",
     "template": "mystery_chest", "params": {}},
    {"id": "night_visitor", "weight": 10, "name": "神秘访客",
     "desc": "雾中出现的神秘身影。",
     "template": "set_flag",
     "params": {"flag": "h_abyss_whisper", "key": "saw_the_rift",
                "header": "🌫️ 【神秘访客】雾气突然涌起，一道模糊的身影拦住了你。\n“深渊的裂隙……正在低语……去找它。”\n身影说完便消散在雾中，你隐约感到，某个秘密被揭开了(隐藏线索已记入见闻)。"}},
    # v87 02 章 7.5：彩蛋扩充（权重相应调低老彩蛋）
    {"id": "old_map", "weight": 12, "name": "泛黄藏宝图",
     "desc": "一张泛黄的藏宝图。",
     "template": "set_flag",
     "params": {"flag": "h_lost_library", "key": "got_old_map",
                "header": "🗺️ 【泛黄藏宝图】你在一棵老树的树洞里发现一张泛黄的藏宝图！\n图上画着一条通往圣堂地窖深处的地下通道，边缘写着：\n“三页旧纸，一扇石门——书页不齐，石门不开。”\n你收好藏宝图(隐藏线索：失落图书馆·书页之一 已记入见闻)。"}},
    {"id": "gold_slime", "weight": 8, "name": "金色史莱姆",
     "desc": "一只通体金黄的史莱姆！",
     "template": "loot_gold_mats",
     "params": {"min": 200, "max": 400, "scale_lv": 30,
                "mats": ["琥珀精华"], "blueprint_chance": 0,
                "header": "✨ 【金色史莱姆】一只通体金黄的史莱姆蹦跳着挡住去路！\n你三两下把它敲扁——金色的浆液迸溅出来！\n💰 获得 {gold} 金币！{mat_line}{bp_line}",
                "mat_line": "\n🎒 获得稀有材料：{mat}！", "bp_line": ""}},
]
EXPLORE_EGG_SUM = sum(e["weight"] for e in EXPLORE_EGG_EVENTS)


EVENT_WEIGHT_SUM = sum(e["weight"] for e in EXPLORE_EVENTS)
