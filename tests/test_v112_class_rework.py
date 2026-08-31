# -*- coding: utf-8 -*-
"""v112 职业体系重构回归（test_v112_class_rework.py）

覆盖：
 1. 数据完整性：6 隐藏线结构（流派/线级被动/核心资源/新字段）；全库技能名唯一；
    技能书 10 本（learn_skill 可解析 / require_class 有效）
 2. 传承链路：路由带流派索引、别名路由、线级+流派技能授予、同职业升档保留流派
 3. 隐藏技能书管线：源流拒绝/等级拒绝/正常学习/重复拦截/道具消耗/战斗可用
 4. 核心资源：6 线专属资源挂载

运行：python tests/test_v112_class_rework.py（exit=0 全绿）
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, run, FakeEvent, make_player

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
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return "".join(str(x) for x in results)


def test_data_integrity():
    print("【1. 数据完整性】")
    hidden = {k: v for k, v in C.CLASSES.items() if v.get("hidden")}
    # v151 隐藏职业已删（龙裔/时咒/星语/暗影/暮影/苦修 6 线）
    check("0 隐藏线（v151 已删）", len(hidden) == 0, str(len(hidden)))
    # 全库技能名唯一（不同 ID 同名=0 铁律）
    flat = {}
    for _c, _t in C.PLAYER_SKILLS.items():
        flat.update(_t["skills"] if isinstance(_t, dict) and "skills" in _t else _t)
    for _c, _t in (C.TUTOR_SKILLS or {}).items():
        if isinstance(_t, dict):
            flat.update(_t)
    name2id = {}
    dups = []
    for k, v in flat.items():
        nm = v.get("name", k)
        if nm in name2id and name2id[nm] != k:
            dups.append((nm, name2id[nm], k))
        name2id[nm] = k
    check("全库技能名唯一", not dups, str(dups[:5]))
    # 技能书数据（v151：收敛为 5 本——龙息之怒/元素湮灭/毒爆术/安眠曲/收割）
    tomes = {k: v for k, v in C.ITEMS.items() if v.get("learn_skill")}
    check("技能书 5 本", len(tomes) == 5, str(len(tomes)))
    for k, v in tomes.items():
        ls = v["learn_skill"]
        req = v.get("require_class")
        found = None
        for cid in C.CLASSES:
            found = E.skill_info(cid, ls)
            if found:
                break
        check(f"{v['name']} learn_skill 可解析", found is not None, ls)
        check(f"{v['name']} require_class 有效", not req or req in C.CLASSES, str(req))


async def test_evolve_chain(m):
    print("【2. 传承链路（v151：隐藏传承已删，改验基础职业导师转职链路）】")
    routes = m._hidden_class_routes()
    check("隐藏路由为空（v151 已删）", len(routes) == 0, str(len(routes)))
    aliases = m._hidden_alias_map()
    check("隐藏别名映射为空（v151 已删）", len(aliases) == 0, str(aliases))
    # 基础职业导师转职：30 级战士 → 战士导师攻线 T1（狂战士），60 级升 T2 保留攻线
    from conftest import FakeEvent, run
    async def talk(m, gid, qid, msg):
        ev = FakeEvent(gid, qid, msg)
        results = await run(m.talk_choice, ev)
        return "".join(str(x) for x in results)
    make_player("g1", "p1", "修一", "战士", level=30)
    db.update_player("g1", "p1", cur_map="white_deer", cur_subarea="white_deer_1")
    await talk(m, "g1", "p1", "对话 老兵·格里姆")
    await talk(m, "g1", "p1", "3")   # 我想转职
    out = await talk(m, "g1", "p1", "1")  # 狂战士（攻线）
    p = db.get_player("g1", "p1")
    check("30 级转狂战士 = T1 攻线",
          p["class_name"] == "cls_zhan_shi" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    await talk(m, "g1", "p1", "0")
    db.update_player("g1", "p1", level=60)
    await talk(m, "g1", "p1", "对话 老兵·格里姆")
    await talk(m, "g1", "p1", "3")
    out = await talk(m, "g1", "p1", "1")  # 狂战统领（攻线 T2）
    p = db.get_player("g1", "p1")
    check("升档 T2 狂战统领保留攻线", p["class_tier"] == 2 and p["evolve_path"] == 1,
          str((p["class_tier"], p["evolve_path"])))
    check("T2 文案显示狂战统领", "狂战统领" in out, out[:120])
    # 分支专属技能隔离：T1 战士学 T2 分支技能（lv58 龙息之怒）被拒
    make_player("g1", "p2", "修二", "战士", level=60)
    db.update_player("g1", "p2", skill_points=100)
    out = await cmd(m, "skill_learn", "g1", "p2", "技能学习 龙息之怒")
    check("T1 学 T2 分支技被拒", "需要先转职" in out or "学不了" in out or "专属" in out, out[:150])


async def test_tome(m):
    print("【3. 技能书管线（v113 龙息之怒=战士攻线技，书挂 cls_zhan_shi）】")
    # 源流拒绝：刺客（非战士源流）用龙息之怒技能书 → 拒绝
    make_player("g2", "w0", "刺客", "刺客", level=60)
    db.add_item("g2", "w0", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await cmd(m, "use", "g2", "w0", "使用 龙息之怒技能书")
    check("源流拒绝(刺客用战士书)", "战士" in out and "不合" in out, out[:150])
    check("道具未消耗", db.count_item("g2", "w0", "i_tome_long_xi_zhi_nu") == 1, "")
    # 正常学习：60 级战士（>= Lv.55）用龙息之怒技能书 → 学会
    make_player("g2", "w1", "剑士", "战士", level=60)
    db.add_item("g2", "w1", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await cmd(m, "use", "g2", "w1", "使用 龙息之怒技能书")
    check("战士学习成功", "龙息之怒" in out and "学会" in out, out[:150])
    p = db.get_player("g2", "w1")
    check("learned_skills 写入", "龙息之怒" in p.get("learned_skills", []), str(p.get("learned_skills")))
    check("道具已消耗", db.count_item("g2", "w1", "i_tome_long_xi_zhi_nu") == 0, "")
    # 重复学习拦截
    db.add_item("g2", "w1", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await cmd(m, "use", "g2", "w1", "使用 龙息之怒技能书")
    check("重复学习拦截", "早已掌握" in out, out[:120])
    # 等级拒绝：40 级战士（< Lv.58）用龙息之怒技能书 → 拒绝
    make_player("g3", "w2", "学徒", "战士", level=40)
    db.add_item("g3", "w2", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await cmd(m, "use", "g3", "w2", "使用 龙息之怒技能书")
    check("等级不足被拒", "Lv.58" in out, out[:150])
    check("道具未消耗(等级不足)", db.count_item("g3", "w2", "i_tome_long_xi_zhi_nu") == 1, "")
    # 战斗可用（学会后可施放真伤）
    from data.plugins.dragonfall.game import battle as BT
    p = db.get_player("g2", "w1")
    info = E.skill_info(p["class_name"], "龙息之怒")
    b = BT.Battle("怪物", {"name": "T", "hp": 5000, "max_hp": 5000, "atk": 10, "def": 500, "spd": 5}, {}, p)
    hp0 = b.enemy["hp"]
    b._player_skill(b._player_stats(p), "龙息之怒", info, p)
    check("技能战斗可用(真伤无视防御)", b.enemy["hp"] < hp0, f"{hp0}→{b.enemy['hp']}")


async def main():
    clean_db()
    m = Main(None)
    test_data_integrity()
    await test_evolve_chain(m)
    await test_tome(m)
    print(f"\n===== v112 职业体系重构回归: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
