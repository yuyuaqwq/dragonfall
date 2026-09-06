#!/usr/bin/env python3
"""v180E 阶段6：tick actor_ref 支持 companion（宠物 actor）序列化门禁。

背景（审计2 问题3）：
- tick_effects 序列化 actor_ref 只认 "player" / enemies uid；
  宠物 actor（companions 成员，kind=pet）为 actor 的卡（pet_act）to_state 时
  actor_ref="" → from_state 恢复被丢弃 → 靠补挂兜底（节奏重置）。
- v180E 修复：actor_ref 增加 "pet" 字面量，from_state 绑 b.pet（精确恢复 next_at）。

验证：
1. pet_act 卡 to_state actor_ref="pet"
2. from_state 恢复卡 actor 绑 b.pet（同引用）
3. next_at/interval 精确保留（不重置）
4. 恢复后仅 1 张 pet_act（无双卡）
5. 老档（无序列化卡）→ 兜底补挂 1 张
"""
import sys, os
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

    print("===== v180E tick actor_ref 支持 pet（序列化） =====\n")

    def mk_player():
        return {"class_name": "战士", "level": 30, "hp": 5000, "max_hp": 5000,
                "mp": 200, "max_mp": 200, "buffs": {}, "equipment": {},
                "attributes": {}, "learned_skills": [], "race": "human"}

    def mk_enemy():
        return {"name": "测试怪", "hp": 99999, "max_hp": 99999, "atk": 100, "def": 50,
                "mdef": 50, "spd": 10, "lv": 30, "buffs": {}, "uid": "e_0"}

    # 1. 新战斗挂 pet_act 卡 → to_state actor_ref="pet"
    p = mk_player()
    pet = {"pet_key": "pet_wolf", "name": "狼崽", "level": 30, "satiety": 100}
    b = BT.Battle("monster", mk_enemy(), {}, p, pet=pet)
    b._now = 5.0
    b._reschedule_pet_tick()
    n_pet = sum(1 for x in b.tick_effects if x.get("uid") == "pet_act")
    check("新战斗挂 1 张 pet_act 卡", n_pet == 1, f"n={n_pet}")
    st = b.to_state()
    refs = [x.get("actor_ref") for x in st.get("tick_effects", []) if x.get("uid") == "pet_act"]
    check("to_state actor_ref='pet'", refs == ["pet"], f"refs={refs}")

    # 2. from_state 恢复：1 张、actor 绑 b.pet、节奏保留
    b2 = BT.Battle.from_state(st)
    pets2 = [x for x in b2.tick_effects if x.get("uid") == "pet_act"]
    check("恢复后仅 1 张 pet_act（无双卡）", len(pets2) == 1, f"n={len(pets2)}")
    check("恢复卡 actor is b2.pet（同引用）", pets2 and pets2[0].get("actor") is b2.pet,
          f"actor={pets2[0].get('actor') if pets2 else None}")
    check("next_at 精确保留（不重置）", pets2 and abs(float(pets2[0].get("next_at", -1)) - 3.0) < 1e-6,
          f"next_at={pets2[0].get('next_at') if pets2 else None}")

    # 3. 老档（tick_effects 空）→ 兜底补挂 1 张
    st3 = b.to_state()
    st3["tick_effects"] = []
    b3 = BT.Battle.from_state(st3)
    pets3 = [x for x in b3.tick_effects if x.get("uid") == "pet_act"]
    check("老档(无序列化卡)兜底补挂 1 张", len(pets3) == 1, f"n={len(pets3)}")

    # 4. 无宠物战斗 from_state 不异常（pet 空 dict 时 actor_ref 逻辑不崩）
    p4 = mk_player()
    b4 = BT.Battle("monster", mk_enemy(), {}, p4)
    b4._now = 2.0
    st4 = b4.to_state()
    b5 = BT.Battle.from_state(st4)
    check("无宠物战斗 from_state 不崩", True)

    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
