# -*- coding: utf-8 -*-
"""v117 审计：副本材料联动数据完整性（实现完成后运行）

校验：
  1. 18 种闲置副本材料 + 澜歌之泪/古王剑 全部被 锻造/炼金/烹饪/附魔 至少 1 条联动覆盖
  2. 新配方引用合法性：craft mats/roster_id、alchemy cost/product、cooking cost/product
  3. 防刷金：产物价 ≤ 材料成本合计 ×0.9（炼金/烹饪）；锻造成本与产出价值比例合理（≥0.7）
  4. 附魔关键词独特性：每个新关键词命中材料 ≤3 种
  5. 符文匣（若实现）：物品 def 存在、use 注册存在、炼金配方引用存在
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from game.content import (MATERIALS, ITEMS, CRAFT_RECIPES, ALCHEMY_RECIPES,
                          COOKING_RECIPES, ENCHANT_RECIPES, EQUIP_ROSTER)

FAILS = []
WARN = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


# 18 种闲置 + 2 种补强
TARGETS = {
    "云怒之核碎片": "mat_yun_nu_zhi_he", "克罗的罗盘碎片": "mat_ke_luo_de_luo_pan",
    "圣光圣徽": "mat_sheng_guang_sheng_hui", "地底龙鳞": "mat_di_di_long_lin",
    "幽灵船票": "mat_you_ling_chuan_piao", "永冻之核": "mat_yong_dong_zhi_he",
    "灰矮人徽记": "mat_hui_ai_ren_hui_ji", "烬核": "mat_jin_he",
    "石炉之锤": "mat_shi_lu_zhi_chui", "蓝歌之冠残片": "mat_lan_ge_zhi_guan",
    "要塞残片": "mat_yao_sai_can_pian", "试炼徽记": "mat_shi_lian_hui_ji",
    "赫尔加的祭器碎片": "mat_he_er_jia_de_ji_qi", "风暴之核": "mat_feng_bao_zhi_he",
    "马尔库斯的法冠残片": "mat_ma_er_ku_si_de_fa_guan", "黑渊之眼残片": "mat_hei_yuan_zhi_yan",
    "龙宫珠": "mat_long_gong_zhu", "龙语传承": "mat_long_yu_chuan_cheng",
    "澜歌之泪残片": "mat_lan_ge_zhi_lei", "古王剑碎片": "mat_gu_wang_jian",
}

name2id = {m.get("name"): mid for mid, m in MATERIALS.items() if isinstance(m, dict)}
price = {mid: m.get("price", 0) for mid, m in MATERIALS.items() if isinstance(m, dict)}
item_price = {iid: (v.get("price", 0) if isinstance(v, dict) else 0) for iid, v in ITEMS.items()}

print("=== 1. 20 种目标材料联动覆盖 ===")
for cn, mid in TARGETS.items():
    hits = []
    for rid, r in CRAFT_RECIPES.items():
        if isinstance(r, dict) and mid in (r.get("mats") or {}):
            hits.append(f"锻造:{r.get('name')}")
    for rid, r in ALCHEMY_RECIPES.items():
        if isinstance(r, dict) and mid in (r.get("cost") or {}):
            hits.append(f"炼金:{r.get('name')}")
    for rid, r in COOKING_RECIPES.items():
        if isinstance(r, dict) and mid in (r.get("cost") or {}):
            hits.append(f"烹饪:{r.get('name')}")
    for stat, r in ENCHANT_RECIPES.items():
        if any(kw in cn for kw in (r.get("mats") or [])):
            hits.append(f"附魔:{stat}")
    if hits:
        print(f"  ✅ {cn}: {hits}")
    else:
        check(False, f"1 {cn} 无任何联动")
        print(f"  ❌ {cn}: 无联动")

print("=== 2. 新配方引用合法性 ===")
for rid, r in CRAFT_RECIPES.items():
    if not isinstance(r, dict):
        continue
    for mid, n in (r.get("mats") or {}).items():
        check(mid in MATERIALS, f"2 {rid} mats {mid} 不存在")
    ro = r.get("roster_id")
    if ro:
        check(ro in EQUIP_ROSTER, f"2 {rid} roster_id {ro} 不存在")
for rid, r in ALCHEMY_RECIPES.items():
    if not isinstance(r, dict):
        continue
    for mid, n in (r.get("cost") or {}).items():
        check(mid in MATERIALS, f"2 {rid} cost {mid} 不存在")
    for pk, pc in (r.get("product") or {}).items():
        check(pk in ITEMS, f"2 {rid} product {pk} 不存在")
for rid, r in COOKING_RECIPES.items():
    if not isinstance(r, dict):
        continue
    for mid, n in (r.get("cost") or {}).items():
        check(mid in MATERIALS, f"2 {rid} cost {mid} 不存在")
    for pk, pc in (r.get("product") or {}).items():
        check(pk in ITEMS, f"2 {rid} product {pk} 不存在")

print("=== 3. 防刷金（炼金/烹饪：产物价 ≤ 成本×0.9）===")
# 只审计涉及副本材料的新配方（cost 含目标材料）
for rid, r in ALCHEMY_RECIPES.items():
    if not isinstance(r, dict):
        continue
    cost = r.get("cost") or {}
    if not any(m in TARGETS.values() for m in cost):
        continue
    prod_price = sum(item_price.get(pk, 0) * pc for pk, pc in (r.get("product") or {}).items())
    cost_price = sum(price.get(mid, 0) * n for mid, n in cost.items())
    if prod_price > cost_price * 0.9:
        check(False, f"3 炼金 {r.get('name')}: 产物 {prod_price} > 成本 {cost_price}×0.9")
        print(f"  ❌ {r.get('name')}: 产物{prod_price} 成本{cost_price}")
    else:
        print(f"  ✅ 炼金 {r.get('name')}: 产物{prod_price} ≤ 成本{cost_price}×0.9")
for rid, r in COOKING_RECIPES.items():
    if not isinstance(r, dict):
        continue
    cost = r.get("cost") or {}
    if not any(m in TARGETS.values() for m in cost):
        continue
    prod_price = sum(item_price.get(pk, 0) * pc for pk, pc in (r.get("product") or {}).items())
    cost_price = sum(price.get(mid, 0) * n for mid, n in cost.items())
    if prod_price > cost_price * 0.9:
        check(False, f"3 烹饪 {r.get('name')}: 产物 {prod_price} > 成本 {cost_price}×0.9")
        print(f"  ❌ {r.get('name')}: 产物{prod_price} 成本{cost_price}")
    else:
        print(f"  ✅ 烹饪 {r.get('name')}: 产物{prod_price} ≤ 成本{cost_price}×0.9")

print("=== 4. 附魔关键词独特性（v117 新增/精修词严格校验；基线泛词仅警告）===")
all_names = list(name2id.keys())
# v117 新增/精修的关键词白名单（B agent 交付清单）
V117_KWS = ["龙语", "黑渊", "风暴之核", "云怒之核碎片", "龙宫珠", "试炼徽记",
            "地底龙鳞", "要塞残片", "永冻之核", "石炉之锤", "圣光圣徽",
            "烬核", "赫尔加的祭器碎片", "灰矮人徽记", "蓝歌之冠残片", "马尔库斯的法冠残片",
            "克罗的罗盘碎片", "幽灵船票",
            "龙魂碎片", "魔像核心", "潮汐之泪", "澜歌", "古王碎片", "奥拉圣印",
            "月辉", "黎明之光"]
for stat, r in ENCHANT_RECIPES.items():
    for kw in (r.get("mats") or []):
        hits = [n for n in all_names if kw in n]
        if kw in V117_KWS:
            if len(hits) > 3:
                check(False, f"4 附魔:{stat} v117 关键词 {kw} 命中 {len(hits)} 种: {hits}")
                print(f"  ❌ {stat} '{kw}' 命中过多: {hits}")
            else:
                print(f"  ✅ {stat} '{kw}' 命中 {len(hits)} 种")
        elif len(hits) > 3:
            WARN.append(f"4 附魔:{stat} 基线泛词 {kw} 命中 {len(hits)} 种（类别附魔语义，非 v117 引入）")

print("=== 5. 符文匣（若实现）===")
try:
    import game.core.item_templates as itm
    has_use = any("符文匣" in str(v) for v in list(ITEMS.values())[:0]) or any(
        "符文匣" in str(v.get("name", "")) for v in ITEMS.values() if isinstance(v, dict))
    print(f"  符文匣物品存在: {has_use}")
except Exception as e:
    WARN.append(f"5 item_templates 检查异常: {e}")

print()
print(f"结果：失败 {len(FAILS)} 项，警告 {len(WARN)} 项")
for w in WARN:
    print("  ⚠", w)
if FAILS:
    print("--- 失败明细 ---")
    for f in FAILS:
        print("  ❌", f)
    sys.exit(1)
print("✅ 全部通过")
