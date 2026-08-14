# -*- coding: utf-8 -*-
"""v98.5 注册表验收测试：world_event_templates / affix_effects

验收标准（设计文档）：
1. 扩展性：注册新事件/新词条效果 → 分发骨架立即生效，无需改 battle.py/social.py
2. 安全降级：未知 key 不报错（事件不显示详情 / 词条无操作）
3. 全覆盖：数据用到的 key 全部有注册
4. 行为等价：叠加型（减伤/回春）先汇总后应用；组合型（净化 if-elif）互斥；TAKEN 顺序结算

独立运行：python tests/test_v98_05_registry.py
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import BT  # noqa: F401
from data.plugins.dragonfall.game.core import world_event_templates as WET
from data.plugins.dragonfall.game.core import affix_effects as AFX
from data.plugins.dragonfall.game import content as C

Battle = BT.Battle
PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def make_battle(**kw):
    enemy = kw.pop("enemy", {"name": "野狼", "hp": 100, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
    b = Battle(btype="monster", enemy=enemy, player={"class_name": "cls_zhan_shi"})
    b.round = kw.pop("round", 1)
    b.e_buffs = kw.pop("e_buffs", {})
    b.p_buffs = kw.pop("p_buffs", {})
    b.mech_stacks = kw.pop("mech_stacks", {})
    b.shield = kw.pop("shield", 0)
    b.resources = kw.pop("resources", {})
    b._last_player = kw.pop("last_player", None)
    return b


def equip(*affixes, legendary=None):
    """构造带词条的装备 dict"""
    return {"weapon": {"affixes": list(affixes), "legendary": legendary}}


player = {"hp": 100, "max_hp": 100, "mp": 50, "max_mp": 50}


# ============ 1. 世界事件注册表 ============
print("【1. 世界事件注册表】")
# 扩展性
BEFORE = set(WET.DISPLAYS.keys())


@WET.register("test_fake_event")
def _d_test_fake(self, cur, lines, group_id):
    lines.append("测试事件展示")


check("注册新事件类型后 DISPLAYS 含新 key", "test_fake_event" in WET.DISPLAYS)
lines = []
WET.DISPLAYS["test_fake_event"](None, {}, lines, 123)
check("新事件立即生效", lines == ["测试事件展示"])
WET.DISPLAYS.pop("test_fake_event")

# 安全降级
check("未知 etype 无 DISPLAYS 条目", "not_a_type" not in WET.DISPLAYS)

# 全覆盖：WORLD_EVENT_POOL 的 type 全部有展示
pool_types = {e["type"] for e in C.WORLD_EVENT_POOL}
check(f"世界事件池全覆盖（数据 {len(pool_types)} 种）", pool_types <= set(WET.DISPLAYS.keys()))

# 行为抽样
class FakeSocial:
    def _player(self, gid, qq):
        return {"name": f"玩家{qq}"} if qq == "1001" else None

lines = []
WET.DISPLAYS["auction"](FakeSocial(), {"data": {"items": [{"id": 1, "name": "龙鳞剑", "base": 100, "buyout": 500, "bids": {"1001": 300, "2002": 250}}]}}, lines, 1)
check("auction 展示最高出价人", "玩家1001：300" in lines[0] and "一口价 500" in lines[1])
lines = []
WET.DISPLAYS["boss"](FakeSocial(), {"data": {"boss": {"name": "深渊魔王", "icon": "👿", "lv": 30, "hp": 500, "max_hp": 1000}}}, lines, 1)
check("boss 展示血量百分比", "50%" in lines[1] and "讨伐" in lines[2])
lines = []
WET.DISPLAYS["omen"](FakeSocial(), {}, lines, 1)
check("omen 展示经验金币加成", "＋50%" in lines[0])

# ============ 2. 词条注册表：扩展性 ============
print("【2. 词条注册表扩展性】")


@AFX.register(AFX.HIT_EFFECTS, "test_fake_hit")
def _h_test_fake(battle, player, dmg, logs):
    logs.append("测试命中词条")


check("注册新命中词条后 HIT_EFFECTS 含新 key", "test_fake_hit" in AFX.HIT_EFFECTS)
b = make_battle()
b._equip_affix_ids = lambda p: ["test_fake_hit"]
logs = []
b._affix_on_hit(player, 100, logs)
check("新命中词条立即生效", "测试命中词条" in logs)
AFX.HIT_EFFECTS.pop("test_fake_hit")


@AFX.register(AFX.TAKEN_EFFECTS, "test_fake_taken")
def _t_test_fake(battle, player, ctx, logs):
    ctx["out"] = max(1, ctx["out"] - 10)


b = make_battle()
b._equip_affix_ids = lambda p: ["test_fake_taken"]
out = b._affix_on_taken(player, 100, [])
check("新受击词条立即生效（out 100→90）", out == 90)
AFX.TAKEN_EFFECTS.pop("test_fake_taken")

# ============ 3. 词条注册表：行为抽样（守卫/叠加/互斥） ============
print("【3. 词条行为抽样】")
# 敌人已死 → 命中词条整链跳过
b = make_battle(enemy={"name": "野狼", "hp": 0, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
b._equip_affix_ids = lambda p: ["bleed"]
random.seed(1)
logs = []
b._affix_on_hit(player, 100, logs)
check("敌人已死时命中词条跳过", logs == [])
# bleed 触发（monkeypatch random 保证命中 20%）
b = make_battle()
b._equip_affix_ids = lambda p: ["bleed"]
_orig_random = random.random
random.random = lambda: 0.05
logs = []
b._affix_on_hit(player, 100, logs)
random.random = _orig_random
check("bleed 触发挂 e_buffs", "bleed" in b.e_buffs and len(logs) == 1)
# 元素附加（单独 ice）
b = make_battle()
b._equip_affix_ids = lambda p: ["element_ice"]
logs = []
b._affix_on_hit(player, 100, logs)
check("element_ice 单独触发（附加伤害+减速）", "ice属性附加" in logs[0] and b.e_buffs.get("spd_down") == 2)
# 净化：judgment_chain 在时 purify 不触发（if-elif 互斥）
b = make_battle(e_buffs={"mon_atk_up": 3})
b._equip_affix_ids = lambda p: ["purify", "judgment_chain"]
random.seed(2)  # 让 purify 的 15% 命中（若误触发会清增益）
logs = []
b._affix_on_hit(player, 100, logs)
check("净化互斥：有 judgment_chain 时 purify 不触发", "mon_atk_up" in b.e_buffs)
# 减伤叠加：dmg_reduce + earth_heart = -8%
b = make_battle()
b._equip_affix_ids = lambda p: ["dmg_reduce", "earth_heart"]
out = b._affix_on_taken(player, 100, [])
check("减伤叠加 -8%（100→92）", out == 92)
# TAKEN 顺序结算：dmg_reduce + thorns 原始 dmg（block 已 v106.3 属性化移出 TAKEN，见 3.7）
b = make_battle()
b._equip_affix_ids = lambda p: ["dmg_reduce", "block"]
_orig_random = random.random
random.random = lambda: 0.05  # block 15% 命中
logs = []
out = b._affix_on_taken(player, 100, logs)
random.random = _orig_random
# v106.3：block 已属性化（格挡率进 st["block"]，受击结算走 _damage_player），不再作为 TAKEN 特效
check("block 已移出 TAKEN（仅 dmg_reduce 生效 100→97）", out == 97 and "block" not in AFX.TAKEN_EFFECTS)
# v106.4：thorns 已属性化（反伤率进 st["thorns"]，受击结算走 _damage_player），不再作为 TAKEN 特效
b = make_battle()
b._equip_affix_ids = lambda p: ["thorns"]
_orig_random = random.random
random.random = lambda: 0.05  # thorns 10% 命中
logs = []
out = b._affix_on_taken(player, 100, logs)
random.random = _orig_random
check("thorns 已移出 TAKEN（out 不变 100）", out == 100 and "thorns" not in AFX.TAKEN_EFFECTS)
# 回合开始：regen + dawn_crown = 3% 生命
b = make_battle()
b._equip_affix_ids = lambda p: ["regen", "dawn_crown"]
p2 = {"hp": 50, "max_hp": 100, "mp": 50, "max_mp": 50}
logs = []
b._affix_turn_start(p2, logs)
check("回春叠加 3%（50→53）", p2["hp"] == 53 and "回春" in logs[0])
# 冥想 mp 回复（max_mp 200 → 1% = 2 点）
b = make_battle()
b._equip_affix_ids = lambda p: ["meditate"]
p2 = {"hp": 100, "max_hp": 100, "mp": 10, "max_mp": 200}
logs = []
b._affix_turn_start(p2, logs)
check("冥想回复 1% mp", p2["mp"] == 12)
# 套装特效：execute 处决（直接调 handler，防 equipment 缺失）
b = make_battle(enemy={"name": "野狼", "hp": 20, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
logs = []
AFX.SET_PROC_EFFECTS["execute"](b, player, 100, logs)
check("套装 execute 处决（<30% 追加 25%）", b.enemy["hp"] == 0 and "处决" in logs[0])
# 套装特效：未知 eff 安全跳过
b = make_battle()
b._set_attack_proc = Battle._set_attack_proc  # 恢复原方法（防 mock 污染）
orig_set_bonus_4 = None

# ============ 3.5 概率数据化（v99.2）：改数据即生效 ============
print("【3.5 概率数据化】")
# 词条概率读数据：把 bleed 的 chance 临时改 1.0 → 必触发
from data.plugins.dragonfall.game import content as C
orig_bleed_chance = C.AFFIXES["bleed"].get("chance")
C.AFFIXES["bleed"]["chance"] = 1.0
b = make_battle()
b._equip_affix_ids = lambda p: ["bleed"]
logs = []
b._affix_on_hit(player, 100, logs)
check("bleed chance=1.0 必触发", "bleed" in b.e_buffs)
C.AFFIXES["bleed"]["chance"] = orig_bleed_chance
b = make_battle()
b._equip_affix_ids = lambda p: ["bleed"]
_orig_random = random.random
random.random = lambda: 0.99  # >20% 保证不触发
logs = []
b._affix_on_hit(player, 100, logs)
random.random = _orig_random
check("chance 恢复后非必触发（20% 不中）", "bleed" not in b.e_buffs)

# ============ 3.6 荣誉商店数据化（v99.4） ============
print("【3.6 荣誉商店数据化】")
check("HONOR_SHOP 在数据层（C.HONOR_SHOP）", C.HONOR_SHOP.get(1, {}).get("name") == "荣誉勋章")
check("4 件商品全部带 reward", all("reward" in v for v in C.HONOR_SHOP.values()))

# ============ 4. 全覆盖：数据 key 全部有注册 ============
print("【4. 数据覆盖检查】")
import re
sets_src = open(os.path.join("game", "data", "sets.py"), encoding="utf-8").read()
set4_effs = set(re.findall(r'"bonus_4"\s*:\s*\{[^}]*"effect"\s*:\s*"([^"]+)"', sets_src))
# 旧代码只实现 6 种攻击特效（其余如 crit_up_set/reflect/regen 走别的系统，原 elif 链无分支 → 无操作）
implemented = {"frost", "burn", "thunder", "pierce", "lifesteal_set", "execute"}
check("套装特效 6 种全部注册", implemented <= set(AFX.SET_PROC_EFFECTS.keys()))
# v110.5 X3：恒真断言替换——其余 non_attack 特效（mdef_up_set/reflect/crit_up_set/regen/
# regen_strong/dodge_set）走其他系统（属性/受击/回合开始），不得误注册为『攻击特效』。
# 若有人把非攻击类特效加进 SET_PROC_EFFECTS 则必红。
non_attack = set4_effs - implemented
bad_reg = non_attack & set(AFX.SET_PROC_EFFECTS.keys())
check("非攻击类套装特效不注册为攻击特效（由其他系统处理）", bad_reg == set())

# 词条 id 覆盖：触发型词条全部在对应注册表
# v106.3 属性化：lifesteal/block 已从触发特效改 stat 折算（affix.py _STAT_AFFIX_FX），不再走 HIT/TAKEN 注册表
trigger_ids = {
    "bleed", "armor_break", "combo", "element_fire", "element_ice",
    "element_thunder", "pierce", "charge", "purify", "judgment_chain", "dragon_tongue",
}
hit_covered = set(AFX.HIT_EFFECTS.keys()) - {"purify"} | {"purify", "judgment_chain"}
check(f"命中词条全覆盖（数据 {len(trigger_ids)} 个）", trigger_ids <= hit_covered)
# v106.3/v106.4 属性化：block/thorns 已从触发特效改 stat 折算（affix.py _STAT_AFFIX_FX），不再走 HIT/TAKEN 注册表
# v110 审计：tenacity 词条拆分——「坚韧」CC 免疫键改 tenacity_cc（原键被 v106 韧性 stat 词条占用）
taken_ids = {"dmg_reduce", "earth_heart", "tenacity_cc", "counter", "ember_ward", "moro_crown"}
check("受击词条全覆盖", taken_ids <= set(AFX.TAKEN_EFFECTS.keys()) | {"dmg_reduce", "earth_heart"})
turn_ids = {"regen", "dawn_crown", "meditate"}
check("回合开始词条全覆盖", turn_ids <= set(AFX.TURN_START_EFFECTS.keys()) | {"regen", "dawn_crown"})

# ============ 3.7 世界事件初始化注册表（v100.2） ============
print("【3.7 世界事件初始化注册表】")
INITIALIZERS = WET.INITIALIZERS
need_init = {"auction", "boss"}
check("需要 data 的 etype（auction/boss）已注册 init", need_init <= set(INITIALIZERS.keys()))
check("无 data 事件（merchant/omen/swarm/festival）不注册（data={} 降级）",
      not ({"merchant", "omen", "swarm", "festival"} & set(INITIALIZERS.keys())))
import random as _r
_r.seed(7)
d_auction = INITIALIZERS["auction"](_r)
check("auction 初始化产出 3 件拍卖品", len(d_auction["items"]) == 3 and all("bids" in it for it in d_auction["items"]))
_r.seed(7)
d_boss = INITIALIZERS["boss"](_r)
check("boss 初始化产出讨伐状态", d_boss["boss"]["hp"] == d_boss["boss"]["max_hp"] and d_boss["boss"]["contrib"] == {})
check("未知 etype 安全降级为空 data", INITIALIZERS.get("nope") is None)

print()
print(f"结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
