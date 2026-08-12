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

# ---- 5. 数据完整性 ----
print("== 5. 数据完整性 ==")
food_keys = [k for k, v in C.ITEMS.items()
             if isinstance(v, dict) and v.get("hot_turns") is not None]
buff_food_keys = [k for k, v in C.ITEMS.items()
                  if isinstance(v, dict) and v.get("effect")
                  and (v.get("heal") or v.get("mana") or v.get("stamina") is not None)]
check("hot 食物总量 ≥ 30", len(food_keys) >= 30, str(len(food_keys)))
check("战斗料理(增益) ≥ 5", len(buff_food_keys) >= 5, str(buff_food_keys))
check("矮人烈酒 desc 修复(无'3 场战斗')", "3 场战斗" not in C.ITEMS.get("i_dwarf_liquor", {}).get("desc", ""))
check("矮人烈酒走 food_buff", IT.infer_template(C.ITEMS["i_dwarf_liquor"]) == "food_buff")
check("矮人烈酒非 buff_atk(原 30% 超模)", C.ITEMS["i_dwarf_liquor"].get("effect") != "buff_atk")
affix_food_keys = [k for k, v in C.ITEMS.items()
                   if isinstance(v, dict) and v.get("food_effect")
                   and (v.get("heal") or v.get("mana") or v.get("stamina") is not None)]
check("效果料理(food_effect) ≥ 15", len(affix_food_keys) >= 15, str(len(affix_food_keys)))
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

# ---- 6. food_buff 模板 ----
print("== 6. food_buff 战斗料理 ==")
burger = C.ITEMS["i_deer_burger"]
class BufCtx:
    def __init__(self, battle):
        self.battle = battle
        self.data = burger
        self.player = {"hp": 50, "max_hp": 100, "mp": 50, "max_mp": 100}
        self.group_id = "g1"
        self.qq_id = "q1"
    def _db(self):
        class D:
            def update_player(self, *a, **k): pass
        return D()
    def hook(self, n, *a, **k):
        if n == "stamina_msg":
            return "⚡ 恢复 35 点体力(85/100)\n"
        return 0

rb = IT.TEMPLATES["food_buff"](BufCtx(battle=True))
check("汉堡战斗内 payload=buff:food_def_up", rb.payload == "buff:food_def_up", rb.payload)
ro = IT.TEMPLATES["food_buff"](BufCtx(battle=False))
check("汉堡战斗外即时回血+体力", "恢复 30 点生命" in ro.text and "恢复 35 点体力" in ro.text, ro.text)

# 战斗内吃料理播报（food_ 前缀 → 料理文案）
b2 = Battle("monster", {"name": "野狗", "hp": 500, "max_hp": 500, "atk": 5, "def": 0,
                        "matk": 0, "mdef": 0, "spd": 1000}, {})
p2 = {"hp": 100, "max_hp": 100, "mp": 50, "max_mp": 100, "class_name": "cls_zhan_shi",
      "level": 1, "learned_skills": [], "race": "human", "attributes": {}}
l2, _ = b2.player_turn("use_item", "buff:food_def_up", p2)
check("料理播报(非'饮下战斗药水')", "吃下了料理" in "\n".join(l2), "\n".join(l2))
check("food_def_up 生效 def×1.15",
      b2._apply_buffs(b2._player_stats(p2), b2.p_buffs).get("def") == int(b2._player_stats(p2).get("def", 0) * 1.15))

# ---- 7. food_effect 效果料理 ----
print("== 7. food_effect 效果料理 ==")
snake = C.ITEMS["i_snake_soup"]
check("蛇羹 infer→food_effect", IT.infer_template(snake) == "food_effect", str(snake.get("food_effect")))
check("蛇羹 desc 含【吸血】", "【吸血】" in snake.get("desc", ""), snake.get("desc", ""))
class AffCtx:
    def __init__(self, battle):
        self.battle = battle
        self.data = snake
        self.player = {"hp": 50, "max_hp": 100, "mp": 50, "max_mp": 100}
        self.group_id = "g1"
        self.qq_id = "q1"
    def _db(self):
        class D:
            def update_player(self, *a, **k): pass
        return D()
    def hook(self, n, *a, **k):
        if n == "stamina_msg":
            return "⚡ 恢复 25 点体力(85/100)\n"
        return 0
