# -*- coding: utf-8 -*-
"""v121 审计修复回归测试：覆盖审计发现并已修复的问题。

覆盖：
  1. 敌方 spd_down 减速改变其 CTB 行动频率（审计 P1-1，battle._after_actor_ct("e") buffed spd）
  2. 敌方睡眠按回合递减（审计 P1-2：_enemy_turn 不再多重递减，只走 _end_round）
  3. 玩家被控跳过时敌方同步时间流逝（审计 P2-1：统一 _after_actor_ct("p")）
  4. 召唤援军带 ct=-spd（审计 P2-2：_summon_minions）
  5. 防御连动下每次行动伤害减半（单机 _enemy_phase defend=True）
  6. 副本 _instance_apply_enemy_act_ct 用 buffed spd（spd_down 单位 cost 变大）
  7. 副本超时自动防御同步队友 ct 时间流逝
  8. 副本切怪/换层重置玩家 ct（_instance_reset_player_cts）
"""
import sys, os
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
    logs, ended = b.player_turn("attack", None, make_player())
    # 有减速（spd_down → 敌方有效 20 → cost 5）：同窗口内敌方行动次数应减少
    b2 = BT.Battle("monster", make_enemy(40), player=make_player())
    b2.e_buffs["spd_down"] = 2
    cnt = [0]
    orig = BT.Battle._after_actor_ct
    def wrap(self, side, unit=None, player=None):
        if side == "e":
            cnt[0] += 1
        return orig(self, side, unit, player)
    BT.Battle._after_actor_ct = wrap
    logs2, ended2 = b2.player_turn("attack", None, make_player())
    BT.Battle._after_actor_ct = orig
    check("减速后敌方当段行动次数减少", cnt[0] <= 3, f"enemy_acts={cnt[0]}（未减速对比需 >3）")
    # 直接验证 cost 计算：减速后 e_cost 变大
    b3 = BT.Battle("monster", make_enemy(40), player=make_player())
    cost0 = b3._ct_cost(b3._enemy_stats().get("spd", 0))
    b3.e_buffs["spd_down"] = 2
    cost1 = b3._ct_cost(b3._enemy_stats().get("spd", 0))
    check("减速后敌方 cost 变大", cost1 > cost0, f"{cost0} -> {cost1}")


