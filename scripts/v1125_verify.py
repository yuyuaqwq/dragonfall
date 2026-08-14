# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\yuyu\qqbot')
from data.plugins.dragonfall.game import content as C

print('=== CLASSES ===')
print('总数:', len(C.CLASSES), '| 隐藏:', sum(1 for c in C.CLASSES.values() if c.get('hidden')))
fs = C.CLASSES['cls_fa_shi']['evolve_branches']
print('cls_fa_shi:', fs)
ch = C.CLASSES['cls_chronomancer']
print('cls_chronomancer:', ch['name'], ch['evolve_branches'], '| 血缘:', ch['src_base'])

print('=== 技能 ===')
print('PLAYER_SKILLS:', len(C.PLAYER_SKILLS), '| BRANCH_SKILLS:', len(C.BRANCH_SKILLS), '| 资源:', len(C.CORE_RESOURCES))
fsb = C.BRANCH_SKILLS['cls_fa_shi']['branches']
for t in (1, 2, 3):
    print('  fa_shi t%d:' % t, {bn: [s['name'] for s in sk.values()] for bn, sk in fsb[t].items()})
chb = C.BRANCH_SKILLS['cls_chronomancer']['branches']
for t in (1, 2, 3):
    print('  chrono t%d:' % t, {bn: [s['name'] for s in sk.values()] for bn, sk in chb[t].items()})
print('chrono 线级:', [s['name'] for s in C.PLAYER_SKILLS['cls_chronomancer']['skills'].values()])

total = sum(len(sk) for c in C.BRANCH_SKILLS.values() for t in c['branches'].values() for bn, sk in t.items())
print('分支总技能数:', total)

flat = {}
for _c, _t in C.PLAYER_SKILLS.items():
    flat.update(_t['skills'] if isinstance(_t, dict) and 'skills' in _t else _t)
for _c, _t in (C.TUTOR_SKILLS or {}).items():
    if isinstance(_t, dict):
        flat.update(_t)
name2id, dups = {}, []
for k, v in flat.items():
    nm = v.get('name', k)
    if nm in name2id and name2id[nm] != k:
        dups.append(nm)
    name2id[nm] = k
print('技能名重复:', dups)

names = []
for cls_id, cls in C.CLASSES.items():
    names.append(cls['name'])
    for t, brs in (cls.get('evolve_branches') or {}).items():
        names.extend(brs)
dup_names = [n for n in set(names) if names.count(n) > 1]
print('职业名+档位名重复:', dup_names)

from data.plugins.dragonfall.main import Main
m = Main(None)
routes = m._hidden_class_routes()
print('隐藏档位路由数:', len(routes))
# v113 收敛：时咒线只留时停单流派（虚空/血咒已删）
for n in ('时停', '时律术士', '时间领主'):
    print('  路由', n, '->', routes.get(n))
aliases = m._hidden_alias_map()
print('别名 时咒/时停/时溯:', aliases.get('时咒'), aliases.get('时停'), aliases.get('时溯'))
