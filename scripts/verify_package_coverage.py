#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导出覆盖验收：把游戏仓真源逐域导出 → 核对「条数 / 校验 / 联想候选」是否都进了编辑器。

用法：
    python scripts/verify_package_coverage.py            # 全量（逐域导出 + --check + 编辑器侧核对）
    python scripts/verify_package_coverage.py --check    # 不落盘，只核对现有包

它做四件事（任何一项失败 → 退出码非 0）：
  1. 逐域跑导出器（域列表从导出器源码的 DERIVERS 读，不手写第二份）；
  2. 每个域 --check 必须报「与真源一致」；
  3. 编辑器侧：清单 domains 与已实现域一致、每域有数据文件（**按框架 domain_path 的落点**）、
     每域条数 > 0 且逐条过 schema（静默空表 = 本项目最怕的故障）；
  4. 打印每域的联想候选数（hints.refs）。

只读两个仓（除导出器自身的落盘职责外不写任何文件），不起服务器。
框架仓位置：$GWEN_FRAMEWORK_DIR > 导出器的 DEFAULT_FRAMEWORK_DIR。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                                   # 游戏仓根
EXPORT = os.path.join(HERE, "export_game_package.py")
FRAMEWORK = os.environ.get("GWEN_FRAMEWORK_DIR") or "C:/Users/yuyu/framework-engine"
PKG_ID = "orlandia"
PLUGIN_ERRORS: list = []          # 域插件加载失败（由 _derivers() 填；main 计入失败）


def _derivers() -> list:
    """已实现的域 —— **执行导出器模块**读它的 `DERIVERS`（字面量 + `scripts/export_domains/` 插件域）。

    为什么不再爬源码字面量：域注册表自 2026-09-13 起是**运行期合并**的（支持域插件），
    爬字面量会让插件域在门禁里“看不见”= 静默漏域；插件加载失败也记进 DOMAIN_PLUGIN_ERRORS
    由 main() 计入失败（不静默）。顺带记录模块级错误供 main 使用。
    """
    import importlib.util
    global PLUGIN_ERRORS
    for _p in (REPO, HERE):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    spec = importlib.util.spec_from_file_location("_xp_coverage_export", EXPORT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_xp_coverage_export"] = mod
    spec.loader.exec_module(mod)
    PLUGIN_ERRORS = list(getattr(mod, "DOMAIN_PLUGIN_ERRORS", []) or [])
    return sorted(mod.DERIVERS)


def _run_cli(*args) -> tuple:
    r = subprocess.run([sys.executable, EXPORT, *args], cwd=REPO, capture_output=True, text=True)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只核对现有包，不重新导出")
    args = ap.parse_args()

    sys.path.insert(0, os.path.abspath(FRAMEWORK))
    from editor import packages as PK      # noqa: PLC0415
    from editor import hints as HN         # noqa: PLC0415

    pkg = os.path.join(os.path.abspath(FRAMEWORK), "games", PKG_ID)
    doms = _derivers()
    fails: list = [f"域插件加载失败（该域没有被导出，按失败计）：{e}" for e in PLUGIN_ERRORS]
    print(f"游戏仓 = {REPO}\n框架仓 = {os.path.abspath(FRAMEWORK)}\n导出器已实现的域：{doms}")
    if not doms:
        print("❌ 读不到已实现的域（DERIVERS 解析失败）")
        return 1

    print("\n=== 1. 逐域导出 + --check 与真源一致 ===")
    for d in doms:
        if not args.check:
            rc, out = _run_cli("--domain", d)
            print(f"  {'✅' if rc == 0 else '❌'} 导出 {d:<14} {out.splitlines()[0] if out else ''}")
            if rc != 0:
                fails.append(f"导出 {d} 失败：{out[:200]}")
        rc2, out2 = _run_cli("--domain", d, "--check")
        ok2 = rc2 == 0 and "不一致" not in out2
        print(f"     {'✅' if ok2 else '❌'} --check {d}")
        if not ok2:
            fails.append(f"{d} --check 不一致：{out2[:200]}")

    print("\n=== 2. 编辑器侧：落点 / 条数 / 校验 / 联想候选 ===")
    man = PK.load_manifest(pkg)
    declared = man.get("domains") or []
    if sorted(declared) != sorted(doms):
        fails.append(f"清单 domains({declared}) 与已实现域({doms}) 不一致")
    hints = HN.build(pkg)
    refs = hints.get("refs") or {}
    print(f"\n  {'域':<14}{'条数':>7}{'字节':>10}  {'校验':<6}{'待修':>5}{'联想 key':>9}  落点")
    for d in declared:
        want = PK.domain_path(pkg, d)
        has = os.path.isfile(want)
        st = PK.domain_status(pkg, d)
        ok = bool(st.get("ok")) and not (st.get("invalid") or [])
        print(f"  {d:<14}{st.get('count', 0):>7}{os.path.getsize(want) if has else 0:>10}  "
              f"{'✅' if ok else '❌':<6}{len(st.get('invalid') or []):>5}{len(refs.get(d) or []):>9}  "
              f"{'content/' + ('rules' if 'rules' in want.replace(chr(92), '/') else 'data')}")
        if not has:
            fails.append(f"{d} 数据文件不在框架期望的落点：{want}")
        if not st.get("count"):
            fails.append(f"{d} 条数为 0（静默空表）")
        if not ok:
            fails.append(f"{d} 校验未过：{(st.get('invalid') or [])[:2]}")

    total = sum(PK.domain_status(pkg, d).get("count", 0) for d in declared)
    print(f"\n=== 3. 汇总 ===\n  域 {len(declared)} 个 / 条目合计 {total} / 失败 {len(fails)}")
    for f in fails:
        print("  ❌", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
