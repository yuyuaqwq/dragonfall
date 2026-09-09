# -*- coding: utf-8 -*-
"""v181.P2C-C5 控制族执行器 OLD vs NEW 差分探针（proc_control 9 key 全量）

策略（方案文档 §5.2 族级 OLD-NEW 差分探针，仿 test_p2cc2_we_family_probe）：
同一 battle 场景分别跑
  - OLD = 直接调 WEAPON_EFFECTS[key][event] 旧 handler（绕过 proc 分发）
  - NEW = proc() 族分发（key→proc_control→族执行器）
断言 logs / ctx / state（eff 计数/CD/used、e_buffs 控态、敌 buffs）逐字段相等。
固定 random.seed —— 概率类（chance）同 seed 下 OLD/NEW 判定一致。

构造场景（9 key × 事件/双态）：
- frost_ring(hit)：普通（减速分支）+ 已减速（冻结分支）+ boss（冻结免疫退化减速）
- holy_judgment_field(hit)：普通 boss 双态（减速+禁疗）
- everfrost_domain(skill_hit)：普通/boss + CD 冷却中（不触发）+ 冷却到期（触发）
- everfrost_scepter(skill_hit)：普通/boss
- frost_crown(taken)：普通/boss + 已达每场限次（不触发）+ 未达限次（触发计数）
- holy_word_bind(heal)：无 overflow（触发）+ overflow（跳过）
- time_freeze(threshold)：hp 低于阈值（触发定身）+ hp 高于阈值（不触发）+ 已用过
- randuin_weary/ice_vein(enemy_act)：叠 1~4 次（验证 max_stack=3 封顶 + _spd_down_pct 乘算）
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc, _we_family, _WE_EXEC_KEYS
import _c10_old_we as _OLDWE

# key → (事件, 场景构造器列表)
CONTROL_KEYS = [
    "frost_ring", "holy_judgment_field", "everfrost_domain", "everfrost_scepter",
    "frost_crown", "holy_word_bind", "time_freeze", "randuin_weary", "ice_vein",
]
EVENTS = {
    "frost_ring": "hit", "holy_judgment_field": "hit",
    "everfrost_domain": "skill_hit", "everfrost_scepter": "skill_hit",
    "frost_crown": "taken", "holy_word_bind": "heal",
    "time_freeze": "threshold", "randuin_weary": "enemy_act", "ice_vein": "enemy_act",
}

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

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

def mk_enemy(hp=100000, boss=False):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    if boss:
        e["role"] = "boss"
    return e

def state_slices(b, p):
    """采集对比用状态切片（同 C2 探针）。"""
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
                      (b._tgt_buffs(), "b._tgt_buffs()")):
        if bag:
            out[name] = copy.deepcopy(bag)
    return out

def prep_old(key, ev, maker):
    """造 OLD 场景：返回 (battle, player, ctx, logs)。不跑。"""
    p = mk_player([key])
    e = mk_enemy(boss=maker.get("boss", False))
    if maker.get("e_buffs"):
        e["buffs"].update(maker["e_buffs"])   # 预置敌方控态（已减速→冻结分支等）
    b = BT.Battle("monster", e, player=p)
    if maker.get("player_hp") is not None:
        # ⚠️ Battle init 按 level 重算 max_hp → init 后显式设血量（引擎 init 后不再重算）
        p["max_hp"] = 9999
        p["hp"] = maker["player_hp"]          # time_freeze 阈值场景
    if maker.get("pre_eff"):
        p.setdefault("eff", {}).update(maker["pre_eff"])  # 预置 CD/计数/used 态
    return b, p

def ctx_of(ev):
    return {"hit": {"dmg": 100, "is_crit": False},
            "skill_hit": {"dmg": 200, "is_crit": False, "skill": "冰刃", "kind": "冰"},
            "taken": {"dmg": 300, "taken": 300},
            "heal": {"heal": 100, "overflow": 0, "target": {}},
            "threshold": {"dmg": 500},
            "enemy_act": {}}[ev]

def run_pair(key, maker, n_runs=60, extra_ctx=None):
    """同 seed 跑 OLD（直调旧 handler）与 NEW（proc 族分发），逐字段对比。"""
    ev = EVENTS[key]
    mism = []
    for i in range(n_runs):
        seed = 5000 + i * 13 + (1 if maker.get("boss") else 0)
        # ---- OLD：直调旧 handler（= 未族化时的分发路径）----
        random.seed(seed)
        b_old, p_old = prep_old(key, ev, maker)
        logs_old = []
        handler = _OLDWE.old_handler(key, ev)
        ctx_old = dict(ctx_of(ev))
        if extra_ctx is not None:
            ctx_old.update(extra_ctx)
        handler(b_old, p_old, ctx_old, logs_old)
        # ---- NEW：proc 族分发（key 已在 _WE_EXEC_KEYS 路由表 → proc_control）----
        random.seed(seed)
        b_new, p_new = prep_old(key, ev, maker)
        logs_new = []
        ctx_new = dict(ctx_of(ev))
        if extra_ctx is not None:
            ctx_new.update(extra_ctx)
        we_proc(b_new, p_new, ev, ctx_new, logs_new)
        # ---- compare ----
        if logs_old != logs_new:
            mism.append(f"run{i}: logs OLD={logs_old} NEW={logs_new}")
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

def test_control_probe():
    # 1) frost_ring：普通（减速）/ 已减速（冻结）/ boss（冻结免疫退化减速）
    print("【1. frost_ring OLD==NEW（hit：减速/冻结/boss 退化 3 态）】")
    for maker in ({"boss": False}, {"boss": False, "e_buffs": {"spd_down": 1}},
                  {"boss": True}, {"boss": True, "e_buffs": {"spd_down": 1}}):
        mism = run_pair("frost_ring", maker)
        check(f"frost_ring OLD==NEW {maker}", not mism, str(mism[:2]))
    # 2) holy_judgment_field
    print("【2. holy_judgment_field OLD==NEW（hit：减速+禁疗，boss+普通）】")
    for maker in ({"boss": False}, {"boss": True}):
        mism = run_pair("holy_judgment_field", maker)
        check(f"holy_judgment_field OLD==NEW {maker}", not mism, str(mism[:2]))
    # 3) everfrost_domain：普通/boss + CD 态（冷却中跳过 / 到期触发）
    print("【3. everfrost_domain OLD==NEW（skill_hit：冻结/CD 冷却中/CD 到期/boss）】")
    cd_now = {"pre_eff": {"we_everfrost_cd": 50}}       # _now=0 → 冷却中
    cd_past = {"pre_eff": {"we_everfrost_cd": -5}}      # 已到期
    for maker in ({"boss": False}, {"boss": True}, cd_now, cd_past,
                  {"boss": True, **cd_now}, {"boss": True, **cd_past}):
        mism = run_pair("everfrost_domain", maker)
        check(f"everfrost_domain OLD==NEW {maker}", not mism, str(mism[:2]))
    # 4) everfrost_scepter
    print("【4. everfrost_scepter OLD==NEW（skill_hit：冻结/boss 退化）】")
    for maker in ({"boss": False}, {"boss": True}):
        mism = run_pair("everfrost_scepter", maker)
        check(f"everfrost_scepter OLD==NEW {maker}", not mism, str(mism[:2]))
    # 5) frost_crown：普通/boss + 限次态（已满不触发 / 未满触发计数）
    print("【5. frost_crown OLD==NEW（taken：冻结限次/boss）】")
    full = {"pre_eff": {"we_frost_crown_cnt": 2}}
    once = {"pre_eff": {"we_frost_crown_cnt": 1}}
    for maker in ({"boss": False}, {"boss": True}, full, once,
                  {"boss": True, **full}):
        mism = run_pair("frost_crown", maker)
        check(f"frost_crown OLD==NEW {maker}", not mism, str(mism[:2]))
    # 6) holy_word_bind：heal（无 overflow 触发 / overflow 跳过）
    print("【6. holy_word_bind OLD==NEW（heal：触发/overflow 跳过）】")
    mism = run_pair("holy_word_bind", {"boss": False})
    check("holy_word_bind OLD==NEW (heal 无溢出)", not mism, str(mism[:2]))
    mism = run_pair("holy_word_bind", {"boss": False},
                    extra_ctx={"heal": 100, "overflow": 80, "target": {}})
    check("holy_word_bind OLD==NEW (heal overflow 跳过)", not mism, str(mism[:2]))
    # 7) time_freeze：threshold（hp<30% 触发 / hp 高于阈值不触发 / 已用过）
    print("【7. time_freeze OLD==NEW（threshold：低血触发/高血不触发/已用过）】")
    for maker in ({"player_hp": 2000}, {"player_hp": 5000},
                  {"player_hp": 2000, "pre_eff": {"we_time_freeze_used": True}}):
        mism = run_pair("time_freeze", maker)
        check(f"time_freeze OLD==NEW {maker}", not mism, str(mism[:2]))
    # 8) randuin_weary / ice_vein：叠层（连续 4 次 enemy_act，验证 max_stack=3 封顶）
    print("【8. randuin_weary/ice_vein OLD==NEW（enemy_act：连续叠层封顶）】")
    for key in ("randuin_weary", "ice_vein"):
        for boss in (False, True):
            for n_pre in (0, 2, 3):
                maker = {"boss": boss,
                         "e_buffs": {("_randuin_stack" if key == "randuin_weary" else "_ice_vein_stack"): n_pre}}
                mism = run_pair(key, maker, n_runs=20)
                check(f"{key} OLD==NEW (boss={boss} pre={n_pre})", not mism, str(mism[:2]))

if __name__ == "__main__":
    # 前置：9 key 已族化 proc_control 且进路由
    for k in CONTROL_KEYS:
        assert _we_family(k) == "proc_control", f"{k} 缺 family=proc_control"
    from game.core.weapon_effects import _WE_EXEC_KEYS
    for k in CONTROL_KEYS:
        assert _WE_EXEC_KEYS.get(k) == "proc_control", f"{k} 未进 C5 路由"
    test_control_probe()
    print(f"\n结果: {passed} 通过, 0 失败")
