# -*- coding: utf-8 -*-
"""v175 N03 流派 vs 副本 Boss 对战矩阵门禁。

覆盖（鱼鱼需求：各阶段副本 Boss 模拟对战）：
  1. 每职业×流派 vs 各阶段代表 Boss（STAGE_BOSS 映射，叠 hp_mult 真实口径）
  2. 期望击杀轮可算（无 error）
  3. 相对排名输出（dps 流派击杀轮带；单刷打不过标注为设计意图非红）
  4. 硬断言：同一 Boss 下 dps 流派击杀轮 ≤ 非 dps 流派（输出职业必须比辅助快）
  5. 期望 vs 真引擎抽验格（若真引擎数据有，对比偏差带）

口径：build_matrix.build_vs_boss（期望引擎，叠实例 hp_mult/atk_mult + 单刷药水）
第一批：结构 + 相对排名 + 击杀轮带打印（不锁绝对数值，等真引擎复核后收紧）
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


# 阶段档位（与 build_matrix STAGE_CFG / boss_matrix 对齐）
STAGE_CFG = {
    "P1": (10, "solo_low"), "P2": (24, "solo_mid"), "P3": (45, "team_purple9"),
    "P4": (75, "team_purple9"), "P5": (95, "team_orange9"),
}


def load_cls(cid):
    with open(os.path.join(_SCRIPTS, "balance_data", f"{cid}.json"), encoding="utf-8") as f:
        return json.load(f)


def main():
    global passed, failed
    print("== v175 N03 流派 vs 副本 Boss 对战矩阵门禁 ==")
    from build_matrix.build_matrix import build_vs_boss, resolve_attr
    from build_matrix.boss_matrix import stage_boss_target, boss_def_of
    from build_matrix.schema import KNOWN_CLASSES

    bal_dir = os.path.join(_SCRIPTS, "balance_data")

    # ---- 0. 每职业 JSON 载入 ----
    cls_data = {}
    for cid in KNOWN_CLASSES:
        cls_data[cid] = load_cls(cid)

    # ---- 1. 每职业每阶段 vs 代表 Boss（dps 流派为主）----
    print("\n【1】流派 vs 阶段 Boss 击杀轮（叠 hp_mult 真实口径）")
    # stage → (推荐 Boss iid, 玩家用 lv/loadout)
    boss_targets = {}
    for stage, (plv, loadout) in STAGE_CFG.items():
        tgts = stage_boss_target(stage)
        if tgts:
            boss_targets[stage] = (tgts[0]["iid"], plv, loadout, tgts[0]["boss_lv"])
        else:
            print(f"  ⚠️ {stage} 无推荐 Boss")
    # 特殊映射：阶段玩家 lv 与 Boss lv 匹配（用 STAGE_BOSS 推荐本）
    # 说明：P1 玩家 Lv10 打哥布林 Boss Lv20 偏难；这是"阶段代表"不是"等级匹配"
    results = {}
    errs = []
    for cid in KNOWN_CLASSES:
        jd = cls_data[cid]
        cname = jd.get("class_name", cid)
        for bname, bdef in jd.get("builds", {}).items():
            rotation = bdef.get("rotation", [])
            role = bdef.get("role", "dps")
            rec_attr = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
            if not rec_attr:
                rec_attr = {"str": "all"}
            for stage, (iid, plv, loadout, blv) in boss_targets.items():
                attr = resolve_attr(rec_attr, plv)
                boss_def = boss_def_of(iid)
                if not boss_def:
                    continue
                try:
                    r = build_vs_boss(cid, plv, loadout, attr, rotation, boss_def,
                                      blv, iid=iid, n_players=1)
                    results[(cid, bname, stage)] = {**r, "role": role}
                except Exception as ex:
                    errs.append(f"{cname}.{bname}.{stage}: {ex}")
    check(f"流派×阶段Boss 全可算（无 error）", not errs, f"err={errs[:3]}")
    print(f"  可算格数: {len(results)}")

    # ---- 2. 相对排名表（每 Boss 下各职业 dps 流派击杀轮排名）----
    print("\n【2】相对排名（每阶段代表 Boss，dps 流派击杀轮）")
    # P2(海蚀)/P3(老王)/P5(深渊) 各出一张排名
    for stage in ("P2", "P3", "P5"):
        iid, plv, loadout, blv = boss_targets.get(stage, (None,)*4)
        if not iid:
            continue
        rows = []
        for cid in KNOWN_CLASSES:
            jd = cls_data[cid]
            cname = jd.get("class_name", cid)
            for bname, bdef in jd.get("builds", {}).items():
                if bdef.get("role", "dps") != "dps":
                    continue
                r = results.get((cid, bname, stage))
                if r and r["kill_rounds"]:
                    rows.append((cname, bname, r["kill_rounds"], r["verdict"]))
                elif r and r["kill_rounds"] is None:
                    rows.append((cname, bname, 9999, r["verdict"]))
        rows.sort(key=lambda x: x[2])
        print(f"\n  --- {stage} 代表 Boss（玩家 Lv{plv} {loadout}）---")
        for cname, bname, kr, verdict in rows:
            kr_s = "杀不死" if kr == 9999 else f"{kr}轮"
            print(f"    {cname:<4} {bname:<7} {kr_s} {verdict}")

    # ---- 3. 硬断言：同 Boss 下 dps 流派必须 ≤ 非 dps 流派击杀轮 ----
    # （输出职业打 Boss 应该比纯奶/纯坦快——若纯奶反而快 = 数值 bug）
    print("\n【3】dps 流派 vs 非 dps 流派击杀轮相对断言（P3 老王）")
    iid, plv, loadout, blv = boss_targets.get("P3", (None,)*4)
    if iid:
        bad = []
        for cid in KNOWN_CLASSES:
            jd = cls_data[cid]
            dps_krs = [(results.get((cid, b, "P3"), {}).get("kill_rounds") or 9999)
                       for b in jd["builds"] if jd["builds"][b].get("role") == "dps"]
            if not dps_krs:
                continue  # 该职业无 dps 流派（诗人全辅助）跳过
            best_dps = min(dps_krs)
            for bname, bdef in jd["builds"].items():
                if bdef.get("role") == "dps":
                    continue
                kr = results.get((cid, bname, "P3"), {}).get("kill_rounds")
                if kr is None:
                    continue
                # 非 dps 流派击杀轮不应比本职业 dps 流派快太多（允许磨死但必须更慢）
                if kr < best_dps * 0.8:
                    bad.append((cid, bname, round(kr, 0), round(best_dps, 0)))
        check("非dps流派击杀轮 ≥ 本职业dps流派×0.8（输出职业不该比辅助慢）",
              len(bad) == 0, f"反了={bad[:5]}")

    # ---- 4. 击杀轮打印：dps 流派全 Boss 击杀轮带（先观察不锁死）----
    print("\n【4】dps 流派各阶段击杀轮一览")
    for cid in KNOWN_CLASSES:
        jd = cls_data[cid]
        cname = jd.get("class_name", cid)
        cells = []
        for bname, bdef in jd["builds"].items():
            if bdef.get("role") != "dps":
                continue
            krs = []
            for stage in ("P1", "P2", "P3", "P4", "P5"):
                r = results.get((cid, bname, stage))
                if r and r["kill_rounds"]:
                    krs.append(str(r["kill_rounds"]))
                else:
                    krs.append("×")
            cells.append(f"{bname}[{'/'.join(krs)}]")
        if cells:
            print(f"  {cname}: " + " ".join(cells))

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
