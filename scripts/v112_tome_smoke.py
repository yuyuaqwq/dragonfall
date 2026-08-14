# -*- coding: utf-8 -*-
"""v113 P1 技能书冒烟：物品数据/使用管线/源流校验/等级校验/正常学习
（v113 收敛：龙息之怒=战士攻线技，书挂 cls_zhan_shi；星陨斩/血之契约/野性呼唤书已删）"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # dragonfall/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))  # qqbot/

os.environ.setdefault("GWEN_GAME_DB", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tome_test.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")

from tests.conftest import FakeEvent, clean_db, run, make_player
from game import content as C
from game import db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()
    from data.plugins.dragonfall.main import Main
    m = Main(None)

    print("【1. 物品数据】")
    tomes = {k: v for k, v in C.ITEMS.items() if v.get("learn_skill")}
    check("技能书 7 本注册", len(tomes) == 7, str(len(tomes)))
    for k, v in tomes.items():
        ls = v["learn_skill"]
        info = None
        for cid in C.CLASSES:
            from game import engine as E
            info = E.skill_info(cid, ls)
            if info:
                break
        check(f"{v['name']} learn_skill={ls} 可解析", info is not None, ls)
        req = v.get("require_class")
        check(f"{v['name']} require_class={req} 有效", not req or req in C.CLASSES, req)

    print("【2. 源流校验】")
    # 刺客（非战士源流）用龙息之怒技能书（require cls_zhan_shi）→ 拒绝
    make_player("g1", "w0", "刺", "刺客", level=60)
    db.add_item("g1", "w0", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    ev = FakeEvent("g1", "w0", "使用 龙息之怒技能书")
    out = await run(m.use, ev)
    txt = "".join(str(x) for x in out)
    check("刺客使用战士书被源流拒绝", "战士" in txt and "不合" in txt, txt[:150])
    check("道具未消耗", db.count_item("g1", "w0", "i_tome_long_xi_zhi_nu") == 1, "")

    print("【3. 等级校验】")
    # 40 级战士（< Lv.55）用龙息之怒技能书 → 等级拒绝
    make_player("g1", "w1", "剑士", "战士", level=40)
    db.add_item("g1", "w1", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await run(m.use, FakeEvent("g1", "w1", "使用 龙息之怒技能书"))
    txt = "".join(str(x) for x in out)
    check("等级不足被拒", "Lv.55" in txt, txt[:150])
    check("道具未消耗(等级不足)", db.count_item("g1", "w1", "i_tome_long_xi_zhi_nu") == 1, "")

    print("【4. 正常学习】")
    # 60 级战士（>= Lv.55）用龙息之怒技能书 → 成功
    db.update_player("g1", "w1", level=60)
    p = db.get_player("g1", "w1")
    check("已学技能不含龙息之怒", "龙息之怒" not in p.get("learned_skills", []), str(p.get("learned_skills")))
    out = await run(m.use, FakeEvent("g1", "w1", "使用 龙息之怒技能书"))
    txt = "".join(str(x) for x in out)
    check("学习成功", "龙息之怒" in txt and "学会" in txt, txt[:150])
    p = db.get_player("g1", "w1")
    check("learned_skills 写入", "龙息之怒" in p.get("learned_skills", []), str(p.get("learned_skills")))
    check("道具已消耗", db.count_item("g1", "w1", "i_tome_long_xi_zhi_nu") == 0, "")
    # 重复使用 → 已学拦截
    db.add_item("g1", "w1", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await run(m.use, FakeEvent("g1", "w1", "使用 龙息之怒技能书"))
    txt = "".join(str(x) for x in out)
    check("重复学习拦截", "早已掌握" in txt, txt[:120])

    print("【5. 战斗可用性】")
    from game import engine as E
    from game import battle as BT
    p = db.get_player("g1", "w1")
    info = E.skill_info(p["class_name"], "龙息之怒")
    check("龙息之怒在战士技能表", info is not None and info.get("kind") == "真伤", str(info))
    b = BT.Battle("怪物", {"name": "T", "hp": 5000, "max_hp": 5000, "atk": 10, "def": 500, "spd": 5}, {}, p)
    hp0 = b.enemy["hp"]
    st = b._player_stats(p)
    b._player_skill(st, "龙息之怒", info, p)
    check("战士施放龙息之怒(真伤无视防御)", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")

    print(f"\n===== v113 技能书冒烟: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
