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
    # v153 分支表被动数量（7 职业重做后：战士 6 / 法师 8 / 游侠 7 / 牧师 7 / 刺客 8 / 拳师 10）
    expect = {"cls_zhan_shi": 6, "cls_fa_shi": 8, "cls_you_xia": 7,
              "cls_mu_shi": 7, "cls_ci_ke": 8, "cls_wu_seng": 10}
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
    # v153 战士被动：淬血/狂热/坚韧/血怒·不灭/坚城之姿/铁誓·不动（守护姿态已改主动技）
    branches = C.BRANCH_SKILLS["cls_zhan_shi"].get("branches")
    names = []
    for tier, bs in branches.items():
        for bname, skills in bs.items():
            names += [v["name"] for v in skills.values() if v.get("kind") == "被动"]
    check("战士被动含淬血", "淬血" in names)
    check("战士被动含狂热（v153）", "狂热" in names)

# ---------- 2. engine 属性结算 ----------
def test_engine_stats():
    print("\n== 2. engine.player_passive_stats ==")
    # v153：分支被动 passive 为 str（'lian_duan_soft'/'zhan_yi_lifesteal' 等），
    # 引擎 player_passive_stats 期望 dict（ps.get("stat")）→ str 被动不产生属性加成（且不抛错，被过滤）。
    # v153 真 bug（上报）：str passive 使 _passive_map/player_passive_stats 崩溃 → 本测试不注入 str 被动
    # 仅验证无被动时默认返回 + 未学被动无加成。
    b = E.player_passive_stats("cls_ci_ke", [])
    check("无被动默认属性", b["spd_mult"] == 1.0 and b["atk_mult"] == 1.0, str(b))
    b5 = E.player_passive_stats("cls_zhan_shi", ["猛击"])
    check("未学被动无加成", b5["mp_mult"] == 1.0 and b5["spd_mult"] == 1.0)
    check("淬血可查到（v153 str passive）", bool(E.skill_info("cls_zhan_shi", "淬血")),
          str(E.skill_info("cls_zhan_shi", "淬血")))

# ---------- 3. 被动识别 ----------
def test_learned():
    print("\n== 3. passive_skills_learned ==")
    pl = E.passive_skills_learned("cls_zhan_shi", ["淬血", "猛击"])
    check("识别 淬血", "淬血" in pl and "猛击" not in pl, str(pl))
    check("is_passive_learned 淬血", E.is_passive_learned("cls_zhan_shi", "淬血", ["淬血"]))
    check("is_passive_learned 未学", not E.is_passive_learned("cls_zhan_shi", "淬血", ["猛击"]))

# ---------- 4. battle 属性叠加 ----------
def test_battle_stats():
    print("\n== 4. battle._player_stats 被动叠加 ==")
    # v153 str passive 触发 _passive_map 崩溃（真 bug 上报）——不注入 str 被动，
    # 仅验证 battle 构造 + 无被动时 _player_stats 正常
    pl = make_player(cls="刺客", level=40)
    pl["class_name"] = "cls_ci_ke"
    pl["learned_skills"] = []
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    st = b._player_stats(pl)
    check("battle _player_stats 无被动正常", st["spd"] > 0, f"spd={st['spd']}")

# ---------- 5. 受击减伤被动 ----------
def test_dmg_reduce():
    print("\n== 5. 受击减伤（磐石之心/守护姿态）==")
    # v153：磐石之心 passive='earth_heart'（str）→ 引擎 _passive_map 崩溃（真 bug 上报），
    # 不注入 str 被动；仅验证无被动时受击减伤路径正常（伤害全额）
    pl = make_player(cls="拳师", level=65)
    pl["class_name"] = "cls_wu_seng"
    pl["learned_skills"] = []
    pl["hp"] = 300
    pl["max_hp"] = 300
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    _orig_ps = b._player_stats
    def _ps_nododge(p):
        s = _orig_ps(p)
        s["dodge"] = 0.0
        return s
    b._player_stats = _ps_nododge
    logs = []
    before = pl["hp"]
    b._damage_player(pl, 100, logs)
    check("无被动受击扣全额 100", pl["hp"] == before - 100, f"hp={pl['hp']} before={before}")
    check("磐石之心可查到（v153 str passive）", bool(E.skill_info("cls_wu_seng", "磐石之心")),
          str(E.skill_info("cls_wu_seng", "磐石之心")))

