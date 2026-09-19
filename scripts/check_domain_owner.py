#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""域 owner/tier 门禁（`scripts/check_domain_owner.py`）—— B15a 新建，对应计划 §9.5。

为什么需要
----------
§0 第 5 条「可迁移（插拔）」要求：任何「通用能力 / 定制能力」的位置必须**随时可翻**，
迁移 = 改一处声明 + 移文件 + 重跑冻结门禁。而「一处声明」= 包侧 `editor/domains.json`
每个域的 `owner` / `tier`；§1 铁律 1b 写明「域声明必须带 owner 标注」。
本门禁把这条从「口头约定」变成可跑的判据（三条）：

  ① **标注齐备**：`editor/domains.json` 每个域都必须有 `owner` + `tier`，取值合法；
  ② **标注自洽**（限本阶段可判定的形态）：
       · `owner=engine` 的域，其**包内域模块**禁 import 包内模块 / 宿主模块（只许引擎公开 API + 标准库）；
       · `owner=package` 的域，其**包内域模块**禁 import 宿主模块
         （`data.plugins.dragonfall.*` / `data.*` / `game.*` / 相对 `from ..` 跨出包根）。
  ③ **可迁域登记**（**不阻塞**）：`tier=portable` 的域若命中 §9.2 I3 已登记反例
     （`maps` 的 nodes/roles vs 宿主 subareas/alias、`items` 迭代序=排序键序、
     `craft` 字典序 vs 插入序），输出警告并列出 —— **I3 形状可逆性复核留 B21**（本阶段只登记，不判死）。

口径（本门禁与报告用同一套，别再发明第二套）
------------------------------------------
* `owner`: `package` = 该域的形状/模块归**数据包**；`engine` = 引擎自带域（§9.3 声明表族）。
* `tier` : `portable` = 计划承认的「通用族 / 形态与引擎既有原语同构」，将来可上移引擎（迁移前须过 I3）；
           `fixed`    = 定制族（留包），或引擎自带域（已在家、不再迁移）。
* **域模块解析**（可判定形态，逐条登记）：`content/<域>.py`、`content/**/<域>.py`（同名模块），
  外加下表 `MODULE_ALIASES`（模块名与域不同名的少数几个，来源 = 该模块自己的 docstring 声明的域）。
  一个域解析不到模块 = 纯数据域（或模块尚未拆分）→ 该域的检查记 `N/A（无单域模块）`，
  **打印出来、不静默跳过**。

用法
----
    python scripts/check_domain_owner.py            # 全量
    python scripts/check_domain_owner.py --check    # 同义（本项目门禁惯例；本门禁自始只读）

