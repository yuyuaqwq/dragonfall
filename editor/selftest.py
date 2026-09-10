#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""编辑器只读自检：解析 → 校验 → 分组 → key 往返。**不写任何文件**。

    python editor/selftest.py

退出码 0 = 全部通过。用于快速确认编辑器数据层与 schema 判据一致。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_io  # noqa: E402

FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    mark = "✅" if cond else "❌"
    if not cond:
        FAIL += 1
    print(f"  {mark} {name}" + (f"  — {detail}" if detail else ""))


def main():
    print("== 编辑器数据层自检 ==")
    print(f"  校验器引擎 : {data_io.validator_engine()}")
    print(f"  数据来源   : {data_io.source_info()['source']}")

    tables = data_io.parse_source_tables()
    entries = data_io.iter_entries(tables)
    check("解析出技能条目", len(entries) > 0, f"{len(entries)} 条")
    check("三张表齐全", set(tables) == set(data_io.TABLES), str(sorted(tables)))

    bad = []
    for e in entries:
        _m, d = data_io.get_skill(e["key"])
        if d is None:
            bad.append((e["key"], "解析不到"))
            continue
        res = data_io.validate_skill(d)
        if not res["ok"]:
            bad.append((e["key"], res["errors"][:1]))
    check("现网技能全部过 schema", not bad, f"{len(bad)} 条违规" if bad else "0 违规")
    for k, v in bad[:5]:
        print("      !!", k, v)

    # key 往返：每个 key 都能解析回同一条数据
    rt = 0
    for e in entries:
        _m, d = data_io.get_skill(e["key"])
        if d is not None and d.get("name") == e["name"]:
            rt += 1
    check("key 往返一致", rt == len(entries), f"{rt}/{len(entries)}")

    # 非法值必须被拦下
    _m, sample = data_io.get_skill(entries[0]["key"])
    dirty = dict(sample, kind="不存在的职业")
    check("非法 kind 被拦下", not data_io.validate_skill(dirty)["ok"],
          str(data_io.validate_skill(dirty)["errors"][:1]))

    # diff
    d = data_io.diff_values({"a": 1, "b": {"c": 2}}, {"a": 2, "b": {"c": 2}})
    check("diff 定位到字段", len(d) == 1 and d[0]["path"] == "a", str(d))

    payload = data_io.list_payload()
    check("列表分组非空", payload["total"] == len(entries), f"total={payload['total']}")

    print(f"\n结论: {'全绿 ✅' if FAIL == 0 else f'{FAIL} 项失败 ❌'}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
