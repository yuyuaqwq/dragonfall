# -*- coding: utf-8 -*-
"""v153 职业机制设计文档：数值与结构自动校验 + 派生列回填

用法:
    python audit_v153.py             # 只校验，输出报告
    python audit_v153.py --write     # 校验 + 把 总eq/cyc/eps 三列回填进文档

验收标准：A~N 全段 0 告警（S2 清单为空）
"""
import re, sys, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOC = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/docs/CLASS_MECHANICS_v153.md"
WRITE = '--write' in sys.argv
raw = open(DOC, encoding='utf-8').read()
lines = raw.split('\n')

# ============ 引擎标定常数（读 battle.py）============
BASE_DELAY = 40.0
SPD_CT_CAP = 80.0
BASE_SPD = 50.0                       # 基准速度
BASE_COST = BASE_DELAY / min(BASE_SPD, SPD_CT_CAP)   # = 0.8s

CAP_EPS = {'BASE': 0.85, 'T1': 1.00, 'T2': 1.15, 'T3': 1.30}          # 裸 eps
CAP_EPS_COND = {'BASE': 1.05, 'T1': 1.30, 'T2': 1.50, 'T3': 1.75}     # 条件后 eps
CAP_EQ_LOOK = {'BASE': 2.0, 'T1': 2.6, 'T2': 3.6, 'T3': 4.6}          # 观感帽
EXPECT = {'BASE': 8, 'T1': 6, 'T2': 6, 'T3': 5}
MULTI_CAP_RATIO = 1.10
AOE_EPS_RATIO = 0.80
CLAIM_CAST = {                         # §0.3 声称的 cast 主区间
    '一、战士': (0.9, 2.0), '二、法师': (1.0, 2.6), '三、游侠': (0.6, 1.3),
    '四、牧师': (0.9, 1.8), '五、刺客': (0.5, 1.0), '六、拳师': (0.7, 1.5),
}
UNIQUE_PER_CLASS = 42

ALERTS = defaultdict(list)


def alert(sec, line, name, msg):
    ALERTS[sec].append((line, name, msg))


# ============ 表格解析 ============
def parse_tables(lines):
    tables, i = [], 0
    while i < len(lines):
        l = lines[i].strip()
        if l.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-\|]+\|$', lines[i + 1].strip()):
            header = [c.strip() for c in l.strip('|').split('|')]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith('|'):
                rows.append((j + 1, [c.strip() for c in lines[j].strip().strip('|').split('|')]))
                j += 1
            tables.append((i + 1, header, rows))
            i = j
        else:
            i += 1
    return tables


tables = parse_tables(lines)

secs = []
for n, l in enumerate(lines, 1):
    m = re.match(r'^(#{2,4})\s+(.*)', l)
    if m:
        secs.append((n, len(m.group(1)), m.group(2).strip()))


def ctx(lineno):
    ch = sub = ''
    for n, lvl, t in secs:
        if n <= lineno:
            if lvl == 2:
                ch, sub = t, ''
            elif lvl >= 3:
                sub = t
    return ch, sub


def tier_of(lineno):
    for n in range(lineno, 0, -1):
        s = lines[n - 1].strip()
        m = re.match(r'^#{0,4}\s*\*\*(T[123])（', s) or re.match(r'^\*\*(T[123])（', s)
        if m:
            return m.group(1)
        if re.match(r'^#{0,4}\s*(基础技能)', s):
            return 'BASE'
        if s.startswith('## ') or s.startswith('### '):
            if n < lineno:
                break
    return '?'


def class_of(ch):
    return ch.split(' —')[0]


