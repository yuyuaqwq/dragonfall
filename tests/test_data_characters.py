# -*- coding: utf-8 -*-
"""data 层 · 角色族：职业 / 技能 / 分支 / 符文 / 称号

验证 CLASSES / PLAYER_SKILLS / BRANCH_SKILLS / RUNES / TITLES 的结构约定。
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
    print("【data·角色族：职业】")
    check("CLASSES 6 职业", len(C.CLASSES) >= 6, str(len(C.CLASSES)))
    check("职业含 战士", C.resolve("classes", "战士") in C.CLASSES, str(list(C.CLASSES)[:3]))
    check("职业含 法师", C.resolve("classes", "法师") in C.CLASSES, str(list(C.CLASSES)[:3]))
    cls = C.CLASSES.get(C.resolve("classes", "战士"), {})
    check("职业含基础技能表", isinstance(cls, dict), str(type(cls)))

    print("【data·角色族：技能】")
    check("PLAYER_SKILLS 6 职业+13隐藏", len(C.PLAYER_SKILLS) == 19 and C.PLAYER_SKILLS.get("cls_bard") is not None and C.PLAYER_SKILLS.get("cls_spellblade") is not None, str(len(C.PLAYER_SKILLS)))
    check("每职业有技能表", all(isinstance(v, dict) and len(v) > 0 for v in C.PLAYER_SKILLS.values()),
          str({k: len(v) for k, v in C.PLAYER_SKILLS.items()}))
    check("BRANCH_SKILLS 6 职业（隐藏单线无分支）", len(C.BRANCH_SKILLS) == 6, str(len(C.BRANCH_SKILLS)))
    check("每职业 3 分支（21 章三转体系 30/60/90）", all(len(v.get("branches", {})) == 3 for v in C.BRANCH_SKILLS.values()),
          str({k: len(v.get("branches", {})) for k, v in C.BRANCH_SKILLS.items()}))
    sk = C.resolve("skills", "烈焰冲击")
    check("resolve(skills, 烈焰冲击) 有值", bool(sk), str(sk))
    if sk:
        check("display(skills, ID)→烈焰冲击", C.display("skills", sk) == "烈焰冲击", C.display("skills", sk))

    print("【data·角色族：符文】")
    check("RUNES 16 个符文", len(C.RUNES) >= 10, str(len(C.RUNES)))
    check("符文含 残忍", C.resolve("runes", "残忍") in C.RUNES, str(list(C.RUNES)[:5]))
    check("符文值含 effect", all(isinstance(v, dict) and "effect" in v for v in C.RUNES.values()),
          str(list(C.RUNES.values())[0])[:60])

    print("【data·角色族：称号】")
    check("TITLES 非空", hasattr(C, "TITLES") and len(getattr(C, "TITLES", [])) > 0, "TITLES")

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
