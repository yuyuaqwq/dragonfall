# -*- coding: utf-8 -*-
"""S9-2 修正：`game/` 包内新插入的绝对 `from game.… import …` → 相对导入。

为什么必须改：本仓库并存两套 import 路径（plan §8-R2）——
  * 裸式   `from game import content`           （插件根在 sys.path 上）
  * 包式   `from data.plugins.dragonfall.game import content`（生产/部分测试）
包内文件用**绝对** `from game.…` 时，包式路径下顶层 `game` 未必可导入 → 
`ModuleNotFoundError: No module named 'game'`。包内一律用相对导入即可两套通吃。

换算：当前文件包 P（如 ['game','commands']）→ 目标模块 T（如 game.content_rules.panel）
  共同前缀 common → 点数 = (len(P) - common) + 1

范围：仅 `game/` 下（tests / tools / editor / scripts 保持绝对——它们自己把插件根加进
sys.path，且刻意共用同一模块树）。

用法：python tools/s9_relativize_game_imports.py [--apply]
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(REPO, "game")
SKIP_DIRS = {"__pycache__"}
PAT = re.compile(r"(?m)^([ \t]*)(from\s+)game(\.?[\w.]*\s+import\s+[^\n#]+)")


def dots_for(rel_path: str, target: str) -> str:
    """rel_path 相对 REPO（game/...）；target 形如 'game.content_rules.panel'。"""
    pkg = rel_path.split("/")[:-1]                     # ['game','commands']
    tparts = target.split(".")
    common = 0
    while common < min(len(pkg), len(tparts)) and pkg[common] == tparts[common]:
        common += 1
    up = len(pkg) - common
    return "." * (up + 1)


def main(argv):
    apply = "--apply" in argv
    changed = []
    for dp, dn, fs in os.walk(GAME):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in sorted(fs):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, REPO).replace("\\", "/")
            text = open(p, encoding="utf-8", newline="").read()

            def repl(m):
                indent, ffrom, rest = m.group(1), m.group(2), m.group(3)
                # rest 形如 '.content_rules.panel import X' 或 ' import X'
                sub = rest.strip()
                if sub.startswith("import"):
                    target = "game"
                    tail = sub
                else:
                    mod, _, tail_import = sub.partition(" import ")
                    target = "game" + mod.strip()
                    tail = "import " + tail_import
                dots = dots_for(rel, target)
                tparts = target.split(".")
                pkg = rel.split("/")[:-1]
                common = 0
                while common < min(len(pkg), len(tparts)) and pkg[common] == tparts[common]:
                    common += 1
                remainder = ".".join(tparts[common:])
                head = f"{indent}{ffrom}{dots}{remainder + ' ' if remainder else ''}{tail}"
                return head

            new, n = PAT.subn(repl, text)
            if n:
                changed.append((rel, n))
                if apply:
                    open(p, "w", encoding="utf-8", newline="").write(new)
    print(f"{'已改写' if apply else 'DRY-RUN'}：{len(changed)} 个文件")
    for rel, n in changed:
        print(f"   {rel}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
