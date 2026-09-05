#!/usr/bin/env python3
"""实证 v4：宠物 actor 伤害归属隔离——谁打读谁的被动。

语义（鱼鱼拍板 2026-09-06）：
- 目标身上的确定 debuff（猎印标记基础 +8%/层）→ 谁打都吃，宠物吃天经地义
- 攻击者自身被动（自然之眼 hunt_mark_up 额外 +6%/层）→ 只有带该被动的攻击者吃
  宠物 actor 无该被动 → 宠物撕咬不吃自然之眼额外加成
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

async def main():
    clean_db()
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.data.pets import PET_POOL

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
        b._pet_skill_turn(p, logs)
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

    NZY = "自然之眼"
    # 宠物（attacker=宠物 actor）
    pA = avg(pet_bite, False, [])
    pB = avg(pet_bite, True, [])
    pC = avg(pet_bite, True, [NZY])
    print(f"宠物: A(无标记)={pA:.1f}  B(标记,玩家无被动)={pB:.1f}  C(标记+玩家自然之眼)={pC:.1f}")
    print(f"  B vs A: {(pB-pA)/pA*100:+.1f}%  ← 标记基础(应≈+40%，宠物该吃)")
    print(f"  C vs B: {(pC-pB)/pB*100:+.1f}%  ← 自然之眼额外(宠物无此被动，应≈0%)")
    pet_extra_ok = abs((pC - pB) / pB * 100) < 2.0 if pB else False
    print(f"  宠物不吃自然之眼: {'✅' if pet_extra_ok else '❌'}")

    # 玩家（attacker=玩家 actor）
    qA = avg(player_atk, False, [])
    qB = avg(player_atk, True, [])
    qC = avg(player_atk, True, [NZY])
    print(f"\n玩家: A={qA:.1f}  B={qB:.1f}  C={qC:.1f}")
    print(f"  B vs A: {(qB-qA)/qA*100:+.1f}%  ← 标记基础")
    print(f"  C vs B: {(qC-qB)/qB*100:+.1f}%  ← 自然之眼额外(玩家带被动应吃到)")
    player_extra_ok = ((qC - qB) / qB * 100 > 5.0) if qB else False
    print(f"  玩家吃自然之眼: {'✅' if player_extra_ok else '❌'}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
