# -*- coding: utf-8 -*-
"""S8/S9 拆仓改造：游戏侧对引擎包的引用从 `game.battle2` 改为裸包 `saintess_engine`。

背景（docs/ENGINE_CONTENT_SPLIT_PLAN.md §7.5 / FRAMEWORK_SPLIT_PLAN.md S8-S9）：
引擎包物理分离到框架仓库（dragonfall 侧 `framework/` 为 submodule，内含 `saintess_engine/`），
游戏侧不再走 `game.battle2` 这个包内路径 —— 改为直接依赖框架包名 `saintess_engine`
（符合「重构改干净、不留兼容壳」铁律，S9 删 shim 后的终态）。

本脚本做两类改写（dry-run 默认，`--apply` 落盘）：
  1. 代码引用：`game.battle2` → `saintess_engine`
  2. 路径文案：`game/battle2` → `framework/saintess_engine`（注释/docstring 里的路径提法）

sys.path 接线（框架根 = `<plugin>/framework`，包名 `saintess_engine`）：
  * `game/__init__.py` —— 游戏运行时（命令层/服务层），手工接线
  * 测试：凡定义了 `PLUGIN_DIR`/`_PLUGIN_DIR` 的文件，在其定义行后自动补一行
    `sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))`（锚点最通用：
    比 `sys.path.insert(0, PLUGIN_DIR)` 更普适 —— 后者写法不一，前者几乎恒有）
  * 既无 PLUGIN_DIR 又 import saintess_engine 的（走 conftest 的）由 conftest 覆盖，
    `--report-orphan` 列出需人工确认的

不改动对象：
  * `game/battle2/`（引擎本体，迁框架仓；其路径文案由框架仓内改写）
  * `examples/` `schema/` `editor/`（随框架归位，在框架仓内改写）
  * `_archive_unused/` `tests/_retired_old_engine/`（归档/退役）
  * 本脚本自身与 `_tmp_*.py` 临时探针

用法：
    python tools/split_engine_imports.py                      # dry-run
    python tools/split_engine_imports.py --apply              # 落盘
    python tools/split_engine_imports.py --report-orphan      # 只列需手工接线的文件
"""
from __future__ import annotations

import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {"_archive_unused", "__pycache__", ".git", ".pytest_cache",
             "_retired_old_engine", "node_modules", ".workdir",
             "design", "docs", "audit"}

# 这些子树随「框架归位」在框架仓内改，不在本次 dragonfall 范围内
DEFER_DIRS = ("examples/", "schema/", "editor/", "game/battle2/", "framework/")

SELF_SKIP = {"tools/split_engine_imports.py"}

# 注入锚点：PLUGIN_DIR / _PLUGIN_DIR 的定义行（注入点在其后）
ANCHOR = re.compile(r"^(?P<indent>[ \t]*)(?P<var>_?PLUGIN_DIR)\s*=\s*os\.path\.dirname\(")
INJECT = ('{indent}sys.path.insert(0, os.path.join({var}, "framework"))  '
          '# 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）')


def iter_py(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py") and not fn.startswith("_tmp_"):
                yield os.path.join(dirpath, fn)


def _inject_framework_path(text: str) -> tuple:
    """在 PLUGIN_DIR 定义行后补框架根 sys.path 接线。返回 (新文本, 是否注入)。"""
    if 'os.path.join(PLUGIN_DIR, "framework")' in text \
            or 'os.path.join(_PLUGIN_DIR, "framework")' in text:
        return text, False
    lines = text.splitlines(keepends=True)
    out = []
    done = False
    for ln in lines:
        out.append(ln)
        if done:
            continue
        m = ANCHOR.match(ln)
        if m:
            nl = "\r\n" if ln.endswith("\r\n") else "\n"
            out.append(INJECT.format(indent=m.group("indent"), var=m.group("var")) + nl)
            done = True
    return ("".join(out), True) if done else (text, False)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report-orphan", action="store_true")
    ap.add_argument("--no-inject", action="store_true")
    args = ap.parse_args(argv)

    rows, orphans, inj_rows = [], [], []
    tot_code = tot_path = 0
    for p in sorted(iter_py(REPO)):
        rel = os.path.relpath(p, REPO).replace("\\", "/")
        if rel in SELF_SKIP or rel.startswith(DEFER_DIRS):
            continue
        try:
            text = open(p, encoding="utf-8", newline="").read()
        except (OSError, UnicodeDecodeError):
            continue
        has_code = "game.battle2" in text
        has_path = "game/battle2" in text
        if not has_code and not has_path:
            continue
        new = text.replace("game.battle2", "saintess_engine") \
                  .replace("game/battle2", "framework/saintess_engine")
        # 测试/工具/根级入口：补框架根接线（game/ 侧由 __init__ 负责）
        injected = False
        if not args.no_inject and (rel.startswith("tests/") or rel.startswith("tools/")
                                   or "/" not in rel):
            new, injected = _inject_framework_path(new)
        rows.append((rel, text.count("game.battle2"), text.count("game/battle2")))
        if injected:
            inj_rows.append(rel)
        tot_code += text.count("game.battle2")
        tot_path += text.count("game/battle2")
        # 孤儿判定：引用引擎但既不 import game.* 也不借道 conftest
        if has_code and not rel.startswith("game/"):
            import re
            if not re.search(r"^\s*(from|import)\s+(game\.|data\.plugins\.|conftest)",
                             text, re.M) and rel != "tests/conftest.py":
                orphans.append(rel)
        if args.apply:
            open(p, "w", encoding="utf-8", newline="").write(new)

    if args.report_orphan:
        print(f"=== 需手工 sys.path 接线的文件（{len(orphans)}）===")
        for r in orphans:
            print("   ", r)
        return 0

    for rel, nc, npq in rows:
        print(f"  {rel:58s} code={nc:3d} path={npq:2d}"
              f"{'  +sys.path' if rel in inj_rows else ''}")
    print(f"\n{'改写落盘' if args.apply else 'DRY-RUN'} | 文件 {len(rows)} | "
          f"代码引用 {tot_code} | 路径文案 {tot_path} | sys.path 注入 {len(inj_rows)}")
    if orphans:
        print(f"⚠️ 需手工接线的孤儿文件 {len(orphans)} 个（--report-orphan 看清单）")
    if not args.apply:
        print("（加 --apply 落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
