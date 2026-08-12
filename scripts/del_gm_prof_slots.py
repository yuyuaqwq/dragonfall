# -*- coding: utf-8 -*-
import io
p = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\commands\_registry.py"
t = io.open(p, 'r', encoding='utf-8').read()
lines = t.split('\n')
out = [l for l in lines if 'gm_prof_slots' not in l]
assert len(out) == len(lines) - 1, 'gm_prof_slots 条目未删干净'
io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print('_registry.py: gm_prof_slots 已删')
