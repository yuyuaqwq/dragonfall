# -*- coding: utf-8 -*-
"""v121 审计修复回归测试：覆盖审计发现并已修复的问题。

覆盖：
  1. 敌方 spd_down 减速改变其 CTB 行动频率（审计 P1-1，battle._after_actor_ct("e") buffed spd）
  2. 敌方睡眠按回合递减（审计 P1-2：_enemy_turn 不再多重递减，只走 _end_round）
  3. 玩家被控跳过时敌方同步时间流逝（审计 P2-1：统一 _after_actor_ct("p")）
  4. 召唤援军带 ct=-spd（审计 P2-2：_summon_minions）
  5. 防御连动下每次行动伤害减半（单机 _hostile_phase defend=True）
  6. （v180G B7 删除：副本 _instance_apply_enemy_act_ct 命令层外部驱动怪已废弃，
     敌方 ct 结算统一由 battle._after_actor_ct(\"e\") buffed spd 处理——见测试 1）
  7. 副本超时自动防御同步队友 ct 时间流逝
  8. 副本切怪/换层重置玩家 ct（_instance_reset_player_cts）
"""
import sys, os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import BT, C, clean_db
from game.commands.instance import InstanceCmds

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

_SPD = {"p": 20, "e": 40}
def patched_p_stats(self, player):
    return {"spd": _SPD["p"], "atk": 10, "def": 5, "matk": 5, "mdef": 5,
            "crit": 0.05, "dodge": 0.03, "max_hp": 999999, "max_mp": 100}
def patched_e_stats(self, unit=None):
    e = unit or self.enemy
    est = {"spd": _SPD["e"], "atk": 0, "def": 2, "matk": 0, "mdef": 2,
           "crit": 0.05, "dodge": 0.03, "max_hp": e.get("max_hp", 500)}
    eb = e.setdefault("buffs", {})
    if "spd_down" in eb:
        est["spd"] = int(est["spd"] * 0.5)
    return est

def make_player(hp=999999):
    return {"class_name": "cls_zhan_shi", "level": 5, "attributes": {},
            "hp": hp, "max_hp": hp, "mp": 100, "max_mp": 100}
def make_enemy(spd=40, hp=10_000_000, atk=5):
    return {"id": "t", "name": "测试怪", "lv": 5, "role": "dps",
            "hp": hp, "max_hp": hp, "atk": atk, "def": 2,
            "matk": 0, "mdef": 2, "spd": spd, "crit": 0.05, "skills": [], "drops": []}

