# -*- coding: utf-8 -*-
"""N03·交付3 技能倍率快照（v130.9 数值测试框架）

锁定 12 职业（PLAYER_SKILLS 全量键）各 2 个代表技能的 power / mp / lv / SKILL_UP.p：
  基础技 = lv==1 的技能（无 lv1 则取排序首个）
  成型技 = lv∈[10,15] 档位最高的技能（无该档则取排序末个）
断言值 = 当前代码实测锁定（打印后写死，2026-08-27 baseline）。

数据现状说明：6 个隐藏职业（龙裔誓约/时咒法师/星语者/暗影神谕/暮影行者/淬势者）
在 PLAYER_SKILLS 仅登记 lv40 觉醒被动（星语者等 4 职仅 1 个技能），
其成型技能档位在 BRANCH_SKILLS（lv≥32）——按卡要求只取 PLAYER_SKILLS[cls]['skills']，
故隐藏职业快照为 lv40 被动现状（power=0），防误调同样生效。

运行：python tests/test_numeric_skill_power.py（exit=0 全绿）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C  # noqa: E402

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

# 锁定表：cid -> (基础技, 成型技)，每项 = (技能名, lv, power, mp, SKILL_UP.p)
# v151 职业重构：隐藏职业全删，6 基础职业数值按 v151 新表实测锁定
LOCK = {
    "cls_zhan_shi":     (("挥砍", 1, 1.0, 3, 12), ("旋风斩", 14, 0.946, 10, 12)),  # v133: 1.1→0.946 峰值红线
    "cls_fa_shi":       (("火球术", 1, 1.1, 5, 12), ("元素弹幕", 14, 0.7, 12, 9)),
    "cls_you_xia":      (("疾风连射", 1, 0.6, 5, 9), ("风之疾走", 14, 0, 0, 0)),
    "cls_mu_shi":       (("治愈术", 1, 1.0, 8, 15), ("圣光驱散", 12, 0, 10, 0)),
    "cls_ci_ke":        (("刺击", 1, 0.8, 3, 12), ("双刃乱舞", 14, 0.7, 8, 9)),
    "cls_wu_seng":      (("直拳", 1, 0.8, 3, 12), ("钢拳", 12, 1.3, 8, 12)),
}

def select(cls_skills):
    """与锁定表同口径的选择：基础技=lv1（无则首个）；成型技=[10,15]最高（无则末个）。"""
    rows = sorted(((i.get("lv", 0), i.get("name", ""), i) for i in cls_skills.values()))
    base = next((r for r in rows if r[0] == 1), rows[0] if rows else None)
    in_range = [r for r in rows if 10 <= r[0] <= 15]
    mature = in_range[-1] if in_range else (rows[-1] if rows else None)
    return base, mature

def main():
    cls_ids = list(C.PLAYER_SKILLS.keys())
    check("PLAYER_SKILLS 恰 6 职业", len(cls_ids) == 6, f"n={len(cls_ids)} ids={cls_ids}")
    for cid in LOCK:
        check(f"职业 {cid} 存在于 PLAYER_SKILLS", cid in C.PLAYER_SKILLS)

    print("【12 职业 × 2 代表技能 power/mp/lv + SKILL_UP.p 快照】")
    for cid, (ebase, emature) in LOCK.items():
        info = C.PLAYER_SKILLS[cid]
        cn = info.get("name", cid)
        skills = info.get("skills", {})
        bsel, msel = select(skills)
        for tag, sel, exp in (("基础技", bsel, ebase), ("成型技", msel, emature)):
            if sel is None:
                check(f"{cid}({cn}) {tag} 存在", False, "PLAYER_SKILLS 无技能条目")
                continue
            name = sel[1]
            got = (name, sel[0], sel[2].get("power", 0), sel[2].get("mp", 0),
                   C.SKILL_UP.get(name, {}).get("p", 0))
            check(f"{cid}({cn}) {tag}『{name}』lv={exp[1]} power={exp[2]} mp={exp[3]} p={exp[4]}",
                  got == exp, f"got={got}")
            print(f"    {cn:6s} {tag}『{name}』 lv={got[1]} power={got[2]} mp={got[3]} p={got[4]}")

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)