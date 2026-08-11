# -*- coding: utf-8 -*-
"""v59 战斗状态展示：buff/叠层/护盾在战斗底部列出"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import battle as BT
from game.commands.combat import CombatCmds

passed = 0
def check(name, cond, detail=""):
    global passed
    assert cond, f"{name}: {detail}"
    passed += 1
    print(f"  ✓ {name}")

mixin = CombatCmds.__new__(CombatCmds)

def mk_player():
    # stage5 核心资源后 _resource_line 需要 class_name
    return {"class_name": "cls_you_xia", "hp": 800, "max_hp": 1000, "mp": 120, "max_mp": 300, "mech_stacks": {}}

def test_status_line():
    print("【战斗状态展示】")
    player = mk_player()
    b = BT.Battle("monster", {"name": "山贼头目", "hp": 3000, "max_hp": 4000})
    b.mech_stacks = {"rage": 5, "burn": 3, "bless": 2}  # v59 叠层存战斗状态
    b.shield = 150
    b.p_buffs = {"atk_up": 3, "def_up": 2}
    b.e_buffs = {"def_down": 2, "poison": 3, "mark": 2}
    s = mixin._status_line(player, b)
    check("玩家叠层显示", "狂暴×5" in s and "灼烧×3" in s, s)
    check("玩家buff显示", "攻击↑(剩3回合)" in s and "防御↑(剩2回合)" in s, s)
    check("玩家护盾显示", "护盾150" in s, s)
    check("敌方状态显示", "破甲(剩2回合)" in s and "中毒(剩3回合)" in s and "标记(剩2回合)" in s, s)
    check("格式有分隔", "🛡️你：" in s and "👹敌：" in s, s)

def test_footer():
    print("【战斗底部】")
    player = mk_player()
    b = BT.Battle("monster", {"name": "山贼头目", "hp": 3000, "max_hp": 4000})
    b.mech_stacks = {"rage": 5}  # v59 叠层存战斗状态
    b.p_buffs = {"atk_up": 3}
    b.e_buffs = {"def_down": 2}
    f = mixin._battle_footer(player, b, b.enemy)
    check("怪物血条", "山贼头目】❤️ 3000/4000" in f, f)
    check("玩家血蓝", "800/1000" in f and "120/300" in f, f)
    check("状态行追加", "攻击↑(剩3回合)" in f and "破甲(剩2回合)" in f, f)

def test_no_status():
    print("【无状态不显示】")
    b = BT.Battle("monster", {"name": "野狗", "hp": 50, "max_hp": 50})
    player = mk_player()
    s = mixin._status_line(player, b)
    check("无状态为空", s == "", repr(s))
    f = mixin._battle_footer(player, b, b.enemy)
    check("footer只有血蓝", "野狗" in f and "🛡️你" not in f, f)

def test_enrage():
    print("【敌方狂暴显示】")
    b = BT.Battle("monster", {"name": "骷髅王", "hp": 500, "max_hp": 2000, "enraged": True})
    player = mk_player()
    s = mixin._status_line(player, b)
    check("狂暴标记", "😡狂暴" in s, s)

if __name__ == "__main__":
    test_status_line()
    test_footer()
    test_no_status()
    test_enrage()
    print(f"\n结果: {passed} 通过, 0 失败")
