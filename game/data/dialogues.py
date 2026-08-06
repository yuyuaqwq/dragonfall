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
    # ==================== 副业导师（19 章第八章：三关拜师） ====================
    # 通用结构：ask(理论) → ask_wrong → practice_intro → practice_check → master_intro → master_check → master_pass(拜师成功) → chat
    # 选项 action 扩展：
    #   {"apprentice_check": {"item": 材料名, "count": N}} + 选项 fail_next → 命令层检查背包，不足走 fail_next
    #   {"unlock_prof": 副业key} → 拜师成功激活副业 + 记录学徒资格
    #   {"give_prof_exp": N} → 给副业经验
    #   {"consume_item": {"item": 材料名, "count": N}} → 扣材料（授业交付）
    # 条件 need 扩展：{"not_apprentice": 副业key} → 未拜师才显示（已拜师走 chat 分支）

    # ---------- 采集·草药师艾琳（橡木镇） ----------
    "npc_herb_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "小姑娘别怕，采药不是力气活。想拜师学采集，先回答我——哪种草能治伤口？",
                "options": [
                    {"text": "止血草", "need": {"not_apprentice": "gather"}, "next": "practice_intro", "answer": True},
                    {"text": "毒蘑菇", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "荆棘叶", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "gather"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "艾琳笑着摇头：再想想，采错药可是要出人命的。哪种草能治伤口？",
                "options": [
                    {"text": "止血草", "need": {"not_apprentice": "gather"}, "next": "practice_intro", "answer": True},
                    {"text": "毒蘑菇", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "荆棘叶", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "不错，有点天分。不过光会认不行——去橡木草地采 3 份草药回来给我看看。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "回来啦？让我看看你采的草药。",
                "options": [
                    {"text": "草药采够了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "草药", "count": 3}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "艾琳摇头：还差一点，采够了再来找我。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                ],
            },
            "master_intro": {
                "text": "最后一道考验——把 1 份最鲜嫩的草药亲手交给我，证明你的眼力。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "嗯……让我看看这份草药。",
                "options": [
                    {"text": "草药在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "草药", "count": 1}, "consume_item": {"item": "草药", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "艾琳摇头：这份还不够新鲜，再采一份来。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                ],
            },
            "master_pass": {
                "text": "好！从今天起你就是我的学徒了。这把小铲送给你，好好学！",
                "options": [
                    {"text": "谢谢艾琳婆婆！", "next": "chat", "action": {"unlock_prof": "gather", "give_prof_exp": 50, "give_item": {"key": "草药", "count": 3}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "艾琳笑眯眯：采药讲究的是耐心，跟种花一个道理。有空常来，婆婆给你讲讲故事。",
                "options": [
                    {"text": "告辞", "next": "__end__"},
                ],
            },
        },
    },
    # ---------- 挖掘·矿工长巴尔金（铁港城） ----------
    "npc_mine_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "挖矿跟喝酒一样，讲究一个痛快！想拜师学挖掘，先回答我——什么矿石最坚硬？",
                "options": [
                    {"text": "源质", "need": {"not_apprentice": "mining"}, "next": "practice_intro", "answer": True},
                    {"text": "铁矿石", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "秘银", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "mining"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "巴尔金灌了口烈酒：哈哈哈，再想想！越往地下走，好东西越硬！",
                "options": [
                    {"text": "源质", "need": {"not_apprentice": "mining"}, "next": "practice_intro", "answer": True},
                    {"text": "铁矿石", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "秘银", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "有点眼力！去矿洞挖 5 份铁矿石回来，让我看看你的力气。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "回来了？把矿石摆出来我瞧瞧。",
                "options": [
                    {"text": "铁矿石挖够了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "铁矿石", "count": 5}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "巴尔金摇头：不够不够，矿洞里还有的是！",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一道考验——交 1 份精铁上来，证明你分得清矿的好坏。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "嗯，让老子看看这块料。",
                "options": [
                    {"text": "精铁在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "精铁", "count": 1}, "consume_item": {"item": "精铁", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "巴尔金皱眉：这块不成色！再去找找。",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "好小子！从今天起你就是矿工行会的人了。这把鹤嘴锄拿好，别丢矿工的脸！",
                "options": [
                    {"text": "谢巴尔金大哥！", "next": "chat", "action": {"unlock_prof": "mining", "give_prof_exp": 50, "give_item": {"key": "铁矿石", "count": 3}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "巴尔金豪迈大笑：挖矿的汉子没有孬种！缺矿石就来找我喝一杯。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ---------- 垂钓·老渔夫马库斯（铁港城） ----------
    "npc_fish_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "……夜里的海，有鱼。想拜师学垂钓，先回答我——哪种鱼只在深夜出没？",
                "options": [
                    {"text": "夜光鲛", "need": {"not_apprentice": "fishing"}, "next": "practice_intro", "answer": True},
                    {"text": "银鳞鱼", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "金鲤", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "fishing"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "马库斯望着海面，轻声说：夜里才出来的鱼，身上带着光……再想想。",
                "options": [
                    {"text": "夜光鲛", "need": {"not_apprentice": "fishing"}, "next": "practice_intro", "answer": True},
                    {"text": "银鳞鱼", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "金鲤", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "……知道。去钓 3 条银鳞鱼回来，让老头子看看你的耐心。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "……回来了？鱼篓给我看看。",
                "options": [
                    {"text": "银鳞鱼钓够了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "银鳞鱼", "count": 3}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "马库斯摇头：……还差几条，海里的鱼跑不了。",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一道考验——钓 1 条金鲤回来，证明你的运气。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "……金鲤，金灿灿的，让我看看。",
                "options": [
                    {"text": "金鲤在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "金鲤", "count": 1}, "consume_item": {"item": "金鲤", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "马库斯淡淡说：……不是金鲤。再试试。",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "……行，你过关了。这根鱼竿送你。以后潮起潮落，鱼都在那里等你。",
                "options": [
                    {"text": "谢谢马库斯爷爷！", "next": "chat", "action": {"unlock_prof": "fishing", "give_prof_exp": 50, "give_item": {"key": "银鳞鱼", "count": 2}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "马库斯望着海：……钓鱼不急，急的人钓不到大鱼。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ---------- 烹饪·大厨罗莎（白鹿城） ----------
    "npc_cook_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "年轻人会做饭吗？不会？没关系！先回答我——烤肉串的主料是啥？",
                "options": [
                    {"text": "兽肉", "need": {"not_apprentice": "cooking"}, "next": "practice_intro", "answer": True},
                    {"text": "草药", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "面粉", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "cooking"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "罗莎叉腰大笑：哈哈哈，那玩意儿能烤吗！再想想！",
                "options": [
                    {"text": "兽肉", "need": {"not_apprentice": "cooking"}, "next": "practice_intro", "answer": True},
                    {"text": "草药", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "面粉", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "有悟性！给我收集 2 份兽肉和 1 份草药来，当今天的食材。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "食材带回来了？让我看看新鲜不新鲜。",
                "options": [
                    {"text": "食材齐了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "兽肉", "count": 2}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "罗莎摆手：不够不够！厨房里可不兴偷工减料。",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一道考验——交 1 份面粉上来，让我看看你备料的功夫。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "面粉呢？拿来我看看成色。",
                "options": [
                    {"text": "面粉在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "面粉", "count": 1}, "consume_item": {"item": "面粉", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "罗莎摇头：这面粉不行，换一袋来！",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "行，收你当徒弟！这本基础菜谱送你，好好练手艺！",
                "options": [
                    {"text": "谢谢罗莎大厨！", "next": "chat", "action": {"unlock_prof": "cooking", "give_prof_exp": 50, "give_item": {"key": "兽肉", "count": 2}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "罗莎热情道：学会做饭走遍天下都不怕！缺食材随时来找我。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ---------- 炼金·炼金术士梅尔文（晨曦城） ----------
    "npc_alchemy_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "外行总以为炼金是玩火。哼，治疗药水的主料是什么？答不上来就滚。",
                "options": [
                    {"text": "草药", "need": {"not_apprentice": "alchemy"}, "next": "practice_intro", "answer": True},
                    {"text": "矿石", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "羽毛", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "alchemy"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "梅尔文冷笑：啧，连这都不知道，还想碰烧瓶？再想想。",
                "options": [
                    {"text": "草药", "need": {"not_apprentice": "alchemy"}, "next": "practice_intro", "answer": True},
                    {"text": "矿石", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "羽毛", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "哼，勉强算你答对了。去收集 3 份草药和 1 个空瓶来，我要看看你的材料鉴别能力。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "材料拿来了？摆桌上，我看看。",
                "options": [
                    {"text": "材料齐了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "草药", "count": 3}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "梅尔文不耐：这点材料都凑不齐，还想当炼金术士？",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一项——交 1 份草药上来，我教你分辨药性。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "草药呢？拿来看看。",
                "options": [
                    {"text": "草药在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "草药", "count": 1}, "consume_item": {"item": "草药", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "梅尔文皱眉：这株药性太差。换一株。",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "……行，收你了。这本基础炼金配方拿去，别炸了我的工房。",
                "options": [
                    {"text": "谢谢梅尔文先生！", "next": "chat", "action": {"unlock_prof": "alchemy", "give_prof_exp": 50, "give_item": {"key": "空瓶", "count": 2}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "梅尔文冷哼：炼金是严谨的科学，不是戏法。有空多读读书。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ---------- 打造·铁匠大师奥格（铁港城） ----------
    "npc_craft_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "打铁，凭的是手和心。想拜师学打造，先回答我——打造装备需要什么？",
                "options": [
                    {"text": "图纸+材料", "need": {"not_apprentice": "craft"}, "next": "practice_intro", "answer": True},
                    {"text": "只有材料", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "只有金币", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "craft"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "奥格敲了敲铁砧：没有图纸，材料就是废铁！再想想。",
                "options": [
                    {"text": "图纸+材料", "need": {"not_apprentice": "craft"}, "next": "practice_intro", "answer": True},
                    {"text": "只有材料", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "只有金币", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "懂行！去矿洞挖 5 份铁矿石回来，让我看看你的力气。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "矿石搬来了？放这儿，我瞅瞅。",
                "options": [
                    {"text": "铁矿石齐了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "铁矿石", "count": 5}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "奥格摇头：不够打一把剑的，再去挖！",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一道考验——交 1 份铁矿石上来，让我看看你识料的眼力。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "铁矿石拿来，我掂掂分量。",
                "options": [
                    {"text": "铁矿石在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "铁矿石", "count": 1}, "consume_item": {"item": "铁矿石", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "奥格摇头：这块矿杂质太多，换一块！",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "好，从今天起你就是我的学徒了。基础武器图纸拿去，别砸了我的招牌！",
                "options": [
                    {"text": "谢奥格师傅！", "next": "chat", "action": {"unlock_prof": "craft", "give_prof_exp": 50, "give_item": {"key": "铁矿石", "count": 3}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "奥格擦了擦手：打铁如做人，实打实，不能虚。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ---------- 强化·强化师克拉拉（白鹿城） ----------
    "npc_enhance_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "强化是门生意，也是门赌术。想拜师学强化，先回答我——+6 以上强化失败会怎样？",
                "options": [
                    {"text": "降 2 级", "need": {"not_apprentice": "enhance"}, "next": "practice_intro", "answer": True},
                    {"text": "降 1 级", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "装备消失", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "enhance"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "克拉拉拨着算盘：高风险高回报，+6 以上失败可不止掉一级。再想想。",
                "options": [
                    {"text": "降 2 级", "need": {"not_apprentice": "enhance"}, "next": "practice_intro", "answer": True},
                    {"text": "降 1 级", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "装备消失", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "明白人！去收集 3 颗强化石来，让我看看你的本钱。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "强化石带来了？我点点数。",
                "options": [
                    {"text": "强化石齐了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "强化石", "count": 3}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "克拉拉摇头：本钱不够可玩不起强化，再去收几颗。",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一项——交 1 颗强化石上来，让我看看你的诚意。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "强化石呢？拿来看看成色。",
                "options": [
                    {"text": "强化石在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "强化石", "count": 1}, "consume_item": {"item": "强化石", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "克拉拉皱眉：这颗品质太差，换一颗。",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "行，收你了！送你 3 颗强化石练手。记住：赌对了是本事，赌输了是学费！",
                "options": [
                    {"text": "谢克拉拉姐！", "next": "chat", "action": {"unlock_prof": "enhance", "give_prof_exp": 50, "give_item": {"key": "强化石", "count": 3}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "克拉拉挑眉：强化这事，心里要有一本账，别红了眼。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ---------- 附魔·符文大师吉姆利（铁砧要塞） ----------
    "npc_rune_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                "text": "符文不是刻上去的花纹，是大地母神的语言。想拜师学附魔，先回答我——法师最适合附魔什么属性？",
                "options": [
                    {"text": "魔攻", "need": {"not_apprentice": "enchant"}, "next": "practice_intro", "answer": True},
                    {"text": "攻击", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "速度", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "enchant"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "吉姆利敲着符文石：法师靠魔力吃饭，附魔也得顺着力量走。再想想。",
                "options": [
                    {"text": "魔攻", "need": {"not_apprentice": "enchant"}, "next": "practice_intro", "answer": True},
                    {"text": "攻击", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "速度", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                ],
            },
            "practice_intro": {
                "text": "有悟性！去收集 3 份魔法粉尘来，让我看看你收集材料的本事。",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                "text": "魔法粉尘带来了？我看看纯度。",
                "options": [
                    {"text": "魔法粉尘齐了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "魔法粉尘", "count": 3}}, "fail_next": "practice_wait"},
                    {"text": "还差一些", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                "text": "吉姆利摇头：粉尘不够，符文画不完整。",
                "options": [{"text": "这就去", "next": "practice_check"}],
            },
            "master_intro": {
                "text": "最后一项——交 1 份魔法粉尘上来，作为你入门的第一份材料。",
                "options": [
                    {"text": "这就去", "next": "master_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "master_check": {
                "text": "魔法粉尘呢？拿来我看看。",
                "options": [
                    {"text": "魔法粉尘在这里，请收下", "next": "master_pass", "action": {"apprentice_check": {"item": "魔法粉尘", "count": 1}, "consume_item": {"item": "魔法粉尘", "count": 1}}, "fail_next": "master_wait"},
                    {"text": "还差一些", "next": "master_wait"},
                ],
            },
            "master_wait": {
                "text": "吉姆利摇头：纯度不够，画不出完整的符文。",
                "options": [{"text": "这就去", "next": "master_check"}],
            },
            "master_pass": {
                "text": "好，从今往后你就是符文塔的学徒了。这颗符文石送你，记住符文之心。",
                "options": [
                    {"text": "谢吉姆利大师！", "next": "chat", "action": {"unlock_prof": "enchant", "give_prof_exp": 50, "give_item": {"key": "魔法粉尘", "count": 2}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "吉姆利低语：符文刻在石上，也刻在心里。多听大地母神的话。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
}
