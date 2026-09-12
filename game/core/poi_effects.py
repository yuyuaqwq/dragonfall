# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - poi_effects.py（v125.2：POI 效果注册表）

消灭 commands/combat.py 里 _handle_poi（9 分支 if-chain）/ _handle_inst_poi
（5 分支）的硬编码：世界 POI 按 effect 键、副本内联 POI 按 inst:<type> 键
统一查 POI_EFFECTS 注册表；未知键返回 None，由命令层显式告警（不再静默
fallback 吞掉数据拼写错误）。

设计（仿 core/event_templates.py）：
- POI_EFFECTS: {效果名: 函数}，函数签名 fn(ctx) -> str（返回展示文本）
- ctx 为 PoiContext（group_id/qq_id/player/cur_map/poi_id/poi/st/hooks）
- 副本结算所需命令层能力（_mark_poi_used/_player）经 ctx.hooks 注入
- 机制子键（open_secret/skip_elite/skip_wave/unlock）与石碑子键
  （unlock/avoid_trap/boss_buff）收敛为子分发表 _MECHANISM_ACTIONS/
  _RUNE_STONE_ACTIONS（{子键: (动作函数, 播报文案)} 数据声明）
- 模板函数内延迟导入 db/content/data（遵循 core 聚合链规则，防循环导入）

