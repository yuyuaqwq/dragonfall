# -*- coding: utf-8 -*-
"""临时工具：查 15 位主线 giver 的显示名/性别"""
import re

src = open('game/data/npcs.py', encoding='utf-8').read()
ids = ['npc_baron', 'npc_doctor', 'npc_tavern_owner', 'npc_guildmaster', 'npc_citylord',
       'npc_auctioneer', 'npc_abbess', 'npc_king', 'npc_knight_commander', 'npc_saintess',
       'npc_elf_queen', 'npc_elf_guardian', 'npc_elf_sage', 'npc_north_chief', 'npc_pope']
for i in ids:
    m = re.search(r'"%s":\s*\{([^}]*)\}' % i, src, re.S)
    if not m:
        print('%s | NO BLOCK' % i)
        continue
    body = m.group(1)
    name = re.search(r'"name":\s*"([^"]+)"', body)
    gender = re.search(r'"gender":\s*"([^"]+)"', body)
    print('%s | %s | %s' % (i, name.group(1) if name else '?', gender.group(1) if gender else '?'))
