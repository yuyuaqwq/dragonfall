# -*- coding: utf-8 -*-
"""wiki 行号引用自检：`file.py:NNN` 是否还指向它声称的符号。

背景（2026-09-11）：`docs/engine-wiki/` 大量行文用 `file.py:行号` 指位（792 处）。
引擎一改，行号整体漂移 → 文档把人带到错误的行。本工具按「文档那一行提到的符号名」
反查符号当前真实行号，不一致即报 drift（附建议行号）。

用法：
    python tools/check_wiki_refs.py            # 全量报告
    python tools/check_wiki_refs.py --fix-hint # 只列有建议值的
退出码：0 = 无 drift；1 = 有 drift（可接 CI）。

判据边界（有意保守）：
- 只对「文档行里出现符号名」的引用做判定；纯行号无符号名 → 跳过（无法判定）。
- 支持 `def`/`class`/赋值 三类符号；同名多处 → 取离引用行最近的一处。
- 文件按 basename 解析，同名多份（engine 与 content 都有 skills.py 等）用 basename
  索引 + 目录偏好（battle2/ 优先），找不到 → 报 unresolved 而不猜。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "docs", "engine-wiki")
# --fix 自动改写白名单（运行时由 --fix-files= 覆盖）
FIX_ALLOW = set()

REF_RE = re.compile(r"([\w/]+\.py):(\d+)(?:-(\d+))?")
# 文档行里的候选符号名：反引号内、或后随 ( 的标识符
CAND_IDENT_RE = re.compile(r"`([A-Za-z_][\w\.]{2,})`")
CAND_CALL_RE = re.compile(r"\b([A-Za-z_][\w]{2,})\s*\(")

_SKIP_DIRS = {"__pycache__", ".git", "_archive_unused", "tests"}


def _build_index():
    """basename → [相对路径...]（battle2/ 优先，tests/ 排除）。"""
    idx = {}
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for f in fs:
            if f.endswith(".py"):
                idx.setdefault(f, []).append(os.path.relpath(os.path.join(root, f), ROOT))
    for k in idx:
        idx[k].sort(key=lambda p: (0 if "battle2" in p else 1, len(p)))
    return idx


def _symbol_lines(path):
    """path 内 def/class（任意缩进）+ 模块级赋值 符号 → 行号列表。

    ⚠️ 只收**模块级**赋值：函数体内的局部赋值（`dmg = ...` / `actor = ...`）与
    参数名同名，会把 wiki 表格里的参数列误判成符号 → 大量假 drift（2026-09-11
    首版即踩：events.md 全表误报）。
    """
    out = {}
    try:
        lines = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        return out
    for i, l in enumerate(lines, 1):
        m = re.match(r"\s*(?:async\s+)?def\s+(\w+)", l)
        if m:
            out.setdefault(m.group(1), []).append(i)
            continue
        m = re.match(r"\s*class\s+(\w+)", l)
        if m:
            out.setdefault(m.group(1), []).append(i)
            continue
        if l[:1] in (" ", "\t"):
            continue  # 非模块级赋值 → 不收（局部/字段名会假报）
        m = re.match(r"([A-Za-z_]\w*)\s*(?::[^=]+)?=", l)
        if m:
            out.setdefault(m.group(1), []).append(i)
    return out


def main() -> int:
    fixed_hint_only = "--fix-hint" in sys.argv
    fix = "--fix" in sys.argv
    # --fix 只在「本次改动过的引擎文件」上自动改写（避免误改判不准的老引用）
    allow = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--fix-files=")]
    global FIX_ALLOW
    FIX_ALLOW = set(allow[0].split(",")) if allow else set()
    fixups = {}
    index = _build_index()
    symcache = {}
    drifts, unresolved, checked = [], [], 0
    for root, dirs, fs in os.walk(WIKI):
        for f in sorted(fs):
            if not f.endswith(".md"):
                continue
            wpath = os.path.join(root, f)
            wrel = os.path.relpath(wpath, WIKI).replace(os.sep, "/")
            for ln, text in enumerate(open(wpath, encoding="utf-8").read().splitlines(), 1):
                for m in REF_RE.finditer(text):
                    base, n = m.group(1), int(m.group(2))
                    end = int(m.group(3)) if m.group(3) else n
                    bname = os.path.basename(base)
                    cands = index.get(bname)
                    if not cands:
                        unresolved.append((wrel, ln, base, n, "文件未找到"))
                        continue
                    target = cands[0]
                    if target not in symcache:
                        symcache[target] = _symbol_lines(target)
                    syms = symcache[target]
                    # 候选符号：wiki 行里出现、且确实是该文件符号的标识符。
                    # 取「文本位置上离该引用最近」的那个 —— 表格一行里常同时出现
                    # 多个符号名，就近者才是该引用指向的符号（否则会修错行）。
                    cand_pos = []
                    for mm in CAND_IDENT_RE.finditer(text):
                        nm = mm.group(1).split(".")[-1]
                        if nm in syms:
                            cand_pos.append((abs(mm.start() - m.start()), nm))
                    for mm in CAND_CALL_RE.finditer(text):
                        if mm.group(1) in syms:
                            cand_pos.append((abs(mm.start() - m.start()), mm.group(1)))
                    if not cand_pos:
                        continue  # 无符号线索 → 无法判定（有意跳过）
                    cand_pos.sort()
                    name = cand_pos[0][1]
                    checked += 1
                    if any(n <= ln2 <= end for ln2 in syms[name]):
                        continue
                    ln2 = min(syms[name], key=lambda x: abs(x - n))
                    drifts.append((wrel, ln, f"{base}:{n}", name, ln2, text.strip()[:90]))
                    if fix and bname in FIX_ALLOW:
                        fixups.setdefault(wpath, []).append((f"{base}:{n}", f"{base}:{ln2}"))
    print(f"wiki 行号引用自检：可判定 {checked} 处 → drift {len(drifts)} 处"
          f"；未解析文件 {len(unresolved)} 处")
    if unresolved:
        print("\n-- 未解析文件（basename 不在仓库） --")
        for r in unresolved[:15]:
            print(f"  {r[0]}:{r[1]} → {r[2]}:{r[3]}  ({r[4]})")
    if drifts:
        print("\n-- drift（文档说 A 行，符号实际在 B 行） --")
        for d in drifts:
            print(f"  {d[0]}:{d[1]}  {d[2]} → {d[3]} 实际 :{d[4]}   | {d[5]}")
    else:
        print("\n无 drift ✅")
    if fixups:
        total = 0
        for wpath, subs in fixups.items():
            t = open(wpath, encoding="utf-8").read()
            for old, new in subs:
                if old in t:
                    t = t.replace(old, new)
                    total += 1
            open(wpath, "w", encoding="utf-8", newline="\n").write(t)
        print(f"\n-- --fix 已改写 {total} 处（限定文件：{', '.join(sorted(FIX_ALLOW))}）--")
    return 1 if drifts else 0


if __name__ == "__main__":
    sys.exit(main())
