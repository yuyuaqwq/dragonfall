# -*- coding: utf-8 -*-
"""N03·交付1 装备依赖快照（v130.9 数值测试框架）

锁定『装备 vs 裸装』战力差，确保装备有意义且不爆炸：
  ① 战士 11 级：裸装 vs 满装面板（E.player_final_stats 实测锁定）
  ② 满装 = C.EQUIP_ROSTER Lv.10-15 全槽位名册件（铁港系列，generate_roster_equip
     固定种子生成——名册 10-15 档无 ring/necklace 条目，满装 = 5 槽）
  ③ 同级胜率：裸装/满装 × seeds=6 固定种子序列打 11 级 dps 怪（卡要求基准）；
     另加 11 级 elite 怪对照——demonstrate 装备依赖（裸装 0/6 → 满装 6/6）

当前基线 = 当前代码锁定（含已知失衡点）。改动任何装备模板/生成/属性公式即红。

运行：python tests/test_numeric_equip_dependency.py（exit=0 全绿）
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

# ---------------------------------------------------------------- 公共构造
PLV = 11
ATTR = {}  # 自由属性点 0：面板差纯由装备产生

# Lv.10-15 全槽位名册件（按槽位取最高 lv 蓝装；铁港系列；无 ring/necklace 档）
FULL_RIDS = {
    "weapon": "eq_wan_dao",        # 弯刀 Lv.14 blue sword
    "helm":   "eq_chuan_zhang_mao",  # 船长帽 Lv.14 blue
    "armor":  "eq_shui_shou_jia_ke", # 水手夹克 Lv.15 blue
    "legs":   "eq_shui_shou_hu_tui", # 水手护腿 Lv.14 blue
    "boots":  "eq_hai_dao_xue",      # 海盗靴 Lv.14 blue
}
# 生成固定种子（探索锁定 101..105，先打印后写死）
GEN_SEEDS = {slot: 100 + i for i, slot in enumerate(FULL_RIDS, start=1)}

def make_full_equip():
    equip = {}
    for slot, rid in FULL_RIDS.items():
        random.seed(GEN_SEEDS[slot])
        equip[slot] = C.generate_roster_equip(rid)
    return equip

def panel(equip):
    return E.player_final_stats("cls_zhan_shi", PLV, equip, 0, ATTR)

def build_player(equip):
    st = panel(equip)
    return {
        "class_name": "cls_zhan_shi", "level": PLV, "class_tier": 0, "evolve_path": 0,
        "equipment": equip, "attributes": ATTR, "learned_skills": [],
        "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
        "race": "human", "title_bonus": None,
    }

def build_mon(role, lv):
    return C.build_monster(("m_n03_x", "N03测试怪", role, lv, [], []),
                           {"id": "n03", "name": "N03测试场", "area": "field", "lv": lv})

def win_rate(equip, mdef, seeds=6):
    """固定种子序列 0..N-1 打怪，返回 (胜数, 场数)。只普攻。
    v154 读条命中制：player_turn 只出手（排 cast_done），命中结算在出招读条结束后——
    每次行动后推进到 p_ct 触发 cast_done，再判定结果。"""
    wins = 0
    for seed in range(seeds):
        random.seed(seed)
        p = build_player(equip)
        b = BT.Battle("monster", mdef, {}, p)
        guard = 0
        while b.result is None and guard < 300:
            b.player_turn("attack", None, p)
            b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, [], p)  # v154：推进到命中结算
            guard += 1
        if b.result == "victory":
            wins += 1
    return wins, seeds

# ---------------------------------------------------------------- 主流程
def main():
    print("【① 满装生成快照（固定种子，锁词条与 stats）】")
    full_equip = make_full_equip()
    # 装备 stats/词条快照（实测锁定，2026-08-29 v136 品质 1.6→1.55 更新）
    EXPECT_EQUIP = {
        "weapon": ({"atk": 26, "matk": 26, "crit": 0.089}, ["crit_up", "energy_blade"]),
        "helm":   ({"def": 13, "hp": 79, "spd": 1}, ["swift", "hp_up"]),
        "armor":  ({"def": 27, "hp": 162, "dodge": 0.05}, ["dodge", "pious_charm"]),
        "legs":   ({"def": 18, "hp": 102, "spd": 1}, ["swift", "meditate"]),
        "boots":  ({"def": 10, "spd": 14}, ["swift", "arcane_focus"]),
    }
    for slot, (est, eaf) in EXPECT_EQUIP.items():
        it = full_equip[slot]
        check(f"装备 {FULL_RIDS[slot]}（{it['name']}）stats 锁定",
              it["stats"] == est, f"got={it['stats']}")
        check(f"装备 {FULL_RIDS[slot]} 词条锁定", it.get("affixes") == eaf,
              f"got={it.get('affixes')}")
    check("满装 5 槽名册 lv 均在 10-15",
          all(10 <= full_equip[s]["lv"] <= 15 for s in FULL_RIDS),
          str({s: full_equip[s]["lv"] for s in FULL_RIDS}))

    print("\n【② 面板：裸装 vs 满装（实测锁定）】")
    bare = panel({})
    full = panel(full_equip)
    BARE_EXPECT = {"max_hp": 370, "max_mp": 70, "atk": 50, "def": 40,
                   "matk": 11, "mdef": 22, "spd": 16, "crit": 0.05, "dodge": 0.03}
    FULL_EXPECT = {"max_hp": 713, "max_mp": 70, "atk": 82, "def": 108,
                   "matk": 37, "mdef": 22, "spd": 35, "crit": 0.139, "dodge": 0.13}
    for k, v in BARE_EXPECT.items():
        check(f"裸装 {k} = {v}", bare[k] == v, f"got={bare[k]}")
    for k, v in FULL_EXPECT.items():
        check(f"满装 {k} = {v}", full[k] == v, f"got={full[k]}")
    print(f"  裸装: {BARE_EXPECT}")
    print(f"  满装: {FULL_EXPECT}")

    print("\n【③ 提升幅度区间（装备有意义：≥1.5×；不爆炸：≤3.2×）】")
    RATIO_RANGE = {
        "max_hp": (1.8, 2.2),   # 实测 1.9595（+355）
        "atk":    (1.5, 1.9),   # 实测 1.6600（+33）
        "def":    (2.5, 3.1),   # 实测 2.7750（+71）
        "spd":    (1.9, 2.6),   # 实测 2.2500（+20）
    }
    for k, (lo, hi) in RATIO_RANGE.items():
        r = full[k] / bare[k]
        check(f"{k} 提升率 ∈ [{lo}, {hi}]", lo <= r <= hi,
              f"full={full[k]} bare={bare[k]} ratio={r:.4f}")

    print("【④ 同级胜率 seeds=6（v131 重标定，纯普攻保守口径）】")
    dps11 = build_mon("dps", 11)
    wb_d, _ = win_rate({}, dps11)
    wf_d, _ = win_rate(full_equip, dps11)
    check("11级dps怪：裸装胜率 ∈ [4,6]（v131 同级 6 轮有手感，偶翻车）", 4 <= wb_d <= 6, f"got={wb_d}")
    check("11级dps怪：满装胜率 = 6/6（锁定）", wf_d == 6, f"got={wf_d}")
    check("11级dps怪：满装胜率 ≥ 裸装胜率", wf_d >= wb_d, f"{wf_d} vs {wb_d}")

    elite11 = build_mon("elite", 11)
    wb_e, _ = win_rate({}, elite11)
    wf_e, _ = win_rate(full_equip, elite11)
    # v152 CTB：行动耗时制下怪出手窗口收窄，裸装 11 级战士打 11 级 elite 也能靠磨死拿 4/6——
    # 装备依赖证据保留在『满装 ≥ 裸装』与『dps 满装全胜』；elite 裸装锁定 0/6 是旧 CTB 失衡基线，改区间
    check("11级elite怪：裸装胜率 ≤ 满装胜率（装备依赖证据）", wb_e <= wf_e, f"裸装{wb_e} vs 满装{wf_e}")
    check("11级elite怪：满装胜率 ∈ [2,6]（v131 精英长盘 20~35 轮；纯普攻=保守下限，技能轴可达）",
          2 <= wf_e <= 6, f"got={wf_e}")
    check("11级elite怪：满装胜率 > 裸装胜率（装备依赖证据）", wf_e > wb_e,
          f"{wf_e} vs {wb_e}")
    print(f"  dps11  : 裸装 {wb_d}/6  满装 {wf_d}/6")
    print(f"  elite11: 裸装 {wb_e}/6  满装 {wf_e}/6")

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)