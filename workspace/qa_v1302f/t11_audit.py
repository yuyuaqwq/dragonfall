# -*- coding: utf-8 -*-
"""T11 只读审计脚本 v2（修：brace 匹配 / 同行多条目 / 段边界）"""
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game'

def rd(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()

sets_src = rd('data/sets.py')
aff_src = rd('data/affixes.py')
battle_src = rd('battle.py')
cfg_src = rd('data/battle_config.py')
core_src = rd('data/core_resources.py')
skills_src = rd('data/skills.py')
roster_src = rd('data/equip_roster.py')
craft_src = rd('data/craft.py')
shop_src = rd('data/shop.py')
drops_src = rd('core/drops.py')
items_src = rd('data/items.py')

def brace_block(src, i):
    """从 i（指向'{'）做括号匹配取完整 dict 文本"""
    j = src.find('{', i)
    depth = 0
    while j < len(src):
        if src[j] == '{': depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0: break
        j += 1
    return src[i:j + 1]

# ---------- A. 12 套装 ----------
seg = sets_src[sets_src.find('"set_xue_shi_zhan_tuan"'):sets_src.find('CLASS_SET_STAGES')]
set_keys = re.findall(r'"((?:set|resonance|echo)[a-z_]*)"\s*:', seg)
set_keys = [k for k in set_keys if k.startswith('set_') and not k.startswith('set_han')]
# 精确：12 个 key 出现在 SETS dict 内（排除注释/CLASS_SET_THEMES）
set_keys = []
for m in re.finditer(r'^    "(set_[a-z_]+)":\s*\{', seg, re.M):
    set_keys.append(m.group(1))
print('== 12 套装 key ==', len(set_keys), set_keys)

m = re.search(r'SET_EFFECT_CONSUMED = \((.*?)\)\n', battle_src, re.S)
consumed = re.findall(r'"([^"]+)"', m.group(1))

print('== 套装效果使用（含 bonus_4/5）==')
set_info = {}
for sk in set_keys:
    i = seg.find('"%s"' % sk)
    blk = brace_block(seg, i)
    set_info[sk] = blk
    for tier in ('bonus_2', 'bonus_4', 'bonus_5'):
        tm = re.search(r'"%s"\s*:\s*{' % tier, blk)
        if tm:
            tb = brace_block(blk, tm.start())
            effm = re.search(r'"effect"\s*:\s*"([^"]+)"', tb)
            if effm:
                ok = 'OK' if effm.group(1) in consumed else '!! NOT CONSUMED'
                print('  %s %s effect=%s %s' % (sk, tier, effm.group(1), ok))

print('== 消费点行号 ==')
for eff in consumed:
    ln = []
    for mm in re.finditer(r'_set_eff\(\s*[^,]+,\s*"%s"' % re.escape(eff), battle_src):
        ln.append(battle_src.count('\n', 0, mm.start()) + 1)
    if eff in ('res_gain', 'res_max'):
        for mm in re.finditer(r'_set_res_proc\(\s*[^,]+,\s*"(%s)' % re.escape(eff), battle_src):
            ln.append(battle_src.count('\n', 0, mm.start()) + 1)
        for mm in re.finditer(r'_set_res_max_bonus\(', battle_src):
            ln.append(battle_src.count('\n', 0, mm.start()) + 1)
    print('  %s: %s' % (eff, ln))

# ---------- B. 31 词条 ----------
v130_start = aff_src.find('# v130.2 装备-资源联动词条')
v130_end = aff_src.find('AFFIX_POOL_BY_QUALITY =')
v130seg = aff_src[v130_start:v130_end]
aff_keys = re.findall(r'^    "([a-z_]+)":\s*\{', v130seg, re.M)
print('== 31 词条 key ==', len(aff_keys), aff_keys)

reg = {}
for name in ('RES_AFFIX_GAIN', 'RES_AFFIX_MAX', 'RES_AFFIX_TURN_START', 'RES_AFFIX_ON_TAKEN'):
    mm = re.search(r'%s = \((.*?)\)' % name, battle_src, re.S)
    reg[name] = re.findall(r'"([^"]+)"', mm.group(1))
direct = {}
for pat in (r'_affix_effs\(player,\s*"([a-z_]+)"', r'_affix_effs\(pl,\s*"([a-z_]+)"',
            r'_affix_eff_tiered\(player,\s*"([a-z_]+)"'):
    for mm in re.finditer(pat, battle_src):
        direct.setdefault(mm.group(1), []).append(battle_src.count('\n', 0, mm.start()) + 1)
ae_src = rd('core/affix_effects.py')
for mm in re.finditer(r'"([a-z_]+)"\s+in battle\._equip_affix_ids', ae_src):
    direct.setdefault(mm.group(1), []).append('affx:' + str(ae_src.count('\n', 0, mm.start()) + 1))
for mm in re.finditer(r'boiling_blood', battle_src + ae_src):
    direct.setdefault('boiling_blood', []).append('taken-reduce')
for mm in re.finditer(r'"energy_tide"\s+in', ae_src):
    direct.setdefault('energy_tide', []).append('affx:' + str(ae_src.count('\n', 0, mm.start()) + 1))

print('== 词条消费覆盖 ==')
uncovered = []
for k in aff_keys:
    where = [g for g in reg if k in reg[g]]
    if k in direct:
        where.append('direct@%s' % ','.join(str(x) for x in direct[k][:4]))
    if not where:
        uncovered.append(k)
    print('  %s: %s' % (k, 'OK ' + '; '.join(where) if where else '!! NO CONSUMER'))
print('  未覆盖:', uncovered or '无')

# ---------- C. 41 件 ----------
fixed_start = aff_src.find('# ================= v130.2c 资源联动套装固定词条')
fixed_seg = aff_src[fixed_start:aff_src.find('# ================= v130.2d', fixed_start)]
item_names = re.findall(r'"([^"\']+)":\s*\[', fixed_seg)
item_names = [n for n in item_names if 'v130' not in n and '=' not in n]
print('== 固定词条 41 件 ==', len(item_names))
for n in item_names:
    print('  ', n)
miss = [n for n in item_names if '"name": "%s"' % n not in roster_src]
print('  roster 缺失:', miss if miss else '无（41 件全在）')

sets_pieces = {}
for n in item_names:
    i = roster_src.find('"%s"' % n)
    assert i >= 0, n
    line = roster_src[i:roster_src.find('\n', i)]
    sm = re.search(r'"set"\s*:\s*"([^"]+)"', line)
    sets_pieces.setdefault(sm.group(1) if sm else 'NO_SET', []).append(n)
    qm = re.search(r'"quality"\s*:\s*"([^"]+)"', line)
print('== 每套装件数 / 品质 ==')
for s, items in sets_pieces.items():
    print('  set=%s: %d 件 %s' % (s, len(items), items))
print('  NO_SET:', sets_pieces.get('NO_SET', []) or '无')

set_display = {}
for sk in set_keys:
    nm = re.search(r'"name"\s*:\s*"([^"]+)"', set_info[sk])
    if nm:
        set_display[nm.group(1)] = sk
for s in set_display:
    n = len(sets_pieces.get(s, []))
    print('  %s: %d 件 %s' % (s, n, 'OK' if n >= 2 else '!! 2件效果不可达'))
odd = [s for s in sets_pieces if s != 'NO_SET' and s not in set_display]
print('  名册 set 名未匹配套装定义:', odd or '无')

# 品质一致性（固定词条所在品质档）
qual_check = {
    '日冕权杖': 'purple', '誓约权杖': 'blue', '元素使徒法杖': 'orange', '元素使徒之冠': 'orange',
    '元素使徒长袍': 'orange', '元素使徒坠饰': 'orange', '时之领主秘仪': 'orange', '时之领主时戒': 'orange',
}
for n, exp in qual_check.items():
    i = roster_src.find('"%s"' % n)
    line = roster_src[i:roster_src.find('\n', i)]
    qm = re.search(r'"quality"\s*:\s*"([^"]+)"', line)
    got = qm.group(1) if qm else '?'
    flag = 'OK' if got == exp else '!! EXPECT ' + exp
    print('  品质 %s = %s %s' % (n, got, flag))

print('  craft.py 图纸覆盖:', sum(1 for n in item_names if n in craft_src), '/', len(item_names))
print('  drops.py 掉落覆盖:', sum(1 for n in item_names if n in drops_src), '/', len(item_names))
print('  shop.py 商店覆盖:', sum(1 for n in item_names if n in shop_src), '/', len(item_names))
print('  items.py 覆盖:', sum(1 for n in item_names if n in items_src), '/', len(item_names))

# ---------- D. SHADOW_STEALTH_DMG_MULT ----------
sm = re.search(r'SHADOW_STEALTH_DMG_MULT = \{(.*?)\}', cfg_src, re.S)
pairs = re.findall(r'"([^"]+)"\s*:\s*([\d.]+)', sm.group(1))
print('== SHADOW_STEALTH_DMG_MULT ==')
for k, v in pairs:
    i = skills_src.find('"%s"' % k)
    print('  %s x%s: skills.py %s' % (k, v, '存在' if i >= 0 else '!! 不存在'))
    if i >= 0:
        blk = brace_block(skills_src, i)
        dm = re.search(r'"desc"\s*:\s*"([^"]*)"', blk)
        print('     desc:', dm.group(1)[:70] if dm else '?')

# ---------- E. ZEN_HOLD_CFG ----------
print('== ZEN_HOLD_CFG ==', re.search(r'ZEN_HOLD_CFG = \{[^}]*\}', cfg_src).group(0))
m1 = re.search(r'def _zen_hold_mult', battle_src)
print('  battle._zen_hold_mult @', battle_src.count('\n', 0, m1.start()) + 1)
for mm in re.finditer(r'_zen_hold_mult\(', battle_src):
    print('   consumer @', battle_src.count('\n', 0, mm.start()) + 1)

# ---------- F. overflow_shield ----------
print('== overflow_shield ==')
for ln in core_src.split('\n'):
    if 'overflow_shield' in ln:
        print('  core:', ln.strip())
m = re.search(r'if rd\.get\("overflow_shield"\)', battle_src)
print('  引擎 @', battle_src.count('\n', 0, m.start()) + 1 if m else '!! 引擎无消费')

# ---------- G. 版本记号 ----------
print('== desc/name 版本记号检查 ==')
ver_pat = re.compile(r'v\d+\.\d+[a-z]?|v13\d|B\d|R\d')
bad = 0
for sk in set_keys:
    for fm in re.finditer(r'"(name|desc)"\s*:\s*"([^"]+)"', set_info[sk]):
        if ver_pat.search(fm.group(2)):
            bad += 1
            print('  !! %s %s: %s' % (sk, fm.group(1), fm.group(2)))
for aid in aff_keys:
    for fm in re.finditer(r'"desc"\s*:\s*"([^"]+)"', v130seg[v130seg.find('"%s"' % aid):][:500]):
        if ver_pat.search(fm.group(1)):
            bad += 1
            print('  !! affix %s desc: %s' % (aid, fm.group(1)))
        break
print('  版本记号命中:', bad, '（0=干净）')

# ---------- H. 资源 desc 数值抽查 ----------
print('== 资源 desc 数值一致性（18% vs 10%）==')
for ln in core_src.split('\n'):
    if '"desc"' in ln and ('18%' in ln or '每层' in ln):
        print('  RES-DESC:', ln.strip())