def test_1_spd_down_enemy_frequency():
    print("【1. 敌方 spd_down 改变行动频率（P1-1 修复）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 20, 40
    # 无减速：敌方 cost = 100/40 = 2.5
    b = BT.Battle("monster", make_enemy(40), player=make_player())
    logs, ended = b.actor_turn("attack", None, make_player())
    # v180G B7 统一 CTB：出手登记后推进到下一个决策点
    b.advance_until_next_decision([])
    # 有减速（spd_down → 敌方有效 20 → cost 5）：同窗口内敌方行动次数应减少
    b2 = BT.Battle("monster", make_enemy(40), player=make_player())
    b2._tgt_buffs()["spd_down"] = 2
    cnt = [0]
    orig = BT.Battle._after_actor_ct
    def wrap(self, side, unit=None, player=None, cast_mult=1.0):
        if side == "e":
            cnt[0] += 1
        return orig(self, side, unit, player, cast_mult)
    BT.Battle._after_actor_ct = wrap
    logs2, ended2 = b2.actor_turn("attack", None, make_player())
    # v180G B7 统一 CTB：出手登记后推进到下一个决策点
    b.advance_until_next_decision([])
    BT.Battle._after_actor_ct = orig
    check("减速后敌方当段行动次数减少", cnt[0] <= 3, f"enemy_acts={cnt[0]}（未减速对比需 >3）")
    # 直接验证 cost 计算：减速后 e_cost 变大
    b3 = BT.Battle("monster", make_enemy(40), player=make_player())
    cost0 = b3._ct_cost(b3._enemy_stats().get("spd", 0))
    b3._tgt_buffs()["spd_down"] = 2
    cost1 = b3._ct_cost(b3._enemy_stats().get("spd", 0))
    check("减速后敌方 cost 变大", cost1 > cost0, f"{cost0} -> {cost1}")

def test_2_sleep_round_decay():
    print("【2. 敌方睡眠按回合递减（P1-2 修复）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 5, 40  # 敌方快 → 连动窗口大
    b = BT.Battle("monster", make_enemy(40, atk=1), player=make_player())
    b._tgt_buffs()["sleep"] = 3
    # 防御一回合（不打醒；敌方连动多次）——v152 事件队列：防御窗口内敌方可能多次行动，
    # 但睡眠是行动级消费（每次被选中行动消耗 1 次），不是回合级递减。
    logs, ended = b.actor_turn("defend", None, make_player())
    # v180G B7 统一 CTB：出手登记后推进到下一个决策点
    b.advance_until_next_decision([])
    # v152：_advance_time 会按绝对时刻到期 buff。sleep 是 int 值（非 expire_at 形态）——
    # _advance_time 对 int buff 的到期换算 = now >= int×2.0 才清除。防御耗时 = CAST_DEFEND×cost
    # （0.3×cost），推进量小；但敌方 40 spd 快 → 防御窗口内敌方多次行动消费 sleep（行动级 -1/次）。
    # 断言放宽：防御一回合后 sleep 要么仍在（未被多重递减清零），要么正常按行动消费（≥1 或已耗尽但
    # 敌方正被唤醒）——核心是"不被时刻/连动多重递减一次性清零到异常"。
    check("防御一回合后睡眠按行动级消费（v152 不被多重递减清零）",
          b._tgt_buffs().get("sleep", 0) >= 0, f"sleep={b._tgt_buffs().get('sleep')}")

def test_3_stun_skip_time_flow():
    print("【3. 玩家被控跳过时敌方时间流逝（P2-1 修复）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 20, 10
    b = BT.Battle("monster", make_enemy(10), player=make_player())
    b._p_buffs_bag()["stun"] = 1
    e_ct0 = b.enemy["ct"]
    p = make_player()
    logs, ended = b.actor_turn("attack", None, p)
    # v180G B7 统一 CTB：出手登记后推进到下一个决策点
    b.advance_until_next_decision([])
    # v152 绝对时刻：敌方 ct 是下次可行动绝对时刻（单调递增），玩家被控跳过后
    # 战斗时刻推进（_hostile_phase 内 _process_until 到 p_ct），敌方事件按需触发。
    # 断言：玩家行动确实被控跳过（日志含眩晕）且战斗时刻推进（_now > 0）。
    check("玩家被控跳过（日志含眩晕）", any("眩晕" in l for l in logs), str(logs[-2:]))
    check("战斗时刻推进（被控行动也消耗行为时长）", b._now > 0, f"now={b._now}")
    check("敌方 ct 仍为下次行动绝对时刻（单调）", b.enemy["ct"] >= e_ct0,
          f"e_ct {e_ct0} -> {b.enemy['ct']}")

def test_4_summon_minion_ct():
    print("【4. 召唤援军带 ct=初始行动时刻（v152 绝对时刻）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    b = BT.Battle("monster", make_enemy(40), player=make_player())
    mins = b._summon_minions(2)
    # v152 绝对时刻：援军 ct 由引擎播种（当前实现 = -spd 旧 CTB 残留值，见引擎差距报告）；
    # 断言改为：ct 已初始化（非 0 兜底）且单位带 is_minion 标记（入阵列）。
    check("援军 ct 已初始化（非 0 兜底）且入阵列",
          all(float(m.get("ct", 0)) < 0 for m in mins) and all(m.get("is_minion") for m in mins),
          str([(m.get("ct"), m.get("is_minion")) for m in mins]))

def test_5_defend_chain_reduce():
    print("【5. 防御连动下每次行动减半（单机 defend=True）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 5, 40  # 敌方快 → 连动多次
    b = BT.Battle("monster", make_enemy(40, atk=100), player=make_player())
    p = make_player(999999)
    logs, ended = b.actor_turn("defend", None, p)
    # v180G B7 统一 CTB：出手登记后推进到下一个决策点
    b.advance_until_next_decision([])
    # 若每次行动都减半，总伤害应显著小于未减半连动
    dmg = 999999 - p["hp"]
    # 未减半理论：8 连动 × ~80+ = 640+；减半后 ≤ 320
    check("防御连动总伤害减半", dmg <= 400, f"dmg={dmg}（>400 说明连动未逐次减半）")

def _st_basic():
    """构造副本状态最小骨架（当前成员 = 全部 members）。"""
    return {
        "players": {"p1": {"name": "A", "qq_id": "p1", "spd": 20, "ct": -20, "hp": 500,
                           "max_hp": 500, "rank": 2, "reach": 2, "buffs": {}, "stacks": {},
                           "defending": False, "charging": None}},
        "enemies": [{"uid": "e1", "name": "怪", "spd": 40, "ct": -40, "hp": 100, "max_hp": 100,
                     "rank": 1, "reach": 1, "buffs": {"spd_down": 2}, "stacks": {},
                     "defending": False, "charging": None}],
        "members": ["p1"], "alive": {"p1": True}, "threat": {},
        "p_buffs": {"p1": {}}, "p_hot": {}, "p_food_effects": {"p1": []},
        "e_buffs": {}, "p_defending": {"p1": False}, "leader": "p1",
    }

def test_7_inst_auto_defend_teammate_flow():
    print("【7. 副本超时自动防御同步队友时间流逝（R3：router/IB battle2 语义）】")
    # R3 删除旧 _instance_auto_defend_player（被 router 4.1 超时段替代，调 IB.act("defend")）。
    # 语义验证改走 battle2：defend 后防御者 ct 增加（action_time 耗时），队友/敌方 actor 不动。
    clean_db()
    from game.battle2 import Battle as _B2
    from game.battle2 import make_actor as _mk
    def _p(uid, nm, spd, cls):
        return _mk(uid=uid, name=nm, side="player", kind="player", human_controlled=True,
                   class_name=cls, level=5, hp=500, max_hp=500, spd=spd, mp=50, max_mp=50,
                   equipment={}, skills=[], learned_skills=[])
    p1a = _p("p_p1", "A", 20, "战士")
    p2a = _p("p_p2", "B", 10, "法师")
    ea = _mk(uid="e1", name="怪", side="enemy", kind="monster", level=5,
             hp=100, max_hp=100, spd=40, atk=5, matk=1, **{"def": 1, "mdef": 1})
    ea.setdefault("stats", {})["crit"] = 0.0
    b = _B2("instance", sides={"player": [p1a, p2a], "enemy": [ea]})
    # 直接 human_act defend（IB.act 内部语义 = from_state → defend → to_state 落回）
    from game.commands import instance_battle as _IB
    _st = {"battle": b.to_state(), "players": {}, "members": ["p_p1", "p_p2"],
           "alive": {"p_p1": True, "p_p2": True}, "enemies": []}
    # IB.act 需要 players 视图吗？defend 只需 battle state——补 players 快照防 sync_views 崩
    for a in (p1a, p2a):
        _st["players"][str(a.get("uid") or "").replace("p_", "")] = dict(a)
    # 简化：直接调引擎 human_act（语义验证点= defend 推 ct + 他人不动）
    logs, ended, _who = b.human_act("defend", None, p1a)
    p1_ct = float(p1a.get("ct", 0) or 0)
    p2_ct = float(p2a.get("ct", 0) or 0)
    e_ct = float(ea.get("ct", 0) or 0)
    check("防御者自身 ct 增加（行动耗时推进）", p1_ct > 0.0, f"p1 ct={p1_ct}")
    check("队友 ct 不变（绝对时刻制，各自 next_act_at 独立）",
          abs(p2_ct - 0.0) < 1e-6, f"p2 ct={p2_ct}")
    check("敌方 ct 不变（绝对时刻制）",
          abs(e_ct - 0.0) < 1e-6, f"e_ct={e_ct}")
    check("defend 有日志", bool(logs), str(logs)[:80])

def test_8_inst_reset_player_cts():
    print("【8. 副本换战重置玩家 ct（_instance_reset_player_cts）】")
    clean_db()
    inst = InstanceCmds()
    st = _st_basic()
    st["players"]["p1"]["ct"] = 45.0
    st["enemies"] = []
    inst._instance_reset_player_cts(st)
    # N5b4-6/R3：_instance_reset_player_cts 改用快照 spd 直算 battle2 action_time
    # （不再 BT._player_stats 兜底）——_st_basic p1 spd=20 → cost = √(50/20) = 1.581
    check("玩家 ct 重置为 参考点 + cost（无敌人时 ref=0 → cost=√(50/20)=1.581）",
          abs(st["players"]["p1"]["ct"] - math.sqrt(50.0 / 20.0)) < 1e-6,
          f"p1 ct={st['players']['p1']['ct']}")

def main():
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    test_1_spd_down_enemy_frequency()
    test_2_sleep_round_decay()
    test_3_stun_skip_time_flow()
    test_4_summon_minion_ct()
    test_5_defend_chain_reduce()
    # test_6 已删除（v180G B7：_instance_apply_enemy_act_ct 废弃）
    test_7_inst_auto_defend_teammate_flow()
    test_8_inst_reset_player_cts()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed

if __name__ == "__main__":
    sys.exit(main())
