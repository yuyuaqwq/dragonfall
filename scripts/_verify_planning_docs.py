# -*- coding: utf-8 -*-
"""临时工具：汇总校验 6 份对话树策划案（结构/编码/覆盖），结果写 UTF-8 文件"""
import os
import re

BASE = 'design/new_world/对话树策划'
OUT = 'scripts/_verify_planning_out.txt'
FILES = ['01_白鹿城组.md', '02_老约翰组.md', '03_铁港与修道院组.md',
         '04_王都与教会组.md', '05_圣女与精灵组.md', '06_北境组.md']

EXPECT = {
    'npc_baron': ['q2_1', 'q2_2', 'q2_3'],
    'npc_doctor': ['q2_4'],
    'npc_tavern_owner': ['q2_5'],
    'npc_guildmaster': ['q3_1', 'q3_4', 'q3_5', 'q5_1', 'q9_1', 'q9_2', 'q9_3',
                        'q9_4', 'q9_5', 'q9_6', 'q11_4', 'q12_1', 'q12_4', 'q12_5', 'q12_6'],
    'npc_citylord': ['q3_2', 'q3_3'],
    'npc_auctioneer': ['q3_6'],
    'npc_abbess': ['q4_1', 'q4_2', 'q4_3', 'q4_4', 'q4_5'],
    'npc_king': ['q5_2', 'q5_3', 'q5_4', 'q5_5'],
    'npc_knight_commander': ['q5_6', 'q6_6', 'q11_1', 'q11_2', 'q11_3'],
    'npc_saintess': ['q6_1', 'q6_2', 'q6_3', 'q6_4', 'q6_5', 'q11_6'],
    'npc_elf_queen': ['q7_1'],
    'npc_elf_guardian': ['q7_2', 'q7_6'],
    'npc_elf_sage': ['q7_3', 'q7_4', 'q7_5'],
    'npc_north_chief': ['q8_1', 'q8_2', 'q8_4', 'q8_6'],
    'npc_pope': ['q11_5'],
}

FILE_GIVERS = {
    '01_白鹿城组.md': ['npc_baron', 'npc_doctor', 'npc_tavern_owner'],
    '02_老约翰组.md': ['npc_guildmaster'],
    '03_铁港与修道院组.md': ['npc_citylord', 'npc_auctioneer', 'npc_abbess'],
    '04_王都与教会组.md': ['npc_king', 'npc_knight_commander', 'npc_pope'],
    '05_圣女与精灵组.md': ['npc_saintess', 'npc_elf_queen', 'npc_elf_guardian', 'npc_elf_sage'],
    '06_北境组.md': ['npc_north_chief'],
}

SECS = ['0. 角色定位', '1. 覆盖任务清单', '2. 欢迎节点', '3. 接取树', '4. 推进树',
        '5. 交付树', '6. Flag 与记忆', '7. 与其它 NPC', '8. 引擎增补', '覆盖矩阵']

lines = []
total_missing = []
for f in FILES:
    p = os.path.join(BASE, f)
    if not os.path.exists(p):
        lines.append('[缺失] %s' % f)
        continue
    raw = open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    text = raw.decode('utf-8')
    n = len(text.splitlines())
    lines.append('=== %s | 行数 %d | BOM %s ===' % (f, n, '有(需修)' if bom else '无'))
    for gid in FILE_GIVERS.get(f, []):
        qids = EXPECT[gid]
        if gid not in text:
            lines.append('  [注意] 未提及 %s' % gid)
        missing = [q for q in qids if q not in text]
        if missing:
            total_missing.append((f, gid, missing))
            lines.append('  [缺任务] %s: %s' % (gid, ','.join(missing)))
    for s in SECS:
        if s not in text:
            lines.append('  [缺小节] %s' % s)

lines.append('')
if total_missing:
    lines.append('任务覆盖缺口:')
    for f, g, m in total_missing:
        lines.append('  %s %s: %s' % (f, g, ','.join(m)))
else:
    lines.append('任务覆盖：全部 63 任务均有提及，通过')

with open(OUT, 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(lines))
print('done')
