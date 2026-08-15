# -*- coding: utf-8 -*-
"""B14 收尾：docstring 游戏名《剑与魔法》→ 奥兰迪亚·余烬纪年（仅替换带书名号形式，剧情文案"以剑与魔法同魔龙一战"无书名号不受影响）。"""
import glob, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OLD = '《剑与魔法》'
NEW = '奥兰迪亚·余烬纪年'
targets = sorted(glob.glob('game/**/*.py', recursive=True)) + ['main.py']
changed = []
for f in targets:
    raw = open(f, encoding='utf-8').read()
    if OLD in raw:
        n = raw.count(OLD)
        open(f, 'w', encoding='utf-8', newline='').write(raw.replace(OLD, NEW))
        changed.append((f, n))
print('changed files:', len(changed))
for f, n in changed:
    print(' %3d  %s' % (n, f))
