# -*- coding: utf-8 -*-
"""core 层 · 世界族：垂钓 / 传送

验证 roll_fish / portal_cost 等世界交互逻辑。
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
    print("【core·世界族：垂钓】")
    rf = getattr(C, "roll_fish", None)
    if rf:
        f = rf()
        check("roll_fish 返回 dict", isinstance(f, dict) and "name" in f, str(f)[:80])
    else:
        check("roll_fish 可访问", False, "未暴露")

    print("【core·世界族：传送】")
    pc = getattr(C, "portal_cost", None)
    if pc:
        m = {"lv": 5}
        check("portal_cost 正数", pc(m) > 0, str(pc(m)))
        m2 = {"lv": 20}
        check("portal_cost 等级更高更贵", pc(m2) >= pc(m), "%s vs %s" % (pc(m), pc(m2)))
    else:
        check("portal_cost 可访问", False, "未暴露")

    print("【v56.2 怪物等级段曲线（乱秒修复）】")
    ms = getattr(C, "monster_stats", None)
    if ms:
        m1 = ms(10, "dps")
        m15 = ms(15, "dps")
        m30 = ms(30, "dps")
        m60 = ms(60, "dps")
        check("Lv≤15 怪数值不变(10级)", m1["hp"] == 180, "hp=%s" % m1["hp"])
        check("Lv≤15 怪数值不变(15级)", m15["hp"] == 255, "hp=%s" % m15["hp"])
        check("30级怪 hp 放大(1056)", m30["hp"] > 900 and m30["hp"] < 1300, "hp=%s" % m30["hp"])
        check("60级怪 hp 继续放大", m60["hp"] > m30["hp"] * 2, "%s vs %s" % (m60["hp"], m30["hp"]))
        check("30级怪 atk 不变(线性)", ms(30, "dps")["atk"] == int(12 + 3.5 * 29), "atk=%s" % ms(30, "dps")["atk"])
        check("60级怪 atk 放缓(<线性)", ms(60, "dps")["atk"] < 12 + 3.5 * 59, "atk=%s" % ms(60, "dps")["atk"])
        e1 = getattr(C, "monster_exp", None)
        if e1:
            check("30级怪经验补偿", e1(30, "dps") > 9 * 28, "exp=%s" % e1(30, "dps"))
    else:
        check("monster_stats 可访问", False, "未暴露")

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
