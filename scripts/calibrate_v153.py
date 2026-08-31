# -*- coding: utf-8 -*-
"""v153 数值标定：用目标 eps 反解每个技能的 base，并回填文档

原理（与 audit_v153.py 完全一致的口径）：
    cyc  = 0.8 + cast
    总eq = base × 1.40 × 有效段数 × (0.8 若真伤)
    eps  = 总eq / cyc

    base = 目标eps × cyc / (1.40 × 有效段数 × 0.8 若真伤)

目标 eps 的选取规则：
    档位上限 × 角色系数，再被「条件倍率上限 / 条件倍率」与「AOE 单目标上限」压低。

用法:
    python calibrate_v153.py           # 干跑，只打印改动
    python calibrate_v153.py --write   # 回填 base 列
"""
import re, sys, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
DOC = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/docs/CLASS_MECHANICS_v153.md"
WRITE = '--write' in sys.argv
lines = open(DOC, encoding='utf-8').read().split('\n')

BASE_COST = 0.8
TIER_TOP = {'BASE': 0.85, 'T1': 1.00, 'T2': 1.15, 'T3': 1.30}
CAP_EPS = {'BASE': 0.85, 'T1': 1.00, 'T2': 1.15, 'T3': 1.30}
CAP_COND = {'BASE': 1.05, 'T1': 1.30, 'T2': 1.50, 'T3': 1.75}
CAP_EQ_LOOK = {'BASE': 2.0, 'T1': 2.6, 'T2': 3.6, 'T3': 4.6}   # 观感帽，反解 base 时也要受它约束
AOE_RATIO = 0.80

ROLE_MULTI = 0.85      # 多段（留出 ≤ 同档单体×1.10 的余量）
ROLE_NORMAL = 0.80     # 普通单体
ROLE_PEAK = 1.00       # 顶点 / 终结
ROLE_AOE = 0.55        # AOE

PEAK_HINT = re.compile(
    r'终结技|顶点|终焉|归一|圣域|镇世|天籁|死寂|曙光|贯日|死神|崩山|万毒|战争化身|破晓|永恒|终末|不灭')


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


CN = {'四': 4, '五': 5, '六': 6, '七': 7, '八': 8}


def eff_hits(hits, mech):
    m = re.search(r'(?:追加|改为|额外)\s*([四五六七八]|\d)\s*段', mech)
    if m:
        v = CN.get(m.group(1), int(m.group(1)) if m.group(1).isdigit() else hits)
        return max(hits, v)
    return hits


def max_mult(mech):
    """取出机制列里最大的条件倍率（与 audit_v153.py A 段同一套规则）"""
    out = [1.0]
    for m in re.finditer(r'×\s*(1\.[0-9]+)', mech):
        out.append(float(m.group(1)))
    for m in re.finditer(r'×\(1\s*\+\s*([0-9.]+)\s*×\s*([^)]+?)\)', mech):
        coef, var = float(m.group(1)), m.group(2).strip()
        n = {'连段': 5, '核数': 5, '磐核数': 5, '层数': 9, '段': 5}.get(var)
        if n:
            out.append(round(1 + coef * n, 3))
    for m in re.finditer(r'每层\s*\+([0-9.]+)%', mech):
        n = 9 if '印记' in mech else (8 if '毒' in mech else 5)
        out.append(round(1 + float(m.group(1)) / 100 * n, 3))
    for m in re.finditer(r'每系\s*×\s*([0-9.]+)', mech):
        out.append(round(float(m.group(1)) ** 3, 3))
    for m in re.finditer(r'\(\s*1\s*\+\s*目标破绽\s*/\s*(\d+)\s*×\s*([0-9.]+)\)', mech):
        out.append(round(1 + 50 / float(m.group(1)) * float(m.group(2)), 3))
    for m in re.finditer(r'(?:最高|满层|满核|满毒)\s*[（(]?\s*×?\s*([0-9.]+)', mech):
        out.append(float(m.group(1)))
    for m in re.finditer(r'\(最高 ×([0-9.]+)', mech):
        out.append(float(m.group(1)))
    return max(out)


