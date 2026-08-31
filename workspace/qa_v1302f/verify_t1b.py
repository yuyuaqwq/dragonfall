# -*- coding: utf-8 -*-
"""审计 T1 补充验证：幽影刃×1.25 链路（4影步可行）在真实回合流下乘区是否可达"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(sys.path[0])))
_WD = os.path.dirname(os.path.abspath(__file__))
os.environ["GWEN_GAME_DB"] = os.path.join(_WD, "audit_t1_private.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(_WD)), "tests"))
from unittest import mock
from conftest import BT, clean_db  # noqa: E402
R = BT.random


def make_enemy(hp=200000, atk=5):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 5,
            "def": 20, "mdef": 20, "spd": 1, "crit": 0.05}


def mk_player(cls, tier, path, learned=(), level=95):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "测试勇者"}


def deterministic(fn):
    with mock.patch.object(R, "random", return_value=0.99), \
            mock.patch.object(R, "uniform", return_value=0.0):
        return fn()


clean_db()
# ---- 经济可行链路：4 影步 → 暗影步(3) → 下回合 幽影刃(3) ----
b, p = BT.Battle("monster", make_enemy(), player=mk_player("cls_shadow_blade", 3, 3,
                                                            learned=["暗影步", "幽影刃"])), None
p = b.player
b.resources["shadow_step"] = 4
logs1 = deterministic(lambda: b.player_turn("skill", "暗影步", p)[0])
print(f"[1] 暗影步施放回合后: stealth={b.p_buffs.get('stealth')!r} 影步={b.resources.get('shadow_step')}")
h = b.enemy["hp"]
logs2 = deterministic(lambda: b.player_turn("skill", "幽影刃", p)[0])
dmg = h - b.enemy["hp"]
tag = "🌙潜行x1.25" in str(logs2)
print(f"[2] 下回合 幽影刃: 伤害={dmg} 含🌙潜行x1.25标签={tag} 影步={b.resources.get('shadow_step')}")
# 对照：同回合注入潜行的幽影刃（测试文件口径）
b2, p2 = BT.Battle("monster", make_enemy(), player=mk_player("cls_shadow_blade", 3, 3,
                                                             learned=["幽影刃"])), None
p2 = b2.player
b2.resources["shadow_step"] = 4
b2.p_buffs["stealth"] = 1
h2 = b2.enemy["hp"]
logs3 = deterministic(lambda: b2._do_player_skill("幽影刃", p2))
print(f"[3] 注入潜行同回合 幽影刃: 伤害={h2 - b2.enemy['hp']} 含🌙潜行x1.25标签={'🌙潜行x1.25' in str(logs3)}")
# ---- 满血必暴对照：非潜行 幽影刃 是否必暴（满血） ----
b3, p3 = BT.Battle("monster", make_enemy(), player=mk_player("cls_shadow_blade", 3, 3,
                                                             learned=["幽影刃"])), None
p3 = b3.player
b3.resources["shadow_step"] = 4
h3 = b3.enemy["hp"]
logs4 = deterministic(lambda: b3._do_player_skill("幽影刃", p3))
print(f"[4] 非潜行满血 幽影刃: 伤害={h3 - b3.enemy['hp']} 含💥暴击标签={'💥暴击' in str(logs4)}")
clean_db()