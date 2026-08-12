# -*- coding: utf-8 -*-
"""v101.28 食物持续恢复（hot）专项测试：
1. 食物 infer_template → food；药水仍 → heal（互不干扰）
2. tpl_food 战斗内 payload = "hot:比例,比例,回合"
3. _do_use_item hot: 分支 → 设置 p_hot + 播报
4. 每回合开始 hot 结算（回血/回蓝 + 剩余回合 + 结束清理）
5. tpl_food 战斗外 = 即时回复（合并播报）
"""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game.core import item_templates as IT
from data.plugins.dragonfall.game import engine as E
from data.plugins.dragonfall.game.battle import Battle

PASS = 0
FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {extra}")

# ---- 1. infer_template 分流 ----
print("== 1. 模板分流 ==")
food = {"name": "麦酒", "price": 10, "hot": 0.05, "hot_turns": 3, "hot_mana": 0.06,
        "heal": 0.15, "mana": 0.15, "stamina": 15}
potion = {"name": "治疗药水(小)", "price": 10, "heal": 0.2}
check("食物带 hot → food 模板", IT.infer_template(food) == "food")
check("药水无 hot → heal 模板", IT.infer_template(potion) == "heal")

# 真实数据抽查
ale = C.ITEMS.get("i_ale", {})
check("真实麦酒有 hot 字段", "hot" in ale, str(ale))
check("真实麦酒 hot=0.05", ale.get("hot") == 0.05)
check("真实麦酒 desc 含持续恢复说明", "战斗中每回合" in ale.get("desc", ""), ale.get("desc", ""))
treat = C.ITEMS.get("i_treat_s", {})
check("治疗药水无 hot 字段", "hot" not in treat)
check("治疗药水 desc 未污染", "战斗中每回合" not in treat.get("desc", ""))
check("真实麦酒 infer→food", IT.infer_template(ale) == "food")
check("真实药水 infer→heal", IT.infer_template(treat) == "heal")

# ---- 2. tpl_food 战斗内 payload ----
print("== 2. tpl_food payload ==")
class FakeCtx:
    def __init__(self, battle):
        self.battle = battle
        self.data = ale
        self.player = {"hp": 100, "max_hp": 100, "mp": 50, "max_mp": 100}
    def _db(self):
        class D:
            def update_player(self, *a, **k): pass
        return D()
    def hook(self, name, *a, **k):
        if name == "stamina_msg":
            return ""
        return 0

r = IT.TEMPLATES["food"](FakeCtx(battle=True))
check("战斗内 payload=hot:0.05,0.06,3", r.payload == "hot:0.05,0.06,3", r.payload)

# ---- 3. Battle hot 全链路 ----
print("== 3. 战斗内 hot 全链路 ==")
enemy = {"name": "野狗", "hp": 50, "max_hp": 50, "atk": 5, "def": 0, "matk": 0, "mdef": 0, "spd": 1000}
b = Battle("monster", enemy, {})
player = {"hp": 50, "max_hp": 100, "mp": 20, "max_mp": 100, "class_name": "cls_zhan_shi",
          "level": 1, "learned_skills": [], "race": "human", "attributes": {}}
logs, ended = b.player_turn("use_item", "hot:0.05,0.06,3", player)
joined = "\n".join(logs)
check("吃下播报", "🍲 你吃下了食物" in joined and "每回合恢复 5% 生命" in joined, joined[:120])
check("p_hot 已设置", b.p_hot == {"heal": 0.05, "mana": 0.06, "turns": 3}, str(b.p_hot))
hp0, mp0 = player["hp"], player["mp"]

# 下回合（普攻）：hot 结算
logs2, _ = b.player_turn("attack", "", player)
j2 = "\n".join(logs2)
check("回合开始 hot 回血", "持续恢复生效" in j2 and player["hp"] > hp0, f"{j2[:100]} hp={player['hp']}")
check("hot 回蓝", player["mp"] > mp0, f"mp={player['mp']}")
check("剩余回合提示", "剩余 2 回合" in j2, j2[:100])
check("turns 递减", b.p_hot["turns"] == 2, str(b.p_hot))

# 再两回合 → hot 结束
b.player_turn("attack", "", player)
logs4, _ = b.player_turn("attack", "", player)
check("hot 结束清理", b.p_hot == {}, str(b.p_hot))

# 吃食物当回合不结算（吃+结算不能同回合重复）
b2 = Battle("monster", enemy, {})
p2 = {"hp": 50, "max_hp": 100, "mp": 20, "max_mp": 100, "class_name": "cls_zhan_shi",
      "level": 1, "learned_skills": [], "race": "human", "attributes": {}}
l0, _ = b2.player_turn("use_item", "hot:0.05,0,3", p2)
check("吃食物回合不额外结算", "持续恢复生效" not in "\n".join(l0))

# ---- 4. 战斗外即时回复 ----
print("== 4. tpl_food 战斗外 ==")
class CtxOut:
    def __init__(self):
        self.battle = None
        self.data = ale
        self.player = {"hp": 50, "max_hp": 100, "mp": 20, "max_mp": 100}
        self.group_id = "g1"
        self.qq_id = "q1"
        self.removed = False
    def _db(self):
        class D:
            def update_player(self, g, q, **k): pass
        return D()
    def hook(self, name, *a, **k):
        if name == "stamina_msg":
            return "⚡ 恢复 15 点体力(85/100)\n"
        if name == "add_stamina":
            return 15
        return 0

co = CtxOut()
ro = IT.TEMPLATES["food"](co)
check("战斗外即时回血文案", "恢复 15 点生命" in ro.text, ro.text)
check("战斗外带体力文案", "恢复 15 点体力" in ro.text, ro.text)

# 满血且无 stamina/mana 需求 → 拦截
class CtxFull:
    def __init__(self):
        self.battle = None
        self.data = {"name": "炖菜", "heal": 0.4, "hot": 0.06, "hot_turns": 3}
        self.player = {"hp": 100, "max_hp": 100, "mp": 100, "max_mp": 100}
        self.group_id = "g1"
        self.qq_id = "q1"
    def _db(self):
        class D:
            def update_player(self, *a, **k): pass
        return D()
    def hook(self, name, *a, **k): return ""
rf = IT.TEMPLATES["food"](CtxFull())
check("满血纯治疗拦截不消耗", rf.consume is False and "满的" in rf.text, rf.text)

# ---- 5. 全量食物数据完整性 ----
print("== 5. 数据完整性 ==")
food_keys = [k for k, v in C.ITEMS.items()
             if isinstance(v, dict) and v.get("hot_turns") is not None]
check("食物总量 ≥ 50", len(food_keys) >= 50, str(len(food_keys)))
bad = []
for k in food_keys:
    v = C.ITEMS[k]
    if not (1 <= v.get("hot_turns", 0) <= 5):
        bad.append((k, "turns", v.get("hot_turns")))
    h = v.get("hot") or 0
    hm = v.get("hot_mana") or 0
    if h < 0 or h > 0.3 or hm < 0 or hm > 0.3:
        bad.append((k, "hot", (h, hm)))
check("hot 数值全部合法", not bad, str(bad[:3]))

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
