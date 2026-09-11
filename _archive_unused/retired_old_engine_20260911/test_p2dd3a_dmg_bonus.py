# -*- coding: utf-8 -*-
"""v181.P2D-D3a 技能被动伤害乘区族等价探针（test_p2dd3a_dmg_bonus.py）

验证挂点6 _skill_passive_dmg_bonus 的 3 个 proc（arcane_resonance / element_origin /
element_sync）从 battle.py 内联 for 迁移到 passive_procs.py 注册表族
（dmg_mult_cond 扩展 mult_kind 分派 + 新族 flag_set_cond）后行为零变化
（OLD vs NEW 双实现差分）。

方法（方案 §7 OLD-vs-NEW 探针，仿 test_p2dd2a/test_p2dd2b）：
1. OLD = 迁移前 _skill_passive_dmg_bonus 原 3 段循环体逐字副本（51aa7e0）。
2. NEW = 现引擎 _skill_passive_dmg_bonus（→ run_proc_family dmg_mult_cond / flag_set_cond）。
3. 差分矩阵：
   - arcane_resonance：学/不学 奥术共鸣 × mech∈{arcane(奥术弹幕), fire_mark(织焰非奥术)} ×
     mult 0.15/缺字段
   - element_origin：学/不学 元素起源 × 目标三系印记 {0,0,0}/{1,1,1}/{2,2,2}/{2,3,1} ×
     layers 2/mult 0.20/缺字段 → 断言 passive_bonus 一致（三系印记 ≥2 且非空才乘）
   - element_sync：学/不学 元素同调 × element∈{fire(可挂印), none(非元素)} ×
     last_element ∈ {fire(同系), ice(异系), None} → 断言 _elem_sync_bonus 标记一致
     （副作用；置位后由挂印分支消费清零——这里只验证前置判定置位）
   - 连乘语义：学奥术共鸣+元素起源 同开、同系连发+印记齐 → passive_bonus 连乘一致
   - 多条目防御（element_origin/element_sync 只判首条；arcane_resonance 逐条连乘）
   - 注册表静态断言（PROC_FAMILIES/FAMILY_HANDLERS/计数 17 声明 8 族）
   - 零默认值：_ps 空 dict/缺字段 → 不触发

运行（与门禁同款 python）：
  python tests/test_p2dd3a_dmg_bonus.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player  # noqa: E402
from data.plugins.dragonfall.game import engine as EG  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import passive_procs as PP  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls_id, passives, hp=500):
    """构造战斗玩家 dict（学指定被动中文名；resources/stacks/buffs/enemy 手置用于边界场景）。"""
    pl = make_player(cls=cls_id, level=60)
    pl = db.get_player(pl.get("group_id", "g1"), pl.get("qq_id", "q1")) if pl.get("qq_id") else pl
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": 100},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {}, "buffs": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd}


def mk_battle(player, enemy=None):
    b = BT.Battle("monster", enemy or mk_enemy(), {}, player)
    b._focus.setdefault("resources", {})
    b._focus.setdefault("stacks", {})
    b._focus.setdefault("buffs", {})
    b._focus.setdefault("eff", {})
    b.enemy.setdefault("element_marks", {})
    b.enemy.setdefault("buffs", {})
    # _skill_passive_dmg_bonus 尾部（斩杀/血魔法段）读技能管线实例属性——探针直呼挂点，
    # 补齐真实 _actor_skill 管线在此前设置的默认值（行为等价：血魔法未触发 0.30）
    b._hp_cost_bonus = getattr(b, "_hp_cost_bonus", 0.0)
    return b


def run_hook(b, mech="arcane", kind="魔法", element="fire", info=None):
    """跑 NEW 引擎 _skill_passive_dmg_bonus 挂点（st/est 空字典——3 段不依赖面板值）。
    返回 (passive_bonus, _procs)——挂点返回 4 元组 (pb, execute_tag, element, _procs)。"""
    st = {}
    est = {}
    info = dict(info or {})
    info.setdefault("element", element)
    pb, _tag, _el, _pr = b._skill_passive_dmg_bonus(st, est, b._focus, info, mech, kind)
    return pb, _pr


# ============================================================
# OLD：迁移前 _skill_passive_dmg_bonus 原 3 段循环体逐字副本（51aa7e0）
# ============================================================
def OLD_3procs(b, mech="arcane", kind="魔法", element="fire", info=None):
    """OLD 挂点6 3 段（奥术共鸣/元素起源/元素同调）——迁移前 6962-6989 逐字副本。
    返回 (passive_bonus, _elem_sync_bonus)。前置公共段（pierce/fire_bonus/element_dmg 等）
    未学则不触发，本探针只测 3 proc 学/不学 → 与 NEW 公共段等价（同一引擎前置段）。"""
    _pm = b._passive_map(b._focus)
    _procs = _pm["proc"]
    passive_bonus = 1.0
    info = dict(info or {})
    element = info.get("element", element)  # info 显式 element 优先；缺省回落参数 element
    for _pn, _ps in _procs.get("arcane_resonance", []):
        if mech in ("arcane",):  # MECH_PROC_GROUPS.arcane_dmg 快照（51aa7e0 表值）
            passive_bonus *= (1 + float(_ps.get("mult", 0.0) or 0.0))
    for _pn, _ps in _procs.get("element_origin", []):
        try:
            _mk_origin = b._elem_marks()
            if _mk_origin and all(int(_mk_origin.get(_ek, 0) or 0) >= int(_ps.get("layers", 0) or 0)
                                  for _ek in ("fire", "ice", "thunder")):
                passive_bonus *= (1 + float(_ps.get("mult", 0.0) or 0.0))
        except Exception:
            pass
        break
    _sync = False
    for _pn, _ps in _procs.get("element_sync", []):
        if element and EG.ELEMENT_MARKS.get(element):
            try:
                if b._p_last_element() == element:
                    _sync = True
            except Exception:
                pass
        break
    return passive_bonus, _sync


def test_arcane_resonance():
    print("\n== 1. arcane_resonance 奥术共鸣（mech 口径）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_fa_shi", ["奥术共鸣"] if learned else [])
        for mech_tag, mech in (("奥术arcane", "arcane"), ("非奥术fire_mark", "fire_mark"),
                               ("无mech", "")):
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            r_old, _ = OLD_3procs(b_old, mech=mech)
            pb_new, _ = run_hook(b_new, mech=mech)
            r_new = pb_new
            check(f"学={learned} {mech_tag}: passive_bonus {r_old}=={r_new}",
                  abs(r_old - r_new) < 1e-9, f"{r_old} vs {r_new}")
        # 缺字段（_ps 无 mult）→ 不触发（零默认值）
        if learned:
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            for b in (b_old, b_new):
                pm = b._passive_map(b._focus)
                pm["proc"]["arcane_resonance"] = [("奥术共鸣", {"proc": "arcane_resonance"})]
                b._passive_map = lambda pl, _pm=pm: _pm
            r_old, _ = OLD_3procs(b_old, mech="arcane")
            pb_new, _ = run_hook(b_new, mech="arcane")
            check("缺 mult 字段 → 不触发（1.0）", abs(r_old - 1.0) < 1e-9
                  and abs(pb_new - 1.0) < 1e-9, f"{r_old} vs {pb_new}")
    # 未学（learned=False）时 mk_player 无 _proc_pm 注入——OLD/NEW 空跑一致已在循环覆盖；
    # 上面 learned 分支结束——下方独立补"学到但缺字段"覆盖（零默认值铁律需真被动在场）


def test_element_origin():
    print("\n== 2. element_origin 元素起源（三系印记）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_fa_shi", ["元素起源"] if learned else [])
        for marks_tag, marks in (("全0", {"fire": 0, "ice": 0, "thunder": 0}),
                                 ("全1", {"fire": 1, "ice": 1, "thunder": 1}),
                                 ("全2", {"fire": 2, "ice": 2, "thunder": 2}),
                                 ("2,3,1", {"fire": 2, "ice": 3, "thunder": 1}),
                                 ("空dict", {})):
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            for b in (b_old, b_new):
                b.enemy["element_marks"] = dict(marks)
            r_old, _ = OLD_3procs(b_old)
            pb_new, _ = run_hook(b_new)
            check(f"学={learned} 印记{marks_tag}: {r_old}=={pb_new}",
                  abs(r_old - pb_new) < 1e-9, f"{r_old} vs {pb_new}")
        # 缺字段（_ps 无 layers/mult）→ 不触发（零默认值）
        if learned:
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            for b in (b_old, b_new):
                b.enemy["element_marks"] = {"fire": 2, "ice": 2, "thunder": 2}
                pm = b._passive_map(b._focus)
                pm["proc"]["element_origin"] = [("元素起源", {"proc": "element_origin"})]
                b._passive_map = lambda pl, _pm=pm: _pm
            r_old, _ = OLD_3procs(b_old)
            pb_new, _ = run_hook(b_new)
            check("缺 layers/mult 字段 → 不触发（1.0）", abs(r_old - 1.0) < 1e-9
                  and abs(pb_new - 1.0) < 1e-9, f"{r_old} vs {pb_new}")
    # learned=False 空跑已在循环覆盖——下方独立补"学到但缺字段"（独立于 learned 循环）


def test_element_sync():
    print("\n== 3. element_sync 元素同调（置 _elem_sync_bonus 标记）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_fa_shi", ["元素同调"] if learned else [])
        for el_tag, element in (("火系fire", "fire"), ("非元素none", "none"), ("无键''", "")):
            for last_tag, last in (("同系fire", "fire"), ("异系ice", "ice"), ("无last", None)):
                b_old = mk_battle(dict(p))
                b_new = mk_battle(dict(p))
                if last is not None:
                    b_old._focus["last_element"] = last
                    b_new._focus["last_element"] = last
                # OLD：本地 _sync 模拟（不真置 battle 属性，避免污染）——读语义一致
                _, _sync_old = OLD_3procs(b_old, element=element)
                # NEW：真置位 → 读回 battle 标记（与挂印分支消费同源）
                pb_new, _ = run_hook(b_new, element=element)
                _sync_new = bool(getattr(b_new, "_elem_sync_bonus", False))
                expect = learned and bool(element and EG.ELEMENT_MARKS.get(element)) and element == last
                check(f"学={learned} {el_tag} {last_tag}: 置位 {_sync_old}=={_sync_new} (期望 {expect})",
                      _sync_old == _sync_new == expect,
                      f"OLD {_sync_old} NEW {_sync_new} expect {expect}")


def test_combined_and_multi():
    print("\n== 4. 连乘语义（奥术共鸣+元素起源 同开 / 元素同调）+ 多条目防御 ==")
    # 4a. 连乘：奥术系 + 三系印记齐 → 1.0 × 1.15 × 1.20 = 1.38（同开）
    p = mk_player("cls_fa_shi", ["奥术共鸣", "元素起源"])
    b_old = mk_battle(dict(p))
    b_new = mk_battle(dict(p))
    for b in (b_old, b_new):
        b.enemy["element_marks"] = {"fire": 2, "ice": 2, "thunder": 2}
    r_old, _ = OLD_3procs(b_old, mech="arcane")
    pb_new, _ = run_hook(b_new, mech="arcane")
    check("连乘 1.15×1.20=1.38 OLD==NEW",
          abs(r_old - pb_new) < 1e-9 and abs(pb_new - 1.38) < 1e-9,
          f"{r_old} vs {pb_new}")
    # 4b. 非奥术系 + 印记齐 → 只乘 1.20（1.20）
    b_old2 = mk_battle(dict(p))
    b_new2 = mk_battle(dict(p))
    for b in (b_old2, b_new2):
        b.enemy["element_marks"] = {"fire": 2, "ice": 2, "thunder": 2}
    r_old2, _ = OLD_3procs(b_old2, mech="fire_mark")
    pb_new2, _ = run_hook(b_new2, mech="fire_mark")
    check("非奥术 + 印记齐 → 1.20 OLD==NEW",
          abs(r_old2 - pb_new2) < 1e-9 and abs(pb_new2 - 1.20) < 1e-9,
          f"{r_old2} vs {pb_new2}")
    # 4c. element_sync 双条目防御：首条（真同调）命中置位 break（第二条不判——OLD 同）
    p3 = mk_player("cls_fa_shi", ["元素同调"])
    b_old3 = mk_battle(dict(p3))
    b_new3 = mk_battle(dict(p3))
    for b in (b_old3, b_new3):
        b._focus["last_element"] = "fire"
        pm = b._passive_map(b._focus)
        pm["proc"]["element_sync"] = [
            ("元素同调", {"proc": "element_sync"}),
            ("测试第二条", {"proc": "element_sync"}),
        ]
        b._passive_map = lambda pl, _pm=pm: _pm
    _, sync_old = OLD_3procs(b_old3, element="fire")
    run_hook(b_new3, element="fire")
    sync_new = bool(getattr(b_new3, "_elem_sync_bonus", False))
    check("element_sync 双条目：首条即 break 置位一致",
          sync_old == sync_new is True, f"{sync_old} vs {sync_new}")
    # 4d. element_origin 双条目防御：首条不足也无条件 break → 不乘（第二条本可触发但不判）
    p4 = mk_player("cls_fa_shi", ["元素起源"])
    b_old4 = mk_battle(dict(p4))
    b_new4 = mk_battle(dict(p4))
    for b in (b_old4, b_new4):
        b.enemy["element_marks"] = {"fire": 2, "ice": 2, "thunder": 2}
        pm = b._passive_map(b._focus)
        pm["proc"]["element_origin"] = [
            ("元素起源", {"proc": "element_origin", "layers": 9, "mult": 0.20}),
            ("测试第二条", {"proc": "element_origin", "layers": 1, "mult": 0.50}),
        ]
        b._passive_map = lambda pl, _pm=pm: _pm
    r_old4, _ = OLD_3procs(b_old4)
    pb_new4, _ = run_hook(b_new4)
    check("element_origin 双条目：首条不足即 break → 1.0 OLD==NEW",
          abs(r_old4 - 1.0) < 1e-9 and abs(pb_new4 - 1.0) < 1e-9,
          f"{r_old4} vs {pb_new4}")
    # 4e. arcane_resonance 双条目：无 break 逐条连乘（两条 mult 0.15/0.10 → ×1.15×1.10）
    p5 = mk_player("cls_fa_shi", ["奥术共鸣"])
    b_old5 = mk_battle(dict(p5))
    b_new5 = mk_battle(dict(p5))
    for b in (b_old5, b_new5):
        pm = b._passive_map(b._focus)
        pm["proc"]["arcane_resonance"] = [
            ("奥术共鸣", {"proc": "arcane_resonance", "mult": 0.15}),
            ("测试第二条", {"proc": "arcane_resonance", "mult": 0.10}),
        ]
        b._passive_map = lambda pl, _pm=pm: _pm
    r_old5, _ = OLD_3procs(b_old5, mech="arcane")
    pb_new5, _ = run_hook(b_new5, mech="arcane")
    check("arcane_resonance 双条目：逐条连乘 ×1.15×1.10=1.265 OLD==NEW",
          abs(r_old5 - pb_new5) < 1e-9 and abs(pb_new5 - 1.265) < 1e-9,
          f"{r_old5} vs {pb_new5}")


def test_registry_static():
    print("\n== 5. 注册表静态（P2-D3a 3 proc 声明 + 8 族）+ 零默认值 ==")
    expect_map = {
        "arcane_resonance": "dmg_mult_cond",
        "element_origin": "dmg_mult_cond",
        "element_sync": "flag_set_cond",
    }
    for proc, fam in expect_map.items():
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              str(PP.PROC_FAMILIES.get(proc)))
    check("flag_set_cond 执行器已注册", "flag_set_cond" in PP.FAMILY_HANDLERS)
    check("PROC_FAMILIES 含 45 声明", len(PP.PROC_FAMILIES) == 45, str(sorted(PP.PROC_FAMILIES)))
    check("FAMILY_HANDLERS 共 17 族", len(PP.FAMILY_HANDLERS) == 17, str(list(PP.FAMILY_HANDLERS)))
    # P2-D4a：挂点10/11 6 proc 并入（tenacity→cc_break_cost 新族 + zhan_yi_full_reduce/
    # core_full/core_reduce/core_last_stand/core_overflow→dr_cond 新族）+ P2-D5b 3 proc
    # （poison_all_up→dot_mult_cond、poison_weaken→dot_weaken 新族、hunt_mark_cap→
    # dmg_mult_cond；soul_mark_cap cap 段同族）→ 声明 34 / 族 13
    # 零默认值：_ps 空 / 缺字段 → 不触发
    for kind in ("arcane_mech", "element_marks"):
        ctx = {"player": {}, "ps": {}, "ps_name": "x", "mult_kind": kind, "mult": 1.0, "mech": "arcane"}
        out = PP.run_proc_family(None, ["arcane_resonance"], ctx)
        check(f"空 _ps mult_kind={kind} → 不触发 mult 不变", out == [] and ctx["mult"] == 1.0, str(out))
    ctx_sync = {"player": {}, "ps": {}, "ps_name": "x", "flag_kind": "elem_sync", "element": "fire"}
    out_sync = PP.run_proc_family(None, ["element_sync"], ctx_sync)
    check("flag_set_cond 缺 battle → 不触发", out_sync == [], str(out_sync))


def main():
    clean_db()
    test_arcane_resonance()
    test_element_origin()
    test_element_sync()
    test_combined_and_multi()
    test_registry_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()