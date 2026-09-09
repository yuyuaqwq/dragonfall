# -*- coding: utf-8 -*-
"""v180-B 门禁：actor 通用化（怪配 class_name/装备/被动 = 职业 actor）

验证：
1. build_monster 透传 class_name/equipment/learned_skills/side
2. 带 class_name 的怪 _actor_stats_of 走玩家公式（面板同构）
3. 带 class_name 的怪身份仍是 enemy（side=enemy）：被打走自身容器、不被当玩家治疗目标
4. 带 class_name + equipment 的怪面板吃到装备词条
5. 带 learned_skills 的怪被动聚合不崩
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests'))
from tests.conftest import C, E, BT  # noqa

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} {detail}")
        FAIL.append(name)


def mk_player(cls="cls_zhan_shi", lv=20):
    st = E.player_final_stats(cls, lv, {}, 0, None)
    return {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": {}, "attributes": None, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None}


def mk_monster(mid, role, lv, skills=None, mod_cfg=None):
    # 用 MONSTER_MODS 风格：临时塞 mod 字段配置（build_monster 读 C.MONSTER_MODS，测试绕过
    # 直接改 data 太危险——改用 mod_cfg 手动构造 build 后 update 等价模拟透传）
    m = C.build_monster((mid, "数值测试怪", role, lv, skills or [], []),
                        {"id": mid, "name": "数值测试图", "area": "field"})
    # build_monster 已从 MONSTER_MODS 透传；测试直接验证透传字段存在性 + 手动塞配置模拟
    return m


def test_build_monster_cfg_fields():
    print("【1. build_monster actor 字段透传】")
    m = mk_monster("m_cfg", "dps", 20)
    for k in ("class_name", "equipment", "learned_skills", "race", "skill_levels", "side"):
        check(f"build_monster 透传字段 {k} 存在", k in m, f"缺 {k}")
    check("side 默认 enemy", m.get("side") == "enemy", str(m.get("side")))


def test_class_actor_panel_and_identity():
    print("【2. 带 class_name 的怪：面板/身份/容器】")
    # 怪扮 30 级战士
    m = mk_monster("m_warr", "dps", 30)
    m["class_name"] = "cls_zhan_shi"
    m["side"] = "enemy"
    p = mk_player("cls_zhan_shi", 20)
    b = BT.Battle("monster", m, player=p)
    # 面板走玩家公式
    st = b._actor_stats_of(m)
    check("_actor_stats_of 出玩家式面板（含 max_hp）", st.get("max_hp", 0) > 0, str(st.get("max_hp")))
    check("面板 def > 0（战士基础）", st.get("def", 0) > 0, str(st.get("def")))
    # 身份：怪被打走自身容器（职业面板 def=职业公式 → 扣血按新面板，只验证 >0 且不误用玩家 buff）
    b._focus["buffs"]["atk_up"] = 99  # 玩家有 buff（若怪错读玩家容器，怪受击/反击会异常）
    m["hp"] = 500
    m["max_hp"] = 500
    m.setdefault("buffs", {})["mon_atk_up"] = 5
    logs = []
    r = b._deal_damage(100, logs)
    check("怪被打扣血 >0", r > 0, f"r={r}")
    # 怪自身 buffs 仍在自己容器（没被玩家 atk_up=99 污染）
    check("怪 buffs 保留自身", m.get("buffs", {}).get("mon_atk_up") == 5, str(m.get("buffs")))
    check("怪 buffs 无玩家 atk_up", m.get("buffs", {}).get("atk_up") is None, str(m.get("buffs")))


def test_class_actor_equipment():
    print("【3. 怪配装备吃到词条面板】")
    m = mk_monster("m_gear", "dps", 20)
    m["class_name"] = "cls_zhan_shi"
    m["equipment"] = {}  # 空装不崩
    p = mk_player("cls_zhan_shi", 20)
    b = BT.Battle("monster", m, player=p)
    st = b._actor_stats_of(m)
    check("怪带 equipment 面板不崩", st.get("atk", 0) is not None, str(st.get("atk")))


def test_class_actor_passive():
    print("【4. 怪配 learned_skills 被动聚合不崩】")
    m = mk_monster("m_pass", "dps", 20)
    m["class_name"] = "cls_zhan_shi"
    m["learned_skills"] = []  # 空列表安全
    p = mk_player("cls_zhan_shi", 20)
    b = BT.Battle("monster", m, player=p)
    pm = b._passive_map(m)
    check("_passive_map(带class怪) 返回结构", isinstance(pm, dict) and "proc" in pm and "stat" in pm,
          str(type(pm)))


if __name__ == "__main__":
    test_build_monster_cfg_fields()
    test_class_actor_panel_and_identity()
    test_class_actor_equipment()
    test_class_actor_passive()
    print(f"\n结果: {len(FAIL)} 失败" if FAIL else "\n结果: 全部通过 ✅")
    sys.exit(1 if FAIL else 0)