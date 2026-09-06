# -*- coding: utf-8 -*-
"""v180-B 扩展性验收门禁：配数据的 actor 被全引擎认（P15）"""

import os, sys, random

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


def mk_player(cls="cls_zhan_shi", lv=20, qq="t1"):
    st = E.player_final_stats(cls, lv, {}, 0, None)
    return {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": {}, "attributes": None, "learned_skills": [], "qq_id": qq,
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None, "name": "玩家"}


def mk_enemy(hp=5000, role="dps"):
    return C.build_monster(("m_test", "测试怪", role, 20, [], []),
                           {"id": "m_test", "name": "测试图", "area": "field"})


def test_guard_summon_redirect():
    """召唤物带 guard 配置 → 挡刀转移承受（数据驱动，非特判）"""
    print("【1. 随从 guard 配置化挡刀（redirect）】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(), player=p)
    # 造一个带 guard 的随从实体（模拟 _summon_entity 生成结果）——def 高保证挡 100 后存活
    b.companions.append({"tid": "vine_guard", "name": "藤蔓守卫", "icon": "🌿",
                         "hp": 1000, "max_hp": 1000, "atk": 0, "def": 500,
                         "dmg_type": "phys", "rank": 1, "reach": 1, "kind": "summon",
                         "side": "player", "buffs": {},
                         "absorb_once": False, "aura_atk_all": 0, "eats_aoe": False,
                         "guard": {"chance": 1.0, "mode": "redirect", "absorb_once": False}})
    random.seed(1)
    logs = []
    dmg = b._guard_check(100, logs)  # v180E 阶段3：统一挡刀核心
    check("guard 概率命中（chance=1.0）挡下", dmg == 0, f"dmg={dmg}")
    check("随从承受伤害（hp 减少）", b.summons[0]["hp"] < 1000, str(b.summons[0]["hp"]))
    check("有挡刀日志", any("挡下" in l for l in logs), str(logs))
    # absorb_once 随从：挡 1 次消失（先移除普通随从，只剩 absorb_once 在场）
    b.companions = [c for c in b.companions if c.get("tid") != "vine_guard"]
    b.companions.append({"tid": "vine2", "name": "藤蔓守卫·吸收", "icon": "🌿",
                         "hp": 1000, "max_hp": 1000, "atk": 0, "def": 500,
                         "dmg_type": "phys", "rank": 1, "reach": 1, "kind": "summon",
                         "side": "player", "buffs": {},
                         "absorb_once": False, "aura_atk_all": 0, "eats_aoe": False,
                         "guard": {"chance": 1.0, "mode": "redirect", "absorb_once": True}})
    n_before = len(b.summons)
    random.seed(2)
    dmg2 = b._guard_check(50, [])
    check("absorb_once 挡后消失", len(b.summons) == n_before - 1, f"{len(b.summons)} vs {n_before-1}")
    check("absorb_once 挡下伤害", dmg2 == 0, f"dmg2={dmg2}")


def test_guard_absorb_pet_data():
    """宠物 block 型参战自动转配 guard（mode=absorb）→ _pet_block_check 数据化挡刀"""
    print("【2. 宠物 guard 数据化（absorb）】")
    p = mk_player()
    # 黑猫 = block 型宠物（PET_POOL skill_type='block', 25%, 3 刻）
    pet = {"qq_id": p["qq_id"], "pet_key": "pet_cat", "name": "黑猫",
           "level": 15, "exp": 0, "satiety": 100, "bond": 0, "last_sat_time": 0}
    b = BT.Battle("monster", mk_enemy(), player=p, pet=pet)
    # 开战挂卡处已调 _pet_ensure_guard → pet 应带 guard
    check("block 宠物参战带 guard", isinstance(pet.get("guard"), dict), str(pet.get("guard")))
    check("guard mode=absorb", pet["guard"].get("mode") == "absorb", str(pet["guard"]))
    check("guard chance=0.25", abs(float(pet["guard"].get("chance", 0)) - 0.25) < 0.01, str(pet["guard"]))
    # 直接触发挡刀（冷却已过——开战 _now=0 且 interval=3 → 前 3 秒冷却，推进时间）
    b._now = 4.0
    random.seed(3)
    logs = []
    dmg = b._guard_check(100, logs)  # v180E 阶段3：宠物在 companions 带 guard → 统一核心 absorb 池
    check("guard absorb 挡下（25% 概率固定种子命中）", dmg == 0, f"dmg={dmg} logs={logs}")


def test_ctrl_immune_data():
    """控制免疫数据化：任意 actor 声明 bonus_5_ctrl_immune / cc_immune 生效"""
    print("【3. 控制免疫数据化】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(), player=p)
    # 无免疫 → 不免疫
    check("无免疫配置不免疫", "slow" not in b._set_bonus_5_ctrl_immune(p), "")
    # 装备"伪霜狼套"（5 件同一系列）→ helper 返回 ["slow"]
    try:
        for slot, item in [("weapon", {"set": "霜狼", "slot": "weapon"}), ("helm", {"set": "霜狼", "slot": "helm"}),
                           ("armor", {"set": "霜狼", "slot": "armor"}), ("boots", {"set": "霜狼", "slot": "boots"}),
                           ("legs", {"set": "霜狼", "slot": "legs"})]:
            p["equipment"][slot] = item
        imm = b._set_bonus_5_ctrl_immune(p)
        check("霜狼 5 件 → 免疫 slow（数据驱动）", "slow" in imm, str(imm))
    except Exception as ex:
        check("霜狼 5 件装配", False, str(ex))


def test_class_actor_as_focus():
    """配 class_name 的随从 actor（side=player）承伤走自身容器（状态容器统一验收）"""
    print("【4. class_name actor 状态容器同构】")
    p = mk_player()
    b = BT.Battle("monster", mk_enemy(), player=p)
    # 造一个"我方随从 actor"：带 class_name + 自身 resources/buffs（像玩家的怪/宠物）
    follower = {"class_name": "cls_fa_shi", "side": "player", "name": "贤者之影",
                "hp": 300, "max_hp": 300, "mp": 100, "max_mp": 100,
                "equipment": {}, "learned_skills": [], "attributes": None,
                "buffs": {"atk_up": 3}, "resources": {"element_charge": 2},
                "stacks": {}, "eff": {}, "shields": {"test": {"value": 50, "halve": False}},
                "charging": None, "defending": False}
    # _is_focus_player: side=player → True（当焦点玩家）
    check("side=player actor 是焦点玩家", b._is_focus_player(follower), "")
    # 容器路由退化后：受击读 actor 自身 buffs（不受 Battle 玩家 buffs 影响）
    b.player["buffs"]["atk_up"] = 99  # 污染 Battle 玩家——follower 受击不应读它
    _hp0 = follower["hp"]
    logs = []
    # 直接走承伤核心（shield 50 先吸收 50，剩 30 穿透 → 扣 30）
    b._damage_actor(follower, 80, logs, source="测试")
    check("随从 actor 承伤扣血（盾吸收 50 后剩 30 穿透）", follower["hp"] == _hp0 - 30,
          f"{follower['hp']} vs {_hp0-30}")
    check("随从 actor 自身 buffs 保留", follower["buffs"].get("atk_up") == 3, str(follower["buffs"]))
    check("随从 actor 自身 resources 保留", follower["resources"].get("element_charge") == 2,
          str(follower["resources"]))


if __name__ == "__main__":
    test_guard_summon_redirect()
    test_guard_absorb_pet_data()
    test_ctrl_immune_data()
    test_class_actor_as_focus()
    print(f"\n结果: {len(FAIL)} 失败" if FAIL else "\n结果: 全部通过 ✅")
    sys.exit(1 if FAIL else 0)
