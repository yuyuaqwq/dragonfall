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
    print("\n== 1. 被动技能定义 ==")
    for cls, cname in [("cls_zhan_shi", "战士"), ("cls_fa_shi", "法师"), ("cls_you_xia", "游侠"),
                       ("cls_mu_shi", "牧师"), ("cls_ci_ke", "刺客"), ("cls_wu_seng", "拳师")]:
        tbl = C.PLAYER_SKILLS[cls]["skills"]
        passives = [v for v in tbl.values() if v.get("kind") == "被动"]
        # v106.2：战士/游侠新增穿透被动；v112.1：各职业 +1 一转觉醒被动（Lv.30）
        expect_n = 6 if cls in ("cls_zhan_shi", "cls_you_xia") else 5
        check(f"{cname} 被动数量={expect_n}", len(passives) == expect_n, f"实际 {len(passives)}")
        for v in passives:
            check(f"  {v['name']} lv={v['lv']} mp=0", v.get("mp") == 0 and v.get("lv") in (12, 25, 30, 38, 55, 45, 48),
                  f"mp={v.get('mp')} lv={v.get('lv')}")
    # 抽查代表性被动
    zs = C.PLAYER_SKILLS["cls_zhan_shi"]["skills"]
    names = [v["name"] for v in zs.values() if v.get("kind") == "被动"]
    check("战士被动含战意高涨", "战意高涨" in names)
    check("战士被动含铁壁之心", "铁壁之心" in names)

# ---------- 2. engine 属性结算 ----------
def test_engine_stats():
    print("\n== 2. engine.player_passive_stats ==")
    b = E.player_passive_stats("法师", ["魔力涌动"])
    check("法师魔力涌动 mp_mult=1.15", abs(b["mp_mult"] - 1.15) < 1e-9, str(b))
    b2 = E.player_passive_stats("游侠", ["风行步", "鹰眼"])
    check("游侠风行步 spd_mult=1.08", abs(b2["spd_mult"] - 1.08) < 1e-9, str(b2))
    check("游侠鹰眼 crit_add=0.03", abs(b2["crit_add"] - 0.03) < 1e-9, str(b2))
    b3 = E.player_passive_stats("战士", ["战意高涨"])
    check("战士战意高涨 无属性加成(条件型)", b3["atk_mult"] == 1.0, str(b3))
    # 未学被动 → 无加成
    b4 = E.player_passive_stats("战士", ["猛击"])
    check("未学被动无加成", b4["mp_mult"] == 1.0 and b4["spd_mult"] == 1.0)

# ---------- 3. 被动识别 ----------
def test_learned():
    print("\n== 3. passive_skills_learned ==")
    pl = E.passive_skills_learned("战士", ["战意高涨", "铁壁之心", "猛击"])
    check("识别 战意高涨+铁壁之心", "战意高涨" in pl and "铁壁之心" in pl and "猛击" not in pl, str(pl))
    check("is_passive_learned 铁壁之心", E.is_passive_learned("战士", "铁壁之心", ["战意高涨", "铁壁之心"]))
    check("is_passive_learned 未学", not E.is_passive_learned("战士", "铁壁之心", ["猛击"]))

# ---------- 4. battle 属性叠加 ----------
def test_battle_stats():
    print("\n== 4. battle._player_stats 被动叠加 ==")
    pl = make_player(cls="游侠", level=30)
    pl["class_name"] = "cls_you_xia"  # 生产 class_name 是 cls_id（make_player 已 resolve，此行保留兼容）
    pl["learned_skills"] = ["风行步"]
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    st = b._player_stats(pl)
    base_spd = E.player_final_stats(pl["class_name"], pl["level"], pl.get("equipment", {}), pl.get("class_tier", 0), pl.get("attributes"), pl.get("evolve_path", 0), None, pl.get("race"))["spd"]  # v87.17 与 _player_stats 同参（race）
    check("风行步 spd +8%", st["spd"] == int(base_spd * 1.08), f"st={st['spd']} base={base_spd}")
    # 法师魔力涌动
    pl2 = make_player(cls="法师", level=40)
    pl2["class_name"] = "cls_fa_shi"
    pl2["learned_skills"] = ["魔力涌动"]
    b2 = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    st2 = b2._player_stats(pl2)
    base_mp = E.player_final_stats(pl2["class_name"], pl2["level"], pl2.get("equipment", {}), pl2.get("class_tier", 0), pl2.get("attributes"), pl2.get("evolve_path", 0), None, pl2.get("race"))["max_mp"]  # v87.17 同参
    check("魔力涌动 max_mp +15%", st2["max_mp"] == int(base_mp * 1.15), f"st={st2['max_mp']} base={base_mp}")