# ============ 技能解析 ============
skills = []
derived = {}          # line -> (总eq, cyc, eps) 待回填
for start, header, rows in tables:
    hn = [h.replace(' ', '') for h in header]
    if 'base' not in hn or 'cast' not in hn:
        continue
    c = lambda k: hn.index(k) if k in hn else None
    ib, ih, ica = c('base'), c('hits'), c('cast')
    ilv, icd, imp = c('lv'), c('cd'), c('mp')
    imech = len(hn) - 1
    for (ln, cells) in rows:
        if len(cells) < len(hn):
            continue
        name = cells[0]
        if name in ('技能', '名称') or set(name) <= set('-: '):
            continue
        ch, sub = ctx(ln)
        r = dict(line=ln, name=name, ch=ch, sub=sub, tier=tier_of(ln),
                 lv=int(cells[ilv]) if ilv is not None and cells[ilv].isdigit() else None,
                 base_s=cells[ib],
                 hits=int(cells[ih]) if ih is not None and cells[ih].isdigit() else 1,
                 cast=float(cells[ica]) if ica is not None and re.match(r'^[0-9.]+$', cells[ica]) else None,
                 mech=cells[imech], kind=cells[c('kind')] if c('kind') else '',
                 cd=cells[icd] if icd is not None else '',
                 mp=cells[imp] if imp is not None else '')
        r['truedmg'] = '真伤' in r['kind']
        r['is_passive'] = '被动' in r['kind']
        r['aoe'] = '[AOE]' in r['mech']
        r['has_dmg'] = r['base_s'] not in ('—', '-', '')
        # 派生列
        if r['has_dmg'] and r['cast'] is not None:
            base = float(r['base_s'])
            eq = round(base * 1.4 * r['hits'] * (0.8 if r['truedmg'] else 1), 2)
            cyc = round(BASE_COST + r['cast'], 2)
            r.update(eq=eq, cyc=cyc, eps=round(eq / cyc, 3))
        else:
            r.update(eq=None, cyc=(round(BASE_COST + r['cast'], 2) if r['cast'] is not None else None), eps=None)
        skills.append(r)
        if r['cast'] is not None:
            eq_s = f'{r["eq"]}' if r['eq'] is not None else '—'
            eps_s = f'{r["eps"]}' if r['eps'] is not None else '—'
            derived[ln] = (eq_s, f'{r["cyc"]}', eps_s)
        else:
            derived[ln] = ('—', '—', '—')   # 被动/无 cast：三列都空

# ============ A. eps 天花板 / 观感帽 / 条件倍率（脚本重算）============
for r in skills:
    if not r['has_dmg'] or r['eps'] is None:
        continue
    tier = r['tier']
    cap_eps = CAP_EPS.get(tier, 9)
    cap_cond = CAP_EPS_COND.get(tier, 9)
    cap_look = CAP_EQ_LOOK.get(tier, 9)
    if r['aoe']:
        cap_eps *= AOE_EPS_RATIO
    if r['eps'] > cap_eps + 0.005:
        alert('A', r['line'], r['name'],
              f"[裸eps超限] {r['tier']} eps {r['eps']} > {round(cap_eps, 3)}"
              f"{'（AOE 档）' if r['aoe'] else ''}  base={r['base_s']} cast={r['cast']}")
    if r['eq'] > cap_look + 0.005:
        alert('A', r['line'], r['name'], f"[观感帽] 单发总eq {r['eq']} > {cap_look}")

    # 条件倍率：脚本自己乘
    mults = []
    for m in re.finditer(r'×\s*(1\.[0-9]+)', r['mech']):
        mults.append(float(m.group(1)))
    for m in re.finditer(r'×\(1\s*\+\s*([0-9.]+)\s*×\s*([^)]+?)\)', r['mech']):
        coef, var = float(m.group(1)), m.group(2)
        n = {'连段': 5, '核数': 5, '磐核数': 5, '层数': 9, '段': 5}.get(var.strip())
        if n:
            mults.append(round(1 + coef * n, 3))
    for m in re.finditer(r'每层\s*\+([0-9.]+)%', r['mech']):
        n = 9 if '印记' in r['mech'] else (8 if '毒' in r['mech'] else 5)
        mults.append(round(1 + float(m.group(1)) / 100 * n, 3))
    for m in re.finditer(r'每系\s*×\s*([0-9.]+)', r['mech']):
        mults.append(round(float(m.group(1)) ** 3, 3))
    for m in re.finditer(r'\(\s*1\s*\+\s*目标破绽\s*/\s*(\d+)\s*×\s*([0-9.]+)\)', r['mech']):
        mults.append(round(1 + 50 / float(m.group(1)) * float(m.group(2)), 3))
    for m in re.finditer(r'最高\s*×\s*([0-9.]+)', r['mech']):
        mults.append(float(m.group(1)))
    for m in re.finditer(r'\(最高 ×([0-9.]+)', r['mech']):
        mults.append(float(m.group(1)))
    for mu in mults:
        if mu <= 1.0:
            continue
        v = round(r['eps'] * mu, 3)
        if v > cap_cond + 0.005:
            alert('A', r['line'], r['name'],
                  f"[条件eps超限] eps {r['eps']} ×{mu} = {v} > {r['tier']} 条件上限 {cap_cond}")

