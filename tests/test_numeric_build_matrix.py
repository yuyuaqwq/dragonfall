# -*- coding: utf-8 -*-
"""v175 N01 流派×加点×装备全矩阵期望一致性门禁。

覆盖（鱼鱼需求：不同加点组合 / 不同流派玩法 / 不同属性装备）：
  1. 7 职业 JSON 齐全且 schema 通过（职业 agent 产出完整性）
  2. 每职业 3 流派 × rotation 技能名全在技能池（builds 引用真实）
  3. 全矩阵可跑（7职业×3流派×5阶段×推荐加点 → 无 error 格）
  4. 同职业 3 流派 DPS 极差 ≤ 红线（防废流派/超模；第一批先宽后收紧）
  5. 加点敏感性：主属性最优 vs 次优加点 DPS 差距带内（防单属性碾压）

口径：build_matrix（A1 期望引擎，真实引擎公式）。Boss 用裸模板同级 boss
（跨职业横向比较统一口径，不叠 hp_mult——叠了全打不死没法比）。
"""
import os
import sys

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


# 红线（第一批：先宽后收紧。跑出实测后按鱼鱼拍板 3倍/5倍 收紧）
SAME_CLASS_DPS_RATIO_MAX = 8.0     # 同职业 3 流派 DPS 极差 ≤8×（暂宽，定标后收紧到 3）
CROSS_CLASS_DPS_RATIO_MAX = 12.0   # 同阶段跨职业 DPS 极差 ≤12×（暂宽，定标后收紧到 5）
ATTR_SENS_RATIO_MAX = 1.5          # 主属性最优 vs 次优加点 DPS 差距 ≤50%（→ 15% 待收紧）


