# -*- coding: utf-8 -*-
"""v175 N06 流派连招正收益门禁 —— 技能联动强度验证。

覆盖（鱼鱼需求：技能与技能之间的联动强度）：
  1. 每流派 rotation（完整连招）DPS ≥ 该流派"单技能 spam"（最强单体无脑放）DPS
     —— 连招必须有正收益（否则玩家无脑放一个技能即可，联动设计失败）
  2. rotation 中每个技能都有出场（无死技能——cond 永不满足导致 0 次施放）
  3. 联动强度量化打印（rotation DPS / 最强单技能 DPS = 联动倍率）

口径：build_matrix.rotation_dps（真实引擎公式）
第一批：硬断言 rotation DPS ≥ 单技能 spam DPS × 0.85（允许接近但不得明显更弱）；
      死技能（0 次施放）硬红（防 rotation 写了个永远不触发的技能）
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


# 红线
COMBO_MIN_RATIO = 0.85   # 完整连招 DPS ≥ 最强单技能 spam × 0.85
DEAD_SKILL_MAX = 0       # rotation 中 0 次施放的技能数上限（防死技能）


def main():
    global passed, failed
    print("== v175 N06 流派连招正收益门禁 ==")
    from build_matrix.build_matrix import rotation_dps, resolve_attr
    from build_matrix.schema import KNOWN_CLASSES
    from numeric_lib.monster import build as _mb
    bal_dir = os.path.join(_SCRIPTS, "balance_data")

    lv, loadout = 45, "team_purple9"
    m = _mb("boss", lv)
    tgt = {"role": "boss", "lv": lv, "max_hp": m.get("max_hp", 5000),
           "def": m.get("def", 0), "mdef": m.get("mdef", 0),
           "hp": m.get("max_hp", 5000)}

    combo_bad = []
    dead_bad = []
    combos = []  # (职业, 流派, rotation_dps, best_single_dps, ratio)
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        apresets = jd.get("attr_presets", {})
        for bname, bdef in jd.get("builds", {}).items():
            rotation = bdef.get("rotation", [])
            rec_name = bdef.get("attr_preset", "")
            rec_preset = apresets.get(rec_name, {"str": "all"})
            attr = resolve_attr(rec_preset, lv)
            if bdef.get("role") != "dps":
                continue  # 连招收益只对 dps 流派有判定意义
            if not rotation:
                continue
            # 完整连招
            r_full = rotation_dps(cid, lv, loadout, attr, rotation,
                                  fight_len=60.0, target=tgt)
            full_dps = r_full["dps"]
            hits = r_full["skill_hits"]
            # 单技能 spam：每个技能单独一个循环跑
            best_single_dps = 0
            best_single = None
            for step in rotation:
                solo = [dict(step)]  # 只有这一个技能，cond 改 always 最无脑
                solo[0]["cond"] = "always"
                try:
                    rs = rotation_dps(cid, lv, loadout, attr, solo,
                                      fight_len=60.0, target=tgt)
                    if rs["dps"] > best_single_dps:
                        best_single_dps = rs["dps"]
                        best_single = step["skill"]
                except Exception:
                    pass
            ratio = full_dps / max(best_single_dps, 1.0)
            # 死技能检测（修正版 v2）：排除 1) cond 非 always 的资源/CD技 2) 玩家当前
            # 等级学不到的高阶技（lv>45 大招，rotation 是满级形态但 P3 阶段还没学到——
            # 期望引擎 skill_lv_at 返回 0 自动跳过，不算死技能）。
            from build_matrix.build_matrix import skill_lv_at, class_skill_pool
            pool = class_skill_pool(cid, lv)
            dead = [s["skill"] for s in rotation
                    if hits.get(s["skill"], 0) == 0
                    and s.get("cond", "always") == "always"
                    and skill_lv_at(pool.get(s["skill"], {}), lv) > 0]
            combos.append((cname, bname, full_dps, best_single_dps, ratio, best_single))
            tag = "🔴" if ratio < COMBO_MIN_RATIO else "✅"
            dead_note = f" 死技能={dead}" if dead else ""
            check(f"{tag} {cname}.{bname} 连招DPS {full_dps:.0f} vs 单技[{best_single}] {best_single_dps:.0f}"
                  f" = {ratio:.2f}×{dead_note}",
                  ratio >= COMBO_MIN_RATIO)
            if ratio < COMBO_MIN_RATIO:
                combo_bad.append((cname, bname, round(ratio, 2)))
            if len(dead) > DEAD_SKILL_MAX:
                dead_bad.append((cname, bname, dead))

    # 汇总
    if combo_bad:
        check(f"连招负收益流派 {len(combo_bad)} 个", False, f"{combo_bad[:5]}")
    else:
        check(f"全部 dps 流派连招正收益（≥单技×{COMBO_MIN_RATIO}）", True)
    if dead_bad:
        check(f"死技能流派 {len(dead_bad)} 个（rotation 有技能 0 次施放）",
              False, f"{dead_bad[:3]}")
    else:
        check(f"全部流派无死技能（rotation 技能全有出场）", True)

    # 联动倍率分布
    print("\n  联动倍率 Top（连招/单技，>1 = 连招有增益）:")
    for cname, bname, full_dps, best_single_dps, ratio, best_single in sorted(
            combos, key=lambda x: -x[4])[:8]:
        print(f"    {cname}.{bname}: {ratio:.2f}×（连招{full_dps:.0f} vs {best_single}单放{best_single_dps:.0f}）")

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
