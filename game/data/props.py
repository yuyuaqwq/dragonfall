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

    # ======================
    # v87.10 场所专属元素（阶段一：核心城镇）
    # ======================
    "forge_table": {
        "name": "锻造台", "icon": "⚒️",
        "desc": "一张厚实的橡木工作台，台面上摆满了锤子、钳子和淬火槽，木面被敲得坑坑洼洼。",
        "texts": [
            "你拿起台上的铁钳掂了掂——沉甸甸的，铁匠的伙伴果然跟冒险者的剑一样值得信赖。",
            "锻造台的一角刻着一行小字：『每一件好兵器，都是被耐心喂大的。』",
        ],
        "effect": None,
    },
    "anvil": {
        "name": "铁砧", "icon": "🔨",
        "desc": "一座结实的铁砧，砧面磨得发亮，映着炉火的光。",
        "texts": [
            "你伸手敲了敲铁砧，『叮——』一声清脆的金属鸣响在铺子里回荡。",
            "铁砧边角有一道深痕，不知道是哪个性急的铁匠敲出来的。",
        ],
        "effect": None,
    },
    "bellows": {
        "name": "风箱", "icon": "🌬️",
        "desc": "一只老式的皮制风箱，拉着它能把炉火烧得呼呼作响。",
        "texts": [
            "你拉了两下风箱，炉膛里的火苗腾地蹿高，映得整间铺子一片橘红。",
            "风箱的皮面缝了又缝，补丁摞补丁——看得出它被用了很多年。",
        ],
        "effect": None,
    },
    "bar_counter": {
        "name": "吧台", "icon": "🍺",
        "desc": "一条擦得锃亮的木质吧台，台面上放着几只倒扣的酒杯。",
        "texts": [
            "你倚着吧台坐了一会儿，听酒保跟常客闲扯今天镇上的新鲜事。",
            "吧台台面上有一道浅浅的划痕，不知道是哪个醉汉的杰作。",
        ],
        "effect": None,
    },
    "ale_barrel": {
        "name": "酒桶", "icon": "🛢️",
        "desc": "几只码得整整齐齐的橡木酒桶，桶上标着年份和酒名。",
        "texts": [
            "你拍了拍酒桶，里面传来沉甸甸的回响——装得满满当当。",
            "酒桶上贴着标签：『橡木镇特酿·三年陈』，闻着就有一股麦香。",
        ],
        "effect": None,
    },
    "fireplace": {
        "name": "壁炉", "icon": "🔥",
        "desc": "一座石砌壁炉，炉火正旺，木柴噼啪作响，暖意融融。",
        "texts": [
            "你凑到壁炉边烤了烤手，暖意顺着指尖爬满全身。这一刻，旅途的疲惫都被融化了。",
            "壁炉上方的架子上摆着几件小摆件，都是旅人留下的纪念品。",
        ],
        "effect": None,
    },
    "medicine_cabinet": {
        "name": "药柜", "icon": "💊",
        "desc": "一面贴墙的木药柜，一格一格的小抽屉上都贴着药材名。",
        "texts": [
            "你拉开一格抽屉，里面是晒干的草药，药香扑鼻。你赶紧合上——偷看药柜可不礼貌。",
            "药柜最上层摆着一只白瓷瓶，标签写着『内服』，笔迹端端正正。",
        ],
        "effect": None,
    },
    "mortar_pestle": {
        "name": "捣药臼", "icon": "🌿",
        "desc": "一只石臼配着铜杵，臼壁上还沾着没洗净的绿色药渣。",
        "texts": [
            "你拿起铜杵轻轻捣了两下，一股草药味在空气中散开。",
            "臼里的药渣还微微湿润，看来主人不久前才用过它。",
        ],
        "effect": None,
    },
    "candle_stand": {
        "name": "烛台", "icon": "🕯️",
        "desc": "几盏银烛台排成一列，烛火轻轻摇曳，在墙上投下柔和的光影。",
        "texts": [
            "你凑近一盏烛台，火苗在你眼底跳动。这一刻，连呼吸都安静了下来。",
            "烛油沿着烛台缓缓滑落，凝成细长的泪痕——它们已经燃了很久。",
        ],
        "effect": None,
    },
    "holy_icon": {
        "name": "圣像", "icon": "⛪",
        "desc": "一尊低眉垂目的圣像，双手合拢，衣袍的褶皱被刻得细腻柔和。",
        "texts": [
            "你站在圣像前，不知为何，心里那些毛躁的念头悄悄平复了下来。",
            "圣像的基座上刻着一行小字：『愿光指引迷途者。』",
        ],
        "effect": None,
    },
    "throne": {
        "name": "王座", "icon": "👑",
        "desc": "一把高背雕花的座椅，扶手镶着金线，坐垫是深红的绒布。",
        "texts": [
            "你当然不敢坐上去——但光是站在它面前，就能感觉到那种沉甸甸的分量。",
            "王座扶手上有一道细微的磨痕，是无数只紧张的手留下的。",
        ],
        "effect": None,
    },
    "tapestry": {
        "name": "挂毯", "icon": "🧶",
        "desc": "一幅巨大的织锦挂毯，描绘着古老的战役，金线在火光下微微发亮。",
        "texts": [
            "你仰头细看挂毯——织着一位骑士持剑而立，身后是燃烧的城池。故事感扑面而来。",
            "挂毯边缘的线头有些松散，但这件作品依然透着岁月的华贵。",
        ],
        "effect": None,
    },
    "armor_stand": {
        "name": "甲胄架", "icon": "🛡️",
        "desc": "一具立在墙边的全身甲，头盔的面甲合拢着，甲面上留着碰撞的凹痕。",
        "texts": [
            "你伸手敲了敲甲胄，金属发出一声闷响——是货真价实的铁甲，不是摆样子。",
            "甲胄的胸甲上刻着一枚徽记，可惜磨损得看不清了。它一定见过真正的战场。",
        ],
        "effect": None,
    },
    "quest_board": {
        "name": "任务板", "icon": "📜",
        "desc": "行会墙上钉着一块大木板，上面贴满了委托单，从『帮我找猫』到『讨伐山贼』什么都有。",
        "texts": [
            "你扫了一眼任务板——大部分委托对你来说太简单了，但最底下一张『深入烬山』的悬赏让你多看了两眼。",
            "任务板的一角贴着一张快褪色的委托：『寻找失踪的商队——赏金面议』。",
        ],
        "effect": None,
    },
    "trophy_rack": {
        "name": "奖杯架", "icon": "🏆",
        "desc": "一座展示柜，摆着各种战利品：褪色的龙牙、半面魔物头骨、发黑的金币。",
        "texts": [
            "你凑近看了看奖杯架——每一件战利品背后，都有一段拿命换来的故事。",
            "展示柜最高处放着一只残缺的号角，标签写着：『第一次讨伐纪念』。",
        ],
        "effect": None,
    },
    "deer_head": {
        "name": "鹿头装饰", "icon": "🦌",
        "desc": "墙上挂着一只雄鹿的头骨，鹿角又大又漂亮，显然是猎人的得意战利品。",
        "texts": [
            "你抬头看那只鹿头——鹿角的分叉数得出来，主人一定对那次狩猎津津乐道。",
            "鹿头的角上系着一根褪色的红绳，像是某种古老的祝福。",
        ],
        "effect": None,
    },
    "hunting_bow": {
        "name": "猎弓", "icon": "🏹",
        "desc": "一张保养得极好的木弓，弓弦绷得很紧，旁边挂着箭袋。",
        "texts": [
            "你试着拉了拉弓弦——纹丝不动。这弓的力道，没有几年臂力根本拉不开。",
            "弓身上刻着一道小小的刻痕，数了数，大概代表着打到的猎物数。",
        ],
        "effect": None,
    },
    "animal_hide": {
        "name": "兽皮", "icon": "🐻",
        "desc": "一张铺在地上的兽皮，毛色油亮，边角被磨得起了毛边。",
        "texts": [
            "你踩上去试了试——又软又暖，确实比睡草堆舒服多了。",
            "兽皮的腹部有一道旧伤疤，那是它生前留下的最后一道痕迹。",
        ],
        "effect": None,
    },
    "weapon_rack": {
        "name": "武器架", "icon": "🗡️",
        "desc": "一排插着各式兵器的木架：长剑、战斧、长矛，擦得干干净净。",
        "texts": [
            "你拔出一把长剑看了看刃口——虽然算不上神兵，但保养得一丝不苟。",
            "武器架的底层放着一把训练用木剑，剑身被磕得坑坑洼洼，看得出用得很勤。",
        ],
        "effect": None,
    },
    "cauldron": {
        "name": "坩埚", "icon": "🧪",
        "desc": "一只架在炉火上的铜坩埚，里面的液体咕嘟咕嘟冒着泡，散发出奇特的气味。",
        "texts": [
            "你探头看了一眼坩埚——紫色的液体翻滚着，冒出的泡泡炸开时发出轻微的嘶声。还是别碰为好。",
            "坩埚边的台子上摆着一排小瓶，装着各种颜色的粉末，标签都朝里，看不清字。",
        ],
        "effect": None,
    },
    "fishing_net": {
        "name": "渔网", "icon": "🎣",
        "desc": "一张挂在杆上晾晒的渔网，网眼细密，水珠在阳光下闪闪发亮。",
        "texts": [
            "你摸了摸渔网——网线结实而湿润，还带着海水的咸味。",
            "渔网上卡着一片银色的鳞片，在光下闪着光。",
        ],
        "effect": None,
    },
    "fish_drying_rack": {
        "name": "晒鱼架", "icon": "🐟",
        "desc": "一排木架上晾着剖开的鱼，鱼身抹着盐，海风一吹微微晃动。",
        "texts": [
            "咸鱼的味道扑面而来——虽然有点冲，但你知道，这是海边人家过冬的底气。",
            "晒鱼架上的鱼大小不一，看来今天渔获不错。",
        ],
        "effect": None,
    },
    "oar": {
        "name": "船桨", "icon": "🛶",
        "desc": "几支靠在墙边的木船桨，桨面被水磨得光滑，泛着温润的光泽。",
        "texts": [
            "你拿起一支船桨掂了掂——很趁手。也许有一天你会划着它出海。",
            "船桨上刻着一个歪歪扭扭的名字，大概是某个小水手的杰作。",
        ],
        "effect": None,
    },
    "miner_lamp": {
        "name": "矿灯", "icon": "💡",
        "desc": "一盏铁皮矿灯，灯罩被熏得发黑，但火苗依然亮得稳稳当当。",
        "texts": [
            "你提起矿灯晃了晃——火苗纹丝不动，是好灯。矿工们就靠它在黑暗里挣饭吃。",
            "矿灯的把手上缠着粗糙的布条，是常年握持留下的痕迹。",
        ],
        "effect": None,
    },
    "goods_shelf": {
        "name": "货架", "icon": "📦",
        "desc": "一排齐墙的货架，摆着布匹、香料、铁器和各种杂货，码得整整齐齐。",
        "texts": [
            "你顺着货架看过去——从针头线脑到上好的精铁锭，一应俱全。商行的底气都在这排架子上。",
            "货架最上层放着一只落灰的木箱，标签写着『特殊订货，勿动』。",
        ],
        "effect": None,
    },
}

