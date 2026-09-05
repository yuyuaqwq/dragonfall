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
    return {"class_name": "cls_you_xia", "name": "测试", "level": 20, "hp": 800, "max_hp": 1000,
            "mp": 120, "max_mp": 300, "mech_stacks": {}}

def _new_battle(monster=None, player=None):
    """v180-B ①：Battle 状态权威在玩家 actor dict——先不带 player 构造（避免 __init__
    v95.19 用 _player_stats 重算 max_hp/max_mp 覆盖测试给定面板），再绑玩家 actor dict。
    状态经 _p_* helper 惰性建袋注入绑定后的 player。"""
    b = BT.Battle("monster", monster or {"name": "山贼头目", "hp": 3000, "max_hp": 4000})
    b.player = player if player is not None else mk_player()
    return b

def test_status_line():
    print("【战斗状态展示】")
    b = _new_battle()
    b._p_stacks().update({"rage": 5, "bless": 2})  # 重构图：burn/poison/mark 已迁敌方 debuffs
    # v180-B：护盾权威在 player actor dict["shields"]——display 层兼容壳 getattr 已读空，
    # 直接写权威袋（结构同引擎 _add_shield：value + turns/expire_at）
    b._p_shields_bag()["test_shield"] = {"value": 150, "turns": 999}
    b._p_buffs_bag().update({"atk_up": 3, "def_up": 2})
    b.e_buffs.update({"def_down": 2})
    b.enemy["debuffs"] = {"burn": {"n": 3}, "poison": {"n": 3}, "mark": {"n": 2}}
    player = b.player
    s = mixin._status_line(player, b)
    check("玩家叠层显示", "狂暴×5" in s and "神恩×2" in s, s)
    check("玩家buff显示", "攻击↑(剩3刻)" in s and "防御↑(剩2刻)" in s, s)
    check("玩家护盾显示", "✨护盾150" in s, s)
    check("敌方状态显示", "破甲(剩2刻)" in s and "🔥灼烧×3" in s
          and "☠️毒×3" in s and "🎯标记×2" in s, s)
    check("格式有分隔", "🛡️你：" in s and "👹敌：" in s, s)

def test_footer():
    print("【战斗底部】")
    b = _new_battle()
    b._p_stacks().update({"rage": 5})  # v59 叠层存战斗状态
    b._p_buffs_bag().update({"atk_up": 3})
    b.e_buffs.update({"def_down": 2})
    player = b.player
    f = mixin._battle_footer(player, b, b.enemy)
    # v164.1：血量汇总行已删——血量在站位图逐只带出（❤️当前/最大）
    check("站位图怪物血条", "山贼头目 ❤️3000/4000" in f, f)
    check("玩家血蓝", "800/1000" in f and "120/300" in f, f)
    check("状态行追加", "攻击↑(剩3刻)" in f and "破甲(剩2刻)" in f, f)

def test_no_status():
    print("【无状态不显示】")
    b = _new_battle({"name": "野狗", "hp": 50, "max_hp": 50})
    player = b.player
    s = mixin._status_line(player, b)
    check("无状态为空", s == "", repr(s))
    f = mixin._battle_footer(player, b, b.enemy)
    check("footer只有血蓝", "野狗" in f and "🛡️你" not in f, f)

def test_enrage():
    print("【敌方狂暴显示】")
    b = _new_battle({"name": "骷髅王", "hp": 500, "max_hp": 2000, "enraged": True})
    player = b.player
    s = mixin._status_line(player, b)
    check("狂暴标记", "😡狂暴" in s, s)

if __name__ == "__main__":
    test_status_line()
    test_footer()
    test_no_status()
    test_enrage()
    print(f"\n结果: {passed} 通过, 0 失败")
