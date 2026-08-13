# -*- coding: utf-8 -*-
"""《剑与魔法》核心层 - event_templates.py（v97.3：事件模板引擎）

消灭 commands/combat.py 里探索事件/彩蛋的 if-elif 硬编码：
事件数据只声明 template + params，执行统一走本模块注册表。

设计：
- TEMPLATES: {模板名: 函数}，函数签名 fn(ctx) -> str（返回展示文本）
- ctx 为 EventContext（group_id/qq_id/player/cur_map/params/hooks/rnd）
- 模板函数内延迟导入 db/content/engine（遵循 core 聚合链规则，防循环导入）
- 命令层专属回调（如 title_bonus）经 ctx.hooks 注入

扩展方式：
- 加事件：data/events.py 加一条 dict（template 用现有模板 + params）
- 加新玩法：register 一个新模板函数（~20 行），之后全数据化
"""
import random

TEMPLATES = {}


def register(name):
    """模板注册装饰器。"""
    def deco(fn):
        TEMPLATES[name] = fn
        return fn
    return deco


# v101.25 #349：探索宝箱/宝匣图纸掉落与战斗同规则——已学图纸折算为图纸残页，未学整张入包
# （playtest round72 小蓝抓包：宝箱掉『海风长弓图纸』已学仍整张入包，背包白占格子）
_BP_PAGE_BY_QUALITY = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}


