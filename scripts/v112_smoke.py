# -*- coding: utf-8 -*-
"""v113 冒烟：隐藏线路由 + 传承授予 + 流派技能归属
（v113 收敛：龙裔线只留龙血流，魔剑士/符文剑士/圣殿骑士流派已删；星语线更名）"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # dragonfall/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))  # qqbot/

os.environ.setdefault("GWEN_GAME_DB", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "smoke_test.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")

from tests.conftest import FakeEvent, clean_db, make_player
from game import content as C
from game import db
from game.commands.player import PlayerCmds

async def main():
    g, q = "g1", "w1"
    clean_db()
    inst = PlayerCmds()
    # 1. 路由表（v113 单流派收敛后档位名全可路由）
    routes = PlayerCmds._hidden_class_routes(inst)
    checks = [
        ("route 龙血战士", routes.get("龙血战士")),
        ("route 龙裔斗士", routes.get("龙裔斗士")),
        ("route 龙魂战将", routes.get("龙魂战将")),
        ("route 时停", routes.get("时停")),
        ("route 暗杀", routes.get("暗杀")),
        ("route 暮刃大师", routes.get("暮刃大师")),
        ("route 武僧", routes.get("武僧")),
    ]
    for name, v in checks:
        print(f"{name}: {v}")
    aliases = PlayerCmds._hidden_alias_map(inst)
    for a in ("龙血", "龙裔", "时咒", "占星", "星运", "亡灵", "影武", "暗杀", "苦修", "武僧"):
        print(f"alias {a}: {aliases.get(a)}")
    # 2. 传承：40 级战士 → 龙裔线龙血流（dragonborn 血脉）
    make_player(g, q, cls="cls_zhan_shi", level=40)
    db.update_player(g, q, hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    p = db.get_player(g, q)
    ev = FakeEvent(g, q, "转职 龙血战士")
    out = []
    async for r in PlayerCmds()._evolve_hidden_generic(ev, g, q, p, "cls_dragon_oath", 1, 1):
        out.append(r if isinstance(r, str) else str(r))
    print("== 传承输出 ==")
    for line in out:
        print(" |", str(line)[:120])
    p = db.get_player(g, q)
    print("class:", p["class_name"], "tier:", p["class_tier"], "path:", p["evolve_path"])
    print("learned:", p.get("learned_skills"))
    assert p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 1 and p["evolve_path"] == 1
    assert "龙魂" in p.get("learned_skills", []) and "龙息" in p.get("learned_skills", [])
    # 3. 同职业升档：60 级 龙血 → 龙裔斗士（T2，流派保持 1）
    db.update_player(g, q, level=60)
    p = db.get_player(g, q)
    out = []
    async for r in PlayerCmds()._evolve_hidden_generic(ev, g, q, p, "cls_dragon_oath", 2, 1):
        out.append(r if isinstance(r, str) else str(r))
    p = db.get_player(g, q)
    print("== 升档 T2 ==", p["class_tier"], p["evolve_path"], p.get("learned_skills"))
    assert p["class_tier"] == 2 and p["evolve_path"] == 1
    # 4. 跨职业进入时咒线（法师 60 级 → 时停流派，60 级直接 T2；人类血脉默认即可）
    g2, q2 = "g2", "w2"
    make_player(g2, q2, cls="cls_fa_shi", level=60)
    db.update_player(g2, q2, hidden_class_unlock=["cls_chronomancer"])
    p2 = db.get_player(g2, q2)
    ev2 = FakeEvent(g2, q2, "转职 时律术士")
    out = []
    async for r in PlayerCmds()._evolve_hidden_generic(ev2, g2, q2, p2, "cls_chronomancer", 2, 1):
        out.append(r if isinstance(r, str) else str(r))
    p2 = db.get_player(g2, q2)
    print("== 时咒线 T2 进入 ==", p2["class_name"], p2["class_tier"], p2["evolve_path"])
    print("learned:", p2.get("learned_skills"))
    assert p2["class_tier"] == 2 and p2["evolve_path"] == 1
    assert "魔力贯穿" in p2.get("learned_skills", [])
    # 5. 流派归属：龙焰吐息属龙裔线 T3 龙魂战将
    from game import engine as E
    owner = E.branch_skill_owner("cls_dragon_oath", "龙焰吐息")
    print("branch_skill_owner 龙焰吐息:", owner)
    assert owner == (3, "龙魂战将")
    # 6. 核心资源
    rd = E.core_resource_def("cls_dragon_oath")
    print("core resource:", rd.get("name"), rd.get("key"))
    assert rd.get("key") == "dragon_might"
    print("\nSMOKE OK")

asyncio.run(main())
