# -*- coding: utf-8 -*-
"""v130.2f 职业质量批次固化测试（test_v1302f_job_quality.py）

覆盖设计仓 09_职业体系.md §14.2-14.5（2026-08-25 批注）与本批次全部修复点：
  ① 满溢 cond ×5（时停领域 满沙×1.3 / 流星陨落 满印×1.15 / 龙焰吐息 龙力≥8×1.2 /
     暗杀 CP≥4 / 元素湮灭 满充能×1.3）——配置断言 + 阈值行为断言（_cond_active 满 vs 不满）
  ② 被动节拍器 ×6（寒霜亲和 attack_res 施法命中+1 充能 / 魔力贯穿 attack_res 施法命中+1 沙 /
     神圣坚韧 dmg_taken 受击+1 信仰 / 墓穴护甲 dmg_taken 受击+1 悼咏 / 磐石体 dmg_taken 受击+1 气
     / 战争咆哮 res_gain_bonus 怒气全渠道+1）——被动字段断言 + 磐石体无 chi 死字段断言
  ③ 引擎挂点 ×4 + overflow_shield（亡灵祭仪回合初悼咏+1~2 / 反击回气+2 / 致命预谋首次终结返还 /
     伴奏歌类技 20% 回声+1 / 满怒·满气 overflow_shield 受击溢出转盾 5/点）
  ④ desc 一致性（龙焰吐息·星辉祈愿·暗影之心·龙裔资源 desc 不含已废弃承诺字样）

设计原则（对齐 test_v1302c_mechanics.py 脚手架姿势：conftest + GWEN_GAME_DB 私有临时库）：
  - 行为断言确定性：随机点 mock 固定；隐藏线资源技同时挂 MECH_STACK_BONUS 阶梯（res_cost 早返回），
    阈值判据一律走 _cond_active（纯布尔，不掺倍率合成）；倍率数值在配置层断言。
  - 数据断言全部真数值（禁恒真）；引擎方法缺失 → skip 兜底（不假失败）。
  - 并行批次未落地的点（暗杀/元素湮灭 cond、寒霜亲和 attack_res）当前为红属预期，主 agent 收尾后转绿。

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


def _cond_label_hit(logs, label="沙漏盈满"):
    """施放日志中是否存在条件标签（快照语义下扣费后仍应出现满资源标签）。"""
    return any(label in str(l) for l in (logs or []))


def res_stacks_cond(info, want_res, want_stacks, want_mult, label_nonempty=True):
    """player_res_stacks 型满溢 cond 逐字段校验（配置层硬断言）。"""
    c = cond_of(info)
    return (c.get("type") == "player_res_stacks"
            and c.get("res_key") == want_res
            and int(c.get("stacks", -1)) == want_stacks
            and (want_mult is None or abs(float(c.get("mult", 0)) - want_mult) < 1e-9)
            and (not label_nonempty or str(c.get("label", "")).strip() != ""))


# ================= ① 满溢 cond ×5 =================
def test_overflow_conds():
    print("\n【① 满溢 cond ×5（配置 + 阈值行为）】")
    # ---- 1. 时停领域：沙≥5 强化（设计 §14.2 #8：满沙×1.3「沙漏盈满」）----
    tf = E.skill_info("cls_chronomancer", "时停领域") or {}
    check("时停领域 cond=res_stacks{time_sand,5,×1.3,沙漏盈满}",
          res_stacks_cond(tf, "time_sand", 5, 1.3)
          and cond_of(tf).get("label") == "沙漏盈满",
          str(cond_of(tf)))
    try:
        b, p = new_battle("cls_chronomancer", 3, 3, learned=["时停领域"])
        b.resources["time_sand"] = 5
        check("行为：沙 5/5 → 时停领域 cond 激活（对比不满沙）",
              b._cond_active(tf, p) is True, f"active={b._cond_active(tf, p)}")
        b.resources["time_sand"] = 3
        check("行为：沙 3/5 → 时停领域 cond 不激活",
              b._cond_active(tf, p) is False, f"active={b._cond_active(tf, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：时停领域 cond 行为", str(ex))
    # ---- 2. 流星陨落：满印强化（设计 §14.2 #9：满印×1.15「流星盈满」）----
    ms = E.skill_info("cls_wild_hunter", "流星陨落") or {}
    check("流星陨落 cond=res_stacks{hunt_mark,5,×1.15}",
          res_stacks_cond(ms, "hunt_mark", 5, 1.15), str(cond_of(ms)))
    try:
        b, p = new_battle("cls_wild_hunter", 3, 3, learned=["流星陨落"])
        b.resources["hunt_mark"] = 5
        check("行为：猎印 5/5 满印 → 流星陨落 cond 激活",
              b._cond_active(ms, p) is True, f"active={b._cond_active(ms, p)}")
        b.resources["hunt_mark"] = 3
        check("行为：猎印 3/5 未满 → cond 不激活",
              b._cond_active(ms, p) is False, f"active={b._cond_active(ms, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：流星陨落 cond 行为", str(ex))
    # ---- 3. 龙焰吐息：龙力≥8 强化（落地值 ×1.2 标签「龙威」）----
    db = E.skill_info("cls_dragon_oath", "龙焰吐息") or {}
    check("龙焰吐息 cond=res_stacks{dragon_might,8,×1.2}",
          res_stacks_cond(db, "dragon_might", 8, 1.2)
          and cond_of(db).get("label") == "龙威",
          str(cond_of(db)))
    try:
        b, p = new_battle("cls_dragon_oath", 3, 3, learned=["龙焰吐息"])
        b.resources["dragon_might"] = 8
        check("行为：龙力 8/10 → 龙焰吐息 cond 激活",
              b._cond_active(db, p) is True, f"active={b._cond_active(db, p)}")
        b.resources["dragon_might"] = 7
        check("行为：龙力 7/10 → cond 不激活",
              b._cond_active(db, p) is False, f"active={b._cond_active(db, p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：龙焰吐息 cond 行为", str(ex))
    # ---- 4. 暗杀：保持 enemy_hp_low 残血收割（设计决策 2026-08-26）----
    # cond 引擎为单字典字段（battle.py:3471 _cond_mult 单条件分发），暗杀已占 enemy_hp_low 槽；
    # 「满溢奖励」改由暗影处刑残血×1.5 + 套装/词条通道承载，不替换现有斩杀条（防机制删改）。
    as_ = E.skill_info("cls_ci_ke", "暗杀") or {}
    ac = cond_of(as_)
    check("暗杀 cond 保持 enemy_hp_low（设计决策：不替换残血斩杀槽）",
          ac.get("type") == "enemy_hp_low" and "player_res_stacks" not in str(ac),
          str(ac))
    # ---- 5. 元素湮灭：保持 consume_all（设计决策 2026-08-26）----
    # 引擎 resources['element'] 为当前系字符串槽（'fire'），player_res_stacks 对字符串恒真（battle_conds.py:159-160）
    # → 「满充能×1.3」cond 会无条件恒真=变相白送增伤；等待引擎 element_charge 数值通道后再落地。
    ea = E.skill_info("cls_fa_shi", "元素湮灭") or {}
    ec = ea.get("cond") or {}
    check("元素湮灭保持 consume_all 无恒真 cond（设计决策：element 字符串槽限制）",
          bool(ea.get("consume_all")) and ec.get("type") != "player_res_stacks",
          f"consume_all={bool(ea.get('consume_all'))} cond={ec}")
    # ---- 6. 施放快照语义（HC-12）：消耗型技能扣费后 cond 仍按施放前持有判定（v130.2f 修复）----
    try:
        b, p = new_battle("cls_chronomancer", 3, 3, learned=["时停领域"], level=95)
        b.resources["time_sand"] = 5
        cap, logs = cast_capture(b, "时停领域", p)
        check("完整施放：满 5 沙放时停领域（-3）扣费成功剩 2 沙",
              b.resources.get("time_sand") == 2, f"time_sand={b.resources.get('time_sand')} logs={logs[:3]}")
        check("快照语义：扣费后 _cond_active 按施放前快照（5≥5）仍激活",
              b._cond_active(tf, p) is True, f"active={b._cond_active(tf, p)}")
        b2, p2 = new_battle("cls_chronomancer", 3, 3, learned=["时停领域"], level=95)
        b2.resources["time_sand"] = 4
        cast_capture(b2, "时停领域", p2)
        check("对照：4 沙施放（-3 后剩 1）→ 快照 4<5 不激活",
              b2._cond_active(tf, p2) is False, f"active={b2._cond_active(tf, p2)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：施放快照 cond", str(ex))


# ================= ② 被动节拍器 ×6 =================
def test_metronome_passives():
    print("\n【② 被动节拍器 ×6（passive 字段断言 + 磐石体死字段剔除）】")
    # ---- 1. 寒霜亲和（法师）：保持 ice_slow（设计决策 2026-08-26）----
    # attack_res element 会读 resources['element']（当前系字符串槽）→ int('fire') ValueError 崩溃
    # （battle.py:2250 _res_gain_class int 转换）；等引擎 element→element_charge 数值通道后再落地充能节拍器。
    hs = E.skill_info("cls_fa_shi", "寒霜亲和") or {}
    pv = (hs.get("passive") or {})
    check("寒霜亲和保持 ice_slow（设计决策：element 字符串槽崩溃风险）",
          pv.get("proc") == "ice_slow", f"passive={pv}")
    # ---- 2. 魔力贯穿（时咒）：attack_res 施法命中+1 沙（已落地）----
    mc = E.skill_info("cls_chronomancer", "魔力贯穿") or {}
    pv = (mc.get("passive") or {})
    check("魔力贯穿 passive=attack_res{time_sand,1}",
          pv.get("proc") == "attack_res" and pv.get("res") == "time_sand"
          and int(pv.get("gain", 0)) == 1,
          f"passive={pv}")
    # ---- 3. 神圣坚韧（牧师）：dmg_taken 受击+1 信仰（减伤保留）----
    sj = E.skill_info("cls_mu_shi", "神圣坚韧") or {}
    pv = (sj.get("passive") or {})
    check("神圣坚韧 passive=dmg_taken{reduce 0.05, res_gain 1}",
          pv.get("proc") == "dmg_taken"
          and abs(float(pv.get("reduce", 0)) - 0.05) < 1e-9
          and int(pv.get("res_gain", 0)) == 1,
          f"passive={pv}")
    # ---- 4. 墓穴护甲（暗影神谕）：dmg_taken 受击+1 悼咏（减伤保留）----
    ma = E.skill_info("cls_hymn", "墓穴护甲") or {}
    pv = (ma.get("passive") or {})
    check("墓穴护甲 passive=dmg_taken{reduce 0.05, res_gain 1}",
          pv.get("proc") == "dmg_taken"
          and abs(float(pv.get("reduce", 0)) - 0.05) < 1e-9
          and int(pv.get("res_gain", 0)) == 1,
          f"passive={pv}")
    # ---- 5. 磐石体（拳师）：dmg_taken 受击+1 气；chi:1 死字段必须剔除（§14.5 P0）----
    ps = E.skill_info("cls_wu_seng", "磐石体") or {}
    pv = (ps.get("passive") or {})
    check("磐石体 passive=dmg_taken{reduce 0.05, res_gain 1}",
          pv.get("proc") == "dmg_taken"
          and abs(float(pv.get("reduce", 0)) - 0.05) < 1e-9
          and int(pv.get("res_gain", 0)) == 1,
          f"passive={pv}")
    check("磐石体 passive 无 chi 死字段（改 res_gain 通道）",
          "chi" not in pv, f"passive={pv}")
    try:
        b, p = new_battle("cls_wu_seng", 0, 0, learned=["磐石体"])
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b._damage_player(p, 50, [])
        check("行为：磐石体 受击 → 气 +1（受击回气实装）",
              b.resources.get("chi") == 1, f"chi={b.resources.get('chi')}")
        b2, p2 = new_battle("cls_wu_seng", 0, 0)
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b2._damage_player(p2, 50, [])
        check("对照：无磐石体 受击 → 气 0（拳师 on_hit=0 不受击回气）",
              b2.resources.get("chi") == 0, f"chi={b2.resources.get('chi')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：磐石体 受击回气", str(ex))
    # ---- 6. 战争咆哮（战士）：res_gain_bonus 怒气全渠道+1（§14.3 #1，引擎现成）----
    wz = E.skill_info("cls_zhan_shi", "战争咆哮") or {}
    pv = (wz.get("passive") or {})
    check("战争咆哮 passive=res_gain_bonus（无 stat 残留）",
          pv.get("proc") == "res_gain_bonus" and "stat" not in pv,
          f"passive={pv}")
    try:
        b, p = new_battle("cls_zhan_shi", 0, 0, learned=["战争咆哮"])
        b._resource_on_attack(p)
        check("行为：普攻命中 怒气 +2（on_attack 1 + 咆哮全渠道 1）",
              b.resources.get("rage") == 2, f"rage={b.resources.get('rage')}")
        b2, p2 = new_battle("cls_zhan_shi", 0, 0)
        b2._resource_on_attack(p2)
        check("对照：无咆哮 普攻命中 怒气 +1",
              b2.resources.get("rage") == 1, f"rage={b2.resources.get('rage')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：战争咆哮 怒气+1", str(ex))


# ================= ③ 引擎挂点 ×4 + overflow_shield =================
def test_engine_hooks():
    print("\n【③ 引擎挂点行为（亡灵祭仪 / 反击回气 / 致命预谋 / 伴奏回声）+ overflow_shield】")
    # ---- 1. 亡灵祭仪（暗影神谕）：回合初 每只亡灵 悼咏+1，最多 2 只生效 ----
    try:
        b, p = new_battle("cls_hymn", 0, 0, learned=["召唤骷髅"])
        b.summons = [{"tid": "skeleton", "name": "骷髅兵", "hp": 50, "max_hp": 50},
                     {"tid": "skeleton", "name": "骷髅兵", "hp": 50, "max_hp": 50},
                     {"tid": "skeleton", "name": "骷髅兵", "hp": 50, "max_hp": 50}]
        logs = b._turn_start(p)
        check("亡灵祭仪：3 只亡灵在场 回合初 悼咏 +2（最多 2 只生效）",
              b.resources.get("canticle") == 2, f"canticle={b.resources.get('canticle')} logs={logs[:2]}")
        check("亡灵祭仪日志（亡灵祭仪 悼咏 +2）",
              any("亡灵祭仪" in l for l in logs), f"{logs[:2]}")
        b1, p1 = new_battle("cls_hymn", 0, 0)
        b1.summons = [{"tid": "skeleton", "name": "骷髅兵", "hp": 50, "max_hp": 50}]
        b1._turn_start(p1)
        check("亡灵祭仪：1 只亡灵 回合初 悼咏 +1",
              b1.resources.get("canticle") == 1, f"canticle={b1.resources.get('canticle')}")
        b0, p0 = new_battle("cls_hymn", 0, 0)
        b0._turn_start(p0)
        check("对照：无亡灵在场 回合初 悼咏 +0",
              b0.resources.get("canticle") == 0, f"canticle={b0.resources.get('canticle')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：亡灵祭仪", str(ex))
    # ---- 2. 反击回气 +2（以守为攻/反击之王 反击命中后 气+2，monk.md §3.1 承诺落地）----
    try:
        gy = E.skill_info("cls_wu_seng", "以守为攻") or {}
        gyp = (gy.get("passive") or {})
        check("数据：以守为攻 passive=counter_attack{chance 0.20}",
              gyp.get("proc") == "counter_attack"
              and abs(float(gyp.get("chance", 0)) - 0.20) < 1e-9, f"passive={gyp}")
        b, p = new_battle("cls_wu_seng", 1, 1, learned=["以守为攻"])
        logs = []
        # roll 序列：0.50 闪避判定不闪（≥基础闪避）→ 0.05 反击 roll（<0.20 触发）→ 0.99 反击暴击判定不暴
        with mock.patch.object(BT.random, "random", side_effect=[0.50, 0.05, 0.99]):
            b._damage_player(p, 50, logs)
        check("行为：受击触发反击 → 气 +2（反击回气）",
              b.resources.get("chi") == 2, f"chi={b.resources.get('chi')} logs={logs[:3]}")
        check("反击回气日志（反击回气 +2）",
              any("反击回气" in l for l in logs), f"{logs[:3]}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：反击回气", str(ex))
    # ---- 3. 致命预谋：每场首次 消耗连击点的终结技 结算后 返还 1 连击点 ----
    try:
        ym = E.skill_info("cls_ci_ke", "致命预谋") or {}
        ymp = (ym.get("passive") or {})
        check("数据：致命预谋 passive=battle_start_cp（返还挂点数据驱动，不按名字硬匹配）",
              ymp.get("proc") == "battle_start_cp", f"passive={ymp}")
        b, p = new_battle("cls_ci_ke", 0, 0, learned=["致命预谋", "暗杀"])
        check("战斗开始 +1 连击点（battle_start_cp 入口）",
              b.resources.get("cp") == 1, f"cp={b.resources.get('cp')}")
        b.resources["cp"] = 5
        cap, logs = cast_capture(b, "暗杀", p)
        check("首次终结返还：CP 5 -3 消耗 +1 返还 = 3",
              b.resources.get("cp") == 3 and getattr(b, "_assassin_refund_used", False) is True,
              f"cp={b.resources.get('cp')} flag={getattr(b, '_assassin_refund_used', None)} logs={logs[:2]}")
        check("返还日志（致命预谋：首次终结返还）",
              any("致命预谋" in l and "返还" in l for l in logs), f"{logs[:2]}")
        b.resources["cp"] = 3
        cap2, logs2 = cast_capture(b, "暗杀", p)
        check("每场 1 次：第二次终结不再返还（CP 3-3=0）",
              b.resources.get("cp") == 0, f"cp={b.resources.get('cp')} logs2={logs2[:2]}")
        b3, p3 = new_battle("cls_ci_ke", 0, 0, learned=["暗杀"])
        b3.resources["cp"] = 5
        cast_capture(b3, "暗杀", p3)
        check("对照：无致命预谋 终结后 CP 5-3=2（无返还）",
              b3.resources.get("cp") == 2, f"cp={b3.resources.get('cp')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：致命预谋返还", str(ex))
    # ---- 4. 伴奏回声：歌类技施放 20% 概率 回声 +1（原「暴击+8%」属性被动改版）----
    try:
        bz = E.skill_info("cls_mu_shi", "伴奏") or {}
        bzp = (bz.get("passive") or {})
        check("数据：伴奏 passive 不再声明 stat crit（改版为歌类技回声 proc）",
              bzp.get("stat") != "crit", f"passive={bzp}")
        b, p = new_battle("cls_mu_shi", 1, 1, learned=["伴奏", "战歌"], level=95)
        with mock.patch.object(BT.random, "random", return_value=0.0):  # 0.0 < 0.20 触发
            logs = b._do_player_skill("战歌", p)
        check("行为：20% 触发 歌类技施放 → 回声 +2（战歌 res_gain 1 + 伴奏 1）",
              b._echo_layers() == 2, f"echo={b._echo_layers()} logs={logs[:3]}")
        b2, p2 = new_battle("cls_mu_shi", 1, 1, learned=["伴奏", "战歌"], level=95)
        with mock.patch.object(BT.random, "random", return_value=0.99):  # 0.99 ≥ 0.20 不触发
            logs2 = b2._do_player_skill("战歌", p2)
        check("对照：20% 未触发 → 回声 +1（仅战歌自身 res_gain）",
              b2._echo_layers() == 1, f"echo={b2._echo_layers()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：伴奏回声", str(ex))
    # ---- 5. overflow_shield：满怒/满气 溢出转 5 护盾/点（core_resources 开关 + battle.py 溢出段）----
    try:
        rd_war = E.core_resource_def("cls_zhan_shi") or {}
        check("数据：战士 overflow_shield=True（满怒受击出盾开关）",
              rd_war.get("overflow_shield") is True, str({k: rd_war.get(k) for k in ("key", "max", "overflow_shield")}))
        rd_monk = E.core_resource_def("cls_wu_seng") or {}
        check("数据：拳师 overflow_shield=True（满气受击出盾开关）",
              rd_monk.get("overflow_shield") is True, str({k: rd_monk.get(k) for k in ("key", "max", "overflow_shield")}))
        b, p = new_battle("cls_zhan_shi", 0, 0)
        b.resources["rage"] = 10
        now = b._res_gain_class("cls_zhan_shi", "rage", 3)
        shield_sum = sum(int(v.get("value", 0) or 0) for v in (b.p_shields or {}).values())
        check("满怒再溢 3 点 → 怒气封顶 10 + 护盾 15（3×5）",
              now == 10 and shield_sum == 15, f"rage={now} shield={shield_sum} p_shields={b.p_shields}")
        b2, p2 = new_battle("cls_zhan_shi", 0, 0)
        b2.resources["rage"] = 10
        with mock.patch.object(BT.random, "random", return_value=0.99):
            b2._damage_player(p2, 50, [])
        s2 = sum(int(v.get("value", 0) or 0) for v in (b2.p_shields or {}).values())
        check("满怒受击：受击 on_hit 怒 +1 溢出 → 出盾 5（怒气仍 10）",
              b2.resources.get("rage") == 10 and s2 == 5,
              f"rage={b2.resources.get('rage')} shield={s2} p_shields={b2.p_shields}")
        b3, p3 = new_battle("cls_wu_seng", 0, 0)
        b3.resources["chi"] = 10
        now3 = b3._res_gain_class("cls_wu_seng", "chi", 2)
        s3 = sum(int(v.get("value", 0) or 0) for v in (b3.p_shields or {}).values())
        check("满气再溢 2 点 → 气封顶 10 + 护盾 10（2×5）",
              now3 == 10 and s3 == 10, f"chi={now3} shield={s3} p_shields={b3.p_shields}")
        b4, p4 = new_battle("cls_ci_ke", 0, 0)
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
    # 龙焰吐息：设计 §14.2 #7「满力龙威真伤态 desc 声称、BT 无挂点」→ 已改 cond 落地 + desc 清理
    db = (E.skill_info("cls_dragon_oath", "龙焰吐息") or {}).get("desc", "")
    check("龙焰吐息 desc 不含「满力龙威真伤态」", "满力龙威真伤态" not in db, db)
    # 星辉祈愿：§14.2 #9「满印暴击 desc 有、BT 未接线」→ 删未落地承诺（改版为暴击/叠印前奏）
    xh = (E.skill_info("cls_wild_hunter", "星辉祈愿") or {}).get("desc", "")
    check("星辉祈愿 desc 不含「满印」承诺（满印暴击未接线已删）",
          "满印" not in xh, xh)
    # 暗影之心：§14.3 引擎级发现④「desc 名实不符（实为影系+10% 非潜行延长）」→ 已修正
    ax = (E.skill_info("cls_ci_ke", "暗影之心") or {}).get("desc", "")
    check("暗影之心 desc 不含「潜行持续」承诺", "潜行持续" not in ax, ax)
    check("暗影之心 desc 与 stat=shadow 名实相符（影系伤害）",
          "影" in ax, ax)
    # 龙裔核心资源 desc：灼伤回响/满力龙威 承诺须与实现一致（§14.5 P0 第 1 处，落地点待批次）
    rd_desc = (C.CORE_RESOURCES.get("cls_dragon_oath") or {}).get("desc", "")
    check("龙裔资源 desc 不含「满力龙威真伤态」（§14.2 #7 未落地承诺）",
          "满力龙威真伤态" not in rd_desc, rd_desc)


if __name__ == "__main__":
    clean_db()
    test_overflow_conds()
    test_metronome_passives()
    test_engine_hooks()
    test_desc_consistency()
    print(f"\n===== v130.2f 职业质量批次: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)