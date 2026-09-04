# -*- coding: utf-8 -*-
"""v175 R 系列 apply：按 r1_fix_gen 生成的 JSON 精确改 skills.py 的 exprs ratio + desc。

只改两处：
  1. exprs 数组第一行的 (atk|matk)*X 系数 → 新 ratio（技能 name 定位）
  2. desc 里 "XX% 物理/魔法攻击" 的百分比 → 新 ratio×100（含真伤文案）
power 旧字段不动（已不参与伤害计算，v161 exprs 优先）。

用法：python scripts/build_matrix/r1_fix_apply.py /tmp/r1_fixes.json
"""
from __future__ import annotations
import os, sys, json, re

_PLUGIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
for _p in (_QQBOT, _PLUGIN):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN, "tests", "test_game_data.db"))

SKILLS_FILE = os.path.join(_PLUGIN, "game", "data", "skills.py")


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r1_fixes.json"
    with open(json_path, encoding="utf-8") as f:
        fixes = json.load(f)
    with open(SKILLS_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    total_changed = 0
    skipped = []
    for cid, flist in fixes.items():
        for f in flist:
            nm = f["name"]
            stat = f.get("stat", "atk")
            old_r = f["old_ratio"]
            new_r = f["new_ratio"]
            # 找技能定义块（name 行往上找 exprs）
            name_line = None
            for i, ln in enumerate(lines):
                if f"'name': '{nm}'" in ln or f'"name": "{nm}"' in ln:
                    name_line = i
                    break
            if name_line is None:
                skipped.append(f"{nm}: name 未找到")
                continue
            # 从 name 行向上 20 行内找该技能 expr 行（含旧 ratio 的 exprs）
            expr_line = None
            for i in range(max(0, name_line - 25), name_line):
                if "exprs" in lines[i] and f"{stat}*{old_r}" in lines[i]:
                    expr_line = i
                    break
            if expr_line is None:
                # 可能 exprs 在 name 之后（少见）→ 向下找
                for i in range(name_line, min(len(lines), name_line + 25)):
                    if "exprs" in lines[i] and f"{stat}*{old_r}" in lines[i]:
                        expr_line = i
                        break
            if expr_line is None:
                skipped.append(f"{nm}: expr 行未找到 (old={stat}*{old_r})")
                continue
            # 替换该行 ratio
            new_expr_line = lines[expr_line].replace(f"{stat}*{old_r}", f"{stat}*{new_r}")
            if new_expr_line == lines[expr_line]:
                skipped.append(f"{nm}: 替换无变化")
                continue
            lines[expr_line] = new_expr_line
            # desc 百分比同步：找 desc 行（name 行附近）里 "OLD% 物理/魔法攻击"
            pct_old = int(round(old_r * 100))
            pct_new = int(round(new_r * 100))
            desc_line = None
            for i in range(max(0, name_line - 5), min(len(lines), name_line + 8)):
                if "desc" in lines[i] and f"{pct_old}%" in lines[i]:
                    desc_line = i
                    break
            if desc_line is not None:
                # 只替换百分比数字（防止误伤 +301 固定伤害等）
                lines[desc_line] = re.sub(
                    rf"({pct_old})%", f"{pct_new}%", lines[desc_line], count=1)
            total_changed += 1
            print(f"✅ {nm}: {stat}*{old_r} → {stat}*{new_r} ({cid})")

    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\n== 改动 {total_changed} 个技能 ==")
    if skipped:
        print(f"⚠️ 跳过 {len(skipped)}:")
        for s in skipped[:15]:
            print(f"  {s}")


if __name__ == "__main__":
    main()
