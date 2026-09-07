# -*- coding: utf-8 -*-
"""v181.P2C-C8 proc_passive_mult + proc_stack 族 OLD vs NEW 差分探针（正式测试）。

策略（方案 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc2_we_family_probe.py）：
- OLD = WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc，模拟未族化）
- NEW = proc() 族分发（family 路由到 _we_exec_passive_mult/_we_exec_stack 执行器）
固定 random.seed；断言 logs / ctx / state（hp/mp/shields/buffs/stacks/eff/debuffs/e_buffs）
逐字段相等。

场景（4 + 7 key × 各自触发事件 + 多态）：
- proc_passive_mult 4 key：
    twilight_execute / star_slayer_edge（passive：敌 hp 阈值两态）
    arcane_firmament（battle_start 置标 + passive 魔法/物理两态）
    combo_end（hit 置标[battle 连段活跃] + passive 暴击/非暴两态）
- proc_stack 7 key：
    wind_mark / novice_hunt_combo / thunder_weave（hit 叠层；thunder 满层置 charge）
    rune_amp / sage_amp / eternal_codex（skill_cast 叠层）
    time_staff（turn_start 叠层+回血；passive 消费）
    + 各双事件 key 的 passive 乘区消费段（rune_amp/sage_amp/eternal_codex/time_staff/thunder_weave）
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS
import _c10_old_we as _OLDWE

PMULT_KEYS = ["twilight_execute", "star_slayer_edge", "arcane_firmament", "combo_end"]
STACK_KEYS = ["wind_mark", "thunder_weave", "rune_amp", "sage_amp", "eternal_codex",
              "time_staff", "novice_hunt_combo"]

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
    e = b.enemy or {}
    for k in ("hp", "max_hp"):
        out[f"e.{k}"] = e.get(k)
    for bag, name in ((e.get("buffs"), "e.buffs"), (e.get("debuffs"), "e.debuffs"),
                      (e.get("e_buffs"), "e.e_buffs"), (b.e_buffs, "b.e_buffs"),
                      (b._p_stacks() if hasattr(b, "_p_stacks") else None, "b.p_stacks"),
                      (b._p_eff() if hasattr(b, "_p_eff") else None, "b.p_eff")):
        if bag:
            out[name] = snapshot(bag)
    return out

def run_pair(key, event, ctx_maker, n_runs=20, player_mut=None, enemy_hp=None):
    """同一 key/事件 OLD handler vs NEW proc，逐次同 seed。player_mut(player) 建好后改（低血等）。"""
    mism = []
    for i in range(n_runs):
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
        random.seed(seed)
        p_new = mk_player([key])
        if player_mut:
            player_mut(p_new)
        b_new = BT.Battle("monster", mk_enemy(*enemy_hp) if enemy_hp else mk_enemy(), player=p_new)
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
        if ctx_old != ctx_new:
            mism.append(f"run{i}: ctx OLD={ctx_old} NEW={ctx_new}")
        if mism:
            break
    return mism

def test_passive_mult():
    print("【1. proc_passive_mult 4 key】")
    # twilight 低血（hp 30 / max 100，ratio=0.30 < 0.40）；star 高血（hp 90 / max 100）
    for key, ehp, emax in (("twilight_execute", 30, 100), ("star_slayer_edge", 90, 100)):
        mism = run_pair(key, "passive",
                        lambda: {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"},
                        n_runs=5, enemy_hp=(ehp, emax))
        check(f"{key} passive 阈值命中 OLD==NEW", not mism, str(mism[:2]))
    # 反向：twilight 高血不触发 / star 中血不触发
    for key, ehp, emax in (("twilight_execute", 50, 100), ("star_slayer_edge", 50, 100)):
        mism = run_pair(key, "passive",
                        lambda: {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"},
                        n_runs=3, enemy_hp=(ehp, emax))
        check(f"{key} passive 阈值外 OLD==NEW", not mism, str(mism[:2]))
    # arcane_firmament：battle_start 置标 + passive 魔法/物理
    mism = run_pair("arcane_firmament", "battle_start", lambda: {}, n_runs=3)
    check("arcane_firmament battle_start OLD==NEW", not mism, str(mism[:2]))
    for kind in ("魔法", "物理"):
        mism = run_pair("arcane_firmament", "passive",
                        lambda k=kind: {"mult": 1.0, "tags": [], "is_crit": False, "kind": k},
                        n_runs=5)
        check(f"arcane_firmament passive kind={kind} OLD==NEW", not mism, str(mism[:2]))
    # combo_end：hit 置标需 combo 活跃玩家（cls_ci_ke + evolve_path=1）
    def mut(p):
        p["class_name"] = "cls_ci_ke"
        p["evolve_path"] = 1
    mism = run_pair("combo_end", "hit", lambda: {"dmg": 100, "is_crit": False},
                    n_runs=5, player_mut=mut)
    check("combo_end hit 置标 OLD==NEW", not mism, str(mism[:2]))
    # passive 消费：先置标再 proc（OLD 手置标 / NEW 手置标同样）
    for crit in (True, False):
        def cm(c=crit):
            return {"mult": 1.0, "tags": [], "is_crit": c, "kind": "物理"}
        mism = run_pair("combo_end", "passive", cm, n_runs=5)
        check(f"combo_end passive crit={crit} OLD==NEW（未置标空转）", not mism, str(mism[:2]))

def test_stack_production():
    print("【2. proc_stack 生产段（叠层写槽）】")
    # wind_mark：hit 叠层 3 次
    mism = run_pair("wind_mark", "hit", lambda: {"dmg": 100}, n_runs=8)
    check("wind_mark hit 叠层 OLD==NEW", not mism, str(mism[:2]))
    # novice_hunt_combo：hit 暴击叠层（非暴不叠）
    for crit in (True, False):
        mism = run_pair("novice_hunt_combo", "hit",
                        lambda c=crit: {"dmg": 100, "is_crit": c}, n_runs=8)
        check(f"novice_hunt_combo hit crit={crit} OLD==NEW", not mism, str(mism[:2]))
    # thunder_weave：hit 叠层至满 → charge
    mism = run_pair("thunder_weave", "hit", lambda: {"dmg": 100}, n_runs=8)
    check("thunder_weave hit 叠层 OLD==NEW", not mism, str(mism[:2]))
    # rune_amp/sage_amp/eternal_codex：skill_cast 叠层
    for key in ("rune_amp", "sage_amp", "eternal_codex"):
        mism = run_pair(key, "skill_cast", lambda: {"skill": "测试", "kind": "魔法"}, n_runs=8)
        check(f"{key} skill_cast 叠层 OLD==NEW", not mism, str(mism[:2]))
    # time_staff：turn_start 叠层+回血
    def mut(p):
        p["hp"] = int(p["max_hp"] * 0.5)
    mism = run_pair("time_staff", "turn_start", lambda: {}, n_runs=8, player_mut=mut)
    check("time_staff turn_start 叠层+回血 OLD==NEW", not mism, str(mism[:2]))

def test_stack_passive_consume():
    print("【3. proc_stack 被动乘区消费段】")
    # 预置层数/charge 后跑 passive：层数在 stacks 槽，charge 在 eff 槽（生产事件已由旧 handler 写）
    for key, stack_n, tag in (("time_staff", 6, "6层"), ("eternal_codex", 5, "5层"),
                              ("rune_amp", 3, "3层")):
        def mut(p, sn=stack_n, k=key):
            p.setdefault("stacks", {})[k] = sn
        mism = run_pair(key, "passive",
                        lambda: {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"},
                        n_runs=5, player_mut=mut)
        check(f"{key} passive {tag} OLD==NEW", not mism, str(mism[:2]))
    # rune_amp 消费后清 0 已含在 state_slices 对比
    for key in ("sage_amp", "thunder_weave"):
        def mut(p, k=key):
            p.setdefault("eff", {})["we_sage_charge" if k == "sage_amp" else "we_thunder_charge"] = 0.25 if k == "sage_amp" else 0.20
        mism = run_pair(key, "passive",
                        lambda: {"mult": 1.0, "tags": [], "is_crit": False, "kind": "物理"},
                        n_runs=5, player_mut=mut)
        check(f"{key} passive charge 消费 OLD==NEW", not mism, str(mism[:2]))

def test_migrated_route():
    print("【4. 族路由/白名单】")
    for k in PMULT_KEYS:
        check(f"{k} → proc_passive_mult", _we_family(k) == "proc_passive_mult"
              and _WE_EXEC_KEYS.get(k) == "proc_passive_mult", f"fam={_we_family(k)}")
    for k in STACK_KEYS:
        check(f"{k} → proc_stack", _we_family(k) == "proc_stack"
              and _WE_EXEC_KEYS.get(k) == "proc_stack", f"fam={_we_family(k)}")


def test_three_passive_hookpoints():
    """【5. passive 三挂点（heal/taken/dmg）NEW==OLD（含旧语义：heal/taken ctx 也写 mult 无害）】"""
    keys = ["time_staff", "rune_amp", "eternal_codex", "sage_amp", "thunder_weave",
            "combo_end", "twilight_execute", "star_slayer_edge", "arcane_firmament",
            "wind_mark", "novice_hunt_combo"]
    def prep(p, key):
        p.setdefault("stacks", {})["time_staff"] = 3
        p.setdefault("stacks", {})["rune_amp"] = 2
        p.setdefault("eff", {})["we_sage_charge"] = 0.25
        p.setdefault("eff", {})["we_combo_end"] = 0.4
    for ctxbase in ({"heal": 100}, {"taken": 50}, {"mult": 1.0, "tags": [], "kind": "物理"}):
        for key in keys:
            mism = []
            for i in range(3):
                seed = 9000 + i * 7
                random.seed(seed)
                p_old = mk_player([key]); prep(p_old, key)
                b_old = BT.Battle("monster", mk_enemy(), player=p_old)
                ctx_old = dict(ctxbase); logs_old = []
                fn = None
                try:
                    fn = _OLDWE.old_handler(key, "passive")
                except Exception:
                    fn = None
                if fn:
                    fn(b_old, p_old, ctx_old, logs_old)
                random.seed(seed)
                p_new = mk_player([key]); prep(p_new, key)
                b_new = BT.Battle("monster", mk_enemy(), player=p_new)
                ctx_new = dict(ctxbase); logs_new = []
                we_proc(b_new, p_new, "passive", ctx_new, logs_new)
                if ctx_old != ctx_new or logs_old != logs_new                         or p_old.get("stacks") != p_new.get("stacks") or p_old.get("eff") != p_new.get("eff"):
                    mism.append((i, dict(ctx_old), dict(ctx_new), logs_old, logs_new))
                    break
            check(f"passive挂点 {list(ctxbase.keys())} {key} OLD==NEW", not mism, str(mism[:1]))

if __name__ == "__main__":
    test_passive_mult()
    test_stack_production()
    test_stack_passive_consume()
    test_three_passive_hookpoints()
    test_migrated_route()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
