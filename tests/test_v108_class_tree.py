# -*- coding: utf-8 -*-
"""v108 职业树化测试（test_v108_class_tree.py）

覆盖：
 1. 数据完整性：13 隐藏 src_base；战士分支改名（坚盾卫士/坚城统帅）；职业名+分支名无重名
 2. 修为继承：40 级转 = T1；60 级转 = T2（直接）；90 级转 = T3；技能按等级继承
 3. 等级门槛拦截：40 级转 T2/T3 被拒
 4. 同职业逐阶升 T1→T2→T3；跳档拦截；已是高阶提示；跨职业直接 T3（修为继承）
 5. 『转职』无参数（隐藏职业）显示下一阶 / 已满
 6. 『转职重置』隐藏职业回渊源根基（付费）
 7. 吟游诗人 30/60 档位 + 魔剑士 60/75 特色档位

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
    check("隐藏职业 13 个", len(hidden) == 13, str(len(hidden)))
    check("全部有 src_base", all(v.get("src_base") for v in hidden.values()),
          str([k for k, v in hidden.items() if not v.get("src_base")]))
    check("src_base 均为基础职业", all(not C.CLASSES[v["src_base"]].get("hidden") for v in hidden.values()),
          str([(k, v["src_base"]) for k, v in hidden.items() if C.CLASSES.get(v["src_base"], {}).get("hidden")]))
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
    # 隐藏职业"职业名 == 自身 T1 档位名"是合法设计（奥术师 T1 就叫奥术师），排除
    legal_self = {cls["name"] for cls in C.CLASSES.values() if cls.get("hidden")}
    dup = [n for n in dup_raw if n not in legal_self]
    check("职业名+档位名无重名", not dup, str(dup))
    # 隐藏档位全名全部可路由
    routes = m._hidden_class_routes()
    hidden_names = []
    for cls_id, cls in hidden.items():
        for t, brs in (cls.get("evolve_branches") or {}).items():
            hidden_names.extend(brs)
    check("隐藏档位名全部入路由表(39)",
          all(n in routes for n in hidden_names) and len(hidden_names) == len(set(hidden_names)),
          f"{len(hidden_names)} 名 / 路由 {len(routes)}")

    print("[2] 修为继承（转职 tier 按等级）")
    make_player("g1", "p1", "修一", "战士", level=40)
    db.update_player("g1", "p1", hidden_class_unlock=["cls_dragon_warrior"])
    out = await cmd(m, "evolve", "g1", "p1", "转职 龙血战士")
    p = db.get_player("g1", "p1")
    check("40 级转龙血战士 = T1",
          p["class_name"] == "cls_dragon_warrior" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    make_player("g1", "p2", "修二", "战士", level=60)
    db.update_player("g1", "p2", hidden_class_unlock=["cls_dragon_warrior"])
    out = await cmd(m, "evolve", "g1", "p2", "转职 龙裔斗士")
    p = db.get_player("g1", "p2")
    check("60 级转龙裔斗士 = T2", p["class_name"] == "cls_dragon_warrior" and p["class_tier"] == 2,
          str((p["class_name"], p["class_tier"])))
    check("T2 文案显示龙裔斗士", "龙裔斗士" in out, out[:150])
    make_player("g1", "p3", "修三", "战士", level=90)
    db.update_player("g1", "p3", hidden_class_unlock=["cls_dragon_warrior"])
    out = await cmd(m, "evolve", "g1", "p3", "转职 龙魂战将")
    p = db.get_player("g1", "p3")
    check("90 级转龙魂战将 = T3", p["class_name"] == "cls_dragon_warrior" and p["class_tier"] == 3,
          str((p["class_name"], p["class_tier"])))
    sk = C.PLAYER_SKILLS["cls_dragon_warrior"]["skills"]
    expect90 = [C.display("skills", s) for s, i in sk.items() if i["lv"] <= 90]
    check("技能继承 lv<=90 全给", set(p["learned_skills"]) == set(expect90),
          f"{len(p['learned_skills'])}/{len(expect90)}")

    print("[3] 等级门槛拦截")
    make_player("g1", "p4", "修四", "法师", level=40)
    db.update_player("g1", "p4", hidden_class_unlock=["cls_arcanist"])
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥术大师")
    check("40 级转奥术大师(T2)被拒", "Lv.60" in out, out[:150])
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥秘主宰")
    check("40 级转奥秘主宰(T3)被拒", "Lv.90" in out, out[:150])
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥术师")
    check("40 级转奥术师(T1)成功", "传承完成" in out, out[:150])

    print("[4] 同职业逐阶升 + 跳档/跨职业")
    db.update_player("g1", "p4", level=60)
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥术大师")
    p = db.get_player("g1", "p4")
    check("T1→T2 逐阶升", p["class_tier"] == 2, str(p["class_tier"]))
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥术师")
    check("已是高阶提示", "已是奥术师" in out, out[:120])
    db.update_player("g1", "p4", level=90)
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥秘主宰")
    p = db.get_player("g1", "p4")
    check("T2→T3 逐阶升", p["class_tier"] == 3, str(p["class_tier"]))
    out = await cmd(m, "evolve", "g1", "p4", "转职 奥秘主宰")
    check("满阶提示已是", "已是奥术师" in out, out[:120])
    # 跨职业 90 级直接 T3（修为继承，未先转隐藏）
    make_player("g1", "p5", "修五", "法师", level=90)
    db.update_player("g1", "p5", hidden_class_unlock=["cls_arcanist"])
    out = await cmd(m, "evolve", "g1", "p5", "转职 奥秘主宰")
    p = db.get_player("g1", "p5")
    check("90 级跨职业直接 T3 成功", "传承完成" in out and p["class_tier"] == 3, str((out[:80], p["class_tier"])))
    # 同职业 T1 跳 T3 拦截
    make_player("g1", "p6", "修六", "法师", level=90)
    db.update_player("g1", "p6", hidden_class_unlock=["cls_arcanist"])
    await cmd(m, "evolve", "g1", "p6", "转职 奥术师")
    out = await cmd(m, "evolve", "g1", "p6", "转职 奥秘主宰")
    check("同职业跳档拦截", "时机未到" in out, out[:120])

    print("[5] 『转职』无参数（隐藏职业显示下一阶/已满）")
    out = await cmd(m, "evolve", "g1", "p6", "转职")
    check("隐藏职业显示下一阶", "下一阶" in out and "奥术大师" in out, out[:150])
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

    print("[7] 吟游诗人/魔剑士特色档位")
    make_player("g1", "p7", "吟游", "牧师", level=30)
    db.update_player("g1", "p7", hidden_class_unlock=["cls_bard"])
    out = await cmd(m, "evolve", "g1", "p7", "转职 吟游诗人")
    p = db.get_player("g1", "p7")
    check("30 级吟游诗人 = T1", p["class_name"] == "cls_bard" and p["class_tier"] == 1,
          str((p["class_name"], p["class_tier"])))
    db.update_player("g1", "p7", level=60)
    out = await cmd(m, "evolve", "g1", "p7", "转职 游吟歌者")
    p = db.get_player("g1", "p7")
    check("60 级游吟歌者 = T2", p["class_tier"] == 2 and "游吟歌者" in out, str((p["class_tier"], out[:80])))
    make_player("g1", "p8", "剑修", "战士", level=60)
    db.update_player("g1", "p8", hidden_class_unlock=["cls_spellblade"])
    out = await cmd(m, "evolve", "g1", "p8", "转职 魔剑士")
    p = db.get_player("g1", "p8")
    check("60 级魔剑士 = T1", p["class_name"] == "cls_spellblade" and p["class_tier"] == 1,
          str((p["class_name"], p["class_tier"])))
    out = await cmd(m, "evolve", "g1", "p8", "转职 魔剑宗师")
    check("60 级魔剑宗师(T2)被拒", "Lv.75" in out, out[:150])
    db.update_player("g1", "p8", level=75)
    out = await cmd(m, "evolve", "g1", "p8", "转职 魔剑宗师")
    p = db.get_player("g1", "p8")
    check("75 级魔剑宗师 = T2", p["class_tier"] == 2, str(p["class_tier"]))

    print("[8] 血缘限制（非渊源职业被拒）")
    # 战士（已解锁奥术师）转奥术师 → 被拒（渊源=法师）
    make_player("g1", "p9", "修九", "战士", level=50)
    db.update_player("g1", "p9", hidden_class_unlock=["cls_arcanist"])
    out = await cmd(m, "evolve", "g1", "p9", "转职 奥术师")
    check("战士转奥术师被拒", "只向法师一脉" in out, out[:150])
    p = db.get_player("g1", "p9")
    check("职业未切换", p["class_name"] == "cls_zhan_shi", str(p["class_name"]))
    # 游侠转龙血战士 → 被拒（渊源=战士）
    make_player("g1", "p10", "修十", "游侠", level=50)
    db.update_player("g1", "p10", hidden_class_unlock=["cls_dragon_warrior"])
    out = await cmd(m, "evolve", "g1", "p10", "转职 龙血战士")
    check("游侠转龙血被拒", "只向战士一脉" in out, out[:150])
    # 法师转吟游诗人 → 被拒（渊源=牧师）
    make_player("g1", "p11", "修十一", "法师", level=40)
    db.update_player("g1", "p11", hidden_class_unlock=["cls_bard"])
    out = await cmd(m, "evolve", "g1", "p11", "转职 吟游诗人")
    check("法师转诗人被拒", "只向牧师一脉" in out, out[:150])
    # 渊源职业转职正常（战士→魔剑士 60 级）
    make_player("g1", "p12", "修十二", "战士", level=60)
    db.update_player("g1", "p12", hidden_class_unlock=["cls_spellblade"])
    out = await cmd(m, "evolve", "g1", "p12", "转职 魔剑士")
    p = db.get_player("g1", "p12")
    check("战士转魔剑士成功(渊源)", p["class_name"] == "cls_spellblade" and p["class_tier"] == 1,
          str((p["class_name"], p["class_tier"])))
    # 已转隐藏职业后升档不受血缘限制（同职业）
    out = await cmd(m, "evolve", "g1", "p12", "转职 魔剑宗师")
    check("隐藏职业内升档不查血缘", "Lv.75" in out, out[:150])

    print(f"\n===== v108 职业树测试: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
