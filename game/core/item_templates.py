# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - item_templates.py（v97.7：道具效果模板引擎）

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

TEMPLATES = {}
META = {}


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
    if data.get("hot"):
        # v101.28 食物持续恢复：有 hot 字段 = 食物 → food 模板
        # （战斗内=持续恢复，战斗外=即时回复+体力；药水无 hot 字段走原逻辑）
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
    战斗外：满血纯治疗拦截不消耗；复合物品（带 stamina/mana）满血仍可用。"""
    d = ctx.data
    heal_v = d["heal"]
    # <=1 视为百分比（0.2=20%；1.0=100% 完全回复），>1 固定值（旧式配方兼容）
    if heal_v <= 1:
        heal_v = int(ctx.player["max_hp"] * heal_v)
    if ctx.battle:
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


@register("mana", battle_ok=True)
def tpl_mana(ctx):
    """魔力恢复。mana <= 1 百分比（1.0=100%），> 1 固定值。
    战斗内：payload=f"mana:{绝对恢复量}"（battle.player_turn 的 _do_use_item
    识别 mana: 前缀回蓝并播报数字——v101.27 修"💊 你使用了战斗道具"无回复数值，
    此前 payload="0" 只播报不回显；回蓝统一在 _do_use_item 应用，避免双份恢复）。"""
    d = ctx.data
    mana_v = d["mana"]
    # <=1 视为百分比（1.0=100% 完全回复），>1 固定值
    if mana_v <= 1:
        mana_v = int(ctx.player["max_mp"] * mana_v)
    if ctx.battle:
        return ItemResult(payload=f"mana:{mana_v}")
    db = ctx._db()
    st_msg = ctx.hook("stamina_msg", ctx.group_id, ctx.qq_id, ctx.player) or ""
    new_mp = min(ctx.player["max_mp"], ctx.player["mp"] + mana_v)
    db.update_player(ctx.group_id, ctx.qq_id, mp=new_mp)
    ctx.hook("remove_item")
    return ItemResult(
        text=f"💙 你使用了【{d['name']}】，恢复 {mana_v} 点魔力！\n💙 {new_mp}/{ctx.player['max_mp']}{st_msg}")


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
              "rock_shield": "special:shield_small", "holy_shield": "special:shield_big"}


def _make_buff_tpl(key):
    def tpl_buff(ctx):
        if not ctx.battle:
            return ItemResult(text="战斗药水只能在战斗中使用！(输入『攻击』进入战斗后使用)")
        mapped = _BUFF_KEYS[key]
        if mapped.startswith("special:"):
            # v101.28f 药水特殊效果（护盾/反伤/处决/闪避/免疫等）→ special payload
            return ItemResult(payload=mapped)
        return ItemResult(payload=f"buff:{mapped}")
    return tpl_buff


for _k in _BUFF_KEYS:
    TEMPLATES[_k] = _make_buff_tpl(_k)
    META[_k] = {"battle_ok": True}


@register("return_vila")
def tpl_return_vila(ctx):
    """回城卷轴：回最近城镇（v95.13：原写死 oak_town，新世界地图按距离）。"""
    db = ctx._db()
    C = ctx._C()
    cur = ctx.player.get("cur_map", "")
    dest = ctx.hook("nearest_town", cur) or ctx._C().START_MAP
    entry_sa = C.map_entry_subarea(dest) if dest else None
    sas = C.MAP_BY_ID.get(dest, {}).get("subareas") or []
    first_sa = next((s for s in sas if s["id"] == entry_sa), None) or (sas[0] if sas else None)
    db.update_player(ctx.group_id, ctx.qq_id,
                     cur_map=dest, cur_subarea=first_sa["id"] if first_sa else "")
    town_name = C.MAP_BY_ID.get(dest, {}).get("name", "城镇")
    ctx.hook("remove_item")
    return ItemResult(text=f"🧭 卷轴展开，光芒闪过——你回到了{town_name}！")


@register("lucky")
def tpl_lucky(ctx):
    """幸运护符：10 分钟打怪金币 ×1.5、材料 +1。"""
    import time
    db = ctx._db()
    ctx.hook("remove_item")
    db.update_player(ctx.group_id, ctx.qq_id, lucky_until=int(time.time()) + 600)
    return ItemResult(
        text="🍀 幸运护符泛起微光，你的气息变得祥和……\n"
             "💡 10 分钟内打怪金币＋50%、材料掉落＋1！")


# ---- v102.3 生活技能差异化：鱼饵（垂钓品质加权，仅 1 次） ----
_BAIT_INFO = {
    "bait_glow": ("萤光鱼饵", "下次垂钓紫/橙档概率大幅提升"),
    "bait_dough": ("面团鱼饵", "下次垂钓绿/蓝档概率提升"),
    "bait_blood": ("血饵", "下次垂钓稀有鱼种概率提升"),
}


def _make_bait_tpl(key):
    def tpl_bait(ctx):
        db = ctx._db()
        if ctx.battle:
            return ItemResult(text="鱼饵只能在水边使用，战斗结束后再挂饵吧～", consume=False)
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
    return ItemResult(text="🔧 星铁强化剂渗入装备纹理，泛着星火微光……\n💡 下次『强化』必定成功！")


@register("clear_red")
def tpl_clear_red(ctx):
    """红名清除券：立即消除红名。"""
    db = ctx._db()
    if not ctx.hook("is_redname", ctx.qq_id):
        return ItemResult(text="你现在不是红名，用不着这张券～(留着防身吧)", consume=False)
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
             f"💡 输入『宠物』查看，『喂养 <材料>』恢复饱食度，升到 Lv.10 解锁宠物技能！")


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
             f"💡 输入『骑乘 {mdef['name']}』骑上它，『坐骑』查看全部！")


@register("none")
def tpl_none(ctx):
    """兜底：不能使用的物品（含未实现的战斗卷轴等占位数据）。"""
    return ItemResult(text=f"『{ctx.item_name()}』不能使用。", consume=False)
