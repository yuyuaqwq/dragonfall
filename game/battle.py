# -*- coding: utf-8 -*-
"""v9 统一战斗引擎 —— 遇怪 / 世界BOSS / PVP 共用

核心：Battle 状态机
  - 持久化：db.save_battle 存 state dict（battle_state.state 字段）
  - buff 系统：玩家/敌方各自 buff 表 {effect: 剩余回合}，每回合递减
  - 技能特效全部落地：旧 engine.player_attack 的 extra（破甲降防/寒冰减速/毒箭中毒/
    标记猎杀/处决残血/吸血）此前被 main.py 丢弃，这里真正写入战斗状态并生效
  - 敌方增益也落地：monster_turn 的 mextra（mon_atk_up/mon_def_up）此前被丢弃

btype:
  - monster   : 探索遇怪（可逃跑）
  - worldboss : 世界 Boss（v9.1 启用，不可逃跑）
  - pvp       : 玩家对战（v9.2 启用，不可逃跑，enemy 为对方玩家快照）
"""
import random
import time

from . import content as C
from . import engine as E
from .data.battle_config import (  # v125.2 B1 + v130.2 并入：战斗主路径数值/白名单数据表 + v130 引擎新机制表
    MECH_STACK_BONUS, MECH_STACK_WHITELIST, DOT_DEFS,
    DOT_BLEED_DOUBLE_HP_PCT, DOT_ADAPT_DECAY_STEP, DOT_RESIST_CAP,
    BOSS_ATTACK_MULTS, CONTROL_MECHS, SKILL_CC_WHITELIST,
    MECH_FULL_HP_CRIT, MECH_FROZEN_MULT, MECH_COMBO_STACKS,
    MECH_PROC_GROUPS, MECH_STAT_PASSIVES,
    ELEMENT_MARKS_MAX, REACTION_TABLE, ELEMENT_MARK_GAIN_PER_HIT,
    ELEMENT_SAME_CAST_EXTRA_CHARGE, RAGE_GAIN_HP_SCALE, ENERGY_HIGH,
    COMBO_CFG, ASSASSIN_ON_CRIT_GAIN, ASSASSIN_ON_TAKE_HIT_PENALTY,
    MOMENTUM_CFG, SHADOW_STEP_CFG, ECHO_CFG, BARD_BRANCHES,
    BRANCH_RESOURCE_OVERRIDE, HUNT_MARK_ON_LAND_HIT, HUNT_MARK_CRIT_EXTRA,
)
from .core.battle_conds import PASSIVE_COND_CHECKS, PASSIVE_COND_STAT_KEYS, passive_cond_ok  # v1.x 被动条件注册表

# v95.4 普攻文案按职业区分（玩家反馈：全职业"你挥剑攻击"违和）
# v112 数据驱动收敛（D5）：文案下沉 CLASSES[职业]["attack_text"]，逻辑层只读数据


# v105 P3(M01)：种族残血攻倍率常量——battle 结算与 race_talent_display 展示共用，
# 调数值只改这里（此前两处各自硬编码 1.20/0.90，调值会文案失配）
RACE_BERSERK_MULT = 1.20   # 无畏：HP 低于 berserk_hp 阈值时攻击 ×1.20（展示文案 +20%）
RACE_TIMID_MULT = 0.90     # 怯战：HP 低于 timid_hp 阈值时攻击 ×0.90（展示文案 -10%）


def _basic_attack_verb(player: dict) -> str:
    """普攻动作文案（按职业；未知职业 fallback 挥剑攻击）"""
    return C.CLASSES.get(player.get("class_name", ""), {}).get("attack_text", "挥剑攻击")


# 增益倍率映射：effect -> (修正属性, 倍率/加成)
BUFF_MULT = {
    "atk_up":         ("atk", 1.30),
    "atk_up_strong":  ("atk", 1.75),
    "echo_bless":     ("atk", 1.05),   # v97.4 回音洞穴祝福：本场攻击 +5%（一次性，探索事件写入）
    "matk_up":        ("matk", 1.50),   # #244a：与技能描述 matk+50% 对齐（原 1.35 与 desc 不符）
    "matk_up_strong": ("matk", 1.80),
    "matk_up_pot":    ("matk", 1.30),   # 9.3 鲛人之泪：本回合魔攻 +30%
    "def_up":         ("def", 1.45),
    "spd_up":         ("spd", 1.40),
    "crit_up":        ("crit", 0.20),      # 暴击率 +20%
    # v101.28f 药水强度分档（名字不同效果不同的真实落地：战吼/龙力 +40%、蛮力 +20%、风灵 +20%、致命 +30%、锐目 +15%）
    "atk_up_big":     ("atk", 1.40),
    "atk_up_small":   ("atk", 1.20),
    "spd_up_small":   ("spd", 1.20),
    "crit_up_small":  ("crit", 0.15),
    "crit_up_big":    ("crit", 0.30),
    # v101.28b 食物增益（战斗料理线：数值约为药水 1/3，价格低+带战斗外恢复）
    "food_atk_up":    ("atk", 1.10),
    "food_def_up":    ("def", 1.15),
    "food_spd_up":    ("spd", 1.12),
    "food_crit_up":   ("crit", 0.08),
    "food_matk_up":   ("matk", 1.10),
    "food_spd_up_small": ("spd", 1.10),  # v105 M16 精灵果酱：战斗中本场速度+10%（策划 19:129）
    "mon_atk_up":     ("atk", 1.30),
    "mon_atk_up_strong": ("atk", 1.70),
    "mon_def_up":     ("def", 1.40),
    "mon_atk_down":   ("atk", 0.70),   # v51 挫志怒吼：敌方攻击 -30%
}
# v104 M02 P1-4：团队增益 effect=xx_all → 施放者自身有效 buff 键（与 instance.py buff_effects 同口径）
TEAM_BUFF_KEYS = {
    "def_all": "def_up", "atk_all": "atk_up",
    "matk_all": "matk_up_strong", "crit_all": "crit_up", "spd_all": "spd_up",
}
# v113.1：团队技能 reduce_all 真·百分比减伤（此前被 TEAM_BUFF_KEYS 误映射为 def_up 防御提升，
# 玩家看到"减伤 x%"实际是防御+45%）。reduce_all 是团队减伤 effect，不走 TEAM_BUFF_KEYS，
# 在 _skill_buff 单独处理成 p_buffs["reduce_all"]=减伤百分比。
# v1.x：数值下沉 skills.py 技能条目 reduce_all 字段（原 REDUCE_ALL_PCT 中文名硬编码表已删），
# 消费端改读 info.get("reduce_all", 0)。副本广播侧（instance.py team_effects["reduce_all"]）
# 保持既有口径，本文只修 battle.py 单机侧。
# 负面效果
DEF_DOWN_MULT = 0.5   # 破甲斩：敌方防御减半
SPD_DOWN_MULT = 0.5   # 寒冰箭：敌方速度减半（暂不影响结算，留接口）
# DOT 重构常量集中（契约 §2.4）：每层每回合 % 敌方最大生命
# 历史常量，dot 已改混合公式（_tick_dots 用 _atk_parts/_matk_parts/_hp_parts，不再读这些）；保留定义兼容外部引用
POISON_PCT = 0.05     # 毒：每层每回合 5% 敌方最大生命（保留旧名兼容外部引用）
BURN_PCT = 0.03       # 灼烧：每层每回合 3% 敌方最大生命
BLEED_PCT = 0.05      # 流血：每回合 5% 敌方最大生命（词条 2~3 回合）
DEFEND_REDUCE = 0.5   # 防御：敌方伤害减半
BUFF_TURNS = 3        # 增益默认持续回合
DEBUFF_TURNS = 2      # 减益默认持续回合

# v121 CTB 行动时间轴：全局行动消耗常量
BASE_DELAY = 100.0    # 行动消耗基数（待 Agent D 模拟标定）
SPD_CT_CAP = 80.0     # 参与 ct 计算的 spd 软上限（min(spd, cap)）

# v125.1 审计 P2-2：宠物技能类型注册表（数据驱动，替代 _pet_skill_turn 内 if/elif 链）
# handler 签名 fn(battle, player, pdef, pname, sname, line, logs) -> None（直接改 battle 状态 + 追加日志）
# 数值全部读 PET_POOL 条目 skill_value/skill_interval（data/pets.py），加新技能类型 = register 一个函数
PET_SKILL_EFFECTS = {}


def _pet_skill_register(stype):
    """宠物技能类型注册装饰器。"""
    def deco(fn):
        PET_SKILL_EFFECTS[stype] = fn
        return fn
    return deco


def _pet_skill_dmg(battle, player, pdef, pname, sname, line, logs, magic=False):
    """宠物物理/魔法攻击 × skill_value 伤害（atk_pct/matk_pct/lifesteal/pierce 共用计算）。"""
    st = battle._player_stats(player)
    est = battle._enemy_stats()
    if magic:
        dmg = E.calc_damage(int(st["matk"] * pdef["skill_value"]), est.get("mdef", 0))
    else:
        dmg = E.calc_damage(int(st["atk"] * pdef["skill_value"]), est.get("def", 0))
    battle._damage_enemy(dmg, logs)
    logs.append(f"🐾 {pname}的【{sname}】造成 {dmg} 点伤害！" + (f"「{line}」" if line else ""))
    return dmg


def _pet_skill_victory(battle, logs):
    """宠物击杀判定（与 _pet_skill_turn 原分支行为一致）。"""
    if battle._enemy_dead():
        battle.result = "victory"
        logs.append(f"🎉 你击败了【{battle.enemy.get('name', '敌人')}】！(宠物击杀)")


@_pet_skill_register("atk_pct")
def _psk_atk_pct(battle, player, pdef, pname, sname, line, logs):
    """撕咬/烈焰尾击/狮鹫俯冲：攻击力 × value 伤害。"""
    _pet_skill_dmg(battle, player, pdef, pname, sname, line, logs)
    _pet_skill_victory(battle, logs)


@_pet_skill_register("matk_pct")
def _psk_matk_pct(battle, player, pdef, pname, sname, line, logs):
    """霜刃/龙息：魔攻 × value 伤害。"""
    _pet_skill_dmg(battle, player, pdef, pname, sname, line, logs, magic=True)
    _pet_skill_victory(battle, logs)


@_pet_skill_register("lifesteal")
def _psk_lifesteal(battle, player, pdef, pname, sname, line, logs):
    """吸血撕咬：攻击 × value 伤害，并回复伤害 50% 生命（重伤减半）。"""
    dmg = _pet_skill_dmg(battle, player, pdef, pname, sname, line, logs)
    heal = max(1, int(dmg * 0.5))
    if battle.p_buffs.get("mortal_wound"):  # v1.3 重伤：宠物吸血减半
        heal = int(heal * 0.5)
    player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
    logs.append(f"🩸 {pname}汲取了 {heal} 点生命归还给你！")
    _pet_skill_victory(battle, logs)


@_pet_skill_register("pierce")
def _psk_pierce(battle, player, pdef, pname, sname, line, logs):
    """碎岩冲撞：攻击 × value 伤害，并破防（敌方防御减半 2 回合）。"""
    _pet_skill_dmg(battle, player, pdef, pname, sname, line, logs)
    battle.e_buffs["def_down"] = max(int(battle.e_buffs.get("def_down", 0) or 0), 2)
    logs.append(f"🛡️ {pname}的【{sname}】击碎了敌人的护甲！(防御减半 2 回合)")
    _pet_skill_victory(battle, logs)


@_pet_skill_register("heal_pct")
def _psk_heal_pct(battle, player, pdef, pname, sname, line, logs):
    """月光祝福/圣光羽翼/星辉治愈/月华低语：回复 max_hp × value 生命。"""
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = int(player.get("max_hp", player.get("hp", 1)) * pdef["skill_value"])
        player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
        logs.append(f"🐾 {pname}的【{sname}】为你回复了 {heal} 点生命！" + (f"「{line}」" if line else ""))


@_pet_skill_register("buff_atk")
def _psk_buff_atk(battle, player, pdef, pname, sname, line, logs):
    """雷鸣鼓舞：攻击强化（数值实读 skill_value，_apply_buffs 用 _pet_buff_vals 覆盖常量）。"""
    battle.p_buffs["atk_up"] = max(int(battle.p_buffs.get("atk_up", 0) or 0), 2)
    _pbv = getattr(battle, "_pet_buff_vals", {})
    _pbv["atk"] = max(float(_pbv.get("atk", 0.0) or 0.0), float(pdef["skill_value"]))
    battle._pet_buff_vals = _pbv
    logs.append(f"🐾 {pname}的【{sname}】为你加持攻击强化！(攻击 +{int(pdef['skill_value'] * 100)}%，2 回合)" + (f"「{line}」" if line else ""))


@_pet_skill_register("crit_up")
def _psk_crit_up(battle, player, pdef, pname, sname, line, logs):
    """狩猎之眼/星羽疾风：暴击提升（数值实读 skill_value）。"""
    battle.p_buffs["crit_up"] = max(int(battle.p_buffs.get("crit_up", 0) or 0), 2)
    _pbv = getattr(battle, "_pet_buff_vals", {})
    _pbv["crit"] = max(float(_pbv.get("crit", 0.0) or 0.0), float(pdef["skill_value"]))
    battle._pet_buff_vals = _pbv
    logs.append(f"🐾 {pname}的【{sname}】为你加持暴击提升！(暴击 +{int(pdef['skill_value'] * 100)}%，2 回合)" + (f"「{line}」" if line else ""))


