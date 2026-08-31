# -*- coding: utf-8 -*-
"""T13: EQ computation via module import (read-only)."""
import importlib.util, io

def load(path):
    spec = importlib.util.spec_from_file_location("df_skills", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

base = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/"
SK = load(base + "skills.py")
BC = load(base + "battle_config.py")

def find_skill(name):
    """search SK.SKILLS + class branches"""
    d = SK.SKILLS if hasattr(SK, "SKILLS") else {}
    if name in d:
        return d[name]
    # class branches: cls -> branches -> branch -> skills
    for cls, cd in getattr(SK, "CLASSES", {}).items():
        for bk, bd in cd.get("branches", {}).items():
            for bname, skills in bd.items():
                if name in (skills or {}):
                    return skills[name]
    # fallback: scan CLASS_SKILLS style
    for attr in dir(SK):
        if attr.startswith("_"):
            continue
        v = getattr(SK, attr)
        if isinstance(v, dict):
            for k, vv in v.items():
                if isinstance(vv, dict) and vv.get("name") == name:
                    return vv
                if isinstance(vv, dict):
                    for k2, vv2 in vv.items():
                        if isinstance(vv2, dict) and vv2.get("name") == name:
                            return vv2
    return None

def eq(name, maxval, extra_mult=1.0, cond_mult_override=None):
    info = find_skill(name)
    if info is None:
        print(f"{name}: NOT FOUND"); return
    power = float(info.get("power") or 0)
    mult = 1.0
    parts = [f"P={power}"]
    ca = info.get("consume_all") or {}
    if ca.get("per"):
        mult *= 1 + float(ca["per"]) * maxval
        parts.append(f"consume_all(1+{ca['per']}x{maxval})")
    rc = info.get("res_cost") or {}
    for k, v in rc.items():
        st = BC.MECH_STACK_BONUS.get(k)
        if st:
            mult *= 1 + st * maxval
            parts.append(f"res_cost {k}(1+{st}x{maxval})")
    c = info.get("cond") or {}
    if c.get("mult") is not None:
        cm = float(c["mult"]) if cond_mult_override is None else cond_mult_override
        mult *= cm
        parts.append(f"cond x{cm} ({c.get('type','?')})")
    mult *= extra_mult
    if extra_mult != 1.0:
        parts.append(f"extra x{extra_mult}")
    aoe = "AOE" if info.get("aoe") else ""
    print(f"{name:10s} EQ={power*mult:6.2f}  [{', '.join(parts)}] {aoe}")

M = BC.MECH_STACK_BONUS
print("MECH_STACK_BONUS:", M)
print()
print("== 龙裔 (dragon_might10) ==");  eq("龙脉终曲", 10); eq("龙焰吐息", 10)
print("== 战士 (rage10) ==");          eq("无畏冲击", 10)
print("== 法师 (element5) ==");        eq("元素湮灭", 5)
print("== 游侠 (energy100) ==");       eq("狩猎终章", 100)
print("== 牧师 ==");                   eq("神罚·圣裁", 10)
print("== 刺客 攻线/基础 ==");         eq("终结·处刑", 5); eq("暗影处刑", 5)
print("== 拳师 (chi10) ==");           eq("破晓之拳", 10)
print("== 时咒 (time_sand5) ==");      eq("时停领域", 5); eq("时间坍缩", 5)
print("== 星语 (hunt_mark5) ==");      eq("流星陨落", 5)
print("== 暗影神谕 ==");               eq("安魂曲", 10)
print("== 暮影 (shadow_step5) ==");    eq("终结·破影一击", 5); eq("幽影刃", 5)
print("== 苦修 (zen10) ==");           eq("撼岳·终焉", 10); eq("气爆", 10)
print("== 星语流星陨落 上下限 ==");    eq("流星陨落", 5, extra_mult=1.6)  # 敌3层标记易伤
print("== 暗夜圣典4件 安魂曲 ==");     eq("安魂曲", 10, extra_mult=1.2)
print("== 星语: 敌标记易伤机制 ==")
print("  _apply_mark: 每层+20%(battle.py:4051-4053), mark_burst 每层+20% additive(battle_mech.py:247-256)")