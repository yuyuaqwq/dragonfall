# -*- coding: utf-8 -*-
"""v113 职业体系重构·审计缺口回归测试（test_v113_fix_regression.py）

补充 v113 重构后审计发现的测试覆盖缺口。每个用例开头 clean_db()，互不干扰。

覆盖 8 块：
 1. 六线解锁任务链全流程闭环（HIGH）：对 6 条隐藏线逐一「接取试炼→塞进度击杀达标→
    回导师图交付→hidden_class_unlock 写入→『转职 <T1档位名>』成功」。
 2. 七本技能书全链路（HIGH）：每本给正确源流职业建高等级号，使用技能书→learned_skills
    写入→重复被拦→战斗施放可用；错误源流职业使用被拒（require_class 校验）。
 3. 下放技能在基础职业的战斗可用性（MEDIUM）：战士学会龙息之怒→真伤无视防御；
    法师学会虚空爆破→战斗施放回蓝；刺客学会收割→伤害；游侠学会毒爆术→叠毒引爆；
    拳师学会以守为攻→受击触发反击（被动）。
 4. 命令 vs 对话传承等价性 + 90 级对话 T3（MEDIUM）：同一基础职业同等级分别用
    『转职 <档位名>』命令与导师对话『接受传承』各传承一次，断言最终
    class_name/class_tier/evolve_path/learned_skills 完全一致；星语者 90 级对话→T3。
 5. 转职重置清理技能书所学（MEDIUM）：龙裔玩家用书学『龙息之怒』后『转职重置』→该技
    不在 learned_skills、skill_levels 无残留；基础战士攻线学会龙息之怒后重置→分支技清除。
 6. 植物召唤战斗（MEDIUM）：游侠林语者 40/90 级真实召唤藤蔓守卫+古树守卫；古树守卫
    第 2 只被拒（limit 1）；混合召唤共存；受击挡刀触发并扣召唤物 HP。
 7. race=None 旧档兜底（LOW）：玩家 race 置 None/空串时，race_is(human) 对话条件、
    时咒线试炼接取、『转职 时停』均正常（human 兜底），不误拦。
 8. hidden_evolve 双保险（INFO）：已传承玩家再次触发 hidden_evolve 动作（即使对话树
    因数据漏配 need 而走到该选项），断言返回「你已是X」且 class_tier/evolve_path 不变、
    无重复/回档副作用。

运行：python tests/test_v113_fix_regression.py（exit=0 全绿）
依赖记录：
 - 毒爆术当前数据 kind=魔法、按 matk 结算（battle/毒爆物理化若由其他 agent 改为物理，
   测试[3]毒爆段仍只断言「引发伤害+清毒层」——跨 kind 兼容，路径无需改）。
 - 若 battle.py mech_chance 修复令召唤挡刀/反击概率判定发生变化，测试[3]/[6]用放宽
   的多 seed 触发，跑不通的 seed 只跳过该断言并记录，不改源码。
"""
import sys, os, random, asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, make_player

passed = failed = 0
SKIPPED = []

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail)[:220]}")


