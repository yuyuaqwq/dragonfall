# -*- coding: utf-8 -*-
"""v112 冒烟回归：隐藏线路由 + 流派归属 + 核心资源 + 龙裔传承最小闭环

原型 scripts/v112_smoke.py（一次性产物，其 smoke_test.db 不再需要）。取其核心断言
转写为正式测试，验证隐藏职业路由/别名/传承/流派技能归属在数据收敛后仍成立：
  1) _hidden_class_routes：档位全名 → (cls_id, tier, 流派索引)
  2) _hidden_alias_map：短别名 → (cls_id, 流派索引)
  3) branch_skill_owner：龙焰吐息 → 龙裔线 T3 龙魂战将
  4) core_resource_def：龙裔线核心资源 key=dragon_might
  5) 龙裔传承最小闭环：40 级战士 + dragonborn 血脉 → cls_dragon_oath T1 path=1,
     习得 龙魂/龙息

刻意不转写 v112_smoke.py 里多段「同职业逐阶升档 + 跨职业进时咒」的完整演化流——
那部分强耦合 CLASSES 职业/技能数据，且并行 Agent(F1) 正在改 commands/player.py
（_branch_title 已见 F1 P1-1 改动），深演化断言易随数据/逻辑漂移而误红。仅保留数据
驱动、行为稳定的核心断言作回归。
"""
import os
import sys
import asyncio

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(HERE, "test_v112_smoke_regression.db"))
sys.path.insert(0, HERE)
from conftest import C, db, clean_db, make_player, FakeEvent  # noqa: E402
from game import engine as E  # noqa: E402
from game.commands.player import PlayerCmds  # noqa: E402

_passed = _failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print("  ✅ %s" % name)
    else:
        _failed += 1
        print("  ❌ %s %s" % (name, detail))


async def main():
    clean_db()
    inst = PlayerCmds()

    print("【隐藏线路由（档位全名 → (cls_id, tier, path)）】")
    routes = PlayerCmds._hidden_class_routes(inst)
    check("route 龙血战士 → 龙裔 T1 流派1",
          routes.get("龙血战士") == ("cls_dragon_oath", 1, 1), str(routes.get("龙血战士")))
    check("route 龙裔斗士 → 龙裔 T2 流派1",
          routes.get("龙裔斗士") == ("cls_dragon_oath", 2, 1), str(routes.get("龙裔斗士")))
    check("route 龙魂战将 → 龙裔 T3 流派1",
          routes.get("龙魂战将") == ("cls_dragon_oath", 3, 1), str(routes.get("龙魂战将")))
    check("route 时停线路由存在", routes.get("时停") is not None, str(routes.get("时停")))

    print("【隐藏短别名 → (cls_id, 流派索引)】")
    aliases = PlayerCmds._hidden_alias_map(inst)
    check("alias 龙血 → (cls_dragon_oath, 流派1)",
          aliases.get("龙血") == ("cls_dragon_oath", 1), str(aliases.get("龙血")))
    check("alias 时咒 → (cls_chronomancer, 流派1)",
          aliases.get("时咒") == ("cls_chronomancer", 1), str(aliases.get("时咒")))

    print("【流派归属 + 核心资源】")
    owner = E.branch_skill_owner("cls_dragon_oath", "龙焰吐息")
    check("branch_skill_owner 龙焰吐息 → (3, 龙魂战将)",
          owner == (3, "龙魂战将"), str(owner))
    rd = E.core_resource_def("cls_dragon_oath")
    check("core_resource_def key=dragon_might",
          isinstance(rd, dict) and rd.get("key") == "dragon_might", str(rd))

    print("【龙裔传承最小闭环（40级战士 + dragonborn 血脉 → 龙裔 T1）】")
    make_player("g1", "q1", "龙裔武者", "cls_zhan_shi", level=40)
    db.update_player("g1", "q1", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    p = db.get_player("g1", "q1")
    ev = FakeEvent("g1", "q1", "转职 龙血战士")
    out = []
    async for r in PlayerCmds()._evolve_hidden_generic(ev, "g1", "q1", p, "cls_dragon_oath", 1, 1):
        out.append(r)
    p2 = db.get_player("g1", "q1")
    check("传承后 class=cls_dragon_oath tier=1 path=1",
          p2["class_name"] == "cls_dragon_oath" and p2["class_tier"] == 1 and p2["evolve_path"] == 1,
          "class=%s tier=%s path=%s" % (p2["class_name"], p2.get("class_tier"), p2.get("evolve_path")))
    learned = p2.get("learned_skills", [])
    check("习得 龙魂/龙息", "龙魂" in learned and "龙息" in learned, str(learned))
    check("传承有输出文案", len(out) > 0, "输出为空")

    # 清理私有库文件
    tmp = db.DB_PATH
    for f in (tmp, tmp + "-journal", tmp + "-wal", tmp + "-shm"):
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass

    print("\n结果: %d 通过, %d 失败" % (_passed, _failed))
    return _failed == 0


if __name__ == "__main__":
    sys.exit(0 if asyncio.run(main()) else 1)
