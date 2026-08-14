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
    check("6 隐藏线", len(hidden) == 6, str(len(hidden)))
    # v113 流派结构：每线收敛为单流派 × 3 档，档位名与 BRANCH_SKILLS 分支 key 一致
    for cid, cls in hidden.items():
        eb = cls.get("evolve_branches", {})
        br = C.BRANCH_SKILLS.get(cid, {}).get("branches", {})
        for t in (1, 2, 3):
            names = eb.get(t, [])
            check(f"{cid} t{t} 分支名与技能表一致",
                  all(n in (br.get(t) or {}) for n in names) and len(names) == len(br.get(t, {})),
                  f"evolve={names} br={list((br.get(t) or {}).keys())}")
        # 线级基础（觉醒即得）在 PLAYER_SKILLS
        basics = C.PLAYER_SKILLS.get(cid, {}).get("skills", {})
        check(f"{cid} 线级基础非空", len(basics) >= 1, str(list(basics)))
        # v112 新字段
        for k in ("aliases", "lore", "hint", "tier_levels", "attack_text", "tutor"):
            check(f"{cid} 字段 {k}", k in cls, k)
        check(f"{cid} 档位门槛 40/60/90", cls.get("tier_levels") == {1: 40, 2: 60, 3: 90}, str(cls.get("tier_levels")))
        # 核心资源
        rd = E.core_resource_def(cid)
        check(f"{cid} 核心资源挂载", bool(rd and rd.get("name")), str(rd))
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
    # 技能书数据（v113：收敛为 7 本——龙息之怒/虚空爆破/毒爆术/骷髅海/安眠曲/收割/气爆）
    tomes = {k: v for k, v in C.ITEMS.items() if v.get("learn_skill")}
    check("技能书 7 本", len(tomes) == 7, str(len(tomes)))
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
    print("【2. 传承链路】")
    routes = m._hidden_class_routes()
    check("路由带流派索引", routes.get("龙血战士") == ("cls_dragon_oath", 1, 1)
          and routes.get("龙裔斗士") == ("cls_dragon_oath", 2, 1)
          and routes.get("暗影祭司") == ("cls_hymn", 1, 1), str(routes.get("龙血战士")))
    aliases = m._hidden_alias_map()
    check("别名映射", aliases.get("龙血") == ("cls_dragon_oath", 1)
          and aliases.get("龙裔") == ("cls_dragon_oath", 1)
          and aliases.get("亡灵") == ("cls_hymn", 1), str(aliases.get("龙血")))
    # 40 级战士 → 龙裔线龙血流：线级被动 + 流派技能
    make_player("g1", "p1", "修一", "战士", level=40)
    db.update_player("g1", "p1", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn")
    out = await cmd(m, "evolve", "g1", "p1", "转职 龙血战士")
    p = db.get_player("g1", "p1")
    check("传承成功(龙血流)", p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 1 and p["evolve_path"] == 1,
          str((p["class_name"], p["class_tier"], p["evolve_path"])))
    learned = p.get("learned_skills", [])
    check("线级被动授予(龙魂/火之亲和)", "龙魂" in learned and "火之亲和" in learned, str(learned))
    check("流派技能授予(龙息)", "龙息" in learned, str(learned))
    check("T3 技能未授予(龙焰吐息,lv75>40)", "龙焰吐息" not in learned, str(learned))
    # 同职业升档保留流派
    db.update_player("g1", "p1", level=60)
    out = await cmd(m, "evolve", "g1", "p1", "转职 龙裔斗士")
    p = db.get_player("g1", "p1")
    check("升档 T2 保留龙血流", p["class_tier"] == 2 and p["evolve_path"] == 1, str((p["class_tier"], p["evolve_path"])))
    # 流派隔离（单流派收敛后指 tier 门槛）：T1 学 T3 技能被拒
    make_player("g1", "p2", "修二", "战士", level=60)
    db.update_player("g1", "p2", hidden_class_unlock=["cls_dragon_oath"], race="dragonborn", skill_points=100)
    out = await cmd(m, "evolve", "g1", "p2", "转职 龙血战士")
    out = await cmd(m, "skill_learn", "g1", "p2", "技能学习 龙焰吐息")
    check("龙血流学龙焰吐息被拒", "学不了" in out or "需要" in out, out[:150])


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
    # 等级拒绝：40 级战士（< Lv.55）用龙息之怒技能书 → 拒绝
    make_player("g3", "w2", "学徒", "战士", level=40)
    db.add_item("g3", "w2", "i_tome_long_xi_zhi_nu",
                {"name": "龙息之怒技能书", "type": "消耗品", "stackable": True, "price": 5000,
                 "learn_skill": "龙息之怒", "require_class": "cls_zhan_shi"})
    out = await cmd(m, "use", "g3", "w2", "使用 龙息之怒技能书")
    check("等级不足被拒", "Lv.55" in out, out[:150])
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
