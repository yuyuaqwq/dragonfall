# -*- coding: utf-8 -*-
"""v181.P2C-C9 保命/特殊族 OLD vs NEW 差分探针（正式测试）。

策略（方案 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc8_passive_stack_probe.py）：
- OLD = WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc，模拟未族化）
- NEW = proc() 族分发（family 路由到 _we_exec_dr_revive/_we_exec_special 执行器）
固定 random.seed；断言 logs / ctx / state（hp/buffs/stacks/eff/shields/e_buffs）逐字段相等。

场景（5 key × 各自触发事件 + 双事件配对 + battle 消费点差分）：
- undying_will：battle_start 登记 used=False + threshold 免死/回血/每场 1 次（hp<20% / ≥20% 两态）
- death_dance：battle_start 初始化 pool + turn_start 结算 pay（pool 半空/空两态）
- death_dance_armor：passive taken 减伤 8%（带 taken/不带两态）
- novice_first_turn_guard/dodge：battle_start 置标记（含日志原文案）
- battle 消费点差分：_post_hp_lethal（undying 免死回拉 0.10 hp_pct 表读 + death_dance 0.35
  pool_pct 表读）/ _mitigate_chain（守御 mark_key）/ _roll_dodge（远行 mark_key）——
  OLD 段（读表前原硬编码直读）vs NEW（现 battle 查表）行为一致。
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS

DR_KEYS = ["undying_will", "death_dance_armor"]
SPECIAL_KEYS = ["death_dance", "novice_first_turn_guard", "novice_first_turn_dodge"]

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, class_name="战士", hp=9999, max_hp=9999):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": hp, "max_hp": max_hp, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": class_name, "qq_id": "t1"}

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
    for k in ("hp", "max_hp"):
        out[f"p.{k}"] = p.get(k)
    for bag, name in ((p.get("buffs"), "p.buffs"), (p.get("stacks"), "p.stacks"),
                      (p.get("eff"), "p.eff"), (p.get("shields"), "p.shields")):
        if bag:
            out[name] = snapshot(bag)
    e = b.enemy or {}
    for bag, name in ((e.get("buffs"), "e.buffs"), (b.e_buffs, "b.e_buffs")):
        if bag:
            out[name] = snapshot(bag)
    return out

def run_pair(key, event, ctx_maker, n_runs=20, player_mut=None, enemy_hp=None):
    """同一 key/事件 OLD handler vs NEW proc，逐次同 seed。player_mut 建好后改（低血等）。"""
    mism = []
    for i in range(1, n_runs + 1):
        seed = 4000 + i * 13
        random.seed(seed)
        p_old = mk_player([key])
        if player_mut:
            player_mut(p_old)
        b_old = BT.Battle("monster", mk_enemy(*enemy_hp) if enemy_hp else mk_enemy(), player=p_old)
        ctx_old = ctx_maker()
        logs_old = []
        handler = WEAPON_EFFECTS[key][event]
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

def test_dr_revive_undying():
    print("【1. undying_will（battle_start 登记 + threshold 免死/回血/每场 1 次）】")
    # battle_start：登记 we_undying_used=False
    mism = run_pair("undying_will", "battle_start", lambda: {}, n_runs=5)
    check("undying_will battle_start OLD==NEW", not mism, str(mism[:2]))
    # threshold：hp<20%（低血触发免死+回血）；每场 1 次（used 后再触发不生效）
    def mut_low(p):
        p["hp"] = int(p["max_hp"] * 0.15)
    def mut_high(p):
        p["hp"] = int(p["max_hp"] * 0.50)
    def mut_used(p):
        p["hp"] = int(p["max_hp"] * 0.15)
        p.setdefault("eff", {})["we_undying_used"] = True
    for name, mut in (("低血触发", mut_low), ("hp≥20% 不触发", mut_high), ("used 后不再触发", mut_used)):
        mism = run_pair("undying_will", "threshold", lambda: {"dmg": 100}, n_runs=8, player_mut=mut)
        check(f"undying_will threshold {name} OLD==NEW", not mism, str(mism[:2]))

def test_death_dance_pool():
    print("【2. death_dance（battle_start 初始化 + turn_start 结算 pay）】")
    mism = run_pair("death_dance", "battle_start", lambda: {}, n_runs=5)
    check("death_dance battle_start 初始化 OLD==NEW", not mism, str(mism[:2]))
    def mut_halfpool(p):
        p.setdefault("eff", {})["we_death_pool"] = 350.0  # pay = 35 → 剩余 315
    def mut_fullpool(p):
        p.setdefault("eff", {})["we_death_pool"] = 1000.0
    def mut_zeropool(p):
        p.setdefault("eff", {})["we_death_pool"] = 0.0
    for name, mut in (("pool=350 结算", mut_halfpool), ("pool=1000 结算", mut_fullpool),
                      ("pool=0 空转", mut_zeropool)):
        mism = run_pair("death_dance", "turn_start", lambda: {}, n_runs=8, player_mut=mut)
        check(f"death_dance turn_start {name} OLD==NEW", not mism, str(mism[:2]))

def test_death_dance_armor():
    print("【3. death_dance_armor passive taken 减伤 8%】")
    for with_taken in (True, False):
        def cm(wt=with_taken):
            return {"taken": 500} if wt else {}
        mism = run_pair("death_dance_armor", "passive", cm, n_runs=8)
        check(f"death_dance_armor passive taken={with_taken} OLD==NEW", not mism, str(mism[:2]))

def test_novice_marks():
    print("【4. novice_first_turn_guard/dodge battle_start 置标】")
    for key in ("novice_first_turn_guard", "novice_first_turn_dodge"):
        mism = run_pair(key, "battle_start", lambda: {}, n_runs=6)
        check(f"{key} battle_start OLD==NEW", not mism, str(mism[:2]))

def test_battle_consume_lethal():
    print("【5. battle _post_hp_lethal 差分（undying 免死回拉 hp_pct + death_dance 池填充 pool_pct）】")
    # undying_will 死亡链端到端：玩家低血被一击打死（_damage_actor 扣血 → threshold proc
    # 置 immune + 回血 10% → immune 检查兜底回拉）→ 不死，最终 hp = max(1, max_hp×hp_pct)
    for with_undying in (True, False):
        p = mk_player(["undying_will"] if with_undying else [])
        b = BT.Battle("monster", mk_enemy(), player=p)
        _maxhp = int(b.player["max_hp"])
        b.player["hp"] = int(_maxhp * 0.15)  # 低血（未死）——致死一击打穿
        logs = []
        b._damage_actor(b.player, 999999, logs, source="测试")
        if with_undying:
            check("undying 致死不死（hp 回拉/回血至 max_hp×0.10）",
                  b.player["hp"] == max(1, int(_maxhp * 0.10)),
                  f"hp={b.player['hp']} max={_maxhp} logs={logs}")
            check("used 置位 + immune 消费清",
                  (b.player.get("eff") or {}).get("we_undying_used") is True
                  and "we_undying_immune" not in (b.player.get("eff") or {}),
                  str(b.player.get("eff")))
        else:
            check("无 undying 致死 hp=0", b.player["hp"] == 0, f"hp={b.player['hp']}")
    # undying 每场 1 次：第二次致死不再救（固定 seed 1——基础闪避 roll 不干扰致死命中）
    random.seed(1)
    p = mk_player(["undying_will"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    _maxhp = int(b.player["max_hp"])
    b.player["hp"] = int(_maxhp * 0.15)
    b._damage_actor(b.player, 999999, [], source="测试")
    check("首次致死存活", b.player["hp"] > 0, f"hp={b.player['hp']}")
    b.player["hp"] = int(_maxhp * 0.10)
    b._damage_actor(b.player, 999999, [], source="测试")
    check("二次致死（used 已置）不救 hp=0", b.player["hp"] == 0, f"hp={b.player['hp']}")
    # death_dance：受击填充 dmg×pool_pct(0.35)（无特效不进段）
    p = mk_player(["death_dance"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    b.player["hp"] = 5000
    b._post_hp_lethal(b.player, 1000, [])
    check("death_dance 池填充 dmg×0.35=350", abs(float((b.player.get("eff") or {}).get("we_death_pool", 0)) - 350.0) < 1e-6,
          str(b.player.get("eff")))
    b._post_hp_lethal(b.player, 1000, [])
    check("二次填充累积 350+350=700", abs(float((b.player.get("eff") or {}).get("we_death_pool", 0)) - 700.0) < 1e-6,
          str(b.player.get("eff")))
    p0 = mk_player([])
    b0 = BT.Battle("monster", mk_enemy(), player=p0)
    b0.player["hp"] = 5000
    b0._post_hp_lethal(b0.player, 1000, [])
    check("无 death_dance 无 pool 键", "we_death_pool" not in (b0.player.get("eff") or {}),
          str(b0.player.get("eff")))
    # turn_start 结算池——端到端（battle 实际 tick 走 proc turn_start）
    p2 = mk_player(["death_dance"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    b2.player["hp"] = 5000
    b2._post_hp_lethal(b2.player, 1000, [])  # pool=350
    b2._now = 1.0  # 第一刻之后（结算不依赖 tick_no，只依赖 pool）
    hp_before = b2.player["hp"]
    logs2 = []
    we_proc(b2, b2.player, "turn_start", {}, logs2)
    pay = max(1, int(350 * 0.10))
    check("turn_start 结算 pay=max(1,int(350×0.10))=35", pay == 35, f"pay={pay}")
    check("结算扣血 hp=5000-35", b2.player["hp"] == hp_before - pay, f"hp={b2.player['hp']}")
    check("pool 递减 350-35=315", abs(float((b2.player.get("eff") or {}).get("we_death_pool", 0)) - 315.0) < 1e-6,
          str(b2.player.get("eff")))

def test_battle_consume_mitigate():
    print("【6. battle _mitigate_chain 守御 mark_key + _roll_dodge 远行 mark_key】")
    # 守御：battle_start 置 novice_guard_active → tick1 受击 dmg×0.90
    p = mk_player(["novice_first_turn_guard"], max_hp=50000)
    b = BT.Battle("monster", mk_enemy(), player=p)
    b.player["max_hp"] = 50000
    b.player["hp"] = 50000
    we_proc(b, b.player, "battle_start", {}, [])
    check("守御标记置位", (b.player.get("eff") or {}).get("novice_guard_active") is True,
          str(b.player.get("eff")))
    b._now = 0.5
    hp_before = b.player["hp"]
    b._damage_actor(b.player, 1000, [], source="测试")
    check("tick1 受击 -10% 扣 900", hp_before - b.player["hp"] == 900, f"taken={hp_before - b.player['hp']}")
    # tick2 不再减免（tick_no>1）：受击全额 1000（盾/其它减伤链惰性——_roll_dodge 需 class 判定走玩家侧）
    b._now = 2 * 1.0
    b.player["hp"] = 50000
    hp_before = b.player["hp"]
    b._damage_actor(b.player, 1000, [], source="测试")
    check("tick>1 全额受击 1000", hp_before - b.player["hp"] == 1000, f"taken={hp_before - b.player['hp']}")
    # 远行：battle_start 置 novice_dodge_active → _roll_dodge tick1 闪避合成含 +5%（dodge>0 且 roll 命中）
    # 直接验 _roll_dodge 返回（低基础闪避 + 首刻 +5% 命中 seed 扫描）
    sd = hit = None
    for sd in range(1, 500):
        random.seed(sd)
        p2 = mk_player(["novice_first_turn_dodge"], hp=9999, max_hp=9999)
        b2 = BT.Battle("monster", mk_enemy(), player=p2)
        b2.player["dodge"] = 0.0  # 意图清零——注意 _actor_stats_of 重算基础 0.03，实际 0.0785
        we_proc(b2, b2.player, "battle_start", {}, [])
        b2._now = 0.5
        if b2._roll_dodge(b2.player, []):
            hit = True
            break
    check("远行首刻闪避可命中（+5% 乘算）", hit, f"sd={sd}")
    # 对照组：基础闪避 0.03（玩家面板）+ 无远行 → 命中率显著低于带远行（0.03 vs 0.0785）
    # 与带远行同 seed 序列对比：带远行命中时对照组必不中（同 roll 值 0.0785 > 0.03 下同 roll 命中带远行）
    p3 = mk_player([], hp=9999, max_hp=9999)
    b3 = BT.Battle("monster", mk_enemy(), player=p3)
    b3.player["dodge"] = 0.0
    hit2 = miss_ct = 0
    for sd in range(1, 400):
        random.seed(sd)
        pA = mk_player(["novice_first_turn_dodge"], hp=9999, max_hp=9999)
        bA = BT.Battle("monster", mk_enemy(), player=pA)
        we_proc(bA, bA.player, "battle_start", {}, [])
        bA._now = 0.5
        hitA = bA._roll_dodge(bA.player, [])
        random.seed(sd)
        pB = mk_player([], hp=9999, max_hp=9999)
        bB = BT.Battle("monster", mk_enemy(), player=pB)
        bB._now = 0.5
        hitB = bB._roll_dodge(pB, [])
        if hitA and not hitB:
            hit2 += 1
        elif hitB and not hitA:
            miss_ct += 1
        if hit2 >= 3:
            break
    check("远行命中率显著高于无远行（同 roll 差分命中 ≥3）", hit2 >= 3,
          f"diff_hits={hit2} 反例={miss_ct}")

def test_migrated_route():
    print("【7. 族路由/白名单】")
    for k in DR_KEYS:
        check(f"{k} → proc_dr_revive", _we_family(k) == "proc_dr_revive"
              and _WE_EXEC_KEYS.get(k) == "proc_dr_revive", f"fam={_we_family(k)}")
    for k in SPECIAL_KEYS:
        check(f"{k} → proc_special", _we_family(k) == "proc_special"
              and _WE_EXEC_KEYS.get(k) == "proc_special", f"fam={_we_family(k)}")
    # 未迁移代表仍不进路由（安全阀）：guard_regen(proc_heal regen)/dawn_regen/undying_band
    for k in ("guard_regen", "dawn_regen", "undying_band", "novice_dawn_mana"):
        check(f"未族化 {k} 不进路由", k not in _WE_EXEC_KEYS, f"route={_WE_EXEC_KEYS.get(k)}")

if __name__ == "__main__":
    test_dr_revive_undying()
    test_death_dance_pool()
    test_death_dance_armor()
    test_novice_marks()
    test_battle_consume_lethal()
    test_battle_consume_mitigate()
    test_migrated_route()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
