# -*- coding: utf-8 -*-
"""实测：get_player 惰性升级在 exp=4071/level=18 时是否触发（复现战斗胜利 1378 场景）"""
import sys, os, json, sqlite3, traceback
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
os.chdir(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

DB = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\game_data.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# 用 gm_alt7 测试（先看它是否存在）
row = conn.execute("SELECT qq_id, name, level, exp FROM players WHERE qq_id='gm_alt7'").fetchone()
print("gm_alt7:", dict(row) if row else None)

if row:
    qid = "gm_alt7"
else:
    qid = None
    print("无 gm_alt7，找其他测试号")
    for r in conn.execute("SELECT qq_id, name, level, exp FROM players LIMIT 30"):
        print(dict(r))
    sys.exit(0)

# 记录原值
orig = dict(conn.execute("SELECT * FROM players WHERE qq_id=?", (qid,)).fetchone())
print("原值 level=%s exp=%s" % (orig["level"], orig["exp"]))

# 模拟：把 level 设 18、exp 设 4071（影刃场景）
conn.execute("UPDATE players SET level=18, exp=4071 WHERE qq_id=?", (qid,))
conn.commit()

# 调用 get_player 触发惰性升级
try:
    from game.store.players import get_player
    p = get_player("private", qid)
    print("get_player 返回: level=%s exp=%s _lv_logs=%s" % (
        p.get("level"), p.get("exp"), "有" if p.get("_lv_logs") else "无"))
    if p.get("_lv_logs"):
        print("_lv_logs 内容:", p["_lv_logs"][0][:60])
    # 再读一次 DB 看写库结果
    db2 = sqlite3.connect(DB)
    r2 = dict(db2.execute("SELECT level, exp FROM players WHERE qq_id=?", (qid,)).fetchone())
    print("DB 现状: level=%s exp=%s" % (r2["level"], r2["exp"]))
    db2.close()
except Exception:
    traceback.print_exc()

# 还原
conn.execute("UPDATE players SET level=?, exp=? WHERE qq_id=?",
             (orig["level"], orig["exp"], qid))
conn.commit()
print("已还原 level=%s exp=%s" % (orig["level"], orig["exp"]))
conn.close()