changes = []
tables = parse_tables(lines)
for start, header, rows in tables:
    hn = [h.replace(' ', '') for h in header]
    if 'base' not in hn or 'cast' not in hn:
        continue
    ib, ih, ica = hn.index('base'), hn.index('hits'), hn.index('cast')
    imech = len(hn) - 1
    for (ln, cells) in rows:
        if len(cells) < len(hn):
            continue
        name, base_s = cells[0], cells[ib]
        if name in ('技能',) or set(name) <= set('-: '):
            continue
        if base_s in ('—', '-', ''):
            continue
        try:
            cast = float(cells[ica])
            hits = int(cells[ih]) if cells[ih].isdigit() else 1
        except ValueError:
            continue
        mech = cells[imech]
        tier = tier_of(ln)
        if tier not in TIER_TOP:
            continue
        truedmg = '真伤' in (cells[hn.index('kind')] if 'kind' in hn else '')
        aoe = '[AOE]' in mech
        eh = eff_hits(hits, mech)
        mm = max_mult(mech)
        cyc = BASE_COST + cast

        # 目标 eps
        if aoe:
            target = TIER_TOP[tier] * ROLE_AOE
        elif eh > 1:
            target = TIER_TOP[tier] * ROLE_MULTI
        elif PEAK_HINT.search(name + mech):
            target = TIER_TOP[tier] * ROLE_PEAK
        else:
            target = TIER_TOP[tier] * ROLE_NORMAL
        target = min(target, CAP_COND[tier] / mm)          # 条件倍率压低
        if aoe:
            target = min(target, CAP_EPS[tier] * AOE_RATIO)
        target = min(target, CAP_EPS[tier])                # 裸上限

        # 向下取整到 2 位（round 会因四舍五入让 eps 微超上限 0.01~0.02）
        import math as _m
        new_base = _m.floor(target * cyc / (1.40 * eh * (0.8 if truedmg else 1)) * 100) / 100
        # 观感帽约束：单发总eq = base×1.4×段 不能超 CAP_EQ_LOOK
        look_cap = CAP_EQ_LOOK.get(tier, 9) / (1.40 * eh * (0.8 if truedmg else 1))
        new_base = min(new_base, _m.floor(look_cap * 100) / 100)
        old_base = float(base_s)
        if abs(new_base - old_base) > 0.004:
            changes.append((ln, name, tier, old_base, new_base, cast, eh, mm,
                            round(target, 3), round(new_base * 1.4 * eh * (0.8 if truedmg else 1) / cyc, 3)))

if WRITE:
    # 按列索引写 base（绝不碰别的列）
    for start, header, rows in tables:
        hn = [h.replace(' ', '') for h in header]
        if 'base' not in hn or 'cast' not in hn:
            continue
        ib = hn.index('base')
        for (ln, cells) in rows:
            if len(cells) != len(hn):
                continue
            fix = next((c for c in changes if c[0] == ln), None)
            if not fix:
                continue
            row = list(cells)
            row[ib] = f'{fix[4]}'          # 新 base
            lines[ln - 1] = '| ' + ' | '.join(row) + ' |'
    open(DOC, 'w', encoding='utf-8').write('\n'.join(lines))

print(f'待调整 {len(changes)} 个技能' + ('（已回填）' if WRITE else '（干跑，加 --write 生效）'))
print(f'{"行":<6}{"技能":<16}{"档":<6}{"旧base":>8}{"新base":>8}{"cast":>7}{"段":>4}{"条件":>7}{"目标eps":>9}{"实得eps":>9}')
for ln, name, tier, old, new, cast, eh, mm, tgt, got in changes:
    print(f'L{ln:<5}{name:<16}{tier:<6}{old:>8}{new:>8}{cast:>7}{eh:>4}{mm:>7}{tgt:>9}{got:>9}')
