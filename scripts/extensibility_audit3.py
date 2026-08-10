# -*- coding: utf-8 -*-
"""v102 第三轮扩展性审计脚本（2026-08-09）

本轮全新维度（前两轮未覆盖）：
A. 字符串字面量比较耦合（== "xxx" / in ("a","b")）——逻辑层硬编码数据名
B. dict 访问魔法 key（d["xxx"]）——字段名散落逻辑层
C. 整数魔法数字（经验/伤害/数量/上限，排除通用 0-5/10/100）
D. AST 重复代码块（同函数体内 ≥5 行结构相同的兄弟语句）
E. 超大函数（≥150 行）
F. TODO/FIXME/HACK 注释、bare except、eval/exec
G. 全局可变状态（非 data/ 目录的模块级 dict/list 字面量）
H. f-string SQL / 字符串拼接 SQL

用法：python scripts/extensibility_audit3.py
"""
import ast
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")
SKIP_DIRS = {"__pycache__", "data"}


def py_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                out.append(os.path.join(dirpath, fn))
    return out


def rel(f):
    return os.path.relpath(f, ROOT)


# ============ A. 字符串比较耦合 ============
print("=" * 70)
print("A. 字符串字面量比较（== / != / in 元组列表）")
print("=" * 70)
seen_a = set()
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    r = rel(f)
    for node in ast.walk(tree):
        # Compare: x == "str" / x != "str"
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                    s = comp.value
                    if len(s) >= 3 and re.search(r"[\u4e00-\u9fff]|[a-z_]{4,}", s):
                        key = (r, node.lineno, s)
                        if key not in seen_a:
                            seen_a.add(key)
                            print(f"  📌 {r}:{node.lineno}  ==/!= '{s}'")
        # In: x in ("a","b") / x in ["a","b"]
        elif isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            pass
        if isinstance(node, ast.If) and isinstance(node.test, ast.BoolOp):
            pass
    # 独立扫 in 元组/列表比较
    for node in ast.walk(tree):
        if isinstance(node, (ast.Compare,)):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, ast.In) and isinstance(comp, (ast.Tuple, ast.List, ast.Set)):
                    strs = [e.value for e in comp.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                    if len(strs) >= 2 and all(len(s) >= 3 for s in strs):
                        key = (r, node.lineno, tuple(strs))
                        if key not in seen_a:
                            seen_a.add(key)
                            print(f"  📌 {r}:{node.lineno}  in {strs}")

# ============ B. dict 魔法 key ============
print("=" * 70)
print("B. dict 下标访问魔法 key（d['xxx']，非 data/ 目录）")
print("=" * 70)
pat_key = re.compile(r"\[(['\"])([a-zA-Z_][\w]*)\1\]")
counts_b = defaultdict(list)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    r = rel(f)
    for m in pat_key.finditer(src):
        key = m.group(2)
        # 过滤：SQL 占位符/格式化/常见短 key
        if key in ("self", "cls", "dict", "list", "str", "int", "bool", "None", "True", "False"):
            continue
        if len(key) < 3:
            continue
        line = src.count("\n", 0, m.start()) + 1
        counts_b[key].append(f"{r}:{line}")
# 统计同一 key 出现 >=3 次的（多处硬编码同一字段名）
for k in sorted(counts_b, key=lambda x: -len(counts_b[x])):
    if len(counts_b[k]) >= 3:
        print(f"  📌 '{k}' ×{len(counts_b[k])}  例: {counts_b[k][0]}")

# ============ C. 整数魔法数字 ============
print("=" * 70)
print("C. 整数魔法数字 top 50（非 data/，排除通用 0-5/8/10/24/60/100）")
print("=" * 70)
COMMON = {0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 24, 60, 100}
counts_c = defaultdict(list)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    r = rel(f)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            v = node.value
            if v in COMMON or v < 0 or v > 100000:
                continue
            counts_c[v].append(f"{r}:{node.lineno}")
for k in sorted(counts_c, key=lambda x: -len(counts_c[x]))[:50]:
    print(f"  {k} ×{len(counts_c[k])}  例: {counts_c[k][0]}")

# ============ D. 重复代码块 ============
print("=" * 70)
print("D. 同函数内重复语句块（≥5 行 AST 结构相同）")
print("=" * 70)
def stmt_shape(stmt):
    """语句的归一化形状（去掉字面量值）"""
    try:
        s = ast.dump(stmt, annotate_fields=False)
    except Exception:
        return None
    # 去掉具体数值/字符串
    s = re.sub(r"Constant\([^)]*\)", "C()", s)
    s = re.sub(r"Name\([^)]*\)", "N()", s)
    return s

count_d = 0
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    r = rel(f)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            shapes = [stmt_shape(s) for s in body]
            seen_shapes = defaultdict(list)
            for i, sh in enumerate(shapes):
                if sh and len(sh) > 200:  # 足够复杂的语句才有意义
                    seen_shapes[sh].append(i)
            for sh, idxs in seen_shapes.items():
                if len(idxs) >= 2:
                    # 检查这几段是否连续 ≥5 行
                    lines = []
                    for i in idxs:
                        try:
                            lines.append((body[i].lineno, body[i].end_lineno))
                        except Exception:
                            pass
                    total_lines = sum(e - s + 1 for s, e in lines)
                    if total_lines >= 10:
                        count_d += 1
                        print(f"  📌 {r}:{node.lineno} {node.name}() 内重复块 ×{len(idxs)}（共{total_lines}行）")
print(f"  （共 {count_d} 组）")

# ============ E. 超大函数 ============
print("=" * 70)
print("E. 超大函数（≥150 行）")
print("=" * 70)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    r = rel(f)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln = (node.end_lineno or node.lineno) - node.lineno
            if ln >= 150:
                print(f"  📌 {r}:{node.lineno} {node.name}() {ln} 行")

# ============ F. TODO/bare except/eval ============
print("=" * 70)
print("F. TODO/FIXME/HACK 注释、bare except、eval/exec")
print("=" * 70)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    r = rel(f)
    for i, line in enumerate(src.split("\n"), 1):
        if re.search(r"#\s*(TODO|FIXME|HACK|XXX)\b", line):
            print(f"  📌 {r}:{i} {line.strip()[:80]}")
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            print(f"  📌 {r}:{node.lineno} bare except")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            print(f"  📌 {r}:{node.lineno} {node.func.id}()")

# ============ G. 全局可变状态 ============
print("=" * 70)
print("G. 模块级可变状态（core/commands/store 的顶层 dict/list 字面量）")
print("=" * 70)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    r = rel(f)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            val = node.value
            if isinstance(val, (ast.Dict, ast.List, ast.Set)) and (val.end_lineno or val.lineno) - val.lineno >= 3:
                print(f"  📌 {r}:{node.lineno} 模块级 {node.targets[0].id} ({'dict' if isinstance(val, ast.Dict) else 'list'} {((val.end_lineno or val.lineno) - val.lineno)} 行)")

# ============ H. SQL 拼接 ============
print("=" * 70)
print("H. f-string SQL / 字符串拼接 SQL")
print("=" * 70)
for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    r = rel(f)
    for i, line in enumerate(src.split("\n"), 1):
        if ("SELECT" in line.upper() or "INSERT" in line.upper() or "UPDATE" in line.upper() or "DELETE" in line.upper()) and ("f\"" in line or "f'" in line or " + " in line):
            print(f"  📌 {r}:{i} {line.strip()[:90]}")

print()
print("扫描完成。")
