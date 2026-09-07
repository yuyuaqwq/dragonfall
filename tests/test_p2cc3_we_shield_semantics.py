# -*- coding: utf-8 -*-
"""v181.P2C-C3 语义门禁（proc_shield 族 10 key 迁入族执行器）。

验证（行为零变化 + 注册表契约 + 编排回路保留）：
1. 10 key family=proc_shield 且命中 C3 路由表（分发走族执行器）
2. 未迁移同族 key（battle.py 编排层直读 key 无——护盾族 10 key 全收；同 family 无残留）
3. 未族化 key（如 wind_split family=proc_extra_dmg）不进路由 → 仍走旧 handler
4. 每类触发（battle_start/taken/threshold/heal/skill_hit）真实触发且日志原文案
5. ⚠️ starlight 周期刷新回路保留：battle _tick_cooldowns 2546-2552 的
   we_starlight_next → re-proc battle_start 语义不变（新增盾 + 重写 next 标记）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import (
    WEAPON_EFFECTS, proc as we_proc, effect_data, _we_family, _WE_EXEC_KEYS,
)

SHIELD_KEYS = ["starlight_bulwark", "eclipse_crown", "sentinel_aegis", "deeprock_aegis",
               "bedrock_crown", "firmament_crown", "gargoyle_heart", "echo_bless",
               "atonement_shield", "endless_radiance"]

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": "战士", "qq_id": "t1"}

def mk_enemy(hp=100000, **kw):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    e.update(kw)
    return e

def test_routing():
    print("【1. 族路由】")
    for k in SHIELD_KEYS:
        check(f"{k} family=proc_shield 且进路由", _we_family(k) == "proc_shield"
              and k in _WE_EXEC_KEYS and _WE_EXEC_KEYS[k] == "proc_shield",
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    # 未族化 key（proc_extra_dmg 等未迁移）→ 不在路由 → 仍走旧 handler
    for k in ("wind_split", "star_pierce", "twilight_execute", "gale_step"):
        check(f"未族化 {k} 不进路由", k not in _WE_EXEC_KEYS, f"route={_WE_EXEC_KEYS.get(k)}")
    # 其他已迁族不受影响
    for k, f in (("smith_blaze_wound", "proc_dot"), ("thorn_armor", "proc_reflect"),
                 ("vital_band", "proc_heal")):
        check(f"{k} C2 族路由保留", _WE_EXEC_KEYS.get(k) == f, f"route={_WE_EXEC_KEYS.get(k)}")

def test_battle_start_trigger():
    print("【2. battle_start 触发（星辉/蚀月）】")
    p = mk_player(["starlight_bulwark"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    logs = []
    we_proc(b, p, "battle_start", {}, logs)
    check("星辉壁垒护盾生成", bool((p.get("shields") or {}).get("we_starlight")),
          str(p.get("shields")))
    check("星辉壁垒日志原文案", any("星辉壁垒" in l for l in logs), str(logs))
    check("星辉壁垒写 we_starlight_next（周期刷新回路保留）",
          float((p.get("eff") or {}).get("we_starlight_next", 0) or 0) > 0, str(p.get("eff")))
    p2 = mk_player(["eclipse_crown"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    logs2 = []
    we_proc(b2, p2, "battle_start", {}, logs2)
    check("蚀月之冠护盾生成", bool((p2.get("shields") or {}).get("we_eclipse")),
          str(p2.get("shields")))
    check("蚀月之冠写 we_eclipse_active", bool((p2.get("eff") or {}).get("we_eclipse_active")),
          str(p2.get("eff")))

def test_starlight_refresh_loop():
    print("【3. ⚠️ starlight 周期刷新回路（battle 2546-2552 re-proc）】")
    # battle._tick_cooldowns：we_starlight_next 到期 → pop → re-proc battle_start
    # （星辉壁垒重获护盾 + 重写 we_starlight_next = 下轮刷新）
    random.seed(21)
    p = mk_player(["starlight_bulwark"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    ACT = 1.0  # constants.ACT_TICK
    sh1 = (p.get("shields") or {}).get("we_starlight")
    check("初始护盾存在", bool(sh1), str(sh1))
    v1 = int(sh1["value"])
    next_at = float((p.get("eff") or {}).get("we_starlight_next", 0))
    # 模拟刻推进：把 _now 推到 we_starlight_next 到期，触发 _tick_cooldowns 重 proc
    b._now = next_at
    b._tick_cooldowns()
    sh2 = (p.get("shields") or {}).get("we_starlight")
    check("刷新后护盾重获（同源叠厚语义 _add_shield）", bool(sh2), str(sh2))
    next_at2 = float((p.get("eff") or {}).get("we_starlight_next", 0) or 0)
    check("we_starlight_next 重写（回路持续）", next_at2 >= next_at + 5 * ACT - 1e-9,
          f"next={next_at}->{next_at2}")
    # 未到期不刷新（we_starlight_next 未到 → 不 pop 不重 proc）
    b._now = next_at - 0.5
    v_before = int((p.get("shields") or {}).get("we_starlight", {}).get("value", 0))
    b._tick_cooldowns()
    check("未到期不额外触发", int((p.get("shields") or {}).get("we_starlight", {}).get("value", 0)) == v_before,
          f"v={v_before}")

def test_taken_trigger():
    print("【4. taken 概率盾（哨兵/深岩）】")
    hit = miss = None
    for sd in range(1, 300):
        random.seed(sd)
        p = mk_player(["sentinel_aegis"])
        b = BT.Battle("monster", mk_enemy(), player=p)
        lg = []
        we_proc(b, p, "taken", {"dmg": 100, "taken": 100}, lg)
        if any("哨兵壁垒" in l for l in lg):
            hit = sd
            break
    for sd in range(1, 300):
        random.seed(sd)
        p = mk_player(["sentinel_aegis"])
        b = BT.Battle("monster", mk_enemy(), player=p)
        lg = []
        we_proc(b, p, "taken", {"dmg": 100, "taken": 100}, lg)
        if not lg:
            miss = sd
            break
    check("哨兵壁垒概率触发与不触发 seed 均存在", hit is not None and miss is not None,
          f"hit={hit} miss={miss}")
    if hit is not None:
        random.seed(hit)
        p2 = mk_player(["sentinel_aegis"])
        b2 = BT.Battle("monster", mk_enemy(), player=p2)
        logs = []
        we_proc(b2, p2, "taken", {"dmg": 100, "taken": 100}, logs)
        check("哨兵壁垒触发加盾 + CD 写", bool((p2.get("shields") or {}).get("we_sentinel"))
              and float((p2.get("eff") or {}).get("we_sentinel_cd", 0) or 0) > 0,
              f"shields={p2.get('shields')} eff={p2.get('eff')} logs={logs}")
        # CD 内不重复触发
        sd_hit_again = None
        for sd2 in range(1, 300):
            random.seed(sd2)
            pp = mk_player(["sentinel_aegis"])
            bb = BT.Battle("monster", mk_enemy(), player=pp)
            # 预置 cd 未到期（now+0.5 刻内）
            (pp.setdefault("eff", {}))["we_sentinel_cd"] = bb._now + 0.5 * 1.0
            lg2 = []
            we_proc(bb, pp, "taken", {"dmg": 100, "taken": 100}, lg2)
            if not lg2:
                sd_hit_again = sd2
                break
        check("CD 内不重复触发", sd_hit_again is not None, f"sd={sd_hit_again}")

def test_threshold_trigger():
    print("【5. threshold 阈值盾（磐石/苍穹/石像鬼）】")
    # test_v140 法：init 后置低血态直接 proc
    random.seed(31)
    p = mk_player(["bedrock_crown"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    p["max_hp"] = 9999
    p["hp"] = 2000
    logs = []
    we_proc(b, p, "threshold", {"dmg": 100}, logs)
    check("磐石守护触发护盾", bool((p.get("shields") or {}).get("we_bedrock")), str(p.get("shields")))
    check("磐石守护 used 标记", (p.get("eff") or {}).get("we_bedrock_used") is True, str(p.get("eff")))
    random.seed(32)
    p2 = mk_player(["firmament_crown"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    p2["max_hp"] = 9999
    p2["hp"] = 2500
    logs2 = []
    we_proc(b2, p2, "threshold", {"dmg": 100}, logs2)
    check("苍穹庇护触发护盾", bool((p2.get("shields") or {}).get("we_firmament")), str(p2.get("shields")))
    check("苍穹庇护计数 1", (p2.get("eff") or {}).get("we_firmament_cnt") == 1, str(p2.get("eff")))
    # 石像鬼之心：盾 + 回血
    random.seed(33)
    p3 = mk_player(["gargoyle_heart"])
    b3 = BT.Battle("monster", mk_enemy(), player=p3)
    b3._now = 0
    p3["max_hp"] = 9999
    p3["hp"] = 1000
    hp_before = p3["hp"]
    logs3 = []
    we_proc(b3, p3, "threshold", {"dmg": 100}, logs3)
    check("石像鬼之心触发护盾+回血", bool((p3.get("shields") or {}).get("we_gargoyle"))
          and p3["hp"] > hp_before, f"shields={p3.get('shields')} hp={hp_before}->{p3['hp']} logs={logs3}")

def test_heal_overflow_trigger():
    print("【6. heal 溢出转盾（回响祝福/赎罪之盾）】")
    p = mk_player(["echo_bless"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    logs = []
    we_proc(b, p, "heal", {"heal": 9999, "overflow": 500, "target": {}}, logs)
    check("回响祝福溢出转盾", bool((p.get("shields") or {}).get("we_echo_bless"))
          and any("回响祝福" in l for l in logs), f"shields={p.get('shields')} logs={logs}")
    p2 = mk_player(["atonement_shield"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    logs2 = []
    we_proc(b2, p2, "heal", {"heal": 9999, "overflow": 500, "target": {}}, logs2)
    check("赎罪之盾溢出转盾 + active 标记",
          bool((p2.get("shields") or {}).get("we_atonement"))
          and (p2.get("eff") or {}).get("we_atonement_active") is True,
          f"shields={p2.get('shields')} eff={p2.get('eff')}")
    # 无溢出（治疗加成段 overflow=0）→ 不转盾（echo_bless/atonement 只在溢出段）
    p3 = mk_player(["echo_bless", "atonement_shield"])
    b3 = BT.Battle("monster", mk_enemy(), player=p3)
    we_proc(b3, p3, "heal", {"heal": 500, "overflow": 0, "target": {}}, [])
    check("无溢出不转盾", not (p3.get("shields")), str(p3.get("shields")))

def test_crit_trigger():
    print("【7. skill_hit 暴击盾（无尽辉光）】")
    p = mk_player(["endless_radiance"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    logs = []
    we_proc(b, p, "skill_hit", {"dmg": 500, "is_crit": True}, logs)
    check("无尽辉光暴击触发护盾", bool((p.get("shields") or {}).get("we_radiance"))
          and any("无尽辉光" in l for l in logs), f"shields={p.get('shields')} logs={logs}")
    # 非暴击不触发
    p2 = mk_player(["endless_radiance"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    we_proc(b2, p2, "skill_hit", {"dmg": 500, "is_crit": False}, [])
    check("非暴击不触发", not (p2.get("shields") or {}).get("we_radiance"), str(p2.get("shields")))

def test_old_handler_parity_shield_values():
    print("【8. 代表性盾值/行为与旧 handler 等价（读表数值）】")
    # sentinel：base+per_lv×lv 公式由表权威（we_data 无覆盖 → 表值 6/0.5）
    # 实际盾值随 battle 面板 level——OLD/NEW 等价（probe）已保证数值一致；此处验证公式生效（值>0）
    for sd in range(1, 200):
        random.seed(sd)
        p = mk_player(["sentinel_aegis"])
        b = BT.Battle("monster", mk_enemy(), player=p)
        lg = []
        we_proc(b, p, "taken", {"dmg": 100, "taken": 100}, lg)
        if lg:
            sh = (p.get("shields") or {}).get("we_sentinel")
            if sh:
                check(f"哨兵壁垒盾值>0 (base+per_lv×lv) (seed {sd})", sh["value"] >= 6, str(sh))
            break
    # starlight 盾 turns=3 刻（expire_at - now = 3×ACT_TICK）
    random.seed(41)
    p = mk_player(["starlight_bulwark"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    b._now = 0.0
    we_proc(b, p, "battle_start", {}, [])
    sh = (p.get("shields") or {}).get("we_starlight")
    check("星辉壁垒 3 刻", sh and abs(float(sh["expire_at"]) - 3.0) < 1e-9, str(sh))
    # eclipse 99 刻
    random.seed(42)
    p2 = mk_player(["eclipse_crown"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    b2._now = 0.0
    we_proc(b2, p2, "battle_start", {}, [])
    sh2 = (p2.get("shields") or {}).get("we_eclipse")
    check("蚀月之冠 99 刻", sh2 and abs(float(sh2["expire_at"]) - 99.0) < 1e-9, str(sh2))

if __name__ == "__main__":
    test_routing()
    test_battle_start_trigger()
    test_starlight_refresh_loop()
    test_taken_trigger()
    test_threshold_trigger()
    test_heal_overflow_trigger()
    test_crit_trigger()
    test_old_handler_parity_shield_values()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