扩展方式：
- 世界 POI：data/pois.py 加 effect 键 + 本模块 register 一个 handler
- 副本 POI：instance_stage_maps.py 加 type + 本模块 register inst:<type>
"""
import json
import random
import time
import uuid
from ..log_setup import LOG

_logger = LOG

POI_EFFECTS = {}


def register(name):
    """POI 效果注册装饰器。"""
    def deco(fn):
        POI_EFFECTS[name] = fn
        return fn
    return deco


class PoiContext:
    """POI 效果执行上下文（世界/副本 POI 共用）。"""

    def __init__(self, group_id, qq_id, player, cur_map, poi_id, poi,
                 st=None, hooks=None):
        self.group_id = group_id
        self.qq_id = qq_id
        self._focus = player    # 世界 POI：DB 玩家 dict（快照）；副本 POI：队长玩家 dict
        self.cur_map = cur_map  # 世界 POI：地图 dict；副本 POI：stage dict
        self.poi_id = poi_id
        self.poi = poi
        self.st = st            # 副本 POI：副本战斗状态（stage_idx/players/alive/members）
        self.hooks = hooks or {}

    # ---- 便捷访问 ----
    @property
    def icon(self):
        return self.poi.get("icon", "🌿")

    @property
    def pname(self):
        return self.poi.get("name", "探索点")

    @property
    def loc(self):
        """世界 POI 展示地名：地图名·子区域名（无子区域则仅地图名）。"""
        cur_map = self.cur_map or {}
        name = cur_map.get("name", "此地")
        sub_name = ""
        cur_sa_id = (self._focus or {}).get("cur_subarea") or ""
        for _sa in (cur_map.get("subareas") or []):
            if _sa["id"] == cur_sa_id:
                sub_name = _sa.get("name", "")
                break
        return f"{name}·{sub_name}" if sub_name else name

    def _db(self):
        from .. import db
        return db

    def _C(self):
        from .. import content as C
        return C

    # ---- 副本 POI 辅助 ----
    @property
    def sidx(self):
        return (self.st or {}).get("stage_idx", 0)

    def mark_used(self, poi_id=None):
        """标记副本 POI 已使用（命令层 _mark_poi_used 经 hooks 注入）。"""
        fn = self.hooks.get("mark_used")
        if fn:
            fn(self.st, self.sidx, poi_id or self.poi_id)

    def db_player(self):
        """读 DB 最新玩家（命令层 _player 经 hooks 注入，副本 chest 发金币用）。"""
        fn = self.hooks.get("player")
        if fn:
            return fn(self.group_id, self.qq_id)
        return None


# ================= 世界 POI（effect 键） =================

@register("recover")
def poi_recover(ctx):
    """篝火：恢复 30% 生命/魔力 + 随机烹饪食材。"""
    db = ctx._db()
    C = ctx._C()
    player = ctx._focus
    hp_gain = int(player["max_hp"] * 0.30)
    mp_gain = int(player["max_mp"] * 0.30)
    db.update_player(ctx.group_id, ctx.qq_id,
                     hp=min(player["max_hp"], player["hp"] + hp_gain),
                     mp=min(player["max_mp"], player["mp"] + mp_gain))
    # v101.4：篝火食材池数据化 → data/poi_pools.py CAMPFIRE_FOOD_POOL
    fd = random.choice(C.CAMPFIRE_FOOD_POOL)
    mid = C.resolve("materials", fd)
    got = ""
    if mid in C.MATERIALS:
        db.add_item(ctx.group_id, ctx.qq_id, mid,
                    {"name": C.display("materials", mid), "type": "材料",
                     "stackable": True, "price": C.MATERIALS[mid]["price"]})
        got = C.display("materials", mid)
    return (f"{ctx.icon} 【{ctx.pname}】你在{ctx.loc}的篝火旁坐下烤火。\n"
            f"❤️ 恢复 {hp_gain} 生命！💙 恢复 {mp_gain} 魔力！\n"
            f"🍖 篝火上还烤着一份{got}，顺手带走了。")


@register("buff")
def poi_buff(ctx):
    """神龛/祭坛：随机 buff（攻击/防御/速度 +10% 持续 5 次战斗）。"""
    db = ctx._db()
    buffs = [("攻击", "atk"), ("防御", "def"), ("速度", "spd")]
    bname, bkey = random.choice(buffs)
    # v104 M23 修复只写不读：battle.py 战斗开始时读取（玩家级键 poi_buff_{qq_id}——
    # battle 无 group_id 上下文，与 echo_bless bless_{qq_id} 同款全局键），
    # 应用 mult 并递减 left，用完删除 key
    db.set_event_state(f"poi_buff_{ctx.qq_id}",
                       json.dumps({"stat": bkey, "mult": 1.10, "left": 5, "name": bname},
                                  ensure_ascii=False))
    return (f"{ctx.icon} 【{ctx.pname}】你向{ctx.loc}的神龛虔诚祈愿，石像仿佛亮了一瞬。\n"
            f"✨ 获得祝福：{bname}+10%(持续 5 次战斗)！")


@register("merchant")
def poi_merchant(ctx):
    """v115 行商营地：随机金币（图等级×5~×10）或一张图纸（简化版，不做强卖流程）。"""
    db = ctx._db()
    C = ctx._C()
    player = ctx._focus
    map_lv = (ctx.cur_map or {}).get("lv", 1)
    if random.random() < 0.5:
        gold = random.randint(map_lv * 5, map_lv * 10)
        db.update_player(ctx.group_id, ctx.qq_id, gold=player["gold"] + gold)
        return (f"{ctx.icon} 【{ctx.pname}】行商在你的{ctx.loc}支起货摊，见你面善，低价收走了一批旧货。\n"
                f"💰 获得 {gold} 金币！(图级 Lv.{map_lv})")
    bp = C.roll_blueprint(max(1, player["level"]))
    _learned = player.get("learned_blueprints") or []
    if bp.get("blueprint_for") in _learned:
        _bpq = bp.get("quality", "white")
        _pages = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}.get(_bpq, 1)
        db.add_item(ctx.group_id, ctx.qq_id, "mat_tu_zhi_can_ye", {
            "name": "图纸残页", "type": "材料", "stackable": True, "price": 10}, count=_pages)
        return (f"{ctx.icon} 【{ctx.pname}】行商神秘地掏出一卷图纸：{bp['name']}！\n"
                f"📜 可惜你已经学会了，化作 {_pages} 张图纸残页（『出售 图纸残页』变现）")
    db.add_item(ctx.group_id, ctx.qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
    return (f"{ctx.icon} 【{ctx.pname}】行商神秘地掏出一卷图纸：{bp['name']}！\n"
            f"📜 他称这是从远方古墓里『顺』来的，你赶紧收好。")


@register("herb")
def poi_herb(ctx):
    """草药丛/鸟巢：1-2 份炼金材料。"""
    db = ctx._db()
    C = ctx._C()
    got = []
    for _ in range(random.randint(1, 2)):
        h = random.choice(C.HERB_POOL)  # v101.4：草药丛材料池数据化 → data/poi_pools.py HERB_POOL
        mid = C.resolve("materials", h)
        if mid in C.MATERIALS:
            db.add_item(ctx.group_id, ctx.qq_id, mid,
                        {"name": C.display("materials", mid), "type": "材料",
                         "stackable": True, "price": C.MATERIALS[mid]["price"]})
            got.append(C.display("materials", mid))
    return (f"{ctx.icon} 【{ctx.pname}】你在{ctx.loc}的草丛里仔细翻找，采到了一些好材料。\n"
            f"🎒 获得：{'、'.join(got)}！")


@register("loot")
def poi_loot(ctx):
    """可疑包裹/龙骸/沉船：金币 / 图纸 / 陷阱（扣血）。"""
    db = ctx._db()
    C = ctx._C()
    player = ctx._focus
    r = random.random()
    if r < 0.6:
        gold = random.randint(20, 80) + player["level"] * 3
        db.update_player(ctx.group_id, ctx.qq_id, gold=player["gold"] + gold)
        return (f"{ctx.icon} 【{ctx.pname}】你打开{ctx.loc}路边的可疑包裹——里面是金币！\n"
                f"💰 获得 {gold} 金币！")
    if r < 0.85:
        bp = C.roll_blueprint(max(1, player["level"]))
        # v101.25 #293：探索掉落已学图纸不再重复入包——与战斗掉落同款折算
        _learned = player.get("learned_blueprints") or []
        if bp.get("blueprint_for") in _learned:
            _bpq = bp.get("quality", "white")
            _pages = {"white": 1, "green": 1, "blue": 2, "purple": 4, "orange": 6}.get(_bpq, 1)
            db.add_item(ctx.group_id, ctx.qq_id, "mat_tu_zhi_can_ye", {
                "name": "图纸残页", "type": "材料", "stackable": True, "price": 10}, count=_pages)
            return (f"{ctx.icon} 【{ctx.pname}】包裹里卷着一张泛黄的图纸……{bp['name']}！\n"
                    f"📜 这张图纸你已经学会了，化作 {_pages} 张图纸残页（『出售 图纸残页』变现）")
        db.add_item(ctx.group_id, ctx.qq_id, f"eq_{uuid.uuid4().hex[:8]}", bp)
        return (f"{ctx.icon} 【{ctx.pname}】包裹里卷着一张泛黄的图纸：{bp['name']}！\n"
                f"📜 看来是某位锻造师遗失的手稿。")
    dmg = int(player["max_hp"] * 0.10) + 5
    new_hp = max(1, player["hp"] - dmg)
    db.update_player(ctx.group_id, ctx.qq_id, hp=new_hp)
    # #256: 陷阱触发文案带先兆（包裹缝隙的寒光）——此前无任何提示直接扣血
    return (f"💥 【{ctx.pname}】包裹的缝隙里隐约闪过一道金属寒光——你还没来得及缩手，一只发条咬人夹弹了出来！\n"
            f"你被夹了一下，损失 {dmg} 生命(当前 ❤️ {new_hp}/{player['max_hp']})")


@register("rune")
def poi_rune(ctx):
    """符文石：图鉴/隐藏线索。"""
    db = ctx._db()
    from ..data.pois import RUNE_POOL
    txt = random.choice(RUNE_POOL)
    db.set_talk_flag(ctx.group_id, ctx.qq_id, "poi_rune_read", "read_rune")
    return (f"{ctx.icon} 【{ctx.pname}】你伸手轻触{ctx.loc}的符文石，碑面泛起幽光。\n"
            f"📖 {txt}")


@register("fish")
def poi_fish(ctx):
    """鱼群聚集：免费垂钓次数（v104 M23 消费契约——垂钓命令读取方：
    key poi_fish_{gid}_{qid}，value {"ts": float, "window": 1800}，
    ts 在 1800s 窗口内 → 免冷却/免体力垂钓一次并删除该 key）。"""
    db = ctx._db()
    db.set_event_state(f"poi_fish_{ctx.group_id}_{ctx.qq_id}",
                       json.dumps({"ts": time.time(), "window": 1800}))
    return (f"{ctx.icon} 【{ctx.pname}】水面泛起细密的涟漪，鱼群正聚在{ctx.loc}的水面下！\n"
            f"🎣 你赶紧甩杆——『垂钓』吧，这次垂钓不消耗体力(30 分钟内有效)！")


@register("note")
def poi_note(ctx):
    """神秘字条：隐藏线索；traveler_grave 特例（见闻 flag，区分首祭/再经）。"""
    db = ctx._db()
    # v115 旅者之墓：见闻 flag（grave_<map>_<qid>）
    if ctx.poi_id == "traveler_grave":
        _gkey = f"grave_{(ctx.cur_map or {}).get('id', '')}_{ctx.qq_id}"
        if not db.get_event_state(_gkey):
            db.set_event_state(_gkey, "1")
            return (f"{ctx.icon} 【{ctx.pname}】你在{ctx.loc}见到一座无名的旅者之墓，苔痕斑驳的碑上刻着几行字。\n"
                    f"🪦 \"{ctx._focus['name']}，愿你的旅途有人记得。\"\n"
                    f"🕯️ 你郑重祭拜，于墓前放下一朵野花。")
        return (f"{ctx.icon} 【{ctx.pname}】你再次路过{ctx.loc}的旅者之墓，碑前的野花还开着。\n"
                f"🪦 你默默驻足片刻，为这位先行的旅人献上沉默的敬意。")
    from ..data.pois import NOTE_POOL
    txt = random.choice(NOTE_POOL)
    db.set_talk_flag(ctx.group_id, ctx.qq_id, "poi_note_found", "found_note")
    return (f"{ctx.icon} 【{ctx.pname}】你摘下{ctx.loc}树干上的字条，墨迹已有些褪色。\n"
            f"📜 {txt}")


@register("sight")
def poi_sight(ctx):
    """v87.9 风景 POI：纯氛围观景（无数值收益）。"""
    from ..data.pois import SIGHT_POOL
    txt = random.choice(SIGHT_POOL)
    return (f"{ctx.icon} 【{ctx.pname}】你停住脚步，抬头望向{ctx.loc}的风景。\n"
            f"🌄 {txt}")


# ================= 副本内联 POI（inst:<type> 键） =================

def _need_block(ctx):
    """副本 POI 前置条件（need）：未满足返回锁定文案，否则 None。"""
    need = ctx.poi.get("need") or {}
    if need:
        unlocks = (ctx.st or {}).get("poi_unlocks", {})
        if need.get("poi_read") and not unlocks.get(need["poi_read"]):
            return f"🔒 {ctx.pname}纹丝不动——需要先找到某种启示/线索。"
        if need.get("unlock") and not unlocks.get(need["unlock"]):
            return f"🔒 {ctx.pname}还没准备好——似乎缺少某样东西。"
    return None


def _act_flag(key):
    """子键动作工厂：置位 st[key] = True。"""
    def act(st, eff):
        st[key] = True
    return act


def _act_unlock(st, eff):
    """子键动作：poi_unlocks[eff.unlock] = True。"""
    st.setdefault("poi_unlocks", {})[eff["unlock"]] = True


def _act_avoid_trap(st, eff):
    """子键动作：poi_unlocks[avoid_<id>] = True。"""
    st.setdefault("poi_unlocks", {})[f"avoid_{eff['avoid_trap']}"] = True


# 机关 effect 子键分发表（数据声明）：{子键: (动作函数, 播报文案)}
_MECHANISM_ACTIONS = {
    "open_secret": (_act_flag("stage_secret_found"), "🔓 隐藏房间出现了！『副本地图』查看详情。"),
    "skip_elite": (_act_flag("skip_elite_next"), "🧭 机关打通了一条捷径——下一层的精英被绕开了！"),
    "skip_wave": (_act_flag("skip_wave_next"), "🧭 援兵被引开了一部分——下一层的敌人减少了！"),
    "unlock": (_act_unlock, "✨ 机关启动，某种封锁被解除了！"),
}

# 石碑 effect 子键分发表（数据声明）：{子键: (动作函数, 播报文案)}
_RUNE_STONE_ACTIONS = {
    "unlock": (_act_unlock, "✨ 碑文的内容似乎触发了什么……(某个机关被解锁了！)"),
    "avoid_trap": (_act_avoid_trap, "✨ 你记住了避开陷阱的路线。"),
    "boss_buff": (_act_flag("boss_buff_next"), "✨ 风神的祝福涌入体内——Boss 战前将获得速度加持！"),
}


@register("inst:chest")
@register("inst:supply")
@register("inst:corpse")
def inst_loot(ctx):
    """宝箱 / 补给 / 遗骸：给 loot（金币 + 材料；v168 起约 12% 额外翻出白/绿/蓝低品质装备）。"""
    db = ctx._db()
    C = ctx._C()
    block = _need_block(ctx)
    if block:
        return block
    logs = []
    loot = ctx.poi.get("loot") or {}
    gold = loot.get("gold", 0)
    mats = loot.get("materials") or []
    p = ctx.db_player()
    if gold > 0 and p:
        db.update_player(ctx.group_id, ctx.qq_id, gold=p["gold"] + gold)
        logs.append(f"💰 你从{ctx.pname}里摸出了 {gold} 金币！")
    for mn in mats:
        mid = C.resolve("materials", mn)
        if mid in C.MATERIALS:
            mname = C.display("materials", mid)
            db.add_item(ctx.group_id, ctx.qq_id, mid, {
                "name": mname, "type": "材料", "stackable": True,
                "price": C.MATERIALS[mid]["price"],
            })
            logs.append(f"🎒 拾取：{mname}")
    # v168 副本宝箱低品质装备档（鱼鱼拍板：非 Boss 房宝箱也开得出装备，不再只有图纸）：
    # 副本房间内宝箱/补给/遗骸约 12% 概率额外翻出一件装备——先 roll 品质
    # （白 40% / 绿 35% / 蓝 25%，仅低品质三档），再按玩家等级就近随机部位生成
    # （lv = 玩家等级 ±3，clamp 到 [1, ∞)，贴合当前等级养成；只吃 1 次 random，
    # 不影响 inst_loot 其余随机序列）。命中不额外占副本 stage 事件，仍只 mark_used 一次。
    if random.random() < 0.12:
        _q_roll = random.random()
        if _q_roll < 0.40:
            _eq_q = "white"
        elif _q_roll < 0.75:
            _eq_q = "green"
        else:
            _eq_q = "blue"
        _slot = random.choice(["weapon", "helm", "armor", "legs", "boots", "ring", "necklace"])
        _lv = max(1, (ctx._focus or {}).get("level", 1) + random.randint(-3, 3))
        eq = C.generate_equip(_slot, _lv, _eq_q)
        db.add_item(ctx.group_id, ctx.qq_id, f"eq_{uuid.uuid4().hex[:8]}", eq)
        # 白 🎒 / 绿 🟢 / 蓝 🔵：品质色块 + 装备名（与 C.QUALITY 档位色一致）
        _emoji = {"white": "🎒", "green": "🟢", "blue": "🔵"}.get(eq.get("quality", "white"), "🎒")
        logs.append(f"{_emoji} 你从{ctx.pname}里翻出一件装备：【{eq['name']}】！")
    ctx.mark_used()
    head = f"💀 你蹲下搜刮{ctx.pname}……" if ctx.poi.get("type") == "corpse" else f"📦 {ctx.pname}："
    return "\n".join([head] + logs)


@register("inst:campfire")
def inst_campfire(ctx):
    """副本篝火：全队回血（heal_pct 消费 POI effect 配置，缺省 0.2）。"""
    block = _need_block(ctx)
    if block:
        return block
    logs = []
    st = ctx.st
    for m in st["members"]:
        if not st["alive"].get(str(m), True):
            continue
        snap = st["players"].get(str(m), {})
        if snap.get("hp") is not None:
            # R3 P3-3：heal_pct 消费 POI effect 配置（instance_stage_maps.py
            # 篝火 heal_pct: 0.2 此前是死配置，硬编码 0.2 未来调参会脱钩）
            _pct = (ctx.poi.get("effect") or {}).get("heal_pct", 0.2)
            heal = max(1, int(snap.get("max_hp", snap["hp"]) * _pct))
            snap["hp"] = min(snap.get("max_hp", snap["hp"]), snap["hp"] + heal)
            logs.append(f"🔥 {snap.get('name', m)} 在{ctx.pname}旁烤火，恢复 {heal} 点生命！")
    ctx.mark_used()
    return "\n".join(logs)


@register("inst:rune_stone")
def inst_rune_stone(ctx):
    """副本石碑：读 lore（可反复读，不标 used）；effect 子键解锁/避陷阱/Boss 祝福。"""
    logs = []
    st = ctx.st
    lore = ctx.poi.get("lore", "碑文模糊不清，似乎被岁月磨平了。")
    logs.append(f"🗿 你阅读{ctx.pname}：")
    logs.append(f"  “{lore}”")
    eff = ctx.poi.get("effect") or {}
    # R3 P1-1：读取石碑即记录自身 poi id——need.poi_read 机关（旧王陵王座机关
    # /龙之墓暗门机关）依赖此标记解锁；此前只写 effect.unlock，无 unlock 的
    # 石碑（如墓志铭石碑）永远无法解锁 poi_read 机关
    st.setdefault("poi_unlocks", {})[ctx.poi_id] = True
    for key, (act, line) in _RUNE_STONE_ACTIONS.items():
        if eff.get(key):
            act(st, eff)
            logs.append(line)
    return "\n".join(logs)


@register("inst:mechanism")
def inst_mechanism(ctx):
    """副本机关：desc + effect 子键（开隐藏房/跳精英/减波次/解锁）。"""
    block = _need_block(ctx)
    if block:
        return block
    logs = []
    st = ctx.st
    desc = ctx.poi.get("desc", f"你扳动了{ctx.pname}。")
    logs.append(f"⚙️ {desc}")
    eff = ctx.poi.get("effect") or {}
    for key, (act, line) in _MECHANISM_ACTIONS.items():
        if eff.get(key):
            act(st, eff)
            logs.append(line)
    ctx.mark_used()
    return "\n".join(logs)


@register("inst:trap")
def inst_trap(ctx):
    """副本陷阱：可拆解（有石碑线索 avoid_<id>）或全队受伤 10% 最大生命。"""
    block = _need_block(ctx)
    if block:
        return block
    st = ctx.st
    if st.get("poi_unlocks", {}).get(f"avoid_{ctx.poi_id}"):
        ctx.mark_used()
        return f"⚠️ 你记得石碑上的提示，小心地拆除了{ctx.pname}！"
    logs = [f"⚠️ 你触发了{ctx.pname}！全队受到 10% 最大生命的伤害！"]
    for m in st["members"]:
        if not st["alive"].get(str(m), True):
            continue
        snap = st["players"].get(str(m), {})
        if snap.get("hp") is not None:
            dmg = max(1, int(snap.get("max_hp", snap["hp"]) * 0.1))
            snap["hp"] = max(0, snap["hp"] - dmg)
            if snap["hp"] <= 0:
                st["alive"][str(m)] = False
                logs.append(f"💀 {snap.get('name', m)} 被陷阱击倒了！")
            else:
                logs.append(f"❤️ {snap.get('name', m)} 剩余 {snap['hp']}/{snap['max_hp']}")
    ctx.mark_used()
    return "\n".join(logs)


def execute_poi(effect_name, ctx):
    """执行 POI 效果；未注册返回 None（调用方显式告警，不再静默 fallback）。"""
    fn = POI_EFFECTS.get(effect_name)
    if not fn:
        return None
    return fn(ctx)
