# -*- coding: utf-8 -*-
"""S9-2：删除过渡 shim 的消费点改写。

删两个 shim：
  `game/engine.py`  —— re-export 引擎公式（现 `saintess_engine.battle.formulas`）+ 内容侧规则
                       （现 `game/content_rules/{skills,panel,gameplay}`）+ 数据表
  `game/core/{battle_bars,formation,formula_expr,skill_kinds}.py`
                    —— S3 已迁 `saintess_engine/`（原 support/ 子包，模块化重排后为顶层子包）

改写策略（逐**出现位置**处理，一个文件可能有多处别名导入）：
  1. 收集文件里所有 `from X import engine as ALIAS` 行（含相对 `from .. import`）
  2. ALIAS.sym 的符号 → 真实来源模块（由 shim 的 re-export 表反查）
  3. **每处**按自身缩进就地换成真实 import（保留原本的惰性导入位置/作用域 ——
     提到模块级会打断既有循环依赖）；一处符号都没用到的直接删行
  4. 正文 `ALIAS.sym` → `sym`
  5. `from ..core.<name> import …` → `from saintess_engine.<name> import …`

跳过：shim 自身 / `_archive_unused/` / `tests/_retired_old_engine/` / 本工具。

用法：python tools/s9_remove_shims.py [--apply]
"""
import ast
import collections
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"_archive_unused", "__pycache__", ".git", ".pytest_cache",
             "_retired_old_engine", "node_modules", "design", "docs", "audit", "framework"}
SHIM_FILES = {"game/engine.py", "game/core/battle_bars.py", "game/core/formation.py",
              "game/core/formula_expr.py", "game/core/skill_kinds.py"}
SELF = {"tools/s9_remove_shims.py"}

CORE_MAP = {
    "battle_bars": "saintess_engine.gauge",
    "formation": "saintess_engine.formation",
    "formula_expr": "saintess_engine.expr",
    "skill_kinds": "saintess_engine.kinds",
}

ALIAS_IMPORT = re.compile(
    r"(?m)^[ \t]*from\s+(?:[\w.]+|\.+)\s+import\s+engine\s+as\s+(\w+)[ \t\r]*(?:#.*)?$")
CORE_IMPORT = re.compile(
    r"(?m)^([ \t]*)from\s+[\w.]*core\.(battle_bars|formation|formula_expr|skill_kinds)"
    r"\s+import\s+([^\n#]+)")


def build_sym_map():
    p = os.path.join(REPO, "game", "engine.py")
    tree = ast.parse(open(p, encoding="utf-8").read())
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


def strip_comments(text: str) -> str:
    return "\n".join(ln.split("#")[0] for ln in text.splitlines())


def main(argv):
    apply = "--apply" in argv
    sym2src = build_sym_map()
    changed, conflicts = [], []
    for dp, dn, fs in os.walk(REPO):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in sorted(fs):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, REPO).replace("\\", "/")
            if rel in SHIM_FILES or rel in SELF:
                continue
            src = open(p, encoding="utf-8", newline="").read()
            if "import engine as" not in src and not CORE_IMPORT.search(src):
                continue
            body = strip_comments(src)
            new, plan, alias_syms, bad = src, [], {}, []
            for m in ALIAS_IMPORT.finditer(src):
                alias = m.group(1)
                used = collections.Counter(re.findall(rf"\b{alias}\.(\w+)", body))
                indent = re.match(r"[ \t]*", m.group(0)).group(0)
                if not used:
                    plan.append((m.start(), m.end(), ""))
                    continue
                groups = collections.defaultdict(list)
                for s in used:
                    if s not in sym2src:
                        bad.append(f"未知符号 {alias}.{s}")
                        continue
                    groups[sym2src[s]].append(s)
                if bad:
                    break
                lines = [f"{indent}from {mod} import {', '.join(sorted(syms))}"
                         for mod, syms in sorted(groups.items())]
                tail = src[m.end():m.end() + 2]
                if tail == "\r\n":
                    repl, end = "\r\n".join(lines) + "\r\n", m.end() + 2
                elif tail[:1] == "\n":
                    repl, end = "\n".join(lines) + "\n", m.end() + 1
                else:
                    repl, end = "\n".join(lines), m.end()
                plan.append((m.start(), end, repl))
                for s in groups.values():
                    for x in s:
                        alias_syms.setdefault(alias, []).append(x)
            if bad:
                conflicts.append((rel, bad))
                continue
            for start, end, repl in sorted(plan, reverse=True):
                new = new[:start] + repl + new[end:]
            for alias, syms in alias_syms.items():
                for s in set(syms):
                    new = re.sub(rf"\b{alias}\.{s}\b", s, new)
            new = CORE_IMPORT.sub(
                lambda m: f"{m.group(1)}from {CORE_MAP[m.group(2)]} import {m.group(3).strip()}",
                new)
            if new != src:
                changed.append(rel)
                if apply:
                    open(p, "w", encoding="utf-8", newline="").write(new)
    print(f"{'已改写' if apply else 'DRY-RUN'}：{len(changed)} 个文件")
    for r in changed:
        print("   ", r)
    if conflicts:
        print(f"\n⚠️ 跳过 {len(conflicts)}（需人工）：")
        for rel, why in conflicts:
            print(f"   {rel}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
