# -*- coding: utf-8 -*-
"""v130.2f2 五项引擎修复行为验证（独立私有临时库，不改任何文件）"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tests"))
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_verify_fixes.db")
os.environ["GWEN_GAME_DB"] = _DB
os.environ.pop("GWEN_NO_SHIMMED_ASTRBOT", None)

from conftest import C, E, BT, clean_db  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def make_enemy(hp=2000, atk=40):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 40,
            "def": 20, "mdef": 20, "spd": 5, "crit": 0.05}


def mk_player(cls, tier, path, learned=(), equipment=None, level=40):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": equipment or {}, "attributes": {}, "race": None,
            "learned_skills": list(learned), "name": "测试勇者"}


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p


clean_db()

print("【① stealth 回合末豁免（暮影伏击流）】")
b, p = new_battle("cls_ci_ke", 0, 0)
b.p_buffs["stealth"] = 1
b.p_buffs["atk_up"] = 1  # 对照：普通回合 buff 正常衰减
b._end_round()
check("潜行跨回合保留（_end_round 后仍存在）", b.p_buffs.get("stealth") == 1,
      f"stealth={b.p_buffs.get('stealth')}")
check("对照：普通 buff 正常递减删除", b.p_buffs.get("atk_up") is None,
      f"atk_up={b.p_buffs.get('atk_up')}")

print("【② 资源获取渠道扩展（技能命中）】")
b, p = new_battle("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
info = {"name": "横扫", "kind": "物理"}
with mock.patch("random.random", return_value=0.99):
    b._resource_on_skill(p, info, [])
check("战争咆哮：技能命中怒气 on_skill2+1=3", int(b.resources.get("rage", 0) or 0) == 3,
      f"rage={b.resources.get('rage')}")
# 对照：无咆哮
b0, p0 = new_battle("cls_zhan_shi", 0, 0)
b0._resource_on_skill(p0, info, [])
check("对照：无咆哮 技能命中怒气=2", int(b0.resources.get("rage", 0) or 0) == 2,
      f"rage={b0.resources.get('rage')}")
# 魔力贯穿：施法命中 +1 沙
b2, p2 = new_battle("cls_chronomancer", 3, 3, learned=["魔力贯穿"])
info2 = {"name": "时间裂隙", "kind": "魔法"}
b2._resource_on_skill(p2, info2, [])
check("魔力贯穿：施法命中 time_sand=on_skill1+1=2",
      int(b2.resources.get("time_sand", 0) or 0) == 2,
      f"time_sand={b2.resources.get('time_sand')}")
# 日志反馈
logs = []
b3, p3 = new_battle("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
b3._resource_on_skill(p3, info, logs)
check("技能命中被动日志含反馈", any("技能命中" in str(l) and "战争咆哮" in str(l) for l in logs),
      f"logs={logs}")
# 终结技语义：有 res_cost 无 res_gain → 不获取（被动也不给）
b4, p4 = new_battle("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
fin = {"name": "狂怒爆发", "kind": "物理", "res_cost": {"rage": 5}}
b4.resources["rage"] = 2
import random as _r
b4._resource_on_skill(p4, fin, [])
check("终结技不获取（含被动渠道，符合消耗型语义）", int(b4.resources.get("rage", 0) or 0) == 2,
      f"rage={b4.resources.get('rage')}")

print("【③ 鹰眼 mark_extra 游侠标记路径】")
b5, p5 = new_battle("cls_you_xia", 0, 0, learned=["鹰眼", "追踪印记"])
b5._last_player = p5
logs5 = []
info5 = {"name": "林语印记", "kind": "物理", "mech": "mark", "mech_val": 1}
with mock.patch("random.random", return_value=0.0):  # 双被动必触
    b5._apply_mech_effect("mark", 1, b5.mech_stacks, 100, logs5, "林语印记", False, info5)
n = int((b5.enemy.get("debuffs") or {}).get("mark", {}).get("n", 0) or 0)
check("标记 mech=mark：基础 1 层 + 双被动额外 2 层 = 3", n == 3, f"n={n}")
check("mark_extra 日志反馈", any("额外标记 +2" in str(l) for l in logs5), f"logs={logs5}")
# 对照：无被动
b6, p6 = new_battle("cls_you_xia", 0, 0)
b6._last_player = p6
b6._apply_mech_effect("mark", 1, b6.mech_stacks, 100, [], "林语印记", False, info5)
n6 = int((b6.enemy.get("debuffs") or {}).get("mark", {}).get("n", 0) or 0)
check("对照：无被动 基础 1 层", n6 == 1, f"n={n6}")
# 非 mark mech 不触发
b7, p7 = new_battle("cls_you_xia", 0, 0, learned=["鹰眼"])
b7._last_player = p7
logs7 = []
info7 = {"name": "猎网陷阱", "kind": "物理", "mech": "burn", "mech_val": 2}
with mock.patch("random.random", return_value=0.0):
    b7._apply_mech_effect("burn", 2, b7.mech_stacks, 100, logs7, "猎网陷阱", False, info7)
check("对照：非 mark mech（burn）不消费 mark_extra", not any("额外标记" in str(l) for l in logs7),
      f"logs={logs7}")

print("【④ overflow_shield 冷却 1 回合 + 渠道统一】")
# 4a 冷却：同回合二次溢出不再转盾；_end_round 后恢复
b8, p8 = new_battle("cls_zhan_shi", 0, 0)
b8.resources["rage"] = 10
lg8 = []
b8._res_gain_class("cls_zhan_shi", "rage", 1, lg8)
sh1 = int((b8.p_shields.get("overflow_shield") or {}).get("value", 0) or 0)
cd1 = b8._overflow_shield_cd
b8._res_gain_class("cls_zhan_shi", "rage", 2, lg8)
sh2 = int((b8.p_shields.get("overflow_shield") or {}).get("value", 0) or 0)
check("第一次溢出 → 5 盾且置冷却", sh1 == 5 and cd1 is True, f"sh1={sh1} cd={cd1}")
check("同回合第二次溢出 → 盾不叠加（冷却）", sh2 == 5, f"sh2={sh2}")
check("冷却日志提示", any("冷却中" in str(l) for l in lg8), f"logs={lg8}")
b8._end_round()
check("回合末冷却重置", b8._overflow_shield_cd is False, f"cd={b8._overflow_shield_cd}")
check("回合末 1 回合盾到期（turns=1 衰减）", not b8.p_shields.get("overflow_shield"),
      f"shields={b8.p_shields}")
b8._res_gain_class("cls_zhan_shi", "rage", 1)
sh3 = int((b8.p_shields.get("overflow_shield") or {}).get("value", 0) or 0)
check("下回合可再转盾（旧盾已到期，新盾 5）", sh3 == 5, f"sh3={sh3}")
check("下回合冷却标记重新置位", b8._overflow_shield_cd is True, f"cd={b8._overflow_shield_cd}")
# 4b 词条/套装/药水渠道（_res_gain 路由）：满怒时 _res_gain +1 也转盾
b9, p9 = new_battle("cls_zhan_shi", 0, 0)
b9.resources["rage"] = 10
lg9 = []
b9._res_gain(p9, "rage", 1, lg9)
sh9 = int((b9.p_shields.get("overflow_shield") or {}).get("value", 0) or 0)
check("词条/套装渠道 _res_gain 满怒溢出 → 转盾 5", sh9 == 5, f"sh9={sh9}")
check("渠道转盾日志", any("满溢转化" in str(l) for l in lg9), f"logs={lg9}")
check("路由后上限仍封顶 10", int(b9.resources.get("rage", 0) or 0) == 10,
      f"rage={b9.resources.get('rage')}")
# 4b 受击被动 res_gain：磐石体 满气受击 → 转盾而非蒸发（转盾后盾被本次伤害立即吸收属设计内自消耗）
b10, p10 = new_battle("cls_wu_seng", 0, 0, learned=["磐石体"])
b10.resources["chi"] = 10
lg10 = []
with mock.patch("random.random", return_value=0.99), mock.patch("random.uniform", return_value=0.0):
    b10._damage_player(p10, 30, lg10, source="靶子")
sh10 = int((b10.p_shields.get("overflow_shield") or {}).get("value", 0) or 0)
conv10 = any(("护盾吸收" in str(l)) or ("满溢转化" in str(l)) for l in lg10)
check("磐石体 满气受击被动 +1 溢出 → 转盾 5（不再蒸发）", conv10 and sh10 == 0 and
      int(b10.resources.get("chi", 0) or 0) == 10,
      f"sh10={sh10} chi={b10.resources.get('chi')} logs={lg10[-4:]}")
check("满值时资源日志不误报增量", not any("受击获取" in str(l) for l in lg10), f"logs={lg10}")
# 4b 序列化：to_state/from_state 保留冷却
b11, p11 = new_battle("cls_zhan_shi", 0, 0)
b11.resources["rage"] = 10
b11._res_gain_class("cls_zhan_shi", "rage", 1)
st = b11.to_state()
b12 = BT.Battle.from_state(st)
check("序列化保持冷却标记", b12._overflow_shield_cd is True, f"cd={b12._overflow_shield_cd}")

print("【⑤ 影步 stealth_extra 时序】")
# 直接走 _on_crit_resource：标记 True 时 +1
b13, p13 = new_battle("cls_shadow_blade", 3, 3)
b13._stealth_atk = True
b13._on_crit_resource(p13)
sd_w = int(b13.resources.get("shadow_step", 0) or 0)
b14, p14 = new_battle("cls_shadow_blade", 3, 3)
b14._on_crit_resource(p14)
sd_wo = int(b14.resources.get("shadow_step", 0) or 0)
check("潜行出手标记 → 影步额外 +1", sd_w == sd_wo + 1, f"with={sd_w} without={sd_wo}")
# 攻击消费块：置位后 buff 删除、标记保留（真实出手链时序最小的模拟）
b15, p15 = new_battle("cls_shadow_blade", 3, 3)
b15.p_buffs["stealth"] = 1
import random as _r15
with mock.patch.multiple("random", random=_r15.random, uniform=lambda a, b: 0.0):
    logs15 = b15._player_skill(b15._player_stats(p15), "幽影刃",
                               E.skill_info("cls_shadow_blade", "幽影刃") or {}, p15) \
        if E.skill_info("cls_shadow_blade", "幽影刃") else []
check("攻击出手消费潜行（buff 已删）", b15.p_buffs.get("stealth") is None,
      f"stealth={b15.p_buffs.get('stealth')}")

print(f"\n===== 行为验证: {passed} passed / {failed} failed =====")
sys.exit(1 if failed else 0)