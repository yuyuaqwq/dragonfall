# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sets_src = open(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\sets.py', encoding='utf-8').read()
aff_src = open(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\affixes.py', encoding='utf-8').read()
core_src = open(r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\core_resources.py', encoding='utf-8').read()

seg = sets_src[sets_src.find('# ================= v130.2c 资源联动套装'):sets_src.find('CLASS_SET_STAGES')]
ver_pat = re.compile(r'v\d+\.\d+[a-z]?|v13\d|B\d|R\d')
bad = []
for m in re.finditer(r'^    "(set_[a-z_]+)":\s*\{', seg, re.M):
    sk = m.group(1)
    i = m.start()
    depth = 0; j = seg.find('{', i)
    while j < len(seg):
        if seg[j] == '{': depth += 1
        elif seg[j] == '}':
            depth -= 1
            if depth == 0: break
        j += 1
    blk = seg[i:j + 1]
    for fm in re.finditer(r'"(name|desc)"\s*:\s*"([^"]+)"', blk):
        if ver_pat.search(fm.group(2)):
            bad.append('%s.%s=%s' % (sk, fm.group(1), fm.group(2)))
v130seg = aff_src[aff_src.find('v130.2 装备-资源联动词条'):aff_src.find('AFFIX_POOL_BY_QUALITY =')]
for m in re.finditer(r'^    "([a-z_]+)":\s*\{', v130seg, re.M):
    aid = m.group(1)
    i = m.start()
    depth = 0; j = v130seg.find('{', i)
    while j < len(v130seg):
        if v130seg[j] == '{': depth += 1
        elif v130seg[j] == '}':
            depth -= 1
            if depth == 0: break
        j += 1
    blk = v130seg[i:j + 1]
    for fm in re.finditer(r'"(name|desc)"\s*:\s*"([^"]+)"', blk):
        if ver_pat.search(fm.group(2)):
            bad.append('affix.%s.%s=%s' % (aid, fm.group(1), fm.group(2)))
print('版本记号命中:', bad or '无（12 套 + 31 词条 name/desc 全干净）')
# 12 资源 desc 数值抽查
for ln in core_src.split('\n'):
    if '"desc"' in ln and ('18%' in ln or '+40%' in ln or '+4%' in ln or '10%' in ln or '18' in ln):
        print('RES-DESC:', ln.strip())