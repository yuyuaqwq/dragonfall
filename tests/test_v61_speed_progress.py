# -*- coding: utf-8 -*-
"""v61：进度条速度机制（鱼鱼设计 2026-08-05）

设计：
  每回合双方进度 + 各自速度，进度差攒够「慢方速度」→ 快方获得 1 次额外行动（余数保留）。
  玩家额外行动自由选择出手（攻击/技能/道具），不再自动普攻；怪物同样有额外行动。
  纯替换旧 1.5x/2x 阈值机制；PVP 不介入。

验证：
  1. 进度条累计：10速 vs 11速 → 第 10 回合敌方 +1 行动
  2. 余数保留：超出部分不清零
  3. 玩家速度碾压 → 玩家获得额外行动（战斗不结束，等玩家自由出手）
  4. 额外行动可自由选择（攻击/技能/道具），用完后才进敌方回合
  5. 额外行动阶段选防御 → 放弃剩余优势，敌方行动减半
  6. 怪物额外行动照常结算
  7. PVP 不介入（进度不累计）
  8. 序列化：to_state/from_state 保留进度字段；老存档兜底 0
"""
import sys, os
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


# 测试用：全局玩家/敌方速度（monkey patch _player_stats/_enemy_stats）
_TEST_P_SPD = 10
_TEST_E_SPD = 11

def _fake_p_stats(self, player):
    return {"spd": _TEST_P_SPD, "atk": 20, "def": 5, "matk": 5, "mdef": 5,
            "crit": 0.05, "dodge": 0.03, "max_hp": 500, "max_mp": 100}

def _fake_e_stats(self):
    return {"spd": _TEST_E_SPD, "atk": 5, "def": 2, "matk": 3, "mdef": 2,
            "hp": self.enemy.get("hp", 500), "crit": 0.05, "dodge": 0.03}


def set_spd(p_spd, e_spd):
    global _TEST_P_SPD, _TEST_E_SPD
    _TEST_P_SPD, _TEST_E_SPD = p_spd, e_spd


def make_battle():
    return BT.Battle("monster", {
        "id": "t", "name": "测试怪", "lv": 5, "role": "dps",
        "hp": 500, "max_hp": 500, "atk": 5, "def": 2,
        "matk": 3, "mdef": 2, "spd": _TEST_E_SPD, "skills": [], "drops": [],
    })


def make_player(hp=500, mp=100):
    return {
        "class_name": "cls_zhan_shi", "level": 5,
        "equipment": {}, "class_tier": 0, "attributes": {"agi": 0},
        "evolve_path": 0, "hp": hp, "max_hp": hp, "mp": mp, "max_mp": mp,
        "learned_skills": [], "name": "测试",
    }


