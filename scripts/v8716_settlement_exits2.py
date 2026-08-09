# -*- coding: utf-8 -*-
"""v87.16 第二轮：用简单字符串替换修复 npcs.py 守卫改职 + props.py 剩余 3 键。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NPC = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\npcs.py"
PROP = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\props.py"

with open(NPC, encoding='utf-8') as f:
    npc = f.read()

# 1. 橡木镇守卫 → 货郎（整块替换）
old_oak = '''    "npc_oak_town_gate_guard": {
        'name': "守门卫兵·大牛",
        'title': "橡木镇守门卫兵",
        'map': "oak_town",
        'icon': "🛡️",
        'funcs': ["lore"],
        'dialogue': "出镇往东是橡木平原，往西是枫橡村。夜里城门关得早，赶路别贪黑。",
    },'''
new_oak = '''    "npc_oak_street_vendor": {
        'name': "货郎·大牛",
        'title': "橡木镇东大街货郎",
        'map': "oak_town",
        'icon': "🧺",
        'funcs': ["lore"],
        'dialogue': "沿东大街走到头就是镇郊，出镇往东是橡木平原，往西是枫橡村。赶路前在我这儿捎点干粮吧。",
    },'''
assert old_oak in npc, 'oak guard block not found'
npc = npc.replace(old_oak, new_oak)
print('oak guard -> street vendor OK')

# 2. 其余守卫改职：只改 name/title/dialogue（map/icon/funcs 保留）
retitle = [
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
for key, name, title, dialogue in retitle:
    # 定位该 NPC 块
    start = npc.find(f'    "{key}": {{')
    assert start > 0, f'{key} not found'
    end = npc.find('\n    },', start)
    block = npc[start:end]
    # 替换 name/title/dialogue 三行
    import re
    block2 = re.sub(r"'name': \"[^\"]*\"", f"'name': \"{name}\"", block, count=1)
    block2 = re.sub(r"'title': \"[^\"]*\"", f"'title': \"{title}\"", block2, count=1)
    block2 = re.sub(r"'dialogue': \"[^\"]*\"", f"'dialogue': \"{dialogue}\"", block2, count=1)
    npc = npc[:start] + block2 + npc[end:]
    print(f'{key} -> {name} OK')

with open(NPC, 'w', encoding='utf-8') as f:
    f.write(npc)
print('npcs.py done')

# ===== props.py 剩余 3 键 =====
with open(PROP, encoding='utf-8') as f:
    prop = f.read()

prop_fix = [
    ("'deep_tunnel:deep_tunnel_gate': [('rune_pillar', '深隧矮人符文柱'), ('minecart', '深隧闸前矿车'), 'camp_flag'],",
     "'deep_tunnel:deep_tunnel_mouth': [('rune_pillar', '深隧矮人符文柱'), ('minecart', '深隧口矿车'), 'camp_flag'],"),
    ("'under_market:under_market_gate': [('rune_pillar', '地底集市闸柱'), ('boundary_stone', '地底集市界碑'), 'camp_flag'],",
     "'under_market:under_market_mouth': [('rune_pillar', '地底集市闸柱'), ('boundary_stone', '地底集市界碑'), 'camp_flag'],"),
    ("'ember_camp:ember_camp_gate': [('boundary_stone', '灰烬营界碑'), ('campfire_remains', '营门余烬火'), 'camp_flag'],",
     "'ember_camp:ember_camp_sentry': [('boundary_stone', '灰烬营界碑'), ('campfire_remains', '哨口余烬火'), 'camp_flag'],"),
]
for old, new in prop_fix:
    assert old in prop, f'props not found: {old[1:40]}'
    prop = prop.replace(old, new)
    print(f'props: {old[1:35]} -> OK')

with open(PROP, 'w', encoding='utf-8') as f:
    f.write(prop)
print('props.py done')
print('ALL DONE')