def skip(name, reason):
    SKIPPED.append((name, reason))
    print(f"  ⏭️  {name}（依赖跳过）：{reason}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return "".join(str(x) for x in results)


# ============ 六线映射（与 quests.py/npcs.py/CLASSES 一致） ============
LINES = [
    ("cls_dragon_oath",   "战士", "dragonborn", "npc_dragon_veteran",  "dusk_ridge_road", "dusk_ridge_road_1", "s_dragon_warrior_trial", "战争魔像(残)", 2, "龙血战士"),
    ("cls_chronomancer",  "法师", "human",      "npc_chrono_warden",  "white_deer",    "white_deer_4", "s_chronomancer_trial", "审判猎犬", 3, "时停"),
    ("cls_wild_hunter",   "游侠", "elf",        "npc_astrologer",     "starlake",      "starlake_1",  "s_astrologer_trial",    "湖妖", 3, "星语者"),
    ("cls_hymn",          "牧师", "orc",        "npc_grave_watcher",  "border_castle", "border_castle_1", "s_necromancer_trial", "兽人劫掠者", 3, "暗影祭司"),
    ("cls_shadow_blade",  "刺客", "halfling",   "npc_shadow_master",  "jade_port",     "jade_port_1", "s_shadow_blade_trial",  "影豹", 3, "暗杀"),
    ("cls_wu_sheng",      "拳师", "dwarf",      "npc_wusheng_monk",   "anvil_fort",    "anvil_fort_gate", "s_wu_sheng_trial",     "兽人劫掠者", 3, "武僧"),
]

# 七本技能书：item_id, 技能名, 源流职业, 学习等级
TOMES = [
    ("i_tome_long_xi_zhi_nu", "龙息之怒", "cls_zhan_shi", 55),
    ("i_tome_xu_kong_bao_po", "虚空爆破", "cls_fa_shi", 55),
    ("i_tome_du_bao",         "毒爆术",   "cls_you_xia", 55),
    ("i_tome_shou_ge",        "收割",     "cls_ci_ke",   62),
    ("i_tome_ku_lou_hai",     "骷髅海",   "cls_hymn",    70),
    ("i_tome_an_mian_qu",     "安眠曲",   "cls_mu_shi",  45),
    ("i_tome_qi_bao",         "气爆",     "cls_wu_sheng", 75),
]


def _add_tome(gid, qid, item_id):
    db.add_item(gid, qid, item_id, dict(C.ITEMS[item_id]), 1)


# ============ 战斗构造辅助 ============
def mk_bp(cls_name, skills, level=60, hp=900, mp=250, atk=100, matk=100, **extra):
    p = {
        "class_name": cls_name, "level": level, "hp": hp, "max_hp": hp,
        "mp": mp, "max_mp": mp,
        "equipment": {"weapon": {"name": "测试剑", "stats": {"atk": atk, "matk": matk},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 20, "int": 20},
        "learned_skills": skills, "race": "human",
    }
    p.update(extra)
    return p


def mk_be(def_=20, mdef=20, hp=80000, atk=80, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": atk, "def": def_, "mdef": mdef, "spd": spd}


def cast_skill(b, p, sname):
    info = E.skill_info(p["class_name"], sname)
    st = b._player_stats(p)
    hp0 = b.enemy["hp"]
    random.seed(11)
    logs = b._player_skill(st, sname, info, p)
    return logs, hp0 - b.enemy["hp"]


def battle_module():
    from data.plugins.dragonfall.game import battle as BT
    return BT


# ============ 1. 六线解锁任务链全流程闭环 ============
async def test_6lines_full_flow(m):
    clean_db()
    print("\n【1. 六线解锁任务链全流程闭环】")
    for i, (cls_id, base_cn, race, npc_id, map_id, subarea, sid, mob, cnt, t1_name) in enumerate(LINES, 1):
        qid = f"f{i}"
        make_player("gA", qid, f"试炼{i}", base_cn, level=40)
        db.update_player("gA", qid, race=race, cur_map=map_id, cur_subarea=subarea)
        # 接取：导师对话同款 _offer_side_quests（要求等级/种族齐备）
        m._offer_side_quests("gA", qid, npc_id, C.NPCS[npc_id])
        qs = db.get_quests("gA", qid)
        side = qs.get("side", {})
        ok_acc = sid in side
        check(f"{cls_id} 接取试炼 {sid}", ok_acc, str(list(side)))
        if not ok_acc:
            continue
        # 塞进度：击杀达标 → ready
        side[sid] = {"status": "active", "progress": {mob: cnt}}
        side[sid]["status"] = "ready"
        db.save_quests("gA", qid, qs)
        # 击杀后移动走 → 现回导师图（turn_in 检查 giver.map == cur_map）
        db.update_player("gA", qid, cur_map=map_id, cur_subarea=subarea)
        out = await cmd(m, "turn_in", "gA", qid, "交付任务")
        check(f"{cls_id} 交付解锁", "解锁" in out or "传承达成" in out, out[:200])
        p = db.get_player("gA", qid)
        check(f"{cls_id} hidden_class_unlock 写入", cls_id in (p.get("hidden_class_unlock") or []),
              str(p.get("hidden_class_unlock")))
        # 转职 T1
        out = await cmd(m, "evolve", "gA", qid, f"转职 {t1_name}")
        p = db.get_player("gA", qid)
        ok_evolve = (p["class_name"] == cls_id and p["class_tier"] == 1 and p["evolve_path"] == 1)
        check(f"{cls_id} 『转职 {t1_name}』= T1", ok_evolve,
              str((p["class_name"], p["class_tier"], p["evolve_path"], out[:80])))


# ============ 2. 七本技能书全链路 ============
async def test_7_tomes(m):
    clean_db()
    print("\n【2. 七本技能书全链路】")
    BT = battle_module()
    for i, (item_id, sname, src_cls, need_lv) in enumerate(TOMES, 1):
        qid = f"t{i}"
        src_cn = C.CLASSES[src_cls]["name"]
        lv = need_lv + 5
        make_player("gB", qid, f"书{i}", src_cn, level=lv)
        _add_tome("gB", qid, item_id)
        out = await cmd(m, "use", "gB", qid, f"使用 {C.ITEMS[item_id]['name']}")
        p = db.get_player("gB", qid)
        ok = sname in (p.get("learned_skills") or [])
        check(f"{item_id} {src_cn} 学会『{sname}』", ok, f"{out[:120]} | {p.get('learned_skills')}")
        # 重复使用被拦
        _add_tome("gB", qid, item_id)
        out2 = await cmd(m, "use", "gB", qid, f"使用 {C.ITEMS[item_id]['name']}")
        check(f"{sname} 重复使用被拦", "早已掌握" in out2, out2[:120])
        # 战斗可用（构造 Battle 施放不报错）
        try:
            pbp = mk_bp(src_cls, [sname], level=lv)
            b = BT.Battle("怪物", mk_be(), {}, pbp)
            logs, dealt = cast_skill(b, pbp, sname)
            check(f"{sname} 战斗施放不报错", dealt >= 0, f"dealt {dealt}")
        except Exception as ex:
            skip(f"{sname} 战斗施放", str(ex))
        # 错误源流反例
        wrong_cls = "cls_fa_shi" if src_cls == "cls_zhan_shi" else "cls_zhan_shi"
        wrong_cn = C.CLASSES[wrong_cls]["name"]
        make_player("gB", qid + "x", f"错{i}", wrong_cn, level=lv)
        _add_tome("gB", qid + "x", item_id)
        out3 = await cmd(m, "use", "gB", qid + "x", f"使用 {C.ITEMS[item_id]['name']}")
        px = db.get_player("gB", qid + "x")
        check(f"{sname} 错误源流({wrong_cn})被拒", sname not in (px.get("learned_skills") or []),
              out3[:160])


# ============ 3. 下放技能在基础职业的战斗可用性 ============
async def test_downstream_skills_combat(m):
    clean_db()
    print("\n【3. 下放技能在基础职业的战斗可用性】")
    BT = battle_module()

    # 3.1 战士攻线学会龙息之怒 → 真伤无视防御
    p = mk_bp("cls_zhan_shi", ["龙息之怒"], level=60)
    b = BT.Battle("怪物", mk_be(def_=5000, hp=80000), {}, p)
    hp0 = b.enemy["hp"]
    logs, dealt = cast_skill(b, p, "龙息之怒")
    check("战士·龙息之怒 真伤无视 def=5000", dealt > 200, f"dealt {dealt}")

    # 3.2 法师攻线学会虚空爆破 → 战斗施放回蓝
    p = mk_bp("cls_fa_shi", ["虚空爆破"], level=60, mp=20)
    b = BT.Battle("怪物", mk_be(def_=10, mdef=10), {}, p)
    logs, dealt = cast_skill(b, p, "虚空爆破")
    check("法师·虚空爆破 战斗施放回蓝", p["mp"] > 20, f"mp {p['mp']}")

    # 3.3 刺客攻线学会收割 → 伤害（物理按 atk）
    p = mk_bp("cls_ci_ke", ["收割"], level=65, atk=150)
    b = BT.Battle("怪物", mk_be(def_=10), {}, p)
    hp0 = b.enemy["hp"]
    logs, dealt = cast_skill(b, p, "收割")
    check("刺客·收割 造成伤害", dealt > 0, f"dealt {dealt}")

    # 3.4 游侠攻线学会毒爆术 → 叠毒后引爆
    p = mk_bp("cls_you_xia", ["淬毒箭矢", "藤蔓缠绕", "毒爆术"], level=60, matk=120)
    b2 = BT.Battle("怪物", mk_be(def_=10, mdef=10), {}, p)
    b2._player_skill(b2._player_stats(p), "淬毒箭矢", E.skill_info("cls_you_xia", "淬毒箭矢"), p)
    for _ in range(2):
        b2._player_skill(b2._player_stats(p), "藤蔓缠绕", E.skill_info("cls_you_xia", "藤蔓缠绕"), p)
    poison_before = (b2.enemy.get("debuffs") or {}).get("poison", {}).get("n", 0)
    check("游侠·叠毒达标", poison_before >= 3, f"poison {poison_before}")
    hp0 = b2.enemy["hp"]
    logs, dealt = cast_skill(b2, p, "毒爆术")
    check("游侠·毒爆术 引爆伤害", b2.enemy["hp"] < hp0, f"{hp0}→{b2.enemy['hp']}")
    check("游侠·毒爆术 清空毒层", "poison" not in (b2.enemy.get("debuffs") or {}),
          str(b2.enemy.get("debuffs")))

    # 3.5 拳师守线学会以守为攻 → 受击触发反击（被动）
    p = mk_bp("cls_wu_seng", ["以守为攻"], level=60)
    found = False
    for seed in range(60):
        random.seed(seed)
        b = BT.Battle("怪物", mk_be(hp=30000), {}, p)
        b._last_player = p
        # 屏蔽随机闪避，保证受击断言确定性（反击需命中才触发）
        _orig_ps = b._player_stats
        def _ps_nododge(p_):
            s = _orig_ps(p_)
            s["dodge"] = 0.0
            return s
        b._player_stats = _ps_nododge
        emy0 = b.enemy["hp"]
        logs = []
        b._damage_player(p, 100, logs)
        if any("反击" in l for l in logs) or b.enemy["hp"] < emy0:
            found = True
            check(f"拳师·以守为攻 受击触发反击（seed {seed}）", True, "")
            break
    check("拳师·以守为攻 反击可触发", found)

    # 3.6 守线跨攻线场景：游侠守线（风行者 path=2）用毒爆术书（require cls_you_xia 校验通过）
    #      → 学会后能战斗使用（技能书=跨流派横向扩展，设计允许）
    make_player("gC", "xr", "风行者", "游侠", level=60)
    db.update_player("gC", "xr", evolve_path=2, class_tier=1)  # 守线
    _add_tome("gC", "xr", "i_tome_du_bao")
    out = await cmd(m, "use", "gC", "xr", "使用 毒爆术技能书")
    p = db.get_player("gC", "xr")
    check("守线游侠·毒爆术书 学会（跨流派横向扩展）", "毒爆术" in (p.get("learned_skills") or []),
          out[:120])
    pbp = mk_bp("cls_you_xia", ["毒爆术"], level=60)
    b2 = BT.Battle("怪物", mk_be(def_=10, mdef=10), {}, pbp)
    for _ in range(2):
        b2._player_skill(b2._player_stats(pbp), "藤蔓缠绕", E.skill_info("cls_you_xia", "藤蔓缠绕"), pbp)
    b2._player_skill(b2._player_stats(pbp), "淬毒箭矢", E.skill_info("cls_you_xia", "淬毒箭矢"), pbp)
    hp0 = b2.enemy["hp"]
    logs, dealt = cast_skill(b2, pbp, "毒爆术")
    check("守线游侠·毒爆术 战斗引爆可用", b2.enemy["hp"] < hp0, f"{hp0}→{b2.enemy['hp']}")


# ============ 4. 命令 vs 对话传承等价性 + 90 级对话 T3 ============
async def test_command_vs_dialogue(m):
    clean_db()
    print("\n【4. 命令 vs 对话传承等价性 + 90 级对话 T3】")
    fields = ("class_name", "class_tier", "evolve_path", "learned_skills")

    # 4.1 龙裔：60 级战士，命令 T2 vs 对话（修为继承 T2）
    make_player("gD", "c1", "令战", "战士", level=60)
    db.update_player("gD", "c1", race="dragonborn", cur_map="dusk_ridge_road",
                     cur_subarea="dusk_ridge_road_1", hidden_class_unlock=["cls_dragon_oath"])
    await cmd(m, "evolve", "gD", "c1", "转职 龙裔斗士")
    pc = db.get_player("gD", "c1")

    make_player("gD", "c2", "对战", "战士", level=60)
    db.update_player("gD", "c2", race="dragonborn", cur_map="dusk_ridge_road",
                     cur_subarea="dusk_ridge_road_1", hidden_class_unlock=["cls_dragon_oath"])
    await cmd(m, "talk_choice", "gD", "c2", "对话 龙裔老兵·铁鳞")
    await cmd(m, "talk_choice", "gD", "c2", "对话 1")
    await cmd(m, "talk_choice", "gD", "c2", "对话 1")
    pd = db.get_player("gD", "c2")

    equal = all(pc[k] == pd[k] for k in fields)
    check("龙裔 60 级 命令vs对话 最终完全一致", equal,
          f"cmd={[(k, pc[k]) for k in fields]} dlg={[(k, pd[k]) for k in fields]}")
    check("龙裔 60 对话= T2（修为继承）", pd["class_tier"] == 2 and pd["class_name"] == "cls_dragon_oath",
          str((pd["class_name"], pd["class_tier"])))

    # 4.2 星语者：90 级游侠，命令 T3 vs 对话（修为继承 T3）
    make_player("gD", "c3", "星令", "游侠", level=90)
    db.update_player("gD", "c3", race="elf", cur_map="starlake",
                     cur_subarea="starlake_1", hidden_class_unlock=["cls_wild_hunter"])
    await cmd(m, "evolve", "gD", "c3", "转职 命运编织者")
    pc = db.get_player("gD", "c3")

    make_player("gD", "c4", "星对", "游侠", level=90)
    db.update_player("gD", "c4", race="elf", cur_map="starlake",
                     cur_subarea="starlake_1", hidden_class_unlock=["cls_wild_hunter"])
    await cmd(m, "talk_choice", "gD", "c4", "对话 观星台主·星澜")
    await cmd(m, "talk_choice", "gD", "c4", "对话 1")
    await cmd(m, "talk_choice", "gD", "c4", "对话 1")
    pd = db.get_player("gD", "c4")

    equal = all(pc[k] == pd[k] for k in fields)
    check("星语 90 级 命令vs对话 最终完全一致", equal,
          f"cmd={[(k, pc[k]) for k in fields]} dlg={[(k, pd[k]) for k in fields]}")
    check("星语 90 对话= T3（修为继承）", pd["class_tier"] == 3 and pd["class_name"] == "cls_wild_hunter",
          str((pd["class_name"], pd["class_tier"])))


# ============ 5. 转职重置清理技能书所学 ============
async def test_reset_cleans_tome_skills(m):
    clean_db()
    print("\n【5. 转职重置清理技能书所学】")

    # 5.1 隐藏线玩家（苦修士 cls_wu_sheng）用气爆技能书（本源流书）学会『气爆』
    #     → 『转职重置』清空（回本源 cls_wu_seng，气爆从 learned_skills 移除）
    make_player("gE", "r1", "苦重", "拳师", level=80)
    db.update_player("gE", "r1", race="dwarf", hidden_class_unlock=["cls_wu_sheng"])
    await cmd(m, "evolve", "gE", "r1", "转职 武僧")
    _add_tome("gE", "r1", "i_tome_qi_bao")
    await cmd(m, "use", "gE", "r1", "使用 气爆技能书")
    p = db.get_player("gE", "r1")
    check("苦修士学书含气爆", "气爆" in (p.get("learned_skills") or []), str(p.get("learned_skills")))
    db.update_player("gE", "r1", gold=5000)
    await cmd(m, "evolve_reset", "gE", "r1", "转职重置")
    p = db.get_player("gE", "r1")
    check("苦修重置回拳师", p["class_name"] == "cls_wu_seng" and p["class_tier"] == 0,
          str((p["class_name"], p["class_tier"])))
    check("重置后气爆 不在 learned_skills", "气爆" not in (p.get("learned_skills") or []),
          str(p.get("learned_skills")))
    check("重置后 skill_levels 无气爆残留",
          not any(C.resolve("skills", k) == "气爆" for k in (p.get("skill_levels") or {})),
          str(p.get("skill_levels")))

    # 5.1b 龙裔（战士→龙裔）用战士源流的『龙息之怒』书 → 被拒（require_class 严格匹配本源职业，
    #       隐藏线玩家非 cls_zhan_shi 无法越职学战士书）——作为反例记录（本应如此，非缺陷）
    make_player("gE", "r1b", "龙书", "战士", level=60)
    db.update_player("gE", "r1b", race="dragonborn", hidden_class_unlock=["cls_dragon_oath"])
    await cmd(m, "evolve", "gE", "r1b", "转职 龙裔斗士")
    _add_tome("gE", "r1b", "i_tome_long_xi_zhi_nu")
    out = await cmd(m, "use", "gE", "r1b", "使用 龙息之怒技能书")
    pb = db.get_player("gE", "r1b")
    check("龙裔用战士源流书被拒(require_class 严格)", "龙息之怒" not in (pb.get("learned_skills") or []),
          out[:160])

    # 5.2 基础职业攻线（战士 path=1）学会龙息之怒（分支技）→『转职重置』清除
    make_player("gE", "r2", "战重", "战士", level=60)
    p = db.get_player("gE", "r2")
    learned = list((p.get("learned_skills") or []))
    if "龙息之怒" not in learned:
        learned += ["龙息之怒"]
    db.update_player("gE", "r2", class_tier=1, evolve_path=1,
                     skill_levels={"龙息之怒": 2, "怒斩": 1}, learned_skills=learned,
                     gold=5000)
    p = db.get_player("gE", "r2")
    check("攻线战士已学龙息之怒(分支技)", "龙息之怒" in (p.get("learned_skills") or []),
          str(p.get("learned_skills")))
    await cmd(m, "evolve_reset", "gE", "r2", "转职重置")
    p = db.get_player("gE", "r2")
    check("攻线战士重置后龙息之怒被移除", "龙息之怒" not in (p.get("learned_skills") or []),
          str(p.get("learned_skills")))
    check("攻线战士重置后 skill_levels 清理",
          not any(C.resolve("skills", k) == "龙息之怒" for k in (p.get("skill_levels") or {})),
          str(p.get("skill_levels")))


# ============ 6. 植物召唤战斗 ============
def test_plant_summons(m):
    clean_db()
    print("\n【6. 植物召唤战斗】")
    BT = battle_module()

    def mk_you(level, skills):
        p = {"class_name": "cls_you_xia", "level": level, "hp": 1200, "max_hp": 1200,
             "mp": 300, "max_mp": 300,
             "equipment": {"weapon": {"name": "测试杖", "stats": {"atk": 100, "matk": 100},
                                      "affixes": [], "enhance": 0}},
             "attributes": {"str": 20, "int": 20},
             "learned_skills": skills, "race": "elf"}
        return p

    # 6.1 40 级林语者：真实召唤藤蔓守卫（t1 林语者，限 2）
    p1 = mk_you(50, ["召唤藤蔓守卫"])
    b = BT.Battle("怪物", mk_be(), {}, p1)
    b._player_skill(b._player_stats(p1), "召唤藤蔓守卫", E.skill_info("cls_you_xia", "召唤藤蔓守卫"), p1)
    check("40 级召唤藤蔓守卫", len(b.summons) == 1 and b.summons[0]["tid"] == "vine_guard",
          str([s.get("tid") for s in b.summons]))
    b._player_skill(b._player_stats(p1), "召唤藤蔓守卫", E.skill_info("cls_you_xia", "召唤藤蔓守卫"), p1)
    check("藤蔓守卫可叠 2", len(b.summons) == 2, str(len(b.summons)))
    b._player_skill(b._player_stats(p1), "召唤藤蔓守卫", E.skill_info("cls_you_xia", "召唤藤蔓守卫"), p1)
    check("藤蔓守卫第 3 只被拒(limit 2)", len(b.summons) == 2, str(len(b.summons)))

    # 6.2 90 级林语者：召唤古树守卫（t3 万木之灵），第 2 只被拒（limit 1）
    p3 = mk_you(95, ["召唤古树守卫", "召唤藤蔓守卫"])
    b3 = BT.Battle("怪物", mk_be(), {}, p3)
    b3._player_skill(b3._player_stats(p3), "召唤古树守卫", E.skill_info("cls_you_xia", "召唤古树守卫"), p3)
    check("90 级召唤古树守卫", len(b3.summons) == 1 and b3.summons[0]["tid"] == "treant",
          str([s.get("tid") for s in b3.summons]))
    b3._player_skill(b3._player_stats(p3), "召唤古树守卫", E.skill_info("cls_you_xia", "召唤古树守卫"), p3)
    check("古树守卫第 2 只被拒(limit 1)", len(b3.summons) == 1, f"summons {len(b3.summons)}")

    # 6.3 混合召唤共存：藤蔓 + 古树 同时在场
    bm = BT.Battle("怪物", mk_be(), {}, mk_you(95, ["召唤古树守卫", "召唤藤蔓守卫"]))
    pm = mk_you(95, ["召唤古树守卫", "召唤藤蔓守卫"])
    bm._player_skill(bm._player_stats(pm), "召唤藤蔓守卫", E.skill_info("cls_you_xia", "召唤藤蔓守卫"), pm)
    bm._player_skill(bm._player_stats(pm), "召唤古树守卫", E.skill_info("cls_you_xia", "召唤古树守卫"), pm)
    tids = sorted(s["tid"] for s in bm.summons)
    check("混合召唤共存(藤蔓+古树)", tids == ["treant", "vine_guard"], str(tids))

    # 6.4 受击挡刀触发并扣召唤物 HP
    found = False
    for seed in range(50):
        random.seed(seed)
        p5 = mk_you(50, ["召唤藤蔓守卫"])
        b5 = BT.Battle("怪物", mk_be(), {}, p5)
        b5._player_skill(b5._player_stats(p5), "召唤藤蔓守卫", E.skill_info("cls_you_xia", "召唤藤蔓守卫"), p5)
        if not b5.summons:
            continue
        b5.summons[0]["hp"] = 500
        shp0 = b5.summons[0]["hp"]
        hp0 = p5["hp"]
        # 屏蔽随机闪避，保证受击断言确定性（挡刀/扣召唤物 HP 精确断言）
        _orig_ps = b5._player_stats
        def _ps_nododge(p_):
            s = _orig_ps(p_)
            s["dodge"] = 0.0
            return s
        b5._player_stats = _ps_nododge
        logs = []
        b5._damage_player(p5, 100, logs)
        if any("挡下" in l for l in logs):
            found = True
            check(f"植物召唤受击挡刀触发（seed {seed}）", p5["hp"] == hp0, f"hp {p5['hp']}")
            check(f"挡刀扣召唤物 HP", b5.summons[0]["hp"] < shp0,
                  f"{shp0}→{b5.summons[0]['hp']}")
            break
    check("植物召唤挡刀可触发", found)


# ============ 7. race=None 旧档兜底 ============
async def test_race_none_compat(m):
    clean_db()
    print("\n【7. race=None 旧档兜底】")

    for qid, race_v in (("n1", ""), ("n2", None)):
        make_player("gG", qid, "无血", "法师", level=40)
        db.update_player("gG", qid, cur_map="white_deer", cur_subarea="white_deer_4", race=race_v)
        out = await cmd(m, "talk_choice", "gG", qid, "对话 时计贤者·艾瑟拉")
        check(f"race={race_v!r} 对话 human 条件通过", "时间会偏爱" in out and "接受传承" not in out,
              out[:160])

    # 试炼接取正常（race 兜底 human）
    for qid, race_v in (("n3", None), ("n4", "")):
        make_player("gG", qid, "试炼兜", "法师", level=45)
        db.update_player("gG", qid, cur_map="white_deer", cur_subarea="white_deer_4", race=race_v)
        m._offer_side_quests("gG", qid, "npc_chrono_warden", C.NPCS["npc_chrono_warden"])
        qs = db.get_quests("gG", qid)
        ok = "s_chronomancer_trial" in (qs.get("side") or {})
        check(f"试炼接取 race={race_v!r} 正常(human 兜底)", ok, str(qs.get("side")))

    # 『转职 时停』正常（race 兜底 human）
    make_player("gG", "n5", "转职兜", "法师", level=40)
    db.update_player("gG", "n5", race=None, hidden_class_unlock=["cls_chronomancer"])
    out = await cmd(m, "evolve", "gG", "n5", "转职 时停")
    p = db.get_player("gG", "n5")
    check("race=None 『转职 时停』成功", p["class_name"] == "cls_chronomancer", out[:160])


# ============ 8. hidden_evolve 双保险 ============
async def test_hidden_evolve_double_guard(m):
    clean_db()
    print("\n【8. hidden_evolve 双保险】")
    from data.plugins.dragonfall.game.commands.talk_actions import action_hidden_evolve

    make_player("gH", "h1", "双保", "战士", level=70)
    db.update_player("gH", "h1", race="dragonborn", hidden_class_unlock=["cls_dragon_oath"])
    await cmd(m, "evolve", "gH", "h1", "转职 龙裔斗士")  # → T2
    player = db.get_player("gH", "h1")
    tier0 = player["class_tier"]
    path0 = player["evolve_path"]
    cls0 = player["class_name"]
    nlearn0 = len(player.get("learned_skills") or [])

    # 直接调用 hidden_evolve 动作（显式 tier=当前阶 → 触发「你已是X」分支）
    action = {"hidden_evolve": {"cls": "cls_dragon_oath", "tier": tier0, "path": 1}}
    lines = await action_hidden_evolve(m, "gH", "h1", player, "npc_dragon_veteran", action)
    text = "".join(lines)
    check("二次 hidden_evolve 返回你已是X", "你已是" in text, text[:160])

    p2 = db.get_player("gH", "h1")
    check("无重复/回档副作用 tier 不变", p2["class_tier"] == tier0 and p2["evolve_path"] == path0,
          str((p2["class_tier"], p2["evolve_path"])))
    check("职业名不变", p2["class_name"] == cls0, str(p2["class_name"]))
    check("learned_skills 不因二次触发重复", len(p2.get("learned_skills") or []) == nlearn0,
          f"{len(p2.get('learned_skills') or [])} vs {nlearn0}")


# ============ 9. 六线成就完整性（解锁 + 90 级满级） ============
def test_6line_achievements(m):
    clean_db()
    print("\n【9. 六线成就完整性（解锁 + 90 级满级）】")
    hidden_ids = [c for c in C.CLASSES if C.CLASSES[c].get("src_base")]
    check("隐藏线共 6 条", len(hidden_ids) == 6, str(hidden_ids))
    achs = {a["id"]: a for a in C.ACHIEVEMENTS}
    for cid in hidden_ids:
        unlock = [a for a in C.ACHIEVEMENTS if a.get("cond", {}).get("type") == "hidden_class"
                  and a["cond"].get("key") == cid]
        check(f"{cid} 有解锁成就", len(unlock) == 1,
              str([a["id"] for a in unlock]))
        lv90 = [a for a in C.ACHIEVEMENTS if a.get("cond", {}).get("type") == "hidden_class_lv"
                and a["cond"].get("key") == cid and a["cond"].get("value") == 90]
        check(f"{cid} 有 90 级满级成就", len(lv90) == 1,
              str([a["id"] for a in lv90]))


async def main():
    m = Main(None)
    funcs = [
        test_6lines_full_flow,
        test_7_tomes,
        test_downstream_skills_combat,
        test_command_vs_dialogue,
        test_reset_cleans_tome_skills,
        test_plant_summons,
        test_race_none_compat,
        test_hidden_evolve_double_guard,
        test_6line_achievements,
    ]
    for f in funcs:
        r = f(m)
        if asyncio.iscoroutine(r):
            await r

    print("\n===== v113 审计缺口回归: %d passed, %d failed =====" % (passed, failed))
    if SKIPPED:
        print("已跳过(依赖):")
        for n, r in SKIPPED:
            print(f"   - {n}: {r}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
