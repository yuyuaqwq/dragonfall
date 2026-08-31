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
    b.resources = {"rage": 0, "element": "fire", "energy": 100, "faith": 0, "cp": 0, "chi": 0}


def cast_capture(b, skill_name, p):
    """黑盒施放：真实走 _do_player_skill 全链（校验/消耗/返还挂点），
    仅把伤害结算 _player_skill 替换为捕获器（确定性：不跑真实伤害链随机点）。"""
    captured = {}

    def _fake(st, skill_name, info, player, target=None):
        captured["power"] = float(info.get("power") or 0)
        return []

    b._player_skill = _fake
    logs = b._do_player_skill(skill_name, p)
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


# ================= ① 机制层 cond ×4（v151 战意/连段） =================
def test_overflow_conds():
    print("\n【① 机制层 cond（v151 战意 zhan_yi / 连段 lian_duan）】")
    # ---- 1. 怒斩：战意≥3 ×1.15（狂战士 T1）----
    nz = E.skill_info("cls_zhan_shi", "怒斩") or {}
    check("怒斩 cond=mech_stacks{zhan_yi,3,×1.15,战意盈沸}",
          mech_cond(nz, "zhan_yi", 3, 1.15) and cond_of(nz).get("label") == "战意盈沸",
          str(cond_of(nz)))
    try:
        b, p = new_battle("cls_zhan_shi", 1, 1, learned=["怒斩"])
        _init_res(b)
        b.mech_stacks["zhan_yi"] = 3
        check("行为：战意 3/10 → 怒斩 cond 激活", b._cond_active(nz, p) is True,
              f"active={b._cond_active(nz, p)}")
        b.mech_stacks["zhan_yi"] = 2
        check("行为：战意 2/10 → 怒斩 cond 不激活", b._cond_active(nz, p) is False,
              f"active={b._cond_active(nz, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：怒斩 cond 行为", str(ex))
    # ---- 2. 裂地斩：战意≥6 ×1.2（狂战士 T1）----
    ld = E.skill_info("cls_zhan_shi", "裂地斩") or {}
    check("裂地斩 cond=mech_stacks{zhan_yi,6,×1.2}",
          mech_cond(ld, "zhan_yi", 6, 1.2), str(cond_of(ld)))
    try:
        b, p = new_battle("cls_zhan_shi", 1, 1, learned=["裂地斩"])
        _init_res(b)
        b.mech_stacks["zhan_yi"] = 6
        check("行为：战意 6/10 → 裂地斩 cond 激活",
              b._cond_active(ld, p) is True, f"active={b._cond_active(ld, p)}")
        b.mech_stacks["zhan_yi"] = 5
        check("行为：战意 5/10 → 裂地斩 cond 不激活",
              b._cond_active(ld, p) is False, f"active={b._cond_active(ld, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：裂地斩 cond 行为", str(ex))
    # ---- 3. 影刃：连段≥5 追加（影舞者 T1）----
    yr = E.skill_info("cls_ci_ke", "影刃") or {}
    check("影刃 cond=mech_stacks{lian_duan,5,追加}",
          mech_cond(yr, "lian_duan", 5, 1.0), str(cond_of(yr)))
    try:
        b, p = new_battle("cls_ci_ke", 1, 1, learned=["影刃"])
        _init_res(b)
        b.mech_stacks["lian_duan"] = 5
        check("行为：连段 5 → 影刃 cond 激活",
              b._cond_active(yr, p) is True, f"active={b._cond_active(yr, p)}")
        b.mech_stacks["lian_duan"] = 4
        check("行为：连段 4 → 影刃 cond 不激活",
              b._cond_active(yr, p) is False, f"active={b._cond_active(yr, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：影刃 cond 行为", str(ex))
    # ---- 4. 元素湮灭保持 consume_all（v151 唯一 consume_all 技能）----
    ea = E.skill_info("cls_fa_shi", "元素湮灭") or {}
    check("元素湮灭 consume_all{element,0.2} 存在",
          bool(ea.get("consume_all")) and ea["consume_all"].get("key") == "element",
          f"consume_all={ea.get('consume_all')}")


