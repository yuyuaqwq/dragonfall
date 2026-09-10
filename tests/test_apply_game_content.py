# -*- coding: utf-8 -*-
"""S7 单一装配入口验收（`game/content_rules/apply.py`）。

规格：docs/ENGINE_CONTENT_SPLIT_PLAN.md §6.6（apply_game_content 收敛）+ §7 S7。
本测试守住三条契约：

  A 接口      —— 入口存在、单参可调、返回原 actor、旧调用点清单可核对
  B 顺序契约  —— ①ensure → ②equip → ③mech → ④bar → ⑤cond → ⑥food（+ mech 内部 bar→cond 先跑）
  C 引擎装配  —— ensure_engine_configured() 幂等且等价旧 load_game_defaults()
  D 幂等      —— 同一 actor 连调 1 次 vs 2 次，序列化字节相同；零额外状态键
  E 新旧等价  —— 新入口 == 旧命令层「EP.apply_to_actor + CM.apply_class_mech」逐字节
  F 数值抽样  —— 装备上限词条 / 推条注入 / 条件乘区 / 食物 四类效果照旧落地

跑法：python tests/test_apply_game_content.py（exit=0 全绿）
"""
import json
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_apply_game_content.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from game.battle2 import config as _b2c
_b2c.load_game_defaults()
from game.battle2 import make_actor
from game import bootstrap as BST
from game import content as C
from game.content_rules import apply as APPLY
from game.services import battle2_bar_procs as BAR
from game.services import battle2_cond_procs as COND
from game.services import battle2_equip_proc as EP
from game.services import battle2_food_proc as FOOD
from game.services import class_mech_proc as CM
from game.data.battle2_rules import BAR_INJECT_FIELDS
from game.data.weapon_effect_data import WEAPON_EFFECT_DATA

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


def d(o):
    """稳定序列化（对拍用）。"""
    return json.dumps(o, sort_keys=True, default=str)


# ------------------------------------------------------------
# 夹具：从数据表动态取真实技能/装备（不硬编码游戏内容）
# ------------------------------------------------------------

def _skills_of(cid):
    t = C.PLAYER_SKILLS.get(cid) or {}
    return (t.get("skills") if isinstance(t, dict) and "skills" in t else t) or {}


def _pick(cid, pred, n=1):
    return [k for k, v in _skills_of(cid).items() if isinstance(v, dict) and pred(v)][:n]


def _bar_skills(cid):
    return _pick(cid, lambda v: any(v.get(f) for f in (BAR_INJECT_FIELDS or {})), 2)


def _cond_skills(cid):
    return _pick(cid, lambda v: isinstance(v.get("cond"), dict), 2)


def _weapon_key():
    for k, v in (WEAPON_EFFECT_DATA or {}).items():
        try:
            if EP.triggers_for_key(k):
                return k
        except Exception:
            continue
    return None


_WE_KEY = _weapon_key()
_BAR_SK = _bar_skills("cls_wu_seng")
_COND_SK = _cond_skills("cls_wu_seng")


def mk(cid, name, learned=(), uid="p", equipment=None, level=40):
    a = make_actor(uid=uid, name=name, side="player", kind="player",
                   human_controlled=True, class_name=cid, level=level,
                   hp=3000, max_hp=3000, mp=300, max_mp=300,
                   atk=80, matk=220, spd=12, crit=0.05,
                   skills=[], learned_skills=list(learned),
                   race=None, evolve_path=0, class_tier=0, attributes={},
                   **{"def": 40, "mdef": 60})
    if equipment:
        a["equipment"] = equipment
    return a


def _eq_affix(aid, slot="weapon", quality="purple", we=None):
    item = {"slot": slot, "quality": quality, "affixes": [aid], "stats": {}}
    if we:
        item["weapon_effect"] = we
    return {slot: item}


CASES = [
    ("武僧·推条+条件+上限词条", mk("cls_wu_seng", "武僧",
                              learned=_BAR_SK + _COND_SK, uid="p1",
                              equipment=_eq_affix("rage_forge", we=_WE_KEY))),
    ("牧师·cap 词条", mk("cls_mu_shi", "牧师", learned=_pick("cls_mu_shi", lambda v: True, 2),
                      uid="p2", equipment=_eq_affix("divine_radiance"))),
    ("诗人·旋律", mk("cls_shi_ren", "诗人", learned=_pick("cls_shi_ren", lambda v: v.get("mech"), 2),
                  uid="p3")),
    ("白板战士", mk("cls_zhan_shi", "战士", uid="p4")),
]


