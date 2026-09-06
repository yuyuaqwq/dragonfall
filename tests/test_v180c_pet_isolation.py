#!/usr/bin/env python3
"""v180-C S3 随从 actor 伤害归属门禁（宠物 actor 化）。

背景（2026-09-06 鱼鱼拍板）：
- 宠物 = 不在战场显示的 actor（hidden + untargetable），进 companions
- 伤害归属：谁攻击吃谁的被动（actor 身份路由，attacker 参数）
  - 目标身上确定 debuff（猎印标记基础 +8%/层）→ 谁打都吃
  - 攻击者自身被动（自然之眼 hunt_mark_up 额外 +6%/层）→ 只有带该被动的攻击者吃
    宠物 actor 无该被动 → 宠物撕咬不吃自然之眼额外加成
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.data.pets import PET_POOL

    print("===== v180-C S3 随从 actor 伤害归属 =====\n")

    def mk_player(learned=None, hp=5000):
        p = {
            "class_name": "游侠", "level": 30, "hp": hp, "max_hp": hp,
            "mp": 100, "max_mp": 100,
            "equipment": {"weapon": {"name": "测试弓", "stats": {"atk": 500, "matk": 100},
                                     "affixes": [], "enhance": 0}},
            "attributes": {"str": 10, "int": 10},
            "learned_skills": learned or [], "race": "human",
        }
        return p

    def mk_enemy(def_=50, hp=999999):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 100, "def": def_, "mdef": 50, "spd": 10, "lv": 30}

    wolf = next(p for p in PET_POOL if p["key"] == "pet_wolf")

    def pet_bite(with_mark, player_learned):
        random.seed(42)
        p = mk_player(learned=player_learned)
        b = BT.Battle("怪物", mk_enemy(), {}, p)
        if with_mark:
            b.enemy.setdefault("debuffs", {})["hunt_mark"] = 5
        b.pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100}
        b._pet_ensure_actor()
        hp0 = b.enemy["hp"]
        logs = []
        b._companion_act(b.pet, logs)  # v180E 阶段2：宠物技能走通用执行器（auto_act）
        return hp0 - b.enemy["hp"]

    def player_atk(with_mark, player_learned):
        random.seed(7)
        p = mk_player(learned=player_learned)
        b = BT.Battle("怪物", mk_enemy(), {}, p)
        if with_mark:
            b.enemy.setdefault("debuffs", {})["hunt_mark"] = 5
        st = b._player_stats(p)
        dmg = BT.E.calc_damage(int(st["atk"] * 1.0), b._enemy_stats().get("def", 0))
        b._damage_enemy(dmg, [], attacker=p)
        return 999999 - b.enemy["hp"]

    N = 40
    def avg(fn, mark, learned):
        return sum(fn(mark, learned) for _ in range(N)) / N

    # 1. 宠物 actor 化：参战进 companions（hidden+untargetable）
    print("\n— 宠物 actor 化 —")
    p1 = mk_player()
    b1 = BT.Battle("怪物", mk_enemy(), {}, p1)
    b1.pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100}
    b1._pet_ensure_actor()
    check("宠物进 companions", any(c is b1.pet for c in b1.companions),
          f"companions={len(b1.companions)}")
    check("宠物带 side=player/kind=pet", b1.pet.get("side") == "player" and b1.pet.get("kind") == "pet",
          str({k: b1.pet.get(k) for k in ("side", "kind")}))
    check("宠物 hidden+untargetable", b1.pet.get("hidden") is True and b1.pet.get("untargetable") is True,
          str({k: b1.pet.get(k) for k in ("hidden", "untargetable")}))
    check("宠物 buffs 容器就位", isinstance(b1.pet.get("buffs"), dict), str(type(b1.pet.get("buffs"))))
    b1._pet_ensure_actor()
    check("幂等不重复加", len([c for c in b1.companions if c is b1.pet]) == 1,
          str(len([c for c in b1.companions if c is b1.pet])))

    # 2. 宠物伤害归属：不吃玩家被动额外，吃标记基础
    print("\n— 宠物伤害归属（attacker=宠物 actor）—")
    NZY = "自然之眼"
    pA = avg(pet_bite, False, [])
    pB = avg(pet_bite, True, [])
    pC = avg(pet_bite, True, [NZY])
    d_mark = (pB - pA) / pA * 100 if pA else 0
    d_nzy = (pC - pB) / pB * 100 if pB else 0
    check(f"宠物吃标记基础增伤（{d_mark:+.1f}%，应≈+40%）", d_mark > 25.0, f"mark {d_mark:+.1f}%")
    check(f"宠物不吃自然之眼额外（{d_nzy:+.1f}%，应≈0%）", abs(d_nzy) < 2.0, f"nzy {d_nzy:+.1f}%")

    # 3. 玩家对照：吃标记 + 吃自然之眼
    print("\n— 玩家对照（attacker=玩家 actor）—")
    qA = avg(player_atk, False, [])
    qB = avg(player_atk, True, [])
    qC = avg(player_atk, True, [NZY])
    d_mark_p = (qB - qA) / qA * 100 if qA else 0
    d_nzy_p = (qC - qB) / qB * 100 if qB else 0
    check(f"玩家吃标记基础（{d_mark_p:+.1f}%）", d_mark_p > 25.0, f"{d_mark_p:+.1f}%")
    check(f"玩家吃自然之眼（{d_nzy_p:+.1f}%，应>5%）", d_nzy_p > 5.0, f"{d_nzy_p:+.1f}%")

    # 4. 宠物攻击正常
    print("\n— 宠物攻击正常 —")
    p4 = mk_player()
    b4 = BT.Battle("怪物", mk_enemy(), {}, p4)
    b4.pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100}
    b4._pet_ensure_actor()
    hp4 = b4.enemy["hp"]
    logs4 = []
    b4._companion_act(b4.pet, logs4)  # v180E 阶段2：宠物技能走通用执行器
    check("宠物撕咬造成伤害", hp4 - b4.enemy["hp"] > 0, f"dealt {hp4 - b4.enemy['hp']}")

    # 5. 宠物 actor 不被 _companions_trigger 死亡清理误删（v180-C S3 bug 回归）
    print("\n— 宠物不被误删 —")
    p5 = mk_player()
    b5 = BT.Battle("怪物", mk_enemy(), {}, p5)
    b5.pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100}
    b5._pet_ensure_actor()
    check("宠物 actor 已入 companions", any(c is b5.pet for c in b5.companions),
          f"n={len(b5.companions)}")
    b5._companions_trigger("player_act", [])
    check("触发后宠物仍存活（未被死亡清理误删）", any(c is b5.pet for c in b5.companions),
          f"n={len(b5.companions)}")

    # 6. 死亡契约不牺牲宠物（只牺牲 kind=summon）
    print("\n— 死亡契约不牺牲宠物 —")
    p6 = mk_player(hp=10)
    b6 = BT.Battle("怪物", mk_enemy(), {}, p6)
    b6.pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100}
    b6._pet_ensure_actor()
    # 塞一个真召唤物
    b6._summon_entity("skeleton", mk_player(), [])
    check("宠物 + 召唤物都在", len(b6.companions) == 2, f"n={len(b6.companions)}")
    # 手动模拟死亡契约触发：致死 + 有 death_pact 被动（调 _post_hp_lethal 致死钩子）
    b6._death_pact_used = False
    try:
        p6["hp"] = -1  # 致死
        orig_pm = b6._passive_map
        b6._passive_map = lambda a: {"proc": {"death_pact": [("测试契约", {})]}}
        try:
            b6._post_hp_lethal(p6, 5, [])
        finally:
            b6._passive_map = orig_pm
    except Exception:
        pass
    check("宠物未被死亡契约牺牲", any(c is b6.pet for c in b6.companions),
          f"kind={[c.get('kind') for c in b6.companions]}")
    check("死亡契约已消耗（有召唤物可牺牲）", b6._death_pact_used is True,
          f"used={b6._death_pact_used}")

    # 7. v180E 阶段2：宠物 buff_atk/crit_up 收编 auto_act——buff 写入 owner + 强度值可序列化
    print("\n— 宠物 buff_owner 收编（v180E 阶段2）—")
    p7 = mk_player()
    b7 = BT.Battle("怪物", mk_enemy(), {}, p7)
    b7.pet = {"pet_key": "pet_thunderbird", "name": "雷羽鸟", "level": 30, "satiety": 100}
    b7._pet_ensure_actor()
    check("buff_atk 宠物翻译 auto_act(trigger=interval)",
          (b7.pet.get("auto_act") or {}).get("act", {}).get("type") == "buff_owner"
          and (b7.pet.get("auto_act") or {}).get("act", {}).get("buff") == "atk_up",
          str(b7.pet.get("auto_act")))
    logs7 = []
    r7 = b7._companion_act(b7.pet, logs7)
    check("buff_owner 执行成功", r7 and p7.get("buffs", {}).get("atk_up", 0) >= 2,
          f"r={r7} buffs={p7.get('buffs')}")
    check("buff 强度值存 owner.pet_buff_vals(可序列化)",
          abs(float((p7.get("pet_buff_vals") or {}).get("atk", 0) or 0) - 0.30) < 1e-9,
          f"vals={p7.get('pet_buff_vals')}")
    # 强度值被 _apply_buffs 消费（面板 atk ×1.30 而非 BUFF_MULT 常量 1.30 的近似）
    p7b = mk_player()
    b7b = BT.Battle("怪物", mk_enemy(), {}, p7b)
    b7b.pet = {"pet_key": "pet_thunderbird", "name": "雷羽鸟", "level": 30, "satiety": 100}
    b7b._pet_ensure_actor()
    b7b._companion_act(b7b.pet, [])
    # 换一个 crit_up 宠物验证独立键
    p7c = mk_player()
    b7c = BT.Battle("怪物", mk_enemy(), {}, p7c)
    b7c.pet = {"pet_key": "pet_panther", "name": "影豹", "level": 30, "satiety": 100}
    b7c._pet_ensure_actor()
    check("crit_up 宠物翻译 auto_act(buff=crit_up)",
          (b7c.pet.get("auto_act") or {}).get("act", {}).get("buff") == "crit_up",
          str(b7c.pet.get("auto_act")))
    logs7c = []
    r7c = b7c._companion_act(b7c.pet, logs7c)
    check("crit_up buff_owner 执行成功",
          r7c and p7c.get("buffs", {}).get("crit_up", 0) >= 2
          and abs(float((p7c.get("pet_buff_vals") or {}).get("crit", 0) or 0) - 0.20) < 1e-9,
          f"r={r7c} buffs={p7c.get('buffs')} vals={p7c.get('pet_buff_vals')}")

    print()
    print(f"===== v180-C S3 随从 actor 伤害归属: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
