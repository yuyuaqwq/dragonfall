# -*- coding: utf-8 -*-
"""v101 死代码精化扫描：排除命令装饰器/注册表 handler 后，找真零引用函数"""
import ast
import os
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

# 第一遍：收集所有 def + 装饰器信息
defs = defaultdict(list)  # name -> [(file, line, is_cmd)]
refs = defaultdict(int)
decorated = set()  # (file, name) 被命令/注册装饰器标记

for f in py_files(GAME):
    src = open(f, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    rel = os.path.relpath(f, ROOT)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_cmd = False
            for dec in node.decorator_list:
                dname = ""
                if isinstance(dec, ast.Name):
                    dname = dec.id
                elif isinstance(dec, ast.Attribute):
                    dname = dec.attr
                elif isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Attribute):
                        dname = dec.func.attr
                    elif isinstance(dec.func, ast.Name):
                        dname = dec.func.id
                if dname in ("regex", "register", "register_init", "command", "on_", "matcher"):
                    is_cmd = True
                    break
            defs[node.name].append((rel, node.lineno, is_cmd))
        elif isinstance(node, ast.Name):
            refs[node.id] += 1
        elif isinstance(node, ast.Attribute):
            refs[node.attr] += 1

print("=== 真零引用函数（非命令/非注册 handler）===")
for name, dl in sorted(defs.items()):
    if name.startswith("__"):
        continue
    # 全部都是命令装饰的 → 跳过
    if all(d[2] for d in dl):
        continue
    # 引用次数 <= 定义次数 → 无外部调用
    if refs[name] <= len(dl):
        # 排除装饰器工厂（deco/register 本身就是被调用者）
        if name in ("register", "deco", "check", "main", "run"):
            continue
        print(f"  📌 {name} 引用 {refs[name]} 次")
        for d in dl[:2]:
            tag = " [命令]" if d[2] else ""
            print(f"      {d[0]}:{d[1]}{tag}")