# ============ B. 记法唯一性 ============
for n, l in enumerate(lines, 1):
    if re.search(r'\|\s*[0-9.]+\(×\d+\)', l):
        alert('B', n, '', f'残留 (×N) 记法: {l.strip()[:70]}')

# ============ C. 多段 ≤ 同档单体 ×1.10（含条件追加段）============
G = defaultdict(list)
for r in skills:
    if r['tier'] in CAP_EPS and r['eps'] is not None:
        G[(r['ch'], r['sub'], r['tier'])].append(r)
for k, rs in sorted(G.items()):
    singles = [r['eps'] for r in rs if r['hits'] == 1 and not r['aoe']]
    if not singles:
        continue
    smax, capc = max(singles), round(max(singles) * MULTI_CAP_RATIO, 3)
    for r in rs:
        hits = r['hits']
        m = re.search(r'(?:追加|改为|额外)\s*([四五六七八]|\d)\s*段', r['mech'])
        cn = {'四': 4, '五': 5, '六': 6, '七': 7, '八': 8}
        if m:
            hits = max(hits, cn.get(m.group(1), int(m.group(1)) if m.group(1).isdigit() else hits))
        if hits <= 1:
            continue
        base = float(r['base_s'])
        eq_h = round(base * 1.4 * hits * (0.8 if r['truedmg'] else 1), 2)
        eps_h = round(eq_h / r['cyc'], 3)
        if eps_h > capc + 0.005:
            alert('C', r['line'], r['name'],
                  f"多段 eps {eps_h}（hits={hits}{'，含条件追加段' if m else ''}）> 同档单体max {smax}×1.10={capc}")

# ============ D. 分档数量 + 等级升序 ============
B = defaultdict(list)
for r in skills:
    B[(r['ch'], r['sub'], r['tier'])].append(r)
for k in sorted(B, key=lambda x: (x[0], x[1], x[2])):
    rs = B[k]
    lvs = [r['lv'] for r in rs if r['lv'] is not None]
    if k[2] in EXPECT and len(rs) != EXPECT[k[2]]:
        alert('D', 0, f'{class_of(k[0])}/{k[1][:10]}/{k[2]}', f'技能数 {len(rs)} ≠ 期望 {EXPECT[k[2]]}')
    if lvs != sorted(lvs):
        alert('D', 0, f'{class_of(k[0])}/{k[1][:10]}/{k[2]}', f'等级乱序 {lvs}')

# ============ E. 重名 ============
seen = defaultdict(list)
for r in skills:
    seen[r['name']].append(r['line'])
for nm, ls in seen.items():
    if len(ls) > 1:
        alert('E', 0, nm, f'重名，出现于 {ls}')

# ============ F. 真伤 ≤2/线 ============
TR = defaultdict(list)
for r in skills:
    if r['truedmg']:
        TR[(class_of(r['ch']), r['sub'][:10])].append(r['name'])
for k, v in sorted(TR.items()):
    if len(v) > 2:
        alert('F', 0, f'{k[0]}/{k[1]}', f'真伤 {len(v)} 个 > 2: {v}')

# ============ G. mp=0 白名单 ============
W = re.compile(r'兑现|姿态|架[设]|切换|吟唱|卸[除负]|消耗.{0,8}(层|点|核|信念)')
for r in skills:
    if r['mp'] != '0' or r['is_passive']:
        continue
    if not W.search(r['mech']):
        alert('G', r['line'], r['name'], f'mp=0 非白名单三类: kind={r["kind"]} mech={r["mech"][:34]}')

# ============ G2. 0 消耗产出资源（被动不计：被动不占出手，不存在"免费刷"）============
for r in skills:
    if r['is_passive']:
        continue
    if r['mp'] == '0' and re.search(r'回蓝|回.{0,3}MP|\+1\s*(?:层|段|核|印)', r['mech']):
        alert('G2', r['line'], r['name'], f'mp=0 却产出资源：{r["mech"][:40]}')

