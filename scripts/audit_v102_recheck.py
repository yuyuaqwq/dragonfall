# -*- coding: utf-8 -*-
"""v102 复核扫描：C 级残留 + B1/B2/B3 完整清单 + 审计维度复查"""
import ast, os, re, sys

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"
PY = []
for d, _, files in os.walk(ROOT):
    for f in files:
        if f.endswith(".py"):
            PY.append(os.path.join(d, f))

def read(p):
    try:
        return open(p, encoding="utf-8").read()
    except Exception:
        return ""

print("=" * 60)
print("【1】C 级残留复查（v102 后应清零）")
print("=" * 60)

# C1 地图 type 中文比较残留
c1 = []
pat_c1 = ["城镇区域", "城镇外郊", "城镇街道", "城镇出口"]
for p in PY:
    src = read(p)
    for m in re.finditer(r'==\s*["\']([^"\']*城镇[^"\']*)["\']|in\s*\(?["\'][^"\']*城镇', src):
        c1.append((p, m.group(0)))
print(f"\nC1 地图 type 中文比较残留: {len(c1)} 处")
for p, m in c1[:10]:
    print(f"  {p}: {m}")

# C2 中文物品名/类型判断残留
c2 = []
for p in PY:
    src = read(p)
    for kw in ["回城卷轴", "宠物蛋", "坐骑蛋"]:
        for m in re.finditer(r'==\s*["\']' + kw + r'["\']|in\s*\(?["\']' + kw, src):
            c2.append((p, kw, m.group(0)))
print(f"\nC2 中文物品名判断残留: {len(c2)} 处")
for p, kw, m in c2[:10]:
    print(f"  {p}: {m}")

# C3 职业 ID 裸比较残留
c3 = []
for p in PY:
    src = read(p)
    for m in re.finditer(r"==\s*['\"]cls_(\w+)['\"]|['\"]cls_(\w+)['\"]\s*==", src):
        c3.append((p, m.group(0)))
print(f"\nC3 职业 ID 裸比较残留: {len(c3)} 处")
for p, m in c3[:10]:
    print(f"  {p}: {m}")

# C4/C5 数据表定义位置
print("\nC4/C5 数据表位置检查:")
for p in PY:
    src = read(p)
    if re.search(r"SKILL_UP\s*=|CORE_RESOURCES\s*=", src):
        print(f"  SKILL_UP/CORE_RESOURCES 定义: {p}")
    if re.search(r"STAT_TEMPLATES|stat_templates", src) and "/data/" in p:
        print(f"  stat_templates: {p}")

# C6 属性 key 组合残留
c6 = []
for p in PY:
    src = read(p)
    for m in re.finditer(r"in\s*\(\s*['\"](crit|dodge)['\"]\s*,\s*['\"](crit|dodge)['\"]\s*\)", src):
        c6.append((p, m.group(0)))
print(f"\nC6 ('crit','dodge') 裸写残留: {len(c6)} 处")
for p, m in c6[:10]:
    print(f"  {p}: {m}")

print()
print("=" * 60)
print("【2】B1 超大函数完整清单（≥120 行，对照审计 10 个）")
print("=" * 60)
big = []
for p in PY:
    src = read(p)
    try:
        tree = ast.parse(src)
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            n = node.end_lineno - node.lineno + 1
            if n >= 120:
                big.append((n, p, node.lineno, node.name))
big.sort(reverse=True)
for n, p, ln, name in big:
    print(f"  {n:>3}行  {p}:{ln} {name}")

print()
print("=" * 60)
print("【3】B2 动态列名 SQL 完整清单")
print("=" * 60)
b2 = []
for p in PY:
    src = read(p)
    for i, line in enumerate(src.splitlines(), 1):
        if re.search(r'f["\'](UPDATE|INSERT INTO|DELETE FROM)[^"\']*\{', line):
            b2.append((p, i, line.strip()[:90]))
print(f"共 {len(b2)} 处:")
for p, i, line in b2:
    print(f"  {p}:{i} {line}")

print()
print("=" * 60)
print("【4】B3 整数魔法数字统计（裸数字出现频率 top20）")
print("=" * 60)
from collections import Counter
cnt = Counter()
for p in PY:
    if "test" in p:
        continue
    src = read(p)
    # 找 == 30 / * 30 / 30, 等上下文中的裸数字（跳过 0/1/2/3/4/5 低值）
    for m in re.finditer(r'(?<![.\w])([6-9]|\d{2,})(?![.\w])', src):
        v = int(m.group(1))
        if v >= 6:
            cnt[v] += 1
for v, c in cnt.most_common(20):
    print(f"  {v} x{c}")
