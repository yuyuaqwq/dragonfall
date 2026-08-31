# -*- coding: utf-8 -*-
"""T11 补充验证：套装段/词条段/掉落-商店链路"""
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = r'C:\Users\yuyu\qqbot\data\plugins\dragonfall\game'
def rd(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()

sets_src = rd('data/sets.py')
aff_src = rd('data/affixes.py')
battle_src = rd('battle.py')
roster_src = rd('data/equip_roster.py')
craft_src = rd('data/craft.py')
shop_src = rd('data/shop.py')
drops_src = rd('core/drops.py')
items_src = rd('data/items.py')

# ---- 12 套装（从完整行开始的 v130.2c 段）----
seg = sets_src[sets_src.find('# ================= v130.2c 资源联动套装'):sets_src.find('CLASS_SET_STAGES')]
set_keys = re.findall(r'^    "(set_[a-z_]+)":\s*\{', seg, re.M)
print('12 套装 key:', len(set_keys))
for sk in set_keys:
    print('  ', sk)
m = re.search(r'SET_EFFECT_CONSUMED = \((.*?)\)\n', battle_src, re.S)
consumed = re.findall(r'"([^"]+)"', m.group(1))

def brace_block(src, i):
    j = src.find('{', i)
    depth = 0
    while j < len(src):
        if src[j] == '{': depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0: break
        j += 1
    return src[i:j + 1]

missing_effect = []
for sk in set_keys:
    i = seg.find('"%s"' % sk)
    blk = brace_block(seg, i)
    for tier in ('bonus_2', 'bonus_4', 'bonus_5'):
        tm = re.search(r'"%s"\s*:\s*{' % tier, blk)
        if tm:
            tb = brace_block(blk, tm.start())
            effm = re.search(r'"effect"\s*:\s*"([^"]+)"', tb)
            if effm and effm.group(1) not in consumed:
                missing_effect.append((sk, tier, effm.group(1)))
print('套装 effect 无消费:', missing_effect or '无（全部在 SET_EFFECT_CONSUMED）')

# ---- 31 词条 ----
v130_start = aff_src.find('v130.2 装备-资源联动词条')
v130_end = aff_src.find('AFFIX_POOL_BY_QUALITY =')
v130seg = aff_src[v130_start:v130_end]
aff_keys = re.findall(r'^    "([a-z_]+)":\s*\{', v130seg, re.M)
print('31 词条 key:', len(aff_keys), aff_keys)

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
for mm in re.finditer(r'"energy_tide"\s+in', ae_src):
    direct.setdefault('energy_tide', []).append('affx:' + str(ae_src.count('\n', 0, mm.start()) + 1))
if 'boiling_blood' in ae_src:
    direct['boiling_blood'] = ['affx:205']

uncovered = []
for k in aff_keys:
    where = [g for g in reg if k in reg[g]]
    if k in direct:
        where.append('direct@%s' % ','.join(str(x) for x in direct[k][:3]))
    if not where:
        uncovered.append(k)
print('词条未覆盖:', uncovered or '无（31 全有消费点）')

# ---- 41 件：掉落（eq id）/ 商店 ----
fixed_start = aff_src.find('# ================= v130.2c 资源联动套装固定词条')
fixed_seg = aff_src[fixed_start:aff_src.find('# ================= v130.2d', fixed_start)]
item_names = re.findall(r'"([^"\']+)":\s*\[', fixed_seg)
item_names = [n for n in item_names if '=' not in n and 'v13' not in n]
# 名册里每一项的 id
id_of = {}
for n in item_names:
    i = roster_src.find('"%s"' % n)
    line = roster_src[:i]
    ki = line.rfind('"eq_')
    eid = line[ki:line.find('"', ki + 1)]
    id_of[n] = eid
print('== 掉落/商店链路（41 件）==')
no_drop = []
for n in item_names:
    eid = id_of[n]
    in_drop = (eid in drops_src) or (n in drops_src)
    in_shop = (n in shop_src) or (eid in shop_src)
    in_craft = n in craft_src
    src_line = [l for l in roster_src.split('\n') if ('"%s"' % n) in l]
    src = re.search(r'"source"\s*:\s*"([^"]+)"', src_line[0]).group(1) if src_line else '?'
    ok = (src == '商店' and in_shop) or (src == '图纸' and in_craft) or in_drop
    if not ok:
        no_drop.append((n, eid, src, in_craft, in_shop, in_drop))
    print('  %-8s %-24s src=%-4s craft=%s shop=%s drop=%s' % (eid[:18], n, src, in_craft, in_shop, in_drop))
print('链路缺失:', no_drop or '无')
# drops.py 到底怎么引用
print('drops.py 中 eq 引用示例:', re.findall(r'"(eq_[a-z_0-9]+)"', drops_src)[:10])
# shop.py 引用示例
print('shop.py 引用示例:', re.findall(r'"[^" ]*誓约[^" ]*"', shop_src)[:10])