class Battle:
    def __init__(self, btype: str = "monster", enemy: dict | None = None, title_bonus: dict = None, player: dict | None = None, pet: dict | None = None, dmg_mult: float = 1.0, enemies: list | None = None, allies: list | None = None):
        self.btype = btype                 # monster | worldboss | pvp
        self.dmg_mult = dmg_mult           # v93 GM 世界 Boss 伤害倍率（gm_伤害 设置，仅 worldboss 生效）
        self.pet = pet or {}               # 24 章宠物：{pet_key,name,level,satiety}（战斗内宠物技能用）
        self.round = 0
        # v2 多对多阵列（§3.2）：enemies=敌方阵列每怪一个 dict；allies=我方阵列
        # （单机 = [player]；副本由命令层维护）。enemy 单怪兼容包装为单怪阵列。
        self._enemies_raw = enemy or {}    # 主目标 dict（单怪时整个敌方单位）
        if enemies is not None:
            self.enemies = [dict(u) for u in enemies]
            # v121 CTB：敌方单位 ct 缺省 -spd（快者先手）；随 enemies 阵列持久化
            for u in self.enemies:
                if "ct" not in u:
                    u["ct"] = -float(u.get("spd", 0) or 0)
            if not any(u.get("rank") for u in self.enemies):
                for i, u in enumerate(self.enemies):
                    u.setdefault("uid", f"e_{i}")
                    u.setdefault("rank", 1)
                    u.setdefault("reach", 1)
                    u.setdefault("buffs", {})
                    u.setdefault("stacks", {})
                    u.setdefault("defending", False)
                    u.setdefault("charging", None)
        else:
            # 单怪兼容包装（§3.2）
            self.enemies = [self._wrap_enemy_unit(self._enemies_raw, 0)]
        # v126.7 胜利结算引用：打死怪后 _remove_unit 会清空 enemies（单怪场景 b.enemy 变 {}），
        # 结算层（_handle_victory）需要原主怪的 exp/gold/lv/drops——构造时保存一份副本。
        self._origin_enemy = dict(self.enemies[0]) if self.enemies else {}
        self.allies: list = allies or []   # v122 我方阵列（治疗指定队友：副本传存活玩家快照引用）
        self.player = player or {}         # v105 攻击方属性读取（_monster_dodge_check 需要玩家精准）
        self.p_buffs: dict = {}            # 玩家增益 {effect: turns}
        self._reduce_all_left: int = 0     # v113.1 团队减伤 reduce_all 剩余回合（百分比存 p_buffs["reduce_all"]）
        self.poi_buff: dict | None = None  # v104 M23 神龛祝福：{stat,mult,name}，持久 5 次战斗，battle 开始时消费 1 次
        self.p_hot: dict = {}              # v101.28 食物持续恢复 {"heal": 比例, "mana": 比例, "turns": 剩余回合}
        self.p_food_effects: list = []     # v101.28e 食物效果（战斗中吃料理获得，本场有效；独立于装备词条体系）
        self.p_shields: dict = {}          # v101.28d 护盾 buff 化：来源 → {"value": 盾值, "turns": 剩余回合}，同源可叠厚，异源并存
        self.e_minions: list = []          # v101.28l #438 真召唤：敌方援军实体 [{name,hp,max_hp,atk,matk}]
        self.summons: list = []            # v107 召唤物：玩家侧独立实体 [{tid,name,icon,hp,max_hp,atk,def,dmg_type}]
        self.p_defending = False           # 玩家本回合是否防御
        self.charging: dict | None = None  # v2 玩家侧蓄力状态 {"skill","left","name"}（§6）
        self.result = None                 # None | victory | defeat | fled
        self.title_bonus = title_bonus or {}  # 副业大师称号属性加成
        self.team_effects: list = []         # v50 团队技能效果（副本全队广播用）
        self.mech_stacks: dict = {}          # v59 分支机制叠层（随战斗持久化，不再挂 player 避免每回合丢失）
        # v2.0 核心资源（12 章 1.2：怒气/元素亲和/精力/信仰/连击点/气）
        # 随战斗序列化，同 mech_stacks 机制；阶段五引擎先挂载，技能数据落地后消费
        self.resources: dict = {}          # v2.0 核心资源（怒气/元素亲和/精力/信仰/连击点/气），随战斗序列化
        self.cooldown: dict = {}           # v2.0 技能冷却（技能名 → 剩余回合数），随战斗序列化；回合结束递减
        self.combo_seq: list = []          # v2.0 拳师连招序列（拳/踢/掌 tag 记录，满 3 触发三连）
        self._last_element = None           # v130.2 法师攻线·元素：上次施放元素（同系连发判定）
        self._tailwind_prev_energy = None   # v130.2d 疾风余韵：上回合结束时精力快照（跨回合态，随战斗序列化）
        self.p_eff: dict = {}              # v130.2 物品效果持久数据（resource_amp / mana_cost_down / buff_phys_next / phys_up / battle_start 预充标记），随战斗序列化
        if player:
            # v95.19: 战斗内属性统一用实时计算值——DB max_hp/max_mp 是注册/升级快照，换装备后过时，
            # 会导致战斗内血量上限/治疗 clamp/护盾与『角色』面板不一致（装备 HP 加成战斗内不生效）
            try:
                _st = self._player_stats(player)
                player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
                player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
            except Exception:
                pass
            # v97.4 回音洞穴祝福：探索事件写入 event_state bless_{qid}（玩家级，players 表全局无 group_id），本场攻击 +5%，一次性
            if player.get("qq_id") and not self.p_buffs.get("echo_bless"):
                try:
                    import json as _json
                    from . import db as _db
                    _key = f"bless_{player['qq_id']}"
                    _raw = _db.get_event_state(_key)
                    if _raw:
                        self.p_buffs["echo_bless"] = 1
                        _db.set_event_state(_key, "")
                except Exception:
                    pass
            # v104 M23 神龛祝福（探索 POI 写入，玩家级键 poi_buff_{qq_id}——battle 无 group_id
            # 上下文，与 echo_bless bless_{qq_id} 同款全局键）：战斗开始时读取 → 本场对应属性
            # ×1.10，left-1；用完删除 key（flee 也算消耗 1 次，按文案「持续 5 次战斗」计）
            if player.get("qq_id") and not getattr(self, "poi_buff", None):
                try:
                    import json as _json
                    from . import db as _db
                    _key = f"poi_buff_{player['qq_id']}"
                    _raw = _db.get_event_state(_key)
                    if _raw:
                        _pb = _json.loads(_raw)
                        if isinstance(_pb, dict) and _pb.get("stat") in ("atk", "def", "spd") \
                                and int(_pb.get("left", 0) or 0) > 0:
                            self.poi_buff = {"stat": _pb["stat"],
                                             "mult": float(_pb.get("mult", 1.10)),
                                             "name": _pb.get("name", _pb["stat"])}
                            _pb["left"] = int(_pb["left"]) - 1
                            if _pb["left"] <= 0:
                                _db.delete_event_state(_key)
                            else:
                                _db.set_event_state(_key, _json.dumps(_pb, ensure_ascii=False))
                except Exception:
                    pass
            self._init_resources(player)
        # 阶段八：战斗开始词条——护盾（10% 生命护盾/3 回合，数值读 affixes 数据 shield_hp_pct/turns；
        # v101.28d 盾 buff 化）
        if player and "shield" in self._equip_affix_ids(player):
            _se = (C.AFFIXES.get("shield") or {}).get("effect") or {}
            self._add_shield("affix_shield",
                             int(player.get("max_hp", 100) * float(_se.get("shield_hp_pct", 0.10))),
                             int(_se.get("turns", 3)))
        # v130.2c 战斗开始资源词条：起手之势（拳师开局 +1 气；统一读取器 battle_start 事件）
        if player:
            self._affix_res_proc(player, "battle_start", [])
        # v130.2c 套装战斗开始效果：夜幕合契·影纱（+1 连击点）/ 蓄势涌动（开局 2 气）
        if player:
            _keys0 = self._branch_keys(player)
            _cp_eff = self._set_eff(player, "battle_start_cp", 2)
            if _cp_eff and "cp" in _keys0:
                self._res_gain(player, "cp", int(_cp_eff.get("value", 1) or 1))
            _chi_eff = self._set_eff(player, "battle_start_res", 2, res="chi")
            if _chi_eff and "chi" in _keys0:
                self._res_gain(player, "chi", int(_chi_eff.get("value", 2) or 2))
        # v121 CTB 行动时间轴：玩家 ct（越小越先行动），开局 = -spd（快者先手）
        self.p_ct: float = 0.0
        try:
            if player:
                self.p_ct = -float(self._player_stats(player).get("spd", 0) or 0)
        except Exception:
            self.p_ct = -float(player.get("spd", 0) or 0) if player else 0.0
        self._player_hit: bool = False        # 本场玩家是否受过击（v2.1 条件：未受击增伤）
        self.first_attack_done: bool = False  # 阶段九：龙之吐息首击标记（每场首次攻击 +15%）
        self._death_pact_used: bool = False   # v107 死亡契约（暗影祭司）：每场 1 次标记
        self._set_immune_used: bool = False   # v130.2c 圣典·日冕 4 件：满信仰免伤 每战 1 次标记
        # O116 受击伤害日志延迟输出：_enemy_turn 只计算伤害并暂存"造成 X 点伤害"文案，
        # 由 _damage_player 在闪避判定后决定是否输出（闪避时不再同时报伤害）
        self._pending_dmg_lines: list = []
        # v2 受击伤害来源（打断判定用）：最近一次对敌方造成伤害的来源名（默认玩家）
        self._last_hitter: str = "你"
        # DOT 重构（契约 §2.1）：持续减益结算闸门——单机每玩家行动结算一次（现状频率）；
        # 副本由 instance 层 set False；世界 Boss 由 combat 层 force=True 触发
        self._dot_pending: bool = True

    # ---------------- v2 阵列兼容代理（§3.2） ----------------
    @staticmethod
    def _wrap_enemy_unit(e: dict, idx: int) -> dict:
        """单怪敌方 dict → 阵列单位（原地补 v2 站位字段，保持引用以便外部读 hp 同步）。"""
        u = e or {}
        u.setdefault("uid", f"e_{idx}")
        u.setdefault("rank", 1)
        u.setdefault("reach", 1)
        u.setdefault("buffs", u.get("buffs") or {})
        u.setdefault("stacks", u.get("stacks") or {})
        u.setdefault("defending", False)
        u.setdefault("charging", None)
        u.setdefault("ct", -float(u.get("spd", 0) or 0))  # v121 CTB 缺省 -spd
        return u

    @property
    def enemy(self) -> dict:
        """兼容代理：主目标 = 最前排第一个存活单位（无存活返回 enemies[0]）。"""
        for u in self.enemies:
            if u.get("hp", 0) > 0:
                return u
        if self.enemies:
            return self.enemies[0]
        return {}

    @enemy.setter
    def enemy(self, val: dict):
        """兼容写入：单怪场景外部改写 b.enemy = {...} 时同步主目标（enemies[0]）。"""
        if not self.enemies:
            self.enemies.append(self._wrap_enemy_unit(val, 0))
        else:
            self.enemies[0] = self._wrap_enemy_unit(val, 0)

    @property
    def e_buffs(self) -> dict:
        """兼容代理：主目标单位级增益（可读写）。"""
        return self.enemy.setdefault("buffs", {})

    @e_buffs.setter
    def e_buffs(self, val: dict):
        self.enemy["buffs"] = val or {}

    @property
    def e_defending(self) -> bool:
        """兼容代理：主目标防御状态。"""
        return bool(self.enemy.get("defending", False))

    @e_defending.setter
    def e_defending(self, val: bool):
        self.enemy["defending"] = bool(val)

    @property
    def mech_stacks(self) -> dict:
        """玩家侧叠层保留原语义（battle 实例字段）；敌方叠层在 enemy["stacks"]。"""
        if not hasattr(self, "_mech_stacks"):
            self._mech_stacks = {}
        return self._mech_stacks

    @mech_stacks.setter
    def mech_stacks(self, val: dict):
        self._mech_stacks = val or {}

    # ---------------- 序列化 ----------------
    def to_state(self) -> dict:
        return {
            "type": self.btype,
            "round": self.round,
            # v2：敌方完整阵列（核心）；enemy 保留为兼容键（= 主目标引用）
            "enemy": self.enemy,
            "enemies": self.enemies,
            "charging": self.charging,
            "pet": self.pet,
            "p_buffs": self.p_buffs,
            # v113.1 团队减伤 reduce_all 剩余回合：percent 存 p_buffs、回合数独立计时，
            # 必须随存档持久化，否则恢复后 __init__=0 被下回合立即弹掉 reduce_all。
            "reduce_all_left": self._reduce_all_left,
            "poi_buff": getattr(self, "poi_buff", None),
            "p_hot": self.p_hot,
            "p_food_effects": self.p_food_effects,
            "p_shields": self.p_shields,
            # v101.28l 旧观兼容键保留（= 敌方阵列中 summon 型援军副本，命令层写回用）
            "e_minions": self.e_minions,
            "summons": self.summons,
            "e_buffs": self.e_buffs,
            "p_defending": self.p_defending,
            "e_defending": self.e_defending,
            "title_bonus": self.title_bonus,
            "mech_stacks": self.mech_stacks,
            "resources": self.resources,
            # v130.2 物品效果持久数据（resource_amp/mana_cost_down/buff_phys_next/phys_up/战前预充标记）
            "eff_data": getattr(self, "p_eff", {}),
            "cooldown": self.cooldown,
            "combo_seq": self.combo_seq,
            "p_ct": self.p_ct,
            "player_hit": self._player_hit,
            "first_attack_done": self.first_attack_done,
            "death_pact_used": getattr(self, "_death_pact_used", False),
            "set_immune_used": getattr(self, "_set_immune_used", False),
            # v104 M02 P2-9：断线恢复后 burst 机制（灼烧引爆/剑刃风暴/神恩护盾）与
            # 元素跃迁日志依赖 _last_player/_shifted_element，必须随战斗状态持久化
            "last_player": getattr(self, "_last_player", None),
            "shifted_element": getattr(self, "_shifted_element", None),
            # DOT 重构（契约 §2.1）：持续减益结算闸门状态随战斗序列化
            "dot_pending": getattr(self, "_dot_pending", True),
            "tailwind_prev_energy": getattr(self, "_tailwind_prev_energy", None),  # v130.2d 疾风余韵跨回合状态
        }

    @classmethod
    def from_state(cls, st: dict):
        # v2：有完整阵列用阵列；只有单怪 enemy → 包成单怪阵列（旧存档容错）
        enemies = st.get("enemies")
        if enemies:
            b = cls(st.get("type", "monster"), None, st.get("title_bonus") or {}, pet=st.get("pet") or {},
                    enemies=[dict(u) for u in enemies])
        else:
            b = cls(st.get("type", "monster"), st.get("enemy", {}) or {}, st.get("title_bonus") or {}, pet=st.get("pet") or {})
            # 旧存档：只有 e_buffs 时并入主单位 buffs（§3.2 容错）
            legacy = st.get("e_buffs") or {}
            if legacy:
                main = b.enemy
                merged = dict(legacy)
                merged.update(main.get("buffs") or {})
                main["buffs"] = merged
        b.round = st.get("round", 0)
        b.allies = st.get("allies") or []   # v122 治疗指定队友（副本传存活玩家快照引用）
        b.p_buffs = st.get("p_buffs", {}) or {}
        b._reduce_all_left = int(st.get("reduce_all_left", 0) or 0)  # v113.1 恢复减伤剩余回合
        b.poi_buff = st.get("poi_buff")
        b.p_hot = st.get("p_hot", {}) or {}
        b.p_food_effects = st.get("p_food_effects", []) or st.get("p_food_affixes", []) or []
        b.p_shields = st.get("p_shields", {}) or {}
        b.e_minions = st.get("e_minions", []) or []
        b.summons = st.get("summons", []) or []
        b.charging = st.get("charging")
        b.p_defending = st.get("p_defending", False)
        b.e_defending = st.get("e_defending", False)
        b.mech_stacks = st.get("mech_stacks", {}) or {}
        b.resources = st.get("resources", {}) or {}
        b.p_eff = st.get("eff_data", {}) or {}  # v130.2 物品效果持久数据
        b.cooldown = st.get("cooldown", {}) or {}
        b.combo_seq = st.get("combo_seq", []) or []
        b.team_effects = []
        # v121 CTB：玩家 ct 读取（老存档兜底 0）；敌方单位 ct 兜底 -spd
        b.p_ct = float(st.get("p_ct", getattr(b, "p_ct", 0.0)) or 0.0)
        for _u in b.enemies:
            if "ct" not in _u:
                _u["ct"] = -float(_u.get("spd", 0) or 0)
        b._player_hit = bool(st.get("player_hit", False))
        b.first_attack_done = bool(st.get("first_attack_done", False))
        b._death_pact_used = bool(st.get("death_pact_used", False))
        b._set_immune_used = bool(st.get("set_immune_used", False))
        # v104 M02 P2-9：恢复 _last_player/_shifted_element；_last_player 为空保持
        # 未设置（hasattr=False，避免 battle_mech 对 None 调 _player_stats 崩溃）
        _lp = st.get("last_player")
        if _lp:
            b._last_player = _lp
        b._shifted_element = st.get("shifted_element")
        # DOT 重构（契约 §2.1）：恢复持续减益结算闸门（老档案缺失默认 True=每玩家行动结算一次）
        b._dot_pending = bool(st.get("dot_pending", True))
        b._tailwind_prev_energy = st.get("tailwind_prev_energy")  # v130.2d 疾风余韵跨回合状态
        # DOT 重构（契约 §2.3）：老档案迁移——敌方持续减益迁为目标级 enemy["debuffs"]。
        # 旧档 mech_stacks 里的 poison/burn/mark（敌方减益）迁移为 debuffs 结构后清键；
        # 玩家侧键（dragon_mark/rage/shadow/chi 等）与 e_buffs 标记不受影响。
        if not b.enemy.get("debuffs"):
            _old_m = st.get("mech_stacks") or {}
            _new_deb = {}
            for _k in ("poison", "burn", "mark"):
                if _k in _old_m:
                    _v = int(_old_m[_k] or 0)
                    if _v > 0:
                        _new_deb[_k] = {"n": _v, "mult": 1.0}
                    b.mech_stacks.pop(_k, None)
            if _new_deb:
                b.enemy["debuffs"] = _new_deb
        return b

    # ---------------- 核心资源（v2.0 / v130.2 分支级 resource_override） ----------------
    def _branch_keys(self, player: dict) -> list:
        """当前职业/转职分支激活的核心资源 key 列表（v130.2 分支级 resource_override）。
        命中 BRANCH_RESOURCE_OVERRIDE[(class, evolve_path)] → 用分支指定资源（歌者 共鸣+回声、
        元素/奥秘法师 充能条）；否则回落 core_resources 按 class 默认单资源。
        基础法师（纯蓝施法者）无分支时不持有任何资源 → 返回 []。"""
        cls = player.get("class_name", "") or ""
        path = int(player.get("evolve_path", 0) or 0)
        tier = int(player.get("class_tier", 0) or 0)
        ov = BRANCH_RESOURCE_OVERRIDE.get((cls, path))
        if ov is not None:
            return list(ov)
        if cls == "cls_fa_shi" and not (path and tier):
            # v130.2（鱼鱼拍板）：基础法师无核心资源——纯蓝施法者，充能条是转职首获
            return []
        rd = E.core_resource_def(cls)
        return [rd["key"]] if rd else []

    def _is_branch_of(self, player: dict, *branch_names: str) -> bool:
        """判断玩家当前转职分支名是否在 branch_names 中（拿当前 tier 分支列表，path 选列）。
        攻线 path=1 / 守线 path=2；隐藏线 class_name 即隐藏职业，不走此判定。"""
        cls = player.get("class_name", "")
        tier = int(player.get("class_tier", 0) or 0)
        path = int(player.get("evolve_path", 0) or 0)
        if tier < 1 or path < 1:
            return False
        cls_info = C.CLASSES.get(cls) or {}
        branches = (cls_info.get("evolve_branches") or {}).get(tier) or []
        if path - 1 >= len(branches):
            return False
        return branches[path - 1] in branch_names

    def _is_path(self, player: dict, path: int) -> bool:
        """玩家转职分支线判定（攻线=1 / 守线=2；evolve_path 恒为所选线，跨 tier 进化改名仍命中；
        基础/无分支 evolve_path=0 不命中）。v130.2 P1-1：修复 8 处挂点只认 tier1 分支名（狂战士/
        影舞者/格斗士/风行者/元素法师等），60/90 级进化改名后机制全档断档的系统性问题。"""
        return int(player.get("evolve_path", 0) or 0) == int(path or 0)

    def _elem_charge(self) -> int:
        """法师充能条当前值（v130.2：element 资源数值化 0-5；resources['element'] 保留当前系字符串，兼容旧消费点）"""
        return int(self.resources.get("element_charge", 0) or 0)

    def _res_read(self, key: str) -> int:
        """读取资源值（element → 充能条 element_charge；其余直读 resources[key]）"""
        if key == "element":
            return self._elem_charge()
        return int(self.resources.get(key, 0) or 0)

    def _res_gain(self, player: dict, key: str, amount: int, logs: list | None = None) -> int:
        """资源增加（带上限）。element → 充能条（CORE_RESOURCES element max=5）；
        副资源（resonance 等按 key 注册）→ core_resource_gain_key；其余按 class 定义。
        v130.2 P1-3 修复：基础 key（rage/cp/energy/faith/dragon_might/zen 等，非按 key 注册的副资源）
        旧实现只返回新值不写回 self.resources[k] → restore_resource 药水/战前预充/隐藏线 res_gain 全静默失效；
        现统一写回（调用方丢弃返回值也落库正确，无双重累加风险——各调用方均不以返回值为累加基准）。
        v130.2 R1：logs 可选透传——echo 分支经 _echo_add 产出「🎵 回声驻留 +N」反馈（歌者施放可见）。"""
        if key == "element":
            # v130.2c 元素使徒 2 件：充能条上限 +1（5 → 6）——走 _res_max 统一上限
            mx = self._res_max(player, key)
            self.resources["element_charge"] = min(mx, self._elem_charge() + int(amount or 0))
            return self.resources["element_charge"]
        if key == "echo":
            # v130.2 收尾：echo 驻留叠层存 mech_stacks（战斗内不清零），不走 resources 影子槽
            return self._echo_add(player, logs if logs is not None else [], int(amount or 0))
        if E.core_resource_def_by_key(key):
            new = E.core_resource_gain_key(key, self.resources, int(amount or 0))
            self.resources[key] = new
            return new
        rd = E.core_resource_def(player.get("class_name", ""))
        if not rd:
            return self.resources.get(key, 0)
        new = min(self._res_max(player, key), int(self.resources.get(key, 0) or 0) + int(amount or 0))
        self.resources[key] = new
        return new

    def _res_spend(self, key: str, amount: int) -> bool:
        """资源消耗（足够则扣除返回 True；不足不扣返回 False）。element → 充能条。"""
        if key == "element":
            cur = self._elem_charge()
            if cur < int(amount or 0):
                return False
            self.resources["element_charge"] = cur - int(amount or 0)
            return True
        cur = int(self.resources.get(key, 0) or 0)
        if cur < int(amount or 0):
            return False
        self.resources[key] = cur - int(amount or 0)
        return True

    def _res_gain_class(self, cls: str, k: str, amount: int) -> int:
        """类主资源增加（带上限 + 隐藏线满溢转盾）。v130.2：悼咏 canticle overflow_shield=True
        时满 10 后每溢出 1 点转自身 5 点护盾（冷却 1 回合，priest.md §5.2）。"""
        rd = E.core_resource_def(cls)
        if not rd:
            return self.resources.get(k, 0)
        # v130.2 R1：上限口径与 _res_max 统一（词条 max_bonus + 套装 res_max）；无 player 参数取本场玩家；
        # self.player 为 None（from_state 恢复等）时按空 dict 守卫，套装/词条加成归 0
        _pl = self.player or {}
        mx = int(rd.get("max", 99) or 99) + self._res_affix_max_bonus(_pl, k) + self._set_res_max_bonus(_pl, k)
        cur = int(self.resources.get(k, 0) or 0)
        amount = int(amount or 0)
        overflow = 0
        if amount > 0 and cur + amount > mx:
            overflow = cur + amount - mx
        new = min(mx, cur + amount)
        if rd.get("overflow_shield") and overflow > 0:
            shield = int(overflow * 5)
            self._add_shield("canticle_overflow", shield, 1)
        self.resources[k] = new
        return new

    def _amp_resource(self, player: dict, trigger: str) -> int:
        """v130.2 资源增幅（resource_amp）消费挂点（P0-1：4 种药水写无读修复）。
        p_eff['amps'] 中 trigger 匹配且剩余计数>0 的条目，额外 _res_gain 对应资源 amount。
        trigger ∈ {on_hit_taken 受击 / on_land_hit 出手命中 / on_heal 治疗 / regen 自然回复}。
        on_hit 双语义（沸腾战血=受击/影袭=出手命中）由 hits_left 区分：>0 → 出手命中逐次递减；
        ≤0 → 回合制（turns 在 _end_round 递减）。返回本次额外增加总量。"""
        amps = (self.p_eff or {}).get("amps")
        if not amps:
            return 0
        extra = 0
        for key, amp in list(amps.items()):
            if not isinstance(amp, dict):
                continue
            t = str(amp.get("trigger", ""))
            if trigger == "on_land_hit":
                if t != "on_hit" or int(amp.get("hits_left", 0) or 0) <= 0:
                    continue
            elif trigger == "on_hit_taken":
                if t != "on_hit" or int(amp.get("hits_left", 0) or 0) > 0:
                    continue
            elif t != trigger:
                continue
            remain = int(amp.get("hits_left", 0) or 0) if trigger == "on_land_hit" \
                else int(amp.get("turns_left", 0) or 0)
            if remain <= 0:
                continue
            amount = int(amp.get("amount", 0) or 0)
            if amount <= 0:
                continue
            self._res_gain(player, str(amp.get("key", "") or key), amount)
            extra += amount
            if trigger == "on_land_hit":  # hits 制出手命中逐次消耗
                amp["hits_left"] = remain - 1
                if amp["hits_left"] <= 0 and int(amp.get("turns_left", 0) or 0) <= 0:
                    del amps[key]
        if not amps:
            self.p_eff.pop("amps", None)
        return extra

    # ---------------- v130.2c 装备-资源词条接线（31 词条接线：统一读取器 + 各挂点） ----------------
    # 修复对象：affixes.py v130.2 资源联动词条 31 个（此前纯展示无效果）。
    # gain 类 12：战意/战吼回响/浴血/残血灼薪/充能汲引/圣辉回响/虔诚护符/暴击回点/暴击蓄能/
    #             连段回收/磐息/起手之势；max_bonus 类 6：怒火熔铸/神赐容光/圣光之心/盈满背囊/
    #             气量强化/节奏之徽；回能 1：精力潮汐；减免 2：凝神塑能/圣徽之佑（+精力刀刃）；
    #             倍率 2：爆发贯体/终结之技；减伤 1：沸血浇筑。
    RES_AFFIX_GAIN = ("war_spirit", "warcry_echo", "blood_bath", "ember_brand", "arcana_flux",
                      "holy_echo", "pious_charm", "crit_return", "crit_charge",
                      "combo_recover", "rock_rest", "opening_stance")
    RES_AFFIX_MAX = ("rage_forge", "divine_radiance", "holy_heart", "full_pack",
                     "chi_limit", "rhythm_badge")
    # v130.2d 六词条机制恢复（直接挂点登记，供收口审计 test_v1252_audit_closure 引用）：
    # 疾风余韵 turn_start → _turn_start 自然回段；连段护持 on_taken → _combo_break 受击保留判定
    RES_AFFIX_TURN_START = ("swift_tailwind",)
    RES_AFFIX_ON_TAKEN = ("combo_ward",)
    # v130.2c 资源联动套装 effect 全部由 battle.py 直连消费（供收口审计 test_v1252_audit_closure 引用）
    SET_EFFECT_CONSUMED = ("res_gain", "res_max", "ultimate_cost_reduce", "cdr_set",
                           "crit_on_marked", "res_cost_reduce", "heal_team_on_miracle_t2plus",
                           "first_hit_immune", "elegy_dmg", "battle_start_cp", "finisher_crit",
                           "combo_finisher_per_layer", "battle_start_res", "chi_skill_phys",
                           "full_rage_pursuit")

    def _affix_effs(self, player: dict, aid: str) -> list:
        """已装备词条的全部实例 effect 列表（可跨件叠加；每件 = (effect dict, tier 值或 None)）。
        tier = effect.tiers[装备品质] 纯数值档，覆盖该词条的主数值键（消费方按需读取）。"""
        out = []
        for item in (player.get("equipment") or {}).values():
            if not item or aid not in (item.get("affixes") or []):
                continue
            info = C.AFFIXES.get(aid) or C.LEGENDARY_EFFECTS.get(aid) or {}
            eff = dict(info.get("effect") or {})
            tv = None
            tiers = eff.get("tiers")
            if isinstance(tiers, dict):
                tv = tiers.get(item.get("quality", ""))
                eff.pop("tiers", None)
            out.append((eff, tv))
        return out

    def _affix_eff_tiered(self, player: dict, aid: str) -> tuple:
        """单实例便捷读取：返回 (effect, tier)；未装备 → (None, None)。"""
        effs = self._affix_effs(player, aid)
        return effs[0] if effs else (None, None)

    def _res_affix_max_bonus(self, player: dict, key: str) -> int:
        """词条资源上限加成（max_bonus 类 6 个，按 effect.res 匹配资源位）。
        rhythm_badge 带 max_total=2 总帽（多件叠加受限）；full_pack 按装备品质 tier 取档（10/20）。"""
        if not self._equip_affix_ids(player):
            return 0
        bonus = 0
        total_cap = None
        for aid in self.RES_AFFIX_MAX:
            for eff, tier in self._affix_effs(player, aid):
                if not eff or eff.get("res") != key:
                    continue
                b = int(eff.get("max_bonus", 0) or 0)
                if tier is not None:
                    b = int(tier or 0)
                if b <= 0:
                    continue
                mt = eff.get("max_total")
                if mt is not None:
                    total_cap = int(mt) if total_cap is None else min(int(mt), total_cap)
                bonus += b
        if total_cap is not None:
            bonus = min(bonus, total_cap)
        return bonus

    def _res_max(self, player: dict, key: str) -> int:
        """资源当前上限（基础上限 + 词条 max_bonus + 套装 res_max；按 key 注册的副资源优先，否则按职业主资源）。"""
        rd = E.core_resource_def_by_key(key) or E.core_resource_def(player.get("class_name", "")) or {}
        return int(rd.get("max", 99) or 99) + self._res_affix_max_bonus(player, key) + self._set_res_max_bonus(player, key)

    def _rage_full(self, player: dict) -> bool:
        """沸血浇筑条件：怒气全满（rage ≥ 上限，含怒火熔铸上限加成；上限读 battle_config 系 core_resources max=10）。"""
        return int(self.resources.get("rage", 0) or 0) >= self._res_max(player, "rage")

    def _affix_res_proc(self, player: dict, event: str, logs: list):
        """v130.2c 资源词条统一读取器：在事件点结算 gain 类词条 effect 的 res/gain/on/cond。
        event ∈ on_attack/on_skill/buff_skill/combo_skill/on_cast/on_heal/on_crit/on_taken/battle_start。
        语义对齐 affixes.py 数据：
        - on 命中才触发（战意 on_attack/on_skill、战吼回响 buff_skill、充能汲引 on_cast、圣辉回响 on_heal、
          暴击系 on_crit、连段回收 combo_skill、受击系 on_taken、起手之势 battle_start）；
        - 残血灼薪（无 on 字段，cond=hp_lt_30）按怒气三路获取事件（普攻/技能/受击）+ 血量 <30% 判定；
        - 圣辉回响 tier 覆盖 gain（蓝 1/紫 2）；暴击回点 chance 判定（蓝 15%/紫 25%，tier 覆盖）。"""
        ids = self._equip_affix_ids(player)
        if not ids:
            return
        _hp = max(0, player.get("hp", 0) or 0)
        _mx = max(1, player.get("max_hp", 1) or 1)
        _hp_ok = (_hp / _mx) < 0.30
        hp_cond_events = ("on_attack", "on_skill", "on_taken")  # 怒气三路：残血灼薪挂靠
        for aid in self.RES_AFFIX_GAIN:
            if aid not in ids:
                continue
            for eff, tier in self._affix_effs(player, aid):
                if not eff:
                    continue
                res = eff.get("res")
                if not res:
                    continue
                ons = eff.get("on")
                if isinstance(ons, str):
                    ons = [ons]
                if eff.get("cond") == "hp_lt_30":  # 残血灼薪：无 on 字段
                    if event not in hp_cond_events or not _hp_ok:
                        continue
                elif ons and event not in ons:
                    continue
                gain = int(eff.get("gain", 1) or 0)
                if aid == "crit_return":  # 暴击回点：tier 覆盖 chance（非 gain）
                    chance = float(tier if tier is not None else eff.get("chance", 0.15) or 0.15)
                    if random.random() >= chance:
                        continue
                elif tier is not None:  # 圣辉回响等：tier 覆盖 gain
                    gain = int(tier or gain)
                if gain <= 0:
                    continue
                _before = self._res_read(res)
                added = self._res_gain(player, res, gain)
                if added > _before:  # v130.2 R1：真实增量判定（满资源不再误报）
                    _nm = (C.AFFIXES.get(aid) or {}).get("name", aid)
                    _rd = E.core_resource_def_by_key(res) or E.core_resource_def(player.get("class_name", "")) or {}
                    logs.append(f"✦ {_nm}：{_rd.get('name', res)} +{gain}！")

    def _mp_cost_reduce(self, player: dict, info: dict) -> int:
        """v130.2c 魔力消耗减免（词条）：返回固定减免值。
        凝神塑能（元素/奥术技能 蓝耗 -10%，乘算折算为当前蓝耗减免额；基础法师即受益）、
        圣徽之佑（神迹技 蓝耗 -5/史诗 -10，tier 取档；神迹技 = 消耗信仰/悼咏的技能）。"""
        mp = int((info or {}).get("mp", 0) or 0)
        if mp <= 0:
            return 0
        reduce = 0
        cls = player.get("class_name", "")
        # 凝神塑能：元素/奥术技能 = 带 element 字段或 res_gain element 的法师技能
        eff, tier = self._affix_eff_tiered(player, "arcane_focus")
        if eff and cls == "cls_fa_shi" and (info.get("element") or (info.get("res_gain") or {}).get("element")):
            pct = float(tier if tier is not None else eff.get("mp_cost_reduce", 0.10) or 0.10)
            reduce += int(mp * pct)
        # 圣徽之佑：神迹技（消耗信仰/悼咏）
        eff, tier = self._affix_eff_tiered(player, "sigil_blessing")
        if eff:
            rc = info.get("res_cost") or {}
            ca = info.get("consume_all") or {}
            is_miracle = bool(rc.get("faith") or rc.get("canticle") or ca.get("key") in ("faith", "canticle"))
            if is_miracle:
                reduce += int(tier if tier is not None else eff.get("mp_cost_reduce", 5) or 5)
        return reduce

    def _affix_skill_dmg_mult(self, player: dict, info: dict, kind: str) -> float:
        """v130.2c 技能伤害倍率词条：
        爆发贯体（气力技=拳师物理技能 +10%）、终结之技（终结技=res_cost/consume_all 消耗型技能，
        +10%/15%/20% tier 取档）。返回倍率（无词条 = 1.0）。"""
        if not self._equip_affix_ids(player):
            return 1.0
        mult = 1.0
        if kind == "物理" and player.get("class_name", "") == "cls_wu_seng":  # 拳师（v130.2c 修正 class id）
            for eff, tier in self._affix_effs(player, "burst_break"):
                if not eff:
                    continue
                v = float(tier if tier is not None else eff.get("chi_skill_phys", 0.10) or 0.10)
                mult *= 1.0 + v
        if info and (info.get("res_cost") or info.get("consume_all")):
            for eff, tier in self._affix_effs(player, "finisher"):
                if not eff:
                    continue
                v = float(tier if tier is not None else eff.get("finisher_dmg", 0.10) or 0.10)
                mult *= 1.0 + v
        return mult

    def _init_resources(self, player: dict):
        """战斗开始：按职业/转职分支初始化核心资源 dict（v130.2 分支级 resource_override）。
        元素法师→当前系 fire + 充能条 0；游侠精力满 100；其余 0。"""
        # v130.2 战前待用效果注入（战前猛火餐/夜枭茶/澎湃烈酒/香薰圣烛，物品消费端战场前挂载；
        # 与 battle_start_cp 被动同入口，战斗初始化段一次性，from_state 恢复不再触发）
        self._apply_pending_prebattle(player)
        keys = self._branch_keys(player)
        if not keys:
            return
        for k in keys:
            if k == "element":
                # resources['element'] 保持当前系字符串（代码多处按字符串读）；充能数值走 element_charge
                self.resources["element"] = "fire"
                self.resources["element_charge"] = 0
            elif k == "echo":
                # 回声 = mech_stacks 驻留叠层（战斗内不清零），不占 resources 数值位
                self.mech_stacks.setdefault("echo", 0)
            elif k == "energy":
                # 游侠精力：唯一自然回资源，战斗开始满额 100（ranger.md 设计稿 + E1 回归修复）
                self.resources[k] = int((C.CORE_RESOURCES.get("cls_you_xia") or {}).get("max", 100) or 100)
            else:
                self.resources[k] = 0
        # v110.3 P1-11：致命预谋被动——战斗开始 +1 连击点（数据驱动 battle_start_cp，替代名字硬匹配）
        if "cp" in keys and self._passive_map(player)["proc"].get("battle_start_cp", []):
            self.resources["cp"] = 1

    def _apply_pending_prebattle(self, player: dict):
        """v130.2 战前待用效果注入（物品消费端战场前挂载）。
        economy『使用 战前猛火餐/夜枭茶/澎湃烈酒/香薰圣烛』战斗外写入玩家级
        event_state prebattle_{qq_id}（item_templates._v130_pend_add），战斗初始化段在此
        读取并注入：battle_start_resource → 预充资源 + 可选 buff；resource_amp → 挂载 amp。
        仅注入玩家职业/分支持有的资源位（_branch_keys），跨职业误用静默跳过；注入后清 key。"""
        qq = player.get("qq_id")
        if not qq:
            return
        import json as _json
        from . import db as _db
        _key = f"prebattle_{qq}"
        _raw = _db.get_event_state(_key)
        if not _raw:
            return
        try:
            _pend = _json.loads(_raw)
        except Exception:
            _db.delete_event_state(_key)
            return
        if not isinstance(_pend, list):
            _db.delete_event_state(_key)
            return
        keys = self._branch_keys(player)
        for _pe in _pend:
            if not isinstance(_pe, dict):
                continue
            _rk = _pe.get("key", "")
            if not _rk or _rk not in keys:
                continue
            if _pe.get("type") == "battle_start_resource":
                _amt = int(_pe.get("amount", 0) or 0)
                if _amt > 0:
                    self._res_gain(player, _rk, _amt)
                _bf = _pe.get("buff")
                if isinstance(_bf, dict) and _bf.get("kind") == "phys_up":
                    _pct = float(_bf.get("pct", 0.05) or 0)
                    _t = int(_bf.get("turns", 3) or 3)
                    self.p_buffs["phys_up"] = max(int(self.p_buffs.get("phys_up", 0) or 0), _t)
                    self.p_eff["phys_up"] = max(float(self.p_eff.get("phys_up", 0) or 0), _pct)
            elif _pe.get("type") == "resource_amp":
                amps = self.p_eff.setdefault("amps", {})
                _prev = amps.get(_rk) or {}
                amps[_rk] = {
                    "key": _rk, "amount": int(_pe.get("amount", 0) or 0),
                    "trigger": _pe.get("trigger", ""),
                    "turns_left": max(int(_prev.get("turns_left", 0) or 0), int(_pe.get("turns", 0) or 0)),
                    "hits_left": max(int(_prev.get("hits_left", 0) or 0), int(_pe.get("hits", 0) or 0)),
                }
        # 注入后清除战前待用（一次性，防重复）
        _db.delete_event_state(_key)

    def _resource_label(self, player: dict) -> str:
        """战斗状态栏显示核心资源(如 ⚡ 怒气 3/10 / ✦ 元素亲合 3/5 / ✦ 共鸣 4/10·回声 2/3)。"""
        keys = self._branch_keys(player)
        if not keys:
            return ""
        parts = []
        for k in keys:
            if k == "echo":
                v = int(self.mech_stacks.get("echo", 0) or 0)
                parts.append(f"✦ 回声 {v}/{ECHO_CFG['max_layers']}")
            elif k == "element":
                v = self._elem_charge()
                # v130.2c 元素使徒 2 件：上限 5 → 6 随 _res_max 展示
                mx = self._res_max(player, k)
                parts.append(f"✦ 元素亲合 {v}/{mx}")
            else:
                # 主资源（怒气/精力/信仰/连击点/气/龙力等）= CORE_RESOURCES 以 class id 为 key，
                # 取 definitions 映射到 key（class 资源定义的 key 字段）而非直接 by_key 查。
                rd = E.core_resource_def(player.get("class_name", "")) or {}
                if rd.get("key") != k:
                    # 副资源（如分支 override 引入的独立 key）才按 key 查
                    rd2 = E.core_resource_def_by_key(k) or {}
                    # 隐藏线主资源（龙力/时之沙/猎印/影步/禅意）class 定义兜底
                    if not rd2 and not rd:
                        continue
                    rd = rd2 or rd
                if not rd:
                    continue
                v = int(self.resources.get(k, 0) or 0)
                mx = self._res_max(player, k)
                parts.append(f"✦ {rd['name']} {v}/{mx}")
        return " ".join(parts)

    # ---------------- 技能冷却（v2.0） ----------------
    def _skill_cd_left(self, skill_name: str) -> int:
        """技能剩余冷却回合数(0 = 可用)。"""
        return int(self.cooldown.get(skill_name, 0) or 0)

    def _skill_on_cd(self, skill_name: str) -> bool:
        return self._skill_cd_left(skill_name) > 0

    def _set_skill_cd(self, skill_name: str, cd: int):
        """设置技能冷却(cd 回合，1 表示下一回合即可用)。
        v106.1 冷却缩减：cd ×(1-cdr)（cap 40%），保底 1（cd=1 的技能不受影响）。"""
        if cd > 0:
            cdr = 0.0
            try:
                cdr = min(float(self._player_stats(self.player).get("cdr", 0) or 0), 0.4)
            except Exception:
                cdr = 0.0
            if cdr > 0 and cd > 1:
                cd = max(1, int(cd * (1 - cdr)))
            # v130.2c 时之领主 2 件：时停领域 冷却 -1（cdr_set on=time_freeze，最低 1）
            if skill_name == "时停领域":
                _ce = self._set_eff(self.player, "cdr_set", 2, on="time_freeze")
                if _ce:
                    cd = max(1, cd + int(_ce.get("value", -1) or -1))
            self.cooldown[skill_name] = cd

    def _tick_cooldowns(self):
        """回合结束：所有冷却－1，归零清除。"""
        for k in list(self.cooldown):
            self.cooldown[k] -= 1
            if self.cooldown[k] <= 0:
                del self.cooldown[k]

    # ---------------- 连招序列（v2.0，拳师） ----------------
    # 连招顺序：拳 → 踢 → 掌 →（三连触发）→ 重新开始
    COMBO_ORDER = ["拳", "踢", "掌"]

    def _combo_push(self, tag: str) -> bool:
        """记录连招 tag（拳/踢/掌）。返回是否触发三连。
        非连招 tag 不清空序列（只有非连招技能打断不重置）。"""
        if tag not in self.COMBO_ORDER:
            return False
        expect = self.COMBO_ORDER[len(self.combo_seq)]
        if tag == expect:
            self.combo_seq.append(tag)
        else:
            # 顺序不对：从该 tag 重新开始（如果 tag 是起手拳则开始新序列）
            self.combo_seq = [tag] if tag == self.COMBO_ORDER[0] else []
        if len(self.combo_seq) == len(self.COMBO_ORDER):
            self.combo_seq = []
            return True
        return False

    def _combo_label(self) -> str:
        """当前连招进度显示(如 拳→踢→_)。"""
        if not self.combo_seq:
            return ""
        parts = list(self.combo_seq)
        while len(parts) < len(self.COMBO_ORDER):
            parts.append("_")
        return "→".join(parts)

    # ---------------- v130.2 新机制挂点（资源即身份：转职分支独占，基础无） ----------------
    # —— 刺客攻线·影舞者：连段计数 combo（连了才涨、断了重来；仅攻线结算）——
    def _combo_active(self, player: dict) -> bool:
        """连段计数是否活跃（仅攻线·影舞者；基础/毒线/影步线均不读 combo）"""
        return player.get("class_name", "") == "cls_ci_ke" and self._is_path(player, 1)

    def _combo_add(self, player: dict) -> int:
        """命中 +1 连段（上限 cap=10）。"""
        combo = int(self.mech_stacks.get("combo", 0) or 0)
        combo = min(int(COMBO_CFG.get("cap", 10) or 10), combo + 1)
        self.mech_stacks["combo"] = combo
        return combo

    def _combo_break(self, player: dict, keep_chance: float = 0.0) -> None:
        """受击或落空 → 连段归零（断了重来）。
        v130.2d 连段护持：受击时按词条概率保留连段（史诗 15%/传说 30%，tier 取档）；落空不受保护。"""
        if keep_chance > 0 and random.random() < keep_chance:
            return
        self.mech_stacks.pop("combo", None)

    def _combo_keep_chance(self, player: dict) -> float:
        """v130.2d 连段护持：受击连段保留概率（读 effect.combo_keep_chance，tier 覆盖；攻线限定）。"""
        if not self._combo_active(player):
            return 0.0
        chance = 0.0
        for eff, tier in self._affix_effs(player, "combo_ward"):
            if not eff:
                continue
            v = float(tier if tier is not None else eff.get("combo_keep_chance", 0.0) or 0.0)
            if v > chance:
                chance = v
        return chance

    def _combo_finish_min(self, player: dict) -> int:
        """v130.2d 连段之锋：连段生效阈值 -1（combo ≥3 → ≥2，最低 1；攻线限定）。"""
        if not self._combo_active(player):
            return int(COMBO_CFG.get("finish_min", 3) or 3)
        reduce = 0
        for eff, tier in self._affix_effs(player, "combo_edge"):
            if not eff:
                continue
            v = int(tier if tier is not None else eff.get("combo_threshold_reduce", 0) or 0)
            if v > 0:
                reduce += v
        return max(1, int(COMBO_CFG.get("finish_min", 3) or 3) - reduce)

    def _combo_dmg_mult(self, player: dict) -> float:
        """终结技连段增伤：combo ≥3 起每层 +5%，上限 +40%（8 层封顶）。
        v130.2c 夜幕合契·影纱 5 件：每层 5% → 8%，8 层封顶 +64%（per_layer 读套装 effect）。"""
        if not self._combo_active(player):
            return 1.0
        combo = int(self.mech_stacks.get("combo", 0) or 0)
        if combo < self._combo_finish_min(player):
            return 1.0
        per = float(COMBO_CFG.get("per_layer", 0.05) or 0.05)
        cap = float(COMBO_CFG.get("max_bonus", 0.40) or 0.40)
        _ce = self._set_eff(player, "combo_finisher_per_layer", 5)
        if _ce:
            per = float(_ce.get("per_layer", 0.08) or 0.08)
            cap = per * int(_ce.get("max_layers", 8) or 8)  # v130.2 R1：层数帽读数据（缺省 8）
        bonus = min(combo * per, cap)
        return 1.0 + bonus

    # —— 拳师攻线·格斗士：蓄势 Momentum（每 1 气持有 物理伤害 +3%，满 +30%）——
    def _momentum_mult(self, player: dict) -> float:
        """蓄势持有加伤倍率。仅攻线·格斗士（monk evolve_path=1）吃到；气耗尽自然归 0。"""
        cls = player.get("class_name", "")
        if not (cls == "cls_wu_seng" and self._is_path(player, 1)):
            return 1.0
        chi = int(self.resources.get("chi", 0) or 0)
        cap = int(MOMENTUM_CFG.get("cap_chi", 10) or 10)
        per = float(MOMENTUM_CFG.get("per_chi", 0.03) or 0.03)
        # v130.2d 蓄势精通：攻线每 1 气物理伤害 +3% → +4%（词条 effect.momentum_per_chi 覆盖常量；
        # 攻线蓄势限定随上方 class/path 门；苦修士线锁系数不上浮不受影响）
        for _meff, _mtier in self._affix_effs(player, "momentum_mastery"):
            if not _meff:
                continue
            _mv = float(_mtier if _mtier is not None else _meff.get("momentum_per_chi", 0.0) or 0.0)
            if _mv > 0:
                per = _mv
                break
        return 1.0 + min(chi, cap) * per

    # —— 游侠守线·风行者：满弦状态（精力 ≥80 时 低耗/连射技能 暴击率 +10%）——
    def _energy_high_crit(self, player: dict, info: dict | None = None) -> bool:
        """满弦状态判定：守线·风行者（you_xia evolve_path=2）且精力 ≥80 且技能处于低耗/连射档。
        v130.2：满弦烈酒 p_buffs["full_tension"] = 阈值视为已满足（立即满弦，handler 已做守线专属判定）。"""
        if self.p_buffs.get("full_tension"):
            return True
        if player.get("class_name", "") != "cls_you_xia" or not self._is_path(player, 2):
            return False
        # v130.2 P1-4：读「施放前」精力（_do_player_skill 已快照）；直接调用/非技能链回落当前值。
        _pres = getattr(self, "_pre_cost_res", None)
        energy_val = int(_pres.get("energy", 0) or 0) if isinstance(_pres, dict) \
            else int(self.resources.get("energy", 0) or 0)
        if energy_val < int(ENERGY_HIGH.get("threshold", 80) or 80):
            return False
        if info is not None:
            cost = int((info.get("res_cost") or {}).get("energy", 0) or 0)
            if cost > int(ENERGY_HIGH.get("max_cost", 25) or 25):
                return False
        return True

    # —— 法师攻线·元素：目标侧 element_marks 登记（每目标每系独立 0..3）——
    def _elem_marks(self, target: dict | None = None) -> dict:
        """目标侧元素印记 dict {fire/ice/thunder: 0..N}；缺省 = 当前交战目标。"""
        tgt = target or getattr(self, "_active_target", None) or self.enemy
        if not isinstance(tgt, dict):
            return {}
        marks = tgt.get("element_marks")
        if not isinstance(marks, dict):
            marks = {}
            tgt["element_marks"] = marks
        return marks

    def _elem_mark_apply(self, element: str, target: dict | None = None, layers: int = 1,
                         player: dict | None = None) -> int:
        """施法命中叠加目标元素印记（每系上限 ELEMENT_MARKS_MAX=3；印记铭刻词条 +1 → 4）。
        返回该系新层数。"""
        if element not in ("fire", "ice", "thunder"):
            return 0
        marks = self._elem_marks(target)
        cur = int(marks.get(element, 0) or 0)
        new = min(self._elem_mark_max(player), cur + int(layers or 1))
        marks[element] = new
        return new

    def _elem_mark_max(self, player: dict | None = None) -> int:
        """v130.2d 印记铭刻：元素印记每系上限（基础 ELEMENT_MARKS_MAX=3；词条 effect.max_sigil 叠加，
        元素法师 cls_fa_shi 攻线转职后生效，cond=element_mage）。player 缺省取本场 self.player。"""
        pl = player or self.player or {}
        bonus = 0
        if pl.get("class_name", "") == "cls_fa_shi" and self._is_path(pl, 1):
            for eff, tier in self._affix_effs(pl, "sigil_engrave"):
                if not eff:
                    continue
                v = int(tier if tier is not None else eff.get("max_sigil", 0) or 0)
                if v > 0:
                    bonus += v
                # v130.2 R1 印记帽：词条 effect.max_total 封顶多件叠加（R2 配 sigil_engrave max_total=1；未读到不封顶）
                _mt = int(eff.get("max_total", 0) or 0)
                if _mt > 0 and bonus > _mt:
                    bonus = _mt
        return int(ELEMENT_MARKS_MAX or 3) + bonus

    def _elem_marks_total(self, target: dict | None = None) -> int:
        """目标三系印记总和（供元素共鸣类加成引用）。"""
        marks = self._elem_marks(target)
        return sum(int(v or 0) for v in marks.values()) if marks else 0

    # —— 法师攻线·元素：last_element 同系连发（被动「元素凝聚」：连续两次同系施放，第二次 +1 充能）——
    def _last_element_set(self, player: dict, element: str) -> bool:
        """记录上次施放元素。返回本次是否「同系连发」（与上次同系 → True）。"""
        last = self._last_element if hasattr(self, "_last_element") else None
        self._last_element = element
        if not last or last != element:
            return False
        # 元素凝聚被动：同系连发第二次施放额外 +1 充能（攻线·元素法师）
        if (player.get("class_name", "") == "cls_fa_shi"
                and self._is_path(player, 1)
                and ELEMENT_SAME_CAST_EXTRA_CHARGE):
            self._res_gain(player, "element", ELEMENT_SAME_CAST_EXTRA_CHARGE)
        return True

    # —— 牧师攻线·歌者：回声驻留叠层（echo 存 mech_stacks，战斗内不清零，上限 max_layers）——
    def _echo_layers(self) -> int:
        return int(self.mech_stacks.get("echo", 0) or 0)

    def _echo_add(self, player: dict, logs: list, amount: int = 1) -> int:
        """回声叠层（上限 max_layers）。v130.2 收尾：echo 生产收敛为 res_gain 单通道，
        按技能数据 res_gain['echo'] 数值叠加（原 kind 钩子无条件 +1 已删，防双源双倍速）。"""
        if player.get("class_name", "") != "cls_mu_shi" or not self._is_branch_of(player, *BARD_BRANCHES):
            return 0
        cur = self._echo_layers()
        cap = int(ECHO_CFG.get("max_layers", 3) or 3)
        if cur >= cap:
            return cur
        cur = min(cap, cur + int(amount or 0))
        self.mech_stacks["echo"] = cur
        logs.append(f"🎵 回声驻留 +{int(amount or 0)}：全队回合恢复随回声层数(当前 {cur}/{cap})")
        return cur

    def _is_bard_skill(self, player: dict, info: dict | None = None) -> bool:
        """技能是否歌者分支技能（歌类技 → 施放叠回声 + 增益续时）。"""
        if player.get("class_name", "") != "cls_mu_shi" or not self._is_branch_of(player, *BARD_BRANCHES):
            return False
        if info is None:
            return True
        owner = E.branch_skill_owner("cls_mu_shi", info.get("name", ""))
        return bool(owner and owner[1] in BARD_BRANCHES)

    # —— 法师攻线·元素：引爆技反应表结算（cond type='reaction'，读目标 element_marks）——
    def _reaction_table_resolve(self, player: dict, element: str, st: dict, logs: list) -> tuple | None:
        """引爆技按 引爆系 × 目标 element_marks 组合查 REACTION_TABLE 结算（蒸发/超载/冻结/感电）。

        返回 (reaction_mult, 反应日志, chain_flag) 或 None（目标无对应印记系）。
        aoe/freeze 在函数内结算；chain 返回 flag 由调用方 multi+1。结算后清除被反应消费的目标印记系。
        """
        if element not in ("fire", "ice", "thunder"):
            return None
        marks = self._elem_marks()
        target_el = None
        for cast_el, mark_el in REACTION_TABLE:
            if cast_el == element and int(marks.get(mark_el, 0) or 0) > 0:
                target_el = mark_el
                break
        if target_el is None:
            return None
        r = REACTION_TABLE[(element, target_el)]
        rmult = float(r.get("mult", 1.0))
        # v130.2d 反应催化：元素反应伤害 +15%（元素法师转职后生效；词条 effect.reaction_dmg 叠加）
        rmult *= self._reaction_catalyst_mult(player)
        log = f"💥{r['name']}！"
        chain_flag = False
        # v104 R3 P1-1：元素共鸣被动——元素反应伤害 +15%（在基础反应倍率上叠加；随后复位）
        if getattr(self, "_elem_reaction_boost", 1.0) > 1.0:
            rmult *= self._elem_reaction_boost
            self._elem_reaction_boost = 1.0
        extra = r.get("extra", "")
        if extra == "aoe":
            aoe_dmg = int((st or {}).get("matk", 0) * 1.2 * rmult)
            self._aoe_damage_enemy(aoe_dmg, logs)
            log = f"💥超载爆发！额外 {aoe_dmg} 点全体伤害！"
        elif extra == "freeze":
            self.e_buffs["freeze"] = 1
            log = "❄️冻结！目标被冰封 1 回合！"
        elif extra == "chain":
            chain_flag = True
            log = "⚡感电连锁！追加一次攻击！"
        clear_el = r.get("clear", "")
        if clear_el:
            marks.pop(clear_el, None)
        return rmult, log, chain_flag

    def _reaction_catalyst_mult(self, player: dict) -> float:
        """v130.2d 反应催化：元素反应伤害倍率（effect.reaction_dmg=0.15；元素法师攻线转职后生效）。"""
        if not (player.get("class_name", "") == "cls_fa_shi" and self._is_path(player, 1)):
            return 1.0
        bonus = 0.0
        for eff, tier in self._affix_effs(player, "reaction_catalyst"):
            if not eff:
                continue
            v = float(tier if tier is not None else eff.get("reaction_dmg", 0.0) or 0.0)
            if v > 0:
                bonus += v
        return 1.0 + bonus if bonus > 0 else 1.0

    def _ct_cost(self, spd) -> float:
        """v121 CTB：行动消耗 cost = BASE_DELAY / max(1, min(spd, SPD_CT_CAP))。"""
        try:
            eff = min(float(spd or 0), SPD_CT_CAP)
        except Exception:
            eff = 0.0
        return BASE_DELAY / max(1.0, eff)

    def _after_actor_ct(self, side: str, unit: dict | None = None, player: dict | None = None):
        """v121 CTB：行动者 ct += cost；其余所有存活单位 ct -= cost。
        side="p"：玩家行动完（用传入 player 的速度；from_state 恢复/副本构造无 self.player，
        必须传 player 否则 spd 视为 0 导致 p_ct 每次 +BASE_DELAY 卡死玩家）；
        side="e"：指定敌方单位行动完（该单位 cost 广播给玩家和其他敌）。
        敌方单位无 get("ct") 时兜底 setdefault(-spd)。"""
        if side == "p":
            _p = player or self.player or {}
            p_cost = self._ct_cost(self._player_stats(_p).get("spd", 0) if _p else 0)
            self.p_ct += p_cost
            for u in self.enemies:
                u.setdefault("ct", -float(u.get("spd", 0) or 0))
                if u.get("hp", 0) > 0:
                    u["ct"] = float(u.get("ct", 0) or 0) - p_cost
        else:
            u = unit or {}
            u.setdefault("ct", -float(u.get("spd", 0) or 0))
            # v121 审计修复：敌方 cost 用 buffed spd（_enemy_stats 应用 spd_down ×0.5 等），
            # 否则敌方减速/增益不影响其行动频率（与玩家侧 _player_stats 对称）
            e_cost = self._ct_cost(self._enemy_stats(u).get("spd", 0))
            u["ct"] = float(u.get("ct", 0) or 0) + e_cost
            # 玩家侧时间流逝
            self.p_ct -= e_cost
            # 其他存活敌方单位时间流逝
            for other in self.enemies:
                if other is u:
                    continue
                other.setdefault("ct", -float(other.get("spd", 0) or 0))
                if other.get("hp", 0) > 0:
                    other["ct"] = float(other.get("ct", 0) or 0) - e_cost

    # ---------------- v2 目标选择 / 蓄力（§3.2、§6） ----------------
    def _player_attacker(self, player: dict) -> dict:
        """玩家攻击方（射程按职业 reach，数据层未落地时默认 2=远程）。"""
        return {"uid": "player", "reach": int(player.get("reach") or 2)}

    def _resolve_player_target(self, player: dict, target=None) -> dict | None:
        """解析玩家行动目标（单怪兼容：恒为唯一/enemy 主目标）。
        返回目标单位 dict；无存活敌方返回 None。distinct 记录在 self._active_target。

        v127.3 目标编号：target 支持 a<序号>（敌方第 N）/ 纯数字（敌方第 N，修复
        『技能1 2』不能选敌）/ uid 精确 / 名字前缀。b<序号> 是友方目标（治疗），
        不在此解析。
        """
        import re as _re
        from .core.formation import alive_units, numbered_units, select_target
        alive = alive_units(self.enemies)
        if not alive:
            self._active_target = None
            return None
        if len(alive) == 1:
            # 单怪路径零随机（v103 确定性铁律：不改变存量单怪 random 顺序）
            self._active_target = alive[0]
            return alive[0]
        attacker = self._player_attacker(player)
        if target is None:
            picked = select_target(attacker, self.enemies)
        else:
            # v127.3 编号解析：a2 / 纯数字 2 → 敌方第 2 个目标（站位顺序）
            picked = None
            _m = _re.match(r"^(?:a)?(\d+)$", str(target).strip().lower())
            if _m:
                _n = int(_m.group(1))
                _numed = numbered_units(self.enemies)
                if 1 <= _n <= len(_numed):
                    picked = _numed[_n - 1][1]
                else:
                    self._target_not_found = str(target)
            else:
                # 指定目标：uid 精确或名字前缀匹配（存活）
                for u in self.enemies:
                    if u.get("hp", 0) > 0 and (str(u.get("uid", "")) == str(target) or str(u.get("name", "")).startswith(str(target))):
                        picked = u
                        break
                if picked is None and target not in (None, ""):
                    self._target_not_found = str(target)
            if picked is not None and int(picked.get("rank", 1) or 1) > attacker["reach"]:
                # 射程校验（审计 P1 修复）：目标在攻击范围外 → 拒绝（提示 + 不消耗回合）
                self._active_target = None
                self._target_out_of_range = True
                return None
            if picked is None:
                picked = select_target(attacker, self.enemies)
        self._active_target = picked
        return picked

    def _resolve_ally_target(self, target) -> dict | None:
        """v122 治疗指定队友：b<序号>（v127.3 编号）或 uid 精确或名字前缀匹配（存活）。
        allies 为空（单人战斗）或找不到 → None。b1 在 allies 空时=None=治疗自己。"""
        import re as _re
        if not target or not self.allies:
            return None
        _m = _re.match(r"^b(\d+)$", str(target).strip().lower())
        if _m:
            _n = int(_m.group(1))
            from .core.formation import numbered_units
            _numed = numbered_units(self.allies)
            if 1 <= _n <= len(_numed):
                return _numed[_n - 1][1]
            return None
        for u in self.allies:
            if u.get("hp", 0) > 0 and (
                    str(u.get("uid", "")) == str(target)
                    or str(u.get("name", "")).startswith(str(target))):
                return u
        return None

    def _player_charge_release(self, player: dict, logs: list) -> bool:
        """蓄力回合开始结算：left 递增计时，归零自动释放技能。返回是否已释放。"""
        if not self.charging or not self.charging.get("skill"):
            self.charging = None
            return False
        left = int(self.charging.get("left", 1) or 1)
        cname = self.charging.get("name", self.charging.get("skill", "?"))
        if left > 0:
            self.charging["left"] = max(0, left - 1)
            if self.charging["left"] == 0:
                # 归零 → 自动结算技能效果（不重复扣 MP/资源）
                skill_name = self.charging["skill"]
                self.charging = None
                logs.append(f"✨ 【{cname}】蓄力完成，轰然落下！")
                self._releasing_charge = True
                try:
                    self._do_player_skill(skill_name, player)
                finally:
                    self._releasing_charge = False
                return True
            else:
                logs.append(f"⏳ 你正在蓄力【{cname}】(剩 {self.charging['left']} 回合)，本回合无法普攻/技能！")
        return False

    def _player_charging_blocked(self, logs: list, action: str) -> bool:
        """蓄力期间非防御/道具行动 → 拦截（提示剩余回合），返回是否被拦截。"""
        if not (self.charging and self.charging.get("skill")):
            return False
        if action in ("defend", "use_item", "flee"):
            return False
        cname = self.charging.get("name", self.charging.get("skill", "?"))
        left = int(self.charging.get("left", 1) or 1)
        logs.append(f"⏳ 你正在蓄力【{cname}】(剩 {left} 回合)！可『防御』或『使用 <道具>』")
        return True

    def _interrupt_charging(self, unit, logs, source="敌人"):
        """打断单位蓄力（主动伤害/被控）。玩家侧返还 50% 已扣 MP（向上取整）。"""
        ch = unit.get("charging")
        if not ch:
            return
        ustr = unit.get("name") or "目标"
        unit["charging"] = None
        logs.append(f"🔨 【{ustr}】的蓄力被{source}打断了！")
        # 玩家侧返还 50% 已扣 MP（§6.2规则4；敌方不返还）
        if unit.get("side") == "ally":
            # 蓄力花费记录在 charging 上（施放时已扣，打断按 half 返还）
            spent = int(ch.get("mp_spent", 0) or 0)
            if spent > 0:
                unit["mp"] = min(unit.get("max_mp", unit.get("mp", 0)),
                                 unit.get("mp", 0) + (spent + 1) // 2)
                logs.append(f"✨ 返还了 {(spent + 1) // 2} 点魔力。")

    # ---------------- 玩家行动入口 ----------------
    def player_turn(self, action: str, skill_name: str | None, player: dict, enemy_act: bool = True, target=None) -> tuple:
        """执行玩家行动。返回 (日志列表, 是否结束)
        action: attack | skill | defend | flee | use_item
        player: 玩家 dict（战斗内会修改 hp/mp，由调用方负责存库）
        enemy_act: 是否在玩家行动后立即结算敌方回合（PVP 传 False，由对方真人操作）
        target: v2 指定目标（uid 或名字前缀，None=自动选择）
        v121：CTB 行动时间轴——玩家正常行动 +1 回合；行动后玩家 ct += cost，
        其余敌方单位 ct -= cost，随后进入敌方行动段（敌方连动由 _enemy_phase 判定）。
        不再有额外行动 / 先手概念，快 = 更频繁轮到行动。
        """
        logs = []
        # v95.19: 战斗内上限统一实时值——覆盖 from_state 恢复的战斗（恢复时不传 player，
        # __init__ 刷新不到；DB max_hp/max_mp 换装备后过时，会导致战斗内上限与面板不一致）
        try:
            _st = self._player_stats(player)
            player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
            player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
        except Exception:
            pass
        # v63 玩家被沉默：技能类行动先被拦截转普攻（置于 O118 校验前，避免未学习技能
        # 在沉默下先被拦截而无法转普攻）；后续沉默状态下只能普攻/防御/道具
        if "silence" in self.p_buffs and action == "skill":
            logs.append("🤐 你被沉默，无法使用技能！(只能普攻/防御/道具)")
            action = "attack"

        # O118 技能施放失败保护：正常回合开始前先校验（技能不存在/未学习/冷却/蓝/
        # 核心资源不足），失败不消耗回合、不结算敌方行动，玩家可重新选择其他行动
        if action == "skill":
            _fl, _blocked = self._skill_cast_blocked(skill_name, player)
            if _blocked:
                _fl.append("技能施放失败！可选择其他行动")
                return logs + _fl, False

        # ---- 正常回合开始 ----
        self.round += 1
        # v116.1 pv_broken：玩家本回合是否用过技能（供敌方 _boss_mech 反扑判定）——回合开始复位
        self._player_recent_skill = False
        # v2 蓄力：回合开始结算——归零自动释放技能（§6.2）
        self._player_charge_release(player, logs)
        logs += self._turn_start(player)
        # v101.28 食物持续恢复：正常回合开始结算 hot（每回合一次，含眩晕/冻结回合）
        if self.p_hot and self.p_hot.get("turns", 0) > 0:
            logs += self._apply_hot(player)
        # 24 章宠物技能：回合开始自动触发（宠物击杀直接胜利）
        if self.pet:
            logs = self._pet_skill_turn(player, logs)
            if self.result == "victory":
                self._end_round()
                return logs, True
        # v63 玩家被控：眩晕/冻结 → 跳过本回合行动（CTB 下行动浪费，玩家 ct 照走，随后敌方行动段）
        # v121 审计修复：统一走 _after_actor_ct("p")——被控也是"玩家行动消耗"，
        # 敌方应同步时间流逝（与蓄力等待/防御等路径一致），避免被控方反而配速占优
        if "stun" in self.p_buffs:
            logs.append("🌀 你被眩晕，无法行动！")
            self.p_buffs.pop("stun", None)
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            return self._enemy_phase(player, logs, enemy_act)
        if "freeze" in self.p_buffs:
            logs.append("❄️ 你被冻结，无法行动！")
            self.p_buffs.pop("freeze", None)
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            return self._enemy_phase(player, logs, enemy_act)

        # v2 蓄力期间：普攻/技能被拦截（可防御/道具），敌方照常行动
        if self._player_charging_blocked(logs, action):
            # v121 CTB：蓄力等待也是玩家行动 → 玩家 ct 照走（PVP 不介入）
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            return self._enemy_phase(player, logs, enemy_act, defend=(action == "defend"))

        # v2 目标解析（攻击/技能指定的目标；其余行动重置为主目标）
        if action in ("attack", "skill"):
            # v122 治疗类技能：目标=队友（由 _do_player_skill 解析），不解析敌人目标
            _is_heal = False
            if action == "skill" and skill_name:
                _info0 = E.skill_info(player.get("class_name", ""), skill_name)
                _is_heal = bool(_info0 and _info0.get("kind") == "治疗")
            if _is_heal:
                self._active_target = None
            else:
                self._target_out_of_range = False
                self._target_not_found = None
                self._resolve_player_target(player, target)
                if getattr(self, "_target_out_of_range", False):
                    # 射程校验拒绝（审计 P1 修复）：不消耗回合，玩家可重新选择
                    logs.append(f"⛔ 【{target}】在你的攻击范围之外，够不着！(近战只可及前排)")
                    return logs, False
                # v127.3：指定目标未找到 → 明确提示（不再静默回退自动选择）
                if getattr(self, "_target_not_found", None):
                    logs.append(f"⚠️ 没有找到目标『{self._target_not_found}』，攻击自动选择！(站位图编号：a1/a2… 敌方，b1/b2… 友方)")
                    self._target_not_found = None
        else:
            self._active_target = None

        if action == "defend":
            return self._do_defend(player, logs, enemy_act)
        if action == "flee":
            return self._do_flee(player, logs)
        if action == "use_item":
            logs += self._do_use_item(skill_name or "", player)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True
            # v121 CTB：使用道具也是玩家行动 → 玩家 ct 照走（PVP 不介入）
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            return self._enemy_phase(player, logs, enemy_act)

        st = self._player_stats(player)
        if action == "skill":
            logs += self._do_player_skill(skill_name, player, target=target)  # v122：target 传治疗队友目标
            # v116.1 pv_broken：记录玩家本回合用了技能，敌方 _boss_mech 据此决定反扑
            self._player_recent_skill = True
        else:
            logs += self._player_attack(st, player)

        if self._enemy_dead():
            self.result = "victory"
            self._end_round()
            return logs, True

        # v121 CTB：玩家行动完 → 玩家 ct += cost、其余敌方单位 ct -= cost（PVP 不介入）
        if self.btype != "pvp":
            self._after_actor_ct("p", player=player)

        # v107 召唤物自动攻击：玩家正常行动结束后、敌方行动前（每回合一次）
        if self.summons:
            logs = self._summons_act(player, logs)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True

        # 敌方行动段
        return self._enemy_phase(player, logs, enemy_act)

    def _enemy_phase(self, player: dict, logs: list, enemy_act: bool, defend: bool = False) -> tuple:
        """v121 CTB 敌方行动段：while 敌方存活单位中最小 ct < 玩家 ct → 该单位行动一次，
        行动后结算其 ct（自身 +cost、其余含玩家 -cost）；死亡单位即时移出候选（存活判定沿用 alive）。
        被控（stun/freeze）跳过的敌方单位行动后仍照常结算其 ct（行动被浪费）。
        defend=True 时敌方伤害减半。硬上限：单次玩家行动后敌方最多连动 8 次，超限 break。
        PVP（btype=="pvp"，或 enemy_act=False 由对方真人操作）不介入。"""
        if enemy_act and self.btype != "pvp":
            from .core.formation import alive_units
            _guard = 0  # 敌方连动硬上限（防极端配速死循环）
            while _guard < 8:
                alive = alive_units(self.enemies)
                if not alive or self._player_dead(player):
                    break
                min_e_ct = min(float(u.get("ct", 0) or 0) for u in alive)
                if min_e_ct >= self.p_ct:
                    break
                unit = min(alive, key=lambda u: float(u.get("ct", 0) or 0))
                mlogs, dmg = self._enemy_turn(player, unit)
                logs += mlogs
                if defend and dmg > 0:
                    dmg = max(1, int(dmg * DEFEND_REDUCE))
                    # O116 与伤害文案一起延迟输出（闪避时不显示）
                    self._pending_dmg_lines.append(f"(格挡后 {dmg} 点伤害)")
                self._damage_player(player, dmg, logs, source=unit.get("name", "敌人"))
                # 行动后结算该单位 ct（被控跳过同样结算 —— 行动被浪费）
                self._after_actor_ct("e", unit)
                if self._player_dead(player):
                    self.result = "defeat"
                _guard += 1
            self._active_target = None  # 敌方行动结束后重置玩家下次目标
        self._end_round()
        return logs, self.result is not None

    def _add_shield(self, key: str, value: int, turns: int = 3):
        """v101.28d 护盾 buff 化：同源叠加盾值 + 刷新回合（取 max），异源并存各计各的回合。
        v106.2 护盾强度：shield_power 属性 ×(1+shield_power)（cap 50%）"""
        if value <= 0:
            return
        try:
            _spv = min(float(self._player_stats(self.player).get("shield_power", 0) or 0), 0.5)
            if _spv > 0:
                value = int(value * (1 + _spv))
        except Exception:
            pass
        cur = self.p_shields.get(key)
        if cur:
            cur["value"] += value
            cur["turns"] = max(cur["turns"], turns)
        else:
            self.p_shields[key] = {"value": value, "turns": turns}

    def _do_use_item(self, payload: str, player: dict) -> list:
        """战斗中使用消耗品：恢复/增益(v61 抽公共，普通回合与额外行动共用)"""
        logs = []
        if payload.startswith("foodfx:"):
            # v101.28e 食物效果：foodfx:效果ID,效果ID（本场战斗有效，独立于装备词条）
            aids = [a for a in payload[7:].split(",") if a]
            for a in aids:
                if a not in self.p_food_effects:
                    self.p_food_effects.append(a)
            # 护盾效果特判：立即获得 10% 生命护盾（3 回合）
            if "shield" in aids:
                self._add_shield("food_shield", int(player.get("max_hp", 100) * 0.10), 3)
            from .core.food_effects import FOOD_EFFECT_NAMES
            names = [FOOD_EFFECT_NAMES.get(a, a) for a in aids]
            logs.append(f"🍲 你吃下了料理，获得【{'、'.join(names)}】效果！(本场战斗)")
            return logs
        if payload.startswith("hot:"):
            # v101.28 食物持续恢复：hot:回血比例,回蓝比例,回合数（模板 tpl_food 生成）
            _p = payload[4:].split(",")
            hpct = float(_p[0]) if _p and _p[0] else 0.0
            mpct = float(_p[1]) if len(_p) > 1 and _p[1] else 0.0
            turns = int(_p[2]) if len(_p) > 2 and _p[2] else 3
            # v110 审计修复：hot 重复食用改「不叠加取高」（原后写覆盖——低值食物
            # 会顶掉高值恢复，与设计「不叠加取高」不符）
            _cur_hot = self.p_hot or {}
            self.p_hot = {"heal": max(hpct, float(_cur_hot.get("heal", 0) or 0)),
                          "mana": max(mpct, float(_cur_hot.get("mana", 0) or 0)),
                          "turns": max(turns, int(_cur_hot.get("turns", 0) or 0))}
            _desc = []
            if hpct > 0:
                _desc.append(f"每回合恢复 {int(hpct * 100)}% 生命")
            if mpct > 0:
                _desc.append(f"每回合恢复 {int(mpct * 100)}% 魔力")
            logs.append(f"🍲 你吃下了食物，{('、'.join(_desc))}！({turns} 回合)")
            return logs
        if payload.startswith("mana:"):
            # v101.27：魔力药水战斗内回显数字（tpl_mana payload="mana:N"）
            mv = int(payload[5:])
            before = player["mp"]
            player["mp"] = min(player.get("max_mp", player["mp"]), player["mp"] + mv)
            logs.append(f"💙 你使用了战斗道具，恢复 {player['mp'] - before} 点魔力！({player['mp']}/{player.get('max_mp', '?')})")
            return logs
        if payload.startswith("hm:"):
            # v104R3 M16 P2-3：复合药水（heal+mana）战斗内双恢复（tpl_heal_mana payload="hm:hp,mp"）
            _p = payload[3:].split(",")
            hv = int(_p[0]) if _p and _p[0] else 0
            mv = int(_p[1]) if len(_p) > 1 and _p[1] else 0
            msgs = []
            if hv > 0:
                before = player["hp"]
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + hv)
                msgs.append(f"恢复 {player['hp'] - before} 点生命")
            if mv > 0:
                before = player["mp"]
                player["mp"] = min(player.get("max_mp", player["mp"]), player["mp"] + mv)
                msgs.append(f"恢复 {player['mp'] - before} 点魔力")
            logs.append(f"💊 你使用了战斗道具，{'、'.join(msgs)}！")
            return logs
        if payload.startswith("special:"):
            # v101.28f 药水特殊效果（next_atk_up/heal_up/magic_resist/thorns_pot/dodge_pot/cc_immune/execute_pot/def_down/shield）
            # v125.1 P2-1：分发下沉 POTION_EFFECTS 注册表（game/core/potion_effects.py），数值读 items.py effect_data
            # v130.2：资源联动药水 effect_data 数值随 payload 传递（special:<kind>:<json>，
            # item_templates _make_buff_tpl 注入）→ 解析出 value 传入 handler（旧药水无数据保持 None 走 DEFAULTS）
            kind = payload[8:]
            value = None
            if ":" in kind:
                _k, _, _j = kind.partition(":")
                try:
                    import json as _json
                    _d = _json.loads(_j)
                    if isinstance(_d, dict) and _d:
                        value = _d
                        kind = _k
                except Exception:
                    pass
            return self._apply_potion_special(kind, player, logs, value)
        if payload.startswith("buff:"):
            # v54 战斗药水：effect → p_buffs 增益 3 回合
            # 9.3：支持逗号分隔复合 buff（如龙涎药剂 buff:atk_up,def_up）
            kind = payload[5:]
            _cn = {"atk_up": "攻击", "def_up": "防御", "spd_up": "速度", "crit_up": "暴击",
                   "matk_up_pot": "魔攻",
                   "food_atk_up": "攻击", "food_def_up": "防御", "food_spd_up": "速度",
                   "food_spd_up_small": "速度",
                   "food_crit_up": "暴击", "food_matk_up": "魔攻",
                   # v101.28f 药水强度分档
                   "atk_up_big": "攻击", "atk_up_small": "攻击", "spd_up_small": "速度",
                   "crit_up_small": "暴击", "crit_up_big": "暴击",
                   "matk_up": "魔攻", "matk_up_strong": "魔攻"}
            for _k in kind.split(","):
                self.p_buffs[_k] = max(self.p_buffs.get(_k, 0), 3)
            _names = '、'.join(_cn.get(k, k) for k in kind.split(','))
            # v101.28b 食物 buff（food_ 前缀键）播报区分：料理 vs 药水
            if any(k.startswith("food_") for k in kind.split(",")):
                logs.append(f"🍖 你吃下了料理，{_names}提升！(3 回合)")
            else:
                logs.append(f"🧪 你饮下战斗药水，{_names}大幅提升！(3 回合)")
        else:
            heal = int(payload or 0)  # 复用 skill_name 传恢复量
            # 阶段九：半身人灵巧双手——消耗品效果 +10%
            rr = E.race_stats(player.get("race")).get("item_effect")
            if rr:
                heal = max(1, int(heal * (1 + rr)))
            if heal > 0:
                before = player["hp"]
                player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                logs.append(f"💊 你使用了战斗道具，恢复 {player['hp'] - before} 点生命！({player['hp']}/{player['max_hp']})")
            else:
                logs.append("💊 你使用了战斗道具！")
        return logs

    def _apply_potion_special(self, kind: str, player: dict, logs: list, value=None) -> list:
        """v101.28f 药水特殊效果分发（非属性 buff 类，3 回合制；next_atk_up 一次性）。

        v125.1 P2-1：改查 POTION_EFFECTS 注册表（game/core/potion_effects.py），
        数值由 items.py 药水条目 effect_data 提供（注册表 DEFAULTS 扫描自数据层）。
        新增药水效果 = items.py 加 effect/effect_data + potion_effects.py register 函数。
        v130.2：value = 物品级 effect_data（由 special payload special:<kind>:<json> 解析传入）；
        None（旧特殊药水）→ 走注册表 DEFAULTS（数据层单一权威）。
        """
        from .core.potion_effects import POTION_EFFECTS  # 延迟导入（core 聚合链惯例）
        eff = POTION_EFFECTS.get(kind)
        if not eff:
            logs.append("🧪 你饮下了药剂！")
            return logs
        msg = eff(self, player, value)
        if msg:
            logs.append(msg)
        return logs

    def _apply_hot(self, player: dict) -> list:
        """v101.28 食物持续恢复：每回合开始结算（回血/回蓝，回合数递减）。"""
        h = self.p_hot
        logs = []
        max_hp = player.get("max_hp", player.get("hp", 100))
        max_mp = player.get("max_mp", player.get("mp", 100))
        if h.get("heal"):
            gain = int(max_hp * h["heal"])
            if gain > 0:
                before = player.get("hp", 0)
                player["hp"] = min(max_hp, before + gain)
                logs.append(f"🍲 持续恢复生效，恢复 {player['hp'] - before} 点生命！({player['hp']}/{max_hp})")
        if h.get("mana"):
            gain = int(max_mp * h["mana"])
            if gain > 0:
                before = player.get("mp", 0)
                player["mp"] = min(max_mp, before + gain)
                logs.append(f"🍲 持续恢复生效，恢复 {player['mp'] - before} 点魔力！({player['mp']}/{max_mp})")
        h["turns"] -= 1
        if h["turns"] <= 0:
            self.p_hot = {}
        else:
            logs.append(f"（剩余 {h['turns']} 回合）")
        return logs

    def _skill_cast_blocked(self, skill_name: str, player: dict) -> tuple:
        """O118 技能施放前置校验（无副作用，不扣资源/蓝）：技能不存在/未学习/冷却中/
        蓝不足/核心资源不足 → 返回 (日志列表, True)。
        拦截时玩家回合不开始、敌方不行动，玩家可重新选择其他行动。
        与 _do_player_skill 的校验口径保持一致（那里负责真正扣除消耗）。"""
        logs = []
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            logs.append(f"没有技能『{skill_name}』！")
            return logs, True
        if not E.is_skill_learned(player["class_name"], player["level"], skill_name,
                                  player.get("learned_skills", [])):
            logs.append(f"该技能需要 Lv.{info['lv']} 才能使用，你才 Lv.{player['level']}(或『技能学习 {skill_name}』提前学习)")
            return logs, True
        # v2.0 冷却：CD 未结束拦截（强控/终结技等）
        if self._skill_on_cd(skill_name):
            left = self._skill_cd_left(skill_name)
            logs.append(f"⏳【{skill_name}】还在冷却中(剩余 {left} 回合)！")
            return logs, True
        if player["mp"] < info["mp"]:
            logs.append("💙 魔力不足！")
            return logs, True
        # v2.0 核心资源：『消耗全部』终结技（consume_all）至少需 1 点
        consume_all = info.get("consume_all") or {}
        if consume_all:
            ck = consume_all.get("key", "")
            if self._res_read(ck) < 1:
                rd = E.core_resource_def(player["class_name"])
                rname = (E.core_resource_def_by_key(ck) or rd or {}).get("name", ck)
                logs.append(f"⚡ {rname}不足！需要至少 1 点，当前 0(『攻击』攒资源)")
                return logs, True
        else:
            # 普通 res_cost：逐资源校验（纯检查，不扣除）——consume_all 分支处理完不再落入（双声明技能 P1-2）
            res_cost = info.get("res_cost") or {}
            for rk, rv in res_cost.items():
                rd = E.core_resource_def(player["class_name"])
                if not rd and not E.core_resource_def_by_key(rk):
                    continue
                k = rk or (rd or {}).get("key", "")
                _rv = int(rv or 0)
                # v130.2 R1：精力消耗统一折算（词条精力刀刃 + 套装猎首），与扣减同源（P1-1）
                if rk == "energy":
                    _rv = self._energy_cost_reduce(player, info, _rv)
                if self._res_read(k) < _rv:
                    rname = (E.core_resource_def_by_key(k) or rd or {}).get("name", k)
                    cur = self._res_read(k)
                    logs.append(f"⚡ {rname}不足！需要 {_rv}，当前 {cur}(『攻击』攒资源)")
                    return logs, True
        return logs, False

    def _do_player_skill(self, skill_name: str, player: dict, target=None) -> list:
        """玩家施放技能(v61 抽公共，普通回合与额外行动共用)"""
        logs = []
        st = self._player_stats(player)
        info = E.skill_info(player["class_name"], skill_name)
        if not info:
            logs.append(f"没有技能『{skill_name}』！")
            return logs
        if not E.is_skill_learned(player["class_name"], player["level"], skill_name,
                                  player.get("learned_skills", [])):
            logs.append(f"该技能需要 Lv.{info['lv']} 才能使用，你才 Lv.{player['level']}(或『技能学习 {skill_name}』提前学习)")
            return logs
        # v2.0 冷却：CD 未结束拦截（强控/终结技等）——蓄力释放跳过（施放时已入 CD，§6.2）
        _releasing = bool(getattr(self, "_releasing_charge", False))
        if not _releasing and self._skill_on_cd(skill_name):
            left = self._skill_cd_left(skill_name)
            logs.append(f"⏳【{skill_name}】还在冷却中(剩余 {left} 回合)！")
            return logs
        # v2.0 核心资源：技能消耗检查（res_cost，如怒气/连击点/信仰/气）
        # v104 R3 P1-4 修复：先验蓝再扣资源（原实现先扣 res_cost 后查 mp，蓝不足时怒气/连击点白扣）
        if not _releasing and player["mp"] < info["mp"]:
            logs.append("💙 魔力不足！")
            return logs
        # v130.2 P1-4：施放前核心资源快照（满弦判定 / 隐藏线每层加成读「施放时持有值」而非扣费后值）——
        # 满弦语义=「施放时精力≥80」，扣费后精力永低于满档导致高耗档永不触发；龙力/禅意每层加成因
        # 消耗型金技扣费后归 0 无法按层放大的同病。后续消费点读 self._pre_cost_res（未命中回落当前值）。
        self._pre_cost_res = dict(self.resources)
        # v104 R3 P1-6：『消耗全部』终结技（consume_all）动态结算——资源不满也可施放，扣光该资源。
        # v130.2 统一公式：动态威力 = 数据表 power × (1 + per×当前持有值)——满资源时恰为策划案 EQ 基准
        # （破晓之拳 2.4×(1+0.1×10)=4.8、元素湮灭 2.4×(1+0.2×5)=4.8；per=0 则威力恒为数据表 power，
        # 仅作全耗门槛，如暗影处刑 3.2×1.0×cond1.5=EQ4.8）。旧式 1+per×cur 丢弃基础 power，
        # 与 v130.2 技能数据/desc 口径不符（暗影处刑满点 3.0×1.5=4.5≠4.8、破晓之拳满 10 气 2.0≠4.8）。
        consume_all = info.get("consume_all") or {}
        if consume_all:
            ck = consume_all.get("key", "")
            cur = self._res_read(ck)
            if cur < 1:
                rd = E.core_resource_def(player["class_name"])
                rname = (E.core_resource_def_by_key(ck) or rd or {}).get("name", ck)
                logs.append(f"⚡ {rname}不足！需要至少 1 点，当前 0(『攻击』攒资源)")
                return logs
            info = dict(info)
            info["power"] = round(float(info.get("power", 0.0) or 0.0)
                                  * (1.0 + float(consume_all.get("per", 0.0) or 0.0) * cur), 3)
            # v130.2c 套装全耗减免（保留残点走轴，最低消耗 1）：
            # 元素使徒 4 件（全耗奥义充能消耗 -1，-5→-4）/ 余烬军团徽章 4 件（满怒大招怒气消耗 -1）
            _left = 0
            # v130.2 R1：全耗减免「留 1 点」读套装 effect.value（元素使徒 value=1；余烬军团读 rage_cost_reduce 兼容）
            if ck == "element":
                _ue = self._set_eff(player, "ultimate_cost_reduce", 4, res="element")
                if _ue:
                    _left = int(_ue.get("value", 1) or 1)
            elif ck == "rage" and self._rage_full(player):
                _frp = self._set_eff(player, "full_rage_pursuit", 4)
                if _frp:
                    _left = int(_frp.get("value", _frp.get("rage_cost_reduce", 1)) or 1)
            if ck == "element":
                self.resources["element_charge"] = _left
            else:
                self.resources[ck] = _left
        else:
            res_cost = info.get("res_cost") or {}
            if res_cost and not _releasing:  # 蓄力释放跳过资源扣减（施放时已扣）
                for rk, rv in res_cost.items():
                    _rv = int(rv or 0)
                    # v130.2 R1：精力消耗统一折算（词条精力刀刃 + 套装猎首）——与预检 _skill_cast_blocked 同源
                    if rk == "energy":
                        _rv = self._energy_cost_reduce(player, info, _rv)
                    if not self._res_spend(rk, _rv):
                        rd = E.core_resource_def(player["class_name"])
                        rname = (E.core_resource_def_by_key(rk) or rd or {}).get("name", rk)
                        cur = self._res_read(rk)
                        logs.append(f"⚡ {rname}不足！需要 {rv}，当前 {cur}(『攻击』攒资源)")
                        return logs
        # v122 治疗指定队友：指定的队友不存在 → 拦截（不扣资源、不消耗回合）；
        # 单人战斗（无 allies）忽略目标，按治疗自己处理
        if info.get("kind") == "治疗" and target and self.allies:
            if self._resolve_ally_target(target) is None:
                logs.append(f"队伍里没有『{target}』～(副本中『技能 <名称> <队友名>』可指定治疗目标)")
                return logs
        # v34 符文·聚能：MP 消耗 -x%
        mana_lvl = self._enchant_lvl(self._enchant_effects(player), "mana_flow")
        mp_cost = info["mp"]
        if mana_lvl:
            mp_cost = max(1, int(mp_cost * (1 - C.rune_value("mana_flow", mana_lvl))))
        # v130.2 元素亲和药剂（mana_cost_down）：技能魔力消耗 ×(1-pct)（与符文乘算叠加）
        if self.p_buffs.get("mana_cost_down"):
            _mcd = float((self.p_eff or {}).get("mana_cost_down", 0) or 0)
            if _mcd > 0:
                mp_cost = max(1, int(mp_cost * (1 - _mcd)))
        # v130.2c 消耗减免词条：凝神塑能（元素/奥术技能蓝耗 -10%）/ 圣徽之佑（神迹技蓝耗 -5/史诗 -10）
        _mp_red = self._mp_cost_reduce(player, info)
        if _mp_red:
            mp_cost = max(1, mp_cost - _mp_red)
        if not _releasing:  # 蓄力释放跳过 MP 扣减（施放时已扣，§6.2）
            player["mp"] -= mp_cost
        # v2 蓄力技能（§6）：施放扣 MP/资源 → 进入蓄力，本回合不结算技能效果
        if not getattr(self, "_releasing_charge", False) and int(info.get("charge", 0) or 0) >= 1:
            cname = info.get("name") or skill_name
            self.charging = {"skill": skill_name, "left": int(info["charge"]),
                             "name": cname, "mp_spent": mp_cost}
            logs.append(f"✨ 你开始蓄力【{cname}】，需要 {int(info['charge'])} 回合！")
            # 冷却照常进入（§6.2 施放即冷却）
            cd = info.get("cd", 0)
            if cd:
                self._set_skill_cd(skill_name, cd)
            return logs
        logs += self._player_skill(st, skill_name, info, player, target=target)  # v122：target 传治疗队友目标
        # v130.2c 圣典·日冕 2 件：施放二档以上神迹 → 全体队友额外恢复 30 体力
        self._set_miracle_team_heal(player, info, logs)
        # v2.0 冷却：技能表 cd 字段（回合），施放后进入冷却
        cd = info.get("cd", 0)
        if cd:
            self._set_skill_cd(skill_name, cd)
        return logs

    # ---------------- 防御 / 逃跑 ----------------
    def _do_defend(self, player: dict, logs: list, enemy_act: bool = True) -> tuple:
        logs.append("🛡️ 你架起防御姿态，受到的伤害减半！")
        self.p_defending = True
        # v121 CTB：防御也是玩家行动 → 玩家 ct 照走；敌方段统一走 _enemy_phase 的 ct 判定
        # （defend=True 时 _enemy_phase 内每个敌方单位伤害减半），PVP 不介入
        if enemy_act and self.btype != "pvp":
            self._after_actor_ct("p", player=player)
            return self._enemy_phase(player, logs, enemy_act, defend=True)
        self._end_round()
        return logs, self.result is not None

    def _do_flee(self, player: dict, logs: list) -> tuple:
        if self.btype in ("worldboss", "pvp"):
            logs.append("💨 这里无法逃跑！背水一战吧！")
            if self.btype == "pvp":
                # PVP：不触发 AI 反击，等对方真人行动
                return logs, False
            # v121 CTB：逃跑失败也被敌方追击 → 玩家 ct 照走，敌方段按 ct 判定
            self._after_actor_ct("p", player=player)
            return self._enemy_phase(player, logs, True)
        if random.random() < C.FLEE_CHANCE:
            logs.append("💨 你成功脱离了战斗！")
            self.result = "fled"
            return logs, True
        logs.append("💨 逃跑失败！被追上了！(可以再『逃跑』，或『防御』『用药』撑住)" )
        # v121 CTB：逃跑也是玩家行动 → 玩家 ct 照走（PVP 不介入），敌方段按 ct 判定
        if self.btype != "pvp":
            self._after_actor_ct("p", player=player)
        return self._enemy_phase(player, logs, True)

    # ---------------- 玩家行动结算 ----------------
    def _enchant_effects(self, player: dict) -> dict:
        """v34：读取玩家已装备符文效果 → {effect: 最高等级}"""
        effects = {}
        for slot, item in (player.get("equipment") or {}).items():
            if not item:
                continue
            for en in item.get("enchant", []):
                if en.get("effect"):
                    lvl = int(en.get("lvl", 1) or 1)
                    effects[en["effect"]] = max(effects.get(en["effect"], 0), lvl)
        return effects

    def _enchant_lvl(self, effs: dict, effect: str) -> int:
        """符文效果等级(无则 0)"""
        return int(effs.get(effect, 0) or 0)

    def _player_stats(self, player: dict) -> dict:
        st = E.player_final_stats(player.get("class_name", "战士"), player.get("level", 1),
                                  player.get("equipment", {}),
                                  player.get("class_tier", 0),
                                  player.get("attributes"),
                                  player.get("evolve_path", 0),
                                  getattr(self, "title_bonus", None) or {},
                                  player.get("race"))
        st = self._apply_buffs(st, self.p_buffs)
        # v104 M23 神龛祝福：持久 buff（stat ×1.10，5 次战斗），战斗开始时已消费 1 次
        _pb = getattr(self, "poi_buff", None)
        if _pb and _pb.get("stat") in st:
            st[_pb["stat"]] = int(st.get(_pb["stat"], 0) * float(_pb.get("mult", 1.10)))
        # #245: 玩家减速生效（与 _enemy_stats 的 spd_down 处理对称）——此前 p_buffs["spd_down"]
        # 只被挂载从未应用，减速玩家仍按原速度先手/触发速度优势
        if "spd_down" in self.p_buffs:
            st["spd"] = int(st.get("spd", 0) * SPD_DOWN_MULT)
        # v33/v34 符文属性：疾风(速度+) / 铁壁(防御+)
        effs = self._enchant_effects(player)
        if self._enchant_lvl(effs, "swift"):
            st["spd"] = int(st.get("spd", 0) * (1 + C.rune_value("swift", effs["swift"])))
        if self._enchant_lvl(effs, "ironwall"):
            st["def"] = int(st.get("def", 0) * (1 + C.rune_value("ironwall", effs["ironwall"])))
        # v64 被动属性：魔力涌动/风行步/疾影/鹰眼（百分比属性被动）
        pb = E.player_passive_stats(player.get("class_name", "战士"), player.get("learned_skills", []))
        if pb.get("mp_mult", 1.0) != 1.0:
            st["max_mp"] = int(st.get("max_mp", 0) * pb["mp_mult"])
            st["mp"] = int(st.get("mp", 0) * pb["mp_mult"])
        if pb.get("spd_mult", 1.0) != 1.0:
            st["spd"] = int(st.get("spd", 0) * pb["spd_mult"])
        if pb.get("crit_add", 0.0):
            # v110 §三：暴击率上限统一 0.5（PCT_CAPS 权威；原 0.6 与 buff 1.0 不一致）
            st["crit"] = min(st.get("crit", 0) + pb["crit_add"], C.PCT_CAPS.get("crit", 0.5))
        # v106.1 冷却缩减被动（cdr_add → st["cdr"]，cap 40%）
        if pb.get("cdr_add", 0.0):
            st["cdr"] = min(st.get("cdr", 0) + pb["cdr_add"], 0.4)
        # v106.2 穿透被动（pene_phys_add/pene_magi_add → 乘算合成，与词条一致）
        if pb.get("pene_phys_add", 0.0):
            st["pene_phys"] = min(1 - (1 - st.get("pene_phys", 0)) * (1 - pb["pene_phys_add"]), 0.6)
        if pb.get("pene_magi_add", 0.0):
            st["pene_magi"] = min(1 - (1 - st.get("pene_magi", 0)) * (1 - pb["pene_magi_add"]), 0.6)
        # v106.3 吸血/暴击伤害/格挡被动（加法并入属性，cap 由聚合层）
        for _pk, _pv in (("lifesteal_add", "lifesteal"), ("crit_dmg_add", "crit_dmg"),
                         ("block_add", "block")):
            if pb.get(_pk, 0.0):
                st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
        # v106.4 反伤/物魔免/物法吸被动（加法并入属性）
        for _pk, _pv in (("thorns_add", "thorns"), ("phys_reduce_add", "phys_reduce"),
                         ("magic_reduce_add", "magic_reduce"),
                         ("lifesteal_phys_add", "lifesteal_phys"),
                         ("lifesteal_magi_add", "lifesteal_magi")):
            if pb.get(_pk, 0.0):
                st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
        # v109 P0-2：隐藏职业被动并入补全（龙魂/星辰之力/万兽之力等 lv62 被动此前完全无效）
        for _pk, _pv in (("heal_power_add", "heal_power"), ("shield_power_add", "shield_power"),
                         ("elem_res_add", "elem_res"), ("abyss_res_add", "abyss_res"),
                         ("luck_add", "luck"), ("summon_power_add", "summon_power"),
                         ("dodge_add", "dodge")):  # v113.1：游侠觉醒被动「风之加护」闪避并入
            if pb.get(_pk, 0.0):
                st[_pv] = min(st.get(_pv, 0) + pb[_pk], C.PCT_CAPS.get(_pv, 0.6))
        # v104 R3 P1-1：条件属性被动战斗内结算（12 章 §12.2：战意高涨/战争咆哮/死战/厚土）
        # engine.py 面板只结算无 cond 属性，条件型（rage>=5/hp 阈值/battle_start）在此按战场状态动态生效
        # v1.x：条件判定改查 PASSIVE_COND_CHECKS 注册表（原 if/elif 硬编码）
        pm = self._passive_map(player)
        for _pn, _ps in pm.get("stat", []):
            _st = _ps.get("stat")
            # v1.x：条件判定改查 PASSIVE_COND_CHECKS 注册表（原 if/elif 硬编码）；
            # 仅消费 PASSIVE_COND_STAT_KEYS 白名单内条件（dual_stat/hp_low_30 由其它站点消费）
            if _ps.get("cond") in PASSIVE_COND_STAT_KEYS \
                    and passive_cond_ok(self, player, _ps, default=False) \
                    and _st in ("atk", "def", "matk", "mdef"):
                st[_st] = int(st.get(_st, 0) * (1 + float(_ps.get("mult", 0))))
        return st

    def _passive_map(self, player: dict) -> dict:
        """v104 R3 P1-1：已学被动按 proc/stat 聚合（数据驱动，替代名字硬匹配）。
        返回 {\"proc\": {proc名: [(被动名, passive字段), ...]}, \"stat\": [(被动名, passive字段), ...]}"""
        out = {"proc": {}, "stat": []}
        cls = player.get("class_name", "")
        for ps_name in E.passive_skills_learned(cls, player.get("learned_skills", [])):
            info = E.skill_info(cls, ps_name)
            ps = (info or {}).get("passive") or {}
            if ps.get("proc"):
                out["proc"].setdefault(ps["proc"], []).append((ps_name, ps))
            elif ps.get("stat"):
                out["stat"].append((ps_name, ps))
        return out

    def _player_attack(self, st: dict, player: dict) -> list:
        """普攻(含标记加成 + v10 套装攻击特效 + v34 符文效果)"""
        logs = []
        est = self._enemy_stats()
        effs = self._enchant_effects(player)
        # v34 破甲：无视 x% 防御（按等级）
        ap_lvl = self._enchant_lvl(effs, "armor_pierce")
        if ap_lvl:
            est = dict(est)
            est["def"] = int(est["def"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
        # v109.2 P1-1 运势：幸运转化为暴击补充（luck → crit，上限 +12%）；PVP 对方韧性对称生效
        # v130.2c 巡林长披风：命中带标记目标 暴击率 +5%（crit_on_marked）
        is_crit = random.random() < (st["crit"] + min(float(st.get("luck", 0) or 0) * 0.3, 0.12) + self._set_crit_bonus(player)) * self._tenacity_mult(est)
        # v109.2 P1-1 运势：暴击命中后 30% 概率追加 50% 伤害（幸运一击）
        lucky = is_crit and random.random() < 0.30
        # v106 穿透：玩家物穿/固定物穿削减怪物有效防御
        _pp, _pf = self._pene_vals(st)
        # v107 伤害类型四层架构：普攻显式声明 phys（物理段，吃 def/物免/格挡/物吸）
        dmg = E.calc_damage(st["atk"], est["def"], is_crit, pene_pct=_pp, pene_flat=_pf, dmg_type="phys")
        if lucky:
            dmg = int(dmg * 1.5)
            logs.append("✨ 幸运一击！暴击伤害额外提升 50%！")
        # v109.2 P3-4：魔能涌动对普攻生效（魔剑士附魔普攻→magi 段；原只在技能端消费，普攻浪费 buff）
        if self.p_buffs.get("spellblade_surge"):
            _pp_magi, _pf_magi = self._pene_vals(st, magic=True)
            surge_dmg = E.calc_damage(int(st["matk"] * 0.80), est["mdef"], is_crit,
                                      pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
            dmg += surge_dmg
            _magi_part = surge_dmg  # v110 P1-3：魔涌魔段记入（敌方魔免消费用）
            del self.p_buffs["spellblade_surge"]
            logs.append(f"🔮 魔能涌动：普攻附带 {surge_dmg} 点魔法伤害！")
        else:
            _magi_part = 0
        # 阶段八：装备被动词条伤害加成（处决/追猎/精准/龙语印记等）
        affix_mult, affix_tags = self._affix_dmg_mult(player)
        dmg = int(dmg * affix_mult)
        # 阶段九：种族攻击天赋（无畏/怯战 残血、龙之吐息 首击）
        race_mult, race_tags = self._race_attack_mult(player)
        dmg = int(dmg * race_mult)
        if race_tags:
            affix_tags = list(affix_tags) + race_tags
        # v130.2 拳师蓄势 Momentum（攻线·格斗士）：普攻为物理伤害，吃「每 1 气 +3%」持有加伤
        mom_mult = self._momentum_mult(player)
        if mom_mult != 1.0:
            dmg = int(dmg * mom_mult)
            affix_tags = list(affix_tags) + [f"🔥蓄势x{round(mom_mult, 2)}"]
        # v130.2 澎湃烈酒（phys_up，P0-5 消费端）：本场物理伤害 +pct%（p_eff 存 pct / p_buffs 存剩余回合）
        if self.p_buffs.get("phys_up"):
            _pu = float((self.p_eff or {}).get("phys_up", 0) or 0)
            if _pu > 0:
                dmg = int(dmg * (1 + _pu))
                affix_tags = list(affix_tags) + [f"🍺物理x{round(1 + _pu, 2)}"]
        # v130.2 引气精华（buff_phys_next，P0-2 消费端）：下一次物理攻击 +pct%（一次性，随即清；豁免回合递减）
        if self.p_buffs.get("buff_phys_next"):
            _bpn = float((self.p_eff or {}).get("buff_phys_next", 0) or 0)
            if _bpn > 0:
                dmg = int(dmg * (1 + _bpn))
                del self.p_buffs["buff_phys_next"]
                self.p_eff.pop("buff_phys_next", None)
                affix_tags = list(affix_tags) + [f"🥊引气x{round(1 + _bpn, 2)}"]
        # v34 残忍：暴击伤害 +x%（按等级，符文特效）
        brutal_lvl = self._enchant_lvl(effs, "brutal")
        if brutal_lvl and is_crit:
            dmg = int(dmg * (1 + C.rune_value("brutal", brutal_lvl)))
        # v106.3 暴击伤害属性（crit_dmg 面板化：词条折算 + 种族 + 被动 + 药水）
        cdmg = float(st.get("crit_dmg", 0) or 0)
        if self.p_buffs.get("crit_dmg_pot"):
            cdmg = 1 - (1 - cdmg) * (1 - 0.25)  # 狂暴药剂 +25% 暴伤（乘算并入）
        if is_crit and cdmg > 0:
            dmg = int(dmg * (1 + cdmg))
        dmg = self._apply_mark(dmg)
        dmg = self._boss_dmg_filter(dmg, player, logs)
        # v110 P1-3：玩家攻击端消费敌方防守属性（物免/格挡/魔免/元素抗；PVP 对称，PVE 怪无键=0 无感）
        dmg, _magi_part = self._enemy_mitigate(dmg, _magi_part, None, logs, kind="物理")
        # v105 怪物闪避：闪避成功跳过本次伤害结算/符文特效/词条触发/资源获取
        if not self._monster_dodge_check(logs):
            self._damage_enemy(dmg, logs)
            tag = " 💥暴击" if is_crit else ""
            if affix_tags:
                tag += " " + "·".join(affix_tags)
            logs.append(f"你{_basic_attack_verb(player)}，造成 {dmg} 点伤害！{tag}")
            # v130.2c 余烬军团徽章 4 件：满怒时 普攻二段追击（威力 30% → 50%；v130 无沸血二段机制，最小实现）
            _pse = self._set_eff(player, "full_rage_pursuit", 4)
            if _pse and self._rage_full(player):
                _pd = max(1, int(dmg * float(_pse.get("power", 0.50) or 0.50)))
                self._damage_enemy(_pd, logs)
                logs.append(f"🔥 沸血二段：满怒追击追加 {_pd} 点伤害！")
            # v106.3 吸血统一结算（属性化：词条/种族/被动/药水 → st["lifesteal"] 一处消费）
            # v110 审计修复：普攻魔涌（魔能涌动附魔）魔段拆分结算——物段走物吸、魔段走法吸，
            # 与 v109 P2-4 技能端分账（_player_skill）同款，补普攻端漏网
            _phys_part = dmg - _magi_part
            if _phys_part > 0:
                self._settle_lifesteal(player, _phys_part, logs)
            if _magi_part > 0:
                self._settle_lifesteal(player, _magi_part, logs, magic=True)
            # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱/破魔）
            self._apply_enchant_attack(effs, dmg, st, player, logs)
            # 阶段八：攻击命中后词条触发（流血/破甲/连击/元素附加等）
            self._affix_on_hit(player, dmg, logs)
            self._food_on_hit(player, dmg, logs)
            self._set_attack_proc(player, dmg, logs)
            # v130.2：刺客攻线·影舞者 连段计数——命中 +1（上限 10）
            if self._combo_active(player):
                new_combo = self._combo_add(player)
                logs.append(f"🌪️ 连段 {new_combo}/{COMBO_CFG['cap']}")
            # v2.0 核心资源：普攻获取（战士怒气/刺客连击点/拳师气）
            self._resource_on_attack(player, is_crit=is_crit)
            # v130.2c 资源词条：普攻命中（战意 on_attack / 残血灼薪 血量条件）+ 暴击命中（暴击蓄能/暴击回点）
            self._affix_res_proc(player, "on_attack", logs)
            if is_crit:
                self._affix_res_proc(player, "on_crit", logs)
            # v130.2 资源增幅：普攻出手命中（影袭药水 hits 制额外 +1 连击点等，P0-1 消费端）
            _amp_hit = self._amp_resource(player, "on_land_hit")
            if _amp_hit:
                logs.append(f"⚡ 影袭药剂：出手命中额外资源 +{_amp_hit}！")
        else:
            # v130.2：刺客攻线 落空 → 连段归零（断了重来）
            if self._combo_active(player):
                self._combo_break(player)
        return logs

    def _settle_lifesteal(self, player: dict, dmg: int, logs: list, magic: bool = False, dmg_type: str = "phys"):
        """v106.3 吸血统一结算（属性面板化）：heal = dmg × 吸血率

        来源全部汇聚到 st["lifesteal"]（通用，词条吸血/种族/被动/药水），
        v106.4 细分：物理吸血 lifesteal_phys（物理攻击段）、法术吸血 lifesteal_magi（魔法攻击段）
        与通用吸血乘算合成 1-(1-a)(1-b)；药水 buff 乘算并入，cap 30%。
        v107 真伤不吸血（纯真伤语义，鱼鱼拍板）：dmg_type == "true" 直接跳过。
        """
        if dmg <= 0 or dmg_type == "true":
            return
        st = self._player_stats(player)
        rate = float(st.get("lifesteal", 0) or 0)
        # v106.4：按伤害类型叠加细分吸血（乘算合成，不双算）
        sub_key = "lifesteal_magi" if magic else "lifesteal_phys"
        sub = float(st.get(sub_key, 0) or 0)
        if sub > 0:
            rate = 1 - (1 - rate) * (1 - sub)
        if self.p_buffs.get("lifesteal_pot"):
            rate = 1 - (1 - rate) * (1 - 0.15)  # 嗜血药剂 +15% 吸血（乘算并入）
        rate = min(rate, 0.30)
        # v1.3 重伤（mortal_wound）：目标被重创后吸血效果减半（Boss『重创』类技能施加）
        if self.p_buffs.get("mortal_wound"):
            rate *= 0.5
        if rate <= 0:
            return
        heal = int(dmg * rate)
        if heal <= 0:
            return
        player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
        logs.append(f"🩸 吸血：回复 {heal} 点生命！")

    def _resource_on_attack(self, player: dict, is_crit: bool = False):
        """v2.0 核心资源：普攻命中自动获取(on_attack)。
        v130.2：星语猎印「任意命中 +1」（on_hit 命中语义）+ 暴击额外 +1；
        暮影/刺客 on_crit 暴击攒点由 _on_crit_resource 统一结算。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        gain = rd.get("on_attack", 0)
        # v104 R3 P1-1：气力凝聚（气获取+1）/ 狂战之魂·气力之心（资源获取+1）被动加成
        pm = self._passive_map(player)
        for _pn, _ps in pm["stat"]:
            if _ps.get("stat") == "chi_gain" and k == "chi":
                gain += int(_ps.get("mult", 1))
        for _pn, _ps in pm["proc"].get("res_gain_bonus", []):
            if k in ("rage", "chi", "cp", "faith"):
                gain += 1
        # v104 R3 P1-1：神圣狂热——攻击获得信仰 +2（牧师攻击型分支）
        for _pn, _ps in pm["proc"].get("attack_res", []):
            if k == _ps.get("res", "faith") and _ps.get("gain"):
                gain += int(_ps.get("gain", 0))
        # v130.2 星语猎印：命中才攒——普攻命中再按 on_hit（任意命中追加）+1
        if cls in HUNT_MARK_ON_LAND_HIT and rd.get("on_hit"):
            gain += int(rd["on_hit"])
        if gain:
            self.resources[k] = self._res_gain_class(cls, k, gain)
        # v130.2 暴击命中结算挂点（on_crit：暮影影步 / 刺客攻线连击点 / 星语猎印暴击额外）
        if is_crit:
            self._on_crit_resource(player)

    def _resource_on_skill(self, player: dict, info: dict = None, logs: list | None = None):
        """v2.0 核心资源：技能命中获取（on_skill 或技能 res_gain 覆盖）。
        牧师治疗获取信仰（on_heal）。有 res_cost 的终结技不获取（消耗型）。
        v130.2：res_gain dict 支持副资源 key（歌者 {\"resonance\": N}、法师 {\"element\": N} 充能条）；
        星语猎印「任意命中 +1 追加」（come through on_hit）。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        # v130.2：元素法师充能条 / 攻线歌者双资源等，不一定以类主 key 为资源位——用分支激活资源集合
        act_keys = self._branch_keys(player)
        # 终结技（有 res_cost）默认不获取资源——除非技能自带 res_gain（消耗与获取并存）
        if info and info.get("res_cost") and info.get("res_gain") is None:
            return
        # 技能自带 res_gain 覆盖默认（如终结技 0 获取）。
        # res_gain 可为 int（常规）或 dict（按资源名取值，如林语印记 {\"energy\": 10}）。
        gain = 0
        if info and info.get("res_gain") is not None:
            rg = info["res_gain"]
            if isinstance(rg, dict):
                # v130.2 副资源 key：逐一结算到对应资源（歌者共鸣/法师充能条），未激活主键照常
                for rk, rv in rg.items():
                    amt = int(rv or 0)
                    if not amt:
                        continue
                    if rk in act_keys or rk == "element" or E.core_resource_def_by_key(rk):
                        self._res_gain(player, rk, amt, logs)
                # 主资源 key 若在 dict 里已结算，避免重复累加
                if k in rg:
                    gain = 0
                else:
                    gain = rd.get("on_skill", 0)
            else:
                gain = int(rg)
        elif rd.get("on_skill"):
            gain = rd["on_skill"]
        # v130.2 P1-2（on_heal 消费端修复）：治疗技能按 rd['on_heal'] 给职业主资源（牧师/悼咏 +2）。
        # 仅主资源位持有者生效——歌者分支被覆盖为双资源（resonance+echo）时 faith 不在激活集合 → 不重复给
        # （歌者治疗走分支挂载 res_gain，见 v130.2 双资源口径；engine 不得给歌者双计数）。
        if info and info.get("kind") == "治疗" and rd.get("on_heal") and k in act_keys:
            gain += int(rd["on_heal"])
        # v130.2 星语猎印：技能命中再按 on_hit（任意命中追加）+1
        on_skill_extra = 0
        if cls in HUNT_MARK_ON_LAND_HIT and rd.get("on_hit"):
            on_skill_extra = int(rd["on_hit"])
        if gain or on_skill_extra:
            if k == "element":
                self._res_gain(player, "element", gain + on_skill_extra, logs)
            else:
                self.resources[k] = self._res_gain_class(cls, k, gain + on_skill_extra)

    def _on_crit_resource(self, player: dict):
        """v130.2 暴击命中结算挂点（on_crit）：暮影影步 on_crit 攒步、刺客攻线 on_crit +1 连击点、
        星语猎印暴击额外 +1（crit_mark）。仅命中暴击时调用。"""
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd:
            return
        k = rd["key"]
        proc_ok = False
        # 暮影影步：暴击命中 on_crit 攒步（核心资源 on_crit > 0），潜行出手额外 +1
        if rd.get("on_crit"):
            gain = int(rd["on_crit"])
            if self.p_buffs.get("stealth"):
                gain += int(SHADOW_STEP_CFG.get("stealth_extra", 1) or 0)
            self.resources[k] = E.core_resource_gain(cls, self.resources, gain)
            proc_ok = True
        # 刺客攻线·影舞者：on_crit 额外 +1 连击点（叠于 on_attack/on_skill）
        elif cls == "cls_ci_ke" and self._is_path(player, 1):
            self.resources[k] = E.core_resource_gain(cls, self.resources, ASSASSIN_ON_CRIT_GAIN)
            proc_ok = True
        # 星语猎印：暴击额外 +1（crit_mark）
        if cls in HUNT_MARK_ON_LAND_HIT and HUNT_MARK_CRIT_EXTRA:
            self.resources[k] = E.core_resource_gain(cls, self.resources, HUNT_MARK_CRIT_EXTRA)
            proc_ok = True
        return proc_ok

    def _apply_enchant_attack(self, effs: dict, dmg: int, st: dict, player: dict, logs: list):
        """v34：攻击后符文效果结算(灼烧/冻结/吸血/连锁/虚弱/破魔)"""
        if not effs:
            return
        p_mech = self.mech_stacks
        # 灼热：攻击附带灼烧 n 层（DOT 重构：敌方灼烧为目标级 enemy["debuffs"]，不再写 p_mech）
        burn_lvl = self._enchant_lvl(effs, "burn")
        if burn_lvl:
            _enemy = self.enemy or {}
            _blv = int(C.rune_value("burn", burn_lvl))
            _deb = _enemy.setdefault("debuffs", {})
            _cur = _deb.get("burn") or {"n": 0, "mult": 1.0}
            _cur["n"] = min(5, int(_cur.get("n", 0) or 0) + _blv)
            _deb["burn"] = _cur
            logs.append(f"🔥 符文灼热：敌人灼烧层数 {_cur['n']}")
        # 冰霜：x% 概率冻结 1 回合
        freeze_lvl = self._enchant_lvl(effs, "freeze")
        if freeze_lvl and random.random() < C.rune_value("freeze", freeze_lvl):
            self.e_buffs["freeze"] = 1
            logs.append("❄️ 符文冰霜：敌人被冻结，跳过下回合！")
        # 吸血：造成伤害的 x% 回复生命
        ls_lvl = self._enchant_lvl(effs, "lifesteal")
        if ls_lvl and dmg > 0:
            heal = int(dmg * C.rune_value("lifesteal", ls_lvl))
            player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
            logs.append(f"🩸 符文吸血：回复 {heal} 点生命！")
        # 连锁：x% 概率额外雷击 y% 攻击伤害
        chain_lvl = self._enchant_lvl(effs, "chain")
        if chain_lvl:
            prob, mult = C.rune_value("chain", chain_lvl)
            # 契约断言：data/runes.py chain lvl 返回 [prob, mult] 二元素列表，防未来改单值静默错位
            assert isinstance(prob, (int, float)) and isinstance(mult, (int, float)), \
                f"rune chain lvl={chain_lvl} 应返回 [prob, mult]，实得 {C.rune_value('chain', chain_lvl)!r}"
            if random.random() < prob:
                cd = int(st.get("atk", 0) * mult)
                self._damage_enemy(cd, logs)
                logs.append(f"⚡ 符文连锁：雷击造成 {cd} 点额外伤害！")
        # 虚弱：攻击使敌人攻击 -x%（3 回合）
        weak_lvl = self._enchant_lvl(effs, "weaken")
        if weak_lvl:
            self.e_buffs["mon_atk_down"] = 3
            self.e_buffs["_weaken_val"] = C.rune_value("weaken", weak_lvl)
            logs.append(f"😵 符文虚弱：敌人攻击力下降！")
        # 破魔：魔法伤害 +x%（对普攻无加成，技能路径处理）
        mb_lvl = self._enchant_lvl(effs, "magic_break")
        if mb_lvl:
            pass  # 在技能魔法伤害里处理

    # ---------------- 阶段八：装备特效词条触发（20 章） ----------------
    def _equip_affix_ids(self, player: dict) -> list:
        """玩家已装备的全部词条 ID(affixes + legendary 专属)"""
        ids = []
        for item in (player.get("equipment") or {}).values():
            if not item:
                continue
            ids.extend(item.get("affixes", []) or [])
            if item.get("legendary"):
                ids.append(item["legendary"])
        # v101.28e 食物效果独立成体系，不再合并进装备词条（p_food_effects 由 food 挂点消费）
        return ids

    # ---------------- v130.2c 资源联动套装统一读取器（12 套 effect 消费入口） ----------------
    def _set_effs(self, player: dict, min_tier: int = 2) -> list:
        """已达成档位（≥min_tier 件）套装的全部 effect dict，[(effect dict, 档位)]。
        与 _affix_effs 同模式；装备 set 字段支持 set_xxx ID 与中文名（engine._set_info 双向解析）。"""
        out = []
        for sname, cnt in E.active_sets(player.get("equipment") or {}).items():
            if cnt < min_tier:
                continue
            info = E._set_info(sname)
            if not info:
                continue
            for tier in (2, 4, 5):
                if cnt >= tier:
                    eff = info.get(f"bonus_{tier}") or {}
                    if isinstance(eff, dict) and eff.get("effect"):
                        out.append((eff, tier))
        return out

    def _set_eff(self, player: dict, eff_name: str, min_tier: int = 2, res=None, on=None) -> dict | None:
        """取首个匹配 effect（可按 res/on 过滤）；未装备返回 None。"""
        for eff, _tier in self._set_effs(player, min_tier):
            if eff.get("effect") != eff_name:
                continue
            if res is not None and eff.get("res") != res:
                continue
            if on is not None:
                ons = eff.get("on")
                if isinstance(ons, str):
                    ons = [ons]
                if not ons or on not in ons:
                    continue
            return eff
        return None

    def _undead_on_field(self) -> bool:
        """场上是否存在亡灵单位：玩家召唤骷髅（skeleton tid）或敌方名称含亡灵系关键词。
        关键词与成就 亡灵使者 kills_type 同源（亡灵/骷髅/僵尸/幽灵）。"""
        for s in self.summons:
            if s.get("hp", 0) > 0 and (s.get("tid") == "skeleton" or "骷髅" in str(s.get("name", ""))):
                return True
        for u in self.enemies:
            if u.get("hp", 0) > 0 and any(k in str(u.get("name", "")) for k in ("亡灵", "骷髅", "僵尸", "幽灵")):
                return True
        return False

    def _set_res_proc(self, player: dict, event: str, logs: list):
        """v130.2c 套装 res_gain 统一读取器：on_taken 受击 / on_heal 治疗 / undead_on_field 回合开始亡灵在场。
        血誓战团（受击回怒）/ 圣徽·誓约（受击/治疗回信仰）/ 暗夜圣典（亡灵在场悼咏 +1）。"""
        for eff, _tier in self._set_effs(player, 2):
            if eff.get("effect") != "res_gain" or not eff.get("res"):
                continue
            ons = eff.get("on")
            if isinstance(ons, str):
                ons = [ons]
            if event == "undead_on_field":
                if not (ons and "undead_on_field" in ons) or not self._undead_on_field():
                    continue
            elif not ons or event not in ons:
                continue
            gain = int(eff.get("value", 1) or 1)
            if gain <= 0:
                continue
            _before = self._res_read(eff["res"])
            added = self._res_gain(player, eff["res"], gain)
            if added > _before:  # v130.2 R1：真实增量判定（满资源不再误报）
                _rd = E.core_resource_def(player.get("class_name", ""))
                _rnm = (E.core_resource_def_by_key(eff["res"]) or _rd or {}).get("name", eff["res"])
                logs.append(f"⚔️ 套装回响：{_rnm} +{gain}！")

    def _set_res_max_bonus(self, player: dict, key: str) -> int:
        """套装 res_max 资源上限加成（元素使徒 2 件：元素亲和充能条上限 +1，5 → 6）。"""
        bonus = 0
        for eff, _tier in self._set_effs(player, 2):
            if eff.get("effect") == "res_max" and eff.get("res") == key:
                bonus += int(eff.get("value", 0) or 0)
        return bonus

    def _set_crit_bonus(self, player: dict, info: dict | None = None) -> float:
        """套装暴击率加成：巡林长披风（命中带标记目标 +5%）/ 夜幕合契·影纱 4 件（终结技 +15%）。"""
        bonus = 0.0
        eff = self._set_eff(player, "crit_on_marked", 2)
        if eff and "mark" in self.e_buffs:
            bonus += float(eff.get("crit", 0.05) or 0.05)
        if info and ((info.get("res_cost") or {}).get("cp")
                     or (info.get("consume_all") or {}).get("key") == "cp"):
            eff4 = self._set_eff(player, "finisher_crit", 4)
            if eff4:
                bonus += float(eff4.get("crit", 0.15) or 0.15)
        return bonus

    def _energy_cost_reduce(self, player: dict, info: dict, base_cost: int) -> int:
        """v130.2 R1 P1-1：精力消耗统一折算——先词条「精力刀刃」折扣（tier 档 5%/8%/12%，保底 1 点），
        再套装「猎首」折扣（对带标记敌人 50/100 档 -10%）。预检 _skill_cast_blocked 与扣减
        _do_player_skill 共用此函数，保证两处消耗口径完全同源。"""
        _rv = int(base_cost or 0)
        _ee, _et = self._affix_eff_tiered(player, "energy_blade")
        if _ee:
            _disc = float(_et if _et is not None else _ee.get("cost_reduce", 0.05) or 0.05)
            _rv = max(1, int(_rv * (1 - _disc)))
        return self._energy_cost_after_sets(player, info, _rv, orig=int(base_cost or 0))

    def _energy_cost_after_sets(self, player: dict, info: dict, rv: int, orig: int | None = None) -> int:
        """v130.2c 猎首远征队徽记 4 件：对带标记敌人释放 50/100 档终结技时 精力消耗 -10%。
        档位按原始消耗判定（orig 缺省 = rv），折扣作用于传入的 rv（可叠加精力刀刃词条）。"""
        rc = info.get("res_cost") or {}
        _base = orig if orig is not None else rv
        if rc.get("energy") and "mark" in self.e_buffs:
            eff = self._set_eff(player, "res_cost_reduce", 4, res="energy", on="finisher_marked")
            # v130.2 R1：50/100 档阈值读数据 effect.min_cost（R2 配；缺省 50）
            if eff and _base >= int(eff.get("min_cost", 50) or 50):
                return max(1, int(rv * (1 - float(eff.get("value", 0.10) or 0.10))))
        return rv

    def _set_miracle_team_heal(self, player: dict, info: dict, logs: list):
        """v130.2c 圣典·日冕 2 件：施放二档以上神迹时 全体队友额外恢复 30 体力。
        档位口径：信仰神迹数据仅 3（圣光惩击·一档）与 10（满点神迹）两档，二档以上 = res_cost faith ≥5 或全耗信仰。"""
        eff = self._set_eff(player, "heal_team_on_miracle_t2plus", 2)
        if not eff:
            return
        rc = info.get("res_cost") or {}
        ca = info.get("consume_all") or {}
        # v130.2 R1：二档判定阈值读数据 effect.miracle_min（R2 配；缺省 5）
        _mmin = int(eff.get("miracle_min", 5) or 5)
        if not (ca.get("key") == "faith" or int(rc.get("faith", 0) or 0) >= _mmin):
            return
        hp = int(eff.get("hp", 30) or 30)
        if player.get("hp", 0) < player.get("max_hp", 1):
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + hp)
        for _ally in (self.allies or []):
            if isinstance(_ally, dict) and _ally.get("hp", 0) < _ally.get("max_hp", 1):
                _ally["hp"] = min(_ally.get("max_hp", _ally.get("hp", 1)), _ally.get("hp", 0) + hp)
        logs.append(f"🌞 圣典·日冕：神迹余晖笼罩全队，恢复 {hp} 点体力！")

    def _set_skill_dmg_mult(self, player: dict, info: dict, kind: str, skill_name: str) -> float:
        """v130.2c 套装技能伤害倍率：
        暗夜圣典 4 件（满档安魂曲/献祭暗焰 伤害 +20%）、势不可挡 4 件（气力技/终结技 物理伤害 +15%）。"""
        mult = 1.0
        eff4 = self._set_eff(player, "elegy_dmg", 4)
        if eff4 and skill_name in ("安魂曲", "献祭暗焰"):
            # v130.2 R1：暗夜圣典「满档」判定——数据 effect.cond=canticle_full 时需悼咏满档才加成（R2 配；缺省无条件）
            if eff4.get("cond") != "canticle_full" or self._res_read("canticle") >= self._res_max(player, "canticle"):
                mult *= 1.0 + float(eff4.get("value", 0.20) or 0.20)
        effs = self._set_eff(player, "chi_skill_phys", 4)
        if effs and kind == "物理":
            # v130.2 R1：势不可挡收窄为 chi 资源相关（res_cost.chi / consume_all key==chi / 拳师），与 burst_break 口径一致
            _rc = info.get("res_cost") or {}
            _ca = info.get("consume_all") or {}
            is_chi_fin = player.get("class_name", "") == "cls_wu_seng" or bool(_rc.get("chi")) or _ca.get("key") == "chi"
            if is_chi_fin:
                mult *= 1.0 + float(effs.get("value", 0.15) or 0.15)
        return mult

    def _set_bonus_5(self, player: dict) -> list:
        """已激活 5 件套的套装名列表(10 章五节 5 件效果，战斗特效型)"""
        return [sname for sname, cnt in E.active_sets(player.get("equipment") or {}).items()
                if cnt >= 5]

    def _race_bonus(self, player: dict) -> dict:
        """种族天赋表(08 章，battle 消费战斗型天赋)"""
        return E.race_stats(player.get("race"))

    def _race_attack_mult(self, player: dict) -> tuple:
        """种族对玩家攻击的伤害倍率（无畏/怯战 残血攻击、龙之吐息 首击）。
        返回 (倍率, 标签列表)。"""
        rt = self._race_bonus(player)
        if not rt:
            return 1.0, []
        mult = 1.0
        tags = []
        ratio = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        bz = rt.get("berserk_hp")
        if bz and ratio < bz:
            mult *= RACE_BERSERK_MULT
            tags.append("🔥无畏")
        tm = rt.get("timid_hp")
        if tm and ratio < tm:
            mult *= RACE_TIMID_MULT
            tags.append("😰怯战")
        fh = rt.get("first_hit")
        if fh and not self.first_attack_done:
            mult *= 1 + fh
            tags.append(f"🐲龙之吐息x{round(1 + fh, 2)}")
            self.first_attack_done = True
        return mult, tags

    def _affix_dmg_mult(self, player: dict) -> tuple:
        """被动词条/专属对本次伤害的倍率。返回 (倍率, 标签列表)。

        处决（低血增伤）/追猎（标记）/破魔（魔法系）/龙威（龙系）/黎明之光（深渊系）
        /精准（命中强化近似 +10%）/龙语印记（每层 +2% 伤害）。
        数值全查表（v126 数值下沉）：词条读 affixes.py effect（dmg_mult + execute_threshold/
        enemy_contains/enemy_role/enemy_marked 条件 + tag），套装 5 件读 sets 数据
        bonus_5_cond（enemy_contains/player_hp_below/dmg_mult/tag），斩杀阈值统一读数据。
        """
        ids = self._equip_affix_ids(player)
        # 套装 5 件对敌增伤不依赖词条（10 章五节，复用龙威/黎明破晓的关键词模式）
        mult = 1.0
        tags = []
        s5names = self._set_bonus_5(player)
        ename = self.enemy.get("name", "")
        e = self.enemy
        hp_ratio = e.get("hp", 0) / max(1, e.get("max_hp", 1))
        # v104 M07 修复 P1/P2：灰烬守卫（残血增攻）与迷雾（沼泽/毒腐系增伤）5 件效果同表
        p_ratio = player.get("hp", 0) / max(1, player.get("max_hp", 1))
        for sname in s5names:
            _sc = (E._set_info(sname) or {}).get("bonus_5_cond") or {}
            if not _sc:
                continue
            _ok = True
            if _sc.get("enemy_contains") and not any(k in ename for k in _sc["enemy_contains"]):
                _ok = False
            if _ok and _sc.get("player_hp_below") is not None and not (p_ratio < float(_sc["player_hp_below"])):
                _ok = False
            if _ok:
                mult *= float(_sc.get("dmg_mult", 1.0))
                tags.append(_sc.get("tag", sname))
        if not ids:
            # v101.28e/f：无词条时不能提前返回——食物/药水倍率（处决/精准/狂怒/死神）仍要结算
            return self._extra_dmg_mult(hp_ratio, mult, tags)
        # 被动词条/专属增伤：遍历数据 effect 的 dmg_mult（条件字段一并读数据；
        # 遍历顺序保持旧代码分支序，斩杀线统一 30% 由 execute_threshold 数据声明）
        for aid in ("execute", "jack_hook", "ancient_king", "hunt", "break_magic",
                    "dragon_aw", "dawn_light", "precise"):
            if aid not in ids:
                continue
            _ai = C.AFFIXES.get(aid) or C.LEGENDARY_EFFECTS.get(aid) or {}
            _ae = _ai.get("effect") or {}
            _dm = _ae.get("dmg_mult")
            if not _dm:
                continue
            _ok = True
            _th = _ae.get("execute_threshold")
            if _th is not None and not (hp_ratio < float(_th)):
                _ok = False
            if _ok and _ae.get("enemy_contains") and not any(k in ename for k in _ae["enemy_contains"]):
                _ok = False
            if _ok and _ae.get("enemy_role") and e.get("role") != _ae["enemy_role"]:
                _ok = False
            if _ok and _ae.get("enemy_marked") and "mark" not in self.e_buffs:
                _ok = False
            if _ok:
                mult *= float(_dm)
                tags.append(_ae.get("tag", _ai.get("name", aid)))
        # v101.28e/f：食物+药水额外倍率（处决/精准/狂怒/死神），与词条是否为空无关
        mult, tags = self._extra_dmg_mult(hp_ratio, mult, tags)
        return mult, tags

    def _extra_dmg_mult(self, hp_ratio: float, mult: float, tags: list) -> tuple:
        """v101.28e/f 食物效果 + 药水特殊效果的伤害倍率（独立于装备词条）。

        食物：处决（<30% +30%）/ 精准（+10%）。
        药水：死神药剂（<30% +30%）/ 狂怒药剂（下次攻击 +50%，一次性消耗）。
        龙语印记：每层 +2% 伤害（v104 移入此处——此前 _affix_dmg_mult 在无词条时提前
        return 会漏结算该倍率，有词条路径在调用后单独结算，两路径行为不一致）。
        """
        foods = getattr(self, "p_food_effects", []) or []
        # v110 审计修复：处决阈值 0.35 → 0.30（v109 拍板「斩杀线以 30% 为准」，
        # 与文案/设计 <30% 及 execute 被动 cond_hp=0.30 统一）
        if "execute" in foods and hp_ratio < 0.30:
            mult *= 1.30
            tags.append("💀处决")
        if "precise" in foods:
            mult *= 1.10
            tags.append("🎯精准")
        if self.p_buffs.get("execute_pot") and hp_ratio < 0.30:
            mult *= 1.30
            tags.append("💀处决")
        if self.p_buffs.get("next_atk_up"):
            mult *= 1.50
            del self.p_buffs["next_atk_up"]
            tags.append("⚔️狂怒")
        dm = int(self.mech_stacks.get("dragon_mark", 0) or 0)
        if dm:
            # v126 数值下沉：每层增伤读龙语印记数据 mark_pct（缺省 2%）
            _dt = (C.AFFIXES.get("dragon_tongue") or {}).get("effect") or {}
            mult *= 1 + float(_dt.get("mark_pct", 0.02)) * dm
        return mult, tags

    def _affix_element_dmg(self, player: dict, element: str) -> float:
        """元素伤害加成（冰/雷属性伤害 +x%）：技能带对应 element 时生效
        来源：专属词条（LEGENDARY_EFFECTS ice_dmg/thunder_dmg，澜歌之泪/奥拉圣印等）
             + 套装 5 件（10 章五节：月语/海神=冰系 +10%、苍穹=雷系 +10%）"""
        if not element:
            return 1.0
        bonus = 0.0
        for aid in self._equip_affix_ids(player):
            info = C.LEGENDARY_EFFECTS.get(aid)
            if not info:
                continue
            eff = info.get("effect") or {}
            if element == "ice":
                bonus += eff.get("ice_dmg", 0) or 0
            elif element == "thunder":
                bonus += eff.get("thunder_dmg", 0) or 0
        # 套装 5 件元素增伤（月语=寒月冰、海神=水属落地冰、苍穹=雷）
        s5 = "|".join(self._set_bonus_5(player))
        if element == "ice" and ("月语" in s5 or "海神" in s5):
            bonus += 0.10
        if element == "thunder" and "苍穹" in s5:
            bonus += 0.10
        return 1.0 + bonus

    def _affix_on_hit(self, player: dict, dmg: int, logs: list):
        """攻击命中后词条触发：流血/破甲/连击/吸血/元素附加/贯穿/蓄力/净化/龙语印记/审判之链
        v98.5：效果数据化 → core/affix_effects.py HIT_EFFECTS（并列 if 语义，顺序遍历）"""
        ids = self._equip_affix_ids(player)
        if not ids or self.enemy.get("hp", 0) <= 0:
            return
        from .core.affix_effects import HIT_EFFECTS
        for fn in HIT_EFFECTS.values():
            fn(self, player, dmg, logs)
        # v114 星陨（星陨之剑专属，effect aoe:True）：攻击 10% 概率全屏星陨 → 真 AOE
        # （Boss+全部援军各吃全额 200%，不走挡刀；chance/mult 读数据，数据缺失用 0.10/2.0 兜底）
        for aid in ids:
            _ai = C.AFFIXES.get(aid) or C.LEGENDARY_EFFECTS.get(aid) or {}
            _ae = _ai.get("effect") or {}
            if _ae.get("aoe") and random.random() < float(_ai.get("chance", 0.10)):
                ad = int(dmg * float(_ae.get("mult", 2.0)))
                self._aoe_damage_enemy(ad, logs)
                logs.append(f"☄️ {_ai.get('name', '星陨')}！全体造成 {ad} 点伤害！")

    def _affix_on_taken(self, player: dict, dmg: int, logs: list) -> int:
        """受击词条：减伤/格挡/坚韧/反击/反伤/深渊腐蚀。返回结算后的伤害。
        v98.5：效果数据化 → core/affix_effects.py TAKEN_EFFECTS（ctx 顺序结算）"""
        ids = self._equip_affix_ids(player)
        if not ids:
            return dmg
        from .core.affix_effects import TAKEN_EFFECTS
        ctx = {"dmg": dmg, "out": dmg}
        for fn in TAKEN_EFFECTS.values():
            fn(self, player, ctx, logs)
        return ctx["out"]

    def _affix_turn_start(self, player: dict, logs: list):
        """回合开始词条：回春(1% 生命)/冥想(1% 魔力)/晨曦祝福(2% 生命)
        v98.5：效果数据化 → core/affix_effects.py TURN_START_EFFECTS"""
        ids = self._equip_affix_ids(player)
        if not ids:
            return
        from .core.affix_effects import TURN_START_EFFECTS
        for fn in TURN_START_EFFECTS.values():
            fn(self, player, logs)

    # ---------------- v101.28e 食物效果挂点（独立于装备词条） ----------------
    def _food_on_hit(self, player: dict, dmg: int, logs: list):
        """攻击命中后料理效果触发（吸血/流血/破甲/连击/龙语印记/元素/贯穿/蓄力）。"""
        if not self.p_food_effects or self.enemy.get("hp", 0) <= 0:
            return
        from .core.food_effects import FOOD_HIT_EFFECTS
        for key in self.p_food_effects:
            fn = FOOD_HIT_EFFECTS.get(key)
            if fn:
                fn(self, player, dmg, logs)

    def _food_on_taken(self, player: dict, dmg: int, logs: list) -> int:
        """受击料理效果（反击/反伤）。返回结算后伤害（当前食物效果不改减伤，透传）。"""
        if not self.p_food_effects:
            return dmg
        from .core.food_effects import FOOD_TAKEN_EFFECTS
        ctx = {"dmg": dmg, "out": dmg}
        for key in self.p_food_effects:
            fn = FOOD_TAKEN_EFFECTS.get(key)
            if fn:
                fn(self, player, ctx, logs)
        return ctx["out"]

    def _food_turn_start(self, player: dict, logs: list):
        """回合开始料理效果（回春/冥想/晨曦祝福）。"""
        if not self.p_food_effects:
            return
        from .core.food_effects import FOOD_TURN_START_EFFECTS
        for key in self.p_food_effects:
            fn = FOOD_TURN_START_EFFECTS.get(key)
            if fn:
                fn(self, player, logs)


    def _skill_heal(self, st, skill_name, info, player, lv, mech, mval, p_mech, logs, target_ally=None):
        """治疗分支（v103.6 从 _player_skill 拆出；v122 支持指定队友目标 target_ally）"""
        # v122 治疗目标单位：指定队友 → 队友快照（引用）；None → 施法者自己
        target_unit = target_ally if target_ally is not None else player
        # v32 条件转化：治疗技能也吃战场状态（如神谕者自身低血时治疗量提升）
        cond_mult = self._cond_mult(info, player, lv)
        # v104 R3 P2-18：条件满足即显示标签（含 mult=1.0 的纯条件技，如符文护体"魔能≥3"）
        cond_label = info.get("cond", {}).get("label", "") if self._cond_active(info, player) else ""
        # v95r38：power<1 的治疗技能按 max_hp 百分比结算（如拳师气息调息 15% HP），
        # power>=1 保持原有"魔攻×power"模式（治愈术 200% 等），与消耗品 heal<1 百分比语义一致
        if info.get("power", 0) < 1:
            heal = int(player.get("max_hp", 0) * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
        else:
            heal = int(st["matk"] * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
        # v110.3 P2-9：被动·神恩——治疗技能效果 +X%（数据驱动 proc="heal"，替代名字硬匹配）。
        #              注意与下方 stat=="heal" 的神圣恩典为不同触发源，勿合并。
        #              ⚠ mult 为"完整倍率"语义（skills.py:725 神恩 mult=1.1 = 治疗×1.10，+10%）；
        #              故用 heal*=mult 而非 (1+mult)，保证两被动同学时 ×1.21（1.1×1.1）为现状保持。
        _pm_heal = self._passive_map(player)["proc"].get("heal", [])
        for _pn, _ps in _pm_heal:
            heal = int(heal * float(_ps.get("mult", 1.0)))
        # v104 R3 P1-1：神圣恩典（治疗+10%）/ 圣祷（20% 概率治疗+30%）
        _pm = self._passive_map(player)
        for _pn, _ps in _pm["stat"]:
            if _ps.get("stat") == "heal":
                heal = int(heal * (1 + float(_ps.get("mult", 0))))
        for _pn, _ps in _pm["proc"].get("heal_crit", []):
            if random.random() < float(_ps.get("chance", 0.2)):
                heal = int(heal * (1 + float(_ps.get("mult", 0))))
                logs.append(f"✨ {_pn}：治疗暴击！治疗量提升！")
        # 阶段八：圣光套 2 件效果——治疗 +10%
        if E.has_set(player.get("equipment", {}), "圣光套"):
            heal = int(heal * 1.10)
        # v101.28f 圣光药剂：治疗技能效果 +20%（3 回合）
        if self.p_buffs.get("heal_up"):
            heal = int(heal * 1.20)
        # v106.2 治疗强度：heal_power 属性 ×(1+heal_power)（cap 50%，职业/词条/套装多来源）
        try:
            _hpv = min(float(self._player_stats(player).get("heal_power", 0) or 0), 0.5)
            if _hpv > 0:
                heal = int(heal * (1 + _hpv))
        except Exception:
            pass
        # 阶段九：种族受疗天赋（目前仅龙裔孤傲之血 -10%；人类 v106.2 已移除圣光亲和改 exp_bonus）
        # v122：受疗天赋按被治疗者结算（奶队友时队友是龙裔同样 -10%）
        hr = self._race_bonus(target_unit).get("heal_received", 0) or 0
        if hr:
            heal = max(1, int(heal * (1 + hr)))
            logs.append(f"🐉 孤傲之血：治疗效果 -{int(-hr*100)}%！")
        # v130.2 信仰结晶副效果（next_heal_up，P0-3 消费端）：下一次治疗技能效果 +pct%（一次性，随即清 p_eff）
        _nhu = float((self.p_eff or {}).get("next_heal_up", 0) or 0)
        if _nhu > 0:
            heal = int(heal * (1 + _nhu))
            del self.p_eff["next_heal_up"]
            logs.append(f"✨ 信仰结晶：治疗技能效果 +{int(_nhu * 100)}%！")
        hp_before = target_unit.get("hp", 0)
        target_unit["hp"] = min(target_unit.get("max_hp", target_unit.get("hp", 0)), hp_before + heal)
        # v110.3 P2-4：庇护之光按“真实治疗溢出量”结算（数据驱动 proc="heal_shield"，替代名字硬匹配）
        # 此前 clamp 后按 hp-(max_hp-hp) 计算，任意治疗补满都误给 ≈20% max_hp 护盾
        # v122：治疗队友时溢出护盾加给被治疗者（队友快照 p_shields；自己场景保持 self._add_shield）
        for _pn, _ps in self._passive_map(player)["proc"].get("heal_shield", []):
            overflow = hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0))
            if overflow > 0:
                shield_gain = int(overflow * float(_ps.get("pct", 0.2)))
                if target_ally is not None:
                    _sh = target_unit.setdefault("p_shields", {})
                    _cur = _sh.get("overflow")
                    if _cur:
                        _cur["value"] = _cur.get("value", 0) + shield_gain
                        _cur["turns"] = max(_cur.get("turns", 0), 2)
                    else:
                        _sh["overflow"] = {"value": shield_gain, "turns": 2}
                    logs.append(f"🛡️ {_pn}：治疗溢出转化为 {shield_gain} 点护盾！")
                else:
                    self._add_shield("overflow", shield_gain, 2)
                    logs.append(f"🛡️ {_pn}：治疗溢出转化为 {shield_gain} 点护盾！")
        if target_unit.get("hp", 0) >= target_unit.get("max_hp", target_unit.get("hp", 0)) and mech == "bless":
            p_mech["bless"] = E.mech_stack_gain("bless", p_mech, mval)
        if target_ally is not None:
            logs.append(f"你施展【{skill_name}】，圣光治愈了 {target_unit.get('name', '队友')} {heal} 点生命！" + (f" ⚔️{cond_label} x{round(cond_mult, 2)}！" if cond_label else ""))
        else:
            logs.append(f"你施展【{skill_name}】，圣光治愈了你 {heal} 点生命！" + (f" ⚔️{cond_label} x{round(cond_mult, 2)}！" if cond_label else ""))
        if mech == "bless":
            logs.append(f"✨ 神恩凝聚：{p_mech.get('bless', 0)} 层(下次『神圣之光』转化护盾)")
        # v50 团队治疗：记录全队效果（副本广播）
        if info.get("team"):
            self.team_effects.append({"kind": "heal_all", "power": info["power"], "lv": lv, "matk": st["matk"]})
            logs.append(f"🌟【团队】圣光笼罩全队，所有人恢复 {heal} 点生命！")
        # v2.0 核心资源：治疗获取信仰（on_heal=2）
        self._resource_on_skill(player, info, logs)
        # v130.2c 资源词条：治疗技能施放（战意 on_skill 通用技能事件）
        self._affix_res_proc(player, "on_skill", logs)
        # v130.2 资源增幅：治疗触发（香薰圣烛 on_heal 额外 +1 信仰，回合制）
        _amp_heal = self._amp_resource(player, "on_heal")
        if _amp_heal:
            logs.append(f"⚡ 香薰圣烛：治疗额外获取信仰 +{_amp_heal}！")
        # v130.2c 资源词条：治疗命中（圣辉回响 on_heal +1/史诗 +2，tier 取档）
        self._affix_res_proc(player, "on_heal", logs)
        # v130.2c 圣徽·誓约 4 件：治疗回信仰 +1（套装 res_gain on_heal）
        self._set_res_proc(player, "on_heal", logs)

        return logs


    def _skill_buff(self, st, skill_name, info, player, lv, mech, mval, p_mech, logs):
        """增益分支（v103.6 从 _player_skill 拆出）"""
        eff = info.get("effect")
        if eff:
            # v1.x：mon_atk_down/element_shift/stealth/mark/sleep/shield_all/reduce_all
            # 7 分支注册表化 → core/battle_mech.py SKILL_BUFF_EFFECTS；TEAM_BUFF_KEYS 保留原逻辑
            from .core.battle_mech import SKILL_BUFF_EFFECTS
            h = SKILL_BUFF_EFFECTS.get(eff)
            if h:
                h(self, skill_name, info, player, lv, logs)
            else:
                # v104 M02 P1-4：团队增益 effect=xx_all 映射为施放者自身有效键（def_all→def_up 等）
                key = TEAM_BUFF_KEYS.get(eff, eff)
                # v104 M02 P2-11：同 effect 不同技能 buff 覆盖取高（与药水路径一致）
                base_turns = E.skill_buff_turns(lv)
                # v130.2 歌者回声：增益技持续 + 回声层数 回合（priest_转职.md §3.0）
                if self._is_bard_skill(player, info):
                    base_turns += int(ECHO_CFG.get("buff_extend_per_layer", 1) or 1) * self._echo_layers()
                self.p_buffs[key] = max(self.p_buffs.get(key, 0), base_turns)
        # v1.x：原 burn_burst/rage_burst/bless_shield 三分支（v29 effect 型引爆/转化）
        # 全库无数据 producer（skills.py 无 effect=burn_burst/rage_burst/bless_shield 条目）
        # → 死代码删除；其专属 cond_mult/cond_label 计算一并移除。
        self._apply_mech_gain(mech, mval, p_mech, logs, skill_name)
        logs.append(f"你施展【{skill_name}】！")
        if eff == "element_shift" and getattr(self, "_shifted_element", None):
            logs.append(f"✦ 元素跃迁！切换到 {E.ELEMENT_CN.get(self._shifted_element, '?')}系(下次元素技能伤害+20%)")
            self._shifted_element = None
        # v50 团队增益：记录全队效果（副本广播）
        team = info.get("team")
        if team:
            st2 = self._player_stats(player)
            self.team_effects.append({"kind": team, "effect": eff, "lv": lv, "stats": st2})
            logs.append(f"🌟【团队】{info.get('name', skill_name)} 笼罩全队！")
        # v2.0 核心资源：增益技能获取（如战吼怒气+3）
        self._resource_on_skill(player, info, logs)
        # v130.2c 资源词条：增益技能（战吼回响 buff_skill 怒气 +1）
        self._affix_res_proc(player, "buff_skill", logs)

        return logs
    def _player_skill(self, st: dict, skill_name: str, info: dict, player: dict, target=None) -> list:
        """施放技能：治疗/增益/攻击 + 特效全部落地(v27 技能等级 + v29 分支机制)"""
        logs = []
        lv = E.skill_level_of(player, skill_name)  # #259：兼容 skill_levels key 为中文名（战斗内等级此前恒 Lv.1）
        kind = info["kind"]
        mech = info.get("mech", "")
        # v122 治疗指定队友：解析目标（allies 空=单人战斗 → None=奶自己）
        target_ally = self._resolve_ally_target(target) if kind == "治疗" else None
        # v107 召唤：技能带 summon 字段 → 生成召唤物实体（治疗/增益/攻击技能均可带，先召唤再结算技能）
        if info.get("summon"):
            self._summon_entity(info["summon"], player, logs)
        # v107 血魔法（猩红学者）：消耗当前 HP % 换伤害加成（hp_cost 字段，0.10 = 扣 10% 当前生命）
        self._hp_cost_bonus = 0.0
        if info.get("hp_cost") and player.get("hp", 0) > 0:
            cost = max(1, int(player["hp"] * float(info["hp_cost"])))
            player["hp"] = max(1, player.get("hp", 0) - cost)
            logs.append(f"🧛 血之代价：消耗 {cost} 点生命换取力量！")
            self._hp_cost_bonus = 0.30
        # v56：叠层随技能等级成长（每 2 级 +1 层）
        mval = E.skill_mech_val(info, lv)
        # 分支专属状态层（玩家侧：狂暴/圣盾/风印/影袭/气力/神恩/毒层）
        p_mech = self.mech_stacks
        if kind == "治疗":
            return self._skill_heal(st, skill_name, info, player, lv, mech, mval, p_mech, logs, target_ally=target_ally)
        if kind == "增益":
            return self._skill_buff(st, skill_name, info, player, lv, mech, mval, p_mech, logs)
        if kind == "嘲讽":
            # v51 挑衅怒吼：嘲讽（单人=敌方降攻+叠狂暴；副本=instance 层拉仇恨）
            self.e_buffs["mon_atk_down"] = E.skill_buff_turns(lv)
            self._apply_mech_gain("rage", 1, p_mech, logs, skill_name)
            logs.append(f"📢 你大声挑衅【{self.enemy.get('name', '敌人')}】！敌人恼羞成怒，攻击力下降！")
            if info.get("team"):
                self.team_effects.append({"kind": "taunt", "lv": lv})
                logs.append(f"🌟【团队】{info.get('name', skill_name)}：Boss 的注意力被牢牢锁定！")
            return logs

        est = self._enemy_stats()
        # v109.2 P1-1 运势：幸运转化为暴击补充（luck → crit，上限 +12%）；PVP 对方韧性对称生效
        # v130.2c 套装暴击：巡林长披风（带标记 +5%）/ 夜幕合契·影纱 4 件（终结技 +15%）
        is_crit = random.random() < (st["crit"] + min(float(st.get("luck", 0) or 0) * 0.3, 0.12) + self._set_crit_bonus(player, info)) * self._tenacity_mult(est)
        # v130.2 游侠满弦状态（守线·风行者）：精力 ≥80 且低耗/连射技能 暴击率 +10%
        if self._energy_high_crit(player, info):
            is_crit = is_crit or random.random() < float(ENERGY_HIGH.get("crit_bonus", 0.10) or 0.10)
        # v104 R3 P1-1：猎手本能——对标记目标暴击 +10%（e_buffs["mark"] 为目标易伤标记）
        if "mark" in self.e_buffs:
            for _pn, _ps in self._passive_map(player)["stat"]:
                if _ps.get("stat") == "crit_mark" and random.random() < float(_ps.get("mult", 0.1)):
                    is_crit = True
        # v104 R3 P1-10：潜行状态（stealth）——下次攻击必暴，攻击后消耗
        if self.p_buffs.get("stealth"):
            is_crit = True
            del self.p_buffs["stealth"]
            logs.append("🌙 潜行生效！本次攻击必定暴击！")
        # v34 符文：装备效果（破甲/暴伤/破魔/攻击特效）
        effs = self._enchant_effects(player)
        ap_lvl = self._enchant_lvl(effs, "armor_pierce")
        if ap_lvl:
            est = dict(est)
            est["def"] = int(est["def"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
            est["mdef"] = int(est["mdef"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
        # 机制：影袭（满血必暴）——查表 MECH_FULL_HP_CRIT（v125.2 B1）
        if mech in MECH_FULL_HP_CRIT and self.enemy.get("hp", 0) >= self.enemy.get("max_hp", 1):
            is_crit = True
        # v109.2 P1-1 运势：暴击命中后 30% 概率追加 50% 伤害（幸运一击，含必暴机制）
        lucky = is_crit and random.random() < 0.30
        # 机制：冰霜（冻结目标碎冰增伤）——查表 MECH_FROZEN_MULT（v125.2 B1）
        frozen_bonus = 1.0
        if mech in MECH_FROZEN_MULT and "freeze" in self.e_buffs:
            frozen_bonus = MECH_FROZEN_MULT[mech]
        # 机制：圣光/毒/影/气/审判/狂暴 层数加成
        stack_bonus = self._mech_stack_bonus(mech, p_mech, info)
        # v30 条件转化：按战场状态变形态（残血斩杀/背水一战）
        cond_mult = self._cond_mult(info, player, lv)
        # v104 R3 P2-18：条件满足即显示标签（含 mult=1.0 的纯条件技）
        cond_label = info.get("cond", {}).get("label", "") if self._cond_active(info, player) else ""
        multi = info.get("multi", 1)
        # 机制：风印 → 连击次数增加（查表 MECH_COMBO_STACKS，v125.2 B1）
        if mech in MECH_COMBO_STACKS:
            multi += p_mech.get(mech, 0)
        # v34 破魔：魔法伤害 +x%
        mb_lvl = self._enchant_lvl(effs, "magic_break")
        magic_bonus = (1 + C.rune_value("magic_break", mb_lvl)) if mb_lvl and kind == "魔法" else 1.0
        # v109.2 P2-9：半死字段数据驱动化（原按技能名硬编码，改名即失效）——
        # 破甲本能(proc pierce)/烈焰亲和(proc fire_bonus)/双修精通(stat cond=dual_stat)
        _pm = self._passive_map(player)
        _procs = _pm["proc"]
        passive_bonus = 1.0
        # 技能元素（"current"=当前元素亲和系）——提前解析供 proc 型被动判定
        element = info.get("element", "")
        if element == "current":
            element = self.resources.get("element", "fire")
        # 破甲本能：破防技能伤害 +10%（proc pierce，原硬编码技能名）
        for _pn, _ps in _procs.get("pierce", []):
            if info.get("pierce"):
                passive_bonus *= float(_ps.get("mult", 1.1))
        # 烈焰亲和：火系魔法伤害 +10%（proc fire_bonus，原 stat=fire+技能名硬编码；mult 为增量语义）
        for _pn, _ps in _procs.get("fire_bonus", []):
            if element == "fire" and kind == "魔法":
                passive_bonus *= (1 + float(_ps.get("mult", 0.10)))
        # 双修精通：力量/智力同时增加时攻击 +5%（stat cond=dual_stat，v1.x 查 PASSIVE_COND_CHECKS）
        for _pn, _ps in _pm["stat"]:
            if _ps.get("cond") == "dual_stat" and passive_cond_ok(self, player, _ps):
                passive_bonus *= (1 + float(_ps.get("mult", 0.05)))
        # v104 R3 P1-1：分支/基础 proc 型被动伤害挂点（数据驱动：万象亲和/元素之心/毒师/淬毒之心/
        # 追猎者/猎魔之眼/奥术之心/武技/疾驰/审判之心/暗影之心/暗影之舞/元素共鸣）
        # 元素伤害类（元素系技能）
        for _pn, _ps in _procs.get("element_dmg", []):
            if element and E.ELEMENT_MARKS.get(element):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # v110.3 P2-9：毒系技能伤害（mech 判定，废弃"名字含毒"子串；毒爆术 mech=poison_burst 一并覆盖）
        # v125.2 B1：mech 归属查表 MECH_PROC_GROUPS
        for _pn, _ps in _procs.get("poison_dmg", []):
            if mech in MECH_PROC_GROUPS.get("poison_dmg", ()):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 对标记目标伤害（追猎者/猎魔之眼：e_buffs["mark"] 为目标易伤标记）
        for _pn, _ps in _procs.get("mark_dmg", []):
            if "mark" in self.e_buffs:
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 奥术系伤害（奥术之心）——v125.2 B1：mech 归属查表 MECH_PROC_GROUPS
        for _pn, _ps in _procs.get("arcane_dmg", []):
            if mech in MECH_PROC_GROUPS.get("arcane_dmg", ()):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 连招技能伤害（武技）
        for _pn, _ps in _procs.get("combo_dmg", []):
            if info.get("combo"):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 速度优势增伤（疾驰）
        for _pn, _ps in _procs.get("speed_dmg", []):
            if st.get("spd", 0) > est.get("spd", 0):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # 机制型 stat 被动（审判之心 judge / 暗影之心 shadow）：对应 mech 技能伤害加成
        # v125.2 B1：mech 归属查表 MECH_STAT_PASSIVES
        for _pn, _ps in _pm["stat"]:
            _sstat = _ps.get("stat")
            if _sstat in MECH_STAT_PASSIVES and mech == MECH_STAT_PASSIVES[_sstat]:
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
            elif _sstat == "stealth_crit_dmg" and self.p_buffs.get("stealth"):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # v104 R3 P1-1：复仇被动消费——受击后下次攻击 +30%（挨打反打，一次后清除）
        if self.p_buffs.get("revenge_atk"):
            for _pn, _ps in _procs.get("counter", []):
                passive_bonus *= float(_ps.get("mult", 1.3))
            del self.p_buffs["revenge_atk"]
        # v107 斩杀（影武者）：目标 HP<30% 时伤害加成（cond_hp 斩杀线 / mult 加成）
        _execute_tag = ""
        if self.enemy.get("hp", 0) > 0 and self.enemy.get("max_hp", 1) > 0:
            _hp_ratio = self.enemy["hp"] / self.enemy["max_hp"]
            for _pn, _ps in _procs.get("execute", []):
                if _hp_ratio < float(_ps.get("cond_hp", 0.30)):
                    passive_bonus *= (1 + float(_ps.get("mult", 0.40)))
                    _execute_tag = f"⚔️斩杀x{round(1 + float(_ps.get('mult', 0.40)), 2)}"
                    break
        # v107 血魔法（猩红学者）：hp_cost 换 +30% 伤害
        if self._hp_cost_bonus:
            passive_bonus *= (1 + self._hp_cost_bonus)
        # 元素反应增伤（元素共鸣：触发反应时 +15%）
        for _pn, _ps in _procs.get("reaction", []):
            self._elem_reaction_boost = float(_ps.get("mult", 1.15))
        # 元素反应：当前系 × 目标印记（技能带 element 字段时判定；"current"=当前元素亲和系）
        reaction_mult = 1.0
        reaction_log = ""
        if element and E.ELEMENT_MARKS.get(element):
            marks = {k: v for k, v in self.e_buffs.items() if k in E.ELEMENT_MARKS.values()}
            r = E.element_reaction(element, marks)
            if r:
                reaction_mult = r["mult"]
                # v104 R3 P1-1：元素共鸣被动——元素反应伤害 +15%（在基础反应倍率上叠加）
                if getattr(self, "_elem_reaction_boost", 1.0) > 1.0:
                    reaction_mult *= self._elem_reaction_boost
                    self._elem_reaction_boost = 1.0
                reaction_log = f"💥{r['name']}！"
                # 超载：额外全体伤害（v114 真 AOE：Boss+全部援军各吃全额，不走挡刀）
                if r["extra"] == "aoe":
                    aoe_dmg = int(st["matk"] * 1.2 * reaction_mult)
                    self._aoe_damage_enemy(aoe_dmg, logs)
                    reaction_log = f"💥超载爆发！额外 {aoe_dmg} 点全体伤害！"
                # 冻结：目标冻结 1 回合
                elif r["extra"] == "freeze":
                    self.e_buffs["freeze"] = 1
                    reaction_log = "❄️冻结！目标被冰封 1 回合！"
                # 感电：连击 +1（追加一次伤害）
                elif r["extra"] == "chain":
                    multi += 1
                    reaction_log = "⚡感电连锁！追加一次攻击！"
                # 清除印记（感电保留）
                if r["clear"]:
                    for mk in E.ELEMENT_MARKS.values():
                        self.e_buffs.pop(mk, None)
        # v130.2 攻线·元素：引爆技反应表（cond type='reaction'，消耗充能时按引爆系+目标印记结算）。
        # 独立于旧 e_buffs 反应体系，读目标侧 element_marks（mage_转职.md §1.0②）
        if info.get("cond", {}).get("type") == "reaction" and element:
            rr = self._reaction_table_resolve(player, element, st, logs)
            if rr is not None:
                rmult, rlog, chain_flag = rr
                reaction_mult *= rmult
                if reaction_log:
                    reaction_log += rlog
                else:
                    reaction_log = rlog
                if chain_flag:
                    multi += 1
        # v130.2 拳师蓄势 Momentum（攻线·格斗士）：物理技能吃「每 1 气 +3%」持有加伤
        _mom_mult = self._momentum_mult(player)
        if kind == "物理" and _mom_mult != 1.0:
            passive_bonus *= _mom_mult
            self._mom_mult = _mom_mult
        else:
            self._mom_mult = 1.0
        # v130.2 刺客攻线·影舞者：终结技（res_cost cp）连段增伤（combo≥3 每层 +5%，上限 +40%）
        _combo_mult = 1.0
        if self._combo_active(player) and (info.get("res_cost") or {}).get("cp"):
            _combo_mult = self._combo_dmg_mult(player)
            if _combo_mult != 1.0:
                passive_bonus *= _combo_mult
        self._combo_mult = _combo_mult
        # v130.2c 伤害倍率词条：爆发贯体（气力技物理 +10%）/ 终结之技（终结技 +10%~20%，tier 取档）
        # v130.2c 套装伤害倍率：暗夜圣典 4 件（安魂曲/献祭暗焰 +20%）/ 势不可挡 4 件（气力技/终结技物理 +15%）
        _sk_af = self._affix_skill_dmg_mult(player, info, kind) * self._set_skill_dmg_mult(player, info, kind, skill_name)
        if _sk_af != 1.0:
            passive_bonus *= _sk_af
        self._sk_af_mult = _sk_af
        total = 0
        _magi_part = 0  # v109.2 P2-4：混合伤害魔法段累计（吸血分账用）
        # 阶段八：装备被动词条伤害加成（处决/追猎/精准/龙语印记等）+ 专属元素伤害
        affix_mult, affix_tags = self._affix_dmg_mult(player)
        if self._mom_mult != 1.0:
            affix_tags = list(affix_tags) + [f"🔥蓄势x{round(self._mom_mult, 2)}"]
        if self._combo_mult != 1.0:
            affix_tags = list(affix_tags) + [f"🌪️连段x{round(self._combo_mult, 2)}"]
        if getattr(self, "_sk_af_mult", 1.0) > 1.0:
            affix_tags = list(affix_tags) + [f"⚔️套装技x{round(self._sk_af_mult, 2)}"]
        # v130.2 澎湃烈酒（phys_up）/ 引气精华（buff_phys_next）：物理技能伤害 +pct%
        # （幂等乘入 passive_bonus；buff_phys_next 一次性随即清，豁免回合递减；P0-2/P0-5 消费端）
        if kind == "物理" and (self.p_buffs.get("phys_up") or self.p_buffs.get("buff_phys_next")):
            _pu = float((self.p_eff or {}).get("phys_up", 0) or 0)
            _bpn = float((self.p_eff or {}).get("buff_phys_next", 0) or 0)
            if _pu > 0:
                passive_bonus *= (1 + _pu)
            if _bpn > 0:
                passive_bonus *= (1 + _bpn)
                del self.p_buffs["buff_phys_next"]
                self.p_eff.pop("buff_phys_next", None)
            _tags_pu = ([f"🍺物理x{round(1 + _pu, 2)}"] if _pu > 0 else []) + \
                       ([f"🥊引气x{round(1 + _bpn, 2)}"] if _bpn > 0 else [])
            if _tags_pu:
                affix_tags = list(affix_tags) + _tags_pu
        elem_mult = self._affix_element_dmg(player, element)
        # 阶段九：种族攻击天赋（无畏/怯战 残血、龙之吐息 首击）
        race_mult, race_tags = self._race_attack_mult(player)
        if race_tags:
            affix_tags = list(affix_tags) + race_tags
        pmult = (E.skill_power_mult(lv, info) * frozen_bonus * stack_bonus * cond_mult
                 * magic_bonus * passive_bonus * reaction_mult * affix_mult * elem_mult * race_mult)
        # vF3 P1 连乘封顶：技能伤害倍率连乘（技能×冻结×叠层×条件×魔法×被动×反应×词缀×元素×种族）
        # 只 clamp 技能伤害倍率段；暴击(×1.5)/暴伤(crit_dmg)/幸运一击(×1.5) 为独立乘区，在下方另行施加不受此限。
        if pmult > C.SKILL_PMULT_CAP:
            pmult = C.SKILL_PMULT_CAP
        # v106 穿透：物理技能用物穿/固定物穿，魔法技能用法穿/固定法穿
        _pp_phys, _pf_phys = self._pene_vals(st, magic=False)
        _pp_magi, _pf_magi = self._pene_vals(st, magic=True)
        for _ in range(multi):
            # v107 伤害类型四层架构：物理→phys / 魔法→magi / 真伤→true（新增，绕过全减伤）
            if kind == "真伤":
                dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), 0, is_crit, dmg_type="true")
            elif kind == "物理":
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), 0, is_crit, pierce=True,
                                          dmg_type="phys")
                else:
                    dmg_i = E.calc_damage(int(st["atk"] * info["power"] * pmult), est["def"], is_crit,
                                          pene_pct=_pp_phys, pene_flat=_pf_phys, dmg_type="phys")
                # v87 魔剑士·混合伤害：magic_add 追加魔法段（魔能斩 130% 物 + 30% 魔）
                if info.get("magic_add"):
                    dmg_m = E.calc_damage(int(st["matk"] * info["magic_add"] * pmult), est["mdef"], is_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
                    dmg_i += dmg_m
                    _magi_part += dmg_m
            else:
                # v109.2 P1-6：pierce 魔法分支修复——审判之剑等魔法 pierce 技能此前被结算链忽略
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int(st["matk"] * info["power"] * pmult), 0, is_crit, pierce=True,
                                          dmg_type="magi")
                else:
                    dmg_i = E.calc_damage(int(st["matk"] * info["power"] * pmult), est["mdef"], is_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
            # v87 魔剑士·魔力涌动：消耗 buff，本次攻击追加 80% 魔法伤害
            if self.p_buffs.get("spellblade_surge"):
                surge_dmg = E.calc_damage(int(st["matk"] * 0.80 * pmult), est["mdef"], is_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
                dmg_i += surge_dmg
                _magi_part += surge_dmg
                del self.p_buffs["spellblade_surge"]
            # v34 残忍：暴击伤害 +x%（按等级，符文特效）
            brutal_lvl = self._enchant_lvl(effs, "brutal")
            if brutal_lvl and is_crit:
                dmg_i = int(dmg_i * (1 + C.rune_value("brutal", brutal_lvl)))
            # v106.3 暴击伤害属性（crit_dmg 面板化：词条折算 + 种族 + 被动 + 药水）
            cdmg = float(st.get("crit_dmg", 0) or 0)
            if self.p_buffs.get("crit_dmg_pot"):
                cdmg = 1 - (1 - cdmg) * (1 - 0.25)  # 狂暴药剂 +25% 暴伤（乘算并入）
            if is_crit and cdmg > 0:
                dmg_i = int(dmg_i * (1 + cdmg))
            # v109.2 P1-1 运势：幸运一击——暴击后 30% 概率追加 50% 伤害
            if lucky:
                dmg_i = int(dmg_i * 1.5)
            dmg_i = self._apply_mark(dmg_i)
            total += dmg_i
        if lucky:
            logs.append("✨ 幸运一击！暴击伤害额外提升 50%！")
        total = self._boss_dmg_filter(total, player, logs, dmg_type={"物理": "phys", "魔法": "magi", "真伤": "true"}.get(kind, "phys"))
        # v110 P1-3：玩家攻击端消费敌方防守属性（物免/格挡/魔免/元素抗；PVP 对称，PVE 怪无键=0 无感）
        total, _magi_part = self._enemy_mitigate(total, _magi_part, element, logs, kind=kind)
        # v105 怪物闪避：技能主伤害判定一次（闪避成功 total 归零，日志自然显示 0 伤害）
        if self._monster_dodge_check(logs):
            total = 0
        else:
            aoe = info.get("aoe")
            if aoe:
                # v114/v2 AOE：结构语义化 scope（True→"all"），技能 reach 覆盖职业 reach，falloff 衰减
                scope = "all" if aoe is True else str(aoe)
                self._aoe_reach = int(info.get("reach") or 3)
                self._aoe_falloff = float(info.get("aoe_falloff", 1.0) or 1.0)
                _boss_dmg = self._aoe_damage(total, logs, scope, source=skill_name)
            else:
                self._damage_enemy(total, logs)
                _boss_dmg = total
            # v106.3 吸血统一结算（属性化：词条/种族/被动/药水 → st["lifesteal"] 一处消费）
            # v106.4：魔法技能走法术吸血（lifesteal_magi），物理技能走物理吸血（lifesteal_phys）
            # v107：真伤不吸血（dmg_type="true" 直接跳过）
            # v109.2 P2-4：混合段分账——物理技能带魔法段（魔能斩/魔能涌动）时，
            # 物段走物理吸血、魔段走法术吸血（原整体按 phys 结算）
            if _magi_part > 0:
                if _boss_dmg - _magi_part > 0:
                    self._settle_lifesteal(player, _boss_dmg - _magi_part, logs, magic=False, dmg_type="phys")
                self._settle_lifesteal(player, _magi_part, logs, magic=True, dmg_type="magi")
            else:
                self._settle_lifesteal(player, _boss_dmg, logs, magic=(kind == "魔法"),
                                       dmg_type={"物理": "phys", "魔法": "magi", "真伤": "true"}.get(kind, "phys"))
        if multi > 1:
            logs.append(f"你施展【{skill_name}】，连击 {multi} 次，共造成 {total} 点伤害！")
        else:
            # v127.3 多怪时日志带目标名（a1 指定/自动选择都显示打了谁；单怪保持原文案）
            _alive_n = sum(1 for u in self.enemies if u.get("hp", 0) > 0)
            _tg_d = getattr(self, "_active_target", None) or self.enemy
            _tgtxt = f"对【{_tg_d.get('name', '敌人')}】" if _alive_n > 1 and _tg_d else ""
            logs.append(f"你施展【{skill_name}】，{_tgtxt}造成 {total} 点伤害！")
        # v107 吸MP（虚空行者）：魔法伤害的 mp_steal% 回复自身魔力（打空敌人蓝条的反向续航）
        if info.get("mp_steal") and total > 0:
            gain = int(total * float(info["mp_steal"]))
            if gain > 0:
                player["mp"] = min(player.get("max_mp", C.DEFAULT_MAX_MP),
                                   player.get("mp", 0) + gain)
                logs.append(f"🌑 虚空汲取：回复 {gain} 点魔力！")
        # 特效合并成紧凑标签（避免一行堆满长后缀）
        tags = []
        if is_crit:
            tags.append("💥暴击")
        if mech in MECH_FULL_HP_CRIT and self.enemy.get("hp", 0) >= self.enemy.get("max_hp", 1):
            tags.append("满血影袭必暴")
        if frozen_bonus > 1.0:
            tags.append("❄️碎冰增伤")
        if stack_bonus > 1.0:
            tags.append(f"⚡增幅x{round(stack_bonus, 2)}")
        if cond_mult > 1.0 and cond_label:
            tags.append(f"⚔️{cond_label}x{round(cond_mult, 2)}")
        elif cond_mult == 1.0 and cond_label:
            # v104 R3 P2-18：mult=1.0 的纯条件技（如符文护体"魔能≥3"）条件满足时也提示
            tags.append(f"⚔️{cond_label}")
        if mb_lvl:
            tags.append(f"🔮破魔x{round(magic_bonus, 2)}")
        # v107 斩杀标签（影武者）
        if _execute_tag:
            tags.append(_execute_tag)
        # v107 血魔法标签（猩红学者）
        if self._hp_cost_bonus:
            tags.append("🧛血祭x1.3")
        # 阶段八：词条伤害标签（处决/追猎/精准等）
        if affix_tags:
            tags.extend(affix_tags)
        if elem_mult > 1.0:
            tags.append(f"✨元素x{round(elem_mult, 2)}")
        if tags:
            logs[-1] += " " + "·".join(tags)
        if reaction_log:
            logs.append(reaction_log)
        # v2.0 元素印记：施放带 element 的技能后给目标挂印记 + 法师切换当前系
        if element and E.ELEMENT_MARKS.get(element):
            extra_layers = 1
            # v104 R3 P1-1：追踪印记——30% 概率额外叠 1 印记（游侠基础被动）
            for _pn, _ps in _procs.get("mark_extra", []):
                if random.random() < float(_ps.get("chance", 0.3)):
                    extra_layers += 1
            E.element_mark_apply(self.e_buffs, element, extra_layers)
            # v130.2 目标侧 element_marks 登记（每系上限 3；仅命中叠加——mage_转职.md §1.0①）
            if total > 0:
                new_marks = self._elem_mark_apply(element, layers=extra_layers, player=player)
                if player.get("class_name", "") == "cls_fa_shi" and self._is_path(player, 1):
                    logs.append(f"✦ 元素印记：目标{ {'fire': '火', 'ice': '冰', 'thunder': '雷'} [element]}印 {new_marks}/{self._elem_mark_max(player)}")
                # v130.2 last_element 同系连发：记录上次元素，同系第二次施放额外 +1 充能（元素凝聚）
                if player.get("class_name", "") == "cls_fa_shi":
                    self._last_element_set(player, element)
            # v104 R3 P1-1：寒霜亲和——冰系技能命中附带减速 2 回合
            if element == "ice":
                for _pn, _ps in _procs.get("ice_slow", []):
                    self.e_buffs["spd_down"] = max(self.e_buffs.get("spd_down", 0), 2)
                    logs.append("❄️ 寒霜亲和：敌人被减速！")
            if self.resources.get("element") is not None:
                self.resources["element"] = element
        # v2.0 连招序列：拳师 combo 字段推进（拳→踢→掌 三连触发额外效果）
        combo_tag = info.get("combo", "")
        if combo_tag:
            combo_full = self._combo_push(combo_tag)
            if combo_full:
                combo_bonus = int(total * 0.30)
                # v109.2 P1-2：连招精通——三连击破追加伤害提升至 50%（0.30 → 0.50，武圣连击强化设计落地）
                for _pn, _ps in _procs.get("combo_boost", []):
                    combo_bonus = int(total * 0.50)
                    break
                self._damage_enemy(combo_bonus, logs)
                logs.append(f"🥊 三连击破！拳-踢-掌完美连招，追加 {combo_bonus} 点伤害！(下次气力技+20%)")
                self.resources["combo_ready"] = 1
            else:
                logs.append(f"🥊 连招 {self._combo_label()}")
        # v34 符文攻击特效（灼烧/冻结/吸血/连锁/虚弱）
        self._apply_enchant_attack(effs, total, st, player, logs)
        # 阶段八：攻击命中后词条触发（流血/破甲/连击/元素附加等）
        self._affix_on_hit(player, total, logs)
        # v101.28e 攻击命中后料理效果触发
        self._food_on_hit(player, total, logs)

        # ---- 分支机制结算（v29） ----
        self._last_player = player
        self._apply_mech_effect(mech, mval, p_mech, total, logs, skill_name, is_crit, info)
        # v63 额外控制效果（cc 字段，独立于 mech 叠层）：眩晕/沉默/净化
        # v125.2 B1：cc 白名单查表 SKILL_CC_WHITELIST
        cc = info.get("cc")
        if cc and cc in SKILL_CC_WHITELIST:
            self._apply_mech_effect(cc, 1, p_mech, total, logs, skill_name, is_crit, info)

        # ---- 技能特效（v9 落地）----
        # v2.0：技能名硬编码特效已废弃（12 章技能全数据驱动，mech/effect/cond 在 _apply_mech_effect 覆盖）
        # v104 R3 P2-10 修复：吸血改按 lifesteal 数据字段触发（原只认 effect=="lifesteal"，
        # 全表无技能带此 effect → 嗜血斩 lifesteal:0.25 实机 0 吸血）；数值由 skill_lifesteal_pct 读字段
        if info.get("lifesteal"):
            heal = int(total * E.skill_lifesteal_pct(info, lv))
            if self.p_buffs.get("mortal_wound"):  # v1.3 重伤：技能吸血减半
                heal = int(heal * 0.5)
            player["hp"] = min(player.get("max_hp", player["hp"]), player.get("hp", 0) + heal)
            logs.append(f"💉 『{skill_name}』汲取了 {heal} 点生命！")
        # v2.0 破防（pierce 数据字段）：直接给敌方降防
        if info.get("pierce") and self.enemy.get("hp", 0) > 0:
            self.e_buffs["def_down"] = E.skill_buff_turns(lv)
        # v2.0 核心资源：攻击技能获取（战士怒气/刺客连击点/拳师气，res_gain 覆盖默认）
        self._resource_on_skill(player, info, logs)
        # v130.2c 资源词条：技能命中（战意 on_skill / 充能汲引 on_cast 元素奥术技 / 连段回收 combo_skill）
        self._affix_res_proc(player, "on_skill", logs)
        if player.get("class_name", "") == "cls_fa_shi" and (info.get("element") or (info.get("res_gain") or {}).get("element")):
            self._affix_res_proc(player, "on_cast", logs)
        if info.get("combo"):
            self._affix_res_proc(player, "combo_skill", logs)
        # v130.2 资源增幅：技能出手命中（影袭药水 hits 制额外 +1 连击点等，仅命中；P0-1 消费端）
        if total > 0:
            _amp_hit = self._amp_resource(player, "on_land_hit")
            if _amp_hit:
                logs.append(f"⚡ 影袭药剂：出手命中额外资源 +{_amp_hit}！")
        # v130.2 刺客攻线·影舞者：技能命中 +1 连段 / 落空归零（断了重来）
        if self._combo_active(player):
            if total > 0:
                new_combo = self._combo_add(player)
                logs.append(f"🌪️ 连段 {new_combo}/{COMBO_CFG['cap']}")
            else:
                self._combo_break(player)
        # v130.2 暴击命中结算（on_crit：暮影影步/刺客攻线/星语猎印暴击额外）
        if total > 0 and is_crit:
            self._on_crit_resource(player)
            # v130.2c 资源词条：技能暴击命中（暴击蓄能 精力 +3 / 暴击回点 连击点概率 +1）
            self._affix_res_proc(player, "on_crit", logs)

        # ---- v10 套装攻击特效 ----
        if total > 0:
            self._set_attack_proc(player, total, logs)
        return logs

    # ---------------- v29 分支机制 ----------------
    def _mech_stack_bonus(self, mech: str, p_mech: dict, info: dict) -> float:
        """层数型机制对本次伤害的倍率（v125.2 B1：每层增伤查表 MECH_STACK_BONUS）
        v130.2 P1-5：隐藏线每层加成（dragon_might +18%/zen +12%，已并入 MECH_STACK_BONUS）——
        消耗型终极技（res_cost 含该核心资源键）按「施放前持有层数」叠乘（龙脉终曲 满龙力 ×2.8、
        撼岳·终焉 满禅意 ×2.2），读 self._pre_cost_res（见 _do_player_skill 快照，扣费后归 0 放不大）。"""
        step = MECH_STACK_BONUS.get(mech)
        if step:
            n = p_mech.get(mech, 0)
            if n:
                return 1.0 + n * step
        # v130.2：技能 res_cost 消费的核心资源键若在 MECH_STACK_BONUS 且非 mech 叠层型（dragon_might/zen），
        # 按其「施放前持有层数」补阶梯加成——mech 叠层型（rage/chi/shadow/spellblade，在 MECH_STACK_WHITELIST）
        # 层数存 mech_stacks 由上方 mech 分支结算，此处分流避免双重累加。
        rc = (info or {}).get("res_cost") or {}
        if rc:
            _pres = getattr(self, "_pre_cost_res", None)
            _pres = _pres if isinstance(_pres, dict) else None
            for _k, _step in MECH_STACK_BONUS.items():
                if _k in MECH_STACK_WHITELIST:
                    continue
                if int(rc.get(_k, 0) or 0) <= 0:
                    continue
                n = int(_pres.get(_k, 0) or 0) if _pres else int(self.resources.get(_k, 0) or 0)
                if n > 0:
                    return 1.0 + n * _step
        return 1.0

    def _cond_mult(self, info: dict, player: dict, lv: int = 1) -> float:
        """条件转化（v30）：按战场状态返回伤害倍率。
        cond 结构：{"type": "...", "hp_pct": 0.4, "mult": 1.6, "label": "处决狙击"}
        倍率随技能等级成长（v56）：每级 +0.05，lv 默认 1 保持向后兼容。
        v98.4：判定逻辑数据化 → core/battle_conds.py COND_CHECKS 注册表
        （22 种条件类型；未知 type 安全降级 1.0，与旧 elif 链兜底一致）
        """
        cond = info.get("cond")
        if not cond:
            return 1.0
        from .core.battle_conds import COND_CHECKS
        check = COND_CHECKS.get(cond.get("type"))
        if check and check(self, player, cond):
            return E.skill_cond_mult(cond, lv, info)
        return 1.0

    def _cond_active(self, info: dict, player: dict) -> bool:
        """v104 R3 P2-18：条件是否当前满足（与 _cond_mult 同判定，不关心倍率数值）。
        用于条件标签显示——mult=1.0 的纯条件技（如符文护体"魔能≥3"）此前因
        cond_mult>1.0 判定永不显示标签，玩家看不到条件存在。"""
        cond = info.get("cond")
        if not cond:
            return False
        from .core.battle_conds import COND_CHECKS
        check = COND_CHECKS.get(cond.get("type"))
        return bool(check and check(self, player, cond))

    def _apply_mech_gain(self, mech: str, mval: int, p_mech: dict, logs: list, skill_name: str):
        """增益类技能叠层(v59：封顶；v125.2 B1：可叠层 mech 白名单查表 MECH_STACK_WHITELIST)"""
        if mech and mval and mech in MECH_STACK_WHITELIST:
            p_mech[mech] = E.mech_stack_gain(mech, p_mech, mval)

    def _boss_ctrl_dur(self, key: str, val: int) -> int:
        """v120 审计修复 q5：敌方/BOSS 控制免疫·霸体——眩晕/冰冻/沉默/睡眠等控制效果
        作用在 Boss（敌方 dict is_boss 标记或 role=="boss"）上时时长减半（向下取整、至少 1 回合）。
        非 Boss 单位原样返回（不改变非 Boss 行为）。"""
        e = self.enemy or {}
        if not (e.get("is_boss") or e.get("role") == "boss"):
            return val
        return max(1, int(val) // 2)

    def _apply_mech_effect(self, mech: str, mval: int, p_mech: dict, total: int, logs: list, skill_name: str, is_crit: bool = False, info: dict | None = None):
        """攻击技能施放后的机制结算（v98.4：数据化 → core/battle_mech.py MECH_EFFECTS）
        v113.1：info（技能 dict）下传，handler 可读技能自带 mech_chance 固定概率。"""
        from .core.battle_mech import MECH_EFFECTS
        handler = MECH_EFFECTS.get(mech)
        if handler:
            handler(self, mval, p_mech, total, logs, skill_name, is_crit, info)
        # v120 审计修复 q5：玩家施加的控制（眩晕/冰冻/沉默）统一切入 Boss 控制抗性——
        # Boss 时长减半（至少 1 回合）；非 Boss 不变（handler 已设时长，此处术后收紧）。
        # v125.2 B1：控制白名单查表 CONTROL_MECHS
        if mech in CONTROL_MECHS:
            tgt = getattr(self, "_active_target", None) or self.enemy
            if tgt.get("is_boss") or tgt.get("role") == "boss":
                for k in CONTROL_MECHS:
                    if k in self.e_buffs:
                        self.e_buffs[k] = self._boss_ctrl_dur(k, self.e_buffs[k])
        # v2 控制打断蓄力：眩晕/冻结/沉默施加到蓄力目标 → 打断（§6.2规则4）
        if mech in CONTROL_MECHS:
            tgt = getattr(self, "_active_target", None) or self.enemy
            if tgt.get("charging"):
                self._interrupt_charging(tgt, logs, source=skill_name or self._last_hitter)

    # ---------------- v10 套装攻击特效 ----------------
    def _set_attack_proc(self, player: dict, dmg: int, logs: list):
        """玩家攻击后触发已激活套装的 4 件攻击特效
        v98.5：效果数据化 → core/affix_effects.py SET_PROC_EFFECTS"""
        effs = E.set_bonus_4(player.get("equipment", {}))
        if not effs:
            return
        from .core.affix_effects import SET_PROC_EFFECTS
        for eff in effs:
            fn = SET_PROC_EFFECTS.get(eff)
            if fn:
                fn(self, player, dmg, logs)

    # ---------------- 敌方回合 ----------------
    def _boss_dmg_filter(self, dmg: int, player: dict, logs: list, dmg_type: str = "phys", dot: bool = False) -> int:
        """v83 04 章 2.5：Boss 护盾/反伤过滤（挂在玩家伤害结算主路径）。
        shield：护盾存在期间受伤 -50%，先扣盾再扣血（破盾提示）。
        v110：真伤豁免 -50%（四层架构"真伤绕过全部减伤"），但护盾 HP 层仍吸收（仅护盾可吸收）。
        reflect：血量 <25% 反弹 15% 伤害给玩家。
        v93：worldboss 应用 GM 伤害倍率（gm_伤害 设置）。"""
        if self.btype == "worldboss" and self.dmg_mult != 1.0:
            dmg = int(dmg * self.dmg_mult)
            if dmg < 1:
                dmg = 1
        mech = self.enemy.get("mech")
        if self.btype == "pvp":
            return dmg
        mechs = [x.strip() for x in (mech or "").split(",") if x.strip()]
        e = self.enemy
        # v1.x：护盾双源——boss_shield（mech=shield，BOSS_MECHS 写入）与
        # e_buffs["shield"]（怪物增益技 effect=shield，MON_BUFF_EFFECTS 写入，如珊瑚护盾/铁壁/云盾）
        if "shield" in mechs or self.e_buffs.get("shield"):
            sh = e.get("boss_shield", 0)
            src = "boss_shield"
            if not sh:
                sh = int(self.e_buffs.get("shield", 0) or 0)
                src = "shield"
            if sh > 0:
                if dmg_type == "true":
                    absorbed = min(sh, dmg)  # 真伤不 -50%，护盾层仍吸收
                    sh -= absorbed
                else:
                    real = int(dmg * 0.5)
                    absorbed = min(sh, real)
                    sh -= absorbed
                    dmg = real
                if sh <= 0:
                    e.pop("boss_shield", None)
                    self.e_buffs.pop("shield", None)
                    logs.append("💥 护盾破碎！")
                elif src == "boss_shield":
                    e["boss_shield"] = sh
                else:
                    self.e_buffs["shield"] = sh
        if "reflect" in mechs:
            if not dot:  # v1.3 dot 只走护盾减半/吸收，不触发反射反伤
                ratio = e.get("hp", 0) / max(1, e.get("max_hp", 1))
                if ratio < 0.25:
                    rb = int(dmg * 0.15)
                    if rb > 0:
                        # R3 P2-3：反伤保底 1 HP（永不致死）——设计取舍：反伤是"代价"不是
                        # "处决"，避免残血玩家被反弹伤害补刀造成挫败；04 章机制表仅写"反弹 15%"
                        player["hp"] = max(1, player.get("hp", 1) - rb)
                        logs.append(f"🩸【{e['name']}】龙鳞反伤！你受到 {rb} 点反弹伤害！")
        return dmg

    def _boss_mech(self, logs: list, unit=None):
        """v58/v83 Boss 专属机制（04 章 2.5）：enrage/summon/heal/shield/phase/stacks/reflect
        支持逗号分隔多机制（如 "enrage,summon"）。状态存 enemy dict（随战斗序列化持久化）
        v98.4：机制实现数据化 → core/battle_mech.py BOSS_MECHS（reflect 仍是被动，在 _boss_dmg_filter）
        v2：unit 参数（多怪场景逐个单位触发自身 mech；缺省=主目标）。
        v116.1：新增条件反制机制开开场技(phase_open)/低血追击(player_low)/反扑(pv_broken)，
        phases 剧本化交给 _b_phase（换招/演出回合/阈值预告）。"""
        e = unit or self.enemy
        mech = e.get("mech")
        if not mech or self.btype == "pvp":
            return
        from .core.battle_mech import BOSS_MECHS
        mechs = [x.strip() for x in mech.split(",") if x.strip()]
        r = self.round
        for m in mechs:
            handler = BOSS_MECHS.get(m)
            if handler:
                handler(self, logs, e, r)

    def _boss_cfg(self, e: dict) -> dict:
        """v116.1：按 enemy id 从数据层解析 Boss 条件/剧本配置。
        优先取 enemy dict 自带的 scripts（数据层已直写），否则按 id 在 INSTANCES /
        MONSTER_MODS 找条目读 opening/triggers/phases/chains 字段。返回含缺省 key 的 dict。"""
        if not e:
            return {"opening": None, "triggers": {}, "phases": [], "chains": []}
        cfg = dict(e.get("scripts") or {})
        if not cfg:
            mid = (e.get("id") or "").strip()
            if mid:
                try:
                    from .data.monster_mods import MONSTER_MODS
                    from .data.instances import INSTANCES
                    src = INSTANCES.get(mid) or MONSTER_MODS.get(mid) or {}
                    for k in ("opening", "triggers", "phases", "chains"):
                        if src.get(k) is not None and (e.get("mech") or ""):
                            cfg[k] = src[k]
                except Exception:
                    cfg = {}
        cfg.setdefault("opening", None)
        cfg.setdefault("triggers", {})
        cfg.setdefault("phases", [])
        cfg.setdefault("chains", [])
        return cfg

    def _clear_reactive_flags(self, e: dict):
        """v116.1：清空反制/追击瞬态标记（敌方每回合开头调用，仅触发当回合生效）。"""
        if e is None:
            return
        e.pop("_low_hp_active", None)
        e.pop("_pv_broken_active", None)

    def _reactive_extra_attack(self, e: dict, pst: dict, logs: list) -> int:
        """v116.1 pv_broken 反扑：本回合追加一次普攻（趁你破绽）。返回追加伤害。"""
        if not e.get("_pv_broken_active"):
            return 0
        est = self._enemy_stats(e)
        xtra = E.calc_damage(est.get("atk", 0), pst.get("def", 0), False)
        logs.append(f"💢【{e['name']}】反扑的一击，追加 {xtra} 点伤害！")
        self._pending_dmg_lines.append(f"【{e['name']}】追加攻击，造成 {xtra} 点伤害！")
        return xtra

    def _enemy_turn(self, player: dict, unit=None) -> tuple:
        """敌方单个单位行动。返回 (日志列表, 对玩家伤害)。
        v2：unit 缺省 = 主目标（单怪兼容）；支持单位级蓄力。"""
        if self.btype == "pvp":
            return self._pvp_enemy_turn(player)
        e = unit or self.enemy
        eb = e.setdefault("buffs", {})
        ename = e.get("name", "怪物")
        logs = []
        # v2：本次敌方行动目标 = 该单位（_enemy_stats 默认按 _active_target 解析单位属性；
        # 兼容测试 monkeypatch 的 1 参 _enemy_stats）
        self._active_target = e
        # v116.1 反制/追击瞬态标记：每回合开头清空，仅本回合触发的回合生效
        self._clear_reactive_flags(e)
        self._boss_mech(logs, e)
        # v116.1 阶段演出回合：_b_phase 触发进入新阶段时设 battle._phase_skip_act，
        # 本回合 Boss 不行动（给玩家呼吸点），消费后立即复位避免影响后续回合/单位。
        if getattr(self, "_phase_skip_act", False):
            self._phase_skip_act = False
            logs.append(f"🎬 【{ename}】正在蜕变，尚未行动！")
            return logs, 0
        pst = self._player_stats(player)
        dmg = 0
        # v29 冻结：跳过敌方回合
        if "freeze" in eb:
            logs.append(f"❄️ 【{ename}】被冻结，无法行动！")
            eb.pop("freeze", None)
            return logs, 0
        # v63 眩晕
        if "stun" in eb:
            logs.append(f"🌀 【{ename}】被眩晕，无法行动！")
            eb.pop("stun", None)
            return logs, 0
        # v109.2 P1-3：睡眠（受击解除，按回合递减）
        # v121 审计修复：回合递减只由 _end_round 统一执行（每玩家行动 1 次）——
        # 此分支此前每次被选中行动都 -1，CTB 连动下睡眠一回合被多重递减直接清零
        if "sleep" in eb:
            logs.append(f"💤 【{ename}】陷入沉睡，无法行动！")
            return logs, 0
        est = self._enemy_stats()
        # v2 敌方蓄力单位：left-1；归零自动释放技能（结算效果，不普攻）
        if e.get("charging"):
            return self._enemy_charge_tick(e, pst, est, logs, ename)
        # 30% 概率使用技能（v63：沉默时只能普攻）
        skill = None
        silenced = "silence" in eb
        if e.get("skills") and random.random() < C.MON_SKILL_CHANCE and not silenced:
            skill = random.choice(e["skills"])
            sinfo = C.MONSTER_SKILLS.get(skill)
            if sinfo:
                sname = sinfo.get("name", skill)  # 显示中文名
                kind = sinfo.get("kind")
                # v116 敌方蓄力接线：抽中带 charge 的技能且敌方未在蓄力 → 进入蓄力
                # （本回合不结算伤害，先给意图预告，之后回合由 _enemy_charge_tick 结算）
                charge_n = int(sinfo.get("charge", 0) or 0)
                if charge_n > 0 and not e.get("charging"):
                    e["charging"] = {"skill": skill, "left": charge_n, "name": sname}
                    logs.append(
                        f"⚠️ 【意图】{ename} 正在蓄力【{sname}】！下回合将造成大伤害——"
                        f"可『防御』减半或『打断技』赌它读条失败！")
                    return logs, 0
                if kind == "增益":
                    from .core.battle_mech import MON_BUFF_EFFECTS
                    eff = sinfo.get("effect")
                    eff_fn = MON_BUFF_EFFECTS.get(eff)
                    if eff_fn:
                        eff_fn(self, logs, sname)
                    return logs, 0
                power = sinfo.get("power", 1.0)
                # v104 M02 P2-10：怪物技能暴击按自身 crit 判定；v106 韧性
                is_crit = random.random() < est.get("crit", C.MON_SKILL_CRIT) * self._tenacity_mult(pst)
                if kind == "物理":
                    _pp, _pf = self._pene_vals(est)
                    dmg = E.calc_damage(int(est["atk"] * power), pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf,
                                        dmg_type="phys")
                    _pst_pr = self._player_stats(player)
                    pr = min(float(_pst_pr.get("phys_reduce", 0) or 0), 0.4)
                    if pr > 0:
                        red = max(1, int(dmg * pr))
                        dmg = max(1, dmg - red)
                        logs.append(f"🪨 物理免伤，减免 {red} 点物理伤害！")
                else:
                    _pp, _pf = self._pene_vals(est, magic=True)
                    dmg = E.calc_damage(int(est["matk"] * power), pst["mdef"], is_crit, pene_pct=_pp, pene_flat=_pf,
                                        dmg_type="magi")
                    if kind != "物理":
                        _pst_mr = self._player_stats(player)
                        mr = float(_pst_mr.get("magic_reduce", 0) or 0)
                        if self.p_buffs.get("magic_resist"):
                            mr = 1 - (1 - mr) * (1 - 0.15)
                        mr = min(mr, 0.4)
                        if mr > 0:
                            red = max(1, int(dmg * mr))
                            dmg = max(1, dmg - red)
                            logs.append(f"🛡️ 魔法免伤，减免 {red} 点伤害！")
                        elif mr < 0:
                            red = max(1, int(dmg * -mr))
                            dmg = dmg + red
                            logs.append(f"🔥 鲁莽之心，额外受到 {red} 点伤害！")
                # 元素抗性减免
                melem = sinfo.get("element", "")
                if melem:
                    resist = 0.0
                    pids = self._equip_affix_ids(player)
                    try:
                        _pst_el = self._player_stats(player)
                        elem_attr = min(float(_pst_el.get("elem_res", 0) or 0), 0.5)
                        abyss_attr = min(float(_pst_el.get("abyss_res", 0) or 0), 0.5)
                    except Exception:
                        elem_attr = abyss_attr = 0.0
                    if melem in ("fire", "ice", "thunder"):
                        resist = elem_attr
                        if "elem_resist" in pids and elem_attr < 0.08:
                            resist += 0.08 - elem_attr
                    elif melem == "dark":
                        resist = abyss_attr
                        if "abyss_resist" in pids and abyss_attr < 0.10:
                            resist += 0.10 - abyss_attr
                    if resist > 0:
                        red = max(1, int(dmg * resist))
                        dmg = max(1, dmg - red)
                        logs.append(f"🛡️ 元素抗性减免 {red} 点伤害！")
                # O116 延迟输出
                self._pending_dmg_lines.append(
                    f"【{ename}】使用了【{sname}】，对你造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
                # v63 怪物技能控制
                mmech = sinfo.get("mech")
                if mmech:
                    from .core.battle_mech import MON_CTRL_EFFECTS
                    ctrl_fn = MON_CTRL_EFFECTS.get(mmech)
                    if ctrl_fn:
                        mval = int(sinfo.get("mech_val", 1) or 1)
                        ctrl_fn(self, player, logs, mval)
                dmg += self._reactive_extra_attack(e, pst, logs)
                return logs, dmg
        # 怪物普攻
        is_crit = random.random() < est.get("crit", 0.05) * self._tenacity_mult(pst)
        _pp, _pf = self._pene_vals(est)
        dmg = E.calc_damage(est["atk"], pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf)
        _pst_pr = self._player_stats(player)
        pr = min(float(_pst_pr.get("phys_reduce", 0) or 0), 0.4)
        if pr > 0:
            red = max(1, int(dmg * pr))
            dmg = max(1, dmg - red)
            logs.append(f"🪨 物理免伤，减免 {red} 点物理伤害！")
        self._pending_dmg_lines.append(
            f"【{ename}】攻击你，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        dmg += self._reactive_extra_attack(e, pst, logs)
        return logs, dmg

    def _enemy_charge_tick(self, e: dict, pst: dict, est: dict, logs: list, ename: str) -> tuple:
        """敌方蓄力单位回合：left-1；归零自动释放技能（结算效果，不普攻）。"""
        ch = e.get("charging") or {}
        left = int(ch.get("left", 1) or 1)
        cname = ch.get("name", ch.get("skill", "?"))
        if left > 0:
            ch["left"] = max(0, left - 1)
            e["charging"] = ch if ch["left"] > 0 else None
            if ch["left"] == 0:
                # 蓄力完成释放：意图预告（释放回合）+ 立即结算（传技能 key 供查表）
                logs.append(f"✨ 【{ename}】的【{cname}】蓄力完成，轰然落下！")
                # 释放 = 结算一次该单位的技能效果（无目标次要：对玩家造成伤害）
                return self._enemy_release_charge(e, ch.get("skill") or cname, pst, est, logs, ename)
            # 蓄力持续回合：精简意图预告（剩 N）
            logs.append(f"⚠️ 【意图】{ename} 蓄力中(剩 {ch['left']})！")
            return logs, 0
        return logs, 0

    def _enemy_release_charge(self, e: dict, skill_name: str, pst: dict, est: dict, logs: list, ename: str) -> tuple:
        """敌方蓄力释放：按 MONSTER_SKILLS 里的技能结算伤害（对整个玩家方）。
        返回 (logs, 对玩家伤害)。"""
        sinfo = C.MONSTER_SKILLS.get(skill_name) or {}
        if not sinfo:
            return logs, 0
        kind = sinfo.get("kind")
        power = sinfo.get("power", 1.0)
        is_crit = random.random() < est.get("crit", C.MON_SKILL_CRIT) * self._tenacity_mult(pst)
        sname = sinfo.get("name", skill_name)
        if kind == "增益":
            from .core.battle_mech import MON_BUFF_EFFECTS
            eff_fn = MON_BUFF_EFFECTS.get(sinfo.get("effect"))
            if eff_fn:
                eff_fn(self, logs, sname)
            return logs, 0
        if kind == "物理":
            _pp, _pf = self._pene_vals(est)
            dmg = E.calc_damage(int(est["atk"] * power), pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf,
                                dmg_type="phys")
        else:
            _pp, _pf = self._pene_vals(est, magic=True)
            dmg = E.calc_damage(int(est["matk"] * power), pst["mdef"], is_crit, pene_pct=_pp, pene_flat=_pf,
                                dmg_type="magi")
        self._pending_dmg_lines.append(
            f"【{ename}】的【{sname}】对你造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        return logs, max(0, dmg)

    def _pvp_enemy_turn(self, player: dict) -> tuple:
        """PVP：敌方玩家行动(v9.2 启用；先实现 AI 普攻)。

        ⚠️ v110 审计标注（D20）：真实 PVP 中不可达——PVP 战斗 `enemy_act` 恒 False
        （battle 回合由双方玩家轮流操作，无 AI 回合），本函数仅经 _enemy_turn 的
        `if enemy_act:` 分支挂接，属僵尸分支（保留以防未来 PVP 挂机 AI 使用）。
        """
        est = self._enemy_stats()
        pst = self._player_stats(player)
        logs = []
        # v106 韧性：被暴击率 × (1 - 玩家韧性)；穿透：PVP 敌方玩家快照的物穿生效（双向）
        is_crit = random.random() < est.get("crit", 0.05) * self._tenacity_mult(pst)
        _pp, _pf = self._pene_vals(est)
        dmg = E.calc_damage(est["atk"], pst["def"], is_crit, pene_pct=_pp, pene_flat=_pf)
        # v106.4 物理免伤统一属性结算（PVP 同口径）
        _pst_pr = self._player_stats(player)
        pr = min(float(_pst_pr.get("phys_reduce", 0) or 0), 0.4)
        if pr > 0:
            red = max(1, int(dmg * pr))
            dmg = max(1, dmg - red)
            logs.append(f"🪨 物理免伤，减免 {red} 点物理伤害！")
        # O116 伤害文案延迟输出（闪避判定后），避免"造成伤害"与"闪避"同显
        self._pending_dmg_lines.append(
            f"【{self.enemy['name']}】向你发起攻击，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        return logs, dmg

    # ---------------- 状态修正 ----------------
    def _apply_buffs(self, st: dict, buffs: dict) -> dict:
        st = dict(st)
        for eff, turns in buffs.items():
            if eff in BUFF_MULT:
                attr, val = BUFF_MULT[eff]
                # v104 M17 P2-5：宠物 buff（buff_atk/crit_up）实读 PET_POOL skill_value，
                # 覆盖 BUFF_MULT 常量（此前日志 25% 实际 30%，数据层承诺"加宠物=加一行"失效）
                if attr in ("atk", "crit"):
                    _pv = getattr(self, "_pet_buff_vals", {}).get(attr)
                    if _pv is not None:
                        val = 1.0 + _pv if attr == "atk" else _pv
                if attr == "crit":
                    # v110 §三：暴击率上限统一 0.5（原 min(1.0) 可到 100%，与设计 50% 上限不符）
                    st["crit"] = min(C.PCT_CAPS.get("crit", 0.5), st.get("crit", 0) + val)
                else:
                    st[attr] = int(st.get(attr, 0) * val)
        return st

    def _enemy_stats(self, unit=None) -> dict:
        """敌方当前属性(应用敌方增益/减益)。v2：unit 缺省=主目标（单怪兼容）。"""
        if unit is None:
            unit = getattr(self, "_active_target", None) or self.enemy
        e = unit
        eb = e.setdefault("buffs", {})
        est = {
            "atk": e.get("atk", 0), "def": e.get("def", 0),
            "matk": e.get("matk", 0), "mdef": e.get("mdef", 0),
            "spd": e.get("spd", 0), "crit": e.get("crit", 0.05),
            # v109.2 PVP 韧性对称：敌方玩家快照 tenacity 传入 est（玩家攻击端暴击率 ×(1-敌韧)）
            "tenacity": e.get("tenacity", 0) or 0,
            # v110 P1-3：敌方防守属性聚合（PVP 玩家攻击端消费；PVE 怪无这些键=0 无感）
            "block": e.get("block", 0) or 0, "dodge": e.get("dodge", 0) or 0,
            "phys_reduce": e.get("phys_reduce", 0) or 0, "magic_reduce": e.get("magic_reduce", 0) or 0,
            "elem_res": e.get("elem_res", 0) or 0, "abyss_res": e.get("abyss_res", 0) or 0,
            "precise": e.get("precise", 0) or 0,
        }
        est = self._apply_buffs(est, eb)
        # v58 Boss 狂暴：血量 <30% 触发后攻击 +35%（v125.2 B1：乘区查表 BOSS_ATTACK_MULTS）
        if e.get("enraged"):
            est["atk"] = int(est["atk"] * BOSS_ATTACK_MULTS["enraged"])
            est["matk"] = int(est["matk"] * BOSS_ATTACK_MULTS["enraged"])
        # v83 04 章 2.5：多阶段（每阶段 +20%）/ 叠层强化（每层 +8%）
        if e.get("phase_count"):
            pm = 1 + BOSS_ATTACK_MULTS["phase_step"] * e["phase_count"]
            est["atk"] = int(est["atk"] * pm)
            est["matk"] = int(est["matk"] * pm)
        # v116.1 条件触发反制：玩家低血追击(+25%) / 玩家大招反扑(+30%)——仅受击当回合生效
        if e.get("_low_hp_active"):
            est["atk"] = int(est["atk"] * BOSS_ATTACK_MULTS["low_hp"])
            est["matk"] = int(est["matk"] * BOSS_ATTACK_MULTS["low_hp"])
        if e.get("_pv_broken_active"):
            est["atk"] = int(est["atk"] * BOSS_ATTACK_MULTS["pv_broken"])
            est["matk"] = int(est["matk"] * BOSS_ATTACK_MULTS["pv_broken"])
        if e.get("mech_stacks_n"):
            sm = 1 + BOSS_ATTACK_MULTS["stack_step"] * e["mech_stacks_n"]
            est["atk"] = int(est["atk"] * sm)
        if "def_down" in eb:
            # 阶段八：词条破甲 15%（_armor_break_pct），旧技能破甲减半兜底
            pct = float(eb.get("_armor_break_pct", DEF_DOWN_MULT) or DEF_DOWN_MULT)
            est["def"] = int(est["def"] * (1 - pct))
        if "spd_down" in eb:
            est["spd"] = int(est["spd"] * SPD_DOWN_MULT)
        # v34 符文虚弱：敌人攻击 -x%
        if "mon_atk_down" in eb:
            wv = float(eb.get("_weaken_val", 0.15) or 0.15)
            est["atk"] = int(est["atk"] * (1 - wv))
            est["matk"] = int(est["matk"] * (1 - wv))
        # v120 审计修复 q5：敌方攻强总帽——enrage/phase/stacks/low_hp/pv_broken/atk_up 等
        # 乘区叠加后不得突破 3.0×该单位基础 atk/matk，防满配置 BOSS 一击秒杀。
        # 帽值 3.0 的道理：狂暴1.35×阶段(如×1.4)×叠层(如×1.24)×低血1.25 等真实可同时叠加的
        # 乘区乘积上限大致落在 2~3 倍内，取 3.0 保正常配装强度不受钳制，仅拦极端叠加秒杀。
        for _k in ("atk", "matk"):
            _base = max(0, int(e.get(_k, 0) or 0))
            if _base > 0:
                est[_k] = min(est[_k], int(_base * BOSS_ATTACK_MULTS["cap"]))
        # v1.1 毒蚀（契约 §10.1）：每层毒使目标防御/魔防 -4%（上限 20%），
        # 层数衰减时自动恢复（动态计算，不改 enemy dict 本体）
        _poison_n = int((e.get("debuffs") or {}).get("poison", {}).get("n", 0) or 0)
        if _poison_n > 0:
            _erode = min(0.20, _poison_n * 0.04)
            est["def"] = int(est["def"] * (1 - _erode))
            est["mdef"] = int(est["mdef"] * (1 - _erode))
        return est

    def _enemy_mitigate(self, dmg: int, magi_part: int, element: str | None, logs: list, kind: str = "物理",
                        dot: bool = False) -> tuple:
        """v110 P1-3：玩家攻击端消费敌方防守属性（与 _pvp_enemy_turn 玩家受击口径对称）。
        物理段吃敌方物免(≤40%)+格挡(≤40%，命中物段减半)；魔法段吃敌方魔免(≤40%)+元素抗(≤40%，按元素)。
        真伤绕过全部减伤（四层架构）；dot=True 时跳过格挡 roll（持续伤害不触发格挡事件）。
        PVE 标准怪无这些键(=0) → 伤害不变。
        返回 (削减后伤害, 削减后魔段)（魔段回传供吸血分账）。"""
        if kind == "真伤":
            return dmg, magi_part
        est = self._enemy_stats()
        if kind == "魔法":
            phys, magi = 0, dmg
        else:
            phys, magi = max(0, dmg - magi_part), magi_part
        reduced = 0
        pr = min(float(est.get("phys_reduce", 0) or 0), 0.4)
        if pr > 0 and phys > 0:
            red = max(1, int(phys * pr))
            phys -= red
            reduced += red
        if not dot:
            bc = min(float(est.get("block", 0) or 0), 0.4)
            if bc > 0 and phys > 0 and random.random() < bc:
                red = max(1, int(phys * 0.5))
                phys -= red
                reduced += red
                logs.append("🛡️ 敌人格挡了攻击！")
        mr = min(float(est.get("magic_reduce", 0) or 0), 0.4)
        if mr > 0 and magi > 0:
            red = max(1, int(magi * mr))
            magi -= red
            reduced += red
        if element and E.ELEMENT_MARKS.get(element):
            # v110 审计修复：cap 0.4 → 0.5（对齐防御端 _enemy_turn / PCT_CAPS["elem_res"]=0.5 /
            # 设计 §三「元素抗上限 50%」；此前 PVP 敌方元素抗 40%~50% 段在玩家攻击端被截断）
            er = min(float(est.get("elem_res", 0) or 0), 0.5)
            if er > 0 and magi > 0:
                red = max(1, int(magi * er))
                magi -= red
                reduced += red
        if reduced > 0:
            logs.append(f"🛡️ 敌方防守削减 {reduced} 点伤害！")
        return max(0, phys + magi), magi

    def _apply_mark(self, dmg: int) -> int:
        """标记易伤（v1.1 按层，契约 §10.1）：每层 +20%（5 层 +100%，对齐设计 27章:305）。
        e_buffs["mark"] 计时窗口保留（由 _m_mark 写入），层数在 enemy.debuffs 随回合衰减。"""
        n = int((self.enemy.get("debuffs") or {}).get("mark", {}).get("n", 0) or 0)
        if n > 0:
            return int(dmg * (1 + 0.20 * n))
        return dmg

    def _pet_skill_turn(self, player: dict, logs: list) -> list:
        """24 章宠物技能：每 N 回合自动触发（不占玩家行动、不消耗 MP）。
        撕咬(atk_pct)/龙息(matk_pct)/月光祝福(heal_pct) 在玩家回合开始触发；
        影袭(block) 在 _damage_player 前拦截（见 _pet_block_check）。
        Lv.10 解锁；饱食度 =0 时技能失效。
        """
        pet = self.pet or {}
        if not pet:
            return logs
        if int(pet.get("level", 0)) < 10:
            return logs
        if int(pet.get("satiety", 0)) <= 0:
            return logs
        pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
        if not pdef:
            return logs
        interval = int(pdef.get("skill_interval", 0) or 0)
        if interval <= 0 or self.round % interval != 0:
            return logs
        stype = pdef.get("skill_type")
        pname = pet.get("name") or pdef["name"]
        sname = pdef["skill_name"]
        line = C.pet_line(pdef["key"])  # v101.11 宠物战斗台词
        # v125.1 P2-2：按 PET_SKILL_EFFECTS 注册表分发（原 if/elif 链，数值读 PET_POOL 数据）
        handler = PET_SKILL_EFFECTS.get(stype)
        if handler:
            handler(self, player, pdef, pname, sname, line, logs)
        return logs

    def _pet_block_check(self, dmg: int, logs: list) -> int:
        """24 章宠物技能·影袭：每 N 回合 value 概率替主人挡一次攻击(敌方伤害结算前)。"""
        if dmg <= 0:
            return dmg
        pet = self.pet or {}
        if not pet:
            return dmg
        if int(pet.get("level", 0)) < 10:
            return dmg
        if int(pet.get("satiety", 0)) <= 0:
            return dmg
        pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
        if not pdef or pdef.get("skill_type") != "block":
            return dmg
        interval = int(pdef.get("skill_interval", 0) or 0)
        if interval <= 0 or self.round % interval != 0:
            return dmg
        if random.random() < pdef.get("skill_value", 0):
            pname = pet.get("name") or pdef["name"]
            logs.append(f"🐾 {pname}的【{pdef['skill_name']}】替你挡下了这次攻击！")
            return 0
        return dmg

    def _tick_dots(self, player: dict, logs: list, force: bool = False) -> list:
        """DOT 重构（契约 §2.2 + §10.1 + §11.1）：敌方持续减益（毒/灼烧/流血）统一结算。

        每次结算（每层每回合混合公式）：
          poison = (atk×0.5 + max_hp×1.5%) × n × mult
          burn   = (matk×0.4 + max_hp×1.0%) × n × mult
          bleed  = (atk×0.6 + max_hp×1.5%) × n × mult（目标当前生命 <30% 时 ×2，放血）
        随后经 敌方防守削减(_enemy_mitigate) → Boss 护盾过滤(_boss_dmg_filter)；
        结算后层数 n-1，归零消散。总抗 = min(0.95, dot_res + 适应adapt[k])；
        poison/burn 最近 2 回合未再叠层时适应 -4%（耐受消退）。
        免疫列表 immune_dots 命中类型直接移除不结算。

        - 伤害类型：毒/灼烧=magi，流血=phys
        - 灼烧走 fire 元素抗、毒不吃元素抗、流血吃物理物免
        - 结算频率：单机每玩家行动一次（_dot_pending 闸门）；副本/世界 Boss 由命令层控制
        - force=True（世界 Boss 全局多行动一次）时跳过闸门
        文案按类型区分：毒发身亡 / 灼烧致死 / 失血过多；死亡后 break。
        """
        if not force:
            if not getattr(self, "_dot_pending", True):
                return logs
            self._dot_pending = False
        e = self.enemy or {}
        deb = e.get("debuffs") or {}
        if not deb:
            return logs
        max_hp = int(e.get("max_hp", 1) or 1)
        immune = e.get("immune_dots") or []
        # v1.1 混合公式：施放者攻击快照（防御性取数，失败按 0 处理只留生命部分）
        try:
            _st = self._player_stats(player)
            _atk = max(0, int(_st.get("atk", 0) or 0))
            _matk = max(0, int(_st.get("matk", 0) or 0))
        except Exception:
            _atk = _matk = 0
        # 每层每回合混合公式：poison=atk×0.5+max_hp×1.5% / burn=matk×0.4+max_hp×1% / bleed=atk×0.6+max_hp×1.5%
        # v125.2 B1：系数下沉 data/battle_config.py DOT_DEFS（纯数据）
        _atk_parts = {_k: _v["atk"] for _k, _v in DOT_DEFS.items()}
        _matk_parts = {_k: _v["matk"] for _k, _v in DOT_DEFS.items()}
        _hp_parts = {_k: _v["hp"] for _k, _v in DOT_DEFS.items()}
        for k in DOT_DEFS:
            d = deb.get(k)
            if not d:
                continue
            n = int(d.get("n", 0) or 0)
            if n <= 0:
                deb.pop(k, None)
                continue
            # 免疫：命中该类型时直接移除该层并提示免疫，不结算伤害
            if k in immune:
                deb.pop(k, None)
                logs.append(f"🛡️ 【{e.get('name', '敌人')}】免疫{('中毒' if k == 'poison' else '灼烧' if k == 'burn' else '流血')}，减益消散了！")
                continue
            mult = float(d.get("mult", 1.0) or 1.0)
            # v1.2 总抗：基础抗性 + 减益适应（cap 0.95）
            base_res = float(e.get("dot_res", 0) or 0)
            adapt_v = float((e.get("adapt") or {}).get(k, 0.0) or 0.0)
            res = min(DOT_RESIST_CAP, base_res + adapt_v)
            # v1.1 混合公式：每层 = (攻击系数 + 最大生命小百分比) × 层数 × 被动倍率 × (1 - 总抗)
            atk_part = _atk * _atk_parts[k] + _matk * _matk_parts[k]
            hp_part = max_hp * _hp_parts[k]
            p = int((atk_part + hp_part) * n * mult * (1 - res))
            # 伤害段：灼烧=magi 走火元素抗；毒=magi 不吃元素抗；流血=phys 吃物理物免
            if k == "burn":
                dt = "magi"
                p, _ = self._enemy_mitigate(p, p, "fire", logs, kind="魔法", dot=True)
            elif k == "poison":
                dt = "magi"
                p, _ = self._enemy_mitigate(p, p, None, logs, kind="魔法", dot=True)
            else:
                dt = "phys"
                p, _ = self._enemy_mitigate(p, 0, None, logs, kind="物理", dot=True)
            # v83 Boss 护盾过滤：盾/吸收对 dot 生效（护盾 -50%）；dot 不触发反射反伤
            p = self._boss_dmg_filter(p, player, logs, dmg_type=dt, dot=True)
            # v1.1 放血：目标当前生命 <30%（处决线）时流血伤害 ×2（处决/斩杀联动）
            # v125.2 B1：阈值查表 DOT_BLEED_DOUBLE_HP_PCT
            _bleed_tag = ""
            if k == "bleed" and e.get("hp", 0) < max_hp * DOT_BLEED_DOUBLE_HP_PCT:
                p *= 2
                _bleed_tag = "(放血)"
            if p > 0:
                self._damage_enemy(p, logs, wake_sleep=False, target=e)  # dot 不打醒睡眠、不打断蓄力
            kname = "毒" if k == "poison" else "灼烧" if k == "burn" else "流血"
            _mult_tag = f"(强化×{mult:.1f})" if mult != 1.0 else ""
            logs.append(f"{'☠️' if k == 'poison' else '🔥' if k == 'burn' else '🩸'} 【{e.get('name', '敌人')}】{kname}发作，损失 {p} 点生命！(剩余 {n - 1} 层){_mult_tag}{_bleed_tag}")
            n -= 1
            if n <= 0:
                deb.pop(k, None)
                logs.append(f"💨 【{e.get('name', '敌人')}】的{kname}消散了！")
            else:
                d["n"] = n
            # v1.2 适应回落：poison/burn 最近 2 回合未再叠层 → 该类型适应 -4%（耐受消退）
            # v125.2 B1：步长查表 DOT_ADAPT_DECAY_STEP
            if k in ("poison", "burn"):
                _last = int(d.get("last_round", 0) or 0)
                if _last > 0 and self.round - _last >= 2:
                    _am = e.setdefault("adapt", {})
                    _am[k] = max(0.0, float(_am.get(k, 0.0) or 0.0) - DOT_ADAPT_DECAY_STEP)
            if self._enemy_dead():
                self.result = "victory"
                death_text = ("毒发身亡" if k == "poison" else "灼烧致死" if k == "burn" else "失血过多")
                logs.append(f"🎉 你击败了【{e.get('name', '敌人')}】！({death_text})")
                break
        # v1.3 标记层与 dot 同生命周期：每回合结算后 n-1，归零移除（与 e_buffs["mark"] 2 回合计时同步）
        _mk = deb.get("mark")
        if _mk:
            _mn = int(_mk.get("n", 0) or 0) - 1
            if _mn <= 0:
                deb.pop("mark", None)
            else:
                _mk["n"] = _mn
        return logs

    def _tailwind_regen_bonus(self, player: dict) -> int:
        """v130.2d 疾风余韵：上回合结束时精力 ≥80 → 本回合精力自然回复 +10（词条 effect.regen）。
        跨回合状态由 _end_round 记录 _tailwind_prev_energy（每战初始化 None，随战斗序列化）。"""
        _prev = getattr(self, "_tailwind_prev_energy", None)
        if _prev is None or int(_prev or 0) < int(ENERGY_HIGH.get("threshold", 80) or 80):
            return 0
        if "swift_tailwind" not in self._equip_affix_ids(player):
            return 0
        bonus = 0
        for eff, tier in self._affix_effs(player, "swift_tailwind"):
            if not eff:
                continue
            v = int(tier if tier is not None else eff.get("regen", 0) or 0)
            if v > 0:
                bonus += v
        return bonus

    def _turn_start(self, player: dict) -> list:
        """回合开始：持续伤害结算 + v10 套装每回合回复"""
        logs = []
        # DOT 重构（契约 §2.1/§2.2）：敌方持续减益（毒/灼烧/流血）统一由 _tick_dots 结算。
        # _tick_dots 内部持有 _dot_pending 闸门——单机探索怪（btype=monster）与 PVP 每次玩家行动=一回合，
        # 回合开始复位闸门 → 每行动结算一次（与现状频率一致）；副本（instance）每轮结算一次的
        # 闸门由 from_state 按 st["dot_pending"] 恢复，世界 Boss（worldboss）由 combat 层 force 结算，
        # 故此两模式不在此复位。
        if self.btype in ("monster", "pvp"):
            self._dot_pending = True
        # 原地追加（_tick_dots 向传入 logs 追加文案并返回同一列表，勿用 += 以免二次自拼接）
        self._tick_dots(player, logs)
        # 阶段八：词条回合开始回复（回春/冥想/晨曦祝福）
        self._affix_turn_start(player, logs)
        self._food_turn_start(player, logs)
        # v130.2c 暗夜圣典 2 件：场上亡灵≥1 时 悼咏积攒 +1（回合开始）
        self._set_res_proc(player, "undead_on_field", logs)
        # 圣光/永恒套：每回合开始回复生命
        for eff in E.set_bonus_4(player.get("equipment", {})):
            if eff in ("regen", "regen_strong") and player.get("hp", 0) < player.get("max_hp", 1):
                pct = 0.05 if eff == "regen" else 0.08
                heal = int(player.get("max_hp", player.get("hp", 1)) * pct)
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"✨ 套装祝福生效，你回复了 {heal} 点生命！")
                break
        # v104 M07 修复 P1：星尘套 5 件——夜间每回合回蓝 5%（10 章五节；夜间 = 19:00-06:00 服务器本地时间）
        if "星尘" in "|".join(self._set_bonus_5(player)) and player.get("mp", 0) < player.get("max_mp", 1):
            _hour = time.localtime().tm_hour
            if _hour >= 19 or _hour < 6:
                gain = int(player.get("max_mp", player.get("mp", 1)) * 0.05)
                player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + gain)
                logs.append(f"🌙 星尘祝福：夜风拂过，你回复了 {gain} 点魔力！({player['mp']}/{player.get('max_mp', '?')})")
        # v34 符文·治愈：每回合回复 x% 生命
        regen_lvl = self._enchant_lvl(self._enchant_effects(player), "regen")
        if regen_lvl and player.get("hp", 0) < player.get("max_hp", 1):
            heal = int(player.get("max_hp", player.get("hp", 1)) * C.rune_value("regen", regen_lvl))
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
            logs.append(f"✨ 符文治愈生效，你回复了 {heal} 点生命！")
        # v109.2 P2-9：气力调和每回合回血 2%（proc turn_heal，原按技能名硬编码——v109.1 改名即断链事故源）
        for _pn, _ps in self._passive_map(player)["proc"].get("turn_heal", []):
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * float(_ps.get("pct", 0.02)))
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"🍃 {_pn}生效，你回复了 {heal} 点生命！")
            break
        # v104 R3 P1-1：生命之泉——全队每回合回血 5%（单人战斗=自身，副本由 instance 广播）
        for _pn, _ps in self._passive_map(player)["proc"].get("team_regen", []):
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * float(_ps.get("mult", 0.05)))
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"💧 {_pn}：生命之泉涌动，你回复了 {heal} 点生命！")
            break
        # v109.2 P2-9：奥术直觉/符文刻印 每回合自动充能（proc arcane_regen / stat spellblade_regen，
        # 原按技能名硬编码——改名即失效风险同款）
        # v125.1 P2-3：mech 键读被动数据 mech 字段（skills.py 奥术直觉 passive.mech="arcane"），
        # 不再按 proc 名写死 mech_stacks 键
        for _pn, _ps in self._passive_map(player)["proc"].get("arcane_regen", []):
            _mech = _ps.get("mech") or "arcane"  # 兜底保旧行为
            self.mech_stacks[_mech] = E.mech_stack_gain(_mech, self.mech_stacks, 1)
            logs.append(f"📖 {_pn}：充能自动+1(当前 {self.mech_stacks[_mech]} 层)")
            break
        for _pn, _ps in self._passive_map(player)["stat"]:
            # v113 魔剑士流派已删：spellblade_regen 无数据（保留兼容分支，mech 键同样读数据字段）
            if _ps.get("stat") == "spellblade_regen":
                _mech = _ps.get("mech") or "spellblade"  # 兜底保旧行为
                self.mech_stacks[_mech] = E.mech_stack_gain(_mech, self.mech_stacks, 1)
                logs.append(f"⚔️ {_pn}：魔能自动+1(当前 {self.mech_stacks[_mech]} 层)")
                break
        # v2.0 核心资源：回合回复（游侠精力 +25/回合）
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if rd and rd.get("regen", 0) > 0:
            k = rd["key"]
            old = int(self.resources.get(k, 0) or 0)
            # v130.2c 词条上限：自然回走 _res_gain（盈满背囊上限 +10/20 生效，行为与旧路径零差异）
            new = self._res_gain(player, k, int(rd.get("regen", 0) or 0))
            if new > old:
                logs.append(f"🍃 {rd['name']}回复 {new - old} 点({new}/{self._res_max(player, k)})")
            # v130.2d 疾风余韵：上回合结束时精力 ≥80 → 本回合自然回复 +10（读词条 effect.regen）
            if k == "energy":
                _tw_bonus = self._tailwind_regen_bonus(player)
                if _tw_bonus > 0:
                    _old2 = int(self.resources.get(k, 0) or 0)
                    _new2 = self._res_gain(player, k, _tw_bonus)
                    if _new2 > _old2:
                        logs.append(f"🌈 疾风余韵：上回合精力满弦，本回合回复 +{_new2 - _old2} 点{rd['name']}！")
        # v130.2 资源增幅：自然回触发（迅捷之核 本回合精力额外 +30，P0-1 消费端）
        _amp_pt = self._amp_resource(player, "regen")
        if _amp_pt:
            logs.append(f"⚡ 迅捷之核：自然回复额外资源 +{_amp_pt}！")
        # v130.2 歌者回声驻留：每层回合初始全队恢复 6 体力（priest_转职.md §3.0）
        echo_n = self._echo_layers()
        if echo_n > 0:
            _heal_e = int(ECHO_CFG.get("heal_per_layer", 6) or 6) * echo_n
            if echo_n >= int(ECHO_CFG.get("max_layers", 3) or 3):
                _heal_e *= 2  # 策划案 12 章 5.1.1：回声满层时每层恢复翻倍（3 层=36/回合）
            if player.get("hp", 0) < player.get("max_hp", 1):
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + _heal_e)
                logs.append(f"🎵 回声余韵：全队恢复 {_heal_e} 点体力({echo_n} 层)")
            for _ally in (self.allies or []):
                if isinstance(_ally, dict) and _ally.get("hp", 0) < _ally.get("max_hp", 1):
                    _ally["hp"] = min(_ally.get("max_hp", _ally.get("hp", 1)), _ally.get("hp", 0) + _heal_e)
        return logs

    def _end_round(self):
        """回合结束：buff 剩余回合递减 + v2.0 技能冷却递减"""
        for tbl in (self.p_buffs, self.e_buffs):
            for k in list(tbl):
                # v95.24 #252 / v121 CTB：控制类 buff（stun/freeze）是"行动级"控制——
                # 由行动消费点（_enemy_turn 被控跳过 / player_turn 被控跳过）负责 pop，
                # 不能在回合结束时递减：否则施放当回合若敌方尚未轮到行动（副本 enemy_act=False、
                # CTB 下敌方该轮未行动、敌方施放眩晕给玩家）会被直接吞掉，眩晕永远不生效。
                if k in ("stun", "freeze"):
                    continue
                # v121 CTB：元素印记（fire/ice/thunder_mark）是层数标记而非回合 buff——
                # 旧 v61 靠"速度优势回合不结束回合（_end_round 推迟）"掩盖了这里的误递减；
                # CTB 下每回合都正常结束，印记施放当回合就被清掉，元素反应（挂印→异系触发）
                # 体系整体失效。印记生命周期 = 触发反应清除（clear=True）或战斗结束。
                if k in ("fire_mark", "ice_mark", "thunder_mark"):
                    continue
                # v125.3 收口审计 P1：next_atk_up（狂怒/月露/彩虹/黑羽药剂）是"下一次攻击消费"型
                # 一次性 buff（_extra_dmg_mult 命中即 del）——按回合递减 turns=1 当回合结束被删，
                # 下回合攻击吃不到 +50%。豁免回合递减，生命周期 = 攻击消费或战斗结束。
                # v130.2 P0-2：引气精华 buff_phys_next 同款一次性语义（物理技消费即 del）→ 一并豁免。
                if k in ("next_atk_up", "buff_phys_next"):
                    continue
                # v113.1：reduce_all 存的是减伤百分比（float），回合数记 self._reduce_all_left，
                # 需单独递减（数值递减会让百分比被 -1 污染）。
                # v1.x：e_buffs["shield"]（怪物增益护盾）存的是护盾值（HP 量），
                # 由 _boss_dmg_filter 按伤害扣减，不能按回合递减。
                if k in ("reduce_all", "shield"):
                    continue
                tbl[k] -= 1
                if tbl[k] <= 0:
                    del tbl[k]
        # v113.1：团队减伤 buff 独立计时
        if self.p_buffs.get("reduce_all") is not None:
            self._reduce_all_left = int(getattr(self, "_reduce_all_left", 1) or 1) - 1
            if self._reduce_all_left <= 0:
                self.p_buffs.pop("reduce_all", None)
        # v101.28d 护盾回合递减：各来源独立计时，到 0 消失
        for key in list(self.p_shields):
            self.p_shields[key]["turns"] -= 1
            if self.p_shields[key]["turns"] <= 0:
                del self.p_shields[key]
        # v130.2 资源增幅回合制 turns 衰减（hits 制由 _amp_resource 出手命中逐次扣）→ 归 0 清 amp
        _amp_m = (self.p_eff or {}).get("amps")
        if _amp_m:
            for _ak in list(_amp_m):
                _a = _amp_m[_ak]
                if not isinstance(_a, dict) or int(_a.get("turns_left", 0) or 0) <= 0:
                    continue
                _a["turns_left"] = int(_a["turns_left"]) - 1
                if int(_a.get("turns_left", 0) or 0) <= 0 and int(_a.get("hits_left", 0) or 0) <= 0:
                    del _amp_m[_ak]
            if not _amp_m:
                self.p_eff.pop("amps", None)
        self._tick_cooldowns()
        # v130.2d 疾风余韵：回合结束记录精力（下回合 _turn_start 判定 ≥80 → 自然回复 +10）
        self._tailwind_prev_energy = int(self.resources.get("energy", 0) or 0)

    def _attacker_precise(self) -> float:
        """攻击方精准（v105 精准体系）：PVP 时攻击方是对方玩家快照（用 _player_stats 计算装备/词条精准），
        PVE 怪物无精准=0（玩家闪避不被削减）。任何异常按 0 处理。"""
        try:
            en = self.enemy or {}
            # v120 审计修复 q3：类从未定义 self.mode（恒 AttributeError 被吞→恒 0.0），
            # Battle 用 self.btype 区分类型（monster/worldboss/pvp）→ 改用 btype，PVP 精准真实生效。
            if self.btype == "pvp" and en.get("equipment"):
                return float(self._player_stats(en).get("precise", 0) or 0)
            return float(en.get("precise", 0) or 0)
        except Exception:
            return 0.0

    def _pene_vals(self, st: dict, magic: bool = False) -> tuple:
        """v106 穿透取值：返回 (百分比穿透, 固定穿透)。
        magic=True 取法穿对 mdef，否则取物穿对 def。百分比 cap 0.6（聚合层已 cap，这里兜底防脏值）。
        v106.2 穿透药水：pene_pot（物穿+15%）/ pene_magi_pot（法穿+15%）与属性乘算合成。"""
        try:
            if magic:
                pct = min(float(st.get("pene_magi", 0) or 0), 0.6)
                flat = max(int(st.get("pene_mflat", 0) or 0), 0)
                if self.p_buffs.get("pene_magi_pot"):
                    pct = min(1 - (1 - pct) * 0.85, 0.6)
                return pct, flat
            pct = min(float(st.get("pene_phys", 0) or 0), 0.6)
            flat = max(int(st.get("pene_flat", 0) or 0), 0)
            if self.p_buffs.get("pene_pot"):
                pct = min(1 - (1 - pct) * 0.85, 0.6)
            return pct, flat
        except Exception:
            return (0.0, 0)

    @staticmethod
    def _tenacity_mult(pst: dict) -> float:
        """v106 韧性：被暴击率 × (1 - 韧性)，韧性 cap 50%"""
        try:
            return 1.0 - min(float(pst.get("tenacity", 0) or 0), 0.5)
        except Exception:
            return 1.0

    def _monster_dodge_check(self, logs: list) -> bool:
        """v105 怪物闪避判定：怪物闪避率 × (1 - 我方精准)（精准上限 60%），闪避率上限 30%。
        命中判定成功追加闪避日志并返回 True（调用方跳过本次伤害结算）。"""
        try:
            mon_dodge = min(float((self.enemy or {}).get("dodge", 0) or 0), 0.30)
            if mon_dodge <= 0:
                return False
            my_hit = 0.0
            try:
                my_hit = min(float(self._player_stats(self.player).get("precise", 0) or 0), 0.60)
            except Exception:
                my_hit = 0.0
            eff = mon_dodge * (1 - my_hit)
            if eff > 0 and random.random() < eff:
                logs.append(f"💨 {self.enemy.get('name', '怪物')} 闪避了攻击！")
                return True
        except Exception:
            pass
        return False

    def _aoe_damage(self, dmg: int, logs: list, scope: str = "all", source=None) -> int:
        """v2 AOE 多目标结算（§5）：对 select_aoe_targets 每个目标独立走完整伤害链。

        - scope ∈ "front"/"all"/"rankN"（技能自带 reach 时由调用方把 attacker reach 覆盖好）。
        - 逐目标独立结算：rank>1 目标受 aoe_falloff（默认 1.0）衰减；各自独立扣血。
        - 目标死亡即时压缩（_remove_unit）并继续结算剩余目标。
        返回对主目标实际造成的伤害（吸血按主目标段计）。"""
        from .core import formation as _fm
        attacker = {"reach": getattr(self, "_aoe_reach", 3), "uid": "aoe"}
        falloff = float(getattr(self, "_aoe_falloff", 1.0) or 1.0)
        if dmg <= 0:
            return 0
        targets = _fm.select_aoe_targets(attacker, self.enemies, scope)
        if not targets:
            return 0
        main = self.enemy
        main_hit = 0
        for t in targets:
            if t.get("hp", 0) <= 0:
                continue
            t_dmg = dmg
            if int(t.get("rank", 1) or 1) > 1 and falloff != 1.0:
                t_dmg = max(1, int(t_dmg * falloff))
            # G3 修复（审计）：逐目标消费各自防御——反推攻击方等效 atk 后按目标 def 重算
            # （与召唤物挡刀同款反推；dmg 是调用方按主目标防御算好的值）
            _tdef = max(0, int(t.get("def", 0) or 0))
            if _tdef > 0:
                try:
                    _atk = (t_dmg + int((t_dmg * t_dmg + 4 * t_dmg * _tdef) ** 0.5)) // 2
                    t_dmg = max(1, int(E.calc_damage(_atk, _tdef, variance=0)))
                except Exception:
                    pass
            # 击杀结算当前目标（打断钩子 + 防御过滤）
            dealt = self._damage_enemy(t_dmg, logs, target=t, source=source or self._last_hitter)
            logs.append(f"💥 对【{t.get('name', '敌人')}】造成 {dealt} 点伤害！")
            if dealt > 0 and t is main:
                main_hit = dealt
        return main_hit

    def _aoe_damage_enemy(self, dmg: int, logs: list) -> int:
        """v114 旧 AOE 入口（兼容）：全阵 AOE，返回对主目标伤害。"""
        return self._aoe_damage(dmg, logs, "all", None)

    def _damage_enemy(self, dmg: int, logs: list, wake_sleep: bool = True, target=None, source=None) -> int:
        """对敌方单位造成伤害（§3.2）。返回实际对目标造成（或其 HP 被扣）的伤害。

        - target：目标单位 dict；None=当前玩家活跃目标(_active_target)或主目标(self.enemy)。
        - 删除旧"援军挡刀吸收"逻辑（站位天然承担）：每单位独立扣血。
        - 主动伤害>0 且目标蓄力中 → 打断（打断钩子，返还 50%MP 见 _interrupt_charging）。
        - wake_sleep：dot 传 False（持续伤害不打醒睡眠、也不打断蓄力）。
        F1 P1-4：PVP 防御生效——目标防御中(defending)时伤害减半。"""
        if target is None:
            target = getattr(self, "_active_target", None) or self.enemy
        if dmg <= 0:
            return 0
        if target.get("defending"):
            dmg = max(1, int(dmg * DEFEND_REDUCE))
            logs.append(f"(格挡后 {dmg} 点伤害)")
        if wake_sleep and target.get("buffs", {}).get("sleep"):
            target["buffs"].pop("sleep", None)
            logs.append("💥 敌人被攻击惊醒！")
        # 主动伤害打断蓄力（DOT→wake_sleep=False 不打断）
        if wake_sleep and target.get("charging"):
            self._interrupt_charging(target, logs, source=source or self._last_hitter)
        before = target.get("hp", 0)
        target["hp"] = max(0, before - dmg)
        if target["hp"] <= 0:
            # v2 阵型压缩（§4.3）：单位死亡即时移除 + 后排前移补位（审计 P1 修复）
            self._remove_unit("enemy", target)
        return dmg


    def _summon_minions(self, n: int = 1) -> list:
        """v2（§7.2）：敌方援军入 enemies 阵列（rank1/reach1，站位天然挡刀）。
        保持 e_minions 旧字段同步（命令层/instance 展示与持久化兼容）。
        每只血量=Boss 20%、攻击=Boss 40%。"""
        e = self.enemy or {}
        created = []
        base_uid = len(self.enemies)
        for i in range(n):
            m = {
                "uid": f"e_min_{base_uid + i}",
                "side": "enemy",
                "rank": 1,
                "reach": 1,
                "name": f"{e.get('name', '首领')}的爪牙",
                "hp": int(e.get("max_hp", 1) * 0.20),
                "max_hp": int(e.get("max_hp", 1) * 0.20),
                "atk": int(e.get("atk", 0) * 0.40),
                "matk": int(e.get("matk", 0) * 0.40),
                "def": int(e.get("def", 0) * 0.40),
                "mdef": int(e.get("mdef", 0) * 0.40),
                "spd": int(e.get("spd", 0) or 1),
                # v121 审计修复：援军必须带 ct（-spd 与其余构造路径一致），
                # 否则缺省按 0.0 兜底会在战斗中期近乎立即行动并连动，破坏 CTB 节奏
                "ct": -float(int(e.get("spd", 0) or 1)),
                "crit": e.get("crit", 0.05),
                "buffs": {},
                "stacks": {},
                "defending": False,
                "charging": None,
                "is_minion": True,
            }
            self.enemies.append(m)
            self.e_minions.append(m)
            created.append(m)
        return created

    # ---------------- v107 召唤物系统 ----------------
    def _summon_entity(self, tid: str, player: dict, logs: list) -> bool:
        """v107 召唤：按模板生成召唤物实体（属性按玩家实时属性比例缩放，吃 summon_power）。
        同类型达到 limit 上限时不重复召唤（骷髅海可叠 3，单宠 1）。"""
        try:
            from .data.summons import SUMMONS
        except Exception:
            return False
        tmpl = SUMMONS.get(tid)
        if not tmpl:
            return False
        cur = [s for s in self.summons if s.get("tid") == tid]
        if len(cur) >= int(tmpl.get("limit", 3)):
            logs.append(f"⛔ 已有 {len(cur)} 个{tmpl['name']}（上限 {tmpl['limit']}）！")
            return False
        st = self._player_stats(player)
        sp = float(st.get("summon_power", 0) or 0)  # 隐藏职业专属强化（亡灵/兽王）
        hp = max(20, int(st.get("max_hp", 200) * float(tmpl["hp_ratio"]) * (1 + sp)))
        atk = max(5, int(st.get("atk", 50) * float(tmpl["atk_ratio"]) * (1 + sp)))
        df = max(2, int(st.get("def", 20) * float(tmpl["def_ratio"]) * (1 + sp)))
        self.summons.append({"tid": tid, "name": tmpl["name"], "icon": tmpl.get("icon", ""),
                             "hp": hp, "max_hp": hp, "atk": atk, "def": df,
                             "dmg_type": tmpl.get("dmg_type", "phys"),
                             "rank": int(tmpl.get("rank", 1) or 1),
                             "reach": int(tmpl.get("reach", 1) or 1)})
        logs.append(f"{tmpl.get('icon', '')} {tmpl['name']} 加入战斗！(HP {hp} / 攻击 {atk} / 站位{self.summons[-1]['rank']}层)")
        return True

    def _summons_act(self, player: dict, logs: list) -> list:
        """v107 召唤物自动攻击：每个存活召唤物攻击一次（玩家行动后、敌方行动前）。
        真伤召唤物（影狼）走 dmg_type=true 绕过全减伤；按自身 reach 选目标（§7）。"""
        if not self.summons:
            return logs
        for s in list(self.summons):
            if s.get("hp", 0) <= 0 or self._enemy_dead():
                continue
            # v2：召唤物按自身 reach 选目标（射程内最前排）
            target = self._pick_summon_target(s)
            if target is None:
                continue
            if s["dmg_type"] == "true":
                dmg = max(1, int(s["atk"] * (1 + random.uniform(-0.15, 0.15))))
            else:
                est = self._enemy_stats(target)
                # 非真伤：按召唤物自身 dmg_type（phys/magi）传给 calc_damage，
                # 不再硬编码 phys（当前三模板均 phys 故行为不变，属防回归）。
                dmg = E.calc_damage(s["atk"], est.get("def", 0), dmg_type=s.get("dmg_type", "phys"))
            dmg = max(1, dmg)
            self._damage_enemy(dmg, logs, target=target, source=s.get("name", "召唤物"))
            logs.append(f"{s.get('icon', '')} {s['name']} 攻击，造成 {dmg} 点伤害！")
        # 清理死亡召唤物
        for s in list(self.summons):
            if s.get("hp", 0) <= 0:
                logs.append(f"💀 {s['name']} 倒下了！")
                self.summons.remove(s)
        return logs

    def _pick_summon_target(self, s: dict) -> dict | None:
        """v2：召唤物按自身 reach 选敌方目标（§7.3——射程内最前排）。"""
        from .core.formation import alive_units, select_target
        alive = alive_units(self.enemies)
        if not alive:
            return None
        if len(alive) == 1:
            return alive[0]
        return select_target(s, self.enemies)

    def _remove_unit(self, side: str, unit: dict) -> list:
        """v2 单位死亡统一移除入口（§3.2）：从阵列移除 + 该侧阵型压缩 + 击杀槽文案。
        返回压缩时被移除（死亡）的单位列表。"""
        from .core.formation import compact
        removed = []
        if side == "enemy":
            if unit in self.enemies:
                self.enemies.remove(unit)
                removed = compact(self.enemies)
            # 同步 e_minions 旧字段（镜像同对象）
            if unit in self.e_minions:
                self.e_minions[:] = [m for m in self.e_minions if m.get("hp", 0) > 0]
            self.enemy  # 刷新主目标引用（property）
        elif side == "ally":
            lives = []
            for u in (self.allies or []):
                if u.get("hp", 0) > 0:
                    lives.append(u)
                else:
                    removed.append(u)
            self.allies[:] = lives
            removed += compact(self.allies)
        return removed

    def _summon_block_check(self, player: dict, dmg: int, logs: list) -> int:
        """v107 召唤物挡刀：敌人攻击时按模板 bodyguard 概率由随机存活召唤物承受伤害。
        v109.2 P2-1：伤害按召唤物 def 结算（原全额转移——皮厚召唤物挡刀更久）；
        P2-2：summon_power 强化挡刀率（×1+sp，上限 85%）。
        触发后本次伤害不再结算到玩家（拦截优先于闪避/格挡）。"""
        alive = [s for s in self.summons if s.get("hp", 0) > 0]
        if not alive:
            return dmg
        try:
            from .data.summons import SUMMONS
        except Exception:
            return dmg
        s = random.choice(alive)
        tmpl = SUMMONS.get(s.get("tid", ""), {})
        sp = float(self._player_stats(player).get("summon_power", 0) or 0)
        chance = min(float(tmpl.get("bodyguard", 0.40)) * (1 + sp), 0.85)
        if random.random() >= chance:
            return dmg
        # P2-1：按召唤物 def 结算——从对玩家伤害反推攻击方等效 atk，再套召唤物防御公式
        try:
            _pdef = max(0, int(self._player_stats(player).get("def", 0) or 0))
            _atk = (dmg + int((dmg * dmg + 4 * dmg * _pdef) ** 0.5)) // 2
            taken = max(1, int(E.calc_damage(_atk, max(0, int(s.get("def", 0) or 0)), variance=0)))
        except Exception:
            taken = max(1, int(dmg))
        s["hp"] -= taken
        logs.append(f"{s.get('icon', '')} {s['name']} 为你挡下 {taken} 点伤害！")
        if s["hp"] <= 0:
            logs.append(f"💀 {s['name']} 在保护你时倒下了！")
            self.summons.remove(s)
        return 0

    def _drain_pending_dmg(self) -> list:
        """O116：取出并清空延迟的受击伤害日志（命中后由 _damage_player 输出）。"""
        lines = list(getattr(self, "_pending_dmg_lines", None) or [])
        self._pending_dmg_lines = []
        return lines

    def _damage_player(self, player: dict, dmg: int, logs: list, source: str = "敌人"):
        if dmg <= 0:
            self._pending_dmg_lines = []
            return
        # v2 蓄力打断：玩家蓄力中受到主动伤害>0 → 打断并返还 50% MP（§6.2规则4）
        if self.charging and self.charging.get("skill"):
            pname = player.get("name", "你")
            cname = self.charging.get("name", self.charging.get("skill", "?"))
            spent = int(self.charging.get("mp_spent", 0) or 0)
            self.charging = None
            logs.append(f"🔨 【{pname}】的蓄力被{source}打断了！")
            if spent > 0:
                player["mp"] = min(player.get("max_mp", player.get("mp", 0)),
                                   player.get("mp", 0) + (spent + 1) // 2)
                logs.append(f"✨ 返还了 {(spent + 1) // 2} 点魔力。")
        # 24 章宠物技能·影袭：替主人挡一次攻击（主动保护优先于自身闪避，拦截后直接结束本次伤害）
        dmg = self._pet_block_check(dmg, logs)
        if dmg <= 0:
            # O116 还原原顺序：先报攻击伤害，再报挡刀
            _pl = self._drain_pending_dmg()
            if _pl:
                logs[:] = _pl + logs
            return
        # v107 召唤物挡刀：概率由召唤物承受（拦截优先于玩家闪避/格挡）
        dmg = self._summon_block_check(player, dmg, logs)
        if dmg <= 0:
            # O116 还原原顺序：先报攻击伤害，再报挡刀
            _pl = self._drain_pending_dmg()
            if _pl:
                logs[:] = _pl + logs
            return
        # v105 闪避体系（鱼鱼拍板"闪避改乘算"）：全部来源乘算合成 1-Π(1-dᵢ)，统一 40% 总上限
        # 攻击方精准削减：有效闪避 = 闪避 × (1 - 攻击方精准)，精准上限 60%（PVP 互殴生效，PVE 怪物无精准）
        dodge = min(float(self._player_stats(player).get("dodge", 0) or 0), 0.40)
        # 伪装帷幕（effect=dodge_up 闪避率 +40%）：乘算并入
        if self.p_buffs.get("dodge_up"):
            dodge = 1 - (1 - dodge) * (1 - 0.40)
        # 无声被动——被攻击概率降低 30%：乘算并入
        for _pn, _ps in self._passive_map(player)["proc"].get("dodge_up", []):
            dodge = 1 - (1 - dodge) * (1 - float(_ps.get("mult", 0.3)))
        # 影步药剂 15%：并入乘算（不再独立判定——旧实现独立判定绕过 40% 上限，基础 40%+药水可达 49.7%）
        if self.p_buffs.get("dodge_pot"):
            dodge = 1 - (1 - dodge) * (1 - 0.15)
        # 攻击方精准削减（PVP：对方玩家精准；PVE：怪物无精准=0 不削减）
        atk_hit = self._attacker_precise()
        if atk_hit > 0:
            dodge = dodge * (1 - min(atk_hit, 0.60))
        dodge = min(dodge, 0.40)
        if dodge > 0 and random.random() < dodge:
            # O116 闪避成功：丢弃延迟的伤害日志，只报闪避（命中/闪避二选一）
            self._pending_dmg_lines = []
            logs.append("💨 你闪避了攻击！")
            # v130.2 暮影影步：闪避成功 on_dodge_success 攒步（core_resources on_dodge_success>0）
            _rd = E.core_resource_def(player.get("class_name", ""))
            if _rd and _rd.get("on_dodge_success"):
                _rk = _rd["key"]
                self.resources[_rk] = self._res_gain_class(player.get("class_name", ""), _rk, int(_rd["on_dodge_success"]))
                logs.append(f"🫧 影步积攒 +{_rd['on_dodge_success']}({self.resources.get(_rk, 0)}/{_rd['max']})")
            return
        # O116 命中：此刻才输出"造成 X 点伤害"日志（此前由 _enemy_turn 延迟暂存）
        logs += self._drain_pending_dmg()
        # v130.2c 圣典·日冕 4 件：满信仰状态下首次受击免伤（每战 1 次，随战斗序列化）
        if (not getattr(self, "_set_immune_used", False)
                and self._set_eff(player, "first_hit_immune", 4)
                and self._res_read("faith") >= self._res_max(player, "faith")):
            self._set_immune_used = True
            logs.append("☀️ 圣典·日冕：满信仰免伤结界抵挡了这次攻击！")
            return
        # v113.1：团队技能 reduce_all 真·百分比减伤（此前误映射 def_up 防御提升）——
        # p_buffs["reduce_all"] 存减伤百分比，回合数由 self._reduce_all_left 单独计时。
        # 单机侧在此按比例减伤；副本广播侧（instance.py 消费 team_effects["reduce_all"]）另口径。
        _rd_pct = float(self.p_buffs.get("reduce_all") or 0)
        if _rd_pct > 0:
            _rd = int(dmg * min(_rd_pct, 0.9))
            if _rd > 0:
                dmg = max(1, dmg - _rd)
                logs.append(f"🕸️ 团队屏障减伤 {_rd} 点！")
        elif _rd_pct < 0:
            # v130.2 P0-4：熔核之心战损——全减伤负值 = 受伤加重（-20% → 受击 +20%）。
            # 原实现只处理 >0 把负值整个跳过，熔核变成白嫖满怒无代价；此处补 <0 分支，不覆盖正向 reduce_all。
            _pen_rd = int(dmg * -_rd_pct)
            if _pen_rd > 0:
                dmg += _pen_rd
                logs.append(f"🔥 熔核代价：全减伤惩罚·受伤加重 {_pen_rd} 点！")
        # v106.3 格挡属性统一结算（词条折算/种族岩壁格挡/被动/药水 → st["block"]）
        # 圣盾被动 stat=block mult=0.1 已并入被动加成（_PASSIVE_STAT_APPLY block → block_add）
        block_chance = float(self._player_stats(player).get("block", 0) or 0)
        if self.p_buffs.get("block_pot"):
            block_chance = 1 - (1 - block_chance) * (1 - 0.15)  # 岩壁药剂 +15% 格挡（乘算并入）
        block_chance = min(block_chance, 0.40)
        if block_chance > 0 and random.random() < block_chance:
            block_reduce = max(1, int(dmg * 0.5))
            dmg = max(1, dmg - block_reduce)
            logs.append(f"🛡️ 格挡！减免 {block_reduce} 点伤害！")
            # v107 格挡反击（圣殿骑士）：格挡成功后按 chance 反伤（物理段，mult 为反伤系数）
            # v110.3 P2-1：多个格挡反击被动逐个独立 roll，命中即停；此前 break 在 for 末尾无条件退出，只 roll 第一个被动
            for _pn, _ps in self._passive_map(player)["proc"].get("block_counter", []):
                if self.enemy.get("hp", 0) > 0 and random.random() < float(_ps.get("chance", 0.5)):
                    rd = max(1, int(dmg * float(_ps.get("mult", 0.5))))
                    rd = self._boss_dmg_filter(rd, player, logs)
                    self._damage_enemy(rd, logs)
                    logs.append(f"🛡️ {_pn}：格挡反击！反弹 {rd} 点伤害！")
                    break  # 命中即停（一次格挡最多一次反击）
        self._player_hit = True  # v2.1 条件：记录本场受击（未受击增伤判定）
        # v104 R3 P1-1：复仇被动——受击后下次攻击 +30%（挨打反打）
        for _pn, _ps in self._passive_map(player)["proc"].get("counter", []):
            self.p_buffs["revenge_atk"] = max(self.p_buffs.get("revenge_atk", 0), 1)
            break
        # 阶段八：受击词条（减伤/格挡/反击/反伤/腐蚀/坚韧）
        dmg = self._affix_on_taken(player, dmg, logs)
        dmg = self._food_on_taken(player, dmg, logs)
        # v130.2c 套装受击回资源：血誓战团（受击回怒 +1）/ 圣徽·誓约（受击回信仰 +1）
        self._set_res_proc(player, "on_taken", logs)
        # v64/v104 被动 proc 结算（按 passive 字段查 learned_skills，替换名字硬匹配）：
        #   dmg_taken → 减伤（铁壁之心/磐石体/磐石之心/磐石之躯/守护姿态）；reflect → 反伤（反震）
        ps_names = E.passive_skills_learned(player.get("class_name", ""), player.get("learned_skills", []))
        reduce_total = 0
        for ps_name in ps_names:
            info = E.skill_info(player.get("class_name", ""), ps_name)
            ps = (info or {}).get("passive") or {}
            proc = ps.get("proc")
            if proc == "dmg_taken":
                rpct = float(ps.get("reduce") or 0)
                if rpct <= 0:
                    continue
                # v1.x：条件判定改查 PASSIVE_COND_CHECKS（原 hp_low_30 if 硬编码；
                # 条件不满足 → 跳过本次减伤，语义与旧 `cond==hp_low_30 and hp>=30% → continue` 一致）
                if not passive_cond_ok(self, player, ps):
                    continue
                reduce_total += int(dmg * rpct)
                # v113.1：守护姿态 passive 带 res_gain（受击怒气+2 承诺）——此前本分支只减伤
                # 不结算 res_gain，承诺落空。消费到职业核心资源（战士怒气等）。
                _rg = int(ps.get("res_gain") or 0)
                if _rg > 0:
                    _rcls = player.get("class_name", "")
                    _rdef = E.core_resource_def(_rcls)
                    if _rdef:
                        _rk = _rdef["key"]
                        self.resources[_rk] = E.core_resource_gain(_rcls, self.resources, _rg)
                        logs.append(f"⚡ {ps_name}：受击获取 {_rg} 点资源（{_rk} {self.resources[_rk]}）")
            elif proc == "reflect" and self.enemy.get("hp", 0) > 0:
                # v113.1：反震——按 chance 概率反伤（缺省 100%：无条件反伤，保持旧行为）
                if "chance" in ps and random.random() >= float(ps.get("chance") or 0):
                    continue
                rd = int(dmg * float(ps.get("mult") or 0))
                if rd > 0:
                    # v104 M02 P1-5：反伤走 Boss 护盾过滤（扣盾减半/反伤），再结算援军挡刀
                    rd = self._boss_dmg_filter(rd, player, logs)
                    self._damage_enemy(rd, logs)
                    logs.append(f"🪨 {ps_name}：反弹 {rd} 点伤害！")
        if reduce_total:
            dmg = max(1, dmg - reduce_total)
            logs.append(f"🛡️ 被动减伤 {reduce_total} 点")
        # v106.4 反伤属性统一结算（词条折算/种族/被动/药水 → st["thorns"]）
        _pst_th = self._player_stats(player)
        th = float(_pst_th.get("thorns", 0) or 0)
        if self.p_buffs.get("thorns_pot"):
            th = 1 - (1 - th) * (1 - 0.30)  # 荆棘药剂 +30% 反伤（乘算并入）
        th = min(th, 0.5)
        if th > 0 and self.enemy.get("hp", 0) > 0:
            rd = int(dmg * th)
            if rd > 0:
                rd = self._boss_dmg_filter(rd, player, logs)
                self._damage_enemy(rd, logs)
                logs.append(f"🌵 反伤！反弹 {rd} 点伤害！")
        # v107 反击（苦修士）：受击后按 chance 概率立即普攻反击（物理段，吃暴击）
        # v109 P0-3：多个反击被动（以守为攻+反击之王）逐个独立 roll，命中即停；此前 break 在
        # for 末尾无条件退出，只 roll 第一个被动 → 反击之王(lv70)被废
        if self.enemy.get("hp", 0) > 0:
            for _pn, _ps in self._passive_map(player)["proc"].get("counter_attack", []):
                if random.random() < float(_ps.get("chance", 0.20)):
                    _st_ca = self._player_stats(player)
                    _est_ca = self._enemy_stats()
                    _ca_crit = random.random() < float(_st_ca.get("crit", 0) or 0)
                    ca_dmg = E.calc_damage(_st_ca["atk"], _est_ca.get("def", 0), _ca_crit,
                                           dmg_type="phys")
                    ca_dmg = self._boss_dmg_filter(ca_dmg, player, logs)
                    self._damage_enemy(ca_dmg, logs)
                    logs.append(f"🥊 反击！你立刻回击造成 {ca_dmg} 点伤害！"
                                + (" 💥暴击" if _ca_crit else ""))
                    break  # 命中即停（一次受击最多一次反击）
        # v51 盾牌反击：被攻击时 60% 概率反击 120% 伤害
        if self.p_buffs.get("counter", 0) > 0 and self.enemy.get("hp", 0) > 0:
            if random.random() < C.SHIELD_COUNTER_CHANCE:
                pst2 = self._player_stats(player)
                est2 = self._enemy_stats()
                cd = E.calc_damage(int(pst2["atk"] * 1.2), est2.get("def", 0))
                self._damage_enemy(cd, logs)
                logs.append(f"🛡️ 盾牌反击！对【{self.enemy.get('name', '敌人')}】造成 {cd} 点伤害！")
        # 龙鳞套：被攻击时 25% 概率反弹 25% 伤害
        if "reflect" in E.set_bonus_4(player.get("equipment", {})) and self.enemy.get("hp", 0) > 0:
            if random.random() < C.REFLECT_CHANCE:
                rd = int(dmg * 0.25)
                rd = self._boss_dmg_filter(rd, player, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
                self._damage_enemy(rd, logs)
                logs.append(f"🐉 龙鳞反震！反弹 {rd} 点伤害！")
        # v29 金身：每层减伤 4%
        mech = self.mech_stacks
        iron = int(mech.get("iron", 0) or 0)
        if iron > 0:
            reduce = int(dmg * 0.04 * iron)
            dmg = max(1, dmg - reduce)
            logs.append(f"🪷 金身减伤 {reduce} 点({iron} 层)")
        # v34 符文·壁垒：受击时 x% 概率获得护盾（y% 生命值）；荆棘：受击反弹 x% 伤害
        effs = self._enchant_effects(player)
        barrier_lvl = self._enchant_lvl(effs, "barrier")
        if barrier_lvl:
            prob, pct = C.rune_value("barrier", barrier_lvl)
            # 契约断言：data/runes.py barrier lvl 返回 [prob, pct] 二元素列表，防未来改单值静默错位
            assert isinstance(prob, (int, float)) and isinstance(pct, (int, float)), \
                f"rune barrier lvl={barrier_lvl} 应返回 [prob, pct]，实得 {C.rune_value('barrier', barrier_lvl)!r}"
            if random.random() < prob:
                shield_gain = int(player.get("max_hp", player.get("hp", 1)) * pct)
                self._add_shield("rune_barrier", shield_gain, 2)
                logs.append(f"🛡️ 符文壁垒：获得 {shield_gain} 点护盾！")
        thorns_lvl = self._enchant_lvl(effs, "thorns")
        if thorns_lvl and self.enemy.get("hp", 0) > 0:
            rd = int(dmg * C.rune_value("thorns", thorns_lvl))
            rd = self._boss_dmg_filter(rd, player, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
            self._damage_enemy(rd, logs)
            logs.append(f"🌵 符文荆棘：反弹 {rd} 点伤害！")
        # v106.4 反伤属性统一结算在 _damage_player 段（thorns_pot 已乘算并入 thorns，
        # 此段删除 v101.28f 旧独立反弹——否则双重结算，2026-08-13 回归抓包）
        # v29 神恩护盾：优先吸收（v59：护盾存战斗状态；v101.28d：多来源护盾逐个扣，同源叠厚异源并存）
        shields = self.p_shields
        if shields:
            absorb_total = 0
            for key in list(shields):
                s = shields[key]
                absorb = min(s["value"], dmg)
                s["value"] -= absorb
                dmg -= absorb
                absorb_total += absorb
                if s["value"] <= 0:
                    del shields[key]
                if dmg <= 0:
                    break
            if absorb_total > 0:
                left = sum(s["value"] for s in shields.values())
                logs.append(f"✨ 护盾吸收 {absorb_total} 点伤害(剩余 {left})")
                if dmg <= 0:
                    return
        player["hp"] = max(0, player.get("hp", 0) - dmg)
        # v107 死亡契约（暗影祭司）：致死时牺牲一个召唤物以 20% HP 存活（每场 1 次）
        if player["hp"] <= 0 and self.summons and not self._death_pact_used:
            for _pn, _ps in self._passive_map(player)["proc"].get("death_pact", []):
                self._death_pact_used = True
                fallen = self.summons.pop()
                player["hp"] = max(1, int(player.get("max_hp", player["hp"]) * 0.20))
                logs.append(f"💀 死亡契约！{fallen.get('name', '亡灵')} 替你承受了致命一击，你以 {player['hp']} HP 站起！")
                break
        # v2.0 核心资源：受击获取（战士怒气/牧师信仰/拳师气）
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        # v130.2 P1-5：on_hit 双语义解耦——星语猎手 on_hit 是「任意命中」语义（ranger.md §3.1(b)），
        # 受击不得按旧钩子当「受击回资源」读（白名单 HUNT_MARK_ON_LAND_HIT，数据驱动非硬编码）：
        # 猎印只有命中才攒（普攻/技能走 _resource_on_attack/_resource_on_skill），无受击渠道。
        if rd and rd.get("on_hit") and cls not in HUNT_MARK_ON_LAND_HIT:
            k = rd["key"]
            gain = int(rd["on_hit"])
            # v130.2 战士血债怒火（攻线·狂战士 T1）：受击回怒 = 1 + ⌊缺失HP%×4⌋，封顶 5
            #   （warrior_转职 下放签名：卖血换怒——满血+1、缺25%血+2、缺一半+3、濒死+5）
            if cls == "cls_zhan_shi" and self._is_path(player, 1):
                _max = max(1, player.get("max_hp", 1) or 1)
                _missing = max(0.0, min(1.0, 1.0 - (float(player.get("hp", 0) or 0) / _max)))
                gain = int(RAGE_GAIN_HP_SCALE.get("base", 1) or 1)
                gain += int(_missing * float(RAGE_GAIN_HP_SCALE.get("coef", 4.0) or 4.0))
                gain = min(int(RAGE_GAIN_HP_SCALE.get("cap", 5) or 5), gain)
            self.resources[k] = self._res_gain_class(cls, k, gain)
        # v130.2 资源增幅：受击触发（沸腾战血 3 回合内受击额外 +2 怒，P0-1 消费端；回合制 turns 衰减）
        _amp_th = self._amp_resource(player, "on_hit_taken")
        if _amp_th:
            logs.append(f"⚡ 沸腾战血：受击额外资源 +{_amp_th}！")
        # v130.2c 资源词条：受击（浴血 怒气/虔诚护符 信仰/磐息 气 +1；残血灼薪 血量条件判定）
        self._affix_res_proc(player, "on_taken", logs)
        # v130.2 暮影影步：受击清空全部（全额惩罚，assassin.md §5.2）——on_hit=0 不列 base 分支，单独处理
        if cls == "cls_shadow_blade" and rd:
            if int(self.resources.get(rd["key"], 0) or 0) > 0:
                self.resources[rd["key"]] = 0
                logs.append("🫧 受击！影步清空")
        # v130.2 刺客攻线·影舞者：受击回退 -1 连击点 + 连段归零（高风险高回报，assassin_转职 §1.0）
        if cls == "cls_ci_ke" and self._is_path(player, 1):
            _pen = int(ASSASSIN_ON_TAKE_HIT_PENALTY or 0)
            cur_cp = int(self.resources.get("cp", 0) or 0)
            if cur_cp > 0 and _pen < 0:
                penalty = min(cur_cp, -_pen)
                self.resources["cp"] = cur_cp - penalty
                logs.append(f"🗡️ 受击！连击点 -{penalty}({self.resources['cp']}/{rd['max'] if rd else 5})")
            self._combo_break(player, self._combo_keep_chance(player))
        # v110.3 P2-9：被动·神圣坚韧——受击后按 chance 概率回复 pct 生命（数据驱动 dmg_taken_heal，替代名字硬匹配）
        if player["hp"] > 0:
            for _pn, _ps in self._passive_map(player)["proc"].get("dmg_taken_heal", []):
                if random.random() < float(_ps.get("chance", 0.2)):
                    heal = int(player.get("max_hp", player.get("hp", 1)) * float(_ps.get("pct", 0.05)))
                    player["hp"] = min(player.get("max_hp", player["hp"]), player["hp"] + heal)
                    logs.append(f"✨ {_pn}：回复 {heal} 点生命！")

    def _enemy_dead(self) -> bool:
        # v2：敌方阵列无存活（§3.2）——同时压缩移除死亡单位
        from .core.formation import alive_units
        return not alive_units(self.enemies)

    def _player_dead(self, player: dict) -> bool:
        return player.get("hp", 1) <= 0
