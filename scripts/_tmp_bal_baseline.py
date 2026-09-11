# -*- coding: utf-8 -*-
"""数值平衡审计——基线探针：
用游戏引擎自身函数建立 30/60/90 级玩家与怪物数值基线。
只读，不改 game/ 与 tests/。"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from battle2.formulas import calc_damage
from game.content_rules.panel import player_final_stats
from game.core import stats as S
from game.core import stats as stats_mod

def player(level, class_name="cls_wild_hunter", gear="bare"):
    eq = {}
    if gear == "gear":
        # 代表性中后期配装：主武/防具/戒指 品质 blue（mult 1.6）同等级
        eq = {
            "weapon": {"stats": S.equip_stats("weapon", level, "blue")},
            "armor": {"stats": S.equip_stats("armor", level, "blue")},
            "ring": {"stats": S.equip_stats("ring", level, "blue")},
            "helm": {"stats": S.equip_stats("helm", level, "blue")},
            "legs": {"stats": S.equip_stats("legs", level, "blue")},
            "necklace": {"stats": S.equip_stats("necklace", level, "blue")},
            "boots": {"stats": S.equip_stats("boots", level, "blue")},
        }
    # attributes：每级 +3 自由点，按攻击职业大致分配 str
    attrs = {"str": 2 * (level - 1), "vit": 1 * (level - 1), "int": 0, "agi": 0}
    st = player_final_stats(class_name, level, eq, tier=1, attributes=attrs,
                             evolve_path=0, title_bonus={}, race="human")
    return st

def monster(level, role):
    return stats_mod.monster_stats(level, role)

for lv in (30, 60, 90):
    print(f"===== Lv {lv} 玩家（毒/游侠 cls_wild_hunter） =====")
    for gear in ("bare", "gear"):
        st = player(lv, "cls_wild_hunter", gear)
        print(f"  [{gear}] hp={st['max_hp']} atk={st['atk']} matk={st['matk']} "
              f"def={st['def']} mdef={st['mdef']} spd={st['spd']}")
    print(f"===== Lv {lv} 玩家（灼烧/法师 cls_fa_shi） =====")
    for gear in ("bare", "gear"):
        st = player(lv, "cls_fa_shi", gear)
        print(f"  [{gear}] hp={st['max_hp']} atk={st['atk']} matk={st['matk']} "
              f"def={st['def']} mdef={st['mdef']} spd={st['spd']}")
    print(f"===== Lv {lv} 怪物 =====")
    for role in ("tank", "elite", "boss"):
        m = monster(lv, role)
        print(f"  [{role}] hp={m['hp']} atk={m['atk']} def={m['def']} "
              f"matk={m['matk']} mdef={m['mdef']} spd={m['spd']} dot_res={m.get('dot_res')}")

# Boss 战期望回合数参考：直伤 Boss 击杀需要 ~20-30 回合
print("\nBoss atk vs 玩家(gear) 承伤参考：")
for lv in (30, 60, 90):
    m = monster(lv, "boss")
    for cls in ("cls_wild_hunter", "cls_fa_shi"):
        st = player(lv, cls, "gear")
        # 敌人普攻伤害 calc_damage(boss_atk, player_def) ≈ boss_atk²/(boss_atk+def)
        import random
        d = calc_damage(m["atk"], st["def"], False, 0.0)
        print(f"  lv{lv} {cls} boss普攻≈{d} / 玩家hp={st['max_hp']} "
              f"(回合数容限≈{st['max_hp']//max(1,d)})")
