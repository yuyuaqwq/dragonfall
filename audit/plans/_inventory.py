# -*- coding: utf-8 -*-
"""盘点 audit/plans/*_fixplan.json 的 confirmed/doc_only 条目（只读辅助，可随时删除）。"""
import json, glob, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
rows = []
for f in sorted(glob.glob('audit/plans/*_fixplan.json')):
    j = json.load(open(f, encoding='utf-8'))
    for x in j.get('findings', []):
        rows.append((j['domain'], x['id'], x['sev'], x['verdict'], x['title'], '|'.join(x.get('files', []))))
print('TOTAL actionable:', len(rows))
print('== confirmed ==')
for r in rows:
    if r[3] == 'confirmed':
        print('[%s] %s (%s) %s :: %s' % (r[0], r[1], r[2], r[4], r[5]))
print('== doc_only ==')
for r in rows:
    if r[3] == 'doc_only':
        print('[%s] %s (%s) %s :: %s' % (r[0], r[1], r[2], r[4], r[5]))
