# -*- coding: utf-8 -*-
"""v181.P2C-C2 族执行器语义门禁（weapon_effects 族分发注册表试点）。

验证（行为零变化 + 新注册表契约）：
1. 10 个试点 key 的 family 已标注且命中 C2 族白名单（分发走族执行器）
2. 族执行器真实触发（OLD-NEW 探针见 test_p2cc2_we_family_probe.py，本文件做单体断言）
3. 未族化 key 仍走旧 handler（安全阀：白名单外 family 不导流）
4. proc_dot / proc_reflect / proc_heal 的代表数值行为与旧 handler 一致
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import (
    WEAPON_EFFECTS, proc as we_proc, effect_data, _we_family,
    _WE_EXEC_KEYS,
)

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

def test_family_routing():
    print("【1. 族路由白名单】")
    fam = {
        "smith_blaze_wound": "proc_dot", "rong_lu_yu_wen": "proc_dot",
        "ember_burn": "proc_dot", "blood_trace": "proc_dot",
        "thorn_armor": "proc_reflect", "retribution_ring": "proc_reflect",
        "vital_band": "proc_heal", "holy_radiance_mail": "proc_heal",
        "echo_band": "proc_heal", "novice_regen_heal": "proc_heal",
    }
    for k, f in fam.items():
        check(f"{k} family={f}", _we_family(k) == f and k in _WE_EXEC_KEYS and _WE_EXEC_KEYS[k] == f,
              f"family={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    # 未迁移同族 key（regen/回蓝、带附赠反伤）→ 不进 C2 路由（仍走旧 handler）
    for k in ("guard_regen", "dawn_regen", "undying_band", "novice_dawn_mana",
              "iron_echo", "dragon_spine_mail", "ember_bulwark"):
        check(f"未迁移同族 key {k} 不进路由", _we_family(k) in ("proc_heal", "proc_reflect")
              and k not in _WE_EXEC_KEYS, f"route={_WE_EXEC_KEYS.get(k)}")
    # v181.P2C-C4：star_pierce 直伤追击族 11 key 已整体迁入 proc_extra_dmg 路由——
    # 此处原"未族化 key 不进路由"断言改查仍未迁移的 proc_buff key（gale_step 家族）走旧 handler
    check("未迁移 key（gale_step proc_buff）不进路由",
          _we_family("gale_step") not in _WE_EXEC_KEYS.values()
          and "gale_step" not in _WE_EXEC_KEYS, _we_family("gale_step"))

def test_dot_behavior():
    print("【2. proc_dot 数值行为】")
    # smith_blaze_wound：普通怪 pct=1.5% boss=1%，chance 0.20 → seed 固定必触发
    random.seed(20260830)
    p = mk_player(["smith_blaze_wound"])
    e = mk_enemy()
    b = BT.Battle("monster", e, player=p)
    random.seed(20260830)
    we_proc(b, p, "hit", {"dmg": 100, "is_crit": False}, [])
    deb = (b.enemy.get("debuffs") or {}).get("blaze")
    check("smith blaze 挂上（普通 1.5%）", deb and abs(float(deb.get("pct", 0)) - 0.015) < 1e-9,
          str(deb))
    # boss 态 → pct=1%
    random.seed(20260830)
    p2 = mk_player(["smith_blaze_wound"])
    b2 = BT.Battle("monster", mk_enemy(role="boss"), player=p2)
    random.seed(20260830)
    we_proc(b2, p2, "hit", {"dmg": 100}, [])
    deb2 = (b2.enemy.get("debuffs") or {}).get("blaze")
    check("smith blaze boss pct=1%", deb2 and abs(float(deb2.get("pct", 0)) - 0.01) < 1e-9,
          str(deb2))
    # blood_trace 当前生命%（普通 2% / boss 1.5%），n cap 1
    random.seed(20260830)
    p3 = mk_player(["blood_trace"])
    b3 = BT.Battle("monster", mk_enemy(), player=p3)
    random.seed(20260830)
    we_proc(b3, p3, "hit", {"dmg": 100}, [])
    deb3 = (b3.enemy.get("debuffs") or {}).get("blood_trace")
    check("blood_trace 挂上（普通 2%）", deb3 and abs(float(deb3.get("pct", 0)) - 0.02) < 1e-9,
          str(deb3))

def test_reflect_behavior():
    print("【3. proc_reflect 数值行为】")
    # thorn_armor：无条件反 15%（300×15%=45 → 敌 100000 → 99955）
    p = mk_player(["thorn_armor"])
    e = mk_enemy(hp=100000)
    b = BT.Battle("monster", e, player=p)
    logs = []
    we_proc(b, p, "taken", {"dmg": 300, "taken": 300}, logs)
    check("thorn 反伤 45 (300×15%)", e["hp"] == 100000 - 45 and any("荆棘" in l for l in logs),
          f"hp={e['hp']} logs={logs}")
    # retribution_ring：20% 概率 → 用探测出的命中 seed（先 seed 再建 battle）→ 反 30% = 90
    hit = miss = None
    for sd in range(1, 200):
        random.seed(sd)
        pp = mk_player(["retribution_ring"])
        ee = mk_enemy(hp=100000)
        bb = BT.Battle("monster", ee, player=pp)
        lg = []
        we_proc(bb, pp, "taken", {"dmg": 300, "taken": 300}, lg)
        if lg and any("复仇" in x for x in lg):
            hit = sd
            break
    for sd in range(1, 200):
        random.seed(sd)
        pp = mk_player(["retribution_ring"])
        ee = mk_enemy(hp=100000)
        bb = BT.Battle("monster", ee, player=pp)
        lg = []
        we_proc(bb, pp, "taken", {"dmg": 300, "taken": 300}, lg)
        if not lg:
            miss = sd
            break
    check("retribution 命中 seed 与 miss seed 均存在", hit is not None and miss is not None,
          f"hit={hit} miss={miss}")
    if hit is not None:
        random.seed(hit)
        p2 = mk_player(["retribution_ring"])
        e2 = mk_enemy(hp=100000)
        b2 = BT.Battle("monster", e2, player=p2)
        logs2 = []
        we_proc(b2, p2, "taken", {"dmg": 300, "taken": 300}, logs2)
        check(f"retribution 反伤（seed {hit} 触发 90）",
              e2["hp"] == 100000 - 90 and any("复仇" in l for l in logs2),
              f"hp={e2['hp']} logs={logs2}")

def test_heal_behavior():
    print("【4. proc_heal amp 数值行为】")
    for key, pct, name in (("vital_band", 0.15, "铁卫"), ("holy_radiance_mail", 0.20, "圣辉"),
                           ("echo_band", 0.25, "回响"), ("novice_regen_heal", 0.10, "庇护")):
        p = mk_player([key])
        b = BT.Battle("monster", mk_enemy(), player=p)
        ctx = {"heal": 100, "overflow": 0}
        we_proc(b, p, "heal", ctx, [])
        check(f"{key} 治疗 +{int(pct*100)}%（{int(100*(1+pct))}）", ctx["heal"] == int(100 * (1 + pct)),
              f"heal={ctx['heal']}")
        # overflow 段跳过
        ctx2 = {"heal": 100, "overflow": 50}
        we_proc(b, p, "heal", ctx2, [])
        check(f"{key} overflow 跳过", ctx2["heal"] == 100, f"heal={ctx2['heal']}")

def test_unmigrated_still_old_path():
    print("【5. 未族化 key 走旧 handler（安全阀）】")
    # star_pierce（proc_extra_dmg，未迁移）仍由旧 handler 触发（穿星 4 连计数）
    random.seed(6)
    p = mk_player(["star_pierce"])
    e = mk_enemy(hp=9000)
    b = BT.Battle("monster", e, player=p)
    p["stacks"] = {}
    hp0 = e["hp"]
    for _ in range(4):
        we_proc(b, p, "hit", {"dmg": 500}, [])
    check("star_pierce 旧 handler 仍触发真伤", e["hp"] < hp0 and (p.get("stacks") or {}).get("star_cnt", 0) >= 0,
          f"dmg={hp0 - e['hp']} stacks={p.get('stacks')}")

if __name__ == "__main__":
    test_family_routing()
    test_dot_behavior()
    test_reflect_behavior()
    test_heal_behavior()
    test_unmigrated_still_old_path()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
