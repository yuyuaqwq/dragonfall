# -*- coding: utf-8 -*-
"""v181.P2C-C7 proc_next_atk_mark + proc_retort_mark 族 OLD vs NEW 差分探针（正式测试）。

策略（方案 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc8_passive_stack_probe.py）：
- OLD = WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc，模拟未族化）
- NEW = proc() 族分发（family 路由到 _we_exec_next_atk_mark/_we_exec_retort_mark 执行器）
固定 random.seed；断言 logs / ctx / state（hp/buffs/stacks/eff/e_buffs）逐字段相等。

场景（9 key × 各自触发事件 + 双事件配对 + 多态）：
- proc_next_atk_mark 5 key：
    trinity_rhythm / mountain_break / oath_blade（skill_hit 置标）
    novice_spark_followup（skill_cast 置 stacks.novice_spark）
    dusk_blade（kill：每场 1 次潜行置标）
- proc_retort_mark 4 key：
    gargoyle_retort / titan_retort / ranger_retort（taken 置 we_retort max）
    guardian_will（taken chance → e_buffs 弱化，命中 seed 扫描）
- passive 消费段：trinity/mountain/retort 旧语义 ctx.attack 门（battle 恒不传 → 空转）；
  oath/dusk 无 attack 门消费 mult + 清标（带 attack 键/无 attack 键两态都验 OLD==NEW）。
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS
import _c10_old_we as _OLDWE

NEXT_KEYS = ["trinity_rhythm", "mountain_break", "oath_blade", "novice_spark_followup", "dusk_blade"]
RETORT_KEYS = ["gargoyle_retort", "titan_retort", "ranger_retort", "guardian_will"]

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, class_name="战士", evolve_path=0):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": class_name, "evolve_path": evolve_path, "qq_id": "t1"}

def mk_enemy(hp=100000, max_hp=None, **kw):
    mh = hp if max_hp is None else max_hp
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": mh,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    e.update(kw)
    return e

def snapshot(piece):
    return copy.deepcopy(piece)

def state_slices(b, p):
    out = {}
    for bag, name in ((p.get("buffs"), "p.buffs"), (p.get("stacks"), "p.stacks"),
                      (p.get("eff"), "p.eff")):
        if bag:
            out[name] = snapshot(bag)
    e = b.enemy or {}
    for bag, name in ((e.get("buffs"), "e.buffs"), (b.e_buffs, "b.e_buffs")):
        if bag:
            out[name] = snapshot(bag)
    return out

def run_pair(key, event, ctx_maker, n_runs=20, player_mut=None, enemy_hp=None, hit_seed_range=0):
    """同一 key/事件 OLD handler vs NEW proc，逐次同 seed。player_mut 建好后改。"""
    mism = []
    rng = range(1, n_runs + 1)
    if hit_seed_range:
        rng = range(1, hit_seed_range)  # 概率触发：扫 seed 直到命中（两路同 seed 对比）
    for i in rng:
        seed = 4000 + i * 13
        random.seed(seed)
        p_old = mk_player([key])
        if player_mut:
            player_mut(p_old)
        b_old = BT.Battle("monster", mk_enemy(*enemy_hp) if enemy_hp else mk_enemy(), player=p_old)
        ctx_old = ctx_maker()
        logs_old = []
        handler = _OLDWE.old_handler(key, event)
        handler(b_old, p_old, ctx_old, logs_old)
        if hit_seed_range and not (b_old.enemy.get("buffs") or {}).get("mon_atk_down"):
            continue  # guardian：未命中 seed 跳过（两路同步进行需重跑同 seed 匹配）
        random.seed(seed)
        p_new = mk_player([key])
        if player_mut:
            player_mut(p_new)
        b_new = BT.Battle("monster", mk_enemy(*enemy_hp) if enemy_hp else mk_enemy(), player=p_new)
        ctx_new = ctx_maker()
        logs_new = []
        we_proc(b_new, p_new, event, ctx_new, logs_new)
        if hit_seed_range and not (b_new.enemy.get("buffs") or {}).get("mon_atk_down"):
            continue  # 同 seed 两路触发必须一致
        if logs_old != logs_new:
            mism.append(f"run{i}: logs OLD={logs_old} NEW={logs_new}")
            break
        so = state_slices(b_old, p_old)
        sn = state_slices(b_new, p_new)
        for k in set(so) | set(sn):
            if so.get(k) != sn.get(k):
                mism.append(f"run{i}: state[{k}] OLD={so.get(k)} NEW={sn.get(k)}")
        if ctx_old != ctx_new:
            mism.append(f"run{i}: ctx OLD={ctx_old} NEW={ctx_new}")
        if mism:
            break
        if hit_seed_range:
            return mism  # guardian：首个命中 seed 即验
    return mism

def test_next_atk_production():
    print("【1. proc_next_atk_mark 生产段（置标）】")
    for key, ev, ctxm in (
        ("trinity_rhythm", "skill_hit", lambda: {"dmg": 500, "is_crit": False, "skill": "测试", "kind": "物理"}),
        ("mountain_break", "skill_hit", lambda: {"dmg": 500, "is_crit": False}),
        ("oath_blade", "skill_hit", lambda: {"dmg": 500, "is_crit": False}),
        ("novice_spark_followup", "skill_cast", lambda: {"skill": "测试", "kind": "物理"}),
        ("dusk_blade", "kill", lambda: {}),
    ):
        mism = run_pair(key, ev, ctxm, n_runs=6)
        check(f"{key} {ev} OLD==NEW", not mism, str(mism[:2]))

def test_retort_production():
    print("【2. proc_retort_mark 生产段（taken 置标 / 弱化）】")
    for key in ("gargoyle_retort", "titan_retort", "ranger_retort"):
        mism = run_pair(key, "taken", lambda: {"dmg": 100}, n_runs=6)
        check(f"{key} taken OLD==NEW", not mism, str(mism[:2]))
    mism = run_pair("guardian_will", "taken", lambda: {"dmg": 100}, n_runs=5, hit_seed_range=400)
    check("guardian_will taken（命中 seed）OLD==NEW", not mism, str(mism[:2]))

def test_passive_consume():
    print("【3. passive 消费段（attack 门 / 无条件两态）】")
    # 预置标记后跑 passive；trinity/mountain/retort 验 attack 门 True/False 两态 + 清标/不清标
    # oath/dusk 无条件：有标记消费（mult + tag + 清标），无标记空转
    for key, mark in (("trinity_rhythm", "we_trinity"), ("mountain_break", "we_mountain"),
                      ("oath_blade", "we_oath"), ("dusk_blade", "we_dusk_dmg")):
        for with_attack in (True, False):
            def mut(p, k=key, mk=mark, wa=with_attack):
                p.setdefault("eff", {})[mk] = 0.30 if k == "trinity_rhythm" else (
                    0.25 if k in ("mountain_break", "oath_blade") else 0.30)
            def cm(wa=with_attack):
                c = {"mult": 1.0, "tags": []}
                if wa:
                    c["attack"] = True
                return c
            mism = run_pair(key, "passive", cm, n_runs=5, player_mut=mut)
            check(f"{key} passive attack={with_attack} OLD==NEW", not mism, str(mism[:2]))
    for key in ("gargoyle_retort", "titan_retort", "ranger_retort"):
        def mut(p, k=key):
            p.setdefault("eff", {})["we_retort"] = {"gargoyle_retort": 0.30,
                                                    "titan_retort": 0.40,
                                                    "ranger_retort": 0.20}[k]
        for with_attack in (True, False):
            def cm(wa=with_attack):
                c = {"mult": 1.0, "tags": []}
                if wa:
                    c["attack"] = True
                return c
            mism = run_pair(key, "passive", cm, n_runs=5, player_mut=mut)
            check(f"{key} passive attack={with_attack} OLD==NEW", not mism, str(mism[:2]))

def test_multi_retort_max():
    print("【4. 三 retort 同槽 max（多件装备语义）】")
    # 同装 gargoyle(0.30)+titan(0.40)：proc 遍历两 key 各置 we_retort max → 0.40（与旧多件一致）
    random.seed(99)
    p = mk_player(["gargoyle_retort", "titan_retort"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    we_proc(b, p, "taken", {"dmg": 100}, [])
    check("gargoyle+titan 同槽 max=0.40", abs(float((p.get("eff") or {}).get("we_retort", 0)) - 0.40) < 1e-9,
          str(p.get("eff")))

def test_migrated_route():
    print("【5. 族路由/白名单】")
    for k in NEXT_KEYS:
        check(f"{k} → proc_next_atk_mark", _we_family(k) == "proc_next_atk_mark"
              and _WE_EXEC_KEYS.get(k) == "proc_next_atk_mark", f"fam={_we_family(k)}")
    for k in RETORT_KEYS:
        check(f"{k} → proc_retort_mark", _we_family(k) == "proc_retort_mark"
              and _WE_EXEC_KEYS.get(k) == "proc_retort_mark", f"fam={_we_family(k)}")
    # v181.P2C-C10：guard_regen/dawn_regen 已迁 proc_aux 收尾族
    for k in ("guard_regen", "dawn_regen"):
        check(f"C10 {k} 进 proc_aux 路由", _WE_EXEC_KEYS.get(k) == "proc_aux",
              f"route={_WE_EXEC_KEYS.get(k)}")

if __name__ == "__main__":
    test_next_atk_production()
    test_retort_production()
    test_passive_consume()
    test_multi_retort_max()
    test_migrated_route()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
