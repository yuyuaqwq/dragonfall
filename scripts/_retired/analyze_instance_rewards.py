# -*- coding: utf-8 -*-
"""v115 分析：副本通关奖励 + 副本材料锻造产出等级（一次性工具）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data.instances import INSTANCES
from game.data.craft import CRAFT_RECIPES

print("=== 22 副本通关奖励（gold/exp/blueprint）===")
bp_total = 0
rows = []
for iid, ins in INSTANCES.items():
    rows.append((ins.get("lv") or 0, ins["name"], ins.get("gold"), ins.get("exp"), ins.get("blueprint"),
                 (ins.get("materials") or ins.get("mats") or ["?"])[0] if (ins.get("materials") or ins.get("mats")) else "无",
                 ins.get("mat_count")))
    if ins.get("blueprint"):
        bp_total += 1
for r in sorted(rows):
    print(f"  Lv.{r[0]} {r[1]}: gold={r[2]} exp={r[3]} blueprint={r[4]} 专属材料={r[5]}x{r[6]}")
print("蓝图副本数:", bp_total)

print()
print("=== 用副本材料的锻造配方（产出装备等级/部位/品质）===")
INST_MIDS = ("mat_ge_bu_lin_hui_ji", "mat_hai_yao_lin_pian", "mat_gu_lu_de_huang_guan",
             "mat_chen_xi_zhi_guan", "mat_ao_lan_zhi_zhu", "mat_mo_luo_zhi_guan",
             "mat_jie_ke_de_jin_gou")
lv_hist = {}
for rid, r in CRAFT_RECIPES.items():
    if not isinstance(r, dict):
        continue
    mats = r.get("mats") or {}
    if any(mid in mats for mid in INST_MIDS):
        lv_hist[r.get("name")] = (r.get("lv"), r.get("slot"), r.get("quality"))
for name, (lv, slot, q) in sorted(lv_hist.items(), key=lambda x: x[1][0] or 0):
    print(f"  {name}: lv={lv} slot={slot} q={q}")

# 副本材料总价对比：单次通关材料价值 vs 野图材料
print()
print("=== 副本材料售价区间 ===")
prices = sorted({m.get("price") for m in sys.modules.get("game.data.items", None) and __import__("game.data.items", fromlist=["MATERIALS"]).MATERIALS.values() if isinstance(m, dict) and m.get("price")})
print("全材料售价分布（抽样）:", prices[:10], "...", prices[-5:])
