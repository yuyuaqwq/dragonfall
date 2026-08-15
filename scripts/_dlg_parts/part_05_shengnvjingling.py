# -*- coding: utf-8 -*-
"""05 圣女与精灵组 主线对话树实现分片（策划案 05 翻译）

覆盖 4 NPC：
- npc_saintess（圣女·艾莉丝）：q6_1/q6_2/q6_3/q6_4/q6_5/q11_6（无支线）
- npc_elf_queen（精灵女王·艾拉蕊·星语）：q7_1（无支线）
- npc_elf_guardian（月影卫士长·瑟兰）：q7_2/q7_6 + 支线 s12
- npc_elf_sage（贤者·伊露恩）：q7_3/q7_4/q7_5 + 支线 s13

纯字面量 dict，供 scripts/_merge_dlg_parts.py 以 ast.literal_eval 解析合并。
台词 100% 照策划案 05 成稿机械搬运。
"""
# fmt: off
DIALOGUES_PART = {
    # ==================== 圣女·艾莉丝 ====================
    "npc_saintess": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_any_active": True, "quest_done": "q6_5"},
                     "text": "艾莉丝披着旧斗篷立在银铃河畔，直到听见你的脚步声才回头：『你回来了。银铃河的水声，还像小时候那样好听。』"},
                    {"need": {"quest_done": "q6_1"},
                     "text": "艾莉丝向你微微欠身：『西境的事，就交给你了。教会追杀我的日子，总算暂告一段落……我在晨曦城等你平安的消息。』"},
                    {"need": {"quest_done": "q12_1"},
                     "text": "艾莉丝站在晨曦城头，月光落在她掌心的一缕圣光上：『走到这一步了。谢谢你陪我走了这么远。』"},
                ],
                "text": "圣女·艾莉丝扶着树干缓缓站起，一脸疲惫却目光倔强：『你……你是行会派来的？老约翰他还活着？我的圣光能治愈伤口，却治不了教会的谎言。谢谢你，愿意相信我。』",
                "options": [
                    {"text": "🤔 你伤得很重，我帮你包扎一下？", "next": "wnd_worry", "need": {"not_quest_done": "q6_1"}},
                    {"text": "🗺️ 老约翰让我来找你……他欠你一个人情？", "next": "wnd_john", "need": {"not_quest_done": "q6_1"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q6_1"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q6_2"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q6_3"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q6_4"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q6_5"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q11_6"}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_1"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_2"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_3"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_4"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_5"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q11_6"}},
                    {"text": "🧊 要不要我给你暖暖身子？", "next": "wnd_chat", "need": {"quest_done": "q6_1", "not_quest_done": "q11_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_worry": {
                "text": "你上前替她缠紧绷带。她低低\"嘶\"了一声，却弯了弯嘴角：『好多年没人这样关心过我了。圣女庭的规矩是——圣女只能给予，不能索求。可你给的……我收下了。』",
                "options": [
                    {"text": "🤔 说说你这些年过的是什么日子？", "next": "wnd_worry_1", "need": {"not_quest_done": "q6_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_worry_1": {
                "texts": [
                    {"need": {"quest_pending": "q6_1"},
                     "text": "她望向银铃河流去的方向，声音很轻：『日子？是一天天数着第二次日出——因为每次日出，都有人在我的经文里提醒我，我是\"封印的一部分\"。这条河我没法自己走出去，……你愿意，陪我走吗？』"},
                ],
                "text": "她摇摇头，把涌到嘴边的话咽回去：『有些事，等离开这条河再说吧。』",
                "options": [
                    {"text": "✅ 我愿意护送你离开银铃河。", "next": "quest_talk", "need": {"quest_pending": "q6_1"}},
                    {"text": "🤔 你说的\"封印\"，究竟是怎么回事？", "next": "wnd_seal", "need": {"not_quest_done": "q6_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_seal": {
                "texts": [
                    {"need": {"quest_done": "q7_4"},
                     "text": "她眼神微动：『精灵的史书你也看到了吧——封印需要以圣光为祭。那不是玩笑，是代价。……可我不认命。』"},
                ],
                "text": "她攥紧衣角：『历代圣女都是封印的活祭，三百年来已 36 位\"病逝\"。她们不是病逝……是在我不确定的某座祭坛上，被献祭了。我不想再当祭品。』",
                "options": [
                    {"text": "🤔 你亲眼见过献祭吗？", "next": "wnd_seal_2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_seal_2": {
                "text": "她闭上眼：『没有。圣女只在古籍里读到真相，就被软禁了起来。可我知道，下一场祭，轮到我了。所以我才逃。』",
                "options": [
                    {"text": "相信我，我会带你出去。", "next": "quest_talk", "need": {"quest_pending": "q6_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_john": {
                "text": "她的眉眼舒展了些：『老约翰……是这世上少数没把我当\"圣器\"看的人。他欠我祖父一个人情，才受托照拂我。你带着他的标记来找我，我就信了三分。』",
                "options": [
                    {"text": "🤔 那剩下的七分呢？", "next": "wnd_john_2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_john_2": {
                "text": "她认真打量你，片刻后垂下眼帘：『剩下的七分……是你看我的眼神。这世上看我的人，要么仰视\"圣女\"，要么俯视\"逃犯\"。只有你看我，像看一个普通的、走累了的姑娘。』",
                "options": [
                    {"text": "我确实把你当普通姑娘。", "next": "wnd_worry_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_chat": {
                "texts": [
                    {"need": {"quest_done": "q11_6"},
                     "text": "她望着远方的山峦，语气平静却又温柔：『这一次，我终于不是被推上来的。是我自己要站在封印前的。谢谢你，给了我这份底气。』"},
                ],
                "text": "她低头望着掌心的一缕圣光，轻声：『圣光能治愈伤口，却治不了谎言。可至少……现在站在我身边的人，不会再骗我了。』",
                "options": [
                    {"text": "🗺️ 讲讲你的小时候吧？", "next": "wnd_childhood", "need": {"quest_done": "q6_5"}},
                    {"text": "🤔 你不怕死吗？", "next": "wnd_fear", "need": {"quest_done": "q6_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_childhood": {
                "text": "『小时候在圣女庭，我最喜欢偷偷溜到回廊尽头那扇窗。窗外的梧桐树每年春天都开白花。我以为那是我这辈子唯一能遇见的美。』",
                "options": [
                    {"text": "现在呢，你遇见的美多了吗？", "next": "wnd_chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_fear": {
                "text": "『怕。我也怕死。可比起死，我更怕明知道是错的，还要笑着走完那一程。』",
                "options": [
                    {"text": "我陪着你。", "next": "wnd_chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q6_1"},
                     "text": "她向你伸出手，指尖微颤却坚定：『银铃河的水，会把追兵的踪迹冲淡。陪我走完这段路——只要你愿意相信我，我就相信这次逃离是对的。』"},
                    {"need": {"quest_pending": "q6_2"},
                     "text": "艾莉丝递给你一枚生锈的钥匙：『旧王陵的壁画，藏着英雄王艾德里克的最后一笔。我的圣光能送我走到陵门，剩下的……要你去闯。古王·奥德里克的残魂是最后的守墓者，他说——只有配得上真相的人，才能带走那副壁画。』"},
                    {"need": {"quest_pending": "q6_3"},
                     "text": "她脸色一白，压低声音：『是罗兰·圣剑的骑士团，追上来了。他带了龙猎犬，正封住出林的路。我们必须先从他们的包围里撕开一个口子。』她顿了顿：『……他若是看清我的脸，会犹豫。这是我们的机会。』"},
                    {"need": {"quest_pending": "q6_4"},
                     "text": "艾莉丝握紧你带回的壁画拓片：『追兵退了，可罗兰没有走。他站在林外，剑还举着，手却在抖。他在等——等我给他一个答案。「他想知道真相，可他不确定该信谁。」这一次，要你在剑上留三分力，让他输，却输得坦荡。』"},
                    {"need": {"quest_pending": "q6_5"},
                     "text": "罗兰折剑离去之后，营地安静下来。她坐在篝火边，忽然开口：『你想听吗？圣女庭的日子——不是你想象的那样的。那里没有童年，只有等待。』"},
                    {"need": {"quest_pending": "q11_6"},
                     "text": "晨曦城的钟声渐远，她站在城垛上，逆光而立。封印只剩三天。这一次，她没有半点犹疑：『枢机主教要把我再次推上祭坛，好让封印再撑一百年。可这一次——我不想当祭品了。我想和你一起，站在封印之前。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "✅ 我愿意，与你同行。", "next": "q1_accept", "need": {"quest_pending": "q6_1"}, "action": {"set_flag": "saintess_trust"}},
                    {"text": "🤔 我们往哪走？逃得掉吗？", "next": "q1_route", "need": {"quest_pending": "q6_1"}},
                    {"text": "🤔 教会为什么会追杀你到这种地步？", "next": "q1_church", "need": {"quest_pending": "q6_1"}},
                    {"text": "✅ 我去闯旧王陵。", "next": "q2_accept", "need": {"quest_pending": "q6_2"}, "action": {"quest_take": True}},
                    {"text": "🤔 古王残魂说的\"正确的选择\"是什么？", "next": "q2_king", "need": {"quest_pending": "q6_2"}},
                    {"text": "🤔 壁画上可能画着什么？", "next": "q2_paint", "need": {"quest_pending": "q6_2"}},
                    {"text": "✅ 我去对付追兵。", "next": "q3_accept", "need": {"quest_pending": "q6_3"}, "action": {"quest_take": True}},
                    {"text": "🤔 罗兰·圣剑，你认识他？", "next": "q3_roland", "need": {"quest_pending": "q6_3"}},
                    {"text": "🤔 为什么他会\"犹豫\"？", "next": "q3_hesitate", "need": {"quest_pending": "q6_3"}},
                    {"text": "✅ 我与他堂堂正正战一场。", "next": "q4_accept", "need": {"quest_pending": "q6_4"}, "action": {"quest_take": True}},
                    {"text": "🤔 为何要\"留手\"？", "next": "q4_spare", "need": {"quest_pending": "q6_4"}},
                    {"text": "🤔 这一战之后呢？", "next": "q4_after", "need": {"quest_pending": "q6_4"}},
                    {"text": "🪩 讲讲看。", "next": "q5_accept", "need": {"quest_pending": "q6_5"}, "action": {"set_flag": "saintess_story", "quest_take": True}},
                    {"text": "🤔 你为什么现在愿意讲了？", "next": "q5_why", "need": {"quest_pending": "q6_5"}},
                    {"text": "🤔 罗兰呢，他也知道这些吗？", "next": "q5_roland", "need": {"quest_pending": "q6_5"}},
                    {"text": "✨ 好，那我们去给这个故事写个不一样的开头。", "next": "q11_accept", "need": {"quest_pending": "q11_6"}, "action": {"set_flag": "saintess_resolve", "quest_take": True}},
                    {"text": "🤔 你不怕这一去，就再也回不来了？", "next": "q11_fear", "need": {"quest_pending": "q11_6"}},
                    {"text": "🗺️ 你的圣光……真的撑得住吗？", "next": "q11_light", "need": {"quest_pending": "q11_6"}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q1_accept": {
                "text": "她看着你，眼眶有些发红，却努力笑出来：『好。银铃河的对岸，是晨曦城的阴影够不着的地方。走吧，孩子——我喊惯了，一时改不了口。』",
                "options": [
                    {"text": "✅ 启程！", "next": "__end__", "need": {"quest_pending": "q6_1"}, "action": {"quest_take": True}},
                ],
            },
            "q1_route": {
                "text": "她压低声音：『沿银铃河西行，过旧渡口，往旧王陵的岔道去。那里有座废弃的界碑，能藏一整夜。教会骑士不熟悉河岸，我们的胜算就是时间差。』",
                "options": [
                    {"text": "✅ 我这就安排路线。", "next": "q1_accept", "need": {"quest_pending": "q6_1"}},
                    {"text": "🤔 旧王陵……你为什么要提起那里？", "next": "q1_tomb", "need": {"quest_pending": "q6_1"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q1_church": {
                "text": "她苦笑：『因为我生来就是\"封印的一部分\"。教会需要一具装满圣光的容器，好让封印再撑一百年。至于我是人是魂，不在他们的考量里。』",
                "options": [
                    {"text": "✅ 我不会让他们得逞。", "next": "q1_accept", "need": {"quest_pending": "q6_1"}},
                    {"text": "🤔 那……旧王陵里可能有什么答案？", "next": "q1_tomb", "need": {"quest_pending": "q6_1"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q1_tomb": {
                "text": "她眼神一亮又暗下：『古籍里读到的——三百年前的英雄王艾德里克，曾把一段不能写进人类史书的真相，刻进了旧王陵的壁画里。我想……那或许是证词，能还我和历代圣女一个清白。』",
                "options": [
                    {"text": "✅ 我们先离开银铃河，再说王陵的事。", "next": "q1_accept", "need": {"quest_pending": "q6_1"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q2_accept": {
                "text": "她后退一步给你让路：『陵里的魔物是三百年前的守护咒唤起的，不会放任何人空手过。记住——真相和命，你至少要带回一个。』",
                "options": [
                    {"text": "我出发了。", "next": "__end__"},
                ],
            },
            "q2_king": {
                "text": "她摩挲着钥匙：『古王说艾德里克\"做了正确的选择，却被世人误解\"。我猜想——所谓\"击杀魔王\"，不过是教会为了让人们记住一个敌人。艾德里克真正做的，是封印住某个更可怕的存在。』",
                "options": [
                    {"text": "✅ 我去把证据带回来。", "next": "q2_accept", "need": {"quest_pending": "q6_2"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q2_paint": {
                "text": "她低声道：『我赌它画的，是艾德里克与\"魔王\"并肩站着、共同封住裂隙的画面。若是真的——人类史书的第一页，就是个笑话。』",
                "options": [
                    {"text": "✅ 我去把证据带回来。", "next": "q2_accept", "need": {"quest_pending": "q6_2"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q3_accept": {
                "text": "她拽住你的手腕又松开：『别恋战，引开龙猎犬，把追兵打退到河对岸就回头。罗兰若亲自带队……你留他性命，余下的交给我。』",
                "options": [
                    {"text": "我去了。", "next": "__end__"},
                ],
            },
            "q3_roland": {
                "text": "她眺望远方：『罗兰·圣剑……他见过我最年幼的样子。我加冕那天，是他扶我登上圣位的。他是这世上，少数记得\"艾莉丝\"而不是\"圣女艾莉丝\"的人。』",
                "options": [
                    {"text": "🗺️ 那你们怎么走到对立面的？", "next": "q3_opp", "need": {"quest_pending": "q6_3"}},
                    {"text": "✅ 我去对付追兵。", "next": "q3_accept"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q3_opp": {
                "text": "她苦笑：『不是走到了对立面。是教会把我的\"逃走\"写成\"堕落\"，让他奉命来抓我。他若看清我还是当年那个妹妹般的姑娘……他会为难。』",
                "options": [
                    {"text": "✅ 那就让他为难去吧，我去开路。", "next": "q3_accept"},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q3_hesitate": {
                "text": "她低声：『龙猎犬只会对\"猎物\"呲牙。可罗兰若看见——猎物眼里有人的光，他下不了手。这是我赌的，也是我活下来的赌注。』",
                "options": [
                    {"text": "✅ 我这就去会会他。", "next": "q3_accept", "need": {"quest_pending": "q6_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q4_accept": {
                "text": "她郑重地望着你：『他要的是\"我的剑不会错\"的信念被击碎，而不是\"罗兰·圣剑\"战败的耻辱。让他在倒下时仍能起身，来找我要一个真相。』",
                "options": [
                    {"text": "明白了。我去去就回。", "next": "__end__"},
                ],
            },
            "q4_spare": {
                "text": "她轻声道：『真正的动摇，不是膝盖跪地，是信仰裂开一条缝。你留三分力，他才会怀疑\"这一剑，是不是本就该犹豫\"。』",
                "options": [
                    {"text": "✅ 我明白了，去会他。", "next": "q4_accept", "need": {"quest_pending": "q6_4"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q4_after": {
                "text": "她望着罗兰所在方向的林梢：『如果他愿意听，我就把封印的真相告诉他。压在他肩上二十年的、教会那套\"魔王传说是教会的根基\"的信仰……该松一松了。』",
                "options": [
                    {"text": "✅ 那这一战，就当作引他回头的台阶。", "next": "q4_accept"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_accept": {
                "text": "她拨了拨火堆，声音轻得像梦：『每天天亮前，我就要在圣女庭的圣像前跪满一个时辰。然后是课业——不是剑术，是怎么\"当好一具容器\"。没有人问过我，我喜不喜欢。』她抬起头，火光映着她的脸：『今天你想听，我就都告诉你。』",
                "options": [
                    {"text": "我听着呢。", "next": "__end__"},
                ],
            },
            "q5_why": {
                "text": "她顿了顿：『因为你是第一个，让我觉得\"说出来了也不会被当成笑话\"的人。而且……罗兰走了，今晚的营火，只够坐两个人。』",
                "options": [
                    {"text": "🪩 那我说说我的童年，也换你的？", "next": "q5_accept", "need": {"quest_pending": "q6_5"}},
                    {"text": "❌ 改天再说。", "next": "welcome"},
                ],
            },
            "q5_roland": {
                "text": "她摇头：『他不知道。他奉教会之命\"守护\"我的时候，我早就学会了把真话锁进心里。他对我的好，是和圣女庭的墙一样——温柔的，却也是困住她的笼子。』",
                "options": [
                    {"text": "🪩 那今晚，把笼子打开给我看。", "next": "q5_accept", "need": {"quest_pending": "q6_5"}},
                    {"text": "❌ 改天再说。", "next": "welcome"},
                ],
            },
            "q11_accept": {
                "text": "她笑了，眼眶却红了——那是终于可以不再当祭品的、如释重负的泪：『从逃离银铃河那天起，我就一直在逃。今天，我不逃了。我要站在封印前，不是为了牺牲，是为了和所有人一起，把那个循环打破。』",
                "options": [
                    {"text": "并肩吧。", "next": "__end__"},
                ],
            },
            "q11_fear": {
                "text": "她轻声：『怕。可我怕的从不是死，是被又一次按在祭坛上、在沉默里\"病逝\"。这一次我能自己选路，就算终点是险境，我也觉得——值。』",
                "options": [
                    {"text": "✨ 那我们一起走。", "next": "q11_accept", "need": {"quest_pending": "q11_6"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q11_light": {
                "text": "她摊开掌心，一缕圣光明灭：『教会的圣光是\"被分发的光\"，只够喂给封印。可你的黎明，是\"愿意守护的光\"。两者不一样——所以我信，我们能撑到真相被点亮的那天。』",
                "options": [
                    {"text": "✨ 那就让我们一起来点亮它。", "next": "q11_accept", "need": {"quest_pending": "q11_6"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "quest_status": {
                "text": "她替你理了理斗篷上的草屑：『你的冒险日志我记着。该去的地方去吧，办妥了回来找我。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_2"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_3"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q6_4"}},
                    {"text": "🗺️ 旧王陵的壁画，我该怎么闯？", "next": "adv_q2", "need": {"quest_active": "q6_2"}},
                    {"text": "🗺️ 骑士团的追兵，我该怎么对付？", "next": "adv_q3", "need": {"quest_active": "q6_3"}},
                    {"text": "🗺️ 罗兰那一战，我该怎么打？", "next": "adv_q4", "need": {"quest_active": "q6_4"}},
                    {"text": "🗺️ 罗兰的事……后来呢？", "next": "adv_roland", "need": {"quest_done": "q6_4", "not_quest_done": "q6_6"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q6_2"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q6_3"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q6_4"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q6_5"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q11_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "adv_roland": {
                "text": "她的目光柔和下来：『罗兰折了自己的剑，回晨曦城去了。他说他会在那边处理教会的事，让我们去西境。那张壁画拓片……我交给他保管了，那里面有他的答案。』",
                "options": [
                    {"text": "🗺️ 他会没事吗？", "next": "adv_roland_2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "adv_roland_2": {
                "text": "她望着天边：『他是我见过最像\"骑士\"字面意思的人——不是教会造的那把剑，是真的会为了守护而折断自己的人。他会没事的，我相信他。』",
                "options": [
                    {"text": "好，那我们也继续走吧。", "next": "__end__"},
                ],
            },
            "adv_q2": {
                "text": "『旧王陵的石门不会自动开。古王残魂的剑，只有配得上真相的人能拔出来。别急，一步一步来——壁画不会长腿跑掉。』",
                "options": [
                    {"text": "✅ 我去找石门了。", "next": "__end__"},
                    {"text": "🤔 我该注意什么？", "next": "adv_q2_hint"},
                ],
            },
            "adv_q2_hint": {
                "text": "『陵里的守护咒会找背光者的破绽。记得带够火把，也别离同伴太远。古王残魂的话，最好一个字都别当耳旁风。』",
                "options": [
                    {"text": "记住了。", "next": "__end__"},
                ],
            },
            "adv_q3": {
                "text": "『龙猎犬还在堵林口。你从北坡绕，绕到它们背后。罗兰若在，别和他正面对——把他引到我这边来。』",
                "options": [
                    {"text": "✅ 我去了。", "next": "__end__"},
                ],
            },
            "adv_q4": {
                "text": "『罗兰还在林外等。记住，剑下留三分——他不是敌人，是迷了路的故人。这一战，赢他，也赢回他。』",
                "options": [
                    {"text": "✅ 我这就去会他最后一战。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q6_1"},
                     "text": "她和你并肩过了渡口，终于长长舒了一口气：『……谢谢。你的圣光，我记在心里。』她顿了顿，声音轻却稳：『历代圣女都是封印的活祭，三百年来已有 36 位「病逝」。我……不想再当祭品了。』"},
                    {"need": {"quest_ready": "q6_2"},
                     "text": "她把壁画拓片举到眼前，指尖微颤：『……是真的。壁画上，英雄王艾德里克和那个被称为\"魔王\"的存在并肩站着，正共同封住一道裂隙。人类史书写的\"击杀魔王\"……是改写过的。』"},
                    {"need": {"quest_ready": "q6_3"},
                     "text": "追兵被击退，她站在你身后，望着那个没追上来的人影：『你看……他没有追。龙猎犬都散了，他一个人愣在原地。他看见我的脸了。』"},
                    {"need": {"quest_ready": "q6_4"},
                     "text": "她扶住半跪的罗兰，转头看你，眼里有光：『他倒下了，也服了。他让我把这句带给你——从今天起，他的剑只守护真相。他折了自己的剑。』"},
                    {"need": {"quest_ready": "q6_5"},
                     "text": "篝火噼啪，她说完最后一个字，安静了很久：『……这就是我的童年。没有玩具，没有玩伴，只有一尊圣像，和倒数的日出。』你听完，沉默了——这个 19 岁的姑娘，背着三百年的血债。她轻轻笑了笑：『可今晚，有人陪我坐到火堆灭了。够了。』"},
                    {"need": {"quest_ready": "q11_6"},
                     "text": "晨曦城的风掀起她的斗篷，她扬起脸，第一次笑得那样毫无阴霾：『这一次，我不想当祭品了。我想和你一起，站在封印之前。』她与光融为一体一般，伸出手：『走吧——去给这个故事，写一个不一样的结局。』"},
                ],
                "options": [
                    {"text": "✅ 收下这份信任！", "next": "__end__", "need": {"quest_ready": "q6_1"}, "action": {"quest_take": True}},
                    {"text": "🤔 那下一步怎么办？", "next": "q1_next", "need": {"quest_ready": "q6_1"}},
                    {"text": "✅ 收下真相！", "next": "__end__", "need": {"quest_ready": "q6_2"}, "action": {"quest_take": True}},
                    {"text": "🤔 那\"烬山下的真相\"又是什么？", "next": "q2_ember", "need": {"quest_ready": "q6_2"}},
                    {"text": "✅ 收下这短暂的平静！", "next": "__end__", "need": {"quest_ready": "q6_3"}, "action": {"quest_take": True}},
                    {"text": "🤔 他会追上来吗？", "next": "q3_back", "need": {"quest_ready": "q6_3"}},
                    {"text": "✅ 迎回这位盟友！", "next": "__end__", "need": {"quest_ready": "q6_4"}, "action": {"quest_take": True}},
                    {"text": "🤔 那他要去哪？", "next": "q4_go", "need": {"quest_ready": "q6_4"}},
                    {"text": "✅ 收下她的故事！", "next": "__end__", "need": {"quest_ready": "q6_5"}, "action": {"quest_take": True}},
                    {"text": "🤔 以后的日子，会不一样吗？", "next": "q5_future", "need": {"quest_ready": "q6_5"}},
                    {"text": "✅ 并肩走下去！", "next": "__end__", "need": {"quest_ready": "q11_6"}, "action": {"quest_take": True}},
                    {"text": "🤔 谢谢你愿意相信我。", "next": "q11_thanks", "need": {"quest_ready": "q11_6"}},
                ],
            },
            "q1_next": {
                "text": "她攥紧钥匙：『去旧王陵。英雄王艾德里克的壁画，藏着能证明我们清白的证词。』",
                "options": [
                    {"text": "那我们就往旧王陵去。", "next": "__end__", "need": {"quest_ready": "q6_1"}, "action": {"quest_take": True}},
                ],
            },
            "q2_ember": {
                "text": "她合上拓片，望向西边：『古王说\"你们要找到烬山下的真相\"。仿佛有一句没说完的话……也许得走到烬山，才能听清。他们来了——骑士团的追兵，该我们应付了。』",
                "options": [
                    {"text": "好，交给我来挡。", "next": "__end__", "need": {"quest_ready": "q6_2"}, "action": {"quest_take": True}},
                ],
            },
            "q3_back": {
                "text": "她摇摇头：『不会立刻。他需要一夜——想想他这二十年都挥向了谁。若是他想通了，会自己来找我的。到那时，才是最艰难的一场仗。』",
                "options": [
                    {"text": "那我们等着他。", "next": "__end__", "need": {"quest_ready": "q6_3"}, "action": {"quest_take": True}},
                ],
            },
            "q4_go": {
                "text": "她低声：『他回晨曦城，去处理教会里的事，让我们去西境——精灵的史书里，记载着完整的圣战。西境，恐怕是我们下一个要去的地方。』",
                "options": [
                    {"text": "我们去西境。", "next": "__end__", "need": {"quest_ready": "q6_4"}, "action": {"quest_take": True}},
                ],
            },
            "q5_future": {
                "text": "她望着将熄的余烬：『会。从前我只敢\"等待\"，不敢\"想要\"。从今晚起，我想试着……自己去要一点什么，比如真相，比如活着。』",
                "options": [
                    {"text": "✅ 那我们一起去找它。", "next": "__end__", "need": {"quest_ready": "q6_5"}, "action": {"quest_take": True}},
                ],
            },
            "q11_thanks": {
                "text": "她轻声道：『该说谢谢的是我。是你告诉我，圣光可以不只是\"被分发的容器\"，也可以是一盏自己点亮的灯。走吧。』",
                "options": [
                    {"text": "✅ 我们走。", "next": "__end__", "need": {"quest_ready": "q11_6"}, "action": {"quest_take": True}},
                ],
            },
        },
    },

    # ==================== 精灵女王·艾拉蕊·星语 ====================
    "npc_elf_queen": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q7_1"},
                     "text": "艾拉蕊女王端坐月桂王座，目光穿过你落在更远的虚空：『你已听完了精灵的证词。如今你带着这份记忆离去——愿你记得，历史不是只有你会读的那一本。』"},
                ],
                "text": "银月精灵女王·艾拉蕊·星语缓缓抬眸，指间流转着一缕月华：『凡人的气息……却带着一股执意探寻真相的劲头。人类，你正走在一条危险的道路上。但精灵不会忘记——三百年前，我们也在烬山。』",
                "options": [
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 请告诉我，三百年前精灵究竟经历了什么？", "next": "wnd_history", "need": {"not_quest_done": "q7_1"}},
                    {"text": "🗺️ 你看出我\"走在危险的道路上\"？", "next": "wnd_danger", "need": {"not_quest_done": "q7_1"}},
                    {"text": "🌙 聊聊精灵与月亮更深处的渊源？", "next": "wnd_moon"},
                    {"text": "🗺️ 关于\"三百年前的精灵\"，你还想说什么？", "next": "wnd_dawn", "need": {"quest_done": "q7_1"}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_history": {
                "text": "她微微倾身：『三百年前，精灵的箭手、矮人的战锤、北境的战吼，与人类英雄王一同在烬山并肩。我们为的不是\"击杀\"，是\"封住\"。』她顿了顿：『至于其中的差别……你该去问贤者伊露恩，他读得比我细致。』",
                "options": [
                    {"text": "📜 那便从觐见你开始吧。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🤔 \"击杀\"和\"封住\"，重要吗？", "next": "wnd_hist2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_hist2": {
                "text": "她凝视着你：『若那场战役只是\"击杀一个魔王\"，那么杀掉他、封印自解。可你一路走来该已明白——封印从未自解。人类史书与精灵史书，记的是同一件事的两个版本。』",
                "options": [
                    {"text": "📜 让我见见能翻开那份史书的人。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 你为何愿信一个人类？", "next": "wnd_trust"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_danger": {
                "text": "她指尖的月华微微漾开：『你身上的气息，是未愈合的裂缝，也是被唤醒的光。追寻真相的人，走的路越真，脚底的冰就越薄。』",
                "options": [
                    {"text": "🤔 那我该如何走？", "next": "wnd_danger2"},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_danger2": {
                "text": "她轻声道：『莫孤身。真相需要见证者，也需要同伴。精灵守候了三百年，等的就是一个愿与他们一同守望的人。』",
                "options": [
                    {"text": "📜 那我就是那个守望的人。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 守望什么？", "next": "wnd_keep"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_trust": {
                "text": "她的眸色难得柔和：『精灵不信\"人类的承诺\"——但我们信\"愿意来月冠王庭听真话的人\"。你跨越了银月林海的雾，踏进这里，这份诚意，月光收下了。』",
                "options": [
                    {"text": "📜 那我该如何觐见你？", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🤔 你为何愿信一个人类？", "next": "wnd_trust_2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_trust_2": {
                "text": "她轻轻摇头：『不是信任人类，是信任\"愿意来听的人\"。三百年来，敢孤身踏入月冠王庭的人类屈指可数。你走到了这里——够了。』",
                "options": [
                    {"text": "📜 那便请女王带我入门。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_keep": {
                "text": "她望向窗外的银月：『守望那扇门后、世人快遗忘的真相。你来的正是时候——银月林海的深处，已经起了涟漪。』",
                "options": [
                    {"text": "📜 那就接住这份使命。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 银月林海怎么了？", "next": "wnd_ripple"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_ripple": {
                "text": "她眸色微沉：『月狼发狂、月华枯竭，都是近来的怪事。精灵守了三百年平静，眼下却像是有什么东西，正沿着月光的缝隙往外渗。』",
                "options": [
                    {"text": "📜 我愿替精灵去查。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 那不是精灵自己的林海吗，为何要我说上话？", "next": "wnd_why_us"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_why_us": {
                "text": "她淡淡道：『守林的是瑟兰那孩子，寻根问底却是另一种本事。有些账，精灵碍于情面不便深究——而一个外来的、愿意刨根问底的人，正合适。』",
                "options": [
                    {"text": "📜 那我便去做那个刨根问底的人。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_moon": {
                "text": "她抬手，月光似有实质地落入她掌心：『月不是挂在天上的灯笼，是照进深渊的一盏灯。精灵相信——只要还有人记得月光的样子，夜就不会彻底黑下去。』",
                "options": [
                    {"text": "🗺️ 这盏灯，如今还够亮吗？", "next": "wnd_moon2"},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_moon2": {
                "text": "她手指合拢，月华熄灭：『三百年前够亮，这些年被慢慢抽走了一些。你来之前，我以为它要靠精灵独自守着。现在嘛……也许该换一批新的人来掌灯了。』",
                "options": [
                    {"text": "📜 那我愿意接下那盏灯。", "next": "quest_talk", "need": {"quest_pending": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_dawn": {
                "texts": [
                    {"need": {"quest_done": "q12_1"},
                     "text": "她难得的露出一丝笑：『你带着联军并肩走过烬山的那一夜，精灵的弓手们还记得你的背影。历史会记住这一天。』"},
                ],
                "text": "她轻轻道：『凡人，你让精灵记住了一件事——不是所有人类都值得警惕。若日后战火燃起，月冠王庭的箭，会为可信之人而鸣。』",
                "options": [
                    {"text": "🗺️ 若真有那一天，你会站在哪边？", "next": "wnd_dawn2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_dawn2": {
                "text": "『站在月光记得的那一边。三百年前精灵在烬山，三百年后依然会去。你若也站在那边——我们便是同路的月亮。』",
                "options": [
                    {"text": "🌙 那我们约好了。", "next": "wnd_dawn3"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_dawn3": {
                "text": "她微微颔首，指间的月华轻轻跃动了一下，像是应答：『约好了。愿我们的路，都通向黎明。』",
                "options": [
                    {"text": "🌙 临行前，我还能问一句吗？", "next": "q1_parting"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q7_1"},
                     "text": "艾拉蕊女王站起身，月华绕她一圈铺成道路：『凡人，你愿做精灵这段历史的见证者吗？若你应允，我以月冠王庭的礼法接待你——你要的真相，就在月桂之下翻开的那一卷史书里。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "✅ 我愿为见证者。", "next": "q1_accept", "need": {"quest_pending": "q7_1"}, "action": {"quest_take": True}},
                    {"text": "🤔 什么是\"月冠之礼\"？", "next": "q1_rite", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 你说的\"危险道路\"，是指什么？", "next": "q1_danger", "need": {"quest_pending": "q7_1"}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q1_accept": {
                "text": "她伸出手，一缕月华落在你肩头，如一枚清凉的印记：『月冠之礼已成。从这一刻起，你是精灵认定的\"走夜路的人\"。贤者伊露恩，会告诉你精灵记住的那一段。』",
                "options": [
                    {"text": "觐见此礼！", "next": "__end__"},
                ],
            },
            "q1_rite": {
                "text": "『月冠之礼，是以月华为印，承认你与精灵有并肩之义。此礼不是束缚，是盟约——我们守约，正如我们守候真相三百年。』",
                "options": [
                    {"text": "✅ 我接受这份盟约。", "next": "q1_accept", "need": {"quest_pending": "q7_1"}},
                    {"text": "🤔 这盏\"灯\"究竟能照多远？", "next": "wnd_rite_var"},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q1_danger": {
                "text": "她的声音放轻：『你正在查的那件事，教会用三百年掩埋，精灵用三百年铭记。触碰它的人，往往走不到真相那一页——就被抹去了。』",
                "options": [
                    {"text": "✅ 我不怕被抹去。", "next": "q1_accept", "need": {"quest_pending": "q7_1"}},
                    {"text": "🗺️ 那我该如何自保？", "next": "q1_watch"},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q1_watch": {
                "text": "『找到愿意并肩的人。证明已备在月桂之下，接下来的路，需要不是一个人走。去银月林海吧——那里有你要的证据，也有考验。』",
                "options": [
                    {"text": "✅ 我这就去。", "next": "q1_accept", "need": {"quest_pending": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "text": "她以指轻叩王座扶手：『精灵的记性很好。你要办的事，办妥了再来见我。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q7_1"},
                     "text": "女王以月华托起一卷镶银的书页递给你：『我读过你的眼睛。既然你愿当见证者，那便去见贤者伊露恩——精灵的史书，由他念给你听最妥。愿月桂的香气，为你开路。』"},
                ],
                "options": [
                    {"text": "✅ 收下月冠之礼！", "next": "__end__", "need": {"quest_ready": "q7_1"}, "action": {"quest_take": True}},
                    {"text": "🤔 多谢女王。我该去哪里找贤者？", "next": "q1_sage", "need": {"quest_ready": "q7_1"}},
                ],
            },
            "q1_sage": {
                "text": "『伊露恩的书房在星语湖畔，那棵枯了半边却仍开花的月桂树下。去找他之前——先去银月林海，瑟兰会告诉你怎么走。』",
                "options": [
                    {"text": "多谢指引。", "next": "__end__", "need": {"quest_ready": "q7_1"}, "action": {"quest_take": True}},
                ],
            },
            "q1_parting": {
                "text": "你转身欲行，女王的低语从身后追来：『凡人——若你在林海里听见月光枯竭的声响，那是深渊在试探。别回头，去把真相带回来。精灵的信诺，已在月桂下许给你了。』",
                "options": [
                    {"text": "🌙 我必带回真相。", "next": "__end__"},
                ],
            },
            "wnd_rite_var": {
                "text": "她指尖轻旋一缕月华，绕成一枚小小的环：『月冠之礼并非加冕，是一盏递给你照路的灯。你带着它走，夜里的深渊，便不敢轻易近你的身。』",
                "options": [
                    {"text": "✅ 那我看清这盏灯了，出发吧。", "next": "__end__"},
                ],
            },
        },
    },

    # ==================== 月影卫士长·瑟兰 ====================
    "npc_elf_guardian": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q7_2", "not_quest_done": "q7_6"},
                     "text": "瑟兰倚在月光斑驳的树干上，拇指摩挲着空空的弓扣：『银月林的夜，越来越像一锅要沸腾的水。那拨叛逃的暗影精灵……居然敢动我和森林的东西。』"},
                    {"need": {"quest_done": "q7_6"},
                     "text": "瑟兰把失而复得的月弓挂在身后，朝你点头：『月弓回来了。这片林子的债，我记下了——也记下你这个朋友。』"},
                ],
                "text": "月影卫士长·瑟兰自树影间现身，眼眶压着一丝不安：『跟紧我。银月林的夜，比你想的要深。近来连温顺的月狼都变得狂暴易怒了——是林深处有东西，想把它们逼疯。』",
                "options": [
                    {"text": "🤔 月狼为什么会变成这样？", "next": "wnd_wolf", "need": {"not_quest_done": "q7_2"}},
                    {"text": "🗺️ 这里的森林，一向这么危险吗？", "next": "wnd_forest", "need": {"quest_done": "q7_2"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_2"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_6"}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_2"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_6"}},
                    {"text": "🗺️ 你是女王护卫？怎么老在林里？", "next": "wnd_guard"},
                    {"text": "🗺️ 月影卫士的忠诚，是怎么守出来的？", "next": "wnd_oath", "need": {"quest_done": "q7_2"}},
                    {"text": "🗺️ 聊聊林子的近况吧？", "next": "wnd_forest2", "need": {"quest_done": "q7_6"}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_wolf": {
                "text": "他目光沉下去：『月狼本是和林子共生死的温顺生灵，连幼崽都敢从我靴边过。可最近它们眼睛发红、见人就扑——这不是它们的本性，是有什么东西在把它们的魂往疯狂里拽。』",
                "options": [
                    {"text": "📜 那我帮你去查。", "next": "quest_talk", "need": {"quest_pending": "q7_2"}},
                    {"text": "🗺️ 你知道是什么在污染它们吗？", "next": "wnd_wolf2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_wolf2": {
                "text": "他压低嗓音：『我只能闻到一丝……咸腥的、不像这座林子的气味，从深处飘来。我说不清那是什么，但我知道它属于深渊。』",
                "options": [
                    {"text": "📜 我替你去林深处看看。", "next": "quest_talk", "need": {"quest_pending": "q7_2"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_forest": {
                "text": "他环顾林海：『它不危险——只要你知道怎么读它的脾气。真正危险的，是那些忘了林子会翻脸的蠢货，比如那批叛逃的暗影精灵，竟敢偷走我的月弓。』",
                "options": [
                    {"text": "🗺️ 那把月弓……对你很重要？", "next": "wnd_bow", "need": {"quest_done": "q7_2", "not_quest_done": "q7_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_bow": {
                "text": "他低声道：『它跟了我五百年。是我还在学走路时，长老用月桂心给我削的。那不只是武器——是半生的见证。』",
                "options": [
                    {"text": "📜 那我帮你夺回来。", "next": "quest_talk", "need": {"quest_pending": "q7_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_guard": {
                "text": "他简短道：『我的职责是守在女王身侧。但林子和王冠是同一张脸——护林，就是护王庭。近来林里不安，我便常出来走，替她把夜的污浊拦在外头。』",
                "options": [
                    {"text": "🗺️ 说说林子里你最得意的巡猎？", "next": "wnd_guard2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_guard2": {
                "text": "他唇角难得一勾：『三百年前那场雾里，我单弓挡下过一队来犯的林影。那是我这辈子最好的一箭——也是我这把弓最亮的一次。……可惜弓现在不在手里了。』",
                "options": [
                    {"text": "📜 那我们去把你的弓带回来。", "next": "quest_talk", "need": {"quest_pending": "q7_6"}},
                    {"text": "🗺️ 那之后呢？", "next": "wnd_guard3"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_guard3": {
                "text": "他别开眼：『雾散了，林子里添了不少坟。月狼的、同伴的、还有我自己的半截年纪。够了，去办正事吧。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_oath": {
                "text": "他抚过月桂哨：『月影卫士的誓是刻在骨里的——不给女王添一件忧愁，不给林子添一道疤。三百年来，我一件件都应了。』",
                "options": [
                    {"text": "🗺️ 那你最放不下的是哪一道疤？", "next": "wnd_scar"},
                    {"text": "📜 我需要任务。", "next": "quest_talk"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_scar": {
                "text": "他沉默片刻：『是那只从小跟我长大的银鬃狼。雾起那夜它替我挡了一箭，倒在我怀里。我捧着它，却救不回它。从那以后我懂了——守林的人，也要守得住自己的手。』",
                "options": [
                    {"text": "🗺️ 你后悔当这个卫士长吗？", "next": "wnd_scar2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_scar2": {
                "text": "他摇头，目光笃定：『不后悔。后悔的，是从没能守住该守的。所以这把月弓、这片林子，我一样都不让撒手。』",
                "options": [
                    {"text": "📜 那我们一起把它们守住。", "next": "quest_talk"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_forest2": {
                "texts": [
                    {"need": {"quest_done": "q9_5"},
                     "text": "瑟兰把一支刻了你名纹的箭递给你：『联军营地那夜，我看见你站在各族中间。你说得对——有些林子，得靠彼此一起守。这支箭，留作当我们盟约的凭证。』"},
                ],
                "text": "他低声道：『月弓回来了，我的心也落回原处。异族的冒险者，你让我这个守了五百年林子的老家伙，头一回觉得——林子之外，也有可以托付后背的人。』",
                "options": [
                    {"text": "🗺️ 那我们之间的约定，会长久吗？", "next": "wnd_forest3"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_forest3": {
                "text": "他难得地笑了一下：『月影卫士的诺可，和这弓弦一样——五百年没断过。你既接下了我这份情，那便也是一辈子的事。』",
                "options": [
                    {"text": "那我收下了。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q7_2"},
                     "text": "瑟兰抽出一支灰皮的箭递给你：『去，把林深处那些狂暴的月狼清一清——能找到源头最好。这支箭染了月桂的汁，能护你一夜不被迷障咬住。』"},
                    {"need": {"quest_pending": "q7_6"},
                     "text": "瑟兰攥紧的拳头青筋绷起：『这把弓跟了我五百年。那些叛逃、投了深渊的暗影精灵，趁疏忽把它偷走了。帮我夺回来——这份情，我月影卫士用一生还你。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "✅ 我去清理月狼。", "next": "q2_accept", "need": {"quest_pending": "q7_2"}, "action": {"quest_take": True}},
                    {"text": "🤔 源头在哪？我怎么找？", "next": "q2_source", "need": {"quest_pending": "q7_2"}},
                    {"text": "🗺️ 这些月狼，以前和你很亲近吗？", "next": "q2_close", "need": {"quest_pending": "q7_2"}},
                    {"text": "✅ 我去会会那些暗影精灵。", "next": "q6_accept", "need": {"quest_pending": "q7_6"}, "action": {"quest_take": True}},
                    {"text": "🤔 他们偷弓……只是为了武器吗？", "next": "q6_why", "need": {"quest_pending": "q7_6"}},
                    {"text": "🗺️ 那把弓，对你到底意味着什么？", "next": "q6_bow", "need": {"quest_pending": "q7_6"}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_accept": {
                "text": "他点头：『月狼好认，眼睛发红的那批就是被污染的。别手软——救不回来的，让它们走得干净些，才是林子的慈悲。』",
                "options": [
                    {"text": "我这就去。", "next": "__end__"},
                ],
            },
            "q2_source": {
                "text": "他指西北：『循着那股咸腥去，越深越浓。源头八成在一处塌陷的旧坟岗边——小心，那里不只月狼。』",
                "options": [
                    {"text": "✅ 我去查个明白。", "next": "q2_accept", "need": {"quest_pending": "q7_2"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q2_close": {
                "text": "他的声音低下去：『有一只额头带伤的银鬃母狼，小时候我救过它，它懂事得会给我叼来野果。要是它也在那批疯了的里头……你就当替我们两个，送它一程。』",
                "options": [
                    {"text": "✅ 我不会让它白死。", "next": "q2_accept", "need": {"quest_pending": "q7_2"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q6_accept": {
                "text": "他眼中难得亮起一线光：『他们躲在西缘的废弃树巢里。五个——都裹着暗影，夜里几乎看不见。带上这支月桂哨，遇到险境吹一声，林里的兄弟会替你挡一箭。』",
                "options": [
                    {"text": "我去去就回。", "next": "__end__"},
                ],
            },
            "q6_why": {
                "text": "他冷笑：『只为给他们的新主子献礼——一把能承载月华的弓，在深渊那边是稀罕的祭品。可他们忘了，月桂只认守林人的手。』",
                "options": [
                    {"text": "✅ 那我把它从祭品里抢回来。", "next": "q6_accept", "need": {"quest_pending": "q7_6"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q6_bow": {
                "text": "他摩挲着腰间的空弓扣：『我握了它五百年，握得手心都有了它的纹路。它若真被献祭，折的不只是弓，是我和这片林子之间那根最细的弦。』",
                "options": [
                    {"text": "✅ 我把那根弦替你接回来。", "next": "q6_accept", "need": {"quest_pending": "q7_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "text": "瑟兰简短道：『事办妥了再来回话。林子的账，我记着呢。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_2"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_6"}},
                    {"text": "🗺️ 月狼清得怎样了？", "next": "adv_q2", "need": {"quest_active": "q7_2"}},
                    {"text": "🗺️ 月弓找到了吗？", "next": "adv_q6", "need": {"quest_active": "q7_6"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q7_2"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q7_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "adv_q2": {
                "text": "『红眼的月狼又多了。你清掉多少，就有更多补上——若那股咸腥的源头还在，这就是无底洞。』",
                "options": [
                    {"text": "✅ 我加快速度。", "next": "__end__"},
                    {"text": "🗺️ 源头到底长什么样？", "next": "adv_q2_src"},
                ],
            },
            "adv_q2_src": {
                "text": "『说不清形状。像一坨会呼吸的烂泥，泛着月华被吸干后的死灰色。你要是真撞见——别恋战，先退，回来告诉我位置。』",
                "options": [
                    {"text": "✅ 我明白了。", "next": "__end__"},
                ],
            },
            "adv_q6": {
                "text": "『弓还在西缘树巢里，暗影精灵守得很紧。别硬冲，先用雾遮身，等他们换哨。』",
                "options": [
                    {"text": "✅ 我这就摸进去。", "next": "__end__"},
                    {"text": "🗺️ 若被发现了怎么办？", "next": "adv_q6_esc"},
                ],
            },
            "adv_q6_esc": {
                "text": "『吹响月桂哨，我的人会引弓掩护你从东侧林窗撤。弓可以再夺，命只有一条。』",
                "options": [
                    {"text": "✅ 我记住了。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q7_2"},
                     "text": "瑟兰看着你带回的消息，眉心的沟壑更深：『红眼的月狼退了……可源头还在林子里发酵。星语湖那边，怕也不太平了。你这一趟，让我看清了森林的伤口有多深。』"},
                    {"need": {"quest_ready": "q7_6"},
                     "text": "失而复得的月弓回到他手中。他抚过弓弦，单膝跪下：『月弓物归原主。从今往后，月影卫士与你的情谊，就像这弓弦一样结实。』"},
                ],
                "options": [
                    {"text": "✅ 收下林子的谢意！", "next": "__end__", "need": {"quest_ready": "q7_2"}, "action": {"quest_take": True}},
                    {"text": "🗺️ 那源头怎么办？", "next": "q2_fix", "need": {"quest_ready": "q7_2"}},
                    {"text": "✅ 收下这五百年的情谊！", "next": "__end__", "need": {"quest_ready": "q7_6"}, "action": {"quest_take": True}},
                    {"text": "🗺️ 你的弓，还有别的故事吗？", "next": "q6_story", "need": {"quest_ready": "q7_6"}},
                ],
            },
            "q2_fix": {
                "text": "他神色凝重：『去星语湖找贤者伊露恩。吸食月华的手法，只在他读过的古籍里出现过——他说得清这是不是深渊的渗透。』",
                "options": [
                    {"text": "✅ 我去星语湖。", "next": "__end__", "need": {"quest_ready": "q7_2"}, "action": {"quest_take": True}},
                ],
            },
            "q6_story": {
                "text": "他站起身，语气难得和缓：『我握着它守了五百年，守的是这片林子，也是它记住的每一个月夜。往后它每晚的月光里，会有一份是你的。』",
                "options": [
                    {"text": "我很荣幸。", "next": "__end__", "need": {"quest_ready": "q7_6"}, "action": {"quest_take": True}},
                ],
            },
        },
    },

    # ==================== 贤者·伊露恩 ====================
    "npc_elf_sage": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q7_5"},
                     "text": "伊露恩合上书卷，推了推镜片，眼里是淡淡的欣慰：『歌谣你听过了，史书你读过了。剩下的谜，在烬山与北境的边界上。——历史记住了你，不只是作为英雄，更是作为真相的见证者。』"},
                    {"need": {"quest_done": "q7_4", "not_quest_done": "q7_5"},
                     "text": "伊露恩指尖轻点泛黄的书页：『证词你已到手。还想再听一段吗？有些真相，不在史书上，在歌谣里。』"},
                    {"need": {"quest_done": "q7_3", "not_quest_done": "q7_4"},
                     "text": "伊露恩轻叹：『星语湖的月华回来了，那缕咸腥却顺着月光渗进了更深处。你若真想找全真相……去看看贤者书房压箱底的那卷吧。』"},
                ],
                "text": "精灵贤者·伊露恩从满架古卷后抬起头，镜片后的目光亮了一下：『啊，一个来听真相的人类。有趣。精灵的史书写的是\"封印加固\"，人类的史书却写着\"魔王伏诛\"——同一个事件，两种记忆。你不觉得，蹊跷得很吗？』",
                "options": [
                    {"text": "🤔 星语湖的月华怎么会枯？", "next": "wnd_lake", "need": {"not_quest_done": "q7_3"}},
                    {"text": "🗺️ \"两种记忆\"，为什么会出现？", "next": "wnd_two", "need": {"not_quest_done": "q7_4"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_3"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_4"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": "q7_5"}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_3"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_4"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_5"}},
                    {"text": "🗺️ 你在读的那卷书，讲的是什么？", "next": "wnd_book"},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_lake": {
                "text": "他合上书：『星语湖是月华的泉眼。有人把水里的月光一滴一滴抽走——这种手法，我只在深渊年代的古籍里见过。那是渗透的记号。』",
                "options": [
                    {"text": "📜 那我替你去星语湖看看。", "next": "quest_talk", "need": {"quest_pending": "q7_3"}},
                    {"text": "🗺️ 深渊……真有那么近吗？", "next": "wnd_lake2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_lake2": {
                "text": "他目光深远：『银月林海的月狼发了狂，星语湖的月华枯了——深渊不在遥远的地下，它正从被遗忘的缝隙里，一点一点渗出来。』",
                "options": [
                    {"text": "📜 我得去查个明白。", "next": "quest_talk", "need": {"quest_pending": "q7_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_two": {
                "text": "他翻开两卷泛黄的史书并排摆开：『同一场战斗，精灵记的是\"加固封印\"，人类记的是\"击杀魔王\"。史官都赌上了性命记录——你猜，谁在手底下改了字？』",
                "options": [
                    {"text": "🤔 那真相在哪里？", "next": "wnd_two2"},
                    {"text": "📜 我需要任务。", "next": "quest_talk"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_two2": {
                "text": "他压低声音：『在两卷不同的记载都不愿提及的那一页。要读到它，得先解了星语湖的毒，再走过贤者书房的尘。一步一步来。』",
                "options": [
                    {"text": "📜 那我如何开始？", "next": "quest_talk", "need": {"quest_pending": "q7_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_book": {
                "text": "他抚过书脊：『这是《月之史诗》的手抄残卷。精灵不烧书，不删字——好让三百年后的读者，自己决定信哪一句。』",
                "options": [
                    {"text": "🗺️ 那这卷里，有关于人类的部分吗？", "next": "wnd_book2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_book2": {
                "text": "他翻到某一页：『有。记载着一个叫艾德里克的凡人，和一道金色身影，如何并肩把裂隙封上。可惜这页缺了一角——缺掉的部分，恐怕在人类的族谱里，被涂成了黑色。』",
                "options": [
                    {"text": "🤔 那金色身影是谁？", "next": "wnd_guardian", "need": {"quest_done": "q7_4"}},
                    {"text": "🤔 那金色身影是谁？", "next": "wnd_guardian", "need": {"quest_done": "q7_5"}},
                    {"text": "📜 我需要任务。", "next": "quest_talk"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "wnd_guardian": {
                "text": "他合上卷，眸色深沉：『人类的史书叫他\"魔王蚀夜\"。精灵的书页上没有写他的名字。守夜者不图名——他只要世人记得，裂隙是他用身躯堵住的。』",
                "options": [
                    {"text": "🎵 再讲点关于他的事吧？", "next": "quest_talk", "need": {"quest_pending": "q7_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q7_3"},
                     "text": "伊露恩将一块吸饱月华的坠饰放你掌中：『湖水的月华被抽走了，罪魁是湖心那头被污染的星语湖王。带着它，月华会替你引路。』"},
                    {"need": {"quest_pending": "q7_4"},
                     "text": "伊露恩递给你一把刻着月桂纹的钥匙：『星语湖的毒解了，可最早的记载在精灵废墟深处的书房里。那卷《月之史诗》被遗弃在塌了一半的廊下，护卫它的古菌兽还在。去把它取回来。』"},
                    {"need": {"quest_pending": "q7_5"},
                     "text": "伊露恩合上《月之史诗》，望向窗外满月：『证词你已读过了。还有一段，不在史书里，在歌谣里——关于那位用身躯堵住深渊之口的守夜者。夜里，月光下，我唱给你听。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "✅ 我去星语湖查个明白。", "next": "q3_accept", "need": {"quest_pending": "q7_3"}, "action": {"quest_take": True}},
                    {"text": "🤔 那湖王为什么会变成那样？", "next": "q3_king", "need": {"quest_pending": "q7_3"}},
                    {"text": "🗺️ 抽走的月华，去了哪里？", "next": "q3_where", "need": {"quest_pending": "q7_3"}},
                    {"text": "✅ 我去精灵废墟取文献。", "next": "q4_accept", "need": {"quest_pending": "q7_4"}, "action": {"quest_take": True}},
                    {"text": "🤔 那卷书为什么这么重要？", "next": "q4_why", "need": {"quest_pending": "q7_4"}},
                    {"text": "🗺️ 废墟里还有什么危险？", "next": "q4_stuff", "need": {"quest_pending": "q7_4"}},
                    {"text": "🎵 我想听。", "next": "q5_accept", "need": {"quest_pending": "q7_5"}, "action": {"set_flag": "know_guardian", "quest_take": True}},
                    {"text": "🤔 为什么歌谣不在史书里？", "next": "q5_why", "need": {"quest_pending": "q7_5"}},
                    {"text": "🗺️ 守夜者……是谁？", "next": "q5_who", "need": {"quest_pending": "q7_5"}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q3_accept": {
                "text": "他点头：『湖王被月华的枯竭逼疯了。击败它，让湖面重新泛起光——那缕咸腥，也会在月光清理后现出真身。』",
                "options": [
                    {"text": "我这就去。", "next": "__end__"},
                ],
            },
            "q3_king": {
                "text": "他推了推镜片：『污染先夺走了月华，再夺走了它的理智。星辰湖王本只是湖灵的化身——如今它成了深渊的哨兵。击败它，等于把哨兵的灯先吹灭了。』",
                "options": [
                    {"text": "✅ 那我们先把灯吹灭。", "next": "q3_accept", "need": {"quest_pending": "q7_3"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q3_where": {
                "text": "他望向北方，目光沉定：『抽走月华的手，不在这座湖里。它在更深处——顺着那股咸腥的根一路追下去，终点多半是一座被遗忘的祭坛。先解星语湖，再谈它的去处。』",
                "options": [
                    {"text": "✅ 我记住了。", "next": "q3_accept", "need": {"quest_pending": "q7_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q4_accept": {
                "text": "他眼神郑重：『那卷书里，写的是四百年前烬山之战的另一页。护卫它的古菌兽只认月桂信物——你身上那缕月华，足以让它安静下来。把书带回来，我为你读它。』",
                "options": [
                    {"text": "我去去就回。", "next": "__end__"},
                ],
            },
            "q4_why": {
                "text": "他深吸一口气：『因为那里头，记着教会三百年不敢让世人看见的东西——封印真正的结构，以及维持它，需要付出什么代价。』",
                "options": [
                    {"text": "✅ 那我们必须把它带回来。", "next": "q4_accept", "need": {"quest_pending": "q7_4"}},
                    {"text": "❌ 再想想。", "next": "welcome"},
                ],
            },
            "q4_stuff": {
                "text": "『废墟里沉积着百年的尘与雾，还有几头守门的古菌兽。别硬撼——用月华安抚它们。运气好的话，一本书，你一根毫毛都不必少地背回来。』",
                "options": [
                    {"text": "✅ 我记下了。", "next": "q4_accept", "need": {"quest_pending": "q7_4"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_accept": {
                "text": "他取出一支无弦的木笛，月光落在琴弦上：『那你听好了。这首《守夜者之歌》，是精灵祖辈在烬山篝火旁传下来的。人类把它改成了\"魔王伏诛\"——可歌谣记得的，是那个挡在裂隙前的身影。』",
                "options": [
                    {"text": "我听着。", "next": "__end__"},
                ],
            },
            "q5_why": {
                "text": "他轻声：『因为史书要留名，歌谣只要让夜里的人记得有人守过。守夜者选了后者——他不需要名字，他只需要裂隙不再吞没人。』",
                "options": [
                    {"text": "🎵 那我更要听这首歌。", "next": "q5_accept", "need": {"quest_pending": "q7_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_who": {
                "text": "他目光深远：『守夜者，是父神留在世间的守望人，看守这世界那道伤口的影子。人类叫他\"魔王蚀夜\"——那是教会亲手涂黑的名字。』",
                "options": [
                    {"text": "🎵 请唱给我听。", "next": "q5_accept", "need": {"quest_pending": "q7_5"}},
                    {"text": "🗺️ 他还守着那个伤口吗？", "next": "q5_now", "need": {"quest_pending": "q7_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_now": {
                "text": "他叹了口气：『三百年来，他一直在。只是世人都忘了，那道被堵住三百年、如今又开始渗水的裂隙，正是他用自己的身躯压着的那一道。』",
                "options": [
                    {"text": "🎵 我想去见他。", "next": "q5_accept", "need": {"quest_pending": "q7_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "text": "伊露恩抬了抬镜片：『有些证词要等。你办妥的事，回来与我对一遍旁的页码。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_3"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_4"}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q7_5"}},
                    {"text": "🗺️ 星语湖王解决了吗？", "next": "adv_q3", "need": {"quest_active": "q7_3"}},
                    {"text": "🗺️ 书房里的书取回来了吗？", "next": "adv_q4", "need": {"quest_active": "q7_4"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q7_3"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q7_4"}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": "q7_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "adv_q3": {
                "text": "『湖心的浪还泛着死灰色，说明湖王仍未退。月华在往一处汇聚——循着那点亮走，就能找到它。』",
                "options": [
                    {"text": "✅ 我继续找它。", "next": "__end__"},
                    {"text": "🗺️ 月华在往哪边聚？", "next": "adv_q3_dir"},
                ],
            },
            "adv_q3_dir": {
                "text": "『朝西偏南，那片水最黑的地方。小心湖面的倒影——深渊善用倒影骗人。』",
                "options": [
                    {"text": "我记住了。", "next": "__end__"},
                ],
            },
            "adv_q4": {
                "text": "『废墟的廊下，书还压在塌方边。古菌兽守着它，见你持月华应会退避——若恼了，就退出廊，等雾散再进。』",
                "options": [
                    {"text": "✅ 我再去一趟。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q7_3"},
                     "text": "伊露恩望着重新泛起月华的湖面，神色凝重：『星语湖王倒下，月华回来了——可那一缕咸腥的根，还顺着月光渗向别处。深渊的手，已经伸到了精灵的家门口。』"},
                    {"need": {"quest_ready": "q7_4"},
                     "text": "伊露恩翻开泛黄的书页，指尖在一个词上一顿，抬眸看你：『你看，这里写着——\"余烬元年，人类英雄王艾德里克与守夜者蚀夜联手，加固深渊裂隙之封印\"。而人类的史书写的是——\"英雄王艾德里克击杀魔王蚀夜\"。』他轻声：『同一个事件，两种记忆。』"},
                    {"need": {"quest_ready": "q7_5"},
                     "text": "歌声在月光下飘散。伊露恩望着你：『歌谣的旋律记住了吗？人类的史书把守夜者写成魔王，可歌谣里唱的，是那个用身躯堵住深渊之口的身影。』他郑重道：『孩子，你该去北境看看了——那里有答案，也有危险。』"},
                ],
                "options": [
                    {"text": "✅ 收下学者的谢意！", "next": "__end__", "need": {"quest_ready": "q7_3"}, "action": {"quest_take": True}},
                    {"text": "🤔 那我们下一步怎么办？", "next": "q3_next", "need": {"quest_ready": "q7_3"}},
                    {"text": "✅ 收下这卷真相！", "next": "__end__", "need": {"quest_ready": "q7_4"}, "action": {"quest_take": True}},
                    {"text": "🤔 那……维持封印的代价是什么？", "next": "q4_cost", "need": {"quest_ready": "q7_4"}},
                    {"text": "🌙 收下这段歌谣！", "next": "__end__", "need": {"quest_ready": "q7_5"}, "action": {"quest_take": True}},
                    {"text": "🤔 守夜者现在还在守着吗？", "next": "q5_still", "need": {"quest_ready": "q7_5"}},
                ],
            },
            "q3_next": {
                "text": "他指尖轻点堆满灰的古籍柜：『要弄懂深渊从那道缝隙渗进来多少，就得翻翻最早的那本记载。贤者书房里，还压着一卷四百年前的《月之史诗》。』",
                "options": [
                    {"text": "✅ 我去取那卷书。", "next": "__end__", "need": {"quest_ready": "q7_3"}, "action": {"quest_take": True}},
                ],
            },
            "q4_cost": {
                "text": "他垂下眼帘，声音罕见地发沉：『这卷书最后一页写着：\"封印所需圣光，须以圣光容器之生命为祭，每百年一祭。\"孩子，你确定要知道吗？』",
                "options": [
                    {"text": "✨ 告诉我，让我自己决定。", "next": "q4_cost2", "action": {"set_flag": "know_seal_cost"}},
                    {"text": "🤔 我……再想想。", "next": "quest_done_talk"},
                ],
            },
            "q4_cost2": {
                "text": "他翻开最后一页，字迹随着他的话语清晰起来：『历代圣女的\"病逝\"，不是天命，是祭。教会用谎言维持了三百年，为的就是每百年续上这一盏灯。而你身后的她——是下一个容器。』",
                "options": [
                    {"text": "🕯️ 我不会让她走上那条路。", "next": "q4_resolve", "need": {"quest_ready": "q7_4"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q4_resolve": {
                "text": "他合上书，望着你许久：『那你要找到另一条路。去烬山之下的真相里找，去北境的烽火里找。书读完了，路要你走。』",
                "options": [
                    {"text": "✅ 我去找一条不一样的路。", "next": "__end__", "need": {"quest_ready": "q7_4"}, "action": {"quest_take": True}},
                ],
            },
            "q5_still": {
                "text": "他望向遥远的烬山方向：『他在。只要裂隙还渗着水，那道金色身影就不会离开。去吧——北境冰川下有他要你带去的消息。』",
                "options": [
                    {"text": "✅ 那我去北境。", "next": "__end__", "need": {"quest_ready": "q7_5"}, "action": {"quest_take": True}},
                ],
            },
        },
    },
}