def main():
    global passed, failed
    print("== v175 N01 流派×加点×装备全矩阵期望一致性门禁 ==")
    bm_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
    if bm_dir not in sys.path:
        sys.path.insert(0, bm_dir)

    from build_matrix.schema import validate, KNOWN_CLASSES
    from build_matrix.build_matrix import rotation_dps, resolve_attr, build_panel, class_skill_pool
    from numeric_lib.monster import build as _mb
    from data.plugins.dragonfall.game import engine as E

    bal_dir = os.path.join(bm_dir, "balance_data")

    # ---- 0. 前置：7 职业 JSON 齐全且 schema 通过 ----
    print("\n【0】职业 JSON 完整性")
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            check(f"{cid} JSON 存在", False, "缺文件")
            continue
        errs = validate(fp)
        check(f"{cid} JSON schema 通过", not errs, f"errs={errs[:2]}")
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        nbuild = len(jd.get("builds", {}))
        check(f"{cid} 3 流派", nbuild == 3, f"builds={nbuild}")
        nattr = len(jd.get("attr_presets", {}))
        check(f"{cid} ≥3 加点预设", nattr >= 3, f"attr={nattr}")

    # ---- 1. rotation 技能名全在技能池（builds 引用真实） ----
    print("\n【1】流派技能引用完整性")
    from data.plugins.dragonfall.game.data import skills as SK
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        pool = class_skill_pool(cid, 999)  # 全等级池
        bad = []
        for bname, bdef in jd.get("builds", {}).items():
            for step in bdef.get("rotation", []):
                sk = step.get("skill", "")
                if sk not in pool:
                    bad.append(f"{bname}.{sk}")
        check(f"{cid} 流派技能全有效", not bad, f"幽灵技能={bad[:5]}")

    # ---- 2. 全矩阵可跑（7×3×5 阶段 × 推荐加点 → 无 error） ----
    print("\n【2】全矩阵扫描（每职业3流派×5阶段×推荐加点）")
    stage_cfgs = [("P1", 10, "solo_low"), ("P2", 24, "solo_mid"),
                  ("P3", 45, "team_purple9"), ("P4", 75, "team_purple9"),
                  ("P5", 95, "team_orange9")]
    results = {}  # (cid, bname) -> {stage: {attr: dps/kill}}
    err_cells = []
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        for bname, bdef in jd.get("builds", {}).items():
            rotation = bdef.get("rotation", [])
            rec_name = bdef.get("attr_preset", "")
            apresets = jd.get("attr_presets", {})
            rec_preset = apresets.get(rec_name, {"str": "all"})
            for stage_name, lv, loadout in stage_cfgs:
                attr = resolve_attr(rec_preset, lv)
                m = _mb("boss", lv)
                tgt = {"role": "boss", "lv": lv, "max_hp": m.get("max_hp", 5000),
                       "def": m.get("def", 0), "mdef": m.get("mdef", 0),
                       "hp": m.get("max_hp", 5000)}
                try:
                    r = rotation_dps(cid, lv, loadout, attr, rotation,
                                     fight_len=60.0, target=tgt)
                    results.setdefault((cid, bname), {})[stage_name] = {
                        "dps": r["dps"], "kill": r["kill_rounds"],
                        "empty": r["empty_mp_rounds"],
                    }
                except Exception as ex:
                    err_cells.append(f"{cid}.{bname}.{stage_name}: {ex}")
    check(f"全矩阵无 error 格（共 7×3×5=105 格）", not err_cells, f"err={err_cells[:3]}")
    print(f"  跑通格数: {sum(len(v) for v in results.values())}")

    # ---- 3. 同职业 3 流派 DPS 极差 ≤ 红线（P3 Lv45 档代表）----
    # ⚠️ 按 role 分口径：dps 流派之间比 DPS；heal/tank/support/control 流派 dps=0 是
    # 定位使然（纯奶无输出），不跟 dps 流派比 DPS（鱼鱼拍板：单刷允许打不过，按相对强弱排）。
    # 参考 ROTATIONS 的既有口径：治疗/辅助职业有输出兜底技能（v174 补过）但主职是奶/辅。
    print("\n【3】同职业 dps 流派 DPS 极差（P3/Lv45 代表档，按 role 分口径）")
    from data.plugins.dragonfall.game.data import builds as BD
    build_roles = {}  # (cid, bname) -> role
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        for bname, bdef in jd.get("builds", {}).items():
            build_roles[(cid, bname)] = bdef.get("role", "dps")
    same_bad = []
    for cid in KNOWN_CLASSES:
        # 只取 role=dps 的流派（同定位才比输出效率）
        dps_by_build = {}
        non_dps = []
        for (c, bname), stages in results.items():
            if c != cid or "P3" not in stages:
                continue
            if build_roles.get((c, bname), "dps") == "dps":
                dps_by_build[bname] = stages["P3"]["dps"]
            else:
                non_dps.append(bname)
        role_note = f"，非dps流派[{','.join(non_dps)}]单列" if non_dps else ""
        if len(dps_by_build) >= 2:
            vals = list(dps_by_build.values())
            mx, mn = max(vals), max(min(vals), 1.0)
            ratio = mx / mn
            flag = "✅" if ratio <= SAME_CLASS_DPS_RATIO_MAX else "🔴"
            check(f"{flag} {cid} dps流派 DPS 极差 {ratio:.1f}× ≤{SAME_CLASS_DPS_RATIO_MAX}×"
                  f"（{ {k: round(v, 0) for k, v in dps_by_build.items()} }）{role_note}",
                  ratio <= SAME_CLASS_DPS_RATIO_MAX)
            if ratio > SAME_CLASS_DPS_RATIO_MAX:
                same_bad.append((cid, round(ratio, 1)))
        elif dps_by_build:
            only = next(iter(dps_by_build))
            check(f"✅ {cid} 仅 1 个 dps 流派（{only} dps={dps_by_build[only]:.0f}）{role_note}", True)

    # ---- 4. 同阶段跨职业 DPS 极差 ≤ 红线（每职业最强流派，P3） ----
    print("\n【4】同阶段跨职业 DPS 极差（P3/Lv45 每职业最强流派）")
    cross = {}
    for cid in KNOWN_CLASSES:
        best = 0
        for (c, bname), stages in results.items():
            if c == cid and "P3" in stages:
                best = max(best, stages["P3"]["dps"])
        if best > 0:
            cross[cid] = best
    if cross:
        vals = list(cross.values())
        mx, mn = max(vals), max(min(vals), 1.0)
        ratio = mx / mn
        check(f"跨职业 P3 最强流派 DPS 极差 {ratio:.1f}× ≤{CROSS_CLASS_DPS_RATIO_MAX}×"
              f"（{ {k.split('_')[-1]: round(v, 0) for k, v in cross.items()} }）",
              ratio <= CROSS_CLASS_DPS_RATIO_MAX)

    # ---- 5. 加点敏感性：P3 主属性 vs 全预设 DPS 离差 ≤ 红线 ----
    print("\n【5】加点敏感性（P3 每流派推荐加点 vs 全预设极差）")
    attr_bad = []
    for cid in KNOWN_CLASSES:
        fp = os.path.join(bal_dir, f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        apresets = jd.get("attr_presets", {})
        for bname, bdef in jd.get("builds", {}).items():
            rotation = bdef.get("rotation", [])
            rec_name = bdef.get("attr_preset", "")
            rec_preset = apresets.get(rec_name, {})
            if not rec_preset:
                continue
            # 用 Lv45 档测
            dps_by_attr = {}
            for aname, apreset in apresets.items():
                attr = resolve_attr(apreset, 45)
                m = _mb("boss", 45)
                tgt = {"role": "boss", "lv": 45, "max_hp": m.get("max_hp", 5000),
                       "def": m.get("def", 0), "mdef": m.get("mdef", 0),
                       "hp": m.get("max_hp", 5000)}
                try:
                    r = rotation_dps(cid, 45, "team_purple9", attr, rotation,
                                     fight_len=60.0, target=tgt)
                    dps_by_attr[aname] = r["dps"]
                except Exception:
                    pass
            if len(dps_by_attr) >= 2:
                vals = list(dps_by_attr.values())
                mx, mn = max(vals), max(min(vals), 1.0)
                ratio = mx / mn
                if ratio > ATTR_SENS_RATIO_MAX:
                    attr_bad.append((cid, bname, round(ratio, 2),
                                     {k: round(v, 0) for k, v in dps_by_attr.items()}))
    if attr_bad:
        for cid, bname, ratio, details in attr_bad[:8]:
            check(f"🔴 {cid}.{bname} 加点极差 {ratio}×", False, f"details={details}")
    else:
        check(f"全部流派加点敏感性 ≤{ATTR_SENS_RATIO_MAX}×", True)

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