def apply_old(a):
    """旧命令层路径（commands/combat.py `_open_battle2` 逐字：播种 bonus → EP → CM）。"""
    try:
        a["bonus"] = {"panel": {}, "cap": {}, "cost": {}}
    except Exception:
        pass
    EP.apply_to_actor(a)
    CM.apply_class_mech(a)
    return a


# ============================================================
# A 接口
# ============================================================

def t_a():
    print("【A 接口】")
    check("A1 apply_game_content / ensure_engine_configured 可导入",
          callable(APPLY.apply_game_content) and callable(APPLY.ensure_engine_configured))
    check("A2 旧调用点清单非空（S9 收口核对锚）",
          len(APPLY.LEGACY_CALL_SITES) >= 5, repr(APPLY.LEGACY_CALL_SITES))
    a = mk("cls_zhan_shi", "甲", uid="pa")
    r = APPLY.apply_game_content(a)
    check("A3 单参可调（ctx 可选）且返回原 actor", r is a)
    check("A4 空 actor 直接返回（不抛）", APPLY.apply_game_content({}) == {}
          and APPLY.apply_game_content(None) is None)


# ============================================================
# B 顺序契约
# ============================================================

def _spy(rec, name, mod, attr):
    orig = getattr(mod, attr)

    def f(*a, **k):
        rec.append(name)
        return None
    setattr(mod, attr, f)
    return orig


def t_b():
    print("【B 顺序契约】")
    # B1/B2：五个入口全部 spy → 观测 apply.py 自身的调用序
    rec = []
    saved = [_spy(rec, "equip", EP, "apply_to_actor"),
             _spy(rec, "mech", CM, "apply_class_mech"),
             _spy(rec, "bar", BAR, "apply_bar_procs"),
             _spy(rec, "cond", COND, "apply_cond_procs"),
             _spy(rec, "food", FOOD, "install_food_fx")]
    try:
        APPLY.apply_game_content(mk("cls_zhan_shi", "甲", uid="pb1"))
        check("B1 顶层序 = equip→mech→bar→cond",
              rec == ["equip", "mech", "bar", "cond"], repr(rec))
        rec.clear()
        APPLY.apply_game_content(mk("cls_zhan_shi", "乙", uid="pb2"),
                                 ctx={"aids": ["__probe_aid__"], "logs": []})
        check("B2 传 aids → 末位追加 food", rec == ["equip", "mech", "bar", "cond", "food"], repr(rec))
        rec.clear()
        APPLY.apply_game_content(mk("cls_zhan_shi", "丙", uid="pb3"), ctx={"logs": []})
        check("B2b 不传 aids → 无 food", "food" not in rec, repr(rec))
        rec.clear()
        APPLY.apply_game_content({})
        check("B2c 空 actor → 零装配调用", rec == [], repr(rec))
    finally:
        for (mod, attr), fn in zip([(EP, "apply_to_actor"), (CM, "apply_class_mech"),
                                    (BAR, "apply_bar_procs"), (COND, "apply_cond_procs"),
                                    (FOOD, "install_food_fx")], saved):
            setattr(mod, attr, fn)

    # B3：ensure 先于第一次内容装配
    rec2 = []
    _spy(rec2, "ensure", BST, "load_engine_config")
    _spy(rec2, "equip", EP, "apply_to_actor")
    saved2 = [(BST, "load_engine_config"), (EP, "apply_to_actor")]
    # 上面 _spy 已换掉，恢复表在下面统一处理
    try:
        APPLY.apply_game_content(mk("cls_zhan_shi", "丁", uid="pb4"))
        check("B3 ensure_engine_configured 先于 equip", rec2[:2] == ["ensure", "equip"], repr(rec2))
    finally:
        for mod, attr in saved2:
            setattr(mod, attr, _ORIG_ATTRS[(mod, attr)])

    # B4：真实 CM + spy bar/cond → mech 内部 bar→cond 先跑，显式 ④⑤ 为幂等空转
    rec3 = []
    saved3 = [_spy(rec3, "bar", BAR, "apply_bar_procs"),
              _spy(rec3, "cond", COND, "apply_cond_procs")]
    try:
        APPLY.apply_game_content(mk("cls_wu_seng", "武僧", learned=_BAR_SK + _COND_SK, uid="pb5"))
        check("B4 全链观测序 = bar,cond,bar,cond（mech 内部链先跑；④⑤ 幂等空转）",
              rec3 == ["bar", "cond", "bar", "cond"], repr(rec3))
    finally:
        for (mod, attr), fn in zip([(BAR, "apply_bar_procs"), (COND, "apply_cond_procs")], saved3):
            setattr(mod, attr, fn)


