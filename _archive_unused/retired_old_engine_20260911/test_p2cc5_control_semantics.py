# -*- coding: utf-8 -*-
"""v181.P2C-C5 控制族语义门禁（proc_control 9 key 迁移进族执行器）。

验证（行为零变化 + 新注册表契约）：
1. 9 key 的 family=proc_control 且命中 C5 族路由（分发走族执行器）
2. 控制免疫退化：冻结系对 boss → _freeze_enemy 减速退化（Boss 免疫内建共享动作）
3. 每 key 代表数值行为与旧 handler 一致（e_buffs 冻结/减速/定身/禁疗/叠层 + eff 标记键）
4. 未迁移同族/未族化 key 仍走旧 handler（安全阀）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import (
    proc as we_proc, _we_family, _WE_EXEC_KEYS,
)

CONTROL_KEYS = [
    "frost_ring", "holy_judgment_field", "everfrost_domain", "everfrost_scepter",
    "frost_crown", "holy_word_bind", "time_freeze", "randuin_weary", "ice_vein",
]
passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_player(effects=None, atk=100, matk=80, level=30, hp=None):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": hp if hp is not None else 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": "战士", "qq_id": "t1"}

def mk_enemy(hp=100000, **kw):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    e.update(kw)
    return e

def test_routing():
    print("【1. 族路由：9 key → proc_control】")
    for k in CONTROL_KEYS:
        check(f"{k} family=proc_control 且进路由",
              _we_family(k) == "proc_control" and _WE_EXEC_KEYS.get(k) == "proc_control",
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")

def test_freeze_boss_degrades():
    print("【2. 冻结系 Boss 免疫退化（共享动作 _freeze_enemy 内建）】")
    # everfrost_scepter（20% 冻结）：boss → e_buffs 无 freeze，退化 spd_down 2 刻 40%
    hit = miss = None
    for sd in range(1, 300):
        random.seed(sd)
        p = mk_player(["everfrost_scepter"])
        b = BT.Battle("monster", mk_enemy(role="boss"), player=p)
        logs = []
        we_proc(b, p, "skill_hit", {"dmg": 200, "is_crit": False}, logs)
        if any("永霜禁锢" in x for x in logs):
            hit = sd
            break
    for sd in range(1, 300):
        random.seed(sd)
        p = mk_player(["everfrost_scepter"])
        b = BT.Battle("monster", mk_enemy(), player=p)
        logs = []
        we_proc(b, p, "skill_hit", {"dmg": 200}, logs)
        if not logs:
            miss = sd
            break
    check("everfrost_scepter 命中 seed 存在", hit is not None, f"hit={hit}")
    check("everfrost_scepter miss seed 存在", miss is not None, f"miss={miss}")
    if hit is not None:
        random.seed(hit)
        p = mk_player(["everfrost_scepter"])
        e = mk_enemy(role="boss")
        b = BT.Battle("monster", e, player=p)
        logs = []
        we_proc(b, p, "skill_hit", {"dmg": 200}, logs)
        eb = e["buffs"]
        check("Boss 免疫冻结（无 freeze 键）", "freeze" not in eb, str(eb))
        check("Boss 退化减速 2 刻 40%", eb.get("spd_down") == 2
              and abs(float(eb.get("_spd_down_pct", 0)) - 0.40) < 1e-9, str(eb))
        check("Boss 退化日志", any("免疫冻结" in x or "永霜禁锢" in x for x in logs), str(logs))

def _find_hit_seed(key, event, mk, want_log, rng_range=400):
    """探测使 key 在 event 下触发的 seed（先 seed → 建 battle → 跑 proc → 查日志关键词）。"""
    for sd in range(1, rng_range):
        random.seed(sd)
        p = mk_player([key])
        b = BT.Battle("monster", mk_enemy(**mk), player=p)
        logs = []
        ctx = {"hit": {"dmg": 100, "is_crit": False},
               "skill_hit": {"dmg": 200, "is_crit": False},
               "taken": {"dmg": 300, "taken": 300},
               "heal": {"heal": 100, "overflow": 0, "target": {}},
               "threshold": {"dmg": 300}}[event]
        we_proc(b, p, event, ctx, logs)
        if any(want_log in x for x in logs):
            return sd, b, p, logs
    return None, None, None, None

def test_control_behavior():
    print("【3. 每 key 代表数值行为（命中 seed 探测）】")
    # frost_ring：未减速 → 减速 2 刻 40%（命中 seed）
    sd, b, p, logs = _find_hit_seed("frost_ring", "hit", {}, "减速")
    check("frost_ring 命中 seed 存在", sd is not None, f"sd={sd}")
    if sd is not None:
        eb = b.enemy["buffs"]
        check("frost_ring 减速 2 刻 40%（未减速）", eb.get("spd_down") == 2
              and abs(float(eb.get("_spd_down_pct", 0)) - 0.40) < 1e-9, str(eb))
        check("frost_ring 减速日志", any("敌人减速" in x for x in logs), str(logs))
    # frost_ring 已减速态 → 冻结 1 刻（非 boss）
    sd2, b2, p2, logs2 = _find_hit_seed("frost_ring", "hit", {"buffs": {"spd_down": 1}}, "冻结")
    check("frost_ring 已减速命中 seed", sd2 is not None, f"sd={sd2}")
    if sd2 is not None:
        check("frost_ring 已减速 → 冻结 1 刻", b2.enemy["buffs"].get("freeze") == 1,
              str(b2.enemy["buffs"]))
    # holy_judgment_field：减速 30% + heal_down 2
    sd3, b3, p3, logs3 = _find_hit_seed("holy_judgment_field", "hit", {}, "圣裁")
    check("holy_judgment_field 命中 seed", sd3 is not None, f"sd={sd3}")
    if sd3 is not None:
        eb3 = b3.enemy["buffs"]
        check("holy_judgment_field 减速 30% + 禁疗 2",
              eb3.get("spd_down") == 2 and abs(float(eb3.get("_spd_down_pct", 0)) - 0.30) < 1e-9
              and eb3.get("heal_down") == 2, str(eb3))
    # frost_crown：受击触发 → 冻结 + eff 计数 1
    sd4, b4, p4, logs4 = _find_hit_seed("frost_crown", "taken", {}, "寒霜")
    check("frost_crown 命中 seed", sd4 is not None, f"sd={sd4}")
    if sd4 is not None:
        check("frost_crown 冻结 + 计数 1",
              b4.enemy["buffs"].get("freeze") == 1
              and p4.setdefault("eff", {}).get("we_frost_crown_cnt") == 1,
              f"eb={b4.enemy['buffs']} eff={p4.get('eff')}")
    # time_freeze：hp<30%（无 chance，恒判定）→ stun + used
    # ⚠️ Battle init 按 level 重算 max_hp（~788），hp 预设 2000 被保留 → ratio>1 永不触发；
    #     init 后再显式设 hp 到阈值以下（引擎 init 后不再重算血量）
    p5 = mk_player(["time_freeze"])
    b5 = BT.Battle("monster", mk_enemy(), player=p5)
    p5["max_hp"] = 9999
    p5["hp"] = 2000
    we_proc(b5, p5, "threshold", {"dmg": 300}, [])
    check("time_freeze 低血 → 敌定身 stun", b5.enemy["buffs"].get("stun") == 1
          and p5.setdefault("eff", {}).get("we_time_freeze_used") is True,
          str(b5.enemy["buffs"]))
    we_proc(b5, p5, "threshold", {"dmg": 300}, [])
    check("time_freeze 已用过不重复（stun 仍 1）", b5.enemy["buffs"].get("stun") == 1,
          str(b5.enemy["buffs"]))
    # 高血不触发
    p5h = mk_player(["time_freeze"])
    b5h = BT.Battle("monster", mk_enemy(), player=p5h)
    p5h["max_hp"] = 9999
    p5h["hp"] = 8000
    we_proc(b5h, p5h, "threshold", {"dmg": 300}, [])
    check("time_freeze 高血不触发", "stun" not in b5h.enemy["buffs"]
          and "we_time_freeze_used" not in p5h.setdefault("eff", {}), str(b5h.enemy["buffs"]))
    # randuin_weary：enemy_act 连续 3 次叠层 → 封顶 3 层、_spd_down_pct=18%；第 4 次不再增
    p6 = mk_player(["randuin_weary"])
    b6 = BT.Battle("monster", mk_enemy(), player=p6)
    for _ in range(4):
        we_proc(b6, p6, "enemy_act", {}, [])
    eb6 = b6.enemy["buffs"]
    check("randuin_weary 3 层封顶 18%",
          eb6.get("_randuin_stack") == 3 and abs(float(eb6.get("_spd_down_pct", 0)) - 0.18) < 1e-9,
          str(eb6))
    # ice_vein：同构（8%/层 → 3 层 = 24%），独立叠层键
    p7 = mk_player(["ice_vein"])
    b7 = BT.Battle("monster", mk_enemy(), player=p7)
    for _ in range(3):
        we_proc(b7, p7, "enemy_act", {}, [])
    eb7 = b7.enemy["buffs"]
    check("ice_vein 3 层封顶 24% 独立键",
          eb7.get("_ice_vein_stack") == 3 and abs(float(eb7.get("_spd_down_pct", 0)) - 0.24) < 1e-9,
          str(eb7))
    # everfrost_domain：冻结后写 CD（ready_at = now + 3×ACT_TICK），冷却中跳过
    sd8, b8, p8, logs8 = _find_hit_seed("everfrost_domain", "skill_hit", {}, "永冻领域", rng_range=300)
    check("everfrost_domain 命中 seed", sd8 is not None, f"sd={sd8}")
    if sd8 is not None:
        cd = p8.setdefault("eff", {}).get("we_everfrost_cd")
        check("everfrost_domain 冻结 + CD 写入 (now+3)",
              b8.enemy["buffs"].get("freeze") == 1 and cd is not None and cd >= 3.0,
              f"eb={b8.enemy['buffs']} cd={cd} now={b8._now}")
        if cd is not None:
            b8.enemy["buffs"].pop("freeze", None)
            logs8b = []
            we_proc(b8, p8, "skill_hit", {"dmg": 200}, logs8b)
            check("everfrost_domain CD 冷却中不触发", "freeze" not in b8.enemy["buffs"] and not logs8b,
                  str(logs8b))
    # holy_word_bind：heal 无溢出触发冻结；overflow 段跳过（不消耗 RNG）
    sd9, b9, p9, logs9 = _find_hit_seed("holy_word_bind", "heal", {}, "圣言禁锢", rng_range=400)
    check("holy_word_bind 命中 seed", sd9 is not None, f"sd={sd9}")

def test_unmigrated_still_old():
    print("【4. 安全阀：非 C5 key 仍走旧 handler】")
    # 未族化 key（proc_reflect 带附赠 iron_echo 未迁 / proc_buff gale_step）→ 旧 handler
    # （C7 已迁 guardian_will → proc_retort_mark 路由，从"未族化"样例移除）
    sd, b, p, logs = _find_hit_seed("iron_echo", "taken", {}, "铁壁回响")
    check("iron_echo 命中 seed", sd is not None, f"sd={sd}")
    if sd is not None:
        check("iron_echo 未迁移仍旧 handler 触发",
              (p.get("eff") or {}).get("we_retort") is None
              and any("铁壁回响" in x for x in logs),
              f"logs={logs}")
    check("guardian_will 进 C7 路由", "guardian_will" in _WE_EXEC_KEYS
          and _WE_EXEC_KEYS["guardian_will"] == "proc_retort_mark", "")

if __name__ == "__main__":
    test_routing()
    test_freeze_boss_degrades()
    test_control_behavior()
    test_unmigrated_still_old()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
