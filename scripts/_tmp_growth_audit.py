# -*- coding: utf-8 -*-
"""《奥兰迪亚》玩家属性成长 vs 怪物属性成长 曲线审计脚本（只读，不改任何源码）

真实引擎输出：
  - 玩家面板：game.engine.player_final_stats(裸装 = 无装备/无属性点/未转职/无称号/无种族/无被动)
  - 怪物面板：game.core.drops.build_monster(四 role 普通怪, lv_jitter=0, 未知名 mid=纯模板无个体修正)
输出 markdown 报告：6 基础职业 × 9 等级 × 4 role 全比值表 + ATK/DEF 对抗成长趋势 + 碾压结论。
"""
import os
import sys

# 插件根 = 本脚本上一级目录；确保能 import game.*
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from game.content_rules.panel import player_final_stats# noqa: E402
from game.core.drops import build_monster          # noqa: E402
from game.data.classes import CLASSES              # noqa: E402

# ---------------- 参数 ----------------
LVLS = [1, 5, 10, 16, 22, 30, 45, 60, 80]
TREND_LVLS = [1, 5, 10, 11, 16, 22, 30, 45, 60, 80]   # 含 11：观察 16 级 hp 放大拐点前后
ROLES = ["tank", "dps", "speedster", "caster"]
ROLE_CN = {"tank": "坦克", "dps": "输出", "speedster": "敏捷", "caster": "施法"}
STATS = ["max_hp", "atk", "def", "spd", "matk", "mdef"]
STATS_SHORT = {"max_hp": "HP", "atk": "ATK", "def": "DEF", "spd": "SPD",
               "matk": "MATK", "mdef": "MDEF"}

# 6 基础职业（以 classes.py 实际 key 为准：排除见习 + 隐藏线）
BASE_KEYS = [k for k, v in CLASSES.items() if not v.get("hidden") and k != "cls_novice"]
CLS_CN = {k: CLASSES[k]["name"] for k in BASE_KEYS}

MAP_OBJ = {"id": "audit_map", "name": "审计地图"}


def player_panel(cls: str, lv: int) -> dict:
    """裸装面板：无装备 / 无自由属性点 / 未转职 / 无称号 / 无种族 / 无被动"""
    return player_final_stats(
        class_name=cls, level=lv, equipment={}, tier=0,
        attributes={}, evolve_path=0, title_bonus=None, race=None,
        learned_skills=[],
    )


def monster_panel(role: str, lv: int) -> dict:
    """普通怪面板：lv_jitter=0 固定等级；mid 故意用不在 MONSTER_MODS 的未知名 → 纯 role 模板"""
    return build_monster(("m_audit_plain", "审计普通怪", role, lv, [], []), MAP_OBJ, lv_jitter=0)


def cell_ratios(p: dict, m: dict) -> str:
    """六个属性的 玩家/怪 比值，一格显示"""
    parts = []
    for k in STATS:
        mv = m.get(k, 0) or 1
        parts.append(f"{STATS_SHORT[k]}{p.get(k, 0) / mv:.2f}")
    return " ".join(parts)


def first_ratio_le(seq, thr):
    """返回第一个比值 <=thr 的 (等级, 属性名, 值)；全 >thr 返回 None"""
    for lv, ratios in seq:
        for k, v in ratios.items():
            if v <= thr:
                return (lv, STATS_SHORT[k], v)
    return None


