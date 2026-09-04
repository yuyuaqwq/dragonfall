# -*- coding: utf-8 -*-
"""v175e N08 词条乘区流派门禁 —— 暴击/急速/穿透/元素配装强度验证。

覆盖（鱼鱼需求：暴击法师、急速游侠等乘区玩法）：
  1. 每职业每 dps 流派 5 种乘区配装可跑（atk/crit/spd/pene/elem）
  2. 乘区收益在合理带：最优乘区 ≤ 基准 atk × 1.25（防词条碾压）
  3. 乘区收益有意义：最优乘区 ≥ 基准 atk × 1.03（防词条无差异=配装无意义）
  4. 各乘区流派跨职业可比较（无单乘区全职业碾压 = 设计不健康）

口径：build_matrix（期望引擎 v175e，含暴击/穿透/全伤乘区），Lv75 紫装 vs 同级 Boss。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_HERE)
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

import json  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# 红线
AFFIX_MAX_RATIO = 1.25   # 最优乘区 ≤ atk 基准 ×1.25（防词条碾压）
AFFIX_MIN_RATIO = 1.03   # 最优乘区 ≥ atk 基准 ×1.03（防配装无意义）
LV = 75
LOADOUT = "team_purple9"
AFFIXES = ("atk", "crit", "spd", "pene", "elem")


def main():
    global passed, failed
    print(f"== v175e N08 词条乘区流派门禁（Lv{LV} {LOADOUT}）==")
    from build_matrix.build_matrix import rotation_dps, resolve_attr, boss_instance_panel
    from build_matrix.schema import KNOWN_CLASSES
    from build_matrix.boss_matrix import all_bosses
    from data.plugins.dragonfall.game.data import skills as SK

    # 目标 Boss：Lv58-65 档（精灵废墟/月神）
    boss = [b for b in all_bosses() if 55 <= b["inst_lv"] <= 65][0]
    bp = boss_instance_panel(boss["iid"], 1)
    tgt = {"role": "boss", "lv": boss["boss_lv"], "max_hp": bp["max_hp"],
           "def": bp["def"], "mdef": bp["mdef"], "hp": bp["max_hp"]}
    bal_dir = os.path.join(_SCRIPTS, "balance_data")

    over_bad, flat_bad, errs = [], [], []
    affix_best = {}
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        cdef = SK.PLAYER_SKILLS.get(cid, {}).get("name", cname)
        for bname, bdef in jd.get("builds", {}).items():
            if bdef.get("role") != "dps":
                continue
            rotation = bdef.get("rotation", [])
            rec = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
            if not rec:
                rec = {"str": "all"}
            attr = resolve_attr(rec, LV)
            dps_by = {}
            for at in AFFIXES:
                try:
                    r = rotation_dps(cid, LV, LOADOUT, attr, rotation,
                                     fight_len=60.0, target=tgt, affix_type=at)
                    dps_by[at] = r["dps"]
                except Exception as ex:
                    errs.append(f"{cname}.{bname}.{at}: {ex}")
                    dps_by[at] = 0.0
            base = dps_by.get("atk", 1.0)
            best_at = max(AFFIXES, key=lambda x: dps_by[x])
            best_dps = dps_by[best_at]
            ratio = best_dps / max(base, 1.0)
            affix_best.setdefault(best_at, []).append(f"{cname}·{bname}")
            # 断言 1：乘区收益不碾压（≤1.25）
            if ratio > AFFIX_MAX_RATIO:
                over_bad.append((cname, bname, round(ratio, 2), best_at))
            # 断言 2：乘区有意义（≥1.03）
            if ratio < AFFIX_MIN_RATIO:
                flat_bad.append((cname, bname, round(ratio, 2)))

    check(f"乘区扫描无 error", not errs, f"err={errs[:3]}")
    check(f"全部流派最优乘区收益 ≤{AFFIX_MAX_RATIO}×（防词条碾压）",
          len(over_bad) == 0, f"超={over_bad[:5]}")
    check(f"全部流派最优乘区收益 ≥{AFFIX_MIN_RATIO}×（配装有意义）",
          len(flat_bad) == 0, f"无差异={flat_bad[:5]}")

    # 断言 3：无单乘区全职业碾压（若某乘区是最优的流派 >70% = 设计单调）
    print("\n【最优乘区分布】")
    for at, lst in sorted(affix_best.items(), key=lambda x: -len(x[1])):
        print(f"  {at}: {len(lst)} 个流派 ({lst[:6]}{'...' if len(lst) > 6 else ''})")
    total = sum(len(v) for v in affix_best.values())
    if total:
        for at, lst in affix_best.items():
            if len(lst) / total > 0.7:
                check(f"⚠️ {at} 乘区占比 {len(lst)}/{total} >70%（设计单调候选）", False)
    check("乘区分布无单乘区垄断 >70%", True)

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
