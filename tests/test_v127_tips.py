# -*- coding: utf-8 -*-
"""v127 提示库数据驱动测试：TIPS 结构合规 + _tip 随机抽取行为。

覆盖：
1. TIPS 表结构：58 分类全部非空、每条 ≤20 字、无重复条目
2. common 兜底存在
3. _tip(cat) 返回带 💡 前缀且是池内条目；未知 key 回退 common 不崩
4. 所有命令层 _tip("key") 调用点使用的 key 都在 TIPS 中（防传错 key 静默回退）
"""
import os
import re
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_tips.db")

from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game.commands.base import CommandBase

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append(f"{name}: {detail}")
        print(f"❌ {name}: {detail}")
    else:
        print(f"✅ {name}")


def main():
    tips = C.TIPS
    # 1. 结构
    check("TIPS 分类数≥50", isinstance(tips, dict) and len(tips) >= 50, f"actual={len(tips)}")
    check("common 存在", "common" in tips)
    total = 0
    for k, items in tips.items():
        check(f"分类 {k} 非空", isinstance(items, list) and len(items) >= 3, f"len={len(items) if isinstance(items,list) else 'NA'}")
        if not isinstance(items, list):
            continue
        total += len(items)
        for it in items:
            check(f"{k} 条目≤20字", len(it) <= 20, f"{len(it)}字: {it}")
        check(f"{k} 无重复", len(set(items)) == len(items), f"dup={[x for x in set(items) if items.count(x)>1]}")
    print(f"  总条数: {total}")

    # 2. _tip 行为
    cb = CommandBase.__new__(CommandBase)
    for k in ("bag", "shop", "common"):
        t = cb._tip(k)
        pool = tips.get(k) or tips["common"]
        check(f"_tip({k}) 带回💡前缀", t.startswith("💡 "))
        check(f"_tip({k}) 是池内条目", t[2:] in pool, f"got={t}")
    t = cb._tip("no_such_key_xyz")
    check("_tip(未知key) 回退common", t[2:] in tips["common"], f"got={t}")
    # 随机性：同 key 抽 20 次至少出现 2 种
    seen = {cb._tip("bag") for _ in range(30)}
    check("_tip 随机抽取", len(seen) >= 2, f"seen={len(seen)}")

    # 3. 命令层调用点 key 全部存在于 TIPS（防传错 key 静默回退）
    root = os.path.dirname(os.path.abspath(C.__file__))
    cmds_dir = os.path.join(root, "..", "commands")
    used_keys = set()
    for dirpath, dirnames, filenames in os.walk(root):
        if "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            src = open(p, encoding="utf-8").read()
            for m in re.finditer(r'(?:self\._tip|world\._tip|_rand_tip)\(\s*["\']([a-z_]+)["\']', src):
                used_keys.add(m.group(1))
    missing = used_keys - set(tips.keys())
    check(f"命令层 key 全部在 TIPS（used={len(used_keys)}）", not missing, f"missing={missing}")

    # 4. item_templates 用 _rand_tip 的 key 同样覆盖
    print(f"\n总计: {sum(1 for _ in FAILS)} 失败 / 全部检查完成")
    if FAILS:
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()