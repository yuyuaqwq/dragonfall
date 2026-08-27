# -*- coding: utf-8 -*-
"""临时冒烟：验证 v132 新排版（到达视图 + 地图面板同源）——鱼鱼模板对照"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from conftest import C, clean_db
clean_db()

from game.commands import world as W

# 构造玩家
player = {"qq_id": "999999", "group_id": "g1", "name": "测试员", "level": 1,
          "cur_map": "oak_plain", "cur_subarea": "oak_plain_1"}

cmds = W.WorldCmds()

# ---- 1. 野外到达视图（橡木平原·草地边缘）----
cur_map = C.MAP_BY_ID["oak_plain"]
sa = next(s for s in cur_map["subareas"] if s["id"] == "oak_plain_1")
out = cmds._subarea_arrive(player, cur_map, sa, None, None)
print("========== 野外到达视图 ==========")
print(out)
print()

# ---- 2. 城镇到达视图（橡木镇·冒险者广场）----
player2 = dict(player)
player2["cur_map"] = "oak_town"
player2["cur_subarea"] = "oak_town_1"
cur_map2 = C.MAP_BY_ID["oak_town"]
sa2 = next(s for s in cur_map2["subareas"] if s["id"] == "oak_town_1")
out2 = cmds._subarea_arrive(player2, cur_map2, sa2, None, None)
print("========== 城镇到达视图 ==========")
print(out2)