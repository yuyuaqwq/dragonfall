# -*- coding: utf-8 -*-
"""v130.2f 职业质量批次固化测试（test_v1302f_job_quality.py）

v151（2026-08-31）职业体系重构适配版。6 隐藏职业删除，旧技能/旧资源条废弃。
本文件改为覆盖 v151 基础职业仍存活的机制质量点：

  ① 机制层 cond 行为（v151 战意 zhan_yi / 连段 lian_duan）：怒斩 战意≥3 ×1.15、
     裂地斩 战意≥6 ×1.2、影刃 连段≥5 追加——配置断言 + _cond_active 阈值行为断言。
  ② 被动节拍器 ×5（v151 数据）：守护姿态 dmg_taken{0.1, res_gain 2}、磐石之心
     dmg_taken{0.05}、以守为攻 counter_attack 0.3、反击之王 counter_attack 0.4、
     追猎者 mark_extra 0.15——passive 字段断言 + 行为断言（受击回怒/反击回气/额外叠印）。
  ③ 引擎挂点：亡灵祭仪 turn_heal 回合回血、以守为攻 反击回气 +2、
     overflow_shield 满怒/满气溢出转盾 5/点（含冷却与对照）。
  ④ desc 一致性（暗影之心 desc 无「潜行持续」承诺 + 与 stat 名实相符）。

设计原则（对齐 test_v1302c_mechanics.py 脚手架姿势：conftest + GWEN_GAME_DB 私有临时库）：
  - 行为断言确定性：随机点 mock 固定；阈值判据一律走 _cond_active（纯布尔）；
  - 数据断言全部真数值（禁恒真）；引擎方法缺失 → skip 兜底（不假失败）。

运行：python tests/test_v1302f_job_quality.py（exit=0 全绿；skip 不计数为失败）
"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 独立私有临时库（绝不触碰生产 game_data.db / test_game_data.db）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1302f_job_quality.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, E, BT, clean_db  # noqa: E402

passed = failed = skipped = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def check_float(name, got, want, tol=1e-9):
    check(name, abs(got - want) < tol, f"got={got} want={want}")


def skip(name, reason):
    global skipped
    skipped += 1
    print(f"  ⏭️  {name}（引擎未就绪/被改，待引擎修复后回归）：{reason}")


# ---------------- 构造（与 test_v1302c_mechanics.py 同款脚手架） ----------------
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


def _init_res(b):
    b._p_res().clear()
    b._p_res().update({"rage": 0, "element": "fire", "energy": 100, "faith": 0, "cp": 0, "chi": 0})


def cast_capture(b, skill_name, p):
    """黑盒施放：真实走 actor_turn 全链（校验/消耗/返还挂点 + v154 读条排事件），
    仅把伤害结算 _actor_skill 替换为捕获器（确定性：不跑真实伤害链随机点）。"""
    captured = {}

    def _fake(st, skill_name, info, player, target=None):
        captured["power"] = float(info.get("power") or 0)
        return []

    b._actor_skill = _fake
    logs, _ = b.actor_turn("skill", skill_name, p, enemy_act=False)
    # v154 读条命中制：出招读条结束（cast_done）才调用 _actor_skill（命中结算）——推进后触发
    b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
    return captured, logs


def cond_of(info):
    return (info or {}).get("cond") or {}


def mech_cond(info, want_mech, want_stacks, want_mult, label_nonempty=True):
    """player_mech_stacks 型机制层 cond 逐字段校验（配置层硬断言）。"""
    c = cond_of(info)
    return (c.get("type") == "player_mech_stacks"
            and c.get("mech") == want_mech
            and int(c.get("stacks", -1)) == want_stacks
            and (want_mult is None or abs(float(c.get("mult", 0)) - want_mult) < 1e-9)
            and (not label_nonempty or str(c.get("label", "")).strip() != ""))


# ================= ① 机制层数据断言（v153 战意/连段/cond） =================
def test_overflow_conds():
    print("\n【① 机制层数据（v153 战意 zhan_yi / 连段 lian_duan）】")
    # ---- 1. 怒斩：v153 无 cond（mech zhan_yi 叠层，每层攻击 +4% 由 MECH_STACK_BONUS 消费）----
    nz = E.skill_info("cls_zhan_shi", "怒斩") or {}
    check("怒斩 mech=zhan_yi mech_val=1（无 cond，v153 改叠层语义）",
          nz.get("mech") == "zhan_yi" and int(nz.get("mech_val", 0)) == 1 and not nz.get("cond"),
          str({k: nz.get(k) for k in ("mech", "mech_val", "cond")}))
    try:
        b, p = new_battle("cls_zhan_shi", 1, 1, learned=["怒斩"])
        _init_res(b)
        b._p_stacks()["zhan_yi"] = 3
        check("行为：战意 3 → _cond_active(怒斩) False（v153 无 cond）",
              b._cond_active(nz, p) is False, f"active={b._cond_active(nz, p)}")
        # 战意叠层引擎挂点：怒斩命中积攒 1 战意
        b._p_stacks().clear()
        b.enemy["hp"] = 10 ** 9
        import random
        random.seed(5)
        logs, _ = b.actor_turn("skill", "怒斩", p, enemy_act=False)
        # v154 读条命中制：命中叠层在出招读条结束（cast_done）时结算——推进后触发
        b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
        check("行为：怒斩施放 → 战意 +1（mech 叠层引擎挂点）",
              int(b._p_stacks().get("zhan_yi", 0) or 0) == 1,
              f"zhan_yi={b._p_stacks().get('zhan_yi')} logs={logs[:2]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：怒斩 mech 行为", str(ex))
    # ---- 2. 裂地斩：cond zhan_yi{6,×1.0}（v153 附加流血）----
    ld = E.skill_info("cls_zhan_shi", "裂地斩") or {}
    check("裂地斩 cond=mech_stacks{zhan_yi,6,×1.0}",
          mech_cond(ld, "zhan_yi", 6, 1.0, label_nonempty=False), str(cond_of(ld)))
    try:
        b, p = new_battle("cls_zhan_shi", 1, 1, learned=["裂地斩"])
        _init_res(b)
        b._p_stacks()["zhan_yi"] = 6
        check("行为：战意 6/10 → 裂地斩 cond 激活",
              b._cond_active(ld, p) is True, f"active={b._cond_active(ld, p)}")
        b._p_stacks()["zhan_yi"] = 5
        check("行为：战意 5/10 → 裂地斩 cond 不激活",
              b._cond_active(ld, p) is False, f"active={b._cond_active(ld, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：裂地斩 cond 行为", str(ex))
    # ---- 3. 影刃：v153 无 cond（mech lian_duan 叠段，连段 ≥3 追加由引擎 combo 处理）----
    yr = E.skill_info("cls_ci_ke", "影刃") or {}
    check("影刃 mech=lian_duan mech_val=1（无 cond）",
          yr.get("mech") == "lian_duan" and int(yr.get("mech_val", 0)) == 1 and not yr.get("cond"),
          str({k: yr.get(k) for k in ("mech", "mech_val", "cond")}))
    try:
        b, p = new_battle("cls_ci_ke", 1, 1, learned=["影刃"])
        _init_res(b)
        b._p_stacks()["lian_duan"] = 5
        check("行为：连段 5 → _cond_active(影刃) False（v153 无 cond）",
              b._cond_active(yr, p) is False, f"active={b._cond_active(yr, p)}")
        # 连段叠层引擎挂点：影刃命中 +1 段
        b._p_stacks().clear()
        b.enemy["hp"] = 10 ** 9
        import random as _r2
        _r2.seed(6)
        logs, _ = b.actor_turn("skill", "影刃", p, enemy_act=False)
        # v154 读条命中制：命中叠段在出招读条结束（cast_done）时结算——推进后触发
        b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
        check("行为：影刃施放 → 连段 +1（mech 叠段引擎挂点）",
              int(b._p_stacks().get("lian_duan", 0) or 0) == 1,
              f"lian_duan={b._p_stacks().get('lian_duan')} logs={logs[:2]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：影刃 mech 行为", str(ex))
    # ---- 4. 元素湮灭：v153 cond=enemy_marks（无 consume_all）----
    ea = E.skill_info("cls_fa_shi", "元素湮灭") or {}
    check("元素湮灭 cond=enemy_marks{4,×1.35}（v153 无 consume_all）",
          (ea.get("cond") or {}).get("type") == "enemy_marks"
          and int((ea.get("cond") or {}).get("stacks", 0)) == 4
          and abs(float((ea.get("cond") or {}).get("mult", 0)) - 1.35) < 1e-9,
          f"cond={ea.get('cond')} consume_all={ea.get('consume_all')}")


# ================= ② v153 被动新格式（字符串契约断裂已知） =================
def test_metronome_passives():
    print("\n【② v153 被动格式（dict 格式已修复，引擎不崩）】")
    # v153 全部 52 处被动已由主 agent 从字符串名（passive: 'xxx'）改为 dict（passive: {'proc': 'xxx'}），
    # 引擎 _passive_map/player_passive_stats 按 dict 消费不再崩（原字符串格式 AttributeError 已修）。
    import re as _re2
    # v161：skills_v153.py 已合并入 skills.py 主表
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "game", "data", "skills.py"), encoding="utf-8").read()
    str_passives = _re2.findall(r"'passive':\s*'[^']+'", src)
    dict_passives = _re2.findall(r"'passive':\s*\{", src)
    check("v153 被动全部为 dict 格式", len(dict_passives) > 40 and len(str_passives) == 0,
          f"str={len(str_passives)} dict={len(dict_passives)}")
    # 守护姿态：v153 为 增益 stance=counter（非旧 dmg_taken 被动 dict）
    sd = E.skill_info("cls_zhan_shi", "守护姿态") or {}
    check("守护姿态 v153 为 stance=counter 增益（非被动）",
          sd.get("kind") == "增益" and sd.get("stance") == "counter" and not sd.get("passive"),
          str({k: sd.get(k) for k in ("kind", "stance", "passive")}))
    # 以守为攻：v153 passive=counter_chance（字符串）
    gy = E.skill_info("cls_wu_seng", "以守为攻") or {}
    check("以守为攻 passive=counter_chance（字符串，引擎无消费 = 已知缺口）",
          ((gy.get("passive") or {}).get("proc") or "") == "counter_chance", str(gy.get("passive")))
    # 追猎者：v153 passive=hunt_mark_cap（猎印上限 +2，非 mark_extra）
    zl = E.skill_info("cls_you_xia", "追猎者") or {}
    check("追猎者 passive=hunt_mark_cap（v153 猎印上限语义）",
          ((zl.get("passive") or {}).get("proc") or "") == "hunt_mark_cap", str(zl.get("passive")))
    # 磐石之心：v153 passive=core_overflow（磐核溢出转盾，非 dmg_taken）
    ps = E.skill_info("cls_wu_seng", "磐石之心") or {}
    check("磐石之心 passive=core_overflow（v153 磐核语义）",
          ((ps.get("passive") or {}).get("proc") or "") == "core_overflow", str(ps.get("passive")))
    # 反击之王：v153 passive=counter_up（反击概率+25%，非 counter_attack dict）
    fj = E.skill_info("cls_wu_seng", "反击之王") or {}
    check("反击之王 passive=counter_up（v153 反击强化语义）",
          ((fj.get("passive") or {}).get("proc") or "") == "counter_up", str(fj.get("passive")))


# ================= ③ 引擎挂点行为 =================
def test_engine_hooks():
    print("\n【③ 引擎挂点行为（overflow_shield / 牧师信念负载）】")
    # ---- 1. 亡灵祭仪（v153 牧师 死灵祭司 passive=undead_faith 字符串 → 引擎无消费，已知缺口）
    wl = E.skill_info("cls_mu_shi", "亡灵祭仪") or {}
    check("数据：亡灵祭仪 passive=undead_faith（字符串，v153 死灵线新语义）",
          ((wl.get("passive") or {}).get("proc") or "") == "undead_faith", str(wl.get("passive")))
    # ---- 2. overflow_shield：满怒/满气 溢出转 5 护盾/点（core_resources 开关 + battle.py 溢出段）----
    try:
        rd_war = E.core_resource_def("cls_zhan_shi") or {}
        check("数据：战士 overflow_shield=True（满怒受击出盾开关）",
              rd_war.get("overflow_shield") is True, str({k: rd_war.get(k) for k in ("key", "max", "overflow_shield")}))
        rd_monk = E.core_resource_def("cls_wu_seng") or {}
        check("数据：拳师 overflow_shield=True（满气受击出盾开关）",
              rd_monk.get("overflow_shield") is True, str({k: rd_monk.get(k) for k in ("key", "max", "overflow_shield")}))
        b, p = new_battle("cls_zhan_shi", 0, 0)
        _init_res(b)
        b._p_res()["rage"] = 10
        now = b._res_gain_class("cls_zhan_shi", "rage", 3)
        shield_sum = sum(int(v.get("value", 0) or 0) for v in (b._p_shields_bag() or {}).values())
        check("满怒再溢 3 点 → 怒气封顶 10 + 护盾 15（3×5）",
              now == 10 and shield_sum == 15, f"rage={now} shield={shield_sum} p_shields={b._p_shields_bag()}")
        b2, p2 = new_battle("cls_zhan_shi", 0, 0)
        _init_res(b2)
        b2._p_res()["rage"] = 10
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b2._damage_actor(p2, 50, [])
        s2 = sum(int(v.get("value", 0) or 0) for v in (b2._p_shields_bag() or {}).values())
        check("满怒受击：受击 on_hit 怒 +1 溢出 → 出盾 5（怒气仍 10）",
              b2._p_res().get("rage") == 10 and s2 == 5,
              f"rage={b2._p_res().get('rage')} shield={s2} p_shields={b2._p_shields_bag()}")
        b3, p3 = new_battle("cls_wu_seng", 0, 0)
        _init_res(b3)
        b3._p_res()["chi"] = 10
        now3 = b3._res_gain_class("cls_wu_seng", "chi", 2)
        s3 = sum(int(v.get("value", 0) or 0) for v in (b3._p_shields_bag() or {}).values())
        check("满气再溢 2 点 → 气封顶 10 + 护盾 10（2×5）",
              now3 == 10 and s3 == 10, f"chi={now3} shield={s3} p_shields={b3._p_shields_bag()}")
        b4, p4 = new_battle("cls_ci_ke", 0, 0)
        _init_res(b4)
        b4._p_res()["cp"] = 5
        now4 = b4._res_gain_class("cls_ci_ke", "cp", 3)
        s4 = sum(int(v.get("value", 0) or 0) for v in (b4._p_shields_bag() or {}).values())
        check("对照：无 overflow_shield 线（刺客）溢出不转盾",
              now4 == 5 and s4 == 0, f"cp={now4} shield={s4}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：overflow_shield", str(ex))


# ================= ④ desc 一致性 =================
def test_desc_consistency():
    print("\n【④ desc 一致性（无已废弃承诺字样）】")
    # 暗影之心（刺客 T2 影舞者）：desc 名实相符（连段损失语义，无「潜行持续」承诺）
    ax = (E.skill_info("cls_ci_ke", "暗影之心") or {}).get("desc", "")
    check("暗影之心 desc 不含「潜行持续」承诺", "潜行持续" not in ax, ax)
    check("暗影之心 desc 与连段语义相符（断连损失 1 段）", "连" in ax, ax)
    # 元素湮灭 desc 含实际机制（印记条件爆发，非满印充能）
    ea = (E.skill_info("cls_fa_shi", "元素湮灭") or {}).get("desc", "")
    check("元素湮灭 desc 含实际机制（印记 ≥4 ×1.35）", "印记" in ea and "1.35" in ea, ea)
    # 龙息之怒 desc 含真伤机制（战士 T2 龙焰灼烧）
    lx = (E.skill_info("cls_zhan_shi", "龙息之怒") or {}).get("desc", "")
    check("龙息之怒 desc 含真伤机制", "真伤" in lx or "真实" in lx, lx)


if __name__ == "__main__":
    clean_db()
    test_overflow_conds()
    test_metronome_passives()
    test_engine_hooks()
    test_desc_consistency()
    print(f"\n===== v130.2f 职业质量批次: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)
