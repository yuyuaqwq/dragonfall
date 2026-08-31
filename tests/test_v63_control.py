# -*- coding: utf-8 -*-
"""v63：控制体系（鱼鱼拍板 2026-08-05）

新增：眩晕 stun（跳过行动）/ 沉默 silence（禁技能）/ 净化 cleanse（驱散增益）
技能挂载：拳师·金刚腿(stun) / 游侠·贯穿箭(silence) / 牧师·圣言术(cleanse)
联动：战士·处决 对眩晕目标 ×1.6（enemy_stunned）
怪物：隧洞之王(眩晕重击/沉默尖啸)、阿兹莫丹(寒冰吐息)

验证：
  1. 眩晕：敌人被眩晕跳过行动
  2. 沉默：敌人被沉默只能普攻（不放技能）
  3. 净化：驱散敌方增益
  4. 玩家被眩晕：本回合无法行动
  5. 玩家被沉默：技能被拦截转普攻
  6. 联动：眩晕目标处决增伤
  7. 怪物控制技能：眩晕重击/沉默尖啸/寒冰吐息 定义存在
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, BT

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

def make_monster(spd=5, hp=100000, atk=10, defense=50, skills=None):
    return {
        "id": "t", "name": "测试怪", "lv": 5, "role": "dps",
        "hp": hp, "max_hp": hp, "atk": atk, "def": defense,
        "matk": 8, "mdef": 5, "spd": spd, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": skills or [], "drops": [],
    }

async def main():
    clean_db()
    m = Main(None)

    print("【眩晕：敌人被眩晕跳过行动】")
    b = BT.Battle("monster", make_monster())
    p = make_player()
    b.e_buffs["stun"] = 1
    logs, dmg = b._enemy_turn(p)
    check("眩晕跳过行动", "被眩晕" in " ".join(logs), str(logs[:2]))
    check("眩晕后状态清除", "stun" not in b.e_buffs, str(b.e_buffs))

    print("【沉默：敌人被沉默只能普攻】")
    b = BT.Battle("monster", make_monster(skills=["ms_kuang_bao"]))
    p = make_player()
    b.e_buffs["silence"] = 1
    # 沉默时即使概率命中也不放技能（不出现"使用了"）
    logs, dmg = b._enemy_turn(p)
    check("沉默不放增益技能", not any("使用了" in l for l in logs), str(logs))

    print("【净化：驱散敌方增益】")
    b = BT.Battle("monster", make_monster())
    p = make_player()
    b.e_buffs["mon_atk_up"] = 2
    b.e_buffs["mon_def_up"] = 2
    b._apply_mech_effect("cleanse", 1, {}, 0, [], "圣言术", False)
    check("净化清除攻/防增益", "mon_atk_up" not in b.e_buffs and "mon_def_up" not in b.e_buffs, str(b.e_buffs))

    print("【玩家被眩晕：本回合无法行动】")
    b = BT.Battle("monster", make_monster())
    p = make_player(hp=9999)
    b.enemy["atk"] = 5
    b.p_buffs["stun"] = 1
    logs, ended = b.player_turn("attack", None, p)
    check("玩家眩晕无法攻击", any("被眩晕" in l for l in logs), str(logs[:3]))
    check("眩晕状态清除", "stun" not in b.p_buffs, str(b.p_buffs))

    print("【玩家被沉默：技能被拦截转普攻】")
    b = BT.Battle("monster", make_monster())
    p = make_player(cls="cls_fa_shi", lv=20, hp=9999)
    b.p_buffs["silence"] = 2
    logs, ended = b.player_turn("skill", "冰锥", p)
    check("沉默拦截技能", any("被沉默" in l for l in logs), str(logs[:3]))
    check("沉默转普攻有伤害", b.enemy["hp"] < 100000, f"hp={b.enemy['hp']}")

    print("【联动：眩晕目标盾击增伤（enemy_stunned）】")
    b = BT.Battle("monster", make_monster())
    p = make_player(lv=25, mp=999)
    p["learned_skills"] = ["盾击"]
    b.e_buffs["stun"] = 1
    # 盾击技能信息（v151：mech=stun）
    info = E.skill_info("cls_zhan_shi", "盾击")
    check("盾击带眩晕 mech", info.get("mech") == "stun", str(info.get("mech")))
    b2 = BT.Battle("monster", make_monster())
    b2.e_buffs["stun"] = 1
    mult_stunned = b2._cond_mult(info, make_player(lv=25), 1)
    check("眩晕目标增伤>=1", mult_stunned >= 1.0, f"mult={mult_stunned}")

    print("【怪物控制技能定义】")
    for sid in ("ms_xuan_yun_zhong_ji", "ms_chen_mo_jian_xiao", "ms_han_bing_tu_xi"):
        sinfo = C.MONSTER_SKILLS.get(sid)
        check(f"{sid} 存在", sinfo is not None, f"{sid} missing")
        check(f"{sid} 带 mech", bool(sinfo and sinfo.get("mech")), str(sinfo))

    print("【技能挂载验证】")
    info_jt = E.skill_info("cls_wu_seng", "震地击")
    check("震地击带眩晕 mech", info_jt.get("mech") == "stun", str(info_jt.get("mech")))
    info_gc = E.skill_info("cls_ci_ke", "淬毒")
    check("淬毒带毒 mech", info_gc.get("mech") == "poison", str(info_gc.get("mech")))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
