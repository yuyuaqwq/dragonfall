#!/usr/bin/env python3
"""验证：宠物 actor 在 _companions_trigger 死亡清理中是否被误删（v180-C S3 bug 复现/验证修复）。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

async def main():
    clean_db()
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.data.pets import PET_POOL

    def mk_player(hp=5000):
        return {"class_name": "游侠", "level": 30, "hp": hp, "max_hp": hp,
                "mp": 100, "max_mp": 100,
                "equipment": {"weapon": {"name": "测试弓", "stats": {"atk": 500},
                                         "affixes": [], "enhance": 0}},
                "attributes": {"str": 10, "int": 10},
                "learned_skills": [], "race": "human"}

    def mk_enemy(def_=50, hp=99999):
        return {"name": "测试怪", "hp": hp, "max_hp": hp,
                "atk": 100, "def": def_, "mdef": 50, "spd": 10, "lv": 30}

    wolf = next(p for p in PET_POOL if p["key"] == "pet_wolf")
    p = mk_player()
    b = BT.Battle("怪物", mk_enemy(), {}, p)
    b.pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100,
             "skill_type": "atk_pct", "skill_value": 0.4, "skill_interval": 3}
    b._pet_ensure_actor()
    before = [c for c in b.companions]
    print(f"宠物 actor 化后 companions: {len(before)} 个, kind={[c.get('kind') for c in before]}")
    # 模拟玩家行动后触发（真实战斗 actor_turn 尾部会调）
    logs = []
    b._companions_trigger("actor_act", logs)
    after = [c for c in b.companions]
    print(f"触发 _companions_trigger 后 companions: {len(after)} 个")
    pet_alive = any(c is b.pet for c in after)
    print(f"宠物是否存活: {'✅ 是' if pet_alive else '❌ 被误删!'}")
    print(f"日志: {logs[:3]}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
