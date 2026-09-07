# -*- coding: utf-8 -*-
"""P2F-2 分段曲线表驱动化 逐 lv 等值探针（2026-09-07，wt_p2f2）

P2F-2 把 hp_stage_mult / atk_stage_mult / _boss_atk_stage 三条分段曲线从
函数体写死改为查 data 表（HP_STAGE_MULT / ATK_STAGE_MULT /
BOSS_ATK_STAGE_MULT_LEGACY），行为零变化。本测试用**独立复刻的旧公式参照**
（与 P2F-2 前 stats.py 实现逐行同构，勿改）做逐 lv 1..200 等值断言，
并锁 monster_curve 门禁关键点（boss Lv60 atk=1217 / dps Lv60 atk=608）与
curve_override 替换语义（hp_stage_mult/atk_stage_mult 仍须是模块函数可整体替换——
numeric_lib.monster.curve_override 依赖）。

⚠️ int 截断序铁律：monster_stats boss 分支两级 int（int(线性×_boss_atk_stage)
再 ×段乘区 int）绝不重排——等值断言含 monster_stats 全网格（role × lv 1..200 ×
area None/instance 全属性 dict）兜底。

运行：python tests/test_numeric_p2f2_curve_tables.py（exit=0 全绿）
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # tests/
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)                        # dragonfall/
_SCRIPTS_DIR = os.path.join(_PLUGIN_DIR, "scripts")
for _p in (_SCRIPTS_DIR, _PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa: E402,F401
setup_env()
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402
from data.plugins.dragonfall.game.data.stat_templates import (  # noqa: E402
    MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH,
    NORMAL_HP_STAGE_MULT, BOSS_ATK_STAGE_MULT, INSTANCE_BOSS_ATK_STAGE_MULT,
)
# P2F-2 新表落点：stat_templates（HP/ATK 曲线）/ equipment（分系）/ formula_skeleton（boss legacy + 参数）
try:
    from data.plugins.dragonfall.game.data import (  # noqa: E402
        HP_STAGE_MULT, ATK_STAGE_MULT, BOSS_ATK_STAGE_MULT_LEGACY,
        WEAPON_DIST, ARMOR_FAMILY, ARMOR_FAMILY_ALIAS,
    )
    _TABLES_AVAILABLE = True
except ImportError:  # P2F-2 前（表尚未下沉）：全部置 None，相关检查跳过
    HP_STAGE_MULT = ATK_STAGE_MULT = BOSS_ATK_STAGE_MULT_LEGACY = None
    WEAPON_DIST = ARMOR_FAMILY = ARMOR_FAMILY_ALIAS = None
    _TABLES_AVAILABLE = False

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

# ---------- 旧公式独立参照（与 P2F-2 前 stats.py 逐行同构，勿改） ----------
def _ref_hp_stage_mult(lv: int) -> float:
    if lv <= 15:
        return 1.0
    if lv <= 30:
        return 1.0 + (lv - 15) * 0.05
    if lv <= 60:
        return 1.75 + (lv - 30) * 0.03
    return 2.65 + (lv - 60) * 0.02

def _ref_atk_stage_mult(lv: int) -> float:
    if lv <= 30:
        return 1.0
    return 1.0 + (lv - 30) * 0.004

def _ref_boss_atk_stage(lv: int) -> float:
    if lv <= 30:
        return 1.0
    if lv <= 60:
        return 1.0 - (lv - 30) * 0.005
    return max(0.2, 0.85 - (lv - 60) * 0.004)

def _ref_stage_mult(segments, lv):
    """旧 _stage_mult 同构复刻（段表执行器参照）。"""
    if not segments:
        return 1.0
    if lv <= segments[0][0]:
        return 1.0
    mult = 1.0
    prev_max = 0
    for max_lv, slope in segments:
        if lv <= max_lv:
            return mult + (lv - prev_max) * slope
        mult += (max_lv - prev_max) * slope
        prev_max = max_lv
    return mult + (lv - prev_max) * segments[-1][1]

def _ref_monster_stats(lv, role, area=None):
    """P2F-2 前 monster_stats 完整复刻（结构 = 现实现，仅段曲线走旧公式）。"""
    base = MONSTER_ROLE_BASE[role]
    growth = MONSTER_ROLE_GROWTH[role]
    stats = {}
    for k in base:
        if k in ("dodge", "pene_phys", "pene_magi"):
            stats[k] = round(base[k] + growth.get(k, 0) * (lv - 1), 3)
        else:
            stats[k] = int(base[k] + growth[k] * (lv - 1))
    if role == "boss":
        stats["hp"] = int(stats["hp"] * min(1 + lv * 0.06, 3.0))
    if role == "elite":
        stats["hp"] = int(stats["hp"] * min(1 + lv * 0.04, 3.0))
    if role == "boss":
        stats["def"] = int(stats["def"] * 1.25)
        stats["mdef"] = int(stats["mdef"] * 1.25)
    if role == "elite":
        stats["def"] = int(stats["def"] * 1.15)
        stats["mdef"] = int(stats["mdef"] * 1.15)
    stats["hp"] = int(stats["hp"] * _ref_hp_stage_mult(lv))
    if role != "boss":
        stats["atk"] = int(stats["atk"] * _ref_atk_stage_mult(lv))
    if role in ("tank", "dps", "caster", "speedster", "healer"):
        stats["hp"] = int(stats["hp"] * _ref_stage_mult(NORMAL_HP_STAGE_MULT, lv))
    elif role == "boss" and area == "instance":
        stats["atk"] = int(int(stats["atk"] * _ref_boss_atk_stage(lv))
                           * _ref_stage_mult(INSTANCE_BOSS_ATK_STAGE_MULT, lv))
    elif role == "boss" and area != "instance":
        stats["atk"] = int(int(stats["atk"] * _ref_boss_atk_stage(lv))
                           * _ref_stage_mult(BOSS_ATK_STAGE_MULT, lv))
    if role == "boss":
        stats["dot_res"] = 0.9
    elif role == "elite":
        stats["dot_res"] = 0.8
    return stats

def main():
    print("【P2F-2 逐 lv 等值：hp_stage_mult / atk_stage_mult / _boss_atk_stage 1..200】")

    # 1) 曲线函数 == 旧公式参照（逐 lv 1..200，含 15/16/30/31/60/61 边界）
    bad = 0
    for lv in range(1, 201):
        if ST.hp_stage_mult(lv) != _ref_hp_stage_mult(lv):
            bad += 1
            print(f"    ❌ hp_stage_mult lv{lv}: got={ST.hp_stage_mult(lv)} ref={_ref_hp_stage_mult(lv)}")
        if ST.atk_stage_mult(lv) != _ref_atk_stage_mult(lv):
            bad += 1
            print(f"    ❌ atk_stage_mult lv{lv}: got={ST.atk_stage_mult(lv)} ref={_ref_atk_stage_mult(lv)}")
        if ST._boss_atk_stage(lv) != _ref_boss_atk_stage(lv):
            bad += 1
            print(f"    ❌ _boss_atk_stage lv{lv}: got={ST._boss_atk_stage(lv)} ref={_ref_boss_atk_stage(lv)}")
    check("3 曲线 × 逐 lv 1..200 == 旧公式参照（600 点）", bad == 0, f"bad={bad}")

    # 2) data 表 == 旧曲线逐 lv 等价（表驱动数据源单点校验；表未下沉时跳过）
    if not _TABLES_AVAILABLE:
        print("  ⏭️  表未下沉（P2F-2 前基线）——段表等价断言跳过")
    else:
        ok = all(_ref_stage_mult(HP_STAGE_MULT, lv) == _ref_hp_stage_mult(lv) for lv in range(1, 201))
        check("HP_STAGE_MULT 表(_stage_mult 语义) == 旧 hp_stage_mult（逐 lv 1..200）", ok)
        ok = all(_ref_stage_mult(ATK_STAGE_MULT, lv) == _ref_atk_stage_mult(lv) for lv in range(1, 201))
        check("ATK_STAGE_MULT 表 == 旧 atk_stage_mult（逐 lv 1..200）", ok)
        ok = True
        for lv in range(1, 201):
            ref = max(BOSS_ATK_STAGE_MULT_LEGACY["floor"],
                      _ref_stage_mult(BOSS_ATK_STAGE_MULT_LEGACY["seg"], lv))
            if ref != _ref_boss_atk_stage(lv):
                ok = False
                print(f"    ❌ boss 段表 lv{lv}: floor后={ref} ref={_ref_boss_atk_stage(lv)}")
        check("BOSS_ATK_STAGE_MULT_LEGACY 段表+floor(0.2) == 旧 _boss_atk_stage（逐 lv 1..200）", ok)

        # 5) 装备分系表已下沉 data（纯 dict 零函数，key/值完整）
        ok = (WEAPON_DIST["sword"]["atk"] == 1.0 and WEAPON_DIST["staff"]["matk"] == 1.0
              and len(WEAPON_DIST) == 8 and WEAPON_DIST["shield"]["atk"] == 0.3)
        check("WEAPON_DIST 下沉 data 且 8 系完整", ok)
        ok = (ARMOR_FAMILY["heavy"]["hp_mult"] == 1.6
              and ARMOR_FAMILY["cloth"]["mdef_mult"] == 1.5
              and ARMOR_FAMILY["leather"]["spd_mult"] == 1.3
              and ARMOR_FAMILY_ALIAS["str"] == "heavy"
              and ARMOR_FAMILY_ALIAS["agi"] == "leather"
              and ARMOR_FAMILY_ALIAS["int"] == "cloth")
        check("ARMOR_FAMILY / ARMOR_FAMILY_ALIAS 下沉 data 完整", ok)

    # 3) monster_stats 全网格等值：7 role × lv 1..200 × area(None/instance) 全属性 dict
    #    —— 锁两级 int 截断序（boss 分支 int(int(线性×_boss_atk_stage)×段乘区) 不重排）
    bad = 0
    roles = ["tank", "dps", "caster", "speedster", "healer", "elite", "boss"]
    for role in roles:
        for lv in range(1, 201):
            for area in (None, "instance"):
                got = ST.monster_stats(lv, role, area)
                ref = _ref_monster_stats(lv, role, area)
                if got != ref:
                    bad += 1
                    if bad <= 5:
                        print(f"    ❌ monster_stats({role},lv{lv},{area})\n"
                              f"       got={got}\n       ref={ref}")
    check("monster_stats 7 role × lv 1..200 × 2 area 全属性等值（2800 网格）",
          bad == 0, f"bad={bad}")

    # 4) 关键点锁定（monster_curve 门禁口径）
    s = ST.monster_stats(60, "boss")
    check("monster_curve 锁：boss Lv60 atk == 1217", s["atk"] == 1217, f"got={s['atk']}")
    s = ST.monster_stats(60, "dps")
    check("monster_curve 锁：dps Lv60 atk == 608", s["atk"] == 608, f"got={s['atk']}")
    s = ST.monster_stats(30, "boss")
    check("monster_curve 锁：boss Lv30 atk == 344", s["atk"] == 344, f"got={s['atk']}")
    sb = ST.monster_stats(60, "boss", "instance")
    check("area=instance boss 分支独立可跑（副本 vs 野外不同源）", sb["atk"] > 0)

    # 5→(已并入 §2 表下沉检查块) 装备分系表 checks move up; keep numbering comments minimal.
    # (WEAPON_DIST/ARMOR_FAMILY 断言已在 _TABLES_AVAILABLE 分支内执行)

    # 6) curve_override 替换语义：hp_stage_mult/atk_stage_mult 仍是模块级函数可整体替换
    _orig_h, _orig_a = ST.hp_stage_mult, ST.atk_stage_mult
    ST.hp_stage_mult = lambda lv: 2.0
    ST.atk_stage_mult = lambda lv: 1.5
    _ms = ST.monster_stats(5, "dps")
    ST.hp_stage_mult, ST.atk_stage_mult = _orig_h, _orig_a
    # dps lv5：hp 线性 165 × 2.0 → 330（NORMAL_HP_STAGE_MULT ≤15 段 1.0 不再叠）；
    # atk 线性 int(48) × 1.5 → 72
    check("curve_override 语义：替换 hp/atk_stage 后 monster_stats 消费新函数",
          _ms["hp"] == 330 and _ms["atk"] == 72,
          f"got hp={_ms['hp']} atk={_ms['atk']}")

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
