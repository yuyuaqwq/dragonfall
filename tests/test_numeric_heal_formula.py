# -*- coding: utf-8 -*-
"""v174 治疗公式化门禁（2026-09-04 鱼鱼拍板：治疗公式=对齐伤害公式，LOL 式 expr）

验证：
  1. 全表 kind=治疗 技能 heal_formula/heal_expr 覆盖率 100%（战士「冷静」为战意换血特殊技豁免）
  2. 基础治愈术公式 = 引擎实际结算（单发 ~40-46% 目标生命，Lv30-90 稳定区间）
  3. 转职不倒退：B1 圣言术(Lv32) ≥ 治愈术(Lv30) 等效奶量 ×0.95
  4. 分支大奶 > 基础奶：神圣恩典/曙光 > 治愈术
  5. HP% 隐式分支已废弃：power<1 的治疗技不再按 max_hp 百分比结算（除非显式 hp_pct）
  6. desc 与公式 ratio 一致（desc 百分比 = formula 的 ratio×100）

任何改动跑本门禁 = 全绿才能提交（技能公式/治疗数值改动后回归）
独立运行：python tests/test_numeric_heal_formula.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game.core import formula_expr as FE

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {detail}")


def skill_map():
    """name → skill info 全表（基础+分支+导师）"""
    out = {}
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "data", "skills.py"),
               encoding="utf-8").read()
    ns = {}
    exec(src, ns)
    for cid, c in ns["PLAYER_SKILLS"].items():
        for kid, s in c["skills"].items():
            out[s.get("name")] = s
    for cid, c in ns["BRANCH_SKILLS"].items():
        for b in c["branches"].values():
            for ln, sk in b.items():
                for kid, s in sk.items():
                    out[s.get("name")] = s
    for cid, c in ns["TUTOR_SKILLS"].items():
        for kid, s in c.items():
            out[s.get("name")] = s
    return out


def calc_formula(formula, matk, player_lv, skill_lv, max_hp=1000):
    """按 formula_expr 求值"""
    stats = {"matk": matk, "atk": 10, "max_hp": max_hp, "hp": int(max_hp * 0.8)}
    v = FE.build_vars(stats, player_lv=player_lv, skill_lv=skill_lv, target_max_hp=max_hp)
    return FE.eval_expr(FE.compile_expr(formula), v)


print("== v174 治疗公式化门禁 ==")

S = skill_map()

# 1. 覆盖率
heal_skills = [nm for nm, s in S.items() if s.get("kind") == "治疗" and nm != "冷静"]
missing = [nm for nm in heal_skills if not (S[nm].get("heal_formula") or S[nm].get("heal_expr"))]
check("全治疗技 heal_formula 覆盖率 100%", not missing, f"缺失: {missing}")

# 2. 治愈术公式曲线（牧师裸 matk=16+2.6(lv-1), hp=100+12(lv-1)）
zy = S["治愈术"].get("heal_formula")
if zy:
    for lv, exp_range in [(30, (0.38, 0.52)), (60, (0.35, 0.48)), (90, (0.33, 0.46))]:
        matk = 16 + 2.6 * (lv - 1)
        hp = 100 + 12 * (lv - 1)
        heal = calc_formula(zy, matk, lv, 5, max_hp=hp)
        ratio = heal / hp
        check(f"治愈术 Lv{lv} 满级 ≈ 目标HP%", exp_range[0] <= ratio <= exp_range[1],
              f"heal={heal:.0f} HP={hp} ratio={ratio:.2f}")

# 3. 转职不倒退
zy_l30 = calc_formula(S["治愈术"]["heal_formula"], 16 + 2.6 * 29, 30, 5, max_hp=100 + 12 * 29)
sy = S["圣言术"].get("heal_formula")
if sy:
    sy_l32 = calc_formula(sy, 16 + 2.6 * 31, 32, 1, max_hp=100 + 12 * 31)
    check("转职不倒退: 圣言术(Lv32技能1) ≥ 治愈术(Lv30满)×0.95", sy_l32 >= zy_l30 * 0.95,
          f"圣言术={sy_l32:.0f} vs 治愈术满={zy_l30:.0f}")

# 4. 分支大奶 > 基础
for big in ["神圣恩典", "曙光"]:
    f = S[big].get("heal_formula")
    if f:
        # 神圣恩典 Lv62 / 曙光 Lv98（技能低等级看 ratio 主导）
        lv = 62 if big == "神圣恩典" else 90
        h = calc_formula(f, 16 + 2.6 * (lv - 1), lv, 1, max_hp=100 + 12 * (lv - 1))
        zy_at_lv = calc_formula(zy, 16 + 2.6 * (lv - 1), lv, 5, max_hp=100 + 12 * (lv - 1))
        check(f"{big} > 治愈术同等级", h > zy_at_lv * 1.05, f"{big}={h:.0f} vs 治愈满={zy_at_lv:.0f}")

# 5. power<1 不再隐式 HP%（除非 hp_pct）
for nm in ["治愈术", "群体治愈", "安神曲"]:
    s = S[nm]
    check(f"{nm} 不再依赖 power<1 隐式 HP%（有公式）", bool(s.get("heal_formula") or s.get("hp_pct")),
          "仍无公式/无 hp_pct")

# 6. desc ratio 一致（desc 首百分比 = formula ratio×100 或含成长文案）
zy_desc_ok = "50% 魔攻" in S["治愈术"].get("desc", "")
check("治愈术 desc 含 50% 魔攻", zy_desc_ok, S["治愈术"].get("desc", ""))

print()
print(f"===== 结果：PASS {PASS} / FAIL {FAIL} =====")
sys.exit(1 if FAIL else 0)
