# -*- coding: utf-8 -*-
"""S9-2 收尾：作用域感知的「缺名」修复。

背景：批量把 `E.sym` 换成裸名 `sym` 时，原文件里的 `from game import engine as E`
可能是**函数内**导入。就地替换会让符号只在那个函数可见，别的函数用同一个裸名就
NameError（`unbound` 检测不能只看「文件里出现过绑定」，必须看**作用域可见性**）。

本脚本用 stdlib `symtable` 判定：某个名字在**某作用域**里是 global（既非 local 也非
free）却被引用，且模块作用域没有绑定 → 真缺名。只对「原引擎 shim 的符号表」里的名字
动手（避免误伤推导式变量 / `__file__` 之类）。

修法：在最后一个顶层 import 之后插入模块级 `from <真实来源> import <符号>`。

用法：python tools/s9_fix_missing_names.py [--apply]
"""
import ast
import os
import subprocess
import symtable
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"_archive_unused", "__pycache__", ".git", ".pytest_cache",
             "_retired_old_engine", "node_modules", "design", "docs", "audit", "framework"}
SELF = {"tools/s9_fix_missing_names.py"}


def sym2src_from_git():
    src = subprocess.run(["git", "show", "HEAD:game/engine.py"], cwd=REPO,
                         capture_output=True, text=True, encoding="utf-8").stdout
    tree = ast.parse(src)
    m = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.level and not node.module:
                for a in node.names:
                    m[a.asname or a.name] = "game." + a.name
            elif node.level:
                for a in node.names:
                    m[a.asname or a.name] = "game." + node.module
            else:
                for a in node.names:
                    m[a.asname or a.name] = node.module or ""
    return m


def unresolved_globals(text: str, path: str) -> set:
    """作用域感知：某作用域里引用到的**全局**名，模块层没有绑定 → 缺名。"""
    try:
        top = symtable.symtable(text, path, "exec")
    except (SyntaxError, ValueError):
        return set()
    module_names = {s.get_name() for s in top.get_symbols()}
    miss = set()

    # 模块层：被引用但没有绑定
    for sym in top.get_symbols():
        n = sym.get_name()
        if sym.is_referenced() and n not in module_names:
            miss.add(n)

    def walk(tbl):
        for sym in tbl.get_symbols():
            n = sym.get_name()
            if sym.is_referenced() and sym.is_global() and n not in module_names:
                miss.add(n)
        for child in tbl.get_children():
            walk(child)

    walk(top)
    return miss


def main(argv):
    apply = "--apply" in argv
    sym2src = sym2src_from_git()
    print(f"符号来源表 {len(sym2src)} 条")
    fixed, left = [], []
    for dp, dn, fs in os.walk(REPO):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in sorted(fs):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, REPO).replace("\\", "/")
            if rel in SELF or rel.startswith(("tools/s9_", "tools/_survey", "tools/_find")):
                continue
            text = open(p, encoding="utf-8", newline="").read()
            miss = unresolved_globals(text, p) & set(sym2src)
            if not miss:
                continue
            fixable = {n: sym2src[n] for n in miss if sym2src[n]}
            unknown = sorted(n for n in miss if not sym2src[n])
            if unknown:
                left.append((rel, unknown))
            if not fixable:
                continue
            groups = {}
            for n, mod in fixable.items():
                groups.setdefault(mod, []).append(n)
            lines = [f"from {mod} import {', '.join(sorted(syms))}"
                     for mod, syms in sorted(groups.items())]
            tree = ast.parse(text)
            last = None
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last = node
            nl = "\r\n" if "\r\n" in text else "\n"
            src_lines = text.splitlines(keepends=True)
            at = last.end_lineno if last else 0
            new = "".join(src_lines[:at]) + nl.join(lines) + nl + "".join(src_lines[at:])
            fixed.append((rel, sorted(fixable)))
            if apply:
                open(p, "w", encoding="utf-8", newline="").write(new)

    print(f"\n{'已修' if apply else 'DRY-RUN'}：{len(fixed)} 个文件")
    for rel, names in fixed:
        print(f"   {rel}: {names}")
    if left:
        print(f"\n⚠️ 无法定源（需人工）：{len(left)}")
        for rel, names in left:
            print(f"   {rel}: {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
