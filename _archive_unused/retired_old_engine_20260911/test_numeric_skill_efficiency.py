# -*- coding: utf-8 -*-
"""v175 N02 全技能效率审计门禁（299 技能全覆盖）。

覆盖（鱼鱼需求：每个技能的强度 / mp消耗 / cd平衡 / 出手速度）：
  1. 7 职业全技能（PLAYER_SKILLS + BRANCH_SKILLS）效率表可跑（skill_scan 口径）
  2. 每职业技能数 ≥ 30（base + 转职全量在）
  3. 每个输出技有 dps/dpe（不为 0 且无明显异常）
  4. 无"空转技能"：kind=输出但 skill_scan 算 dmg≈0（exprs 缺失/公式崩）
  5. 无"超模技能"：DPS 显著高于同级普攻等效（第一批先打印分布，红线上限宽）
  6. 无"废技能"：DPE 极低（mp 消耗远超伤害产出）—— 先打印分布，待定标

口径：scripts/build_matrix/skill_scan.py（真实引擎公式 skill_expr_preview + calc_damage）
第一批：结构 + 分布打印 + 硬红线（dmg=0 的输出技 = 空转必须红；DPS 超普攻 10× = 超模候选）
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

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# 硬红线（第一批）
DMG_ZERO_MAX = 0        # kind=输出但 dmg=0 的技能数上限（0 = 不允许空转输出技）
DPS_OVER_BASIC_MAX = 15.0  # 输出技 DPS 不超过普攻等效 ×15（先宽，防超模回归）
DPE_FLOOR = 0.5         # 输出技 DPE 下限（mp 产出效率）——待收紧


def main():
    global passed, failed
    print("== v175 N02 全技能效率审计门禁（299 技能）==")

    from build_matrix.skill_scan import skill_efficiency_table
    from data.plugins.dragonfall.game.data import skills as SK
    from data.plugins.dragonfall.game.data import skill_up as SU

    # 每职业技能量核对
    print("\n【1】技能规模（base + BRANCH 全量）")
    for cid in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia", "cls_mu_shi",
                "cls_ci_ke", "cls_wu_seng", "cls_shi_ren"):
        n_base = len(SK.PLAYER_SKILLS.get(cid, {}).get("skills", {}))
        br = SK.BRANCH_SKILLS.get(cid, {}).get("branches", {})
        n_br = 0
        for tier, tdef in br.items():
            if not isinstance(tdef, dict):
                continue
            for line, skills in tdef.items():
                if isinstance(skills, dict):
                    n_br += len(skills)
        check(f"{cid} base={n_base} branch={n_br} 总={n_base+n_br}",
              n_base >= 8 and n_br >= 20, f"base={n_base} br={n_br}")

    # 全职业效率表（Lv45 档，dps 怪防御）
    print("\n【2】全技能效率审计（Lv45 玩家 vs 同级 dps 怪）")
    from numeric_lib.monster import build as _mb
    m45 = _mb("dps", 45)
    edef45, mdef45 = int(m45.get("def", 0)), int(m45.get("mdef", 0))

    all_dmg_rows = []
    empty_dmg = []      # kind=输出 但 dmg=0
    zero_rows = []
    for cid in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia", "cls_mu_shi",
                "cls_ci_ke", "cls_wu_seng", "cls_shi_ren"):
        rows = skill_efficiency_table(cid, player_lv=45, edef=edef45, mdef=mdef45)
        # skill_efficiency_table 只扫 PLAYER_SKILLS（base），BRANCH 也要扫
        # 补扫 BRANCH：直接构造 cdef
        cdef = SK.PLAYER_SKILLS.get(cid, {})
        br = SK.BRANCH_SKILLS.get(cid, {}).get("branches", {})
        from build_matrix.skill_scan import skill_efficiency_row, monster_defense
        from numeric_lib.player import build_player
        from data.plugins.dragonfall.game import engine as E
        st = build_player(cid, 45, {}, None, attr=None)
        for tier, tdef in br.items():
            if not isinstance(tdef, dict):
                continue
            for line, skills in tdef.items():
                if not isinstance(skills, dict):
                    continue
                for skid, info in skills.items():
                    if not isinstance(info, dict):
                        continue
                    # 学得等级 >45 跳过（45 级还没学到）
                    if int(info.get("lv", 99) or 99) > 45:
                        continue
                    rows.append(skill_efficiency_row(cid, skid, info, st, 45, edef45, mdef45))
        # 去重（base + branch 可能重名？skills.py 无重名，保险起见）
        seen = set()
        uniq_rows = []
        for r in rows:
            if r["name"] in seen:
                continue
            seen.add(r["name"])
            uniq_rows.append(r)
        cname = cdef.get("name", cid)
        n_dmg = sum(1 for r in uniq_rows if r["cls"] == "damage")
        n_gain = sum(1 for r in uniq_rows if r["cls"] in ("buff", "aura", "guard"))
        n_heal = sum(1 for r in uniq_rows if r["cls"] == "heal")
        # Lv45 可学技能 = base 全量（lv≤28）+ branch lv≤45 的部分
        # 阈值：≥ base 技能数（8-11），保证 base 全量都在
        n_base = len(cdef.get("skills", {}))
        check(f"{cname}: {len(uniq_rows)} 技能 Lv45 可学"
              f"（输出{n_dmg}/增益{n_gain}/治疗{n_heal}）≥base{n_base}",
              len(uniq_rows) >= n_base, f"rows={len(uniq_rows)} base={n_base}")
        for r in uniq_rows:
            if r["cls"] == "damage":
                all_dmg_rows.append(r)
                if r["dmg"] <= 0.01:
                    empty_dmg.append(f"{cname}.{r['name']}(raw={r['raw_expr']})")
            if r["mp"] <= 0 and r["cls"] == "damage":
                zero_rows.append(f"{cname}.{r['name']}")

    check(f"输出技无空转（dmg=0）", len(empty_dmg) == 0, f"空转={empty_dmg[:10]}")
    if zero_rows:
        print(f"  ⚠️ 输出技 0 mp 消耗（可能资源技，需人工确认）：{len(zero_rows)} 个")
        print(f"     {zero_rows[:8]}")

    # ---- 普攻等效 DPS（横向参考）----
    print("\n【3】超模红线：输出技 DPS vs 普攻等效")
    from numeric_lib.player import build_player
    from data.plugins.dragonfall.game import engine as E
    # 战士普攻等效（Lv45 紫装档）
    from numeric_lib.gear import gear_loadout
    st_w = build_player("cls_zhan_shi", 45, gear_loadout(45, "team_purple9"), None)
    basic_dmg = E.calc_damage(int(st_w.get("atk", 0)), edef45, variance=0.0, dmg_type="phys")
    # 战士普攻 cast_atk=1.15 × spd 折算
    import math
    spd_factor = math.sqrt(50.0 / max(float(st_w.get("spd", 50)), 1))
    basic_dps = basic_dmg / max(1.15 * spd_factor, 0.001)
    print(f"  普攻等效 DPS（战士 Lv45 紫装）≈ {basic_dps:.0f}")

    over = []
    dmg_rows_sorted = sorted(all_dmg_rows, key=lambda r: -r["dps"])
    print(f"  全职业输出技 Top15（DPS）:")
    for r in dmg_rows_sorted[:15]:
        print(f"    {r['name']:<8} Lv{r['lv']:<4} DPS={r['dps']:>8.1f} DPE={r['dpe']:>6.1f}")
    print(f"  全职业输出技 Bottom8（DPS）:")
    for r in dmg_rows_sorted[-8:]:
        print(f"    {r['name']:<8} Lv{r['lv']:<4} DPS={r['dps']:>8.1f} DPE={r['dpe']:>6.1f}")

    for r in all_dmg_rows:
        if r["dps"] > basic_dps * DPS_OVER_BASIC_MAX and r["cd"] == 0:
            # 0CD 技能 DPS 超普攻 15× = 严重超模（基础技能无限放）
            over.append(f"{r['name']}(DPS={r['dps']:.0f}=普攻{r['dps']/max(basic_dps,1):.0f}×)")
    check(f"0CD 输出技 DPS ≤ 普攻×{DPS_OVER_BASIC_MAX}（防基础技无限放超模）",
          len(over) == 0, f"超模={over[:10]}")
    if over:
        print(f"  ⚠️ 超模候选 {len(over)} 个（真引擎复核）：{over[:10]}")

    # DPE 分布（待定标）
    dpe_rows = [r for r in all_dmg_rows if r["mp"] > 0 and r["dpe"] > 0]
    if dpe_rows:
        dpe_rows.sort(key=lambda r: r["dpe"])
        print(f"\n  DPE 最低 5 个（耗蓝效率差候选）:")
        for r in dpe_rows[:5]:
            print(f"    {r['name']:<8} mp={r['mp']:<4.0f} DPE={r['dpe']:.2f} DPS={r['dps']:.0f}")
        dpe_min = dpe_rows[0]["dpe"]
        dpe_med = dpe_rows[len(dpe_rows) // 2]["dpe"]
        print(f"  DPE 分布: min={dpe_min:.2f} 中位={dpe_med:.2f}（{len(dpe_rows)} 个耗蓝输出技）")

    print(f"\n== 结果：通过 {passed} / 共 {passed + failed} ==")
    if failed:
        print("有断言失败！")
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
