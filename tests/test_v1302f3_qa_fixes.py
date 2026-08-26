# -*- coding: utf-8 -*-
"""v130.2f3 上线前 QA 补测：真实回合流行为断言 + 数据收敛断言（test_v1302f3_qa_fixes.py）

背景（workspace/qa_v1302f/audit_T12.md）：既有 145 断言中「真实回合流」= 0——
全部单方法直调 + 资源预置注入，从未走 player_turn → _end_round → 跨回合出手路径；
T1 P0-1/P0-2（暮影潜行当回合衰减 / 破影一击 6 步死锁）与 T7 P1-1/P1-2/P1-3
（鹰眼死被动 / 战争咆哮渠道 1/3 / 魔力贯穿渠道错位）均在此绿灯下漏网。

本文件全量覆盖 P0/P1 修复点，断言按「目标行为」写（并行修复批次落地即全绿）：
  1. 暮影伏击流（P0）：完整回合流——暗影步施放 → _end_round 潜行保留 → 下回合
     破影一击（4 费 ≤ 影步上限 5）伤害含 ×1.5（对比无潜行基准）；非潜行无乘区。
  2. 战争咆哮技能渠道：施放技能命中 → 怒气 +2（技能渠道并入 res_gain_bonus，
     目标口径 on_skill 1 + 咆哮 1；普攻旧行为仍 +2）。
  3. 魔力贯穿技能渠道：施放技能命中 → 时之沙 +1（attack_res 在技能渠道生效）；
     终结技（有 res_cost）不触发（语义保持）。
  4. 鹰眼游侠标记路径：游侠施放标记技 → mark_extra 15% 额外叠印（mock random
     控制）；法师对照无触发。
  5. overflow_shield 冷却：战士满怒受击两次（同回合）→ 只转盾一次；跨回合后再转。
  6. 破影一击费用：res_cost shadow_step=4 + 伏击流经济闭环（1+4 = 5 ≤ 5）。
  7. desc 收敛：龙脉终曲/龙力无「+18%」；裂岳连击/气爆无「破势」空头措辞；
     流星陨落无「引爆×1.5」；破竹布靴配方含 roster_id。
  8. 奥术主宰/死神之箭 EQ 上限：power×cond.mult ≤ 6.5（读 skills.py 数据实算）。

构造手法（对齐 test_v1302f_job_quality.py）：conftest 装配层 + GWEN_GAME_DB
私有临时库；行为断言确定性靠 mock random / 捕获器（E.calc_damage → raw 捕获，
仅替换伤害结算，资源/日志挂点全部真实走链）。直接设资源处均已在注释注明。

运行：python tests/test_v1302f3_qa_fixes.py（exit=0 全绿；红 = 并行批次未落地项）
"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 独立私有临时库（绝不触碰生产 game_data.db / test_game_data.db / 其余测试私有库）
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1302f3_qa_fixes.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, E, BT, clean_db  # noqa: E402
from data.plugins.dragonfall.game.data import battle_config as BC  # noqa: E402
from data.plugins.dragonfall.game.data import craft as CRAFT_MOD  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# ---------------- 构造（与 test_v1302c_mechanics.py / test_v1302f_job_quality.py 同款脚手架） ----------------
def make_enemy(hp=5000, atk=40):
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


def crit_accumulate(b, p, n):
    """真实回合流攒影步：n 回合普攻，每回合固定随机序列 [暴击判定命中, 幸运一击不触发]。
    注：靶子怪 dodge=0 → _monster_dodge_check 不掷骰（实测探针确认）；暴击后必掷幸运一击。"""
    seq = []
    for _ in range(n):
        seq += [0.0, 0.99]
    with mock.patch.object(BT.random, "random", side_effect=seq):
        for _ in range(n):
            b.player_turn("attack", None, p, enemy_act=False)


def _capture_calc(cap):
    """伤害捕获器：取 E.calc_damage 首参（atk×power×pmult 的 raw 值），返回 0 跳过真实伤害链。
    资源获取/日志挂点全部照常执行（真实施放序列的其余部分不替换）。"""
    def _fake(*args, **kwargs):
        cap["raw"] = int(args[0] or 0)
        return 0
    return _fake


def eq_of(cls, name):
    """读 skills.py 数据实算 EQ = power × cond.mult（任务 #8：数据源实算）。"""
    info = E.skill_info(cls, name) or {}
    c = info.get("cond") or {}
    return float(info.get("power", 0) or 0) * float(c.get("mult", 1.0) or 1.0)


