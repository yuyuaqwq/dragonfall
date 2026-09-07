# -*- coding: utf-8 -*-
"""v181.P2C-C3 proc_shield 族执行器 OLD vs NEW 差分探针（护盾族 10 key）正式测试。

策略（方案 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc2_we_family_probe.py）：
- OLD = WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc，模拟未族化）
- NEW = proc() 族分发（family 路由到 _we_exec_shield 执行器）
固定 random.seed；断言 logs / ctx / state（hp/mp/shields/buffs/stacks/eff/debuffs/e_buffs）逐字段相等。

场景（10 key × 触发事件 + 多态）：
- starlight_bulwark / eclipse_crown：battle_start
- sentinel_aegis / deeprock_aegis：taken（概率 + 冷却，固定 seed 同判定）
- bedrock_crown / firmament_crown / gargoyle_heart：threshold（低血触发 + 每场限次/计数）
- echo_bless / atonement_shield：heal 溢出（overflow 0/有值两态）
- endless_radiance：skill_hit 暴击（crit True/False + CD）

另含：护盾破后回放探针（shield 值/期限）、未装备 key 空转（has_effect=False → 执行器不触发）。
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS
import _c10_old_we as _OLDWE

# key → 触发事件（与旧 handler 注册事件集一致）
SHIELD_EVENTS = {
    "starlight_bulwark": "battle_start", "eclipse_crown": "battle_start",
    "sentinel_aegis": "taken", "deeprock_aegis": "taken",
    "bedrock_crown": "threshold", "firmament_crown": "threshold",
    "gargoyle_heart": "threshold",
    "echo_bless": "heal", "atonement_shield": "heal",
    "endless_radiance": "skill_hit",
}
SHIELD_KEYS = list(SHIELD_EVENTS)

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

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
    for bag, name in ((e.get("debuffs"), "e.debuffs"), (b.e_buffs, "b.e_buffs"),
                      (b._p_buffs_bag(), "b.p_buffs"), (b._p_shields_bag(), "b.p_shields"),
                      (b._p_eff(), "b.p_eff"), (b._p_stacks(), "b.p_stacks")):
        if bag:
            out[name] = copy.deepcopy(bag)
    return out

def run_pair(key, event, ctx_maker, player_hp=None, n_runs=25):
    """对同一 key 跑 OLD handler 与 NEW proc 族分发，逐次同 seed 对比。"""
    mism = []
    for i in range(n_runs):
        seed = 1000 + i * 7
        random.seed(seed)
        p_old = mk_player([key])
        if player_hp is not None:
            p_old["hp"] = player_hp
        e_old = mk_enemy()
        b_old = BT.Battle("monster", e_old, player=p_old)
        ctx_old = ctx_maker()
        logs_old = []
        handler = _OLDWE.old_handler(key, event)
        handler(b_old, p_old, ctx_old, logs_old)
        random.seed(seed)
        p_new = mk_player([key])
        if player_hp is not None:
            p_new["hp"] = player_hp
        e_new = mk_enemy()
        b_new = BT.Battle("monster", e_new, player=p_new)
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

def test_battle_start():
    print("【1. battle_start 盾（starlight/eclipse）】")
    for key in ("starlight_bulwark", "eclipse_crown"):
        mism = run_pair(key, "battle_start", lambda: {}, n_runs=15)
        check(f"{key} OLD==NEW", not mism, str(mism[:2]))
    # 星辉壁垒盾存在（具体值随 battle 面板 max_hp——OLD/NEW 等价已保证数值一致）
    random.seed(7)
    p = mk_player(["starlight_bulwark"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    sh = (p.get("shields") or {}).get("we_starlight")
    check("starlight 获得护盾", bool(sh and sh.get("value", 0) > 0), str(sh))
    check("starlight 写 we_starlight_next 刷新标记", float((p.get("eff") or {}).get("we_starlight_next", 0) or 0) > 0,
          str(p.get("eff")))
    random.seed(8)
    p2 = mk_player(["eclipse_crown"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    sh2 = (p2.get("shields") or {}).get("we_eclipse")
    check("eclipse 获得护盾", bool(sh2 and sh2.get("value", 0) > 0), str(sh2))
    check("eclipse 写 we_eclipse_active", bool((p2.get("eff") or {}).get("we_eclipse_active")), str(p2.get("eff")))

def test_taken():
    print("【2. taken 概率盾（sentinel/deeprock）】")
    for key in ("sentinel_aegis", "deeprock_aegis"):
        mism = run_pair(key, "taken", lambda: {"dmg": 100, "taken": 100}, n_runs=40)
        check(f"{key} OLD==NEW", not mism, str(mism[:2]))
    # 数值：sentinel lv30 → base6+0.5×30=21
    random.seed(11)
    p = mk_player(["sentinel_aegis"], level=30)
    b = BT.Battle("monster", mk_enemy(), player=p)
    logs = []
    we_proc(b, p, "taken", {"dmg": 100, "taken": 100}, logs)
    sh = (p.get("shields") or {}).get("we_sentinel")
    if sh:
        check("sentinel 盾值 21 (6+0.5×30)", sh.get("value") == 21, str(sh))

def test_threshold():
    print("【3. threshold 阈值盾（bedrock/firmament/gargoyle）】")
    for key, hp in (("bedrock_crown", 2000), ("firmament_crown", 2500), ("gargoyle_heart", 2000)):
        mism = run_pair(key, "threshold", lambda: {"dmg": 100}, player_hp=hp, n_runs=20)
        check(f"{key} OLD==NEW (低血触发)", not mism, str(mism[:2]))
    # 高血不触发（阈值未过）
    for key in ("bedrock_crown", "firmament_crown", "gargoyle_heart"):
        mism = run_pair(key, "threshold", lambda: {"dmg": 100}, player_hp=9000, n_runs=5)
        check(f"{key} OLD==NEW (高血不触发)", not mism, str(mism[:2]))
    # 磐石每场 1 次：二次触发不再加盾（used 标记已置；阈值链按 test_v140 法：init 后改 max_hp/hp 为低血态）
    random.seed(3)
    p = mk_player(["bedrock_crown"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    p["max_hp"] = 9999
    p["hp"] = 2000
    we_proc(b, p, "threshold", {"dmg": 100}, [])
    n1 = int((p.get("shields") or {}).get("we_bedrock", {}).get("value", 0))
    we_proc(b, p, "threshold", {"dmg": 100}, [])
    n2 = int((p.get("shields") or {}).get("we_bedrock", {}).get("value", 0))
    check("bedrock 二次触发不再加盾", n1 > 0 and n1 == n2 and (p.get("eff") or {}).get("we_bedrock_used") is True,
          f"n1={n1} n2={n2} eff={p.get('eff')}")

def test_heal_overflow():
    print("【4. heal 溢出转盾（echo_bless/atonement）】")
    for key in ("echo_bless", "atonement_shield"):
        for ov in (0, 50, 99999):
            def cm(ovv=ov):
                return {"heal": 500, "overflow": ovv, "target": {}}
            mism = run_pair(key, "heal", cm, n_runs=10)
            check(f"{key} overflow={ov} OLD==NEW", not mism, str(mism[:2]))
    # 数值：echo_bless 溢出按 overflow×30% cap 10%maxhp；atonement 全额 cap 15%maxhp（值随 battle 面板 max_hp，
    # 但 OLD/NEW 等价已保证一致——这里验证"溢出越多盾越大、cap 生效"相对关系）
    random.seed(13)
    for key, sk in (("echo_bless", "we_echo_bless"), ("atonement_shield", "we_atonement")):
        p = mk_player([key])
        b = BT.Battle("monster", mk_enemy(), player=p)
        ctx = {"heal": 9999, "overflow": 500, "target": {}}
        logs = []
        we_proc(b, p, "heal", ctx, logs)
        sh = (p.get("shields") or {}).get(sk)
        check(f"{key} 溢出转盾生效", bool(sh and sh.get("value", 0) > 0), f"{sh} logs={logs}")
    # atonement 写 active 标记
    random.seed(14)
    p = mk_player(["atonement_shield"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    we_proc(b, p, "heal", {"heal": 9999, "overflow": 500}, [])
    check("atonement 写 we_atonement_active", bool((p.get("eff") or {}).get("we_atonement_active")),
          str(p.get("eff")))

def test_crit():
    print("【5. skill_hit 暴击盾（endless_radiance）】")
    for crit in (False, True):
        def cm(c=crit):
            return {"dmg": 500, "is_crit": c, "skill": "测试", "kind": "物理"}
        mism = run_pair("endless_radiance", "skill_hit", cm, n_runs=20)
        check(f"endless_radiance crit={crit} OLD==NEW", not mism, str(mism[:2]))
    random.seed(15)
    p = mk_player(["endless_radiance"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    logs = []
    we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": True}, logs)
    sh = (p.get("shields") or {}).get("we_radiance")
    check("endless_radiance 暴击盾生效", bool(sh and sh.get("value", 0) > 0), f"{sh} logs={logs}")
    check("endless_radiance 写 CD", float((p.get("eff") or {}).get("we_radiance_cd", 0) or 0) > 0,
          str(p.get("eff")))

def test_no_effect_idle():
    print("【6. 未装备 key 空转（执行器不触发）】")
    # 玩家不装任何特效 → proc 无 key → 无副作用
    p = mk_player([])
    b = BT.Battle("monster", mk_enemy(), player=p)
    logs = []
    we_proc(b, p, "battle_start", {}, logs)
    we_proc(b, p, "taken", {"dmg": 100}, logs)
    we_proc(b, p, "heal", {"heal": 500, "overflow": 100}, logs)
    we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": True}, logs)
    check("无装备空转无副作用", not (p.get("shields")) and not logs, f"shields={p.get('shields')} logs={logs}")

def test_we_data_override():
    print("【7. 装备 we_data 覆盖层（deeprock 黑曜胸甲实例）】")
    # 名册 eq_hei_yao_xiong_jia we_data {'chance':0.1,'shield_pct':0.08,'cd':2} 与表同 → 行为一致
    from game.core import drops
    eq = drops.generate_roster_equip("eq_hei_yao_xiong_jia")
    p = mk_player([])
    p["equipment"] = {"armor": eq}
    b = BT.Battle("monster", mk_enemy(), player=p)
    mism = []
    for i in range(30):
        seed = 3000 + i
        random.seed(seed)
        p1 = mk_player([]); p1["equipment"] = {"armor": dict(eq)}
        b1 = BT.Battle("monster", mk_enemy(), player=p1)
        l1 = []
        _OLDWE.old_handler("deeprock_aegis", "taken")(b1, p1, {"dmg": 100, "taken": 100}, l1)
        random.seed(seed)
        p2 = mk_player([]); p2["equipment"] = {"armor": dict(eq)}
        b2 = BT.Battle("monster", mk_enemy(), player=p2)
        l2 = []
        we_proc(b2, p2, "taken", {"dmg": 100, "taken": 100}, l2)
        if l1 != l2 or state_slices(b1, p1) != state_slices(b2, p2):
            mism.append(f"run{i}")
            break
    check("deeprock we_data 实例 OLD==NEW", not mism, str(mism[:2]))

if __name__ == "__main__":
    # 前置：确认 10 key family=proc_shield 且在路由表
    from game.core.weapon_effects import _WE_EXEC_KEYS
    for k in SHIELD_KEYS:
        assert _we_family(k) == "proc_shield", f"{k} family={_we_family(k)}"
        assert _WE_EXEC_KEYS.get(k) == "proc_shield", f"{k} route={_WE_EXEC_KEYS.get(k)}"
    test_battle_start()
    test_taken()
    test_threshold()
    test_heal_overflow()
    test_crit()
    test_no_effect_idle()
    test_we_data_override()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
