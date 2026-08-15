# -*- coding: utf-8 -*-
"""临时工具：导出 MAIN_QUESTS 的 giver→任务映射（含 story 台词），供策划案子任务使用"""
import re
from collections import OrderedDict

src = open('game/data/quests.py', encoding='utf-8').read()
main = src.split('MAIN_QUESTS = [', 1)[1].split('SIDE_QUESTS', 1)[0]

quests = []
for b in re.finditer(r'\{\s*(.*?)\n\s*\},', main, re.S):
    t = b.group(1)
    d = dict(re.findall(r'"(\w+)":\s*"([^"]*)"', t))
    if d.get('id', '').startswith('q'):
        quests.append(d)

gmap = OrderedDict()
for q in quests:
    gmap.setdefault(q.get('giver', '?'), []).append(q)

out = []
out.append('任务数: %d' % len(quests))
for g, qs in gmap.items():
    out.append('')
    out.append('=== %s (%d) ===' % (g, len(qs)))
    for q in qs:
        out.append('  %s %s' % (q['id'], q['name']))
        if q.get('story'):
            out.append('    story: %s' % q['story'])
        if q.get('desc'):
            out.append('    desc: %s' % q['desc'])
        if q.get('reward_item'):
            out.append('    reward_item: %s' % q['reward_item'])

with open('scripts/_giver_map.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('written', len(out), 'lines')