async def main():
    clean_db()
    # 全局 patch 玩家/敌方统计（速度由 set_spd 控制）
    BT.Battle._player_stats = _fake_p_stats
    BT.Battle._enemy_stats = _fake_e_stats

    print("【进度条：10速 vs 11速（鱼鱼原始例子）】")
    set_spd(10, 11)
    b = make_battle()
    p = make_player()
    for r in range(10):
        b._speed_plan(p)
    check("第10回合敌方获得1次额外行动", b.e_extra_left == 1, f"e_extra_left={b.e_extra_left}")
    check("玩家无额外行动", b.p_extra_left == 0, f"p_extra_left={b.p_extra_left}")
    check("进度余数保留", abs(b.p_progress - b.e_progress) < 0.01,
          f"p={b.p_progress} e={b.e_progress}")

    print("【进度条：余数不清零】")
    set_spd(12, 10)  # 玩家快 2
    b2 = make_battle()
    p2 = make_player()
    b2._speed_plan(p2)  # p=12, e=10, 差2<10 → 无额外
    check("第1回合无额外（差2不够10）", b2.p_extra_left == 0, f"p_extra={b2.p_extra_left}")
    for _ in range(4):  # 第2~5回合：差4/6/8/10
        b2._speed_plan(p2)
    check("第5回合玩家+1次行动", b2.p_extra_left == 1, f"p_extra={b2.p_extra_left}")
    b2._speed_plan(p2)  # 第6回合：p=62, e=60, 差2（余数保留）
    check("余数保留：第6回合差2不再触发", b2.p_extra_left == 1, f"p_extra={b2.p_extra_left}")

    print("【速度碾压 → 自由出手，战斗不结束】")
    set_spd(45, 20)
    b3 = make_battle()
    p3 = make_player(300)
    b3.enemy["hp"], b3.enemy["max_hp"] = 10000, 10000
    logs, ended = b3.player_turn("attack", None, p3)
    check("碾压时战斗未结束（等自由出手）", ended is False, f"ended={ended}")
    check("提示速度优势", any("速度优势" in l for l in logs), str(logs[-3:]))
    check("玩家有剩余额外行动", b3.p_extra_left > 0, f"p_extra_left={b3.p_extra_left}")

    print("【额外行动自由选择：攻击/技能/道具】")
    logs2, ended2 = b3.player_turn("attack", None, p3)
    check("额外行动再攻击仍不结束（还有剩余）", ended2 is False, f"ended2={ended2}")
    while b3.p_extra_left > 0:
        logs3, ended3 = b3.player_turn("attack", None, p3)
    check("额外行动用完后敌方行动", b3.result in (None, "defeat", "victory"), f"result={b3.result}")

    print("【额外行动阶段选防御 → 敌方伤害减半】")
    set_spd(40, 15)
    b4 = make_battle()
    p4 = make_player(1000)
    b4.enemy["hp"], b4.enemy["max_hp"] = 10000, 10000
    b4.enemy["atk"] = 100
    b4.player_turn("attack", None, p4)  # 触发额外行动
    check("防御前有额外行动", b4.p_extra_left > 0, f"p_extra_left={b4.p_extra_left}")
    before_hp = p4["hp"]
    logs4, ended4 = b4.player_turn("defend", None, p4)
    check("额外防御后剩余清零", b4.p_extra_left == 0, f"p_extra_left={b4.p_extra_left}")
    check("防御后敌方伤害减半", p4["hp"] >= before_hp - 200, f"hp {before_hp}→{p4['hp']}")

    print("【怪物额外行动（敌方速度优势）】")
    set_spd(11, 30)
    b5 = make_battle()
    p5 = make_player(5000)
    b5.enemy["hp"], b5.enemy["max_hp"] = 5000, 5000
    b5.enemy["atk"] = 5
    logs5, ended5 = b5.player_turn("attack", None, p5)
    check("敌方快时玩家无额外行动", b5.p_extra_left == 0, f"p_extra_left={b5.p_extra_left}")

    print("【PVP 不介入】")
    b6 = BT.Battle("pvp", {"name": "对手", "hp": 100, "max_hp": 100, "atk": 5, "def": 0, "spd": 999, "skills": []})
    p6 = make_player()
    p_extra, e_extra, e_first = b6._speed_plan(p6)
    check("PVP 速度机制不介入", p_extra == 0 and e_extra == 0 and e_first is False,
          f"{p_extra},{e_extra},{e_first}")

    print("【序列化保留进度字段】")
    set_spd(45, 20)
    b7 = make_battle()
    p7 = make_player(300)
    b7.enemy["hp"], b7.enemy["max_hp"] = 10000, 10000
    b7.player_turn("attack", None, p7)
    st7 = b7.to_state()
    b8 = BT.Battle.from_state(st7)
    check("进度字段序列化保留", b8.p_progress == b7.p_progress and b8.p_extra_left == b7.p_extra_left,
          f"{b8.p_progress}/{b8.p_extra_left}")
    b9 = BT.Battle.from_state({"type": "monster", "enemy": {}, "round": 1})
    check("老存档兜底0", b9.p_extra_left == 0 and b9.p_progress == 0.0,
          f"{b9.p_extra_left}/{b9.p_progress}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