# ================= 1. 暮影伏击流（P0）：真实回合流 + 潜行乘区 ×1.5 =================
def test_shadow_ambush_flow():
    print("\n【1. 暮影伏击流（P0）真实回合流：暗影步→_end_round→破影一击 ×1.5】")
    # ---- 数据：破影一击 4 费 + 伏击流经济闭环（任务 #6，P0-2 修复锚）----
    pj = E.skill_info("cls_shadow_blade", "终结·破影一击") or {}
    ay = E.skill_info("cls_shadow_blade", "暗影步") or {}
    check("破影一击 res_cost.shadow_step = 4（P0-2 死锁修复）",
          int(((pj.get("res_cost") or {}).get("shadow_step", -1))) == 4,
          f"res_cost={pj.get('res_cost')}")
    check("暗影步 res_cost.shadow_step = 1（潜行唯一入口）",
          int(((ay.get("res_cost") or {}).get("shadow_step", -1))) == 1,
          f"res_cost={ay.get('res_cost')}")
    sb_rd = E.core_resource_def("cls_shadow_blade") or {}
    total = int(((pj.get("res_cost") or {}).get("shadow_step", 0))) \
        + int(((ay.get("res_cost") or {}).get("shadow_step", 0)))
    check(f"经济闭环：暗影步 1 + 破影 4 = {total} ≤ 影步上限 5（伏击连招可行）",
          total == 5 and total <= int(sb_rd.get("max", 0)),
          f"rd={ {k: sb_rd.get(k) for k in ('key', 'max')} }")
    check("潜行乘区数据：终结·破影一击 ×1.5（同源 battle_config）",
          abs(float(BC.SHADOW_STEALTH_DMG_MULT.get("终结·破影一击", 0) or 0) - 1.5) < 1e-9,
          str(BC.SHADOW_STEALTH_DMG_MULT))
    # ---- 4 费门槛行为校验（_skill_cast_blocked，直接设资源处：影步门槛校验对象）----
    b0, p0 = new_battle("cls_shadow_blade", 3, 3, learned=["暗影步", "终结·破影一击"], level=95)
    b0.resources["shadow_step"] = 3  # 直接设资源：静态门槛校验（上一档不足）
    _, blk3 = b0._skill_cast_blocked("终结·破影一击", p0)
    check("4 费门槛：3 步施放被拦（技能施放失败保护）", blk3 is True, f"blocked={blk3}")
    b0.resources["shadow_step"] = 4
    _, blk4 = b0._skill_cast_blocked("终结·破影一击", p0)
    check("4 费门槛：4 步可施放", blk4 is False, f"blocked={blk4}")

    # ---- 真实回合流 A：影步真实攒取（5 连暴击普攻）→ 暗影步 → 跨回合 → 破影一击 ----
    b, p = new_battle("cls_shadow_blade", 3, 3, learned=["暗影步", "终结·破影一击"], level=95)
    crit_accumulate(b, p, 5)
    check("真实攒步：5 回合暴击普攻 → 影步 5/5（on_crit 渠道走通）",
          b.resources.get("shadow_step") == 5, f"shadow_step={b.resources.get('shadow_step')}")
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_a, over_a = b.player_turn("skill", "暗影步", p, enemy_act=False)
    check("暗影步真实施放（player_turn 技能全链）：扣 1 步 → 4",
          b.resources.get("shadow_step") == 4, f"shadow_step={b.resources.get('shadow_step')} logs={logs_a[:2]}")
    check("P0-1：暗影步施放后经 _end_round（player_turn 尾部已走），潜行保留",
          (b.p_buffs or {}).get("stealth") == 1, f"p_buffs={b.p_buffs}")
    b._end_round()  # 再跨一个回合末：潜行必须持续保留（豁免衰减，同 next_atk_up 语义）
    check("P0-1：再经历一次 _end_round（跨双回合），潜行仍保留",
          (b.p_buffs or {}).get("stealth") == 1, f"p_buffs={b.p_buffs}")

    cap_s = {}
    with mock.patch.object(E, "calc_damage", side_effect=_capture_calc(cap_s)):
        with mock.patch.object(BT.random, "random", return_value=0.99):
            logs_s, over_s = b.player_turn("skill", "终结·破影一击", p, enemy_act=False)
    check("伏击终结：下回合施放破影一击成功（扣 4 步 → 0，经济闭环走通）",
          b.resources.get("shadow_step") == 0,
          f"shadow_step={b.resources.get('shadow_step')} logs={logs_s[:2]}")
    check("潜行必暴：潜行生效日志（🌙 潜行生效）",
          any("🌙 潜行生效" in l for l in logs_s), f"{logs_s[:4]}")
    check("乘区标签：日志带「🌙潜行x1.5」",
          any("潜行x1.5" in l for l in logs_s), f"{logs_s[:4]}")
    check("潜行出手后 buff 消费（stealth 已删除，一次性语义）",
          (b.p_buffs or {}).get("stealth") is None, f"p_buffs={b.p_buffs}")

    # ---- 真实回合流 B（对照）：同攒取流程但不施放暗影步，非潜行破影一击 ----
    b2, p2 = new_battle("cls_shadow_blade", 3, 3, learned=["终结·破影一击"], level=95)
    crit_accumulate(b2, p2, 5)
    cap_n = {}
    with mock.patch.object(E, "calc_damage", side_effect=_capture_calc(cap_n)):
        with mock.patch.object(BT.random, "random", return_value=0.99):
            logs_n, over_n = b2.player_turn("skill", "终结·破影一击", p2, enemy_act=False)
    check("对照：无潜行破影一击 raw 基准已取到（伤害结算同链）", cap_n.get("raw", 0) > 0,
          f"raw_n={cap_n.get('raw')}")
    check("对照：非潜行破影一击无乘区标签（恒 1.0）",
          not any("潜行" in l for l in logs_n), f"{logs_n[:4]}")
    got = cap_s.get("raw", 0)
    want = round(1.5 * cap_n.get("raw", 0))
    check(f"×1.5 实算：潜行 raw {got} ≈ 1.5 × 非潜行 raw {cap_n.get('raw', 0)} = {want}（|Δ|≤2）",
          abs(got - want) <= 2, f"got={got} want={want}")


