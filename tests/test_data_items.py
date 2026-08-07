# -*- coding: utf-8 -*-
"""data 层 · 物品族：物品 / 材料 / 套装 / 配方 / 炼金 / 附魔

验证 ITEMS / MATERIALS / SETS / CRAFT_RECIPES / ALCHEMY_RECIPES / ENCHANT_RECIPES 的完整性。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


def main():
    print("【data·物品族：物品】")
    check("ITEMS key 为 ID（mat_/i_ 前缀）", list(C.ITEMS)[0].startswith(("i_", "mat_")), list(C.ITEMS)[0])
    potion = C.ITEMS.get("i_treatment_potion", {})
    check("i_treatment_potion.name=治疗药水", potion.get("name") == "治疗药水", str(potion)[:80])
    mat = C.resolve("materials", "狼皮")
    check("resolve(materials, 狼皮) 有值", bool(mat), str(mat))
    print("【data·物品族：材料】")
    check("MATERIALS 130 材料", len(C.MATERIALS) >= 100, str(len(C.MATERIALS)))
    check("材料含 狼皮", mat in C.MATERIALS, str(list(C.MATERIALS)[:5]))

    print("【data·物品族：套装】")
    check("SETS 42 套装", len(C.SETS) >= 30, str(len(C.SETS)))
    check("套装含部件定义", all(isinstance(v, dict) for v in C.SETS.values()), str(list(C.SETS)[:3]))

    print("【data·物品族：配方】")
    check("CRAFT_RECIPES 87 配方（名册化）", len(C.CRAFT_RECIPES) >= 80, str(len(C.CRAFT_RECIPES)))
    if C.CRAFT_RECIPES:
        r = next(iter(C.CRAFT_RECIPES.values()))
        check("配方含 mats", isinstance(r.get("mats"), dict) and len(r["mats"]) > 0, str(r)[:80])
    check("CRAFT_RECIPE_ALIASES 非空", len(C.CRAFT_RECIPE_ALIASES) > 0, str(len(C.CRAFT_RECIPE_ALIASES)))

    print("【data·物品族：武器配方 weapon_type 全英文 ID（v53.1）】")
    WT_IDS = ("sword", "staff", "bow", "mace", "dagger", "fist", "spear", "shield")
    bad_wt = [(k, r.get("name"), r.get("weapon_type")) for k, r in C.CRAFT_RECIPES.items()
              if r.get("slot") == "weapon" and r.get("weapon_type") not in WT_IDS]
    check("所有武器配方 weapon_type 英文 ID", not bad_wt, str(bad_wt[:3]))
    # 全部武器配方可锻造（v53.1 修复前：毕业套武器 weapon_type 中文 → craft_recipe_make KeyError）
    fail_make = []
    for k, r in C.CRAFT_RECIPES.items():
        if r.get("slot") == "weapon":
            try:
                eq = C.craft_recipe_make(k)
                if not eq or eq.get("name") != r.get("name"):
                    fail_make.append((k, r.get("name")))
            except Exception as e:
                fail_make.append((k, str(e)))
    check("全部武器配方可锻造且名字正确", not fail_make, str(fail_make[:3]))

    print("【data·物品族：毕业套武器名不撞白装前缀（v53.1）】")
    WHITE_PREFIX = set(C.EQUIP_NAME_PREFIX["white"])
    clash = []
    for cid, theme in C.CLASS_SET_THEMES.items():
        w0 = theme["weapons"][0]
        if any(w0.startswith(p) for p in WHITE_PREFIX):
            clash.append((theme.get("name"), w0))
    check("阶段1 武器名无粗制/陈旧等白装前缀", not clash, str(clash))
    # 毕业套武器配方全部存在且唯一（防同名牌双配方）
    from collections import Counter
    name_cnt = Counter()
    for cid, theme in C.CLASS_SET_THEMES.items():
        for w in theme["weapons"]:
            name_cnt[w] += 1
    dup = {n: c for n, c in name_cnt.items() if c > 1}
    check("毕业套武器名无重复", not dup, str(dup))

    print("【data·物品族：炼金/附魔】")
    check("ALCHEMY_RECIPES 非空", len(C.ALCHEMY_RECIPES) > 0, str(len(C.ALCHEMY_RECIPES)))
    check("ENCHANT_RECIPES 非空", len(C.ENCHANT_RECIPES) > 0, str(len(C.ENCHANT_RECIPES)))
    check("ENCHANT_STONES 非空", len(C.ENCHANT_STONES) > 0, str(len(C.ENCHANT_STONES)))

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
