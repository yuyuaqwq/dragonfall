# -*- coding: utf-8 -*-
"""v95.29 城镇活人计划 Part2：剩余城镇补酱油 NPC
用法：python scripts/add_flavor_npcs2.py
"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
NPCS_PATH = os.path.join(BASE, "..", "game", "data", "npcs.py")
SUBAREAS_PATH = os.path.join(BASE, "..", "game", "data", "subareas.py")

NEW_NPCS = {
    # ===== 月门城 =====
    "npc_moongate_traveler": {"name": "商队护卫·快刀", "title": "月门城商队护卫", "map": "moon_gate", "icon": "🗡️", "dialogue": "跟着商队翻过月冠隘口，一路风大石头多。不过到了月门城就踏实了——这里的旅店被子暖和！"},
    "npc_moongate_inn": {"name": "旅店伙计·月牙", "title": "银月旅店伙计", "map": "moon_gate", "icon": "🛏️", "dialogue": "客官您运气好，今晚还剩一间朝月的房间！夜里躺在窗边看月亮，保管您值回房钱。"},
    "npc_moongate_spice": {"name": "香料贩·桂香", "title": "月门城香料贩", "map": "moon_gate", "icon": "🌶️", "dialogue": "月桂、星椒、云盐……从山那边运来的好香料！闻闻这星椒，炒肉一绝！"},
    # ===== 星歌镇 =====
    "npc_starsong_acrobat": {"name": "杂耍艺人·转盘", "title": "星歌镇杂耍艺人", "map": "star_song", "icon": "🤹", "dialogue": "看好了！三个盘子一起转！……哎哟，又掉一个。没关系，再来！反正观众还没走光。"},
    "npc_starsong_florist": {"name": "花贩·露珠", "title": "星歌镇花贩", "map": "star_song", "icon": "🌸", "dialogue": "星歌镇的夜里开的花，白天也香。买一枝别在胸前吧，冒险也要有仪式感嘛！"},
    "npc_starsong_waiter": {"name": "店小二·灯笼", "title": "星歌旅店伙计", "map": "star_song", "icon": "🏮", "dialogue": "夜路走多了，进来歇歇脚吧。我们店的热茶不要钱，管够！"},
    # ===== 寒角堡 =====
    "npc_frost_leather": {"name": "皮匠·厚毛", "title": "寒角堡皮匠", "map": "frost_horn", "icon": "🧥", "dialogue": "北地的风比刀子还利！这件熊皮外套，穿上它，连霜巨魔见了都得让你三分。"},
    "npc_frost_elder": {"name": "部落长者·灰须", "title": "寒角堡部落长者", "map": "frost_horn", "icon": "🪶", "dialogue": "年轻的时候，我也曾握剑远征。现在嘛，我的战场是火塘边的故事会。来，坐下听一段？"},
    "npc_frost_drinker": {"name": "酒客·大杯", "title": "霜角酒馆常客", "map": "frost_horn", "icon": "🍺", "dialogue": "霜角堡的规矩：酒杯不能空，故事不能短！……嗝，这条其实是我编的，但大家都很配合。"},
    "npc_frost_armorer": {"name": "甲匠·铁鳞", "title": "寒角堡守备营甲匠", "map": "frost_horn", "icon": "🛡️", "dialogue": "营里的甲片都是我一片片敲的。北地的仗不好打，甲不行就是拿命开玩笑！"},
    # ===== 铁砧要塞 =====
    "npc_anvil_apprentice": {"name": "矮人学徒·炉渣", "title": "铁砧要塞锻工学徒", "map": "anvil_fort", "icon": "🔨", "dialogue": "师父说，矮人的锤子一辈子只认一个主人。我这把锤子还认生，正跟它培养感情呢！"},
    "npc_anvil_clerk": {"name": "议会书记·铁笔", "title": "铁砧议会厅书记官", "map": "anvil_fort", "icon": "📜", "dialogue": "长老们的会议纪要，每一页我都要抄三遍——第一遍听，第二遍记，第三遍防他们改口。"},
    "npc_anvil_runeapp": {"name": "符文学徒·刻痕", "title": "符文工坊学徒", "map": "anvil_fort", "icon": "✨", "dialogue": "符文刻错一笔，整块石头就废了。我桌上那堆废料……大概能垒个小塔了。"},
    "npc_anvil_mule": {"name": "骡夫·驼铃", "title": "铁砧堡运货骡夫", "map": "anvil_fort", "icon": "🫏", "dialogue": "从铁港到铁砧，骡子换了三匹，我一件没丢！信誉，就是我们骡夫的本钱！"},
    # ===== 极光镇 =====
    "npc_aurora_lantern": {"name": "灯笼匠·光点", "title": "极光镇灯笼匠", "map": "aurora_town", "icon": "🏮", "dialogue": "极光虽美，照不亮夜路。我这灯笼用冰晶石做的芯，亮一整晚不带灭的！"},
    "npc_aurora_butler": {"name": "管家·暖烛", "title": "极光镇镇长公馆管家", "map": "aurora_town", "icon": "🕯️", "dialogue": "公馆的壁炉每天添三次柴。镇长大人说，客人的手不能凉着——这是极光镇的待客之道。"},
    "npc_aurora_reindeer": {"name": "驯鹿人·雪角", "title": "极光镇驯鹿人", "map": "aurora_town", "icon": "🦌", "dialogue": "我的驯鹿叫'北风'，跑起来比风还快！要不要骑一圈？……它今天心情不错，应该不会撂橛子。"},
    "npc_aurora_innkeep2": {"name": "旅店帮手·热汤", "title": "暖炉旅店帮手", "map": "aurora_town", "icon": "🍲", "dialogue": "刚炖好的鹿肉汤，加了极地香草！喝一碗，从嗓子暖到脚底板。"},
    "npc_aurora_sled": {"name": "雪橇夫·滑痕", "title": "极光镇雪橇夫", "map": "aurora_town", "icon": "🛷", "dialogue": "要去永冻冰原？雪橇一天就到！路上能看到极光落在雪地上，那景色，啧啧，一辈子忘不了。"},
    # ===== 龙裔聚落 =====
    "npc_dragonkin_child": {"name": "龙裔孩童·小爪", "title": "龙裔聚落孩童", "map": "dragon_kin", "icon": "🧒", "dialogue": "你看我手上的鳞片！长老说等我能喷出火星，就让我去祭坛帮忙！……虽然现在还只能冒烟。"},
    "npc_dragonkin_priestess": {"name": "祭司学徒·燃香", "title": "龙裔祭坛祭司学徒", "map": "dragon_kin", "icon": "🕯️", "dialogue": "祭坛的圣火千年不灭。我每天的工作就是添柴、祈祷、再添柴……长老说这叫修行。"},
    "npc_dragonkin_cook": {"name": "龙裔厨娘·炙烤", "title": "龙裔聚落厨娘", "map": "dragon_kin", "icon": "🍖", "dialogue": "龙裔的菜谱很简单：肉、火、盐。但火候嘛，可是祖传的秘诀！来，尝尝这块肋排！"},
    # ===== 翡翠港 =====
    "npc_jade_sailor": {"name": "水手·绿浪", "title": "翡翠港水手", "map": "jade_port", "icon": "⚓", "dialogue": "翡翠港的船，能去海上任何地方！只要你不晕船，也不怕海妖唱歌。"},
    "npc_jade_spice": {"name": "香料商·青烟", "title": "翡翠集市香料商", "map": "jade_port", "icon": "🌿", "dialogue": "这包是群岛的丁香，那罐是深海的盐晶！海上运来的都是好东西，尝尝？"},
    "npc_jade_waiter": {"name": "旅店账房·算珠", "title": "船坞旅店账房", "map": "jade_port", "icon": "🧮", "dialogue": "住一晚三十铜，管一顿早饭。多住一晚送一壶热茶！本店童叟无欺，账本就在柜台，随便查。"},
    # ===== 贝壳镇 =====
    "npc_shell_coral": {"name": "珊瑚贩·红枝", "title": "贝壳镇珊瑚贩", "map": "shell_town", "icon": "🪸", "dialogue": "这枝红珊瑚，是我潜了九丈深才采到的！摆在桌上，天天都是海的颜色。"},
    "npc_shell_fisher": {"name": "渔夫·满舱", "title": "贝壳镇渔夫", "map": "shell_town", "icon": "🎣", "dialogue": "今天的网是满的！鲷鱼、鲈鱼、还有几条不认识的……反正在海上，认识不认识都能吃。"},
    "npc_shell_helper": {"name": "旅店帮手·海螺", "title": "贝壳镇旅店帮手", "map": "shell_town", "icon": "🐚", "dialogue": "靠海的房间，晚上能听着潮声睡觉。城里人稀罕这个，我们天天听，耳朵都习惯了！"},
    "npc_shell_kelp": {"name": "捞藻人·绿衣", "title": "贝壳镇捞海藻人", "map": "shell_town", "icon": "🌊", "dialogue": "海藻晒干了能入药、能当柴、还能织绳！海里全是宝贝，就看你会不会捞。"},
    # ===== 无名港 =====
    "npc_nameless_sellsword": {"name": "佣兵·无名", "title": "无名港佣兵", "map": "nameless_harbor", "icon": "⚔️", "dialogue": "这座港里的规矩你记住了：不问名字，不问来历，不问货。……当然，价钱还是要问的。"},
    "npc_nameless_clerk": {"name": "港务文员·墨痕", "title": "无名港港务厅文员", "map": "nameless_harbor", "icon": "📒", "dialogue": "每艘进港的船都要登记。名字可以假、货可以瞒，但这本册子上的墨迹必须是真的。"},
    "npc_nameless_deckhand": {"name": "水手·黑帆", "title": "无名港远洋水手", "map": "nameless_harbor", "icon": "🪢", "dialogue": "远洋的船，装的都是远洋的故事。想知道？先请我喝一杯，故事下酒才够味。"},
    "npc_nameless_pilot": {"name": "引航员·雾灯", "title": "无名港外海引航员", "map": "nameless_harbor", "icon": "💡", "dialogue": "夜里进港，跟着我的灯走。雾再大，我的灯也亮——这是无名港的老规矩了。"},
    # ===== 珍珠城 =====
    "npc_pearl_crafter": {"name": "珍珠匠·圆润", "title": "珍珠城珍珠匠", "map": "pearl_city", "icon": "📿", "dialogue": "这一串，颗颗都是南海深水珠！穿一颗要半天功夫，急不得。好东西，都急不得。"},
    "npc_pearl_lady": {"name": "城主侍女·轻纱", "title": "珍珠城城主府侍女", "map": "pearl_city", "icon": "👗", "dialogue": "城主大人正在理事。您要是有要紧事，我可以帮您递个话——但要等她把潮汐图看完。"},
    "npc_pearl_auction2": {"name": "拍卖行伙计·亮槌", "title": "珊瑚拍卖行伙计", "map": "pearl_city", "icon": "🔔", "dialogue": "今晚压轴的是一件深海夜明珠！起拍价嘛……反正我三个月的薪水都够不着。"},
    "npc_pearl_merchant": {"name": "商行掌柜·海算", "title": "珍珠城商行掌柜", "map": "pearl_city", "icon": "🧮", "dialogue": "珍珠论颗卖，海货论筐收。我在这行干了三十年，眼力比海深！"},
    "npc_pearl_fishwife": {"name": "鱼市婆·咸风", "title": "珍珠城渔港鱼贩", "map": "pearl_city", "icon": "🐟", "dialogue": "刚靠岸的船，鱼还带着海水的鲜气！来两条？算你便宜点，下次还来我摊子！"},
    # ===== 深岩隧道 =====
    "npc_tunnel_foreman": {"name": "工头·响鞭", "title": "深岩隧道工头", "map": "deep_tunnel", "icon": "📢", "dialogue": "三班倒，人不歇，灯不灭！这条隧道是矮人兄弟们一镐一镐凿出来的。干活！"},
    "npc_tunnel_engineer": {"name": "工程师·圆规", "title": "深岩隧道工程师", "map": "deep_tunnel", "icon": "📐", "dialogue": "岩层的走向、铁轨的坡度、通风口的间距……每一寸都要算准。地底干活，错一尺就是塌方！"},
    "npc_tunnel_cook": {"name": "厨娘·热锅", "title": "深岩隧道营地厨娘", "map": "deep_tunnel", "icon": "🍲", "dialogue": "地底湿气重，喝碗姜汤再干活！矿工们都说，我这一锅汤能顶半件皮袄。"},
    "npc_tunnel_trackman": {"name": "轨道工·压道", "title": "深岩隧道轨道工", "map": "deep_tunnel", "icon": "🛤️", "dialogue": "这铁轨是通往地底集市的命脉！矿车一天跑八趟，我的锤子一天敲八千下。稳得很！"},
    # ===== 地底集市 =====
    "npc_under_herbalist": {"name": "菌药贩·灰帽", "title": "地底集市菌药贩", "map": "under_market", "icon": "🍄", "dialogue": "荧光菇治失眠，血耳菇止血，暗苔治咳嗽……地底的东西，看着吓人，用着灵光！"},
    "npc_under_broker": {"name": "拍卖掮客·巧舌", "title": "地底集市拍卖掮客", "map": "under_market", "icon": "🗣️", "dialogue": "地底的宝贝，识货的才有缘。您要是想找点稀罕物，找我，准没错——佣金嘛，好商量。"},
    "npc_under_helper": {"name": "旅店伙计·昏灯", "title": "地底集市旅店伙计", "map": "under_market", "icon": "🛏️", "dialogue": "地底没有白天黑夜，我们的钟点全靠菌灯的明暗。累了就睡，醒了就干，自由得很！"},
    "npc_under_farmer": {"name": "菌农·孢子", "title": "地底集市菌农", "map": "under_market", "icon": "🌱", "dialogue": "我种的荧光菇，又大又亮！拿去当灯使，能亮半个月。当然，炖汤更香。"},
    # ===== 灰烬营地 =====
    "npc_ember_weaponsmith": {"name": "武器匠·烬铁", "title": "灰烬营地武器匠", "map": "ember_camp", "icon": "⚒️", "dialogue": "地底的铁，淬过岩浆才是好铁！我这儿的家伙什，劈岩石都跟切豆腐似的。"},
    "npc_ember_adjutant": {"name": "副官·黑旗", "title": "灰烬营地副官", "map": "ember_camp", "icon": "📯", "dialogue": "营长大人正忙着规划新路线。您要有委托，先跟我说，我给您排个号！"},
    "npc_ember_mapper": {"name": "绘图员·炭笔", "title": "灰烬营地地底绘图员", "map": "ember_camp", "icon": "🗺️", "dialogue": "地底的地图，都是用命换来的。这一笔是熔岩道，这一划是塌方区……您可千万别走我画错的地方。"},
    "npc_ember_storeman": {"name": "粮秣员·实秤", "title": "灰烬营地补给站粮秣员", "map": "ember_camp", "icon": "⚖️", "dialogue": "干粮、火把、绳索、药膏……一样都不能少。去地底，多带一根绳子，就多一条命！"},
    # ===== 风翼城 =====
    "npc_wind_cloudmerchant": {"name": "云商·白帆", "title": "风翼城云商", "map": "wind_city", "icon": "🪁", "dialogue": "云母、风石、天鹰羽毛……云上有的，我这儿都卖！要什么？报个价，云舟三天送到。"},
    "npc_wind_scribe": {"name": "议会书记·飘墨", "title": "云翼议会厅书记官", "map": "wind_city", "icon": "📜", "dialogue": "长老们的决议，风一吹就散。所以我用云墨写在石板上——风吹不动，才记得住。"},
    "npc_wind_guard2": {"name": "云门卫·展翼", "title": "风翼城云门守卫", "map": "wind_city", "icon": "🛡️", "dialogue": "云门一开，就是云海。第一次站这儿的人腿都软——放心，门边有护栏，我扶着您！"},
    # ===== 月冠王庭 =====
    "npc_elf_poet2": {"name": "精灵诗人·月弦", "title": "月冠王庭吟游诗人", "map": "moon_court", "icon": "🎻", "dialogue": "月光是最好的听众，星河是最好的幕布。要我唱一支古老的精灵谣吗？"},
    "npc_elf_maid": {"name": "侍女·露华", "title": "月辉王宫侍女", "map": "moon_court", "icon": "👗", "dialogue": "女王的会客厅在月影回廊尽头。她此刻正在听风，您要拜访的话，等风停了再去吧。"},
    "npc_elf_trainee": {"name": "月影卫见习·星痕", "title": "月影卫营见习卫士", "map": "moon_court", "icon": "🗡️", "dialogue": "月影卫的规矩：影子先动，人后动。我练了三年，影子总算肯听我的话了。"},
    "npc_elf_librarian": {"name": "书阁学徒·卷页", "title": "贤者书阁学徒", "map": "moon_court", "icon": "📚", "dialogue": "这座书阁的藏书，据说够读三百年。我负责整理第九层……现在才理到第三排。"},
    "npc_elf_gateguard2": {"name": "宫门卫·银芒", "title": "月庭宫门守卫", "map": "moon_court", "icon": "🛡️", "dialogue": "月庭重地，请报上名来。……放心，只是登记，不会盘问三遍的，今天不是满月。"},
    # ===== 寒脊营地 =====
    "npc_cold_skinner": {"name": "皮货商·霜皮", "title": "寒脊营地皮货商", "map": "cold_ridge", "icon": "🧥", "dialogue": "雪狼皮、冰熊皮、白狐皮！北地的皮货，南边的人抢着要。您要哪张？给您挑张最厚的！"},
    "npc_cold_oldherder": {"name": "老牧民·长鞭", "title": "寒脊营地老牧民", "map": "cold_ridge", "icon": "🐑", "dialogue": "我赶了四十年驯鹿，闭着眼都能回营地。年轻人，雪地里迷路别慌，跟着鹿蹄印走！"},
    "npc_cold_bowyer": {"name": "弓匠·白桦", "title": "寒脊营地弓匠", "map": "cold_ridge", "icon": "🏹", "dialogue": "好弓要有好木。北地的白桦，韧得像钢！我这儿的弓，拉满不裂，放箭不飘。"},
    "npc_cold_patrol": {"name": "巡逻兵·踏雪", "title": "寒脊营地巡逻兵", "map": "cold_ridge", "icon": "🛡️", "dialogue": "夜里的雪原，狼嚎是家常便饭。有我们巡逻队守着，营地里的炉火才能安心烧着。"},
    # ===== 龙脊山口 =====
    "npc_pass_caravan": {"name": "商队护卫·长路", "title": "龙脊山口商队护卫", "map": "dragon_pass", "icon": "🐫", "dialogue": "翻龙脊山口的商队，都得在这儿歇脚补粮。山风大，路也陡，但过了山口就是另一片天地！"},
    "npc_pass_attendant": {"name": "长老侍从·火纹", "title": "龙裔长老堂侍从", "map": "dragon_pass", "icon": "🕯️", "dialogue": "长老正在温习古老的龙语祷文。您要拜访的话，请先在门外候一候——龙语背到一半，不能打断。"},
    "npc_pass_sentinel": {"name": "关隘哨兵·风旗", "title": "龙脊山口关隘哨兵", "map": "dragon_pass", "icon": "🚩", "dialogue": "山口的旗子一年换七次，全是被风撕烂的。您看那旗角——这就是龙脊的风，烈着呢！"},
}

MOUNTS = {
    "moon_gate_1": ["npc_moongate_traveler"],
    "moon_gate_2": ["npc_moongate_inn"],
    "moon_gate_3": ["npc_moongate_spice"],
    "star_song_1": ["npc_starsong_acrobat"],
    "star_song_2": ["npc_starsong_florist"],
    "star_song_3": ["npc_starsong_waiter"],
    "frost_horn_1": ["npc_frost_leather"],
    "frost_horn_2": ["npc_frost_elder"],
    "frost_horn_3": ["npc_frost_drinker"],
    "frost_horn_4": ["npc_frost_armorer"],
    "anvil_fort_1": ["npc_anvil_apprentice"],
    "anvil_fort_2": ["npc_anvil_clerk"],
    "anvil_fort_3": ["npc_anvil_runeapp"],
    "anvil_fort_gate": ["npc_anvil_mule"],
    "aurora_town_1": ["npc_aurora_lantern"],
    "aurora_town_2": ["npc_aurora_butler"],
    "aurora_town_3": ["npc_aurora_reindeer"],
    "aurora_town_4": ["npc_aurora_innkeep2"],
    "aurora_town_path": ["npc_aurora_sled"],
    "dragon_kin_1": ["npc_dragonkin_child"],
    "dragon_kin_2": ["npc_dragonkin_priestess"],
    "dragon_kin_3": ["npc_dragonkin_cook"],
    "jade_port_1": ["npc_jade_sailor"],
    "jade_port_2": ["npc_jade_spice"],
    "jade_port_3": ["npc_jade_waiter"],
    "shell_town_1": ["npc_shell_coral"],
    "shell_town_2": ["npc_shell_fisher"],
    "shell_town_3": ["npc_shell_helper"],
    "shell_town_beach": ["npc_shell_kelp"],
    "nameless_harbor_1": ["npc_nameless_sellsword"],
    "nameless_harbor_2": ["npc_nameless_clerk"],
    "nameless_harbor_3": ["npc_nameless_deckhand"],
    "nameless_harbor_anchorage": ["npc_nameless_pilot"],
    "pearl_city_1": ["npc_pearl_crafter"],
    "pearl_city_2": ["npc_pearl_lady"],
    "pearl_city_3": ["npc_pearl_auction2"],
    "pearl_city_4": ["npc_pearl_merchant"],
    "pearl_city_5": ["npc_pearl_fishwife"],
    "deep_tunnel_1": ["npc_tunnel_foreman"],
    "deep_tunnel_2": ["npc_tunnel_engineer"],
    "deep_tunnel_3": ["npc_tunnel_cook"],
    "deep_tunnel_mouth": ["npc_tunnel_trackman"],
    "under_market_1": ["npc_under_herbalist", "npc_under_farmer"],
    "under_market_2": ["npc_under_broker"],
    "under_market_3": ["npc_under_helper"],
    "ember_camp_1": ["npc_ember_weaponsmith"],
    "ember_camp_2": ["npc_ember_adjutant"],
    "ember_camp_3": ["npc_ember_mapper"],
    "ember_camp_4": ["npc_ember_storeman"],
    "wind_city_1": ["npc_wind_cloudmerchant"],
    "wind_city_2": ["npc_wind_scribe"],
    "wind_city_gate": ["npc_wind_guard2"],
    "moon_court_1": ["npc_elf_poet2"],
    "moon_court_2": ["npc_elf_maid"],
    "moon_court_3": ["npc_elf_trainee"],
    "moon_court_4": ["npc_elf_librarian"],
    "moon_court_gate": ["npc_elf_gateguard2"],
    "cold_ridge_1": ["npc_cold_skinner"],
    "cold_ridge_2": ["npc_cold_oldherder"],
    "cold_ridge_3": ["npc_cold_bowyer"],
    "cold_ridge_sentry": ["npc_cold_patrol"],
    "dragon_pass_1": ["npc_pass_caravan"],
    "dragon_pass_2": ["npc_pass_attendant"],
    "dragon_pass_gate": ["npc_pass_sentinel"],
}

# ============ 写入 npcs.py（末尾追加 NPCS.update） ============
def append_npcs():
    with open(NPCS_PATH, encoding="utf-8") as f:
        txt = f.read()
    # 按 id 逐个检查（分批执行时 npcs.py 可能已有 v95.29 标记）
    missing = [k for k in NEW_NPCS if f"{k!r}:" not in txt and f'"{k}":' not in txt]
    if not missing:
        print("npcs.py 全部 id 已存在，跳过")
        return
    block = "\n\n# ===== v95.29 城镇活人计划 Part2（酱油 NPC）=====\nNPCS.update({\n"
    for k in missing:
        v = NEW_NPCS[k]
        block += f"    {k!r}: {{\n"
        for fk, fv in v.items():
            block += f"        {fk!r}: {fv!r},\n"
        block += "    },\n"
    block += "})\n"
    with open(NPCS_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(txt + block)
    print(f"npcs.py 追加 {len(missing)} 个 NPC")

# ============ 写入 subareas.py（每个 sa 的 npcs 数组追加） ============
def append_mounts():
    with open(SUBAREAS_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    cur_id = None
    changed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
        if m:
            cur_id = m.group(1)
            i += 1
            continue
        if cur_id in MOUNTS and '"npcs"' in line:
            add_ids = MOUNTS[cur_id]
            # 情况A：单行数组 "npcs": [...] 或 "npcs": [],
            mm = re.search(r'"npcs"\s*:\s*\[([^\]]*)\]', line)
            if mm:
                inner = mm.group(1).strip()
                existing_ids = set(re.findall(r'"([a-z0-9_]+)"', inner))
                add_ids = [x for x in add_ids if x not in existing_ids]
                if add_ids:
                    if inner:
                        new_inner = inner + ", " + ", ".join(repr(x) for x in add_ids)
                    else:
                        new_inner = ", ".join(repr(x) for x in add_ids)
                    lines[i] = line[:mm.start(1)] + new_inner + line[mm.end(1):]
                    changed += 1
                cur_id = None
                i += 1
                continue
            # 情况B：多行数组 "npcs": [\n  "id"\n],（结束行可能是 "],            \"monsters\": []" 紧凑格式）
            if re.search(r'"npcs"\s*:\s*\[\s*$', line):
                indent = re.match(r'(\s*)', line).group(1) + "    "
                j = i + 1
                while j < len(lines) and "]," not in lines[j]:
                    j += 1
                if j < len(lines):
                    # 检查数组内是否已有 id（防重复挂载）
                    existing = " ".join(lines[i+1:j])
                    new_ids = [x for x in add_ids if x not in existing]
                    if new_ids:
                        # 前一行（原最后一项）若不以逗号结尾，补逗号
                        prev = j - 1
                        prev_line = lines[prev].rstrip("\r\n")
                        if prev_line.strip() and not prev_line.rstrip().endswith(","):
                            lines[prev] = prev_line + ",\n"
                        # 在结束行（含 ], 的行）前插入新 id
                        lines.insert(j, indent + ", ".join(repr(x) for x in new_ids) + ",\n")
                        changed += 1
                    cur_id = None
                    i = j + 1
                    continue
        i += 1
    with open(SUBAREAS_PATH, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print(f"subareas.py 挂载 {changed} 处")

if __name__ == "__main__":
    append_npcs()
    append_mounts()
    import py_compile
    for p in (NPCS_PATH, SUBAREAS_PATH):
        py_compile.compile(p, doraise=True)
        print(f"编译 OK: {os.path.basename(p)}")
