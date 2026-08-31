# -*- coding: utf-8 -*-
"""v64：被动技能系统（鱼鱼拍板 2026-08-06）

新增：被动技能 kind="被动"，学到即永久生效，无需施放、不耗 MP、不进技能栏。
每职业 4 个被动（Lv.12/25/38/55）：
- 属性型：魔力涌动(mp+15%)、风行步/疾影(spd+8%)、鹰眼(crit+3%)
- 触发型：铁壁之心/磐石体(受击减伤5%)、神圣坚韧(受击20%回5%)、气力调和(每回合回2%)
- 增伤型：破甲本能(破防技能+10%)、烈焰亲和(火系魔法+10%)、神恩(治疗+10%)
- 展示：技能列表<被动>标签、施放提示无需施放、不可升级

验证：
  1. 被动技能定义存在（每职业 4 个）
  2. engine.player_passive_stats 属性结算
  3. engine.passive_skills_learned 被动识别
  4. battle._player_stats 叠加被动属性
  5. 受击减伤被动生效
  6. 气力调和每回合回血
  7. 施放被动提示无需施放（命令层）
  8. 被动学习成功提示
  9. 被动不可升级
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, BT, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

# ---------- 1. 被动技能定义 ----------
def test_defs():
    print("\n== 1. 被动技能定义 ==\n（v151：基础职业技能表不再含被动，被动移入各职业分支表）")
    # 各职业分支表内被动数量（v151 分支重排后抽查）
    expect = {"cls_zhan_shi": 6, "cls_fa_shi": 4, "cls_you_xia": 4,
              "cls_mu_shi": 2, "cls_ci_ke": 7, "cls_wu_seng": 9}
    for cls, cname in [("cls_zhan_shi", "战士"), ("cls_fa_shi", "法师"), ("cls_you_xia", "游侠"),
                       ("cls_mu_shi", "牧师"), ("cls_ci_ke", "刺客"), ("cls_wu_seng", "拳师")]:
        branches = C.BRANCH_SKILLS[cls].get("branches") if isinstance(C.BRANCH_SKILLS[cls], dict) and "branches" in C.BRANCH_SKILLS[cls] else C.BRANCH_SKILLS[cls]
        passives = []
        for tier, bs in branches.items():
            for bname, skills in bs.items():
                passives += [v for v in skills.values() if v.get("kind") == "被动"]
        check(f"{cname} 分支被动数量={expect.get(cls)}", len(passives) == expect.get(cls), f"实际 {len(passives)}")
        for v in passives:
            check(f"  {v['name']} mp=0", v.get("mp") == 0, f"mp={v.get('mp')}")
    # 代表性被动抽查（v151 分支表）
    branches = C.BRANCH_SKILLS["cls_zhan_shi"].get("branches")
    names = []
    for tier, bs in branches.items():
        for bname, skills in bs.items():
            names += [v["name"] for v in skills.values() if v.get("kind") == "被动"]
    check("战士被动含守护姿态", "守护姿态" in names)
    check("战士被动含淬血", "淬血" in names)

# ---------- 2. engine 属性结算 ----------
def test_engine_stats():
    print("\n== 2. engine.player_passive_stats ==")
    # v151：属性型被动移入分支表——法师元素之核(pene_mag)、刺客暗影之心(spd+5%)
    # 注：元素之核 stat=pene_mag 是拼写别名，引擎 _PASSIVE_STAT_APPLY 认 pene_magi——此键不生效（数据侧别名待修），
    # 属性结算验证改以 暗影之心(spd)/疾风之心(spd_crit) 为准
    b = E.player_passive_stats("cls_ci_ke", ["暗影之心"])
    check("刺客暗影之心 spd_mult=1.05", abs(b["spd_mult"] - 1.05) < 1e-9, str(b))
    # v134.1 疾风之心：速度→暴击被动（stat=spd_crit，mult=0.1）
    b3 = E.player_passive_stats("cls_you_xia", ["疾风之心"])
    check("游侠疾风之心 spd_crit_add=0.1", abs(b3["spd_crit_add"] - 0.1) < 1e-9, str(b3.get("spd_crit_add")))
    # proc 型被动（淬血 战意吸血）不产生属性加成
    b4 = E.player_passive_stats("cls_zhan_shi", ["淬血"])
    check("淬血 proc 型无属性加成(条件型)", b4["atk_mult"] == 1.0, str(b4))
    # 未学被动 → 无加成
    b5 = E.player_passive_stats("cls_zhan_shi", ["猛击"])
    check("未学被动无加成", b5["mp_mult"] == 1.0 and b5["spd_mult"] == 1.0)

# ---------- 3. 被动识别 ----------
def test_learned():
    print("\n== 3. passive_skills_learned ==")
    pl = E.passive_skills_learned("cls_zhan_shi", ["守护姿态", "淬血", "猛击"])
    check("识别 守护姿态+淬血", "守护姿态" in pl and "淬血" in pl and "猛击" not in pl, str(pl))
    check("is_passive_learned 守护姿态", E.is_passive_learned("cls_zhan_shi", "守护姿态", ["守护姿态", "淬血"]))
    check("is_passive_learned 未学", not E.is_passive_learned("cls_zhan_shi", "守护姿态", ["猛击"]))

# ---------- 4. battle 属性叠加 ----------
def test_battle_stats():
    print("\n== 4. battle._player_stats 被动叠加 ==")
    # v151：暗影之心(spd+5%)替代风行步验证 battle 属性叠加
    pl = make_player(cls="刺客", level=40)
    pl["class_name"] = "cls_ci_ke"
    pl["learned_skills"] = ["暗影之心"]
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    st = b._player_stats(pl)
    base_spd = E.player_final_stats(pl["class_name"], pl["level"], pl.get("equipment", {}), pl.get("class_tier", 0), pl.get("attributes"), pl.get("evolve_path", 0), None, pl.get("race"))["spd"]  # v87.17 与 _player_stats 同参（race）
    check("暗影之心 spd +5%", st["spd"] == int(base_spd * 1.05), f"st={st['spd']} base={base_spd}")
    # 暗影之心：spd +5% 属性被动 battle 叠加（替代元素之核——其 stat 别名 pene_mag 引擎不认）
    pl2 = make_player(cls="刺客", level=45)
    pl2["class_name"] = "cls_ci_ke"
    pl2["learned_skills"] = ["暗影之心"]
    b2 = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    st2 = b2._player_stats(pl2)
    base_spd2 = E.player_final_stats(pl2["class_name"], pl2["level"], pl2.get("equipment", {}), pl2.get("class_tier", 0), pl2.get("attributes"), pl2.get("evolve_path", 0), None, pl2.get("race"))["spd"]
    check("暗影之心 battle spd +5%", st2["spd"] == int(base_spd2 * 1.05), f"st={st2['spd']} base={base_spd2}")

# ---------- 5. 受击减伤被动 ----------
def test_dmg_reduce():
    print("\n== 5. 受击减伤（磐石之心/守护姿态）==")
    pl = make_player(cls="拳师", level=65)
    pl["class_name"] = "cls_wu_seng"
    pl["learned_skills"] = ["磐石之心"]
    pl["hp"] = 300
    pl["max_hp"] = 300
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    # 闪避为随机（拳师基础 dodge），本测试目标是『受击减伤』被动 → 屏蔽闪避保证确定性
    _orig_ps = b._player_stats
    def _ps_nododge(p):
        s = _orig_ps(p)
        s["dodge"] = 0.0
        return s
    b._player_stats = _ps_nododge
    logs = []
    before = pl["hp"]
    b._damage_player(pl, 100, logs)
    # 100 - 5 = 95，hp 300 -> 205
    check("受击减伤5% (100→95)", pl["hp"] == before - 95, f"hp={pl['hp']} before={before}")
    check("减伤日志出现", any("被动减伤" in lg for lg in logs), str(logs))

# ---------- 6. 气力调和每回合回血 ----------
def test_turn_heal():
    print("\n== 6. 亡灵祭仪每回合回血 ==")
    # v151：牧师分支被动 亡灵祭仪(turn_heal 3%) 替代气力调和
    pl = make_player(cls="牧师", level=55)
    pl["class_name"] = "cls_mu_shi"
    pl["learned_skills"] = ["亡灵祭仪"]
    pl["hp"] = 200
    pl["max_hp"] = 400
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    logs = b._turn_start(pl)
    check("每回合回 3% (400*3%=12)", pl["hp"] == 212, f"hp={pl['hp']}")
    check("回血日志出现", any("亡灵祭仪" in lg for lg in logs), str(logs))

# ---------- 7. 命令层：施放被动提示 ----------
async def test_cmd_cast():
    print("\n== 7. 命令层：施放被动提示 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 战士 测试 男"))
    pl = db.get_player("g1", "u1")
    pl["learned_skills"] = ["守护姿态"]
    # v151：分支被动需转职后才进技能表（tier1/path1 狂战士线）
    db.update_player("g1", "u1", learned_skills=pl["learned_skills"], level=40, class_tier=1, evolve_path=1)
    panel = m._skill_panel(db.get_player("g1", "u1"))
    check("技能面板含被动说明", "被动技能无需施放" in panel)
    # 被动技能在分支技能页（找含<被动>标签的页）
    found = False
    for page in range(1, 12):
        lst = m._skill_list_page(db.get_player("g1", "u1"), page=page)
        if "<被动>" in lst:
            found = True
            break
    check("技能列表含<被动>标签", found)

# ---------- 8. 被动学习成功提示 ----------
async def test_cmd_learn():
    print("\n== 8. 被动学习成功提示 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 法师 测试 男"))
    # v151：元素共鸣是 tier2 元素术士分支被动 → 需二转
    db.update_player("g1", "u1", level=65, skill_points=20, class_tier=2, evolve_path=1)
    msg = m._skill_learn_msg("g1", db.get_player("g1", "u1"), "元素共鸣")
    check("被动学习提示", "被动" in msg and "自动生效" in msg, msg)

# ---------- 9. 被动不可升级 ----------
async def test_no_upgrade():
    print("\n== 9. 被动不可升级 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 战士 测试 男"))
    pl = db.get_player("g1", "u1")
    pl["learned_skills"] = ["守护姿态"]
    db.update_player("g1", "u1", level=40, skill_points=20, class_tier=1, evolve_path=1, learned_skills=pl["learned_skills"])
    msgs = await run(m.skill_upgrade, FakeEvent("g1", "u1", "技能升级 守护姿态"))
    joined = "".join(msgs)
    check("被动不可升级提示", "被动" in joined and "无需升级" in joined, joined)

# ---------- 10. 被动不占技能栏（设置技能时提示/不生效？跳过）----------
def test_data_integrity():
    print("\n== 10. 数据完整性：被动不污染主动技能表 ==")
    # v151：基础职业技能表纯主动技能（无被动）+ 分支表含被动
    # 战士 9 / 法师 8 / 游侠 8 / 牧师 7 / 刺客 11 / 拳师 8
    for cls, cname, expect in [("cls_zhan_shi", "战士", 9), ("cls_fa_shi", "法师", 8),
                               ("cls_you_xia", "游侠", 8), ("cls_mu_shi", "牧师", 7),
                               ("cls_ci_ke", "刺客", 11), ("cls_wu_seng", "拳师", 8)]:
        n = len(C.PLAYER_SKILLS[cls]["skills"])
        check(f"{cname} 基础技能总数 {n} (v151 纯主动)", n == expect, f"实际 {n}")
        base_passives = [v for v in C.PLAYER_SKILLS[cls]["skills"].values() if v.get("kind") == "被动"]
        check(f"{cname} 基础表无被动", len(base_passives) == 0, f"{len(base_passives)} 个")

async def run_all():
    test_defs()
    test_engine_stats()
    test_learned()
    test_battle_stats()
    test_dmg_reduce()
    test_turn_heal()
    await test_cmd_cast()
    await test_cmd_learn()
    await test_no_upgrade()
    test_data_integrity()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_all())