def main():
    out = []
    A = out.append

    # 缓存面板（含第三节成长率分段所需的 15/31 级）
    _ALL_LVLS = set(LVLS + TREND_LVLS + [15, 31])
    P = {c: {lv: player_panel(c, lv) for lv in _ALL_LVLS} for c in BASE_KEYS}
    M = {r: {lv: monster_panel(r, lv) for lv in _ALL_LVLS} for r in ROLES}

    A("# 《奥兰迪亚》玩家属性成长 vs 怪物属性成长 曲线审计报告")
    A("")
    A("> 数据全部来自真实引擎实测（只读分析，未改任何源码）：")
    A("> - 玩家面板：`game/engine.py player_final_stats()`，**裸装**（空装备/0 自由属性点/未转职/无称号/无种族/无被动）")
    A("> - 怪物面板：`game/core/drops.py build_monster()`，同等级普通怪四 role（tank/dps/speedster/caster），`lv_jitter=0` 固定等级、未知名 mid 无个体修正 = 纯 role 模板")
    A("> - 职业 key 以 `game/data/classes.py` 实际为准。注：任务猜测名 `cls_wild_hunter`(隐藏线 星语者)/`cls_quan_shi`(不存在) 均不对，")
    A(">   实际基础职业 = `cls_zhan_shi`/`cls_fa_shi`/`cls_you_xia`/`cls_mu_shi`/`cls_ci_ke`/`cls_wu_seng`")
    A("")
    A(f"基础职业：{', '.join(f'`{k}`({v})' for k, v in CLS_CN.items())}")
    A("")
    A("## 〇、怪物四 role 同等级面板速查（build_monster 实测）")
    A("")
    A("| 等级 | role | max_hp | atk | def | spd | matk | mdef |")
    A("|---|---|---|---|---|---|---|---|")
    for lv in LVLS:
        for r in ROLES:
            m = M[r][lv]
            A(f"| {lv} | {ROLE_CN[r]} | {m['max_hp']} | {m['atk']} | {m['def']} | {m['spd']} | {m['matk']} | {m['mdef']} |")
    A("")

    # ---------- 一、六职业 × 四 role 全比值表（每职业一张，格内 = HP ATK DEF SPD MATK MDEF 六个比值） ----------
    A("## 一、玩家裸装面板 ÷ 同等级普通怪面板 比值表（比值 >2 视为碾压）")
    A("")
    A("每格六个比值依次为 **HP / ATK / DEF / SPD / MATK / MDEF**（玩家÷怪）。")
    A("")
    for idx, c in enumerate(BASE_KEYS, 1):
        A(f"### 1.{idx} {CLS_CN[c]}（`{c}`）")
        A("")
        A("| 等级 | 坦克怪(tank) | 输出怪(dps) | 敏捷怪(speedster) | 施法怪(caster) |")
        A("|---|---|---|---|---|")
        for lv in LVLS:
            p = P[c][lv]
            cells = []
            for r in ROLES:
                cells.append(cell_ratios(p, M[r][lv]))
            A(f"| {lv} | {' | '.join(cells)} |")
        A("")

    # ---------- 二、ATK/DEF 对抗成长趋势 ----------
    A("## 二、攻击/防御对抗成长趋势（每级玩家 ATK÷怪 DEF 与 玩家 DEF÷怪 ATK）")
    A("")
    A("箭头 = 与上一采样级相比的涨跌（↑涨 ↓跌 →平）。怪物 ATK 31 级起放缓、HP 16 级起放大（v56.2 曲线），注意拐点。")
    A("")
    for idx, c in enumerate(BASE_KEYS, 1):
        A(f"### 2.{idx} {CLS_CN[c]}（`{c}`）")
        A("")
        A("| 等级 | ATK÷TANK.DEF | ATK÷DPS.DEF | ATK÷SPD.DEF | ATK÷CAST.DEF | DEF÷TANK.ATK | DEF÷DPS.ATK | DEF÷SPD.ATK | DEF÷CAST.ATK |")
        A("|---|---|---|---|---|---|---|---|")
        prev = None
        for lv in TREND_LVLS:
            p = P[c][lv]
            vals = []
            for r in ROLES:
                m = M[r][lv]
                vals.append(p["atk"] / (m["def"] or 1))
            for r in ROLES:
                m = M[r][lv]
                vals.append(p["def"] / (m["atk"] or 1))
            if prev is not None:
                row = [f"**{lv}**"]
                for i, v in enumerate(vals):
                    d = v - prev[i]
                    arrow = "→" if abs(d) < 0.005 else ("↑" if d > 0 else "↓")
                    row.append(f"{v:.2f}{arrow}")
            else:
                row = [str(lv)]
                for v in vals:
                    row.append(f"{v:.2f}")
            A("| " + " | ".join(row) + " |")
            prev = vals
        A("")

    # ---------- 三、每级平均成长率对比 ----------
    A("## 三、每级平均成长率对比（面板实测，1→80 级全程）")
    A("")
    A("| 职业 | ΔHP/级 | ΔATK/级 | ΔDEF/级 | ΔSPD/级 | ΔMATK/级 | ΔMDEF/级 |")
    A("|---|---|---|---|---|---|---|")
    for c in BASE_KEYS:
        p1, p80 = P[c][1], P[c][80]
        A(f"| {CLS_CN[c]} | {(p80['max_hp'] - p1['max_hp']) / 79:.1f} | {(p80['atk'] - p1['atk']) / 79:.2f} | "
          f"{(p80['def'] - p1['def']) / 79:.2f} | {(p80['spd'] - p1['spd']) / 79:.2f} | "
          f"{(p80['matk'] - p1['matk']) / 79:.2f} | {(p80['mdef'] - p1['mdef']) / 79:.2f} |")
    A("")
    A("| 怪 role | ΔHP/级(≤15) | ΔHP/级(16-30) | ΔHP/级(31+) | ΔATK/级(≤30) | ΔATK/级(31+) | ΔDEF/级 | ΔMATK/级 | ΔMDEF/级 | ΔSPD/级 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for r in ROLES:
        m1, m15, m16, m30, m31, m80 = (M[r][1], M[r][15], M[r][16], M[r][30], M[r][31], M[r][80])
        A(f"| {ROLE_CN[r]}怪 | {(m15['max_hp'] - m1['max_hp']) / 14:.1f} | {(m30['max_hp'] - m16['max_hp']) / 14:.1f} | "
          f"{(m80['max_hp'] - m31['max_hp']) / 49:.1f} | {(m30['atk'] - m1['atk']) / 29:.2f} | {(m80['atk'] - m31['atk']) / 49:.2f} | "
          f"{(m80['def'] - m1['def']) / 79:.2f} | {(m80['matk'] - m1['matk']) / 79:.2f} | {(m80['mdef'] - m1['mdef']) / 79:.2f} | "
          f"{(m80['spd'] - m1['spd']) / 79:.2f} |")
    A("")

    # ---------- 四、碾压起始等级 ----------
    A("## 四、碾压判定：从哪一级起玩家属性全面碾压同级怪（全部 6 项比值 >2 / 至少 4 项 >2）")
    A("")
    A("> 「全>2」列中 `Lv.X（首个≤2:YY）` 表示**该级起即存在 ≤2 的弱项属性 YY**（即从未达成六项全面碾压，短板属性起步就不足）；`—` 表示从未有 ≥4 项 >2。")
    A("> 判定采样等级：1/5/10/16/22/30/45/60/80。")
    A("")
    A("| 职业 | vs坦克怪 全>2 | vs坦克怪 ≥4项>2 | vs输出怪 全>2 | vs输出怪 ≥4项>2 | vs敏捷怪 全>2 | vs敏捷怪 ≥4项>2 | vs施法怪 全>2 | vs施法怪 ≥4项>2 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for c in BASE_KEYS:
        row = [f"{CLS_CN[c]}"]
        for r in ROLES:
            seq = []
            for lv in LVLS:
                p = P[c][lv]
                m = M[r][lv]
                seq.append((lv, {k: p.get(k, 0) / (m.get(k, 0) or 1) for k in ["max_hp", "atk", "def", "spd", "matk", "mdef"]}))
            hit_all = first_ratio_le(seq, 2.0)
            hit_4 = None
            for lv, ratios in seq:
                if sum(1 for v in ratios.values() if v > 2.0) >= 4:
                    hit_4 = lv
                    break
            if hit_all is None:
                row.append("Lv.1 即全>2")
            else:
                row.append(f"从未全面（{hit_all[0]}级首个≤2:{hit_all[1]}）")
            row.append(f"Lv.{hit_4}" if hit_4 else "—")
        A("| " + " | ".join(row) + " |")
    A("")

    report = "\n".join(out)
    print(report)

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_growth_audit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"\n[report saved] {report_path}")


if __name__ == "__main__":
    main()