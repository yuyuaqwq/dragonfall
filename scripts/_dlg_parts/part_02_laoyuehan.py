# -*- coding: utf-8 -*-
"""02 老约翰组 主线对话树实现分片（策划案 02 翻译）"""
DIALOGUES_PART = {
    "npc_guildmaster": {
        "start": "welcome",
        "nodes": {
            "welcome": {
                "texts": [
                    {"need": {"quest_done": "q12_6"}, "text": "老约翰望着行会大厅里那面挂满勋章与断剑的墙，微微一笑：『我老了，小子。如今这行会的门朝哪儿开，得靠你替我先看一眼了。来，坐下，陪老头子喝最后一杯正式的。』"},
                    {"need": {"quest_done": "q12_4"}, "text": "老约翰把酒杯往桌上一磕，眼睛有些发亮：『敬过黎明之后的第一杯酒了。可我总觉得……还有一句没说完。小子，别急着走，行会还有些体面活儿要交给你。』"},
                    {"need": {"quest_done": "q11_4"}, "text": "老约翰披着旧甲，站在行会门口，望着北方的天际：『二百年前我还毛头小子……如今又要往烬山跑了。这趟回来，铁港得好好给你记一笔。』"},
                    {"need": {"quest_done": "q9_6"}, "text": "老约翰守夜归来，铁壶里温着酒：『烬山的夜，我一闭眼还能听见裂隙在喘。小子，你那份战功，联军都记着呢。来，先暖暖手再说。』"},
                    {"need": {"quest_done": "q9_1"}, "text": "老约翰摊开一张磨得发亮的烬山地图：『三百年了，这山上的每一寸我都踩过。如今又要上去，心里反而踏实了——因为这回你不是一个人。』"},
                    {"need": {"quest_done": "q5_1"}, "text": "老约翰摩挲着缺了半截的手指，若有所思：『那枚圣徽……你把它交到该去的地方了。有些话，我这辈子只对两样人讲过——跟我并肩的兄弟，和听得懂真话的人。』"},
                    {"need": {"quest_done": "q3_5"}, "text": "老约翰瞥了你自己那只完好的手一眼，又看向自己的，咧嘴一笑：『读过圣战旧事的人不多，你算是头一个不嫌老头子絮叨的。铁港城这滩水，正好有人陪你一起蹚。』"},
                    {"need": {"quest_done": "q3_4"}, "text": "老约翰压低声音：『那封信你答应送了吧？路上别乱拆。这行会有规矩——有些委托，越是神秘，越是重要。』"},
                    {"need": {"quest_done": "q3_1"}, "text": "老约翰抬手招呼：『好小子，铁港城待得还习惯？这地方的风最野，也最能养出真本事。』"},
                ],
                "text": "老约翰·铁砧懒洋洋地靠在那张堆满酒桶与地图的木桌后，打量了你片刻：『年轻人，听说你在白鹿城干得不错？欢迎来铁港——冒险者的圣地，也是……麻烦的中心。』",
                "options": [
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q3_1"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q3_4"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q3_5"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q5_1"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q9_1"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q9_2"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q9_3"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q9_4"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q9_5"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q9_6"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q11_4"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q12_1"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q12_4"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q12_5"}},
                    {"text": "📜 接这个委托。", "next": "quest_talk", "need": {"quest_pending": "q12_6"}},
                    {"text": "📜 有活儿要交给我。", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q3_1"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q3_4"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q3_5"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q5_1"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q9_1"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q9_2"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q9_3"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q9_4"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q9_5"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q9_6"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q11_4"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q12_1"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q12_4"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q12_5"}},
                    {"text": "✅ 任务办妥了。", "next": "quest_done_talk", "need": {"quest_ready": "q12_6"}},
                    {"text": "✅ 有支线要交付。", "next": "__end__", "need": {"side_ready": True}, "action": {"side_take": True}},
                    {"text": "🤔 手头的任务还没着落。", "next": "quest_status", "need": {"quest_any_active": True}},
                    {"text": "🗺️ 打听行会与铁港。", "next": "lore"},
                    {"text": "🔥 聊聊当年的圣战。", "next": "war_story", "need": {"quest_done": "q3_1"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "lore": {
                "text": "老约翰指了指墙上的行会徽记：『这是我们行会的徽——一把断剑，一只眼睛。断剑是三百年前英雄留下的；眼睛，是提醒我们：这世上总有人看得见别人看不见的东西。』",
                "options": [
                    {"text": "🤔 那你是从哪一代看起这徽记的？", "next": "lore_self"},
                    {"text": "🗺️ 铁港城有什么门道？", "next": "lore_harbor"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "lore_self": {
                "text": "老约翰：『我年轻时提着这把剑满大陆跑，见过的怪物比有些人见过的鸡还多。后来打不动了，就坐在这个位子上，替后辈看看地图、挡挡风浪。你可以笑我老了，别笑我看人的眼力。』",
                "options": [
                    {"text": "🗺️ 接着说铁港城。", "next": "lore_harbor"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "lore_harbor": {
                "text": "老约翰：『铁港城是靠海吃饭的——码头、酒馆、地下黑市，鱼龙混杂。有人在这儿发迹，有人在这儿栽跟头。记住一句：别信海上的酒，也别信码头的笑。』",
                "options": [
                    {"text": "🗺️ 行会总部怎么运作？", "next": "lore_guild"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "lore_guild": {
                "text": "老约翰：『行会有铁牌、银牌、金牌，还有从没发过的“传奇”牌。你刚进门是铁牌，踏实地干，牌子会自己说话。』",
                "options": [
                    {"text": "🔥 那断剑背后是谁的故事？", "next": "war_story"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "war_story": {
                "texts": [
                    {"need": {"quest_done": "q9_6"}, "text": "老约翰望着投进窗里的北风，声音很轻：『再提圣战，就是给这段往事收尾了。烬山脚下那一眼金光……等你自己去看过，你就明白我为什么从不愿多说。』"},
                    {"need": {"quest_done": "q5_1"}, "text": "老约翰：『圣战收尾那年，我以为教会说的是真的——魔王已死，封印稳固。后来才知道，有些“稳固”，是拿人命填的。你小子，比当年的我有出息。』"},
                    {"need": {"quest_done": "q3_5"}, "text": "老约翰：『我跟你讲的圣战往事，可能跟史书对不上。可史书是写给别人看的，我这条命，是自己在烬山滚过的。你信哪本，随你。』"},
                ],
                "text": "老约翰：『想听圣战旧事？嘿嘿，那可得先陪我喝两杯。三百年前的事，说来话长——你若有心，日后来听我慢慢讲。』",
                "options": [
                    {"text": "🔥 讲讲断指。", "next": "finger_tale"},
                    {"text": "🗡️ 你这根手指，是怎么断的？", "next": "finger_story", "need": {"quest_pending": "q3_5"}},
                    {"text": "🔥 烬山到底是什么样的地方？", "next": "ember_story", "need": {"quest_pending": "q3_5"}},
                    {"text": "🗡️ 讲讲烬山。", "next": "ember_tale"},
                    {"text": "😔 历史与真相。", "next": "truth_tale", "need": {"quest_done": "q3_5"}},
                    {"text": "📜 我愿意听。", "next": "accept_q3_5", "need": {"quest_pending": "q3_5"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "finger_tale": {
                "text": "老约翰低头看着自己缺了半截的指根：『烬山那回，恶魔的爪子带走了它。也从那天起，我学会一件事——人不能光听别人说，得自己亲眼去看。』",
                "options": [
                    {"text": "🤔 你看见了什么？", "next": "truth_tale"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ember_tale": {
                "text": "老约翰：『烬山是这个世界最老的伤口。三百年前英雄王在那儿守住了什么，至今没人敢真正说出口。你若有一天走到了那金光底下——替我看看。』",
                "options": [
                    {"text": "🔥 我若见了，回头告诉你。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "truth_tale": {
                "text": "老约翰压低声：『历史是胜利者写的，可真相不会消失。圣女那桩事、烬山那桩事，都是同一枚硬币。信了谎言的人，眼睛会瞎；愿意翻书的人，路子才走得远。』",
                "options": [
                    {"text": "📖 我记下了。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_talk": {
                "texts": [
                    {"need": {"quest_pending": "q3_1"}, "text": "老约翰：『来得正好，小子。你是行会从白鹿城一路推荐过来的吧？铁港城的情况你还不熟——先把行会总部摸个门清，算是入门的道理。我这儿正好缺个要跑腿的。』"},
                    {"need": {"quest_pending": "q3_4"}, "text": "老约翰把一封盖着火漆的信放到桌上，神情少有的严肃：『有人托行会送封信，点名要你送。送到白石修道院，玛格丽特院长会接待你。别多问，也别拆。有些委托，知道得越少越安全。』"},
                    {"need": {"quest_pending": "q3_5"}, "text": "老约翰看了你一眼，又低头看自己那缺了半截的手指，半晌才说：『你既然在行会里待出了名堂，有些旧账……我大抵是瞒不住了。想听圣战那些陈年烂事吗？行，坐下来，我讲给你听。』"},
                    {"need": {"quest_pending": "q5_1"}, "text": "老约翰看到你取出的圣徽，脸色一凝，随即长叹：『……果然。她终于还是跑了。你从白石修道院回来，想必已经看见了一些不该有的东西。坐。这件事，我欠你一个交代。』"},
                    {"need": {"quest_pending": "q9_1"}, "text": "老约翰披上那件洗得发白的旧甲，声音沉了下来：『明早出发去烬山。人类、精灵、矮人、北境诸部——三百年来头一遭并肩。走吧小子，这回不是接委托，是去给这个古老的故事收个尾。』"},
                    {"need": {"quest_pending": "q9_2"}, "text": "老约翰拄着剑，望着烬山脚下的黑烟：『山里的恶魔在清路前的工事。你带一队上去，把那群恶鬼的头阵劈开，给联军扫出一条道来。记住——老兵不是不会老，是瞧见它们还敢露头，就气不过。』"},
                    {"need": {"quest_pending": "q9_3"}, "text": "老约翰的脸色比山石还沉：『赫尔加那疯婆子在祭坛上搞撕裂封印的仪式。你潜上去探清楚她的布阵，摸清祭坛的门道——别急着动手，我们得看清楚她要干什么。』"},
                    {"need": {"quest_pending": "q9_4"}, "text": "老约翰把手按在你肩上：『祭坛的门已经探清了，现在就看你的剑了。赫尔加是这一环的钥匙，宰了她，仪式才停得下来。小子，这一刀，替三百年前死在烬山的老兄弟们一起砍。』"},
                    {"need": {"quest_pending": "q9_5"}, "text": "老约翰把你拉到营火旁：『精灵的箭手、矮人的战锤、北境的战吼、骑士团的光盾——四个阵营的代表都聚在这儿，等你一句话。联军不是人多就够，得心齐。你替我去把那几堆火拢到一块儿。』"},
                    {"need": {"quest_pending": "q9_6"}, "text": "老约翰塞给你一壶酒：『今儿夜里轮到你守营。烬山的坌是二十步开外的裂隙，晚上常有深渊奴仆来试咱们的防线。你小子值夜机灵点——活的回来，死了的带不回来，记住了。』"},
                    {"need": {"quest_pending": "q11_4"}, "text": "老约翰拧开酒壶盖，仰头灌了一口，忽而笑了：『三百年前，我跟着英雄王走过这条路。今天，我跟着你，再走一次。各部联军都点齐了，就差你一句话——什么时候走，我听你的。』"},
                    {"need": {"quest_pending": "q12_1"}, "text": "老约翰的剑锋在地面划出一道焦痕：『裂隙那边的深渊猎犬开始涌了，先锋压上来。联军齐阵，你带骑士团的光盾顶在最前头，给后面的箭雨和矮人战阵争取时间。这一仗，所有人都看着你的剑起势。』"},
                    {"need": {"quest_pending": "q12_4"}, "text": "老约翰在铁港行会门口摆了一整排酒桶，天不亮就把钟敲响了：『回来了……回来了好。整个铁港城，你是头一个走到黎明的人。别急着去领功——先喝了这第一杯，让所有人都知道：那个头一个把黎明带来的小子，是咱们行会的。』"},
                    {"need": {"quest_pending": "q12_5"}, "text": "老约翰望着天边渐亮的光，声音低了些：『仗打完了，可人还得说再见。老约翰、艾莉丝、罗兰、各族代表……每个人都有一句想亲口对你说的话。别嫌烦，这是他们给救命恩人的礼数。』"},
                    {"need": {"quest_pending": "q12_6"}, "text": "老约翰整了整衣襟，难得庄重：『行会从创会那天起，就没往谁胸口别过“传奇”两个字。今天，你是头一个。来，站到正中间，让我当着所有人的面，把该给的体面给你。』"},
                ],
                "text_from": "story",
                "options": [
                    {"text": "📜 领了。", "next": "accept_q3_1", "need": {"quest_pending": "q3_1"}},
                    {"text": "🤔 铁港城是什么来头？", "next": "harbor_info", "need": {"quest_pending": "q3_1"}},
                    {"text": "📜 我送。", "next": "accept_q3_4", "need": {"quest_pending": "q3_4"}},
                    {"text": "🤔 这是谁托的？", "next": "letter_ask", "need": {"quest_pending": "q3_4"}},
                    {"text": "📜 我愿意听。", "next": "accept_q3_5", "need": {"quest_pending": "q3_5"}},
                    {"text": "🤔 说说圣战的事。", "next": "war_story", "need": {"quest_pending": "q3_5"}},
                    {"text": "📜 我交差。", "next": "accept_q5_1", "need": {"quest_pending": "q5_1"}},
                    {"text": "🤔 你知道圣女的下落？", "next": "truth", "need": {"quest_pending": "q5_1"}},
                    {"text": "📜 出发。", "next": "accept_q9_1", "need": {"quest_pending": "q9_1"}},
                    {"text": "🤔 联军都到齐了？", "next": "expedition_forces", "need": {"quest_pending": "q9_1"}},
                    {"text": "📜 我带队上去。", "next": "accept_q9_2", "need": {"quest_pending": "q9_2"}},
                    {"text": "🤔 你上过烬山的战场？", "next": "hunter_old", "need": {"quest_pending": "q9_2"}},
                    {"text": "📜 我去探祭坛。", "next": "accept_q9_3", "need": {"quest_pending": "q9_3"}},
                    {"text": "🤔 赫尔加在祭坛做什么？", "next": "halga_ritual", "need": {"quest_pending": "q9_3"}},
                    {"text": "📜 我去宰了她。", "next": "accept_q9_4", "need": {"quest_pending": "q9_4"}},
                    {"text": "🤔 她真要撕开封印？", "next": "seal_tear", "need": {"quest_pending": "q9_4"}},
                    {"text": "📜 我去见他们。", "next": "accept_q9_5", "need": {"quest_pending": "q9_5"}},
                    {"text": "🤔 四族有什么矛盾？", "next": "alliance_grief", "need": {"quest_pending": "q9_5"}},
                    {"text": "📜 我去值夜。", "next": "accept_q9_6", "need": {"quest_pending": "q9_6"}},
                    {"text": "🤔 夜里会来什么？", "next": "watch_dark", "need": {"quest_pending": "q9_6"}},
                    {"text": "📜 集结联军。", "next": "accept_q11_4", "need": {"quest_pending": "q11_4"}},
                    {"text": "🤔 这一次和上次有什么不同？", "next": "march_diff", "need": {"quest_pending": "q11_4"}},
                    {"text": "📜 我带光盾顶前面。", "next": "accept_q12_1", "need": {"quest_pending": "q12_1"}},
                    {"text": "🤔 先锋是深渊猎犬？", "next": "pack_tactics", "need": {"quest_pending": "q12_1"}},
                    {"text": "📜 我接这杯酒。", "next": "accept_q12_4", "need": {"quest_pending": "q12_4"}},
                    {"text": "🤔 这杯酒，敬给谁？", "next": "toast_to", "need": {"quest_pending": "q12_4"}},
                    {"text": "📜 我去听大家的告别。", "next": "accept_q12_5", "need": {"quest_pending": "q12_5"}},
                    {"text": "🤔 都有谁在等我？", "next": "who_waits", "need": {"quest_pending": "q12_5"}},
                    {"text": "📜 我站到中间。", "next": "ritual_gather", "need": {"quest_pending": "q12_6"}},
                    {"text": "😐 再想想。", "next": "welcome"},
                ],
            },
            "quest_status": {
                "texts": [
                    {"need": {"quest_active": "q3_1"}, "text": "老约翰：『你小子刚进铁港，先把行会总部门道摸清——认认路，认认人。办妥了回来，我跟你细说这里的水有多深。』"},
                    {"need": {"quest_active": "q3_4"}, "text": "老约翰把门边的斗篷递给你：『信还揣着呢？别耽搁，白石修道院那段路不算近。路上留神——你就是个送信的，别的别沾。』"},
                    {"need": {"quest_active": "q3_5"}, "text": "老约翰：『想听圣战旧事？那咱得先把话头拣起来。你坐，我这儿正好温着酒——等你想好了，老头子就讲给你听。』"},
                    {"need": {"quest_active": "q5_1"}, "text": "老约翰看着你手里的圣徽，欲言又止：『你带着它从白石修道院回来了？……好。坐。这件事，我攒了太久的话，正好一并说给你听。』"},
                    {"need": {"quest_active": "q9_1"}, "text": "老约翰望了望北边渐沉的天色：『联军在前头等着，烬山在更前头看着。你收拾停当没有？这趟路，一步都不能省。』"},
                    {"need": {"quest_active": "q9_2"}, "text": "老约翰朝烬山方向扬了扬下巴：『恶魔还没清干净，联军进不了山门。小子，锋头要快、选要害——别跟它们缠斗，一刀一个，扫完缺口就回来。』"},
                    {"need": {"quest_active": "q9_3"}, "text": "老约翰压低声音：『祭坛的符文轮盘你探到了没？记着，跟赫尔加对峙时别硬拼，看清她的布阵。你探回来的每一个细节，都可能救下一整队人。』"},
                    {"need": {"quest_active": "q9_4"}, "text": "老约翰神色凝重：『赫尔加还在撑仪式。你手上有圣徽，那是她最忌讳的东西——必要时，让它见见光。记住了，宰了她，裂隙才有救。』"},
                    {"need": {"quest_active": "q9_5"}, "text": "老约翰：『四族代表还在营火边等着呢。别让他们把屁股坐热了又凉——你那一句话，还在他们心口悬着。』"},
                    {"need": {"quest_active": "q9_6"}, "text": "老约翰拧开水壶递给值夜回来的你：『裂隙那儿有点不对劲，金光底下像有什么在喘。你守夜那回看见的景象，一字不落讲给我听。』"},
                    {"need": {"quest_active": "q11_4"}, "text": "老约翰把磨亮的剑举起来看了看：『各部联军都点齐了，就差你一声令下。记住了，这回不听任何人的调遣——只听你自己的。』"},
                    {"need": {"quest_active": "q12_1"}, "text": "老约翰的剑还带着血：『先锋的深渊猎犬还压着没退干净。顶住，兄弟们都看着你。』"},
                    {"need": {"quest_active": "q12_4"}, "text": "老约翰见你进门，先塞了杯酒过来：『回来啦？先歇歇。铁港城的钟不急着敲——等你缓过这口气，大家再一起敬你。』"},
                    {"need": {"quest_active": "q12_5"}, "text": "老约翰望了望码头上散开又聚回的人影：『都在等着跟你道别呢。别拖——有些话，越拖越说不出口。』"},
                    {"need": {"quest_active": "q12_6"}, "text": "老约翰收起平日的打趣，难得端庄地整了整衣襟：『仪式就等你站到正中。准备好了，说一声，我就起头。』"},
                ],
                "text": "老约翰：『这档子事你办到哪儿了？办妥了回来找我，没办妥也跟我说道说道，别一个人扛着。』",
                "options": [
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q3_1"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q3_4"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q3_5"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q5_1"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q9_1"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q9_2"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q9_3"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q9_4"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q9_5"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q9_6"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q11_4"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q12_1"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q12_4"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q12_5"}},
                    {"text": "✅ 办妥了，来交付。", "next": "quest_done_talk", "need": {"quest_ready": "q12_6"}},
                    {"text": "🤔 我再去想想办法。", "next": "welcome"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "quest_done_talk": {
                "texts": [
                    {"need": {"quest_ready": "q3_1"}, "text": "老约翰把一杯麦酒推到你面前：『摸熟了？好。铁港城不问出身，只看本事——你能把行会总部走明白，就算迈过第一道门了。先从码头那帮水鬼开始，让这城认认你的名字。』"},
                    {"need": {"quest_ready": "q3_4"}, "text": "老约翰打量了你片刻，眼里有一丝异样：『信……送到了？好。这封信可能比你想的重要得多。小子，路上没拆开看是对的——有些事，得你亲眼到了地方才会懂。』"},
                    {"need": {"quest_ready": "q3_5"}, "text": "老约翰沉默了一会儿，给自己和你也各倒了一杯：『那些陈年旧事，讲出来心里头舒坦些。记着——历史是胜利者写的，可真相不会消失，它只是……等着有人去翻开。你，就是那个愿意翻书的人。』"},
                    {"need": {"quest_ready": "q5_1"}, "text": "老约翰扶着桌子缓缓站起身，又郑重地坐下：『……果然。她终于还是跑了。小子，你听我说——圣女不是绑架失踪，她是逃出来的，逃命。三百年前的圣战，有隐情。你带着这个去晨曦城，找国王腓特烈三世。他会信你。』"},
                    {"need": {"quest_ready": "q9_1"}, "text": "老约翰望着绵延至山脚的营火，火光映在老脸上：『联军扎营了。营火连成一片，像山下的星河。三百年了，人类、精灵、矮人、北境诸部——头一次并肩站在一块儿。这一仗，有你一份功劳。』"},
                    {"need": {"quest_ready": "q9_2"}, "text": "老约翰一剑撑地，放声大笑：『哈哈哈，看吧，老兵不死！恶魔战士倒了一地的灰，联军正往前走。我老约翰又活了一次年轻的梦。前进，去祭坛！』"},
                    {"need": {"quest_ready": "q9_3"}, "text": "老约翰指着祭坛方向，声音发沉：『你亲眼看见赫尔加了吧？她站在符文轮盘上，正在撕开封印。必须在仪式完成前打断她。祭坛的钥匙，就握在你手里。』"},
                    {"need": {"quest_ready": "q9_4"}, "text": "老约翰迎风而立，声音却沉得像铁：『赫尔加倒下了，可她说的话像根钉子扎在心上——封印裂了，三天，只剩三天。我们没有退路，只有一路向前。』"},
                    {"need": {"quest_ready": "q9_5"}, "text": "老约翰朝那营火围成一圈的四族代表努了努嘴：『成了。你一句话，把四堆火拢成了一堆。你看——他们正冲你递酒呢。三百年后，我们再次并肩，这一次，不会让历史重演。』"},
                    {"need": {"quest_ready": "q9_6"}, "text": "老约翰接过值夜的记录，眉头紧锁：『裂隙边缘的金光……底下有什么东西在注视着你。你看到的那一下子，比什么都重要。走，该往封印之核去了。』"},
                    {"need": {"quest_ready": "q11_4"}, "text": "老约翰把酒壶别在腰上，郑重地伸出手：『各部分队都点齐了。三百年前我跟着英雄王走这条路，今天，我跟着你，再走一次。你下命令吧，小子——老头子的剑，还使得动。』"},
                    {"need": {"quest_ready": "q12_1"}, "text": "老约翰抹了一把脸上的灰，眼里却亮着：『先锋退下去了！深渊猎犬溃了阵，联军士气正盛——可裂隙还在扩大。真正的决战，才刚刚开始。兄弟，你还没到松口气的时候。』"},
                    {"need": {"quest_ready": "q12_4"}, "text": "老约翰把一杯麦酒稳稳递到你手里，声音有些哑：『敬——黎明之后的第一杯酒。铁港城的钟敲了，冒险者们举杯，你是他们之中，第一个走到黎明的人。喝吧，这是你挣的。』"},
                    {"need": {"quest_ready": "q12_5"}, "text": "老约翰站在码头，望着散去又聚回的人群：『都道完别了。艾莉丝在挥手，罗兰在致礼，四族的代表还守着那堆营火——没有人先走。没有你，我们走不到今天。这趟告别，够记一辈子。』"},
                    {"need": {"quest_ready": "q12_6"}, "text": "老约翰郑重地取出一枚传奇徽章，当着所有人的面，别在你胸前：『从今以后，你就是行会的一面旗。没有加冕为王，没有成神——你只是走成了头一个“传奇”。大陆的冒险，还在继续。』"},
                ],
                "text": "老约翰：『这档子事你办到哪儿了？办妥了回来找我，没办妥也跟我说道说道，别一个人扛着。』",
                "options": [
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q3_1"}, "action": {"quest_take": True, "set_flag": "met_ironharbor"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q3_4"}, "action": {"quest_take": True, "set_flag": "saw_letter"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q3_5"}, "action": {"quest_take": True, "set_flag": "heard_war_story"}},
                    {"text": "💰 收下报酬。", "next": "q5_1_deliver", "need": {"quest_ready": "q5_1"}, "action": {"quest_take": True, "set_flag": "know_truth"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q9_1"}, "action": {"quest_take": True, "set_flag": "expedition_set"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q9_2"}, "action": {"quest_take": True, "set_flag": "battle_worn"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q9_3"}, "action": {"quest_take": True, "set_flag": "saw_helga"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q9_4"}, "action": {"quest_take": True, "set_flag": "know_seal_cost"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q9_5"}, "action": {"quest_take": True, "set_flag": "alliance_united"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q9_6"}, "action": {"quest_take": True, "set_flag": "saw_the_rift"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q11_4"}, "action": {"quest_take": True, "set_flag": "final_march"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q12_1"}, "action": {"quest_take": True, "set_flag": "battle_worn"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q12_4"}, "action": {"quest_take": True, "set_flag": "dawn_beer"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q12_5"}, "action": {"quest_take": True, "set_flag": "farewell_done"}},
                    {"text": "💰 收下报酬。", "next": "__end__", "need": {"quest_ready": "q12_6"}, "action": {"quest_take": True, "set_flag": "legend_bearer"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_first", "need": {"quest_ready": "q3_1"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_letter", "need": {"quest_ready": "q3_4"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_scar", "need": {"quest_ready": "q3_5"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_saintess", "need": {"quest_ready": "q5_1"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_ember_invite", "need": {"quest_ready": "q9_1"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_old_war", "need": {"quest_ready": "q9_2"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_halga", "need": {"quest_ready": "q9_4"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_march", "need": {"quest_ready": "q11_4"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_return", "need": {"quest_ready": "q12_4"}},
                    {"text": "🗺️ 交付后多聊两句。", "next": "talk_legacy", "need": {"quest_ready": "q12_6"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "q5_1_deliver": {
                "text": "老约翰低声：『她是圣光的容器，可教会要的从来不是光，是那道光带来的权威。你去晨曦城，见到国王，把圣徽给他看——他会懂的。铁港城，永远给你留着一盏灯。』",
                "options": [
                    {"text": "🕊️ 我替你把话带到他跟前。", "next": "__end__", "action": {"set_flag": "saw_saintess_seal"}},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "harbor_info": {
                "text": "老约翰：『铁港城是冒险者的圣地——码头边酒馆林立，地下黑市鱼龙混杂。想立足，先摸清这里的规矩。行会总部嘛，就是你现在站着的地方。』",
                "options": [
                    {"text": "🗺️ 那行会徽记上的断剑和眼睛是怎么回事？", "next": "gar_emblem"},
                    {"text": "📜 领了。", "next": "accept_q3_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gar_emblem": {
                "text": "老约翰指了指墙上那面徽记：『断剑，是三百年前英雄留下的；眼睛，是提醒咱们——这世上总有人看着别人看不见的东西。你要在行会混出名堂，先学着看那些“看不见的”。』",
                "options": [
                    {"text": "🤔 什么样的“看不见的东西”？", "next": "gar_emblem2"},
                    {"text": "📜 领了。", "next": "accept_q3_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "gar_emblem2": {
                "text": "老约翰意味深长地压低声音：『比如——圣女失踪的传言，白鹿城那是热闹；到了铁港，就没人敢轻易接这话头。你在白鹿城听见的，在这儿，得小心埋在肚子里。』",
                "options": [
                    {"text": "📜 领了。", "next": "accept_q3_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q3_1": {
                "text": "老约翰：『好，先把行会这门摸熟。等回头，码头的风浪经你趟过，我再说别的。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "met_ironharbor"}},
                ],
            },
            "letter_ask": {
                "text": "老约翰把信往你手里一塞：『匿名托付，押金给得极重，指名道姓要你送。要我说，别打听——打听多了，对你没好处。』",
                "options": [
                    {"text": "🤔 那我就这么不明不白地送？", "next": "letter_pressure"},
                    {"text": "🔒 行，我不问。", "next": "accept_q3_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "letter_pressure": {
                "text": "老约翰难得收起玩笑：『小子，行会有行会的规矩。有些委托，跑腿的人越糊涂，路上越安全。你只要把信亲手交到玛格丽特院长手里，别的，会有人替你记着这份人情。』",
                "options": [
                    {"text": "🕊️ 送到就回。", "next": "accept_q3_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q3_4": {
                "text": "老约翰压低声音：『小心着点，小子。这封信……可能比你想的要重要十倍。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "saw_letter"}},
                ],
            },
            "finger_story": {
                "text": "老约翰低头看自己缺了半截的指根，声音平淡：『烬山收尾那一年，我被一个恶魔的爪子带走了半截指头。它咬掉了我的指头，也咬掉了我身上最后一点“什么都不能做”的糊涂。从此我记着一件事——眼见为实。』",
                "options": [
                    {"text": "🤔 你看见了什么？", "next": "finger_what"},
                    {"text": "📜 我愿意听。", "next": "accept_q3_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "finger_what": {
                "text": "老约翰却忽然沉默了，半晌给自己倒了杯酒：『……等你到了那一天，自然会懂。现在，还不是时候。』",
                "options": [
                    {"text": "🤔 好，我会记住。", "next": "accept_q3_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ember_story": {
                "text": "老约翰望着窗外北方的天际：『烬山……是这个世界最老的伤口。三百年前英雄王在那里守住了什么，没人说得清。咱们只知道——那山上，埋着太多说不出口的事。』",
                "options": [
                    {"text": "🤔 你也是那儿的幸存者？", "next": "finger_story"},
                    {"text": "📜 我愿意听。", "next": "accept_q3_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q3_5": {
                "text": "老约翰拍拍你的肩：『好小子，敢听旧账，也有胆陪老头子坐冷板凳。行，这段公案，我记你一份。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "heard_war_story"}},
                ],
            },
            "truth": {
                "text": "老约翰把圣徽拿在手里，反复摩挲：『这枚圣徽，是圣女临走前留给信得过的信物。你知道教会为什么这么紧张吗？——因为圣女不是绑架失踪，她是逃出来的。逃命。』",
                "options": [
                    {"text": "🤔 她为什么要逃？", "next": "truth_why"},
                    {"text": "🗡️ 教会想抓她回去做什么？", "next": "truth_church"},
                    {"text": "📜 我交差。", "next": "accept_q5_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "truth_why": {
                "text": "老约翰压低声音：『圣光容器……生来就要“成为封印的一部分”。三百年前那些“病逝”的圣女，没一个是病死的。她查到了这个，就拼了命逃出来了。』",
                "options": [
                    {"text": "🤔 那她现在在哪儿？", "next": "truth_where"},
                    {"text": "📜 我交差。", "next": "accept_q5_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "truth_where": {
                "text": "老约翰摇头：『这我不清楚，也最好别知道。可你手上有圣徽，又有我这句真话——你该去晨曦城，找国王腓特烈三世。他会信你。』",
                "options": [
                    {"text": "🗺️ 为什么是国王？", "next": "truth_king"},
                    {"text": "📜 我交差。", "next": "accept_q5_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "truth_king": {
                "text": "老约翰：『国王跟教会不对付。边境的烽火不会撒谎，他心里比谁都清楚——这世上有些“稳固”，是演给人看的。你把真话带给他，就是给这盘棋添一颗能落地的子。』",
                "options": [
                    {"text": "📜 我交差。", "next": "accept_q5_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "truth_church": {
                "text": "老约翰低声道：『教会要抓她回去，是为了献祭——让封印再撑一百年。他们一口咬定“魔王已死、封印稳固”，可那份稳固，是拿一条又一条人命填出来的。』",
                "options": [
                    {"text": "🗡️ 我不会让这种事发生。", "next": "accept_q5_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q5_1": {
                "text": "老约翰郑重地把圣徽递回给你：『带上它，去晨曦城。小子，从此你我不只是行会同僚——你是这世上，少数几个听得懂我这句话的人。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "saw_saintess_seal"}},
                ],
            },
            "expedition_forces": {
                "text": "老约翰：『人类、精灵、矮人、北境诸部——四族的旗子都插在烬山脚下了。三百年头一回，把旧账放一边，凑齐了这阵仗。缺的，就是往前迈的这一步。』",
                "options": [
                    {"text": "🗡️ 为什么偏偏是现在？", "next": "expedition_now"},
                    {"text": "📜 出发。", "next": "accept_q9_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "expedition_now": {
                "text": "老约翰目光一沉：『因为裂隙在裂。北境的烽火、烬山的黑烟、你带回来的那些真相——都指向同一个地方。不去，这座山就是下一个修道院。』",
                "options": [
                    {"text": "📜 出发。", "next": "accept_q9_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q9_1": {
                "text": "老约翰：『好。烬山在等我们。这一仗，老头子陪你走到底。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "expedition_set"}},
                ],
            },
            "hunter_old": {
                "text": "老约翰拄剑而立：『三百年前我来过这里……那时候，我还能劈开恶魔的头骨。现在嘛，只能劈开酒桶了。可老兵不死，只是换了种打法。你替我冲，我在阵后给你断后路。』",
                "options": [
                    {"text": "🗡️ 那你就看着我怎么劈。", "next": "accept_q9_2"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q9_2": {
                "text": "老约翰：『好——锋头要快，选要害，别缠斗。扫完缺口就回来，别逞英雄。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "battle_worn"}},
                ],
            },
            "halga_ritual": {
                "text": "老约翰面色铁青：『那疯婆子站在符文轮盘上，隔着老远冲我们喊——原话我记得清楚。』",
                "options": [
                    {"text": "🗣️ 她说了什么？", "next": "halga_quote"},
                    {"text": "📜 我去探祭坛。", "next": "accept_q9_3"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "halga_quote": {
                "text": "老约翰一字一句，像是咬着牙补出来的：『她说——“封印松动是必然的。你们的教会用谎言维持了三百年，也该到还债的时候了。”她不是信口开河，小子，她说的正是咱们查到的东西。』",
                "options": [
                    {"text": "🗡️ 那就去堵住她的嘴。", "next": "accept_q9_3"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q9_3": {
                "text": "老约翰：『探清楚她布阵的门道就回来——我们得知道，她下一步要撕哪儿。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "saw_helga"}},
                ],
            },
            "seal_tear": {
                "text": "老约翰低声道：『赫尔加是这一环的钥匙。她主持的仪式，就是在往下撕封印——每转一圈，裂隙就薄一分、黑一分。你不是去跟她讲道理，是去停掉那架轮盘。』",
                "options": [
                    {"text": "🗡️ 圣徽能压住她吗？", "next": "seal_emblem"},
                    {"text": "📜 我去宰了她。", "next": "accept_q9_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "seal_emblem": {
                "text": "老约翰点点头：『你手上的圣徽，承载着历代圣女的光。那是最纯的圣光，也是赫尔加那套邪法最忌讳的东西。必要时，让它见见光。』",
                "options": [
                    {"text": "📜 我去宰了她。", "next": "accept_q9_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q9_4": {
                "text": "老约翰把手按在你肩上，声音很重：『这一刀，替三百年前死在烬山的老兄弟们一起砍。去吧。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "know_seal_cost"}},
                ],
            },
            "alliance_grief": {
                "text": "老约翰：『精灵记着人族背过盟约，矮人嫌北境太莽，北境觉得南方忘恩负义，骑士团又一身教会的包袱——三百年积的疙瘩，堆一块儿了。你要去，不是讲大道理，是让他们看见一个愿意把后背交出去的愣头青站在中间。』",
                "options": [
                    {"text": "🗡️ 信任这种东西，得有人先迈一步。", "next": "accept_q9_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q9_5": {
                "text": "老约翰：『好——把几堆火拢成一堆。三百年后，我们再次并肩，这一次，不会让历史重演。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "alliance_united"}},
                ],
            },
            "watch_dark": {
                "text": "老约翰压低声音：『深渊奴仆夜里常来试探防线，这个好对付。真正要盯的是裂隙本身——那金光底下，有什么东西在注视着咱们。你若看见了，回来一个字都别漏。』",
                "options": [
                    {"text": "🤔 那金光底下是什么？", "next": "watch_rift"},
                    {"text": "📜 我去值夜。", "next": "accept_q9_6"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "watch_rift": {
                "text": "老约翰沉吟：『三百年前英雄王用命封住的东西……我不说是怪物。孩子，等你在那金光里看清楚了，你就知道这世界欠它一声“谢”还是“罪”。』",
                "options": [
                    {"text": "📜 我去值夜。", "next": "accept_q9_6"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q9_6": {
                "text": "老约翰：『活着回来。黑夜过去，你若还站在营火边，就是最好的捷报。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "saw_the_rift"}},
                ],
            },
            "march_diff": {
                "text": "老约翰目光灼灼：『上一次，联军是教会的命令、王室的敕令撑起来的；这一次，没有命令，没有敕令——纯粹是四族自己想明白了，要跟这三百年的谎言做个了断。这才是真正的“并肩”。』",
                "options": [
                    {"text": "😔 可三百年前，你说你信错了一次。", "next": "march_regret"},
                    {"text": "📜 集结联军。", "next": "accept_q11_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "march_regret": {
                "text": "老约翰沉默片刻，给自己倒满酒：『刻进骨头的教训，也挡不住这趟非走不可。正因为年轻时信错了一次，如今我才更不能袖手旁观。这趟，我会跟到底。』",
                "options": [
                    {"text": "📜 集结联军。", "next": "accept_q11_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q11_4": {
                "text": "老约翰：『三百年前，我跟着英雄王走过这条路。今天，我跟着你，再走一次。你下令吧，小子。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "final_march"}},
                ],
            },
            "pack_tactics": {
                "text": "老约翰：『深渊猎犬成片成片地涌，单打独斗是找死。你顶上，精灵的箭雨、矮人的战阵就压得上来。你不是一个人扛——你扛住的这口气，就是全军的锚。』",
                "options": [
                    {"text": "📜 我带光盾顶前面。", "next": "accept_q12_1"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q12_1": {
                "text": "老约翰：『记住，老兵我站在你身后三步远。你想往哪儿破，我就跟你往哪儿压。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "battle_worn"}},
                ],
            },
            "toast_to": {
                "text": "老约翰把酒举过眉梢：『打仗有一半是为了不输，另一半，是为了赢回来的时候，能有一杯酒，敬给那些没走到今天的人。这第一杯——你先敬了自己。别急着领功，先让所有人记住：那个人，是咱们行会的。』",
                "options": [
                    {"text": "🕯️ 也敬没能走到黎明的人。", "next": "toast_fallen"},
                    {"text": "📜 我接这杯酒。", "next": "accept_q12_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "toast_fallen": {
                "text": "老约翰点点头，把酒洒了一半在地上：『敬烬山的老骨头、敬这三百年来的每一句谎言下压着的真心。他们没白等——今儿，有人替他们喝到了黎明。』",
                "options": [
                    {"text": "📜 我接这杯酒。", "next": "accept_q12_4"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q12_4": {
                "text": "老约翰：『那就喝吧，小子。这是你挣来的。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "dawn_beer"}},
                ],
            },
            "who_waits": {
                "text": "老约翰扫了一圈营地：『艾莉丝站在码头边上，罗兰握着那把折过的剑，四族的代表还守着营火。每个人，都有句想亲口跟你说的话。别嫌絮叨——这是救命恩人才有的礼数。』",
                "options": [
                    {"text": "🕊️ 先见艾莉丝吧。", "next": "farewell_saintess"},
                    {"text": "⚔️ 先见罗兰。", "next": "farewell_roland"},
                    {"text": "🔥 先见各族代表。", "next": "farewell_races"},
                    {"text": "📜 我去听大家的告别。", "next": "accept_q12_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "farewell_saintess": {
                "text": "艾莉丝朝你弯了弯嘴角，声音很轻：\"谢谢你。这一次，我是自愿站在这里，不是作为祭品——是作为见证黎明的人。\"",
                "options": [
                    {"text": "🤍 我记住了。", "next": "accept_q12_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "farewell_roland": {
                "text": "罗兰把那把折断又重铸的剑背到肩上，郑重道：\"骑士的剑，只为守护值得守护的人。从今天起，我也是。\"",
                "options": [
                    {"text": "⚔️ 我也记住了。", "next": "accept_q12_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "farewell_races": {
                "text": "精灵的箭手按胸致礼，矮人举了举锤子，北境人吼了一嗓子战吼，骑士团的光盾齐刷刷立起——没有一句话，却像是说了千言万语。",
                "options": [
                    {"text": "🔥 我都收下了。", "next": "accept_q12_5"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "accept_q12_5": {
                "text": "老约翰看着散开的人群轻笑：『都道完别了。可你瞧，没有人先走。没有你，我们走不到今天。这趟告别，够记一辈子。』",
                "options": [
                    {"text": "📜 出发！", "next": "__end__", "action": {"quest_take": True, "set_flag": "farewell_done"}},
                ],
            },
            "ritual_gather": {
                "text": "老约翰清了清嗓子，敲了两下桌面让喧闹安静下来：『各位，行会创会以来头一遭——请大家静一静。』",
                "options": [
                    {"text": "🤫（顺着人群安静下来）", "next": "ritual_walk"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ritual_walk": {
                "text": "老约翰示意你走到大厅正中，环视满堂冒险者：『三百年前，这里的人追的是英雄王的光。三百年后，我们追的是——眼前这个把黎明带回来的孩子。』",
                "options": [
                    {"text": "✨（站到正中，接受注视）", "next": "ritual_medal"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ritual_medal": {
                "text": "老约翰从怀里取出一枚崭新的传奇徽章，双手捧着，郑重别在你胸前：『从今以后，你就是行会的一面旗。』",
                "options": [
                    {"text": "🛡️（挺直胸膛，接下徽章）", "next": "ritual_bless"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ritual_bless": {
                "text": "老约翰难得动容，压低了声音：『没加冕为王，没成神——你只是走了所有冒险者该走的路，走成了第一个“传奇”。老头子这辈子最骄傲的事，就是当初在铁港城门口，朝你伸了那杯酒。』",
                "options": [
                    {"text": "🕯️ 也谢你，老约翰。", "next": "ritual_close"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "ritual_close": {
                "text": "老约翰拍在你肩上的手微微用力，而后松开，咧嘴一笑：『大陆的冒险，还在继续。这面旗，你扛稳了。』",
                "options": [
                    {"text": "🛡️ 我记住了。", "next": "__end__", "action": {"quest_take": True, "set_flag": "legend_bearer"}},
                ],
            },
            "talk_first": {
                "text": "老约翰拍了拍你的肩：『铁港城头一脚你踩实了。往后这城里，没有人能再拿“你是新来的”欺负你——你是我老约翰看中的人。』",
                "options": [
                    {"text": "🛡️ 我记下了。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_letter": {
                "text": "老约翰望着窗外的码头出神：『那封信会送到哪里、掀起多大的浪，现在谁也说不清。可你答应送出去的那一刻起，你已经不是个跑腿的了——你在帮一个人，把一句话捎到它该去的地方。』",
                "options": [
                    {"text": "✉️ 我会把话带到。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_scar": {
                "text": "老约翰给自己斟满酒：『今天这些话，我大半辈子没跟人提过。说出来，不是图个痛快——是想让你知道，我信你信得值。』",
                "options": [
                    {"text": "🔥 我不会辜负。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_saintess": {
                "text": "老约翰低声：『她是圣光的容器，可教会要的从来不是光，是那道光带来的权威。你去晨曦城，见到国王，把圣徽给他看——他会懂的。铁港城，永远给你留着一盏灯。』",
                "options": [
                    {"text": "🕊️ 我替你把话带到他跟前。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_ember_invite": {
                "text": "老约翰望着北边渐起的烟：『烬山要去了，心里反倒踏实。这次不是一个人，是一整支为真相而来的队伍。小子，你做到了三百年没人做到的事——把四族聚到一条路上。』",
                "options": [
                    {"text": "🔥 这才刚开始。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_old_war": {
                "text": "老约翰拄着剑，难得地笑了：『今天这一架，让我想起年轻时候。说实话，老了也有老的好处——知道自己底细，就不再怕死了，只怕留遗憾。这回，没遗憾。』",
                "options": [
                    {"text": "⚔️ 你还没老。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_halga": {
                "text": "老约翰：『赫尔加临死还说教会一边假装封印稳固、一边等献祭。她说得没错。三百年前我信错了人一次，这次，我信你。』",
                "options": [
                    {"text": "🤝 我也信你。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_march": {
                "text": "老约翰把酒壶别好，沉声道：『三百年前我跟着英雄王，今天跟着你。有人一辈子只跟一次，我这条命，跟了两次对的人——值了。』",
                "options": [
                    {"text": "🛡️ 我们一起走完这趟。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_return": {
                "text": "老约翰把杯子轻轻放回桌面，声音有些哑：『这杯酒我敬你，也敬所有没能喝到的人。你替他们喝到了黎明——就够本了。往后，日子还长。』",
                "options": [
                    {"text": "🍺 敬黎明。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
            "talk_legacy": {
                "text": "老约翰遥望行会那面断剑与眼睛的徽记：『断剑是英雄留下的，眼睛是提醒我们——总有人看得见别人看不见的东西。如今，那面眼睛，该轮到你看前路了。退休的老头子，只配在墙根儿坐着，看你带着行会往前走。』",
                "options": [
                    {"text": "🛡️ 我会扛好这面旗。", "next": "__end__"},
                    {"text": "告辞。", "next": "__end__"},
                ],
            },
        },
    },
}