# 子区域 → PROPS 分配（key = "地图id:子区域id"，value = prop id 列表）
# 挂载克制：城镇广场 2-3 个、野外要点 1-2 个；不撒太密
SUBAREA_PROPS = {
    "oak_town:oak_town_1": ['fountain', 'notice_board', 'benches'],
    "oak_town:oak_town_2": ['statue', 'tapestry', 'candle_stand'],
    "oak_town:oak_town_4": ['bar_counter', 'ale_barrel', 'fireplace'],
    "maple_village:maple_village_1": ['old_tree', 'flower_bed'],
    "white_deer:white_deer_1": ['fountain', 'statue', 'clock_tower'],
    "white_deer:white_deer_3": ['forge_table', 'anvil', 'bellows'],
    "ironharbor:ironharbor_1": ['anchor', 'lighthouse', 'fishing_boats'],
    "ironharbor:ironharbor_5": ['fishing_boats', 'bar_counter', 'ale_barrel', 'fireplace'],
    "dawn_city:dawn_city_1": ['fountain', 'statue', 'clock_tower'],
    "dawn_city:dawn_city_3": ['flower_bed', 'candle_stand', 'holy_icon'],
    "ironshield_town:ironshield_town_1": ['windmill', 'market_stall'],
    "moon_gate:moon_gate_1": ['fountain', 'clock_tower'],
    "star_song:star_song_1": ['market_stall', 'benches'],
    "moon_court:moon_court_1": ['moon_pool', 'elf_carving'],
    "jade_port:jade_port_1": ['anchor', 'fishing_boats'],
    "shell_town:shell_town_1": ['fishing_boats', 'anchor'],
    "nameless_harbor:nameless_harbor_1": ['lighthouse', 'anchor'],
    "pearl_city:pearl_city_1": ['fishing_boats', 'lighthouse'],
    "frost_horn:frost_horn_1": ['ice_sculpture', 'campfire_remains'],
    "aurora_town:aurora_town_1": ['aurora_gazing', 'benches'],
    "anvil_fort:anvil_fort_1": ['rune_pillar', 'minecart'],
    "deep_tunnel:deep_tunnel_1": ['rune_pillar', 'minecart'],
    "deep_tunnel:deep_tunnel_2": ['deep_well'],
    "under_market:under_market_1": ['market_stall', 'rune_pillar'],
    "ember_camp:ember_camp_1": ['campfire_remains', 'camp_flag'],
    "wind_city:wind_city_1": ['highland_rock'],
    "silver_brook:silver_brook_1": ['fountain', 'old_tree'],
    "dragon_pass:dragon_pass_1": ['boundary_stone', 'highland_rock'],
    "oak_meadow:oak_meadow_1": ['boundary_stone', 'wild_flowers'],
    "oak_forest:oak_forest_2": ['old_tree', 'campfire_remains'],
    "emerald_forest:emerald_forest_2": ['old_tree', 'wild_flowers'],
    "misty_swamp:misty_swamp_1": ['ruined_wagon'],
    "gold_plain:gold_plain_1": ['wild_flowers', 'boundary_stone'],
    "silver_river:silver_river_1": ['mountain_spring', 'birch_grove'],
    "old_battlefield:old_battlefield_1": ['stone_altar_ruin', 'ruined_wagon'],
    "ancient_tree:ancient_tree_1": ['old_tree'],
    "frost_field:frost_field_1": ['ice_sculpture', 'boundary_stone'],
    "cinder_mountain:cinder_mountain_2": ['stone_altar_ruin'],
    "black_forest:black_forest_2": ['old_tree', 'campfire_remains'],
    "dragon_ridge:dragon_ridge_1": ['highland_rock', 'boundary_stone'],
    "coral_reef:coral_reef_1": ['fishing_boats'],
    "storm_sea:storm_sea_1": ['anchor'],
    "molten_abyss:molten_abyss_1": ['deep_well'],
    "silver_wind_road:silver_wind_road_1": ['boundary_stone', 'wild_flowers'],
    "silver_wind_road:silver_wind_road_2": ['campfire_remains', 'old_tree'],
    "west_ridge_wilds:west_ridge_wilds_1": ['wild_flowers', 'boundary_stone'],
    "west_ridge_wilds:west_ridge_wilds_2": ['stone_altar_ruin'],
    "dusk_ridge_road:dusk_ridge_road_1": ['highland_rock'],
    "mist_tide_passage:mist_tide_passage_1": ['lighthouse'],
    "black_tide_strait:black_tide_strait_1": ['anchor'],
    "dwarf_long_gallery:dwarf_long_gallery_1": ['rune_pillar', 'minecart'],
    "cold_spine_snow_trail:cold_spine_snow_trail_1": ['ice_sculpture'],
    "dragon_ridge_old_road:dragon_ridge_old_road_1": ['boundary_stone', 'stone_altar_ruin'],
    "dragonborn_valley_trail:dragonborn_valley_trail_1": ['highland_rock'],
    "sky_ladder_path:sky_ladder_path_1": ['highland_rock', 'mountain_spring'],
    "oak_town:oak_town_3": ['forge_table', 'anvil', 'bellows'],
    "oak_town:oak_town_5": ['medicine_cabinet', 'mortar_pestle'],
    "white_deer:white_deer_2": ['throne', 'tapestry'],
    "white_deer:white_deer_4": ['candle_stand', 'holy_icon'],
    "white_deer:white_deer_5": ['bar_counter', 'ale_barrel', 'fireplace'],
    "white_deer:white_deer_6": ['medicine_cabinet', 'mortar_pestle'],
    "white_deer:white_deer_7": ['fireplace', 'goods_shelf'],
    "white_deer:white_deer_8": ['forge_table', 'anvil'],
    "ironharbor:ironharbor_2": ['throne', 'tapestry'],
    "ironharbor:ironharbor_3": ['quest_board', 'trophy_rack', 'weapon_rack'],
    "ironharbor:ironharbor_4": ['trophy_rack', 'goods_shelf'],
    "ironharbor:ironharbor_6": ['goods_shelf'],
    "ironharbor:ironharbor_7": ['miner_lamp', 'forge_table'],
    "ironharbor:ironharbor_8": ['fishing_net', 'fish_drying_rack', 'oar'],
    "ironharbor:ironharbor_9": ['forge_table', 'anvil', 'bellows'],
    "dawn_city:dawn_city_2": ['throne', 'tapestry', 'armor_stand'],
    "dawn_city:dawn_city_4": ['armor_stand', 'weapon_rack'],
    "dawn_city:dawn_city_5": ['cauldron', 'mortar_pestle'],
    "ironshield_town:ironshield_town_2": ['tapestry'],
    "ironshield_town:ironshield_town_3": ['weapon_rack', 'armor_stand', 'forge_table'],
    "ironshield_town:ironshield_town_4": ['quest_board', 'weapon_rack'],
    "maple_village:maple_village_2": ['fireplace', 'candle_stand'],
    "maple_village:maple_village_3": ['deer_head', 'hunting_bow', 'animal_hide'],
    "maple_village:maple_village_4": ['bar_counter', 'fireplace', 'ale_barrel'],
}