# ---------- 5. 受击减伤被动 ----------
def test_dmg_reduce():
    print("\n== 5. 受击减伤（铁壁之心/磐石体）==")
    pl = make_player(cls="战士", level=30)
    pl["class_name"] = "cls_zhan_shi"
    pl["learned_skills"] = ["铁壁之心"]
    pl["hp"] = 300
    pl["max_hp"] = 300
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    logs = []
    before = pl["hp"]
    b._damage_player(pl, 100, logs)
    # 100 - 5 = 95，hp 300 -> 205
    check("受击减伤5% (100→95)", pl["hp"] == before - 95, f"hp={pl['hp']} before={before}")
    check("减伤日志出现", any("被动减伤" in lg for lg in logs), str(logs))

# ---------- 6. 气力调和每回合回血 ----------
def test_turn_heal():
    print("\n== 6. 气力调和每回合回血 ==")
    pl = make_player(cls="拳师", level=40)
    pl["class_name"] = "cls_wu_seng"
    pl["learned_skills"] = ["气力调和"]
    pl["hp"] = 200
    pl["max_hp"] = 400
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    logs = b._turn_start(pl)
    check("每回合回 2% (400*2%=8)", pl["hp"] == 208, f"hp={pl['hp']}")
    check("回血日志出现", any("气力调和" in lg for lg in logs), str(logs))

# ---------- 7. 命令层：施放被动提示 ----------
async def test_cmd_cast():
    print("\n== 7. 命令层：施放被动提示 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 战士 测试 男"))
    pl = db.get_player("g1", "u1")
    pl["learned_skills"] = ["战意高涨"]
    db.update_player("g1", "u1", learned_skills=pl["learned_skills"], level=15)
    panel = m._skill_panel(db.get_player("g1", "u1"))
    check("技能面板含被动说明", "被动技能无需施放" in panel)
    # 被动技能在第 2 页（每页 5 条，战士 21 技能分 5 页）
    lst2 = m._skill_list_page(db.get_player("g1", "u1"), page=4)
    check("技能列表含<被动>标签", "<被动>" in lst2, lst2[:300])

# ---------- 8. 被动学习成功提示 ----------
async def test_cmd_learn():
    print("\n== 8. 被动学习成功提示 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 法师 测试 男"))
    db.update_player("g1", "u1", level=15, skill_points=20)
    msg = m._skill_learn_msg("g1", db.get_player("g1", "u1"), "烈焰亲和")
    check("被动学习提示", "被动" in msg and "自动生效" in msg, msg)

# ---------- 9. 被动不可升级 ----------
async def test_no_upgrade():
    print("\n== 9. 被动不可升级 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 战士 测试 男"))
    pl = db.get_player("g1", "u1")
    pl["learned_skills"] = ["战意高涨"]
    db.update_player("g1", "u1", level=15, skill_points=20, learned_skills=pl["learned_skills"])
    msgs = await run(m.skill_upgrade, FakeEvent("g1", "u1", "技能升级 战意高涨"))
    joined = "".join(msgs)
    check("被动不可升级提示", "被动" in joined and "无需升级" in joined, joined)

# ---------- 10. 被动不占技能栏（设置技能时提示/不生效？跳过）----------
def test_data_integrity():
    print("\n== 10. 数据完整性：被动不污染主动技能表 ==")
    # 阶段六：新世界每职业 10 主动 + 4 被动 = 14；v95 补 Lv.2 过渡技能 +1 → 15
    # v106.2：战士/游侠 +穿透被动 → 16；v112.1：各职业 +1 一转觉醒被动（Lv.30）
    # v114.2：蓄力/打断新技能——战士+蓄力斩、法师+陨石术+法术禁制、游侠+蓄力狙击、牧师+大治疗术
    for cls, cname, expect in [("cls_zhan_shi", "战士", 18), ("cls_fa_shi", "法师", 18),
                               ("cls_you_xia", "游侠", 18), ("cls_mu_shi", "牧师", 17),
                               ("cls_ci_ke", "刺客", 16), ("cls_wu_seng", "拳师", 16)]:
        n = len(C.PLAYER_SKILLS[cls]["skills"])
        check(f"{cname} 技能总数 {n} (10基础+5被动+觉醒)", n == expect, f"实际 {n}")

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
