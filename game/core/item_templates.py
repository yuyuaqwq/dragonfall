# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - item_templates.py（v97.7：道具效果模板引擎）

消灭 commands/economy.py use() 里消耗品的 if-elif 硬编码：
道具数据只声明效果字段（heal/mana/stamina/effect/type），执行统一走本模块注册表。

设计：
- TEMPLATES: {模板名: 函数}，函数签名 fn(ctx) -> ItemResult
- ctx 为 ItemContext（group_id/qq_id/player/data/battle/params/hooks）
- 模板函数内延迟导入 db/content（遵循 core 聚合链规则，防循环导入）
- 命令层专属回调（add_stamina/nearest_town/is_redname/roll_blueprint 等）经 ctx.hooks 注入
- 战斗内/战斗外双路径：
    · ctx.battle 非空 → 模板只计算 payload（交给 battle.player_turn 应用），不改状态
    · ctx.battle 为空   → 模板直接执行副作用并返回展示文本
- META: {模板名: {"battle_ok": bool}} 战斗中是否允许使用

扩展方式：
- 加道具：data/items.py CONSUMABLES 加一条 dict（heal/mana/stamina/effect 组合即可，无需新代码）
- 加新玩法：register 一个新模板函数（~15 行），之后全数据化
"""
import json
import random
import time

from ..data import TIPS  # noqa: F401  (v127 指令随机提示库，数据驱动)

TEMPLATES = {}
META = {}


def _rand_tip(cat):
    """v127 数据驱动随机提示：从 TIPS 分类库随机抽 1 条（含 💡 前缀）。"""
    pool = TIPS.get(cat) or TIPS.get("common") or ["看看『帮助』了解更多"]
    return "💡 " + random.choice(pool)


def register(name, battle_ok=False):
    """模板注册装饰器。battle_ok=True 表示战斗中可用（heal/mana/stamina/buff）。"""
    def deco(fn):
        TEMPLATES[name] = fn
        META[name] = {"battle_ok": battle_ok}
        return fn
    return deco


class ItemResult:
    """模板执行结果。payload 非空时由命令层转交 battle.player_turn。"""

    def __init__(self, text="", payload=None, consume=True):
        self.text = text          # 展示文本（战斗外直接展示；战斗中拼入战斗日志）
        self.payload = payload    # 战斗内传给 player_turn 的 payload（如 "buff:atk_up" / "123"）
        self.consume = consume    # False = 不扣物品（如满血纯治疗拦截）


class ItemContext:
    """道具使用上下文。battle 非空 = 战斗中使用。"""

    def __init__(self, group_id, qq_id, player, data, battle=None, hooks=None):
        self.group_id = group_id
        self.qq_id = qq_id
        self.player = player
        self.data = data
        self.battle = battle
        self.hooks = hooks or {}

    @property
    def lv(self):
        return self.player.get("level", 1)

    def _db(self):
        from .. import db
        return db

    def _C(self):
        from .. import content as C
        return C

    def hook(self, name, *args, **kwargs):
        fn = self.hooks.get(name)
        if fn:
            return fn(*args, **kwargs)
        return None

    def item_name(self):
        return self.data.get("name", "道具")


def infer_template(data):
    """从道具数据推断模板名（use() 分发用）。"""
    from .. import content as C  # v102.2 延迟导入（core 聚合链惯例）
    if data.get("learn_skill"):
        # v112 P1：隐藏技能书（learn_skill + require_class 数据驱动，优先于通用 effect）
        return "skill_tome"
    if data.get("hot") or data.get("hot_mana"):
        # v101.28 食物持续恢复：有 hot 字段 = 食物 → food 模板
        # （战斗内=持续恢复，战斗外=即时回复+体力；药水无 hot 字段走原逻辑）
        # v104 M08 P1-4：hot_mana 且无 hot 也是食物（苹果酒/蜂蜜茶/码头朗姆等 8 种
        # 只有 hot_mana/hot_turns 无 hot，此前被 infer 判为 mana 药水——战斗内变
        # 即时回蓝，desc 却写"每回合回复魔力"，实机与文案不符）
        return "food"
    if data.get("effect"):
        # v101.28b 食物增益：effect + 恢复字段 = 战斗料理（战斗内 buff，战斗外恢复）
        eff = data.get("effect")
        if data.get("heal") or data.get("mana") or data.get("stamina") is not None:
            return "food_buff"
        return eff if eff in TEMPLATES else "none"
    if data.get("food_effect"):
        # v101.28e 食物效果（独立于装备词条）：food_effect + 恢复字段 = 效果料理
        if data.get("heal") or data.get("mana") or data.get("stamina") is not None:
            return "food_effect"
        return "none"
    if data.get("heal") and data.get("mana"):
        # v104R3 M16 P2-3：heal+mana 复合药水（全效药水/月之露/高级·超级全效等）——
        # 原 infer 命中 heal 模板战斗外只回血不回蓝（desc 承诺双回复落空），
        # 复合模板战斗内外双恢复（须在 food_buff/food_effect 判定之后、heal 之前）
        return "heal_mana"
    if data.get("heal"):
        return "heal"
    if data.get("mana"):
        return "mana"
    if data.get("stamina") is not None:
        return "stamina"
    eff = data.get("effect")
    if eff:
        return eff if eff in TEMPLATES else "none"
    # v102.2：type 中文文案收敛为常量（改物品类型文案只动数据+constants）
    if data.get("type") == C.ITEM_TYPE_PET_EGG:
        return "pet_egg"
    if data.get("type") == C.ITEM_TYPE_MOUNT:
        return "mount"
    return "none"


# ================= 模板实现 =================

@register("heal", battle_ok=True)
def tpl_heal(ctx):
    """生命恢复。heal <= 1 视为百分比（0.2=20%、1.0=100%），> 1 固定值（旧物品兼容）。
    战斗内：payload = 绝对恢复值（battle.player_turn 实际应用）。
    战斗外：满血纯治疗拦截不消耗；复合物品（带 stamina/mana）满血仍可用。
    v104 M02 P1-5：战斗内满血同款拦截（此前白扣道具+白送敌方一回合）。"""
    d = ctx.data
    heal_v = d["heal"]
    # <=1 视为百分比（0.2=20%；1.0=100% 完全回复），>1 固定值（旧式配方兼容）
    if heal_v <= 1:
        heal_v = int(ctx.player["max_hp"] * heal_v)
    if ctx.battle:
        # v104 M02 P1-5：战斗内满血拦截（与战斗外同规则）——满血纯治疗不扣道具、
        # 不消耗回合（consume=False 由 economy use() 短路，敌方不动）。
        # 血量取权威来源：副本战斗读 st["players"] 快照（DB 可能过时，v95r76）；
        # 普通战斗 hp 用 DB（每回合同步），上限用引擎实时值（DB max 换装/升级后
        # 可能过时，对齐 battle.player_turn v95.19 刷新逻辑）。
        if not d.get("stamina") and not d.get("mana"):
            _hp, _max = _battle_cur_max(ctx, "hp", "max_hp")
            if _hp >= _max:
                return ItemResult(
                    text=f"❤️ 你现在的生命是满的({_hp}/{_max})，用不着【{d['name']}】～",
                    consume=False)
        return ItemResult(payload=str(heal_v))
    # 战斗外
    if ctx.player["hp"] >= ctx.player["max_hp"] and not d.get("stamina") and not d.get("mana"):
        return ItemResult(
            text=f"❤️ 你现在的生命是满的({ctx.player['hp']}/{ctx.player['max_hp']})，用不着【{d['name']}】～",
            consume=False)
    db = ctx._db()
    st_msg = ctx.hook("stamina_msg", ctx.group_id, ctx.qq_id, ctx.player) or ""
    new_hp = min(ctx.player["max_hp"], ctx.player["hp"] + heal_v)
    db.update_player(ctx.group_id, ctx.qq_id, hp=new_hp)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"💊 你使用了【{d['name']}】，恢复 {heal_v} 点生命！\n❤️ {new_hp}/{ctx.player['max_hp']}{st_msg}")


def _battle_cur_max(ctx, cur_key, max_key):
    """战斗内当前值与上限的权威来源（v104 M02 P1-5 满血/满蓝判定用）：
    - 副本战斗：st["players"][qq_id] 快照（引擎每回合刷新并写回，权威）
    - 普通战斗：DB player（每回合 player_turn 后同步）；上限按引擎实时重算
      （v95.19：DB max_hp/max_mp 换装/升级后可能过时，player_turn 开头也会刷新）"""
    st = ctx.battle
    if isinstance(st, dict):
        snap = (st.get("players") or {}).get(str(ctx.qq_id))
        if snap:
            return snap.get(cur_key, 0), snap.get(max_key, 0)
    from .. import engine as E  # 延迟导入（core 聚合链惯例）
    try:
        tb = (st or {}).get("title_bonus") or {}
        real = E.player_final_stats(
            ctx.player.get("class_name", ""),
            ctx.player.get("level", 1),
            ctx.player.get("equipment", {}),
            ctx.player.get("class_tier", 0),
            ctx.player.get("attributes"),
            ctx.player.get("evolve_path", 0),
            tb, ctx.player.get("race"))
        return ctx.player.get(cur_key, 0), int(real.get(max_key, ctx.player.get(max_key, 0)))
    except Exception:
        return ctx.player.get(cur_key, 0), ctx.player.get(max_key, 0)


@register("mana", battle_ok=True)
def tpl_mana(ctx):
    """魔力恢复。mana <= 1 百分比（1.0=100%），> 1 固定值。
    战斗内：payload=f"mana:{绝对恢复量}"（battle.player_turn 的 _do_use_item
    识别 mana: 前缀回蓝并播报数字——v101.27 修"💊 你使用了战斗道具"无回复数值，
    此前 payload="0" 只播报不回显；回蓝统一在 _do_use_item 应用，避免双份恢复）。
    v104 M02 P1-5：战斗内/战斗外满蓝同款拦截（此前满蓝白扣道具）。"""
    d = ctx.data
    mana_v = d["mana"]
    # <=1 视为百分比（1.0=100% 完全回复），>1 固定值
    if mana_v <= 1:
        mana_v = int(ctx.player["max_mp"] * mana_v)
    if ctx.battle:
        # v104 M02 P1-5：战斗内满蓝拦截（与 tpl_heal 同规则）——满蓝纯回蓝不扣
        # 道具、不消耗回合；血量取权威来源（副本快照/引擎实时上限，见 _battle_cur_max）
        if not d.get("stamina") and not d.get("heal"):
            _mp, _max = _battle_cur_max(ctx, "mp", "max_mp")
            if _mp >= _max:
                return ItemResult(
                    text=f"💙 你现在的魔力是满的({_mp}/{_max})，用不着【{d['name']}】～",
                    consume=False)
        return ItemResult(payload=f"mana:{mana_v}")
    # 战斗外：满蓝纯回蓝拦截不消耗（v104 M02 P1-5 补齐，此前满蓝也扣）
    if ctx.player["mp"] >= ctx.player["max_mp"] and not d.get("stamina") and not d.get("heal"):
        return ItemResult(
            text=f"💙 你现在的魔力是满的({ctx.player['mp']}/{ctx.player['max_mp']})，用不着【{d['name']}】～",
            consume=False)
    db = ctx._db()
    st_msg = ctx.hook("stamina_msg", ctx.group_id, ctx.qq_id, ctx.player) or ""
    new_mp = min(ctx.player["max_mp"], ctx.player["mp"] + mana_v)
    db.update_player(ctx.group_id, ctx.qq_id, mp=new_mp)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"💙 你使用了【{d['name']}】，恢复 {mana_v} 点魔力！\n💙 {new_mp}/{ctx.player['max_mp']}{st_msg}")


@register("heal_mana", battle_ok=True)
def tpl_heal_mana(ctx):
    """v104R3 M16 P2-3：heal+mana 复合药水（全效药水/月之露等）。
    战斗外：复用 _food_out_battle 即时双恢复（回血回蓝+体力，满状态拦截不消耗）。
    战斗内：payload=f"hm:{hp},{mp}"（battle._do_use_item 的 hm: 分支双恢复）；
    全满拦截不消耗（对齐 tpl_heal/tpl_mana 的 M02 P1-5 满状态规则）。"""
    d = ctx.data
    if ctx.battle:
        _hp, _max_hp = _battle_cur_max(ctx, "hp", "max_hp")
        _mp, _max_mp = _battle_cur_max(ctx, "mp", "max_mp")
        if _hp >= _max_hp and _mp >= _max_mp:
            return ItemResult(
                text=f"❤️💙 你的生命和魔力都是满的({_hp}/{_max_hp} · {_mp}/{_max_mp})，用不着【{d['name']}】～",
                consume=False)
        hv = d["heal"] if d["heal"] > 1 else int(ctx.player["max_hp"] * d["heal"])
        mv = d["mana"] if d["mana"] > 1 else int(ctx.player["max_mp"] * d["mana"])
        return ItemResult(payload=f"hm:{hv},{mv}")
    # 战斗外：全满拦截（_food_out_battle 对带 mana 物品无全满拦截，此处补）
    if (ctx.player["hp"] >= ctx.player["max_hp"]
            and ctx.player["mp"] >= ctx.player["max_mp"]
            and not d.get("stamina")):
        return ItemResult(
            text=f"❤️💙 你的生命和魔力都是满的({ctx.player['hp']}/{ctx.player['max_hp']} · {ctx.player['mp']}/{ctx.player['max_mp']})，用不着【{d['name']}】～",
            consume=False)
    return _food_out_battle(ctx)


@register("stamina", battle_ok=True)
def tpl_stamina(ctx):
    """体力恢复（纯体力食物）。体力满时拦截不消耗。
    战斗内：体力由 use() 的 st 分支处理，payload="0"（不恢复 HP）。"""
    d = ctx.data
    val = int(d.get("stamina", 0))
    if ctx.battle:
        return ItemResult(payload="0")
    st_gain = ctx.hook("add_stamina", ctx.group_id, ctx.qq_id, val, ctx.player) or 0
    if st_gain <= 0:
        p = ctx.hook("get_player") or ctx.player
        cur = ctx.hook("stamina_cur", p) or 0
        mx = ctx.hook("stamina_max", p) or 0
        return ItemResult(
            text=f"🍖 你肚子还饱着呢(体力 {cur}/{mx})，先活动活动再吃吧～", consume=False)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"🍖 你吃下了【{d['name']}】！\n⚡ 恢复 {st_gain} 点体力({ctx.hook('stamina_cur', ctx.hook('get_player') or ctx.player)}/{ctx.hook('stamina_max', ctx.hook('get_player') or ctx.player)})")


@register("food", battle_ok=True)
def tpl_food(ctx):
    """v101.28 食物（hot 字段标记）：战斗内=持续恢复（hot 每回合回血/回蓝），
    战斗外=即时回复+体力（与 heal/mana 模板同效果，合并播报）。"""
    d = ctx.data
    if ctx.battle:
        heal_pct = float(d.get("hot") or 0)
        mana_pct = float(d.get("hot_mana") or 0)
        turns = int(d.get("hot_turns") or 3)
        return ItemResult(payload=f"hot:{heal_pct},{mana_pct},{turns}")
    return _food_out_battle(ctx)


@register("food_buff", battle_ok=True)
def tpl_food_buff(ctx):
    """v101.28b 战斗料理（effect + 恢复字段）：战斗内=属性 buff（弱化版，3 回合），
    战斗外=即时回复+体力（同 tpl_food 战斗外）。"""
    d = ctx.data
    if ctx.battle:
        eff = d.get("effect", "")
        key = _BUFF_KEYS.get(eff, eff)
        return ItemResult(payload=f"buff:{key}")
    return _food_out_battle(ctx)


@register("food_effect", battle_ok=True)
def tpl_food_effect(ctx):
    """v101.28e 效果料理（food_effect + 恢复字段）：战斗内=获得食物效果（本场有效），
    战斗外=即时回复+体力（同 tpl_food 战斗外）。"""
    d = ctx.data
    if ctx.battle:
        aids = d.get("food_effect", "")
        if isinstance(aids, str):
            aids = [a for a in aids.split(",") if a]
        return ItemResult(payload=f"foodfx:{','.join(aids)}")
    return _food_out_battle(ctx)


def _food_out_battle(ctx):
    """食物战斗外公共逻辑：即时回复 + 体力（满血拦截）。"""
    d = ctx.data
    db = ctx._db()
    st_msg = ctx.hook("stamina_msg", ctx.group_id, ctx.qq_id, ctx.player) or ""
    msgs = []
    changed = False
    if d.get("heal"):
        hv = d["heal"] if d["heal"] > 1 else int(ctx.player["max_hp"] * d["heal"])
        if ctx.player["hp"] < ctx.player["max_hp"] or d.get("mana") or d.get("stamina"):
            new_hp = min(ctx.player["max_hp"], ctx.player["hp"] + hv)
            db.update_player(ctx.group_id, ctx.qq_id, hp=new_hp)
            msgs.append(f"恢复 {hv} 点生命")
            changed = True
    if d.get("mana"):
        mv = d["mana"] if d["mana"] > 1 else int(ctx.player["max_mp"] * d["mana"])
        if ctx.player["mp"] < ctx.player["max_mp"] or d.get("stamina"):
            new_mp = min(ctx.player["max_mp"], ctx.player["mp"] + mv)
            db.update_player(ctx.group_id, ctx.qq_id, mp=new_mp)
            msgs.append(f"恢复 {mv} 点魔力")
            changed = True
    if not changed:
        return ItemResult(
            text=f"❤️ 你现在的状态是满的({ctx.player['hp']}/{ctx.player['max_hp']})，用不着【{d['name']}】～",
            consume=False)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"🍖 你吃下了【{d['name']}】，{'、'.join(msgs)}！\n{st_msg}".rstrip("\n"))


# ---- 战斗药水（6 种 effect → p_buffs key）----
_BUFF_KEYS = {"buff_atk": "atk_up", "buff_def": "def_up", "buff_spd": "spd_up",
              "buff_crit": "crit_up", "buff_matk": "matk_up_pot",
              "buff_atk_def": "atk_up,def_up",
              # v101.28b 食物增益（弱化版 BUFF_MULT food_* 键，战斗中 3 回合）
              "buff_atk_food": "food_atk_up", "buff_def_food": "food_def_up",
              "buff_spd_food": "food_spd_up", "buff_crit_food": "food_crit_up",
              "buff_matk_food": "food_matk_up",
              # v104 M08 P2-12：精灵果酱 food_spd_up_small（v105 M16 已在 battle.py BUFF_MULT
              # 实现 spd+10% 本场，键不在本映射表易误导维护——补进注释对齐）
              "food_spd_up_small": "food_spd_up_small",
              # v101.28f 药水强度分档（战吼/龙力/蛮力/风灵/致命/锐目/秘法/星辉/虚空/战圣）
              "buff_atk_big": "atk_up_big", "buff_atk_small": "atk_up_small",
              "buff_spd_small": "spd_up_small", "buff_crit_small": "crit_up_small",
              "buff_crit_big": "crit_up_big",
              "buff_matk_strong": "matk_up_strong", "buff_matk_crit": "matk_up_strong,crit_up_small",
              "buff_atk_big_def": "atk_up_big,def_up",
              # v101.28f 药水特殊效果（→ special: payload，_do_use_item 分发）
              "next_atk_up": "special:next_atk_up", "heal_up": "special:heal_up",
              "magic_resist": "special:magic_resist", "thorns_pot": "special:thorns_pot",
              "dodge_pot": "special:dodge_pot", "cc_immune": "special:cc_immune",
              "execute_pot": "special:execute_pot", "armor_break_pot": "special:def_down",
              "lifesteal_pot": "special:lifesteal_pot",  # v106.3 嗜血药剂
              "crit_dmg_pot": "special:crit_dmg_pot",    # v106.3 狂暴药剂
              "block_pot": "special:block_pot",          # v106.3 岩壁药剂
              # v125.3 收口审计 P1 修复：穿甲/破法药剂缺映射 → 战斗中使用走 none 被拒（有 handler 有数据无通路）
              "pene_pot": "special:pene_pot", "pene_magi_pot": "special:pene_magi_pot",
              "rock_shield": "special:shield_small", "holy_shield": "special:shield_big",
              # v130.2 资源联动消耗品（战斗内特殊分发；effect_data 数值随 payload 传递，见 _make_buff_tpl）
              "restore_resource": "special:restore_resource",
              "restore_resource_full": "special:restore_resource_full",
              "resource_amp": "special:resource_amp",
              "mana_cost_down": "special:mana_cost_down",
              "buff_phys_next": "special:buff_phys_next",
              "full_tension": "special:full_tension"}
# v130.2 资源联动消耗品 effect 名集合：effect_data 每件数值不同，须随 special payload 传递
#（旧特殊药水如 next_atk_up 共用一套 DEFAULTS，保持 special:<kind> 裸 payload 兼容旧测试/行为）
_V130_ITEM_EFFECTS = {"restore_resource", "restore_resource_full", "resource_amp",
                      "mana_cost_down", "buff_phys_next", "full_tension",
                      "battle_start_resource"}


def _make_buff_tpl(key):
    def tpl_buff(ctx):
        if not ctx.battle:
            return ItemResult(text="战斗药水只能在战斗中使用！(输入『攻击』进入战斗后使用)")
        mapped = _BUFF_KEYS[key]
        if mapped.startswith("special:"):
            # v130.2：资源类/数值各异的药水把物品 effect_data 随 payload 传递（special:<kind>:<json>），
            # battle._do_use_item 解析后传入 handler（旧特殊药水无 effect_data → 保持 special:<kind>）
            payload = mapped
            if key in _V130_ITEM_EFFECTS:
                _ed = ctx.data.get("effect_data")
                if isinstance(_ed, dict) and _ed:
                    payload = mapped + ":" + json.dumps(_ed, ensure_ascii=True, separators=(",", ":"))
            return ItemResult(payload=payload)
        return ItemResult(payload=f"buff:{mapped}")
    return tpl_buff


for _k in _BUFF_KEYS:
    TEMPLATES[_k] = _make_buff_tpl(_k)
    META[_k] = {"battle_ok": True}


def _v130_pend_add(ctx, entry):
    """v130.2 战前待用队列：event_state prebattle_{qq_id} 追加效果（json list），
    战斗初始化段 battle._init_resources 读取注入（战前猛火餐/夜枭茶/澎湃烈酒/香薰圣烛）。"""
    import time as _t
    db = ctx._db()
    _key = f"prebattle_{ctx.qq_id}"
    _pend = []
    _raw = db.get_event_state(_key)
    if _raw:
        try:
            _pend = json.loads(_raw)
        except Exception:
            _pend = []
    if not isinstance(_pend, list):
        _pend = []
    entry = dict(entry or {})
    entry["ts"] = int(_t.time())
    _pend.append(entry)
    db.set_event_state(_key, json.dumps(_pend, ensure_ascii=False))


@register("resource_amp", battle_ok=True)
def tpl_resource_amp(ctx):
    """v130.2 资源增幅（沸腾战血/影袭药水/迅捷之核/香薰圣烛）：
    战斗内 → special 分发（带 effect_data）；战斗外（香薰圣烛「战斗外点燃」）→ 存入战前待用队列，
    战斗开始时由 _init_resources 挂载 amp。"""
    d = ctx.data
    ed = d.get("effect_data")
    if not ctx.battle:
        _v130_pend_add(ctx, {"type": "resource_amp", **(ed if isinstance(ed, dict) else {})})
        ctx.hook("remove_item")
        return ItemResult(text=f"🕯️ 你点燃了【{d['name']}】——开场后持续生效！(战斗开始后生效，先到先得)")
    payload = "special:resource_amp"
    if isinstance(ed, dict) and ed:
        payload += ":" + json.dumps(ed, ensure_ascii=True, separators=(",", ":"))
    return ItemResult(payload=payload)


@register("battle_start_resource", battle_ok=False)
def tpl_battle_start_resource(ctx):
    """v130.2 战前资源预充（战前猛火餐/夜枭茶/澎湃烈酒）：战斗开始前使用 → 存入战前待用队列，
    战斗开始时由 _init_resources 预充（食物/饮品，非战斗中；夜枭茶 30 分钟有效）。"""
    d = ctx.data
    if ctx.battle:
        return ItemResult(text=f"【{d['name']}】需在战斗开始前使用！战斗中用不上～", consume=False)
    ed = d.get("effect_data")
    if not isinstance(ed, dict) or not ed:
        return ItemResult(text=f"【{d['name']}】效果配置异常，使用失败～", consume=False)
    _v130_pend_add(ctx, {"type": "battle_start_resource", **ed})
    ctx.hook("remove_item")
    name = d["name"]
    extra = "烈酒入喉，气机澎湃！" if name == "澎湃烈酒" else ""
    return ItemResult(
        text=f"🍖 你喝下了【{name}】——战斗开始时预充生效！(30 分钟内有效){extra}")


@register("return_vila")
def tpl_return_vila(ctx):
    """回城卷轴：回最近城镇（v95.13：原写死 oak_town，新世界地图按距离）。"""
    db = ctx._db()
    C = ctx._C()
    cur = ctx.player.get("cur_map", "")
    dest = ctx.hook("nearest_town", cur) or ctx._C().START_MAP
    # v104 P2(M22): 城内直达（回城卷轴）落 subareas[0]（广场），与方碑传送/战败回城/出门一致
    # （core/maps.py:115 注释明确"传送/回家等城内直达走广场不走城门"；原实现落 map_entry_subarea=城门）
    sas = C.MAP_BY_ID.get(dest, {}).get("subareas") or []
    first_sa = sas[0] if sas else None
    db.update_player(ctx.group_id, ctx.qq_id,
                     cur_map=dest, cur_subarea=first_sa["id"] if first_sa else "")
    town_name = C.MAP_BY_ID.get(dest, {}).get("name", "城镇")
    ctx.hook("remove_item")
    return ItemResult(text=f"🧭 卷轴展开，光芒闪过——你回到了{town_name}！")


@register("teleport_portal")
def tpl_teleport_portal(ctx):
    """传送卷轴（v104 P2(M22)：与回城卷轴区分）——方碑锚定传送：
    传送到玩家最后激活的方碑所在城镇广场（复用方碑激活表 db.get_portals，
    落点 subareas[0] 对齐"城内直达走广场"约定，同方碑传送/战败回城）。
    回城卷轴=回最近城镇保命；传送卷轴=回已激活的方碑锚点（定点）。
    说明：菜单式选城需命令层把『使用 卷轴 <目标>』参数透传给模板
    （economy.py cmd_use 不传参，超本文件修改范围），故取最后激活锚点。"""
    if ctx.battle:
        return ItemResult(text="战斗中无法使用传送卷轴！先解决眼前的敌人吧～", consume=False)
    db = ctx._db()
    C = ctx._C()
    cur = ctx.player.get("cur_map", "")
    portals = [m for m in (db.get_portals(ctx.qq_id) or []) if C.MAP_BY_ID.get(m)]
    if not portals:
        return ItemResult(
            text="🌀 传送卷轴泛起微光又暗淡下去——还没有可用的方碑锚点！\n"
                 + _rand_tip("portal"),
            consume=False)
    dest = portals[-1]  # 最后激活的方碑（add_portal 追加序）
    if dest == cur:
        return ItemResult(
            text="你已经在这座方碑所在的城镇了！(传送卷轴没有消耗)",
            consume=False)
    tgt = C.MAP_BY_ID[dest]
    sas = tgt.get("subareas") or []
    first_sa = sas[0] if sas else None
    db.update_player(ctx.group_id, ctx.qq_id,
                     cur_map=dest, cur_subarea=first_sa["id"] if first_sa else "")
    db.add_visited(ctx.group_id, ctx.qq_id, dest)
    db.clear_talk_state(ctx.group_id, ctx.qq_id)  # v95 #142：传送落地清对话，防"还在交谈中"残留
    ctx.hook("remove_item")
    p = C.PORTALS.get(dest, {})
    pname = p.get("name", "方碑") if p else "方碑"
    picon = p.get("icon", "🌌") if p else "🌌"
    anchors = "、".join(C.MAP_BY_ID[m].get("name", m) for m in portals)
    return ItemResult(text=(
        f"🌀 传送卷轴展开，星辉流转——你抵达了【{tgt.get('name', '城镇')}】({picon}{pname})！\n"
        f"📍 当前方碑锚点：{anchors}\n"
        + _rand_tip("portal")))


@register("lucky")
def tpl_lucky(ctx):
    """幸运护符：10 分钟打怪金币 ×1.5、材料 +1。"""
    import time
    db = ctx._db()
    ctx.hook("remove_item")
    db.update_player(ctx.group_id, ctx.qq_id, lucky_until=int(time.time()) + 600)
    return ItemResult(
        text="🍀 幸运护符泛起微光，你的气息变得祥和……\n"
             + _rand_tip("lucky"))


# ---- v102.3 生活技能差异化：鱼饵（垂钓品质加权，仅 1 次） ----
_BAIT_INFO = {
    "bait_glow": ("萤光鱼饵", "下次垂钓紫/橙档概率大幅提升"),
    "bait_dough": ("面团鱼饵", "下次垂钓绿/蓝档品质权重提升"),
    "bait_blood": ("血饵", "下次垂钓稀有鱼种概率提升"),
}


def _make_bait_tpl(key):
    def tpl_bait(ctx):
        db = ctx._db()
        if ctx.battle:
            return ItemResult(text="鱼饵只能在水边使用，战斗结束后再挂饵吧～", consume=False)
        # v104 R3 M15 P3-4：非战斗也校验水域——desc 承诺"只能在水边使用"，
        # 原实现仅拦战斗（ctx.battle），任意地点可用；与垂钓命令同源判定：
        # 当前地图无 FISHING_SPOTS 钓点（城镇/野外）拒绝挂饵
        _C = ctx._C()
        _cur = (ctx.player or {}).get("cur_map", "")
        if _cur and not _C.FISHING_SPOTS.get(_cur):
            return ItemResult(text="鱼饵只能在水边使用——这里没有水域，到有钓点的地方再挂饵吧～", consume=False)
        name, tip = _BAIT_INFO[key]
        ctx.hook("remove_item")
        db.set_event_state(f"bait_{ctx.qq_id}", json.dumps({"kind": key.split("_")[1], "ts": int(time.time())}, ensure_ascii=False))
        return ItemResult(text=f"🎣 你给鱼钩挂上了【{name}】——{tip}！(仅限下一次垂钓)")
    return tpl_bait


for _k in _BAIT_INFO:
    TEMPLATES[_k] = _make_bait_tpl(_k)
    META[_k] = {"battle_ok": False}


@register("enhance_boost")
def tpl_enhance_boost(ctx):
    """星铁强化剂（v102.3）：下一次强化装备必定成功。"""
    db = ctx._db()
    if ctx.battle:
        return ItemResult(text="强化剂要留着到铁匠铺用，战斗中用不上～", consume=False)
    ctx.hook("remove_item")
    db.set_event_state(f"enhance_boost_{ctx.qq_id}", "1")
    return ItemResult(text="🔧 星铁强化剂渗入装备纹理，泛着星火微光……\n" + _rand_tip("enhance"))


@register("clear_red")
def tpl_clear_red(ctx):
    """红名清除券：立即消除红名。"""
    db = ctx._db()
    if not ctx.hook("is_redname", ctx.qq_id):
        return ItemResult(text="你现在不是红名，用不着这张券～(留着防身吧)", consume=False)
    # v110 审计修复：26 章 §3.3「红名清除券（不可 PVP 时使用）」——战斗中禁止使用
    if db.get_battle(ctx.group_id, ctx.qq_id):
        return ItemResult(text="你正在战斗中，无法使用清除券！", consume=False)
    ctx.hook("remove_item")
    db.set_event_state(f"red_{ctx.qq_id}", "0")
    return ItemResult(text="🎫 券面符文亮起，笼罩你的杀气消散了！你不再是红名了。")


@register("open_chest")
def tpl_open_chest(ctx):
    """宝箱：金币 + 50% 概率蓝图（v41：宝箱不再掉成品装备，统一走锻造）。"""
    import uuid
    db = ctx._db()
    C = ctx._C()
    ctx.hook("remove_item")
    gold = random.randint(30, 80) + ctx.lv * 3
    db.update_player(ctx.group_id, ctx.qq_id, gold=ctx.player["gold"] + gold)
    lines = [f"🎁 你打开了【{ctx.item_name()}】！", f"💰 获得 {gold} 金币！"]
    if random.random() < C.CHEST_BP_CHANCE:  # v101.5 常量
        bp = C.roll_blueprint(max(1, ctx.lv))
        db.add_item(ctx.group_id, ctx.qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
        lines.append(f"📜 宝箱里还有：{bp['name']}！")
    return ItemResult(text="\n".join(lines))


@register("open_rune_chest")
def tpl_open_rune_chest(ctx):
    """符文匣（v117 副本材料联动·方案D）：开出一枚随机稀有/紫色符文（blue+purple 品质池）。

    副本闲置材料（黑渊之眼/龙宫珠 等）经炼金配方合成符文匣 → 『使用』联动符文系统。
    入包写法与暗格宝箱一致（instance.py _instance_secret_chest）：key 取
    rune_<effect>_<lvl>（同键可叠加），data 由 C.rune_item(effect, lvl) 构造——含
    name/effect/lvl/quality/price/desc，供『附魔』刻印读取（economy.py 读 rd["effect"]，
    缺字段会 KeyError 崩溃）。紫色符文加权（40%），等级 1–2。
    物品消耗走 ctx.hook("remove_item")（战斗外模板自行扣除，与 tpl_heal 同款）。"""
    db = ctx._db()
    C = ctx._C()
    pool = [k for k, r in C.RUNES.items() if (r.get("quality") or "") in ("blue", "purple")]
    if not pool:
        return ItemResult(text="符文匣里空空如也……(符文数据缺失)", consume=False)
    # 紫色加权：40% 紫 / 60% 蓝（"稀有/紫色符文"描述下的防通胀平衡）
    purple = [k for k in pool if (C.RUNES[k].get("quality") or "") == "purple"]
    blue = [k for k in pool if (C.RUNES[k].get("quality") or "") == "blue"]
    if random.random() < 0.4 and purple:
        rk = random.choice(purple)
    else:
        rk = random.choice(blue) if blue else random.choice(purple)
    r_def = C.RUNES[rk]
    rune_data = C.rune_item(r_def["effect"], random.randint(1, 2))
    if not rune_data:
        return ItemResult(text="符文匣里空空如也……(符文数据缺失)", consume=False)
    db.add_item(ctx.group_id, ctx.qq_id,
                f"rune_{r_def['effect']}_{rune_data['lvl']}", rune_data)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"📦 你打开了【{ctx.item_name()}】！\n"
             f"✨ 匣中泛起微光——符文【{rune_data['name']}】！\n"
             + _rand_tip("enchant"))



@register("pet_egg")
def tpl_pet_egg(ctx):
    """宠物蛋：孵化宠物（已有宠物/同品种拦截）。"""
    db = ctx._db()
    C = ctx._C()
    pet_key = ctx.data.get("pet_key")
    if not pet_key:
        return ItemResult(text="这枚宠物蛋有点奇怪……", consume=False)
    pet = db.pet_get(ctx.qq_id)
    pet = db.pet_decay_satiety(pet)
    if pet:
        db.pet_update(ctx.qq_id, satiety=pet["satiety"], last_sat_time=pet["last_sat_time"])
    if pet:
        if pet.get("pet_key") == pet_key:
            return ItemResult(
                text="你已经有一只【该品种】宠物啦！可以『出售』这颗蛋，或『放生』后重新孵化(图鉴记录保留)。",
                consume=False)
        return ItemResult(text="你已经有一只宠物啦！先『放生』再孵化新品种吧～", consume=False)
    pdef = next((p for p in C.PET_POOL if p["key"] == pet_key), None)
    if not pdef:
        return ItemResult(text="宠物蛋里的生命气息微弱……", consume=False)
    ctx.hook("remove_item")
    db.pet_create(ctx.qq_id, pet_key, pdef["name"])
    db.pet_dex_add(ctx.qq_id, pet_key)
    dex_count = len(db.pet_dex_get(ctx.qq_id))
    return ItemResult(
        text=f"🥚 宠物蛋微微颤动……裂开了！\n"
             f"🎉 {pdef['icon']} 【{pdef['name']}】破壳而出，成为了你的伙伴！(图鉴 {dex_count}/{len(C.PET_POOL)})\n"
             + _rand_tip("pet"))


@register("mount")
def tpl_mount(ctx):
    """坐骑缰绳：解锁坐骑。"""
    db = ctx._db()
    C = ctx._C()
    mk = ctx.data.get("mount_key")
    mdef = C.MOUNT_BY_KEY.get(mk) if mk else None
    if not mdef:
        return ItemResult(text="这缰绳上的气息有点古怪……", consume=False)
    mounts = ctx.player.get("mounts") or {}
    owned = list(mounts.get("owned") or [])
    if mk in owned:
        return ItemResult(text=f"你已经拥有『{mdef['name']}』了！", consume=False)
    owned.append(mk)
    mounts["owned"] = owned
    db.update_player(ctx.group_id, ctx.qq_id, mounts=mounts)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"🐾 缰绳上的封印解开，{mdef['icon']}【{mdef['name']}】顺从地蹭了蹭你！\n"
             + _rand_tip("mount"))


# v104 P2-7 修复：净化卷轴死数据——战斗内清除玩家负面 buff（stun/freeze/silence/spd_down）
_PURIFY_DEBUFF_KEYS = ("stun", "freeze", "silence", "spd_down",
                       "atk_down", "def_down", "matk_down", "mdef_down")


@register("purify", battle_ok=True)
def tpl_purify(ctx):
    """净化卷轴（v104 P2-7 修复：原无 effect 字段 → infer_template 判 none 死数据）。
    战斗内：清除 p_buffs 中的负面效果。普通战斗 p_buffs 为平铺 {buff: 回合}；
    副本战斗为 {成员: {buff: 回合}}，按道具文案『驱散全队负面』清全部成员。
    p_buffs 与战斗引擎 Battle 实例共享同一 dict 对象（battle.py from_state 直接引用
    st["p_buffs"]），此处直接改状态即被 player_turn 感知并随 to_state 持久化；
    payload="0" 走 _do_use_item 默认分支播报（不新增 battle.py 分支的约束下最简实现）。
    战斗外/无负面可驱散：不消耗（与满血治疗拦截同款，M02 P1-5 模式）。"""
    d = ctx.data
    if not ctx.battle:
        return ItemResult(
            text=f"✨ 你展开【{d['name']}】，但此刻你身上没有需要净化的负面状态～",
            consume=False)
    st = ctx.battle
    pb = st.get("p_buffs") if isinstance(st, dict) else getattr(st, "p_buffs", None)
    removed = []
    if isinstance(pb, dict):
        # 副本结构 {成员: {buff:回合}}（全队驱散）；普通战斗平铺 {buff:回合}
        nested = any(isinstance(v, dict) for v in pb.values())
        for t in (list(pb.values()) if nested else [pb]):
            if isinstance(t, dict):
                for k in _PURIFY_DEBUFF_KEYS:
                    if k in t:
                        t.pop(k, None)
                        removed.append(k)
    removed = list(dict.fromkeys(removed))
    if not removed:
        return ItemResult(
            text=f"✨ 你展开【{d['name']}】，但此刻你身上没有需要净化的负面状态～",
            consume=False)
    return ItemResult(payload="0")


@register("skill_tome")
def tpl_skill_tome(ctx):
    """v112 P1 隐藏技能书：一次性学会隐藏技能（learn_skill + require_class 数据驱动）。

    校验链：源流（require_class，可空=全职业）→ 等级 → 已学拦截 → learned_skills 追加。
    战斗内不可使用（battle_ok=False，走 use() 战斗外分支）。
    跨流派学习是设计使然：技能书 = 横向扩展，不选对应流派也能学（§6 铁律）。
    """
    from .. import content as C
    from .. import engine as E
    d = ctx.data
    learn = d.get("learn_skill", "")
    req = d.get("require_class", "") or ""
    # 技能定义按源流职业查（技能书 = 跨流派稀有技，技能属于隐藏线表；玩家职业只用于源流校验）
    info = E.skill_info(req, learn) if req else E.skill_info(ctx.player.get("class_name", ""), learn)
    if not info:
        return ItemResult(text=f"你翻开【{d.get('name', '技能书')}】，但其中的技艺晦涩难解……(技能数据缺失)", consume=False)
    if req:
        req_id = C.resolve("classes", req)
        cls_id = C.resolve("classes", ctx.player.get("class_name", ""))
        if cls_id != req_id:
            src_name = C.CLASSES.get(req_id, {}).get("name", req)
            return ItemResult(
                text=f"书页上流转着【{src_name}】一脉的印记，与你的力量不合……", consume=False)
    need_lv = int(info.get("lv", 1))
    if ctx.player.get("level", 0) < need_lv:
        return ItemResult(
            text=f"书中的技艺需要 Lv.{need_lv} 才能参悟，你才 Lv.{ctx.player.get('level', 0)}。", consume=False)
    learned = list(ctx.player.get("learned_skills", []))
    sname = info.get("name", learn)
    if C.resolve("skills", sname) in [C.resolve("skills", s) for s in learned if s]:
        return ItemResult(text=f"『{sname}』你早已掌握，这本书对你没有用了。", consume=False)
    self_db = ctx._db()
    self_db.update_player(ctx.group_id, ctx.qq_id, learned_skills=learned + [sname])
    try:
        C.check_achievements(ctx.group_id, ctx.qq_id, ctx.player)
    except Exception:
        pass
    ctx.hook("remove_item")  # 战斗外路径模板自行扣除（与 tpl_heal 同款）
    return ItemResult(
        text=f"📖 你参悟了技能书，学会了隐藏技能『{sname}』！\n「{info['desc']}」")


@register("none")
def tpl_none(ctx):
    """兜底：不能使用的物品（含未实现的战斗卷轴等占位数据）。
    v113.5 O117：『使用 风干肉』等材料无引导 → 按类型补副业用途说明。
    v124：任务道具（支线信物/线索）走 use 目标支线——给友好使用文案（不消耗）。"""
    # v124 任务道具：支线信物 use（如 候鸟的信/青铜雨铃/月辉信物），走 _update_use_quests 推进
    if (ctx.data or {}).get("type") == "任务道具":
        return ItemResult(text=f"你使用了『{ctx.item_name()}』。", consume=False)
    # v113.5 O117：材料类（食材/矿材）不可直接使用，提示可走副业加工（烹饪/锻造/炼金）
    # v126.3：配置 type 细分为 18 种（兽材/矿石/草药/…），水合后 data.type 是真实细分值——
    # 按 C.MATERIAL_KIND_TYPES 大类归并判定，否则兽材/矿石等材料漏判退回通用文案
    from .. import content as C  # v102.2 延迟导入（core 聚合链惯例）
    if (ctx.data or {}).get("type") in C.MATERIAL_KIND_TYPES:
        return ItemResult(
            text=f"『{ctx.item_name()}』不能直接使用——这是材料，可『烹饪』『锻造』『炼金』等副业加工成成品～",
            consume=False)
    return ItemResult(text=f"『{ctx.item_name()}』不能使用。", consume=False)
