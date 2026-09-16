# -*- coding: utf-8 -*-
"""生成/校验指令表快照：`tests/_command_table_freeze.json`。

用法：
  python scripts/command_table_freeze.py            # 校验当前有效表 == 快照
  python scripts/command_table_freeze.py --write    # 写入快照（**有意变更契约时**才用，写清理由）

有效表口径（★ P5F-REPOINT 后）：**包内声明表** `content/data/commands.json` → `{key: 合并正则}`。
原实现 direct-载 宿主 `game/commands/_registry.py`，该文件随删壳批消失 —— 声明真源已在包内，
本脚本随之改为按**同一口径**从包内派生（与 `tests/test_v185_command_migration.py::load_command_table`
逐字同款：单条正则原样、多条 → `(?:a)|(?:b)`）。
"""
import glob
import hashlib
import json
import os
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(PLUGIN, "tests", "_command_table_freeze.json")
NOTE = ("指令表冻结快照（有效表 = 包内声明表 `content/data/commands.json` 派生的 "
        "`{key: 合并正则}`）：此后**逐字相等**；有意变更（如新增命令）须显式重跑本脚本 --write 并说明理由。")


def _find_spec():
    """包内声明表路径（不写死包名：framework/games/* 里带 game.json 的那个）。"""
    cands = sorted(glob.glob(os.path.join(PLUGIN, "framework", "games", "*",
                                          "content", "data", "commands.json")))
    cands = [c for c in cands if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(c))), "game.json"))]
    if len(cands) != 1:
        raise SystemExit("无法唯一定位包内声明表（找到 %d 个）：%s" % (len(cands), cands))
    return cands[0]


def _combine(pats):
    pats = [p for p in (pats or ()) if p]
    if not pats:
        return ""
    if len(pats) == 1:
        return pats[0]
    return "|".join("(?:%s)" % p for p in pats)


def load_table():
    with open(_find_spec(), encoding="utf-8") as f:
        specs = json.load(f)
    out = {}
    for k, v in specs.items():
        pats = v.get("patterns", v.get("pattern")) if isinstance(v, dict) else v
        if isinstance(pats, str):
            pats = [pats]
        c = _combine(pats or [])
        if c:
            out[str(k)] = c
    return out


table = {k: v for k, v in sorted(load_table().items())}
blob = json.dumps(table, ensure_ascii=False, sort_keys=True)
digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()

if "--write" in sys.argv:
    payload = {"sha256": digest, "count": len(table), "note": NOTE, "table": table}
    with open(SNAP, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print("written:", SNAP, len(table), digest)
    sys.exit(0)

old = json.load(open(SNAP, encoding="utf-8"))
old_table = old["table"]
diff = [(k, old_table.get(k), table.get(k)) for k in set(old_table) | set(table)
        if old_table.get(k) != table.get(k)]
print("有效表:", len(table), "快照:", len(old_table), "差异:", len(diff))
for k, a, b in sorted(diff)[:20]:
    print("  ", k, "\n    旧:", a, "\n    新:", b)
print("sha:", digest, "==" if digest == old["sha256"] else "!= 快照", old["sha256"])
sys.exit(1 if diff or digest != old["sha256"] else 0)
