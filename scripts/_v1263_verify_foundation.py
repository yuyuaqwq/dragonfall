# -*- coding: utf-8 -*-
"""v126.3 地基快速验证：瘦身/水合/截断（独立私有库，不碰真实库）"""
import os, sys, tempfile, json

os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ.pop("DRAGONFALL_DB", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.store import inventory as INV

G, Q = "g1", "q1"

def reset():
    from game.store.connection import _connect
    conn = _connect()
    conn.execute("DELETE FROM inventory")
    conn.execute("DELETE FROM players")
    conn.commit()
    conn.close()

# 1) 钓鱼入包：类属性不落库，tags 对象包装
reset()
INV.add_item(G, Q, "银鳞鱼", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 6}, tag={"size": 32.5, "weight": 1.2})
INV.add_item(G, Q, "银鳞鱼", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 6}, tag={"size": 18.0, "weight": 0.5})
inv = INV.get_inventory(G, Q)
fish = [i for i in inv if i["key"].endswith("银鳞鱼") or "银鳞鱼" in i["data"].get("name", "")]
assert len(fish) == 1 and fish[0]["count"] == 2, f"堆叠失败: {fish}"
d = fish[0]["data"]
assert d["tags"] == [{"size": 32.5, "weight": 1.2}, {"size": 18.0, "weight": 0.5}], f"tags 错: {d}"
assert d["name"] == "银鳞鱼" and d["price"] == 6, f"水合类属性失败: {d}"
print("[1] 入包+水合 OK:", d["name"], d["price"], len(d["tags"]), "条")

# 2) remove_item 截断（FIFO）
INV.remove_item(G, Q, "银鳞鱼", 1)
inv = INV.get_inventory(G, Q)
fish = [i for i in inv if "银鳞鱼" in i["data"].get("name", "")]
assert fish[0]["count"] == 1 and fish[0]["data"]["tags"] == [{"size": 18.0, "weight": 0.5}], f"截断错: {fish}"
print("[2] remove FIFO 截断 OK")

# 3) 普通材料：类属性不落库，水合读配置
reset()
INV.add_item(G, Q, "丘陵狼皮", {"name": "丘陵狼皮", "type": "兽材", "stackable": True, "price": 12})
inv = INV.get_inventory(G, Q)
herb = [i for i in inv if i["data"].get("name") == "丘陵狼皮"]
assert len(herb) == 1 and herb[0]["count"] == 1, f"丘陵狼皮入包错: {inv}"
assert herb[0]["data"]["price"] == 5 and "tags" not in herb[0]["data"], f"丘陵狼皮水合错: {herb[0]}"
print("[3] 普通物瘦身+水合 OK: name=%s price=%s" % (herb[0]["data"]["name"], herb[0]["data"]["price"]))

# 4) 装备对象保留
reset()
eq = {"name": "铁剑", "slot": "weapon", "enhance": 3, "price": 120}
INV.add_item(G, Q, "eq_iron_sword_abc", eq)
inv = INV.get_inventory(G, Q)
e = [i for i in inv if i["key"] == "eq_iron_sword_abc"]
assert len(e) == 1 and e[0]["data"].get("enhance") == 3 and e[0]["data"].get("name") == "铁剑", f"装备错: {e}"
print("[4] 装备对象保留 OK:", e[0]["data"])

# 5) 水合对象回流（仓库/市场快照）→ _slim 提取 tags
reset()
INV.add_item(G, Q, "银鳞鱼", {"tags": [{"size": 5, "weight": 0.3}, {"size": 6, "weight": 0.4}]})
inv = INV.get_inventory(G, Q)
fish = [i for i in inv if "银鳞鱼" in i["data"].get("name", "")]
assert fish[0]["count"] == 1 and fish[0]["data"]["tags"] == [{"size": 5, "weight": 0.3}, {"size": 6, "weight": 0.4}], f"回流错: {fish}"
raw = fish[0]
print("[5] 快照回流瘦身 OK:", fish[0]["data"]["tags"])

# 6) sell_item_atomic 截断
reset()
INV.add_item(G, Q, "银鳞鱼", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 6}, tag={"size": 1, "weight": 1.7})
INV.add_item(G, Q, "银鳞鱼", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 6}, tag={"size": 2, "weight": 2.3})
INV.add_item(G, Q, "银鳞鱼", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 6}, tag={"size": 3, "weight": 0.9})
ok = INV.sell_item_atomic(G, Q, "银鳞鱼", 2, 20)
assert ok
inv = INV.get_inventory(G, Q)
fish = [i for i in inv if "银鳞鱼" in i["data"].get("name", "")]
assert fish[0]["count"] == 1 and fish[0]["data"]["tags"] == [{"size": 3, "weight": 0.9}], f"卖鱼截断错: {fish}"
print("[6] 卖鱼 FIFO 截断 OK")

# 7) 上限截断
reset()
for i in range(505):
    INV.add_item(G, Q, "银鳞鱼", {"name": "银鳞鱼", "type": "鱼", "stackable": True, "price": 6}, tag={"size": i, "weight": 0.1})
inv = INV.get_inventory(G, Q)
fish = [x for x in inv if "银鳞鱼" in x["data"].get("name", "")]
assert fish[0]["count"] == 505 and len(fish[0]["data"]["tags"]) == 500, f"上限错: count={fish[0]['count']} tags={len(fish[0]['data']['tags'])}"
assert fish[0]["data"]["tags"][0]["size"] == 5, f"FIFO 丢最旧错: {fish[0]['data']['tags'][0]}"
print("[7] 上限500 FIFO OK")

print("\n=== 地基 7/7 全绿 ===")