def _add_bp_or_pages(ctx, db, bp):
    """已学图纸 → 图纸残页入包；未学 → 整张图纸入包。返回 (is_learned, bp_name, pages)。"""
    import uuid
    _learned = ctx.player.get("learned_blueprints") or []
    if bp.get("blueprint_for") in _learned:
        _pages = _BP_PAGE_BY_QUALITY.get(bp.get("quality", "white"), 1)
        db.add_item(ctx.group_id, ctx.qq_id, "mat_tu_zhi_can_ye",
                    {"name": "图纸残页", "type": "材料", "stackable": True, "price": 10},
                    count=_pages)
        return True, bp["name"], _pages
    db.add_item(ctx.group_id, ctx.qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
    return False, bp["name"], 0


class EventContext:
    """模板执行上下文。"""

    def __init__(self, group_id, qq_id, player, cur_map, params=None,
                 name="此地", hooks=None):
        self.group_id = group_id
        self.qq_id = qq_id
        self.player = player
        self.cur_map = cur_map
        self.params = params or {}
        self.name = name
        self.hooks = hooks or {}

    # ---- 便捷访问 ----
    @property
    def lv(self):
        return self.player.get("level", 1)

    def _db(self):
        from .. import db
        return db

    def _C(self):
        from .. import content as C
        return C

    def _E(self):
        from .. import engine as E
        return E

    def param(self, key, default=None):
        return self.params.get(key, default)


# ================= 模板实现 =================

@register("loot_gold")
def tpl_loot_gold(ctx):
    """金币：gold = randint(min,max) + lv*scale_lv。params: min/max/scale_lv/header"""
    db = ctx._db()
    gold = random.randint(ctx.param("min", 10), ctx.param("max", 40)) + ctx.lv * ctx.param("scale_lv", 1)
    db.update_player(ctx.group_id, ctx.qq_id, gold=ctx.player["gold"] + gold)
    header = ctx.param("header", "💰 你捡到了一些金币！")
    return header.replace("{name}", ctx.name).replace("{gold}", str(gold))


@register("loot_materials")
def tpl_loot_materials(ctx):
    """材料：从 mats 池随机 n 份入包，可带蓝图概率。params: mats/n/blueprint_chance/header
    v101.30d #O29：支持 cap_name/cap_count/fallback_mats——指定材料已有 cap_count 份时
    改掉 fallback 池（防任务/准入材料重复拾取，如泛黄书页满 3 张不再出）"""
    import uuid
    db = ctx._db()
    C = ctx._C()
    mats_pool = ctx.param("mats", ["草药"])
    cap_name = ctx.param("cap_name", "")
    if cap_name:
        have = db.count_item(ctx.group_id, ctx.qq_id, cap_name)
        if have >= ctx.param("cap_count", 1):
            mats_pool = ctx.param("fallback_mats", ["古木枝"])
    n = ctx.param("n", 1)
    got = []
    for _ in range(n):
        m = random.choice(mats_pool)
        mid = C.resolve("materials", m)
        if mid in C.MATERIALS:
            db.add_item(ctx.group_id, ctx.qq_id, mid,
                        {"name": C.display("materials", mid), "type": "材料",
                         "stackable": True, "price": C.MATERIALS[mid]["price"]})
            got.append(C.display("materials", mid))
    extra = ""
    bp_chance = ctx.param("blueprint_chance", 0)
    if bp_chance and random.random() < bp_chance:
        bp = C.roll_blueprint(max(1, ctx.lv))
        _learned, _bpn, _pages = _add_bp_or_pages(ctx, db, bp)
        if _learned:
            extra = (f"\n📜 图纸『{_bpn}』你已经学会了，化作 {_pages} 张图纸残页"
                     f"（『出售 图纸残页』变现）！")
        else:
            extra = ctx.param("bp_line", "\n📜 还翻出一张图纸：{bp}！").replace("{bp}", _bpn)
    header = ctx.param("header", "🎒 获得材料：{mats}！{extra}")
    return header.replace("{name}", ctx.name) \
                 .replace("{mats}", "、".join(got)) \
                 .replace("{extra}", extra)


@register("loot_gold_mats")
def tpl_loot_gold_mats(ctx):
    """金币+材料（可带图纸概率）。params: min/max/scale_lv/mats/blueprint_chance/header"""
    import uuid
    db = ctx._db()
    C = ctx._C()
    E = ctx._E()
    gold = random.randint(ctx.param("min", 50), ctx.param("max", 120)) + ctx.lv * ctx.param("scale_lv", 5)
    db.update_player(ctx.group_id, ctx.qq_id, gold=ctx.player["gold"] + gold)
    mat_line = ""
    mats_pool = ctx.param("mats", [])
    if mats_pool:
        mid = C.resolve("materials", random.choice(mats_pool))
        if mid in C.MATERIALS:
            db.add_item(ctx.group_id, ctx.qq_id, mid,
                        {"name": C.display("materials", mid), "type": "材料",
                         "stackable": True, "price": C.MATERIALS[mid]["price"]})
            mat_line = ctx.param("mat_line", "\n🎒 还得到一份材料：{mat}！").replace("{mat}", C.display("materials", mid))
    bp_line = ""
    bp_chance = ctx.param("blueprint_chance", 0)
    # v94 图纸经济：宝箱为图纸主要来源；阶段九：精灵森林之友——探索获得物品概率 +10%
    if ctx.param("explore_item_bonus", False):
        bp_chance = bp_chance + (0.10 if E.race_stats(ctx.player.get("race")).get("explore_item") else 0)
    if bp_chance and random.random() < bp_chance:
        bp = C.roll_blueprint(max(1, ctx.lv))
        _learned, _bpn, _pages = _add_bp_or_pages(ctx, db, bp)
        if _learned:
            bp_line = (f"\n📜 里面有一张图纸『{_bpn}』——你已经学会了，化作 {_pages} 张图纸残页"
                       f"（『出售 图纸残页』变现）！")
        else:
            bp_line = ctx.param("bp_line", "\n📜 里面还有一张泛黄的图纸：{bp}！").replace("{bp}", _bpn)
    header = ctx.param("header", "💰 获得 {gold} 金币！{mat_line}{bp_line}")
    return header.replace("{name}", ctx.name) \
                 .replace("{gold}", str(gold)) \
                 .replace("{mat_line}", mat_line) \
                 .replace("{bp_line}", bp_line)


@register("exp_gain")
def tpl_exp_gain(ctx):
    """经验 + 升级检查（沿用原 omen 逻辑）。params: min/max/scale_lv/header"""
    db = ctx._db()
    C = ctx._C()
    E = ctx._E()
    exp_gain = ctx.param("min", 15) + ctx.lv * ctx.param("scale_lv", 3)
    # #262: 同步 ctx.player 引用再写库——战斗结算进度条显示依赖同一 player dict，
    # 此前只写 DB 不更新引用，规则经验在当次面板"隐形"、玩家感知延迟到下一场
    ctx.player["exp"] = int(ctx.player.get("exp", 0)) + exp_gain
    db.update_player(ctx.group_id, ctx.qq_id, exp=ctx.player["exp"])
    player = db.get_player(ctx.group_id, ctx.qq_id)
    player["_title_bonus"] = ctx.hooks.get("title_bonus", lambda q: None)(ctx.qq_id)
    lines = [ctx.param("header", "✨ 经验 +{exp}").replace("{name}", ctx.name).replace("{exp}", str(exp_gain))]
    lv_logs, player = E.check_player_level_up(ctx.group_id, ctx.qq_id, player)
    if lv_logs:
        lines += [""] + lv_logs
        db.update_player(ctx.group_id, ctx.qq_id, level=player["level"], exp=player["exp"],
                         hp=player["hp"], mp=player["mp"], max_hp=player["max_hp"],
                         max_mp=player["max_mp"], skills=player["skills"],
                         attr_pts=player.get("attr_pts", 0), skill_points=player.get("skill_points", 0),
                         learned_skills=player.get("learned_skills", []))
    return "\n".join(lines)


@register("heal_full")
def tpl_heal_full(ctx):
    """回满血蓝。params: header"""
    db = ctx._db()
    db.update_player(ctx.group_id, ctx.qq_id, hp=ctx.player["max_hp"], mp=ctx.player["max_mp"])
    header = ctx.param("header", "❤️ 生命全满！💙 魔力全满！")
    return header.replace("{name}", ctx.name)


@register("damage")
def tpl_damage(ctx):
    """扣血（陷阱类）。params: pct/min/header"""
    db = ctx._db()
    dmg = int(ctx.player["max_hp"] * ctx.param("pct", 0.15)) + ctx.param("min", 5)
    new_hp = max(1, ctx.player["hp"] - dmg)
    db.update_player(ctx.group_id, ctx.qq_id, hp=new_hp)
    header = ctx.param("header", "你摔伤了，损失 {dmg} 点生命(当前 ❤️ {hp}/{max_hp})")
    return header.replace("{name}", ctx.name) \
                 .replace("{dmg}", str(dmg)) \
                 .replace("{hp}", str(new_hp)) \
                 .replace("{max_hp}", str(ctx.player["max_hp"]))


@register("set_state")
def tpl_set_state(ctx):
    """写入 event_state。params: key(可含 {gid}/{qid})/value/header
    value 支持特殊值 'ts'（存 {"ts": 当前时间戳}），或 dict / callable(ctx)。"""
    import json, time
    db = ctx._db()
    key = ctx.param("key", "").replace("{gid}", str(ctx.group_id)).replace("{qid}", str(ctx.qq_id))
    value = ctx.param("value", {})
    if value == "ts":
        value = {"ts": time.time()}
    elif callable(value):
        value = value(ctx)
    db.set_event_state(key, json.dumps(value, ensure_ascii=False))
    header = ctx.param("header", "")
    return header.replace("{name}", ctx.name)


@register("set_flag")
def tpl_set_flag(ctx):
    """写入隐藏线 talk_flag。params: flag/key/header"""
    db = ctx._db()
    db.set_talk_flag(ctx.group_id, ctx.qq_id, ctx.param("flag"), ctx.param("key"))
    header = ctx.param("header", "")
    return header.replace("{name}", ctx.name)


@register("dialog")
def tpl_dialog(ctx):
    """纯文案（变体池随机）。params: texts(必填)"""
    texts = ctx.param("texts", [])
    if not texts:
        return ""
    return random.choice(texts).replace("{name}", ctx.name)


@register("mystery_chest")
def tpl_mystery_chest(ctx):
    """神秘宝匣：金币 + 当前地图怪物掉落池随机材料 + 必掉图纸。沿用原逻辑。"""
    import uuid
    db = ctx._db()
    C = ctx._C()
    gold = random.randint(50, 120) + ctx.lv * 5
    db.update_player(ctx.group_id, ctx.qq_id, gold=ctx.player["gold"] + gold)
    mat_line = ""
    # v105 M23 P1-4：材料源改当前子区域怪物掉落池（与 combat.py 探索遇怪同源）——
    # v87.6 后怪物全部下沉子区域，地图级 monsters 0/116 全空，原宝匣材料行静默失效（只掉金币+图纸）
    cur_sa_id = ctx.player.get("cur_subarea") or ""
    mon_src = None
    for _sa in (ctx.cur_map.get("subareas") or []):
        if _sa["id"] == cur_sa_id:
            mon_src = _sa.get("monsters")
            break
    if mon_src is None:
        mon_src = ctx.cur_map.get("monsters", [])
    pool = [m[5] for m in mon_src]
    mats = [x for sub in pool for x in sub if x and "图纸" not in x]
    if mats:
        mid = C.resolve("materials", random.choice(mats))
        if mid in C.MATERIALS:
            db.add_item(ctx.group_id, ctx.qq_id, mid,
                        {"name": C.display("materials", mid), "type": "材料",
                         "stackable": True, "price": C.MATERIALS[mid]["price"]})
            mat_line = f"\n🎒 还得到一份材料：{C.display('materials', mid)}！"
    bp = C.roll_blueprint(max(1, ctx.lv))
    _learned, _bpn, _pages = _add_bp_or_pages(ctx, db, bp)
    if _learned:
        bp_txt = (f"📜 里面还有一张图纸『{_bpn}』——你已经学会了，化作 {_pages} 张图纸残页"
                  f"（『出售 图纸残页』变现）！")
    else:
        bp_txt = f"📜 里面还有一张泛黄的图纸：{_bpn}！"
    return (f"📦 【神秘宝匣】你在{ctx.name}的角落发现一只埋藏千年的宝匣！\n"
            f"💰 打开：{gold} 金币！{mat_line}\n"
            f"{bp_txt}")


@register("merchant")
def tpl_merchant(ctx):
    """流浪商人：低价装备（可拒绝）。沿用原 merchant 逻辑。"""
    import uuid
    db = ctx._db()
    C = ctx._C()
    q = random.choices(["white", "green", "blue"], weights=[45, 40, 15])[0]
    equip = C.generate_equip(random.choice(["weapon", "ring", "necklace"]), max(1, ctx.lv), q)
    price = int(equip["price"] * 0.6)
    if ctx.player["gold"] >= price and random.random() < C.TRADER_DEAL_CHANCE:  # v101.5 常量
        db.update_player(ctx.group_id, ctx.qq_id, gold=ctx.player["gold"] - price)
        db.add_item(ctx.group_id, ctx.qq_id, f"eq_{uuid.uuid4().hex[:8]}", equip)
        return (f"🛒 【流浪商人】一个商人拉住你：“勇士，看货！便宜卖你了！”\n"
                f"你花 {price} 金币买下了 {C.QUALITY[equip['quality']]['color']}【{equip['name']}】")
    return (f"🛒 【流浪商人】一个商人向你兜售 {C.QUALITY[equip['quality']]['color']}【{equip['name']}】，"
            f"只要 {price} 金币……你摇了摇头：不买不买。商人悻悻地走了。")


@register("wandering")
def tpl_wandering(ctx):
    """迷路的旅人：限一次谢礼。沿用原 wandering 逻辑。"""
    db = ctx._db()
    C = ctx._C()
    player = db.get_player(ctx.group_id, ctx.qq_id)
    if player.get("explore_wandering"):
        return "🧭 【迷路的旅人】旅人认出了你，笑着摆摆手：'缘分到此为止，下次有缘再见！'"
    # v102.2：特殊物品用 key（i_scroll_escape），材料保留中文名（resolve 按名解析）
    rewards = ["克罗的罗盘", "i_scroll_escape", "谷地露水"]
    rw = random.choice(rewards)
    if rw == "i_scroll_escape":
        db.add_item(ctx.group_id, ctx.qq_id, "i_scroll_escape",
                    {"name": "回城卷轴", "type": "消耗品", "stackable": True,
                     "effect": "return_vila", "price": 500})
    else:
        mid = C.resolve("materials", rw)
        if mid in C.MATERIALS:
            db.add_item(ctx.group_id, ctx.qq_id, mid,
                        {"name": C.display("materials", mid), "type": "材料",
                         "stackable": True, "price": C.MATERIALS[mid]["price"]})
    db.update_player(ctx.group_id, ctx.qq_id, explore_wandering=1)
    return (f"🧭 【迷路的旅人】一位旅人感激你的指路，硬塞给你一件谢礼！\n"
            f"🎒 获得：{rw}")


@register("combo")
def tpl_combo(ctx):
    """组合模板：steps 顺序执行，拼接文本。params: steps: [{template, params, header?...}]"""
    lines = []
    for i, step in enumerate(ctx.param("steps", [])):
        sub_params = dict(ctx.params)
        sub_params.update(step.get("params", {}))
        sub_ctx = EventContext(ctx.group_id, ctx.qq_id, ctx.player, ctx.cur_map,
                               params=sub_params, name=ctx.name, hooks=ctx.hooks)
        fn = TEMPLATES.get(step.get("template"))
        if fn:
            text = fn(sub_ctx)
            if text:
                lines.append(text)
    return "\n".join(lines)


@register("random_choice")
def tpl_random_choice(ctx):
    """v97.4 概率分支：chance 命中执行 hit 子模板，否则 miss。params: chance/hit/miss
    hit/miss 为 {template, params}（与 combo 的 step 同构），支持嵌套。"""
    branch = ctx.param("hit" if random.random() < ctx.param("chance", 0.5) else "miss", None)
    if not branch:
        return ""
    sub_params = dict(ctx.params)
    sub_params.update(branch.get("params", {}))
    sub_ctx = EventContext(ctx.group_id, ctx.qq_id, ctx.player, ctx.cur_map,
                           params=sub_params, name=ctx.name, hooks=ctx.hooks)
    fn = TEMPLATES.get(branch.get("template"))
    if fn:
        text = fn(sub_ctx)
        return text or ""
    return ""


@register("stamina_cost")
def tpl_stamina_cost(ctx):
    """v97.4 扣体力（浮桥落水等）。params: cost/header
    体力下限 0，上限 100 + lv*2（与 base.py _stamina_max 一致）。"""
    db = ctx._db()
    cost = ctx.param("cost", 5)
    max_st = 100 + ctx.lv * 2
    cur = int(ctx.player.get("stamina") or 0)
    new = max(0, cur - cost)
    db.update_player(ctx.group_id, ctx.qq_id, stamina=new)
    header = ctx.param("header", "⚡ 体力 -{cost}（当前 ⚡ {stamina}/{max}）")
    return (header.replace("{name}", ctx.name)
                  .replace("{cost}", str(cost))
                  .replace("{stamina}", str(new))
                  .replace("{max}", str(max_st)))


def execute_event_template(template_name, ctx):
    """执行模板；未注册返回 None（调用方兜底）。"""
    fn = TEMPLATES.get(template_name)
    if not fn:
        return None
    return fn(ctx)