框架仓位置：`$GWEN_FRAMEWORK_DIR` > 默认 `C:/Users/yuyu/framework-engine`（与
`scripts/verify_package_coverage.py` 同口径）；只读，不写任何文件。
退出码：0 = 全过；1 = 有失败项。
"""
from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FRAMEWORK = os.environ.get("GWEN_FRAMEWORK_DIR") or "C:/Users/yuyu/framework-engine"
PKG_ID = "orlandia"

OWNERS = ("package", "engine")
#: **横切读口白名单** —— 任何域模块都允许 import 它（提供的是全包基础设施，不是某域业务）。
#: 加新条目**必须先说明它为什么是横切能力**，别当止痛药用。
#: · content/texts.py：文案表读口（B-2 批起硬编码中文句句壳统一收进 text_specs.json）。
CROSS_DOMAIN_READERS = ("texts",)
TIERS = ("portable", "fixed")

# 域 → 模块（模块名与域不同名的少数几个；依据 = 该模块 docstring 自述的域）
MODULE_ALIASES = {
    "affixes": ["content/affix.py"],                       # 词条域门面（单数名）
    "dialogues": ["content/dialogue.py"],                  # 多轮对话引擎
    "fishing_spots": ["content/fishing.py"],               # 钓点/鱼种池同属 fishing
    "fishing_pool": ["content/fishing.py"],
    "drop_pools": ["content/loot.py"],                     # 掉落策略/解析器半边
    "tlogs": ["content/tlog_collect.py"],                  # 战斗流水采集半边
}

# 宿主模块形态（绝对名 + 相对跨出包根）
HOST_ABS_PREFIXES = ("data.plugins", "data.", "game.", "plugin.", "plugins.")
# 包内模块形态（绝对名 + 包内相对）
INTERNAL_ABS_PREFIXES = ("content",)

# §9.2 I3 已登记反例（tier=portable 的域命中即**警告**，不阻塞）
# ★ 2026-09-20 摘除 `craft`：插入序真源已显式保存在 `content/data/key_order.json`
#   （读口 `catalog_life.py:335 CRAFT_RECIPES = _ordered(_CRAFT_STRIPPED, _ORDER_CRAFT_RECIPES)`），
#   实测 `list(C.CRAFT_RECIPES) == key_order.craft.keys`（== 插入序）、`!= sorted(...)` ⇒
#   「字典序 vs 插入序」**已可逆**，不再是反例。
KNOWN_I3 = {
    "maps": "`nodes`/`roles` vs 宿主 `subareas`/`alias`（形状已对齐引擎 `Space`，但不能还原宿主键名 ⇒ 单向派生；遍历点均显式排序/去重 ⇒ 影响 0）",
    "items": "迭代序 = 排序键序（宿主是插入序）：**无 key_order 声明** ⇒ 顺序真源已丢；实测 900 条**重名 0 组** ⇒ 唯一性/取值类读点不受影响",
}


def imports_of(path: str):
    """AST 扫该模块的 import 形态 → [(kind, name)]，kind ∈ {abs, rel1, rel2+}。"""
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out += [("abs", a.name) for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            lvl = n.level or 0
            kind = "rel%d" % lvl if lvl else "abs"
            if n.module:
                out.append((kind, n.module))
            else:
                #  ★ 2026-09-19 修：`from .. import texts as _T` 的 `n.module is None`，
                #   被名字在 `n.names` 里 —— 旧写法记成 `from .. import *`（信息失真，
                #   且让横切白名单永远匹配不上）。逐个别名取。
                out += [(kind, a.name) for a in n.names]
    return out


def module_candidates(pkg: str, dom: str):
    """该域在包内的候选模块（可判定形态）：同名模块 + 别名表。"""
    cands = []
    cands += [os.path.relpath(p, pkg).replace("\\", "/")
              for p in glob.glob(os.path.join(pkg, "content", "**", dom + ".py"), recursive=True)]
    cands += list(MODULE_ALIASES.get(dom, []))
    seen, out = set(), []
    for c in cands:
        if c not in seen and os.path.isfile(os.path.join(pkg, c)):
            seen.add(c)
            out.append(c)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="同义（本项目门禁惯例；本门禁自始只读）")
    ap.parse_args()

    pkg = os.path.join(os.path.abspath(FRAMEWORK), "games", PKG_ID)
    decl = os.path.join(pkg, "editor", "domains.json")
    print(f"游戏仓   = {REPO}\n框架仓   = {os.path.abspath(FRAMEWORK)}\n包       = {pkg}\n域声明   = {decl}\n")
    if not os.path.isfile(decl):
        print(f"❌ 域声明文件不存在：{decl}")
        print(f"❌ 域 owner/tier：0 域全标注 / 失败 1")
        return 1

    raw = json.load(open(decl, encoding="utf-8"))
    fails: list = []

    # ─────────── ① 标注齐备 + 取值合法 ───────────
    print("=== 1. 标注齐备（每域必须有 owner + tier，取值合法）===")
    no_owner, no_tier, bad_owner, bad_tier = [], [], [], []
    for dom, meta in raw.items():
        if not isinstance(meta, dict):
            fails.append(f"{dom} 声明形状不对（需为对象）")
            continue
        if "owner" not in meta:
            no_owner.append(dom)
        elif meta["owner"] not in OWNERS:
            bad_owner.append(f"{dom}={meta['owner']!r}")
        if "tier" not in meta:
            no_tier.append(dom)
        elif meta["tier"] not in TIERS:
            bad_tier.append(f"{dom}={meta['tier']!r}")
    for label, lst in (("缺 owner", no_owner), ("缺 tier", no_tier),
                       ("owner 取值非法", bad_owner), ("tier 取值非法", bad_tier)):
        if lst:
            fails.append(f"{label}：{lst}")
            print(f"  ❌ {label}（{len(lst)}）：{lst}")
        else:
            print(f"  ✅ {label}：0")
    print(f"  · 域 {len(raw)} 个 / owner {{package: {sum(1 for m in raw.values() if isinstance(m, dict) and m.get('owner') == 'package')}"
          f", engine: {sum(1 for m in raw.values() if isinstance(m, dict) and m.get('owner') == 'engine')}}}"
          f" / tier {{portable: {sum(1 for m in raw.values() if isinstance(m, dict) and m.get('tier') == 'portable')}"
          f", fixed: {sum(1 for m in raw.values() if isinstance(m, dict) and m.get('tier') == 'fixed')}}}")

    # ─────────── ② 标注自洽（域模块的 import 面） ───────────
    print("\n=== 2. 标注自洽（owner 与包内域模块的 import 面对得上）===")
    checked, na, viol = 0, [], []
    for dom in sorted(raw):
        meta = raw[dom]
        owner = meta.get("owner") if isinstance(meta, dict) else None
        if owner not in OWNERS:
            print(f"  {dom:<24} 跳过（owner 缺失/非法 —— 见第 1 节）")
            continue
        mods = module_candidates(pkg, dom)
        if not mods:
            na.append(dom)
            continue
        for rel in mods:
            checked += 1
            kinds = imports_of(os.path.join(pkg, rel))
            bad = []
            for kind, name in kinds:
                if kind == "rel1":
                    if name in CROSS_DOMAIN_READERS:    # ★ 横切读口不判违规
                        continue
                    internal = True
                elif kind.startswith("rel"):
                    if name in CROSS_DOMAIN_READERS:    # ★ 横切读口（`from .. import texts`）不判违规
                        continue
                    internal, hostish = False, True          # from .. = 跨出包根
                    bad.append(f"{rel}: `from .. import {name or '*'}`（相对跨出包根）")
                    continue
                else:
                    internal = name.split(".")[0] in INTERNAL_ABS_PREFIXES
                    hostish = name.startswith(HOST_ABS_PREFIXES)
                    if hostish:
                        bad.append(f"{rel}: `import {name}`（宿主模块）")
                        continue
                if internal and owner == "engine":
                    bad.append(f"{rel}: `{('from .' if kind == 'rel1' else 'import')} "
                               f"{name or ''}`（engine 域模块不得 import 包内模块）")
            if bad:
                viol.append((dom, rel, bad))
                for b in bad:
                    print(f"  ❌ {dom}（owner={owner}）{b}")
            else:
                print(f"  ✅ {dom:<24} owner={owner:<7} {','.join(mods)} → 只依赖引擎/标准库/包内同域")
    if not viol:
        print(f"  ✅ 无不自洽（已判 %d 个域模块 / %d 个纯数据域记 N/A）" % (checked, len(na)))
    else:
        fails.append("标注自洽违规：%s" % [(d, m) for d, m, _ in viol])
    print(f"  · N/A（无单域模块，检查不适用）：{len(na)} 域 → {', '.join(na) if na else '（无）'}")

    # ─────────── ③ 可迁域登记（不阻塞） ───────────
    print("\n=== 3. tier=portable 的 I3 可逆性登记（**警告，不阻塞**）===")
    hit_i3, clean = [], []
    for dom in sorted(raw):
        meta = raw[dom]
        if not isinstance(meta, dict) or meta.get("tier") != "portable":
            continue
        if dom in KNOWN_I3:
            hit_i3.append(dom)
            print(f"  ⚠ {dom}（portable）：{KNOWN_I3[dom]}")
        else:
            clean.append(dom)
    print(f"  · 命中已登记反例 {len(hit_i3)} 域：{', '.join(hit_i3) if hit_i3 else '（无）'}")
    print(f"  · 其余 portable {len(clean)} 域：无已登记反例（**不等于已验可逆** —— I3 形状可逆性复核留 B21**）")

    # ─────────── 汇总 ───────────
    n_owner = sum(1 for m in raw.values() if isinstance(m, dict) and m.get("owner") in OWNERS)
    n_tier = sum(1 for m in raw.values() if isinstance(m, dict) and m.get("tier") in TIERS)
    print(f"\n=== 4. 汇总 ===\n  域 {len(raw)} 个 / owner 齐 {n_owner} / tier 齐 {n_tier}"
          f" / 已判域模块 {checked} / N/A {len(na)} / I3 警告 {len(hit_i3)} / 失败 {len(fails)}")
    for f in fails:
        print("  ❌", f)
    if fails:
        print(f"❌ 域 owner/tier：{len(raw)} 域 / 失败 {len(fails)}")
        return 1
    print(f"✅ 域 owner/tier：{len(raw)} 域全标注 / 失败 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
