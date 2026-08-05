# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - dialogues.py

NPC 多轮对话树（v65）。

设计（可扩展）：
- DIALOGUES[npc_id] = {"start": 起始节点ID, "nodes": {节点ID: 节点}}
- 节点 = {"text": 台词, "options": [选项...]}
- 选项 = {"text": 选项文本, "next": 目标节点ID 或 "__end__",
          "need": 可选条件 dict, "action": 可选动作 dict}
- 条件 need（全部满足才显示该选项）：
    {"quest_done": "q1"}        主线 q1 已完成
    {"quest_active": "q1"}      主线 q1 进行中（active/ready）
    {"quest_pending": "q1"}     主线 q1 待接取
    {"main_done": True}         全部主线完成
    {"level": 10}               等级 ≥ 10
    {"flag": "xxx"}             该 NPC 对话 flag 已设置
- 动作 action（选中后执行，返回通知行）：
    {"set_flag": "xxx"}         设置对话 flag（持久，彩蛋解锁用）
    {"give_gold": 50}           给金币
    {"give_exp": 100}           给经验
    {"give_item": {"key": "狼皮", "count": 2}}   给物品（key 支持中文名/ID）
    {"open_shop": True}         提示打开商店
"""
DIALOGUES = {
    # ==================== 维拉镇 ====================
    "npc_mayor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "年轻人，你来得正是时候。最近镇子外围的野狗越来越猖狂，商队都不敢进城了。",
                "options": [
                    {"text": "野狗是怎么回事？", "next": "dogs"},
                    {"text": "镇长，镇子最近还好吗？", "next": "town"},
                    {"text": "我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q1"}},
                    {"text": "任务完成了！", "next": "quest_done_talk", "need": {"quest_active": "q1"}, "action": {"set_flag": "rewarded"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "dogs": {
                "text": "唉，那些畜生是入秋之后从西边荒地窜过来的，成群结队，见人就咬。猎户们试着清了几次，可它们越打越凶。",
                "options": [
                    {"text": "我这就去解决它们！", "next": "dogs_pledge", "action": {"set_flag": "pledged"}},
                    {"text": "商队损失大吗？", "next": "dogs_trade"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "dogs_pledge": {
                "text": "好样的！镇子西边的路口就是它们的老窝。替我们把它们赶走，镇子不会亏待你的。",
                "options": [
                    {"text": "包在我身上！", "next": "__end__"},
                ],
            },
            "dogs_trade": {
                "text": "上周一支药材商队被冲散了，两车草药丢在荒地里。再这么下去，入冬的物资怕是凑不齐了……",
                "options": [
                    {"text": "我这就去解决它们！", "next": "dogs_pledge", "action": {"set_flag": "pledged"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "town": {
                "text": "镇子还算太平，多亏了铁匠托尔那把好锤子，还有老杰克酒馆的麦酒——大伙儿晚上有个地方松快松快。对了，城门口那位吟游诗人莉莉，最近老念叨什么'隧洞之王'，你感兴趣可以去听听。",
                "options": [
                    {"text": "野狗是怎么回事？", "next": "dogs"},
                    {"text": "我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "text": "正好！镇子西边路口那群野狗越来越猖狂，商队都不敢进城了。帮我解决这个麻烦，镇子不会亏待你的。",
                "options": [
                    {"text": "交给我了！", "next": "quest_accept", "action": {"set_flag": "quest_hint"}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "quest_accept": {
                "text": "好！往西走到野狗出没的地方，把它们清干净，回来找我领赏。",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "text": "你回来了！商队已经在准备进城了，镇子欠你一个大人情。来吧，这是你应得的报酬！",
                "options": [
                    {"text": "收下报酬！", "next": "__end__"},
                ],
            },
        },
    },
    "npc_blacksmith": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "嘿，冒险者！我这儿的家伙什都是上好的货。买把趁手的武器再上路吧！",
                "options": [
                    {"text": "看看你的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "附近有好矿石吗？", "next": "ore"},
                    {"text": "镇上的武器怎么样？", "next": "quality"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ore": {
                "text": "说到矿石——石拳丘陵那群矮人手上才有真货，可惜矿洞被地精占了。镇上北边有条废弃矿道，能挖到些铁矿石，不嫌弃的话可以自己去碰碰运气。",
                "options": [
                    {"text": "看看你的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quality": {
                "text": "不是我吹牛，维拉镇的铁匠铺虽然小，但每一把剑都是我亲手打的。别拿城里那些流水线货跟我们比！",
                "options": [
                    {"text": "看看你的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "shop": {
                "text": "慢慢挑，挑好了喊我一声就行！",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_bartender": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "欢迎光临醉熊酒馆！要听故事还是喝一杯？",
                "options": [
                    {"text": "来一杯麦酒。", "next": "drink", "action": {"set_flag": "drank"}},
                    {"text": "最近有什么传闻？", "next": "rumor"},
                    {"text": "讲讲你的故事？", "next": "story"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "drink": {
                "text": "给你！这是本店招牌——加了蜂蜜的熊麦酒。慢点喝，后劲大着呢。",
                "options": [
                    {"text": "好酒！最近有什么传闻？", "next": "rumor"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "rumor": {
                "text": "嘿，你来得巧。听说翡翠森林最近来了头远古圣鹿，一身皮毛亮得跟月光似的，不少人盯着呢。还有个事儿——石拳丘陵的矿洞被地精占了，矮人气得直跳脚，哈哈哈！",
                "options": [
                    {"text": "远古圣鹿？展开说说。", "next": "stag"},
                    {"text": "地精？它们怎么会占矿洞。", "next": "goblin"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "stag": {
                "text": "那圣鹿是森林的老住户了，以前只听过传说，没见过真身。最近它老在林子里晃，大家都说是森林出了什么变故……德鲁伊那边的人愁眉苦脸的。",
                "options": [
                    {"text": "最近还有什么传闻？", "next": "rumor"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "goblin": {
                "text": "那群绿皮小崽子不知道从哪冒出来的，一窝蜂占了矿洞。矮人长老铁砧气得胡子都翘了，说要找人帮忙打回去。你要是想赚点矮人的友谊，可以去找他聊聊。",
                "options": [
                    {"text": "最近还有什么传闻？", "next": "rumor"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "story": {
                "text": "我年轻的时候也当过冒险者！去过风暴之巅，见过云端之上的隐士……咳，好汉不提当年勇。来，喝酒！",
                "options": [
                    {"text": "好酒！最近有什么传闻？", "next": "rumor"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_innkeeper": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "累了吧？在星夜旅店歇一晚，保你明天生龙活虎！",
                "options": [
                    {"text": "住一晚。", "next": "stay", "action": {"hint": "输入『住宿』恢复满血（需要金币）"}},
                    {"text": "最近有奇怪的客人吗？", "next": "gossip"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "stay": {
                "text": "热水已经备好了，被褥也是刚晒过的。好好睡一觉，明天的事明天再说。",
                "options": [
                    {"text": "老板娘，店里最近热闹吗？", "next": "gossip"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip": {
                "text": "哎哟，可别说——前几天住了个矮人商人，喝多了吹牛说石拳丘陵的矿洞里藏着宝贝。还有那个吟游诗人莉莉，天天在广场上弹琴，唱什么'隧洞之王'，把小孩子都吓哭了！",
                "options": [
                    {"text": "住一晚。", "next": "stay", "action": {"hint": "输入『住宿』恢复满血（需要金币）"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_bounty": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "小子，想赚点外快？每天都有悬赏任务，干完来我这儿领赏金。",
                "options": [
                    {"text": "看看今天的悬赏。", "next": "daily", "action": {"hint": "输入『每日』领取今日悬赏"}},
                    {"text": "你见过最危险的猎物是什么？", "next": "tale"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "daily": {
                "text": "悬赏板就在那边。记住，赏金猎人最重要的是眼力——知道什么该惹，什么不该惹。",
                "options": [
                    {"text": "你见过最危险的猎物是什么？", "next": "tale"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "tale": {
                "text": "哼，那得数赤脊荒原的兽人酋长。三年前我带着一队人去追他的悬赏，结果折了半队人……那家伙的刀比门板还宽。听说现在有个兽人俘虏被关在他营地里，也不知道是真是假。",
                "options": [
                    {"text": "看看今天的悬赏。", "next": "daily", "action": {"hint": "输入『每日』领取今日悬赏"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_bard": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "你听说了吗？矮人那边石拳丘陵的矿洞被地精占了，听说深处出了个'隧洞之王'……",
                "options": [
                    {"text": "唱首歌吧。", "next": "song", "action": {"set_flag": "heard_song"}},
                    {"text": "隧洞之王是什么？", "next": "tunnel_king"},
                    {"text": "讲讲英雄王的传说？", "next": "hero"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "song": {
                "text": "那就献丑啦——\n『月光洒在翡翠林，\n 圣鹿踏过银色的溪。\n 远方来的冒险者呀，\n 你的名字将刻进风里。』",
                "options": [
                    {"text": "隧洞之王是什么？", "next": "tunnel_king"},
                    {"text": "讲讲英雄王的传说？", "next": "hero"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "tunnel_king": {
                "text": "那是矿洞深处的传说。地精们挖穿了什么东西，唤醒了不该醒的存在——大家都叫它'隧洞之王'。矮人们说，那玩意儿在矿脉深处等着，等一个敢下去的勇士。",
                "options": [
                    {"text": "唱首歌吧。", "next": "song"},
                    {"text": "讲讲英雄王的传说？", "next": "hero"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hero": {
                "text": "传说在很久以前，有一位英雄王，他持着圣剑走遍这片大陆，斩尽黑暗。他的故事都写在远境王国的史书里……可惜啊，那都是几百年前的事了。现在的人，只关心麦酒和金币。",
                "options": [
                    {"text": "隧洞之王是什么？", "next": "tunnel_king"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 翡翠森林 ====================
    "npc_druid": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "外来者，森林在哭泣。远古圣鹿被黑暗侵蚀了心智，只有击败它才能让森林重归平静。",
                "options": [
                    {"text": "圣鹿为什么会变成这样？", "next": "why"},
                    {"text": "我能做什么？", "next": "help", "need": {"quest_pending": "q2"}, "action": {"set_flag": "pledged"}},
                    {"text": "任务完成了！", "next": "done", "need": {"quest_active": "q2"}, "action": {"set_flag": "blessed"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "why": {
                "text": "圣鹿本是森林的守护灵，百年来庇佑草木生长。可最近，翡翠森林的深处渗出了一股黑暗的气息……它每日守在源头，一天比一天虚弱，一天比一天疯狂。",
                "options": [
                    {"text": "我能做什么？", "next": "help", "need": {"quest_pending": "q2"}, "action": {"set_flag": "pledged"}},
                    {"text": "那黑暗的气息是什么？", "next": "darkness"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "darkness": {
                "text": "我感受过那股气息……冰冷的，腐朽的，不属于这个世界。像是从地底深处渗上来的。这让我想起老人们对'旧王国'的恐惧——那座沉入地下的王城。",
                "options": [
                    {"text": "我能做什么？", "next": "help", "need": {"quest_pending": "q2"}, "action": {"set_flag": "pledged"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "help": {
                "text": "找到圣鹿，了结它的痛苦。让森林的守护灵安息，翡翠森林才能重获新生。去吧，顺着溪流往林深处走。",
                "options": [
                    {"text": "我这就去。", "next": "__end__"},
                ],
            },
            "done": {
                "text": "你做到了……我能感觉到，森林在重新呼吸。谢谢你，外来者。愿绿叶永远庇护你。",
                "options": [
                    {"text": "森林会好起来的。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 石拳丘陵 ====================
    "npc_dwarf_elder": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "地精那群小崽子霸占了我们的矿洞！勇士，帮我们把矿洞夺回来，矮人的友谊和商店都给你！",
                "options": [
                    {"text": "矿洞里情况怎么样？", "next": "situation"},
                    {"text": "地精为什么要占矿洞？", "next": "why"},
                    {"text": "看看矮人的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "situation": {
                "text": "矿洞三层！第一层全是地精小崽子，第二层有个大个子头目，最深处……咳，我们还没来得及探。总之先把洞口清出来！",
                "options": [
                    {"text": "地精为什么要占矿洞？", "next": "why"},
                    {"text": "看看矮人的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "why": {
                "text": "谁知道呢！那群绿皮以前只敢在山脚捡垃圾。最近像是发了疯似的往地底钻——我怀疑它们挖到了什么不该挖的东西。吟游诗人说什么'隧洞之王'……呸，我才不信！",
                "options": [
                    {"text": "矿洞里情况怎么样？", "next": "situation"},
                    {"text": "看看矮人的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "shop": {
                "text": "矮人打造的货，大陆上最好的！钱货两讫，童叟无欺！",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 赤脊荒原 ====================
    "npc_orc_prisoner": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "勇士……帮我逃出酋长的营地，兽人欠你一个人情。酋长太残暴了，部落需要新的首领……",
                "options": [
                    {"text": "你是怎么被抓的？", "next": "story"},
                    {"text": "我能帮你做什么？", "next": "help", "need": {"quest_pending": "q5"}, "action": {"set_flag": "pledged"}},
                    {"text": "任务完成了！", "next": "done", "need": {"quest_active": "q5"}, "action": {"set_flag": "freed"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "story": {
                "text": "我是血牙氏族的战士。酋长卡兹为了扩张地盘，逼着我们攻打人类的村庄。我不愿看到妇孺流血，顶撞了几句……就被关在这里，等死。",
                "options": [
                    {"text": "我能帮你做什么？", "next": "help", "need": {"quest_pending": "q5"}, "action": {"set_flag": "pledged"}},
                    {"text": "酋长很难对付吗？", "next": "chief"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "chief": {
                "text": "卡兹是赤脊荒原最强的战士，一拳能砸碎岩石。但他欺软怕硬——只要在正面击败他，部落的规矩就是新首领说了算。",
                "options": [
                    {"text": "我能帮你做什么？", "next": "help", "need": {"quest_pending": "q5"}, "action": {"set_flag": "pledged"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "help": {
                "text": "替我向酋长下战书！堂堂正正击败他，部落就会追随你……不，追随愿意让族人活下去的人。",
                "options": [
                    {"text": "我会正面击败他。", "next": "__end__"},
                ],
            },
            "done": {
                "text": "你做到了……我自由了。血牙氏族欠你一份永远的人情，勇士。愿你的名字在草原上传颂！",
                "options": [
                    {"text": "愿你带领部落走向和平。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 黑石城废墟 ====================
    "npc_ghost_knight": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "吾乃旧王国骑士赛德里克……巫妖宰相篡夺了王座。勇士，替我复仇，吾将指引你圣光之路……",
                "options": [
                    {"text": "旧王国发生了什么？", "next": "history"},
                    {"text": "巫妖宰相是谁？", "next": "lich"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "history": {
                "text": "三百年前，旧王国繁荣昌盛，圣光普照。直到宰相弗拉基尔沉迷黑魔法……他召唤了不属于此世的存在，一夜之间，王城沉入地底，只留下这堆废墟。",
                "options": [
                    {"text": "巫妖宰相是谁？", "next": "lich"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "lich": {
                "text": "弗拉基尔早已不是人类。他把自己献祭给了深渊，成了不死的巫妖。王城的亡魂们都被他奴役……只有击败他，吾等才能安息。",
                "options": [
                    {"text": "旧王国发生了什么？", "next": "history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 风暴之巅 ====================
    "npc_sky_hermit": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "哦？居然有人能走到这里。你可知秘银遗迹的传说？那才是强者真正的试炼……",
                "options": [
                    {"text": "秘银遗迹是什么？", "next": "relic"},
                    {"text": "你为什么住在这山巅？", "next": "why"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "relic": {
                "text": "那是上古工匠的杰作，一座以秘银铸造的迷宫，埋藏着失传的锻造秘法。据说只有真正的强者才能走到中心……老夫在这里守了三十年，就是在等一个值得托付的人。",
                "options": [
                    {"text": "你为什么住在这山巅？", "next": "why"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "why": {
                "text": "老夫年轻时是个铁匠学徒，亲眼见过秘银遗迹的辉光。从那以后，俗世的铁锤再也敲不出让我心动的声音……便搬到这山巅，日日看着云海，等那位有缘人。",
                "options": [
                    {"text": "秘银遗迹是什么？", "next": "relic"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 远境城（后期区域） ====================
    "npc_holy_king": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "远境城的大门永远为勇士敞开。城外的光耀狼最近格外凶悍，替王国清除它们，圣光会铭记你的功绩。",
                "options": [
                    {"text": "光耀狼为何凶悍？", "next": "wolves"},
                    {"text": "国王陛下，王国近来如何？", "next": "kingdom"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wolves": {
                "text": "光耀狼本是圣光庇护的灵兽，可近来城外的圣光矿脉异动，狼群被浊气侵染，失了本性。若放任不管，它们会一路扑到城门口。",
                "options": [
                    {"text": "国王陛下，王国近来如何？", "next": "kingdom"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "kingdom": {
                "text": "圣光王国传承千年，从未如今日般动荡。大主教菲奥娜说祭坛的光芒正在减弱……勇者，若你有心，不妨去大教堂拜访她。",
                "options": [
                    {"text": "光耀狼为何凶悍？", "next": "wolves"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
}