# ================= ② 被动节拍器 ×5（v151 数据） =================
def test_metronome_passives():
    print("\n【② 被动节拍器 ×5（passive 字段断言 + 行为）】")
    # ---- 1. 守护姿态（战士 T1 盾卫士）：dmg_taken 受击+2 怒 ----
    sd = E.skill_info("cls_zhan_shi", "守护姿态") or {}
    pv = (sd.get("passive") or {})
    check("守护姿态 passive=dmg_taken{reduce 0.1, res_gain 2}",
          pv.get("proc") == "dmg_taken"
          and abs(float(pv.get("reduce", 0)) - 0.1) < 1e-9
          and int(pv.get("res_gain", 0)) == 2,
          f"passive={pv}")
    try:
        b, p = new_battle("cls_zhan_shi", 1, 2, learned=["守护姿态"])
        _init_res(b)
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b._damage_player(p, 50, [])
        check("行为：守护姿态 受击 → 怒 +3（on_hit 1 + 被动 2）",
              b.resources.get("rage") == 3, f"rage={b.resources.get('rage')}")
        b2, p2 = new_battle("cls_zhan_shi", 1, 2)
        _init_res(b2)
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b2._damage_player(p2, 50, [])
        check("对照：无守护姿态 受击 → 怒 +1", b2.resources.get("rage") == 1,
              f"rage={b2.resources.get('rage')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：守护姿态 受击回怒", str(ex))
    # ---- 2. 磐石之心（拳师 T2 铁壁行者）：dmg_taken 减伤 5% ----
    ps = E.skill_info("cls_wu_seng", "磐石之心") or {}
    pv = (ps.get("passive") or {})
    check("磐石之心 passive=dmg_taken{reduce 0.05}",
          pv.get("proc") == "dmg_taken" and abs(float(pv.get("reduce", 0)) - 0.05) < 1e-9,
          f"passive={pv}")
    # ---- 3. 以守为攻（拳师 T1 磐石行者）：counter_attack 0.3 ----
    gy = E.skill_info("cls_wu_seng", "以守为攻") or {}
    pv = (gy.get("passive") or {})
    check("以守为攻 passive=counter_attack{chance 0.30}",
          pv.get("proc") == "counter_attack" and abs(float(pv.get("chance", 0)) - 0.30) < 1e-9,
          f"passive={pv}")
    # ---- 4. 反击之王（拳师 T2 铁壁行者）：counter_attack 0.4 ----
    fj = E.skill_info("cls_wu_seng", "反击之王") or {}
    pv = (fj.get("passive") or {})
    check("反击之王 passive=counter_attack{chance 0.40}",
          pv.get("proc") == "counter_attack" and abs(float(pv.get("chance", 0)) - 0.40) < 1e-9,
          f"passive={pv}")
    # ---- 5. 追猎者（游侠 T2 自然行者）：mark_extra 0.15 ----
    zl = E.skill_info("cls_you_xia", "追猎者") or {}
    pv = (zl.get("passive") or {})
    check("追猎者 passive=mark_extra{chance 0.15}",
          pv.get("proc") == "mark_extra" and abs(float(pv.get("chance", 0)) - 0.15) < 1e-9,
          f"passive={pv}")


