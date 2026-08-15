# -*- coding: utf-8 -*-
"""v116：敌方蓄力接线 + 意图预告

之前 battle.py 的敌方蓄力结算逻辑（_enemy_charge_tick/_enemy_release_charge）是僵尸代码，
敌方 _enemy_turn 从不为敌方单位写入 `charging`，导致带 charge 的怪物技能永远不触发。
本测试验证接线后：
  1. 抽中带 charge 技能 → 敌方进入蓄力（charging 写入）、本回合不结算伤害、日志含"【意图】"
  2. 下一回合蓄力完成释放：伤害 >0 且日志含"蓄力完成，轰然落下"
  3. 蓄力中被打断：charging 被清空、日志含"打断了"，后续不再释放

独立运行：python tests/test_v116_enemy_charge_telegraph.py
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, BT

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def make_player(cls="cls_zhan_shi", lv=20, hp=5000, mp=500):
    return {
        "class_name": cls, "level": lv,
        "equipment": {}, "class_tier": 0, "attributes": {"str": 0, "agi": 0, "int": 0, "vit": 0},
        "evolve_path": 0, "hp": hp, "max_hp": hp, "mp": mp, "max_mp": mp,
        "learned_skills": [], "name": "测试",
    }


def make_monster(skills=None, atk=100, matk=100):
    return {
        "id": "t", "name": "蓄力巨兽", "lv": 5, "role": "dps",
        "hp": 100000, "max_hp": 100000, "atk": atk, "def": 50,
        "matk": matk, "mdef": 5, "spd": 5, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": skills or [], "drops": [],
    }


def force_skill(skill_name):
    """接管 random：charge 判定（<MON_SKILL_CHANCE）必过 + random.choice 固定返回技能。"""
    random.random = lambda: 0.0
    random.choice = lambda _seq: skill_name


def restore_random():
    if hasattr(random, "random"):
        pass


def test_charge_start_and_release():
    print("【敌方蓄力接线：蓄力回合不结算 + 次回合释放】")
    b = BT.Battle("monster", make_monster(skills=["ms_zhen_ji"], atk=100, matk=100))
    e = b.enemy
    p = make_player(hp=99999)
    b.enemy["charging"] = None

    # 第 1 回合：抽中蓄力技能 → 进入蓄力，不结算伤害
    force_skill("ms_zhen_ji")
    try:
        logs1, dmg1 = b._enemy_turn(p)
    finally:
        restore_random()
    check("第1回合不结算伤害（dmg=0）", dmg1 == 0, f"dmg1={dmg1}")
    check("敌人进入蓄力（charging 写入）", isinstance(e.get("charging"), dict)
          and e["charging"].get("skill") == "ms_zhen_ji", str(e.get("charging")))
    check("日志含【意图】", any("【意图】" in l and "正在蓄力" in l for l in logs1), str(logs1))

    # 第 2 回合：蓄力完成释放 -> 结算伤害
    logs2, dmg2 = b._enemy_turn(p)
    check("第2回合蓄力释放造成伤害（dmg>0）", dmg2 > 0, f"dmg2={dmg2}")
    check("释放含『蓄力完成，轰然落下』", any("蓄力完成" in l for l in logs2), str(logs2))
    check("释放后 charging 清空", not e.get("charging"), str(e.get("charging")))


def test_charge_leftover_telegraph_and_interrupt():
    print("【蓄力持续回合意图 + 蓄力中被打断】")
    # 用 charge 数值更大的虚拟技能模拟多回合蓄力（直接用现成 charge:1 无法覆盖"剩N"，
    # 改为手动构造 charging 进行延续意图验证）
    b = BT.Battle("monster", make_monster(skills=["ms_jian_ta"]))
    e = b.enemy
    p = make_player(hp=99999)
    b.enemy["charging"] = {"skill": "ms_jian_ta", "left": 2, "name": "践踏"}
    logs_sub, dmg_sub = b._enemy_turn(p)
    check("蓄力持续回合（left 2→1）不结算伤害", dmg_sub == 0 and e["charging"]["left"] == 1
          and not e.get("charging", {}).get("left") == 0, f"dmg={dmg_sub} ch={e.get('charging')}")
    check("持续回合意图『蓄力中(剩N)』", any("蓄力中(剩 1" in l or "蓄力中(剩1" in l for l in logs_sub), str(logs_sub))

    # 蓄力中被打断：清空 charging，日志含打断
    b2 = BT.Battle("monster", make_monster(skills=["ms_jian_ta"]))
    p2 = make_player(hp=99999)
    b2.enemy["charging"] = {"skill": "ms_jian_ta", "left": 1, "name": "践踏"}
    clogs = []
    b2._interrupt_charging(b2.enemy, clogs, source="破空斩")
    check("打断后 charging 清空", not b2.enemy.get("charging"), str(b2.enemy.get("charging")))
    check("断开日志含『打断了』", any("打断了" in l for l in clogs), str(clogs))
    # 打断后敌方正常回合 = 重新按概率抽技能（random=0.0 必放技能，但技能不再蓄力一次？charge 技能会重新蓄力）
    force_skill("ms_jian_ta")
    try:
        logs_b, dmg_b = b2._enemy_turn(p2)
    finally:
        restore_random()
    check("打断后下回合重新进入蓄力（charge 技能再次蓄力）", isinstance(b2.enemy.get("charging"), dict)
          and any("正在蓄力" in l for l in logs_b), f"logs={str(logs_b[:3])}")


def test_charge_skill_in_monster_skills_def():
    print("【怪物蓄力技能定义存在】")
    for sid in ("ms_jian_ta", "ms_zhen_ji"):
        info = C.MONSTER_SKILLS.get(sid)
        check(f"{sid} 定义且带 charge>0", info and int(info.get("charge", 0) or 0) > 0, str(info))


async def main():
    clean_db()
    test_charge_start_and_release()
    test_charge_leftover_telegraph_and_interrupt()
    test_charge_skill_in_monster_skills_def()
    print(f"\n===== 结果：PASS {passed} / FAIL {failed} =====")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
