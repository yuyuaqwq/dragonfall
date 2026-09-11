# -*- coding: utf-8 -*-
"""v181.P2C-C6 proc_buff + proc_stack 面板段 OLD vs NEW 差分探针（正式测试）。

策略（方案 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc8_passive_stack_probe.py）：
- OLD = WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc，模拟未族化）
- NEW = proc() 族分发（family → _WE_EXEC_KEYS → proc_buff/proc_stack 执行器）
固定 random.seed；断言 logs / state（buffs/stacks/eff/hp/max_hp）逐字段相等。

场景：
- proc_buff 7 key：gale_step 家族 5 key（battle_start 写 buffs.gale_step + eff.gale_step_pct
  共享键 max 语义）+ novice_wind_spd（hit 写 buffs.novice_wind_spd）+ abyss_barrier
  （battle_start maxhp 永久加成）
- proc_stack 面板段（wind_mark/thunder_weave hit 叠层；C8 已迁，此处回归叠层边界：
  3 层/满层 5 清零 charge）+ _player_stats 面板输出 OLD==NEW（关键：面板 5 键
  spd/atk 输出在 _player_stats 直读改造前后一致）
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS
import _c10_old_we as _OLDWE

BUFF_KEYS = ["gale_step", "swift_boots", "deadman_stride", "temple_stride", "void_stride",
             "novice_wind_spd", "abyss_barrier"]

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
    for k in ("hp", "mp", "max_hp", "max_mp"):
        out[f"p.{k}"] = p.get(k)
    for bag, name in ((p.get("buffs"), "p.buffs"), (p.get("stacks"), "p.stacks"),
                      (p.get("eff"), "p.eff"), (p.get("shields"), "p.shields")):
        if bag:
            out[name] = snapshot(bag)
    return out

def panel_slice(b, p):
    st = b._player_stats(p)
    return {k: st.get(k) for k in ("spd", "atk", "matk", "max_hp", "crit_dmg")}

def run_pair(key, event, ctx_maker, n_runs=10, player_mut=None):
    """同一 key/事件 OLD handler vs NEW proc，逐次同 seed。"""
    mism = []
    for i in range(n_runs):
        seed = 5000 + i * 17
        random.seed(seed)
        p_old = mk_player([key])
        if player_mut:
            player_mut(p_old)
        b_old = BT.Battle("monster", mk_enemy(), player=p_old)
        ctx_old = ctx_maker()
        logs_old = []
        handler = _OLDWE.old_handler(key, event)
        handler(b_old, p_old, ctx_old, logs_old)
        random.seed(seed)
        p_new = mk_player([key])
        if player_mut:
            player_mut(p_new)
        b_new = BT.Battle("monster", mk_enemy(), player=p_new)
        ctx_new = ctx_maker()
        logs_new = []
        we_proc(b_new, p_new, event, ctx_new, logs_new)
        if logs_old != logs_new:
            mism.append(f"run{i}: logs OLD={logs_old} NEW={logs_new}")
            continue
        so = state_slices(b_old, p_old)
        sn = state_slices(b_new, p_new)
        for k in set(so) | set(sn):
            if so.get(k) != sn.get(k):
                mism.append(f"run{i}: state[{k}] OLD={so.get(k)} NEW={sn.get(k)}")
        # 面板输出等价（battle _player_stats 直读改造前后面板 5 键一致）
        po = panel_slice(b_old, p_old)
        pn = panel_slice(b_new, p_new)
        for k in po:
            if po.get(k) != pn.get(k):
                mism.append(f"run{i}: panel[{k}] OLD={po.get(k)} NEW={pn.get(k)}")
        if mism:
            break
    return mism

def test_proc_buff():
    print("【1. proc_buff 7 key OLD==NEW】")
    for key in BUFF_KEYS:
        event = "hit" if key == "novice_wind_spd" else "battle_start"
        mism = run_pair(key, event, lambda: {}, n_runs=6)
        check(f"{key} {event} OLD==NEW（含面板 spd）", not mism, str(mism[:2]))

def test_gale_shared_key_max():
    print("【2. gale_step 家族共享键 max 语义（双装备）】")
    # 双装备 gale_step + swift_boots → buffs.gale_step=max(3,3)=3，eff.gale_step_pct=max(0.15,0.2)
    for seed in (11, 22):
        random.seed(seed)
        p_old = mk_player(["gale_step", "swift_boots"])
        b_old = BT.Battle("monster", mk_enemy(), player=p_old)
        _OLDWE.old_handler("gale_step", "battle_start")(b_old, p_old, {}, [])
        _OLDWE.old_handler("swift_boots", "battle_start")(b_old, p_old, {}, [])
        random.seed(seed)
        p_new = mk_player(["gale_step", "swift_boots"])
        b_new = BT.Battle("monster", mk_enemy(), player=p_new)
        we_proc(b_new, p_new, "battle_start", {}, [])
        check(f"seed{seed} buffs/eff 相等",
              (p_old.get("buffs"), p_old.get("eff")) == (p_new.get("buffs"), p_new.get("eff")),
              f"OLD={(p_old.get('buffs'), p_old.get('eff'))} NEW={(p_new.get('buffs'), p_new.get('eff'))}")
        po, pn = panel_slice(b_old, p_old), panel_slice(b_new, p_new)
        check(f"seed{seed} 面板 spd 相等（双装备 max）", po["spd"] == pn["spd"],
              f"OLD={po['spd']} NEW={pn['spd']}")

def test_stack_panel_boundaries():
    print("【3. proc_stack 面板段叠层边界 OLD==NEW（含 _player_stats 面板键）】")
    # wind_mark：3 层 → 面板 spd ×(1+3×0.02)
    for key, ev, n, expect in (("wind_mark", "hit", 3, None), ("thunder_weave", "hit", 5, None)):
        for seed in (31, 47):
            random.seed(seed)
            p_old = mk_player([key])
            b_old = BT.Battle("monster", mk_enemy(), player=p_old)
            for _ in range(n):
                _OLDWE.old_handler(key, ev)(b_old, p_old, {"dmg": 100}, [])
            random.seed(seed)
            p_new = mk_player([key])
            b_new = BT.Battle("monster", mk_enemy(), player=p_new)
            for _ in range(n):
                we_proc(b_new, p_new, ev, {"dmg": 100}, [])
            check(f"{key} {n}次 seed{seed} stacks 相等",
                  (p_old.get("stacks"), p_old.get("eff")) == (p_new.get("stacks"), p_new.get("eff")),
                  f"OLD={(p_old.get('stacks'), p_old.get('eff'))} NEW={(p_new.get('stacks'), p_new.get('eff'))}")
            po, pn = panel_slice(b_old, p_old), panel_slice(b_new, p_new)
            same = all(po[k] == pn[k] for k in ("spd", "atk"))
            check(f"{key} {n}次 seed{seed} 面板 spd/atk 相等", same,
                  f"OLD={po} NEW={pn}")
    # thunder_weave 4 层边界（不满层不 charge）
    for seed in (59,):
        p_old = mk_player(["thunder_weave"])
        b_old = BT.Battle("monster", mk_enemy(), player=p_old)
        for _ in range(4):
            _OLDWE.old_handler("thunder_weave", "hit")(b_old, p_old, {"dmg": 100}, [])
        p_new = mk_player(["thunder_weave"])
        b_new = BT.Battle("monster", mk_enemy(), player=p_new)
        for _ in range(4):
            we_proc(b_new, p_new, "hit", {"dmg": 100}, [])
        check("thunder 4 层不满不清零（eff 无 charge）",
              p_old.get("stacks") == p_new.get("stacks") and (p_new.get("eff") or {}).get("we_thunder_charge") is None,
              f"stacks={p_new.get('stacks')} eff={p_new.get('eff')}")

def test_migrated_route():
    print("【4. 族路由/白名单】")
    for k in BUFF_KEYS:
        check(f"{k} → proc_buff", _we_family(k) == "proc_buff"
              and _WE_EXEC_KEYS.get(k) == "proc_buff", f"fam={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    # C6 保留 C8 已迁 proc_stack 面板段 key
    for k in ("wind_mark", "thunder_weave"):
        check(f"{k} → proc_stack（C8 保留）", _WE_EXEC_KEYS.get(k) == "proc_stack", f"route={_WE_EXEC_KEYS.get(k)}")

def test_battle_direct_read_gone():
    print("【5. battle _player_stats 直读内容名清零（static grep）】")
    import subprocess, os as _os
    bp = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "game", "battle.py")
    with open(bp, encoding="utf-8") as f:
        txt = f.read()
    seg = txt[txt.find("def _player_stats"): txt.find("def _passive_map")]
    for pat in ("get(\"gale_step_pct\"", "get(\"wind_mark\"", "get(\"novice_wind_spd\"", "get(\"thunder_weave\""):
        check(f"_player_stats 段无 {pat} 直读", pat not in seg, "")

if __name__ == "__main__":
    test_proc_buff()
    test_gale_shared_key_max()
    test_stack_panel_boundaries()
    test_migrated_route()
    test_battle_direct_read_gone()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