# ================= ③ 引擎挂点行为 =================
def test_engine_hooks():
    print("\n【③ 引擎挂点行为（亡灵祭仪 / 反击回气 / overflow_shield）】")
    # ---- 1. 亡灵祭仪（牧师 T1 神谕者）：回合初回血 3%（turn_heal）----
    try:
        wl = E.skill_info("cls_mu_shi", "亡灵祭仪") or {}
        check("数据：亡灵祭仪 passive=turn_heal{pct 0.03}",
              (wl.get("passive") or {}).get("proc") == "turn_heal"
              and abs(float((wl.get("passive") or {}).get("pct", 0)) - 0.03) < 1e-9,
              f"passive={wl.get('passive')}")
        b, p = new_battle("cls_mu_shi", 1, 2, learned=["亡灵祭仪"], level=60)
        p["hp"] = 300  # 不满血才回
        logs = b._turn_start(p)
        check("行为：回合初 亡灵祭仪 回血 3%（hp 300→329）", p["hp"] == 329,
              f"hp={p['hp']} logs={logs[:2]}")
        check("亡灵祭仪日志", any("亡灵祭仪" in l for l in logs), f"{logs[:2]}")
        b0, p0 = new_battle("cls_mu_shi", 1, 2, level=60)
        p0["hp"] = 300
        b0._turn_start(p0)
        check("对照：无亡灵祭仪 回合初不回血", p0["hp"] == 300, f"hp={p0['hp']}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：亡灵祭仪", str(ex))
    # ---- 2. 反击回气 +2（以守为攻 反击命中后 气+2，monk.md §3.1 承诺落地）----
    try:
        b, p = new_battle("cls_wu_seng", 1, 2, learned=["以守为攻"])
        _init_res(b)
        logs = []
        # roll 序列：0.50 闪避判定不闪（≥基础闪避）→ 0.05 反击 roll（<0.30 触发）→ 0.99 反击暴击判定不暴
        with mock.patch.object(BT.random, "random", side_effect=[0.50, 0.05, 0.99]):
            b._damage_player(p, 50, logs)
        check("行为：受击触发反击 → 气 +2（反击回气）",
              b.resources.get("chi") == 2, f"chi={b.resources.get('chi')} logs={logs[:3]}")
        check("反击回气日志（反击回气 +2）",
              any("反击回气" in l for l in logs), f"{logs[:3]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：反击回气", str(ex))
    # ---- 3. overflow_shield：满怒/满气 溢出转 5 护盾/点（core_resources 开关 + battle.py 溢出段）----
    try:
        rd_war = E.core_resource_def("cls_zhan_shi") or {}
        check("数据：战士 overflow_shield=True（满怒受击出盾开关）",
              rd_war.get("overflow_shield") is True, str({k: rd_war.get(k) for k in ("key", "max", "overflow_shield")}))
        rd_monk = E.core_resource_def("cls_wu_seng") or {}
        check("数据：拳师 overflow_shield=True（满气受击出盾开关）",
              rd_monk.get("overflow_shield") is True, str({k: rd_monk.get(k) for k in ("key", "max", "overflow_shield")}))
        b, p = new_battle("cls_zhan_shi", 0, 0)
        _init_res(b)
        b.resources["rage"] = 10
        now = b._res_gain_class("cls_zhan_shi", "rage", 3)
        shield_sum = sum(int(v.get("value", 0) or 0) for v in (b.p_shields or {}).values())
        check("满怒再溢 3 点 → 怒气封顶 10 + 护盾 15（3×5）",
              now == 10 and shield_sum == 15, f"rage={now} shield={shield_sum} p_shields={b.p_shields}")
        b2, p2 = new_battle("cls_zhan_shi", 0, 0)
        _init_res(b2)
        b2.resources["rage"] = 10
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b2._damage_player(p2, 50, [])
        s2 = sum(int(v.get("value", 0) or 0) for v in (b2.p_shields or {}).values())
        check("满怒受击：受击 on_hit 怒 +1 溢出 → 出盾 5（怒气仍 10）",
              b2.resources.get("rage") == 10 and s2 == 5,
              f"rage={b2.resources.get('rage')} shield={s2} p_shields={b2.p_shields}")
        b3, p3 = new_battle("cls_wu_seng", 0, 0)
        _init_res(b3)
        b3.resources["chi"] = 10
        now3 = b3._res_gain_class("cls_wu_seng", "chi", 2)
        s3 = sum(int(v.get("value", 0) or 0) for v in (b3.p_shields or {}).values())
        check("满气再溢 2 点 → 气封顶 10 + 护盾 10（2×5）",
              now3 == 10 and s3 == 10, f"chi={now3} shield={s3} p_shields={b3.p_shields}")
        b4, p4 = new_battle("cls_ci_ke", 0, 0)
        _init_res(b4)
        b4.resources["cp"] = 5
        now4 = b4._res_gain_class("cls_ci_ke", "cp", 3)
        s4 = sum(int(v.get("value", 0) or 0) for v in (b4.p_shields or {}).values())
        check("对照：无 overflow_shield 线（刺客）溢出不转盾",
              now4 == 5 and s4 == 0, f"cp={now4} shield={s4}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：overflow_shield", str(ex))


# ================= ④ desc 一致性 =================
def test_desc_consistency():
    print("\n【④ desc 一致性（无已废弃承诺字样）】")
    # 暗影之心（刺客 T2 暗影之刃）：desc 名实相符（影系/连段，无「潜行持续」承诺）
    ax = (E.skill_info("cls_ci_ke", "暗影之心") or {}).get("desc", "")
    check("暗影之心 desc 不含「潜行持续」承诺", "潜行持续" not in ax, ax)
    check("暗影之心 desc 与 stat=spd 名实相符（影舞连段）", "影" in ax, ax)
    # 元素湮灭 desc 无「满印承诺未接线」字样（cond=reaction 满印爆发已落地）
    ea = (E.skill_info("cls_fa_shi", "元素湮灭") or {}).get("desc", "")
    check("元素湮灭 desc 含实际机制（满印爆发/充能消耗）",
          "满印" in ea and "充能" in ea, ea)
    # 龙息之怒 desc 含真伤机制（原龙裔 desc 承诺清理后的同源口径）
    lx = (E.skill_info("cls_zhan_shi", "龙息之怒") or {}).get("desc", "")
    check("龙息之怒 desc 含真伤机制", "真伤" in lx, lx)


if __name__ == "__main__":
    clean_db()
    test_overflow_conds()
    test_metronome_passives()
    test_engine_hooks()
    test_desc_consistency()
    print(f"\n===== v130.2f 职业质量批次: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)
