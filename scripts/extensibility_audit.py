# -*- coding: utf-8 -*-
"""扩展性审计扫描：if-elif 长链 / 硬编码引用 / 魔法数字 / 可疑字面量"""
import ast
import os
import re
import sys
from collections import defaultdict

ROOT = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game"

# 已知地图/城镇/区域 ID（data 定义处允许出现，代码引用处才算硬编码）
MAP_IDS = {
    "oak_town", "oak_plain", "white_deer_forest", "iron_harbor", "moon_gate",
    "holy_temple", "nameless_harbor", "ash_city", "royal_capital", "elf_forest",
    "dwarf_mountain", "frost_plain", "dragon_ridge", "echo_cave", "abyss",
}

def scan_elif_chains(path):
    """AST 找 if-elif 链（分支数 >= 6 的）"""
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return []
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            chain = [node]
            cur = node
            while cur.orelse and len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
                chain.append(cur)
            if len(chain) >= 6:
                # 提取每个分支的条件摘要
                conds = []
                for n in chain:
                    try:
                        conds.append(ast.unparse(n.test)[:60])
                    except Exception:
                        conds.append("?")
                results.append((node.lineno, len(chain), conds))
    return results

def scan_hardcoded_refs(path, src):
    """硬编码引用：代码里直接出现已知地图 ID / 中文城镇名 / 数字魔法"""
    issues = []
    lines = src.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "\"\"\"", "'''", "//")):
            continue
        # 1. 地图 ID 直接出现（排除 data 文件与注释）
        for mid in MAP_IDS:
            if f'"{mid}"' in line or f"'{mid}'" in line:
                issues.append((i, f"硬编码地图ID: {mid}", stripped[:90]))
        # 2. 中文城镇名直接出现
        for cn in ("橡木镇", "白鹿城", "铁港城", "月门城", "圣堂", "无名港", "灰烬城", "王都"):
            if f'"{cn}"' in line or f"'{cn}'" in line:
                issues.append((i, f"硬编码城镇名: {cn}", stripped[:90]))
        # 3. 11 位数字（QQ号嫌疑）
        m = re.search(r'["\'](\d{9,11})["\']', line)
        if m:
            issues.append((i, f"疑似硬编码QQ/ID: {m.group(1)}", stripped[:90]))
    return issues

def scan_magic_numbers(path, src):
    """魔法数字：判断/计算中的裸数字（启发式，只标记高可疑）"""
    issues = []
    lines = src.splitlines()
    patterns = [
        (r"random\.random\(\)\s*<\s*0\.\d+", "随机概率裸数字"),
        (r"<=\s*\d{2,4}(\s*[):])", "阈值裸数字(2-4位)"),
        (r"==\s*\d{2,4}(\s*[):])", "相等裸数字"),
    ]
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "\"\"\"", "'''")):
            continue
        for pat, name in patterns:
            if re.search(pat, line):
                issues.append((i, name, stripped[:90]))
    return issues

def scan_dup_strings(src):
    """重复长字符串（>30 字符，出现 >=3 次，疑似应抽常量）"""
    strings = re.findall(r'["\']([^"\']{30,})["\']', src)
    cnt = defaultdict(int)
    for s in strings:
        cnt[s] += 1
    return [(s, c) for s, c in cnt.items() if c >= 3]

def main():
    files = []
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if fn.endswith(".py") and not fn.startswith("_"):
                files.append(os.path.join(dirpath, fn))
    files.sort()

    print("=" * 70)
    print("扫描 1：if-elif 长链（>=6 分支，命令/效果分发硬编码）")
    print("=" * 70)
    for f in files:
        rel = os.path.relpath(f, ROOT)
        if "data" in rel:  # 数据层分支多是数据声明，跳过
            continue
        for lineno, n, conds in scan_elif_chains(f):
            print(f"\n📌 {rel}:{lineno}  ({n} 分支)")
            for c in conds[:8]:
                print(f"    ├─ {c}")

    print("\n" + "=" * 70)
    print("扫描 2：硬编码地图ID/城镇名/QQ号（代码引用，排除 data 层定义）")
    print("=" * 70)
    for f in files:
        rel = os.path.relpath(f, ROOT)
        if rel.startswith("data"):
            continue
        with open(f, encoding="utf-8") as fh:
            src = fh.read()
        issues = scan_hardcoded_refs(f, src)
        if issues:
            print(f"\n📌 {rel}")
            for lineno, kind, snippet in issues[:15]:
                print(f"    L{lineno} [{kind}] {snippet}")

    print("\n" + "=" * 70)
    print("扫描 3：魔法数字（概率/阈值裸数字，top 30）")
    print("=" * 70)
    all_magic = []
    for f in files:
        rel = os.path.relpath(f, ROOT)
        if rel.startswith("data"):
            continue
        with open(f, encoding="utf-8") as fh:
            src = fh.read()
        for lineno, kind, snippet in scan_magic_numbers(f, src):
            all_magic.append((rel, lineno, kind, snippet))
    for rel, lineno, kind, snippet in all_magic[:40]:
        print(f"  {rel}:{lineno} [{kind}] {snippet}")

    print("\n" + "=" * 70)
    print("扫描 4：重复长字符串（>=3 次，应抽常量）")
    print("=" * 70)
    for f in files:
        rel = os.path.relpath(f, ROOT)
        if rel.startswith("data") or "test" in rel:
            continue
        with open(f, encoding="utf-8") as fh:
            src = fh.read()
        dups = scan_dup_strings(src)
        if dups:
            print(f"\n📌 {rel}")
            for s, c in dups[:8]:
                print(f"    ×{c}: {s[:80]}")

if __name__ == "__main__":
    main()
