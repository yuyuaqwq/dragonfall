# -*- coding: utf-8 -*-
"""v87.16 定居点出口合理化：14 个无城墙定居点的出口子区域改名 + NPC 改职 + PROPS 挂载更新。

- subareas.py：橡木镇拆「东大街(城镇街道)+镇郊(城镇出口)」，其余 13 城出口改名/改类型
- npcs.py：守门卫兵改职（货郎/老农/猎户/哨兵/引路人），橡木镇新增老农·田叔
- props.py：出口子区域 PROPS 挂载点同步
"""
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUB = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\subareas.py"
NPC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\npcs.py"
PROP = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\props.py"

# ============ 1. subareas.py ============
with open(SUB, encoding='utf-8') as f:
    sub = f.read()

# 橡木镇：城门块 → 东大街 + 镇郊（两个子区域）
oak_gate_block = re.search(r'        \{\n            "id": "oak_town_gate",.*?\n        \},', sub, re.S)
assert oak_gate_block, 'oak_town_gate block not found'
oak_new = '''        {
            "id": "oak_town_street",
            "name": "东大街",
            "icon": "🏘️",
            "desc": "橡木镇最热闹的街道，两侧是木板房与布棚摊，沿街飘着烤面包的香气。走到尽头，镇子就融进了田野。",
            "type": "城镇街道",
            "lv": 1,
            "npcs": ["npc_oak_street_vendor"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_town_outskirts",
            "name": "镇郊",
            "icon": "🌾",
            "desc": "橡木镇边缘的田野，麦垛堆在路边，一条土路向东延伸进橡木平原，向西通往枫橡村。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_oak_outskirts_farmer"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },'''
sub = sub[:oak_gate_block.start()] + oak_new + sub[oak_gate_block.end():]

