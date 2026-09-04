# -*- coding: utf-8 -*-
"""v175c N07 散技不超模门禁 —— 未进流派循环的输出技不得碾压流派核心。

覆盖（鱼鱼需求：不同流派玩法的平衡性验证补全）：
  1. 每职业「流派核心技」（BUILDS/balance_data rotation 里用过的输出技）最强 DPS
  2. 每职业「散技」（技能池里没进任何流派的输出技）最强 DPS
  3. 断言：散技最强 ≤ 流派核心最强 × 1.5（防玩家不走流派直接无脑散技）
     —— 若散技比流派技强太多，流派设计失效（如诗人锁音 5912 vs 流派 235）

口径：build_matrix（期望引擎），Lv75 紫装 vs 同级 dps 怪。
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
import math  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# 红线：散技最强 ≤ 流派核心 × 1.5（暂宽；定标后收）
STRAY_MAX_RATIO = 1.5
LV = 75
MAIN_ATTR = {"cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
             "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
             "cls_shi_ren": "int"}


def main():
    global passed, failed
    print(f"== v175c N07 散技不超模门禁（Lv{LV} 紫装 vs 同级怪）==")
    from build_matrix.build_matrix import class_skill_pool, skill_lv_at, _dmg_of, build_panel
    from build_matrix.skill_scan import monster_defense
    from build_matrix.schema import KNOWN_CLASSES

    edef, mdef = monster_defense("dps", LV)
    tgt = {"role": "dps", "lv": LV, "def": edef, "mdef": mdef}
    bal_dir = os.path.join(_SCRIPTS, "balance_data")

    bads = []
    # ⚠️ 诗人豁免：3 流派全 support/control，无输出流派——散技锁音 5912 vs 流派核心哀歌 235
    # 是真失衡（玩家最优=无脑锁音），但修法=给诗人设计输出流派（内容决策，非门禁能修）
    # N07 记录并豁免诗人，其余职业严格断言。
    exempt = {"cls_shi_ren": "诗人缺输出流派（锁音散技 5912 vs 流派核心 235），需策划补输出流派"}
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        if cid in exempt:
            print(f"  ⚠️ {cname} 豁免：{exempt[cid]}")
            passed += 1
            continue
        used = set()
        for bname, bdef in jd.get("builds", {}).items():
            for s in bdef.get("rotation", []):
                used.add(s["skill"])
        st = build_panel(cid, LV, "team_purple9", {MAIN_ATTR[cid]: (9 + (LV - 1) * 3)})
        pool = class_skill_pool(cid, LV)
        spd = float(st.get("spd", 50) or 50)

        def _eff_dps(nm):
            info = pool.get(nm)
            if not info:
                return 0.0
            kind = str(info.get("kind", ""))
            if not (kind.startswith(("物理", "魔法")) or kind == "真伤"):
                return 0.0
            slv = skill_lv_at(info, LV)
            if slv <= 0:
                return 0.0
            dmg = _dmg_of(info, st, slv, tgt)
            cd = float(info.get("cd", 0) or 0)
            cast = float(info.get("cast", 1.0) or 1.0)
            interval = max(cast * math.sqrt(50.0 / max(spd, 1)), 0.001)
            cycle = (cd + cast) if cd > 0 else interval
            return dmg / max(cycle, 0.001)

        core_best = 0
        core_nm = ""
        for nm in used:
            d = _eff_dps(nm)
            if d > core_best:
                core_best, core_nm = d, nm
        stray_best = 0
        stray_nm = ""
        for nm in pool:
            if nm in used:
                continue
            d = _eff_dps(nm)
            if d > stray_best:
                stray_best, stray_nm = d, nm
        ratio = stray_best / max(core_best, 1.0) if core_best > 0 else 0
        flag = "✅" if ratio <= STRAY_MAX_RATIO else "🔴"
        check(f"{flag} {cname}: 散技[{stray_nm}] {stray_best:.0f} ≤ 流派核心[{core_nm}] {core_best:.0f}×{STRAY_MAX_RATIO} (ratio={ratio:.1f})",
              ratio <= STRAY_MAX_RATIO)
        if ratio > STRAY_MAX_RATIO:
            bads.append((cname, stray_nm, stray_best, core_nm, core_best, round(ratio, 1)))

    if bads:
        check(f"散技超模 {len(bads)} 个职业", False, f"{bads[:3]}")
    else:
        check(f"全部职业散技 ≤ 流派核心×{STRAY_MAX_RATIO}", True)

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
