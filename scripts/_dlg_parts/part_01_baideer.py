# -*- coding: utf-8 -*-
"""01 白鹿城组 主线对话树实现分片（策划案 01 翻译）"""
DIALOGUES_PART = {
    "npc_baron": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q2_3"},
                     "text": "门外传来号角声。白鹿城城主·巴伦男爵放下鹅毛笔，抬眼看向你，眼底多了几分温度：『灰影的事，你办得漂亮。商队总算敢走翡翠森林那条路了——本爵果然没看错人。』"},
                ],
                "text": "白鹿城城主·巴伦男爵合上一卷公文，正了正领口，神色从容：『冒险者，直入正题吧。白鹿城的风向，本爵只跟愿意干活的人谈。』",
                "options": [
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "🗺️ 打听白鹿城的风向。", "next": "gossip", "need": {"quest_done": "q2_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip": {
                "text": "男爵引你到窗边，压低声音：『你手里那块骨片，本爵派人悄悄查过——纹样不像白鹿城、不像教会、也像不着铁港的规矩。本爵嘴上不说，心里明白：这城底下，怕是藏着连王都都不问的东西。别声张，就当本爵什么也没说。』",
                "options": [
                    {"text": "🗺️ 那圣女失踪的传闻，城主怎么看？", "next": "gossip_saint"},
                    {"text": "🗺️ 白鹿城最近还太平吗？", "next": "gossip_town"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_saint": {
                "text": "男爵目光微沉：『圣女殿下……是教会圣光的门面，也是王都的忌讳。本爵治城，只管白鹿城的太平，不掺和王都的是非。只是——近来大圣堂的钟，夜里偶尔会自己响。夜里听得人心里发慌。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_town": {
                "text": "男爵：『狼患一平，商路就活了，白鹿城的日子好过多了。你是行会记名的冒险者，本爵的城门随时为你开着。去吧，铁港那边……大概也快找上你了。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q2_1"},
                     "text": "行会接待员·卡莉已经替你通禀过。府门前的仆役领你穿过两进院落，来到城主挥毫的书案前。白鹿城城主·巴伦男爵抬起头，目光锐利地打量你。巴伦男爵：『你就是卡莉提过的那个新冒险者，从橡木镇来的？行会特意打了招呼，说你在镇上干得不赖。白鹿城比橡木镇大得多，也乱得多——先让本爵看看你的本钱。』"},
                    {"need": {"quest_pending": "q2_2"},
                     "text": "男爵府的书案上摊着一张翡翠森林的地图，几处商道被画了鲜红的叉。巴伦男爵：『翡翠森林的狼群最近异常凶猛，拦路伤人，商队都不敢走那条路了。本爵不想看白鹿城的生意被几头畜生搅黄。替我清理一下。』"},
                    {"need": {"quest_pending": "q2_3"},
                     "text": "一位裹着兽皮的老猎户刚离开城主府，衣角还带着血迹。男爵手边的桌上，捆着一截沾血的狼毛。他正盯着那张悬赏令出神。巴伦男爵：『狼群是退了，可出了大事——翡翠森林深处的狼王『灰影』，咬死了三个猎人。他们家里人跪到本爵府前哭求，猎户也把仇报到了悬赏令上。白鹿城悬赏它很久了，今天这笔账，轮到它还。』"},
                ],
                "text": "白鹿城城主·巴伦男爵：『冒险者，本爵有话要交代。』",
                "options": [
                    {"text": "我是来解决麻烦的。", "next": "q2_1_intent", "need": {"quest_pending": "q2_1"}},
                    {"text": "我刚到白鹿城，人生地不熟。", "next": "q2_1_greet", "need": {"quest_pending": "q2_1"}},
                    {"text": "📜 我接下这个委托。", "next": "q2_2_accept", "need": {"quest_pending": "q2_2"}, "action": {"set_flag": "wolves_pledged", "quest_take": True}},
                    {"text": "狼群为什么突然这么凶？", "next": "q2_2_why", "need": {"quest_pending": "q2_2"}},
                    {"text": "报酬呢？", "next": "q2_2_pay", "need": {"quest_pending": "q2_2"}},
                    {"text": "📜 我替那三位猎人讨这笔账。", "next": "q2_3_accept", "need": {"quest_pending": "q2_3"}, "action": {"set_flag": "gray_shadow_pledged", "quest_take": True}},
                    {"text": "灰影很强吗？", "next": "q2_3_strength", "need": {"quest_pending": "q2_3"}},
                    {"text": "赏金多少？", "next": "q2_3_bounty", "need": {"quest_pending": "q2_3"}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_1_intent": {
                "text": "巴伦男爵：『好，本爵最烦只会耍嘴皮的。最近翡翠森林的狼群异常凶猛，商队都不敢走那条路了。你若真有心，就先替本爵把这摊子事镇住。』",
                "options": [
                    {"text": "✅ 我正是为此而来。", "next": "q2_1_accept", "need": {"quest_pending": "q2_1"}, "action": {"quest_take": True}},
                    {"text": "那地方危险吗？", "next": "q2_1_reward"},
                ],
            },
            "q2_1_greet": {
                "text": "巴伦男爵：『白鹿城的规矩，比橡木镇多，但心肠不坏。你既来了，就好好扎根。城北的翡翠森林最近有点不太平——别的先不提，让你认认门、亮亮手，就从那儿开始。』",
                "options": [
                    {"text": "✅ 我正是为此而来。", "next": "q2_1_accept", "need": {"quest_pending": "q2_1"}, "action": {"quest_take": True}},
                    {"text": "冒昧问一句，报酬？", "next": "q2_1_reward"},
                ],
            },
            "q2_1_reward": {
                "text": "巴伦男爵：『进城见城主，哪能让你白跑？先记你一份人情，回头翡翠森林的活儿，也一并算上赏钱。白鹿城赏罚分明，本爵说话算话。』",
                "options": [
                    {"text": "✅ 好，我答应做该做的事。", "next": "q2_1_accept", "need": {"quest_pending": "q2_1"}, "action": {"quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_1_accept": {
                "text": "巴伦男爵：『行，你的名字本爵记下了。既然来了，就别只为认个门——翡翠森林的狼患，一并交给你。』",
                "options": [
                    {"text": "✅ 见过男爵了，我这就去办正事。", "next": "q2_1_deliver"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q2_1_deliver": {
                "text": "巴伦男爵：『嗯，行会的章子盖过了，你的名帖也算递到本爵这儿了。从今天起，你就是白鹿城记名在册的冒险者。坐，本爵有话说。』",
                "options": [
                    {"text": "✅ 领取城主的第一份人情。", "next": "__end__", "need": {"quest_ready": "q2_1"}, "action": {"quest_take": True}},
                ],
            },
            "q2_2_why": {
                "text": "巴伦男爵：『怪就怪在这儿。往年翡翠森林的狼是躲着人的，今年却见了活物就扑，像是被什么逼急了。猎户进去探过，回来说是狼在往林子外边逃——里面怕是有更凶的东西。』",
                "options": [
                    {"text": "📜 那正好，我一并查个明白。", "next": "q2_2_accept", "action": {"set_flag": "wolves_pledged", "quest_take": True}},
                    {"text": "报酬呢？", "next": "q2_2_pay"},
                ],
            },
            "q2_2_pay": {
                "text": "巴伦男爵：『替你算了笔账——清理狼群，赏一百五十金；真查出狼群异变的根子，本爵另有重赏。白鹿城悬赏令上，从不少写一个子儿。』",
                "options": [
                    {"text": "📜 我接下这个委托。", "next": "q2_2_accept", "action": {"set_flag": "wolves_pledged", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_2_accept": {
                "text": "巴伦男爵：『好！翡翠森林的商道就靠你了。目标都记在悬赏令上，办妥了回来交差。记住——活着回来，本爵的账才会算到底。』",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            "q2_3_strength": {
                "text": "巴伦男爵：『灰影是这片林子百年不遇的狼王，皮糙肉厚，寻常铁器都难破它，还通人性般会藏会跑。猎户说它窝在翡翠森林的古树空地——本爵不建议你单人硬上。』",
                "options": [
                    {"text": "📜 我替那三位猎人讨这笔账。", "next": "q2_3_accept", "action": {"set_flag": "gray_shadow_pledged", "quest_take": True}},
                    {"text": "赏金多少？", "next": "q2_3_bounty"},
                ],
            },
            "q2_3_bounty": {
                "text": "巴伦男爵：『悬赏三百金，外加一张锻造图样，还有白鹿城全城记你一功。拿它的头来换，赏金一个子儿不少。』",
                "options": [
                    {"text": "📜 我替那三位猎人讨这笔账。", "next": "q2_3_accept", "action": {"set_flag": "gray_shadow_pledged", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_3_accept": {
                "text": "巴伦男爵：『有胆量！这是灰影的悬赏令，目标就记在上头。活着回来，别让那三个猎人的血白流。』",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                ],
            },
            "quest_status": {
                "texts": [
                    {"need": {"quest_active": "q2_2"},
                     "text": "巴伦男爵：『翡翠森林的狼群还在闹，商队那边快压不住了。狼的脚印、破损的商车，都在等你去处理。办好了回来交差——本爵的账等着你。』"},
                    {"need": {"quest_active": "q2_3"},
                     "text": "巴伦男爵：『灰影还在古树空地盘踞着，那三个猎人的仇还没报。本爵看得出你有本事，别让它在林子里耀武扬威太久。』"},
                ],
                "text": "巴伦男爵：『冒险日志上写着你的目标。去吧，别让本爵等太久。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "我进展到一半了。（报进度）", "next": "q2_2_hint", "need": {"quest_active": "q2_2"}},
                    {"text": "我进展到一半了。（报进度）", "next": "q2_3_hint", "need": {"quest_active": "q2_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q2_2_hint": {
                "text": "巴伦男爵：『狼群被你赶退了不少，商队开始试探着过林路了。记住——清狼归清狼，若能看破狼群惊慌的根子，回来一并禀报，本爵另有重赏。』",
                "options": [
                    {"text": "我这就回去继续。", "next": "__end__"},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                ],
            },
            "q2_3_hint": {
                "text": "巴伦男爵：『灰影伤了三个猎人，你可别逞强。若一个人应付不来，回城歇息也好——悬赏令在你手上，只要它还在，这账迟早要算。』",
                "options": [
                    {"text": "我这就回去继续。", "next": "__end__"},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q2_2"},
                     "text": "你把狼群清退的消息带回男爵府。男爵脸色先是一松，旋即微微皱眉。巴伦男爵：『干得漂亮，商队今晚就能恢复走货。不过——剿狼的时候，你可曾觉出什么不对？猎户说狼群是被赶出来的，森林深处有更凶的东西。这笔账，记着。』"},
                    {"need": {"quest_ready": "q2_3"},
                     "text": "你提着灰影的皮毛踏进城主府，男爵缓缓站起身，久久未语。巴伦男爵：『灰影……真被你了结了。三个猎人的在天之灵，可以瞑目了。这是悬赏的全数——三百金、一张图样，外加本爵记你一功。』"},
                ],
                "text": "巴伦男爵：『回来了？让本爵听听你的好消息。』",
                "options": [
                    {"text": "✅ 领取赏金。", "next": "q2_2_deliver", "need": {"quest_ready": "q2_2"}, "action": {"quest_take": True}},
                    {"text": "✅ 领取赏金。", "next": "q2_3_deliver", "need": {"quest_ready": "q2_3"}, "action": {"quest_take": True}},
                    {"text": "✅ 领取城主的第一份人情。", "next": "q2_1_deliver", "need": {"quest_ready": "q2_1"}},
                ],
            },
            "q2_2_deliver": {
                "text": "男爵府账房奉上一百五十金。男爵压低了些声音：『狼是退了，可猎户说的话，本爵越寻思越不安。翡翠森林深处，怕是藏了别的东西。你且歇着，本爵若有消息，再传你。』（话锋一滞——猎户已把灰影的事闹到了府上。）",
                "options": [
                    {"text": "我明白了。", "next": "__end__"},
                ],
            },
            "q2_3_deliver": {
                "text": "你从灰影皮毛下取出一枚刻着奇异符文的骨片——那不是任何已知势力的纹样。众目睽睽之下，你悄悄收进怀里。巴伦男爵：『这是？……不，这东西你不该当众拿出来。收好。白鹿城悬赏的是狼头，不是这来历不明的之物。夜里若方便，来本爵书房一趟——有些话，不能在大堂上说。』",
                "options": [
                    {"text": "🗺️ 夜里再说。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_doctor": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q2_4"},
                     "text": "医馆内飘着清苦的药草味，医师·温蒂正在捣药，头也不抬地朝柜台招了招手：『回来了？沼泽的事，镇上的人都知道了。你做的，是对的。』"},
                    {"need": {"quest_active": "q2_4"},
                     "text": "医师·温蒂起身给你斟了杯药茶，眉头微蹙：『还没回来？迷雾沼泽的雾又浓了几分，镇边都开始飘黑气了。你手上的事，赶紧办了。』"},
                ],
                "text": "医师·温蒂替你倒了杯药茶，语气平淡：『镇子不小，看病的多。你来得正好——这里有件事，比头疼脑热要紧得多。』",
                "options": [
                    {"text": "📜 我需要任务。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "🗺️ 这阵子镇上有什么烦心事？", "next": "gossip"},
                    {"text": "🏥 帮我看看伤。", "next": "heal"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip": {
                "text": "医师·温蒂：『王都圣女失踪的事传得到处都是，酒馆里都炸开锅了。可我们是治病的人，管不着王都的是非——脚边的病人都治不过来，何必去数天上的星。』",
                "options": [
                    {"text": "🗺️ 那镇上的药材还好吗？", "next": "gossip_herb"},
                    {"text": "🗺️ 最近有没有治不了的怪病？", "next": "gossip_ailment"},
                    {"text": "🗺️ 圣光骑士们近来常来吗？", "next": "gossip_knight"},
                    {"text": "告别。", "next": "__end__"},
                ],
            },
            "gossip_herb": {
                "text": "温蒂：『药草这事儿我不安了好一阵子。迷雾沼泽的水泛黑光之后，连城里的几味补药都跟着蔫了。你若不忙，替我看看那沼泽出了什么事——这事，比听着要紧。』",
                "options": [
                    {"text": "📜 我这就去看看。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "🗺️ 黑光这东西，是头一回见吗？", "next": "gossip_blacklight"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_ailment": {
                "text": "温蒂：『怪病倒没有，就是不踏实。黑光从沼泽往镇边漫，夜里还有潮虫从地缝里爬出来。我劝人夜里别睡一楼，可听进去的没几个。』她顿了顿，『你常在外边跑，也当心点。』",
                "options": [
                    {"text": "🗺️ 黑光这东西，是头一回见吗？", "next": "gossip_blacklight"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_blacklight": {
                "text": "温蒂：『头一回。我行医这些年，见过疫病、见过中毒、见过兽伤人——就是没见过连水一起泛黑的。药草一排排枯得整整齐齐，像被什么一口气抽走了精气。这不像病，像……有什么东西渗上来了。』",
                "options": [
                    {"text": "📜 我这就去看看。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "🗺️ 那镇上的圣光骑士们怎么说？", "next": "gossip_knight"},
                    {"text": "🗺️ 我还能帮上别的忙吗？", "next": "gossip_other"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_knight": {
                "text": "温蒂：『圣光骑士路过是不看病也不问药的，他们只盯着王都的差事。倒是听人说，大圣堂的钟最近夜里会自己响——圣女失踪那晚就响过。我一个治病的，管不了教堂的钟，只觉得这城里的水，越来越深了。』",
                "options": [
                    {"text": "🗺️ 黑光这东西，是头一回见吗？", "next": "gossip_blacklight"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_other": {
                "text": "温蒂：『你若得空，帮我把镇东赵婶家那口井的水送去验一验——这几日有人喝了拉肚子，我怀疑掺进了那股黑。查清了，比当面酬谢你的人情更实在。』（此为氛围支线提示，非主线任务）",
                "options": [
                    {"text": "我知道了。", "next": "__end__"},
                ],
            },
            "heal": {
                "text": "医师·温蒂：『过来坐。』她细细诊了你的脉，点头：『底子不错，记得伤口要清理干净，药不能停，酒不能喝。拿好这帖——要是真碰上泛黑光的活物，伤口一定要用烈酒冲洗，别让它见风化脓。』",
                "options": [
                    {"text": "多谢。", "next": "heal_done"},
                ],
            },
            "heal_done": {
                "text": "温蒂收起药杵，补了一句：『你再记住一条——遇上黑光，别光想着逞强。身子是冒险的本钱，没了它，什么任务都白搭。』",
                "options": [
                    {"text": "我记下了。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "text": "你迈进医馆。窗台上晾着的药草全都蔫了，几束还泛着暗色。温蒂正对着一株枯草发怔。医师·温蒂：『来得正好。迷雾沼泽最近一直在泛黑光，我照例去采药，沼泽里的水泛着黑光，采集的药草全都枯了。这些可都是镇上的常备药。帮我看看出了什么事。』",
                "options": [
                    {"text": "📜 我去查个明白。", "next": "q2_4_accept", "need": {"quest_pending": "q2_4"}, "action": {"set_flag": "swamp_pledged", "quest_take": True}},
                    {"text": "黑光？听起来不简单。", "next": "q2_4_doubt"},
                    {"text": "怎样才能帮到你？", "next": "q2_4_help"},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_4_doubt": {
                "text": "医师·温蒂：『不简单就对了。我采药二十年，从没见过这样泛黑光的泥水，更没见过药草枯得这么齐。雾气也浓得反常，能见度不到十步。你去，务必小心。』",
                "options": [
                    {"text": "📜 我去查个明白。", "next": "q2_4_accept", "need": {"quest_pending": "q2_4"}, "action": {"set_flag": "swamp_pledged", "quest_take": True}},
                    {"text": "我的任务范围是什么？", "next": "q2_4_scope"},
                    {"text": "怎样才能帮到你？", "next": "q2_4_help"},
                ],
            },
            "q2_4_help": {
                "text": "医师·温蒂：『你在迷雾沼泽里，替我把那些拦路的『大史莱姆』清理掉——它们被黑光一浸，个头和凶性都涨了，堵在通往沼泽深处的小道上。清了它们，我才能安心探究源头。』",
                "options": [
                    {"text": "📜 我去查个明白。", "next": "q2_4_accept", "need": {"quest_pending": "q2_4"}, "action": {"set_flag": "swamp_pledged", "quest_take": True}},
                    {"text": "我的任务范围是什么？", "next": "q2_4_scope"},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_4_scope": {
                "text": "温蒂：『我只要你清掉挡路的五只大史莱姆，让商路和小道通开；至于沼泽深处的黑光之源，你若是顺手看见了、探清了，回来告诉我最好——但那不是强求，别为它逞强折在里头。探源我自己慢慢来。』",
                "options": [
                    {"text": "📜 我明白了，这就去清怪探底。", "next": "q2_4_accept", "need": {"quest_pending": "q2_4"}, "action": {"set_flag": "swamp_pledged", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_4_accept": {
                "text": "医师·温蒂：『好。目标记在冒险日志里——击败五只大史莱姆，探一探沼泽的底。回来时若采到沾黑光的药草，别带进镇上，先拿来给我看。』",
                "options": [
                    {"text": "出发！", "next": "__end__"},
                    {"text": "沼泽里有什么要注意的吗？", "next": "q2_4_advice"},
                ],
            },
            "q2_4_advice": {
                "text": "医师·温蒂：『黑光浸过的活物，性子都变得躁、变得凶——大史莱姆个头比往常大，路上别恋战。至于沼泽深处那团黑光……看到了也好，别靠太近。有些东西，先看清了，才知道怎么躲。』",
                "options": [
                    {"text": "我记下了，出发！", "next": "__end__"},
                    {"text": "那团黑光会伤人吗？", "next": "q2_4_blacklight_warn"},
                ],
            },
            "q2_4_blacklight_warn": {
                "text": "温蒂：『黑光本身未必咬人，可沾了它的活物都变凶，水也泛着说不清的腥甜味。我叮嘱你一句——若发现手头或鞋上沾了那层黑，务必用烈酒洗净。它看着像雾，心里头却像活的一般，会往血管里钻。』",
                "options": [
                    {"text": "我记下了，出发！", "next": "__end__"},
                ],
            },
            "quest_status": {
                "texts": [
                    {"need": {"quest_active": "q2_4"},
                     "text": "医师·温蒂：『迷雾沼泽的雾又浓了，昨晚还有头大史莱姆爬到镇边，被我泼了药赶回去。你的目标——那五只大史莱姆还在沼泽里。多加小心，黑了雾的草别乱碰。』"},
                ],
                "text": "医师·温蒂：『你先忙手上的事。若有像黑光一样的东西，回来告诉我。』",
                "options": [
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "我清掉了不少大史莱姆。（报进度）", "next": "q2_4_progress"},
                    {"text": "我该重点清理那些？", "next": "q2_4_hint"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q2_4_progress": {
                "text": "医师·温蒂：『你清掉的大史莱姆，我已经按个头和黑光程度记了档。越靠沼泽深处的越凶，但也越说明源头就在那里。你把堵路口的清了就回来，剩下的别硬碰。』",
                "options": [
                    {"text": "我这就回去继续。", "next": "__end__"},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                ],
            },
            "q2_4_hint": {
                "text": "医师·温蒂：『你可听过——黑光浸过的活物，都会变得躁而不安。大史莱姆越靠近沼泽深处的就越大。别恋战，清了路口那五只，余下的等我这边想出对策。』",
                "options": [
                    {"text": "我这就回去继续。", "next": "__end__"},
                    {"text": "✅ 任务完成了！", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q2_4"},
                     "text": "你回到医馆，泥水的腥味还沾在靴子上。温蒂放下药杵，目光在你身上停了一瞬。医师·温蒂：『大史莱姆清了？好。你这一趟，至少让镇上的常备药有救了。可——』她捻起一株泛黑的枯草，『沼泽深处的黑光还在扩散。这不是自然的力量……是诅咒。』"},
                ],
                "text": "医师·温蒂：『你回来了。』",
                "options": [
                    {"text": "✅ 领取报酬。", "next": "q2_4_deliver", "need": {"quest_ready": "q2_4"}, "action": {"quest_take": True}},
                    {"text": "🤔 诅咒？你还看到了什么？", "next": "q2_4_probe"},
                ],
            },
            "q2_4_probe": {
                "text": "温蒂把那株枯草凑到你面前：『你看这溃烂的茬口，齐得像被剪子铰的，可没有剪子能铰出这种纹路。它不是病死的、不是晒死的，是被『吸』死的——精气、水分，一起抽走。』她皱眉，『我行了半辈子医，头一回见这种死法。』",
                "options": [
                    {"text": "✅ 我明白了，报酬我领了。", "next": "q2_4_deliver", "need": {"quest_ready": "q2_4"}, "action": {"quest_take": True}},
                ],
            },
            "q2_4_deliver": {
                "text": "温蒂从柜台下取出一包扎好的东西，又替你灌满一壶混着草药的清水。医师·温蒂：『这是你应得的。你记着——黑不是沼泽自己的颜色，是有什么东西从地底下渗上来了。白鹿城之外，怕是也没清净。这份药膏你收着，解毒的，或许用得上。』",
                "options": [
                    {"text": "多谢医师。", "next": "q2_4_leave"},
                ],
            },
            "q2_4_leave": {
                "text": "温蒂望着门外渐暗的天色，低声道：『黑光在往这边漫，早晚有一天会漫到城门口。到那时，白鹿城得有人能一眼认出它的来历……你且记着今天，他日若在别处再撞见黑光，别当它是寻常的夜色。』",
                "options": [
                    {"text": "我记住了。告辞。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_tavern_owner": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q2_5"},
                     "text": "白鹿与麦酒酒馆正是最热闹的时辰。酒馆老板·胖托尼擦着杯子，冲你挤挤眼：『哟，熟人！圣女那事儿，酒桌上都传遍了。您要听哪个版本？——嘘，坐下来再说。』"},
                ],
                "text": "白鹿与麦酒酒馆里人声嘈杂。酒馆老板·胖托尼擦着柜台，见你进来，咧嘴一笑：『来了？麦酒管够，故事管饱——您要酒，还是要故事？』",
                "options": [
                    {"text": "📜 酒要一杯，故事也要听。", "next": "quest_talk", "need": {"quest_pending": ""}},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 打听得差不多了。", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "🗺️ 就着麦酒聊聊白鹿城。", "next": "gossip"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip": {
                "text": "你找了张靠墙的桌子坐下。胖托尼笑着给你端来一杯麦酒。胖托尼：『这话可得小口喝，大口品——酒馆里听来的，一半是好玩，一半是要命的。您听哪样？』",
                "options": [
                    {"text": "🗺️ 讲讲这个月最热闹的传闻。", "next": "gossip_hot"},
                    {"text": "🗺️ 圣光骑士们近来常来吗？", "next": "gossip_knight"},
                    {"text": "🗺️ 那口大圣堂的钟，真是自己响的？", "next": "gossip_bell"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_hot": {
                "text": "胖托尼：『这个月最热闹的，要数城里来了个神秘商队——大半夜进城，天亮就走，车里拉着一口黑漆漆的箱子，谁也打听不出装的是什么。有人说是给教会的贡品，有人说里头是活的。嘿嘿，我只管卖酒，不管装啥。』",
                "options": [
                    {"text": "🗺️ 那口大圣堂的钟呢？", "next": "gossip_bell"},
                    {"text": "🗺️ 圣光骑士们近来常来吗？", "next": "gossip_knight"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_knight": {
                "text": "胖托尼：『前几天还总来，最近来得少了——听说都让王都调的，满世界找那位圣女殿下。走之前一个个愁眉苦脸的，喝酒都不带量。我偷偷听了一耳朵，他们念叨什么『容器』『封印』，我不懂，也不敢问。』",
                "options": [
                    {"text": "🗺️ 那口大圣堂的钟，真是自己响的？", "next": "gossip_bell"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gossip_bell": {
                "text": "胖托尼压低了声音：『钟是真自己响的，响过十三下，就在圣女失踪那晚。那钟挂了三百年，谁也没见它动过。守堂的老修士吓得直念经，说这是『圣物示警』——可示什么警，谁也不敢往深里想。您要是信，就当我没说。』",
                "options": [
                    {"text": "🗺️ 讲讲这个月最热闹的传闻。", "next": "gossip_hot"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "text": "你刚坐到吧台边，胖托尼就探过身来，神秘地压低声音。胖托尼：『嘘——听说了吗？王都的圣女殿下……不见了。教会派了圣光骑士团到处找人，闹得可大了。我在这酒馆听了三十年消息，这种大事，头一回见骑士们连酒都喝不安生。』",
                "options": [
                    {"text": "❓ 圣女失踪？仔细讲讲。", "next": "q2_5_rumor", "action": {"set_flag": "heard_rue_rumor"}},
                    {"text": "教会到处找人，藏不住的就是大新闻。", "next": "q2_5_lean"},
                    {"text": "这事跟白鹿城有什么关系？", "next": "q2_5_relevance"},
                    {"text": "我能帮上什么忙？", "next": "q2_5_role"},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_rumor": {
                "text": "胖托尼：『我也是听骑士喝高了漏的嘴——圣女殿下前一晚还在大圣堂，第二天清早人就没了，寝殿里连血迹都没有。教会急得不行，可越急，越让人觉得蹊跷。』",
                "options": [
                    {"text": "❓ 那佣兵们又怎么说？", "next": "q2_5_sold"},
                    {"text": "❓ 白鹿城的大圣堂也有动静？", "next": "q2_5_bell"},
                    {"text": "❓ 老修士们那边有什么动静？", "next": "q2_5_oldpilgrim"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "🌙 我该在这传谣里做什么？", "next": "q2_5_role"},
                ],
            },
            "q2_5_lean": {
                "text": "胖托尼：『可不是嘛！不过您可别接着这话头到处说——咱开酒馆的，最忌讳传王都的是非。那帮骑士耳朵灵着呢。……哎，说起来，最近他们总来喝酒，喝多了就抱怨王都的差事。』",
                "options": [
                    {"text": "❓ 骑士们抱怨什么？", "next": "q2_5_rumor"},
                    {"text": "❓ 白鹿城的大圣堂也有动静？", "next": "q2_5_bell"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_relevance": {
                "text": "胖托尼：『圣女失踪是王都的事，照理跟白鹿城八竿子打不着。可怪就怪在——大圣堂的钟，最近夜里老自个儿响。那钟三百年没自己响过了。您说，巧不巧？』",
                "options": [
                    {"text": "❓ 钟自己响了十三下？", "next": "q2_5_bell"},
                    {"text": "❓ 酒馆里有人见过圣女吗？", "next": "q2_5_sold"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_bell": {
                "text": "胖托尼：『可不是嘛！圣女失踪那晚，大圣堂的钟自己响了十三下——那儿还躺着一枚没点过的圣烛。神父们脸色都白着，可谁也不敢报到王都去。咱白鹿城啊，看着热闹，底下的水，深着呢。』",
                "options": [
                    {"text": "❓ 佣兵们怎么看这口钟？", "next": "q2_5_sold"},
                    {"text": "❓ 老修士们怎么说这声钟？", "next": "q2_5_oldpilgrim"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_sold": {
                "text": "隔壁酒桌上，一个满身风霜的佣兵敲了敲桌子，冷笑一声。佣兵：『圣女失踪？我看是教会自己把她藏起来了。你头回来白鹿城吧——教会的人啊，嘴里全是圣光，背地里的事，说出来吓死你。』",
                "options": [
                    {"text": "❓ 你这话是什么意思？", "next": "q2_5_sold2"},
                    {"text": "❓ 跑堂那边传了新版本？", "next": "q2_5_townsfolk"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "🌙 我要把这话记进心里。（打听收束）", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                ],
            },
            "q2_5_sold2": {
                "text": "佣兵低了声音：『没什么，都是些不能拿到台面上说的旧事。不过你记着——圣女是圣光的容器，教会把她看得比命还重。真要出了事，那天上地下，准有没被掀开的石头。』他灌了口酒，不再多说。",
                "options": [
                    {"text": "❓ 老修士们那边又怎么说？", "next": "q2_5_oldpilgrim"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_oldpilgrim": {
                "text": "角落一张桌上，一位低头念祷的老信徒听见动静，抬起头，声音发抖。老信徒：『莫要问了，孩子……圣女殿下的事，教会自会料理。我们只管祈祷，祈祷圣光别把谁都收走。』他攥着胸前的圣徽，又补了半句，『这钟声……我活了七十岁，头回听它自己响。怕不是时候要变了。』",
                "options": [
                    {"text": "❓ 跑堂伙计们又传了什么？", "next": "q2_5_townsfolk"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_townsfolk": {
                "text": "吧台边的跑堂小伙计擦着杯子，凑过来压低声音补了一嘴。跑堂伙计：『听我一句，老板娘家的表姐在王都开店，说圣女失踪前一个月，就一直有人见她夜里往教会的密室里跑。城主府那边讳莫如深，酒桌上却都传开了——谁信谁傻，可空穴来风不会没由头。』",
                "options": [
                    {"text": "❓ 佣兵们怎么看这事？", "next": "q2_5_sold"},
                    {"text": "✅ 这消息，我记住了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_role": {
                "text": "胖托尼：『您是冒险者，见得多，走得远。圣女这事满大陆都在传，多留个心眼总没错——往后走到哪，若是听见旁的版本，回来也讲给我听听，咱酒馆管你的酒。』",
                "options": [
                    {"text": "✅ 我把这话记下了。", "next": "q2_5_accept", "need": {"quest_pending": "q2_5"}, "action": {"set_flag": "saintess_rue_heard", "quest_take": True}},
                    {"text": "再想想。", "next": "welcome"},
                ],
            },
            "q2_5_accept": {
                "text": "消息听完，你在吧台上放下一枚铜板当酒钱。胖托尼心领神会地把钱收进钱袋，又给你续上半杯。胖托尼：『成，这事儿您心里有数就行。圣女殿下的事，白鹿城传开了——也传往铁港城那边去了。您要是哪天顺路，多留意着点，保不齐能听见更多。』",
                "options": [
                    {"text": "✅ 这传闻，我心里有数了。", "next": "q2_5_deliver", "action": {"quest_take": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "texts": [
                    {"need": {"quest_active": "q2_5"},
                     "text": "胖托尼：『圣女那事，酒桌上又添了几个新版本。您要不再坐会儿，把该听的听完，回去好好琢磨？』"},
                ],
                "text": "胖托尼：『您先忙。酒馆的门，消息的耳朵，随时为您敞着。』",
                "options": [
                    {"text": "✅ 打听得差不多了。", "next": "quest_done_talk", "need": {"quest_ready": ""}},
                    {"text": "我这就回去继续。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q2_5"},
                     "text": "你重又落座。胖托尼给你倒了杯新麦酒，自己则凑近了压低声音。胖托尼：『打听得差不多了？这遍白鹿城，怕是没几个敢像您这样刨根问底的。圣女殿下失踪，背后的事，比酒桌上的传闻要深得多——您既然上了心，那就多留个心眼。这杯酒，当我请您的。』"},
                ],
                "text": "胖托尼：『您要酒还是要故事？』",
                "options": [
                    {"text": "✅ 领下这份情。", "next": "q2_5_deliver", "need": {"quest_ready": "q2_5"}, "action": {"quest_take": True}},
                    {"text": "🤔 传闻里哪些是真的、哪些是假的？", "next": "q2_5_fact"},
                ],
            },
            "q2_5_fact": {
                "text": "胖托尼摊摊手：『真真假假，连我这个成天听跑堂传话的老板都分不清。佣兵那帮粗人信口开河，吟游诗人添油加醋，骑士守口如瓶——您听个大概就当长了耳朵。要我说，哪天真去铁港城、去王都，亲眼见见，才是真的。』",
                "options": [
                    {"text": "✅ 你说得对。这份情我领了。", "next": "q2_5_deliver", "need": {"quest_ready": "q2_5"}, "action": {"quest_take": True}},
                ],
            },
            "q2_5_deliver": {
                "text": "酒馆外一阵夜风扫过，吧台上的烛火晃了晃。你直觉感到蹊跷——圣女失踪的背后，似乎藏着比表面更深的东西。白鹿城的酒馆，第一次让你意识到，这个世界没有想象中那么简单。胖托尼目送你出门，低声道：『记住我说的话。大圣堂的钟，三百年没自己响过了。它响了，就不是白响的。』",
                "options": [
                    {"text": "夜已深，我该走了。", "next": "__end__"},
                ],
            },
        },
    },
}
