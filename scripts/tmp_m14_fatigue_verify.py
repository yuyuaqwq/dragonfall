# -*- coding: utf-8 -*-
"""v105 M14 挖掘疲劳值临时验证脚本（测试库，跑完即删）"""
import os
import sys
import json
import random
import time

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dragonfall/
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))  # qqbot/
# 独立测试库（避免与并行测试共用 test_game_data.db 相互清表）
TEST_DB = os.path.join(PLUGIN_DIR, "test_game_data_m14.db")
os.environ["GWEN_GAME_DB"] = TEST_DB
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import db, content as C  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402

G, Q = "g1", "fatigue_q1"
passed = failed = 0

def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  OK {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {detail}")

db.init_db()
for t in ("players", "player_groups", "inventory", "quests", "achievements", "stats",
          "event_state", "professions"):
    conn = __import__("sqlite3").connect(TEST_DB)
    conn.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()

db.create_player(G, Q, "疲劳测试", C.resolve("classes", "战士"), {}, 100, 100)
db.update_player(G, Q, level=10, cur_map="rockfall_gorge", stamina=999999, apprentices=["mining"])
m = Main(None)

# ---- 1. tick 计数与疲劳触发 ----
print("【1. 连续挖掘计数】")
cnts = []
for i in range(6):
    cnt, ff = m._mining_fatigue_tick(G, Q)
    cnts.append((cnt, ff))
check("1-4 次不疲劳", [c for c, f in cnts[:4]] == [1, 2, 3, 4] and all(not f for c, f in cnts[:4]), str(cnts))
check("第 5 次进入疲劳", cnts[4] == (5, True), str(cnts))
check("第 6 次持续疲劳", cnts[5] == (6, True), str(cnts))
check("_mining_fatigued 判定 True", m._mining_fatigued(G, Q) is True)

# ---- 2. 恢复：超过 600s 重置 ----
print("【2. 超时恢复】")
raw = db.get_event_state(f"mining_fatigue_{Q}")
st = json.loads(raw)
st["ts"] = int(time.time()) - 601
db.set_event_state(f"mining_fatigue_{Q}", json.dumps(st))
check("超时后 _mining_fatigued=False", m._mining_fatigued(G, Q) is False)
cnt, ff = m._mining_fatigue_tick(G, Q)
check("超时后 tick 重置为 1", cnt == 1 and not ff, f"{cnt},{ff}")

# ---- 3. 损坏状态容错 ----
print("【3. 损坏状态容错】")
db.set_event_state(f"mining_fatigue_{Q}", "not-json{{{")
check("损坏 JSON 返回 None", m._mining_fatigue_state(G, Q) is None)
check("损坏后 _mining_fatigued=False", m._mining_fatigued(G, Q) is False)
db.set_event_state(f"mining_fatigue_{Q}", "")

# ---- 4. 稀有矿脉概率：疲劳减半（确定性验证，prof 4-6 → 15% vs 7.5%）----
print("【4. 疲劳稀有概率减半】")
# 升到副业 Lv.4-6
for _ in range(30):
    db.add_prof_exp(G, Q, "mining", 10)
plv = db.get_prof_level(G, Q, "mining")
print(f"  挖掘副业 Lv.{plv}")
assert 4 <= plv <= 6, "副业等级需落在 4-6 区间"

def roll_once(fatigued, rv):
    """复刻 _settle_mining 的稀有判定（只验概率分支，hill_mine 走深矿池）"""
    rare = [mm[0] for mm in C.MINING_DEEP_POOLS.get("hill_mine", []) for _ in range(mm[1])
            if C.MATERIALS[mm[0]]["price"] >= 150]
    if not rare:
        return None  # 地图无稀有矿 → 换地图
    _rare_ch = 0.15
    if fatigued:
        _rare_ch *= 0.5
    return rv < _rare_ch

# 确保 hill_mine 深矿池内有稀有矿
rare_in_pool = [mm[0] for mm in C.MINING_DEEP_POOLS.get("hill_mine", [])
                for _ in range(mm[1]) if C.MATERIALS[mm[0]]["price"] >= 150]
check("hill_mine 深矿池含稀有矿", len(rare_in_pool) > 0, f"稀有矿数={len(rare_in_pool)}")
check("rv=0.10 正常中稀有", roll_once(False, 0.10) is True)
check("rv=0.10 疲劳不中稀有", roll_once(True, 0.10) is False)
check("rv=0.05 疲劳仍可中稀有(概率未归零)", roll_once(True, 0.05) is True)

# ---- 5. _settle_mining 端到端（随机统计：正常 vs 疲劳稀有率）----
print("【5. _settle_mining 稀有率统计】")
db.update_player(G, Q, cur_map="hill_mine")
db.set_event_state(f"mining_fatigue_{Q}", json.dumps({"cnt": 2, "ts": int(time.time())}))
random.seed(20260812)
normal_rare = sum(1 for _ in range(300) if "竟是稀有矿脉" in (m._settle_mining(G, Q, {"type": "mining"}) or ""))
db.set_event_state(f"mining_fatigue_{Q}", json.dumps({"cnt": 9, "ts": int(time.time())}))
fat_rare = sum(1 for _ in range(300) if "竟是稀有矿脉" in (m._settle_mining(G, Q, {"type": "mining"}) or ""))
print(f"  正常稀有率 {normal_rare}/300={normal_rare/3:.1f}%  疲劳稀有率 {fat_rare}/300={fat_rare/3:.1f}%")
check("疲劳稀有率显著低于正常", fat_rare < normal_rare * 0.8 and fat_rare < normal_rare - 15,
      f"normal={normal_rare}, fat={fat_rare}")
# 疲劳结算文案
out = m._settle_mining(G, Q, {"type": "mining"})
check("疲劳结算附提示", "手臂发酸" in (out or ""), (out or "")[:80])

# ---- 6. 清理疲劳状态（恢复测试用）----
db.set_event_state(f"mining_fatigue_{Q}", "")
print(f"\n结果: passed={passed} failed={failed}")
sys.exit(1 if failed else 0)
