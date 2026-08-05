# -*- coding: utf-8 -*-
"""store 层 · 玩家族：players 档案 + inventory 背包

验证：
  1. create/get/update（属性、技能、快捷指令）
  2. 物品 ID 存储、材料合并、count_item、装备 uuid、remove_item
  3. v46 核心约定：内存用名字，落库转 ID
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


def main():
    clean_db()
    print("【store·玩家族：players 档案】")
    p = make_player("g1", "q1", "格温", "战士")
    check("create_player 返回 player", p is not None and p["name"] == "格温", str(p)[:100])
    check("class_name 正确", p["class_name"] == "战士", str(p.get("class_name")))
    check("level 默认 1", p["level"] == 1, str(p.get("level")))
    db.update_player("g1", "q1", level=5, gold=999)
    p2 = db.get_player("g1", "q1")
    check("update level=5", p2["level"] == 5, str(p2.get("level")))
    check("update gold=999", p2["gold"] == 999, str(p2.get("gold")))
    # 技能存取（v46：内存名字 / 落库 ID）
    db.update_player("g1", "q1", learned_skills=["火球术", "冰箭"])
    p3 = db.get_player("g1", "q1")
    check("技能读回是名字", p3["learned_skills"] == ["火球术", "冰箭"], str(p3.get("learned_skills")))
    # 快捷指令
    db.update_player("g1", "q1", shortcuts={"1": "探索"})
    p4 = db.get_player("g1", "q1")
    check("shortcuts 存取", p4.get("shortcuts") == {"1": "探索"}, str(p4.get("shortcuts")))

    print("【store·玩家族：inventory 背包】")
    clean_db("inventory")
    db.add_item("g1", "q1", "mat_lang_pi", {"name": "狼皮", "type": "材料", "stackable": True})
    db.add_item("g1", "q1", "狼皮", {"name": "狼皮", "type": "材料", "stackable": True}, count=3)
    inv = db.get_inventory("g1", "q1")
    mat_items = [it for it in inv if it["data"].get("type") == "材料"]
    check("材料按 ID 合并", len(mat_items) == 1 and mat_items[0]["count"] == 4,
          str([(it["key"], it["count"]) for it in inv]))
    check("count_item(狼皮)=4", db.count_item("g1", "q1", "狼皮") == 4, str(db.count_item("g1", "q1", "狼皮")))
    check("count_item(mat_lang_pi)=4", db.count_item("g1", "q1", "mat_lang_pi") == 4,
          str(db.count_item("g1", "q1", "mat_lang_pi")))
    db.add_item("g1", "q1", "eq_abc123", {"name": "铁皮长剑", "type": "装备", "stackable": False})
    inv2 = db.get_inventory("g1", "q1")
    eqs = [it for it in inv2 if it["key"].startswith("eq_")]
    check("装备 key 保留 uuid", len(eqs) == 1 and eqs[0]["key"] == "eq_abc123", str([it["key"] for it in inv2]))
    db.remove_item("g1", "q1", "eq_abc123")
    inv3 = db.get_inventory("g1", "q1")
    check("remove_item 生效", all(it["key"] != "eq_abc123" for it in inv3))

    print("\n结果: %d 通过, %d 失败" % (passed, failed))
    return failed == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