# ============ H. 无 CD 伤害技 mp 门槛 ============
for r in skills:
    if not r['has_dmg'] or r['cd'] not in ('—', '-', ''):
        continue
    try:
        mp = int(r['mp'])
    except ValueError:
        alert('H', r['line'], r['name'], f'无 CD 但 mp 异常: {r["mp"]}')
        continue
    floor = 6 if r['tier'] == 'BASE' else 10
    if mp < floor:
        alert('H', r['line'], r['name'], f'无 CD 且 mp={mp} < {floor}（{r["tier"]} 档门槛）')

# ============ I. 孤儿机制 ============
# 已知误报：①【】里包的是 buff 名而非技能名（如结余奖励【凝神】）；
#          ② 机制名恰好是某技能名的子串（如「终章」vs 技能「终章·黎明颂歌」）会漏报。
# 因此本段只当线索，必须人工过一遍。
BUFF_NAMES = {'凝神'}
blob = ' '.join(r['name'] + r['mech'] for r in skills)
for w in sorted(set(re.findall(r'【([^】]{2,6})】', raw))):
    if w in ('AOE', '真伤') or w in BUFF_NAMES:
        continue
    if w not in blob:
        alert('I', 0, w, '核心机制定义了该效果，技能表中无任何技能实现（孤儿机制）')

# ============ J. 机制重复 ============
DUP = defaultdict(list)
for r in skills:
    key = re.sub(r'[（(].*?[)）]', '', r['mech']).replace('**', '').strip()
    if len(key) >= 6 and not r['is_passive']:
        DUP[key].append((r['line'], r['name']))
for k, v in sorted(DUP.items()):
    if len(v) > 1:
        alert('J', v[0][0], v[0][1], f'机制逐字相同：{[x[1] for x in v[1:]]} —— {k[:44]}')

# ============ K. 倒挂（同线 + 同控制类型才比：定身/眩晕/睡眠各算一类）============
GK = defaultdict(list)
for r in skills:
    m = re.search(r'(定身|眩晕|睡眠)\s*\*{0,2}\s*([0-9.]+)s', r['mech'])
    if m and r['lv']:
        GK[(class_of(r['ch']), r['sub'][:8], m.group(1))].append(
            (r['lv'], r['name'], float(m.group(2)), r['line']))
for k, v in sorted(GK.items()):
    v = sorted(v)
    for i in range(1, len(v)):
        if v[i][2] < v[i - 1][2]:
            alert('K', v[i][3], v[i][1],
                  f'{k[2]}倒挂：Lv{v[i-1][0]} {v[i-1][1]}={v[i-1][2]}s → Lv{v[i][0]} {v[i][1]}={v[i][2]}s')

# ============ L. cast 节奏型 vs §0.3 声称 ============
DIST = defaultdict(list)
for r in skills:
    if r['cast'] is not None:
        DIST[class_of(r['ch'])].append(r['cast'])
for k, v in sorted(DIST.items()):
    if k not in CLAIM_CAST or not v:
        continue
    lo, hi = CLAIM_CAST[k]
    inside = [x for x in v if lo - 0.05 <= x <= hi + 0.05]
    if len(inside) / len(v) < 0.70:
        alert('L', 0, k, f'§0.3 声称主区间 [{lo},{hi}]，实测仅 {len(inside)}/{len(v)} 落在区间内；'
                        f'实际 min={min(v)} max={max(v)}')

# ============ M. 唯一技能数 ============
U = defaultdict(set)
for r in skills:
    U[class_of(r['ch'])].add(r['name'])
for k, v in sorted(U.items()):
    if len(v) != UNIQUE_PER_CLASS:
        alert('M', 0, k, f'唯一技能数 {len(v)} ≠ {UNIQUE_PER_CLASS}')

# ============ N. 「回合」残留（「刻」是合法时间单位，不在此列；规则文本与迁移清单自身除外）============
for n, l in enumerate(lines, 1):
    if l.strip().startswith('>') or '不许出现' in l or '残留' in l:
        continue
    if re.search(r'\|\s*[MC]-\d+', l):      # 迁移清单/工单表是元描述，不校验
        continue
    for m in re.finditer(r'(每回合|回合末|回合开始|回合制|N 回合|个回合|回合计)', l):
        alert('N', n, '', f'残留回合表述：{l.strip()[:76]}')

