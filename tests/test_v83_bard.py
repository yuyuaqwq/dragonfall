# -*- coding: utf-8 -*-
"""v112.3 牧师攻线·吟游诗人路线（原 v83 独立诗人职业，v112.3 回归牧师攻线）

v83 诗人是独立隐藏职业；v112 并入圣歌线；v112.1 拆出为第 7 线；v112.3 鱼鱼拍板：
诗人整体替换牧师攻线"圣武士"路线（吟游诗人→灵魂歌者→黎明颂者），独立职业删除。
覆盖：数据归属 / 导师转职流程 / 技能组 / SKILL_UP / 成就无独立诗人条目。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, E, BT, Main, FakeEvent, run, clean_db, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


async def main():
    clean_db()
    m = Main(None)

    # ---- 1. 数据归属 ----
    print("【1. 诗人技能归属牧师攻线】")
    check("cls_bard 独立职业已删除", "cls_bard" not in C.CLASSES, "")
    mu = C.CLASSES.get("cls_mu_shi")
    check("牧师攻线 T1 = 吟游诗人", mu["evolve_branches"][1] == ["吟游诗人", "神谕者"],
          str(mu["evolve_branches"][1]))
    check("牧师攻线 T2 = 灵魂歌者", mu["evolve_branches"][2] == ["灵魂歌者", "大主教"], "")
    check("牧师攻线 T3 = 黎明颂者", mu["evolve_branches"][3] == ["黎明颂者", "圣光先知"], "")
    br = C.BRANCH_SKILLS["cls_mu_shi"]["branches"]
    t1_names = [v.get("name") for v in br[1]["吟游诗人"].values()]
    check("T1 吟游诗人技能组", "战歌" in t1_names and "安眠曲" in t1_names
          and "即兴弹唱" in t1_names and "轻快拨弦" in t1_names, str(t1_names))
    t2_names = [v.get("name") for v in br[2]["灵魂歌者"].values()]
    check("T2 灵魂歌者技能组", "鼓舞" in t2_names and "哀歌" in t2_names
          and "轻风咏叹" in t2_names and "伴奏" in t2_names, str(t2_names))
    t3_names = [v.get("name") for v in br[3]["黎明颂者"].values()]
    check("T3 黎明颂者技能组", "英雄叙事诗" in t3_names and "奥术咏叹调" in t3_names
          and "快板节奏" in t3_names and "终章·黎明颂歌" in t3_names, str(t3_names))
    team_cnt = sum(1 for t in (1, 2, 3) for bn in br[t] for v in br[t][bn].values() if v.get("team"))
    check("团队技能>=5", team_cnt >= 5, str(team_cnt))
    all_names = t1_names + t2_names + t3_names
    for n in all_names:
        check(f"SKILL_UP 有 {n}", n in E.C.SKILL_UP, "")

    # ---- 2. 导师转职流程 ----
    print("【2. 牧师导师转职吟游诗人路线】")
    await cmd(m, "register", "g1", "w1", "注册 牧师 旅人 男")
    db.update_player("g1", "w1", level=30, gold=5000, cur_map="white_deer", cur_subarea="white_deer_1")
    out = await cmd(m, "find_npc", "g1", "w1", "找 圣殿执事·莉亚")
    check("导师对话含转职入口", "我想转职" in out, out[:250])
    out = await cmd(m, "talk_choice", "g1", "w1", "3")  # 我想转职 → 一转菜单
    check("一转菜单含吟游诗人/神谕者", "吟游诗人" in out and "神谕者" in out, out[:250])
    out = await cmd(m, "talk_choice", "g1", "w1", "1")  # 转职为吟游诗人（进攻）
    check("一转成功含吟游诗人", "转职成功" in out and "吟游诗人" in out, out[:200])
    p = db.get_player("g1", "w1")
    check("class_tier=1 path=1", p.get("class_tier") == 1 and p.get("evolve_path") == 1,
          str((p.get("class_tier"), p.get("evolve_path"))))
    db.update_player("g1", "w1", level=60)
    out = await cmd(m, "find_npc", "g1", "w1", "找 圣殿执事·莉亚")
    out = await cmd(m, "talk_choice", "g1", "w1", "3")  # 我想继续转职 → 二转菜单
    check("二转菜单含灵魂歌者/大主教", "灵魂歌者" in out and "大主教" in out, out[:250])
    out = await cmd(m, "talk_choice", "g1", "w1", "1")  # 灵魂歌者
    check("二转成功含灵魂歌者", "转职成功" in out and "灵魂歌者" in out, out[:200])
    db.update_player("g1", "w1", level=90)
    out = await cmd(m, "find_npc", "g1", "w1", "找 圣殿执事·莉亚")
    out = await cmd(m, "talk_choice", "g1", "w1", "3")  # 我想进行最终转职 → 三转菜单
    check("三转菜单含黎明颂者/圣光先知", "黎明颂者" in out and "圣光先知" in out, out[:250])
    out = await cmd(m, "talk_choice", "g1", "w1", "1")  # 黎明颂者
    check("三转成功含黎明颂者", "转职成功" in out and "黎明颂者" in out, out[:200])
    p = db.get_player("g1", "w1")
    check("class_tier=3", p.get("class_tier") == 3, str(p.get("class_tier")))
    check("三转自动领悟 90 级奥义英雄叙事诗", "英雄叙事诗" in (p.get("learned_skills") or []),
          str(p.get("learned_skills")))
    # 终章·黎明颂歌 Lv.98 需手动学（分支门槛：黎明颂者 path=1）
    db.update_player("g1", "w1", level=98, skill_points=100)
    out = await cmd(m, "skill_learn", "g1", "w1", "技能学习 终章·黎明颂歌")
    check("Lv.98 可学终章·黎明颂歌", "已学会" in out or "学会" in out, out[:200])

    # ---- 3. 分支技能学习门槛 ----
    print("【3. 分支技能门槛】")
    make_player("g2", "w2", "歌者", "牧师", level=40)
    db.update_player("g2", "w2", skill_points=100, class_tier=1, evolve_path=1)
    out = await cmd(m, "skill_learn", "g2", "w2", "技能学习 战歌")
    check("一转可学战歌(t1)", "已学会" in out or "学会" in out, out[:200])
    out = await cmd(m, "skill_learn", "g2", "w2", "技能学习 鼓舞")
    check("一转学鼓舞(t2)被拦", "先转职" in out or "学不了" in out, out[:200])
    db.update_player("g2", "w2", level=62, class_tier=2)
    out = await cmd(m, "skill_learn", "g2", "w2", "技能学习 鼓舞")
    check("二转可学鼓舞(t2)", "已学会" in out or "学会" in out, out[:200])
    # 守线牧师不能学攻线技能
    db.update_player("g2", "w2", evolve_path=2)
    out = await cmd(m, "skill_learn", "g2", "w2", "技能学习 英雄叙事诗")
    check("神谕者学攻线技能被拦", "学不了" in out or "先转职" in out, out[:200])

    # ---- 4. 旧圣武士路线已退役 ----
    print("【4. 旧圣武士路线退役】")
    check("圣武士档位名已删除", "圣武士" not in mu["evolve_branches"][1], "")
    aid = [a["id"] for a in C.ACHIEVEMENTS]
    check("无独立诗人成就", "ach_bard_unlock" not in aid and "ach_bard_master" not in aid, "")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
