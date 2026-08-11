# -*- coding: utf-8 -*-
"""v95.30 城镇 NPC 随机性数据配置：roam(游走)/appear(概率)/period(时段)/lines(台词)
铁律：
- 只配酱油 NPC（funcs=[]）——功能 NPC 永不随机（任务链安全）
- roam 只在相连子区域间游走（城镇星形：广场↔场所）
- lines 台词有生活气，每天轮换（日期哈希）
用法：python scripts/add_npc_randomness.py
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

NPCS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "data", "npcs.py")

# npc_id → 补丁字段（update 合并，不覆盖原 dialogue）
PATCHES = {
    # ========== 橡木镇（广场/街道/镇郊 星形） ==========
    "npc_oak_candy": {  # 卖糖人：广场↔东大街 沿街叫卖
        "roam": ["oak_town_1", "oak_town_street"],
        "lines": [
            "糖葫芦哎——现熬的麦芽糖，甜到心里头！冒险者来一串？保准打史莱姆都有劲。",
            "今儿个风大，糖得裹厚点！来，尝尝刚出锅的——小心烫嘴！",
            "收摊前最后一串，便宜卖啦！留着钱给明天的小本生意咯。",
        ],
    },
    "npc_oak_novice": {  # 新手冒险者：广场↔镇郊 练级来回
        "roam": ["oak_town_1", "oak_town_outskirts"],
        "appear": 0.85,
        "lines": [
            "今天一定要打到一张史莱姆黏液！……虽然上次差点被巨型野猪追回镇里，但那都是意外。",
            "行会的小艾说我出剑姿势不对，但我寻思能砍到怪就行呗？",
            "你听说了吗，白鹿城的冒险者都穿铁甲了！我啥时候才能攒够钱换身好装备……",
        ],
    },
    "npc_oak_oldman": {  # 老爷子：广场↔东大街 遛弯
        "roam": ["oak_town_1", "oak_town_street"],
        "lines": [
            "我年轻时也闯过白鹿城！现在嘛，广场这长椅就是我的冒险地。年轻人，外面的世界大着咧。",
            "东大街那家烤面包，我吃了二十年，还是那个味儿。你要不要也去尝尝？",
            "老了，腿脚不利索，就在镇上溜达。看你们年轻人来来往往，也挺好。",
        ],
    },
    "npc_oak_kid": {  # 顽童：满镇乱跑
        "roam": ["oak_town_1", "oak_town_street", "oak_town_4"],
        "appear": 0.8,
        "lines": [
            "我妈说我再追鸡就罚我扫院子！嘿嘿，但我还是会追，你看那只鸡多神气！",
            "镇长家的猫昨天又跑到旅店去了，还是我给它抱回来的！我厉害吧？",
            "等我长大了，也要像冒险者一样拿剑！……不过现在先让我把弹弓玩明白。",
        ],
    },
    "npc_oak_vegwife": {  # 卖菜婶：东大街↔广场
        "roam": ["oak_town_street", "oak_town_1"],
        "lines": [
            "刚从地里摘的，水灵着呢！冒险者也要吃饭，来把青菜，配着野猪肉炖，香得很！",
            "今儿个的萝卜甜，炖汤一绝！你上回说要去打野猪，打着了没？",
            "集市要散了，给你算便宜点，剩的这些带回去，晚上加个菜！",
        ],
    },
    "npc_oak_farmer": {  # 农夫：镇郊↔东大街
        "roam": ["oak_town_outskirts", "oak_town_street"],
        "lines": [
            "这片田我种了二十年了。镇长说镇上来了个能打史莱姆的冒险者，就是你吧？好样的！",
            "今年雨水好，麦子长得比去年高。秋天你有空来，请你吃新麦饼！",
            "田里的活儿干不完咯。你要是闲下来，帮我赶赶田边的野兔？",
        ],
    },
    "npc_oak_bellboy": {"appear": 0.9},  # 旅店伙计偶尔忙
    "npc_oak_herb_girl": {"appear": 0.9},
    # ========== 白鹿城（广场↔酒馆/圣堂/城门） ==========
    "npc_deer_bard": {  # 吟游诗人：广场↔酒馆 卖艺
        "roam": ["white_deer_1", "white_deer_5"],
        "appear": 0.8,
        "lines": [
            "（拨弦）白鹿城的故事三天三夜唱不完——南境的雪、铁港的浪、还有圣光下失落的王冠。给个铜板，我唱你听？",
            "（调弦）新编了一曲《鹿角与麦酒》，献给酒馆的胖托尼老板！唱完这曲，酒钱能免不？",
            "（低语）听说王都那边出了大事……咳，这歌我今天不唱，明天也不唱，你懂的。",
        ],
    },
    "npc_deer_drunk": {  # 醉汉：酒馆↔广场，晚上出没
        "roam": ["white_deer_5", "white_deer_1"],
        "period": ["night"],
        "lines": [
            "我跟你说……嗝！这酒馆的麦酒，全南境第一！当年我……我在海上……嗝，算了，不重要！",
            "嗝……你、你也是冒险者？我年轻时……也差点是！就差那么一点点！",
            "老板！再来一杯！……什么？账？嗝，记我头上，回头我儿子来结！",
        ],
    },
    "npc_deer_guard": {  # 巡城卫兵：广场↔城门 巡逻
        "roam": ["white_deer_1", "white_deer_gate"],
        "lines": [
            "白鹿城宵禁前请回到城墙内。……这是例行提醒，不用紧张，你一看就是个正经冒险者。",
            "今天南门那边来了支大商队，运了满满三车货。白鹿城啊，一天比一天热闹。",
            "巡城一圈又一圈，鞋底都要磨穿了。不过能守着这座城，值！",
        ],
    },
    "npc_deer_nun": {"lines": [  # 修女：圣堂常驻，台词轮换
        "圣光庇佑每一位赶路的人。来，这里有一小袋干粮，带上吧，愿它陪你走完旅程。",
        "愿圣光指引你的道路。累了的时候，圣堂的门永远为你敞开。",
        "最近来圣堂祈祷的冒险者变多了。你们在外闯荡，也别忘了照顾好自己。",
    ]},
    "npc_deer_cook": {"appear": 0.9},
    "npc_deer_enchanter": {"appear": 0.9},
    "npc_deer_gatekeeper": {"roam": ["white_deer_gate", "white_deer_1"], "appear": 0.95},  # 城门卫：门口↔广场
    # ========== 铁港城 ==========
    "npc_harbor_sailor": {  # 老水手：广场↔酒馆 讲海故事
        "roam": ["ironharbor_1", "ironharbor_5"],
        "lines": [
            "小兄弟，想听海上的故事？我这辈子见过比房子还大的鲸鱼、比旗杆还高的浪！……当然，有一半是我编的。",
            "船靠岸了，先来杯酒润润嗓子！海上三个月，嘴里全是咸味。",
            "听说雾潮航道最近不太平……水手们都在传。你走海路的话，多留个心眼。",
        ],
    },
    "npc_harbor_bartender": {"period": ["day", "night"], "lines": [  # 酒保
        "本店规矩：先付钱，后喝酒；吹牛可以，打架出去打。客官，来杯铁锚特调？保证你喝一口想家。",
        "水手们喝多了就爱吹牛，我听着听着也信了三分。铁锚酒馆的故事，比海还深！",
        "打烊前最后一轮！要续杯的赶紧——明天还得早起卸货呢。",
    ]},
    "npc_harbor_watchman": {"period": ["night"], "lines": [  # 打更人：夜里巡街
        "天干物燥——小心火烛！铁港的夜，交给我守着。",
        "三更天了，港口还亮着灯。都是赶夜路的辛苦人哪。",
        "（敲梆子）夜半风声紧，门窗要关严！老铜我巡街，保大家安眠！",
    ]},
    "npc_harbor_fisher": {"period": ["day"], "roam": ["ironharbor_8", "ironharbor_1"], "lines": [  # 渔夫
        "今天潮水不错，网里全是银光闪闪的鱼！要买新鲜的？给冒险者算便宜点！",
        "清晨的鱼最肥！这会儿都快卖完了，就剩这几条倔的。",
        "等退潮了还要再下一网。海里的活计，看天吃饭！",
    ]},
    "npc_harbor_mule": {"appear": 0.85, "lines": [
        "一箱、两箱……嘿哟！铁港的货，就没有我扛不动的。冒险者，要不要来比试比试？",
        "今天卸了三条船的货，肩膀都麻了。但工钱结得爽快，值！",
        "码头的活干完，去酒馆喝一杯。日子嘛，累是累了点，踏实！",
    ]},
    "npc_harbor_trader": {"roam": ["ironharbor_1", "ironharbor_6"], "appear": 0.85},
    "npc_harbor_gate": {"roam": ["ironharbor_gate", "ironharbor_1"], "appear": 0.95},
    # ========== 晨曦城 ==========
    "npc_dawn_guard": {"roam": ["dawn_city_1", "dawn_city_gate"], "lines": [
        "王都重地，请保持肃穆。……但如果你要找圣光骑士团的驻地，顺着大教堂的尖顶走就对了。",
        "今天广场上人真多，都是来朝圣的。王都啊，永远这么热闹。",
        "站岗换班，腰板要直！禁卫军的招牌可不能塌。",
    ]},
    "npc_dawn_herald": {"appear": 0.8, "lines": [
        "圣光王国公告——近日金穗平原盗贼出没，往来商旅请结伴而行！……这位冒险者，你看起来就是该去剿匪的人！",
        "公告！公告！王都城门日落即闭，夜行需持通行令！",
        "嗓子喊哑了也要喊——传令官的活儿，就是把消息送到每个人耳朵里！",
    ]},
    "npc_dawn_stableboy": {"appear": 0.9},
    "npc_dawn_alchemist": {"appear": 0.9},
    # ========== 银溪镇 ==========
    "npc_silver_granny": {"roam": ["silver_brook_4", "silver_brook_1"], "lines": [
        "小伙子，来赶集？我这筐菜心是自家地里种的，三文钱一把，买不了吃亏！",
        "集散了我就去广场边坐坐，听年轻人讲讲外面的新鲜事。",
        "银溪的菜，浇的是溪水，甜着呢！多买点，路上吃！",
    ]},
    "npc_silver_miller": {"appear": 0.9},
    "npc_silver_inn": {"appear": 0.9},
    # ========== 枫橡村 ==========
    "npc_maple_child": {"roam": ["maple_village_1", "maple_village_4"], "appear": 0.85, "lines": [
        "我以后也要当冒险者！像你一样去很远的地方！……不过妈妈说我得先把鸡喂了。",
        "旅店的苔丝姐姐会烤蜂蜜饼！你要是闻到香味，就知道该去旅店啦！",
        "村口的枫树可老了，听爷爷说它比村子还早！",
    ]},
    "npc_maple_granny": {"roam": ["maple_village_1", "maple_village_2"], "appear": 0.9},
    # ========== 铁盾镇 ==========
    "npc_shield_scout": {"roam": ["ironshield_town_4", "ironshield_town_1"], "appear": 0.85, "lines": [
        "刚从丘陵回来，铁甲野猪又多了。镇长正发愁呢。你要是能帮忙清理，军械铺给你打折！",
        "斥候的腿，就是铁盾镇的眼睛！丘陵那边一有动静，我第一个知道。",
        "哨卡换岗了，我去广场喝口热汤。这北风，刮得人骨头疼！",
    ]},
    "npc_shield_townfolk": {"appear": 0.9},
    # ========== 月门城 ==========
    "npc_moongate_traveler": {"roam": ["moon_gate_1", "moon_gate_gate"], "appear": 0.85, "lines": [
        "跟着商队翻过月冠隘口，一路风大石头多。不过到了月门城就踏实了——这里的旅店被子暖和！",
        "明天一早就要赶路了，去隘口那边看看马喂饱了没。",
        "山那边的商路最近通了，货好走多了！",
    ]},
    "npc_moongate_inn": {"appear": 0.9},
    "npc_moongate_spice": {"roam": ["moon_gate_3", "moon_gate_1"], "appear": 0.85},
    # ========== 星歌镇 ==========
    "npc_starsong_acrobat": {"roam": ["star_song_1", "star_song_2"], "appear": 0.75, "lines": [
        "看好了！三个盘子一起转！……哎哟，又掉一个。没关系，再来！反正观众还没走光。",
        "星歌镇的夜晚最适合表演——星光就是舞台灯！",
        "今天练了个新把式，还没摔熟。你先别看，等我练好了再表演！",
    ]},
    "npc_starsong_drunkard": {"period": ["night"], "lines": [
        "酒馆的灯一亮，我就来了。这是星歌镇老酒鬼的自我修养！嗝～",
        "你、你看那颗星星，像不像一杯酒？……我看什么都像酒。",
    ]},
    "npc_starsong_florist": {"roam": ["star_song_2", "star_song_1"], "appear": 0.85},
    # ========== 寒角堡 ==========
    "npc_frost_leather": {"appear": 0.85},
    "npc_frost_drinker": {"period": ["night"], "lines": [
        "霜角堡的规矩：酒杯不能空，故事不能短！……嗝，这条其实是我编的，但大家都很配合。",
        "北地的夜里，没一杯烈酒怎么扛得住！来，敬北风！",
    ]},
    # ========== 铁砧要塞 ==========
    "npc_anvil_mule": {"roam": ["anvil_fort_gate", "anvil_fort_1"], "appear": 0.8},
    "npc_anvil_runeapp": {"appear": 0.9},
    # ========== 极光镇 ==========
    "npc_aurora_lantern": {"roam": ["aurora_town_1", "aurora_town_4"], "appear": 0.85},
    "npc_aurora_sled": {"roam": ["aurora_town_path", "aurora_town_1"], "appear": 0.8},
    # ========== 龙裔聚落 ==========
    "npc_dragonkin_child": {"roam": ["dragon_kin_1", "dragon_kin_3"], "appear": 0.85, "lines": [
        "你看我手上的鳞片！长老说等我能喷出火星，就让我去祭坛帮忙！……虽然现在还只能冒烟。",
        "旅店的烤肉可香了！我偷偷闻过一百次！",
    ]},
    "npc_dragonkin_cook": {"appear": 0.9},
    # ========== 翡翠港 ==========
    "npc_jade_sailor": {"roam": ["jade_port_1", "jade_port_dock"], "appear": 0.85, "lines": [
        "翡翠港的船，能去海上任何地方！只要你不晕船，也不怕海妖唱歌。",
        "船修好了，明天出海！这次要去群岛那边，跑一趟能赚不少。",
        "岸上的日子再好，也比不上船板上的踏实。这话水手都懂！",
    ]},
    "npc_jade_spice": {"roam": ["jade_port_2", "jade_port_1"], "appear": 0.85},
    # ========== 贝壳镇 ==========
    "npc_shell_fisher": {"roam": ["shell_town_2", "shell_town_1"], "appear": 0.85, "lines": [
        "今天的网是满的！鲷鱼、鲈鱼、还有几条不认识的……反正在海上，认识不认识都能吃。",
        "退潮的时候捡贝最划算，潮一退，滩上全是宝！",
    ]},
    "npc_shell_kelp": {"period": ["day"], "appear": 0.8},
    # ========== 无名港 ==========
    "npc_nameless_sellsword": {"roam": ["nameless_harbor_1", "nameless_harbor_3"], "appear": 0.8, "lines": [
        "这座港里的规矩你记住了：不问名字，不问来历，不问货。……当然，价钱还是要问的。",
        "今儿个码头来了艘新船，帆是黑的。在无名港，新船=新故事。",
    ]},
    "npc_nameless_deckhand": {"roam": ["nameless_harbor_3", "nameless_harbor_1"], "appear": 0.85},
    # ========== 珍珠城 ==========
    "npc_pearl_fishwife": {"roam": ["pearl_city_5", "pearl_city_1"], "appear": 0.85, "lines": [
        "刚靠岸的船，鱼还带着海水的鲜气！来两条？算你便宜点，下次还来我摊子！",
        "今天的收成好，城主府的厨房都来我这儿买鱼！",
    ]},
    "npc_pearl_crafter": {"appear": 0.9},
    # ========== 深岩隧道 ==========
    "npc_tunnel_foreman": {"roam": ["deep_tunnel_1", "deep_tunnel_2"], "appear": 0.85, "lines": [
        "三班倒，人不歇，灯不灭！这条隧道是矮人兄弟们一镐一镐凿出来的。干活！",
        "今天进度不错，又往前推进了两尺！按这速度，下个月就能到地底集市了！",
    ]},
    "npc_tunnel_trackman": {"roam": ["deep_tunnel_mouth", "deep_tunnel_1"], "appear": 0.8},
    # ========== 地底集市 ==========
    "npc_under_herbalist": {"roam": ["under_market_1", "under_market_3"], "appear": 0.85},
    "npc_under_helper": {"appear": 0.9},
    # ========== 灰烬营地 ==========
    "npc_ember_storeman": {"appear": 0.9},
    "npc_ember_scout": {"roam": ["ember_camp_4", "ember_camp_1"], "appear": 0.8},
    # ========== 风翼城 ==========
    "npc_wind_cloudmerchant": {"roam": ["wind_city_1", "wind_city_gate"], "appear": 0.85},
    "npc_wind_guard2": {"roam": ["wind_city_gate", "wind_city_1"], "appear": 0.95},
    # ========== 月冠王庭 ==========
    "npc_elf_poet2": {"roam": ["moon_court_1", "moon_court_4"], "appear": 0.8, "lines": [
        "月光是最好的听众，星河是最好的幕布。要我唱一支古老的精灵谣吗？",
        "王庭的月桂开了，香气飘满了广场。这是月冠最美的时节。",
    ]},
    "npc_elf_maid": {"appear": 0.9},
    # ========== 寒脊营地 ==========
    "npc_cold_skinner": {"roam": ["cold_ridge_1", "cold_ridge_3"], "appear": 0.85},
    "npc_cold_patrol": {"period": ["night"], "appear": 0.9, "lines": [
        "夜里的雪原，狼嚎是家常便饭。有我们巡逻队守着，营地里的炉火才能安心烧着。",
        "雪夜巡逻最要小心——白茫茫一片，容易迷方向。跟着我的火把走！",
    ]},
    # ========== 龙脊山口 ==========
    "npc_pass_caravan": {"roam": ["dragon_pass_1", "dragon_pass_gate"], "appear": 0.8, "lines": [
        "翻龙脊山口的商队，都得在这儿歇脚补粮。山风大，路也陡，但过了山口就是另一片天地！",
        "明天一早过隘口，风向正好！今天得把货捆结实了。",
    ]},
    "npc_pass_sentinel": {"roam": ["dragon_pass_gate", "dragon_pass_1"], "appear": 0.95},
    # ========== 副本入口/野外边缘（少量点缀） ==========
    "npc_oak_shepherd": {"lines": [  # 橡木平原牧羊人
        "羊群吃饱了，我也该歇会儿了。这草地上的日子，慢悠悠的，挺好。",
        "小心别踩到羊粪……咳，我说笑的。你是去平原深处打怪的？那可得当心巨型野猪！",
    ]},
    "npc_deer_forester": {"lines": [
        "白鹿之森的树，我都认识。林子里的事，你问我就对了。",
        "野狗最近又往林子深处跑了，你进林小心点。",
    ]},
    "npc_emerald_hunter": {"lines": [
        "翡翠森林的狼，精着呢。它们会绕后。打狼的时候，后背别露给它们！",
        "今天没猎到什么大家伙，就几只兔子。森林的日子，得学会知足。",
    ]},
    "npc_swamp_fisher": {"lines": [
        "迷雾沼泽的鱼，又大又肥！就是上钩之前，你得先跟蚊子搏斗。",
        "雾大的日子别往深处走，容易迷路。我在这儿钓了十年鱼，都不敢。",
    ]},
    "npc_mine_miner": {"lines": [
        "矿洞里黑，但亮堂的地方才有矿。这道理，挖矿和过日子一样。",
        "最近矿道深处总传来奇怪的动静……大概是地精又在捣鼓什么。",
    ]},
    "npc_dock_foreman": {"lines": [
        "货船到港了，伙计们，开工！手脚麻利点，船长等着起锚呢！",
        "这码头啊，每天都有船来船往。铁港城的脉搏，就在这栈桥上跳。",
    ]},
    "npc_valley_fisher": {"lines": [
        "银溪谷地的水凉，鱼也精。钓上来的，都是老江湖！",
        "谷地深处去不得，那边的大家伙会吃人——我可是亲眼见过脚印！",
    ]},
    "npc_windmill_miller": {"lines": [
        "风车一转，日子就往前走了。这原野上的风，是最好的磨坊工！",
        "麦子熟了就得赶紧收，风一吹全洒地里。忙起来饭都顾不上吃！",
    ]},
    "npc_gorge_stonecutter": {"lines": [
        "落石峡谷的石头，硬！但再硬的石头，也怕日复一日的锤子。",
        "这峡谷里的路，都是我们一锤一锤凿出来的。你走的时候，踏实的很！",
    ]},
    "npc_boar_hunter": {"lines": [
        "野猪岭的野猪，皮糙肉厚。射箭要瞄眼睛和脖子，别的地方都是白费！",
        "上回差点被野猪王追下山……咳，那是它运气好。",
    ]},
    "npc_gold_farmchief": {"lines": [
        "金穗平原的麦子，是王国最好的！就是盗贼也眼馋得很，害我们得轮流守夜。",
        "收麦子的时候，最怕天变脸。老天爷赏饭吃，我们就得赶着吃！",
    ]},
    "npc_abbess": {"lines": [
        "白石的墙，白石的心。修道院的门，为迷路的人敞开。",
        "最近总有些奇怪的声响从地窖传来……大概是老鼠吧。一定是老鼠。",
    ]},
    "npc_border_quartermaster": {"lines": [
        "军需官的账本，比城墙还厚！每一捆箭、每一袋粮，都要对上数。",
        "兽人又在前线集结了。边境堡的兵，随时准备打仗。",
    ]},
    "npc_river_ferryman": {"lines": [
        "银铃河的水，看着平静，底下暗流多。坐我的船，稳当！",
        "渡河五文钱，童叟无欺。……你说河里有歌声？那是水妖，别理它。",
    ]},
    "npc_knight_instructor": {"lines": [
        "骑士的剑，要稳；骑士的心，要正。训练场上流的汗，战场上就是命！",
        "这批见习骑士不错，就是还欠点火候。再来三百个俯卧撑！",
    ]},
    "npc_kingroad_gravekeeper": {"lines": [
        "王陵古道，生人止步。……当然，冒险者除外，你们是来找死的，拦不住。",
        "夜里别往古道走，亡者们不太喜欢被打扰。",
    ]},
}


def main():
    with open(NPCS_PATH, encoding="utf-8") as f:
        txt = f.read()
    if "v95.30 城镇 NPC 随机性" in txt:
        print("npcs.py 已包含 v95.30 随机性配置，跳过")
        return
    block = "\n\n# ===== v95.30 城镇 NPC 随机性配置（roam/appear/period/lines）=====\nfor _nid, _patch in {\n"
    for k, v in PATCHES.items():
        block += f"    {k!r}: {v!r},\n"
    block += "}.items():\n    if _nid in NPCS:\n        NPCS[_nid].update(_patch)\n"
    with open(NPCS_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(txt + block)
    import py_compile
    py_compile.compile(NPCS_PATH, doraise=True)
    print(f"npcs.py 追加随机性配置 {len(PATCHES)} 条，编译 OK")


if __name__ == "__main__":
    main()
