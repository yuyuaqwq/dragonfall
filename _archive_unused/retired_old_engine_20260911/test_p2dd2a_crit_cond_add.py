# -*- coding: utf-8 -*-
"""v181.P2D-D2a 条件暴击族 crit_cond_add 等价探针（test_p2dd2a_crit_cond_add.py）

验证挂点1 _passive_crit_bonus 的 4 个条件暴击 proc（zhan_yi_crit / arcane_wisdom /
focus_surplus_crit / element_core）从 battle.py 内联 for 迁移到 passive_procs.py
注册表族 crit_cond_add 后行为零变化（OLD vs NEW 双实现差分）。

方法（方案 §7 OLD-vs-NEW 探针）：
1. OLD = 迁移前 _passive_crit_bonus 原逻辑副本（4 for 循环逐字复刻 4c4ffa7）。
2. NEW = 现引擎 _passive_crit_bonus（→ run_proc_family crit_cond_add）。
3. 差分矩阵：每 proc 学/不学 × 边界状态（战意 7/8、奥术 4/5、专注 39/40、
   元素印记 2/3）+ info 缺省/current 回落 + 副作用标记 + 双条目防御。
   断言返回 bonus 一致 + eff 标记一致。

运行（与门禁同款 python）：
  python tests/test_p2dd2a_crit_cond_add.py
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
    """构造战斗玩家 dict（学指定被动中文名；stacks/resources/enemy 手置用于边界场景）。"""
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": 100},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd}


def mk_battle(player, enemy=None):
    b = BT.Battle("monster", enemy or mk_enemy(), {}, player)
    b._focus.setdefault("resources", {})
    b._focus.setdefault("stacks", {})
    b._focus.setdefault("eff", {})
    b.enemy.setdefault("element_marks", {})
    return b


# ============================================================
# OLD：迁移前 _passive_crit_bonus 原逻辑逐字副本（4c4ffa7）
# ============================================================
def OLD_crit_bonus(b, player, info=None):
    bonus = 0.0
    try:
        pm = b._proc_pm(player)
        # 狂热
        for _pn, _ps in pm["proc"].get("zhan_yi_crit", []):
            if b._zhan_yi_n() >= int(_ps.get("stacks", 0) or 0):
                bonus += float(_ps.get("add", 0.0) or 0.0)
                break
        # 真知（守线·奥秘法师充能条 / 攻线 arcane 叠层）
        for _pn, _ps in pm["proc"].get("arcane_wisdom", []):
            _full = False
            try:
                if b._p_res().get("element_charge") is not None:
                    _full = b._elem_charge() >= b._res_max(player, "element")
                else:
                    _full = int((b._p_stacks() or {}).get("arcane", 0) or 0) >= int(_ps.get("stacks", 0) or 0)
            except Exception:
                _full = False
            if _full:
                bonus += float(_ps.get("add", 0.0) or 0.0)
                break
        # 疾风之心（专注结余 = 精力当前值，≥40 时本技能暴击 +20% 一次性）
        if info is not None:
            for _pn, _ps in pm["proc"].get("focus_surplus_crit", []):
                _pres = getattr(b, "_pre_cost_res", None)
                _eng = int(_pres.get("energy", 0) or 0) if isinstance(_pres, dict) \
                    else int(b._p_res().get("energy", 0) or 0)
                if _eng >= int(_ps.get("surplus", 0) or 0):
                    bonus += float(_ps.get("add", 0.0) or 0.0)
                    b._p_eff()["focus_surplus_proc"] = True
                    break
        # 元素之核（单系印记满 _ps.layers（默认 3）时该系结算暴击 +20%）
        if info is not None:
            for _pn, _ps in pm["proc"].get("element_core", []):
                _el = info.get("element", "")
                if _el == "current":
                    _el = b._p_res().get("element", "fire")
                if _el:
                    _mk = b._elem_marks()
                    if int(_mk.get(_el, 0) or 0) >= int(_ps.get("layers", 0) or 0):
                        bonus += float(_ps.get("add", 0.0) or 0.0)
                break
    except Exception:
        pass
    return bonus


def diff_bonus(name, cls, skill, setup_fn, info_list):
    """OLD vs NEW 差分：同一玩家态跑 OLD 副本与现引擎挂点，比 bonus + eff 标记。"""
    for learned in (False, True):
        p = mk_player(cls, [skill] if learned else [])
        for info in info_list:
            for tag, setup in setup_fn.items():
                b_old = mk_battle(dict(p))
                b_new = mk_battle(dict(p))
                setup(b_old)
                setup(b_new)
                r_old = OLD_crit_bonus(b_old, b_old._focus, info)
                r_new = b_new._passive_crit_bonus(b_new._focus, info=info)
                e_old = bool((b_old._focus.get("eff") or {}).get("focus_surplus_proc"))
                e_new = bool((b_new._focus.get("eff") or {}).get("focus_surplus_proc"))
                check(f"{name} 学={learned} {tag} info={'有' if info is not None else '无'}: "
                      f"bonus {r_old}=={r_new} eff {e_old}=={e_new}",
                      abs(r_old - r_new) < 1e-9 and e_old == e_new,
                      f"{r_old} vs {r_new} / {e_old} vs {e_new}")


# ============================================================
# 1. zhan_yi_crit（狂热：战意 ≥8 → +0.15；无 info 依赖）
# ============================================================
def test_zhan_yi_crit():
    print("\n== 1. zhan_yi_crit（战意 7/8 边界）OLD vs NEW ==")
    setups = {
        "战意0": lambda b: b._focus["stacks"].update({"zhan_yi": 0}),
        "战意7": lambda b: b._focus["stacks"].update({"zhan_yi": 7}),
        "战意8": lambda b: b._focus["stacks"].update({"zhan_yi": 8}),
        "战意10": lambda b: b._focus["stacks"].update({"zhan_yi": 10}),
    }
    diff_bonus("狂热", "cls_zhan_shi", "狂热", setups, [None, {"element": "fire"}])


# ============================================================
# 2. arcane_wisdom（真知：奥术充能满 5 / stacks.arcane ≥5 → +0.20；无 info 依赖）
# ============================================================
def test_arcane_wisdom():
    print("\n== 2. arcane_wisdom（充能 4/5 与满 5；攻线 arcane 叠层 4/5）OLD vs NEW ==")
    setups = {
        # 守线·奥秘法师：resources.element_charge 满条判（charge ≥ _res_max element=5）
        "charge0": lambda b: b._focus["resources"].update({"element_charge": 0}),
        "charge4": lambda b: b._focus["resources"].update({"element_charge": 4}),
        "charge5": lambda b: b._focus["resources"].update({"element_charge": 5}),
        # 攻线 arcane 叠层（无 element_charge 键）
        "arcane0": lambda b: b._focus["stacks"].update({"arcane": 0}),
        "arcane4": lambda b: b._focus["stacks"].update({"arcane": 4}),
        "arcane5": lambda b: b._focus["stacks"].update({"arcane": 5}),
    }
    diff_bonus("真知", "cls_fa_shi", "真知", setups, [None, {"element": "fire"}])


# ============================================================
# 3. focus_surplus_crit（疾风之心：精力快照 ≥40 → +0.20 + 置位 eff 标记；需 info）
# ============================================================
def test_focus_surplus_crit():
    print("\n== 3. focus_surplus_crit（精力快照 39/40 边界 + eff 副作用）OLD vs NEW ==")
    setups = {
        "快照39": lambda b: setattr(b, "_pre_cost_res", {"energy": 39}),
        "快照40": lambda b: setattr(b, "_pre_cost_res", {"energy": 40}),
        "快照60": lambda b: setattr(b, "_pre_cost_res", {"energy": 60}),
        # 快照缺失 → 回落当前 energy（直接调用非技能链场景）
        "无快照当前39": lambda b: b._focus["resources"].update({"energy": 39}),
        "无快照当前40": lambda b: b._focus["resources"].update({"energy": 40}),
    }
    # info 有（技能链）→ 触发路径
    diff_bonus("疾风之心", "cls_you_xia", "疾风之心", setups, [{"element": "fire"}])
    # info=None（直接调用）→ 原 `if info is not None` 守卫：整体不触发
    diff_bonus("疾风之心", "cls_you_xia", "疾风之心", setups, [None])


# ============================================================
# 4. element_core（元素之核：单系印记 ≥3 → +0.20；需 info；current 回落）
# ============================================================
def test_element_core():
    print("\n== 4. element_core（印记 2/3 边界 + current 回落 + el 空）OLD vs NEW ==")
    setups = {
        "火印0": lambda b: b.enemy["element_marks"].update({"fire": 0}),
        "火印2": lambda b: b.enemy["element_marks"].update({"fire": 2}),
        "火印3": lambda b: b.enemy["element_marks"].update({"fire": 3}),
        # element == "current" → 回落 _p_res()["element"]（默认 fire）
        "current火印3": lambda b: b.enemy["element_marks"].update({"fire": 3}),
        "冰印3火印0": lambda b: b.enemy["element_marks"].update({"ice": 3, "fire": 0}),
    }
    infos = [{"element": "fire"}, {"element": "current"},
             {"element": "ice"}, {"element": ""}]
    for info in infos:
        for tag, setup in setups.items():
            for learned in (False, True):
                p = mk_player("cls_fa_shi", ["元素之核"] if learned else [])
                b_old = mk_battle(dict(p))
                b_new = mk_battle(dict(p))
                setup(b_old)
                setup(b_new)
                if info.get("element") == "current":
                    b_old._focus["resources"]["element"] = "fire"
                    b_new._focus["resources"]["element"] = "fire"
                r_old = OLD_crit_bonus(b_old, b_old._focus, info)
                r_new = b_new._passive_crit_bonus(b_new._focus, info=info)
                check(f"元素之核 学={learned} {tag} el={info.get('element')!r}: "
                      f"bonus {r_old}=={r_new}",
                      abs(r_old - r_new) < 1e-9, f"{r_old} vs {r_new}")
    # info=None → 守卫不触发
    for learned in (False, True):
        p = mk_player("cls_fa_shi", ["元素之核"] if learned else [])
        b_old = mk_battle(dict(p))
        b_new = mk_battle(dict(p))
        b_old.enemy["element_marks"]["fire"] = 3
        b_new.enemy["element_marks"]["fire"] = 3
        r_old = OLD_crit_bonus(b_old, b_old._focus, None)
        r_new = b_new._passive_crit_bonus(b_new._focus, info=None)
        check(f"元素之核 学={learned} info=None → 0==0", abs(r_old - r_new) < 1e-9, f"{r_old} vs {r_new}")


# ============================================================
# 5. 注册表静态 + 多条目防御 + 零默认值
# ============================================================
def test_registry_and_multi():
    print("\n== 5. crit_cond_add 注册表 + 多条目 + 零默认值 ==")
    for proc in ("zhan_yi_crit", "arcane_wisdom", "focus_surplus_crit", "element_core"):
        check(f"{proc} → crit_cond_add", PP.PROC_FAMILIES.get(proc) == "crit_cond_add",
              str(PP.PROC_FAMILIES.get(proc)))
    check("crit_cond_add 执行器已注册", "crit_cond_add" in PP.FAMILY_HANDLERS)
    # 全批次并入后 FAMILY_HANDLERS 共 17 族
    check("FAMILY_HANDLERS 共 17 族", len(PP.FAMILY_HANDLERS) == 17, str(list(PP.FAMILY_HANDLERS)))
    # 零默认值：_ps 空 dict / 缺 add → 不触发（缺字段 = 无此行为）
    for kind in ("zhan_yi", "arcane", "focus", "element_mark"):
        ctx = {"player": {}, "info": {"element": "fire"}, "res_kind": kind,
               "ps": {}, "ps_name": "x", "crit_add": 0.0}
        out = PP.run_proc_family(None, ["zhan_yi_crit"], ctx)
        check(f"空 _ps res_kind={kind} → 不触发", out == [] and ctx["crit_add"] == 0.0, str(out))
    # 双条目防御（element_core 无条件 break：第二条不判——多条目下只判首条；OLD/NEW 同）
    p = mk_player("cls_fa_shi", ["元素之核"])
    b_old = mk_battle(dict(p))
    b_new = mk_battle(dict(p))
    for b in (b_old, b_new):
        pm = b._proc_pm(b._focus)
        pm["proc"]["element_core"] = [
            ("元素之核", {"proc": "element_core", "layers": 3, "add": 0.20}),
            ("测试第二条", {"proc": "element_core", "layers": 0, "add": 0.30}),
        ]
        b._proc_pm = lambda pl, _pm=pm: _pm
        b.enemy["element_marks"]["fire"] = 3
    r_old = OLD_crit_bonus(b_old, b_old._focus, {"element": "fire"})
    r_new = b_new._passive_crit_bonus(b_new._focus, info={"element": "fire"})
    # 首条命中 +0.20 后 break → 第二条不判（OLD 同）→ 0.20 非 0.50
    check("双条目：首条命中即 break（0.20 非 0.50）", abs(r_old - 0.20) < 1e-9 and abs(r_new - 0.20) < 1e-9,
          f"{r_old} vs {r_new}")
    # 首条印记不足也无条件 break → 0（第二条 layers=0 本可触发但不判）
    for b in (b_old, b_new):
        b.enemy["element_marks"]["fire"] = 0
    r_old = OLD_crit_bonus(b_old, b_old._focus, {"element": "fire"})
    r_new = b_new._passive_crit_bonus(b_new._focus, info={"element": "fire"})
    check("双条目：首条不足也无条件 break → 0==0", abs(r_old - 0.0) < 1e-9 and abs(r_new - 0.0) < 1e-9,
          f"{r_old} vs {r_new}")


def main():
    clean_db()
    test_zhan_yi_crit()
    test_arcane_wisdom()
    test_focus_surplus_crit()
    test_element_core()
    test_registry_and_multi()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()