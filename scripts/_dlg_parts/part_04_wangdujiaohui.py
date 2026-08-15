# -*- coding: utf-8 -*-
"""04 王都与教会组 主线对话树实现分片（策划案 04 翻译）

分片覆盖：npc_king（q5_2/q5_3/q5_4/q5_5，另有 s8/s11 支线）、
npc_knight_commander（q5_6/q6_6/q11_1/q11_2/q11_3）、npc_pope（q11_5）。

实现要点：
- 纯字面量 dict，供合并脚本 ast.literal_eval 解析。
- 条件/动作键全部取自 00 规范 §2.2/§2.3 清单；
- 任务绑定一律静态 qid（engin 侧 "…动态模式禁用"——故 quest_pending/quest_ready
  在共享节点（welcome/quest_status/progress/quest_done_talk）中按各 NPC 名下主线 qid 分别展开）；
- talk 型任务（q5_2/q5_6/q6_6/q11_5）中间节点不带 quest_take，仅最终接取节点触发；
- 罗兰跨章与教皇 flag 按策划案 §6 的 set 点照写；门控一律用静态 quest_done 驱动。
"""
DIALOGUES_PART = {
    "npc_king": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q5_5"},
                     "text": "旁白：腓特烈三世望着窗外王后的花园，神色缓和。『那朵花的事了了，王后终于能安寝。朕欠你一次情——这情，朕记在心里。』"},
                    {"need": {"quest_done": "q5_4"},
                     "text": "旁白：腓特烈三世的脸色微沉。『审判庭的猎犬到了银铃河……圣女怕是被逼到绝境了。朕必须抢在奥古斯都之前，把人接到身边。』"},
                    {"need": {"quest_done": "q5_3"},
                     "text": "旁白：腓特烈三世指尖轻敲御案。『金穗平原的盗贼，果然不是寻常流寇。那些精良的兵器……朕已命人暗中追查其来路。』"},
                    {"need": {"quest_done": "q5_2"},
                     "text": "旁白：腓特烈三世将一卷羊皮纸推到御案边。『老约翰的信，朕已派人核查过。你说的话，朕信了大半。王都的水，比你想象的要深。』"},
                ],
                "text": "旁白：晨曦城王宫大殿，腓特烈三世在御案后抬眸。『教会说魔王已死，封印稳固。可边境的烽火不会撒谎。朕，等一个人，等了很多天。』",
                "options": [
                    {"text": "📜 陛下，有需要我效劳的吗？", "next": "quest_talk", "need": {"quest_pending": "q5_2"}},
                    {"text": "📜 陛下，有需要我效劳的吗？", "next": "quest_talk", "need": {"quest_pending": "q5_3"}},
                    {"text": "📜 陛下，有需要我效劳的吗？", "next": "quest_talk", "need": {"quest_pending": "q5_4"}},
                    {"text": "📜 陛下，有需要我效劳的吗？", "next": "quest_talk", "need": {"quest_pending": "q5_5"}},
                    {"text": "我手头的王命……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_2"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_3"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_4"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_5"}},
                    {"text": "🗺️ 陛下，近来王都可安好？", "next": "court_gossip"},
                    {"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "court_gossip": {
                "text": "旁白：腓特烈三世压低了声音。『教会的枢机主教奥古斯都，近来频频出入大圣堂，与圣女失踪脱不开干系。审判庭的名义……是圣光，是清洗。朕信不过。你若有心，替朕盯着些。』",
                "options": [
                    {"text": "🗺️ 深谈王都的暗流。", "next": "court_detail"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "court_detail": {
                "text": "旁白：腓特烈三世走到窗前，望着晨曦城的街巷。『王都的百姓还仰望着大圣堂的金顶，以为那里住着圣光。可朕知道，金顶之下，是枢机主教清点的「异端」名单、是审判庭染血的铁架。『忠诚』这两字，在这座城里，最是轻贱。』",
                "options": [
                    {"text": "🤔 陛下为何信得过我？", "next": "king_trust"},
                    {"text": "🗺️ 那陛下自己可查了什么？", "next": "king_own"},
                    {"text": "（静默行礼，不再多问）", "next": "__end__"},
                ],
            },
            "king_trust": {
                "text": "旁白：腓特烈三世目光落在你身上，罕见地带着一丝温度。『因为你会为一个普通村庄的麦田动手，会为一座修道院的黑气挺身——你不为势利所动。这样的手，朕才敢把「查清真相」四个字托付。朕这双手，沾不得太多教会的血，却还留得住一个信字。』",
                "options": [
                    {"text": "臣/民必不负所托。", "next": "__end__"},
                    {"text": "🗺️ 还请教陛下王都的局势。", "next": "court_detail"},
                ],
            },
            "king_own": {
                "text": "旁白：腓特烈三世自嘲地笑了笑。『朕查过。查了三年，只查出教会的一层又一层空壳。边境烽火是真的，封印松动也是真的——可朕的探子一触到「圣女」「祭品」这两个词，就断了线。要么是被灭了口，要么……是教会的手，伸得比朕想象的更远。』",
                "options": [
                    {"text": "那我也从这两个词查起。", "next": "king_word"},
                    {"text": "🗺️ 陛下还知道什么？", "next": "court_detail"},
                    {"text": "（静默）", "next": "__end__"},
                ],
            },
            "king_word": {
                "text": "旁白：腓特烈三世目光微动。『「圣女」这条线，你沿银铃河去摸；「祭品」这条线，去问修道院的玛格丽特，或行会的老约翰。两处都摸到，真相自会拼出个轮廓。朕能挪给你的暗梢，只有这一枚信物——剩下的路，得你自己走。』",
                "options": [
                    {"text": "臣/民领命。", "next": "__end__"},
                    {"text": "🗺️ 陛下还知道什么？", "next": "court_detail"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q5_2"},
                     "text": "旁白：腓特烈三世站起身，走近几步。『老约翰力荐你。他说你见过那方圣徽，见过修道院的黑气——你是为数不多「见过真相」的活人。教会说魔王已死，封印稳固，可朕的边境烽火三日一封。朕需要一个不替教会说话的人，去查清真相。』"},
                    {"need": {"quest_pending": "q5_3"},
                     "text": "旁白：腓特烈三世递给你一张泛黄的舆图。『朕的密探在金穗平原盯了三个月——那伙盗贼有精良的十字弩和链甲，不像流寇，倒像一支被打散的正规军。去看一看，谁能养得起这样一支「匪」。』"},
                    {"need": {"quest_pending": "q5_4"},
                     "text": "旁白：腓特烈三世神色骤紧，快步近前。『朕的密探飞马来报——异端审判庭在银铃河附近发现了圣女的踪迹！他们带了猎犬，嗅觉能追出十里！朕的兵不便与审判庭正面冲突，这件事，只能你去做。』"},
                    {"need": {"quest_pending": "q5_5"},
                     "text": "旁白：腓特烈三世背对着门，声音少见地放软了一些。『王后昨夜又做噩梦了，梦见了那朵教士送来的白花。那花据说是教会「圣物」——可自打进宫起，王后的身子便一日比一日凝重。花前些日子被人盗走，她日夜忧心。朕……不忍心看她这样。替朕寻回那朵圣光百合吧。』"},
                ],
                "text": "旁白：腓特烈三世望着你，目光沉静。『朕得先确认一件事——你愿不愿站到教会对立面，替朕、替真相办事。』",
                "options": [
                    {"text": "朕愿意。", "next": "q5_2_awe", "need": {"quest_pending": "q5_2"}},
                    {"text": "🤔 陛下想查什么真相？", "next": "q5_2_ask", "need": {"quest_pending": "q5_2"}},
                    {"text": "（再想想，躬身告退）", "next": "__end__", "need": {"quest_pending": "q5_2"}},
                    {"text": "朕去会会他们。", "next": "q5_3_gist", "need": {"quest_pending": "q5_3"}},
                    {"text": "🤔 那伙贼的来头？", "next": "q5_3_ask", "need": {"quest_pending": "q5_3"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_3"}},
                    {"text": "朕动身了。", "next": "q5_4_gist", "need": {"quest_pending": "q5_4"}},
                    {"text": "🤔 审判庭动手了？", "next": "q5_4_ask", "need": {"quest_pending": "q5_4"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_4"}},
                    {"text": "朕去寻那朵花。", "next": "q5_5_gist", "need": {"quest_pending": "q5_5"}},
                    {"text": "🤔 那花有何古怪？", "next": "q5_5_ask", "need": {"quest_pending": "q5_5"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_5"}},
                ],
            },
            "q5_2_ask": {
                "text": "旁白：腓特烈三世示意近侍退下。『三个问题：魔王是否真死？封印为何日渐松动？圣女为何要逃？教会给的答案，朕一个字都不信。朕要的是地图上的烽火、你亲眼所见的黑气，拼出来的那份真相。』",
                "options": [
                    {"text": "朕愿意。", "next": "q5_2_awe", "need": {"quest_pending": "q5_2"}},
                    {"text": "🤔 那封印到底怎么了？", "next": "q5_2_seal", "need": {"quest_pending": "q5_2"}},
                    {"text": "🤔 圣女殿下她……真的逃了吗？", "next": "q5_2_saint", "need": {"quest_pending": "q5_2"}},
                    {"text": "（再想想，躬身告退）", "next": "__end__", "need": {"quest_pending": "q5_2"}},
                ],
            },
            "q5_2_seal": {
                "text": "旁白：腓特烈三世眉头深锁。『封印维持了多少年、靠什么维持，教会的说法翻来覆去只有一句「圣光庇佑、魔王已死」。可朕的边境守军报回的消息，是裂隙的气息一年比一年重。要么封印真在松动，要么教会藏着更深的东西没敢叫世人看见。』",
                "options": [
                    {"text": "那圣女为何要逃？", "next": "q5_2_saint", "need": {"quest_pending": "q5_2"}},
                    {"text": "朕愿意。", "next": "q5_2_awe", "need": {"quest_pending": "q5_2"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_2"}},
                ],
            },
            "q5_2_saint": {
                "text": "旁白：腓特烈三世轻轻一叹。『圣女艾莉丝失踪，教会说是「堕落出逃」。可据修道院那边传来的零星字句，圣女是「自己」逃的——逃这一字，朕越琢磨越心惊。一个被教会奉为「容器」的圣女，要逃什么？她知道了什么，会令整个教会忌讳到要全国搜捕？』",
                "options": [
                    {"text": "朕愿去查这条路。", "next": "q5_2_awe", "need": {"quest_pending": "q5_2"}},
                    {"text": "🤔 陛下还卖个关子？", "next": "q5_2_seal", "need": {"quest_pending": "q5_2"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_2"}},
                ],
            },
            "q5_2_awe": {
                "text": "旁白：腓特烈三世微微颔首，目光如炬。『好。从今往后，你查到的每一件事，直接向我禀报——不必经过教会、不必经过行会。记住，王都的宫里，墙会说话，眼会看你。』",
                "options": [
                    {"text": "📜 臣/民领命！（接取）", "next": "q5_2_take", "need": {"quest_pending": "q5_2"}, "action": {"set_flag": "king_pledged", "quest_take": True}},
                    {"text": "🤔 陛下可有什么人手可借？", "next": "q5_2_help", "need": {"quest_pending": "q5_2"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_2"}},
                ],
            },
            "q5_2_help": {
                "text": "旁白：腓特烈三世微微摇头。『朕明面上的亲卫，团团被教会的人盯着。倒是那个行会的总会长老约翰——他年轻时在烬山边上待过，认得些「不该认得的人」。你要借势，去找他；朕能借你的，只有这枚信物与一句密约。』",
                "options": [
                    {"text": "📜 臣/民领命！（接取）", "next": "q5_2_take", "need": {"quest_pending": "q5_2"}, "action": {"set_flag": "king_pledged", "quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_2"}},
                ],
            },
            "q5_2_take": {
                "text": "旁白：腓特烈三世将一枚不起眼的王印信物递给你。『带上它。晨曦城会让你进，教会权柄压不到你头上。去吧——王命在身，朕等你的消息。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_3_gist": {
                "text": "旁白：腓特烈三世压低了声音。『别惊动教会的人。金穗平原的粮道连着晨曦城的粮仓，若被人拿了把柄，朕的王座都得晃。把领头的那只「黑鸦」揪出来——他嘴里，多半有线索。』",
                "options": [
                    {"text": "📜 领命！（接取）", "next": "q5_3_take", "need": {"quest_pending": "q5_3"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_3"}},
                ],
            },
            "q5_3_ask": {
                "text": "旁白：腓特烈三世道。『密探回报，那伙人盘踞金穗平原西侧的废弃哨塔，专劫教会往王都送「圣物」的车队。有意思的是——劫完圣物，他们转手就卖。买家是谁，密探还没查出来。』",
                "options": [
                    {"text": "朕去会会他们。", "next": "q5_3_gist", "need": {"quest_pending": "q5_3"}},
                    {"text": "🤔 为何专劫圣物？", "next": "q5_3_relic", "need": {"quest_pending": "q5_3"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_3"}},
                ],
            },
            "q5_3_relic": {
                "text": "旁白：腓特烈三世负手而行。『这正是朕想不通处。教会送圣物的车队，本应重兵护送——可这伙盗贼劫得格外「顺手」，仿佛里应外合。劫走的圣物多是些封着「旧事」的器物。朕猜，有人不想让某些圣物入王都。』",
                "options": [
                    {"text": "那这些圣物后来流向了哪？", "next": "q5_3_flow", "need": {"quest_pending": "q5_3"}},
                    {"text": "朕去会会他们。", "next": "q5_3_gist", "need": {"quest_pending": "q5_3"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_3"}},
                ],
            },
            "q5_3_flow": {
                "text": "旁白：腓特烈三世目光凝重。『密探循着几件「圣物」的去向追查，最后都断在了一道高墙之外——那不是别处，正是大圣堂枢机主教的私库。盗贼抢走的圣物，转了一圈，又回了教会自己人手上。这出戏唱得，朕都替他们脸红。』",
                "options": [
                    {"text": "好一个「监守自盗」。", "next": "q5_3_gist", "need": {"quest_pending": "q5_3"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_3"}},
                ],
            },
            "q5_3_take": {
                "text": "旁白：腓特烈三世亲手为你推开门。『去吧。箭矢再利，也快不过你的剑。记住——留黑鸦一命，朕要知道谁在背后养他。』",
                "options": [
                    {"text": "朕记下了。", "next": "__end__"},
                    {"text": "🤔 若那「背后的人」太棘手……", "next": "q5_3_fall"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_3_fall": {
                "text": "旁白：腓特烈三世目光转沉。『若当真牵出牵连教会的大人物，你莫要逞强贪功。先把消息递回给朕——朕自有计较。真相，值得一步一步揭开，不必拿命去赌那一时半刻。』",
                "options": [
                    {"text": "朕明白了。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_4_gist": {
                "text": "旁白：腓特烈三世目光一沉。『圣女若落到奥古斯都手里，朕这三百年「封印稳固」的招牌，就得由着他一个人写了。替朕把那些猎犬拦下来，拖住审判庭——朕要抢在他们之前，把圣女接到身边。』",
                "options": [
                    {"text": "📜 领命！（接取）", "next": "q5_4_take", "need": {"quest_pending": "q5_4"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_4"}},
                ],
            },
            "q5_4_ask": {
                "text": "旁白：腓特烈三世低声道。『审判猎犬是教会的獠牙，只认「异端」的血味。它们出现在银铃河，说明审判庭已经锁定了圣女的位置。朕的密探正在老约翰那边接应——你沿着河去，别让猎犬咬住她的行踪。』",
                "options": [
                    {"text": "朕动身了。", "next": "q5_4_gist", "need": {"quest_pending": "q5_4"}},
                    {"text": "🤔 审判庭为何非抓圣女不可？", "next": "q5_4_why", "need": {"quest_pending": "q5_4"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_4"}},
                ],
            },
            "q5_4_why": {
                "text": "旁白：腓特烈三世眉峰微蹙。『圣女是「圣光容器」，理论上应被教会奉若至宝。可审判庭却倾巢而出要「猎捕」她——这本身就荒谬。朕思来想去，只有一个可能：圣女知道了不该知道的秘密，而这个秘密，大得让教会宁可撕破脸也要捂住。』",
                "options": [
                    {"text": "那这秘密，多半与封印有关。", "next": "q5_4_hunch", "need": {"quest_pending": "q5_4"}},
                    {"text": "朕动身了。", "next": "q5_4_gist", "need": {"quest_pending": "q5_4"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_4"}},
                ],
            },
            "q5_4_hunch": {
                "text": "旁白：腓特烈三世微微颔首。『你与朕想到一块去了。圣女离宫前，常在藏书阁抄录古籍——而朕的人查到，她临行前一夜，翻过的那卷书，恰好是三百年前那场圣战的「档案」。她看见了不该看见的，审判庭才会这样发狠。』",
                "options": [
                    {"text": "朕去拦下猎犬，保她周全。", "next": "q5_4_gist", "need": {"quest_pending": "q5_4"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_4"}},
                ],
            },
            "q5_4_take": {
                "text": "旁白：腓特烈三世解下腰间的号角递给你。『若遇险，吹响它。晨曦城的城门，永远为你开着。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_5_gist": {
                "text": "旁白：腓特烈三世眉间微蹙。『朕信不过教会，偏这花是教会亲手送进宫的。据说有人在白石修道院附近见过它——修道院那边的黑气，你亲眼见过。朕不知二者是否有关，只求你安稳把花带回来，莫让它再害人。』",
                "options": [
                    {"text": "📜 领命！（接取）", "next": "q5_5_take", "need": {"quest_pending": "q5_5"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_5"}},
                ],
            },
            "q5_5_ask": {
                "text": "旁白：腓特烈三世压低嗓音。『那花通体莹白，据说会吸食人的「气」。王后捧它的头一夜，宫里的花开全枯了。朕的药师断定那花瓣里泡过什么不干净的东西——可教会闭口不谈。你若寻回，先别急着交回朕，自己留神看看。』",
                "options": [
                    {"text": "朕去寻那朵花。", "next": "q5_5_gist", "need": {"quest_pending": "q5_5"}},
                    {"text": "🤔 教会为何要送花进宫？", "next": "q5_5_intent", "need": {"quest_pending": "q5_5"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_5"}},
                ],
            },
            "q5_5_intent": {
                "text": "旁白：腓特烈三世目光微沉。『这正是朕担心的另一桩。教会送「圣物」进宫，说是「祈福庇佑」，实则何尝不是想借王后之榻，把手探进朕的后宫？那花是否“带诅咒”，又是冲着王后来，还是冲着朕来——朕不敢赌。』",
                "options": [
                    {"text": "那教会可有第二个动作？", "next": "q5_5_more", "need": {"quest_pending": "q5_5"}},
                    {"text": "朕去寻那朵花。", "next": "q5_5_gist", "need": {"quest_pending": "q5_5"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_5"}},
                ],
            },
            "q5_5_more": {
                "text": "旁白：腓特烈三世缓缓摇头。『暂时没有。可正是这份「安静」让朕不安。教会若真要动手，不会只送一朵花。你寻回花后，把它带回来，朕命人剖开花瓣，看看到底藏了什么名堂——这或许就是揭开教会这层皮的第一个口子。』",
                "options": [
                    {"text": "朕去寻那朵花。", "next": "q5_5_gist", "need": {"quest_pending": "q5_5"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q5_5"}},
                ],
            },
            "q5_5_take": {
                "text": "旁白：腓特烈三世望着窗外王后憔悴的身影，轻声道。『王后在等你。这朵花，能不能保得住她……朕把话说在前面，若那花真是害人的东西，丢了也无妨，朕只要你平安回来。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "text": "旁白：腓特烈三世按着御案。『王命在身，进度朕都记着。办妥了回来报朕一声；想打听下落，也尽管开口。』『任务』能随时看日志。",
                "options": [
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_2"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_3"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_4"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_5"}},
                    {"text": "📜 陛下，还有别的差遣吗？", "next": "quest_talk", "need": {"quest_pending": "q5_2"}},
                    {"text": "📜 陛下，还有别的差遣吗？", "next": "quest_talk", "need": {"quest_pending": "q5_3"}},
                    {"text": "📜 陛下，还有别的差遣吗？", "next": "quest_talk", "need": {"quest_pending": "q5_4"}},
                    {"text": "📜 陛下，还有别的差遣吗？", "next": "quest_talk", "need": {"quest_pending": "q5_5"}},
                    {"text": "🗺️ 王命进展如何？", "next": "progress"},
                    {"text": "好，臣/民知道了。", "next": "__end__"},
                ],
            },
            "progress": {
                "texts": [
                    {"need": {"quest_active": "q5_3"},
                     "text": "旁白：腓特烈三世微不可察地点头。『金穗平原那边，密探又送来一封。那伙盗贼昨夜劫了教会车队，正往西边山林里迁。若它们动了，你晚一步就可能扑空——动作快些。』"},
                    {"need": {"quest_active": "q5_4"},
                     "text": "旁白：腓特烈三世的神情骤然凝住。『银铃河刚传来消息——审叛庭的猎犬又吠又咬，有人看见几道白袍影在河边出没。圣女怕是被堵住了。你抄近道沿河而下，千万抢在审判庭之前。』"},
                    {"need": {"quest_active": "q5_5"},
                     "text": "旁白：腓特烈三世低声道。『修道院那边传来风声，说那花的影像曾在院墙根的泥里被看到。你带上鼻子灵一些的向导，别错过了。』"},
                ],
                "text": "旁白：腓特烈三世静候下文。『王命在途，朕等你的消息。』",
                "options": [
                    {"text": "朕这就去办。", "next": "__end__"},
                    {"text": "🤔 陛下可还有什么要叮嘱的？", "next": "progress_detail"},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_2"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_3"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_4"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "progress_detail": {
                "texts": [
                    {"need": {"quest_active": "q5_3"},
                     "text": "旁白：腓特烈三世叮嘱道。『黑鸦那伙人虽凶，却并非铁板一块——他们多是活不下去的流民被裹挟入伍。你若能擒得头目，留他一口气，多半能问出「背后是谁」的真话。莫一味赶尽杀绝，留个活口，比砍十万颗头都有用。』"},
                    {"need": {"quest_active": "q5_4"},
                     "text": "旁白：腓特烈三世沉声道。『审判猎犬嗅觉灵敏，正面硬拼只会引来更多追兵。猎犬恐火、畏烟——你若带上火折子与烟硝，沿河而上时寻一处烟火，能暂时甩开它们的嗅觉。』"},
                    {"need": {"quest_active": "q5_5"},
                     "text": "旁白：腓特烈三世提醒。『那花被窃多日，恐怕已不在修道院。传闻盗花者贪财，或已转手至黑市。你可先往行会的赏金榜与铁港城的当铺打听——说不定能顺藤摸瓜。』"},
                ],
                "text": "旁白：腓特烈三世静候下文。『王命在途，朕等你的消息。』",
                "options": [
                    {"text": "朕记下了。", "next": "__end__"},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_2"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_3"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_4"}},
                    {"text": "✅ 陛下，王命完成了！", "next": "quest_done_talk", "need": {"quest_ready": "q5_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q5_2"},
                     "text": "旁白：腓特烈三世亲自起身相迎。『你来了。老约翰的信、你带回来的每一句话，朕都听进去了。从今往后，你查到的每一件事，直接向朕禀报——不必经过教会，不必经过行会。这个王印，是你与朕之间的密约。』"},
                    {"need": {"quest_ready": "q5_3"},
                     "text": "旁白：腓特烈三世摩挲着密探送回的徽记。『盗贼的头目黑鸦，临死前喊的那句「背后养我们的人」……朕听密探回报了。这话，朕记下了。你替朕揪出的这块遮掩布，比想象中要厚。』"},
                    {"need": {"quest_ready": "q5_4"},
                     "text": "旁白：腓特烈三世神色肃穆。『审判庭的猎犬被你拦下了。银铃河的风声暂时平息——可圣女的路，朕记得还长。先收下朕的谢意，日夜还有用你之处。』"},
                    {"need": {"quest_ready": "q5_5"},
                     "text": "旁白：腓特烈三世接过圣光百合，指尖在花瓣上顿住，脸色微变。『……这气息，朕认得。深渊的腥味，竟渗在一朵教会送来的圣花里。王后遭逢此物，日夜忧惧，是朕之过。花朕收下了，你这份人情，朕永志不忘。』"},
                ],
                "text": "旁白：腓特烈三世颔首。『王命办妥了，你有功于国。这是朕的一点心意，收下吧。』",
                "options": [
                    {"text": "💰 收下王命赏赐。", "next": "deliver_after", "need": {"quest_ready": "q5_2"}, "action": {"quest_take": True}},
                    {"text": "💰 收下王命赏赐。", "next": "deliver_after", "need": {"quest_ready": "q5_3"}, "action": {"set_flag": "king_heard_blackcrow", "quest_take": True}},
                    {"text": "💰 收下王命赏赐。", "next": "deliver_after", "need": {"quest_ready": "q5_4"}, "action": {"quest_take": True}},
                    {"text": "💰 收下王命赏赐。", "next": "deliver_after", "need": {"quest_ready": "q5_5"}, "action": {"quest_take": True}},
                    {"text": "🤔 陛下还有什么嘱咐？", "next": "q5_5_seed"},
                ],
            },
            "deliver_after": {
                "texts": [
                    {"need": {"quest_done": "q5_2"},
                     "text": "旁白：腓特烈三世望着你远去的方向，低声道。『这趟浑水，朕本不该拉你进来。可朕……没得选。愿你手中的剑，能替朕，也替你，守住这一方真相。』"},
                    {"need": {"quest_done": "q5_3"},
                     "text": "旁白：腓特烈三世的目光沉了沉。『那伙「盗贼」的精良兵器，朕已命匠人取样化验——兵刃上淬着一种教会的秘药。看来，养他们的“主”，与教会脱不了干系。你走得越深，越要当心脚下。』"},
                    {"need": {"quest_done": "q5_4"},
                     "text": "旁白：腓特烈三世将一枚暗哨令塞进你手心。『银铃河一役，朕欠圣女一条命。若你日后寻到她，替朕带一句话——王都的王座，愿意为她、为真相，留一盏灯。』"},
                    {"need": {"quest_done": "q5_5"},
                     "text": "旁白：腓特烈三世负手立于窗前。『那朵圣花里的深渊气息，朕已着专人封存。记着：教会送出的每一件「圣物」，或许都染着你不该看见的东西。你手上的线索越积越多，终有一日，会拼成那把打开真相的钥匙。』"},
                ],
                "text": "旁白：腓特烈三世亲自为你斟了一杯酒。『敬，与朕共守真相的冒险者。日后无论你在何方，晨曦城的门，永远为你开。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_5_seed": {
                "text": "旁白：腓特烈三世忽而压低声音。『最后一句话，你且放在心里——若有一日，晨曦城的城门上挂了黑旗，大圣堂的钟不再为我而鸣……你就按这个信物，去找一个人。他欠着朕一条命。』",
                "options": [
                    {"text": "告辞。", "next": "__end__", "action": {"set_flag": "king_seed"}},
                ],
            },
        },
    },
    "npc_knight_commander": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q11_2"},
                     "text": "旁白：罗兰·圣剑自大圣堂的断阶上走来，教皇已脱困。『教皇格里高利九世醒了。奥古斯都本人还在祭坛上。他说要让我们「看看真正的圣光」——我想，是时候让他看看我们一路走到这里的剑光。』"},
                    {"need": {"quest_done": "q11_1"},
                     "text": "旁白：罗兰·圣剑立于骑士团残破的门前，甲胄上还沾着灰。『奥古斯都疯了。囚禁教皇、宣布国王为叛教者……这已经不是为了圣光，是为了权柄。我们必须进大圣堂。』"},
                    {"need": {"quest_done": "q6_6"},
                     "text": "旁白：罗兰·圣剑的佩剑已换成一柄无刃的木剑，神情沉静许多。『晨曦城那边，我自会去处理。你按你的路走下去——若有需要，我的剑听你号令。』"},
                    {"need": {"quest_done": "q5_6"},
                     "text": "旁白：罗兰·圣剑望着你，目光里多了一丝认可。『你的剑里有信念。我正要去执行一项任务——追捕一名「叛教者」。但愿我的剑……不会用错地方。』"},
                ],
                "text": "旁白：晨曦城骑士团驻地的校武场上，罗兰·圣剑收剑而立。『骑士的剑只为守护而挥。你既找上门来，想必不是为了空谈——来吧，让我看看你的本事。』",
                "options": [
                    {"text": "⚔️ 团长，我想讨教剑术。", "next": "quest_talk", "need": {"quest_pending": "q5_6"}},
                    {"text": "⚔️ 团长，我想讨教剑术。", "next": "quest_talk", "need": {"quest_pending": "q6_6"}},
                    {"text": "⚔️ 团长，我想讨教剑术。", "next": "quest_talk", "need": {"quest_pending": "q11_1"}},
                    {"text": "⚔️ 团长，我想讨教剑术。", "next": "quest_talk", "need": {"quest_pending": "q11_2"}},
                    {"text": "⚔️ 团长，我想讨教剑术。", "next": "quest_talk", "need": {"quest_pending": "q11_3"}},
                    {"text": "我手头的任务……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q5_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q6_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_1"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_2"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_3"}},
                    {"text": "🗺️ 团长，近来骑士团可有动静？", "next": "barracks"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "barracks": {
                "text": "旁白：罗兰·圣剑目光扫过训练的骑士，沉声道。『圣光骑士团的剑，本为守护而生。可近年来，教廷越来越喜欢让骑士去做「审判」的事。若有一日，剑锋指向无辜——那剑就不配握在手里。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q5_6"},
                     "text": "旁白：罗兰·圣剑解下披风，露出一柄长剑。『我听说你一路从橡木镇打到铁港城，又见了些不该见的东西。骑士的剑只为守护而挥——可当发现剑锋指向的是无辜者时，我会先折断它。拔剑吧，让我看看你挥剑是为了什么。』"},
                    {"need": {"quest_pending": "q6_6"},
                     "text": "旁白：罗兰·圣剑的剑鞘里，那柄曾为他斩杀无数「异端」的长剑，泛着冷光。他望着你，沉默良久。『我这一生的剑，曾指向过不该指向的人。现在，我要回晨曦城，当着圣光的誓约之厅，把这把剑……折断。你，愿意做我的见证人吗？』"},
                    {"need": {"quest_pending": "q11_1"},
                     "text": "旁白：晨曦城城门紧闭，圣光骑士团的旗帜已被换下，取而代之的是审判庭的黑旗。罗兰·圣剑立于城门外石阶上，面沉如水。『奥古斯都疯了！他囚禁了教皇，宣布国王是叛教者——我没拦住他，还被他夺了旗。现在，整个王都都落在他手里。』"},
                    {"need": {"quest_pending": "q11_2"},
                     "text": "旁白：晨曦大圣堂的大门紧闭，审判庭的守卫在廊柱后探头。罗兰·圣剑握紧剑柄。『教皇就在里面——他被奥古斯都关了太久，再拖下去只怕撑不住。大圣堂的门我认得，可里面有多少审判庭的人，我不清楚。这一仗，只能硬闯。』"},
                    {"need": {"quest_pending": "q11_3"},
                     "text": "旁白：祭坛之上，奥古斯都的身影在圣光中显得格外狰狞。罗兰·圣剑的目光像钉住猎物的鹰隼。『他就在那儿——奥古斯都。我追随过的「圣光」，竟成了这副模样。这一次，我不再为他而挥剑。剑要指向的，是这桩骗了三百年的谎。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "⚔️ 请教团长！", "next": "roland_trial", "need": {"quest_pending": "q5_6"}},
                    {"text": "🤔 团长为何要折剑？", "next": "roland_ask", "need": {"quest_pending": "q5_6"}},
                    {"text": "🤔 那「叛教者」是谁？", "next": "roland_target", "need": {"quest_pending": "q5_6"}},
                    {"text": "（自知不敌，躬身告退）", "next": "__end__", "need": {"quest_pending": "q5_6"}},
                    {"text": "好，我护送你回晨曦城。", "next": "oath_intro", "need": {"quest_pending": "q6_6"}},
                    {"text": "🤔 团长真的要折剑？", "next": "oath_ask", "need": {"quest_pending": "q6_6"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q6_6"}},
                    {"text": "⚔️ 团长，我们一起打进去。", "next": "coup_intro", "need": {"quest_pending": "q11_1"}},
                    {"text": "🤔 教皇和国王殿下怎么样了？", "next": "coup_ask", "need": {"quest_pending": "q11_1"}},
                    {"text": "（先撤，探明敌情再说）", "next": "__end__", "need": {"quest_pending": "q11_1"}},
                    {"text": "⚔️ 攻进去，救出教皇殿下！", "next": "cathedral_intro", "need": {"quest_pending": "q11_2"}},
                    {"text": "🤔 教皇殿下还撑得住吗？", "next": "cathedral_ask", "need": {"quest_pending": "q11_2"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q11_2"}},
                    {"text": "⚔️ 让我们一起了结他！", "next": "august_intro", "need": {"quest_pending": "q11_3"}},
                    {"text": "🤔 他这是要毁掉王国还是圣光？", "next": "august_warp", "need": {"quest_pending": "q11_3"}},
                    {"text": "🤔 他到底说了什么？", "next": "august_ask", "need": {"quest_pending": "q11_3"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q11_3"}},
                ],
            },
            "roland_ask": {
                "text": "旁白：罗兰·圣剑指腹抚过剑脊。『二十年前，我曾奉命剿灭一支「被深渊污染的村庄」。到了那里才发现，那不过是一群被教会冤屈的农人。从那天起我明白——剑可以折，但不可葬无辜者之血。』",
                "options": [
                    {"text": "那团长这二十年……怎么过来的？", "next": "roland_twenty", "need": {"quest_pending": "q5_6"}},
                    {"text": "⚔️ 请教团长！", "next": "roland_trial", "need": {"quest_pending": "q5_6"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_6"}},
                ],
            },
            "roland_twenty": {
                "text": "旁白：罗兰·圣剑的目光扫过校武场边的骑士营帐。『我一边挥剑，一边在等一个答案——等有一天，能分清圣光的命令与圣光的本心。这二十年，我砍过「异端」，也救过被误伤的魂灵，直到那天，一张熟悉的脸让我彻底下定了决心。』",
                "options": [
                    {"text": "那张脸，是圣女殿下吗？", "next": "roland_saint", "need": {"quest_pending": "q5_6"}},
                    {"text": "⚔️ 请教团长！", "next": "roland_trial", "need": {"quest_pending": "q5_6"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_6"}},
                ],
            },
            "roland_saint": {
                "text": "旁白：罗兰·圣剑沉默了一瞬。『是……我认得她。可她本该是教会的「圣光容器」，为何要用审判庭的猎犬去追她？她眼里的光，没有一丝堕落。正是那一眼，我才明白我一直在替谁挥剑。』（——此情对应圣女视角 q6_3/q6_4，E 组对齐）",
                "options": [
                    {"text": "⚔️ 请教团长！", "next": "roland_trial", "need": {"quest_pending": "q5_6"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_6"}},
                ],
            },
            "roland_target": {
                "text": "旁白：罗兰·圣剑望着远方。『教会唤她是「叛教者」，可她不叛圣光，只叛教会的「谎」。我奉命去追她——可如今，我想先弄清这「谎」到底是什么，再决定这一剑要不要出鞘。』",
                "options": [
                    {"text": "那团长与她……可曾相识？", "next": "roland_saint", "need": {"quest_pending": "q5_6"}},
                    {"text": "⚔️ 请教团长！", "next": "roland_trial", "need": {"quest_pending": "q5_6"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_6"}},
                ],
            },
            "roland_trial": {
                "text": "旁白：罗兰·圣剑缓缓拔出长剑，剑尖直指地面。『骑士的剑，只为你守护的东西而挥。若你心中没有要守护的什么——这一战，你会输得很惨。拔剑。』",
                "options": [
                    {"text": "📜 接招！（接取）", "next": "roland_trial_take", "need": {"quest_pending": "q5_6"}, "action": {"quest_take": True}},
                    {"text": "🤔 若我守护的，正是团长该杀的「叛教者」呢？", "next": "roland_boundary", "need": {"quest_pending": "q5_6"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_6"}},
                ],
            },
            "roland_boundary": {
                "text": "旁白：罗兰·圣剑的动作一顿。『那便是今夜这一战的答案——我的剑，会不会为了「命令」而指向你所守护的无辜。若答案是不会，你我便是同路人；若你敢替无辜者挡在我面前，我这一剑便不配落下。』",
                "options": [
                    {"text": "📜 接招！（接取）", "next": "roland_trial_take", "need": {"quest_pending": "q5_6"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q5_6"}},
                ],
            },
            "roland_trial_take": {
                "text": "旁白：罗兰·圣剑举剑过顶。『很好的起手。愿你的剑，永远只为守护而挥——不论教会，不论谁的命令。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                    {"text": "🤔 团长说的「追捕任务」……", "next": "roland_hint"},
                ],
            },
            "roland_hint": {
                "text": "旁白：罗兰·圣剑收剑入鞘。『正是。追捕一名教会唤作「叛教者」的人。若你我日后剑锋相向……愿那一刻，我们还记得今夜说过的话。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "oath_ask": {
                "text": "旁白：罗兰·圣剑抚过剑柄上的圣光骑士团纹章。『这一剑，曾为「圣光」而挥，曾为「教会」而挥。可我追捕了圣女二十年，才发现她眼底的光，比所有教会的说辞都真。这把剑若再握下去，下一剑要指向的，就是真相的守护者。我不允许。』",
                "options": [
                    {"text": "好，我护送你回晨曦城。", "next": "oath_intro", "need": {"quest_pending": "q6_6"}},
                    {"text": "（再想想）", "next": "__end__", "need": {"quest_pending": "q6_6"}},
                ],
            },
            "oath_intro": {
                "text": "旁白：罗兰·圣剑点头，迈步向城门走去。『走吧。晨曦城那边，我欠所有人一个交代。你既是见证人，就该亲眼看看——这一剑断得值不值。』",
                "options": [
                    {"text": "📜 护送团长起程！（接取）", "next": "oath_intro2", "need": {"quest_pending": "q6_6"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q6_6"}},
                ],
            },
            "oath_intro2": {
                "text": "旁白：踏上回晨曦城的路，罗兰·圣剑的话比平日更少。夕阳把两道影子拉得很长。良久，他开口。『这一路，是我向过去告别的路。等进了誓约之厅，你只管看着——那一声脆响之后，罗兰·圣剑这个人，就和那把剑一起，脱胎换骨。』",
                "options": [
                    {"text": "我等着看。", "next": "oath_arena_lead"},
                    {"text": "（静默同行）", "next": "oath_arena_lead"},
                ],
            },
            "oath_arena_lead": {
                "text": "旁白：晨曦城的暮色里，圣光誓约之厅的大门缓缓推开。厅内灯火通明，骑士团上下早已列队站定——他们望着曾经敬仰的团长，无人敢出声。罗兰·圣剑迈步而入，每一步都像踏在自己的旧誓上。",
                "options": [
                    {"text": "（随团长步入厅心）", "next": "oath_arena"},
                    {"text": "（在门前驻足，静候）", "next": "oath_arena"},
                ],
            },
            "oath_arena": {
                "text": "旁白：晨曦城，圣光誓约之厅。三百年来，圣光骑士团团长在此立誓效忠圣光——罗兰·圣剑却一步步走到厅心，将佩剑平举于胸前。满厅肃静，只有他手中的剑泛着冷光。『这把剑，跟了我二十年。它替我「守护」过教会，也替我「守护」过一个个被冤屈的名字——可我刚刚才想明白，很多时候，它是用错了地方。』",
                "options": [
                    {"text": "团长，值得吗？", "next": "oath_worth"},
                    {"text": "（静默以待）", "next": "oath_silent"},
                ],
            },
            "oath_worth": {
                "text": "旁白：罗兰·圣剑的目光巡过誓约之厅的浮雕——那些描绘「英雄王斩杀魔王」的画。『圣光骑士团立团的信条只有一句：剑，只为守护而挥。为了一个圣光不该守护的谎言，我挥了二十年剑。如今折了它，才算把这条信条，立回正处。值不值，我心里清楚。』",
                "options": [
                    {"text": "（继续看着）", "next": "oath_crack"},
                    {"text": "团长，我替你把守厅门。", "next": "oath_crack"},
                ],
            },
            "oath_silent": {
                "text": "旁白：你没有说话。罗兰·圣剑冲你微微颔首，似在致谢——那份沉默胜过了千言万语。他缓缓抬手，将长剑举过头顶。",
                "options": [
                    {"text": "（继续看着）", "next": "oath_crack"},
                    {"text": "团长，我替你守着。", "next": "oath_crack"},
                ],
            },
            "oath_crack": {
                "text": "旁白：罗兰·圣剑双手握剑，猛力一折——咔嚓一声脆响，那柄曾追随他二十年的圣剑，断成两截。半截剑身砸在厅石上，发出清越的悲鸣。罗兰·圣剑跪地，拾起断刃，声音沙哑却字字清晰。『从今天起，我的剑只守护真相。谁要再让我用剑去指无辜者——先踏过我的尸骨。』",
                "options": [
                    {"text": "🤝 团长，从今往后，你我并肩。（表承诺，埋第 11 章 flag 语感）", "next": "oath_hall", "action": {"set_flag": "sword_sworn"}},
                    {"text": "🗡️ 这半截断刃，我替你收着。", "next": "oath_hall"},
                ],
            },
            "oath_hall": {
                "text": "旁白：断剑的脆响在誓约之厅里回荡了很久很久。骑士团众人面面相觑，有人眼眶泛红，有人攥紧拳头，却无一人出声斥责——他们也曾在「圣光的名义」下举起过剑。罗兰·圣剑将断剑高举过顶，让所有人都能看清。『我只求你们记住今夜这把断剑——圣光骑士团的剑，从今往后，只守护真相，不再守护谎言。』",
                "options": [
                    {"text": "（向团长深深一礼）", "next": "oath_ally"},
                    {"text": "🤝 我与你一同立誓。", "next": "oath_ally"},
                    {"text": "🗡️ 这半截断刃，我替你收着。", "next": "oath_keepsake"},
                ],
            },
            "oath_ally": {
                "text": "旁白：罗兰·圣剑缓缓起身，将断刃的一截收入怀中，伸出一只沾着铁锈的手。『你信我，我便信你。圣光骑士团今日之后，可能不再是教廷的刀——但会是你最可靠的盾。去吧，西境的精灵史书里，有完整的圣战。这里，交给我收拾。』",
                "options": [
                    {"text": "✅ 见证完成。", "next": "oath_take", "need": {"quest_ready": "q6_6"}, "action": {"quest_take": True}},
                ],
            },
            "oath_keepsake": {
                "text": "旁白：罗兰·圣剑将半截断刃递到你面前，目光坦然。『替我留着也好。它提醒我，也提醒看过这一幕的人——守护的界限，比挥剑的腕力更重要。你替我留着半截，我替你们守着这条路。』",
                "options": [
                    {"text": "✅ 见证完成。", "next": "oath_take", "need": {"quest_ready": "q6_6"}, "action": {"quest_take": True, "set_flag": "oath_witness"}},
                ],
            },
            "oath_take": {
                "text": "旁白：罗兰·圣剑望着厅外骑士团排列的队列。『从今天起，你们的剑问心无愧。教会震怒也罢、奥古斯都也罢——我起誓，不会再让圣光的名字，被当作屠刀。你们去西境吧，精灵的史书，记得完整的故事。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "coup_ask": {
                "text": "旁白：罗兰·圣剑压低声音。『教皇格里高利九世被他关在大圣堂里，国王腓特烈三世被宣布为「叛教者」、困在王宫。他想用「最终封印」之名，献祭整座白鹿城来「彻底封住魔王」——这已经不是守护圣光，是拿万人骨血铺他的权柄。』",
                "options": [
                    {"text": "⚔️ 团长，我们一起打进去。", "next": "coup_intro", "need": {"quest_pending": "q11_1"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_1"}},
                ],
            },
            "coup_intro": {
                "text": "旁白：罗兰·圣剑解下染血的披风，握紧断剑重铸的新刃。『这一战，我的剑只为真相而挥。进城的门道我熟——你随我来，先夺回大圣堂，救出教皇。』",
                "options": [
                    {"text": "📜 随团长行动！（接取）", "next": "coup_take", "need": {"quest_pending": "q11_1"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_1"}},
                ],
            },
            "coup_take": {
                "text": "旁白：罗兰·圣剑替你推开城门暗格的铁门。『记住，若你我失散，就在大圣堂西侧廊道汇合。圣光骑士团的门徒……会认出这把断剑指引的门。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "cathedral_ask": {
                "text": "旁白：罗兰·圣剑目光落在圣堂塔尖的钟上。『他被关在祭坛后的囚室里，靠着最后一点圣光吊着口气。奥古斯都说要让他「亲眼看看真正的圣光」——我想，那多半是血光。我们得抢在那之前。』",
                "options": [
                    {"text": "⚔️ 攻进去，救出教皇殿下！", "next": "cathedral_intro", "need": {"quest_pending": "q11_2"}},
                    {"text": "🤔 那圣堂里有多少审判庭的人？", "next": "cathedral_guard", "need": {"quest_pending": "q11_2"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_2"}},
                ],
            },
            "cathedral_guard": {
                "text": "旁白：罗兰·圣剑压低声音。『大圣堂平日归我骑士团护卫，如今尽数换上审判庭的黑袍——至少三层封锁，外殿、中殿、祭坛各一批。硬闯伤亡大，我建议你正面佯攻吸引主力，我从旧甬道潜进去，先保住教皇的命。』",
                "options": [
                    {"text": "⚔️ 好，分头行事。", "next": "cathedral_intro", "need": {"quest_pending": "q11_2"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_2"}},
                ],
            },
            "cathedral_intro": {
                "text": "旁白：罗兰·圣剑抬手，示意身后的骑士掩近。『我拆过这座圣堂的门。你从正门佯攻，我带人从侧翼潜进去接应教皇。门开的那一刻，你我正面汇合。』",
                "options": [
                    {"text": "📜 动手！（接取）", "next": "cathedral_take", "need": {"quest_pending": "q11_2"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_2"}},
                ],
            },
            "cathedral_take": {
                "text": "旁白：罗兰·圣剑压低身形，剑尖微垂。『圣光……不，我的剑声，就是信号。进！』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "august_warp": {
                "text": "旁白：罗兰·圣剑深吸一口气。『他做这一切，「最终封印」、「献祭城镇」，说穿了是要让封印永远不破、让「魔王」永远活在传说里——那样，人们才会永远仰望他主宰的圣光。他输给的不是我们，是这场三百年的谎。』",
                "options": [
                    {"text": "⚔️ 那便让他看清真相。", "next": "august_intro", "need": {"quest_pending": "q11_3"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_3"}},
                ],
            },
            "august_ask": {
                "text": "旁白：罗兰·圣剑沉声道。『他说——「为了圣光的荣耀，牺牲是必要的。」他说人们根本不懂权力与信仰的关系；只要魔王还活在传说里，人们才会永远仰望圣光——他守护的根本不是圣光，是那尊「神龛」里的权柄。』（奥古斯都的咆哮自祭坛传来，你听见那句「让你们看看真正的圣光」。）",
                "options": [
                    {"text": "⚔️ 让我们一起了结他！", "next": "august_intro", "need": {"quest_pending": "q11_3"}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_3"}},
                ],
            },
            "august_intro": {
                "text": "旁白：罗兰·圣剑迈步向前，断剑重铸的新刃在手中嗡嗡低鸣。『他囚了教皇、夺了王都、宣布国王为叛教者——而这背后，不过想用一座城的血，换来「封印稳固」的假象。他今日的败，只因剑已不再为他守护。上吧，你打的是他的权柄，我斩的是他的谎言。』",
                "options": [
                    {"text": "📜 上！（接取）", "next": "august_take", "need": {"quest_pending": "q11_3"}, "action": {"quest_take": True}},
                    {"text": "（再想想）", "next": "welcome", "need": {"quest_pending": "q11_3"}},
                ],
            },
            "august_take": {
                "text": "旁白：罗兰·圣剑脚下一蹬，身形如电掠向祭坛。『奥古斯都！圣光的账，我们来当面算！』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "text": "旁白：罗兰·圣剑静立于晨曦城一角。『进度我记着。办妥了回来递个话；想听下一步，也尽管问。『任务』能随时看目标。",
                "options": [
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q5_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q6_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_1"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_2"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_3"}},
                    {"text": "⚔️ 团长，我们继续。", "next": "quest_talk", "need": {"quest_pending": "q5_6"}},
                    {"text": "⚔️ 团长，我们继续。", "next": "quest_talk", "need": {"quest_pending": "q6_6"}},
                    {"text": "⚔️ 团长，我们继续。", "next": "quest_talk", "need": {"quest_pending": "q11_1"}},
                    {"text": "⚔️ 团长，我们继续。", "next": "quest_talk", "need": {"quest_pending": "q11_2"}},
                    {"text": "⚔️ 团长，我们继续。", "next": "quest_talk", "need": {"quest_pending": "q11_3"}},
                    {"text": "🗺️ 任务进展如何？", "next": "progress"},
                    {"text": "好，我知道了。", "next": "__end__"},
                ],
            },
            "progress": {
                "texts": [
                    {"need": {"quest_active": "q6_6"},
                     "text": "旁白：罗兰·圣剑行至半途，回望远方。『晨曦城的城墙已经能看见了。我要在进城前想清楚，如何向满厅前袍泽、向那一双双曾追随我的眼睛，解释这一切。』"},
                    {"need": {"quest_active": "q11_1"},
                     "text": "旁白：罗兰·圣剑压低声音。『城门那边换了黑旗，审判庭的巡军每隔半个时辰一班。我带你们从城墙的旧甬道潜入——我当团长多年，这条「救生路」是我自己留的。』"},
                    {"need": {"quest_active": "q11_2"},
                     "text": "旁白：罗兰·圣剑贴着大圣堂的侧墙。『守卫换岗有一瞬的空当。教皇被关在祭坛后的暗格，门锁只有奥古斯都的钥匙——但钥匙孔，我可以替你撬开。』"},
                    {"need": {"quest_active": "q11_3"},
                     "text": "旁白：罗兰·圣剑握紧剑柄，目光锁死祭坛。『奥古斯都身边还有审判庭的精锐护着。你攻他身前，我绕他身后——他困在「魔王传说」里太久，脚下已没有路了。』"},
                ],
                "text": "旁白：罗兰·圣剑拭剑而立。『团长的路，不问成败，只问对错。』",
                "options": [
                    {"text": "我们这就去办。", "next": "__end__"},
                    {"text": "🤔 可有什么要小心的？", "next": "roland_detail"},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q5_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q6_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_1"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_2"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "roland_detail": {
                "texts": [
                    {"need": {"quest_active": "q6_6"},
                     "text": "旁白：罗兰·圣剑在前头引路，回头叮嘱。『晨曦城有教会的眼线，入城后切莫声张我与你的关系。进城这段，权当你我陌生旅人同行——免得横生枝节，坏事。』"},
                    {"need": {"quest_active": "q11_1"},
                     "text": "旁白：罗兰·圣剑压低声音。『城墙旧甬道入口在城东铁匠铺的柴房后面，门口的砖石有一块松动。你先摸进去探路，我在外面接应——若动静太大，就放烟火为号，我立刻合围。』"},
                    {"need": {"quest_active": "q11_2"},
                     "text": "旁白：罗兰·圣剑叮嘱。『进了大圣堂，别恋战，直奔祭坛后的囚室。教皇的命比杀几个审判庭的人金贵得多——只要他还活着，我们就有翻身的一日。』"},
                    {"need": {"quest_active": "q11_3"},
                     "text": "旁白：罗兰·圣剑最后交底。『奥古斯都被审判庭的精锐护卫们围着。你攻正面，务必牵制住他的卫队；我绕到他身后一击。他若祭出「圣光」的幻象，别慌——那不过是唬人的把戏，剑指向他的本名，他必现形。』"},
                ],
                "text": "旁白：罗兰·圣剑拭剑而立。『团长的路，不问成败，只问对错。』",
                "options": [
                    {"text": "我记下了。", "next": "__end__"},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q5_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q6_6"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_1"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_2"}},
                    {"text": "✅ 团长，事情办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_3"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q5_6"},
                     "text": "旁白：罗兰·圣剑收剑入鞘，额角沁着细汗，却冲你微微颔首。『你的剑里有信念，不是蛮力。很好——最近我要去执行一项任务，追捕一名「叛教者」。希望我的剑，不会用错地方。愿它，和你的一样，只为守护而挥。』"},
                    {"need": {"quest_ready": "q6_6"},
                     "text": "旁白：罗兰·圣剑望着断成两截的剑，声音平静而沉重。『圣光骑士团团长倒戈了。教会震怒也好、奥古斯都暴跳也罢——我的剑，从今天起只听真相的号令。你们去西境吧，精灵的史书里，有完整的圣战。我留在这里，替你们守好这条退路。』"},
                    {"need": {"quest_ready": "q11_1"},
                     "text": "旁白：罗兰·圣剑吐出一口浊气。『城回到我们手里了，可这不代表安全——奥古斯都还有大圣堂这张牌。教皇被困在里面，你若不去救他，下一步他要拿整座白鹿城做「祭品」。接下来，我们去大圣堂。』"},
                    {"need": {"quest_ready": "q11_2"},
                     "text": "旁白：大圣堂的门被你撞开的一刻，囚室里传来教皇虚弱而坚定的声音——罗兰·圣剑转述给你：『教皇格里高利九世说——「我错信了奥古斯都……他打着圣光的名义，做的却是魔鬼的事。孩子，圣光真正的样子，是你心中的正义。」他老人家把最后一口气，留给了这句话。而我们，还有奥古斯都要了结。』"},
                    {"need": {"quest_ready": "q11_3"},
                     "text": "旁白：罗兰·圣剑立于奥古斯都倒下的圣堂阶梯前，剑尖指地。『他到最后还在喊「封印要破了」。可我看得很清楚——一百年、一百年用血去「献祭」换来的所谓封印，才是最深的谎。我折断过剑，现在，我陪你走完这最后一程真相。』"},
                ],
                "text": "旁白：罗兰·圣剑颔首。『办妥了。你的剑，问心无愧。收下这个吧。』",
                "options": [
                    {"text": "💰 收下团长的谢意。", "next": "__end__", "need": {"quest_ready": "q5_6"}, "action": {"set_flag": "roland_met", "quest_take": True}},
                    {"text": "💰 收下团长的谢意。", "next": "__end__", "need": {"quest_ready": "q6_6"}, "action": {"quest_take": True}},
                    {"text": "💰 收下团长的谢意。", "next": "__end__", "need": {"quest_ready": "q11_1"}, "action": {"quest_take": True}},
                    {"text": "💰 收下团长的谢意。", "next": "__end__", "need": {"quest_ready": "q11_2"}, "action": {"quest_take": True}},
                    {"text": "💰 收下团长的谢意。", "next": "__end__", "need": {"quest_ready": "q11_3"}, "action": {"quest_take": True}},
                    {"text": "🤝 团长，往后我们并肩到黎明。", "next": "ally_promise"},
                ],
            },
            "ally_promise": {
                "text": "旁白：罗兰·圣剑伸出手，与你的手紧握在断剑的纹路之上。『从今天起，你的剑与我的剑，是同一面护盾。去烬山也好、去见那位守夜者也罢——我陪你到最后一道封印。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
    "npc_pope": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q11_5"},
                     "text": "旁白：教皇·格里高利九世低垂着眼，声音温和。『忏悔已毕，祝福已予。孩子，带着那颗「愿意守护真相之心」走下去吧——圣光，会为你点灯。』"},
                    {"need": {"quest_active": "q11_5"},
                     "text": "旁白：教皇·格里高利九世望着你，目光里带着托付后的安然。『孩子，该说的都说与你了。你若再想听些旧事，或是要领受圣光的祝福，随时来找我。这座金笼，关得住我的人，关不住我交给你的那道光。』"},
                ],
                "text": "旁白：晨曦大圣堂的侧厢，教皇·格里高利九世躺在软垫上，面色苍白，眼中却带着一丝清亮。『孩子，你来了。这些时日我一直在想——我这一生，守的到底是圣光，还是那个被教会编了三百年的谎。』",
                "options": [
                    {"text": "🙏 教皇殿下，请讲。", "next": "quest_talk", "need": {"quest_pending": "q11_5"}},
                    {"text": "教皇殿下，您的身体……", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "✅ 教皇殿下，忏悔作完了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_5"}},
                    {"text": "🗺️ 教皇殿下，教会的未来……", "next": "blessing_talk"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "blessing_talk": {
                "text": "旁白：教皇·格里高利九世轻叹一声。『教会欠这世道一个真面目。我愿你替我去纠正这一切——不是用圣光的强权，而是用你脚下的路，让世人看见「圣光真正的样子」是什么。』",
                "options": [
                    {"text": "🗺️ 殿下，能与我多谈谈教会的往事吗？", "next": "pope_history"},
                    {"text": "（告辞）", "next": "__end__"},
                ],
            },
            "crown_talk": {
                "text": "旁白：教皇·格里高利九世苦笑道。『世人说「王权与神权并立」，可三百年来，这两顶冠冕其实都压在同一根谎言铸成的梁上。国王腓特烈三世想查真相，教会想捂真相——到头来，受罪的还是田间地头那些相信着圣光的老百姓。』",
                "options": [
                    {"text": "🗺️ 那殿下认为，谁来守护百姓？", "next": "crown_guard"},
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "crown_guard": {
                "text": "旁白：教皇·格里高利九世目光温和。『不是王权，也不是神权——是你这样的普通人站出来，愿意为了真相反抗谎言的那一刻，圣光才真正有了落处。我愿把后半生，用来成全这样的人。』",
                "options": [
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_history": {
                "text": "旁白：教皇·格里高利九世眼神迷离地望向窗外大圣堂的金顶。『这顶冠冕，三百年前压在第一代教皇头上时，他说他要「守护苍生」。可到后来，守护苍生变成守护权柄，守护权柄变成守护谎言。金顶之下，到底还剩下几成「圣光」，我自己也说不清了。』",
                "options": [
                    {"text": "🗺️ 殿下可知圣女为何出逃？", "next": "pope_saint_talk"},
                    {"text": "🤔 那封印……到底是怎么回事？", "next": "pope_seal_talk"},
                    {"text": "🗺️ 那殿下接下来打算如何？", "next": "pope_plan"},
                    {"text": "🗺️ 王座与冠冕，究竟谁在说谎？", "next": "crown_talk"},
                    {"text": "（告辞）", "next": "__end__"},
                ],
            },
            "pope_saint_talk": {
                "text": "旁白：教皇·格里高利九世目光微动。『她在藏书阁抄了三年古籍，把历代「病逝」圣女的名单一条条比对——她不是受感发疯，是靠着清醒与勇气，才敢逃出这座金笼。艾莉丝她……是个好孩子，教会对不起她。』",
                "options": [
                    {"text": "🗺️ 殿下可愿向圣女道歉？", "next": "pope_saint_talk2"},
                    {"text": "🗺️ 教会那些「圣物」……也多是假的？", "next": "pope_relic"},
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_relic": {
                "text": "旁白：教皇·格里高利九世长叹。『教会大圣堂里的所谓「圣物」——贤者之骨、神泪之瓶——多是先辈们为撑住那套谎言「造」出来的。真正的圣物只有一件：三百年前英雄王留下的黎明之光传承。其余的，不过是镀了金的说辞。』",
                "options": [
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_saint_talk2": {
                "text": "旁白：教皇·格里高利九世重重点头。『若她肯见我，我愿跪下来，把「对不起」这三个字，一个字一个字说给她听。她带走了我这辈子欠下的罪——若她能原谅，那圣光便还有救。』",
                "options": [
                    {"text": "🗺️ 圣女庭到底是个什么地方？", "next": "pope_st_court"},
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_st_court": {
                "text": "旁白：教皇·格里高利九世叹道。『圣女庭名义上是「圣光培育之地」，实则是一座用「虔诚」锁住的牢笼。圣女们从小便要学着期待「成为封印」的那一天——她们甚至不被允许质疑，一旦动念，便算「圣光蒙尘」。艾莉丝是唯一一个，把疑问熬成了勇气逃出来的人。』",
                "options": [
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_seal_talk": {
                "text": "旁白：教皇·格里高利九世压低声音。『封印的真正代价，藏在教会的密档里，连历任教皇也只敢交给最信任的人过目——那便是「每一百年，以一代圣女之血养封」。这秘不可宣，可谎言终撑不住了，封印这才裂了。』",
                "options": [
                    {"text": "🗺️ 那如何让封印不再饮血？", "next": "pope_seal_talk2", "action": {"set_flag": "pope_seal_told"}},
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_seal_talk2": {
                "text": "旁白：教皇·格里高利九世目光渐亮。『传说唯一能「传承意志而非献祭生命」的，是三百年前英雄王留下的「黎明之光」。孩子，你若能寻到那份传承，封印或许能换一种封法——这才是真正的出路。』",
                "options": [
                    {"text": "🗺️ 那「黎明之光」现在何处？", "next": "pope_seal_talk3"},
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_seal_talk3": {
                "text": "旁白：教皇·格里高利九世的语气郑重起来。『古籍记载，它在烬山的封印之核，由那位「守夜者」蚀夜守着。要抵达那里，得先过旧王陵、再攀烬山——那是一段连教会都不敢走的路。孩子，你若真能走到，替我向那位守夜者，道一声迟来的明悟。』",
                "options": [
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_plan": {
                "text": "旁白：教皇·格里高利九世缓缓道。『等封印的事有了着落，我会退下这顶冠冕，把教会的权柄还给「守护」二字。我愿用余生，替这三百年的谎赎罪——让圣光，重新住回世人的心里。』",
                "options": [
                    {"text": "🗺️ 那国王腓特烈三世殿下……", "next": "pope_king_news"},
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_king_news": {
                "text": "旁白：教皇·格里高利九世目光平和。『国王腓特烈三世是这场祸里最冤枉也最清醒的人。他曾与我深谈过，说「封印若靠血维持，那圣光便不配被仰望」——当年我还劝他慎言，如今想来，他才是看得最清的。待我出得这囚笼，第一件事便是还他清白。』",
                "options": [
                    {"text": "（回到请教）", "next": "pope_history"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q11_5"},
                     "text": "旁白：教皇·格里高利九世示意你坐到榻边。他缓了缓气，声音沙哑。『孩子，我该先向你、向圣女、向这大陆上每一个被教会欺骗的人——说一声抱歉。三百年来，教会用谎言维持着统治。我曾以为，那也是守护圣光必要的一点「代价」。可奥古斯都让我看清，谎言终有反噬的一天。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "教皇殿下，请讲。", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                    {"text": "🤔 您自己也信那些谎吗？", "next": "confess_self", "need": {"quest_pending": "q11_5"}},
                    {"text": "🗺️ 殿下，先别说教会的错，您自己可还好？", "next": "confess_health", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默恭听）", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_self": {
                "text": "旁白：教皇·格里高利九世苦笑一声。『信与不信，早已分不清了。我继位那年，教会的「封印稳固、魔王已死」之说已经讲了两百多年。我接过的不只是冠冕，还有这一套几乎没人敢质疑的「圣光」。等我开始怀疑时，谎言早已和教会的根基长成了一体。』",
                "options": [
                    {"text": "那您可曾想过说出来？", "next": "confess_why_not", "need": {"quest_pending": "q11_5"}},
                    {"text": "教皇殿下，请继续讲。", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默）", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_why_not": {
                "text": "旁白：教皇·格里高利九世缓缓摇头。『说出去，教会会碎，百姓的信仰会跟着碎。我曾天真地以为，宁可用一个「善意的谎」护住世人的安宁，也不愿戳破它害得天下大乱。可我错了——奥古斯都让我明白，谎言养大的，从来只有更大的谎言与更深的血债。』",
                "options": [
                    {"text": "教皇殿下，请讲。", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默）", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_health": {
                "text": "旁白：教皇·格里高利九世费力地咳了两声。『囚室里那份「圣光」，除了刑架和冰冷的祷词，便是无尽的等待。我靠着一句「我总得活着，把话当面说清」，才撑到今天。别担忧我——孩子，比起我的身子，你脚下那条路，才是要紧的。』",
                "options": [
                    {"text": "教皇殿下，请讲。", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默恭听）", "next": "confess_grief", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_grief": {
                "text": "旁白：教皇·格里高利九世闭了闭眼，仿佛在回忆一件久远又沉重的事。『奥古斯都是我最信任的枢机。我把教会大半的权力交给他，以为他是在替我分担圣光的沉重——直到他囚禁我，宣布国王为叛教者。我这才明白，他守护的从不是圣光，而是那尊神龛里的权柄。』",
                "options": [
                    {"text": "🤔 他说「牺牲是必要的」……", "next": "confess_origin", "need": {"quest_pending": "q11_5"}},
                    {"text": "🗺️ 奥古斯都是何时开始不对劲的？", "next": "confess_august", "need": {"quest_pending": "q11_5"}},
                    {"text": "（继续听他讲）", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_august": {
                "text": "旁白：教皇·格里高利九世望着天花板。『他年轻时，也曾是个相信「圣光护佑苍生」的热忱教士。是那一次次「祭品」「献祭」的密档，一点点磨掉了他的敬畏，换来满心的权欲。我若早一日戳破谎言，他或许不至于走到这一步——这也是我的罪。』",
                "options": [
                    {"text": "🤔 他说「牺牲是必要的」。", "next": "confess_origin", "need": {"quest_pending": "q11_5"}},
                    {"text": "（继续听他讲）", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_origin": {
                "text": "旁白：教皇·格里高利九世的目光忽然变得辽远。『三百年前，教会一手选了「圣女」的传说，说圣女的光辉能镇压魔王。可那不过是为了一代一代「献祭」历代圣女，换回百年「封印稳固」的假象。我从古籍里读到过那段记录——不是「封印」，是血。教会用谎言，把自己钉在了那口名为「信仰」的铡刀下。』",
                "options": [
                    {"text": "🗺️ 那历代圣女……她们都知道吗？", "next": "confess_sacrifice", "need": {"quest_pending": "q11_5"}},
                    {"text": "那圣女殿下……艾莉丝她……", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默）", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_sacrifice": {
                "text": "旁白：教皇·格里高利九世的声音低了下去。『她们大多被教成「圣光容器」，以为生来便是为封印献出一切。她们不是「病逝」，是被教会亲手送上了祭坛——三百年来，三十七位圣女，没有一个能逃脱。艾莉丝是最后一个，也是唯一一个清醒着逃出来的。』",
                "options": [
                    {"text": "🗺️ 那教会为何要这样对待「容器」？", "next": "confess_power", "need": {"quest_pending": "q11_5"}},
                    {"text": "那圣女殿下……她逃得对。", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默）", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_power": {
                "text": "旁白：教皇·格里高利九世目光晦涩。『因为「管理者」需要封印永远稳固、需要「魔王」永远存在——圣女的血，是这场祭祀的「香火」。有了它，教会的权柄才能一代代传下去。我若不亲手戳破它，便等同继续供着这尊食人的神龛。』",
                "options": [
                    {"text": "那圣女殿下……她逃得对。", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                    {"text": "（静默）", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_lie": {
                "text": "旁白：教皇·格里高利九世缓缓摇头。『圣女不是「堕落」——她是看清了真相，才逃的。我明明看过那方圣徽，明明知道圣女在修道院留下的手稿，却一次次选择「相信必要的谎言」。孩子，圣光的重量，从来不该落在谁的血上。』",
                "options": [
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "🗺️ 那陛下为何现在要揭穿它？", "next": "confess_now", "need": {"quest_pending": "q11_5"}},
                    {"text": "🗺️ 那方修道院的手稿，殿下也看过？", "next": "confess_manuscript", "need": {"quest_pending": "q11_5"}},
                    {"text": "（再问他）", "next": "confess_confess", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_manuscript": {
                "text": "旁白：教皇·格里高利九世目光微垂。『白石修道院的玛格丽特，曾秘密送过一份圣女留下的手稿给我。那上面写满了一位圣女看清真相后的绝望与挣扎。我握在手里整整三月，最终却把它锁进了圣物库——我亲手错过了戳破谎言的最好时机。这是我的怯懦。』",
                "options": [
                    {"text": "那殿下如今还锁着它吗？", "next": "confess_manuscript2", "need": {"quest_pending": "q11_5"}},
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "（再问他）", "next": "confess_confess", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_manuscript2": {
                "text": "旁白：教皇·格里高利九世低声道。『我已命人将它取出。你若愿读，自可去圣物库查阅——那上面，有历代圣女用血与泪写下的真相。我愿这份手稿，成为教会迷途的一盏灯，而不是又一封压箱底的信。』",
                "options": [
                    {"text": "（重重点头）", "next": "confess_lie", "need": {"quest_pending": "q11_5"}},
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "（再问他）", "next": "confess_confess", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_now": {
                "text": "旁白：教皇·格里高利九世抬眼，目光清朗了些。『趁我还有一口气，趁封印刚裂、还不至彻底崩塌，趁奥古斯都的疯狂还没让教会彻底腐朽——现在不说，就再没有机会把这个真相，亲手交到一个愿意听的孩子手里了。』",
                "options": [
                    {"text": "🗺️ 殿下就不怕教会坍塌吗？", "next": "confess_fear", "need": {"quest_pending": "q11_5"}},
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "（再问他）", "next": "confess_confess", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_fear": {
                "text": "旁白：教皇·格里高利九世坦然一笑。『怕。怕教会坍塌后，那些仰望圣光的百姓没了依靠，怕我这一句话后，百年秩序溃散。可我更怕——眼睁睁看着又一代圣女被献祭，把这谎再传三百年。两相权衡，我宁可做那个「毁掉教堂」的人，也不做那个亲手递给屠刀的人。』",
                "options": [
                    {"text": "殿下，你做得对。", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "（再问他）", "next": "confess_confess", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_confess": {
                "text": "旁白：教皇·格里高利九世顿了顿，声线发抖。『你说的对，我该把话说到底。——这三百年，教会为了一座「稳固」的空壳，亲手喂养了奥古斯都这样的怪物。我错信的不只是一个枢机，是信了一个用谎言垒成的教会，会替我守护圣光。它不会。圣光，从来只住在愿意守护它的人心里。』",
                "options": [
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "🗺️ 那告解之后，殿下想做什么？", "next": "confess_after", "need": {"quest_pending": "q11_5"}},
                    {"text": "（沉默许久）", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_after": {
                "text": "旁白：教皇·格里高利九世郑重道。『忏悔不是让罪疚把我压垮，而是让我有勇气去纠错。我会亲手拆了那顶「教皇的冠冕」，让教会重归「守护」的本心——可眼前最急的，是先封住那道裂开的封印。这担子，我想托付给你。』",
                "options": [
                    {"text": "那圣光……到底是什么样子？", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                    {"text": "（沉默许久）", "next": "confess_resolve", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_resolve": {
                "text": "旁白：教皇·格里高利九世挣扎着坐直了一些，握住了你的手。『孩子，圣光真正的样子，是你心中的正义——是你这一路为了真相、为了无辜者挥出的每一剑、踏出的每一步。我不再奢求教会替圣光说话，只求有人能把真相，重新装进世人的心里。你……愿意替我去纠正这一切吗？』",
                "options": [
                    {"text": "👑 我愿替您去纠正这一切。", "next": "confess_take", "need": {"quest_pending": "q11_5"}, "action": {"set_flag": "pope_pledge", "quest_take": True}},
                    {"text": "🤔 可我该从何做起？", "next": "confess_how", "need": {"quest_pending": "q11_5"}},
                    {"text": "（我还需要想想）", "next": "welcome", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_how": {
                "text": "旁白：教皇·格里高利九世（握紧你的手）。『先集结联军，把那道裂开的封印重新封住——这是燃眉之急。至于教会……等你从烬山归来，我会亲手拆了那顶「教皇的冠冕」，让圣光不再被谎言绑架。』",
                "options": [
                    {"text": "👑 我愿替您去纠正这一切。", "next": "confess_take", "need": {"quest_pending": "q11_5"}, "action": {"set_flag": "pope_pledge", "quest_take": True}},
                    {"text": "🗺️ 那封印……究竟是怎么裂的？", "next": "confess_seal", "need": {"quest_pending": "q11_5"}},
                    {"text": "（我还需要想想）", "next": "welcome", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_seal": {
                "text": "旁白：教皇·格里高利九世低声道。『封印靠圣女的血维持，可这一代的献祭不曾如期——不是因为艾莉丝逃了，而是因为，靠虚假的「圣物」堆出来的封印，本就是纸糊的。裂的不只是那道封印，是教会三百年来那套谎的根基。』",
                "options": [
                    {"text": "👑 我愿替您去纠正这一切。", "next": "confess_take", "need": {"quest_pending": "q11_5"}, "action": {"set_flag": "pope_pledge", "quest_take": True}},
                    {"text": "（我还需要想想）", "next": "welcome", "need": {"quest_pending": "q11_5"}},
                ],
            },
            "confess_take": {
                "text": "旁白：教皇·格里高利九世眼中浮现一丝泪光，随即化作坚定。『好。圣光会指引你——如同它曾指引三百年前那位英雄王艾德里克。去吧，孩子，把真相和黎明，一起带回这世上来。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                    {"text": "🗺️ 殿下，还有别的话要对我说吗？", "next": "confess_parting"},
                    {"text": "🗺️ 那奥古斯都……该如何处置？", "next": "confess_justice"},
                ],
            },
            "confess_parting": {
                "text": "旁白：教皇·格里高利九世望着你，目光温和。『若你在烬山见到圣女，替我说一声——教皇格里高利，欠她一条命，也欠她一句「对不起」。愿这一路，圣光护你行远。』",
                "options": [
                    {"text": "我会带话给她的，殿下。", "next": "confess_parting2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "confess_parting2": {
                "text": "旁白：教皇·格里高利九世微微颔首。『多谢你，孩子。这一路，你替这世道承担的，比教会的冠冕重得多。去吧——灯塔就在烬山，而黎明，正等着你亲手点亮。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "confess_justice": {
                "text": "旁白：教皇·格里高利九世神色重又沉肃。『奥古斯都罪孽深重，自当交由王国与教会依律公审，而非私刑处决——罪要清算，但「以暴易暴」只会让教会重蹈覆辙。你只管与他了断前面的恶，余下的审判，交给律法与圣光的见证。』",
                "options": [
                    {"text": "我明白了，殿下。", "next": "confess_take2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "confess_take2": {
                "text": "旁白：教皇·格里高利九世疲惫地合了合眼。『去罢。这一战后，你若还能回来，我请你喝教会的陈酿——敬一个敢对「神龛」说不的孩子。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_status": {
                "text": "旁白：教皇·格里高利九世虚弱地靠在榻边。『孩子，忏悔和交托我都说完了。你若要再去回想，或想领受圣光的祝福，都可以。』（『任务』能随时看目标。）",
                "options": [
                    {"text": "✅ 教皇殿下，忏悔作完了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_5"}},
                    {"text": "🙏 我还有话想……（再谈）", "next": "quest_talk", "need": {"quest_pending": "q11_5"}},
                    {"text": "🗺️ 殿下，忏悔之外还想说点什么？", "next": "pope_after"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_after": {
                "texts": [
                    {"need": {"quest_done": "q11_5"},
                     "text": "旁白：教皇·格里高利九世面色缓和了些。『孩子，你替我把这段路走出了个开始。我这一生困在谎里太深，是你让我瞧见了「真相」的模样。去烬山吧——若你回来时我还活着，我请你喝一杯，敬黎明之后的第一杯。』"},
                ],
                "text": "旁白：教皇·格里高利九世含笑。『忏悔不是终点，是新的起点。孩子，愿你走的每一步，都踏在真相之上。』",
                "options": [
                    {"text": "我会回来的，殿下。", "next": "pope_after_promise"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "pope_after_promise": {
                "text": "旁白：教皇·格里高利九世郑重地朝你颔首。『这座城的钟，会为归来的勇士而鸣。去吧——记住，圣光的名字，不该背在身上，而是照亮前路。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q11_5"},
                     "text": "旁白：教皇·格里高利九世将苍老的手覆在你额前，一阵温暖的圣光漫过全身。『我这一生守护过一个错的「圣光」，如今才算把对的圣光，托到了你肩上。教皇的权杖我放下了，可这份祝福，请你带走——愿它护你走到烬山的深处，走到黎明之前。』"},
                ],
                "text": "旁白：教皇·格里高利九世颔首。『你的心，圣光看得见。收下这份祝福。』",
                "options": [
                    {"text": "💰 领受教皇的祝福。", "next": "blessing_receive", "need": {"quest_ready": "q11_5"}, "action": {"quest_take": True, "set_flag": "pope_blessed"}},
                    {"text": "🙏 教皇殿下，最后还有什么想说的吗？", "next": "blessing_take"},
                ],
            },
            "blessing_receive": {
                "text": "旁白：圣光如暖阳般在你周身流转，教皇·格里高利九世疲态的眼角泛起一抹泪光。『去吧，孩子。愿这道光，替你在最暗的时分引路。教会错了三百年，可「守护」二字，不该跟着一起错下去。』",
                "options": [
                    {"text": "🗺️ 殿下，可否也为圣女、为国王，留一道光？", "next": "blessing_others"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "blessing_others": {
                "text": "旁白：教皇·格里高利九世双手合拢，闭目低祷。『圣光若真有宽广，便不应只照向教会。待圣女归来、待国王平反，我会为他们各留一道光——不是我布的恩，是他们守住真相，该得的辉光。你这句话，我记下了。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "blessing_take": {
                "text": "旁白：教皇·格里高利九世平静地闭上眼，嘴角却带着一丝释然。『告诉圣女——她不是祭品，她是黎明前第一个睁眼的人。告诉她，教皇格里高利，等她回家。』",
                "options": [
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
}
