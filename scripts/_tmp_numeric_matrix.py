# -*- coding: utf-8 -*-
"""临时脚本：拉取当前数值方阵全貌（供聊天展示）"""
import sys, json
sys.path.insert(0, 'C:/Users/yuyu/qqbot/data/plugins/dragonfall')

def fmt_row(d): return " | ".join(f"{k}={v}" for k, v in d.items())

# 1. 职业模板
from game.data.classes import CLASSES
print("===== CLASSES =====")
for cid, c in CLASSES.items():
    base = c.get("base", c.get("base_stats", {}))
    growth = c.get("growth", c.get("growth_stats", {}))
    print(f"{cid} | {c.get('name','?')} | tier={c.get('tier','?')} | base[{fmt_row(base)}] | growth[{fmt_row(growth)}]")

# 2. 怪物曲线
from game.core.stats import hp_stage_mult, atk_stage_mult, exp_to_next, monster_exp, monster_gold, monster_stats
print("\n===== EXP_NEEDED =====")
for lv in (1, 10, 30, 60, 90, 100):
    print(f"lv{lv}->{lv+1}: {exp_to_next(lv)}  exp")
print("\n===== STAGE_MULT =====")
for lv in (10, 30, 60, 90, 100):
    print(f"lv{lv}: hp_stage={hp_stage_mult(lv)} atk_stage={atk_stage_mult(lv)}")

# 3. 怪物成长数值（1/30/60/100 级）
from game.data.stat_templates import MONSTER_ROLE_BASE, MONSTER_ROLE_GROWTH, MONSTER_EXP_BASE, MONSTER_GOLD_BASE, FIELD_TIER_MULT
print("\n===== MONSTER 1级/100级 =====")
for role in ("tank", "dps", "caster", "speedster", "healer", "elite", "boss"):
    b = MONSTER_ROLE_BASE[role]; g = MONSTER_ROLE_GROWTH[role]
    s1 = monster_stats(1, role); s100 = monster_stats(100, role)
    print(f"{role}: lv1 hp={s1['hp']} atk={s1['atk']} def={s1['def']} | lv100 hp={s100['hp']} atk={s100['atk']} def={s100['def']} | exp_base={MONSTER_EXP_BASE[role]} gold_base={MONSTER_GOLD_BASE[role]}")

print("\n===== FIELD_TIER_MULT =====")
print(json.dumps(FIELD_TIER_MULT, ensure_ascii=False))

# 4. 危险事件（撞怪率）
import re
world_src = open('C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/world.py', encoding='utf-8').read()
for m in re.finditer(r'.*(encounter_rate|撞怪|危险|越高|0\.25|0\.30|0\.60).*', world_src):
    line = m.group(0).strip()
    if any(k in line for k in ('0.25', '0.30', '0.60', '遇敌')) and '#' in line:
        print(f"world.py: {line[:120]}")

# 5. 住宿费
import re
inn_found = []
for fp in ('C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/economy.py',
           'C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/commands_*.py'):
    try:
        src = open(fp, encoding='utf-8').read()
    except Exception:
        continue
    for m in re.finditer(r'.*(inn|住宿|INN).*(cost|fee|费|gold).*', src):
        line = m.group(0).strip()
        if len(line) < 160:
            inn_found.append(f"{fp.split('/')[-1]}: {line}")
print("\n===== INN 住宿 =====")
for l in inn_found[:12]:
    print(l)