ra = IT.TEMPLATES["food_effect"](AffCtx(battle=True))
check("蛇羹战斗内 payload=foodfx:lifesteal", ra.payload == "foodfx:lifesteal", ra.payload)
ro2 = IT.TEMPLATES["food_effect"](AffCtx(battle=False))
check("蛇羹战斗外恢复", "恢复 20 点生命" in ro2.text, ro2.text)

# 战斗内吃蛇羹 → 获得吸血效果 + 攻击触发吸血
b3 = Battle("monster", {"name": "野狗", "hp": 500, "max_hp": 500, "atk": 5, "def": 0,
                        "matk": 0, "mdef": 0, "spd": 1000}, {})
p3 = {"hp": 100, "max_hp": 100, "mp": 50, "max_mp": 100, "class_name": "cls_zhan_shi",
      "level": 1, "learned_skills": [], "race": "human", "attributes": {},
      "equipment": {}}
l3, _ = b3.player_turn("use_item", "foodfx:lifesteal", p3)
j3 = "\n".join(l3)
check("吃下播报【吸血】", "获得【吸血】效果" in j3, j3)
check("p_food_effects 已设置", b3.p_food_effects == ["lifesteal"], str(b3.p_food_effects))
check("食物效果不进装备词条", "lifesteal" not in b3._equip_affix_ids(p3), str(b3._equip_affix_ids(p3)))
# 攻击命中触发吸血（直接调挂点验证）
hp_b3 = p3["hp"]
hit_logs = []
b3._food_on_hit(p3, 100, hit_logs)
check("吸血触发(8% 伤害)", p3["hp"] == min(p3["max_hp"], hp_b3 + 8), f"{hp_b3}→{p3['hp']}")
check("吸血播报", any("吸血" in l for l in hit_logs), str(hit_logs))

# 护盾料理特判（直接调 _do_use_item 避开敌方行动消耗）
bread = C.ITEMS["i_sacred_bread"]
b4 = Battle("monster", {"name": "野狗", "hp": 500, "max_hp": 500, "atk": 5, "def": 0,
                        "matk": 0, "mdef": 0, "spd": 1000}, {})
p4 = {"hp": 100, "max_hp": 100, "mp": 50, "max_mp": 100, "class_name": "cls_zhan_shi",
      "level": 1, "learned_skills": [], "race": "human", "attributes": {}, "equipment": {}}
b4._do_use_item("foodfx:shield", p4)
check("护盾料理获得 10% 护盾(3回合)", b4.p_shields.get("food_shield", {}).get("value") == int(p4["max_hp"] * 0.10)
      and b4.p_shields.get("food_shield", {}).get("turns") == 3,
      str(b4.p_shields))

# 回春料理：回合开始回血（直接调 food 挂点验证）
b5 = Battle("monster", {"name": "野狗", "hp": 500, "max_hp": 500, "atk": 5, "def": 0,
                        "matk": 0, "mdef": 0, "spd": 1000}, {})
p5 = {"hp": 80, "max_hp": 100, "mp": 50, "max_mp": 100, "class_name": "cls_zhan_shi",
      "level": 1, "learned_skills": [], "race": "human", "attributes": {}, "equipment": {}}
b5.p_food_effects = ["regen"]
hp_before = p5["hp"]
ts_logs = []
b5._food_turn_start(p5, ts_logs)
check("回春回合开始回血(直接调)", p5["hp"] == hp_before + int(p5["max_hp"] * 0.01), f"{hp_before}→{p5['hp']}")
check("回春播报", any("回春生效" in l for l in ts_logs), str(ts_logs))

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
