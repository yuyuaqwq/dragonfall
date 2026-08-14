# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - dialogues.py

NPC 多轮对话树（v65）。

设计（可扩展）：
- DIALOGUES[npc_id] = {"start": 起始节点ID, "nodes": {节点ID: 节点}}
- 节点 = {"text": 台词, "options": [选项...]}
- 选项 = {"text": 选项文本, "next": 目标节点ID 或 "__end__",
          "need": 可选条件 dict, "action": 可选动作 dict}
- 条件 need（全部满足才显示该选项）：
-    {"quest_done": ""}        当前主线已完成（qid 为空 = 按“当前主线”动态判断）
-    {"quest_pending": ""}     当前主线待接取（动态；且校验发布者 == 对话 NPC，见 core/dialogue_conds.py v101.23）
-    {"quest_active": ""}      当前主线进行中（active/ready）
-    {"quest_ready": ""}       当前主线待交付（ready）
{"quest_done": "q1_1"}    指定主线 q1_1 已完成（静态 id 写法）
- 动作 action（选中后执行，返回通知行）：
    {"set_flag": "xxx"}         设置对话 flag（持久，彩蛋解锁用）
    {"give_gold": 50}           给金币
    {"give_exp": 100}           给经验
    {"give_item": {"key": "狼皮", "count": 2}}   给物品（key 支持中文名/ID）
    {"open_shop": True}         提示打开商店
