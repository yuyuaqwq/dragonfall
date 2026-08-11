# -*- coding: utf-8 -*-
"""v95.29 城镇活人计划 Part1：核心城镇（橡木/白鹿/铁港/晨曦/银溪/枫橡/铁盾）补酱油 NPC
用法：python scripts/add_flavor_npcs.py
"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
NPCS_PATH = os.path.join(BASE, "..", "game", "data", "npcs.py")
SUBAREAS_PATH = os.path.join(BASE, "..", "game", "data", "subareas.py")

# ============ 新酱油 NPC 定义（funcs=[] 纯闲聊） ============
NEW_NPCS = {
    # ===== 橡木镇 =====
    "npc_oak_candy": {"name": "卖糖人·蜜嘴", "title": "橡木镇糖贩", "map": "oak_town", "icon": "🍭", "dialogue": "糖葫芦哎——现熬的麦芽糖，甜到心里头！冒险者来一串？保准打史莱姆都有劲。"},
    "npc_oak_novice": {"name": "新手冒险者·阿木", "title": "橡木镇新手冒险者", "map": "oak_town", "icon": "⚔️", "dialogue": "今天一定要打到一张史莱姆黏液！……虽然上次差点被巨型野猪追回镇里，但那都是意外。"},
    "npc_oak_oldman": {"name": "晒太阳的老爷子·常青", "title": "橡木镇老镇民", "map": "oak_town", "icon": "👴", "dialogue": "我年轻时也闯过白鹿城！现在嘛，广场这长椅就是我的冒险地。年轻人，外面的世界大着咧。"},
    "npc_oak_kid": {"name": "顽童·泥鳅", "title": "橡木镇小孩", "map": "oak_town", "icon": "🧒", "dialogue": "我妈说我再追鸡就罚我扫院子！嘿嘿，但我还是会追，你看那只鸡多神气！"},
    "npc_oak_clerk": {"name": "文书·墨点", "title": "镇长办公处文书", "map": "oak_town", "icon": "📜", "dialogue": "镇长又下乡了。你要是想见他，午后准在。……别问我是怎么知道这么多镇里的事，这是文书的直觉。"},
    "npc_oak_apprentice_smith": {"name": "铁匠学徒·炭头", "title": "老铁铁匠铺学徒", "map": "oak_town", "icon": "🔥", "dialogue": "师父说我拉风箱的节奏比打铁稳。总有一天我要亲手打出一把好剑，让师父刮目相看！"},
    "npc_oak_bellboy": {"name": "旅店伙计·跑堂", "title": "橡木桶旅店伙计", "map": "oak_town", "icon": "🍺", "dialogue": "客官住店不？二楼东边那间窗子正对着广场，清晨还能听见鸟儿叫！"},
    "npc_oak_herb_girl": {"name": "抓药学徒·小荷", "title": "草药铺学徒", "map": "oak_town", "icon": "🌿", "dialogue": "这个是薄荷，这个是鼠尾草……哎呀，师父说认错一味药会出大事，我可得仔细些！"},
    "npc_oak_vegwife": {"name": "卖菜婶·青芹", "title": "东大街菜贩", "map": "oak_town", "icon": "🥬", "dialogue": "刚从地里摘的，水灵着呢！冒险者也要吃饭，来把青菜，配着野猪肉炖，香得很！"},
    "npc_oak_farmer": {"name": "农夫·满仓", "title": "橡木镇农夫", "map": "oak_town", "icon": "🌾", "dialogue": "这片田我种了二十年了。镇长说镇上来了个能打史莱姆的冒险者，就是你吧？好样的！"},
    # ===== 白鹿城 =====
    "npc_deer_guard": {"name": "巡城卫兵·铁靴", "title": "白鹿城卫兵", "map": "white_deer", "icon": "🛡️", "dialogue": "白鹿城宵禁前请回到城墙内。……这是例行提醒，不用紧张，你一看就是个正经冒险者。"},
    "npc_deer_bard": {"name": "吟游诗人·琴心", "title": "白鹿城街头诗人", "map": "white_deer", "icon": "🎻", "dialogue": "（拨弦）白鹿城的故事三天三夜唱不完——南境的雪、铁港的浪、还有圣光下失落的王冠。给个铜板，我唱你听？"},
    "npc_deer_scribe": {"name": "书记官·笔直", "title": "城主府书记官", "map": "white_deer", "icon": "✒️", "dialogue": "觐见城主请先在名册登记。……对，就是那一栏。字写工整些，上次有人写太潦草，害我抄了三遍。"},
    "npc_deer_blacksmith_h": {"name": "打铁汉·粗臂", "title": "鹿角铁匠铺帮工", "map": "white_deer", "icon": "🔨", "dialogue": "汉斯老板的手艺，那叫一个绝！我给他打了十年下手，还是学不完他淬火的火候。"},
    "npc_deer_nun": {"name": "修女·百合", "title": "白鹿圣堂修女", "map": "white_deer", "icon": "🕊️", "dialogue": "圣光庇佑每一位赶路的人。来，这里有一小袋干粮，带上吧，愿它陪你走完旅程。"},
    "npc_deer_drunk": {"name": "醉汉·麦桶", "title": "白鹿与麦酒酒馆常客", "map": "white_deer", "icon": "🍻", "dialogue": "我跟你说……嗝！这酒馆的麦酒，全南境第一！当年我……我在海上……嗝，算了，不重要！"},
    "npc_deer_nurse": {"name": "医助·艾草", "title": "白鹿城医师馆助手", "map": "white_deer", "icon": "💊", "dialogue": "温蒂医师交代了，伤口换药前不能沾水。……别嫌我啰嗦，上个月有个冒险者不听劝，伤口又裂了。"},
    "npc_deer_cook": {"name": "帮厨·火舌", "title": "白鹿城烹饪坊帮厨", "map": "white_deer", "icon": "🍳", "dialogue": "师父的秘制酱料，闻着就流口水吧？可惜配方不传外人——我这个帮厨闻了三年都没闻明白！"},
    "npc_deer_enchanter": {"name": "附魔学徒·亮星", "title": "白鹿城强化工坊学徒", "map": "white_deer", "icon": "✨", "dialogue": "小心！这瓶是给武器附魔的龙息油，洒到手上会烫出泡。……别问我是怎么知道的。"},
    "npc_deer_gatekeeper": {"name": "城门卫·直杆", "title": "白鹿城守门卫兵", "map": "white_deer", "icon": "🗡️", "dialogue": "进出城请出示行会徽记。……不是刁难你，上个月有哥布林想混进城，差点被它溜进去。"},
    # ===== 铁港城 =====
    "npc_harbor_sailor": {"name": "老水手·盐须", "title": "铁港城远洋水手", "map": "ironharbor", "icon": "⚓", "dialogue": "小兄弟，想听海上的故事？我这辈子见过比房子还大的鲸鱼、比旗杆还高的浪！……当然，有一半是我编的。"},
    "npc_harbor_mule": {"name": "码头力工·扛山", "title": "铁港城码头力工", "map": "ironharbor", "icon": "💪", "dialogue": "一箱、两箱……嘿哟！铁港的货，就没有我扛不动的。冒险者，要不要来比试比试？"},
    "npc_harbor_trader": {"name": "行脚商·算盘", "title": "铁港城行脚商人", "map": "ironharbor", "icon": "🧮", "dialogue": "东边的丝绸、南边的香料、北边的皮毛……只要给够价，全大陆的货我都能给你弄来。童叟无欺！"},
    "npc_harbor_auction": {"name": "拍卖行伙计·响锤", "title": "金槌拍卖行伙计", "map": "ironharbor", "icon": "🔔", "dialogue": "今晚有批深海珊瑚要拍！上次那件拍卖行经手的精灵弓，最后拍了多少来着？……反正我一年工钱都不够。"},
    "npc_harbor_bartender": {"name": "酒保·满杯", "title": "铁锚酒馆酒保", "map": "ironharbor", "icon": "🥃", "dialogue": "本店规矩：先付钱，后喝酒；吹牛可以，打架出去打。客官，来杯铁锚特调？保证你喝一口想家。"},
    "npc_harbor_ledger": {"name": "账房先生·铁算", "title": "金齿轮商行账房", "map": "ironharbor", "icon": "📒", "dialogue": "入库、出库、对账……这商行的每一枚金币都有去处。别看我瘦，我算账比谁都快！"},
    "npc_harbor_miner_old": {"name": "老矿工·石疤", "title": "铁港城矿工工会老矿工", "map": "ironharbor", "icon": "⛏️", "dialogue": "山丘矿洞的矿脉我闭着眼都能摸出来。年轻人，挖矿不是靠力气，是靠这里——（指了指脑袋）"},
    "npc_harbor_clerk": {"name": "账房·铁算", "title": "金齿轮商行账房", "map": "ironharbor", "icon": "📒", "dialogue": "入库、出库、对账……这商行的每一枚金币都有去处。别看我瘦，我算账比谁都快！"},
    "npc_harbor_fisher": {"name": "渔夫·潮生", "title": "铁港城渔人码头渔夫", "map": "ironharbor", "icon": "🎣", "dialogue": "今天潮水不错，网里全是银光闪闪的鱼！要买新鲜的？给冒险者算便宜点！"},
    "npc_harbor_forge_app": {"name": "锻工·红脸", "title": "铁港城锻造坊锻工", "map": "ironharbor", "icon": "⚒️", "dialogue": "炉火旺着咧！这把剑再淬三遍水就能上架了。别靠太近，火星子不认人。"},
    "npc_harbor_gate": {"name": "城门卫·铁闸", "title": "铁港城守门卫兵", "map": "ironharbor", "icon": "🛡️", "dialogue": "铁港城欢迎你！进去别惹事，城主最讨厌闹事的。……里面有个酒馆叫铁锚，酒不错，报我名字打九折。"},
    # ===== 晨曦城 =====
    "npc_dawn_guard": {"name": "禁卫骑士·白盔", "title": "晨曦城禁卫军", "map": "dawn_city", "icon": "🛡️", "dialogue": "王都重地，请保持肃穆。……但如果你要找圣光骑士团的驻地，顺着大教堂的尖顶走就对了。"},
    "npc_dawn_herald": {"name": "传令官·亮嗓", "title": "晨曦城传令官", "map": "dawn_city", "icon": "📯", "dialogue": "圣光王国公告——近日金穗平原盗贼出没，往来商旅请结伴而行！……这位冒险者，你看起来就是该去剿匪的人！"},
    "npc_dawn_chancellor": {"name": "内廷侍从·轻步", "title": "圣光王宫内廷侍从", "map": "dawn_city", "icon": "🕯️", "dialogue": "陛下今日不朝。……但陛下说了，为国效力的冒险者，王宫永远留一盏灯。"},
    "npc_dawn_deacon": {"name": "执事·烛明", "title": "圣光大教堂执事", "map": "dawn_city", "icon": "🕯️", "dialogue": "大教堂的钟声每日晨昏各响一次。愿圣光指引你的剑，也照亮你的路。"},
    "npc_dawn_stableboy": {"name": "马夫·缰绳", "title": "骑士团驻地马夫", "map": "dawn_city", "icon": "🐴", "dialogue": "这匹是团长的战马，叫'曙光'，脾气大得很！……它其实挺乖的，只要你别站在它身后。"},
    "npc_dawn_alchemist": {"name": "炼金学徒·沸点", "title": "晨曦城炼金工坊学徒", "map": "dawn_city", "icon": "🧪", "dialogue": "嘘——这个坩埚已经煮了三个时辰了！师父说再过一会儿就能开锅……上次我提前开锅，屋顶差点没了。"},
    "npc_dawn_gate": {"name": "城门卫·磐石", "title": "王都守门骑士", "map": "dawn_city", "icon": "🗡️", "dialogue": "王都城门，日开夜闭。冒险者，进了城记得去大教堂瞻仰一下圣辉——那是王国的骄傲。"},
    # ===== 银溪镇 =====
    "npc_silver_miller": {"name": "磨坊主·麦浪", "title": "银溪镇磨坊主", "map": "silver_brook", "icon": "🌾", "dialogue": "风车转一天，磨盘响一天。银溪的面粉是全南境最好的——不信你闻闻这风里的麦香！"},
    "npc_silver_inn": {"name": "旅店跑堂·水花", "title": "银溪镇河畔旅店伙计", "map": "silver_brook", "icon": "🍲", "dialogue": "今晚炖的是河鲜汤，加了一整条银溪鲈鱼！客官住一晚，明早保你精神百倍。"},
    "npc_silver_granny": {"name": "买菜婆·香芹", "title": "银溪镇集市老妇", "map": "silver_brook", "icon": "🧺", "dialogue": "小伙子，来赶集？我这筐菜心是自家地里种的，三文钱一把，买不了吃亏！"},
    # ===== 枫橡村 =====
    "npc_maple_granny": {"name": "晒谷婆·金穗", "title": "枫橡村村民", "map": "maple_village", "icon": "👵", "dialogue": "秋天的枫橡村最漂亮，满村都是红叶子！可惜现在不是秋天，你将就看吧。"},
    "npc_maple_child": {"name": "村童·小豆", "title": "枫橡村小孩", "map": "maple_village", "icon": "🧒", "dialogue": "我以后也要当冒险者！像你一样去很远的地方！……不过妈妈说我得先把鸡喂了。"},
    "npc_maple_hunter_w": {"name": "猎户·灰须", "title": "枫橡村猎户", "map": "maple_village", "icon": "🏹", "dialogue": "野猪岭的野猪最近又肥了。小伙子，你腰间那把剑看着不错，敢不敢跟我去岭上走一遭？"},
    "npc_maple_innkeep": {"name": "旅店帮手·麦穗", "title": "枫叶旅店帮手", "map": "maple_village", "icon": "🛏️", "dialogue": "苔丝姐姐说今晚有蜂蜜烤饼！住店的客人都有份，你来得正巧！"},
    # ===== 铁盾镇 =====
    "npc_shield_smith": {"name": "铁匠·厚掌", "title": "铁盾镇军械铺铁匠", "map": "ironshield_town", "icon": "🔨", "dialogue": "铁盾镇的盾，能挡下兽人的斧头！我打的盾，还能挡下兽人的酋长！……吹牛的，但差不太多。"},
    "npc_shield_scout": {"name": "斥候·快腿", "title": "铁盾镇斥候", "map": "ironshield_town", "icon": "🏃", "dialogue": "刚从丘陵回来，铁甲野猪又多了。镇长正发愁呢。你要是能帮忙清理，军械铺给你打折！"},
    "npc_shield_townfolk": {"name": "镇民·铜壶", "title": "铁盾镇居民", "map": "ironshield_town", "icon": "🏘️", "dialogue": "铁盾镇的日子苦，但踏实。兽人来了就打，打完接着过日子。这就是咱铁盾人的活法。"},
    "npc_shield_sentry": {"name": "哨兵·钉桩", "title": "铁盾镇哨卡卫兵", "map": "ironshield_town", "icon": "🛡️", "dialogue": "镇口哨卡，夜里轮班。北边的旧战场到了晚上总有点动静……不过有我盯着，放心！"},
}

# ============ 挂载：sa_id → 新增 NPC id 列表 ============
MOUNTS = {
    "oak_town_1": ["npc_oak_candy", "npc_oak_novice", "npc_oak_oldman", "npc_oak_kid"],
    "oak_town_2": ["npc_oak_clerk"],
    "oak_town_3": ["npc_oak_apprentice_smith"],
    "oak_town_4": ["npc_oak_bellboy"],
    "oak_town_5": ["npc_oak_herb_girl"],
    "oak_town_street": ["npc_oak_vegwife"],
    "oak_town_outskirts": ["npc_oak_farmer"],
    "white_deer_1": ["npc_deer_guard", "npc_deer_bard"],
    "white_deer_2": ["npc_deer_scribe"],
    "white_deer_3": ["npc_deer_blacksmith_h"],
    "white_deer_4": ["npc_deer_nun"],
    "white_deer_5": ["npc_deer_drunk"],
    "white_deer_6": ["npc_deer_nurse"],
    "white_deer_7": ["npc_deer_cook"],
    "white_deer_8": ["npc_deer_enchanter"],
    "white_deer_gate": ["npc_deer_gatekeeper"],
    "ironharbor_1": ["npc_harbor_sailor", "npc_harbor_trader"],
    "ironharbor_2": ["npc_harbor_ledger"],
    "ironharbor_3": ["npc_harbor_mule"],
    "ironharbor_4": ["npc_harbor_auction"],
    "ironharbor_5": ["npc_harbor_bartender"],
    "ironharbor_6": ["npc_harbor_clerk"],
    "ironharbor_7": ["npc_harbor_miner_old"],
    "ironharbor_8": ["npc_harbor_fisher"],
    "ironharbor_9": ["npc_harbor_forge_app"],
    "ironharbor_gate": ["npc_harbor_gate"],
    "silver_brook_1": ["npc_silver_miller"],
    "silver_brook_3": ["npc_silver_inn"],
    "silver_brook_4": ["npc_silver_granny"],
    "maple_village_1": ["npc_maple_granny", "npc_maple_child"],
    "maple_village_3": ["npc_maple_hunter_w"],
    "maple_village_4": ["npc_maple_innkeep"],
    "ironshield_town_1": ["npc_shield_townfolk"],
    "ironshield_town_3": ["npc_shield_smith"],
    "ironshield_town_4": ["npc_shield_scout"],
    "ironshield_town_sentry": ["npc_shield_sentry"],
    # ===== 晨曦城 =====
    "dawn_city_1": ["npc_dawn_guard", "npc_dawn_herald"],
    "dawn_city_2": ["npc_dawn_chancellor"],
    "dawn_city_3": ["npc_dawn_deacon"],
    "dawn_city_4": ["npc_dawn_stableboy"],
    "dawn_city_5": ["npc_dawn_alchemist"],
    "dawn_city_gate": ["npc_dawn_gate"],
}

# ============ 写入 npcs.py（末尾追加 NPCS.update） ============
def append_npcs():
    with open(NPCS_PATH, encoding="utf-8") as f:
        txt = f.read()
    if "v95.29 城镇活人" in txt:
        print("npcs.py 已包含 v95.29，跳过")
        return
    block = "\n\n# ===== v95.29 城镇活人计划（酱油 NPC）=====\nNPCS.update({\n"
    for k, v in NEW_NPCS.items():
        block += f"    {k!r}: {{\n"
        for fk, fv in v.items():
            block += f"        {fk!r}: {fv!r},\n"
        block += "    },\n"
    block += "})\n"
    with open(NPCS_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(txt + block)
    print(f"npcs.py 追加 {len(NEW_NPCS)} 个 NPC")

# ============ 写入 subareas.py（每个 sa 的 npcs 数组追加） ============
def append_mounts():
    with open(SUBAREAS_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    cur_id = None
    changed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
        if m:
            cur_id = m.group(1)
            i += 1
            continue
        if cur_id in MOUNTS and '"npcs"' in line:
            add_ids = MOUNTS[cur_id]
            # 情况A：单行数组 "npcs": [...] 或 "npcs": [],
            mm = re.search(r'"npcs"\s*:\s*\[([^\]]*)\]', line)
            if mm:
                inner = mm.group(1).strip()
                existing_ids = set(re.findall(r'"([a-z0-9_]+)"', inner))
                add_ids = [x for x in add_ids if x not in existing_ids]
                if add_ids:
                    if inner:
                        new_inner = inner + ", " + ", ".join(repr(x) for x in add_ids)
                    else:
                        new_inner = ", ".join(repr(x) for x in add_ids)
                    lines[i] = line[:mm.start(1)] + new_inner + line[mm.end(1):]
                    changed += 1
                cur_id = None
                i += 1
                continue
            # 情况B：多行数组 "npcs": [\n  "id"\n],（结束行可能是 "],            \"monsters\": []" 紧凑格式）
            if re.search(r'"npcs"\s*:\s*\[\s*$', line):
                indent = re.match(r'(\s*)', line).group(1) + "    "
                j = i + 1
                while j < len(lines) and "]," not in lines[j]:
                    j += 1
                if j < len(lines):
                    # 检查数组内是否已有 id（防重复挂载）
                    existing = " ".join(lines[i+1:j])
                    new_ids = [x for x in add_ids if x not in existing]
                    if new_ids:
                        # 前一行（原最后一项）若不以逗号结尾，补逗号（多行数组最后一项可能无逗号）
                        prev = j - 1
                        prev_line = lines[prev].rstrip("\r\n")
                        if prev_line.strip() and not prev_line.rstrip().endswith(","):
                            lines[prev] = prev_line + ",\n"
                        # 在结束行（含 ], 的行）前插入新 id（尾部统一加一个逗号）
                        lines.insert(j, indent + ", ".join(repr(x) for x in new_ids) + ",\n")
                        changed += 1
                    cur_id = None
                    i = j + 1
                    continue
        i += 1
    with open(SUBAREAS_PATH, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print(f"subareas.py 挂载 {changed} 处")

if __name__ == "__main__":
    append_npcs()
    append_mounts()
    # 语法检查
    import py_compile
    for p in (NPCS_PATH, SUBAREAS_PATH):
        py_compile.compile(p, doraise=True)
        print(f"编译 OK: {os.path.basename(p)}")
