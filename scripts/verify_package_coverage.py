#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""包数据覆盖验收（★ 2026-09-14 B14 开关后 = **纯包内校验**，不再跑导出器）

背景（为什么改成这样）
----------------------
2026-09-14 B14 开关删掉了宿主 `game/data/*.py`（74,707 行 / 87 文件）——**包内
`content/data|rules/*.json` 成为数据唯一真源**；原来的单向导出器
`scripts/export_game_package.py`（+ `scripts/export_domains/` 域插件）随之退役，
归档在 `scripts/_retired/`（来路与语义账见 `scripts/_retired/README.md`）。

因此本门禁从「真源 → 包」的单向核对，改为**包内自洽核对**（四条，任何一条失败 → 退出码非 0）：

  1. **域清单一致**：`game.json:domains` ↔ 包声明域（`editor/domains.json`）↔ 实际数据文件；
  2. **落点正确**：每域数据文件在框架期望的落点（`editor.packages.domain_path`，按域 `kind` 落 data/rules）；
  3. **非空 + 逐条过 schema**：条数 > 0 且校验 0 无效（**静默空表** = 本项目最怕的故障）；
  4. **联想候选**：打印每域 `editor.hints` 的 refs 数（编辑器「联想」能力的覆盖）。
  另加一条**反向检查**：包内存在但清单未声明的域文件 → 报失败（防「导出到一半留下的孤儿文件」）。

用法：
    python scripts/verify_package_coverage.py            # 全量校验
    python scripts/verify_package_coverage.py --check    # 同义（保留参数兼容既有调用；本门禁自始只读，不写任何文件）

框架仓位置：$GWEN_FRAMEWORK_DIR > 默认 `C:/Users/yuyu/framework-engine`。
只读框架仓的 `games/<包>`，不起服务器、不写文件。
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                                   # 游戏仓根（本脚本所在）
FRAMEWORK = os.environ.get("GWEN_FRAMEWORK_DIR") or "C:/Users/yuyu/framework-engine"
PKG_ID = "orlandia"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="同义（保留兼容：本门禁自始只读，两种调用完全等价）")
    ap.parse_args()

    sys.path.insert(0, os.path.abspath(FRAMEWORK))
    from editor import packages as PK      # noqa: PLC0415
    from editor import hints as HN         # noqa: PLC0415

    pkg = os.path.join(os.path.abspath(FRAMEWORK), "games", PKG_ID)
    print(f"游戏仓   = {REPO}\n框架仓   = {os.path.abspath(FRAMEWORK)}\n包       = {pkg}\n"
          f"（★ B14 开关后：真源 = 包内 content/data|rules/*.json；导出器已退役，见 scripts/_retired/）")
    if not os.path.isdir(pkg):
        print(f"❌ 包目录不存在：{pkg}")
        return 1

    fails: list = []

    # ---------- 1. 域清单一致 ----------
    print("\n=== 1. 域清单：game.json:domains ↔ 包声明域 ↔ 数据文件 ===")
    declared = list(PK.declared_domain_ids(pkg))
    man = PK.load_manifest(pkg)
    man_doms = list(man.get("domains") or [])
    if sorted(declared) != sorted(man_doms):
        fails.append(f"game.json:domains 与包声明域不一致：清单独有 {sorted(set(man_doms) - set(declared))} / "
                     f"声明独有 {sorted(set(declared) - set(man_doms))}")
        print(f"  ❌ 清单 {len(man_doms)} 个 vs 声明 {len(declared)} 个")
    else:
        print(f"  ✅ 一致（{len(declared)} 个域）")
    if not declared:
        print("  ❌ 读不到任何域声明")
        return 1

    # ---------- 2~4. 逐域：落点 / 条数 / 校验 / 联想候选 ----------
    print("\n=== 2. 落点 / 条数 / 校验 / 联想候选 ===")
    hints = HN.build(pkg)
    refs = hints.get("refs") or {}
    print(f"\n  {'域':<16}{'条数':>7}{'字节':>10}  {'校验':<6}{'待修':>5}{'联想 key':>9}  落点")
    total = 0
    for d in sorted(declared):
        try:
            want = PK.domain_path(pkg, d)
        except KeyError as e:
            fails.append(f"{d} 域声明异常：{e}")
            print(f"  {d:<16}{'—':>7}{'—':>10}  {'❌':<6}{'—':>5}{'—':>9}  声明异常")
            continue
        has = os.path.isfile(want)
        st = PK.domain_status(pkg, d)
        bad = list(st.get("invalid") or [])
        ok = bool(st.get("ok")) and not bad
        cnt = int(st.get("count", 0) or 0)
        total += cnt
        loc = "rules" if os.path.basename(os.path.dirname(want)) == "rules" else "data"
        print(f"  {d:<16}{cnt:>7}{os.path.getsize(want) if has else 0:>10}  "
              f"{'✅' if ok else '❌':<6}{len(bad):>5}{len(refs.get(d) or []):>9}  content/{loc}")
        if not has:
            fails.append(f"{d} 数据文件不在框架期望的落点：{want}")
        if cnt == 0:
            fails.append(f"{d} 条数为 0（静默空表）")
        if not ok:
            fails.append(f"{d} 校验未过：{bad[:2]}")

    # ---------- 5. 反向：孤儿域文件（包内有、清单没有） ----------
    print("\n=== 3. 孤儿域文件（包内存在但清单未声明）===")
    orphans = []
    for sub in ("data", "rules"):
        for p in sorted(glob.glob(os.path.join(pkg, "content", sub, "*.json"))):
            dom = os.path.splitext(os.path.basename(p))[0]
            if dom not in set(declared):
                orphans.append(f"content/{sub}/{dom}.json")
    if orphans:
        fails.append(f"存在未声明的域文件：{orphans}")
        for o in orphans:
            print(f"  ❌ {o}")
    else:
        print("  ✅ 无孤儿（data/rules 下每个 json 都在清单里）")

    # ---------- 汇总 ----------
    print(f"\n=== 4. 汇总 ===\n  域 {len(declared)} 个 / 条目合计 {total} / 失败 {len(fails)}")
    for f in fails:
        print("  ❌", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
