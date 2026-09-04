# -*- coding: utf-8 -*-
"""v175 N05 加点敏感性门禁 —— 不同加点组合对流派输出影响。

覆盖（鱼鱼需求：不同加点组合的平衡性）：
  1. 全职业×流派×阶段：推荐加点 vs 全预设 DPS 极差 ≤ 红线
     （防单属性碾压：主属性最优加点不该吊打所有其它加点）
  2. 防御向加点（vit）不应让 dps 流派输出崩塌（除非流派定位是坦）
  3. 加点极差分布打印（第一批观察，红线从宽）

口径：build_matrix.rotation_dps（真实引擎公式），裸模板同级 boss 横向比。
第一批：从宽红线 2.0×（主属性 vs 次优差 ≤100%），定标后收紧到 15%。
"""
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))          # tests/
_PLUGIN = os.path.dirname(_HERE)                             # dragonfall/
_SCRIPTS = os.path.join(_PLUGIN, "scripts")
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
for _p in (_QQBOT, _PLUGIN, _HERE, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_HERE, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# 第一批红线（从宽；定标后按鱼鱼拍板收紧到 15% = 1.15×）
ATTR_SENS_MAX = 2.0   # 推荐加点 vs 全预设 DPS 极差 ≤2×（先宽）
# dps 流派不允许出现"某个加点 dps=0/崩塌"
ATTR_ZERO_MAX = 0     # dps 流派加点后 dps<=0 的数量上限


def main():
    global passed, failed
    print("== v175 N05 加点敏感性门禁 ==")
    from build_matrix.build_matrix import rotation_dps, resolve_attr
    from build_matrix.schema import KNOWN_CLASSES
    from numeric_lib.monster import build as _mb
    bal_dir = os.path.join(_SCRIPTS, "balance_data")

    stage_cfg = ("P3", 45, "team_purple9")  # 代表档
    _, lv, loadout = stage_cfg
    m = _mb("boss", lv)
    tgt = {"role": "boss", "lv": lv, "max_hp": m.get("max_hp", 5000),
           "def": m.get("def", 0), "mdef": m.get("mdef", 0),
           "hp": m.get("max_hp", 5000)}

    print("\n【1】全职业×流派 加点极差（P3/Lv45）")
    bad = []
    zero_bad = []
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        apresets = jd.get("attr_presets", {})
        if len(apresets) < 3:
            check(f"⚠️ {cname} 加点预设 <3", False, f"{len(apresets)}")
        for bname, bdef in jd.get("builds", {}).items():
            rotation = bdef.get("rotation", [])
            role = bdef.get("role", "dps")
            rec_name = bdef.get("attr_preset", "")
            dps_by_attr = {}
            for aname, apreset in apresets.items():
                attr = resolve_attr(apreset, lv)
                try:
                    r = rotation_dps(cid, lv, loadout, attr, rotation,
                                     fight_len=60.0, target=tgt)
                    dps_by_attr[aname] = r["dps"]
                except Exception as ex:
                    dps_by_attr[aname] = 0.0
            if len(dps_by_attr) < 3:
                continue
            vals = list(dps_by_attr.values())
            mx, mn = max(vals), max(min(vals), 1.0)
            ratio = mx / mn
            if role == "dps":
                n_zero = sum(1 for v in vals if v <= 1.0)
                if n_zero > ATTR_ZERO_MAX:
                    zero_bad.append(f"{cname}.{bname} 有加点 dps 崩塌")
            tag = "🔴" if ratio > ATTR_SENS_MAX else "✅"
            check(f"{tag} {cname}.{bname} 加点极差 {ratio:.2f}× ≤{ATTR_SENS_MAX}×"
                  f"（推荐[{rec_name}]={dps_by_attr.get(rec_name, 0):.0f} "
                  f"最佳={max(vals):.0f} 最差={min(vals):.0f}）",
                  ratio <= ATTR_SENS_MAX)
            if ratio > ATTR_SENS_MAX:
                bad.append((cname, bname, round(ratio, 2)))

    # 汇总
    if bad:
        check(f"加点极差超标流派 {len(bad)} 个（候选待真引擎复核）", False, f"{bad[:5]}")
    else:
        check(f"全部流派加点极差 ≤{ATTR_SENS_MAX}×", True)
    check(f"dps 流派无加点崩塌（dps=0）", len(zero_bad) == 0, f"{zero_bad[:3]}")

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
