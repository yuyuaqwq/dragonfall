# -*- coding: utf-8 -*-
"""S9-2 续：`from conftest import ..., E, ...` 的收口。

conftest 原先 re-export 引擎别名 `E`（= 已删的 `game.engine` shim）。删 shim 后：
  * 真用 `E.sym` 的文件 → 改成从符号真实来源 import，并把 `E.sym` → `sym`
  * 只是顺手 import 的 → 从 conftest import 行里摘掉 `E`

符号→来源 由 `git show HEAD:game/engine.py` 的 re-export 表反查（权威、不手抄）。

用法：python tools/s9_conftest_E.py [--apply]
"""
import ast
import collections
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(REPO, "tests")
SELF = {"tools/s9_conftest_E.py"}


def sym2src_from_git():
    src = subprocess.run(["git", "show", "HEAD:game/engine.py"], cwd=REPO,
                         capture_output=True, text=True, encoding="utf-8").stdout
    tree = ast.parse(src)
    m = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.level:
                if node.module:
                    for a in node.names:
                        m[a.asname or a.name] = "game." + node.module
                else:
                    # `from . import content as C` → 符号 C 的来源是 game.content
                    for a in node.names:
                        m[a.asname or a.name] = "game." + a.name
            else:
                for a in node.names:
                    m[a.asname or a.name] = node.module or ""
    return m


def main(argv):
    apply = "--apply" in argv
    sym2src = sym2src_from_git()
    print(f"符号来源表 {len(sym2src)} 条")

    IMPORT_RE = re.compile(
        r"(?m)^([ \t]*from\s+conftest\s+import\s+)([^\n#]+?)([ \t]*(?:#.*)?)$")

    changed = []
    for fn in sorted(os.listdir(TESTS)):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(TESTS, fn)
        rel = f"tests/{fn}"
        text = open(p, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in text else "\n"
        m = IMPORT_RE.search(text)
        if not m:
            continue
        names = [x.strip() for x in m.group(2).split(",") if x.strip()]
        if "E" not in names:
            continue
        body = "\n".join(ln.split("#")[0] for ln in text.splitlines())
        used = sorted(set(re.findall(r"\bE\.(\w+)", body)))
        unknown = [s for s in used if s not in sym2src]

        new_names = [x for x in names if x != "E"]
        new_imp = m.group(1) + ", ".join(new_names) + m.group(3)

        if used and not unknown:
            groups = collections.defaultdict(list)
            for s in used:
                groups[sym2src[s]].append(s)
            extra = [f"from {mod} import {', '.join(sorted(syms))}"
                     for mod, syms in sorted(groups.items())]
            block = new_imp + nl + nl.join(extra)
            new = text[:m.start()] + block + text[m.end():]
            for s in used:
                new = re.sub(rf"\bE\.{s}\b", s, new)
        else:
            new = text[:m.start()] + new_imp + text[m.end():]

        if new != text:
            changed.append((rel, used))
            if apply:
                open(p, "w", encoding="utf-8", newline="").write(new)

    print(f"\n{'已改写' if apply else 'DRY-RUN'}：{len(changed)} 个文件")
    n_use = sum(1 for _, u in changed if u)
    print(f"  其中真用 E.sym 的 {n_use} 个；仅顺手 import 的 {len(changed) - n_use} 个")
    for rel, u in changed:
        if u:
            print(f"    {rel}: {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
