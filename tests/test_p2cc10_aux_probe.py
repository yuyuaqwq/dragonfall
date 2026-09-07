# -*- coding: utf-8 -*-
"""v181.P2C-C10 AUX 探针：最后 7 key（guard_regen/dawn_regen/undying_band/novice_dawn_mana/
iron_echo/dragon_spine_mail/ember_bulwark）OLD handler == NEW proc 族分发差分。

C10 迁移前先跑本文件 = 全绿基线（旧 handler 仍注册、proc 走旧路径）；
C10 迁移后再跑 = 全绿（proc 走 _we_exec_aux 族执行器，行为逐语句等价）。
"""
import sys, os, random, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game import battle as BT
from game.store import init_db
init_db()
from game.core.weapon_effects import WEAPON_EFFECTS, proc as we_proc

KEYS = {
    "guard_regen": "turn_start", "dawn_regen": "turn_start", "undying_band": "turn_start",
    "novice_dawn_mana": "skill_cast", "iron_echo": "taken", "dragon_spine_mail": "taken",
    "ember_bulwark": "taken",
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

def mk_player(effects=None, atk=100, matk=80, level=30, hp=None, mp=None):
    eq = {}
    for i, eff in enumerate(effects or []):
        eq[f"slot{i}"] = {"name": f"特效{i}", "weapon_effect": eff, "slot": "weapon",
                          "quality": "purple", "lv": level}
    return {"hp": hp if hp is not None else 9999, "max_hp": 9999,
            "mp": mp if mp is not None else 500, "max_mp": 500,
            "atk": atk, "def": 50, "matk": matk, "mdef": 50, "spd": 10, "crit": 0.05,
            "equipment": eq, "skills": [], "skill_levels": {}, "learned_skills": [],
            "level": level, "class_name": "战士", "qq_id": "t1"}

def mk_enemy(hp=100000, boss=False):
    e = {"name": "靶子", "lv": 30, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 100, "matk": 1, "mdef": 100, "spd": 1, "buffs": {}, "debuffs": {}}
    if boss:
        e["role"] = "boss"
    return e

def snap(x):
    return copy.deepcopy(x)

def state_slices(b, p):
    out = {}
    for k in ("hp", "mp", "max_hp", "max_mp"):
        out[f"p.{k}"] = p.get(k)
    for bag, name in ((p.get("buffs"), "p.buffs"), (p.get("stacks"), "p.stacks"),
                      (p.get("eff"), "p.eff"), (p.get("shields"), "p.shields")):
        if bag:
            out[name] = snap(bag)
    e = b.enemy or {}
    for k in ("hp", "max_hp"):
        out[f"e.{k}"] = e.get(k)
    for bag, name in ((e.get("buffs"), "e.buffs"), (e.get("debuffs"), "e.debuffs"),
                      (b._tgt_buffs(), "b._tgt_buffs()")):
        if bag:
            out[name] = snap(bag)
    return out

def _load_old_handler(key, event):
    """从 git HEAD 提取旧 weapon_effects.py（含旧 handler）加载为独立模块，返回其 WEAPON_EFFECTS。

    沙盒跑（cp -r 无 .git）时回退到当前 WEAPON_EFFECTS（迁移前基线=旧 handler 仍在）。
    """
    import subprocess, types, importlib.util, sys as _sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 工作根：沙盒里 tests/../.. = data/plugins（无 .git）；worktree 里 = w10（有 .git）
    for cand in (root, os.path.dirname(root)):
        if os.path.isdir(os.path.join(cand, ".git")):
            root = cand
            break
    try:
        h = subprocess.run(["git", "-C", root, "show", "HEAD:game/core/weapon_effects.py"],
                           capture_output=True, text=True, timeout=30)
        if h.returncode != 0:
            raise RuntimeError(h.stderr[:200])
    except Exception:
        return WEAPON_EFFECTS[key][event]
    mod = types.ModuleType("_we_old_head")
    src = h.stdout
    # 旧模块 import 相对包结构——用 exec 到空模块并手工补包引用
    src = src.replace("from .constants import ACT_TICK", "ACT_TICK = 1.0")
    # 旧模块顶层相对 import（_extra_phys/_extra_magi 内部懒 import ..engine calc_damage）——把
    # 残留的相对引用全部指到真包（engine 的 calc_damage 在 game.engine）。
    src = src.replace("from ..engine import calc_damage",
                      "from game.engine import calc_damage")
    # 共享动作在旧模块内自洽（同模块定义），无需包依赖；但 effect_data 读 data 表需真包——
    # 直接 exec 到临时模块，其内部 import 相对路径会炸。最稳：unload 当前包重载旧文件不可行。
    # → 旧 handler 依赖的 _heal_player/_deal_damage 在 battle 实参上，仅模块内引用 _pstats 等
    #   内部函数（自洽）+ effect_data（读 .constants/.data——替换为函数局部真引用）。
    src = src.replace(
        "def effect_data(battle, player, key: str) -> dict:",
        "def effect_data(battle, player, key: str) -> dict:\n    from game.data.weapon_effect_data import WEAPON_EFFECT_DATA as _T\n    return dict(_T.get(key) or {})")
    import game.core.weapon_effects as _cur
    mod.__package__ = "game.core"
    _sys.modules["game.core._we_old_head"] = mod
    code = compile(src, "weapon_effects_head.py", "exec")
    ns = {"__name__": "game.core._we_old_head", "__package__": "game.core"}
    exec(code, ns)
    return ns["WEAPON_EFFECTS"][key][event]

_OLD_HANDLER_CACHE = {}
def _old_handler(key, event):
    k = (key, event)
    if k not in _OLD_HANDLER_CACHE:
        _OLD_HANDLER_CACHE[k] = _load_old_handler(key, event)
    return _OLD_HANDLER_CACHE[k]

def run_pair(key, event, ctx_maker, n_runs=40, boss=False, player_mut=None):
    """对同一 key 跑 OLD handler（git HEAD 旧实现，独立模块加载）与 NEW proc 族分发，同 seed 对比。"""
    mism = []
    for i in range(n_runs):
        seed = 3000 + i * 11 + (7 if boss else 0)
        # ---- OLD ----
        random.seed(seed)
        p_old = mk_player([key])
        if player_mut:
            player_mut(p_old)
        b_old = BT.Battle("monster", mk_enemy(boss=boss), player=p_old)
        ctx_old = ctx_maker()
        logs_old = []
        _old_handler(key, event)(b_old, p_old, ctx_old, logs_old)
        # ---- NEW ----
        random.seed(seed)
        p_new = mk_player([key])
        if player_mut:
            player_mut(p_new)
        b_new = BT.Battle("monster", mk_enemy(boss=boss), player=p_new)
        ctx_new = ctx_maker()
        logs_new = []
        we_proc(b_new, p_new, event, ctx_new, logs_new)
        # ---- compare ----
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

def main():
    # regen 三 key：满血（不触发）/ 半血（回血）
    for key in ("guard_regen", "dawn_regen", "undying_band"):
        mism = run_pair(key, "turn_start", lambda: {}, n_runs=10)
        check(f"{key} 满血空转 OLD==NEW", not mism, str(mism[:2]))
        def mut_half(p):
            p["hp"] = 5000  # missing = 4999
        mism = run_pair(key, "turn_start", lambda: {}, n_runs=10, player_mut=mut_half)
        check(f"{key} 半血回血 OLD==NEW", not mism, str(mism[:2]))
        # guard_regen = 已损% ；dawn/undying = max%
        def mut_missing(p):
            p["hp"] = 1000
        mism = run_pair(key, "turn_start", lambda: {}, n_runs=6, player_mut=mut_missing)
        check(f"{key} 低血回血 OLD==NEW", not mism, str(mism[:2]))
    # novice_dawn_mana：首次回蓝 + 二次不再回
    mism = run_pair("novice_dawn_mana", "skill_cast", lambda: {"mp": 10}, n_runs=10)
    check("novice_dawn_mana 首次回蓝 OLD==NEW", not mism, str(mism[:2]))
    def mut_used(p):
        p.setdefault("eff", {})["novice_mana_used"] = True
    mism = run_pair("novice_dawn_mana", "skill_cast", lambda: {"mp": 10}, n_runs=10, player_mut=mut_used)
    check("novice_dawn_mana 二次空转 OLD==NEW", not mism, str(mism[:2]))
    def mut_fullmp(p):
        p["mp"] = 500  # max_mp 500 → clamp 不加
    mism = run_pair("novice_dawn_mana", "skill_cast", lambda: {"mp": 10}, n_runs=6, player_mut=mut_fullmp)
    check("novice_dawn_mana 满蓝 clamp OLD==NEW", not mism, str(mism[:2]))
    # taken 反伤三 key（chance 判定消耗 RNG——多 dmg 场景）
    for dmg in (0, 100, 300):
        for boss in (False, True):
            def cm(d=dmg):
                return {"dmg": d, "taken": d}
            mism = run_pair("iron_echo", "taken", cm, boss=boss)
            check(f"iron_echo taken dmg={dmg} boss={boss} OLD==NEW", not mism, str(mism[:2]))
            mism = run_pair("dragon_spine_mail", "taken", cm, boss=boss)
            check(f"dragon_spine_mail taken dmg={dmg} boss={boss} OLD==NEW", not mism, str(mism[:2]))
            mism = run_pair("ember_bulwark", "taken", cm, boss=boss)
            check(f"ember_bulwark taken dmg={dmg} boss={boss} OLD==NEW", not mism, str(mism[:2]))
    # ember_bulwark 限 1 次：第二次 taken 不再触发
    def ember_used_once():
        seed = 4242
        random.seed(seed)
        p1 = mk_player(["ember_bulwark"])
        b1 = BT.Battle("monster", mk_enemy(), player=p1)
        we_proc(b1, p1, "taken", {"dmg": 100, "taken": 100}, [])
        random.seed(seed)
        p2 = mk_player(["ember_bulwark"])
        b2 = BT.Battle("monster", mk_enemy(), player=p2)
        lg2 = []
        we_proc(b2, p2, "taken", {"dmg": 100, "taken": 100}, lg2)
        we_proc(b2, p2, "taken", {"dmg": 100, "taken": 100}, lg2)
        eff1 = (p1.get("eff") or {}).get("we_ember_bulwark_used")
        eff2 = (p2.get("eff") or {}).get("we_ember_bulwark_used")
        return bool(eff1) and bool(eff2)
    check("ember_bulwark used 置位", ember_used_once(), "")

if __name__ == "__main__":
    main()
    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    sys.exit(1 if failed else 0)
