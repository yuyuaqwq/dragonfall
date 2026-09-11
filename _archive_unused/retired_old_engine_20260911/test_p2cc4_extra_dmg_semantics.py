# -*- coding: utf-8 -*-
"""v181.P2C-C4 直伤追击族语义门禁（行为零变化单体断言）。

在 OLD-NEW 差分探针（test_p2cc4_extra_dmg_probe.py）之外，对每个代表场景做数值/副作用硬断言：
1. 族路由：11 key → _WE_EXEC_KEYS 精确路由 proc_extra_dmg（OLD=WEAPON_EFFECTS 直调旧 handler 等价）
2. afterglow_splash/spellblade_echo/annihilation_echo：skill_hit 奥术溅射（matk 通道）
3. wind_split：hit 物理追加（atk 通道）
4. phantom_barrage：hit 破防追加（无视 50% 防御）+ 第 5 击保底
5. endless_blade：skill_hit 暴击追击 + 每刻限 1
6. hunter_open/siren_fang：hit 每 N 次真伤（计数/清零）
7. star_pierce：hit 第 4 击真伤（atk×0.2 + 已损×3% cap 5%）
8. soul_eater：hit 敌当前生命 2% 伤 + 回等量
9. novice_lifesteal：hit 吸血 heal 5%（ctx.dmg 缺失用 atk）
10. 未迁移 key（iron_echo family=proc_reflect 带附赠）仍走旧 handler（安全阀）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import (
    WEAPON_EFFECTS, proc as we_proc, effect_data,
    _we_family, _WE_EXEC_KEYS,
)

EXTRA_KEYS = [
    "afterglow_splash", "spellblade_echo", "annihilation_echo",
    "wind_split", "phantom_barrage", "endless_blade",
    "hunter_open", "siren_fang", "star_pierce",
    "soul_eater", "novice_lifesteal",
]
EVENTS = {
    "afterglow_splash": "skill_hit", "spellblade_echo": "skill_hit",
    "annihilation_echo": "skill_hit", "wind_split": "hit",
    "phantom_barrage": "hit", "endless_blade": "skill_hit",
    "hunter_open": "hit", "siren_fang": "hit", "star_pierce": "hit",
    "soul_eater": "hit", "novice_lifesteal": "hit",
}

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
    p = {"hp": hp if hp is not None else 9999, "max_hp": 9999, "mp": 500, "max_mp": 500,
         "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
         "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
         "level": level, "class_name": "战士", "qq_id": "t1"}
    return p

def mk_enemy(hp=100000, max_hp=None, boss=False):
    mh = hp if max_hp is None else max_hp
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": mh,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    if boss:
        e["role"] = "boss"
    return e

def wound(p, hp):
    """Battle init 按 level 重算 max_hp → init 后显式设 max_hp/hp（C5 探针同款）。"""
    p["max_hp"] = 9999
    p["hp"] = hp
    return p

def find_trigger_seed(key, ev, ctx, mut=None, n=300):
    """找 proc 触发 seed（logs 非空 或 enemy hp 下降）。"""
    for sd in range(1, n):
        random.seed(sd)
        p = mk_player([key])
        if mut:
            mut(p)
        b = BT.Battle("monster", mk_enemy(), player=p)
        hp0 = b.enemy["hp"]
        lg = []
        we_proc(b, p, ev, dict(ctx), lg)
        if lg or b.enemy["hp"] < hp0:
            return sd
    return None

def test_route():
    print("【1. 族路由 proc_extra_dmg】")
    for k in EXTRA_KEYS:
        check(f"{k} → proc_extra_dmg", _we_family(k) == "proc_extra_dmg"
              and _WE_EXEC_KEYS.get(k) == "proc_extra_dmg",
              f"fam={_we_family(k)} route={_WE_EXEC_KEYS.get(k)}")
    # 未迁移 key：iron_echo（proc_reflect 带附赠未迁）→ 不进路由仍走旧 handler
    # v181.P2C-C10：iron_echo 已迁 proc_aux 收尾族——断言改为进路由
    check("iron_echo C10 进 proc_aux 路由", _we_family("iron_echo") == "proc_reflect"
          and _WE_EXEC_KEYS.get("iron_echo") == "proc_aux", str(_WE_EXEC_KEYS.get("iron_echo")))

def test_splash():
    print("【2. splash_magi 奥术溅射数值】")
    # spellblade_echo（无 chance 恒触发）：技能命中 → 奥术伤害 = matk×0.25 经 mdef 减伤（>0）
    random.seed(123)
    p = mk_player(["spellblade_echo"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    hp0 = b.enemy["hp"]
    we_proc(b, p, "skill_hit", {"dmg": 200, "is_crit": False}, [])
    check("spellblade_echo 触发溅射伤害", b.enemy["hp"] < hp0, f"lost={hp0 - b.enemy['hp']}")
    # afterglow_splash chance=0.30：找触发 seed 验证伤害且日志含 余波
    sd = find_trigger_seed("afterglow_splash", "skill_hit", {"dmg": 200, "is_crit": False})
    check("afterglow_splash 存在触发 seed", sd is not None, "无触发")
    if sd:
        random.seed(sd)
        p2 = mk_player(["afterglow_splash"])
        b2 = BT.Battle("monster", mk_enemy(), player=p2)
        hp0 = b2.enemy["hp"]
        lg = []
        we_proc(b2, p2, "skill_hit", {"dmg": 200}, lg)
        check("afterglow_splash 溅射 + 余波日志", b2.enemy["hp"] < hp0 and any("余波" in x for x in lg),
              f"lost={hp0 - b2.enemy['hp']} logs={lg}")
    # annihilation_echo 无触发 seed 也有（35% 概率）
    sd3 = find_trigger_seed("annihilation_echo", "skill_hit", {"dmg": 200})
    check("annihilation_echo 存在触发 seed", sd3 is not None, "无触发")

def test_wind_split():
    print("【3. wind_split 物理追加】")
    sd = find_trigger_seed("wind_split", "hit", {"dmg": 200, "is_crit": False})
    check("wind_split 存在触发 seed", sd is not None)
    if sd:
        random.seed(sd)
        p = mk_player(["wind_split"])
        b = BT.Battle("monster", mk_enemy(), player=p)
        hp0 = b.enemy["hp"]
        lg = []
        we_proc(b, p, "hit", {"dmg": 200}, lg)
        # 追加伤害 = atk×0.5 经 def（mk_player atk=100 → 面板 atk 110 ×0.5 = 55 → calc(55, def)）
        check("wind_split 物理追加日志", any("裂风矢" in x and "追加" in x for x in lg),
              f"logs={lg}")
        check("wind_split 造成伤害", b.enemy["hp"] < hp0, f"lost={hp0 - b.enemy['hp']}")

def test_phantom():
    print("【4. phantom_barrage 破防追加+保底】")
    # 保底：预置 phantom_cnt=4 → 第 5 击必触发（无视 50% 防御）
    random.seed(7)
    p = mk_player(["phantom_barrage"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    p.setdefault("stacks", {})["phantom_cnt"] = 4
    hp0 = b.enemy["hp"]
    lg = []
    we_proc(b, p, "hit", {"dmg": 200}, lg)
    check("phantom 第 5 击保底触发", b.enemy["hp"] < hp0 and any("幻影" in x for x in lg),
          f"lost={hp0 - b.enemy['hp']} logs={lg}")
    check("phantom 计数清零", (p.get("stacks") or {}).get("phantom_cnt", -1) == 0,
          str(p.get("stacks")))
    # chance 触发路径：找 seed（预置 cnt=0）
    sd = None
    for s in range(1, 200):
        random.seed(s)
        p2 = mk_player(["phantom_barrage"])
        b2 = BT.Battle("monster", mk_enemy(), player=p2)
        lg2 = []
        we_proc(b2, p2, "hit", {"dmg": 200}, lg2)
        if lg2:
            sd = s
            break
    check("phantom chance 触发 seed 存在", sd is not None)

def test_endless():
    print("【5. endless_blade 暴击追击（每刻限 1）】")
    # 暴击 → 追击 + 置 we_blade_used
    random.seed(11)
    p = mk_player(["endless_blade"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    lg = []
    we_proc(b, p, "skill_hit", {"dmg": 200, "is_crit": True}, lg)
    check("endless 暴击追击", any("无尽锋芒" in x for x in lg), f"logs={lg}")
    check("endless 置 used", bool((p.get("eff") or {}).get("we_blade_used")), str(p.get("eff")))
    # 同刻再暴击 → 不再追击
    hp0 = b.enemy["hp"]
    lg2 = []
    we_proc(b, p, "skill_hit", {"dmg": 200, "is_crit": True}, lg2)
    check("endless used 后不再追击", not lg2 and b.enemy["hp"] == hp0, f"logs={lg2}")
    # 非暴 → 不追击不置 used
    p3 = mk_player(["endless_blade"])
    b3 = BT.Battle("monster", mk_enemy(), player=p3)
    lg3 = []
    we_proc(b3, p3, "skill_hit", {"dmg": 200, "is_crit": False}, lg3)
    check("endless 非暴不追击", not lg3 and not (p3.get("eff") or {}).get("we_blade_used"),
          f"logs={lg3} eff={p3.get('eff')}")

def test_nth_true():
    print("【6. true_dmg_nth 每 N 次真伤】")
    # hunter_open count=3：连续 2 次未触发 → 第 3 次触发真伤（atk×0.12 面板≈13）
    p = mk_player(["hunter_open"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    hp0 = b.enemy["hp"]
    for _ in range(2):
        we_proc(b, p, "hit", {"dmg": 200}, [])
    check("hunter 前 2 击不触发", b.enemy["hp"] == hp0, f"lost={hp0 - b.enemy['hp']}")
    lg = []
    we_proc(b, p, "hit", {"dmg": 200}, lg)
    check("hunter 第 3 击真伤", b.enemy["hp"] < hp0 and any("破绽" in x for x in lg),
          f"lost={hp0 - b.enemy['hp']} logs={lg}")
    check("hunter 计数清零", (p.get("stacks") or {}).get("hunter_cnt", -1) == 0, str(p.get("stacks")))
    # siren_fang count=3：面板 atk 110×0.4=44 真伤
    p2 = mk_player(["siren_fang"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    hp0 = b2.enemy["hp"]
    for _ in range(3):
        we_proc(b2, p2, "hit", {"dmg": 200}, [])
    lost = hp0 - b2.enemy["hp"]
    check("siren 第 3 击真伤 44", lost >= 44, f"lost={lost}")

def test_star():
    print("【7. star_pierce 第 4 击真伤（已损加成）】")
    # 敌 9000/10000（已损 1000×3%=30；atk 110×0.2=22；cap 500）→ 52
    p = mk_player(["star_pierce"])
    b = BT.Battle("monster", mk_enemy(hp=9000, max_hp=10000), player=p)
    for _ in range(3):
        we_proc(b, p, "hit", {"dmg": 200}, [])
    hp0 = b.enemy["hp"]
    lg = []
    we_proc(b, p, "hit", {"dmg": 200}, lg)
    lost = hp0 - b.enemy["hp"]
    check("star 第 4 击真伤 52", 48 <= lost <= 56 and any("穿星" in x for x in lg),
          f"lost={lost} logs={lg}")
    check("star 计数清零", (p.get("stacks") or {}).get("star_cnt", -1) == 0, str(p.get("stacks")))

def test_soul_eater():
    print("【8. soul_eater 敌当前生命% 伤+回】")
    # 敌 50000/100000 → 2% = 1000；cap = atk 面板（mk atk=100 → 面板 110）→ bonus = min(110, 1000)=110
    p = mk_player(["soul_eater"], atk=100)
    b = BT.Battle("monster", mk_enemy(hp=50000, max_hp=100000), player=p)
    wound(p, 5000)
    hp0 = b.enemy["hp"]
    ph0 = p["hp"]
    lg = []
    we_proc(b, p, "hit", {"dmg": 200}, lg)
    lost = hp0 - b.enemy["hp"]
    healed = p["hp"] - ph0
    check("soul_eater 伤=cap atk 且回等量", lost == healed and 100 <= lost <= 115,
          f"lost={lost} healed={healed} logs={lg}")
    # 敌低血 200 → 2% = 4（>1）；cap 不影响；仍伤+回
    p2 = mk_player(["soul_eater"])
    b2 = BT.Battle("monster", mk_enemy(hp=200, max_hp=100000), player=p2)
    wound(p2, 5000)
    hp0 = b2.enemy["hp"]
    ph0 = p2["hp"]
    lg2 = []
    we_proc(b2, p2, "hit", {"dmg": 200}, lg2)
    lost2 = hp0 - b2.enemy["hp"]
    healed2 = p2["hp"] - ph0
    check("soul_eater 低血 2% 伤回", lost2 == healed2 and 3 <= lost2 <= 6,
          f"lost={lost2} healed={healed2} logs={lg2}")

def test_lifesteal():
    print("【9. novice_lifesteal 吸血】")
    # ctx.dmg=200 → heal=10
    p = mk_player(["novice_lifesteal"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    wound(p, 5000)
    ph0 = p["hp"]
    we_proc(b, p, "hit", {"dmg": 200}, [])
    healed = p["hp"] - ph0
    check("novice 吸血 heal=10", healed == 10, f"healed={healed}")
    # ctx 无 dmg → atk 面板近似（110×0.05=5）
    p2 = mk_player(["novice_lifesteal"])
    b2 = BT.Battle("monster", mk_enemy(), player=p2)
    wound(p2, 5000)
    ph0 = p2["hp"]
    we_proc(b2, p2, "hit", {"dmg": 0}, [])
    healed2 = p2["hp"] - ph0
    check("novice 无 ctx.dmg 用 atk 吸血 heal=5", healed2 == 5, f"healed={healed2}")
    # 满血 → 0（_heal_player clamp）
    p3 = mk_player(["novice_lifesteal"])
    b3 = BT.Battle("monster", mk_enemy(), player=p3)
    we_proc(b3, p3, "hit", {"dmg": 200}, [])
    check("novice 满血 heal=0", p3["hp"] == p3["max_hp"], f"hp={p3['hp']}")

def test_unmigrated_safety():
    print("【10. 未迁移 key 仍走旧 handler】")
    # iron_echo（proc_reflect 带附赠）不在路由 → taken 仍由旧 handler 反伤+回血
    random.seed(1)
    p = mk_player(["iron_echo"])
    b = BT.Battle("monster", mk_enemy(), player=p)
    hp0 = b.enemy["hp"]
    wound(p, 5000)
    ph0 = p["hp"]
    lg = []
    we_proc(b, p, "taken", {"dmg": 300, "taken": 300}, lg)
    check("iron_echo 旧 handler 反伤+回血", b.enemy["hp"] < hp0 and p["hp"] > ph0,
          f"e_lost={hp0 - b.enemy['hp']} p_gain={p['hp'] - ph0} logs={lg}")

if __name__ == "__main__":
    test_route()
    test_splash()
    test_wind_split()
    test_phantom()
    test_endless()
    test_nth_true()
    test_star()
    test_soul_eater()
    test_lifesteal()
    test_unmigrated_safety()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
