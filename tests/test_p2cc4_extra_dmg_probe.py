# -*- coding: utf-8 -*-
"""v181.P2C-C4 直伤追击族 proc_extra_dmg 迁移探针（OLD vs NEW 差分）。

策略（方案 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc8_passive_stack_probe.py）：
- OLD = WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc，模拟未族化）
- NEW = proc() 族分发（key→_WE_EXEC_KEYS→proc_extra_dmg→_we_exec_extra_dmg）
固定 random.seed；断言 logs / ctx / state（hp/mp/shields/buffs/stacks/eff/debuffs/e_buffs）逐字段相等。

场景（11 key × 触发事件/双态 + 多态）：
- afterglow_splash / spellblade_echo / annihilation_echo（skill_hit 奥术溅射；无 chance 直接触发 / chance 双态）
- wind_split（hit 物理追加 chance）
- phantom_barrage（hit 破防追加：chance 触发 / guarantee 保底 / 无视 50% 防御）
- endless_blade（skill_hit：暴击追击 / 非暴不触发 / used 后不再触发）
- hunter_open / siren_fang（hit 每 N 次真伤：n 到 count 触发清零 / n 未满累积）
- star_pierce（hit 每 4 次真伤：已损加成 + cap / 计数未满）
- soul_eater（hit 敌当前生命% 伤+回等量；敌低血 bonus cap atk）
- novice_lifesteal（hit：ctx.dmg 吸血 / ctx 无 dmg 用 atk 近似 / 玩家满血时 heal 0）
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS

EXTRA_KEYS = [
    "afterglow_splash", "spellblade_echo", "annihilation_echo",     # splash_magi 3
    "wind_split", "phantom_barrage", "endless_blade",                # extra_phys 3
    "hunter_open", "siren_fang", "star_pierce",                      # true_dmg_nth 3
    "soul_eater", "novice_lifesteal",                                 # curhp/lifesteal 2
]
EVENTS = {
    "afterglow_splash": "skill_hit", "spellblade_echo": "skill_hit",
    "annihilation_echo": "skill_hit", "wind_split": "hit",
    "phantom_barrage": "hit", "endless_blade": "skill_hit",
    "hunter_open": "hit", "siren_fang": "hit", "star_pierce": "hit",
    "soul_eater": "hit", "novice_lifesteal": "hit",
}

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, hp=None):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    p = {"hp": hp if hp is not None else 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
         "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
         "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
         "level": level, "class_name": "战士", "qq_id": "t1"}
    return p

def mk_enemy(hp=100000, max_hp=None, boss=False, **kw):
    mh = hp if max_hp is None else max_hp
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": mh,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    if boss:
        e["role"] = "boss"
    e.update(kw)
    return e

def state_slices(b, p):
    out = {}
    for k in ("hp", "mp", "max_hp", "max_mp"):
        out[f"p.{k}"] = p.get(k)
    for bag, name in ((p.get("buffs"), "p.buffs"), (p.get("stacks"), "p.stacks"),
                      (p.get("eff"), "p.eff"), (p.get("shields"), "p.shields")):
        if bag:
            out[name] = copy.deepcopy(bag)
    e = b.enemy or {}
    for k in ("hp", "max_hp"):
        out[f"e.{k}"] = e.get(k)
    for bag, name in ((e.get("buffs"), "e.buffs"), (e.get("debuffs"), "e.debuffs"),
                      (e.get("e_buffs"), "e.e_buffs"), (b.e_buffs, "b.e_buffs"),
                      (b._p_stacks() if hasattr(b, "_p_stacks") else None, "b.p_stacks"),
                      (b._p_eff() if hasattr(b, "_p_eff") else None, "b.p_eff")):
        if bag:
            out[name] = copy.deepcopy(bag)
    return out

def run_pair(key, maker, n_runs=40):
    """同 seed 跑 OLD（直调旧 handler）与 NEW（proc 族分发），逐字段对比。
    maker：{boss, enemy_hp, enemy_max_hp, pre_stacks, pre_eff, player_hp, ctx_extra}"""
    ev = EVENTS[key]
    mism = []
    for i in range(n_runs):
        seed = 6000 + i * 17 + (1 if maker.get("boss") else 0)
        # ---- OLD ----
        random.seed(seed)
        p_old = mk_player([key], hp=maker.get("player_hp"))
        if maker.get("pre_stacks"):
            p_old.setdefault("stacks", {}).update(maker["pre_stacks"])
        if maker.get("pre_eff"):
            p_old.setdefault("eff", {}).update(maker["pre_eff"])
        b_old = BT.Battle("monster", mk_enemy(hp=maker.get("enemy_hp", 100000),
                                              max_hp=maker.get("enemy_max_hp"),
                                              boss=maker.get("boss", False)), player=p_old)
        ctx_old = {"dmg": 200, "is_crit": False}
        if maker.get("ctx_extra"):
            ctx_old.update(maker["ctx_extra"])
        logs_old = []
        handler = WEAPON_EFFECTS[key][ev]
        handler(b_old, p_old, ctx_old, logs_old)
        # ---- NEW ----
        random.seed(seed)
        p_new = mk_player([key], hp=maker.get("player_hp"))
        if maker.get("pre_stacks"):
            p_new.setdefault("stacks", {}).update(maker["pre_stacks"])
        if maker.get("pre_eff"):
            p_new.setdefault("eff", {}).update(maker["pre_eff"])
        b_new = BT.Battle("monster", mk_enemy(hp=maker.get("enemy_hp", 100000),
                                              max_hp=maker.get("enemy_max_hp"),
                                              boss=maker.get("boss", False)), player=p_new)
        ctx_new = {"dmg": 200, "is_crit": False}
        if maker.get("ctx_extra"):
            ctx_new.update(maker["ctx_extra"])
        logs_new = []
        we_proc(b_new, p_new, ev, ctx_new, logs_new)
        # ---- compare ----
        if logs_old != logs_new:
            mism.append(f"run{i}: logs OLD={logs_old} NEW={logs_new}")
            continue
        so = state_slices(b_old, p_old)
        sn = state_slices(b_new, p_new)
        for k in set(so) | set(sn):
            if so.get(k) != sn.get(k):
                mism.append(f"run{i}: state[{k}] OLD={so.get(k)} NEW={sn.get(k)}")
        if ctx_old != ctx_new:
            mism.append(f"run{i}: ctx OLD={ctx_old} NEW={ctx_new}")
        if mism:
            break
    return mism

def test_splash_magi():
    print("【1. splash_magi 3 key（skill_hit 奥术溅射）】")
    # spellblade_echo：无 chance 恒触发（atk 全量跑）
    mism = run_pair("spellblade_echo", {})
    check("spellblade_echo skill_hit OLD==NEW", not mism, str(mism[:2]))
    # chance 双态：afterglow 0.30 / annihilation 0.35（boss 态也跑）
    for key in ("afterglow_splash", "annihilation_echo"):
        for boss in (False, True):
            mism = run_pair(key, {"boss": boss})
            check(f"{key} skill_hit OLD==NEW (boss={boss})", not mism, str(mism[:2]))

def test_wind_split():
    print("【2. wind_split（hit 物理追加 chance 0.25）】")
    for boss in (False, True):
        mism = run_pair("wind_split", {"boss": boss})
        check(f"wind_split hit OLD==NEW (boss={boss})", not mism, str(mism[:2]))

def test_phantom_barrage():
    print("【3. phantom_barrage（hit 破防追加+保底）】")
    # chance 触发 / 保底计数（第 5 击必触发）：预置 phantom_cnt 0~4 各跑
    for n in (0, 1, 4):
        mism = run_pair("phantom_barrage", {"pre_stacks": {"phantom_cnt": n}})
        check(f"phantom_barrage hit OLD==NEW (cnt={n})", not mism, str(mism[:2]))
    # 目标 def 高 → 破防伤害差异也要一致（enemy def 300 重跑）
    mism = run_pair("phantom_barrage", {"enemy_max_hp": 100000,
                                        "pre_stacks": {"phantom_cnt": 4}})
    check("phantom_barrage 高防 OLD==NEW", not mism, str(mism[:2]))

def test_endless_blade():
    print("【4. endless_blade（skill_hit 暴击追击，每刻限 1）】")
    # 暴击触发
    mism = run_pair("endless_blade", {"ctx_extra": {"is_crit": True}})
    check("endless_blade skill_hit 暴击 OLD==NEW", not mism, str(mism[:2]))
    # 非暴不触发
    mism = run_pair("endless_blade", {"ctx_extra": {"is_crit": False}})
    check("endless_blade 非暴 OLD==NEW", not mism, str(mism[:2]))
    # used 后不再触发
    mism = run_pair("endless_blade", {"ctx_extra": {"is_crit": True},
                                      "pre_eff": {"we_blade_used": True}})
    check("endless_blade used 后 OLD==NEW", not mism, str(mism[:2]))

def test_true_dmg_nth():
    print("【5. true_dmg_nth 3 key（hit 每 N 次真伤）】")
    for key, skey in (("hunter_open", "hunter_cnt"), ("siren_fang", "siren_cnt"),
                      ("star_pierce", "star_cnt")):
        for n in (0, 1):
            mism = run_pair(key, {"pre_stacks": {skey: n}})
            check(f"{key} hit OLD==NEW (cnt={n})", not mism, str(mism[:2]))
        # 已满计数 → 触发并清零（含 star_pierce 已损加成）
        cnt = 3 if key != "star_pierce" else 4
        mism = run_pair(key, {"pre_stacks": {skey: cnt - 1},
                              "enemy_hp": 7000, "enemy_max_hp": 10000})
        check(f"{key} hit 满计数触发 OLD==NEW", not mism, str(mism[:2]))

def test_soul_eater():
    print("【6. soul_eater（hit 敌当前生命%伤+回等量）】")
    # 敌高血：cur_hp 2% → 2000（atk 2000 cap 大）
    mism = run_pair("soul_eater", {"ctx_extra": {"dmg": 200}})
    check("soul_eater 高血 OLD==NEW", not mism, str(mism[:2]))
    # 敌低血：2% 小于 atk cap（cap=atk）
    mism = run_pair("soul_eater", {"enemy_hp": 3000, "enemy_max_hp": 100000})
    check("soul_eater 低血 OLD==NEW", not mism, str(mism[:2]))

def test_novice_lifesteal():
    print("【7. novice_lifesteal（hit 吸血 heal_pct 0.05）】")
    # ctx.dmg 200 → heal 10（玩家掉血时）
    mism = run_pair("novice_lifesteal", {"player_hp": 5000,
                                         "ctx_extra": {"dmg": 200}})
    check("novice_lifesteal ctx.dmg OLD==NEW", not mism, str(mism[:2]))
    # ctx 无 dmg → atk 近似（dmg=atk，heal = atk×0.05）
    mism = run_pair("novice_lifesteal", {"player_hp": 5000, "ctx_extra": {"dmg": 0}})
    check("novice_lifesteal atk 近似 OLD==NEW", not mism, str(mism[:2]))
    # 玩家满血 heal 0（_heal_player 无回复）
    mism = run_pair("novice_lifesteal", {"ctx_extra": {"dmg": 200}})
    check("novice_lifesteal 满血 OLD==NEW", not mism, str(mism[:2]))

def test_migrated_route():
    print("【8. 族路由】")
    for k in EXTRA_KEYS:
        check(f"{k} → proc_extra_dmg", _we_family(k) == "proc_extra_dmg"
              and _WE_EXEC_KEYS.get(k) == "proc_extra_dmg",
              f"fam={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")

if __name__ == "__main__":
    test_splash_magi()
    test_wind_split()
    test_phantom_barrage()
    test_endless_blade()
    test_true_dmg_nth()
    test_soul_eater()
    test_novice_lifesteal()
    test_migrated_route()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