# ============ O. 与引擎常量一致性 ============
ENGINE = {'磐核': 5, '连段': 5, '信念': 10, '破绽': 50, '战意': 10}
for n, l in enumerate(lines, 1):
    if re.search(r'\|\s*[MC]-\d+', l):
        continue
    for key, mx in ENGINE.items():
        m = re.search(re.escape(key) + r'\s*0-(\d+)', l)
        if m and int(m.group(1)) != mx:
            alert('O', n, key, f'文档上限 0-{m.group(1)} ≠ 引擎 {mx}：{l.strip()[:70]}')

# ============ 派生列回填（总eq/cyc/eps）============
if WRITE:
    out = []
    i = 0
    while i < len(lines):
        l = lines[i]
        s = l.strip()
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-\|]+\|$', lines[i + 1].strip()):
            header = [c.strip().replace(' ', '') for c in s.strip('|').split('|')]
            if 'hits' in header and 'cast' in header:
                if 'eps' not in header:
                    # 旧表（9 列）：插入总eq/cyc/eps 三列
                    hi = header.index('hits') + 1
                    header = header[:hi] + ['总eq', 'cyc', 'eps'] + header[hi:]
                    out.append('| ' + ' | '.join(header) + ' |')
                    out.append('|' + '---|' * len(header))
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith('|'):
                        cells = [c.strip() for c in lines[j].strip().strip('|').split('|')]
                        if len(cells) == len(header) - 3 and (j + 1) in derived:
                            eq_s, cyc_s, eps_s = derived[j + 1]
                            hi2 = header.index('hits') + 1
                            cells = cells[:hi2] + [eq_s, cyc_s, eps_s] + cells[hi2:]
                        out.append('| ' + ' | '.join(cells) + ' |')
                        j += 1
                else:
                    # 新表（已含 eps 列）：原地更新派生列值（覆盖占位符「—」）
                    ieq, icyc, ieps = header.index('总eq'), header.index('cyc'), header.index('eps')
                    out.append(l)
                    out.append(lines[i + 1])
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith('|'):
                        cells = [c.strip() for c in lines[j].strip().strip('|').split('|')]
                        if len(cells) == len(header) and (j + 1) in derived:
                            eq_s, cyc_s, eps_s = derived[j + 1]
                            cells[ieq], cells[icyc], cells[ieps] = eq_s, cyc_s, eps_s
                        out.append('| ' + ' | '.join(cells) + ' |')
                        j += 1
                i = j
                continue
        out.append(l)
        i += 1
    open(DOC, 'w', encoding='utf-8').write('\n'.join(out))
    print('派生列已回填：', len(derived), '行\n')

# ============ 输出 ============
LABEL = {'A': 'eps 天花板 / 观感帽 / 条件倍率（脚本重算）', 'B': '记法唯一性',
         'C': '多段 ≤ 同档单体 eps ×1.10（含条件追加段）', 'D': '分档数量 + 等级升序',
         'E': '不重名', 'F': '真伤 ≤2/线', 'G': 'mp=0 白名单', 'G2': '规则逃逸（0 消耗产资源）',
         'H': '伤害技必有 CD 或代价', 'I': '孤儿机制', 'J': '机制重复', 'K': '控制倒挂',
         'L': 'cast 节奏型 vs §0.3 声称', 'M': '唯一技能数', 'N': '回合残留（刻是合法单位）',
         'O': '与引擎常量一致性'}
print('=' * 82)
print(f'v153 校验报告　基准：cost({BASE_SPD})={BASE_COST}s　eps=总eq/(0.8+cast)')
print('=' * 82)
total = 0
for sec in ['A', 'C', 'D', 'E', 'F', 'G', 'G2', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'B']:
    items = ALERTS.get(sec, [])
    total += len(items)
    print(f'\n── {sec}. {LABEL[sec]}  {"⚠ " + str(len(items)) + " 条" if items else "✅ 通过"}')
    for ln, name, msg in items:
        print(f'     L{ln:<5} {str(name):<16} {msg}')
print('\n' + '=' * 82)
print(f'【技能条目】{len(skills)}　【总告警】{total} 条 → '
      f"{'✅ 可进入下一阶段' if total == 0 else '⚠ 需修正'}")