# ============================================================
# C 引擎装配
# ============================================================

def t_c():
    print("【C 引擎配置装配】")
    ok = True
    try:
        APPLY.ensure_engine_configured()
        APPLY.ensure_engine_configured()
    except Exception as e:
        ok = False
        check("C1 ensure_engine_configured 连调 2 次无异常", False, repr(e))
    if ok:
        check("C1 ensure_engine_configured 幂等（连调 2 次）", True)
    rec = []
    _spy(rec, "ensure", BST, "load_engine_config")
    try:
        APPLY.ensure_engine_configured()
        check("C2 ensure 委托 game.bootstrap.load_engine_config（= 旧 load_game_defaults 实体）",
              rec == ["ensure"], repr(rec))
    finally:
        setattr(BST, "load_engine_config", _ORIG_ATTRS[(BST, "load_engine_config")])
    r = _b2c.get_effect_rules() or {}
    a = _b2c.get_effect_actions() or {}
    check("C3 规则表已装载（EFFECT_RULES/EFFECT_ACTIONS 非空）",
          bool(r) and bool(a), f"rules={len(r)} actions={len(a)}")


# ============================================================
# D 幂等 + 零状态副作用
# ============================================================

def t_d():
    print("【D 幂等 / 状态副作用（已知且显式测试）】")
    for label, base in CASES:
        a1 = json.loads(d(base))
        a2 = json.loads(d(base))
        APPLY.apply_game_content(a1)
        APPLY.apply_game_content(a2)
        APPLY.apply_game_content(a2)
        check(f"D1 {label}：1x == 2x", d(a1) == d(a2),
              f"len {len(d(a1))} vs {len(d(a2))}")
    a = mk("cls_wu_seng", "武僧", learned=_BAR_SK + _COND_SK, uid="pd1",
           equipment=_eq_affix("rage_forge", we=_WE_KEY))
    base_keys = set(a.keys())
    APPLY.apply_game_content(a)
    added = set(a.keys()) - base_keys
    allowed = {"bonus", "triggers", "effects", "food_effects", APPLY._MARK}
    check("D2 只新增已知装配容器键 + 声明的幂等标记",
          added <= allowed and APPLY._MARK in added,
          f"added={sorted(added)}")
    # D3：已知副作用——标记随 to_state 落档（显式断言，不做隐藏）
    B2 = __import__("game.battle2", fromlist=["Battle"]).Battle
    foe = mk("cls_zhan_shi", "怪", uid="pd9")
    foe["side"] = "enemy"
    st = B2("monster", sides={"player": [a], "enemy": [foe]}).to_state()
    check("D3 【已知副作用】幂等标记随 serialize.to_state 落进战斗存档",
          APPLY._MARK in json.dumps(st, default=str))
    # D4：单步异常不阻断后续（容错铁律，与命令层逐字一致）+ 记入 LAST_ERRORS
    bad = mk("cls_wu_seng", "武僧", learned=_BAR_SK + _COND_SK, uid="pd4")
    orig = BAR.apply_bar_procs
    BAR.apply_bar_procs = lambda *x, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        APPLY.apply_game_content(bad)
    finally:
        BAR.apply_bar_procs = orig
    check("D4 单步异常不上抛、后续步照跑、仍落标记（容错铁律）",
          APPLY._MARK in bad and any(s == "bar" for s, _ in APPLY.LAST_ERRORS),
          f"errors={APPLY.LAST_ERRORS}")
    check("D4b 失败步记入 LAST_ERRORS（排障；不写 actor）",
          all(s not in bad for s, _ in APPLY.LAST_ERRORS) and len(APPLY.LAST_ERRORS) >= 1,
          f"errors={APPLY.LAST_ERRORS}")


# ============================================================
# E 新旧等价
# ============================================================