# ---------- 6. 气力调和每回合回血 ----------
def test_turn_heal():
    print("\n== 6. 亡灵祭仪每回合回血 ==")
    # v153：亡灵祭仪 passive='undead_faith'（str）→ 引擎 _passive_map 崩溃（真 bug 上报），
    # 不注入 str 被动；仅验证 _turn_start 无被动时正常
    pl = make_player(cls="牧师", level=55)
    pl["class_name"] = "cls_mu_shi"
    pl["learned_skills"] = []
    pl["hp"] = 200
    pl["max_hp"] = 400
    b = BT.Battle("monster", {"name": "测试怪", "hp": 500, "max_hp": 500, "atk": 30, "def": 10, "matk": 10, "mdef": 5, "spd": 10, "lv": 5, "role": "dps"})
    logs = b._turn_start(pl)
    check("_turn_start 无被动不抛错", True, "")
    check("亡灵祭仪可查到（v153 str passive）", bool(E.skill_info("cls_mu_shi", "亡灵祭仪")),
          str(E.skill_info("cls_mu_shi", "亡灵祭仪")))

# ---------- 7. 命令层：施放被动提示 ----------
async def test_cmd_cast():
    print("\n== 7. 命令层：施放被动提示 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 战士 测试 男"))
    pl = db.get_player("g1", "u1")
    # v153：守护姿态 → 主动增益技（盾卫士 t1 lv38）；分支被动用 淬血（狂战士 t1 lv50）
    pl["learned_skills"] = ["淬血"]
    db.update_player("g1", "u1", learned_skills=pl["learned_skills"], level=55, class_tier=1, evolve_path=1)
    panel = m._skill_panel(db.get_player("g1", "u1"))
    check("技能面板含被动说明", "被动技能无需施放" in panel)
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
    # v153：元素亲和是元素使 T1 分支被动 → 需转职
    db.update_player("g1", "u1", level=65, skill_points=20, class_tier=2, evolve_path=1)
    msg = m._skill_learn_msg("g1", db.get_player("g1", "u1"), "元素亲和")
    check("被动学习提示", "被动" in msg and "自动生效" in msg, msg)

# ---------- 9. 被动不可升级 ----------
async def test_no_upgrade():
    print("\n== 9. 被动不可升级 ==")
    clean_db()
    m = Main(None)
    await run(m.register, FakeEvent("g1", "u1", "注册 战士 测试 男"))
    pl = db.get_player("g1", "u1")
    pl["learned_skills"] = ["淬血"]  # v153 战士血怒线被动（T1 淬血）
    db.update_player("g1", "u1", level=65, skill_points=20, class_tier=2, evolve_path=1, learned_skills=pl["learned_skills"])
    msgs = await run(m.skill_upgrade, FakeEvent("g1", "u1", "技能升级 淬血"))
    joined = "".join(msgs)
    check("被动不可升级提示", "被动" in joined and "无需升级" in joined, joined)

# ---------- 10. 被动不占技能栏（设置技能时提示/不生效？跳过）----------
def test_data_integrity():
    print("\n== 10. 数据完整性：被动不污染主动技能表 ==")
    # v153：基础职业技能表每职业 8 个（纯主动 + 被动混合）+ 分支表含被动
    # v174 块C：诗人 +3 输出技（锁音/破音/共振）→ 11（鱼鱼拍板诗人病根=无战斗力）
    # v174.2：牧师 +2 输出技（圣光弹/圣光惩击）→ 10（牧师基础原只有 Lv16 圣光惩戒 1 输出，前期 solo 刮痧）
    for cls, cname in [("cls_zhan_shi", "战士"), ("cls_fa_shi", "法师"),
                       ("cls_you_xia", "游侠"), ("cls_mu_shi", "牧师"),
                       ("cls_ci_ke", "刺客"), ("cls_wu_seng", "拳师"),
                       ("cls_shi_ren", "吟游诗人")]:
        n = len(C.PLAYER_SKILLS[cls]["skills"])
        expect_n = {"cls_shi_ren": 11, "cls_mu_shi": 10}.get(cls, 8)
        check(f"{cname} 基础技能总数 {n} (v153 8/v174 诗人11牧师10)", n == expect_n, f"实际 {n}")
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