def test_2_sleep_round_decay():
    print("【2. 敌方睡眠按回合递减（P1-2 修复）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 5, 40  # 敌方快 → 连动窗口大
    b = BT.Battle("monster", make_enemy(40, atk=1), player=make_player())
    b.e_buffs["sleep"] = 3
    # 防御一回合（不打醒；敌方连动多次）
    logs, ended = b.player_turn("defend", None, make_player())
    check("睡眠一回合只递减 1（_end_round）", b.e_buffs.get("sleep", 0) == 2,
          f"sleep={b.e_buffs.get('sleep')}（多重递减会直接清零）")


def test_3_stun_skip_time_flow():
    print("【3. 玩家被控跳过时敌方时间流逝（P2-1 修复）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 20, 10
    b = BT.Battle("monster", make_enemy(10), player=make_player())
    b.p_buffs["stun"] = 1
    e_ct0 = b.enemy["ct"]
    p = make_player()
    logs, ended = b.player_turn("attack", None, p)
    # 敌方 ct 应随玩家被控跳过的 time-flow 减少（e_ct0 - p_cost）
    check("被控跳过后敌方 ct 同步流逝", b.enemy["ct"] < e_ct0,
          f"e_ct {e_ct0} -> {b.enemy['ct']}")


def test_4_summon_minion_ct():
    print("【4. 召唤援军带 ct=-spd（P2-2 修复）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    b = BT.Battle("monster", make_enemy(40), player=make_player())
    mins = b._summon_minions(2)
    check("援军 ct 已初始化 = -spd", all(abs(m.get("ct", 0) + float(m.get("spd", 0))) < 1e-9 for m in mins),
          str([m.get("ct") for m in mins]))


def test_5_defend_chain_reduce():
    print("【5. 防御连动下每次行动减半（单机 defend=True）】")
    clean_db()
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    _SPD["p"], _SPD["e"] = 5, 40  # 敌方快 → 连动多次
    b = BT.Battle("monster", make_enemy(40, atk=100), player=make_player())
    p = make_player(999999)
    logs, ended = b.player_turn("defend", None, p)
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


def test_6_inst_apply_enemy_act_ct_buffed_spd():
    print("【6. 副本敌方 ct 结算用 buffed spd（P1-1 instance 侧）】")
    clean_db()
    inst = InstanceCmds()
    orig_cur = InstanceCmds._instance_current_members
    InstanceCmds._instance_current_members = lambda s_self, g, st: [str(m) for m in st["members"]]
    try:
        st = _st_basic()
        e1 = st["enemies"][0]
        inst._instance_apply_enemy_act_ct(st, "g1", e1)
        # spd_down 后有效 spd 20 → cost 5；单位 ct = -40 + 5 = -35；玩家 ct = -20 - 5 = -25
        check("buffed spd cost 生效（ct 结算正确）",
              abs(e1["ct"] - (-35.0)) < 1e-6 and abs(st["players"]["p1"]["ct"] - (-25.0)) < 1e-6,
              f"e_ct={e1['ct']} p_ct={st['players']['p1']['ct']}")
    finally:
        InstanceCmds._instance_current_members = orig_cur


def test_7_inst_auto_defend_teammate_flow():
    print("【7. 副本超时自动防御同步队友时间流逝】")
    clean_db()
    inst = InstanceCmds()
    orig_cur = InstanceCmds._instance_current_members
    InstanceCmds._instance_current_members = lambda s_self, g, st: [str(m) for m in st["members"]]
    try:
        st = _st_basic()
        st["players"]["p2"] = {"name": "B", "qq_id": "p2", "spd": 10, "ct": -10, "hp": 500,
                               "max_hp": 500, "rank": 2, "reach": 2, "buffs": {}, "stacks": {},
                               "defending": False, "charging": None}
        st["members"] = ["p1", "p2"]
        st["alive"]["p2"] = True
        st["p_buffs"]["p2"] = {}
        st["p_food_effects"]["p2"] = []
        st["p_defending"]["p2"] = False
        p2_ct0 = st["players"]["p2"]["ct"]
        logs = inst._instance_auto_defend_player(st, "g1", "p1")
        check("队友 ct 同步 -cost", st["players"]["p2"]["ct"] < p2_ct0,
              f"p2 {p2_ct0} -> {st['players']['p2']['ct']}")
        check("防御者自身 +cost", st["players"]["p1"]["ct"] > -20.0, f"p1 ct={st['players']['p1']['ct']}")
        check("敌方 -cost", st["enemies"][0]["ct"] < -40.0, f"e_ct={st['enemies'][0]['ct']}")
    finally:
        InstanceCmds._instance_current_members = orig_cur


def test_8_inst_reset_player_cts():
    print("【8. 副本换战重置玩家 ct（_instance_reset_player_cts）】")
    clean_db()
    inst = InstanceCmds()
    st = _st_basic()
    st["players"]["p1"]["ct"] = 45.0
    st["enemies"] = []
    inst._instance_reset_player_cts(st)
    check("玩家 ct 重置为 -spd", abs(st["players"]["p1"]["ct"] - (-20.0)) < 1e-6,
          f"p1 ct={st['players']['p1']['ct']}")


def main():
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    test_1_spd_down_enemy_frequency()
    test_2_sleep_round_decay()
    test_3_stun_skip_time_flow()
    test_4_summon_minion_ct()
    test_5_defend_chain_reduce()
    test_6_inst_apply_enemy_act_ct_buffed_spd()
    test_7_inst_auto_defend_teammate_flow()
    test_8_inst_reset_player_cts()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed


if __name__ == "__main__":
    sys.exit(main())
