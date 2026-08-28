# -*- coding: utf-8 -*-
"""v134.1 意见#47 冒烟：技能列表多等级效果曲线渲染（英雄联盟式）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def main():
    clean_db()
    m = Main()
    for cls, lv, name in (("战士", 10, "战士"), ("牧师", 15, "牧师"), ("刺客", 12, "刺客")):
        g = f"g_{cls}"
        q = f"q_{cls}"
        make_player(g, q, name, cls, level=lv)
        db.update_player(g, q, skill_points=500, cur_map="oak_town")
        p = m._player(g, q)
        # 学 3 个技能（含增益/治疗），升不同等级
        sid = None
        _table = C.PLAYER_SKILLS.get(C.resolve("classes", cls), {})
        # v134.1 意见#47：PLAYER_SKILLS[cls] 结构为 {"name":中文名, "skills":{技能表}}，取内层 skills
        if isinstance(_table, dict) and "skills" in _table:
            _table = _table["skills"]
        for sname, sinfo in _table.items():
            if isinstance(sinfo, dict) and sinfo.get("lv", 1) <= lv:
                sid = sname
                break
        if not sid:
            print(f"  ⚠️ {cls} 无可用技能，跳过")
            continue
        s1 = sid
        # 直接改库标记已学（learned_skills/skill_levels 写 ID——store 读回才稳定，中文名会被 resolve 混淆）
        db.update_player(g, q, learned_skills=[s1], skill_levels={s1: 1})
        p = m._player(g, q)
        out = m._skill_list_page(p, 1)
        print(f"\n== {cls} Lv.{lv} 技能列表 ==")
        for ln in out.splitlines():
            if ln.startswith(("1.", "  · ")):
                print(f"  {ln}")
        check(f"{cls} 技能列表有等级曲线(伤害)", "/" in out, out[:200])
        # 升级到 Lv.3 后曲线应保持全等级展示
        db.update_player(g, q, skill_levels={s1: 3})
        out3 = m._skill_list_page(m._player(g, q), 1)
        check(f"{cls} 技能升级 Lv.3 曲线仍全等级", "112%" in out3 and "148%" in out3, out3[:200])
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()
