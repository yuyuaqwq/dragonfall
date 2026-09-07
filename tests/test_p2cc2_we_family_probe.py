# -*- coding: utf-8 -*-
"""v181.P2C-C2 族执行器 OLD vs NEW 差分探针（proc_dot / proc_reflect / proc_heal amp 3 族 10 key）

策略（方案文档 §5.2 族级 OLD-NEW 差分探针）：同一 battle 场景分别跑
  - OLD = 直接调 WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc 分发，模拟未族化）
  - NEW = proc() 族分发（family 路由到族执行器）
断言 logs / ctx / state（hp/mp/shields/buffs/stacks/eff/debuffs/e_buffs）逐字段相等。
固定 random.seed —— 概率类（chance）同一 seed 下 OLD/NEW 判定一致。

构造场景：
- proc_dot 4 key：hit / skill_hit 事件，boss 与普通两态各跑（验证 dot_pct_boss 分支）
- proc_reflect 2 key：taken 事件（thorn 无条件 / retribution 概率）
- proc_heal amp 4 key：heal 事件（含 overflow 跳过 / 无 overflow 加成两态）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS
import _c10_old_we as _OLDWE
from game.core.weapon_effects import _we_family

DOT_KEYS = ["smith_blaze_wound", "rong_lu_yu_wen", "ember_burn", "blood_trace"]
DOT_EVENTS = {"smith_blaze_wound": "hit", "rong_lu_yu_wen": "hit", "ember_burn": "skill_hit", "blood_trace": "hit"}
REFLECT_KEYS = ["thorn_armor", "retribution_ring"]
HEAL_KEYS = ["vital_band", "holy_radiance_mail", "echo_band", "novice_regen_heal"]

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

def mk_player(effects=None, atk=100, matk=80, level=30):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": "战士", "qq_id": "t1"}

def mk_enemy(hp=100000, boss=False):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    if boss:
        e["role"] = "boss"
    return e

def snapshot(state_piece):
    """深拷贝状态片段（防引用污染）。"""
    import copy
    return copy.deepcopy(state_piece)

def state_slices(b, p):
    """采集对比用状态切片：battle 可观察副作用 + player 状态 + 敌方状态。"""
    out = {}
    # 玩家侧
    for k in ("hp", "mp", "max_hp", "max_mp"):
        out[f"p.{k}"] = p.get(k)
    for bag, name in ((p.get("buffs"), "p.buffs"), (p.get("stacks"), "p.stacks"),
                      (p.get("eff"), "p.eff"), (p.get("shields"), "p.shields")):
        if bag:
            out[name] = snapshot(bag)
    # 敌方侧
    e = b.enemy or {}
    for k in ("hp", "max_hp"):
        out[f"e.{k}"] = e.get(k)
    for bag, name in ((e.get("buffs"), "e.buffs"), (e.get("debuffs"), "e.debuffs"),
                      (e.get("e_buffs"), "e.e_buffs"), (b.e_buffs, "b.e_buffs"),
                      (b._p_buffs_bag() if hasattr(b, "_p_buffs_bag") else None, "b.p_buffs"),
                      (b._p_shields_bag() if hasattr(b, "_p_shields_bag") else None, "b.p_shields"),
                      (b._p_eff() if hasattr(b, "_p_eff") else None, "b.p_eff"),
                      (b._p_stacks() if hasattr(b, "_p_stacks") else None, "b.p_stacks")):
        if bag:
            out[name] = snapshot(bag)
    return out

def run_pair(key, event, ctx_maker, n_runs=40, boss=False):
    """对同一 key 跑 OLD handler 与 NEW proc 族分发，逐次同 seed 对比。"""
    mism = []
    for i in range(n_runs):
        seed = 1000 + i * 7 + (1 if boss else 0)
        # ---- OLD ----
        random.seed(seed)
        p_old = mk_player([key])
        e_old = mk_enemy(boss=boss)
        b_old = BT.Battle("monster", e_old, player=p_old)
        ctx_old = ctx_maker()
        logs_old = []
        handler = _OLDWE.old_handler(key, event)
        handler(b_old, p_old, ctx_old, logs_old)
        # ---- NEW ----
        random.seed(seed)
        p_new = mk_player([key])
        e_new = mk_enemy(boss=boss)
        b_new = BT.Battle("monster", e_new, player=p_new)
        ctx_new = ctx_maker()
        logs_new = []
        we_proc(b_new, p_new, event, ctx_new, logs_new)
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

def test_dot():
    print("【1. proc_dot 4 key（hit/skill_hit，boss+普通双态）】")
    for key in DOT_KEYS:
        ev = DOT_EVENTS[key]
        # 命中触发场景：ctx 无需字段；battle.enemy 由 Battle init 建好
        def cm():
            return {}
        for boss in (False, True):
            mism = run_pair(key, ev, cm, boss=boss)
            check(f"{key} OLD==NEW (boss={boss})", not mism, str(mism[:2]))

def test_reflect():
    print("【2. proc_reflect 2 key（taken）】")
    for key in REFLECT_KEYS:
        for dmg in (0, 100, 300):
            for boss in (False, True):
                def cm(d=dmg):
                    return {"dmg": d, "taken": d}
                mism = run_pair(key, "taken", cm, boss=boss)
                check(f"{key} OLD==NEW (dmg={dmg} boss={boss})", not mism, str(mism[:2]))

def test_heal_amp():
    print("【3. proc_heal amp 4 key（heal，overflow 两态）】")
    for key in HEAL_KEYS:
        for ov in (0, 50):
            for heal0 in (0, 100, 333):
                def cm(ovv=ov, h=heal0):
                    return {"heal": h, "overflow": ovv, "target": {}}
                mism = run_pair(key, "heal", cm, boss=False)
                check(f"{key} OLD==NEW (heal={heal0} overflow={ov})", not mism, str(mism[:2]))

if __name__ == "__main__":
    # 前置：确认 10 key 已族化（proc 分发会走执行器）
    for k in DOT_KEYS + REFLECT_KEYS + HEAL_KEYS:
        assert _we_family(k), f"{k} 缺 family 标注"
    test_dot()
    test_reflect()
    test_heal_amp()
    print(f"\n结果: {passed} 通过, 0 失败")