# ================= 2. 战争咆哮技能渠道（P1-2）：技能命中 +2 / 普攻渠道仍 +2 =================
def test_war_cry_skill_channel():
    print("\n【2. 战争咆哮 res_gain_bonus 技能渠道（全渠道+1 口径）】")
    wz = E.skill_info("cls_zhan_shi", "战争咆哮") or {}
    pv = (wz.get("passive") or {})
    check("数据：战争咆哮 passive=res_gain_bonus（无 stat 残留）",
          pv.get("proc") == "res_gain_bonus" and "stat" not in pv, f"passive={pv}")
    b, p = new_battle("cls_zhan_shi", 0, 0, learned=["战争咆哮", "挥砍"])
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_s = b._do_player_skill("挥砍", p)
    check("技能命中（挥砍，非普攻）× 咆哮 → 怒气 +2（渠道加成生效）",
          b.resources.get("rage") == 2, f"rage={b.resources.get('rage')} logs={logs_s[:3]}")
    check("技能渠道日志（战争咆哮+1 怒气）",
          any("战争咆哮+1" in l for l in logs_s), f"{logs_s[:3]}")
    b2, p2 = new_battle("cls_zhan_shi", 0, 0, learned=["挥砍"])
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b2._do_player_skill("挥砍", p2)
    check("对照：无咆哮 技能命中 → 怒气 +1（挥砍 self res_gain 1）",
          b2.resources.get("rage") == 1, f"rage={b2.resources.get('rage')}")
    b3, p3 = new_battle("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_a = b3.player_turn("attack", None, p3, enemy_act=False)
    check("对照旧行为：普攻渠道（完整施放）仍 +2（on_attack 1 + 咆哮 1）",
          b3.resources.get("rage") == 2, f"rage={b3.resources.get('rage')} logs={logs_a[0][:2] if logs_a else ''}")


# ================= 3. 魔力贯穿技能渠道（P1-3）：attack_res 施法命中 ≥1 / 终结技不触发 =================
def test_mana_pierce_skill_channel():
    print("\n【3. 魔力贯穿 attack_res 技能渠道（施法命中 +1）】")
    mc = E.skill_info("cls_chronomancer", "魔力贯穿") or {}
    pv = (mc.get("passive") or {})
    check("数据：魔力贯穿 passive=attack_res{time_sand,1}",
          pv.get("proc") == "attack_res" and pv.get("res") == "time_sand"
          and int(pv.get("gain", 0)) == 1, f"passive={pv}")
    b, p = new_battle("cls_chronomancer", 3, 3, learned=["魔力贯穿", "时滞术"], level=95)
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_c = b._do_player_skill("时滞术", p)
    check("施法命中（时滞术）× 魔力贯穿 → 时之沙 +2（技能 1 + 贯穿 1）",
          b.resources.get("time_sand") == 2,
          f"time_sand={b.resources.get('time_sand')} logs={logs_c[:3]}")
    check("施法渠道日志（魔力贯穿+1 时之沙）",
          any("魔力贯穿+1" in l for l in logs_c), f"{logs_c[:3]}")
    b2, p2 = new_battle("cls_chronomancer", 3, 3, learned=["时滞术"], level=95)
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b2._do_player_skill("时滞术", p2)
    check("对照：无魔力贯穿 施法命中 → 时之沙 +1（仅技能自身）",
          b2.resources.get("time_sand") == 1, f"time_sand={b2.resources.get('time_sand')}")
    b3, p3 = new_battle("cls_chronomancer", 3, 3, learned=["魔力贯穿", "时停领域"], level=95)
    b3.resources["time_sand"] = 5  # 直接设资源：终结技资源门槛（非本断言对象）
    with mock.patch.object(BT.random, "random", return_value=0.99):
        logs_f = b3._do_player_skill("时停领域", p3)
    check("终结技语义：时停领域（有 res_cost 无 res_gain）扣 3 沙 → 2，attack_res 不触发",
          b3.resources.get("time_sand") == 2,
          f"time_sand={b3.resources.get('time_sand')} logs={logs_f[:3]}")
    check("终结技日志无「魔力贯穿+1」（渠道扩展不破坏消耗型语义）",
          not any("魔力贯穿" in l for l in logs_f), f"{logs_f[:3]}")


# ================= 4. 鹰眼游侠标记路径（P1-1）：mark_extra 15% 额外叠印 =================
def test_hawk_eye_mark_path():
    print("\n【4. 鹰眼 mark_extra 游侠标记路径（15% 额外叠印）】")
    hy = E.skill_info("cls_you_xia", "鹰眼") or {}
    pv = (hy.get("passive") or {})
    check("数据：鹰眼 passive=mark_extra chance 0.15",
          pv.get("proc") == "mark_extra" and abs(float(pv.get("chance", 0) or 0) - 0.15) < 1e-9,
          f"passive={pv}")
    b, p = new_battle("cls_you_xia", 0, 0, learned=["鹰眼", "林语印记"], level=40)
    b.resources["energy"] = 41  # 直接设资源：林语印记施放门槛（非本断言对象）
    # 掷骰序列（靶子怪 dodge=0 不掷）：[暴击判定不暴, mark_extra roll 0.0 触发]
    with mock.patch.object(BT.random, "random", side_effect=[0.99, 0.0]):
        logs_m = b._do_player_skill("林语印记", p)
    mark_n = int(((b.enemy.get("debuffs") or {}).get("mark") or {}).get("n", 0))
    check("游侠施放标记技（林语印记）roll 0.0 → 敌方标记 2 层（15% 额外叠印生效）",
          mark_n == 2, f"mark={mark_n} logs={logs_m[:3]}")
    b2, p2 = new_battle("cls_you_xia", 0, 0, learned=["鹰眼", "林语印记"], level=40)
    b2.resources["energy"] = 41  # 直接设资源同上
    with mock.patch.object(BT.random, "random", side_effect=[0.99, 0.99]):
        b2._do_player_skill("林语印记", p2)
    mark2 = int(((b2.enemy.get("debuffs") or {}).get("mark") or {}).get("n", 0))
    check("对照：roll 0.99（≥0.15 不触发）→ 1 层（概率门控正确）",
          mark2 == 1, f"mark={mark2}")
    b3, p3 = new_battle("cls_you_xia", 0, 0, learned=["林语印记"], level=40)
    b3.resources["energy"] = 41  # 直接设资源同上
    with mock.patch.object(BT.random, "random", side_effect=[0.99, 0.0]):
        b3._do_player_skill("林语印记", p3)
    mark3 = int(((b3.enemy.get("debuffs") or {}).get("mark") or {}).get("n", 0))
    check("对照：无鹰眼 即使 roll 0.0 → 仍 1 层（被动驱动，非恒叠）",
          mark3 == 1, f"mark={mark3}")
    # ---- 法师对照：无触发路径 ----
    check("数据：鹰眼属游侠技能树，法师无此技能（不越职）",
          E.skill_info("cls_fa_shi", "鹰眼") is None, "cls_fa_shi 应有 None")
    b4, p4 = new_battle("cls_fa_shi", 1, 1, learned=["火球术"], level=40)
    with mock.patch.object(BT.random, "random", side_effect=[0.99, 0.99]):
        b4._do_player_skill("火球术", p4)
    check("行为：法师施放元素技（火球术）→ 火印恰 1 层（mark_extra 无触发路径）",
          int(b4.e_buffs.get("fire_mark", 0) or 0) == 1,
          f"fire_mark={b4.e_buffs.get('fire_mark')}")


# ================= 5. overflow_shield 冷却（P2-1）：同回合只转盾一次 / 跨回合再转 =================
def test_overflow_cooldown():
    print("\n【5. overflow_shield 冷却 1 回合（满怒受击同回合单转 / 跨回合再转）】")
    rd_war = E.core_resource_def("cls_zhan_shi") or {}
    check("数据：战士 overflow_shield=True（满溢转盾开关）",
          rd_war.get("overflow_shield") is True,
          str({k: rd_war.get(k) for k in ("key", "max", "overflow_shield")}))
    b, p = new_battle("cls_zhan_shi", 0, 0)
    b.resources["rage"] = 10  # 直接设资源：满怒受击前置（溢出点=受击渠道 on_hit +1）
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b._damage_player(p, 30, [])
    sh1 = b.p_shields.get("overflow_shield") or {}
    check("满怒受击 #1 → 溢出 1 点转盾 5（turns=1 字段钉死持续语义）",
          b.resources.get("rage") == 10 and int(sh1.get("value", 0)) == 5
          and int(sh1.get("turns", 0)) == 1,
          f"rage={b.resources.get('rage')} shields={b.p_shields}")
    hp_after1 = p["hp"]
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b._damage_player(p, 30, [])
    sh2 = b.p_shields.get("overflow_shield") or {}
    check("同回合受击 #2 → #1 的盾被 5 点吸收（掉血 25 而非 30）+ 冷却生效：不再补新盾",
          p["hp"] == hp_after1 - 25 and not sh2 and (b.p_shields or {}).get("overflow_shield") is None,
          f"hp={p['hp']} (before={hp_after1}) shields={b.p_shields}")
    b._end_round()  # 回合末：盾值衰减消失 + overflow 冷却重置
    check("回合末（_end_round）：盾 turns 1→0 消失 + 冷却复位",
          not b.p_shields.get("overflow_shield"), f"shields={b.p_shields}")
    b.round += 1  # 跨回合（模拟 player_turn 回合递增）
    hp_after2 = p["hp"]
    with mock.patch.object(BT.random, "random", return_value=0.99):
        b._damage_player(p, 30, [])
    sh3 = b.p_shields.get("overflow_shield") or {}
    check("跨回合受击 #3 → 冷却重置后再转盾 5（新盾 turns=1，且本击未被盾吸收）",
          int(sh3.get("value", 0)) == 5 and int(sh3.get("turns", 0)) == 1
          and p["hp"] == hp_after2 - 30,
          f"shields={b.p_shields}")


# ================= 6-9. 数据收敛组（费用 / desc / EQ 帽 / roster_id） =================
def test_data_convergence():
    print("\n【6-9. 数据收敛：费用 / desc / EQ 上限 / roster_id】")
    # ---- 6. 破影一击费用（配置断言；行为门槛见用例 1）----
    pj = E.skill_info("cls_shadow_blade", "终结·破影一击") or {}
    check("破影一击 res_cost.shadow_step = 4（配置同源）",
          int(((pj.get("res_cost") or {}).get("shadow_step", -1))) == 4,
          f"res_cost={pj.get('res_cost')}")
    # ---- 7. desc 收敛 ----
    lm = (E.skill_info("cls_dragon_oath", "龙脉终曲") or {}).get("desc", "")
    check("龙脉终曲 desc 无「+18%」（收敛至 +10% 且含实际机制）",
          "18%" not in lm and "10%" in lm, lm)
    rd_desc = (C.CORE_RESOURCES.get("cls_dragon_oath") or {}).get("desc", "")
    check("龙力资源 desc 无「18%」（每层 +10% 与 MECH_STACK_BONUS 0.10 收敛）",
          "18%" not in rd_desc, rd_desc)
    lj = (E.skill_info("cls_wu_sheng", "裂岳连击") or {}).get("desc", "")
    check("裂岳连击 desc 无「破势目标」空头措辞（含实际机制：每 zen +12%）",
          "破势" not in lj, lj)
    qb = (E.skill_info("cls_wu_sheng", "气爆") or {}).get("desc", "")
    check("气爆 desc 无「破势」空头措辞", "破势" not in qb, qb)
    lx = (E.skill_info("cls_wild_hunter", "流星陨落") or {}).get("desc", "")
    check("流星陨落 desc 无「引爆×1.5」（改述实际机制：标记易伤每层＋20%）",
          "引爆" not in lx, lx)
    # ---- 8. EQ 上限：power × cond.mult ≤ 6.5（读 skills.py 数据实算）----
    az = eq_of("cls_fa_shi", "奥术主宰")
    check(f"奥术主宰实算 EQ = {az:.2f} ≤ 6.5（T13 P1-2 超标回收）",
          az <= 6.5 + 1e-9, f"eq={az}")
    ss = eq_of("cls_you_xia", "死神之箭")
    check(f"死神之箭实算 EQ = {ss:.2f} ≤ 6.5（T13 P1-2 超标回收）",
          ss <= 6.5 + 1e-9, f"eq={ss}")
    # ---- 破竹布靴配方含 roster_id（craft.py 配置断言）----
    from data.plugins.dragonfall.game.data import equip_roster as ER
    rec = (CRAFT_MOD.CRAFT_RECIPES or {}).get("rec_po_zhu_bu_xue") or {}
    rid = str(rec.get("roster_id", "") or "")
    roster_entry = (ER.EQUIP_ROSTER or {}).get(rid) or {}
    check("破竹布靴配方含 roster_id 且与名册精确对应（图纸→名册生成链完整）",
          rec.get("name") == "破竹布靴" and rid.startswith("eq_")
          and roster_entry.get("name") == "破竹布靴",
          f"name={rec.get('name')} roster_id={rid} roster_entry_name={roster_entry.get('name')}")


if __name__ == "__main__":
    clean_db()
    test_shadow_ambush_flow()
    test_war_cry_skill_channel()
    test_mana_pierce_skill_channel()
    test_hawk_eye_mark_path()
    test_overflow_cooldown()
    test_data_convergence()
    print(f"\n===== v130.2f3 QA 修复点补测: {passed} passed / {failed} failed =====")
    sys.exit(1 if failed else 0)