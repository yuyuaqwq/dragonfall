# -*- coding: utf-8 -*-
"""v95.32 #403 修复验证：材料/消耗品/掉落源/配方显示全链路"""
import os, sys
sys.path.insert(0, os.path.abspath(r"C:\Users\yuyu\qqbot"))
os.environ.setdefault("GWEN_GAME_DB", os.path.abspath(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\test_game_data.db"))

from data.plugins.dragonfall.game import content as C

MISSING_MATS = ["mat_yao_jing_zhi_chen", "mat_zhi_zhu_du_nang", "mat_rong_yan_shi",
                "mat_shen_yuan_jing_gang", "mat_gui_hun_jing_hua", "mat_sheng_guang_yu_mao",
                "mat_xue_zhi_jing_hua", "mat_an_ying_sui_pian", "mat_huo_yan_he_xin",
                "mat_ling_hun_sui_pian", "mat_shou_ren_liao_ya", "mat_zuo_lang_quan_chi"]
MISSING_PROD = ["i_stone_upgrade", "i_stone_refine", "i_lucky_charm", "i_atk_potion", "i_crit_potion"]

fails = 0
print("=== 1. 材料定义 ===")
for k in MISSING_MATS:
    ok = k in C.MATERIALS and C.MATERIALS[k].get("name")
    print(f"  {k}: {'✅' if ok else '❌ 缺失'}")
    if not ok:
        fails += 1

print("=== 2. 消耗品定义 ===")
for k in MISSING_PROD:
    ok = k in C.ITEMS and C.ITEMS[k].get("name")
    print(f"  {k}: {'✅' if ok else '❌ 缺失'}")
    if not ok:
        fails += 1

print("=== 3. 中文名 resolve ===")
for cn in ["妖精之尘", "蜘蛛毒囊", "熔岩石", "深渊精钢", "鬼魂精华", "圣光羽毛",
           "雪之精华", "暗影碎片", "火焰核心", "灵魂碎片", "兽人獠牙", "座狼犬齿"]:
    mid = C.resolve("materials", cn)
    ok = mid in C.MATERIALS and C.display("materials", mid) == cn
    print(f"  {cn}: {'✅' if ok else '❌ resolve=' + str(mid)}")
    if not ok:
        fails += 1

print("=== 4. 炼金配方 cost/product 全部可解析 ===")
for rkey, r in C.ALCHEMY_RECIPES.items():
    bad = []
    for m, _c in r["cost"].items():
        if m not in C.MATERIALS and m not in C.ITEMS:
            bad.append(f"cost:{m}")
    for p, _c in r["product"].items():
        if p not in C.MATERIALS and p not in C.ITEMS:
            bad.append(f"prod:{p}")
    print(f"  {r['name']}({rkey}): {'✅' if not bad else '❌ ' + ','.join(bad)}")
    if bad:
        fails += 1

print("=== 5. sets.py 引用检查 ===")
import data.plugins.dragonfall.game.data.sets as sets_mod
for s in sets_mod.CLASS_SET_STAGES:
    mats = s.get("mats", {})
    bad = [m for m in mats if m not in C.MATERIALS]
    if bad:
        print(f"  {s.get('lv')}级段: ❌ {bad}")
        fails += 1
print("  CLASS_SET_STAGES 全部材料可解析 ✅")

print("=== 6. 掉落源中文名在怪物表（抽样） ===")
drops_in_game = []
for mp in C.MAPS:
    for sa in (mp.get("subareas") or []):
        for m in (sa.get("monsters") or []):
            drops_in_game.extend(m[5] if len(m) > 5 else [])
        for m in ([sa.get("elite")] if sa.get("elite") else []):
            if m:
                drops_in_game.extend(m[5] if len(m) > 5 else [])
        for m in ([sa.get("boss")] if sa.get("boss") else []):
            if m:
                drops_in_game.extend(m[5] if len(m) > 5 else [])
for cn in ["妖精之尘", "蜘蛛毒囊", "熔岩石", "深渊精钢", "鬼魂精华", "圣光羽毛",
           "雪之精华", "暗影碎片", "火焰核心", "灵魂碎片", "兽人獠牙", "座狼犬齿"]:
    ok = cn in drops_in_game
    print(f"  {cn}: {'✅ 有掉落源' if ok else '❌ 无掉落源'}")
    if not ok:
        fails += 1

print(f"\n{'全部通过 ✅' if fails == 0 else f'{fails} 项失败 ❌'}")
sys.exit(1 if fails else 0)
