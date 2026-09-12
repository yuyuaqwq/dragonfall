# -*- coding: utf-8 -*-
"""生成/校验指令表快照：`tests/_command_table_freeze.json`。

用法：
  python scripts/command_table_freeze.py            # 校验当前有效表 == 快照（迁移期间必须一直相等）
  python scripts/command_table_freeze.py --write    # 写入快照（**只在迁移开始前用**）
"""
import hashlib
import importlib.util
import json
import os
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_DIR = os.path.join(PLUGIN, "game", "commands")
SNAP = os.path.join(PLUGIN, "tests", "_command_table_freeze.json")

spec = importlib.util.spec_from_file_location("_reg", os.path.join(CMD_DIR, "_registry.py"))
reg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg)

table = {k: v for k, v in sorted(reg.COMMAND_REGEX.items())}
blob = json.dumps(table, ensure_ascii=False, sort_keys=True)
digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()

if "--write" in sys.argv:
    payload = {"sha256": digest, "count": len(table),
               "note": "指令表迁移（路线图 #9）冻结快照：有效表逐字不变即迁移无行为变化。",
               "table": table}
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
