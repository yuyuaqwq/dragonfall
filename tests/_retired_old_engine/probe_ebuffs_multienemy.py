# -*- coding: utf-8 -*-
"""e_buffs 收口前多怪行为验证：构造古王+核心双怪，验证 debuff 挂错人 bug。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_ebuffs_probe.db")
os.environ["GWEN_GAME_DB"] = _DB

from data.plugins.dragonfall.game import battle as BT

def main():
    # 造双怪：古王(主) + 王冠核心(副)
    boss = {"name": "古王", "hp": 500, "max_hp": 500, "atk": 50, "matk": 40,
            "def": 30, "mdef": 25, "spd": 8, "is_boss": True}
    core = {"name": "王冠核心", "hp": 200, "max_hp": 200, "atk": 20, "matk": 15,
            "def": 10, "mdef": 10, "spd": 12}
    b = BT.Battle(enemies=[boss, core], player={"name": "测试", "class_name": "cls_ci_ke",
                  "hp": 300, "max_hp": 300, "atk": 60, "def": 20, "spd": 10,
                  "resources": {}, "buffs": {}})
    print("enemies:", [u.get("name") for u in b.enemies])
    print("e_buffs property = 主怪 buffs?:", b._tgt_buffs() is b.enemies[0].get("buffs") or (b._tgt_buffs() == b.enemies[0].setdefault("buffs", {})))
    print("b.enemy 是主怪(古王)?:", b.enemy.get("name"))

    # 场景1：对【王冠核心】(副怪) 施放减速 —— 走 _skill_hit_settle / _tgt 指向副怪时写 debuff
    # 用 _tgt_buffs() 模拟新路径（直接操作副怪）
    b.enemies[1].setdefault("buffs", {})["spd_down"] = 2
    print("\n场景1 直接写副怪 buffs → 副怪:", b.enemies[1]["buffs"])
    print("  主怪 buffs:", b.enemies[0].get("buffs"))
    print("  e_buffs (共享别名) =", dict(b._tgt_buffs()), "← 看不到副怪的 spd_down = 显示层 bug 复现")

    # 场景2：老代码路径 battle.e_buffs["stun"]=1 —— 会挂到主怪
    b._tgt_buffs()["stun"] = 1
    print("\n场景2 battle._tgt_buffs()['stun']=1 → 挂到当前目标:", b.enemies[0]["buffs"])
    print("  副怪 buffs:", b.enemies[1]["buffs"], "← stun 没挂副怪（若意图是对副怪施放=挂错）")

    # 显示层模拟（combat.py L1687 逻辑）
    ebuf = [k for k, v in b._tgt_buffs().items() if v and not isinstance(v, dict)]
    print("\n状态栏 e_buffs 显示:", ebuf, "← 只含主怪 buff")

if __name__ == "__main__":
    main()