"""
DIALOGUES = {
    # ==================== 橡木镇 ====================
    "npc_mayor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                # v101.23：texts 条件变体——q1_1 完成后不再念史莱姆开场白
                "texts": [
                    {"need": {"quest_done": "q1_1"},
                     "text": "哦，是你啊，冒险者！麦田的事多亏了你，镇子总算清净了。最近有什么新鲜事吗？"},
                ],
                "text": "年轻人，你来得正是时候。最近镇子草地的史莱姆越来越猖狂，把我家麦田拱得不成样子。",
                "options": [
                    {"text": "史莱姆是怎么回事？", "next": "dogs", "need": {"not_quest_done": "q1_1"}},
                    {"text": "镇长，镇子最近还好吗？", "next": "town"},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "dogs": {
                # v101.23：台词变体——q1_1 完成后不再讲史莱姆（入口已隐藏，兜底防会话残留）
                "texts": [
                    {"need": {"quest_done": "q1_1"},
                     "text": "史莱姆那事儿早就了结了，麦田也清净了。倒是你，最近有什么新鲜事吗？"},
                ],
                "text": "唉，那些黏糊糊的绿家伙是入秋之后从西边草地渗过来的，专拱麦田，越打越多。庄稼汉们试着清了几次，可它们怎么都除不尽。",
                "options": [
                    {"text": "我这就去解决它们！", "next": "dogs_pledge", "action": {"set_flag": "pledged"}, "need": {"not_quest_done": "q1_1"}},
                    {"text": "麦田损失大吗？", "next": "dogs_trade", "need": {"not_quest_done": "q1_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "dogs_pledge": {
                "text": "好样的！镇子西边的草地就是它们的老窝。替我把它们清干净，镇子不会亏待你的。",
                "options": [
                    {"text": "包在我身上！", "next": "quest_accept", "need": {"quest_pending": ""}, "action": {"quest_take": True}},
                    # v104 M21 P2：入口只需 not_quest_done:q1_1，q1_1 进行中/待交付时
                    # 原唯一选项 quest_pending 不满足 → 无可视选项死路；补兜底选项
                    {"text": "任务在身，先把委托办完再回来。", "next": "__end__", "need": {"quest_active": "q1_1"}},
                    {"text": "任务办妥了，先去交付再回来。", "next": "__end__", "need": {"quest_ready": "q1_1"}},
                ],
            },
            "dogs_trade": {
                "text": "我那两亩麦田眼瞅着要收成了，被拱得七零八落。再这么下去，入冬的口粮怕是凑不齐了……",
                "options": [
                    {"text": "我这就去解决它们！", "next": "dogs_pledge", "action": {"set_flag": "pledged"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "town": {
                "text": "镇子还算太平，多亏了铁匠托尔那把好锤子，还有橡木桶旅店的麦酒——大伙儿晚上有个地方松快松快。对了，城门口那位吟游诗人莉莉，最近老念叨什么'隧洞之王'，你感兴趣可以去听听。",
                "options": [
                    {"text": "史莱姆是怎么回事？", "next": "dogs", "need": {"not_quest_done": "q1_1"}},
                    {"text": "我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                # v101.23：接取台词按当前主线切换（镇长发的任务不止史莱姆）
                # v101.23d：默认走 text_from story——无变体匹配时自动用当前主线 story 台词
                "texts": [
                    {"need": {"quest_pending": "q1_3"},
                     "text": "正好！西边林子里的野猪越来越猖狂，把麦田拱得不成样子。帮我料理一下，镇子不会亏待你的。"},
                    {"need": {"quest_pending": "q1_4"},
                     "text": "白鹿城方向有伤兵逃回来，说哥布林在集结！帮我去溪谷查探一下，镇子不会亏待你的。"},
                    {"need": {"quest_pending": "q1_6"},
                     "text": "来来来，坐下陪老头子喝一杯！我年轻时也有过不少冒险故事，正好讲给你听。"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "交给我了！", "next": "quest_accept", "action": {"set_flag": "quest_hint", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "quest_status": {
                # v95.9：对话式接取/交付引导（取代『交任务』『接取任务』指令文案）
                "text": "冒险日志我都记着呢——任务办妥了，回来跟我说一声就成；想接新任务，也尽管开口。『任务』能随时看进度。",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "好，我知道了。", "next": "__end__"},
                ],
            },
            "quest_accept": {
                "text": "好样的！具体目标都在冒险日志里，办妥了回来找我就行。",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                # v101.23：交付台词按当前主线切换
                "texts": [
                    {"need": {"quest_ready": "q1_3"},
                     "text": "野猪料理干净了？哈哈哈，干得漂亮！林子里的庄稼汉总算能睡个安稳觉了。这是你应得的报酬！"},
                    {"need": {"quest_ready": "q1_4"},
                     "text": "溪谷那边的情况摸清了？好！有你这句话，镇上的人心就定了。这是你应得的报酬！"},
                    {"need": {"quest_ready": "q1_6"},
                     "text": "哈哈哈，麦酒管够！来，这是老头子的一点心意，收下吧！"},
                ],
                "text": "你回来了！麦田总算保住了，镇子欠你一个大人情。来吧，这是你应得的报酬！",
                "options": [
                    {"text": "收下报酬！", "next": "__end__", "action": {"quest_take": True}},
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
                "text": "不是我吹牛，橡木镇的铁匠铺虽然小，但每一把剑都是我亲手打的。别拿城里那些流水线货跟我们比！",
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
    "npc_innkeeper": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "累了吧？在橡木桶旅店歇一晚，保你明天生龙活虎！",
                "options": [
                    {"text": "住一晚。", "next": "stay", "action": {"hint": "输入『住宿』恢复满血(需要金币)"}},
                    {"text": "最近有奇怪的客人吗？", "next": "gossip"},
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "✅ 任务办妥了！", "next": "quest_done", "need": {"quest_ready": ""}},
                    {"text": "✅ 有东西要交给你。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
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
                    {"text": "住一晚。", "next": "stay", "action": {"hint": "输入『住宿』恢复满血(需要金币)"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                # v101.25i：玛莎主线接取入口（q1_5 迷路的猫）——text_from story 自动取当前主线台词
                "text_from": "story",
                "options": [
                    {"text": "交给我了！", "next": "quest_accept", "action": {"set_flag": "quest_hint", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "quest_accept": {
                "text": "好样的！具体目标都在冒险日志里，办妥了回来找我就行。",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            # v105 M19 P3：q1_5 迷路的猫交付台词节点——此前 quest_ready 直接 __end__+quest_take，
            # 交付零 NPC 台词（只回奖励行），现与其他主线 giver（quest_done_talk）对齐
            "quest_done": {
                "text": "『麦酒』！你可算把它找回来了！来，鱼汤炖上了，趁热喝！",
                "options": [
                    {"text": "收下报酬！", "next": "__end__", "action": {"quest_take": True}},
                ],
            },
        },
    },
    "npc_bard": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                # v101.23c：q8_3 矿洞剧情结束后，传闻更新（不再唱"矿洞被地精占了"）
                "texts": [
                    {"need": {"quest_done": "q8_3"},
                     "text": "听说了吗？矮人那边的矿洞闹腾了那么久，总算消停了。不过那'隧洞之王'的传说还在流传……"},
                ],
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
    # ==================== 石拳丘陵 ====================
    "npc_dwarf_elder": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                # v101.23c：q8_3 铁砧会议完成后不再喊"夺回矿洞"（矿洞剧情已翻篇）
                "texts": [
                    {"need": {"quest_done": "q8_3"},
                     "text": "哈哈，老朋友来了！矿洞的事你功不可没，矮人们都记在心里呢。"},
                ],
                "text": "地精那群小崽子霸占了我们的矿洞！勇士，帮我们把矿洞夺回来，矮人的友谊和商店都给你！",
                "options": [
                    {"text": "矿洞里情况怎么样？", "next": "situation"},
                    {"text": "地精为什么要占矿洞？", "next": "why"},
                    {"text": "看看矮人的货。", "next": "shop", "action": {"open_shop": True}},
                    {"text": "📜 我能帮上什么忙？", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "✅ 任务办妥了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                # v101.23c：接取台词按当前主线切换（长老不止矿洞一个任务）
                # v101.23d：默认走 text_from story——q8_3 时自动用铁砧会议 story
                "texts": [
                    {"need": {"quest_pending": "q8_5"},
                     "text": "托尔丁那小子急得跳脚——祖传的酒桶被偷了！那是矮人的传世之宝，帮我找回来！"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "交给我了！", "next": "quest_accept", "action": {"set_flag": "quest_hint", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "quest_accept": {
                "text": "好样的！具体目标都在冒险日志里，办妥了回来找我就行。",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "text": "哈哈哈！矮人从不亏待朋友，这是你应得的报酬！",
                "options": [
                    {"text": "收下报酬！", "next": "__end__", "action": {"quest_take": True}},
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
                "text": "矮人锻造的货，大陆上最好的！钱货两讫，童叟无欺！",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 赤脊荒原 ====================
    # ==================== 黑石城废墟 ====================
    # ==================== 风暴之巅 ====================
    # ==================== 远境城（后期区域） ====================
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
                    {"text": "止血草", "need": {"not_apprentice": "gather"}, "next": "practice_intro"},
                    {"text": "毒蘑菇", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "荆棘叶", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "gather"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "艾琳笑着摇头：再想想，采错药可是要出人命的。哪种草能治伤口？",
                "options": [
                    {"text": "止血草", "need": {"not_apprentice": "gather"}, "next": "practice_intro"},
                    {"text": "毒蘑菇", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "荆棘叶", "need": {"not_apprentice": "gather"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "practice_intro": {
                "text": "不错，有点天分。不过光会认不行——去橡木平原采 3 份草药回来给我看看。",
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
                "text": "好！从今天起你就是我的学徒了。这几份草药送给你，好好学！",
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
                # v101.25 #327：拜师后不再展示入门问答——apprentice 满足时切师傅日常
                "texts": [
                    {"need": {"apprentice": "mining"}, "text": "巴尔金灌了口酒，拍了拍你的肩：好小子！矿洞里的动静我都听着呢，缺铁矿石来我这拿，别跟我客气。"},
                    {"need": {}, "text": "挖矿跟喝酒一样，讲究一个痛快！想拜师学挖掘，先回答我——什么矿石最坚硬？"},
                ],
                "options": [
                    {"text": "源质", "need": {"not_apprentice": "mining"}, "next": "practice_intro"},
                    {"text": "铁矿石", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "秘银", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "mining"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "巴尔金灌了口烈酒：哈哈哈，再想想！越往地下走，好东西越硬！",
                "options": [
                    {"text": "源质", "need": {"not_apprentice": "mining"}, "next": "practice_intro"},
                    {"text": "铁矿石", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "秘银", "need": {"not_apprentice": "mining"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "practice_intro": {
                # v101.25 #318/#319：指引矿洞方位（山丘矿洞·南境绿野）+ 商店兜底买矿，
                # 修复"没挖掘技能挖不了矿"的拜师死锁（playtest round68 小红实锤）
                "text": "有点眼力！去矿洞挖 5 份铁矿石回来，让我看看你的力气。矿脉在南境绿野的山丘矿洞（Lv.18 野区，『前往 山丘矿洞』）——没把握的话，铁港城海风锻造坊也能买到铁矿石，就看你的钱包厚不厚了！",
                "options": [
                    {"text": "这就去", "next": "practice_check"},
                    {"text": "先告辞", "next": "__end__"},
                ],
            },
            "practice_check": {
                # v101.25 #328：接取后先引导挖矿——选项文本不直接给"交付"，而是
                # 先问准备情况；material 型考验校验仍走 apprentice_check（下方交付选项）
                "text": "矿挖得怎么样了？凑齐 5 份铁矿石才够我看你的力气。",
                "options": [
                    {"text": "铁矿石挖够了，请过目", "next": "master_intro", "action": {"apprentice_check": {"item": "铁矿石", "count": 5}}, "fail_next": "practice_wait"},
                    {"text": "还没挖够，先去矿洞", "next": "practice_wait"},
                ],
            },
            "practice_wait": {
                # v101.25 #328/#319：没矿时的引导带方位+商店兜底（此前只说"再挖"）
                "text": "巴尔金摇头：不够不够！山丘矿洞（南境绿野 Lv.18，『前往 山丘矿洞』）里还能挖到，实在不行去铁港城海风锻造坊买几块，别空手回来。",
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
                "text": "好小子！从今天起你就是矿工行会的人了。这几块铁矿石拿好，别丢矿工的脸！",
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
                    {"text": "夜光鲛", "need": {"not_apprentice": "fishing"}, "next": "practice_intro"},
                    {"text": "银鳞鱼", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "金鲤", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "fishing"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "马库斯望着海面，轻声说：夜里才出来的鱼，身上带着光……再想想。",
                "options": [
                    {"text": "夜光鲛", "need": {"not_apprentice": "fishing"}, "next": "practice_intro"},
                    {"text": "银鳞鱼", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "金鲤", "need": {"not_apprentice": "fishing"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
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
                "text": "……行，你过关了。这两条银鳞鱼送你。以后潮起潮落，鱼都在那里等你。",
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
                    {"text": "兽肉", "need": {"not_apprentice": "cooking"}, "next": "practice_intro"},
                    {"text": "草药", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "面粉", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "cooking"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "罗莎叉腰大笑：哈哈哈，那玩意儿能烤吗！再想想！",
                "options": [
                    {"text": "兽肉", "need": {"not_apprentice": "cooking"}, "next": "practice_intro"},
                    {"text": "草药", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "面粉", "need": {"not_apprentice": "cooking"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "practice_intro": {
                "text": "有悟性！给我收集 2 份兽肉来，当今天的食材。",
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
                "text": "行，收你当徒弟！这两份兽肉送你，好好练手艺！",
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
                    {"text": "草药", "need": {"not_apprentice": "alchemy"}, "next": "practice_intro"},
                    {"text": "矿石", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "羽毛", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "alchemy"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "梅尔文冷笑：啧，连这都不知道，还想碰烧瓶？再想想。",
                "options": [
                    {"text": "草药", "need": {"not_apprentice": "alchemy"}, "next": "practice_intro"},
                    {"text": "矿石", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "羽毛", "need": {"not_apprentice": "alchemy"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "practice_intro": {
                "text": "哼，勉强算你答对了。去收集 3 份草药来，我要看看你的材料鉴别能力。\n（草药：野外『探索』遇『🌿 草药丛』可采，橡木平原/白鹿森林/银铃河一带常有）",
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
                "text": "哼，这点材料都凑不齐，还想当炼金术士？",
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
                "text": "……行，收你了。这两个空瓶拿去，别炸了我的工房。",
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
    # ---------- 锻造·铁匠大师奥格（铁港城） ----------
    "npc_craft_master": {
        "start": "ask",
        "nodes": {
            "ask": {
                # v101.25 #327：拜师后不再展示入门问答——apprentice 满足时切师傅日常
                "texts": [
                    {"need": {"apprentice": "craft"}, "text": "奥格抡着锤子忙得满头汗，见你来了咧嘴一笑：来得正好！缺材料就说，锻造铺子的火候我盯着呢。"},
                    {"need": {}, "text": "打铁，凭的是手和心。想拜师学锻造，先回答我——锻造装备需要什么？"},
                ],
                "options": [
                    {"text": "图纸+材料", "need": {"not_apprentice": "craft"}, "next": "practice_intro"},
                    {"text": "只有材料", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "只有金币", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "craft"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "奥格敲了敲铁砧：没有图纸，材料就是废铁！再想想。",
                "options": [
                    {"text": "图纸+材料", "need": {"not_apprentice": "craft"}, "next": "practice_intro"},
                    {"text": "只有材料", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "只有金币", "need": {"not_apprentice": "craft"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
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
                "text": "好，从今天起你就是我的学徒了。这几块铁矿石拿去练练手，别砸了我的招牌！",
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
                "text": "强化是门生意，也是门赌术。想拜师学强化，先回答我——＋6 以上强化失败会怎样？",
                "options": [
                    # F4 P1-1：问答判定反转修复——机制 ENHANCE_FAIL_DROP={5:2,6:1,7:1,8:1}，
                    # ＋6 以上失败只掉 1 级 → 「降 1 级」为正确答案
                    {"text": "降 2 级", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "降 1 级", "need": {"not_apprentice": "enhance"}, "next": "practice_intro"},
                    {"text": "装备消失", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "enhance"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "克拉拉拨着算盘：＋6 以上失败只掉 1 级，＋5 失败才掉 2 级。再想想。",
                "options": [
                    # F4 P1-1：与 ask 节点同步反转（纠错台词已对齐 ENHANCE_FAIL_DROP 机制）
                    {"text": "降 2 级", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "降 1 级", "need": {"not_apprentice": "enhance"}, "next": "practice_intro"},
                    {"text": "装备消失", "need": {"not_apprentice": "enhance"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
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
                    {"text": "魔攻", "need": {"not_apprentice": "enchant"}, "next": "practice_intro"},
                    {"text": "攻击", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "速度", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "随便聊聊", "next": "chat", "need": {"apprentice": "enchant"}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ask_wrong": {
                "text": "吉姆利敲着符文石：法师靠魔力吃饭，附魔也得顺着力量走。再想想。",
                "options": [
                    {"text": "魔攻", "need": {"not_apprentice": "enchant"}, "next": "practice_intro"},
                    {"text": "攻击", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "速度", "need": {"not_apprentice": "enchant"}, "next": "ask_wrong"},
                    {"text": "告辞。", "next": "__end__"},
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
                    {"text": "谢吉姆利大师！", "next": "chat", "action": {"unlock_prof": "enchant", "give_prof_exp": 50, "give_item": {"key": "符文石", "count": 1}}},
                    {"text": "告辞", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "吉姆利低语：符文刻在石上，也刻在心里。多听大地母神的话。",
                "options": [{"text": "告辞", "next": "__end__"}],
            },
        },
    },
    # ==================== v87 隐藏职业：魔剑士残魂（H6 失落图书馆）====================
    # v113：魔剑士流派已舍弃，此处仅存背景 lore
    "npc_spellblade_ghost": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "虚影凝实，一柄锈剑缓缓抬起——『三百年了……终于有人带着信物走进这里。你想听这段往事吗？』",
                "options": [
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "魔剑士是什么？", "next": "lore"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "lore": {
                "text": "『三百年前，我以剑与魔法同魔龙一战。那是我一个人的道路——如今剑仍在，路已断。后辈啊，去走你自己的路吧。』",
                "options": [
                    {"text": "受教了。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== 野外 NPC ====================
    "w_sage_ryder": {
        "start": "greet",
        "nodes": {
            "greet": {
                "text": "(头也不抬)……这里不是观光的林子。你是迷路了，还是专程来找我的？",
                "options": [
                    {"text": "听闻您是位剑术大师，想请教一二。", "next": "sword"},
                    {"text": "您为什么隐居在这里？", "next": "why"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "sword": {
                "text": "(他放下手中擦拭的剑，抬眼看你)剑术？呵……剑不是用来炫耀的。握剑之前，先学会握紧自己的心。你若勤加历练，剑术自会精进——滚吧，别让我说第二遍。",
                "options": [
                    {"text": "受教了，告辞。", "next": "__end__"},
                ],
            },
            "why": {
                "text": "江湖恩怨，说来话长。我这条命是从剑下捡回来的，如今只想在这林子里等一场雪。……你若无事，便去吧。",
                "options": [
                    {"text": "那就不打扰您了。", "next": "__end__"},
                ],
            },
        },
    },
    # ==================== v95.23 职业就职（冒险者行会·小艾） ====================
    "npc_guild_clerks": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "欢迎来到冒险者行会！新人就职登记，我这就给你办。想成为什么样的冒险者？",
                "options": [
                    {"text": "🛡️ 战士——钢铁壁垒，正面硬刚", "next": "confirm_cls_zhan_shi", "need": {"is_novice": True}},
                    {"text": "🔮 法师——元素与奥术的掌控者", "next": "confirm_cls_fa_shi", "need": {"is_novice": True}},
                    {"text": "🏹 游侠——百步穿杨的猎手", "next": "confirm_cls_you_xia", "need": {"is_novice": True}},
                    {"text": "📖 牧师——圣光的信徒与医者", "next": "confirm_cls_mu_shi", "need": {"is_novice": True}},
                    {"text": "🗡️ 刺客——阴影中的利刃", "next": "confirm_cls_ci_ke", "need": {"is_novice": True}},
                    {"text": "🥋 拳师——以拳证道的武斗家", "next": "confirm_cls_wu_seng", "need": {"is_novice": True}},
                    {"text": "我已经就职过了，随便聊聊", "next": "chat", "need": {"not_novice": True}},
                    # v105 O61：welcome 首屏直达交付选项——此前交付入口在 chat 二级菜单，
                    # 功能提示行"✅ 主线达成！和他对话交付领奖～"引导玩家点『我已经就职过了』
                    # 才能看到交付选项，易误判卡死（round104 B8 误报根因）
                    {"text": "✅ 任务办妥了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    # v104 M21 P2：见习玩家在就职前也能对话接取 q1_2（此前任务选项
                    # 只在 chat 节点、需 not_novice，见习期=死路，只能先就职再接任务）
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "confirm_cls_zhan_shi": {"text": "战士？好眼光！铁盾在前，生死在后。确定就职为战士吗？", "options": [{"text": "确定！", "next": "joined", "action": {"unlock_class": "cls_zhan_shi"}}, {"text": "再想想", "next": "welcome"}]},
            "confirm_cls_fa_shi": {"text": "法师？记住，魔法是理解世界的语言，不是炫耀的把戏。确定就职为法师吗？", "options": [{"text": "确定！", "next": "joined", "action": {"unlock_class": "cls_fa_shi"}}, {"text": "再想想", "next": "welcome"}]},
            "confirm_cls_you_xia": {"text": "游侠？风会指引你的箭。确定就职为游侠吗？", "options": [{"text": "确定！", "next": "joined", "action": {"unlock_class": "cls_you_xia"}}, {"text": "再想想", "next": "welcome"}]},
            "confirm_cls_mu_shi": {"text": "牧师？圣光不偏袒任何人，只照亮前行的人。确定就职为牧师吗？", "options": [{"text": "确定！", "next": "joined", "action": {"unlock_class": "cls_mu_shi"}}, {"text": "再想想", "next": "welcome"}]},
            "confirm_cls_ci_ke": {"text": "刺客？……你听到的只是风声。确定就职为刺客吗？", "options": [{"text": "确定！", "next": "joined", "action": {"unlock_class": "cls_ci_ke"}}, {"text": "再想想", "next": "welcome"}]},
            "confirm_cls_wu_seng": {"text": "拳师？拳打千遍，其义自见。确定就职为拳师吗？", "options": [{"text": "确定！", "next": "joined", "action": {"unlock_class": "cls_wu_seng"}}, {"text": "再想想", "next": "welcome"}]},
            "joined": {
                "text": "行会登记完毕！铁牌是你的了——从今天起，你就是一名正式的冒险者。",
                "options": [
                    {"text": "多谢接待员！", "next": "__end__"},
                ],
            },
            "chat": {
                "text": "行会每天都有新委托，冒险者的故事永远不会结束。要接委托就找镇长，想学本事就去各城寻访职业导师。",
                "options": [
                    {"text": "📜 行会有任务委托吗？", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "✅ 任务办妥了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                # v105 M19 P3：接取台词跟随当前主线 story（q1_2 行会入门：铁牌欢迎词），
                # 与镇长/玛莎/矮人长老一致——此前写死"行会刚贴出一份委托"与 q1_2 story 冲突
                "text_from": "story",
                "options": [
                    {"text": "交给我了！", "next": "quest_accept", "action": {"set_flag": "quest_hint", "quest_take": True}},
                    {"text": "再想想。", "next": "chat"},
                ],
            },
            "quest_accept": {
                "text": "好样的！具体目标都在冒险日志里，办妥了回来找我就行。",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "text": "干得漂亮！行会为你的名字记了一笔，这是你应得的报酬！",
                "options": [
                    {"text": "收下报酬！", "next": "__end__", "action": {"quest_take": True}},
                ],
            },
        },
    },
    # ==================== v95.23 职业导师（进阶技能 + 转职） ====================
    "npc_warrior_tutor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "战场上的每一步都是用血换来的。想学真本事，先接我三板斧。",
                "options": [
                    {"text": "请教『破甲斩』(Lv.8 · 800金)", "next": "teach_po_jia", "need": {"class_any": ["cls_zhan_shi"]}},
                    {"text": "请教『战吼』(Lv.3 · 1500金)", "next": "teach_zhan_hou", "need": {"class_any": ["cls_zhan_shi"]}},
                    {"text": "🌟 我想转职！", "next": "evolve_t1", "need": {"class_any": ["cls_zhan_shi"], "evolve_ready": {"tier": 0, "level": 30}}},
                    {"text": "🌟 我想继续转职！", "next": "evolve_t2", "need": {"class_any": ["cls_zhan_shi"], "evolve_ready": {"tier": 1, "level": 60}}},
                    {"text": "🌟 我想进行最终转职！", "next": "evolve_t3", "need": {"class_any": ["cls_zhan_shi"], "evolve_ready": {"tier": 2, "level": 90}}},
                    {"text": "随便聊聊", "next": "chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "teach_po_jia": {"text": "破甲斩——战场上最实用的起手式。学费 800 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "破甲斩", "cost": 800, "need_lv": 6}}}, {"text": "下次再说", "next": "welcome"}]},
            "teach_zhan_hou": {"text": "战吼——一声怒吼，士气如虹。学费 1500 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "战吼", "cost": 1500, "need_lv": 10}}}, {"text": "下次再说", "next": "welcome"}]},
            "evolve_t1": {"text": "Lv.30 的战士，够格了！狂战士以攻代守，盾卫士坚如磐石。选一条路吧。", "options": [{"text": "转职为狂战士（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 1}}}, {"text": "转职为盾卫士（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 2}}}]},
            "evolve_t2": {"text": "Lv.60！向更高处走：狂战统领还是坚盾卫士？", "options": [{"text": "转职为狂战统领（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 1}}}, {"text": "转职为坚盾卫士（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 2}}}]},
            "evolve_t3": {"text": "Lv.90，战士的终点：战争领主，或坚城统帅。", "options": [{"text": "转职为战争领主（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 1}}}, {"text": "转职为坚城统帅（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 2}}}]},
            "evolved": {"text": "好！战士的道路，还远着呢。去把名字刻在战场上传颂吧。", "options": [{"text": "多谢导师！", "next": "__end__"}]},
            "taught": {"text": "回去好好练，别给战士丢脸。", "options": [{"text": "告辞。", "next": "__end__"}]},
            "chat": {"text": "白鹿城的城墙，我守了三十年。想听故事随时来。", "options": [{"text": "告辞。", "next": "__end__"}]},
        },
    },
    "npc_mage_tutor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "魔法不是念咒，是理解世界的语言。想学，先学会倾听。",
                "options": [
                    {"text": "请教『魔力脉冲』(Lv.6 · 800金)", "next": "teach_ao_shu", "need": {"class_any": ["cls_fa_shi"]}},
                    {"text": "请教『冰霜新星』(Lv.24 · 1500金)", "next": "teach_bing_shuang", "need": {"class_any": ["cls_fa_shi"]}},
                    {"text": "🌟 我想转职！", "next": "evolve_t1", "need": {"class_any": ["cls_fa_shi"], "evolve_ready": {"tier": 0, "level": 30}}},
                    {"text": "🌟 我想继续转职！", "next": "evolve_t2", "need": {"class_any": ["cls_fa_shi"], "evolve_ready": {"tier": 1, "level": 60}}},
                    {"text": "🌟 我想进行最终转职！", "next": "evolve_t3", "need": {"class_any": ["cls_fa_shi"], "evolve_ready": {"tier": 2, "level": 90}}},
                    {"text": "随便聊聊", "next": "chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "teach_ao_shu": {"text": "魔力脉冲——把魔力压缩成一束光。学费 800 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "魔力脉冲", "cost": 800, "need_lv": 6}}}, {"text": "下次再说", "next": "welcome"}]},
            "teach_bing_shuang": {"text": "冰霜新星——让时间在寒意中凝固。学费 1500 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "冰霜新星", "cost": 1500, "need_lv": 10}}}, {"text": "下次再说", "next": "welcome"}]},
            "evolve_t1": {"text": "Lv.30 的法师，元素之道与奥秘之道，你选哪一条？", "options": [{"text": "转职为元素法师（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 1}}}, {"text": "转职为奥秘法师（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 2}}}]},
            "evolve_t2": {"text": "Lv.60！元素术士还是奥秘术士？", "options": [{"text": "转职为元素术士（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 1}}}, {"text": "转职为奥秘术士（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 2}}}]},
            "evolve_t3": {"text": "Lv.90，法师的终章：元素贤者，或奥秘贤者。", "options": [{"text": "转职为元素贤者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 1}}}, {"text": "转职为奥秘贤者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 2}}}]},
            "evolved": {"text": "魔法的尽头是世界的真相。继续走吧，法师。", "options": [{"text": "多谢导师！", "next": "__end__"}]},
            "taught": {"text": "回去好好参悟，魔力不会辜负勤勉的人。", "options": [{"text": "告辞。", "next": "__end__"}]},
            "chat": {"text": "白鹿城法师塔的星光，比王都还亮。", "options": [{"text": "告辞。", "next": "__end__"}]},
        },
    },
    "npc_ranger_tutor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "箭离弦之前，先学会看风。港口的风最会骗人。",
                "options": [
                    {"text": "请教『鹰眼』(Lv.38 · 1500金)", "next": "teach_ying_yan", "need": {"class_any": ["cls_you_xia"]}},
                    {"text": "🌟 我想转职！", "next": "evolve_t1", "need": {"class_any": ["cls_you_xia"], "evolve_ready": {"tier": 0, "level": 30}}},
                    {"text": "🌟 我想继续转职！", "next": "evolve_t2", "need": {"class_any": ["cls_you_xia"], "evolve_ready": {"tier": 1, "level": 60}}},
                    {"text": "🌟 我想进行最终转职！", "next": "evolve_t3", "need": {"class_any": ["cls_you_xia"], "evolve_ready": {"tier": 2, "level": 90}}},
                    {"text": "随便聊聊", "next": "chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "teach_ying_yan": {"text": "鹰眼——看穿风的轨迹。学费 1500 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "鹰眼", "cost": 1500, "need_lv": 10}}}, {"text": "下次再说", "next": "welcome"}]},
            "evolve_t1": {"text": "Lv.30 的游侠：林语者聆听万木，风行者追逐自由。", "options": [{"text": "转职为林语者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 1}}}, {"text": "转职为风行者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 2}}}]},
            "evolve_t2": {"text": "Lv.60！自然行者还是疾风射手？", "options": [{"text": "转职为自然行者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 1}}}, {"text": "转职为疾风射手（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 2}}}]},
            "evolve_t3": {"text": "Lv.90，游侠的巅峰：万木之灵，或疾风猎手。", "options": [{"text": "转职为万木之灵（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 1}}}, {"text": "转职为疾风猎手（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 2}}}]},
            "evolved": {"text": "风会记住你的名字，游侠。", "options": [{"text": "多谢导师！", "next": "__end__"}]},
            "taught": {"text": "回去多练，箭无虚发是练出来的。", "options": [{"text": "告辞。", "next": "__end__"}]},
            "chat": {"text": "铁港城的风，吹得人清醒。", "options": [{"text": "告辞。", "next": "__end__"}]},
        },
    },
    "npc_priest_tutor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "圣光不偏袒任何人，只照亮愿意前行的人。孩子，你想学什么？",
                "options": [
                    {"text": "请教『圣光惩戒』(Lv.6 · 800金)", "next": "teach_sheng_guang", "need": {"class_any": ["cls_mu_shi"]}},
                    {"text": "请教『救赎之光』(Lv.10 · 1500金)", "next": "teach_jiu_shu", "need": {"class_any": ["cls_mu_shi"]}},
                    {"text": "🌟 我想转职！", "next": "evolve_t1", "need": {"class_any": ["cls_mu_shi"], "evolve_ready": {"tier": 0, "level": 30}}},
                    {"text": "🌟 我想继续转职！", "next": "evolve_t2", "need": {"class_any": ["cls_mu_shi"], "evolve_ready": {"tier": 1, "level": 60}}},
                    {"text": "🌟 我想进行最终转职！", "next": "evolve_t3", "need": {"class_any": ["cls_mu_shi"], "evolve_ready": {"tier": 2, "level": 90}}},
                    {"text": "随便聊聊", "next": "chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "teach_sheng_guang": {"text": "圣光惩戒——以光为刃，斩断污秽。学费 800 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "圣光惩戒", "cost": 800, "need_lv": 6}}}, {"text": "下次再说", "next": "welcome"}]},
            "teach_jiu_shu": {"text": "救赎之光——让光治愈每一道伤口。学费 1500 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "救赎之光", "cost": 1500, "need_lv": 10}}}, {"text": "下次再说", "next": "welcome"}]},
            "evolve_t1": {"text": "Lv.30 的牧师：吟游诗人以歌开路，神谕者以言传道。", "options": [{"text": "转职为吟游诗人（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 1}}}, {"text": "转职为神谕者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 2}}}]},
            "evolve_t2": {"text": "Lv.60！灵魂歌者还是大主教？", "options": [{"text": "转职为灵魂歌者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 1}}}, {"text": "转职为大主教（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 2}}}]},
            "evolve_t3": {"text": "Lv.90，牧师的终点：黎明颂者，或圣光先知。", "options": [{"text": "转职为黎明颂者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 1}}}, {"text": "转职为圣光先知（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 2}}}]},
            "evolved": {"text": "愿圣光与你同行，牧师。", "options": [{"text": "多谢导师！", "next": "__end__"}]},
            "taught": {"text": "回去默祷，光会回应你的虔诚。", "options": [{"text": "告辞。", "next": "__end__"}]},
            "chat": {"text": "白鹿城的圣殿，晨钟暮鼓从不间断。", "options": [{"text": "告辞。", "next": "__end__"}]},
        },
    },
    "npc_assassin_tutor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "……你听到的只是风声。想学杀人技，先学会不被人看见。",
                "options": [
                    {"text": "请教『影袭』(Lv.11 · 800金)", "next": "teach_ying_xi", "need": {"class_any": ["cls_ci_ke"]}},
                    {"text": "请教『淬毒之刃』(Lv.10 · 1500金)", "next": "teach_cui_du", "need": {"class_any": ["cls_ci_ke"]}},
                    {"text": "🌟 我想转职！", "next": "evolve_t1", "need": {"class_any": ["cls_ci_ke"], "evolve_ready": {"tier": 0, "level": 30}}},
                    {"text": "🌟 我想继续转职！", "next": "evolve_t2", "need": {"class_any": ["cls_ci_ke"], "evolve_ready": {"tier": 1, "level": 60}}},
                    {"text": "🌟 我想进行最终转职！", "next": "evolve_t3", "need": {"class_any": ["cls_ci_ke"], "evolve_ready": {"tier": 2, "level": 90}}},
                    {"text": "随便聊聊", "next": "chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "teach_ying_xi": {"text": "影袭——从阴影中出手，一击毙命。学费 800 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "影袭", "cost": 800, "need_lv": 6}}}, {"text": "下次再说", "next": "welcome"}]},
            "teach_cui_du": {"text": "淬毒之刃——刃上淬毒，见血封喉。学费 1500 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "淬毒之刃", "cost": 1500, "need_lv": 10}}}, {"text": "下次再说", "next": "welcome"}]},
            "evolve_t1": {"text": "Lv.30 的刺客：影舞者活在影子里，毒刃者活在刃尖上。", "options": [{"text": "转职为影舞者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 1}}}, {"text": "转职为毒刃者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 2}}}]},
            "evolve_t2": {"text": "Lv.60！暗影之刃还是淬毒师？", "options": [{"text": "转职为暗影之刃（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 1}}}, {"text": "转职为淬毒师（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 2}}}]},
            "evolve_t3": {"text": "Lv.90，刺客的终路：无影之刃，或蚀骨者。", "options": [{"text": "转职为无影之刃（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 1}}}, {"text": "转职为蚀骨者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 2}}}]},
            "evolved": {"text": "……去吧，影子会跟着你。", "options": [{"text": "多谢导师！", "next": "__end__"}]},
            "taught": {"text": "记住，刺客的荣耀在完成任务的那一刻。", "options": [{"text": "告辞。", "next": "__end__"}]},
            "chat": {"text": "铁港城的阴影里，藏着太多故事。", "options": [{"text": "告辞。", "next": "__end__"}]},
        },
    },
    "npc_monk_tutor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "拳打千遍，其义自见。码头搬货的汉子，一拳能打碎海浪。",
                "options": [
                    {"text": "请教『裂骨击』(Lv.6 · 800金)", "next": "teach_beng_quan", "need": {"class_any": ["cls_wu_seng"]}},
                    {"text": "请教『磐石之体』(Lv.10 · 1500金)", "next": "teach_jin_gang", "need": {"class_any": ["cls_wu_seng"]}},
                    {"text": "🌟 我想转职！", "next": "evolve_t1", "need": {"class_any": ["cls_wu_seng"], "evolve_ready": {"tier": 0, "level": 30}}},
                    {"text": "🌟 我想继续转职！", "next": "evolve_t2", "need": {"class_any": ["cls_wu_seng"], "evolve_ready": {"tier": 1, "level": 60}}},
                    {"text": "🌟 我想进行最终转职！", "next": "evolve_t3", "need": {"class_any": ["cls_wu_seng"], "evolve_ready": {"tier": 2, "level": 90}}},
                    {"text": "随便聊聊", "next": "chat"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "teach_beng_quan": {"text": "裂骨击——以裂骨劲碎敌之防。学费 800 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "裂骨击", "cost": 800, "need_lv": 6}}}, {"text": "下次再说", "next": "welcome"}]},
            "teach_jin_gang": {"text": "磐石之体——身如磐石，万法不侵。学费 1500 金币。", "options": [{"text": "请教我！", "next": "taught", "action": {"tutor_skill": {"skill": "磐石之体", "cost": 1500, "need_lv": 10}}}, {"text": "下次再说", "next": "welcome"}]},
            "evolve_t1": {"text": "Lv.30 的拳师：格斗士以攻代守，磐石行者以守代攻。", "options": [{"text": "转职为格斗士（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 1}}}, {"text": "转职为磐石行者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 1, "path": 2}}}]},
            "evolve_t2": {"text": "Lv.60！拳术师还是铁壁行者？", "options": [{"text": "转职为拳术师（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 1}}}, {"text": "转职为铁壁行者（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 2, "path": 2}}}]},
            "evolve_t3": {"text": "Lv.90，拳师的极境：破晓者，或磐岩壁垒。", "options": [{"text": "转职为破晓者（⚔️ 进攻）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 1}}}, {"text": "转职为磐岩壁垒（🛡️ 防御）", "next": "evolved", "action": {"evolve_class": {"tier": 3, "path": 2}}}]},
            "evolved": {"text": "拳即是心，心即是拳。走吧，拳师。", "options": [{"text": "多谢导师！", "next": "__end__"}]},
            "taught": {"text": "回去把桩功练扎实，功夫不会骗人。", "options": [{"text": "告辞。", "next": "__end__"}]},
            "chat": {"text": "码头的活儿，练的就是一口气。", "options": [{"text": "告辞。", "next": "__end__"}]},
        },
    },
    # v105 M19 P1：主线 flag/抉择体系落地——q10_5 黎明之光·对话抉择（3 分支）
    "npc_eter": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "text": "蚀夜的低语在封印之核中回荡：『……你来了。裂痕在扩大，而我……快要撑不住了。』",
                "options": [
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了。", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                # v105 M19 P1：q10_5 接取即抉择——3 个分支各 set_flag + quest_take
                # （talk 型任务接取即 ready，flag 在交付时决定结局台词变体）
                "text_from": "story",
                "text": "艾德里克的残魂在金光中凝实，向你伸出手。",
                "options": [
                    {"text": "✨ 我愿意，成为新的黎明。", "next": "__end__", "need": {"quest_pending": ""},
                     "action": {"set_flag": "chose_inheritor", "quest_take": True}},
                    {"text": "🤔 这份力量……我真的配得上吗？", "next": "__end__", "need": {"quest_pending": ""},
                     "action": {"set_flag": "chose_doubt", "quest_take": True}},
                    {"text": "🕯️ 除了传承，真的没有别的办法了吗？", "next": "__end__", "need": {"quest_pending": ""},
                     "action": {"set_flag": "chose_alternative", "quest_take": True}},
                ],
            },
            "quest_status": {
                "text": "『圣光不在于血统，而在于心中是否愿意守护。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "📜 我要接新任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "text": "金色的守护者注视着你，眼中是三百年的疲惫与欣慰：『去吧……你守护的黎明，会比我更长久。』",
                "options": [
                    {"text": "收下传承！", "next": "__end__", "action": {"quest_take": True}},
                ],
            },
        },
    },
    # ================= v113 隐藏线血脉传承对话树 6（种族限制：非对应血脉导师直接拒绝） =================
    # 设计：血脉不符 → 拒绝台词（无传承选项）；血脉符合 + 未解锁 → 试炼引导；
    #       血脉符合 + 已解锁 → 『接受传承』（hidden_evolve 动作，异步转职）。
    # 种族前置：dialogue_conds 的 race_is 条件；接取任务另有 require_race 双保险。
    "npc_dragon_veteran": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"race_is": "dragonborn"},
                     "text": "龙裔老兵·铁鳞的目光落在你身上，微微一凝：『龙血的味道……你体内流着龙骨山脉的血。过来，小子。』"},
                ],
                "text": "龙裔老兵·铁鳞上下打量你，缓缓摇头：『龙血不是谁都能受的。你的血脉里，没有龙骨山脉的印记。』",
                "options": [
                    {"text": "🐉 我渴望龙血之力！", "next": "trial", "need": {"race_is": "dragonborn"}},
                    {"text": "🧭 我该如何证明自己？", "next": "hint", "need": {"race_is": "dragonborn"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "trial": {
                "texts": [
                    {"need": {"hidden_unlocked": "cls_dragon_oath", "not_hidden_current": "cls_dragon_oath"},
                     "text": "铁鳞颔首：『试炼已成，龙血已在你的血管里苏醒。坐下来，接受龙裔的传承吧。』"},
                ],
                "text": "铁鳞：『暮岭古道的战争魔像守着最后的龙血矿脉。砸碎它们，让龙血在你血管里醒过来。』",
                "options": [
                    {"text": "🔥 我准备好了，接受传承！", "next": "inherit_ok", "need": {"hidden_unlocked": "cls_dragon_oath", "not_hidden_current": "cls_dragon_oath"}, "action": {"hidden_evolve": {"cls": "cls_dragon_oath", "tier": 0, "path": 1}}},{"text": "📜 接下试炼！", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hint": {
                "text": "铁鳞：『去暮岭古道找那两具战争魔像。砸碎它们，龙血矿脉就会为你敞开。』",
                "options": [{"text": "明白了。", "next": "welcome"}],
            },
            "inherit_ok": {
                "text": "铁鳞：『龙魂已与你同在。去闯出你的传说吧，龙裔。』",
                "options": [{"text": "多谢老兵！", "next": "__end__"}],
            },
        },
    },
    "npc_chrono_warden": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"race_is": "human"},
                     "text": "时计贤者·艾瑟拉推了推单片眼镜，镜片后的目光亮了一下：『人类的求知欲……时间会偏爱这样的灵魂。』"},
                ],
                "text": "时计贤者·艾瑟拉打量着你：『时间只向求道者低语。你的血脉里，还没有那份执念。』",
                "options": [
                    {"text": "⏳ 我想聆听时间之语！", "next": "trial", "need": {"race_is": "human"}},
                    {"text": "🧭 我该如何证明自己？", "next": "hint", "need": {"race_is": "human"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "trial": {
                "texts": [
                    {"need": {"hidden_unlocked": "cls_chronomancer", "not_hidden_current": "cls_chronomancer"},
                     "text": "艾瑟拉：『试炼已成，日晷的指针为你停顿了一瞬。来吧，翻开时间的那一页。』"},
                ],
                "text": "艾瑟拉：『晨曦大圣堂地窖的审判猎犬守候着时间之痕。击败它们，证明你能在时间的洪流中站稳。』",
                "options": [
                    {"text": "⏳ 我准备好了，接受传承！", "next": "inherit_ok", "need": {"hidden_unlocked": "cls_chronomancer", "not_hidden_current": "cls_chronomancer"}, "action": {"hidden_evolve": {"cls": "cls_chronomancer", "tier": 0, "path": 1}}},{"text": "📜 接下试炼！", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hint": {
                "text": "艾瑟拉：『晨曦大圣堂的古老日晷从不在正午指向太阳。找到大圣堂地窖里的审判猎犬，让时间为你停顿。』",
                "options": [{"text": "明白了。", "next": "welcome"}],
            },
            "inherit_ok": {
                "text": "艾瑟拉：『时间已与你同行。去吧，让世界为你停驻片刻。』",
                "options": [{"text": "多谢贤者！", "next": "__end__"}],
            },
        },
    },
    "npc_astrologer": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"race_is": "elf"},
                     "text": "观星台主·星澜抬头望向你，眼中映着星辉：『银月精灵……星语湖的星星，认得你的血脉。』"},
                ],
                "text": "观星台主·星澜轻声叹息：『湖面映着的星星，只向精灵的血脉吐露真名。你的命运，还藏在湖底。』",
                "options": [
                    {"text": "⭐ 我想与星辰对话！", "next": "trial", "need": {"race_is": "elf"}},
                    {"text": "🧭 我该如何证明自己？", "next": "hint", "need": {"race_is": "elf"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "trial": {
                "texts": [
                    {"need": {"hidden_unlocked": "cls_wild_hunter", "not_hidden_current": "cls_wild_hunter"},
                     "text": "星澜：『湖面已清，星星照了进来——命运正在为你转动。接受星辰的传承吧。』"},
                ],
                "text": "星澜：『星语湖被湖妖搅浑了。驱散它们，让星辉重新映照湖面——能看见星星的人，命运才会为你转动。』",
                "options": [
                    {"text": "⭐ 我准备好了，接受传承！", "next": "inherit_ok", "need": {"hidden_unlocked": "cls_wild_hunter", "not_hidden_current": "cls_wild_hunter"}, "action": {"hidden_evolve": {"cls": "cls_wild_hunter", "tier": 0, "path": 1}}},{"text": "📜 接下试炼！", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hint": {
                "text": "星澜：『去星语湖驱散湖妖。湖水清了，星星就会为你指路。』",
                "options": [{"text": "明白了。", "next": "welcome"}],
            },
            "inherit_ok": {
                "text": "星澜：『星辰已认你为主。去吧，命运会为你转动。』",
                "options": [{"text": "多谢星澜！", "next": "__end__"}],
            },
        },
    },
    "npc_grave_watcher": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"race_is": "orc"},
                     "text": "守墓人·枯骨抬起浑浊的眼睛：『兽人……边境堡外的骨头，认得出战血的味道。』"},
                ],
                "text": "守墓人·枯骨嘶哑地笑了笑：『亡者只听血脉的呼唤。你身上没有那份战血。』",
                "options": [
                    {"text": "💀 我想聆听亡者之语！", "next": "trial", "need": {"race_is": "orc"}},
                    {"text": "🧭 我该如何证明自己？", "next": "hint", "need": {"race_is": "orc"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "trial": {
                "texts": [
                    {"need": {"hidden_unlocked": "cls_hymn", "not_hidden_current": "cls_hymn"},
                     "text": "枯骨：『骨头已安息，低语已清晰。来，接下亡者的权柄。』"},
                ],
                "text": "枯骨：『边境堡外的兽人劫掠者躁动不安。让战场上的亡魂安息——能听懂亡者低语的人，才有资格执掌亡者。』",
                "options": [
                    {"text": "💀 我准备好了，接受传承！", "next": "inherit_ok", "need": {"hidden_unlocked": "cls_hymn", "not_hidden_current": "cls_hymn"}, "action": {"hidden_evolve": {"cls": "cls_hymn", "tier": 0, "path": 1}}},{"text": "📜 接下试炼！", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hint": {
                "text": "枯骨：『去边境堡外，让躁动的兽人劫掠者安息。打完这场，你就听得见亡者的低语了。』",
                "options": [{"text": "明白了。", "next": "welcome"}],
            },
            "inherit_ok": {
                "text": "枯骨：『亡者已认你为主。去吧，让它们安息。』",
                "options": [{"text": "多谢枯骨！", "next": "__end__"}],
            },
        },
    },
    "npc_shadow_master": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"race_is": "halfling"},
                     "text": "影刃宗师·夜枭从货箱的阴影里探出身：『半身人……灵巧的血脉，影子喜欢这样的同伴。』"},
                ],
                "text": "影刃宗师·夜枭隐在货箱的阴影中：『影豹只追随影子里的猎手。你的身法，还缺那一点暗影的血。』",
                "options": [
                    {"text": "🗡️ 我想成为影子！", "next": "trial", "need": {"race_is": "halfling"}},
                    {"text": "🧭 我该如何证明自己？", "next": "hint", "need": {"race_is": "halfling"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "trial": {
                "texts": [
                    {"need": {"hidden_unlocked": "cls_shadow_blade", "not_hidden_current": "cls_shadow_blade"},
                     "text": "夜枭：『影豹已败，影子已认主。来吧，接下暗影的传承。』"},
                ],
                "text": "夜枭：『月影林的影豹快过月光。去追上它们、击败它们——那时候你就不再是追影子的人，你就是影子本身。』",
                "options": [
                    {"text": "🗡️ 我准备好了，接受传承！", "next": "inherit_ok", "need": {"hidden_unlocked": "cls_shadow_blade", "not_hidden_current": "cls_shadow_blade"}, "action": {"hidden_evolve": {"cls": "cls_shadow_blade", "tier": 0, "path": 1}}},{"text": "📜 接下试炼！", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hint": {
                "text": "夜枭：『去月影林猎影豹。快过月光，你就成了影子。』",
                "options": [{"text": "明白了。", "next": "welcome"}],
            },
            "inherit_ok": {
                "text": "夜枭：『影子已与你同行。去吧，暗影即吾身。』",
                "options": [{"text": "多谢宗师！", "next": "__end__"}],
            },
        },
    },
    "npc_wusheng_monk": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"race_is": "dwarf"},
                     "text": "武僧·铁山拍了拍你的肩膀，咧嘴一笑：『矮人的筋骨，天生就是练拳的好料子！』"},
                ],
                "text": "武僧·铁山打量着你：『铁砧要塞的拳谱，只传筋骨如铁的血脉。你……还差些火候。』",
                "options": [
                    {"text": "🥊 我想学真拳！", "next": "trial", "need": {"race_is": "dwarf"}},
                    {"text": "🧭 我该如何证明自己？", "next": "hint", "need": {"race_is": "dwarf"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "trial": {
                "texts": [
                    {"need": {"hidden_unlocked": "cls_wu_sheng", "not_hidden_current": "cls_wu_sheng"},
                     "text": "铁山：『三只兽人没白打！来吧，我教你真正的拳。』"},
                ],
                "text": "铁山：『边境堡外的兽人劫掠者猖狂。以一敌三，打完了回来，我教你真正的拳。』",
                "options": [
                    {"text": "🥊 我准备好了，接受传承！", "next": "inherit_ok", "need": {"hidden_unlocked": "cls_wu_sheng", "not_hidden_current": "cls_wu_sheng"}, "action": {"hidden_evolve": {"cls": "cls_wu_sheng", "tier": 0, "path": 1}}},{"text": "📜 接下试炼！", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "hint": {
                "text": "铁山：『去边境堡外，三拳一个，打三只兽人劫掠者回来见我。』",
                "options": [{"text": "明白了。", "next": "welcome"}],
            },
            "inherit_ok": {
                "text": "铁山：『拳即是心。去吧，以武证道。』",
                "options": [{"text": "多谢铁山！", "next": "__end__"}],
            },
        },
    },
}
