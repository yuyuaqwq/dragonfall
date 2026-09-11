# -*- coding: utf-8 -*-
"""S9-1：`X.load_game_defaults()` → 内容侧单一入口 `ensure_engine_configured()`。

背景（S8 拆仓暴露的真实耦合）：
老路径 `from game.battle2 import config as _b2c` 会**顺带 import `game` 包**
（`game/__init__.py` 的 `install()` 把内容侧默认装载器登记进引擎 config）；
新路径 `from saintess_engine import config as _b2c` 不再 import `game` → 紧接着的
`_b2c.load_game_defaults()` 变成 **空调用**（R8 静默降级：引擎 config 的
`_defaults_loader` 为 None 时静默什么都不做）。

干净修法（同时是 S9 收口目标）：引擎不再保留 `load_game_defaults` 这类
**游戏概念 API**；调用方改走内容侧单一装配入口
`game.content_rules.apply.ensure_engine_configured()`（S7 已建立，语义等价）。

替换形态：把调用行整行换成
    from game.content_rules.apply import ensure_engine_configured as _eng_cfg; _eng_cfg()
—— 单行、任意作用域合法（含函数内）、可 grep、不依赖顶部 import 排布。

用法：python tools/split_engine_imports2_lgd.py [--apply]
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"_archive_unused", "__pycache__", ".git", ".pytest_cache",
        "_retired_old_engine", "node_modules", "design", "docs", "audit", "framework"}

CALL = re.compile(r"^(?P<indent>[ \t]*)(?P<alias>[A-Za-z_][\w]*)\.load_game_defaults\(\)"
                  r"(?P<tail>[ \t]*(?:#.*)?)$")
NEW = ("{indent}from game.content_rules.apply import ensure_engine_configured as _eng_cfg; "
       "_eng_cfg(){tail}")

apply = "--apply" in sys.argv
total = 0
files = 0
for dirpath, dirnames, filenames in os.walk(REPO):
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in sorted(filenames):
        if not fn.endswith(".py") or fn.startswith("_survey") or fn.startswith("_dbg"):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, REPO).replace("\\", "/")
        if rel.startswith("tools/split_engine_imports"):
            continue
        text = open(p, encoding="utf-8", newline="").read()
        if "load_game_defaults()" not in text:
            continue
        out, n = [], 0
        for ln in text.splitlines(keepends=True):
            body = ln.rstrip("\r\n")
            nl = ln[len(body):]
            m = CALL.match(body)
            if m:
                out.append(NEW.format(indent=m.group("indent"), tail=m.group("tail")) + nl)
                n += 1
            else:
                out.append(ln)
        if n:
            total += n
            files += 1
            print(f"  {rel}: {n} 处")
            if apply:
                open(p, "w", encoding="utf-8", newline="").write("".join(out))
print(f"\n{'已改写' if apply else 'DRY-RUN'}：{total} 处调用 / {files} 个文件")
