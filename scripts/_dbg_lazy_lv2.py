# -*- coding: utf-8 -*-
"""精确复刻战斗胜利 1376-1378 链路：UPDATE exp -> db.update_player -> get_player"""
import sys, os, json, sqlite3, traceback
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
os.chdir(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

DB = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\game_data.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
orig = dict(conn.execute("SELECT * FROM players WHERE qq_id='gm_alt7'").fetchone())
print("gm_alt7 原值: level=%s exp=%s class=%s" % (orig["level"], orig["exp"], orig["class_name"]))

# 模拟影刃场景：level 18, exp 3909（战斗前）
conn.execute("UPDATE players SET level=18, exp=3909 WHERE qq_id='gm_alt7'")
conn.commit()

try:
    from game import db
    from game.store.players import get_player
    # 1376-1377：战斗胜利写库
    db.update_player("private", "gm_alt7", exp=4071, max_hp=500, max_mp=150)
    print("1377 update_player 完成")
    # 1378：重读
    p = get_player("private", "gm_alt7")
    print("1378 get_player 返回: level=%s exp=%s _lv_logs=%s" % (
        p.get("level"), p.get("exp"), "有" if p.get("_lv_logs") else "无"))
    if p.get("_lv_logs"):
        print("_lv_logs:", p["_lv_logs"][0][:40])
    # 验证 DB
    db2 = sqlite3.connect(DB); db2.row_factory = sqlite3.Row
    r2 = dict(db2.execute("SELECT level, exp FROM players WHERE qq_id='gm_alt7'").fetchone())
    print("DB 现状: level=%s exp=%s" % (r2["level"], r2["exp"]))
    db2.close()
except Exception:
    traceback.print_exc()

conn.execute("UPDATE players SET level=?, exp=? WHERE qq_id='gm_alt7'", (orig["level"], orig["exp"]))
conn.commit()
print("已还原")
conn.close()
