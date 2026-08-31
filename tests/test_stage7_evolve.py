# -*- coding: utf-8 -*-
"""阶段七：转职体系 + 分支技能 v2.0（21 章）

验证：
  1. 数据完整性：12 分支名 / 每分支 10 技能 / tier 划分（t1≤55, t2≤68, t3≥90）
  2. 转职流程：30 一转（选分支）→ 60 二转（自动同分支）→ 90 三转
  3. 分支技能解锁：tier 检查（一转不能学二转技能）
  4. 自动获得：二转被动（Lv.60）/ 三转奥义（Lv.90）
  5. 转职重置：付费清分支技能，保留基础
  6. 新条件类型：enemy_debuff / element_marks / enemy_slowed / speed_ratio / player_untouched / player_buffed
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR
from data.plugins.dragonfall.game import content as C, db, engine as E
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.main import Main

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


async def cmd(m, name, gid, qid, msg):
    handler = getattr(m, name)
    ev = FakeEvent(gid, qid, msg)
    return await run(handler, ev)


def make_battle(player, enemy=None):
    e = enemy or {"name": "木桩", "hp": 1000, "max_hp": 1000, "atk": 10, "def": 10, "spd": 5}
    b = BT.Battle("monster", e, {}, player)
    return b


def test_data():
    print("【数据：分支名对照 21 章】")
    # v151：法师守线 奥秘→时律 重构（奥秘法师/奥秘术士/奥秘贤者 → 时律法师/时律术士/时律贤者）
    expect = {
        "cls_zhan_shi": {1: ["狂战士", "盾卫士"], 2: ["狂战统领", "坚盾卫士"], 3: ["战争领主", "坚城统帅"]},
        "cls_fa_shi": {1: ["元素法师", "时律法师"], 2: ["元素术士", "时律术士"], 3: ["元素贤者", "时律贤者"]},
        "cls_you_xia": {1: ["林语者", "风行者"], 2: ["自然行者", "疾风射手"], 3: ["万木之灵", "疾风猎手"]},
        "cls_mu_shi": {1: ["吟游诗人", "神谕者"], 2: ["灵魂歌者", "大主教"], 3: ["黎明颂者", "圣光先知"]},
        "cls_ci_ke": {1: ["影舞者", "毒刃者"], 2: ["暗影之刃", "淬毒师"], 3: ["无影之刃", "蚀骨者"]},
        "cls_wu_seng": {1: ["格斗士", "磐石行者"], 2: ["拳术师", "铁壁行者"], 3: ["破晓者", "磐岩壁垒"]},
    }
    for cid, tmap in expect.items():
        for t, names in tmap.items():
            actual = list(C.BRANCH_SKILLS[cid]["branches"][t].keys())
            check(f"{cid} t{t} 分支名", actual == names, str(actual))

    print("【数据：每分支技能数（基础 2-10 / 隐藏 0-8，v112 允许空档）】")
    total = 0
    for cid, cinfo in C.BRANCH_SKILLS.items():
        for t, branches in cinfo["branches"].items():
            for bname, skills in branches.items():
                n = len(skills)
                total += n
                check(f"{bname} {n} 技能", n in (0, 1, 2, 3, 4, 5, 6, 7, 8, 10), f"{bname}={n}")
    # v151：6 隐藏职业删除 + 分支 3-key 重构（每职业 2 分支 × 3 tier），分支总技能 = 183
    #   （每 t1 分支 5-6 技能、t2 分支 6 技能、t3 分支 3-4 技能）
    check("分支总技能 183（v151 3-key）", total == 183, str(total))

    print("【数据：tier 划分（v151 3-key：t1≤55 / t2 58-84 / t3≥90）】")
    bad = []
    for cid, cinfo in C.BRANCH_SKILLS.items():
        hidden = bool(C.CLASSES.get(cid, {}).get("hidden"))
        for t, branches in cinfo["branches"].items():
            for bname, skills in branches.items():
                for sname, info in skills.items():
                    lv = info["lv"]
                    if t == 1 and lv > (56 if hidden else 55):
                        bad.append(f"{cid}.{bname}.{sname} lv{lv} 应在 t1")
                    if t == 2 and not (56 <= lv <= 84) and not (hidden and 20 <= lv <= 84):
                        bad.append(f"{cid}.{bname}.{sname} lv{lv} 应在 t2")
                    if t == 3 and lv < (70 if hidden else 90):
                        bad.append(f"{cid}.{bname}.{sname} lv{lv} 应在 t3")
    check("tier 划分正确", not bad, str(bad[:5]))


def test_evolve_flow():
    print("【转职：30 级一转（v95.23 找导师仪式）】")
    m = Main(None)
    clean_db()
    await_cmd(m, "register", "注册 战士 勇者 男")
    db.update_player("g1", "k1", level=30, gold=5000)
    out = await_cmd(m, "evolve", "转职 1")
    check("转职指令引导找导师", "可以转职" in out and "格里姆" in out, out[:200])
    p = db.get_player("g1", "k1")
    check("指令不再直接转职", p.get("class_tier") == 0, str(p.get("class_tier")))
    # v95.23：去白鹿城找战士导师，对话举行转职仪式
    db.update_player("g1", "k1", cur_map="white_deer", cur_subarea="white_deer_1")
    out = await_cmd(m, "find_npc", "找 老兵·格里姆")
    check("导师对话打开含转职选项", "我想转职" in out, out[:300])
    out = await_cmd(m, "talk_choice", "3")  # 🌟 我想转职！
    check("分支选择出现", "狂战士" in out and "盾卫士" in out, out[:300])
    out = await_cmd(m, "talk_choice", "1")  # 狂战士（进攻）
    check("一转成功含狂战士", "狂战士" in out, out[:200])
    p = db.get_player("g1", "k1")
    check("class_tier=1", p.get("class_tier") == 1, str(p.get("class_tier")))
    check("evolve_path=1（进攻路线）", p.get("evolve_path") == 1, str(p.get("evolve_path")))
    check("一转不自动获得二转被动", "狂战之魂" not in (p.get("learned_skills") or []), str(p.get("learned_skills")))

    print("【转职：60 级二转自动同分支 + 自动获得二转被动】")
    db.update_player("g1", "k1", level=60)
    out = await_cmd(m, "find_npc", "找 老兵·格里姆")
    out = await_cmd(m, "talk_choice", "3")  # 🌟 我想继续转职！
    out = await_cmd(m, "talk_choice", "1")  # 狂战统领（进攻）
    check("二转成功含狂战统领", "狂战统领" in out, out[:200])
    p = db.get_player("g1", "k1")
    check("class_tier=2", p.get("class_tier") == 2, str(p.get("class_tier")))
    check("evolve_path 保持 1", p.get("evolve_path") == 1, str(p.get("evolve_path")))
    # v151 3-key 表：狂战统领无 lv60 技能（t2 从 lv58 起），自动获得 = lv≥60 最低（内燃 62）
    check("二转自动获得技能", "内燃" in (p.get("learned_skills") or []), str(p.get("learned_skills")))

    print("【转职：90 级三转 + 自动获得三转奥义】")
    db.update_player("g1", "k1", level=90)
    out = await_cmd(m, "find_npc", "找 老兵·格里姆")
    out = await_cmd(m, "talk_choice", "3")  # 🌟 我想进行最终转职！
    out = await_cmd(m, "talk_choice", "1")  # 战争领主（进攻）
    check("三转成功含战争领主", "战争领主" in out, out[:200])
    p = db.get_player("g1", "k1")
    check("class_tier=3", p.get("class_tier") == 3, str(p.get("class_tier")))
    # v151 3-key 表：战争领主无 lv90 技能（t3 从 lv92 起），自动获得 = lv≥90 最低（战争化身 92）
    check("三转奥义自动获得", "战争化身" in (p.get("learned_skills") or []), str(p.get("learned_skills")))

    print("【转职：满级后提示最终】")
    out = await_cmd(m, "evolve", "转职")
    check("三转后提示已完成", "已完成全部转职" in out, out[:200])


def test_branch_skill_gate():
    print("【分支技能：tier 检查（一转不能学二转技能）】")
    m = Main(None)
    clean_db()
    await_cmd(m, "register", "注册 战士 勇者 男")
    db.update_player("g1", "k1", level=35, gold=5000, skill_points=100, class_tier=1, evolve_path=1)
    # 一转后：能学 32 级分支技能 怒斩（tier1）
    out = await_cmd(m, "skill_learn", "技能学习 怒斩")
    check("一转可学怒斩(t1)", "已学会" in out or "学会" in out, out[:200])
    # v151：乱舞/战争领域已删（3-key 表），t2/t3 拦截用狂战统领 t2 技能 龙息之怒(58)/t3 战争化身(92)
    out = await_cmd(m, "skill_learn", "技能学习 龙息之怒")
    check("一转学龙息之怒被拦", "先转职" in out or "学不了" in out, out[:200])
    # 三转奥义 战争化身：tier3，一转挡
    out = await_cmd(m, "skill_learn", "技能学习 战争化身")
    check("一转学战争化身被拦", "先转职" in out or "学不了" in out, out[:200])

    print("【分支技能：二转后可学 t2，三转后可学 t3】")
    db.update_player("g1", "k1", level=68, class_tier=2)
    out = await_cmd(m, "skill_learn", "技能学习 龙息之怒")
    check("二转可学龙息之怒(t2)", "已学会" in out or "学会" in out, out[:200])
    out = await_cmd(m, "skill_learn", "技能学习 战争化身")
    check("二转学战争化身仍被拦", "先转职" in out or "学不了" in out, out[:200])
    db.update_player("g1", "k1", level=92, class_tier=3)
    out = await_cmd(m, "skill_learn", "技能学习 战争化身")
    check("三转可学战争化身(t3)", "已学会" in out or "学会" in out, out[:200])

    print("【分支技能：错误分支拦截】")
    clean_db()
    await_cmd(m, "register", "注册 战士 勇者 男")
    db.update_player("g1", "k1", level=30, gold=5000, skill_points=100, class_tier=1, evolve_path=2)  # 盾卫士
    out = await_cmd(m, "skill_learn", "技能学习 怒斩")
    check("盾卫士学狂战怒斩被拦", "学不了" in out, out[:200])
    out = await_cmd(m, "skill_learn", "技能学习 盾击")
    check("盾卫士可学盾击", "已学会" in out or "学会" in out, out[:200])


def test_evolve_reset():
    print("【转职重置：付费清分支技能】")
    m = Main(None)
    clean_db()
    await_cmd(m, "register", "注册 战士 勇者 男")
    db.update_player("g1", "k1", level=60, gold=5000, skill_points=100, class_tier=2, evolve_path=1,
                     learned_skills=["挥砍", "怒斩", "内燃"])
    out = await_cmd(m, "evolve_reset", "转职重置")
    check("重置成功", "转职重置成功" in out, out[:200])
    p = db.get_player("g1", "k1")
    check("class_tier 回 0", p.get("class_tier") == 0, str(p.get("class_tier")))
    check("evolve_path 回 0", p.get("evolve_path") == 0, str(p.get("evolve_path")))
    check("分支技能被清", "怒斩" not in (p.get("learned_skills") or []) and "内燃" not in (p.get("learned_skills") or []),
          str(p.get("learned_skills")))
    check("基础技能保留", "挥砍" in (p.get("learned_skills") or []), str(p.get("learned_skills")))
    check("金币扣费", p.get("gold") == 3000, str(p.get("gold")))  # 二转重置 2000

    print("【转职重置：金币不足拦截】")
    clean_db()
    await_cmd(m, "register", "注册 战士 勇者 男")
    db.update_player("g1", "k1", level=30, gold=100, class_tier=1, evolve_path=1)
    out = await_cmd(m, "evolve_reset", "转职重置")
    check("金币不足拦截", "金币" in out, out[:200])
    p = db.get_player("g1", "k1")
    check("未重置", p.get("class_tier") == 1, str(p.get("class_tier")))


def test_new_conds():
    print("【条件：enemy_debuff（目标有减益）】")
    p = {"class_name": "cls_zhan_shi", "level": 50, "equipment": {}, "attributes": {}, "hp": 500, "max_hp": 500}
    b = make_battle(p)
    cond = {"type": "enemy_debuff", "mult": 1.2, "label": "猎物标记"}
    check("无减益不触发", abs(b._cond_mult({"cond": cond}, p) - 1.0) < 1e-9, str(b._cond_mult({"cond": cond}, p)))
    b.e_buffs["def_down"] = 2
    check("有减益触发", abs(b._cond_mult({"cond": cond}, p) - 1.2) < 1e-9, str(b._cond_mult({"cond": cond}, p)))

    print("【条件：enemy_slowed（目标减速）】")
    b2 = make_battle(p)
    cond2 = {"type": "enemy_slowed", "mult": 1.2, "label": "寒霜亲和"}
    check("未减速不触发", abs(b2._cond_mult({"cond": cond2}, p) - 1.0) < 1e-9, "")
    b2.e_buffs["spd_down"] = 2
    check("减速触发", abs(b2._cond_mult({"cond": cond2}, p) - 1.2) < 1e-9, "")

    print("【条件：element_marks（元素印记层数）】")
    b3 = make_battle(p)
    cond3 = {"type": "element_marks", "element": "fire", "stacks": 3, "mult": 1.3, "label": "连环引爆"}
    check("无火印不触发", abs(b3._cond_mult({"cond": cond3}, p) - 1.0) < 1e-9, "")
    b3.e_buffs["fire_mark"] = 2
    check("火印不足不触发", abs(b3._cond_mult({"cond": cond3}, p) - 1.0) < 1e-9, "")
    b3.e_buffs["fire_mark"] = 3
    check("火印≥3 触发", abs(b3._cond_mult({"cond": cond3}, p) - 1.3) < 1e-9, "")

    print("【条件：speed_ratio（速度比）】")
    p4 = {"class_name": "cls_you_xia", "level": 50, "equipment": {}, "attributes": {}, "hp": 500, "max_hp": 500}
    b4 = make_battle(p4, {"name": "慢速怪", "hp": 100, "max_hp": 100, "atk": 5, "def": 5, "spd": 2})
    cond4 = {"type": "speed_ratio", "ratio": 1.5, "mult": 1.5, "label": "疾风连击"}
    pst = b4._player_stats(p4)
    est = b4._enemy_stats()
    check("游侠速度比慢速怪", pst["spd"] / est["spd"] >= 1.5, f"{pst['spd']}/{est['spd']}")
    check("速度比触发", abs(b4._cond_mult({"cond": cond4}, p4) - 1.5) < 1e-9, str(b4._cond_mult({"cond": cond4}, p4)))

    print("【条件：player_untouched（本场未受击）】")
    b5 = make_battle(p)
    cond5 = {"type": "player_untouched", "mult": 1.15, "label": "轻灵"}
    check("未受击触发", abs(b5._cond_mult({"cond": cond5}, p) - 1.15) < 1e-9, "")
    b5._player_hit = True
    check("受击后不触发", abs(b5._cond_mult({"cond": cond5}, p) - 1.0) < 1e-9, "")

    print("【条件：player_buffed（自身有增益）】")
    b6 = make_battle(p)
    cond6 = {"type": "player_buffed", "mult": 1.15, "label": "神圣狂热"}
    check("无增益不触发", abs(b6._cond_mult({"cond": cond6}, p) - 1.0) < 1e-9, "")
    b6.p_buffs["atk_up"] = 2
    check("有增益触发", abs(b6._cond_mult({"cond": cond6}, p) - 1.15) < 1e-9, "")


def await_cmd(m, name, msg):
    """命令层调用（同步包装），返回最后一条回复字符串"""
    import asyncio
    ev = FakeEvent("g1", "k1", msg)
    handler = getattr(m, name)
    results = asyncio.get_event_loop().run_until_complete(run(handler, ev))
    return results[-1] if results else ""


def test_mage_mechanics():
    print("【元素/奥术机制：奥术充能叠层 + 爆发（v112.4：奥术系技能属法师守线秘法族）】")
    # v151：法师守线改为"时律"（时律法师/术士/贤者），奥术系技能（奥术弹幕/爆破/洪流/直觉）
    # 已从 v151 表移除（时律=时间系）。原奥术充能机制改由 时间系 覆盖——验证引擎 mech handler
    # 仍可用（arcane 注册在 MECH_EFFECTS），但技能名断言改为现存技能。
    # 引擎 arcane 机制保留（供未来数据挂载），此处验证 时律 t2 技能 时间共鸣（element=current 时间系）
    p = {"class_name": "cls_fa_shi", "level": 60, "equipment": {}, "attributes": {}, "hp": 1000, "max_hp": 1000}
    b = make_battle(p, {"name": "木桩", "hp": 5000, "max_hp": 5000, "atk": 10, "def": 10, "spd": 5})
    info = E.skill_info("法师", "时间共鸣")
    check("时间共鸣可查到", bool(info), str(info))
    if info:
        lv = 1
        mval = E.skill_mech_val(info, lv)
        p_mech = b.mech_stacks
        # v151 时间共鸣 mech=None（element=current 挂印），验证其挂当前系印记机制
        b.resources["element"] = "fire"
        b._player_skill(b._player_stats(p), "时间共鸣", info, dict(p))
        check("时间共鸣挂火印", b.e_buffs.get("fire_mark", 0) >= 1, str(b.e_buffs.get("fire_mark")))

    print("【元素/奥术机制：元素跃迁切系（element_shift，法师系）】")
    pf = {"class_name": "cls_fa_shi", "level": 60, "equipment": {}, "attributes": {}, "hp": 1000, "max_hp": 1000}
    b2 = make_battle(pf)
    # v130.2：资源下放分支后基础法师（tier0）不再附带元素资源 → 初始无元素态（None）；
    # 元素系技能挂载在攻线·元素法师分支，切系机制仍可动态挂 element 键（下方校验）
    check("基础法师无资源（初始无元素态）", b2.resources.get("element") is None,
          str(b2.resources.get("element")))
    info2 = E.skill_info("法师", "元素跃迁")
    check("元素跃迁可查到", bool(info2), str(info2))
    if info2:
        logs = b2._player_skill(b2._player_stats(pf), "元素跃迁", info2, dict(pf))
        check("切到冰系", b2.resources.get("element") == "ice", str(b2.resources.get("element")))
        check("切系日志", any("元素跃迁" in lg for lg in logs), str(logs))

    print("【元素/奥术机制：current 系技能读当前元素】")
    info3 = E.skill_info("法师", "元素冲击")
    check("元素冲击 element=current", bool(info3) and info3.get("element") == "current", str(info3))
    if info3:
        b3 = make_battle(pf)
        b3.resources["element"] = "thunder"
        logs = b3._player_skill(b3._player_stats(pf), "元素冲击", info3, dict(pf))
        check("current 系按雷系挂雷印", b3.e_buffs.get("thunder_mark", 0) >= 1, str(b3.e_buffs))

    print("【元素/奥术机制：奥术直觉被动回合充能（法师守线）】")
    # v151：奥术直觉已删（时律=时间系），原"回合充能"机制改由 时间系 被动覆盖——
    # 时律 t2 被动：时间凝滞（回合开始充能）已不存在于 v151 表；v151 时律被动为
    # 时间加速（spd_up 增益）。验证 _turn_start 不抛错 + 时间系被动可查。
    b4 = make_battle(p)
    p4 = dict(p)
    p4["learned_skills"] = ["时间加速"]
    info4 = E.skill_info("法师", "时间加速")
    check("时间加速可查到", bool(info4), str(info4))
    logs = b4._turn_start(p4)
    check("回合开始不抛错", True, "")

    print("【元素/奥术机制：player_mech_stacks cond】")
    b5 = make_battle(p)
    cond = {"type": "player_mech_stacks", "mech": "arcane", "stacks": 3, "mult": 1.3, "label": "共鸣"}
    check("充能不足不触发", abs(b5._cond_mult({"cond": cond}, p) - 1.0) < 1e-9, "")
    b5.mech_stacks["arcane"] = 3
    check("充能≥3 触发", abs(b5._cond_mult({"cond": cond}, p) - 1.3) < 1e-9, "")

    print("【元素/奥术机制：element_marks any 任意系】")
    b6 = make_battle(p)
    cond6 = {"type": "element_marks", "element": "any", "stacks": 1, "mult": 1.2, "label": "万象共鸣"}
    check("无印记不触发", abs(b6._cond_mult({"cond": cond6}, p) - 1.0) < 1e-9, "")
    b6.e_buffs["ice_mark"] = 2
    check("任意系印记触发", abs(b6._cond_mult({"cond": cond6}, p) - 1.2) < 1e-9, "")


def main():
    clean_db()
    test_data()
    test_evolve_flow()
    test_branch_skill_gate()
    test_evolve_reset()
    test_new_conds()
    test_mage_mechanics()
    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
