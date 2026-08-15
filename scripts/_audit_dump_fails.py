# -*- coding: utf-8 -*-
import json
d = json.load(open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/scripts/_audit_regression_result.json", encoding="utf-8"))
for x in d:
    if not x["ok"]:
        print("=" * 20 + " " + x["name"] + " " + "=" * 20)
        t = x.get("tail") or ""
        # print the failure summary area (look for ❌ / 失败 / Traceback tail)
        lines = t.splitlines()
        print("\n".join(lines[-35:]))
        print()
