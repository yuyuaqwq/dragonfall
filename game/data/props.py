# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - props.py（v87.9：场景氛围元素）

场景元素（PROPS）与探索点（POI）的区别：
- PROPS 是"看得见、可直接交互"的静态元素——地图面板直接列出『交互 <名称>』，
  交互给氛围描写（纯 flavor），个别带小彩蛋（许愿/钟声等，无战斗数值收益）。
- POI 是"需要探索才可能发现"的隐藏元素——『探索』15% 概率触发。

每个子区域可挂 0-3 个 PROPS（别撒太密，保持克制）。
"""

PROPS = {
    # ---- 城镇·广场/街道 ----
    "fountain": {
        "name": "喷泉", "icon": "⛲",
        "desc": "一座白石砌成的圆形喷泉，水珠在阳光下闪着碎光，池底散落着几枚许愿的铜币。",
        "texts": [
            "你把手探进清凉的泉水里，指尖划过滑腻的青苔。水花溅起，打湿了你的靴子。",
            "你往池子里抛了一枚铜币，它旋转着沉入水底，带走了你一个没说出口的愿望。",
        ],
        "effect": None,
    },
    "statue": {
        "name": "雕像", "icon": "🗿",
        "desc": "一尊手持长剑的英雄石像，目光望向远方，底座刻着模糊的铭文。",
        "texts": [
            "你仰头打量这尊雕像——是传说中那位斩龙英雄。石像的剑锋上停着一只鸽子。",
            "铭文已被风雨磨得看不清，但你能认出几个字：『……愿勇气与你同在。』",
        ],
        "effect": None,
    },
    "notice_board": {
        "name": "告示板", "icon": "📋",
        "desc": "一块钉满羊皮纸的木板，风一吹哗哗作响，上面贴满了寻人启事和悬赏令。",
        "texts": [
            "你扫了一眼告示板：『悬赏：西岭荒原的盗贼团伙，赏金五十金币。』『寻猫：我家虎斑不见了，提供线索者酬谢三枚铜板。』",
            "告示板上有一张被撕掉一半的纸，依稀写着『……通往烬山的门……』，下半截被人扯走了。",
        ],
        "effect": None,
    },
    "clock_tower": {
        "name": "钟楼", "icon": "🕰️",
        "desc": "高耸的石砌钟楼，大钟在正午时会敲响，整座城都能听见。",
        "texts": [
            "你登上钟楼，俯瞰整座城镇的屋顶。风很大，但风景值得——远处的田野像一块块拼布。",
            "你轻轻敲了一下大钟，『嗡——』一声闷响传开，楼下有人抬头朝你喊：『喂！还没到点呢！』",
        ],
        "effect": None,
    },
    "wishing_well": {
        "name": "许愿井", "icon": "🕳️",
        "desc": "一口青石井沿的老井，井口挂着一只木桶。传说向它许愿很灵验。",
        "texts": [
            "你闭上眼许了个愿，把铜币丢进井里。咚——一声清脆的回响从深处传来。",
            "你探头往井里看，黑黢黢的什么也看不清，只闻到一股凉丝丝的水汽。",
        ],
        "effect": "wish",
    },
    "flower_bed": {
        "name": "花坛", "icon": "🌷",
        "desc": "一丛打理得整整齐齐的花坛，红的黄的紫的挤在一起，几只蜜蜂在花间打转。",
        "texts": [
            "你俯身闻了闻——嗯，是初夏的味道。花坛边立着一块小木牌：『请勿采摘，谢谢——花匠敬上』。",
            "一只蝴蝶落在你的肩头，停了两秒，又飞走了。它大概觉得你无害。",
        ],
        "effect": None,
    },
    "benches": {
        "name": "长椅", "icon": "🪑",
        "desc": "一张被坐得发亮的木长椅，椅背上刻着密密麻麻的名字和日期。",
        "texts": [
            "你在长椅上坐了一会儿。旁边一位晒太阳的老者朝你点了点头，又合上了眼。",
            "你注意到椅背上一行小字：『S·K 在此等候了三年，愿你平安归来。』",
        ],
        "effect": None,
    },
    "windmill": {
        "name": "风车", "icon": "🌀",
        "desc": "一座灰墙红顶的风车，巨大的叶片慢悠悠地转着，发出吱呀吱呀的声响。",
        "texts": [
            "你走近风车，磨坊主正往袋子里装面粉，抬头冲你咧嘴一笑：『要买点新磨的黑麦面吗？』",
            "风车的叶片转得正欢，空气里飘着一股新鲜的麦香。",
        ],
        "effect": None,
    },
    "camp_flag": {
        "name": "营地旗帜", "icon": "🚩",
        "desc": "一面绣着冒险者行会徽记的旗帜，在风中猎猎作响。",
        "texts": [
            "你抬头看了一眼旗帜——行会的剑盾徽记，边角已经磨得起了毛边。那是无数冒险者的骄傲。",
            "旗帜的影子在地面上摇曳，像一只无声的鼓舞的手。",
        ],
        "effect": None,
    },
    "market_stall": {
        "name": "集市摊位", "icon": "🏪",
        "desc": "一个搭着蓝白条纹布棚的摊位，摆着干果、香料和花花绿绿的布匹。",
        "texts": [
            "摊主热情地招呼你：『瞧瞧这藏红花，铁港城来的，泡茶一绝！』你摆摆手，他也不恼，接着招呼下一位。",
            "你在摊位前站了一会儿，闻着香料的味道，听摊主跟隔壁摊主闲聊着今早的行情。",
        ],
        "effect": None,
    },

    # ---- 港口/海边 ----
    "anchor": {
        "name": "老锚", "icon": "⚓",
        "desc": "一只锈迹斑斑的船锚，半埋在码头边，铁链上缠着海藻。",
        "texts": [
            "你摸了摸老锚的锈迹。旁边一位老水手说：『它陪了我们三十年，退休了，就搁这儿了。』",
            "海风咸咸的，吹过锚链，发出低低的呜咽声。",
        ],
        "effect": None,
    },
    "lighthouse": {
        "name": "灯塔", "icon": "🗼",
        "desc": "一座红白相间的灯塔，塔顶的灯在夜色里会亮起，为远航的船指引归途。",
        "texts": [
            "你登上灯塔，守塔人正在给灯芯添油。他说：『灯一亮，心里的石头就落地了。』",
            "从塔顶望去，海面铺满碎金似的阳光，远处有船影慢慢靠近。",
        ],
        "effect": None,
    },
    "fishing_boats": {
        "name": "渔船", "icon": "⛵",
        "desc": "几艘漆成蓝色的小渔船并排泊在码头，随着波浪轻轻摇晃。",
        "texts": [
            "渔夫们正在整理渔网，看见你，问：『要出海看看吗？』——当然，得先有船票。",
            "你跳上甲板晃了两下，被船老大笑着赶下来：『别闹，那是要出海的船！』",
        ],
        "effect": None,
    },

    # ---- 野外 ----
    "boundary_stone": {
        "name": "界碑", "icon": "🪨",
        "desc": "一块半人高的青石界碑，棱角被风雨磨圆了，上面刻着地名和一个箭头。",
        "texts": [
            "你蹲下擦了擦碑上的苔藓：『→ 橡木镇，三里。』方向没错，继续走吧。",
            "界碑背面刻着一行小字：『越过此碑者，福祸自担。』",
        ],
        "effect": None,
    },
    "old_tree": {
        "name": "古树", "icon": "🌳",
        "desc": "一棵粗得三人都环抱不过来的老橡树，树冠如盖，树皮上布满深深浅浅的沟壑。",
        "texts": [
            "你把手掌贴在粗糙的树皮上。这棵树见过一百年的日出，而它只是沉默地继续生长。",
            "树洞里积着几枚松果和一片羽毛。有人曾在这里歇脚。",
        ],
        "effect": None,
    },
    "rock_formation": {
        "name": "奇岩", "icon": "🪨",
        "desc": "几块造型古怪的岩石叠在一起，像一只蹲伏的巨兽，风从石缝间穿过。",
        "texts": [
            "你绕着奇岩转了一圈——从某个角度看，它真的像一头沉睡的石龙。",
            "石缝里钻出一只蜥蜴，跟你对视了一秒，然后溜走了。",
        ],
        "effect": None,
    },
    "wild_flowers": {
        "name": "野花丛", "icon": "🌼",
        "desc": "一片不知名的野花，紫的白的黄的开得正热闹，蝴蝶和蜜蜂在花间忙碌。",
        "texts": [
            "你采了一朵小花别在领口。空气里都是草木的清香，心情没来由地好了起来。",
            "花丛深处传来虫鸣，风一吹，整片花海起伏如波浪。",
        ],
        "effect": None,
    },
    "ruined_wagon": {
        "name": "废弃马车", "icon": "🛒",
        "desc": "一辆轮子都散了架的旧马车，倒在路边，车斗里长满了野草。",
        "texts": [
            "你翻了翻车斗——除了几根腐朽的木条，什么也没留下。也许是几年前的一场事故。",
            "车辕上挂着一只生锈的马铃，你轻轻拨了一下，『叮』一声，清脆得像从很远的地方传来。",
        ],
        "effect": None,
    },
    "campfire_remains": {
        "name": "篝火余烬", "icon": "🔥",
        "desc": "一堆已经冷透的篝火灰烬，周围散落着几根没烧完的柴火。",
        "texts": [
            "你蹲下来试了试灰烬的温度——凉的。有人在这里过夜，然后走了。",
            "灰堆里埋着一块烤焦的土豆，你扒出来看了看，摇了摇头又埋回去了。",
        ],
        "effect": None,
    },
    "mountain_spring": {
        "name": "山泉", "icon": "💧",
        "desc": "一泓从石缝间涌出的清泉，汇成小小的水潭，水声潺潺。",
        "texts": [
            "你掬了一捧泉水喝下——清凉甘甜，一路的疲惫仿佛都顺着喉咙滑走了。",
            "泉边有一块平整的石头，上面浅浅地刻着一个旅人留下的名字和日期。",
        ],
        "effect": "refresh",
    },
    "stone_altar_ruin": {
        "name": "石祭台残迹", "icon": "🏛️",
        "desc": "一座半塌的石台，台面上刻着褪色的纹路，像是某个古老仪式的遗迹。",
        "texts": [
            "你伸手抚过台上的纹路——凹槽里还残留着深褐色的痕迹。这里曾经……发生过什么。",
            "祭台四周的石缝里，长出了不知名的野花。时间把一切伤痛都磨成了风景。",
        ],
        "effect": None,
    },
    "highland_rock": {
        "name": "观景岩", "icon": "⛰️",
        "desc": "一块探出山崖的大岩石，视野开阔，能把整片大地尽收眼底。",
        "texts": [
            "你站在观景岩上，风鼓起你的衣摆。远处山峦叠嶂，一条银色的河流蜿蜒而过。",
            "你扶着岩石边缘往下看——云雾在脚下翻涌，像一片白色的海。",
        ],
        "effect": None,
    },
    "birch_grove": {
        "name": "白桦林", "icon": "🌲",
        "desc": "一片笔直的白桦树，银白的树干在阳光下泛着柔和的光，树影斑驳。",
        "texts": [
            "你走进白桦林，脚下踩着厚厚的落叶，沙沙作响。阳光从叶隙间漏下来，像碎金洒了一地。",
            "一只松鼠从树干上探出头，盯着你看了两秒，然后抱着一颗松果跑开了。",
        ],
        "effect": None,
    },

    # ---- 地下/矮人 ----
    "rune_pillar": {
        "name": "符文柱", "icon": "🗄️",
        "desc": "一根刻满矮人符文的石柱，符文的凹槽里隐隐泛着微光。",
        "texts": [
            "你凑近看符文——虽然认不全，但能感觉到柱子深处传来的、沉稳的脉动，像大地的心跳。",
            "你轻轻敲了敲柱子，『咚』——声音浑厚而悠远，在隧道里传出去很远。",
        ],
        "effect": None,
    },
    "minecart": {
        "name": "矿车", "icon": "🛺",
        "desc": "一辆停在轨道上的矿车，车斗里还残留着几块矿石碎屑。",
        "texts": [
            "你推了推矿车，它吱呀吱呀地滑出去一小段，又停住了。轨道的尽头消失在黑暗里。",
            "矿车里捡到一块亮晶晶的石头——不是宝石，但确实好看，你顺手揣进了兜里。",
        ],
        "effect": None,
    },
    "deep_well": {
        "name": "幽深竖井", "icon": "🕳️",
        "desc": "一口深不见底的竖井，井口围着一圈石栏，往下看去只有一片浓稠的黑暗。",
        "texts": [
            "你趴在石栏边往下看——什么都看不见，但隐约能听到极深处传来的滴水声，像是另一个世界的心跳。",
            "你丢了一颗小石子下去，等了很久很久，才传来一声几乎听不见的回音。",
        ],
        "effect": None,
    },

    # ---- 北境/冰雪 ----
    "ice_sculpture": {
        "name": "冰雕", "icon": "🧊",
        "desc": "一座晶莹剔透的冰雕，雕刻着一头昂首的巨熊，在阳光下折射出七彩的光。",
        "texts": [
            "你绕着冰雕走了一圈——每一根鬃毛都刻得清清楚楚。雕刻它的人，一定很爱这片雪原。",
            "你伸手碰了碰冰熊的鼻子，凉丝丝的。它看起来威严，摸起来却有点滑稽。",
        ],
        "effect": None,
    },
    "aurora_gazing": {
        "name": "极光", "icon": "🌌",
        "desc": "夜空中飘荡着翡翠色的光带，像活着的绸缎，缓缓流动、明灭。",
        "texts": [
            "你仰头望着极光，一时间忘了呼吸。光带在天幕上变幻着形状，仿佛在诉说什么古老的故事。",
            "一位当地老人说：『极光啊，是先民在跳舞。他们还在守护着这片大地。』",
        ],
        "effect": None,
    },

    # ---- 精灵/森林 ----
    "moon_pool": {
        "name": "月池", "icon": "🌙",
        "desc": "一汪藏在林间的清澈水池，月光落在水面上，像撒了一层碎银。",
        "texts": [
            "你在月池边坐下，水面倒映着月亮和你自己。安静得能听见露珠滴落的声音。",
            "传说在月池边许下的愿望，会被月光带去精灵王庭。你试了试——反正不亏。",
        ],
        "effect": None,
    },
    "elf_carving": {
        "name": "精灵刻痕", "icon": "🌿",
        "desc": "树干上刻着一圈精致的精灵纹样，线条流畅得像藤蔓，又像流动的水。",
        "texts": [
            "你仔细辨认着刻痕——这大概是某种祝福的符文。树皮在纹样周围格外光滑，像是常有人来抚摸。",
            "你在刻痕下放了一枚树叶作为回礼。也许精灵会看见。",
        ],
        "effect": None,
    },
}

# 子区域 → PROPS 分配（key = "地图id:子区域id"，value = prop id 列表）
# 挂载克制：城镇广场 2-3 个、野外要点 1-2 个；不撒太密
SUBAREA_PROPS = {
    # ==== 绿野·橡木镇 ====
    "oak_town:oak_town_1": ["fountain", "notice_board", "benches"],   # 冒险者广场
    "oak_town:oak_town_2": ["statue"],                                 # 镇长办公处前
    "oak_town:oak_town_4": ["market_stall", "camp_flag"],             # 集市
    # ==== 枫橡村 ====
    "maple_village:maple_village_1": ["old_tree", "flower_bed"],       # 村口
    # ==== 白鹿城 ====
    "white_deer:white_deer_1": ["fountain", "statue", "clock_tower"],  # 白鹿广场
    "white_deer:white_deer_3": ["market_stall"],                       # 鹿角铁匠铺一带
    # ==== 铁港城 ====
    "ironharbor:ironharbor_1": ["anchor", "lighthouse", "fishing_boats"],  # 港口广场
    "ironharbor:ironharbor_5": ["fishing_boats"],                      # 东码头
    # ==== 晨曦城 ====
    "dawn_city:dawn_city_1": ["fountain", "statue", "clock_tower"],    # 王都广场
    "dawn_city:dawn_city_3": ["flower_bed"],                           # 圣光大教堂
    # ==== 铁盾镇 ====
    "ironshield_town:ironshield_town_1": ["windmill", "market_stall"], # 铁盾广场
    # ==== 月门城 ====
    "moon_gate:moon_gate_1": ["fountain", "clock_tower"],              # 月门广场
    # ==== 星歌镇 ====
    "star_song:star_song_1": ["market_stall", "benches"],              # 星歌广场
    # ==== 月庭（精灵）====
    "moon_court:moon_court_1": ["moon_pool", "elf_carving"],           # 王庭广场
    # ==== 翡翠港 ====
    "jade_port:jade_port_1": ["anchor", "fishing_boats"],              # 翡翠码头
    # ==== 贝壳镇 ====
    "shell_town:shell_town_1": ["fishing_boats", "anchor"],            # 贝壳沙滩
    # ==== 无名港 ====
    "nameless_harbor:nameless_harbor_1": ["lighthouse", "anchor"],     # 无名港
    # ==== 珍珠城 ====
    "pearl_city:pearl_city_1": ["fishing_boats", "lighthouse"],        # 珍珠广场
    # ==== 寒角堡 ====
    "frost_horn:frost_horn_1": ["ice_sculpture", "campfire_remains"],  # 寒角堡广场
    # ==== 极光镇 ====
    "aurora_town:aurora_town_1": ["aurora_gazing", "benches"],         # 极光广场
    # ==== 铁砧堡（矮人）====
    "anvil_fort:anvil_fort_1": ["rune_pillar", "minecart"],            # 铁砧大厅
    # ==== 深隧 ====
    "deep_tunnel:deep_tunnel_1": ["rune_pillar", "minecart"],          # 深隧入口
    "deep_tunnel:deep_tunnel_2": ["deep_well"],                        # 中段
    # ==== 地下集市 ====
    "under_market:under_market_1": ["market_stall", "rune_pillar"],    # 集市入口
    # ==== 灰烬营地 ====
    "ember_camp:ember_camp_1": ["campfire_remains", "camp_flag"],      # 营地口
    # ==== 风之城 ====
    "wind_city:wind_city_1": ["highland_rock"],                        # 风之城广场
    # ==== 银溪村 ====
    "silver_brook:silver_brook_1": ["fountain", "old_tree"],           # 银溪广场
    # ==== 龙脊隘口 ====
    "dragon_pass:dragon_pass_1": ["boundary_stone", "highland_rock"],  # 隘口
    # ==== 野外 ====
    "oak_meadow:oak_meadow_1": ["boundary_stone", "wild_flowers"],     # 橡木草地
    "oak_forest:oak_forest_2": ["old_tree", "campfire_remains"],       # 橡木林
    "emerald_forest:emerald_forest_2": ["old_tree", "wild_flowers"],   # 翡翠森林
    "misty_swamp:misty_swamp_1": ["ruined_wagon"],                     # 迷雾沼泽
    "gold_plain:gold_plain_1": ["wild_flowers", "boundary_stone"],     # 金穗平原
    "silver_river:silver_river_1": ["mountain_spring", "birch_grove"], # 银溪河
    "old_battlefield:old_battlefield_1": ["stone_altar_ruin", "ruined_wagon"],  # 古战场
    "ancient_tree:ancient_tree_1": ["old_tree"],                       # 古树
    "frost_field:frost_field_1": ["ice_sculpture", "boundary_stone"],  # 霜原
    "cinder_mountain:cinder_mountain_2": ["stone_altar_ruin"],         # 烬山
    "black_forest:black_forest_2": ["old_tree", "campfire_remains"],   # 黑森林
    "dragon_ridge:dragon_ridge_1": ["highland_rock", "boundary_stone"],  # 龙脊
    "coral_reef:coral_reef_1": ["fishing_boats"],                      # 珊瑚礁
    "storm_sea:storm_sea_1": ["anchor"],                               # 风暴海
    "molten_abyss:molten_abyss_1": ["deep_well"],                      # 熔火深渊
    # ==== v87.7 城镇间新图 ====
    "silver_wind_road:silver_wind_road_1": ["boundary_stone", "wild_flowers"],  # 银风道口
    "silver_wind_road:silver_wind_road_2": ["campfire_remains", "old_tree"],    # 银风驿站
    "west_ridge_wilds:west_ridge_wilds_1": ["wild_flowers", "boundary_stone"],  # 西岭口
    "west_ridge_wilds:west_ridge_wilds_2": ["stone_altar_ruin"],               # 荒原深处
    "dusk_ridge_road:dusk_ridge_road_1": ["highland_rock"],                    # 暮岭
    "mist_tide_passage:mist_tide_passage_1": ["lighthouse"],                   # 雾潮
    "black_tide_strait:black_tide_strait_1": ["anchor"],                       # 黑潮
    "dwarf_long_gallery:dwarf_long_gallery_1": ["rune_pillar", "minecart"],    # 矮人长廊
    "cold_spine_snow_trail:cold_spine_snow_trail_1": ["ice_sculpture"],        # 寒脊雪道
    "dragon_ridge_old_road:dragon_ridge_old_road_1": ["boundary_stone", "stone_altar_ruin"],  # 龙脊古道
    "dragonborn_valley_trail:dragonborn_valley_trail_1": ["highland_rock"],    # 龙裔谷道
    "sky_ladder_path:sky_ladder_path_1": ["highland_rock", "mountain_spring"], # 天梯云径
}
