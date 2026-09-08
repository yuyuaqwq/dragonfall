# -*- coding: utf-8 -*-
"""N5b4-1 验证：命令层展示辅助函数在 battle2 战斗上正确工作。

展示函数（combat.CombatCmds._status_line/_resource_line/_battle_footer/
_battle_formation_panel）N5b4-1 改读 player dict + b.sides——本测试用
battle2 Battle 构造真实战斗（装备装配 → 开战 → 出手挂 buff → 展示），
断言：
- 玩家 buff dict 形态（N7.1 {expire:绝对秒}）折算剩余刻显示
- 护盾 expire_at 折算
- 敌方状态（battle2 actor buffs 同 dict 形态）
- 面板/页脚输出不崩（battle2 无 .enemies 属性 → sides 读法）

跑法：python tests/test_battle2_n5b4_display.py
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n5b4_display.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game.battle2 import config as _b2config  # noqa: E402
_b2config.load_game_defaults()  # noqa: E402
from game.battle2 import Battle as B2, make_actor  # noqa: E402
from game.commands.combat import CombatCmds  # noqa: E402

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


def mk_player():
    return {"qq_id": "1001", "group_id": "g1", "name": "展示勇者", "class_name": "战士",
            "level": 10, "hp": 200, "mp": 50, "max_hp": 200, "max_mp": 50,
            "equipment": {}, "class_tier": 0, "attributes": None,
            "evolve_path": 0, "race": None, "learned_skills": [],
            "resources": {"rage": 3}, "stacks": {}, "buffs": {}, "shields": {}}


def mk_enemy():
    return make_actor(uid="e1", name="山贼头目", side="enemy", kind="monster",
                      human_controlled=False, level=10,
                      hp=3000, max_hp=4000, atk=20, spd=10,
                      **{"def": 10})


def new_battle(player, enemy):
    sides = {"player": [make_actor(uid="p1", name=player.get("name", "你"),
                                   side="player", kind="player",
                                   human_controlled=True, class_name="战士",
                                   level=10, hp=player.get("hp", 200),
                                   max_hp=player.get("max_hp", 200),
                                   mp=player.get("mp", 50), max_mp=50,
                                   atk=40, spd=50, equipment={},
                                   skills=[], learned_skills=[],
                                   **{"def": 10})],
             "enemy": [enemy]}
    return B2("monster", sides=sides, title_bonus={})


def test_status_line_battle2_buffs():
    print("【N5b4-1 battle2 dict buff 形态折算】")
    cmds = CombatCmds.__new__(CombatCmds)
    player = mk_player()
    enemy = mk_enemy()
    b = new_battle(player, enemy)
    focus = b.focus()
    # battle2 buff dict 形态：atk_up 绝对到期 50.0（now=0 → 剩 50 刻）
    focus.setdefault("buffs", {})["atk_up"] = {"expire": 50.0, "stat": "atk",
                                                "op": "mul", "mult": 1.3}
    # 控制类 dict（stun 剩 3 刻：now=0 + turns 3）
    focus["buffs"]["stun"] = {"expire": 3.0, "mode": "skip"}
    # 护盾 dict：expire_at 折算（now=0，剩 5 刻）
    focus.setdefault("shields", {})["we_test"] = {"value": 100, "expire_at": 5.0}
    # 真实命令层流程：行动后 sync_player_from_actor 回写 player dict（展示读 player）
    from game.services import battle2_bridge as BR
    BR.sync_player_from_actor(player, focus)
    s = cmds._status_line(player, b)
    check("atk_up dict → 剩50刻", "⚔️攻击↑(剩50刻)" in s, s)
    check("stun dict → 剩3刻", "🌀眩晕(剩3刻)" in s, s)
    check("护盾 100 → 5刻", "✨护盾100(5刻)" in s, s)
    # 敌方 dict buff（def_down 剩 8 刻）
    enemy.setdefault("buffs", {})["def_down"] = {"expire": 8.0, "stat": "def",
                                                  "op": "mul", "mult": 0.8}
    s2 = cmds._status_line(player, b)
    check("敌方 def_down dict → 剩8刻", "💔破甲(剩8刻)" in s2, s2)


def test_resource_and_footer_battle2():
    print("【N5b4-1 _resource_line / _battle_footer 在 battle2 上不崩】")
    cmds = CombatCmds.__new__(CombatCmds)
    player = mk_player()
    enemy = mk_enemy()
    b = new_battle(player, enemy)
    focus = b.focus()
    focus.setdefault("buffs", {})["atk_up"] = {"expire": 50.0, "stat": "atk",
                                                "op": "mul", "mult": 1.3}
    # 资源行：player dict 读（战士 rage 3）
    rl = cmds._resource_line(player, b)
    check("资源行含怒气", "怒" in rl and "3" in rl, rl)
    # 页脚整体不崩（battle2 无 .enemies 属性 → sides 读法关键路径）
    f = cmds._battle_footer(player, b, enemy)
    check("页脚含玩家血蓝", "200/200" in f, f)
    check("页脚含站位图怪物", "山贼头目" in f, f)
    # 战斗推进后展示仍不崩（advance 自动怪动一下）
    logs = []
    b.auto_run(logs, max_steps=3)
    f2 = cmds._battle_footer(player, b, enemy)
    check("推进后页脚不崩", isinstance(f2, str) and len(f2) > 0, repr(f2[:100]))


def main():
    print("=== N5b4-1 展示层 battle2 适配测试 ===")
    test_status_line_battle2_buffs()
    test_resource_and_footer_battle2()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
