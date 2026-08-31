# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
craft = open(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\craft.py', encoding='utf-8').read()
m = re.findall(r"'roster_id'\s*:\s*'(eq_[a-z_0-9]+)'", craft)
print('roster_id 总数:', len(m))
names = ['血誓战剑','血誓战甲','余烬军团战剑','余烬军团战盔','余烬军团胸甲','余烬军团战靴','元素使徒法杖','元素使徒之冠','元素使徒长袍','元素使徒坠饰','时之领主秘仪','时之领主时戒','巡林长披风','巡林长弓','猎首长弓','猎首皮帽','猎首皮甲','猎首长靴','日冕权杖','日冕圣冠','日冕法衣','日冕圣靴','夜祷权杖','夜祷兜帽','夜祷法衣','夜祷之戒','影纱之刃','影纱面巾','影纱皮衣','影纱护腿','影纱轻靴','蓄势拳套','蓄势束带','破竹拳套','破竹武袍','破竹护腿','破竹布靴']
no_rid = []
for n in names:
    i = craft.find(n)
    seg = craft[max(0, i - 350):i + 120]
    if "'roster_id'" not in seg:
        no_rid.append(n)
print('41 件中无 roster_id 的（应=0，图纸链全通）:', no_rid or '无')
# 逐条 recipe 名称 + roster_id
pairs = []
for mm in re.finditer(r"'(rec_[a-z_0-9]+)'\s*:\s*\{", craft):
    seg = craft[mm.start():mm.start() + 600]
    ridm = re.search(r"'roster_id'\s*:\s*'(eq_[a-z_0-9]+)'", seg)
    pairs.append((mm.group(1), ridm.group(1) if ridm else 'NONE'))
print('recipe 总数:', len(pairs), '| 无 roster_id:', sum(1 for _, r in pairs if r == 'NONE'))
# 41 件名册 id 是否都被 recipe 指向
roster = open(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\equip_roster.py', encoding='utf-8').read()
rid_of = {}
for n in names:
    i = roster.find('"%s"' % n)
    line = roster[:i]
    ki = line.rfind('"eq_')
    eid = line[ki + 1:line.find('"', ki + 1)]
    rid_of[n] = eid
recipe_rids = set(r for _, r in pairs if r != 'NONE')
missing = [(n, e) for n, e in rid_of.items() if e not in recipe_rids]
print('41 件名册 id 未被图纸指向（应=4 誓约蓝装）:', missing)