# 其余 13 城出口：id / name / icon / desc / type / npc 全部替换
sub_repl = [
    # (旧块特征串, 新块特征串) —— 用正则整块替换
    (r'"id": "silver_brook_gate".*?"healer": False',
     '"id": "silver_brook_outskirts",\n            "name": "镇郊田垄",\n            "icon": "🌾",\n            "desc": "银溪镇外的麦田与菜畦，田垄间的小路通向谷地与风车原野，空气中满是新麦的味道。",\n            "type": "城镇出口",\n            "lv": 12,\n            "npcs": ["npc_silver_brook_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "maple_village_gate".*?"healer": False',
     '"id": "maple_village_fields",\n            "name": "村外田野",\n            "icon": "🌾",\n            "desc": "枫橡村外的田野与木栅，麦田尽头的小路通向落石峡谷与野猪岭，村口的老枫树在风里沙沙响。",\n            "type": "城镇出口",\n            "lv": 6,\n            "npcs": ["npc_maple_village_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "ironshield_town_gate".*?"healer": False',
     '"id": "ironshield_town_sentry",\n            "name": "镇口哨卡",\n            "icon": "🛡️",\n            "desc": "铁盾镇口的拒马与烽火台，哨兵在此盘查过往旅人。木栅外是通往丘陵与旧战场的路。",\n            "type": "城镇出口",\n            "lv": 30,\n            "npcs": ["npc_ironshield_town_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "star_song_gate".*?"healer": False',
     '"id": "star_song_path",\n            "name": "镇口林径",\n            "icon": "🌿",\n            "desc": "星歌镇口掩在银叶林间的林间小径，萤火虫在暮色里浮动，小路向南通向翠谷。",\n            "type": "城镇出口",\n            "lv": 48,\n            "npcs": ["npc_star_song_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "aurora_town_gate".*?"healer": False',
     '"id": "aurora_town_path",\n            "name": "镇口雪径",\n            "icon": "❄️",\n            "desc": "极光镇口的雪径在极光下泛着幽蓝的光，雪松夹道，小路通向冰原与霜语峡谷。",\n            "type": "城镇出口",\n            "lv": 70,\n            "npcs": ["npc_aurora_town_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "dragon_kin_gate".*?"healer": False',
     '"id": "dragon_kin_mouth",\n            "name": "聚落口",\n            "icon": "🐉",\n            "desc": "龙裔聚落的入口，两根龙牙石柱分立两侧，石阶向下延伸进龙裔谷道。",\n            "type": "城镇出口",\n            "lv": 82,\n            "npcs": ["npc_dragon_kin_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "jade_port_gate".*?"healer": False',
     '"id": "jade_port_dock",\n            "name": "翡翠码头",\n            "icon": "⛵",\n            "desc": "翡翠港的泊位栈桥，船缆系在木桩上，潮声阵阵，从这里登船可去往群岛海域。",\n            "type": "城镇出口",\n            "lv": 35,\n            "npcs": ["npc_jade_port_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "shell_town_gate".*?"healer": False',
     '"id": "shell_town_beach",\n            "name": "渔港滩",\n            "icon": "🌊",\n            "desc": "贝壳镇外的沙滩泊着几艘独木舟，退潮后礁石露出来，海路通向珊瑚礁与海妖湾。",\n            "type": "城镇出口",\n            "lv": 40,\n            "npcs": ["npc_shell_town_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "nameless_harbor_gate".*?"healer": False',
     '"id": "nameless_harbor_anchorage",\n            "name": "外锚地",\n            "icon": "⚓",\n            "desc": "无名港灯塔下的外海锚区，雾钟在风里低鸣，远洋船从这里启航驶向无尽海。",\n            "type": "城镇出口",\n            "lv": 55,\n            "npcs": ["npc_nameless_harbor_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "deep_tunnel_gate".*?"healer": False',
     '"id": "deep_tunnel_mouth",\n            "name": "深隧口",\n            "icon": "🕳️",\n            "desc": "深岩隧道尽头的开阔口，铁轨从这里伸进矮人长廊，矿灯的光在岩壁上晃动。",\n            "type": "城镇出口",\n            "lv": 65,\n            "npcs": ["npc_deep_tunnel_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "under_market_gate".*?"healer": False',
     '"id": "under_market_mouth",\n            "name": "集市口",\n            "icon": "🪜",\n            "desc": "地底集市的悬梯口，菌灯在头顶发着幽光，悬梯通往真菌森林与熔火深渊方向。",\n            "type": "城镇出口",\n            "lv": 70,\n            "npcs": ["npc_under_market_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "cold_ridge_gate".*?"healer": False',
     '"id": "cold_ridge_sentry",\n            "name": "雪原哨卡",\n            "icon": "🛡️",\n            "desc": "寒脊营地边缘的木栅哨卡，雪地里插着狼皮旗，哨位外是通往铁砧的雪道。",\n            "type": "城镇出口",\n            "lv": 68,\n            "npcs": ["npc_cold_ridge_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
    (r'"id": "ember_camp_gate".*?"healer": False',
     '"id": "ember_camp_sentry",\n            "name": "灰烬哨口",\n            "icon": "🔥",\n            "desc": "灰烬营地边缘的黑铁栏哨位，岩浆渠在旁边流过，哨口外是熔岩道与熔岩滩方向。",\n            "type": "城镇出口",\n            "lv": 85,\n            "npcs": ["npc_ember_camp_gate_guard"],\n            "monsters": [],\n            "elite": None,\n            "boss": None,\n            "funcs": [],\n            "shop": False,\n            "healer": False'),
]

for pat, new in sub_repl:
    m = re.search(pat, sub, re.S)
    if not m:
        print(f'!! subareas: pattern not found: {pat[:40]}')
        continue
    sub = sub[:m.start()] + new + sub[m.end():]
    print(f'  subareas: replaced {pat[6:30]}...')

with open(SUB, 'w', encoding='utf-8') as f:
    f.write(sub)
print('subareas.py done')

# ============ 2. npcs.py ============
with open(NPC, encoding='utf-8') as f:
    npc = f.read()

npc_repl = [
    # 橡木镇守门卫兵·大牛 → 货郎·大牛（东大街）
    (r'"npc_oak_town_gate_guard": \{\n        .*?\n    \},',
     '"npc_oak_street_vendor": {\n'
     "        'name': \"货郎·大牛\",\n"
     "        'title': \"橡木镇东大街货郎\",\n"
     "        'map': \"oak_town\",\n"
     "        'icon': \"🧺\",\n"
     "        'funcs': [\"lore\"],\n"
     "        'dialogue': \"沿东大街走到头就是镇郊，出镇往东是橡木平原，往西是枫橡村。赶路前在我这儿捎点干粮吧。\",\n"
     '    },'),
]
# 其余守门卫兵：title/dialogue 调整（id 不变，挂载点不变，只改职）
npc_retitle = [
    ('npc_silver_brook_gate_guard', '老农·阿田', '银溪镇郊老农',
     '田垄外的路我熟得很：往南是银溪谷地，往东是风车原野。要过溪，走那座石桥。'),
    ('npc_maple_village_gate_guard', '猎户·阿柴', '枫橡村猎户',
     '出村往南是落石峡谷，往北翻过野猪岭。山里野物多，进林子前把家伙备好。'),
    ('npc_ironshield_town_gate_guard', '哨兵·铁柱', '铁盾镇口哨兵',
     '镇口哨卡日夜有人值守。往西是铁盾丘陵，往北是旧战场，往南是金穗平原。'),
    ('npc_star_song_gate_guard', '巡林人·林歌', '星歌镇巡林人',
     '镇口林径通向翠谷，夜里萤火虫多，认路就看银河的方向。'),
    ('npc_aurora_town_gate_guard', '猎手·白霜', '极光镇猎手',
     '镇口雪径往南是永冻冰原，往西是霜语峡谷。雪天路滑，跟着我的足迹走。'),
    ('npc_dragon_kin_gate_guard', '引路者·鳞甲', '龙裔聚落引路者',
     '聚落口石阶向下是龙裔谷道。外人头回来，别碰路边的龙牙石柱。'),
    ('npc_under_market_gate_guard', '引路人·坚岩', '地底集市引路人',
     '集市口悬梯通着三处：真菌森林、地下湖、熔火深渊。认准菌灯颜色就不会走错。'),
    ('npc_cold_ridge_gate_guard', '哨兵·寒风', '寒脊营地哨兵',
     '哨卡外只有一条雪道通铁砧要塞。暴风雪天别赶路，营地火塘一直烧着。'),
    ('npc_ember_camp_gate_guard', '哨兵·焦岩', '灰烬营地哨兵',
     '哨口外是熔岩道和熔岩滩。地底的岔路多，迷路了就顺着岩浆渠走。'),
]

for key, name, title, dialogue in npc_retitle:
    pat = re.compile(r'("' + key + r'": \{\n        .*?)(\'name\': ")([^"]+)("\n        \'title\': ")([^"]+)(")(.*?)(\'dialogue\': ")([^"]+)("\n    \})', re.S)
    m = pat.search(npc)
    if not m:
        print(f'!! npcs: pattern not found: {key}')
        continue
    npc = npc[:m.start()] + f'"{key}": {{\n' + f"        'name': \"{name}\",\n        'title': \"{title}\",\n        'map': \"{m.group(6).split(chr(39))[0]}\"" + '\n' + m.group(0)[m.group(0).find("'icon'"):m.group(0).find("'dialogue'")] + f"        'dialogue': \"{dialogue}\",\n    }}" + npc[m.end():]
    print(f'  npcs: retitled {key} -> {name}')

# 新增老农·田叔（镇郊）
if 'npc_oak_outskirts_farmer' not in npc:
    anchor = '"npc_white_deer_gate_guard": {'
    idx = npc.find(anchor)
    assert idx > 0, 'anchor npc not found'
    new_npc = '''    "npc_oak_outskirts_farmer": {
        'name': "老农·田叔",
        'title': "橡木镇郊老农",
        'map': "oak_town",
        'icon': "🌾",
        'funcs': ["lore"],
        'dialogue': "这镇子没有城墙，出了东大街就是田野。往东走半天到橡木平原，往西过两个村口是枫橡村。",
    },
'''
    npc = npc[:idx] + new_npc + npc[idx:]
    print('  npcs: added npc_oak_outskirts_farmer')

with open(NPC, 'w', encoding='utf-8') as f:
    f.write(npc)
print('npcs.py done')

# ============ 3. props.py ============
with open(PROP, encoding='utf-8') as f:
    prop = f.read()

prop_repl = [
    # 橡木镇：城门 props → 东大街 + 镇郊
    ("'oak_town:oak_town_gate': [('boundary_stone', '橡木镇界碑'), ('old_tree', '镇口老橡树'), 'camp_flag'],",
     "'oak_town:oak_town_street': [('stall', '街角布棚摊'), ('well', '街心水井'), 'washing_line'],\n"
     "    'oak_town:oak_town_outskirts': [('boundary_stone', '橡木镇界碑'), ('old_tree', '镇口老橡树'), 'haystack'],"),
    ("'silver_brook:silver_brook_gate': [('boundary_stone', '银溪镇界碑'), ('old_tree', '溪畔垂柳'), 'camp_flag'],",
     "'silver_brook:silver_brook_outskirts': [('boundary_stone', '银溪镇界碑'), ('old_tree', '溪畔垂柳'), 'haystack'],"),
    ("'maple_village:maple_village_gate': [('boundary_stone', '枫橡村寨碑'), ('old_tree', '村口老枫树'), 'camp_flag'],",
     "'maple_village:maple_village_fields': [('boundary_stone', '枫橡村碑'), ('old_tree', '村口老枫树'), 'haystack'],"),
    ("'ironshield_town:ironshield_town_gate': [('statue', '铁盾卫兵像'), ('boundary_stone', '铁盾镇界碑'), 'camp_flag'],",
     "'ironshield_town:ironshield_town_sentry': [('statue', '铁盾卫兵像'), ('boundary_stone', '铁盾镇界碑'), 'camp_flag'],"),
    ("'star_song:star_song_gate': [('elf_carving', '星歌藤纹'), ('boundary_stone', '星歌镇界碑'), 'camp_flag'],",
     "'star_song:star_song_path': [('elf_carving', '星歌藤纹'), ('boundary_stone', '星歌镇界碑'), 'camp_flag'],"),
    ("'aurora_town:aurora_town_gate': [('ice_sculpture', '极光镇冰鹿像'), ('boundary_stone', '极光镇界碑'), 'camp_flag'],",
     "'aurora_town:aurora_town_path': [('ice_sculpture', '极光镇冰鹿像'), ('boundary_stone', '极光镇界碑'), 'camp_flag'],"),
    ("'dragon_kin:dragon_kin_gate': [('rune_pillar', '龙裔寨门柱'), ('boundary_stone', '龙裔聚落碑'), 'camp_flag'],",
     "'dragon_kin:dragon_kin_mouth': [('rune_pillar', '龙裔聚落柱'), ('boundary_stone', '龙裔聚落碑'), 'camp_flag'],"),
    ("'jade_port:jade_port_gate': [('anchor', '翡翠港埠锚'), ('lighthouse', '翡翠港灯台'), 'camp_flag'],",
     "'jade_port:jade_port_dock': [('anchor', '翡翠港埠锚'), ('lighthouse', '翡翠港灯台'), 'camp_flag'],"),
    ("'shell_town:shell_town_gate': [('anchor', '贝壳镇老锚'), ('fishing_boats', '海门渔船'), 'camp_flag'],",
     "'shell_town:shell_town_beach': [('anchor', '贝壳镇老锚'), ('fishing_boats', '渔港渔船'), 'camp_flag'],"),
    ("'nameless_harbor:nameless_harbor_gate': [('lighthouse', '无名港雾灯'), ('anchor', '无名港旧锚'), 'camp_flag'],",
     "'nameless_harbor:nameless_harbor_anchorage': [('lighthouse', '无名港雾灯'), ('anchor', '无名港旧锚'), 'camp_flag'],"),
    ("'deep_tunnel:deep_tunnel_gate': [('minecart', '隧口矿车'), ('boundary_stone', '深隧界碑'), 'camp_flag']," if "'deep_tunnel:deep_tunnel_gate'" in prop else None,
     "'deep_tunnel:deep_tunnel_mouth': [('minecart', '隧口矿车'), ('boundary_stone', '深隧界碑'), 'camp_flag'],"),
    ("'under_market:under_market_gate': [('minecart', '集市闸车'), ('boundary_stone', '集市界碑'), 'camp_flag']," if "'under_market:under_market_gate'" in prop else None,
     "'under_market:under_market_mouth': [('minecart', '集市闸车'), ('boundary_stone', '集市界碑'), 'camp_flag'],"),
    ("'cold_ridge:cold_ridge_gate': [('boundary_stone', '寒脊营界碑'), ('campfire_remains', '营门篝火'), 'camp_flag'],",
     "'cold_ridge:cold_ridge_sentry': [('boundary_stone', '寒脊营界碑'), ('campfire_remains', '哨卡篝火'), 'camp_flag'],"),
    ("'ember_camp:ember_camp_gate': [('campfire_remains', '灰烬营火'), ('boundary_stone', '灰烬营碑'), 'camp_flag']," if "'ember_camp:ember_camp_gate'" in prop else None,
     "'ember_camp:ember_camp_sentry': [('campfire_remains', '灰烬营火'), ('boundary_stone', '灰烬营碑'), 'camp_flag'],"),
]

for old, new in prop_repl:
    if old is None:
        continue
    if old in prop:
        prop = prop.replace(old, new)
        print(f'  props: replaced {old[1:35]}')
    else:
        print(f'!! props: not found: {old[1:40]}')

with open(PROP, 'w', encoding='utf-8') as f:
    f.write(prop)
print('props.py done')
print('ALL DONE')
