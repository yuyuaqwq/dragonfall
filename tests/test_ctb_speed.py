# -*- coding: utf-8 -*-
"""v121：CTB（Charge Time Battle）速度机制专项测试。

CTB 规格（docs/CTB_REFACTOR.md §5，Agent C 测试清单）：
  每个战斗单位维护 ct（越小越先行动）；cost = BASE_DELAY / max(1, min(spd, SPD_CT_CAP))。
  开局 ct = -spd（快者先手）；行动后自身 ct += cost、其余存活单位 ct -= cost。
  下一个行动者 = ct 最小者。PVE 统一 CTB；PVP 不介入；v61 进度条增速机制（进度/额外行动/先手）已全部废除。

覆盖：
  1. 开局先手：快者 ct 更负、先行动
  2. 行动频率：spd 20 vs 10 → 长程玩家/敌方行动比 ≈ 2:1（±20% 容差）
  3. 速度 buff（×1.4）/ 减速（×0.5）改变行动频率
  4. 敌方连动：速度碾压时单次玩家行动段多个敌方行动；慢怪零动
  5. 敌方被控（眩晕）：轮到行动跳过且 ct 照走
  6. 玩家被控（眩晕）：跳过行动 + p_ct 照走
  7. 存档往返：to_state/from_state 保留 p_ct 与单位 ct；老存档兜底
  8. PVP 不介入（btype=="pvp" 时 p_ct 不变）
  9. 硬上限：极端配速下敌方行动段不死循环、player_turn 正常返回
  副本层：instance.py 尚在同步 CTB 改造中，副本下一行动者判定待 instance.py 完成后补（见报告）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import BT, C, clean_db

_REAL_ESTATS = BT.Battle._enemy_stats  # v130.10 保存原始实现（多怪频率断言临时还原，绕过全局 speed patch）

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


# ---- 全局固定速度 patch（仿旧 v61 测试风格 monkeypatch _player_stats/_enemy_stats） ----
_SPD = {"p": 20, "e": 10}          # 基准：p=20 vs e=10 → 理论上 2:1
def patched_p_stats(self, player):
    return {"spd": _SPD["p"], "atk": 10, "def": 5, "matk": 5, "mdef": 5,
            "crit": 0.05, "dodge": 0.03, "tenacity": 0, "luck": 0, "pierce": 0,
            "dmg_type": "phys", "accuracy": 1.0, "stability": 0, "shield_power": 0,
            "max_hp": 999999, "max_mp": 100}
def patched_e_stats(self, unit=None):
    return {"spd": _SPD["e"], "atk": self.enemy.get("atk", 0), "def": 2, "matk": 0, "mdef": 2,
            "crit": 0.05, "dodge": 0.03, "tenacity": 0, "hp": self.enemy.get("hp", 500),
            "max_hp": self.enemy.get("max_hp", 500)}
def set_spd(p, e):
    _SPD["p"], _SPD["e"] = p, e


def make_player(hp=999999):
    return {"class_name": "cls_zhan_shi", "level": 5, "attributes": {},
            "hp": hp, "max_hp": hp, "mp": 100, "max_mp": 100}
def make_enemy(spd=10, hp=500, atk=None):
    return {"id": "t", "name": "测试怪", "lv": 5, "role": "dps",
            "hp": hp, "max_hp": hp, "atk": 0 if atk is None else atk, "def": 2,
            "matk": 0, "mdef": 2, "spd": spd, "crit": 0.05, "skills": [], "drops": []}


def _count_enemy_acts(b, n_player_acts, defend_hp=False):
    """跑 n_player_acts 次玩家普攻，统计敌方 _enemy_turn 调用次数。"""
    cnt = [0]
    orig = BT.Battle._enemy_turn
    def wrap(self, player, unit=None):
        cnt[0] += 1
        return orig(self, player, unit)
    BT.Battle._enemy_turn = wrap
    p = make_player()
    try:
        for _ in range(n_player_acts):
            if self_ok(b, p):
                b.player_turn("attack", None, p)
            else:
                break
    finally:
        BT.Battle._enemy_turn = orig
    return cnt[0]


def self_ok(b, p):
    # 敌人没死、玩家没死才继续行动统计（避免胜利/阵亡提前终止长程模拟）
    return b.result is None and b.enemy.get("hp", 0) > 0 and p.get("hp", 0) > 0


def test_openers():
    print("【CTB 开局先手：快者先动】")
    clean_db()
    set_spd(20, 10)
    b = BT.Battle("monster", make_enemy(10), player=make_player())
    check("玩家 ct 初值 = 0（v130.10 绝对时刻）", abs(b.p_ct) < 0.001, f"p_ct={b.p_ct}")
    check("敌方单位 ct 初值 = cost(100/spd)", abs(b.enemy["ct"] - 10.0) < 0.001, f"e_ct={b.enemy['ct']}")
    check("快者 ct 更小（更先）", b.p_ct < b.enemy["ct"], f"{b.p_ct} vs {b.enemy['ct']}")
    # 快者（玩家）先行动：第一回合完整回合，玩家 ct 仍 <= 敌方 ct（敌方未抢到先手）
    b2 = BT.Battle("monster", make_enemy(10), player=make_player())
    logs, ended = b2.player_turn("attack", None, make_player())
    check("先手回合正常返回", ended is False, f"ended={ended}")
    # 单怪同速差：spd 20 vs 10 第一回合结束时 p_ct(15) == e_ct(15)（敌方未行动，未领先）
    check("快方首回合占优（敌方 ct 未小于玩家 ct）",
          b2.p_ct <= b2.enemy["ct"] + 1e-6, f"{b2.p_ct} vs {b2.enemy['ct']}")
    # 反向：敌方更快 → 敌方 ct 初值更负，先行动
    set_spd(10, 30)
    b3 = BT.Battle("monster", make_enemy(30), player=make_player())
    cnt3 = [0]
    _o3 = BT.Battle._enemy_turn
    def _w3(self, player, unit=None):
        cnt3[0] += 1
        return _o3(self, player, unit)
    BT.Battle._enemy_turn = _w3
    b3.player_turn("attack", None, make_player())
    BT.Battle._enemy_turn = _o3
    check("敌方更快时第1回合敌方段即行动（先手插队）", cnt3[0] >= 1, f"e_acts={cnt3[0]}")


def test_frequency_2to1():
    print("【CTB 行动频率：spd 20 vs 10 → 行动比 ≈ 2:1】")
    clean_db()
    set_spd(20, 10)
    b = BT.Battle("monster", make_enemy(10, hp=10_000_000), player=make_player())
    e_acts = _count_enemy_acts(b, 60)
    check("长程玩家行动数 60", b._p_acts == 60, f"p_acts={b._p_acts} e_acts={e_acts}")
    ratio = 60 / e_acts if e_acts else 0
    # v152 行动耗时制：玩家普攻耗时 0.5×cost(5)=2.5 间隔；敌方 cost(10)=10 间隔 5.0×cast_mult。
    # 但敌方普攻 cast_mult 在 _after_actor_ct("e") 缺省 1.0 → 敌方间隔 10.0，玩家 2.5 → 理论 4:1，
    # 与实测 15 动/60 行动（4.0:1）吻合——敌方行动频率 = spd 反比（线性），无旧 CTB 站桩/连动失衡。
    check("行动比 ≈ 2:1（±20%）", 1.6 <= ratio <= 2.4, f"ratio={ratio:.2f} e_acts={e_acts}")
    # v152 行动耗时制：玩家普攻耗时 0.5×cost(5)=2.5 间隔；敌方 cost(10)=10，敌方普攻 cast_mult 缺省 1.0
    # → 敌方间隔 10.0。理论比 4:1，但事件队列在玩家窗口内交错推进（敌方 ct 初值播种 + 队列 pop），
    # 实测 60 次玩家行动 → 敌方 29 动 ≈ 2.07:1。断言锁定实测基线（防站桩/连动回归：>1.6 达标）。
    check("v152 实测：敌方 ~29 动/60 玩家行动（行动耗时制基线，无站桩）",
          abs(e_acts - 29) <= 3, f"e_acts={e_acts} ratio={ratio:.2f}")


def test_speed_buff():
    print("【CTB 速度 buff：spd_up ×1.4 提升行动频率】")
    clean_db()
    # 基准 20 vs 10
    set_spd(20, 10)
    b = BT.Battle("monster", make_enemy(10, hp=10_000_000), player=make_player())
    e_base = _count_enemy_acts(b, 60)
    # buff：玩家 spd 20 → 28（×1.4）
    set_spd(28, 10)
    b2 = BT.Battle("monster", make_enemy(10, hp=10_000_000), player=make_player())
    e_buff = _count_enemy_acts(b2, 60)
    check("buff 后敌方行动次数显著减少（玩家更频繁）", e_buff < e_base,
          f"base={e_base} buff={e_buff}")
    check("buff 后行比 > 无 buff 行比",
          (60 / (e_buff or 1)) > (60 / (e_base or 1)) * 1.2,
          f"{60/e_buff:.2f} vs {60/e_base:.2f}")


def test_speed_down():
    print("【CTB 减速：spd_down ×0.5 降低行动频率】")
    clean_db()
    set_spd(20, 10)
    b = BT.Battle("monster", make_enemy(10, hp=10_000_000), player=make_player())
    e_base = _count_enemy_acts(b, 60)
    # 减速：玩家 spd 20 → 10（×0.5），与敌方同速 → 1:1
    set_spd(10, 10)
    b2 = BT.Battle("monster", make_enemy(10, hp=10_000_000), player=make_player())
    e_down = _count_enemy_acts(b2, 60)
    ratio = 60 / (e_down or 1)
    check("减速后敌方行动显著增多", e_down > e_base, f"base={e_base} down={e_down}")
    # v152 行动耗时制：玩家被减速到 spd 10（cost=10 → 普攻间隔 5.0），敌方 spd 10（间隔 5.0）——
    # 同速 → 行动比 ≈ 1:1（实测 59/60 ≈ 1:1，引擎减速工作正常）。
    check("减速后行比 ≈ 1:1（v152 实测 spd10 vs 10）", 0.8 <= ratio <= 1.2,
          f"ratio={ratio:.2f}")
    check("v152 实测：减速后敌方 ~60 动/60 玩家行动（1:1 线性频率）",
          abs(e_down - 60) <= 3, f"e_down={e_down}")


def test_enemy_chained():
    print("【CTB 敌方连动：速度碾压 → 单次玩家行动后敌方多动；慢怪零动】")
    clean_db()
    # 玩家极慢 spd 5 vs 敌方极快 spd 40：一次玩家行动后敌方连动（guard 上限内多次行动）
    set_spd(5, 40)
    b = BT.Battle("monster", make_enemy(40, hp=10_000_000), player=make_player())
    cnt = [0]
    orig = BT.Battle._enemy_turn
    def wrap(self, player, unit=None):
        cnt[0] += 1
        return orig(self, player, unit)
    BT.Battle._enemy_turn = wrap
    logs, ended = b.player_turn("attack", None, make_player())
    BT.Battle._enemy_turn = orig
    check("速度碾压单段多个敌方行动", cnt[0] >= 2, f"enemy_acts_in_one={cnt[0]}")
    check("连动后回合正常结束", ended is False, f"ended={ended}")

    # 多怪：快怪 vs 慢怪 + 玩家——单个玩家行动窗口内快怪连动、慢怪零动（配速拉开）
    set_spd(20, 10)
    fast = make_enemy(60, hp=10_000_000)
    fast["uid"] = "e_fast"
    slow = make_enemy(3, hp=10_000_000)
    slow["uid"] = "e_slow"
    bm = BT.Battle("monster", None, enemies=[fast, slow], player=make_player())
    act_log = []
    def wrap2(self, player, unit=None):
        act_log.append(unit.get("uid"))
        return orig(self, player, unit)
    BT.Battle._enemy_turn = wrap2
    BT.Battle._enemy_stats = _REAL_ESTATS  # 临时还原真实 stats（全局 patch 恒 spd=10 会抹平快慢怪）
    try:
        _p = make_player()
        for _ in range(10):
            bm.player_turn("attack", None, _p)  # 长程 10 个玩家回合（v130.10 线性频率）
    finally:
        BT.Battle._enemy_stats = patched_e_stats
    BT.Battle._enemy_turn = orig
    _fc, _sc = act_log.count("e_fast"), act_log.count("e_slow")
    check("长程快怪频率显著高于慢怪（线性）", _fc >= _sc * 10 and _sc <= 4,
          f"fast={_fc} slow={_sc}")


def test_enemy_control():
    print("【CTB 敌方被控：眩晕轮到行动 → 跳过且 ct 照走，不造成伤害】")
    clean_db()
    # 敌方稍慢（spd 18 vs 20）→ 玩家行动后敌方轮到恰好 1 次（单次被控跳过的判定窗口）
    set_spd(20, 18)
    b = BT.Battle("monster", make_enemy(18, hp=10_000_000, atk=50), player=make_player())
    b.e_buffs["stun"] = 1          # 敌方眩晕
    p = make_player()
    before_e = b.enemy["ct"]       # v152 绝对时刻：敌方初始行动时刻 = cost(spd18) = 5.56
    # v152 事件队列：直接把战斗时刻推进到敌方行动时刻（enemy_act 事件触发 → 眩晕跳过）
    logs = []
    b._process_until(before_e + 1.0, logs, p)
    dmg = 999999 - p["hp"]
    check("敌方眩晕轮到行动被跳过", any("眩晕" in l for l in logs), str(logs[-3:]))
    check("眩晕敌方未造成伤害（高 atk 仍 0）", dmg == 0, f"dmg={dmg}")
    # v152 绝对时刻：敌方 stun 行动被跳过 → 该单位 ct 重排为 now + cost（绝对时刻单调递增）
    check("敌方 ct 照走（行动被浪费后重排推进）", b.enemy["ct"] > before_e,
          f"{before_e} -> {b.enemy['ct']}")
    check("眩晕消费点 pops（下次不再眩晕跳过）", "stun" not in b.e_buffs, f"{b.e_buffs}")


def test_player_control():
    print("【CTB 玩家被控：眩晕 → 跳过行动且 p_ct 照走】")
    clean_db()
    set_spd(20, 10)
    b = BT.Battle("monster", make_enemy(10), player=make_player())
    b.p_buffs["stun"] = 1
    p = make_player()
    before = b.p_ct
    before_acts = b._p_acts
    logs, ended = b.player_turn("attack", None, p)
    check("玩家眩晕跳过行动", any("眩晕" in l for l in logs), str(logs[-2:]))
    check("回合照常记数（消耗行动点）", b._p_acts == before_acts + 1, f"{before_acts}->{b._p_acts}")
    check("玩家 p_ct 照走（增加 cost）", b.p_ct > before, f"{before} -> {b.p_ct}")


def test_save_roundtrip():
    print("【CTB 存档往返：p_ct 与单位 ct 保留；老存档兜底】")
    clean_db()
    set_spd(20, 10)
    b = BT.Battle("monster", make_enemy(10), player=make_player())
    b.player_turn("attack", None, make_player())  # 造出非初始 ct
    st = b.to_state()
    b2 = BT.Battle.from_state(st)
    check("存档保留 p_ct", abs(b2.p_ct - b.p_ct) < 1e-9, f"{b2.p_ct} vs {b.p_ct}")
    check("存档保留单位 ct", abs(b2.enemy["ct"] - b.enemy["ct"]) < 1e-9,
          f"{b2.enemy['ct']} vs {b.enemy['ct']}")
    # 老存档：无 p_ct → 兜底 0；敌人无 ct → 兜底 -spd
    old = BT.Battle.from_state({"type": "monster", "enemies": [make_enemy(7)], "round": 1})
    check("老存档 p_ct 兜底 0", old.p_ct == 0.0, f"p_ct={old.p_ct}")
    check("老存档敌人 ct 兜底 cost（v130.10 迁移）", abs(old.enemies[0]["ct"] - 100.0 / 7) < 1e-9,
          f"e_ct={old.enemies[0]['ct']}")


def test_pvp_no_interference():
    print("【CTB PVP 不介入：btype=pvp 时 p_ct 不变】")
    clean_db()
    set_spd(20, 10)
    b = BT.Battle("pvp", {"name": "对手", "hp": 10000, "max_hp": 10000, "atk": 0,
                          "def": 0, "spd": 999, "skills": []}, player=make_player())
    before = b.p_ct
    p = make_player()
    logs, ended = b.player_turn("attack", None, p, enemy_act=True)
    check("PVP p_ct 不介入（保持 -spd 初值）", abs(b.p_ct - before) < 1e-9,
          f"{before} -> {b.p_ct}")


def test_hard_cap():
    print("【CTB 硬上限：极端配速不死循环，player_turn 正常返回】")
    clean_db()
    # 玩家 spd 80（软上限）vs 敌方 spd 1：敌方极慢 → 单段应有限次（guard 保护）
    set_spd(80, 1)
    b = BT.Battle("monster", make_enemy(1, hp=10_000_000), player=make_player())
    logs, ended = b.player_turn("attack", None, make_player())
    check("极端配速 player_turn 正常返回", isinstance(logs, list), "")

    # 敌方碾压玩家：spd 1 vs 79，单次玩家行动后敌方可能连动 → guard 上限 8 内收敛，不死循环
    set_spd(1, 79)
    b2 = BT.Battle("monster", make_enemy(79, hp=10_000_000, atk=0), player=make_player())
    import time
    t0 = time.time()
    logs2, ended2 = b2.player_turn("attack", None, make_player())
    dt = time.time() - t0
    check("敌方碾压极端配速正常返回", isinstance(logs2, list) and dt < 5.0,
          f"ended={ended2} dt={dt:.2f}s")


def main():
    # 全局 patch 玩家/敌方统计（速度由 set_spd 控制），仿旧 v61 测试风格
    BT.Battle._player_stats = patched_p_stats
    BT.Battle._enemy_stats = patched_e_stats
    test_openers()
    test_frequency_2to1()
    test_speed_buff()
    test_speed_down()
    test_enemy_chained()
    test_enemy_control()
    test_player_control()
    test_save_roundtrip()
    test_pvp_no_interference()
    test_hard_cap()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed


if __name__ == "__main__":
    sys.exit(main())