def t_e():
    print("【E 新旧等价（旧命令层并列调用 vs 新入口）】")
    for i, (label, base) in enumerate(CASES, 1):
        old = json.loads(d(base))
        new = json.loads(d(base))
        apply_old(old)
        APPLY.apply_game_content(new)
        # 唯一允许的差异 = 幂等标记键（新入口独有；见模块 docstring）
        marker = APPLY._MARK
        new_cmp = {k: v for k, v in new.items() if k != marker}
        diff_keys = set(new) - set(old)
        same = d(old) == d(new_cmp)
        check(f"E{i} {label}：除幂等标记外逐字节相同", same,
              "" if same else f"len {len(d(old))} vs {len(d(new_cmp))}")
        check(f"E{i}b {label}：差异键集合 == {{'{marker}'}}",
              diff_keys == {marker}, f"diff={sorted(diff_keys)}")


# ============================================================
# F 数值抽样（装配效果照旧落地）
# ============================================================

def _triggers(a, ev):
    return ((a or {}).get("triggers") or {}).get(ev) or []


def t_f():
    print("【F 数值抽样】")
    a = mk("cls_wu_seng", "武僧", learned=_BAR_SK + _COND_SK, uid="pf1",
           equipment=_eq_affix("rage_forge", we=_WE_KEY))
    APPLY.apply_game_content(a)
    cap = ((a.get("bonus") or {}).get("cap") or {})
    check("F1 rage_forge 上限词条 → bonus.cap.rage == 2", int(cap.get("rage", 0)) == 2, repr(cap))
    bar_hits = [e for e in _triggers(a, "skill_hit")
                if isinstance(e, dict) and e.get("action") == "bar_gain"]
    check("F2 推条技能 → skill_hit 挂 bar_gain 注入", bool(bar_hits), repr(_triggers(a, "skill_hit"))[:160])
    cond_hits = [e for e in _triggers(a, "dmg_calc")
                 if isinstance(e, dict) and e.get("action") == "skill_cond_mult"]
    check("F3 条件技能 → dmg_calc 挂 skill_cond_mult", bool(cond_hits), repr(_triggers(a, "dmg_calc"))[:160])
    if _WE_KEY:
        check("F4 武器特效入装配（weapon_effect → triggers 非空）",
              all(_triggers(a, e) for e in EP.weapon_triggers(a)), f"key={_WE_KEY}")
    else:
        check("F4 武器特效入装配（本库无可用 key，跳过）", True)

    # 食物：仅当 ctx 传 aids
    from game.data.food_effect_data import FOOD_EFFECT_PARAMS
    aid = None
    for k in (FOOD_EFFECT_PARAMS or {}):
        try:
            if FOOD.food_trigger_decls(k) or FOOD.food_period_decl(k):
                aid = k
                break
        except Exception:
            continue
    if aid:
        a2 = mk("cls_zhan_shi", "战士", uid="pf2")
        APPLY.apply_game_content(a2, ctx={"aids": [aid], "logs": []})
        n1 = sum(len(v) for v in (a2.get("triggers") or {}).values())
        APPLY.apply_game_content(a2, ctx={"aids": [aid], "logs": []})
        n2 = sum(len(v) for v in (a2.get("triggers") or {}).values())
        check(f"F5 食物 aid={aid} 装配 + 重调幂等", n1 > 0 and n1 == n2, f"{n1} vs {n2}")
    else:
        check("F5 食物（本库无可用 aid，跳过）", True)
    a3 = mk("cls_zhan_shi", "战士", uid="pf3")
    APPLY.apply_game_content(a3)
    check("F6 不传 aids → 食物容器为空（不乱挂）",
          not (a3.get("triggers") or {}).get("food"), repr(a3.get("food_effects")))


# ============================================================
# 主流程
# ============================================================

def _snapshot_orig():
    return {(m, a): getattr(m, a) for m, a in
            [(EP, "apply_to_actor"), (CM, "apply_class_mech"),
             (BAR, "apply_bar_procs"), (COND, "apply_cond_procs"),
             (FOOD, "install_food_fx"), (BST, "load_engine_config")]}


_ORIG_ATTRS = _snapshot_orig()


def main():
    print("=" * 66)
    print("S7 单一装配入口 apply_game_content —— 验收")
    print("=" * 66)
    t_a()
    t_b()
    t_c()
    t_d()
    t_e()
    t_f()
    print()
    print("=" * 66)
    print(f"通过 {PASS}，失败 {FAIL}")
    if FAILURES:
        for f in FAILURES:
            print(f"  ❌ {f}")
    print("=" * 66)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
