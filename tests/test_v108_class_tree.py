# -*- coding: utf-8 -*-
"""v112 职业树·主题线制测试（test_v108_class_tree.py，v112 重写）

覆盖：
 1. 数据完整性：6 隐藏线 src_base；战士守线改名；职业名+分支名无重名；档位全名全部可路由
 2. 修为继承：40 级转 = T1；60 级转 = T2（直接）；90 级转 = T3；技能按等级继承（线级+流派）
 3. 等级门槛拦截：40 级转 T2/T3 被拒
 4. 同职业逐阶升 T1→T2→T3；跳档拦截；已是高阶提示；跨职业直接 T3（修为继承）
 5. 『转职』无参数（隐藏职业）显示下一阶 / 已满
 6. 『转职重置』隐藏职业回渊源根基（付费）
 7. 六线统一 40/60/90 档位 + 流派路由（『转职 收割』→ 暮影线收割流派）

运行：python tests/test_v108_class_tree.py（exit=0 全绿）
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, run, make_player

passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

async def cmd(m, handler_name, gid, qid, msg):
    ev = __import__("conftest").FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return "".join(str(x) for x in results)

async def main():
    clean_db()
    m = Main(None)

    print("[1] 数据完整性")
    hidden = {k: v for k, v in C.CLASSES.items() if v.get("hidden")}
    check("隐藏职业 6 线", len(hidden) == 6, str(len(hidden)))
    check("全部有 src_base 且为血缘职业",
          all(v.get("src_base") and not C.CLASSES[v["src_base"]].get("hidden") for v in hidden.values()),
          str([(k, v.get("src_base")) for k, v in hidden.items() if not v.get("src_base") or C.CLASSES.get(v["src_base"], {}).get("hidden")]))
    zb = C.CLASSES["cls_zhan_shi"]["evolve_branches"]
    check("战士守线改名 坚盾卫士/坚城统帅",
          zb[2] == ["狂战统领", "坚盾卫士"] and zb[3] == ["战争领主", "坚城统帅"], str(zb))
    # 命名唯一性：职业名 + 全部档位名
    names = []
    for cls_id, cls in C.CLASSES.items():
        names.append(cls["name"])
        for t, brs in (cls.get("evolve_branches") or {}).items():
            names.extend(brs)
    dup_raw = [n for n in set(names) if names.count(n) > 1]
    # v112.3：诗人回归牧师攻线后，已无『职业名 == 自身 T1 档位名』的隐藏线（原独立诗人职业），
    # 合法自匹配集合为空——职业名/档位名全库必须严格无重名
    legal_self = {cls["name"] for cls in C.CLASSES.values() if cls.get("hidden")}
    dup = [n for n in dup_raw if n not in legal_self]
    check("职业名+档位名无重名", not dup, str(dup))
    # v113：隐藏档位全名 = 龙裔3+时咒3+星语3+暗影3+暮影3+苦修3 = 18 名，全部可路由
    routes = m._hidden_class_routes()
    hidden_names = []
    for cls_id, cls in hidden.items():
        for t, brs in (cls.get("evolve_branches") or {}).items():
            hidden_names.extend(brs)
    check("隐藏档位名全部入路由表(18)",
          all(n in routes for n in hidden_names) and len(hidden_names) == len(set(hidden_names)),
          f"{len(hidden_names)} 名 / 路由 {len(routes)}")
    # v113：路由带流派索引（单流派收敛——龙血 T1 path=1 / 龙裔斗士 T2 path=1 / 时间领主 T3 path=1）
    check("路由带流派索引", routes.get("龙血战士") == ("cls_dragon_oath", 1, 1)
          and routes.get("龙裔斗士") == ("cls_dragon_oath", 2, 1)
          and routes.get("时间领主") == ("cls_chronomancer", 3, 1), str(routes.get("龙血战士")))

    print("[2] 修为继承（转职 tier 按等级）")
    make_player("g1", "p1", "修一", "战士", level=40)
    db.update_player("g1", "p1", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    out = await cmd(m, "evolve", "g1", "p1", "转职 龙血战士")
    p = db.get_player("g1", "p1")
    check("40 级转龙血战士 = T1(龙裔线·龙血流)",
          p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    make_player("g1", "p2", "修二", "战士", level=60)
    db.update_player("g1", "p2", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    out = await cmd(m, "evolve", "g1", "p2", "转职 龙裔斗士")
    p = db.get_player("g1", "p2")
    check("60 级转龙裔斗士 = T2", p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 2,
          str((p["class_name"], p["class_tier"])))
    check("T2 文案显示龙裔斗士", "龙裔斗士" in out, out[:150])
    make_player("g1", "p3", "修三", "战士", level=90)
    db.update_player("g1", "p3", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    out = await cmd(m, "evolve", "g1", "p3", "转职 龙魂战将")
    p = db.get_player("g1", "p3")
    check("90 级转龙魂战将 = T3", p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 3,
          str((p["class_name"], p["class_tier"])))
    # v112 技能继承：线级基础 + 本流派（龙血 path=1）全档分支技能 lv<=90
    expect90 = []
    for _s, _i in C.PLAYER_SKILLS["cls_dragon_oath"]["skills"].items():
        if _i["lv"] <= 90:
            expect90.append(C.display("skills", _s))
    for _t in (1, 2, 3):
        _bn = C.CLASSES["cls_dragon_oath"]["evolve_branches"][_t][0]
        for _s, _i in C.BRANCH_SKILLS["cls_dragon_oath"]["branches"][_t][_bn].items():
            if _i["lv"] <= 90:
                expect90.append(_s)
    check("技能继承 lv<=90 全给(线级+龙血流派)", set(p["learned_skills"]) == set(expect90),
          f"{len(p['learned_skills'])}/{len(expect90)} 差: {set(p['learned_skills']) ^ set(expect90)}")

    print("[3] 等级门槛拦截")
    make_player("g1", "p4", "修四", "法师", level=40)
    db.update_player("g1", "p4", hidden_class_unlock=["cls_chronomancer"])
    out = await cmd(m, "evolve", "g1", "p4", "转职 时律术士")
    check("40 级转时律术士(T2)被拒", "Lv.60" in out, out[:150])
    out = await cmd(m, "evolve", "g1", "p4", "转职 时间领主")
    check("40 级转时间领主(T3)被拒", "Lv.90" in out, out[:150])
    out = await cmd(m, "evolve", "g1", "p4", "转职 时停")
    check("40 级转时停(T1)成功", "传承完成" in out, out[:150])

    print("[4] 同职业逐阶升 + 跳档/跨职业")
    db.update_player("g1", "p4", level=60)
    out = await cmd(m, "evolve", "g1", "p4", "转职 时律术士")
    p = db.get_player("g1", "p4")
    check("T1→T2 逐阶升", p["class_tier"] == 2, str(p["class_tier"]))
    out = await cmd(m, "evolve", "g1", "p4", "转职 时停")
    check("已是高阶提示", "已是时咒法师" in out, out[:120])
    db.update_player("g1", "p4", level=90)
    out = await cmd(m, "evolve", "g1", "p4", "转职 时间领主")
    p = db.get_player("g1", "p4")
    check("T2→T3 逐阶升", p["class_tier"] == 3, str(p["class_tier"]))
    out = await cmd(m, "evolve", "g1", "p4", "转职 时间领主")
    check("满阶提示已是", "已是时咒法师" in out, out[:120])
    # 跨职业 90 级直接 T3（修为继承，未先转隐藏）
    make_player("g1", "p5", "修五", "法师", level=90)
    db.update_player("g1", "p5", hidden_class_unlock=["cls_chronomancer"])
    out = await cmd(m, "evolve", "g1", "p5", "转职 时间领主")
    p = db.get_player("g1", "p5")
    check("90 级跨职业直接 T3 成功", "传承完成" in out and p["class_tier"] == 3, str((out[:80], p["class_tier"])))
    # 同职业 T1 跳 T3 拦截
    make_player("g1", "p6", "修六", "法师", level=90)
    db.update_player("g1", "p6", hidden_class_unlock=["cls_chronomancer"])
    await cmd(m, "evolve", "g1", "p6", "转职 时停")
    out = await cmd(m, "evolve", "g1", "p6", "转职 时间领主")
    check("同职业跳档拦截", "时机未到" in out, out[:120])

    print("[5] 『转职』无参数（隐藏职业显示下一阶/已满）")
    out = await cmd(m, "evolve", "g1", "p6", "转职")
    check("隐藏职业显示下一阶", "下一阶" in out and "时律术士" in out, out[:150])
    out = await cmd(m, "evolve", "g1", "p5", "转职")
    check("满阶显示传承完成", "已完成全部传承" in out, out[:120])

    print("[6] 『转职重置』隐藏职业回渊源")
    db.update_player("g1", "p5", gold=5000)
    gold0 = db.get_player("g1", "p5")["gold"]
    out = await cmd(m, "evolve_reset", "g1", "p5", "转职重置")
    p = db.get_player("g1", "p5")
    check("重置回法师", p["class_name"] == "cls_fa_shi" and p["class_tier"] == 0 and p["evolve_path"] == 0,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    check("重置扣费", p["gold"] < gold0, str(p["gold"]))
    check("重置文案回根基", "根基职业" in out and "法师" in out, out[:150])

    print("[7] 统一 40/60/90 档位")
    # 暗影神谕（单流派）：牧师 40 → 暗影祭司 T1
    make_player("g1", "p7b", "亡语", "牧师", level=40)
    db.update_player("g1", "p7b", hidden_class_unlock=["cls_hymn"], race="orc")
    out = await cmd(m, "evolve", "g1", "p7b", "转职 暗影祭司")
    p = db.get_player("g1", "p7b")
    check("40 级暗影祭司 = T1(暗影神谕)",
          p["class_name"] == "cls_hymn" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    # 暮影线（单流派·暗杀）：刺客 60 级『转职 暗杀』= 暗杀流派 T1（T1 流派名入路由）；
    # 再『转职 暮刃大师』升 T2 保留流派
    make_player("g1", "p8", "影修", "刺客", level=60)
    db.update_player("g1", "p8", hidden_class_unlock=["cls_shadow_blade"], race="halfling")
    out = await cmd(m, "evolve", "g1", "p8", "转职 暗杀")
    p = db.get_player("g1", "p8")
    check("60 级『转职 暗杀』= T1 暗杀流派",
          p["class_name"] == "cls_shadow_blade" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    out = await cmd(m, "evolve", "g1", "p8", "转职 暮刃大师")
    p = db.get_player("g1", "p8")
    check("升 T2 暮刃大师保留暗杀流派",
          p["class_tier"] == 2 and p["evolve_path"] == 1 and "暮刃大师" in out,
          str((p["class_tier"], p["evolve_path"], out[:80])))
    # 苦修线（单流派·武僧）：拳师 40 别名『转职 武僧』= 武僧流派 T1
    make_player("g1", "p8b", "拳修", "拳师", level=40)
    db.update_player("g1", "p8b", hidden_class_unlock=["cls_wu_sheng"], race="dwarf")
    out = await cmd(m, "evolve", "g1", "p8b", "转职 武僧")
    p = db.get_player("g1", "p8b")
    check("40 级别名『转职 武僧』= T1 武僧流派",
          p["class_name"] == "cls_wu_sheng" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))

    print("[8] 血缘限制（非渊源职业被拒）")
    # 战士（已解锁时咒线）转时停 → 被拒（渊源=法师）
    make_player("g1", "p9", "修九", "战士", level=50)
    db.update_player("g1", "p9", hidden_class_unlock=["cls_chronomancer"])
    out = await cmd(m, "evolve", "g1", "p9", "转职 时停")
    check("战士转时停被拒", "只向法师一脉" in out, out[:150])
    p = db.get_player("g1", "p9")
    check("职业未切换", p["class_name"] == "cls_zhan_shi", str(p["class_name"]))
    # 游侠转龙血战士 → 被拒（渊源=战士）
    make_player("g1", "p10", "修十", "游侠", level=50)
    db.update_player("g1", "p10", hidden_class_unlock=["cls_dragon_oath"])
    out = await cmd(m, "evolve", "g1", "p10", "转职 龙血战士")
    check("游侠转龙血被拒", "只向战士一脉" in out, out[:150])
    # 法师转暗影祭司 → 被拒（渊源=牧师）
    make_player("g1", "p11", "修十一", "法师", level=40)
    db.update_player("g1", "p11", hidden_class_unlock=["cls_hymn"])
    out = await cmd(m, "evolve", "g1", "p11", "转职 暗影祭司")
    check("法师转暗影祭司被拒", "只向牧师一脉" in out, out[:150])
    # v112.3：诗人已回归牧师攻线（非独立职业），『转职 吟游诗人』不再是传承路由
    routes_now = m._hidden_class_routes()
    check("『吟游诗人』已退出隐藏路由(回归牧师攻线)", "吟游诗人" not in routes_now, "")
    # 渊源职业转职正常（战士→龙血战士=龙裔线龙血流派，60 级）
    make_player("g1", "p12", "修十二", "战士", level=60)
    db.update_player("g1", "p12", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    out = await cmd(m, "evolve", "g1", "p12", "转职 龙血战士")
    p = db.get_player("g1", "p12")
    check("战士转龙血战士成功(渊源·龙血流派)",
          p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    # 已转隐藏职业后升档不受血缘限制（同职业）
    db.update_player("g1", "p12", level=62)
    out = await cmd(m, "evolve", "g1", "p12", "转职 龙裔斗士")
    check("隐藏职业内升档不查血缘(60 级门槛)", "Lv.60" in out or "传承完成" in out, out[:120])

    print(f"\n===== v112 职业树测试: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
