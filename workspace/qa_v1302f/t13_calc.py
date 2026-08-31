# -*- coding: utf-8 -*-
"""T13: programmatic EQ computation from data tables + phantom-number grep."""
import io, re, glob

SK = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py", encoding="utf-8").read()
BC = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/battle_config.py", encoding="utf-8").read()
CR = io.open(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/core_resources.py", encoding="utf-8").read()

MECH = dict(re.findall(r'"(\w+)":\s*([\d.]+),\s*#', BC))

def skill_block(name):
    idx = SK.find('"name": "%s"' % name)
    if idx < 0:
        return None
    lb = SK.rfind("{", 0, idx)
    depth = 0
    for i in range(lb, len(SK)):
        if SK[i] == "{": depth += 1
        elif SK[i] == "}":
            depth -= 1
            if depth == 0:
                return SK[lb:i+1]
    return None

def fields(block):
    d = {}
    for k in ["power", "res_cost", "consume_all", "cond", "aoe", "kind", "multi", "mech", "lifesteal"]:
        m = re.search(r'"%s":\s*([^,}]+)' % k, block)
        if m:
            d[k] = m.group(1).strip()
    return d

def calc(name, maxval, hold=1.0, mult=1.0, note=""):
    b = skill_block(name)
    if b is None:
        print(f"{name}: NOT FOUND"); return
    f = fields(b)
    power = float(f.get("power", 0) or 0)
    eq = power
    parts = [f"P={power}"]
    ca = f.get("consume_all")
    if ca:
        m = re.search(r'"per":\s*([\d.]+)', ca)
        per = float(m.group(1)) if m else 0
        eq = power * (1 + per * maxval)
        parts.append(f"consume_all(1+{per}x{maxval})")
    rc = f.get("res_cost")
    if rc:
        m = re.search(r'"(\w+)":\s*(\d+)', rc)
        if m:
            rk, rv = m.group(1), int(m.group(2))
            st = float(MECH.get(rk, 0))
            if st:
                eq = power * (1 + st * maxval)
                parts.append(f"res_cost {rk}(1+{st}x{maxval})")
    c = f.get("cond")
    if c and "mult" in (c or ""):
        cm = float(re.search(r'"mult":\s*([\d.]+)', c).group(1))
        eq *= cm
        parts.append(f"cond x{cm}")
    if hold != 1.0:
        eq *= hold
        parts.append(f"hold x{hold}")
    if mult != 1.0:
        eq *= mult
        parts.append(f"extra x{mult}")
    aoe = "AOE" if f.get("aoe") else ""
    print(f"{name:12s} EQ={eq:6.2f}  [{', '.join(parts)}] {aoe} {note}")

print("== 龙裔 (dragon_might max10) ==")
calc("龙脉终曲", 10, note="真伤; 实测快照 10 → x2.0 (T3)")
calc("龙焰吐息", 10, note="真伤; cond 龙力>=8; 实测 6.24 (T3)")
print("== 战士 (rage10) ==")
calc("无畏冲击", 10)
print("== 法师 (element5) ==")
calc("元素湮灭", 5)
print("== 游侠 (energy100) ==")
calc("狩猎终章", 100)
print("== 牧师 ==")
calc("神罚·圣裁", 10)
print("== 刺客 ==")
calc("终结·处刑", 5, note="cond HP<40%; 攻线 连段上限+40% 另计")
calc("暗影处刑", 5, note="cond HP<30%; 基础线")
print("== 拳师 (chi10) ==")
calc("破晓之拳", 10)
print("== 时咒 (time_sand5) ==")
calc("时停领域", 5, note="cond 满沙; 时间坍缩=1.5 全场(AOE)")
print("== 星语 (hunt_mark5) ==")
calc("流星陨落", 5, note="cond 满印; 敌3层标记易伤 x1.6 → 5.89 上限")
print("== 暗影神谕 (canticle10) ==")
calc("安魂曲", 10, note="AOE + 50%伤害吸血")
print("== 暮影 (shadow_step5) ==")
calc("终结·破影一击", 5, note="潜行乘区 x1.5 名义; T1 P0 不可达")
calc("幽影刃", 5, note="潜行乘区 x1.25 名义")
print("== 苦修 (zen10, 破势未实现) ==")
calc("撼岳·终焉", 10, note="破势 x1.1 无实现 → 实算 5.50; desc 名义 6.05")
calc("气爆", 10, note="res_cost zen5; 持有后扣")

print("\n== grep phantom numbers in game/ comments ==")
for f in glob.glob(r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/**/*.py", recursive=True):
    s = io.open(f, encoding="utf-8").read()
    for pat in ["5.07", "5.12", "5.89"]:
        for m in re.finditer(re.escape(pat), s):
            line = s[:m.start()].count("\n") + 1
            print(f"{f.split('dragonfall')[-1]}:{line} {s.splitlines()[line-1].strip()[:110]}")

print("\n== overflow_shield flags ==")
for k, v in re.findall(r'"(\w+)":\s*\{[^}]*?"overflow_shield":\s*(True|False)', CR, re.S):
    print(k, "overflow_shield=", v)

print("\n== 苦修 zen_hold & 破势 cond 复核 ==")
print("ZEN_HOLD_CFG:", re.search(r'ZEN_HOLD_CFG\s*=\s*\{[^}]*\}', BC).group(0))
print("撼岳·终焉 块含 cond? ", "cond" in (skill_block("撼岳·终焉") or ""))
print("技能块含 mech? ", "mech" in (skill_block("撼岳·终焉") or ""))