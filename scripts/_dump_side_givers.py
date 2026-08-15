# -*- coding: utf-8 -*-
"""临时工具：查 15 位主线 giver 名下是否有支线（决定对话树要不要 side_offer/side_take 选项）"""
import re

src = open('game/data/quests.py', encoding='utf-8').read()
side = src.split('SIDE_QUESTS = [', 1)[1].split('DAILY_QUESTS', 1)[0]

g = {}
for b in re.finditer(r'"id":\s*"([^"]+)".*?"giver":\s*"([^"]+)"', side, re.S):
    g.setdefault(b.group(2), []).append(b.group(1))

targets = ['npc_baron', 'npc_doctor', 'npc_tavern_owner', 'npc_guildmaster', 'npc_citylord',
           'npc_auctioneer', 'npc_abbess', 'npc_king', 'npc_knight_commander', 'npc_saintess',
           'npc_elf_queen', 'npc_elf_guardian', 'npc_elf_sage', 'npc_north_chief', 'npc_pope']
with open('scripts/_side_lookup.txt', 'w', encoding='utf-8') as f:
    for t in targets:
        f.write('%s -> %s\n' % (t, ','.join(g.get(t, [])) or '无'))
print('done')
