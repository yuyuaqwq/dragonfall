# -*- coding: utf-8 -*-
"""v133 收敛落地 v2：skills.py 按缩进层级精确定位技能块（PLAYER+BRANCH 通用）"""
import json, re

path = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py"
plan2 = json.load(open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/burst_scan/converge_plan_v2.json", encoding='utf-8'))
bplan = json.load(open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/burst_scan/converge_branch_r3.json", encoding='utf-8'))

targets = {}
for v in bplan['converge']:
    targets.setdefault(v['skill'], (v['old_power'], v['target_power']))

with open(path, 'r', encoding='utf-8', newline='') as f:
    raw = f.read()
# 保留原始换行风格：检测 CRLF
is_crlf = '\r\n' in raw
lines = raw.split('\r\n') if is_crlf else raw.split('\n')

def indent(ln):
    return len(ln) - len(ln.lstrip())

def find_block(name_line_idx, name_indent):
    """回溯找块起点（缩进更浅的容器行），向前找块结束（缩进<=起点缩进的下一行）"""
    start = None
    for j in range(name_line_idx - 1, -1, -1):
        ln = lines[j]
        if not ln.strip():
            continue
        if indent(ln) < name_indent and re.search(r'["\']?[A-Za-z_0-9\u4e00-\u9fff]+["\']?\s*:\s*\{', ln):
            start = j
            break
    if start is None:
        return None
    end = len(lines)
    s_indent = indent(lines[start])
    for j in range(name_line_idx + 1, len(lines)):
        ln = lines[j]
        if ln.strip() and indent(ln) <= s_indent:
            end = j
            break
    return start, end

ok, bad, missing = [], [], []
for name, (old_p, new_p) in targets.items():
    target_line = None
    for i, ln in enumerate(lines):
        if re.match(r'\s*"name":\s*"' + re.escape(name) + r'"', ln):
            # 多职业同名（如"处决"）：用列表顺序逐个处理；取第一个未处理匹配
            target_line = i
            break
    if target_line is None:
        missing.append(name)
        continue
    blk = find_block(target_line, indent(lines[target_line]))
    if blk is None:
        missing.append(name)
        continue
    s, e = blk
    found = False
    for j in range(s, e):
        pm = re.search(r'"power":\s*([\d.]+)', lines[j])
        if pm:
            cur = float(pm.group(1))
            if abs(cur - old_p) < 1e-9:
                lines[j] = re.sub(r'("power":\s*)[\d.]+', r'\g<1>' + str(new_p), lines[j], count=1)
                ok.append((name, old_p, new_p))
            elif abs(cur - new_p) < 1e-9:
                ok.append((name, old_p, new_p))  # 已应用（幂等跳过）
            else:
                bad.append((name, old_p, cur, j + 1))
            found = True
            break
    if not found:
        missing.append(name)

print(f'OK {len(ok)} | MISMATCH {len(bad)} | NOT_FOUND {len(missing)}')
for b in bad:
    print('  MISMATCH', b)
for m in missing:
    print('  MISSING', m)

if not bad and not missing:
    out = ('\r\n' if is_crlf else '\n').join(lines)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print('写入完成', path)