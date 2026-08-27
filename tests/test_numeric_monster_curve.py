# -*- coding: utf-8 -*-
"""N03·交付2 怪物成长曲线快照（v130.9 数值测试框架）

锁定 6 角色（tank/dps/caster/speedster/elite/boss）× 5 等级（1/11/22/30/60）
的 hp/atk/def/spd：断言 = 当前代码实测值 + 公式一致性双锁。

公式（对照 data/stat_templates.py MONSTER_ROLE_BASE/GROWTH + core/stats.py）：
  base_stat = base + growth×(lv-1)（hp/atk/def/spd 均为 int 截断）
  等级段修正（v56.2，hp_stage_mult/atk_stage_mult）：
    hp_stage：lv≤15 →1.0；≤30 →1+(lv-15)×0.08；≤60 →2.2+(lv-30)×0.04；>60 →3.4+(lv-60)×0.03
    atk_stage：lv≤30 →1.0；≤60 →1-(lv-30)×0.005；>60 →max(0.2, 0.85-(lv-60)×0.004)
  角色修正：boss hp ×min(1+lv×0.06, 3.0)、elite hp ×min(1+lv×0.04, 3.0)（在段修正前）；
            boss def/mdef ×1.25、elite def/mdef ×1.15（int 截断后乘，再 int）
  dot_res：boss=0.9 / elite=0.8（非普通怪键）

运行：python tests/test_numeric_monster_curve.py（exit=0 全绿）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C  # noqa: E402
from data.plugins.dragonfall.game.core.stats import (  # noqa: E402
    monster_stats, hp_stage_mult, atk_stage_mult,
)

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

ROLES = ["tank", "dps", "caster", "speedster", "elite", "boss"]
LVS = [1, 11, 22, 30, 60]
# (hp, atk, def, spd) 实测锁定表（2026-08-27 baseline，打印后写死）
LOCK = {
    # v131 重标定（2026-08-27）：怪 HP×2/防御×2~4.5/攻击×1.4；boss 血量成长 58→145
    "tank":      {1: (60, 8, 7, 6), 11: (420, 43, 47, 9), 22: (1101, 81, 91, 12),
                  30: (1932, 109, 123, 14), 60: (5787, 181, 243, 23)},
    "dps":       {1: (45, 12, 4, 10), 11: (345, 62, 54, 20), 22: (911, 117, 109, 31),
                  30: (1601, 157, 149, 39), 60: (4809, 260, 299, 69)},
    "caster":    {1: (40, 5, 3, 9), 11: (260, 23, 38, 18), 22: (677, 42, 76, 27),
                  30: (1186, 57, 104, 35), 60: (3545, 94, 209, 62)},
    "speedster": {1: (35, 9, 3, 16), 11: (255, 44, 48, 34), 22: (670, 82, 97, 53),
                  30: (1177, 110, 133, 68), 60: (3532, 182, 268, 122)},
    "elite":     {1: (98, 14, 9, 11), 11: (1144, 79, 72, 26), 22: (3971, 150, 141, 42),
                  30: (8181, 202, 192, 54), 60: (33588, 337, 381, 99)},
    "boss":      {1: (169, 16, 12, 10), 11: (2672, 91, 60, 28), 22: (10037, 173, 111, 47),
                  30: (21388, 233, 150, 62), 60: (69284, 389, 292, 116)},
}

def expect_stats(lv, role):
    """按 stat_templates + stats.py 公式重算 (hp, atk, def, spd)——与实现同序。"""
    base = C.MONSTER_ROLE_BASE[role]
    growth = C.MONSTER_ROLE_GROWTH[role]
    hp = int(base["hp"] + growth["hp"] * (lv - 1))
    if role == "boss":
        hp = int(hp * min(1 + lv * 0.06, 3.0))
    elif role == "elite":
        hp = int(hp * min(1 + lv * 0.04, 3.0))
    hp = int(hp * hp_stage_mult(lv))
    atk = int(int(base["atk"] + growth["atk"] * (lv - 1)) * atk_stage_mult(lv))
    df = int(base["def"] + growth["def"] * (lv - 1))
    if role == "boss":
        df = int(df * 1.25)
    elif role == "elite":
        df = int(df * 1.15)
    spd = int(base["spd"] + growth["spd"] * (lv - 1))
    return hp, atk, df, spd

def main():
    print("【怪物成长曲线：6 role × 5 等级 hp/atk/def/spd】")
    print("  格式: role lv | hp atk def spd | 实测==锁定 | 实测==公式")
    for role in ROLES:
        for lv in LVS:
            s = monster_stats(lv, role)
            got = (s["hp"], s["atk"], s["def"], s["spd"])
            exp = LOCK[role][lv]
            fmt = expect_stats(lv, role)
            tag = f"{role} lv{lv}"
            check(f"{tag} 实测 == 锁定 {got}", got == exp, f"lock={exp}")
            check(f"{tag} 实测 == 公式 {got}", got == fmt, f"formula={fmt}")
            print(f"    {tag:16s} hp={s['hp']:6d} atk={s['atk']:5d} def={s['def']:4d} spd={s['spd']:4d}")
    print("\n【模板一致性复核：对照 base + growth×(lv-1) 线性部分】")
    print("  def：elite ×1.15 / boss ×1.25；spd：无修正 == 线性；"
          "hp：段修正 ≥ 线性；atk：lv≤30 == 线性，lv>30 放缓 < 线性")
    for role in ROLES:
        base = C.MONSTER_ROLE_BASE[role]
        growth = C.MONSTER_ROLE_GROWTH[role]
        for lv in LVS:
            lin_hp = int(base["hp"] + growth["hp"] * (lv - 1))
            lin_atk = int(base["atk"] + growth["atk"] * (lv - 1))
            lin_def = int(base["def"] + growth["def"] * (lv - 1))
            lin_spd = int(base["spd"] + growth["spd"] * (lv - 1))
            got = LOCK[role][lv]
            exp_def = int(lin_def * (1.25 if role == "boss" else 1.15 if role == "elite" else 1.0))
            check(f"{role} lv{lv} spd == 线性值（无修正）",
                  got[3] == lin_spd, f"got={got[3]} lin={lin_spd}")
            check(f"{role} lv{lv} def == 线性×角色修正",
                  got[2] == exp_def, f"got={got[2]} exp={exp_def} lin={lin_def}")
            check(f"{role} lv{lv} hp ≥ 线性值（段修正放大）",
                  got[0] >= lin_hp, f"got={got[0]} lin={lin_hp}")
            if lv <= 30:
                cond = got[1] == lin_atk
                msg = f"got={got[1]} lin={lin_atk}"
            else:
                cond = got[1] < lin_atk
                msg = f"got={got[1]} lin={lin_atk}（31级起放缓 ×1-(lv-30)×0.005）"
            check(f"{role} lv{lv} atk {'== 线性值' if lv <= 30 else '< 线性值（后期放缓）'}", cond, msg)

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)