# -*- coding: utf-8 -*-
"""v101 扩展性深度审计脚本（2026-08-09）

扫描维度：
1. if/elif 分发链 >=4 分支（命令/效果分发，注册表候选）
2. 命令层（commands/）硬编码数据表（>8 行 dict/list 字面量，应下沉 data/）
3. 零调用函数/方法（定义后无任何引用 = 死代码候选）
4. 裸概率 random.random() < 0.xx（魔法数字）
5. 代码层中文字符串字面量（非 data/ 非测试，硬编码文案/名字候选）
6. 魔法数字乘数/阈值（* 0.xx、/ 0.xx、+ 1000 等）

用法：python scripts/extensibility_audit2.py
"""
import ast
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")

def py_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if fn.endswith(".py"):
                out.append(os.path.join(dirpath, fn))
    return out

# ============ 1. if/elif 链 >=4 ============
print("=" * 70)
print("扫描 1：if/elif 分发链（>=4 分支）")
print("=" * 70)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    rel = os.path.relpath(f, ROOT)
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # 收集链
            chain = [node]
            cur = node
            while cur.orelse and len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
                chain.append(cur)
            # 排除纯 if-else（orelse 非 If 结束）
            total = len(chain)
            if total >= 4:
                # 找链里有没有 elif 形式（orelse 有内容）
                has_elif = any(c.orelse for c in chain[:-1]) or bool(chain[-1].orelse)
                if has_elif:
                    line = chain[0].lineno
                    conds = []
                    for c in chain:
                        try:
                            conds.append(ast.unparse(c.test)[:60])
                        except Exception:
                            conds.append("?")
                    print(f"  📌 {rel}:{line} 链 {total} 分支")
                    for cc in conds[:8]:
                        print(f"      - {cc}")

# ============ 2. 命令层大字面量 ============
print("=" * 70)
print("扫描 2：commands/ 层硬编码数据表（>8 行 dict/list）")
print("=" * 70)
for f in py_files(os.path.join(GAME, "commands")):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    rel = os.path.relpath(f, ROOT)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Dict, ast.List, ast.Set)) and not isinstance(node, ast.Dict):
            pass
        if isinstance(node, ast.Dict) and node.lineno:
            end = node.end_lineno or node.lineno
            if end - node.lineno > 8:
                parent = ""
                print(f"  📌 {rel}:{node.lineno}-{end} 大 dict 字面量 ({end-node.lineno} 行)")
        elif isinstance(node, ast.List) and node.lineno:
            end = node.end_lineno or node.lineno
            if end - node.lineno > 8 and any(isinstance(e, ast.Dict) for e in node.elts):
                print(f"  📌 {rel}:{node.lineno}-{end} 大 list-of-dict 字面量 ({end-node.lineno} 行)")

# ============ 3. 零调用函数 ============
print("=" * 70)
print("扫描 3：定义后零调用的函数/方法（死代码候选）")
print("=" * 70)
all_defs = defaultdict(list)  # name -> [(file, line)]
all_refs = defaultdict(int)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    rel = os.path.relpath(f, ROOT)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            all_defs[node.name].append((rel, node.lineno))
        elif isinstance(node, ast.Name):
            all_refs[node.id] += 1
        elif isinstance(node, ast.Attribute):
            all_refs[node.attr] += 1
# 过滤：def 计数 >= refs 计数 → 无调用方（魔法方法/装饰器除外）
for name, defs in sorted(all_defs.items()):
    if name.startswith("_") and not name.startswith("__"):
        continue
    if name in ("register", "register_init", "check", "main", "run"):
        continue
    if all_refs[name] <= len(defs):
        # 排除装饰器引用（ast.Attribute 会漏掉局部变量引用）
        print(f"  📌 {name} 定义 {len(defs)} 处，引用 {all_refs[name]} 次")
        for d in defs[:3]:
            print(f"      {d[0]}:{d[1]}")

# ============ 4. 裸概率 ============
print("=" * 70)
print("扫描 4：裸概率 random.random() < 0.xx")
print("=" * 70)
pat = re.compile(r"random\.random\(\)\s*<\s*0\.\d+")
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    if "random.random()" not in src:
        continue
    rel = os.path.relpath(f, ROOT)
    for m in pat.finditer(src):
        line = src.count("\n", 0, m.start()) + 1
        snippet = src[m.start():m.start() + 60].replace("\n", " ")
        print(f"  📌 {rel}:{line} {snippet}")

# ============ 5. 命令层中文字符串（硬编码名/文案候选） ============
print("=" * 70)
print("扫描 5：commands/ 层中文字符串常量（数据名/文案硬编码候选）")
print("=" * 70)
for f in py_files(os.path.join(GAME, "commands")):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    rel = os.path.relpath(f, ROOT)
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            # 过滤：命令前缀/提示文案/格式串/短词
            if len(s) < 4 or len(s) > 30:
                continue
            if not re.search(r"[\u4e00-\u9fff]", s):
                continue
            if any(k in s for k in ("『", "』", "输入", "请", "！", "？", "…", "…", "：", "，", "。", "%", "+", " ", "\\n")):
                continue
            if s in seen:
                continue
            seen.add(s)
            # 统计出现次数
            cnt = src.count(f'"{s}"') + src.count(f"'{s}'")
            if cnt >= 2:
                print(f"  📌 {rel}:{node.lineno} ×{cnt} '{s}'")

# ============ 6. 魔法乘数 ============
print("=" * 70)
print("扫描 6：魔法乘数/加成（* 0.xx、* 1.xx、+ 0.xx）top 40")
print("=" * 70)
pat2 = re.compile(r"([*/])\s*(0\.\d{1,3}|1\.\d{1,3})")
counts = defaultdict(list)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    rel = os.path.relpath(f, ROOT)
    for m in pat2.finditer(src):
        line = src.count("\n", 0, m.start()) + 1
        key = m.group(0).strip()
        counts[key].append(f"{rel}:{line}")
for k in sorted(counts, key=lambda x: -len(counts[x]))[:40]:
    print(f"  {k} ×{len(counts[k])}  例: {counts[k][0]}")

print()
print("扫描完成。")
