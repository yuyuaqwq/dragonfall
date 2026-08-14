# -*- coding: utf-8 -*-
"""v112 npcs.py 手术：删 5 个被合并线导师 NPC；魔剑士残魂去 quest func"""
import io
import py_compile

path = 'game/data/npcs.py'
src = io.open(path, encoding='utf-8').read()

# 被合并线导师 NPC 删除（其解锁链已并入对应新线）
delete_ids = ["npc_void_watcher", "npc_jungle_hunter", "npc_templar_knight",
              "npc_blood_priest", "npc_beast_tamer"]

for nid in delete_ids:
    marker = f'"{nid}": {{'
    i = src.find(marker)
    if i < 0:
        print(f'!! npc marker not found: {nid}')
        continue
    j = src.find('{', i)
    depth = 0
    k = j
    while k < len(src):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    e = k + 1
    while e < len(src) and src[e] in ' \t':
        e += 1
    if e < len(src) and src[e] == ',':
        e += 1
    if e < len(src) and src[e] == '\n':
        e += 1
    print(f'deleted npc {nid}: chars {i}..{e}')
    src = src[:i] + src[e:]

# 魔剑士残魂：任务已并入龙裔线 → 去 quest func 与 quest 字段（保留 lore）
old_block = """        'funcs': ["quest", "lore"],
        'lore': '这把剑的主人曾是教会的首席魔剑士，他发现了真相，然后名字就被抹去了。剑记得一切——拿起它，就是接住一个被掩埋的誓言。',
        'quest': "s_spellblade_trial",
        'dialogue': "尘封三百年的剑与书……终于有人集齐了信物。来吧，握住这把剑，让魔能重新流转。","""
new_block = """        # v112：魔剑士已并入龙裔线·龙咒流派，试炼任务并入龙骨之血 → 只留 lore
        'funcs': ["lore"],
        'lore': '这把剑的主人曾是教会的首席魔剑士，他发现了真相，然后名字就被抹去了。剑记得一切——拿起它，就是接住一个被掩埋的誓言。',
        'dialogue': "尘封三百年的剑与书……魔剑之名已并入龙裔誓约之路。握紧它，让魔能重新流转。","""
if old_block in src:
    src = src.replace(old_block, new_block)
    print('spellblade_ghost quest func removed')
else:
    print('!! spellblade_ghost block not matched')

io.open(path, 'w', encoding='utf-8').write(src)
print('written')
py_compile.compile(path, doraise=True)
print('py_compile OK')
