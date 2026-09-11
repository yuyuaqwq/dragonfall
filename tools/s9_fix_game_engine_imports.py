# -*- coding: utf-8 -*-
"""S9-2 补漏：`from <...>game.engine import A, B` 形态 → 按符号真实来源改写。"""
import ast
import collections
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"_archive_unused", "__pycache__", ".git", ".pytest_cache",
             "_retired_old_engine", "node_modules", "design", "docs", "audit", "framework"}
PAT = re.compile(r"(?m)^([ \t]*)from\s+[\w.]*?\bengine\s+import\s+([^\n#]+)")


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


def main(argv):
    apply = "--apply" in argv
    sym2src = sym2src_from_git()

    def repl(m):
        indent, names = m.group(1), [x.strip() for x in m.group(2).split(",") if x.strip()]
        groups = collections.defaultdict(list)
        unknown = []
        for spec in names:
            base, _, alias = spec.partition(" as ")
            base = base.strip()
            src = sym2src.get(base)
            if not src:
                unknown.append(base)
                continue
            groups[src].append(spec.strip())
        out = []
        for mod, syms in sorted(groups.items()):
            out.append(f"{indent}from {mod} import {', '.join(syms)}")
        if unknown:
            out.append(f"{indent}# ⚠️ 未定源（原 game.engine 无此符号）: {unknown}")
        return "\n".join(out)

    n = 0
    for dp, dn, fs in os.walk(REPO):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in sorted(fs):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            text = open(p, encoding="utf-8", newline="").read()
            if "engine" not in text:
                continue
            new, k = PAT.subn(repl, text)
            if k:
                rel = os.path.relpath(p, REPO).replace("\\", "/")
                print(f"  {rel}: {k} 处")
                n += k
                if apply:
                    open(p, "w", encoding="utf-8", newline="").write(new)
    print(f"\n{'已改写' if apply else 'DRY-RUN'}：{n} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
