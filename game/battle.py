# -*- coding: utf-8 -*-
"""v9 统一战斗引擎 —— 遇怪 / 世界BOSS / PVP 共用

核心：Battle 状态机
  - 持久化：db.save_battle 存 state dict（battle_state.state 字段）
  - buff 系统：玩家/敌方各自 buff 表 {effect: 剩余刻}，每刻递减
  - 技能特效全部落地：旧 engine.player_attack 的 extra（破甲降防/寒冰减速/毒箭中毒/
    标记猎杀/处决残血/吸血）此前被 main.py 丢弃，这里真正写入战斗状态并生效
  - 敌方增益也落地：monster_turn 的 mextra（mon_atk_up/mon_def_up）此前被丢弃

btype:
  - monster   : 探索遇怪（可逃跑）
  - worldboss : 世界 Boss（v9.1 启用，不可逃跑）
  - pvp       : 玩家对战（v9.2 启用，不可逃跑，enemy 为对方玩家快照）
"""
import random
import re
import time

from . import content as C
from . import engine as E
from .data.battle_config import (  # v125.2 B1 + v130.2 并入：战斗主路径数值/白名单数据表 + v130 引擎新机制表
    MECH_STACK_BONUS, MECH_STACK_WHITELIST, DOT_DEFS,
    DOT_BLEED_DOUBLE_HP_PCT, DOT_ADAPT_DECAY_STEP, DOT_RESIST_CAP,
    DOT_BOSS_PCT_MULT, DOT_PCT_CAP,
    BOSS_ATTACK_MULTS, CONTROL_MECHS, SKILL_CC_WHITELIST,
    MECH_FULL_HP_CRIT, MECH_FROZEN_MULT, MECH_COMBO_STACKS,
    MECH_PROC_GROUPS, MECH_STAT_PASSIVES,
    ELEMENT_MARKS_MAX, REACTION_TABLE, ELEMENT_MARK_GAIN_PER_HIT,
    ELEMENT_SAME_CAST_EXTRA_CHARGE, RAGE_GAIN_HP_SCALE, ENERGY_HIGH,
    COMBO_CFG, ASSASSIN_ON_CRIT_GAIN, ASSASSIN_ON_TAKE_HIT_PENALTY,
    MOMENTUM_CFG, SHADOW_STEP_CFG, SHADOW_STEALTH_DMG_MULT,
        ECHO_CFG, BARD_BRANCHES,
        BRANCH_RESOURCE_OVERRIDE,
        LUCKY_CRIT_CHANCE, LUCKY_CRIT_MULT, MULTI_HIT_CRIT_FIRST_ONLY,  # v133 峰值红线
    )
from .core.battle_conds import PASSIVE_COND_CHECKS, PASSIVE_COND_STAT_KEYS, passive_cond_ok  # v1.x 被动条件注册表
from .core.constants import (  # v130.7 意见#28：逃跑成功率修正常量（core/__init__ 未导出清单，直连避免动聚合层）
    FLEE_CHANCE, FLEE_LEVEL_STEP, FLEE_SPD_STEP, FLEE_MIN, FLEE_MAX,
    # v138.2 异常体系五律：阈值递增/每场上限+饱和/跨阶段保留/饱和收敛（真伤走 DOT_DEFS true_dmg）
    DOT_THRESHOLD_MULT, DOT_THRESHOLD_CAP, DOT_MAX_TRIGGER,
    DOT_PRESERVE_PCT, DOT_PRESERVE_THRESHOLD_BONUS, DOT_SATURATE_MULT,
)

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
    "matk_up_pot":    ("matk", 1.30),   # 9.3 鲛人之泪：本刻魔攻 +30%
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
# DOT 重构常量集中（契约 §2.4）：每层每刻 % 敌方最大生命
# 历史常量，dot 已改混合公式（_tick_dots 用 _atk_parts/_matk_parts/_hp_parts，不再读这些）；保留定义兼容外部引用
POISON_PCT = 0.05     # 毒：每层每刻 5% 敌方最大生命（保留旧名兼容外部引用）
BURN_PCT = 0.03       # 灼烧：每层每刻 3% 敌方最大生命
BLEED_PCT = 0.05      # 流血：每刻 5% 敌方最大生命（词条 2~3 刻）
DEFEND_REDUCE = 0.5   # 防御：敌方伤害减半
BUFF_TURNS = 3        # 增益默认持续刻
DEBUFF_TURNS = 2      # 减益默认持续刻

# v121 CTB 行动时间轴：全局行动消耗常量
# v152 鱼鱼拍板：总耗时 = 行动间隔（BASE_DELAY/spd）+ 固定动作耗时。
# BASE_DELAY=40 经 sim 标定：普通怪战斗 ~49s（60s 内），紧凑不拖沓。
# （旧 100 在新模型下战斗拖到 113s 太长；40 平衡节奏与速度差稀释）
BASE_DELAY = 40.0     # 行动间隔基数（v152 标定：40 保持战斗节奏）
SPD_CT_CAP = 80.0     # 参与 ct 计算的 spd 软上限（min(spd, cap)）
# v154 鱼鱼拍板：速度影响自己的出招(cast)和收招(recovery)，出招跑完=命中。
# 恢复间隔取消——总行动周期 = 出招 + 收招，速度收益全部收敛到动作快慢。
# SPD_REF = 基准速度：速度 50 时动作耗时 = 数据基础值；>50 变快，<50 变慢。
SPD_REF = 50.0        # v154 基准速度（= v152 参考档）
# v152 CTB 彻底化：刻 → 时刻。ACT_TICK = 1 刻对应的全局时刻数。
# 鱼鱼拍板（2026-08-31）：1 刻 = 1 游戏秒（对齐秒，玩家直观）。
# 所有"持续 N 刻 / CD N 刻"换算为 N × ACT_TICK = N 时刻 = N 游戏秒。
# 引擎内部无"刻"概念，只有全局绝对时刻 _now；"刻"是玩家可见的换算单位（1 刻 = 1 秒）。
ACT_TICK = 1.0        # 1 刻 = 1.0 时刻 = 1 游戏秒（鱼鱼拍板对齐秒）
# v154：CAST_* 语义从"固定动作耗时"改为"基准耗时"（速度 50 时 = 该值）。
# 实际耗时 = 基准耗时 × (SPD_REF / 实际速度)；速度 50 时 = 基准值。
CAST_ATK = 1.0        # 普攻基准耗时（1 秒 @spd50）
CAST_SKILL = 1.6      # 技能基准耗时（1.6 秒 @spd50，出手更慢）
CAST_ITEM = 1.0       # 道具基准耗时（1 秒 @spd50）
CAST_FOOD = 1.0       # 食物基准耗时（1 秒 @spd50）
CAST_DEFEND = 0.6     # 防御基准耗时（0.6 秒 @spd50，快动作）
CAST_FLEE = 2.0       # 逃跑基准耗时（2 秒 @spd50，慢，易被打断）
CAST_PET_SKILL = 0.8  # 宠物技能基准耗时（0.8 秒 @spd50，出手快）——v154 宠物独立读条

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
    """碎岩冲撞：攻击 × value 伤害，并破防（敌方防御减半 2 刻）。"""
    _pet_skill_dmg(battle, player, pdef, pname, sname, line, logs)
    battle.e_buffs["def_down"] = max(int(battle.e_buffs.get("def_down", 0) or 0), 2)
    logs.append(f"🛡️ {pname}的【{sname}】击碎了敌人的护甲！(防御减半 2 刻)")
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
    logs.append(f"🐾 {pname}的【{sname}】为你加持攻击强化！(攻击 +{int(pdef['skill_value'] * 100)}%，2 刻)" + (f"「{line}」" if line else ""))


@_pet_skill_register("crit_up")
def _psk_crit_up(battle, player, pdef, pname, sname, line, logs):
    """狩猎之眼/星羽疾风：暴击提升（数值实读 skill_value）。"""
    battle.p_buffs["crit_up"] = max(int(battle.p_buffs.get("crit_up", 0) or 0), 2)
    _pbv = getattr(battle, "_pet_buff_vals", {})
    _pbv["crit"] = max(float(_pbv.get("crit", 0.0) or 0.0), float(pdef["skill_value"]))
    battle._pet_buff_vals = _pbv
    logs.append(f"🐾 {pname}的【{sname}】为你加持暴击提升！(暴击 +{int(pdef['skill_value'] * 100)}%，2 刻)" + (f"「{line}」" if line else ""))


def _ct_initial_wait(spd) -> float:
    """v154 单位初始行动等待 = 基准普攻耗时 × 速度折算系数（第一刀也按速度快慢出）。
    v130.10 语义：初始等待 = BASE_DELAY/spd（恢复间隔制）。
    v154 语义：恢复间隔取消，初始等待 = 出招耗时（基准 CAST_ATK × SPD_REF/spd）。
    速度 50 → 1.0s；速度 25 → 2.0s；速度 80(cap) → 0.625s。
    """
    try:
        eff = min(float(spd or 0), SPD_CT_CAP)
    except Exception:
        eff = 0.0
    return CAST_ATK * (SPD_REF / max(1.0, eff))


class Battle:
    def __init__(self, btype: str = "monster", enemy: dict | None = None, title_bonus: dict = None, player: dict | None = None, pet: dict | None = None, dmg_mult: float = 1.0, enemies: list | None = None, allies: list | None = None, st: dict | None = None, active_keys: list | None = None):
        self.btype = btype                 # monster | worldboss | pvp | instance（瞬态 Battle 结算器）
        self._st = st or {}                # v137 副本内聚状态引用（players/alive/p_defending/threat/taunt_*）
        # v158 副本合并：_inst_cb 副本回调钩子（instance 注入），敌方行动后/玩家行动后通知
        # 命令层同步血量/仇恨/贡献/房间状态。野外（不传 cb）为 None，零影响。
        self._inst_cb = (st or {}).get("_cb") if isinstance(st, dict) else None
        # v137 副本：btype="instance" 的 Battle 仅是命令层（instance.py）驱动的"瞬态结算器"——
        # 玩家行动 player_turn(enemy_act=False) + 序列化 type + allies ct 广播（_after_actor_ct 1393-1436）。
        # 副本战斗主循环（谁行动/敌方阶段/超时/换层）由命令层 instance.py 驱动，不在本引擎内调度。
        # active_keys 参数保留（命令层可注入在场成员 key），本引擎不使用（v137 收编方法已删）。
        self._active_keys = active_keys or [str(p.get("qq_id")) for p in (allies or [])]  # v137 在场玩家 key（退队过滤，命令层注入）
        self.dmg_mult = dmg_mult           # v93 GM 世界 Boss 伤害倍率（gm_伤害 设置，仅 worldboss 生效）
        self.pet = pet or {}               # 24 章宠物：{pet_key,name,level,satiety}（战斗内宠物技能用）
        # v152 CTB 彻底化：刻概念删除。self._now = 全局战斗绝对时刻（从 0 起单调递增）；
        # self._p_acts = 玩家行动次数（展示用，不再叫 round）。所有"刻"结算改为按 _now 时刻到期。
        self._now: float = 0.0
        self._p_acts: int = 0
        # v152：定时事件队列（heapq 按 t 升序）。事件 = {"t": 时刻, "type": str, ...}。
        # 由 _schedule/_process_events 维护；主要用途：Boss 定时机制、宠物技能、DOT 跳动。
        import heapq as _heapq
        self._events: list = []
        self._heapq = _heapq
        # v2 多对多阵列（§3.2）：enemies=敌方阵列每怪一个 dict；allies=我方阵列
        # （单机 = [player]；副本由命令层维护）。enemy 单怪兼容包装为单怪阵列。
        self._enemies_raw = enemy or {}    # 主目标 dict（单怪时整个敌方单位）
        if enemies is not None:
            self.enemies = [dict(u) for u in enemies]
            # v121 CTB：敌方单位 ct 缺省 -spd（快者先手）；随 enemies 阵列持久化
            for u in self.enemies:
                if "ct" not in u:
                    u["ct"] = _ct_initial_wait(u.get("spd", 0))  # v130.10 绝对时刻：初始行动等待 = cost
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
        # v137 副本（btype="instance"）：enemies/allies 直传引用（非拷贝）——引擎内
        # 改单位 buffs/stacks/hp 直接写回 st 对象（R9 引用断裂风险防护，勿改回拷贝）
        if self.btype == "instance":
            if enemies is not None:
                self.enemies = enemies
            else:
                self.enemies = self._st.get("enemies") or self.enemies
            # 存活玩家快照引用（alive 过滤；命令层显式传 allies 时以其为准——含动态加入）
            if allies is not None:
                self.allies = allies
            else:
                self.allies = [p for p in (self._st.get("players") or {}).values()
                               if (self._st.get("alive") or {}).get(str(p.get("qq_id")), True)]
            # 玩家快照站位字段兜底（老存档恢复；对应 instance._instance_ensure_player_fields）
            for _a in self.allies:
                _cls = _a.get("class_name", "")
                _ci = C.CLASSES.get(_cls, {})
                _a.setdefault("rank", _ci.get("default_rank", 2))
                _a.setdefault("reach", _ci.get("reach", _ci.get("default_rank", 2)))
                _a.setdefault("uid", "p_{}".format(_a.get("qq_id", "")))
                _a.setdefault("buffs", {})
                _a.setdefault("stacks", {})
                _a.setdefault("defending", False)
                _a.setdefault("charging", None)
                _a.setdefault("ct", _ct_initial_wait(_a.get("spd", 0)))  # v130.10 绝对时刻播种
            # 玩家 ct 权威 = 各快照 snap["ct"]（self.p_ct 弃用，勿用于 instance 调度）
        else:
            self.allies: list = allies or []   # v122 我方阵列（治疗指定队友：副本传存活玩家快照引用）
        self._origin_enemy = dict(self.enemies[0]) if self.enemies else {}
        # v130.7 意见#17 多目标战斗击杀记录：敌方死亡单位 dict 快照列表
        # （_remove_unit 敌方死亡时记录；胜利结算按全部击杀逐个计任务进度）
        self.killed_enemies: list = []
        self.allies: list = allies or []   # v122 我方阵列（治疗指定队友：副本传存活玩家快照引用）
        self.player = player or {}         # v105 攻击方属性读取（_monster_dodge_check 需要玩家精准）
        self.p_buffs: dict = {}            # 玩家增益 {effect: turns}
        self._reduce_all_left: int = 0     # v113.1 团队减伤 reduce_all 剩余刻（百分比存 p_buffs["reduce_all"]）
        self._p_buff_hits: dict = {}       # v151 时刻制：防御型 buff 受击计数 {effect: 剩余受击次数}——防御/减伤/受击类按"敌方出手次数"计时而非玩家刻
        self.poi_buff: dict | None = None  # v104 M23 神龛祝福：{stat,mult,name}，持久 5 次战斗，battle 开始时消费 1 次
        self.p_hot: dict = {}              # v101.28 食物持续恢复 {"heal": 比例, "mana": 比例, "turns": 剩余刻}
        self.p_food_effects: list = []     # v101.28e 食物效果（战斗中吃料理获得，本场有效；独立于装备词条体系）
        self.p_shields: dict = {}          # v101.28d 护盾 buff 化：来源 → {"value": 盾值, "turns": 剩余刻}，同源可叠厚，异源并存
        self.e_minions: list = []          # v101.28l #438 真召唤：敌方援军实体 [{name,hp,max_hp,atk,matk}]
        self.summons: list = []            # v107 召唤物：玩家侧独立实体 [{tid,name,icon,hp,max_hp,atk,def,dmg_type}]
        self.p_defending = False           # 玩家本刻是否防御
        self.charging: dict | None = None  # v2 玩家侧蓄力状态 {"skill","left","name"}（§6）
        self.result = None                 # None | victory | defeat | fled
        self.title_bonus = title_bonus or {}  # 副业大师称号属性加成
        self.team_effects: list = []         # v50 团队技能效果（副本全队广播用）
        self.mech_stacks: dict = {}          # v59 分支机制叠层（随战斗持久化，不再挂 player 避免每刻丢失）
        # v2.0 核心资源（12 章 1.2：怒气/元素亲和/精力/信仰/连击点/气）
        # 随战斗序列化，同 mech_stacks 机制；阶段五引擎先挂载，技能数据落地后消费
        self.resources: dict = {}          # v2.0 核心资源（怒气/元素亲和/精力/信仰/连击点/气），随战斗序列化
        self.cooldown: dict = {}           # v2.0 技能冷却（技能名 → 剩余刻数），随战斗序列化；刻结束递减
        self.combo_seq: list = []          # v2.0 拳师连招序列（拳/踢/掌 tag 记录，满 3 触发三连）
        self.last_combo_tag: str | None = None  # v130.6 变招：上一招连招 tag（三连清空后仍记忆）
        self._last_element = None           # v130.2 法师攻线·元素：上次施放元素（同系连发判定）
        self._tailwind_prev_energy = None   # v130.2d 疾风余韵：上刻结束时精力快照（跨刻态，随战斗序列化）
        self.p_eff: dict = {}              # v130.2 物品效果持久数据（resource_amp / mana_cost_down / buff_phys_next / phys_up / battle_start 预充标记），随战斗序列化
        # v130.2f2：满溢转盾冷却（每刻限 1 次转盾，刻末 _end_round 重置，随战斗序列化）
        #            + 潜行出手标记（本次出手是否潜行，供暴击结算读；出手时置位/复位，瞬时态不序列化）
        self._overflow_shield_cd: bool = False
        self._stealth_atk: bool = False
        # v139 职业融合：模式状态机（dual_form/focus/vent + charge 电荷），随战斗序列化
        # 状态统一存 self（同 mech_stacks 惯例），通过 _v139_sync 桥接到 player dict
        self._v139_modes: dict = {}
        self._v139_charge: dict = {}
        if player:
            # v95.19: 战斗内属性统一用实时计算值——DB max_hp/max_mp 是注册/升级快照，换装备后过时，
            # 会导致战斗内血量上限/治疗 clamp/护盾与『角色』面板不一致（装备 HP 加成战斗内不生效）
            try:
                _st = self._player_stats(player)
                player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
                player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
            except Exception:
                pass
            # v139 配置注入：core_resources 的 dual_form/focus/vent 定义挂到 player dict
            # （battle_modes/battle_bars 纯函数读 player["dual_form"]/["focus"]/["vent"]；
            #   缺失 = 默认不启用，兼容旧职业/旧存档；转职分支差异由 core_resource_override 覆盖）
            try:
                from . import engine as _E139
                _crd139 = _E139.core_resource_def(player.get("class_name", "")) or {}
                for _mk139 in ("dual_form", "focus", "vent"):
                    if _crd139.get(_mk139) and not player.get(_mk139):
                        player[_mk139] = _crd139[_mk139]
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
        # 阶段八：战斗开始词条——护盾（10% 生命护盾/3 刻，数值读 affixes 数据 shield_hp_pct/turns；
        # v101.28d 盾 buff 化）
        if player and "shield" in self._equip_affix_ids(player):
            _se = (C.AFFIXES.get("shield") or {}).get("effect") or {}
            self._add_shield("affix_shield",
                             int(player.get("max_hp", 100) * float(_se.get("shield_hp_pct", 0.10))),
                             int(_se.get("turns", 3)))
        # v140 S1 战斗开始专属：狼嚎（wolf_howl）/ 蓄势待发（surge_ready）/ 奥术屏障（arcane_ward）
        if player:
            _bs_ids = set(self._equip_affix_ids(player))
            if "wolf_howl" in _bs_ids:
                self.p_eff["wolf_howl_mult"] = 1.10
                self._startup_logs = list(getattr(self, "_startup_logs", []) or []) + ["🐺 狼嚎！本场伤害+10%"]
            if "surge_ready" in _bs_ids:
                self.p_eff["surge_ready"] = True
                self._startup_logs = list(getattr(self, "_startup_logs", []) or []) + ["💪 蓄势待发：下一次攻击伤害 +15%！"]
            if "arcane_ward" in _bs_ids:
                self._add_shield("arcane_ward", int(player.get("max_hp", 100) * 0.15), 3)
                self._startup_logs = list(getattr(self, "_startup_logs", []) or []) + ["🔮 奥术屏障：奥术护盾笼罩周身！"]
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
        # v140 波3.1：特效装备战斗开始（星辉壁垒/疾风步/深渊屏障/蚀月之冠/奥术苍穹等）
        if player:
            try:
                from .core.weapon_effects import proc as _we_proc
                _we_proc(self, player, "battle_start", {}, [])
            except Exception:
                pass
        # v121 CTB 行动时间轴：玩家 ct（越小越先行动），开局 = -spd（快者先手）
        # v130.10 绝对时刻 CTB：玩家时钟从 0 起（时刻制外壳第一刻必动，行动后 +cost）。
        # 旧 v121 初始 -spd 是相对时钟追赶死锁的根源（怪被玩家行动持续回拽 → 站桩）。
        self.p_ct: float = 0.0
        self._player_hit: bool = False        # 本场玩家是否受过击（v2.1 条件：未受击增伤）
        self.first_attack_done: bool = False  # 阶段九：龙之吐息首击标记（每场首次攻击 +15%）
        self._death_pact_used: bool = False   # v107 死亡契约（暗影祭司）：每场 1 次标记
        self._set_immune_used: bool = False   # v130.2c 圣典·日冕 4 件：满信仰免伤 每战 1 次标记
        # O116 受击伤害日志延迟输出：_enemy_turn 只计算伤害并暂存"造成 X 点伤害"文案，
        # 由 _damage_player 在闪避判定后决定是否输出（闪避时不再同时报伤害）
        self._pending_dmg_lines: list = []
        # v154 读条命中制：玩家出手瞬间暂存的结算参数（cast_done 事件触发时消费）
        self._pending_player_cast: dict | None = None
        # v154 读条命中制：玩家是否正在读条（出手 → 命中 之间；可被控制打断）
        self._player_casting: bool = False
        # v2 受击伤害来源（打断判定用）：最近一次对敌方造成伤害的来源名（默认玩家）
        self._last_hitter: str = "你"
        # DOT 重构（契约 §2.1）：持续减益结算闸门——单机每玩家行动结算一次（现状频率）；
        # 副本由 instance 层 set False；世界 Boss 由 combat 层 force=True 触发
        self._dot_pending: bool = True
        # v152：开战初始化事件队列——每个敌方排初始 enemy_act 事件；DOT/宠物/Boss 机制排初始 tick。
        # 注意：from_state 恢复的战斗不在此重排（由 from_state 末尾按存档事件恢复），
        # 仅新建战斗在此初始化。副本（instance）由命令层自行调度，不在此排 enemy_act。
        if self.btype != "instance":
            try:
                for _u in self.enemies:
                    if _u.get("hp", 0) > 0:
                        _init_t = float(_u.get("ct", 0) or _ct_initial_wait(_u.get("spd", 0)))
                        self._schedule(_init_t, {"type": "enemy_act", "unit": _u})
                # v154 宠物独立速度读条：开战排第一个 pet_tick（宠物初始等待 = 出招时间，
                # 按宠物自身 spd 折算）。pet_tick 触发 = 宠物出手（决定技能 + 排 cast_done），
                # 出招跑完 = 技能生效，随后重排下次 pet_tick（周期 = 出招 + 收招）。
                if self.pet and int(self.pet.get("level", 0) or 0) >= 10:
                    _pet_spd = self._pet_spd()
                    _pt = CAST_PET_SKILL * self._ct_cost(_pet_spd)
                    self._schedule(_pt, {"type": "pet_tick"})
                # DOT 由 player_turn 开头 _turn_start 结算（_tick_dots + _dot_pending 闸门），
                # 不排独立 dot_tick 事件（避免重复结算）。
                # Boss 定时机制由 _enemy_turn 内 _boss_mech 触发（每次敌方行动时按 r % interval 判定），
                # 不排独立 mech_tick 事件（避免双重触发）。
                # 注：词条/套装回血（regen）不排独立事件——由 player_turn 开头的 _turn_start
                # 在玩家每次行动时结算（与旧时刻制"每玩家行动结算一次"一致），避免 DOT 重复结算。
            except Exception:
                pass

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
        u.setdefault("ct", _ct_initial_wait(u.get("spd", 0)))  # v130.10 绝对时刻：初始行动等待 = cost
        # v155 兜底（2026-09-01 玩家实战抓包）：旧存档恢复路径（enemies=[] 只有 enemy 兼容键）
        # 的敌人可能缺结算字段——补默认值防 _handle_victory KeyError: 'exp'/'name'
        # ⚠️ 不能补 lv：lv 缺失时 _damage_enemy 等级压制自然跳过（补 lv=1 会让 30 级玩家对
        # 低等级怪触发 ×1.02/级 连乘，伤害虚高——test_v107_dmg_type 实测 dealt 390 vs 218）
        u.setdefault("name", "敌人")
        u.setdefault("exp", 0)
        u.setdefault("gold", 0)
        u.setdefault("drops", [])
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
            # v152：round 概念删除，改 _now（绝对时刻）+ _p_acts（玩家行动计数，展示用）
            "now": self._now,
            "p_acts": self._p_acts,
            # v2：敌方完整阵列（核心）；enemy 保留为兼容键（= 主目标引用）
            "enemy": self.enemy,
            "enemies": self.enemies,
            "killed_enemies": getattr(self, "killed_enemies", []),  # v130.7 意见#17 击杀记录随战斗持久化（跨消息续战胜利不丢）
            "charging": self.charging,
            "pet": self.pet,
            "p_buffs": self.p_buffs,
            # v151 时刻制：防御型 buff 受击计数（随战斗序列化，跨消息续战不丢）
            "p_buff_hits": getattr(self, "_p_buff_hits", {}) or {},
            # v113.1 团队减伤 reduce_all 剩余刻：percent 存 p_buffs、刻数独立计时，
            # 必须随存档持久化，否则恢复后 __init__=0 被下刻立即弹掉 reduce_all。
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
            "last_combo_tag": self.last_combo_tag,
            "p_ct": self.p_ct,
            "player_hit": self._player_hit,
            "first_attack_done": self.first_attack_done,
            "death_pact_used": getattr(self, "_death_pact_used", False),
            "set_immune_used": getattr(self, "_set_immune_used", False),
            # v130.2f 致命预谋：首次终结返还标记（随战斗持久化，防断线恢复后重复返还）
            "assassin_refund_used": getattr(self, "_assassin_refund_used", False),
            # v104 M02 P2-9：断线恢复后 burst 机制（灼烧引爆/剑刃风暴/神恩护盾）与
            # 元素跃迁日志依赖 _last_player/_shifted_element，必须随战斗状态持久化
            "last_player": getattr(self, "_last_player", None),
            "shifted_element": getattr(self, "_shifted_element", None),
            # DOT 重构（契约 §2.1）：持续减益结算闸门状态随战斗序列化
            "dot_pending": getattr(self, "_dot_pending", True),
            "tailwind_prev_energy": getattr(self, "_tailwind_prev_energy", None),  # v130.2d 疾风余韵跨刻状态
            "overflow_shield_cd": getattr(self, "_overflow_shield_cd", False),  # v130.2f2 满溢转盾冷却（断线恢复不重置冷却）
            # v139 职业融合：模式状态机随战斗序列化（dual_form/focus/vent + charge 电荷）
            "v139_modes": getattr(self, "_v139_modes", {}),
            "v139_charge": getattr(self, "_v139_charge", {}),
            # v154 读条命中制：玩家读条状态随战斗持久化（断线恢复不丢读条）
            "player_casting": getattr(self, "_player_casting", False),
            "pending_player_cast": getattr(self, "_pending_player_cast", None),
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
        # v152：round 概念删除，改 _now（绝对时刻）+ _p_acts（玩家行动计数，展示用）。
        # 兼容旧档：读 round 时 _p_acts 兜底；_now 缺省 0。
        b._now = float(st.get("now", 0.0) or 0.0)
        b._p_acts = int(st.get("p_acts", st.get("round", 0)) or 0)
        # v158 副本合并：from_state 透传副本回调钩子（instance 注入 st["_cb"]）
        b._inst_cb = st.get("_cb") if isinstance(st, dict) else None
        b.allies = st.get("allies") or []   # v122 治疗指定队友（副本传存活玩家快照引用）
        b.p_buffs = dict(st.get("p_buffs") or {})
        b._p_buff_hits = dict(st.get("p_buff_hits") or {})  # v151 时刻制：防御型 buff 受击计数
        b._reduce_all_left = int(st.get("reduce_all_left", 0) or 0)  # v113.1 恢复减伤剩余刻
        b.poi_buff = st.get("poi_buff")
        b.p_hot = st.get("p_hot", {}) or {}
        b.p_food_effects = st.get("p_food_effects", []) or st.get("p_food_affixes", []) or []
        b.p_shields = st.get("p_shields", {}) or {}
        b.e_minions = st.get("e_minions", []) or []
        b.killed_enemies = [dict(u) for u in (st.get("killed_enemies") or [])]  # v130.7 意见#17 击杀记录恢复
        b.summons = st.get("summons", []) or []
        b.charging = st.get("charging")
        b.p_defending = st.get("p_defending", False)
        b.e_defending = st.get("e_defending", False)
        b.mech_stacks = st.get("mech_stacks", {}) or {}
        b.resources = st.get("resources", {}) or {}
        b.p_eff = st.get("eff_data", {}) or {}  # v130.2 物品效果持久数据
        b.cooldown = st.get("cooldown", {}) or {}
        b.combo_seq = st.get("combo_seq", []) or []
        b.last_combo_tag = st.get("last_combo_tag") or None
        b.team_effects = []
        # v121 CTB：玩家 ct 读取（老存档兜底 0）；敌方单位 ct 兜底 -spd
        # v130.10 绝对时刻：p_ct<0（旧相对时钟存档）重置 0；怪 ct 缺失或<=0（旧 -spd 语义）重置为初始等待
        b.p_ct = float(st.get("p_ct", getattr(b, "p_ct", 0.0)) or 0.0)
        if b.p_ct < 0:
            b.p_ct = 0.0
        for _u in b.enemies:
            _c = _u.get("ct")
            if "ct" not in _u or float(_c or 0) <= 0:
                _u["ct"] = _ct_initial_wait(_u.get("spd", 0))
        b._player_hit = bool(st.get("player_hit", False))
        b.first_attack_done = bool(st.get("first_attack_done", False))
        b._death_pact_used = bool(st.get("death_pact_used", False))
        b._set_immune_used = bool(st.get("set_immune_used", False))
        b._assassin_refund_used = bool(st.get("assassin_refund_used", False))  # v130.2f 致命预谋返还标记
        b._v139_modes = st.get("v139_modes", {}) or {}   # v139 职业融合：模式状态机恢复
        b._v139_charge = st.get("v139_charge", {}) or {}  # v139 charge 电荷恢复
        # v154 读条命中制：恢复玩家读条状态（断线恢复不丢读条）
        b._player_casting = bool(st.get("player_casting", False))
        b._pending_player_cast = st.get("pending_player_cast")
        # v104 M02 P2-9：恢复 _last_player/_shifted_element；_last_player 为空保持
        # 未设置（hasattr=False，避免 battle_mech 对 None 调 _player_stats 崩溃）
        _lp = st.get("last_player")
        if _lp:
            b._last_player = _lp
        b._shifted_element = st.get("shifted_element")
        # DOT 重构（契约 §2.1）：恢复持续减益结算闸门（老档案缺失默认 True=每玩家行动结算一次）
        b._dot_pending = bool(st.get("dot_pending", True))
        b._tailwind_prev_energy = st.get("tailwind_prev_energy")  # v130.2d 疾风余韵跨刻状态
        b._overflow_shield_cd = bool(st.get("overflow_shield_cd", False))  # v130.2f2 满溢转盾冷却随战斗序列化
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
        # v158 副本合并：instance 类型恢复时按敌方 ct 排 enemy_act 事件——事件队列驱动
        # 敌方行动（v137 起 instance 被排除在 __init__ 排事件之外，靠命令层外部轮转；
        # 合并后副本也走 battle 队列，必须恢复敌方事件）。野外非 instance 已在
        # __init__ 排过，且 from_state 原本不重排（旧存档事件在 _events 里，见 __init__ 注释）；
        # 此处仅对 instance 补排，野外/世界Boss 不受影响。
        if b.btype == "instance":
            for _u in b.enemies:
                if _u.get("hp", 0) > 0:
                    _init_t = float(_u.get("ct", 0) or 0)
                    if _init_t <= 0:
                        _init_t = _ct_initial_wait(_u.get("spd", 0))
                    b._schedule(_init_t, {"type": "enemy_act", "unit": _u})
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
        # v139 桥接：把 self._v139_modes/_v139_charge 挂到 player dict 上，
        # 让 battle_modes/battle_bars 纯函数读写正确的状态源（状态统一存 self）
        if player is not None:
            player["v139_modes"] = self._v139_modes
            player["v139_charge"] = self._v139_charge
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
        # v130.2f2（T6 P1-2/P1-3）：渠道统一——词条/套装/药水/战前预充等渠道的类主资源增益
        # 统一走 _res_gain_class：上限含词条/套装加成（不再按裸 rd.max 封顶被回退），
        # 且满溢量按 overflow_shield 转盾（满资源不再静默蒸发）。副资源（resonance/echo 等）
        # 与键≠类主资源的情况仍走下方按 key 注册路径，行为不变。
        _crd_route = E.core_resource_def(player.get("class_name", ""))
        if _crd_route and key == _crd_route.get("key"):
            return self._res_gain_class(player.get("class_name", ""), key, int(amount or 0), logs)
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

    def _res_gain_class(self, cls: str, k: str, amount: int, logs: list | None = None) -> int:
        """类主资源增加（带上限 + 隐藏线满溢转盾）。v130.2：悼咏 canticle overflow_shield=True
        时满 10 后每溢出 1 点转自身 5 点护盾（冷却 1 刻，priest.md §5.2）。
        v130.2f2（T6 P1-1/P1-3）：①冷却 1 刻落地——转盾后置位 _overflow_shield_cd，
        本刻内不再转盾（多段受击不再段段白嫖），刻末 _end_round 重置；
        ②渠道统一——词条/套装/药水（_res_gain 主资源路由）与受击被动 res_gain（4848 改接）
        满溢也走本函数，满资源不再静默蒸发；③转盾 key 泛化（原硬编码 canticle_overflow，
        战士/拳师转盾也顶悼咏键名，现统一 overflow_shield 同源叠加）。"""
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
            if not getattr(self, "_overflow_shield_cd", False):
                shield = int(overflow * 5)
                self._add_shield("overflow_shield", shield, 1)
                self._overflow_shield_cd = True
                if logs is not None:
                    logs.append(f"🛡️ 满溢转化：{rd.get('name', k)}溢出 {overflow} 点 → 护盾 +{shield}（每刻限 1 次转盾）")
            elif logs is not None:
                logs.append(f"🛡️ 满溢转化：{rd.get('name', k)}溢出 {overflow} 点（本刻已转盾，冷却中）")
        self.resources[k] = new
        return new

    def _amp_resource(self, player: dict, trigger: str) -> int:
        """v130.2 资源增幅（resource_amp）消费挂点（P0-1：4 种药水写无读修复）。
        p_eff['amps'] 中 trigger 匹配且剩余计数>0 的条目，额外 _res_gain 对应资源 amount。
        trigger ∈ {on_hit_taken 受击 / on_land_hit 出手命中 / on_heal 治疗 / regen 自然回复}。
        on_hit 双语义（沸腾战血=受击/影袭=出手命中）由 hits_left 区分：>0 → 出手命中逐次递减；
        ≤0 → 持续时长制（turns 在 _end_round 递减）。返回本次额外增加总量。"""
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
                           "first_hit_immune", "battle_start_cp", "finisher_crit",
                           "combo_finisher_per_layer", "battle_start_res", "chi_skill_phys",
                           "full_rage_pursuit",
                           "holy_halo_shield", "holy_field_heal", "divine_grace_burst",
                           "cloth_heal_overflow", "bless_ward_shield", "holy_bastion_def",
                           "shi_quan_retort", "bi_chui_wall", "pan_shi_steady", "anvil_parry",
                           "tie_shou_blood", "hu_xiao_barrier", "ferry_repel",
                           "tie_pi_bulwark", "shou_wang_ward", "tie_pi_harden")

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

    # ---------------- 技能冷却（v2.0 → v152 时刻制） ----------------
    def _skill_cd_left(self, skill_name: str) -> int:
        """技能剩余冷却（按时刻：ready_at - now，折算成'约 N 刻'展示用；0 = 可用）。
        v152：cooldown 存 ready_at 绝对时刻（不再存剩余刻数）。"""
        ra = self.cooldown.get(skill_name)
        if not ra:
            return 0
        if self._now >= float(ra):
            # 到期即清（惰性清理，避免依赖 _tick 时机）
            del self.cooldown[skill_name]
            return 0
        return max(1, int((float(ra) - self._now) / (ACT_TICK or 2.0)) + 1)

    def _skill_on_cd(self, skill_name: str) -> bool:
        return self._skill_cd_left(skill_name) > 0

    def _set_skill_cd(self, skill_name: str, cd: int):
        """设置技能冷却。v152：cd（刻数）→ 绝对时刻 ready_at = now + cd × ACT_TICK。
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
            self.cooldown[skill_name] = self._now + cd * (ACT_TICK or 2.0)

    def _tick_cooldowns(self):
        """v152 时刻制：冷却到期检查（惰性清除，非递减）。保留函数名兼容外部调用。"""
        _now = self._now
        for k in list(self.cooldown):
            if _now >= float(self.cooldown[k]):
                del self.cooldown[k]
        # v151 修复（特效冷却审计 P1-1）：特效装备冷却（we_*_cd）此前只写不递减——
        # 永冻领域/无尽辉光/哨兵壁垒/深岩壁垒等"冷却 N 刻"实际永久生效。
        # v152：p_eff 中 we_*_cd 存 ready_at 绝对时刻（写入点 weapon_effects.py 已换算），到期惰性清除。
        _pe = self.p_eff
        if isinstance(_pe, dict):
            for _k in [k for k in list(_pe) if k.startswith("we_") and k.endswith("_cd")]:
                if _now >= float(_pe.get(_k, 0) or 0):
                    _pe.pop(_k, None)
        # v151 修复（特效冷却审计 P1-2）：星辉壁垒每 5 刻刷新计数（we_starlight_next）
        # v152：we_starlight_next 存 ready_at 绝对时刻，到期 → 重新触发 battle_start 特效（星辉壁垒刷新护盾）
        if isinstance(_pe, dict) and float(_pe.get("we_starlight_next", 0) or 0) > 0:
            if _now >= float(_pe.get("we_starlight_next", 0) or 0):
                _pe.pop("we_starlight_next", None)
                try:
                    from .core.weapon_effects import proc as _we_proc
                    _we_proc(self, self.player, "battle_start", {}, [])
                except Exception:
                    pass

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
        self.last_combo_tag = tag  # v130.6：无论推进/重置/触发都记忆上一招
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

    # —— 苦修士·武僧：禅意持有加伤（v151 隐藏职业删除：cls_wu_sheng 已移除）——
    def _zen_hold_mult(self, player: dict) -> float:
        """v151 隐藏职业删除：禅意持有加伤（原 cls_wu_sheng 专属）恒 1.0"""
        return 1.0

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
        logs.append(f"🎵 回声驻留 +{int(amount or 0)}：全队刻恢复随回声层数(当前 {cur}/{cap})")
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
            log = "❄️冻结！目标被冰封 1 刻！"
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
        """v154 速度折算系数：动作耗时 = 基准耗时 × 折算系数。
        v121 语义：行动消耗 cost = BASE_DELAY / max(1, min(spd, SPD_CT_CAP))（恢复间隔）。
        v154 语义：恢复间隔取消，速度只影响出招/收招快慢。
        折算系数 = SPD_REF / max(1, min(spd, SPD_CT_CAP))——速度 50 时 = 1.0（基准耗时）。
        """
        try:
            eff = min(float(spd or 0), SPD_CT_CAP)
        except Exception:
            eff = 0.0
        return SPD_REF / max(1.0, eff)

    def _action_times(self, kind: str, player: dict | None = None, skill: dict | None = None,
                      item: dict | None = None, skill_name: str | None = None, spd: float | None = None) -> tuple:
        """v154 数据驱动动作时长（速度折算）：返回 (出招耗时, 收招耗时)。

        优先级：技能/职业/道具数据字段 > 全局默认常量（CAST_*）。
        kind: 'atk'|'skill'|'item'|'food'|'defend'|'flee'
        - skill:   skill.cast（出招）+ skill.recovery（收招，默认 0）；skill_name 传入时自查技能表
        - 职业普攻: class.cast_atk + class.recovery_atk（classes.py 顶层字段）
        - 职业防御: class.cast_defend + class.recovery_defend
        - 职业逃跑: class.cast_flee + class.recovery_flee
        - 道具:    item.cast + item.recovery
        - 兜底:    全局 CAST_* 常量（普攻 1.0/技能 1.6/道具 1.0/食物 1.0/防御 0.6/逃跑 2.0）
        v154 速度折算：出招/收招各 × (SPD_REF / 实际速度)。
        速度 50 = 基准耗时；速度 25 = ×2（慢一倍）；速度 80(cap) = ×0.625（最快）。
        spd 参数：显式传入则用（敌方侧调用）；否则从 player 读（玩家侧）。
        """
        _cast = _recovery = 0.0
        if kind == "skill":
            if not skill and skill_name and player:
                skill = E.skill_info(player.get("class_name", ""), skill_name) or {}
            if skill:
                _cast = float(skill.get("cast", 0) or 0)
                _recovery = float(skill.get("recovery", 0) or 0)
        elif kind == "atk" and player:
            _cls = (C.CLASSES or {}).get(player.get("class_name", ""), {})
            _cast = float(_cls.get("cast_atk", 0) or 0)
            _recovery = float(_cls.get("recovery_atk", 0) or 0)
        elif kind == "defend" and player:
            _cls = (C.CLASSES or {}).get(player.get("class_name", ""), {})
            _cast = float(_cls.get("cast_defend", 0) or 0)
            _recovery = float(_cls.get("recovery_defend", 0) or 0)
        elif kind == "flee" and player:
            _cls = (C.CLASSES or {}).get(player.get("class_name", ""), {})
            _cast = float(_cls.get("cast_flee", 0) or 0)
            _recovery = float(_cls.get("recovery_flee", 0) or 0)
        elif kind == "item" and item:
            _cast = float(item.get("cast", 0) or 0)
            _recovery = float(item.get("recovery", 0) or 0)
        elif kind == "food" and item:
            _cast = float(item.get("cast", 0) or 0)
            _recovery = float(item.get("recovery", 0) or 0)
        # 兜底：数据字段缺失 → 全局默认（不填 = 旧行为）
        if _cast <= 0:
            _cast = {"atk": CAST_ATK, "skill": CAST_SKILL, "item": CAST_ITEM,
                     "food": CAST_FOOD, "defend": CAST_DEFEND, "flee": CAST_FLEE}.get(kind, 1.0)
        # v154 速度折算：出招/收招各 × (SPD_REF / 实际速度)
        if spd is None:
            _spd = float((self._player_stats(player).get("spd", 0) if player else 0) or 0)
        else:
            _spd = float(spd or 0)
        _mult = self._ct_cost(_spd)
        return _cast * _mult, _recovery * _mult

    def _action_cast(self, kind: str, player: dict | None = None, skill: dict | None = None,
                     item: dict | None = None, skill_name: str | None = None, spd: float | None = None) -> float:
        """v154 数据驱动动作时长（速度折算）：返回总动作耗时 = 出招 + 收招。

        （= _action_times 两个返回值之和；保留函数名兼容既有调用。）"""
        _c, _r = self._action_times(kind, player=player, skill=skill, item=item,
                                    skill_name=skill_name, spd=spd)
        return _c + _r

    def _after_actor_ct(self, side: str, unit: dict | None = None, player: dict | None = None, cast_mult: float = 1.0):
        """v154 真·事件队列：行动者 next_act_at = now + 动作总耗时（出招+收招，绝对时刻）。
        兼容壳：保留函数名（大量外部调用）。side="p"：玩家行动完；side="e"：敌方单位行动完。
        cast_mult：**动作总耗时（秒，已含速度折算）**——总耗时 = 出招 + 收招，无恢复间隔。
        （v154 鱼鱼拍板：速度只影响出招/收招，恢复间隔取消。）
        - 玩家：p_ct 升级为"玩家下次可行动绝对时刻"（= now + 动作耗时）
        - 敌方：u["ct"] 升级为"该单位下次可行动绝对时刻"（= now + 动作耗时）
        - 绝对时刻制：其他单位不参与"时间流逝"（它们的 next_act_at 是绝对值，不因别人行动而变）。
        """
        _now = self._now
        if side == "p":
            _p = player or self.player or {}
            # v154：总耗时 = 动作耗时（出招+收招，已含速度折算），无恢复间隔
            self.p_ct = _now + float(cast_mult or 1.0)
            # 敌方：绝对时刻制下无需互相调整（next_act_at 已是绝对值）。兜底初始化。
            for u in self.enemies:
                if "ct" not in u or float(u.get("ct", 0) or 0) <= 0:
                    u["ct"] = _ct_initial_wait(u.get("spd", 0))
        else:
            u = unit or {}
            if "ct" not in u or float(u.get("ct", 0) or 0) <= 0:
                u["ct"] = _ct_initial_wait(u.get("spd", 0))
            # v154：敌方总耗时 = 动作耗时（已含速度折算），无恢复间隔
            # v154 防同刻连环触发：排到的时刻必须严格 > 当前 now（否则事件循环
            # 同一批再次触发被控跳过单位 → 眩晕/冻结后立刻又普攻的 bug）
            u["ct"] = max(_now + float(cast_mult or 1.0), _now + 0.001)
        # v137 副本（btype="instance"）allies 广播：多玩家 CTB 时间流逝对称。
        # 绝对时刻制下各玩家 next_act_at 独立，无需广播调整（各自按自己的 cost 排程）。
        # 保留函数签名兼容；instance 层调度由命令层 _instance_next_actor 按 next_act_at 选人。

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
                # 射程校验（审计 P1 修复）：目标在攻击范围外 → 拒绝（提示 + 不消耗刻）
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
        """蓄力刻开始结算：left 递增计时，归零自动释放技能。返回是否已释放。"""
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
                logs.append(f"⏳ 你正在蓄力【{cname}】(剩 {self.charging['left']} 刻)，本刻无法普攻/技能！")
        return False

    def _player_charging_blocked(self, logs: list, action: str) -> bool:
        """蓄力期间非防御/道具行动 → 拦截（提示剩余刻），返回是否被拦截。"""
        if not (self.charging and self.charging.get("skill")):
            return False
        if action in ("defend", "use_item", "flee"):
            return False
        cname = self.charging.get("name", self.charging.get("skill", "?"))
        left = int(self.charging.get("left", 1) or 1)
        logs.append(f"⏳ 你正在蓄力【{cname}】(剩 {left} 刻)！可『防御』或『使用 <道具>』")
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
        enemy_act: 是否在玩家行动后立即结算敌方刻（PVP 传 False，由对方真人操作）
        target: v2 指定目标（uid 或名字前缀，None=自动选择）
        v121：CTB 行动时间轴——玩家正常行动 +1 刻；行动后玩家 ct += cost，
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
        # v139 配置注入（player 传入时补一次）：core_resources 的 dual_form/focus/vent 定义挂到 player dict
        # （from_state 恢复的战斗 __init__ 不传 player 刷新不到，此处补注入；battle_modes/battle_bars 纯函数读这些字段）
        try:
            from . import engine as _E139b
            _crd139b = _E139b.core_resource_def(player.get("class_name", "")) or {}
            for _mk139b in ("dual_form", "focus", "vent"):
                if _crd139b.get(_mk139b) and not player.get(_mk139b):
                    player[_mk139b] = _crd139b[_mk139b]
            player["v139_modes"] = self._v139_modes
            player["v139_charge"] = self._v139_charge
        except Exception:
            pass
        # v63 玩家被沉默：技能类行动先被拦截转普攻（置于 O118 校验前，避免未学习技能
        # 在沉默下先被拦截而无法转普攻）；后续沉默状态下只能普攻/防御/道具
        if "silence" in self.p_buffs and action == "skill":
            logs.append("🤐 你被沉默，无法使用技能！(只能普攻/防御/道具)")
            action = "attack"

        # O118 技能施放失败保护：正常刻开始前先校验（技能不存在/未学习/冷却/蓝/
        # 核心资源不足），失败不消耗刻、不结算敌方行动，玩家可重新选择其他行动
        if action == "skill":
            _fl, _blocked = self._skill_cast_blocked(skill_name, player)
            if _blocked:
                _fl.append("技能施放失败！可选择其他行动")
                return logs + _fl, False

        # ---- 正常行动开始（v152：不再有刻计数，_p_acts 仅展示用）----
        self._p_acts += 1
        # v116.1 pv_broken：玩家本刻是否用过技能（供敌方 _boss_mech 反扑判定）——刻开始复位
        self._player_recent_skill = False
        # v2 蓄力：刻开始结算——归零自动释放技能（§6.2）
        self._player_charge_release(player, logs)
        logs += self._turn_start(player)
        # v101.28 食物持续恢复：正常刻开始结算 hot（每刻一次，含眩晕/冻结刻）
        if self.p_hot and self.p_hot.get("turns", 0) > 0:
            logs += self._apply_hot(player)
        # v154 宠物独立速度读条：宠物技能由 pet_tick 事件驱动（_process_until 内触发），
        # 不再跟随玩家行动（玩家行动时宠物可能正在读条，节奏由宠物自身 spd 决定）。
        # v63 玩家被控：眩晕/冻结 → 跳过本刻行动（CTB 下行动浪费，玩家 ct 照走，随后敌方行动段）
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
                    # 射程校验拒绝（审计 P1 修复）：不消耗刻，玩家可重新选择
                    logs.append(f"⛔ 【{target}】在你的攻击范围之外，够不着！(近战只可及前排)")
                    return logs, False
                # v127.3：指定目标未找到 → 明确提示（不再静默回退自动选择）
                if getattr(self, "_target_not_found", None):
                    logs.append(f"⚠️ 没有找到目标『{self._target_not_found}』，攻击自动选择！(站位图编号：a1/a2… 敌方，b1/b2… 友方)")
                    self._target_not_found = None
        else:
            self._active_target = None

        if action == "defend":
            # v152 数据驱动：防御动作时长 = 职业 cast_defend（默认 CAST_DEFEND）
            return self._do_defend(player, logs, enemy_act,
                                   cast_mult=self._action_cast("defend", player=player))
        if action == "flee":
            # v152 数据驱动：逃跑动作时长 = 职业 cast_flee（默认 CAST_FLEE）
            return self._do_flee(player, logs, cast_mult=self._action_cast("flee", player=player))
        if action == "use_item":
            logs += self._do_use_item(skill_name or "", player)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True
            # v152：使用道具也是玩家行为，有行为时长（吃药有时长，鱼鱼明确要求）
            # 道具 cast：payload 内嵌 cast:N 则用 N（自定义字段），否则食物/普通道具用全局默认
            _cast_mult = self._item_payload_cast(skill_name or "")
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player, cast_mult=_cast_mult)
            return self._enemy_phase(player, logs, enemy_act)

        st = self._player_stats(player)
        # v154 读条命中制：技能/普攻出手瞬间 → 排 cast_done 事件（出招读条结束 = 命中时刻结算）
        if action == "skill":
            logs += self._do_player_skill(skill_name, player, target=target)  # v122：target 传治疗队友目标
            # v116.1 pv_broken：记录玩家本刻用了技能，敌方 _boss_mech 据此决定反扑
            self._player_recent_skill = True
            # v154 数据驱动：出招 + 收招（速度折算）
            _cast_t, _recover_t = self._action_times("skill", player=player, skill_name=skill_name)
            # 出招读条结束 = 命中 → 排 cast_done 事件（结算用命中时刻状态）
            if self.btype != "pvp":
                self._schedule_cast_done(self._now + _cast_t, {"side": "p", "kind": "skill",
                                                               "skill": skill_name, "target": target})
                # 玩家下次可行动 = 命中时刻 + 收招耗时（= 出手 + 总耗时）
                # 保证 _process_until 推进到 p_ct 时 cast_done 已触发（cast_done < p_ct）
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
                self._player_casting = True
            else:
                # PVP 不介入：立即结算（保持真人轮流；_do_player_skill 内部 PVP 走立即路径）
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
            _cast_mult = _cast_t + _recover_t
        else:
            # v154 读条命中制：普攻出手瞬间暂存参数（命中时刻 cast_done 才结算）
            if self.btype != "pvp":
                self._pending_player_cast = {"kind": "atk", "st": st}
            else:
                logs += self._player_attack(st, player)
            # v154 数据驱动：出招 + 收招（速度折算）
            _cast_t, _recover_t = self._action_times("atk", player=player)
            if self.btype != "pvp":
                self._schedule_cast_done(self._now + _cast_t, {"side": "p", "kind": "atk"})
                # 玩家下次可行动 = 命中时刻 + 收招耗时（= 出手 + 总耗时），保证 cast_done 先触发
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
                self._player_casting = True
            else:
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
            _cast_mult = _cast_t + _recover_t

        if self._enemy_dead():
            self.result = "victory"
            self._end_round()
            return logs, True

        # v154：玩家下次可行动点已由 _after_actor_ct 设为命中时刻 + 收招（PVP 已即时结算）
        # 注意：非 PVP 下 cast_done 事件会在 _enemy_phase 推进时触发结算

        # v107 召唤物自动攻击：玩家正常行动结束后、敌方行动前（每刻一次）
        if self.summons:
            logs = self._summons_act(player, logs)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True

        # 敌方行动段
        return self._enemy_phase(player, logs, enemy_act)

    def _enemy_phase(self, player: dict, logs: list, enemy_act: bool, defend: bool = False) -> tuple:
        """v152 真·事件队列：推进战斗时刻到玩家下次可行动点，期间处理所有事件（敌方行动/DOT/机制）。
        - 玩家行动后：玩家 next_act_at = now + 行为耗时（已在 player_turn 内 _after_actor_ct("p") 排好）
        - _process_until(玩家 next_act_at)：弹出并处理所有 t <= until 的事件
          · enemy_act：敌方单位行动（用其 buffed spd cost 排下一次）
          · dot_tick / mech_tick / pet_tick / regen_tick：持续效果与定时机制
          · cast_done：玩家行为生效（普攻/技能伤害在 cast 结束时结算）
        - 防御状态（defend=True）：期间所有敌方伤害减半
        - 硬上限：单次推进最多处理 64 个事件（防极端配速死循环/无限事件）
        PVP（btype=="pvp"，或 enemy_act=False 由对方真人操作）不介入。
        """
        if enemy_act and self.btype != "pvp":
            until = float(getattr(self, "p_ct", 0) or 0)
            if until <= 0:
                until = self._now + (ACT_TICK or 2.0)
            # v152：行为生效事件——玩家行动已即时结算效果，这里只推进时间处理事件
            self._process_until(until, logs, player, defend=defend)
            # v158 副本合并：instance 玩家行动后只补结算一次"读条命中"事件（cast_done）——
            # 敌方出招读条结束的伤害要在本次行动内结算（否则 from_state 不恢复事件队列，
            # 读条结算跨次丢失 → 敌方伤害永远不结算）。只处理**当前已排好的** cast_done
            # （不 while 追新：敌方新出招的读条留给下次玩家输入，避免一次行动内敌方多次
            # 结算打死玩家——2026-09-01 test_commands_feedback f4 被骷髅兵连打秒杀）。
            if self.btype == "instance":
                _peek = self._events[0] if self._events else None
                if _peek is not None and _peek[2].get("type") == "cast_done":
                    self._process_until(_peek[0] + 0.001, logs, player, defend=defend)
            # v140 波3.1：特效装备敌人行动后（兰顿倦意/冰脉寒流——速度 -6%/-8% 每层）
            try:
                from .core.weapon_effects import proc as _we_proc
                _we_proc(self, player, "enemy_act", {}, logs)
            except Exception:
                pass
            self._active_target = None  # 敌方行动结束后重置玩家下次目标
        else:
            # v157 修复：enemy_act=False（副本/PVP 由外部驱动敌方）时仍要推进玩家事件
            # ——v154 读条命中制把玩家伤害结算搬进 cast_done 事件（_process_until 内触发），
            # 副本 _instance_act 传 enemy_act=False 导致 cast_done 永不触发 → 技能只扣蓝不结算
            # （2026-09-01 玩家实抓：副本卡战斗、蓝扣了技能没伤害）。这里推进到玩家下次
            # 行动点，只处理玩家事件（cast_done/pet_tick 等），不驱动敌方（enemy_act=False
            # 时 _process_until 的 enemy_act 事件直接 continue，见 _process_until 分支）。
            until = float(getattr(self, "p_ct", 0) or 0)
            if until > 0:
                self._process_until(until, logs, player, defend=defend, skip_enemy=True)
        # v152 时刻制：时间推进（含到期检查）。dt = 玩家下次可行动点 - 当前 now。
        # _process_until 已把 now 推进到 <= p_ct 的最新事件时刻；此处补推进到 p_ct（玩家行动点），
        # 期间处理到期（buff/CD/DOT 用绝对时刻，与推进步长无关）。
        _target = float(getattr(self, "p_ct", 0) or 0)
        _dt = _target - self._now
        if _dt > 0:
            self._advance_time(_dt)
        return logs, self.result is not None

    def _schedule(self, t: float, ev: dict):
        """排一个事件到队列（按 t 升序）。ev 含 type 及 payload。
        v152：seq 用全局递增计数器，避免同 t 时比较 dict 报错。"""
        if t < self._now:
            t = self._now
        self._ev_seq = getattr(self, "_ev_seq", 0) + 1
        self._heapq.heappush(self._events, (float(t), self._ev_seq, ev))

    def _interrupt_player_cast(self, logs: list):
        """v154 打断：玩家读条被控制打断 → 行动白费、资源不返还、伤害不结算。
        清空 _pending_player_cast，并从事件队列移除未触发的 cast_done 事件。"""
        self._player_casting = False
        self._pending_player_cast = None
        # 移除队列中尚未触发的玩家 cast_done 事件
        _kept = []
        for _t, _s, _e in self._events:
            if _e.get("type") == "cast_done" and _e.get("side") == "p":
                continue
            _kept.append((_t, _s, _e))
        self._events = _kept
        logs.append("💥 你的出招被打断了！读条中断，行动白费！")

    def _schedule_cast_done(self, t: float, payload: dict):
        """v154 读条命中制：排一个 cast_done 事件（出招读条结束 = 命中时刻）。
        payload: {"side": "p"|"e", "kind": "skill"|"atk"|"item"|..., "skill": skill_name,
                  "target": target_key, ...}
        事件触发时 _process_until 的 cast_done 分支执行实际结算（用命中时刻的实时状态）。
        """
        ev = {"type": "cast_done", **payload}
        self._schedule(t, ev)

    def _process_until(self, until_t: float, logs: list, player: dict, defend: bool = False,
                       skip_enemy: bool = False):
        """处理所有 t <= until_t 的事件。这是 v152 事件队列核心调度。
        skip_enemy: True 时跳过 enemy_act 事件（副本/PVP 外部驱动敌方，v157 防双重行动）"""
        if until_t <= self._now:
            return
        _guard = 0
        from .core.formation import alive_units
        while self._events and _guard < 64:
            t, _seq, ev = self._events[0]
            # v154 边界：处理 t <= until_t（含等于）——收招=0 时 cast_done 恰好 == p_ct，
            # 若用严格 < 会跳过导致命中永远不结算（task-2 发现的引擎缺口）。
            # 防死循环：_after_actor_ct 对敌方重排已加 max(now+cast_mult, now+0.001) 保证严格 > now；
            # 玩家侧 p_ct = now + cast_mult（cast_mult > 0 恒成立），同刻不会无限触发。
            if float(t) > float(until_t) + 1e-9:
                break
            self._heapq.heappop(self._events)
            self._now = max(self._now, float(t))
            _guard += 1
            evt = ev.get("type", "")
            try:
                if evt == "enemy_act":
                    # v157：skip_enemy=True（副本/PVP 外部驱动敌方）→ 跳过敌方行动，
                    # 只处理玩家事件（cast_done/pet_tick），防副本双重敌方行动
                    if skip_enemy:
                        continue
                    unit = ev.get("unit")
                    if not unit or unit.get("hp", 0) <= 0:
                        continue
                    if self._player_dead(player):
                        self.result = "defeat"
                        break
                    mlogs, dmg = self._enemy_turn(player, unit)
                    logs += mlogs
                    # v158 副本合并：敌方行动后通知副本命令层（同步血量/仇恨/贡献/倒地）
                    # 野外不传 cb（None）→ 零影响
                    if self._inst_cb is not None:
                        try:
                            self._inst_cb("enemy_acted", {"unit": unit, "logs": mlogs,
                                                          "dmg": dmg, "battle": self})
                        except Exception:
                            pass
                    # v154 敌方对称读条：_enemy_turn 已排 cast_done（出招读条结束才命中结算），
                    # dmg 恒 0（读条期间不直接打玩家）；敌方下次行动时刻已由 _enemy_turn 内部
                    # _after_actor_ct("e") 设为 命中时刻+收招。此处按新 ct 重排 enemy_act 事件。
                    if unit.get("hp", 0) > 0:
                        self._schedule(float(unit.get("ct", 0) or 0), {"type": "enemy_act", "unit": unit})
                    if self._player_dead(player):
                        self.result = "defeat"
                        break
                # v154：DOT/宠物/Boss 定时/词条回血不排独立事件（由玩家行动 _turn_start / 敌方行动 _boss_mech 触发）
                elif evt == "pet_tick":
                    # v154 宠物独立速度读条：pet_tick = 宠物出手（技能立即决定 + 结算，
                    # 出招跑完 = 生效；宠物技能无命中目标概念——攻击类打主目标、辅助类给玩家）。
                    # 简化：宠物技能在出手时刻直接结算（读条只做节奏展示，不引入宠物命中/打断）。
                    if self.pet and not self._enemy_dead():
                        logs += self._pet_skill_turn(player, logs)
                        if self.result == "victory":
                            break
                    # 重排下次 pet_tick（周期 = 出招 + 收招，按宠物 spd 折算）
                    self._reschedule_pet_tick()
                elif evt == "cast_done":
                    # v154 读条命中制：出招读条结束 = 命中时刻 → 结算（用命中时刻实时状态）
                    side = ev.get("side", "p")
                    if side == "p":
                        self._player_casting = False
                        pc = self._pending_player_cast or {}
                        self._pending_player_cast = None
                        # 目标已死 → 中断（命中落空）
                        if not self._enemy_dead():
                            _kind = pc.get("kind", ev.get("kind", ""))
                            if _kind == "atk":
                                logs += self._player_attack(pc.get("st") or self._player_stats(player), player)
                            elif _kind == "skill":
                                _sn = pc.get("skill_name") or ev.get("skill")
                                _inf = pc.get("info") or {}
                                if _sn and _inf:
                                    logs += self._player_skill(pc.get("st") or self._player_stats(player),
                                                               _sn, _inf, player, target=pc.get("target") or ev.get("target"))
                            elif _kind == "item":
                                # 道具无读条命中（即时生效，v152 行为保留）——这里只是兜底
                                pass
                        else:
                            logs.append("（你的攻击落空了——目标已倒下！）")
                        # 命中后玩家收招已完成（p_ct 已在出手时设为命中时刻+收招），无需再排
                    elif side == "e":
                        # v154 敌方对称读条：敌方出招读条结束 → 命中结算
                        e_unit = ev.get("unit") or {}
                        if e_unit.get("hp", 0) > 0:
                            mlogs, dmg = self._enemy_cast_done(player, e_unit, ev)
                            logs += mlogs
                            if defend and dmg > 0:
                                dmg = max(1, int(dmg * DEFEND_REDUCE))
                                self._pending_dmg_lines.append(f"(格挡后 {dmg} 点伤害)")
                            self._damage_player(player, dmg, logs, source=e_unit.get("name", "敌人"))
                            # v154 打断：玩家读条中受到控制（眩晕/冻结/沉默）→ 打断读条
                            if self._player_casting and dmg > 0:
                                _ctrl = any(k in self.p_buffs for k in ("stun", "freeze", "silence"))
                                if _ctrl:
                                    self._interrupt_player_cast(logs)
                    # v155 修复（2026-09-01 玩家实战抓包）：v154 读条命中制下玩家 cast_done 结算
                    # 杀怪后只走了 _remove_unit 清空 enemies，没有设 result=victory——
                    # 命令层在胜利结算前保存战斗状态（enemies=[] 但 result=None），下次行动
                    # from_state 恢复残缺敌人（_origin_enemy 缺 exp/gold/name）→ _handle_victory
                    # KeyError: 'exp' / _battle_footer KeyError: 'name'。这里补 victory 判定。
                    if self._enemy_dead():
                        self.result = "victory"
                        break
                    if self._player_dead(player):
                        self.result = "defeat"
                        break
            except Exception as _ex:
                # 单个事件异常不阻塞队列（防御性，避免一个坏事件死循环）
                logs.append(f"(事件处理异常: {_ex})")

    def _reschedule_dot(self, player: dict, ev: dict):
        """DOT 跳动后重新排下一次（若有未到期 DOT）。"""
        has_dot = False
        for u in self.enemies:
            db = u.get("debuffs") or {}
            if any(int(d.get("left", 0) or 0) > 0 for d in db.values()):
                has_dot = True
                break
        if has_dot:
            self._schedule(self._now + (ACT_TICK or 2.0), {"type": "dot_tick"})

    def _reschedule_mech(self, ev: dict):
        """Boss 定时机制重新排。interval 从事件 payload 读。"""
        interval = float(ev.get("interval", 3) or 3)
        self._schedule(self._now + interval * (ACT_TICK or 2.0),
                       {"type": "mech_tick", "unit": ev.get("unit"), "interval": interval})

    def _reschedule_pet(self, ev: dict):
        """宠物技能重新排（v152 不再使用——由 player_turn 直接触发）。"""
        pass

    def _add_shield(self, key: str, value: int, turns: int = 3):
        """v101.28d 护盾 buff 化：同源叠加盾值 + 刷新时长（取 max），异源并存各计各的时长。
        v106.2 护盾强度：shield_power 属性 ×(1+shield_power)（cap 50%）
        v152 时刻制：turns（刻数）→ expire_at = now + turns × ACT_TICK。"""
        if value <= 0:
            return
        try:
            _spv = min(float(self._player_stats(self.player).get("shield_power", 0) or 0), 0.5)
            if _spv > 0:
                value = int(value * (1 + _spv))
        except Exception:
            pass
        _exp = self._now + max(1, int(turns or 1)) * (ACT_TICK or 2.0)
        cur = self.p_shields.get(key)
        if cur:
            cur["value"] += value
            # 兼容旧存档 {"value","turns"} → 转 expire_at
            if "turns" in cur and "expire_at" not in cur:
                cur["expire_at"] = self._now + max(1, int(cur.get("turns", 1))) * (ACT_TICK or 2.0)
                cur.pop("turns", None)
            cur["expire_at"] = max(float(cur.get("expire_at", _exp)), _exp)
        else:
            self.p_shields[key] = {"value": value, "expire_at": _exp}

    def _do_use_item(self, payload: str, player: dict) -> list:
        """战斗中使用消耗品：恢复/增益(v61 抽公共，普通刻与额外行动共用)"""
        logs = []
        # v152 数据驱动动作时长：先剥离 payload 尾部 cast/recovery 参数（由 _item_payload_cast
        # 在 player_turn 消费，此处只解析效果本体；不剥离会破坏 int()/split(",") 等解析）
        payload = re.sub(r"(?:^|[;&,])\s*(?:cast|recovery):[\d.]+", "", payload).rstrip(";,")
        if payload.startswith("foodfx:"):
            # v101.28e 食物效果：foodfx:效果ID,效果ID（本场战斗有效，独立于装备词条）
            aids = [a for a in payload[7:].split(",") if a]
            for a in aids:
                if a not in self.p_food_effects:
                    self.p_food_effects.append(a)
            # 护盾效果特判：立即获得 10% 生命护盾（3 刻）
            if "shield" in aids:
                self._add_shield("food_shield", int(player.get("max_hp", 100) * 0.10), 3)
            from .core.food_effects import FOOD_EFFECT_NAMES
            names = [FOOD_EFFECT_NAMES.get(a, a) for a in aids]
            logs.append(f"🍲 你吃下了料理，获得【{'、'.join(names)}】效果！(本场战斗)")
            return logs
        if payload.startswith("hot:"):
            # v101.28 食物持续恢复：hot:回血比例,回蓝比例,刻数（模板 tpl_food 生成）
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
                _desc.append(f"每刻恢复 {int(hpct * 100)}% 生命")
            if mpct > 0:
                _desc.append(f"每刻恢复 {int(mpct * 100)}% 魔力")
            logs.append(f"🍲 你吃下了食物，{('、'.join(_desc))}！({turns} 刻)")
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
            # v54 战斗药水：effect → p_buffs 增益 3 刻
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
            # v151 时刻制（鱼鱼拍板）：防御/受击类 buff 改"受击计数"——铁壁/岩壁/影步/荆棘等
            # 防的是敌方出手，按敌方出手次数计时（3 次受击）而非玩家刻，不受速度差影响。
            # 注：food_def_up 保持持续时长制（食物是持续小加成，非爆发防御，语义不同）
            _def_keys = {"def_up", "def_up_big", "def_up_small",
                         "mdef_up", "dodge_pot", "block_pot", "thorns_pot", "magic_resist"}
            for _k in kind.split(","):
                if _k in _def_keys:
                    self._p_buff_hits[_k] = 3
            _names = '、'.join(_cn.get(k, k) for k in kind.split(','))
            # v101.28b 食物 buff（food_ 前缀键）播报区分：料理 vs 药水
            if any(k.startswith("food_") for k in kind.split(",")):
                logs.append(f"🍖 你吃下了料理，{_names}提升！(3 刻)")
            else:
                logs.append(f"🧪 你饮下战斗药水，{_names}大幅提升！(3 刻)")
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
        """v101.28f 药水特殊效果分发（非属性 buff 类，3 刻制；next_atk_up 一次性）。

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
        """v101.28 食物持续恢复：每刻开始结算（回血/回蓝，刻数递减）。"""
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
            logs.append(f"（剩余 {h['turns']} 刻）")
        return logs

    def _skill_cast_blocked(self, skill_name: str, player: dict) -> tuple:
        """O118 技能施放前置校验（无副作用，不扣资源/蓝）：技能不存在/未学习/冷却中/
        蓝不足/核心资源不足 → 返回 (日志列表, True)。
        拦截时玩家刻不开始、敌方不行动，玩家可重新选择其他行动。
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
            logs.append(f"⏳【{skill_name}】还在冷却中(剩余 {left} 刻)！")
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
            from .core.battle_bars import charge_def as _charge_def
            _is_charge_skill = bool(_charge_def(info))  # v139 电荷制：蓄力阶段只耗 charge_cost，不校验完整 res_cost
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
                # v139 电荷制：蓄力阶段只校验 charge_cost（默认 10），不校验完整 res_cost（满阶释放才扣）
                if _is_charge_skill:
                    _charge_cost = int(_charge_def(info).get("charge_cost", 10) or 10)
                    if rk == "energy":
                        _charge_cost = self._energy_cost_reduce(player, info, _charge_cost)
                    if self._res_read(k) < _charge_cost:
                        rname = (E.core_resource_def_by_key(k) or rd or {}).get("name", k)
                        cur = self._res_read(k)
                        logs.append(f"⚡ {rname}不足！需要 {_charge_cost}，当前 {cur}(『攻击』攒资源)")
                        return logs, True
                    continue
                if self._res_read(k) < _rv:
                    rname = (E.core_resource_def_by_key(k) or rd or {}).get("name", k)
                    cur = self._res_read(k)
                    logs.append(f"⚡ {rname}不足！需要 {_rv}，当前 {cur}(『攻击』攒资源)")
                    return logs, True
        return logs, False

    def _do_player_skill(self, skill_name: str, player: dict, target=None) -> list:
        """玩家施放技能(v61 抽公共，普通刻与额外行动共用)"""
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
            logs.append(f"⏳【{skill_name}】还在冷却中(剩余 {left} 刻)！")
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
            # v130.2f 致命预谋：本场首次 消耗连击点的终结技 结算后 返还 1 连击点（保底节奏）
            if ck == "cp":
                self._assassin_finisher_refund(player, logs)
        else:
            from .core.battle_bars import charge_def as _charge_def2
            _is_charge_skill2 = bool(_charge_def2(info))  # v139 电荷制：蓄力阶段不扣完整 res_cost（电荷分支只扣 charge_cost）
            res_cost = info.get("res_cost") or {}
            if res_cost and not _releasing and not _is_charge_skill2:  # 蓄力释放跳过资源扣减（施放时已扣）；电荷制跳过（满阶释放由电荷分支补扣）
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
            # v130.2f 致命预谋：本场首次 消耗连击点的终结技 结算后 返还 1 连击点（保底节奏）
            if "cp" in res_cost:
                self._assassin_finisher_refund(player, logs)
        # v122 治疗指定队友：指定的队友不存在 → 拦截（不扣资源、不消耗刻）；
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
        # ---- v139 电荷制（云海弓手三律翻译）：技能有 charge_cfg → 走电荷制，不走旧蓄力 ----
        # 「蓄力」动作：电荷 +1 并立即出伤 0.7/1.3/1.9（边攒边打）；受击 -1 阶不清零；满阶强制释放（release_power）
        from .core.battle_bars import charge_def, charge_state, charge_tick, charge_release_power, charge_clear
        _charge_cfg = charge_def(info)
        if _charge_cfg and not getattr(self, "_releasing_charge", False):
            # v139 电荷制蓄力：每次蓄力动作耗 charge_cost（默认 10 精力），不耗完整 res_cost（满阶释放才耗）
            _charge_cost = int(_charge_cfg.get("charge_cost", 10) or 10)
            _res_key = next(iter(info.get("res_cost", {})), None) if info.get("res_cost") else None
            if _res_key:
                _cur = self._res_read(_res_key)
                if _cur < _charge_cost:
                    _res_cn = C.CORE_RESOURCES.get(_res_key, {}).get("name", _res_key)
                    logs.append(f"⚡ 精力不足！需要 {_charge_cost}，当前 {_cur}(『攻击』攒资源)")
                    logs.append("技能施放失败！可选择其他行动")
                    return logs
                self._res_spend(_res_key, _charge_cost)
            _ch = charge_tick(player, info, logs)  # +1 阶 + 边攒边打倍率
            if _ch["released"]:
                # 满阶强制释放：本刻打 release_power 满伤害，随后清空电荷；耗完整 res_cost
                _rel = charge_release_power(info)
                _orig_power = info.get("power", 1.0)
                info["power"] = float(_rel.get("power", 2.8) or 1.0)
                _extra = _rel.get("extra") or {}
                # v139 满阶释放：破防/指定后排等 extra 生效（临时标记，_player_skill 内消费）
                _prev_extra = info.get("_charge_release_extra")
                if _extra:
                    info["_charge_release_extra"] = _extra
                # v139 满阶释放扣完整 res_cost（能量 50；蓄力阶段只扣了 charge_cost）
                for _rk, _rv in (info.get("res_cost") or {}).items():
                    self._res_spend(_rk, int(_rv or 0))
                logs += self._player_skill(st, skill_name, info, player, target=target)
                info["power"] = _orig_power
                if _extra:
                    if _prev_extra is None:
                        info.pop("_charge_release_extra", None)
                    else:
                        info["_charge_release_extra"] = _prev_extra
                charge_clear(player)
                # v139 电荷制：冷却只在满阶释放后进入（蓄力阶段每刻可蓄，不触发 cd）
                cd = info.get("cd", 0)
                if cd:
                    self._set_skill_cd(skill_name, cd)
            else:
                # 未满阶：本刻出伤 ×dmg_mult（边攒边打），不进入旧蓄力，不触发 cd
                _orig_power = info.get("power", 1.0)
                info["power"] = float(_ch.get("dmg_mult", 0.7) or 0.7)
                logs += self._player_skill(st, skill_name, info, player, target=target)
                info["power"] = _orig_power
            return logs
        # ---- v139 focus 开启技（元素架设/时间凝滞）：effect=element_focus/time_stasis → 进入架设态，本刻不出伤 ----
        _focus_effect = info.get("effect", "")
        if _focus_effect in ("element_focus", "time_stasis"):
            from .core.battle_modes import focus_def as _fdef139, focus_state as _fst139, focus_enter as _fent139, focus_exit as _fext139
            if _fdef139(player):
                if _fst139(player).get("active"):
                    _fext139(player, logs)
                    logs.append("🧘 主动解除专注施法状态（无损）。")
                else:
                    _fent139(player, logs)
                # 开启技进入冷却，不落主结算（power=0 无伤害）
                cd = info.get("cd", 0)
                if cd:
                    self._set_skill_cd(skill_name, cd)
                return logs
        # v2 蓄力技能（§6）：施放扣 MP/资源 → 进入蓄力，本刻不结算技能效果
        if not getattr(self, "_releasing_charge", False) and int(info.get("charge", 0) or 0) >= 1:
            cname = info.get("name") or skill_name
            self.charging = {"skill": skill_name, "left": int(info["charge"]),
                             "name": cname, "mp_spent": mp_cost}
            logs.append(f"✨ 你开始蓄力【{cname}】，需要 {int(info['charge'])} 刻！")
            # 冷却照常进入（§6.2 施放即冷却）
            cd = info.get("cd", 0)
            if cd:
                self._set_skill_cd(skill_name, cd)
            return logs
        # v154 读条命中制：普通技能出手 → 排 cast_done 事件（命中时刻才结算）。
        # 不排事件的特例：PVP（真人轮流）、蓄力释放（_releasing_charge 已含蓄力读条语义）。
        if self.btype != "pvp" and not getattr(self, "_releasing_charge", False):
            # 出招读条（cast 秒数，速度折算）在 player_turn 已排 cast_done；
            # 这里把"命中时刻要调用的结算函数 + 参数"暂存到 self._pending_player_cast，
            # 由 _process_until 的 cast_done 分支消费（用命中时刻状态重新计算）。
            self._pending_player_cast = {
                "skill_name": skill_name,
                "info": info,
                "st": st,
                "target": target,
                "mp_cost": mp_cost,
                "mana_lvl": mana_lvl,
            }
            # 出手瞬间已扣 MP/资源/进 CD（读条 = 已投入）；结算在命中时刻由 cast_done 执行
            return logs
        # 非读条路径（PVP / 蓄力释放）：立即结算
        logs += self._player_skill(st, skill_name, info, player, target=target)  # v122：target 传治疗队友目标
        # v130.2f 歌者伴奏改版（灵魂歌者分支被动）：歌类技施放 20% 概率 回声 +1
        # （原「暴击+8%」面板加成的扣除在 _player_stats；数据层并行批次将移除其 stat crit 字段，
        #   届时扣除条件自动失效。歌类技统一标记 = _is_bard_skill（BARD_BRANCHES 分支归属），
        #   不硬造 tag；回声上限 3 由 _echo_add 天然处理）
        if E.is_passive_learned(player.get("class_name", ""), "伴奏", player.get("learned_skills", [])) \
                and self._is_bard_skill(player, info) and random.random() < 0.20:
            self._res_gain(player, "echo", 1, logs)
        # v130.2c 圣典·日冕 2 件：施放二档以上神迹 → 全体队友额外恢复 30 体力
        self._set_miracle_team_heal(player, info, logs)
        # v2.0 冷却：技能表 cd 字段（刻），施放后进入冷却
        cd = info.get("cd", 0)
        if cd:
            self._set_skill_cd(skill_name, cd)
        return logs

    # ---------------- 防御 / 逃跑 ----------------
    def _item_payload_cast(self, payload: str) -> float:
        """v152 道具动作时长：payload 内嵌 cast:N 则用 N（自定义字段），否则默认。
        默认：食物（foodfx/hot）CAST_FOOD=1.0，普通道具 CAST_ITEM=1.0。
        未来扩展：道具模板生成 payload 时带 cast:1.2 即可自定义（recovery 同理 recovery:0.5）。
        """
        _m = re.search(r"(?:^|[;&,])\s*cast:([\d.]+)", payload or "")
        if _m:
            return float(_m.group(1))
        _m = re.search(r"(?:^|[;&,])\s*recovery:([\d.]+)", payload or "")
        _rec = float(_m.group(1)) if _m else 0.0
        if (payload or "").startswith(("foodfx:", "hot:")):
            return CAST_FOOD + _rec
        return CAST_ITEM + _rec

    def _do_defend(self, player: dict, logs: list, enemy_act: bool = True, cast_mult: float = 1.0) -> tuple:
        logs.append("🛡️ 你架起防御姿态，受到的伤害减半！")
        self.p_defending = True
        # v152：防御也是玩家行为，有行为时长（快动作 cast_mult=CAST_DEFEND）。
        # 防御期间敌方可行动（_process_until 处理到玩家 next_act_at），伤害减半由 defend=True 生效。
        if enemy_act and self.btype != "pvp":
            self._after_actor_ct("p", player=player, cast_mult=cast_mult)
            return self._enemy_phase(player, logs, enemy_act, defend=True)
        self._end_round()
        return logs, self.result is not None

    def _do_flee(self, player: dict, logs: list, cast_mult: float = 1.0) -> tuple:
        if self.btype in ("worldboss", "pvp"):
            logs.append("💨 这里无法逃跑！背水一战吧！")
            if self.btype == "pvp":
                # PVP：不触发 AI 反击，等对方真人行动
                return logs, False
            # v152：逃跑失败也被敌方追击 → 玩家 ct 照走（慢动作 cast_mult=CAST_FLEE），敌方段按事件队列判定
            self._after_actor_ct("p", player=player, cast_mult=cast_mult)
            return self._enemy_phase(player, logs, True)
        # v130.7 意见#28：逃跑成功率 = 基础 FLEE_CHANCE ± 等级差×FLEE_LEVEL_STEP
        # ± 速度差×FLEE_SPD_STEP，clamp 到 [FLEE_MIN, FLEE_MAX]——高打低/快打慢更好跑，
        # 越级进高级区更难脱身（玩家等级/速度取战斗实时值）
        p_lv = int(player.get("level", 1) or 1)
        p_spd = int(self._player_stats(player).get("spd", 0) or 0)
        e = self.enemy or {}
        e_lv = int(e.get("lv", 0) or 0)
        e_spd = int(self._enemy_stats().get("spd", 0) or 0)
        # 敌方数据缺失（lv/spd 为 0）时对应差值项退化为 0，仅按可得项修正（防误判逃跑率）
        lv_diff = (p_lv - e_lv) if e_lv > 0 else 0
        spd_diff = (p_spd - e_spd) if e_spd > 0 else 0
        flee_rate = FLEE_CHANCE + lv_diff * FLEE_LEVEL_STEP + spd_diff * FLEE_SPD_STEP
        flee_rate = max(FLEE_MIN, min(FLEE_MAX, flee_rate))
        if random.random() < flee_rate:
            logs.append("💨 你成功脱离了战斗！")
            self.result = "fled"
            return logs, True
        # v130.7 意见#28：逃跑失败给出原因（敌方更高/更快时明示，保持既有提示风格）
        flee_reason = ""
        if lv_diff < 0:
            flee_reason = f"敌方比你高 {-lv_diff} 级，几乎逃不脱；"
        elif spd_diff < 0:
            flee_reason = f"敌方比你快 {-spd_diff} 点，几乎逃不脱；"
        logs.append(f"💨 逃跑失败！被追上了！({flee_reason}可以再『逃跑』，或『防御』『用药』撑住)")
        # v152：逃跑也是玩家行为，有行为时长（慢动作 cast_mult=CAST_FLEE），PVP 不介入
        if self.btype != "pvp":
            self._after_actor_ct("p", player=player, cast_mult=cast_mult)
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
        # v130.2f 歌者伴奏改版（灵魂歌者分支被动）：原「暴击+8%」属性被动 → 「歌类技施放 20% 概率回声+1」。
        # 数据层并行批次将移除 伴奏 的 stat crit 定义；此处仅在数据仍声明 stat crit 时扣除其面板
        # 贡献（移除后条件自动失效，零残留）。回声触发挂点在 _do_player_skill 施放结算处。
        _bz = E.skill_info(player.get("class_name", "战士"), "伴奏") or {}
        _bz_ps = _bz.get("passive") or {}
        if _bz_ps.get("stat") == "crit" and E.is_passive_learned(
                player.get("class_name", "战士"), "伴奏", player.get("learned_skills", [])):
            pb["crit_add"] = max(0.0, float(pb.get("crit_add", 0.0) or 0.0)
                                 - float(_bz_ps.get("add", 0.08) or 0.0))
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
        # v140 波3.1：特效装备常驻面板属性（奥术苍穹魔攻+15%/疾风步速度+/弑星·无尽辉光暴伤+）
        try:
            from .core.weapon_effects import weapon_effect_ids as _we_ids
            _weids = set(_we_ids(self, player))
            if "arcane_firmament" in _weids:
                st["matk"] = int(st.get("matk", 0) * 1.15)
            _gale_pct = float((self.p_eff or {}).get("gale_step_pct", 0) or 0)
            if _gale_pct > 0 and self.p_buffs.get("gale_step"):
                st["spd"] = int(st.get("spd", 0) * (1 + _gale_pct))
            if "star_slayer_edge" in _weids:
                st["crit_dmg"] = float(st.get("crit_dmg", 0) or 0) + 0.30
            if "endless_radiance" in _weids:
                st["crit_dmg"] = float(st.get("crit_dmg", 0) or 0) + 0.25
            # 风痕（风行短弓）：每层速度 +2%
            _wm = int((self.mech_stacks or {}).get("wind_mark", 0) or 0)
            if _wm > 0:
                st["spd"] = int(st.get("spd", 0) * (1 + 0.02 * _wm))
            # v140 波4：新手特效 翠风（novice_wind_spd）——命中后自身速度 +5%（2 刻）
            if self.p_buffs.get("novice_wind_spd"):
                st["spd"] = int(st.get("spd", 0) * 1.05)
            # 雷纹连打（雷纹拳甲）：每层速度 +2%、攻击 +1%
            _tw = int((self.mech_stacks or {}).get("thunder_weave", 0) or 0)
            if _tw > 0:
                st["spd"] = int(st.get("spd", 0) * (1 + 0.02 * _tw))
                st["atk"] = int(st.get("atk", 0) * (1 + 0.01 * _tw))
        except Exception:
            pass
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
        # v130.2f2（T11 P2）：潜行出手标记每次出手前复位——普攻不消费潜行（v104 遗留口径），
        # 置 False 防上次技能潜行出手的标记串场到本次普攻暴击结算（_on_crit_resource 读标记）。
        self._stealth_atk = False
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
        # v133 收敛：追加倍率 1.5→1.3（LUCKY_CRIT_MULT 数据表）
        lucky = is_crit and random.random() < LUCKY_CRIT_CHANCE
        # v106 穿透：玩家物穿/固定物穿削减怪物有效防御
        _pp, _pf = self._pene_vals(st)
        # v107 伤害类型四层架构：普攻显式声明 phys（物理段，吃 def/物免/格挡/物吸）
        dmg = E.calc_damage(st["atk"], est["def"], is_crit, pene_pct=_pp, pene_flat=_pf, dmg_type="phys")
        if lucky:
            dmg = int(dmg * LUCKY_CRIT_MULT)
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
        # v156 玩家侧公共乘区统一组装（词条/狼嚎/蓄势/禅意/物理药水/种族）——
        # 与技能共用 _player_dmg_mult（一处修改，普攻/技能同时生效）
        affix_mult, affix_tags = self._player_dmg_mult(player, "物理")
        dmg = int(dmg * affix_mult)
        # v140 S1 直连消费：蓄势待发（surge_ready）——战斗开始后第一次攻击 +15%（一次性）
        if (self.p_eff or {}).get("surge_ready"):
            dmg = int(dmg * 1.15)
            self.p_eff.pop("surge_ready", None)
            affix_tags = list(affix_tags) + ["💪蓄势x1.15"]
        # v140 S1 直连消费：血誓回响（blood_oath_echo atk_up）——本次攻击 +10%（一次性）
        if (self.p_eff or {}).get("atk_up"):
            dmg = int(dmg * 1.10)
            self.p_eff.pop("atk_up", None)
            affix_tags = list(affix_tags) + ["🩸血誓x1.1"]
        # v140 波3.1：特效装备被动增伤（暮光处决/弑星/岁月流转/三相/破岳/咒誓/反击/暮裂/雷纹等）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wectx = {"mult": 1.0, "tags": [], "attack": True, "is_crit": is_crit,
                      "crit_dmg": float(st.get("crit_dmg", 0) or 0)}
            _we_proc(self, player, "passive", _wectx, logs)
            # v140 波3.2：弱点击破石——目标负面越多增伤越高（vuln 标记）
            _vuln = (self.p_eff or {}).get("vuln")
            if _vuln and int(_vuln.get("turns_left", 0) or 0) > 0:
                _vb = float(_vuln.get("bonus", 0) or 0)
                if _vb > 0:
                    _wectx["mult"] = _wectx.get("mult", 1.0) * (1 + _vb)
                    _wectx["tags"] = _wectx.get("tags", []) + [f"🎯弱点x{1 + _vb:.2f}"]
            if _wectx.get("mult", 1.0) != 1.0:
                dmg = int(dmg * _wectx["mult"])
                affix_tags = list(affix_tags) + _wectx.get("tags", [])
            if _wectx.get("crit_dmg", 0) > 0 and is_crit:
                cdmg = float(st.get("crit_dmg", 0) or 0)
                dmg = int(dmg * (1 + _wectx["crit_dmg"] / max(1e-9, (1 + cdmg))))
                affix_tags = list(affix_tags) + [f"🌙暴伤x{1 + _wectx['crit_dmg']:.2f}"]
        except Exception:
            pass
        # v140 波4：新手特效 星火连击（novice_spark_followup）——释放技能后，下次普攻伤害 +10%
        if self.mech_stacks.get("novice_spark"):
            dmg = int(dmg * 1.10)
            del self.mech_stacks["novice_spark"]
            affix_tags = list(affix_tags) + ["✨星火x1.1"]
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
        # v140 S1 直连消费：鹰眼锐视（eagle_vision）——本次暴击伤害 +30%（一次性消费）
        if is_crit and (self.p_eff or {}).get("eagle_vision"):
            dmg = int(dmg * 1.30)
            self.p_eff.pop("eagle_vision", None)
            affix_tags = list(affix_tags) + ["🦅鹰眼锐视"]
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
            self._set_attack_proc(player, dmg, logs, is_crit=is_crit)
            # v140 波3.1：特效装备攻击命中（风痕/破绽/裂伤/霜环/败血/裂风矢/圣裁/雷纹/幻影/海妖/破败/穿星等）
            try:
                from .core.weapon_effects import proc as _we_proc
                _we_proc(self, player, "hit", {"dmg": dmg, "is_crit": is_crit}, logs)
            except Exception:
                pass
            # v140 波3.2：连携增幅墨——命中使目标毒/灼烧/流血层数 +1（dot_amp 标记）
            _dam = (self.p_eff or {}).get("dot_amp")
            if _dam and int(_dam.get("turns_left", 0) or 0) > 0:
                _per = max(1, int(_dam.get("layer_per_hit", 1) or 1))
                _deb = self.enemy.setdefault("debuffs", {})
                for _dk in ("poison", "burn", "bleed"):
                    if _deb.get(_dk, {}).get("n", 0):
                        _d = _deb.setdefault(_dk, {"n": 0, "mult": 1.0})
                        _d["n"] = int(_d.get("n", 0) or 0) + _per
                logs.append(f"🎨 连携增幅墨：异常层数 +{_per}！")
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
        # v151 隐藏职业删除：星语猎印 on_hit 追加逻辑已移除
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
            # v153 §4（C-18）：力竭中信念不增加（过载后 6 刻）
            if not self.p_buffs.get("faith_exhausted"):
                gain += int(rd["on_heal"])
        # v151 隐藏职业删除：星语猎印技能命中追加逻辑已移除（on_skill_extra 恒 0）
        on_skill_extra = 0
        # v130.2f2（T7 P1-2/P1-3）：被动加成并入技能命中渠道——战争咆哮 res_gain_bonus
        # 「怒气全渠道+1」/ 魔力贯穿 attack_res「施法命中+1沙」在施法命中时也生效。
        # 叠加语义：与技能自带 res_gain 累加（同一获取源不重复）；终结技早返回（2311 附近）在前，
        # 有 res_cost 且无 res_gain 的终结技依旧不获取，渠道扩展不破坏该语义。
        _pm_skill = self._passive_map(player)
        _skill_gain_log = []
        for _pn, _ps in _pm_skill["proc"].get("res_gain_bonus", []):
            if k in ("rage", "chi", "cp", "faith"):
                gain += 1
                _skill_gain_log.append(f"{_pn}+1")
        for _pn, _ps in _pm_skill["proc"].get("attack_res", []):
            if k == _ps.get("res", "") and _ps.get("gain"):
                gain += int(_ps.get("gain", 0))
                _skill_gain_log.append(f"{_pn}+{int(_ps.get('gain', 0))}")
        if _skill_gain_log and logs is not None:
            _rd_n = (E.core_resource_def_by_key(k) or E.core_resource_def(cls) or {}).get("name", k)
            logs.append(f"⚡ 技能命中：{' / '.join(_skill_gain_log)}（{_rd_n}）")
        if gain or on_skill_extra:
            if k == "element":
                self._res_gain(player, "element", gain + on_skill_extra, logs)
            else:
                self.resources[k] = self._res_gain_class(cls, k, gain + on_skill_extra)
        # v139 双形态进入检查：技能结算后资源已更新，若满足入形态条件（狂战士满 10 怒 / 龙裔龙力≥8）自动进入
        # （auto 技能显式声明 或 资源达 enter_requirement 均可触发；免费切换不占行动）
        try:
            from .core.battle_modes import dual_form_def as _dfd139, dual_form_state as _dfs139, dual_form_can_enter as _dfce139, dual_form_enter as _dfe139
            _df_cfg = _dfd139(player)
            if _df_cfg:
                _df_key = _df_cfg.get("key", k)
                _df_val = int(self.resources.get(_df_key, 0) or 0)
                _df_auto = (info or {}).get("auto", "")
                _df_want = _df_auto in ("rage_form_enter", "dragon_form_enter") or _dfce139(player, _df_val)
                if _df_want and not _dfs139(player).get("form") == "alt":
                    if _dfe139(player, logs):
                        logs.append(f"⚡【{_df_cfg.get('form', '形态')}】觉醒！(资源 {_df_val})")
        except Exception:
            pass

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
            # v130.2f2（T11 P2）：潜行已于出手处置 True 标记（消费点 3030-3034 先删 buff）——
            # 此处读标记而非二次查 buff，「潜行出手额外 +1 影步」不再空转
            if self.p_buffs.get("stealth") or getattr(self, "_stealth_atk", False):
                gain += int(SHADOW_STEP_CFG.get("stealth_extra", 1) or 0)
            self.resources[k] = E.core_resource_gain(cls, self.resources, gain)
            proc_ok = True
        # 刺客攻线·影舞者：on_crit 额外 +1 连击点（叠于 on_attack/on_skill）
        elif cls == "cls_ci_ke" and self._is_path(player, 1):
            self.resources[k] = E.core_resource_gain(cls, self.resources, ASSASSIN_ON_CRIT_GAIN)
            proc_ok = True
        # v151 隐藏职业删除：星语猎印暴击额外（crit_mark）已移除
        return proc_ok

    def _assassin_finisher_refund(self, player: dict, logs: list):
        """v130.2f 致命预谋返还挂点：每场首次 消耗连击点的终结技 结算后，返还 1 连击点
        （保底节奏；_assassin_refund_used 防重复，随战斗序列化）。
        被动判定走 battle_start_cp proc（致命预谋 数据层挂载），数据驱动不按名字硬匹配。
        调用点：_do_player_skill 的 res_cost cp / consume_all cp 两处扣费结算后。"""
        if getattr(self, "_assassin_refund_used", False):
            return
        if not self._passive_map(player)["proc"].get("battle_start_cp", []):
            return
        self._assassin_refund_used = True
        _cls = player.get("class_name", "")
        _before = int(self.resources.get("cp", 0) or 0)
        _now = self._res_gain_class(_cls, "cp", 1)
        if _now > _before:  # 真实增量判定（连击点已满时不误报返还）
            logs.append(f"🗡️ 致命预谋：首次终结返还 1 连击点（当前 {_now}）")

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
        # 冰霜：x% 概率冻结 1 刻
        freeze_lvl = self._enchant_lvl(effs, "freeze")
        if freeze_lvl and random.random() < C.rune_value("freeze", freeze_lvl):
            self.e_buffs["freeze"] = 1
            logs.append("❄️ 符文冰霜：敌人被冻结，跳过下刻！")
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
        # 虚弱：攻击使敌人攻击 -x%（3 刻）
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
        与 _affix_effs 同模式；装备 set 字段支持 set_xxx ID 与中文名（engine._set_info 双向解析）。
        v142：加入 bonus_3（区域 3 槽位套）——部分区域套特效注册在 bonus_3"""
        out = []
        for sname, cnt in E.active_sets(player.get("equipment") or {}).items():
            if cnt < min_tier:
                continue
            info = E._set_info(sname)
            if not info:
                continue
            for tier in (2, 3, 4, 5):
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

    def _undead_count(self) -> int:
        """场上存活亡灵单位计数：玩家召唤骷髅（skeleton tid/名含骷髅）或敌方名称含亡灵系关键词。
        关键词与成就 亡灵使者 kills_type 同源（亡灵/骷髅/僵尸/幽灵）。"""
        n = 0
        for s in self.summons:
            if s.get("hp", 0) > 0 and (s.get("tid") == "skeleton" or "骷髅" in str(s.get("name", ""))):
                n += 1
        for u in self.enemies:
            if u.get("hp", 0) > 0 and any(k in str(u.get("name", "")) for k in ("亡灵", "骷髅", "僵尸", "幽灵")):
                n += 1
        return n

    def _undead_on_field(self) -> bool:
        """场上是否存在亡灵单位（v130.2f 改读 _undead_count 统一口径）。"""
        return self._undead_count() > 0

    def _set_res_proc(self, player: dict, event: str, logs: list):
        """v130.2c 套装 res_gain 统一读取器：on_taken 受击 / on_heal 治疗 / undead_on_field 刻开始亡灵在场。
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
                    "dragon_aw", "dawn_light", "precise",
                    # v141.3 D2 passive 专属 + D3 passive 专属
                    "kingdom_lion_heart", "star_destruction", "dragon_annihilation",
                    "divine_execution", "giant_slayer", "mark_hunt", "executioner",
                    "top_hunter", "last_breath"):
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
            if _ok and _ae.get("enemy_role") and not self._affix_role_ok(e, _ae["enemy_role"]):
                _ok = False
            if _ok and _ae.get("enemy_marked") and not self._affix_marked(e):
                _ok = False
            # v140 S1 王狮之心：仅生命 >70% 时增伤生效（cond hp_gt_70 数据字段）
            if _ok and _ae.get("cond") == "hp_gt_70" and not (player.get("hp", 0) / max(1, player.get("max_hp", 1)) > 0.70):
                _ok = False
            if _ok:
                mult *= float(_dm)
                tags.append(_ae.get("tag", _ai.get("name", aid)))
        # v101.28e/f：食物+药水额外倍率（处决/精准/狂怒/死神），与词条是否为空无关
        mult, tags = self._extra_dmg_mult(hp_ratio, mult, tags)
        return mult, tags


    def _affix_role_ok(self, e: dict, role: str) -> bool:
        """v135 哑词条激活·破魔：原 enemy_role == "caster" 条件在全怪物库零命中
        （怪物 role 只用 tank/dps/healer/speedster/elite/boss）→ 放宽为：
        role 精确匹配 caster/healer，或该怪技能表含任意『魔法』系技能（魔法系敌人）。
        数据定义（affixes.py break_magic enemy_role）保留，消费条件放宽使其真实可触发。"""
        if role == "caster":
            if e.get("role") in ("caster", "healer"):
                return True
            sk = e.get("skills") or []
            if sk and any((C.MONSTER_SKILLS.get(s) or {}).get("kind") == "魔法" for s in sk):
                return True
            return False
        return e.get("role") == role

    def _affix_marked(self, e: dict) -> bool:
        """v135 哑词条激活·追猎：标记判定放宽——e_buffs["mark"]（技能标记）+ 目标级
        debuffs.mark（层数 >0，副本/多单位共享标记）任一存在即视为标记目标。
        原实现只认 e_buffs["mark"]（仅游侠标记技写入），战士/法师/牧师/刺客/拳师
        携带追猎词条时零触发 → 放宽后追猎成为普适的『集火增伤』特色词条。"""
        if "mark" in self.e_buffs:
            return True
        mk = (e.get("debuffs") or {}).get("mark") or {}
        return int(mk.get("n", 0) or 0) > 0

    def _player_dmg_mult(self, player: dict, kind: str = "物理") -> tuple:
        """v156 玩家侧公共乘区统一组装——普攻/技能共用（一处修改，两边生效）。

        收拢两边重复的组装逻辑：
          - 词条增伤（_affix_dmg_mult，含食物/药水尾链）
          - 狼嚎 wolf_howl_mult（本场 +10%）
          - 蓄势 momentum / 禅意 zen（物理持有加伤）
          - 澎湃烈酒 phys_up / 引气精华 buff_phys_next（物理 +pct%，一次性消费）
          - 种族天赋 race_mult
        返回 (mult, tags)。技能专属乘区（冻结/潜行/叠层/条件/反应）由调用方另乘。
        """
        mult, tags = self._affix_dmg_mult(player)
        # v140 S1 直连消费：狼嚎（wolf_howl）——本场伤害 +10%（战斗开始置位，命中即乘）
        if (self.p_eff or {}).get("wolf_howl_mult"):
            mult = mult * float(self.p_eff.get("wolf_howl_mult", 1.10))
            tags = list(tags) + ["🐺狼嚎x1.1"]
        # v130.2 拳师蓄势 Momentum（攻线·格斗士）：物理伤害吃「每 1 气 +3%」持有加伤
        _mom = self._momentum_mult(player)
        if kind == "物理" and _mom != 1.0:
            mult *= _mom
            tags = list(tags) + [f"🔥蓄势x{round(_mom, 2)}"]
        # v130.2f2 苦修禅意（武僧线）：物理伤害吃「每 1 禅意 +4%」持有加伤
        _zen = self._zen_hold_mult(player)
        if kind == "物理" and _zen != 1.0:
            mult *= _zen
            tags = list(tags) + [f"🧘禅意x{round(_zen, 2)}"]
        # v130.2 澎湃烈酒（phys_up）/ 引气精华（buff_phys_next）：物理伤害 +pct%
        if kind == "物理" and (self.p_buffs.get("phys_up") or self.p_buffs.get("buff_phys_next")):
            _pu = float((self.p_eff or {}).get("phys_up", 0) or 0)
            _bpn = float((self.p_eff or {}).get("buff_phys_next", 0) or 0)
            if _pu > 0:
                mult *= (1 + _pu)
            if _bpn > 0:
                mult *= (1 + _bpn)
                del self.p_buffs["buff_phys_next"]
                self.p_eff.pop("buff_phys_next", None)
            _tags_pu = ([f"🍺物理x{round(1 + _pu, 2)}"] if _pu > 0 else []) + \
                       ([f"🥊引气x{round(1 + _bpn, 2)}"] if _bpn > 0 else [])
            if _tags_pu:
                tags = list(tags) + _tags_pu
        # 阶段九：种族攻击天赋（无畏/怯战 残血、龙之吐息 首击）
        race_mult, race_tags = self._race_attack_mult(player)
        if race_tags:
            tags = list(tags) + race_tags
        return mult * race_mult, tags

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
        v98.5：效果数据化 → core/affix_effects.py HIT_EFFECTS（并列 if 语义，顺序遍历）
        v156：带 formula 字段的词条走通用执行器（零代码），旧词条仍走注册函数"""
        ids = self._equip_affix_ids(player)
        if not ids or self.enemy.get("hp", 0) <= 0:
            return
        from .core.affix_effects import HIT_EFFECTS, run_affix_formula
        # v156 formula 词条：数据驱动追加伤害（无需手写 handler）
        run_affix_formula(self, player, dmg, logs, trigger="on_hit")
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

    def _set_taken_proc(self, player: dict, dmg: int, logs: list) -> int:
        """v142 数据驱动：套装受击特效（taken_* 型）。
        遍历已激活套装的 bonus_X effect，读 params.type（taken_*）→ 调通用执行器。
        执行器若返回 int（如 taken_dmg_cut 削减伤害）则更新 dmg。"""
        from .core.affix_effects import TAKEN_TYPES, _execute_taken_proc
        for eff, _tier in self._set_effs(player, 2):
            p = (eff or {}).get("params") or {}
            if not p.get("type") or not p["type"].startswith("taken_"):
                continue
            if p["type"] not in TAKEN_TYPES:
                continue
            r = _execute_taken_proc(eff, self, player, dmg, logs)
            if isinstance(r, int):
                dmg = r
        return dmg

    def _affix_turn_start(self, player: dict, logs: list):
        """刻开始词条：回春(1% 生命)/冥想(1% 魔力)/晨曦祝福(2% 生命)
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
        """刻开始料理效果（回春/冥想/晨曦祝福）。"""
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
        # v153 §4（C-18）：牧师信念负载档位——治疗量 × 档位乘区（0-3 清醒×1.0 / 4-7 专注×1.25 / 8-9 透支×1.5）
        _crd_faith = E.core_resource_def(player.get("class_name", ""))
        if _crd_faith and _crd_faith.get("key") == "faith" and _crd_faith.get("load_tiers"):
            _faith_now = float(self.resources.get("faith", 0) or 0)
            _tier_heal = 1.0
            for _t in _crd_faith["load_tiers"]:
                if _faith_now <= float(_t.get("max", 0)):
                    _tier_heal = float(_t.get("heal_mult", 1.0))
                    break
            _faith_mult_applied = _tier_heal
        # v95r38：power<1 的治疗技能按 max_hp 百分比结算（如拳师气息调息 15% HP），
        # power>=1 保持原有"魔攻×power"模式（治愈术 200% 等），与消耗品 heal<1 百分比语义一致
        # v159 表达式：技能配 heal_formula 时走表达式（任意自定义），否则回退旧逻辑
        # v160 逐级：heal_formula 本身为字符串数组（每级一条）或 info 配 heal_exprs 时按级取；
        #   段级 exprs 走 skill_formula_expr_for_seg（独立于伤害 exprs，不串扰）
        _hf_raw = info.get("heal_formula") or info.get("heal_expr")
        _hf = _hf_raw
        if _hf_raw:
            _he = info.get("heal_exprs")
            if isinstance(_he, list) and _he:
                _lvx = max(1, min(int(lv or 1), len(_he)))
                _hf = _he[_lvx - 1]
            elif isinstance(_hf_raw, list) and _hf_raw and all(isinstance(_x, str) for _x in _hf_raw):
                # heal_formula 本身是字符串数组 = 逐级公式（第 N 级取第 N 条，越界取最后）
                _lvx = max(1, min(int(lv or 1), len(_hf_raw)))
                _hf = _hf_raw[_lvx - 1]
        if _hf:
            try:
                from .core.formula_expr import compile_expr, eval_expr, build_vars
                st2 = dict(st)
                st2["_player_lv"] = int(player.get("level", 1) or 1)
                st2["_skill_lv"] = lv
                st2["max_hp"] = player.get("max_hp", 0)
                _vars = build_vars(st2, player_lv=int(player.get("level", 1) or 1),
                                   skill_lv=lv, target_max_hp=player.get("max_hp", 0))
                if isinstance(_hf, str):
                    _hv = eval_expr(compile_expr(_hf), _vars)
                else:
                    # 段列表（同伤害 formula 格式）：求和
                    _hv = 0
                    for _hseg in _hf:
                        _hseg_expr = E.skill_formula_expr_for_seg(_hseg, lv)
                        if isinstance(_hseg, dict) and _hseg_expr:
                            _hv += eval_expr(compile_expr(_hseg_expr), _vars) * float(_hseg.get("mult", 1.0) or 1.0)
                        else:
                            _fstat = _hseg.get("stat", "matk")
                            _fmult = float(_hseg.get("mult", 1.0) or 1.0)
                            _fflat = int(_hseg.get("flat", 0) or 0)
                            if _fstat == "max_hp":
                                _hv += player.get("max_hp", 0) * _fmult + _fflat
                            elif _fstat == "flat":
                                _hv += _fflat
                            else:
                                _hv += st.get("matk", 0) * _fmult + _fflat
                heal = int(_hv * cond_mult)
            except Exception:
                heal = 0
        elif info.get("power", 0) < 1:
            heal = int(player.get("max_hp", 0) * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
        else:
            heal = int(st["matk"] * info["power"] * E.skill_power_mult(lv, info) * cond_mult)
        # v153 §4（C-18）：牧师信念负载档位乘区（清醒×1.0 / 专注×1.25 / 透支×1.5）
        if "_faith_mult_applied" in locals():
            heal = int(heal * _faith_mult_applied)
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
        # v140 S1 直连消费：圣愈不浪费（cloth_heal_overflow）——治疗 +8%，溢出转护盾
        if self._set_eff(player, "cloth_heal_overflow", 4):
            heal = int(heal * 1.08)
        # 阶段八：圣光套 2 件效果——治疗 +10%
        if E.has_set(player.get("equipment", {}), "圣光套"):
            heal = int(heal * 1.10)
        # v101.28f 圣光药剂：治疗技能效果 +20%（3 刻）
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
        # v151 刻制审计：禁疗/重伤消费端修复——敌方 heal_down（层数×10%）/ _anti_heal_pct（百分比）
        # 此前 weapon_effects/affix_effects 只写入不消费（死数据，禁疗无效）
        try:
            _ehd = int((self.e_buffs or {}).get("heal_down", 0) or 0)
            if _ehd > 0:
                heal = max(0, int(heal * (1 - min(_ehd * 0.10, 0.50))))
                logs.append(f"🩸 敌方禁疗：治疗量 -{min(_ehd * 10, 50)}%！")
            _aheal = float((self.e_buffs or {}).get("_anti_heal_pct", 0) or 0)
            if _aheal > 0:
                heal = max(0, int(heal * (1 - min(_aheal, 0.80))))
                logs.append(f"🩸 敌方重伤：治疗量 -{int(min(_aheal, 0.80) * 100)}%！")
        except Exception:
            pass
        # v140 波3.1：特效装备治疗加成（坚毅祝福+15%/圣辉涌动+20%/回响祝福+25%）+ 溢出转盾（圣木/赎罪）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wectx = {"heal": heal, "overflow": 0, "target": target_unit}
            _we_proc(self, player, "heal", _wectx, logs)
            heal = max(1, int(_wectx.get("heal", heal)))
            _we_proc(self, player, "passive", {"heal": heal}, logs)
        except Exception:
            pass
        target_unit["hp"] = min(target_unit.get("max_hp", target_unit.get("hp", 0)), hp_before + heal)
        # v140 S1 直连消费：圣愈不浪费（cloth_heal_overflow）——治疗溢出量 50% 转护盾
        if self._set_eff(player, "cloth_heal_overflow", 4):
            _cho_ov = hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0))
            if _cho_ov > 0:
                _cho_sh = int(_cho_ov * 0.50)
                if target_ally is not None:
                    _sh_t = target_unit.setdefault("p_shields", {})
                    _cur_t = _sh_t.get("cloth_overflow")
                    if _cur_t:
                        _cur_t["value"] = _cur_t.get("value", 0) + _cho_sh
                        _cur_t["turns"] = max(_cur_t.get("turns", 0), 2)
                    else:
                        _sh_t["cloth_overflow"] = {"value": _cho_sh, "turns": 2}
                    logs.append(f"☀️ 圣愈不浪费：治疗溢出转化 {_cho_sh} 点护盾！")
                else:
                    self._add_shield("cloth_overflow", _cho_sh, 2)
                    logs.append(f"☀️ 圣愈不浪费：治疗溢出转化 {_cho_sh} 点护盾！")
        # v140 波3.1：特效装备治疗溢出转盾（回响祝福/赎罪之盾）——clamp 后计算真实溢出
        try:
            _real_overflow = max(0, hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0)))
            if _real_overflow > 0:
                from .core.weapon_effects import proc as _we_proc2
                _we_proc2(self, player, "heal", {"heal": heal, "overflow": _real_overflow}, logs)
        except Exception:
            pass
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
        # v130.2 资源增幅：治疗触发（香薰圣烛 on_heal 额外 +1 信仰，持续时长制）
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
        # v153 §7：诗人旋律——增益技能带 melody 字段 → 起手/吟唱/终章（驻留光环）
        if info.get("melody") or mech in ("melody", "melody_chant", "melody_finale"):
            try:
                from .core.battle_mech import MECH_EFFECTS
                _mh = MECH_EFFECTS.get(mech or "melody")
                if _mh:
                    _mh(self, mval or 1, p_mech, 0, logs, skill_name, False, info)
            except Exception:
                pass
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
                # v130.2 歌者回声：增益技持续 + 回声层数 刻（priest_转职.md §3.0）
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
        # v140 波3.1：特效装备技能释放即叠层（铭文/秘典/永恒契约——含治疗/增益）
        try:
            from .core.weapon_effects import proc as _we_proc
            _we_proc(self, player, "skill_cast", {"skill": skill_name, "kind": kind}, logs)
        except Exception:
            pass
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
        # v130.2f2：顺带记录本次攻击出手时处于潜行（供暮影潜行乘区 破影一击×1.5/幽影刃×1.25 消费，
        #   判定与下方必暴共享同一字段 p_buffs["stealth"]：攻击时消费即视为潜行出手）
        _stealth_hit = False
        self._stealth_atk = False  # v130.2f2（T11 P2）：潜行出手标记每次出手前复位
        if self.p_buffs.get("stealth"):
            is_crit = True
            _stealth_hit = True
            self._stealth_atk = True  # 潜行出手标记——供 _on_crit_resource（潜行出手额外+1 影步）与暗影之舞暴伤被动读取
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
        # v130.2f2 暮影潜行乘区：潜行出手时 终结·破影一击 ×1.5 / 幽影刃 ×1.25（数据驱动
        #   SHADOW_STEALTH_DMG_MULT，assassin.md §5.2；非潜行/非表内技能恒 1.0，不影响其他职业）
        stealth_mult = 1.0
        if _stealth_hit and skill_name in SHADOW_STEALTH_DMG_MULT:
            stealth_mult = float(SHADOW_STEALTH_DMG_MULT[skill_name])
        # v109.2 P1-1 运势：暴击命中后 30% 概率追加 50% 伤害（幸运一击，含必暴机制）
        lucky = is_crit and random.random() < LUCKY_CRIT_CHANCE
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
            elif _sstat == "stealth_crit_dmg" and (self.p_buffs.get("stealth") or getattr(self, "_stealth_atk", False)):
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
                # 冻结：目标冻结 1 刻
                elif r["extra"] == "freeze":
                    self.e_buffs["freeze"] = 1
                    reaction_log = "❄️冻结！目标被冰封 1 刻！"
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
        # v156：蓄势已由 _player_dmg_mult 统一乘入（普攻/技能共用），此处只记录标签
        _mom_mult = self._momentum_mult(player)
        if kind == "物理" and _mom_mult != 1.0:
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
        # v130.6 三连击破回馈实装（combo_ready 消费端，原只写不读的死标记）：
        # 三连后下一次气力技（res_cost 耗气 / consume_all 耗气技能）伤害 +20%，
        # 一次性消费；文案与连招三连 desc 统一为 +20%（钢拳「三连准备」设计意图）
        if self.resources.get("combo_ready"):
            _is_chi_skill = ("chi" in (info.get("res_cost") or {})) or \
                ((info.get("consume_all") or {}).get("key") == "chi")
            if _is_chi_skill:
                passive_bonus *= 1.20
                self.resources["combo_ready"] = 0
                self._combo_ready_used = True
            else:
                self._combo_ready_used = False
        # v130.2c 伤害倍率词条：爆发贯体（气力技物理 +10%）/ 终结之技（终结技 +10%~20%，tier 取档）
        # v130.2c 套装伤害倍率：暗夜圣典 4 件（安魂曲/献祭暗焰 +20%）/ 势不可挡 4 件（气力技/终结技物理 +15%）
        _sk_af = self._affix_skill_dmg_mult(player, info, kind) * self._set_skill_dmg_mult(player, info, kind, skill_name)
        if _sk_af != 1.0:
            passive_bonus *= _sk_af
        self._sk_af_mult = _sk_af
        total = 0
        _magi_part = 0  # v109.2 P2-4：混合伤害魔法段累计（吸血分账用）
        # v156 玩家侧公共乘区统一组装（词条/狼嚎/蓄势/禅意/物理药水/种族）——
        # 与普攻共用 _player_dmg_mult（一处修改，普攻/技能同时生效）
        affix_mult, affix_tags = self._player_dmg_mult(player, kind)
        if self._mom_mult != 1.0:
            affix_tags = list(affix_tags) + [f"🔥蓄势x{round(self._mom_mult, 2)}"]
        if self._combo_mult != 1.0:
            affix_tags = list(affix_tags) + [f"🌪️连段x{round(self._combo_mult, 2)}"]
        if getattr(self, "_combo_ready_used", False):
            affix_tags = list(affix_tags) + ["🥊三连余劲x1.20"]
        if getattr(self, "_sk_af_mult", 1.0) > 1.0:
            affix_tags = list(affix_tags) + [f"⚔️套装技x{round(self._sk_af_mult, 2)}"]
        elem_mult = self._affix_element_dmg(player, element)
        pmult = (E.skill_power_mult(lv, info) * frozen_bonus * stealth_mult * stack_bonus * cond_mult
                 * magic_bonus * passive_bonus * reaction_mult * affix_mult * elem_mult
                 * self._v139_dmg_mult(player, info))
        # vF3 P1 连乘封顶：技能伤害倍率连乘（技能×冻结×潜行×叠层×条件×魔法×被动×反应×词缀×元素×种族×v139形态/专注）
        # 只 clamp 技能伤害倍率段；暴击(×1.5)/暴伤(crit_dmg)/幸运一击(×1.5) 为独立乘区，在下方另行施加不受此限。
        if pmult > C.SKILL_PMULT_CAP:
            pmult = C.SKILL_PMULT_CAP
        # v106 穿透：物理技能用物穿/固定物穿，魔法技能用法穿/固定法穿
        _pp_phys, _pf_phys = self._pene_vals(st, magic=False)
        _pp_magi, _pf_magi = self._pene_vals(st, magic=True)
        # v156 技能基础值（保底伤害）：flat = BASE + 玩家等级×PER_LV + 技能等级×PER_SKILL_LV
        # 鱼鱼拍板：技能 = 基础值 + n%AD/AP（低攻不刮痧，高攻百分比主导）
        _skill_flat = E.skill_flat_value(int(player.get("level", 1) or 1), lv, info)
        for seg in range(multi):
            # v133 峰值红线：多段仅首段吃暴击/幸运（MULTI_HIT_CRIT_FIRST_ONLY，
            # 避免"多段共享单次暴击判定"整段连锁暴击的峰值爆炸）
            _seg_crit = is_crit and (seg == 0 or not MULTI_HIT_CRIT_FIRST_ONLY)
            _lucky_seg = lucky and (seg == 0 or not MULTI_HIT_CRIT_FIRST_ONLY)
            # v156 formula 字段：每技能独立配置伤害公式（数据驱动任意组合）——
            #   [{"stat": "atk"|"matk"|"max_hp"|"flat", "mult": 百分比系数, "flat": 固定值(基础值), "type": "phys"|"magi"|"true"}]
            #   混伤：多段 formula；物理职业魔法技：stat=atk + type=magi；基础值+百分比：flat
            #   未配 formula 自动从 power/kind 生成（向后兼容：物理→atk、魔法→matk、真伤→atk true）
            #   统一走 E.resolve_formula（普攻/敌方/装备/食物共用同一解释器）
            # v157：段级 "skill_flat": true → 注入 v156 技能基础值（等价非 formula 路径 +_skill_flat）。
            #       flat 必须 × pmult（resolve_formula 内部 flat 不乘外层 mult，这里预先乘好）：
            #       base = atk×(power×pmult) + flat×pmult = (atk×power + flat)×pmult，与非 formula 路径等价。
            #       段级 "pierce": true → 绕过防御（等价非 formula 路径 calc_damage(pierce=True)）
            # v160 逐级表达式：技能级 exprs（每级一条完整表达式字符串）→ 构造单段 formula 走统一解释器
            #   用法：'exprs': ['atk*0.8 + 20', 'atk*0.85 + 25', ...]，第 N 级取第 N 条（越界取最后）
            #   单条 expr（字符串）同样走这里（v159：表达式即唯一数值来源，与 formula 数组互斥）
            #   type 由 kind 推导（物理→phys、真伤→true、其余 magi），与旧 formula 自动生成一致
            #   ⚠️ 表达式已内嵌技能等级成长（skill_lv 变量/逐级公式），不再叠加 skill_power_mult——
            #      外层 mult 需剔除技能成长项（pmult 含 skill_power_mult），避免双重成长
            _skill_expr = E.skill_formula_expr(info, lv)
            if _skill_expr:
                _seg_type = "true" if kind == "真伤" else ("phys" if kind == "物理" else "magi")
                st["_player_lv"] = int(player.get("level", 1) or 1)
                st["_skill_lv"] = lv
                _pmult_expr = pmult / E.skill_power_mult(lv, info) if E.skill_power_mult(lv, info) else pmult
                _dmg0, _mseg0 = E.resolve_formula(
                    [{"expr": _skill_expr, "type": _seg_type}], st, est["def"], est["mdef"],
                    is_crit=_seg_crit, pene_phys=_pp_phys, pene_magi=_pp_magi,
                    pene_flat_phys=_pf_phys, pene_flat_magi=_pf_magi,
                    mult=_pmult_expr, variance=0.15,
                )
                dmg_i = _dmg0
                _magi_part += _mseg0
            elif info.get("formula"):
                _fml = []
                for _seg in info["formula"]:
                    _seg = dict(_seg)
                    if _seg.pop("skill_flat", False):
                        _seg["flat"] = int(round((int(_seg.get("flat", 0) or 0) + _skill_flat) * pmult))
                    _fml.append(_seg)
                # v159 表达式变量：注入玩家/技能等级供 build_vars 读取（expr 段用）
                st["_player_lv"] = int(player.get("level", 1) or 1)
                st["_skill_lv"] = lv
                dmg_i, _mseg = E.resolve_formula(
                    _fml, st, est["def"], est["mdef"], is_crit=_seg_crit,
                    pene_phys=_pp_phys, pene_magi=_pp_magi,
                    pene_flat_phys=_pf_phys, pene_flat_magi=_pf_magi,
                    mult=pmult, variance=0.15,
                )
                _magi_part += _mseg
            elif kind == "真伤":
                dmg_i = E.calc_damage(int((st["atk"] * info["power"] + _skill_flat) * pmult), 0, _seg_crit, dmg_type="true")
            elif kind == "物理":
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int((st["atk"] * info["power"] + _skill_flat) * pmult), 0, _seg_crit, pierce=True,
                                          dmg_type="phys")
                else:
                    dmg_i = E.calc_damage(int((st["atk"] * info["power"] + _skill_flat) * pmult), est["def"], _seg_crit,
                                          pene_pct=_pp_phys, pene_flat=_pf_phys, dmg_type="phys")
                # v87 魔剑士·混合伤害：magic_add 追加魔法段（魔能斩 130% 物 + 30% 魔）
                if info.get("magic_add"):
                    dmg_m = E.calc_damage(int(st["matk"] * info["magic_add"] * pmult), est["mdef"], _seg_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
                    dmg_i += dmg_m
                    _magi_part += dmg_m
            else:
                # v109.2 P1-6：pierce 魔法分支修复——审判之剑等魔法 pierce 技能此前被结算链忽略
                if info.get("pierce"):
                    dmg_i = E.calc_damage(int((st["matk"] * info["power"] + _skill_flat) * pmult), 0, _seg_crit, pierce=True,
                                          dmg_type="magi")
                else:
                    dmg_i = E.calc_damage(int((st["matk"] * info["power"] + _skill_flat) * pmult), est["mdef"], _seg_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
            # v87 魔剑士·魔力涌动：消耗 buff，本次攻击追加 80% 魔法伤害
            if self.p_buffs.get("spellblade_surge"):
                surge_dmg = E.calc_damage(int(st["matk"] * 0.80 * pmult), est["mdef"], _seg_crit,
                                          pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
                dmg_i += surge_dmg
                _magi_part += surge_dmg
                del self.p_buffs["spellblade_surge"]
            # v34 残忍：暴击伤害 +x%（按等级，符文特效）
            brutal_lvl = self._enchant_lvl(effs, "brutal")
            if brutal_lvl and _seg_crit:
                dmg_i = int(dmg_i * (1 + C.rune_value("brutal", brutal_lvl)))
            # v106.3 暴击伤害属性（crit_dmg 面板化：词条折算 + 种族 + 被动 + 药水）
            cdmg = float(st.get("crit_dmg", 0) or 0)
            if self.p_buffs.get("crit_dmg_pot"):
                cdmg = 1 - (1 - cdmg) * (1 - 0.25)  # 狂暴药剂 +25% 暴伤（乘算并入）
            if _seg_crit and cdmg > 0:
                dmg_i = int(dmg_i * (1 + cdmg))
            # v109.2 P1-1 运势：幸运一击——暴击后 30% 概率追加 50% 伤害
            if _lucky_seg:
                dmg_i = int(dmg_i * LUCKY_CRIT_MULT)
            dmg_i = self._apply_mark(dmg_i)
            total += dmg_i
        if lucky:
            logs.append("✨ 幸运一击！暴击伤害额外提升 50%！")
        total = self._boss_dmg_filter(total, player, logs, dmg_type={"物理": "phys", "魔法": "magi", "真伤": "true"}.get(kind, "phys"))
        # v140 波3.1：特效装备技能被动增伤（奥术苍穹/岁月流转/永恒契约/铭文/秘典/雷纹/三相/破岳/咒誓/暮裂）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wectx = {"mult": 1.0, "tags": [], "is_crit": is_crit, "kind": kind, "skill": skill_name}
            _we_proc(self, player, "passive", _wectx, logs)
            # v140 波3.2：弱点击破石——目标负面越多增伤越高（vuln 标记）
            _vuln = (self.p_eff or {}).get("vuln")
            if _vuln and int(_vuln.get("turns_left", 0) or 0) > 0:
                _vb = float(_vuln.get("bonus", 0) or 0)
                if _vb > 0:
                    _wectx["mult"] = _wectx.get("mult", 1.0) * (1 + _vb)
            if _wectx.get("mult", 1.0) != 1.0:
                total = int(total * _wectx["mult"])
        except Exception:
            pass
        # v153 §2/§6：元素印记结算倍率 / 磐核爆发倍率消费（battle_mech handler 写入 p_buffs）
        _v153_mult = 1.0
        if self.p_buffs.get("element_burst_mult"):
            _v153_mult *= float(self.p_buffs.pop("element_burst_mult"))
            logs.append(f"🔥 元素结算增伤 ×{_v153_mult:.2f}")
        if self.p_buffs.get("guard_core_burst_mult"):
            _v153_mult *= float(self.p_buffs.pop("guard_core_burst_mult"))
        if self.p_buffs.get("finisher_mult"):
            _v153_mult *= float(self.p_buffs.pop("finisher_mult"))
        if self.p_buffs.get("bone_rush_mult"):
            _v153_mult *= float(self.p_buffs.pop("bone_rush_mult"))
        if self.p_buffs.get("element_overload_aoe"):
            # 超载反应：本次技能转全体 AOE
            info = dict(info)
            info["aoe"] = "all"
            self.p_buffs.pop("element_overload_aoe", None)
        if _v153_mult != 1.0:
            total = int(total * _v153_mult)
        # v153 §2：感电连击（雷印满 3 层结算时连击 +1/+2）——多段追加
        _ele_combo = int(self.p_buffs.get("element_thunder_combo", 0) or 0)
        if _ele_combo:
            self.p_buffs.pop("element_thunder_combo", None)
            _combo_dmg = int(total / max(1, int(info.get("hits", 1) or 1)))
            for _ci in range(_ele_combo):
                total += _combo_dmg
                logs.append(f"⚡ 感电连击！追加 {_combo_dmg} 点伤害！")
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
                # v136 等级压制：_damage_enemy 内部按等级差压制实际伤害，返回值=真实扣血，
                # 回写 total 让后续日志/吸血/结算都反映压制后的值（原 total 未回写→日志虚高）
                _real = self._damage_enemy(total, logs)
                _boss_dmg = _real
                if _real != total:
                    total = _real
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
        if stealth_mult > 1.0:
            tags.append(f"🌙潜行x{round(stealth_mult, 2)}")
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
            # v104 R3 P1-1：寒霜亲和——冰系技能命中附带减速 2 刻
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
        # v140 波3.1：特效装备技能命中（余波/咒刃/湮灭回响/烬燃/永冻/永霜禁锢/无尽辉光/无尽锋芒等）
        try:
            from .core.weapon_effects import proc as _we_proc
            _we_proc(self, player, "skill_hit",
                     {"dmg": total, "is_crit": is_crit, "skill": skill_name, "kind": kind}, logs)
        except Exception:
            pass
        # v140 波3.2：连携增幅墨——技能命中使目标毒/灼烧/流血层数 +1（dot_amp 标记）
        _dam = (self.p_eff or {}).get("dot_amp")
        if _dam and int(_dam.get("turns_left", 0) or 0) > 0 and total > 0:
            _per = max(1, int(_dam.get("layer_per_hit", 1) or 1))
            _deb = self.enemy.setdefault("debuffs", {})
            for _dk in ("poison", "burn", "bleed"):
                if _deb.get(_dk, {}).get("n", 0):
                    _d = _deb.setdefault(_dk, {"n": 0, "mult": 1.0})
                    _d["n"] = int(_d.get("n", 0) or 0) + _per
            logs.append(f"🎨 连携增幅墨：异常层数 +{_per}！")

        # ---- 分支机制结算（v29） ----
        self._last_player = player
        self._apply_mech_effect(mech, mval, p_mech, total, logs, skill_name, is_crit, info)
        # v153：mech2 第二机制（如冰锥 mech=ice_mark + mech2=spd_down 减速）——独立结算
        _mech2 = info.get("mech2")
        if _mech2:
            _m2val = int(info.get("mech2_val", 0) or 0) or 1
            self._apply_mech_effect(_mech2, _m2val, p_mech, total, logs, skill_name, is_crit, info)
        # v63 额外控制效果（cc 字段，独立于 mech 叠层）：眩晕/沉默/净化
        # v125.2 B1：cc 白名单查表 SKILL_CC_WHITELIST
        cc = info.get("cc")
        if cc and cc in SKILL_CC_WHITELIST:
            self._apply_mech_effect(cc, 1, p_mech, total, logs, skill_name, is_crit, info)
        # ---- v139 enemy_bar 挂敌身条：技能命中注入 shaken（拳师破绽/淬势撼岳）----
        # 数据源：技能 info.shaken_gain（三连击破+15/碎颅势+15/旋风踢+5每目标/无影连打每段+3）
        # 触发：阈值满 → 敌方跳过刻（skip_turn）；触发后免疫窗口 + 阈值递增（防无限控）
        _shaken_gain = info.get("shaken_gain")
        if _shaken_gain:
            try:
                from .core.battle_bars import bar_gain, bar_should_trigger, bar_trigger
                _tgt = getattr(self, "_active_target", None) or self.enemy
                _sg = int(_shaken_gain)
                bar_gain(_tgt, "shaken", _sg, logs)
                if bar_should_trigger(_tgt, "shaken"):
                    if bar_trigger(_tgt, "shaken", logs):
                        _tgt_buffs = _tgt.get("buffs", {})
                        _bs = _tgt_buffs.get("shaken", {})
                        logs.append(f"💢 破绽值满！敌人被震慑，下刻无法行动！(阈值提升至 {_bs.get('threshold', '?')})")
            except Exception:
                pass

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
            self._set_attack_proc(player, total, logs, is_crit=is_crit)
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

    def _v139_dmg_mult(self, player: dict, info: dict | None = None) -> float:
        """v139 职业融合：dual_form 形态增伤 × focus 专注增伤（连乘进 pmult）。

        数据驱动：读 player 的 dual_form/focus 数据字段（core_resources 配置），
        无字段 = 1.0（不启用）。focus 的 no_burst_skills 保护由 battle_modes 内部处理。
        """
        if player is None:
            return 1.0
        try:
            # 桥接状态源（若 _is_path 未被调用过，主动挂载）
            player.setdefault("v139_modes", self._v139_modes)
            player.setdefault("v139_charge", self._v139_charge)
            from .core.battle_modes import dual_form_active, dual_form_mult, focus_active, focus_mult
            m = 1.0
            if dual_form_active(player):
                m *= dual_form_mult(player)
            if focus_active(player):
                m *= focus_mult(player, info)
            return m
        except Exception:
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
        作用在 Boss（敌方 dict is_boss 标记或 role=="boss"）上时时长减半（向下取整、至少 1 刻）。
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
        # v130.2f2（T7 P1-1）：鹰眼 mark_extra 在游侠标记路径（mech=mark：林语印记/猎杀标记类技能）
        # 也独立 roll——与法师元素印记路径（_player_skill 3388-3390）同语义：每个被动独立 chance，
        # 额外层经同源 handler 叠加进目标 debuffs.mark（cap 5）。此前消费点只在 element 印记分支，
        # 全库 element 技能仅法师系持有，游侠/星语猎手标记被动（追踪印记 30%/鹰眼 15%）零触发=死被动。
        if mech == "mark":
            _pl_mark = getattr(self, "_last_player", None) or self.player or {}
            _extra_mark = 0
            _trig_mark = []
            for _pn_m, _ps_m in self._passive_map(_pl_mark)["proc"].get("mark_extra", []):
                if random.random() < float(_ps_m.get("chance", 0.15) or 0.15):
                    _extra_mark += 1
                    _trig_mark.append(_pn_m)
            if _extra_mark > 0:
                _mh_mark = MECH_EFFECTS.get("mark")
                if _mh_mark:
                    _mh_mark(self, _extra_mark, p_mech, total, logs, skill_name, is_crit, info)
                logs.append(f"🎯 {'/'.join(_trig_mark)}：额外标记 +{_extra_mark} 层！（与追踪印记叠加）")
        # v120 审计修复 q5：玩家施加的控制（眩晕/冰冻/沉默）统一切入 Boss 控制抗性——
        # Boss 时长减半（至少 1 刻）；非 Boss 不变（handler 已设时长，此处术后收紧）。
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
    def _set_attack_proc(self, player: dict, dmg: int, logs: list, is_crit: bool = False):
        """玩家攻击后触发已激活套装的 4 件攻击特效
        v98.5：效果数据化 → core/affix_effects.py SET_PROC_EFFECTS
        v140 S1：is_crit 透传并落到 battle._last_crit（供 phantom_echo 等 handler 读）
        v142：数据驱动重构——优先读 params.type 调通用执行器，无 params 回退旧注册表"""
        self._last_crit = bool(is_crit)
        effs = E.set_bonus_4(player.get("equipment", {}))
        if not effs:
            return
        from .core.affix_effects import _execute_set_proc
        for eff_name in effs:
            # 从套装数据取完整 effect dict（含 params）
            eff = self._set_eff(player, eff_name, 4) or {"effect": eff_name}
            _execute_set_proc(eff, self, player, dmg, logs)

    # ---------------- 敌方刻 ----------------
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
        # v138.1 阶段四件套：承伤倍率 dmg_taken_mult（>1=更脆，对应「疲态核心件外露」易伤+0.40）——
        # 由 _phase_apply 写入 e._dmg_taken_mult，_enemy_stats 聚合时从 _phase_mod 刷新
        _dtm = float((self.enemy or {}).get("_dmg_taken_mult", 1.0) or 1.0)
        if _dtm != 1.0:
            dmg = max(1, int(dmg * _dtm))
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
        phases 剧本化交给 _b_phase（换招/演出刻/阈值预告）。"""
        e = unit or self.enemy
        mech = e.get("mech")
        if not mech or self.btype == "pvp":
            return
        from .core.battle_mech import BOSS_MECHS
        mechs = [x.strip() for x in mech.split(",") if x.strip()]
        # v152 时刻制：round 删除，r = 从绝对时刻换算的行动轮次（int(now / ACT_TICK)）。
        # 语义 = "第几个标准行动间隔"，供 r % N / r == 1 等"每隔 N 次"机制使用。
        r = self._tick_no()
        for m in mechs:
            handler = BOSS_MECHS.get(m)
            if handler:
                handler(self, logs, e, r)

    def _tick_no(self) -> int:
        """v152：从绝对时刻换算行动轮次（展示/机制用）。1 轮 ≈ ACT_TICK 时刻。"""
        try:
            return int(self._now / (ACT_TICK or 2.0)) + 1
        except Exception:
            return 1

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
        """v116.1：清空反制/追击瞬态标记（敌方每刻开头调用，仅触发当刻生效）。"""
        if e is None:
            return
        e.pop("_low_hp_active", None)
        e.pop("_pv_broken_active", None)

    def _reactive_extra_attack(self, e: dict, pst: dict, logs: list) -> int:
        """v116.1 pv_broken 反扑：本刻追加一次普攻（趁你破绽）。返回追加伤害。"""
        if not e.get("_pv_broken_active"):
            return 0
        est = self._enemy_stats(e)
        xtra = E.calc_damage(est.get("atk", 0), pst.get("def", 0), False)
        logs.append(f"💢【{e['name']}】反扑的一击，追加 {xtra} 点伤害！")
        self._pending_dmg_lines.append(f"【{e['name']}】追加攻击，造成 {xtra} 点伤害！")
        return xtra

    def _enemy_cast_done(self, player: dict, unit: dict, ev: dict) -> tuple:
        """v154 敌方对称读条：敌方出招读条结束（cast_done 事件触发）→ 结算伤害。
        返回 (日志列表, 对玩家伤害)。
        ev payload: {"kind": "skill"|"atk", "skill": 技能key, "power_mult": 伤害系数}
        - skill：按 MONSTER_SKILLS 结算（物理/魔法/元素抗性/控制）
        - atk：敌方普攻结算
        被控跳过/增益/蓄力不走此函数（_enemy_turn 内立即处理）。
        """
        e = unit or {}
        eb = e.setdefault("buffs", {})
        ename = e.get("name", "怪物")
        logs = []
        # v116.1 反制/追击瞬态标记
        self._clear_reactive_flags(e)
        pst = self._player_stats(player)
        est = self._enemy_stats()
        dmg = 0
        _kind = ev.get("kind", "atk")
        # v63 沉默：敌方技能被沉默 → 读条结束时转为普攻（与出手瞬间判定一致）
        if _kind == "skill" and "silence" in eb:
            _kind = "atk"
        if _kind == "skill":
            sinfo = C.MONSTER_SKILLS.get(ev.get("skill") or "") or {}
            if not sinfo:
                _kind = "atk"
            else:
                sname = sinfo.get("name", ev.get("skill", "?"))
                kind = sinfo.get("kind")
                power = float(ev.get("power_mult", sinfo.get("power", 1.0)))
                is_crit = random.random() < est.get("crit", C.MON_SKILL_CRIT) * self._tenacity_mult(pst)
                # v156 通用公式：敌方技能带 formula 字段走数据驱动公式（任意 atk/matk/max_hp/混伤），
                # 否则从 power/kind 自动生成 formula（向后兼容）
                _fml = sinfo.get("formula")
                if _fml:
                    _pp, _pf = self._pene_vals(est)
                    _pp_m, _pf_m = self._pene_vals(est, magic=True)
                    dmg, _ = E.resolve_formula(
                        _fml, est, pst.get("def", 0), pst.get("mdef", 0), is_crit=is_crit,
                        pene_phys=_pp, pene_magi=_pp_m,
                        pene_flat_phys=_pf, pene_flat_magi=_pf_m,
                    )
                    # v157 修复：formula 分支同样走物理/魔法免伤结算（此前直接返回，
                    # 魔法免伤(magic_reduce)/鲁莽之心(mr<0) 对带 formula 的怪物技能失效——
                    # v157 怪物全量配 formula 后暴露。与下方非 formula 分支同款逻辑。
                    if kind == "物理":
                        _pst_pr = self._player_stats(player)
                        pr = min(float(_pst_pr.get("phys_reduce", 0) or 0), 0.4)
                        if pr > 0:
                            red = max(1, int(dmg * pr))
                            dmg = max(1, dmg - red)
                            logs.append(f"🪨 物理免伤，减免 {red} 点物理伤害！")
                    else:
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
                elif kind == "物理":
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
                self._pending_dmg_lines.append(
                    f"【{ename}】使用了【{sname}】，对你造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
                # v63 怪物技能控制（读条结束命中时施加）
                mmech = sinfo.get("mech")
                if mmech:
                    from .core.battle_mech import MON_CTRL_EFFECTS
                    ctrl_fn = MON_CTRL_EFFECTS.get(mmech)
                    if ctrl_fn:
                        mval = int(sinfo.get("mech_val", 1) or 1)
                        ctrl_fn(self, player, logs, mval)
                dmg += self._reactive_extra_attack(e, pst, logs)
                return logs, dmg
        # 敌方普攻（_kind == "atk" 或技能查表失败）
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

    def _enemy_turn(self, player: dict, unit=None) -> tuple:
        """敌方单个单位行动。返回 (日志列表, 对玩家伤害)。
        v2：unit 缺省 = 主目标（单怪兼容）；支持单位级蓄力。
        v154 敌方对称读条：本函数 = 敌方"出手瞬间"（决定动作类型 + 排敌方出招读条）。
        出招读条结束（cast_done）才结算伤害——见 _enemy_cast_done。
        特例：被控跳过（眩晕/冻结/睡眠）、增益/蓄力直接返回（无出招读条）。
        """
        if self.btype == "pvp":
            return self._pvp_enemy_turn(player)
        e = unit or self.enemy
        eb = e.setdefault("buffs", {})
        ename = e.get("name", "怪物")
        logs = []
        # v2：本次敌方行动目标 = 该单位（_enemy_stats 默认按 _active_target 解析单位属性；
        # 兼容测试 monkeypatch 的 1 参 _enemy_stats）
        self._active_target = e
        # v154：est 提前定义（被控/阶段跳过分支的 ct 重排需要 spd）
        est = self._enemy_stats()
        # v116.1 反制/追击瞬态标记：每刻开头清空，仅本刻触发的刻生效
        self._clear_reactive_flags(e)
        self._boss_mech(logs, e)
        # v116.1 阶段演出刻：_b_phase 触发进入新阶段时设 battle._phase_skip_act，
        # 本刻 Boss 不行动（给玩家呼吸点），消费后立即复位避免影响后续刻/单位。
        if getattr(self, "_phase_skip_act", False):
            self._phase_skip_act = False
            logs.append(f"🎬 【{ename}】正在蜕变，尚未行动！")
            self._after_actor_ct("e", e, cast_mult=CAST_ATK * self._ct_cost(est.get("spd", 0)))
            return logs, 0
        # v138.1 反制窗口：Boss 处于阶段模板（_phase_counter）时，每刻战报附一行解题提示
        _ctr = (e or {}).get("_phase_counter")
        if _ctr:
            logs.append(f"💡 反制：{_ctr}")
        pst = self._player_stats(player)
        dmg = 0
        # v29 冻结：跳过敌方刻
        if "freeze" in eb:
            logs.append(f"❄️ 【{ename}】被冻结，无法行动！")
            eb.pop("freeze", None)
            self._after_actor_ct("e", e, cast_mult=CAST_ATK * self._ct_cost(est.get("spd", 0)))
            return logs, 0
        # v63 眩晕
        if "stun" in eb:
            logs.append(f"🌀 【{ename}】被眩晕，无法行动！")
            eb.pop("stun", None)
            self._after_actor_ct("e", e, cast_mult=CAST_ATK * self._ct_cost(est.get("spd", 0)))
            return logs, 0
        # v151 破绽断链修复（引擎差距报告 P0）：破绽触发（skip_turn）→ 敌方跳过行动。
        # bar_trigger 已设 immune_turns>0 且 val 清空；此处读 immune_turns>0 判定本刻应跳过。
        _sk = eb.get("shaken")
        if isinstance(_sk, dict) and int(_sk.get("immune_turns", 0) or 0) > 0:
            logs.append(f"💢 【{ename}】被破绽震慑，无法行动！")
            self._after_actor_ct("e", e, cast_mult=CAST_ATK * self._ct_cost(est.get("spd", 0)))
            return logs, 0
        # v109.2 P1-3：睡眠（受击解除，按刻递减）
        # v121 审计修复：刻递减只由 _end_round 统一执行（每玩家行动 1 次）——
        # 此分支此前每次被选中行动都 -1，CTB 连动下睡眠一刻被多重递减直接清零
        if "sleep" in eb:
            logs.append(f"💤 【{ename}】陷入沉睡，无法行动！")
            self._after_actor_ct("e", e, cast_mult=CAST_ATK * self._ct_cost(est.get("spd", 0)))
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
                # （本刻不结算伤害，先给意图预告，之后刻由 _enemy_charge_tick 结算）
                charge_n = int(sinfo.get("charge", 0) or 0)
                if charge_n > 0 and not e.get("charging"):
                    e["charging"] = {"skill": skill, "left": charge_n, "name": sname}
                    logs.append(
                        f"⚠️ 【意图】{ename} 正在蓄力【{sname}】！下刻将造成大伤害——"
                        f"可『防御』减半或『打断技』赌它读条失败！")
                    return logs, 0
                if kind == "增益":
                    from .core.battle_mech import MON_BUFF_EFFECTS
                    eff = sinfo.get("effect")
                    eff_fn = MON_BUFF_EFFECTS.get(eff)
                    if eff_fn:
                        eff_fn(self, logs, sname)
                    # v154：增益立即生效，但敌方行动也要消耗 ct（读条 + 收招）
                    self._after_actor_ct("e", e, cast_mult=CAST_SKILL * self._ct_cost(est.get("spd", 0)))
                    return logs, 0
                power = sinfo.get("power", 1.0)
                # v154 敌方对称读条：技能出招 → 排 cast_done（出招读条结束才命中结算）
                # 出招读条时长 = 技能 cast（缺省 CAST_SKILL），速度折算
                _cast_t, _rec_t = self._action_times("skill", skill=sinfo, spd=est.get("spd", 0))
                _cast_t = _cast_t or (CAST_SKILL * self._ct_cost(est.get("spd", 0)))
                self._schedule_cast_done(self._now + _cast_t,
                                         {"side": "e", "unit": e, "kind": "skill",
                                          "skill": skill, "power_mult": power})
                logs.append(f"⚔️ 【{ename}】正在施展【{sname}】！(出招 {_cast_t:.1f}s)")
                # 敌方读条后收招：ct = 命中时刻 + 收招（= 出手 + 总耗时）
                self._after_actor_ct("e", e, cast_mult=_cast_t + _rec_t)
                return logs, 0
        # v154 敌方对称读条：敌方普攻出招 → 排 cast_done（出招读条结束才命中结算）
        # 出招读条时长 = 普攻 cast（缺省 CAST_ATK），速度折算
        _cast_t, _rec_t = self._action_times("atk", spd=est.get("spd", 0))
        _cast_t = _cast_t or (CAST_ATK * self._ct_cost(est.get("spd", 0)))
        self._schedule_cast_done(self._now + _cast_t,
                                 {"side": "e", "unit": e, "kind": "atk"})
        logs.append(f"⚔️ 【{ename}】挥爪扑向你！(出招 {_cast_t:.1f}s)")
        # 敌方读条后收招：ct = 命中时刻 + 收招（= 出手 + 总耗时）
        self._after_actor_ct("e", e, cast_mult=_cast_t + _rec_t)
        return logs, 0

    def _enemy_charge_tick(self, e: dict, pst: dict, est: dict, logs: list, ename: str) -> tuple:
        """敌方蓄力单位刻：left-1；归零自动释放技能（结算效果，不普攻）。"""
        ch = e.get("charging") or {}
        left = int(ch.get("left", 1) or 1)
        cname = ch.get("name", ch.get("skill", "?"))
        if left > 0:
            ch["left"] = max(0, left - 1)
            e["charging"] = ch if ch["left"] > 0 else None
            if ch["left"] == 0:
                # 蓄力完成释放：意图预告（释放刻）+ 立即结算（传技能 key 供查表）
                logs.append(f"✨ 【{ename}】的【{cname}】蓄力完成，轰然落下！")
                # 释放 = 结算一次该单位的技能效果（无目标次要：对玩家造成伤害）
                return self._enemy_release_charge(e, ch.get("skill") or cname, pst, est, logs, ename)
            # 蓄力持续刻：精简意图预告（剩 N）
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
        # v154：蓄力释放后敌方重排下次行动（读条 + 收招）
        self._after_actor_ct("e", e, cast_mult=CAST_SKILL * self._ct_cost(est.get("spd", 0)))
        return logs, max(0, dmg)

    def _pvp_enemy_turn(self, player: dict) -> tuple:
        """PVP：敌方玩家行动(v9.2 启用；先实现 AI 普攻)。

        ⚠️ v110 审计标注（D20）：真实 PVP 中不可达——PVP 战斗 `enemy_act` 恒 False
        （battle 刻由双方玩家轮流操作，无 AI 刻），本函数仅经 _enemy_turn 的
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
        # v138.1 阶段四件套：_phase_mod 数值修正（atk_mult/def_add/spd_add/dmg_taken_mult）——
        # 数据来自 game/data/boss_phases.py 模板（+ Boss phases[] 覆盖），由 _phase_apply 写入
        _pm = e.get("_phase_mod") or {}
        if _pm:
            _am = float(_pm.get("atk_mult", 1.0) or 1.0)
            if _am != 1.0:
                est["atk"] = int(est["atk"] * _am)
                est["matk"] = int(est["matk"] * _am)
            est["def"] = max(0, int(est["def"]) + int(_pm.get("def_add", 0) or 0))
            est["mdef"] = max(0, int(est["mdef"]) + int(_pm.get("def_add", 0) or 0))
            est["spd"] = max(1, int(est["spd"]) + int(_pm.get("spd_add", 0) or 0))
            e["_dmg_taken_mult"] = float(_pm.get("dmg_taken_mult", 1.0) or 1.0)
        # v116.1 条件触发反制：玩家低血追击(+25%) / 玩家大招反扑(+30%)——仅受击当刻生效
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
        # v140 波3.1：特效装备敌方减速（兰顿倦意/冰脉寒流——_spd_down_pct 乘算叠加）
        _wespd = float(eb.get("_spd_down_pct", 0) or 0)
        if _wespd > 0:
            est["spd"] = max(1, int(est["spd"] * (1 - min(_wespd, 0.5))))
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
        e_buffs["mark"] 计时窗口保留（由 _m_mark 写入），层数在 enemy.debuffs 随刻衰减。
        v140 S1 分档：暗蚀铭刻（shadow_etch_vuln）每层 +15%；追影者（shadow_track）
        额外 +5%（与暗蚀铭刻叠加 = 每层 +25%）；无则维持 +20%。"""
        n = int((self.enemy.get("debuffs") or {}).get("mark", {}).get("n", 0) or 0)
        if n > 0:
            _pl = getattr(self, "player", None) or {}
            _mk_effs = E.set_bonus_4(_pl.get("equipment") or {})
            _pct = 0.15 if "shadow_etch_vuln" in _mk_effs else 0.20
            if "shadow_track" in _mk_effs:
                _pct += 0.05
            return int(dmg * (1 + _pct * n))
        return dmg

    def _pet_spd(self) -> float:
        """宠物速度：读 PET_POOL 条目 spd 字段（v154 新增，独立行动节奏），兜底 50。"""
        try:
            pet = self.pet or {}
            pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
            if pdef and pdef.get("spd"):
                return float(pdef["spd"])
        except Exception:
            pass
        return 50.0

    def _pet_skill_turn(self, player: dict, logs: list) -> list:
        """24 章宠物技能：由 pet_tick 事件驱动（v154 宠物独立速度读条）。

        撕咬(atk_pct)/龙息(matk_pct)/月光祝福(heal_pct)/影袭(block) 按宠物自身
        出招/收招节奏触发（出招跑完 = 技能生效，读条命中制）；不占玩家行动、不消耗 MP。
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
        stype = pdef.get("skill_type")
        pname = pet.get("name") or pdef["name"]
        sname = pdef["skill_name"]
        line = C.pet_line(pdef["key"])  # v101.11 宠物战斗台词
        # v125.1 P2-2：按 PET_SKILL_EFFECTS 注册表分发（原 if/elif 链，数值读 PET_POOL 数据）
        handler = PET_SKILL_EFFECTS.get(stype)
        if handler:
            handler(self, player, pdef, pname, sname, line, logs)
        return logs

    def _reschedule_pet_tick(self):
        """v154 宠物独立读条：重排下次 pet_tick（周期 = 出招 + 收招，按宠物 spd 折算）。"""
        try:
            _pet_spd = self._pet_spd()
            _pt = CAST_PET_SKILL * self._ct_cost(_pet_spd)
            self._schedule(self._now + _pt, {"type": "pet_tick"})
        except Exception:
            pass

    def _pet_block_check(self, dmg: int, logs: list) -> int:
        """24 章宠物技能·影袭：每 N 刻 value 概率替主人挡一次攻击(敌方伤害结算前)。"""
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
        # v154 读条制：影袭是被动拦截（受击时概率挡刀），按时间冷却制——
        # 开战 interval 秒后才可用，之后每 interval 秒最多一次（原 _tick_no() 时刻折算在读条下失真）。
        _last = getattr(self, "_pet_block_last_at", None)
        if _last is None:
            _last = 0.0  # 开战时刻：前 interval 秒为冷却期
        if interval <= 0 or self._now - _last < interval:
            return dmg
        if random.random() < pdef.get("skill_value", 0):
            self._pet_block_last_at = self._now
            pname = pet.get("name") or pdef["name"]
            logs.append(f"🐾 {pname}的【{pdef['skill_name']}】替你挡下了这次攻击！")
            return 0
        return dmg

    def _tick_dots(self, player: dict, logs: list, force: bool = False) -> list:
        """DOT 重构（契约 §2.2 + §10.1 + §11.1）+ v138.2 异常五律：敌方持续减益统一结算。

        每次结算（每层每刻混合公式）：
          poison = (atk×0.5 + max_hp×1.5%) × n × mult
          burn   = (matk×0.4 + max_hp×1.0%) × n × mult
          bleed  = (atk×0.6 + max_hp×1.5%) × n × mult（目标当前生命 <30% 时 ×2，放血）
        随后经 敌方防守削减(_enemy_mitigate) → Boss 护盾过滤(_boss_dmg_filter)；
        结算后层数 n-1，归零消散。总抗 = min(0.95, dot_res + 适应adapt[k])；
        poison/burn 最近 2 刻未再叠层时适应 -4%（耐受消退）。
        免疫列表 immune_dots 命中类型直接移除不结算。

        v138.2 五律（docs/COMBAT_ENRICH_v138.md §二）：
          律一 阈值递增：debuffs[k].threshold 记录该类型已累积触发阈值，每次触发后
               threshold = min(threshold ×DOT_THRESHOLD_MULT, DOT_THRESHOLD_CAP)（封顶 3.0）——
               防同一构筑「无限复读同一异常」；threshold 为内部调节参数，不直接减伤。
          律二 每场上限+饱和：debuffs[k].trigger_count 累计触发次数，达 DOT_MAX_TRIGGER[k]
               置 saturated=True；饱和后控制类（freeze/stun/sleep）不再结算（Boss 永不被
               无限控死），伤害类（poison/burn/bleed/corros）照常结算（异常仍是输出轴）。
          律三 跨阶段保留：_preserve_debuffs 保留 50% 层数 + 阈值 +15%，供 _b_phase 转换时调用。
          律四 真伤独立结算：DOT_DEFS 带 true_dmg 的类型（腐蚀 corros）绕过 _enemy_mitigate
               的 def/mdef 削减，直走 _boss_dmg_filter（护盾层吸收）→ _damage_enemy，
               仍走免疫检查——异常流成为第二条独立输出轴。
          律五 饱和阈值收敛：饱和后 saturate_mult 逐次 ×DOT_SATURATE_MULT（0.8^t），
               叠入结算乘区防极端构筑把异常乘区叠爆（对应 v133 峰值红线精神）。
        旧 debuffs 无 threshold/trigger_count/saturate_mult 字段 → 默认 0/1.0，不崩。

        - 伤害类型：毒/灼烧=magi，流血=phys；腐蚀=true（真伤）
        - 灼烧走 fire 元素抗、毒不吃元素抗、流血吃物理物免
        - 结算频率：单机每玩家行动一次（_dot_pending 闸门）；副本/世界 Boss 由命令层控制
        - force=True（世界 Boss 全局多行动一次）时跳过闸门
        文案按类型区分：毒发身亡 / 灼烧致死 / 失血过多 / 腐蚀崩解；死亡后 break。
        """
        if not force:
            if not getattr(self, "_dot_pending", True):
                return logs
            self._dot_pending = False
        e = self.enemy or {}
        deb = e.get("debuffs") or {}
        # v138.2 律二（控制侧）：e_buffs 里的控制效果达上限后直接失效（防 Boss 被无限控死）。
        # 独立于 DOT 循环执行（控制类由 eb 驱动、非 debuffs；且 deb 可能为空/已消散，
        # 但控制饱和判定必须每刻都跑——放在 deb 空检查之前）。
        _iname_map = {"poison": "中毒", "burn": "灼烧", "bleed": "流血", "corros": "腐蚀"}
        _eb = e.get("buffs") or {}
        _eb2 = _eb
        for _ck in ("freeze", "stun", "sleep"):
            _cm = DOT_MAX_TRIGGER.get(_ck)
            if _cm is None or not _eb2.get(_ck):
                continue
            _cc = int(_eb2.get(f"{_ck}_trigger_count", 0) or 0)
            if _cc >= _cm:
                _eb2.pop(_ck, None)  # 达上限：控制效果直接消散
                _cn = _iname_map.get(_ck, _ck)
                logs.append(f"🛡️ 【{e.get('name', '敌人')}】对{_cn}产生了饱和抗性，控制不再生效！")
        if not deb:
            return logs
        max_hp = int(e.get("max_hp", 1) or 1)
        # v140 S1 直连消费：暗蚀（erode，hei_zhao_erode 挂）——每刻扣 1% 敌方最大生命暗伤，全额回血
        _er = deb.get("erode")
        if _er:
            _er_n = int(_er.get("n", 0) or 0)
            if _er_n > 0 and e.get("hp", 0) > 0:
                _er_dmg = max(1, int(max_hp * 0.01))
                _er_dmg = self._boss_dmg_filter(_er_dmg, player, logs, dmg_type="true", dot=True)
                self._damage_enemy(_er_dmg, logs, wake_sleep=False, target=e)
                _er_heal = _er_dmg
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + _er_heal)
                logs.append(f"🌑 暗蚀：蚀骨之力侵蚀【{e.get('name', '敌人')}】，损失 {_er_dmg} 点生命，你回复 {_er_heal} 点生命！")
                _er_n -= 1
                if _er_n <= 0:
                    deb.pop("erode", None)
                else:
                    _er["n"] = _er_n
        immune = e.get("immune_dots") or []
        # v1.1 混合公式：施放者攻击快照（防御性取数，失败按 0 处理只留生命部分）
        try:
            _st = self._player_stats(player)
            _atk = max(0, int(_st.get("atk", 0) or 0))
            _matk = max(0, int(_st.get("matk", 0) or 0))
        except Exception:
            _atk = _matk = 0
        # 每层每刻混合公式：poison=atk×0.5+max_hp×1.5% / burn=matk×0.4+max_hp×1% / bleed=atk×0.6+max_hp×1.5%
        # v125.2 B1：系数下沉 data/battle_config.py DOT_DEFS（纯数据）
        _atk_parts = {_k: _v["atk"] for _k, _v in DOT_DEFS.items()}
        _matk_parts = {_k: _v["matk"] for _k, _v in DOT_DEFS.items()}
        _hp_parts = {_k: _v["hp"] for _k, _v in DOT_DEFS.items()}
        _true_parts = {_k: bool(_v.get("true_dmg", False)) for _k, _v in DOT_DEFS.items()}
        # 律二：控制类集合（饱和后不再结算）——冻结/眩晕/睡眠
        # 注意：控制类由 eb（e_buffs）刻递减驱动，非 DOT_DEFS 类型；此处只按 DOT_MAX_TRIGGER
        # 白名单做饱和判定（控制类达上限后不再结算其 eb 效果，层数仍保留供计数）。
        # 控制侧饱和已在函数开头（deb 空检查前）执行，此处 _ctrl 仅用于伤害类/控制类文案分流。
        _ctrl = ("freeze", "stun", "sleep")
        _iname_map = {"poison": "中毒", "burn": "灼烧", "bleed": "流血", "corros": "腐蚀"}
        _kname_map = {"poison": "毒", "burn": "灼烧", "bleed": "流血", "corros": "腐蚀"}
        _icon_map = {"poison": "☠️", "burn": "🔥", "bleed": "🩸", "corros": "🧪"}
        for k in DOT_DEFS:
            d = deb.get(k)
            if not d:
                continue
            n = int(d.get("n", 0) or 0)
            if n <= 0:
                deb.pop(k, None)
                continue
            _iname = _iname_map.get(k, k)
            # 免疫：命中该类型时直接移除该层并提示免疫，不结算伤害
            if k in immune:
                deb.pop(k, None)
                logs.append(f"🛡️ 【{e.get('name', '敌人')}】免疫{_iname}，减益消散了！")
                continue
            # v138.2 律二：饱和检查——控制类达上限后不再结算（伤害类照常）
            _max_trig = DOT_MAX_TRIGGER.get(k)
            _saturated = bool(d.get("saturated", False)) or (
                _max_trig is not None and int(d.get("trigger_count", 0) or 0) >= _max_trig)
            if _saturated and k in _ctrl:
                if not d.get("saturated"):
                    d["saturated"] = True
                    logs.append(f"🛡️ 【{e.get('name', '敌人')}】对{_iname}产生了饱和抗性，控制不再生效！")
                continue
            if _saturated and not d.get("saturated"):
                d["saturated"] = True
                logs.append(f"⚗️ 【{e.get('name', '敌人')}】对{'腐蚀' if k == 'corros' else _iname}的异常积累已饱和，威力逐渐衰减！")
            mult = float(d.get("mult", 1.0) or 1.0)
            # v138.2 律五：饱和阈值收敛——饱和后 saturate_mult 逐次 ×0.8（0.8^t 指数衰减）
            _sat_mult = float(d.get("saturate_mult", 1.0) or 1.0)
            if _saturated and _sat_mult < 1.0:
                mult *= _sat_mult
                _sat_tag = f"(饱和×{_sat_mult:.2f})"
            else:
                _sat_tag = ""
            # v1.2 总抗：基础抗性 + 减益适应（cap 0.95）；真伤分支（律四）不吃总抗
            base_res = float(e.get("dot_res", 0) or 0)
            adapt_v = float((e.get("adapt") or {}).get(k, 0.0) or 0.0)
            res = min(DOT_RESIST_CAP, base_res + adapt_v)
            # v1.1 混合公式：每层 = (攻击系数 + 最大生命小百分比) × 层数 × 被动倍率 × (1 - 总抗)
            # v156 分类重构：DOT_DEFS 带 type（flat/pct/hybrid）——
            #   pct/hybrid 的 hp（百分比）部分在 Boss/精英战 × DOT_BOSS_PCT_MULT（0.5），
            #   且单层每刻 ≤ max_hp × DOT_PCT_CAP（1%）——防"百分比 DOT 无脑过 Boss"。
            atk_part = _atk * _atk_parts[k] + _matk * _matk_parts[k]
            _dot_type = (DOT_DEFS.get(k) or {}).get("type", "flat")
            _hp_part = max_hp * _hp_parts[k]
            if _hp_part > 0 and _dot_type in ("pct", "hybrid"):
                # Boss/精英：百分比部分打折（防无脑过 Boss）
                if e.get("is_boss") or e.get("role") == "boss" or e.get("is_elite"):
                    _hp_part *= DOT_BOSS_PCT_MULT
                # 单层每刻上限（防极端叠层；对普通怪也生效——上限本身就是 1%）
                _cap_v = max_hp * DOT_PCT_CAP
                _hp_part = min(_hp_part, _cap_v)
            hp_part = _hp_part
            p = int((atk_part + hp_part) * n * mult * (1 - res))
            # v138.2 律四：真伤分支——绕过 _enemy_mitigate 的 def/mdef 削减，仍走免疫检查 +
            # Boss 护盾过滤（护盾层吸收）→ _damage_enemy。腐蚀类 = 独立第二条输出轴。
            # 注意：总抗（dot_res/适应）仍参与公式——真伤只豁免防御削减，不豁免目标异常抗性。
            if _true_parts.get(k):
                dt = "true"
                p = self._boss_dmg_filter(p, player, logs, dmg_type="true", dot=True)
            else:
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
            # v138.2 律一：阈值递增——每次触发后 threshold ×1.3（封顶 3.0），防无限复读
            _thr = float(d.get("threshold", 0.0) or 0.0)
            if _thr <= 0.0:
                _thr = 1.0  # 首触基准
            _thr = min(DOT_THRESHOLD_CAP, _thr * DOT_THRESHOLD_MULT)
            d["threshold"] = _thr
            # v138.2 律二：触发计数 +1，达上限置饱和标记
            d["trigger_count"] = int(d.get("trigger_count", 0) or 0) + 1
            _tc = d["trigger_count"]
            if _max_trig is not None and _tc >= _max_trig:
                d["saturated"] = True
                if k not in _ctrl:
                    logs.append(f"⚗️ 【{e.get('name', '敌人')}】的{'腐蚀' if k == 'corros' else _iname}积累已达上限，进入饱和！")
            kname = _kname_map.get(k, k)
            _mult_tag = f"(强化×{mult:.1f})" if mult != 1.0 else ""
            _icon = _icon_map.get(k, "💥")
            logs.append(f"{_icon} 【{e.get('name', '敌人')}】{kname}发作，损失 {p} 点生命！(剩余 {n - 1} 层){_mult_tag}{_bleed_tag}{_sat_tag}")
            n -= 1
            if n <= 0:
                deb.pop(k, None)
                logs.append(f"💨 【{e.get('name', '敌人')}】的{kname}消散了！")
            else:
                d["n"] = n
            # v138.2 律五：饱和阈值收敛——饱和标记置位后，后续触发逐次 ×0.8（0.8^t 指数衰减，
            # 防极端构筑把异常乘区叠爆；对应 v133 峰值红线精神）。置位当次不衰减（饱和前已结算），
            # 从下一次触发起逐次收敛。
            if d.get("saturated") and k not in _ctrl:
                _sm = float(d.get("saturate_mult", 1.0) or 1.0)
                d["saturate_mult"] = _sm * DOT_SATURATE_MULT
            # v1.2 适应回落：poison/burn 最近 2 个行动轮次未再叠层 → 该类型适应 -4%（耐受消退）
            # v125.2 B1：步长查表 DOT_ADAPT_DECAY_STEP
            # v152 时刻制：last_round → last_tick（行动轮次 _tick_no()）
            if k in ("poison", "burn"):
                _last = int(d.get("last_tick", d.get("last_round", 0)) or 0)
                if _last > 0 and self._tick_no() - _last >= 2:
                    _am = e.setdefault("adapt", {})
                    _am[k] = max(0.0, float(_am.get(k, 0.0) or 0.0) - DOT_ADAPT_DECAY_STEP)
            if self._enemy_dead():
                self.result = "victory"
                death_text = ("毒发身亡" if k == "poison" else "灼烧致死" if k == "burn"
                              else "失血过多" if k == "bleed" else "腐蚀崩解")
                logs.append(f"🎉 你击败了【{e.get('name', '敌人')}】！({death_text})")
                break
        # v1.3 标记层与 dot 同生命周期：每刻结算后 n-1，归零移除（与 e_buffs["mark"] 2 刻计时同步）
        _mk = deb.get("mark")
        if _mk:
            _mn = int(_mk.get("n", 0) or 0) - 1
            if _mn <= 0:
                deb.pop("mark", None)
            else:
                _mk["n"] = _mn
        return logs

    def _preserve_debuffs(self, logs: list) -> None:
        """v138.2 律三：跨阶段保留（进度遗产）——阶段转换时保留一半异常进度。

        - 层数保留 DOT_PRESERVE_PCT（50%，向下取整，至少保留 1 层——首层不白费）
        - 阈值 ×(1+DOT_PRESERVE_THRESHOLD_BONUS)（新阶段对同一异常略微更抗，仍封顶 DOT_THRESHOLD_CAP）
        - trigger_count / saturated / saturate_mult 保留原值（每场上限是战斗级约束，跨阶段不清零，
          防止「转阶段重置上限」被利用成无限叠异常）
        调用点：_b_phase（battle_mech.py BOSS_MECHS["phase"]）阶段转换处（主 agent 收尾接线）。
        """
        e = self.enemy or {}
        deb = e.get("debuffs") or {}
        if not deb:
            return
        for k, d in list(deb.items()):
            if not isinstance(d, dict):
                continue
            if k == "mark":
                # 标记是伤害易伤窗口，非异常积蓄，跨阶段不保留（直接清除）
                deb.pop(k, None)
                continue
            n = int(d.get("n", 0) or 0)
            if n > 0:
                keep = max(1, int(n * DOT_PRESERVE_PCT))  # 50%，向下取整，至少 1 层
                d["n"] = keep
            _thr = float(d.get("threshold", 0.0) or 0.0)
            if _thr > 0.0:
                d["threshold"] = min(DOT_THRESHOLD_CAP, _thr * (1.0 + DOT_PRESERVE_THRESHOLD_BONUS))
        logs.append(f"🌀 【{e.get('name', '敌人')}】蜕变了，但残留的异常仍在侵蚀它的躯体！（保留一半层数）")

    def _phase_apply(self, e: dict, phase_cfg: dict, npc: int, logs: list) -> None:
        """v138.1 阶段四件套应用器（battle_mech._b_phase 阶段转换时调用）。

        借鉴《云海猎团》03 章 M3.2：每阶段配「数值变化/行为变化/退出条件/反制窗口」。
        数据来源 game/data/boss_phases.py BOSS_PHASE_TEMPLATES（+ Boss phases[] 内联覆盖）。
        旧 phases（只有 min/add_skills/script）不调用本方法，维持旧行为。

        - 数值变化：atk_mult / def_add / spd_add / dmg_taken_mult（承伤倍率，>1=更脆，对应疲态核心件外露）
        - 行为变化：add_skills（换招表，幂等追加）/ freq_mult（行动频率倍率）/ ult_every（每 N 刻大招）
        - 退出条件：exit_turns（刻数）/ exit_dmg（累计承伤）写入 e._phase_exit（供 _b_phase 轮询）
        - 反制窗口：counter 写入 e._phase_counter（战报展示，引导玩家解题）
        - 演出：icon / enter_line / warn_line
        """
        if not phase_cfg:
            return
        # ---- 数值变化 ----
        _am = float(phase_cfg.get("atk_mult", 1.0) or 1.0)
        _da = int(phase_cfg.get("def_add", 0) or 0)
        _sa = int(phase_cfg.get("spd_add", 0) or 0)
        _dtm = float(phase_cfg.get("dmg_taken_mult", 1.0) or 1.0)
        # 应用到敌方 stats（存 e 上的阶段修正，_enemy_stats 聚合时读取）
        _pm = e.setdefault("_phase_mod", {})
        _pm["atk_mult"] = _am
        _pm["def_add"] = _da
        _pm["spd_add"] = _sa
        _pm["dmg_taken_mult"] = _dtm
        # 承伤倍率直接写 e._dmg_taken_mult（_boss_dmg_filter 读取，无需先经 _enemy_stats）
        e["_dmg_taken_mult"] = _dtm
        # ---- 行为变化：换招表（幂等追加）----
        for s in (phase_cfg.get("add_skills") or []):
            if s and s not in e.get("skills", []):
                e["skills"] = list(e.get("skills", [])) + [s]
        e["_phase_ult_every"] = phase_cfg.get("ult_every")          # 每 N 刻大招（None=无）
        e["_phase_freq_mult"] = float(phase_cfg.get("freq_mult", 1.0) or 1.0)  # 行动频率倍率
        # ---- 退出条件 ----
        e["_phase_exit"] = {
            "turns": phase_cfg.get("exit_turns"),
            "dmg": phase_cfg.get("exit_dmg"),
            # v152 时刻制：entered_at = 行动轮次（_tick_no()）
            "entered_at": self._tick_no(),
        }
        # ---- 反制窗口 ----
        e["_phase_counter"] = phase_cfg.get("counter")
        # ---- 演出 ----
        icon = phase_cfg.get("icon", "🔥")
        name = phase_cfg.get("name", f"第{npc + 1}阶段")
        enter = phase_cfg.get("enter_line") or f"力量再度攀升！"
        logs.append(f"{icon}【{e.get('name', '敌人')}】{name}！{enter}")
        if phase_cfg.get("warn_line"):
            logs.append(f"⚠️ {phase_cfg['warn_line']}")
        # 阶段演出刻：进入新阶段该刻 Boss 不行动（呼吸点，v116.1 既有语义）
        self._phase_skip_act = True

    def _phase_counter_line(self, e: dict) -> str:
        """v138.1 反制窗口文案（战报展示，引导玩家解题）。无则返回空串。"""
        _c = (e or {}).get("_phase_counter")
        return f"💡 反制：{_c}" if _c else ""

    def _tailwind_regen_bonus(self, player: dict) -> int:
        """v130.2d 疾风余韵：上刻结束时精力 ≥80 → 本刻精力自然回复 +10（词条 effect.regen）。
        跨刻状态由 _end_round 记录 _tailwind_prev_energy（每战初始化 None，随战斗序列化）。"""
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
        """刻开始：持续伤害结算 + v10 套装每刻回复"""
        logs = []
        # DOT 重构（契约 §2.1/§2.2）：敌方持续减益（毒/灼烧/流血）统一由 _tick_dots 结算。
        # _tick_dots 内部持有 _dot_pending 闸门——单机探索怪（btype=monster）与 PVP 每次玩家行动=一刻，
        # 刻开始复位闸门 → 每行动结算一次（与现状频率一致）；副本（instance）每轮结算一次的
        # 闸门由 from_state 按 st["dot_pending"] 恢复，世界 Boss（worldboss）由 combat 层 force 结算，
        # 故此两模式不在此复位。
        if self.btype in ("monster", "pvp"):
            self._dot_pending = True
        # 原地追加（_tick_dots 向传入 logs 追加文案并返回同一列表，勿用 += 以免二次自拼接）
        self._tick_dots(player, logs)
        # v151 破绽断链修复（引擎差距报告 P0）：turn_start_bars 此前从未被调用——
        # 拳师破绽条（shaken）的每刻衰减 4/免疫期递减实际不跑。刻开始统一衰减+触发检查。
        try:
            from .core.battle_bars import turn_start_bars
            _trig = turn_start_bars(self.enemy, logs) or []
            for _bk in _trig:
                # 触发效果：skip_turn → 敌方跳过下刻行动（由 _enemy_turn 消费 immune_turns）
                _bd = None
                from .core.battle_bars import bar_def
                _bd = bar_def(_bk) or {}
                if (_bd.get("trigger_effect") or "") == "skip_turn":
                    logs.append(f"💢 破绽触发！敌方即将失去行动！")
        except Exception:
            pass
        # 阶段八：词条刻开始回复（回春/冥想/晨曦祝福）
        self._affix_turn_start(player, logs)
        self._food_turn_start(player, logs)
        # v140 波3.1：特效装备刻开始（铁卫意志/晨曦微光/不灭微光/死亡之舞缓伤/岁月流转）
        try:
            from .core.weapon_effects import proc as _we_proc
            _we_proc(self, player, "turn_start", {}, logs)
        except Exception:
            pass
        # v130.2c 暗夜圣典 2 件：场上亡灵≥1 时 悼咏积攒 +1（刻开始）
        self._set_res_proc(player, "undead_on_field", logs)
        # v130.2f 亡灵祭仪（暗影神谕·悼咏线）：场上每只存活亡灵 刻初 悼咏 +1
        # （core_resources.py cls_hymn 注释承诺「最多 2 只生效」；上限 10/满溢转盾由 _res_gain_class 处理）
        _crd = E.core_resource_def(player.get("class_name", ""))
        if _crd and _crd.get("key") == "canticle":
            _ud_n = self._undead_count()
            if _ud_n > 0:
                _ud_g = min(_ud_n, 2)
                _ud_before = int(self.resources.get("canticle", 0) or 0)
                _ud_now = self._res_gain_class(player.get("class_name", ""), "canticle", _ud_g)
                if _ud_now > _ud_before:  # 真实增量判定（满资源不再误报，同 _set_res_proc 口径）
                    logs.append(f"🕯️ 亡灵祭仪：{_ud_n} 只亡灵在场，悼咏 +{_ud_g}（当前 {_ud_now}/10）")
        # 圣光/永恒套：每刻开始回复生命
        for eff in E.set_bonus_4(player.get("equipment", {})):
            if eff in ("regen", "regen_strong") and player.get("hp", 0) < player.get("max_hp", 1):
                pct = 0.05 if eff == "regen" else 0.08
                heal = int(player.get("max_hp", player.get("hp", 1)) * pct)
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"✨ 套装祝福生效，你回复了 {heal} 点生命！")
                break
        # v140 S1 直连消费：圣堂领域（holy_field_heal）/ 神恩爆发（divine_grace_burst）/ 壁立千仞（hu_xiao_barrier）
        _s4 = E.set_bonus_4(player.get("equipment", {}))
        if "holy_field_heal" in _s4:
            _hfh = (self._set_eff(player, "holy_field_heal", 4) or {})
            _hfh_p = (_hfh or {}).get("params") or {}
            _low = float(_hfh_p.get("cond_hp_lt", _hfh.get("low_pct", 0.50)) or 0.50)
            _hl = float(_hfh_p.get("heal_low_pct", _hfh.get("heal_low", 0.06)) or 0.06)
            _hh = float(_hfh_p.get("heal_high_pct", _hfh.get("heal_high", 0.03)) or 0.03)
            _mx_hp = player.get("max_hp", player.get("hp", 1))
            if player.get("hp", 0) < _mx_hp:
                _pct = _hl if player.get("hp", 0) / max(1, _mx_hp) < _low else _hh
                _hf_heal = int(_mx_hp * _pct)
                player["hp"] = min(_mx_hp, player.get("hp", 0) + _hf_heal)
                logs.append(f"⛪ 圣堂领域：圣光庇护，你回复了 {_hf_heal} 点生命！")
        if "divine_grace_burst" in _s4:
            _dgb_eff = (self._set_eff(player, "divine_grace_burst", 4) or {})
            _dgb_p = (_dgb_eff or {}).get("params") or {}
            _mx_hp2 = player.get("max_hp", player.get("hp", 1))
            _dg_heal = int(_mx_hp2 * float(_dgb_p.get("heal_pct", 0.05)))
            if player.get("hp", 0) < _mx_hp2:
                player["hp"] = min(_mx_hp2, player.get("hp", 0) + _dg_heal)
                logs.append(f"☀️ 神恩爆发：神恩涌动，你回复了 {_dg_heal} 点生命！")
            if not (self.p_eff or {}).get("divine_burst_used") and player.get("hp", 0) / max(1, _mx_hp2) < float(_dgb_p.get("low_hp_lt", 0.30)):
                _dg_extra = int(_mx_hp2 * float(_dgb_p.get("low_extra_pct", 0.15)))
                player["hp"] = min(_mx_hp2, player.get("hp", 0) + _dg_extra)
                self.p_eff["divine_burst_used"] = True
                logs.append(f"☀️ 神恩爆发·濒危：圣辉倾泻，额外回复 {_dg_extra} 点生命！（每场 1 次）")
        if "hu_xiao_barrier" in _s4:
            _hxb_eff = (self._set_eff(player, "hu_xiao_barrier", 4) or {})
            _hxb_p = (_hxb_eff or {}).get("params") or {}
            self._add_shield("hu_xiao_barrier", int(player.get("max_hp", player.get("hp", 1)) * float(_hxb_p.get("shield_pct", 0.03))), int(_hxb_p.get("shield_turns", 1)))
            logs.append("🧱 壁立千仞：千仞壁垒立于身前！")
        # v104 M07 修复 P1：星尘套 5 件——夜间每刻回蓝 5%（10 章五节；夜间 = 19:00-06:00 服务器本地时间）
        if "星尘" in "|".join(self._set_bonus_5(player)) and player.get("mp", 0) < player.get("max_mp", 1):
            _hour = time.localtime().tm_hour
            if _hour >= 19 or _hour < 6:
                gain = int(player.get("max_mp", player.get("mp", 1)) * 0.05)
                player["mp"] = min(player.get("max_mp", player.get("mp", 1)), player.get("mp", 0) + gain)
                logs.append(f"🌙 星尘祝福：夜风拂过，你回复了 {gain} 点魔力！({player['mp']}/{player.get('max_mp', '?')})")
        # v34 符文·治愈：每刻回复 x% 生命
        regen_lvl = self._enchant_lvl(self._enchant_effects(player), "regen")
        if regen_lvl and player.get("hp", 0) < player.get("max_hp", 1):
            heal = int(player.get("max_hp", player.get("hp", 1)) * C.rune_value("regen", regen_lvl))
            player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
            logs.append(f"✨ 符文治愈生效，你回复了 {heal} 点生命！")
        # v109.2 P2-9：气力调和每刻回血 2%（proc turn_heal，原按技能名硬编码——v109.1 改名即断链事故源）
        for _pn, _ps in self._passive_map(player)["proc"].get("turn_heal", []):
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * float(_ps.get("pct", 0.02)))
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"🍃 {_pn}生效，你回复了 {heal} 点生命！")
            break
        # v104 R3 P1-1：生命之泉——全队每刻回血 5%（单人战斗=自身，副本由 instance 广播）
        for _pn, _ps in self._passive_map(player)["proc"].get("team_regen", []):
            if player.get("hp", 0) < player.get("max_hp", 1):
                heal = int(player.get("max_hp", player.get("hp", 1)) * float(_ps.get("mult", 0.05)))
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + heal)
                logs.append(f"💧 {_pn}：生命之泉涌动，你回复了 {heal} 点生命！")
            break
        # v109.2 P2-9：奥术直觉/符文刻印 每刻自动充能（proc arcane_regen / stat spellblade_regen，
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
        # v2.0 核心资源：刻回复（游侠精力 +25/刻）
        cls = player.get("class_name", "")
        rd = E.core_resource_def(cls)
        if rd and rd.get("regen", 0) > 0:
            k = rd["key"]
            old = int(self.resources.get(k, 0) or 0)
            # v130.2c 词条上限：自然回走 _res_gain（盈满背囊上限 +10/20 生效，行为与旧路径零差异）
            new = self._res_gain(player, k, int(rd.get("regen", 0) or 0))
            if new > old:
                logs.append(f"🍃 {rd['name']}回复 {new - old} 点({new}/{self._res_max(player, k)})")
            # v130.2d 疾风余韵：上刻结束时精力 ≥80 → 本刻自然回复 +10（读词条 effect.regen）
            if k == "energy":
                _tw_bonus = self._tailwind_regen_bonus(player)
                if _tw_bonus > 0:
                    _old2 = int(self.resources.get(k, 0) or 0)
                    _new2 = self._res_gain(player, k, _tw_bonus)
                    if _new2 > _old2:
                        logs.append(f"🌈 疾风余韵：上刻精力满弦，本刻回复 +{_new2 - _old2} 点{rd['name']}！")
        # v130.2 资源增幅：自然回触发（迅捷之核 本刻精力额外 +30，P0-1 消费端）
        _amp_pt = self._amp_resource(player, "regen")
        if _amp_pt:
            logs.append(f"⚡ 迅捷之核：自然回复额外资源 +{_amp_pt}！")
        # v153 §4（C-18）：牧师信念负载——每刻 −0.7 衰减 + 过载触发（满 10 清零→全队回复 + 力竭）
        _crd_f = E.core_resource_def(player.get("class_name", ""))
        if _crd_f and _crd_f.get("key") == "faith" and _crd_f.get("decay_per_tick"):
            _f_before = float(self.resources.get("faith", 0) or 0)
            if _f_before >= float(_crd_f.get("max", 10)):
                # 过载触发：清零 → 全队回复
                _ov_pct = float(_crd_f.get("overload_heal_pct", 0.015) or 0.015)
                _ov_heal = int(self.player.get("max_hp", 1) * _ov_pct * _f_before)
                self.resources["faith"] = 0
                logs.append(f"⚡ 信念过载！信仰之力迸发，全队回复 {_ov_heal} 点生命！")
                # 力竭：后续治疗 ×0.5，信念不再增加（6 刻）
                self.p_buffs["faith_exhausted"] = 6
                if self.player.get("hp", 0) < self.player.get("max_hp", 1):
                    self.player["hp"] = min(self.player.get("max_hp", 1), self.player.get("hp", 0) + _ov_heal)
                    logs.append(f"✨ 过载回响：你回复了 {_ov_heal} 点生命！")
            elif _f_before > 0:
                _f_decay = float(_crd_f.get("decay_per_tick", 0.7) or 0.7)
                # 力竭中信念不增加（但仍衰减）
                self.resources["faith"] = max(0.0, _f_before - _f_decay)
                if float(self.resources["faith"]) < _f_before:
                    logs.append(f"🕯️ 信念衰减：{_f_before:.1f} → {float(self.resources['faith']):.1f}")
            # 力竭计数递减
            if self.p_buffs.get("faith_exhausted"):
                self.p_buffs["faith_exhausted"] = int(self.p_buffs["faith_exhausted"]) - 1
        # v130.2 歌者回声驻留：每层刻初始全队恢复 6 体力（priest_转职.md §3.0）
        echo_n = self._echo_layers()
        if echo_n > 0:
            _heal_e = int(ECHO_CFG.get("heal_per_layer", 6) or 6) * echo_n
            if echo_n >= int(ECHO_CFG.get("max_layers", 3) or 3):
                _heal_e *= 2  # 策划案 12 章 5.1.1：回声满层时每层恢复翻倍（3 层=36/刻）
            if player.get("hp", 0) < player.get("max_hp", 1):
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + _heal_e)
                logs.append(f"🎵 回声余韵：全队恢复 {_heal_e} 点体力({echo_n} 层)")
            for _ally in (self.allies or []):
                if isinstance(_ally, dict) and _ally.get("hp", 0) < _ally.get("max_hp", 1):
                    _ally["hp"] = min(_ally.get("max_hp", _ally.get("hp", 1)), _ally.get("hp", 0) + _heal_e)
        # ---- v139 职业融合：刻开始状态机（dual_form 维护 / vent 排气 / focus 计时）----
        from .core.battle_modes import (
            dual_form_def, dual_form_state, dual_form_active, dual_form_tick,
            dual_form_force_return, dual_form_exit, vent_def, vent_should_trigger,
            vent_apply, focus_def, focus_state, focus_tick,
        )
        # dual_form：alt 形态每刻维护成本（从资源扣）
        if dual_form_active(player):
            _dfd = dual_form_def(player)
            _df_tick = dual_form_tick(player, logs)
            for _item in _df_tick:
                if isinstance(_item, dict) and "maintain_cost" in _item:
                    _df_key = _dfd.get("key", "rage")
                    _mc = float(_item["maintain_cost"])  # v153：支持浮点维持（狂暴每刻 −0.6）
                    _cur = float(self.resources.get(_df_key, 0) or 0)
                    if _cur >= _mc:
                        self.resources[_df_key] = _cur - _mc
                        logs.append(f"⚡【{_dfd.get('form', '形态')}】维持消耗 {_mc}（{self.resources.get(_df_key, 0)}）")
                    # 强制回基础形态
                    if dual_form_force_return(player, int(self.resources.get(_df_key, 0) or 0)):
                        dual_form_exit(player, logs)
                        logs.append("⚠️ 力量不支，被迫回到常态！")
        # vent：满值强制排气（游侠精力 100 / 星语者猎印 5）
        _vd = vent_def(player)
        if _vd:
            _v_key = _vd.get("key", "energy")
            _v_cur = int(self.resources.get(_v_key, 0) or 0)
            if vent_should_trigger(player, _v_cur):
                _vr = vent_apply(player, logs)
                self.resources[_v_key] = int(_vr.get("reset_to", 0) or 0)
                logs.append(f"💨 气息满溢，自动排气！(重置为 {_vr.get('reset_to', 0)})")
        # focus：专注计时（额外资源 + 超时退出）
        _fd = focus_def(player)
        if _fd:
            _ft = focus_tick(player, logs)
            if _ft.get("gain"):
                _f_key = _fd.get("key", "element")
                _f_gain = int(_ft["gain"])
                # 专注额外资源（走 _res_gain 带上限）
                _f_before = int(self.resources.get(_f_key, 0) or 0)
                self.resources[_f_key] = self._res_gain(player, _f_key, _f_gain)
                if int(self.resources.get(_f_key, 0) or 0) > _f_before:
                    logs.append(f"🧘 专注积累 +{_f_gain}（{self.resources.get(_f_key, 0)}）")
        return logs

    def _end_round(self, dt: float | None = None):
        """v152 时刻制：推进战斗时刻（替代旧"刻结束递减"）。
        兼容壳：保留 _end_round 函数名（外部大量调用），内部 = _advance_time(dt)。
        dt 缺省 = ACT_TICK（一次标准行动间隔）。真正的时间流逝由 _advance_time 处理。
        v152 彻底化：不再有"每刻 -1"，一切按绝对时刻 expire_at/ready_at 到期。"""
        self._advance_time(dt if dt is not None else (ACT_TICK or 2.0))

    def _advance_time(self, dt: float):
        """v152 核心：推进战斗时刻 dt（正数），处理期间到期的所有计时项。
        - buff（int 刻值 → 兼容旧档转 expire_at；dict bar 由 battle_bars 自行衰减）
        - 护盾 expire_at、技能 CD ready_at、特效装备 CD、资源增幅 turns_left、弱点击破/连携
        - 保留控制类（stun/freeze）不在此到期（行动级消费）；一次性 buff（next_atk_up 等）不在此到期（攻击消费）
        """
        if not dt or dt <= 0:
            return
        _now = self._now
        self._now = _now + float(dt)
        # ---- buff 到期检查（p_buffs / e_buffs）----
        for tbl in (self.p_buffs, self.e_buffs):
            for k in list(tbl):
                v = tbl[k]
                # 控制类 buff：行动级消费，不在时刻递减（与旧语义一致）
                if k in ("stun", "freeze"):
                    continue
                # 元素印记：层数标记，触发反应清除
                if k in ("fire_mark", "ice_mark", "thunder_mark"):
                    continue
                # 一次性 buff：攻击消费，不在时刻递减
                if k in ("next_atk_up", "buff_phys_next", "stealth"):
                    continue
                # reduce_all/shield：特殊语义，不按 int 递减
                if k in ("reduce_all", "shield"):
                    continue
                # bar 状态（dict）：由 battle_bars 自行衰减
                if isinstance(v, dict):
                    continue
                # 防御型 buff（受击计数）：由 _damage_player 受击递减
                if tbl is self.p_buffs and k in (getattr(self, "_p_buff_hits", {}) or {}):
                    continue
                # v152：buff 值兼容三种形态——expire_at(时刻)、turns(刻 int)、原始 int(视为剩余刻)
                if isinstance(v, dict) and "expire_at" in v:
                    if self._now >= float(v["expire_at"]):
                        del tbl[k]
                    continue
                if isinstance(v, dict) and "turns" in v:
                    if self._now >= float(v["turns"]) * (ACT_TICK or 2.0):
                        del tbl[k]
                    continue
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    # 旧 int = 剩余刻数 → 换算时刻到期
                    if self._now >= float(v) * (ACT_TICK or 2.0):
                        del tbl[k]
        # v113.1：团队减伤 buff 独立计时（reduce_all 的到期）
        if self.p_buffs.get("reduce_all") is not None and self._now >= float(getattr(self, "_reduce_all_left", 1) or 1) * (ACT_TICK or 2.0):
            self.p_buffs.pop("reduce_all", None)
            self._reduce_all_left = 0
        # v101.28d 护盾到期：各来源独立 expire_at
        for key in list(self.p_shields):
            sh = self.p_shields[key]
            # 兼容旧 {"turns"} → expire_at
            if "turns" in sh and "expire_at" not in sh:
                sh["expire_at"] = self._now + max(1, int(sh.get("turns", 1))) * (ACT_TICK or 2.0)
                sh.pop("turns", None)
            if self._now >= float(sh.get("expire_at", 0) or 0):
                del self.p_shields[key]
        # v130.2 资源增幅 turns_left 衰减（hits 制由 _amp_resource 出手命中逐次扣）→ 到期清
        _amp_m = (self.p_eff or {}).get("amps")
        if _amp_m:
            for _ak in list(_amp_m):
                _a = _amp_m[_ak]
                if not isinstance(_a, dict):
                    continue
                if int(_a.get("turns_left", 0) or 0) > 0:
                    # 换算：turns_left 刻 → 到期时刻
                    if self._now >= float(_a.get("turns_left", 0)) * (ACT_TICK or 2.0):
                        _a["turns_left"] = 0
                if int(_a.get("turns_left", 0) or 0) <= 0 and int(_a.get("hits_left", 0) or 0) <= 0:
                    del _amp_m[_ak]
            if not _amp_m:
                self.p_eff.pop("amps", None)
        # v140 波3.2：弱点击破/连携增幅 时刻到期
        for _pkey in ("vuln", "dot_amp"):
            _pe = (self.p_eff or {}).get(_pkey)
            if isinstance(_pe, dict) and int(_pe.get("turns_left", 0) or 0) > 0:
                if self._now >= float(_pe.get("turns_left", 0)) * (ACT_TICK or 2.0):
                    self.p_eff.pop(_pkey, None)
        # CD / 特效 CD / 星辉壁垒（惰性清除）
        self._tick_cooldowns()
        # v130.2d 疾风余韵：时刻推进后记录精力（供下一次判定自然回复）
        self._tailwind_prev_energy = int(self.resources.get("energy", 0) or 0)
        # v130.2f2 满溢转盾冷却：时刻制下按冷却时间重置（简化：每次推进后允许再次转盾，
        # 真正的"每刻限 1 次"语义由 _overflow_shield_cd 在转盾瞬间置位并靠 CD 控制频率）
        self._overflow_shield_cd = False

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
        # v136 等级压制：玩家 vs 怪物等级差伤害修正（PVE 生效，PVP 不压；按目标自身等级实时算，
        # 多目标阵列每怪等级不同也能正确压制）。双向曲线（鱼鱼拍板：增伤不封顶，曲线自然延伸）：
        #   低打高：低 1-3 级 ×0.95/级，低 4+ 级 ×0.90/级（指数曲线，封顶 ×0.30 防归零）
        #   高打低：每高 1 级 ×1.02 连乘（指数曲线，不封顶——等级越高碾压越强）
        if self.btype != "pvp" and self.player and target.get("lv"):
            try:
                _plv = int(self.player.get("level", 0) or 0)
                _diff = int(target.get("lv", 0) or 0) - _plv
                if _diff > 0:
                    _mult = 1.0
                    for _i in range(min(_diff, 10)):
                        _mult *= (0.95 if _i < 3 else 0.90)
                    dmg = max(1, int(dmg * max(0.30, _mult)))
                elif _diff < 0:
                    dmg = max(1, int(dmg * (1.02 ** min(-_diff, 50))))
            except Exception:
                pass
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
        atk = max(0, int(st.get("atk", 50) * float(tmpl.get("atk_ratio", 0) or 0) * (1 + sp)))
        df = max(2, int(st.get("def", 20) * float(tmpl["def_ratio"]) * (1 + sp)))
        self.summons.append({"tid": tid, "name": tmpl["name"], "icon": tmpl.get("icon", ""),
                             "hp": hp, "max_hp": hp, "atk": atk, "def": df,
                             "dmg_type": tmpl.get("dmg_type", "phys"),
                             "rank": int(tmpl.get("rank", 1) or 1),
                             "reach": int(tmpl.get("reach", 1) or 1),
                             # v151 召唤物语义：纯挡刀吸收一次 / 全队攻击光环 / 吃 AOE
                             "absorb_once": bool(tmpl.get("absorb_once", False)),
                             "aura_atk_all": float(tmpl.get("aura_atk_all", 0) or 0),
                             "eats_aoe": bool(tmpl.get("eats_aoe", False))})
        # v151 古树光环：常驻全队攻击 +30%（生成时挂 p_buffs，直到召唤物死亡）
        _aura = float(tmpl.get("aura_atk_all", 0) or 0)
        if _aura > 0 and self.player:
            _cur = float(self.p_buffs.get("atk_up_all", 0) or 0)
            self.p_buffs["atk_up_all"] = max(_cur, _aura)
            logs.append(f"🌳 古树光环：全队攻击＋{int(_aura * 100)}%！")
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
            # v151：纯挡刀召唤物（atk=0，如藤蔓守卫）不普攻
            if int(s.get("atk", 0) or 0) <= 0:
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
            # v130.7 意见#17：敌方死亡单位快照进 killed_enemies——unit（本次击杀）
            # 与 compact 返回的阵亡单位（AOE 同时击杀多只）全部记录；同单位只记一次
            for _u in [unit] + removed:
                if _u in self.killed_enemies:
                    continue
                self.killed_enemies.append(dict(_u))
            # v140 波3.1：特效装备击杀后（暮裂潜行——击杀进入潜行，每场 1 次）
            if self.player:
                try:
                    from .core.weapon_effects import proc as _we_proc
                    _we_proc(self, self.player, "kill", {}, getattr(self, "_pending_dmg_lines", None) or [])
                except Exception:
                    pass
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
        # v151：纯挡刀召唤物（absorb_once）吸收 1 次单体后消失（v151 §7 藤蔓守卫）
        if s.get("absorb_once"):
            logs.append(f"🌿 {s['name']} 完成守护，化作碎屑消散……")
            self.summons.remove(s)
            return 0
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
        # 无声被动——闪避率＋30%：乘算并入
        for _pn, _ps in self._passive_map(player)["proc"].get("dodge_up", []):
            dodge = 1 - (1 - dodge) * (1 - float(_ps.get("mult", 0.3)))
        # 影步药剂 15%：并入乘算（不再独立判定——旧实现独立判定绕过 40% 上限，基础 40%+药水可达 49.7%）
        if self.p_buffs.get("dodge_pot"):
            dodge = 1 - (1 - dodge) * (1 - 0.15)
        # v140 波4：新手特效 远行（novice_first_turn_dodge）——每场战斗首刻闪避率 +5%
        if (self.p_eff or {}).get("novice_dodge_active") and self._tick_no() <= 1:
            dodge = 1 - (1 - dodge) * (1 - 0.05)
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
        # v142 数据驱动：铁壁格挡（anvil_parry）——受击 20% 概率免疫本次伤害（每场 3 次，数值读 params）
        _ap_eff = self._set_eff(player, "anvil_parry", 4)
        if _ap_eff:
            _ap_params = (_ap_eff or {}).get("params") or {}
            _apl = int((self.p_eff or {}).get("anvil_parry_left", _ap_params.get("per_battle", 3)) or 3)
            if _apl > 0 and random.random() < float(_ap_params.get("chance", 0.20)):
                self.p_eff["anvil_parry_left"] = _apl - 1
                logs.append(f"🛡️ 铁壁格挡！千锤百炼的拳套挡下了攻击！（剩余 {_apl - 1} 次）")
                return
        # v113.1：团队技能 reduce_all 真·百分比减伤（此前误映射 def_up 防御提升）——
        # p_buffs["reduce_all"] 存减伤百分比，刻数由 self._reduce_all_left 单独计时。
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
            # v142 数据驱动：壁槌反震（bi_chui_wall）——格挡成功必反弹 30% 原始伤害（数值读 params）
            _bw_eff = self._set_eff(player, "bi_chui_wall", 4)
            if _bw_eff and self.enemy.get("hp", 0) > 0:
                _bw_params = (_bw_eff or {}).get("params") or {}
                _bw = max(1, int(dmg * float(_bw_params.get("reflect_pct", 0.30))))
                _bw = self._boss_dmg_filter(_bw, player, logs)
                self._damage_enemy(_bw, logs)
                logs.append(f"🧱 壁槌反震！格挡余劲反弹 {_bw} 点伤害！")
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
        # ---- v151 时刻制：防御型 buff 受击计数递减（鱼鱼拍板：防御药水"3 刻"应按敌方出手次数计）----
        # 铁壁药剂/岩壁药剂/影步药剂/荆棘药剂/技能铁壁 等防御/受击类 buff 不再按玩家刻递减，
        # 改为"实际受击 N 次后消失"——防的是敌方出手，就按敌方出手数计时，不受速度差影响。
        if getattr(self, "_p_buff_hits", None):
            for _hk in [k for k in list(self._p_buff_hits) if int(self._p_buff_hits.get(k, 0) or 0) > 0]:
                _nh = int(self._p_buff_hits.get(_hk, 0) or 0) - 1
                if _nh <= 0:
                    self._p_buff_hits.pop(_hk, None)
                    # 受击次数耗尽 → 移除对应 buff（若 p_buffs 里还有刻数残留也清掉）
                    if _hk in self.p_buffs:
                        self.p_buffs.pop(_hk, None)
                        logs.append(f"🕛 【{_hk}】效果随受击消耗殆尽！")
                else:
                    self._p_buff_hits[_hk] = _nh
        # ---- v139 职业融合：受击处理（dual_form 扣资源 / focus 打断 / charge 打断 -1 阶）----
        from .core.battle_modes import dual_form_def, dual_form_state, dual_form_hit, dual_form_force_return, dual_form_exit, dual_form_active, focus_def, focus_state, focus_on_hit, vent_def, vent_relief
        from .core.battle_bars import charge_state, charge_on_hit
        # dual_form：狂暴/龙焰形态受击 -N（P3 不清零、单刻封顶，由 dual_form_hit 返回应扣量）
        if dual_form_active(player):
            _dfd = dual_form_def(player)
            _df_hc = dual_form_hit(player)
            if _df_hc > 0:
                _df_key = _dfd.get("key", "rage")
                _df_cur = int(self.resources.get(_df_key, 0) or 0)
                self.resources[_df_key] = max(0, _df_cur - _df_hc)
                logs.append(f"⚡【{_dfd.get('form', '形态')}】受击，形态值 -{_df_hc}（{self.resources.get(_df_key, 0)}）")
                # 强制回基础形态检查（资源 < force_return）
                if dual_form_force_return(player, int(self.resources.get(_df_key, 0) or 0)):
                    dual_form_exit(player, logs)
                    logs.append("⚠️ 力量不支，被迫回到常态！")
        # focus：专注中受击打断判定（interrupt_rate 概率，资源保留）
        if focus_state(player).get("active"):
            focus_on_hit(player, logs)
        # charge：蓄力中受击 -1 阶（不清零）
        _ch_st = charge_state(player)
        if int(_ch_st.get("stages", 0) or 0) > 0:
            charge_on_hit(player, {"name": _ch_st.get("skill", "蓄力")}, logs)
        # vent：闪避已在上方 return（闪避成功走 vent_relief），这里命中时不泄压
        # v104 R3 P1-1：复仇被动——受击后下次攻击 +30%（挨打反打）
        for _pn, _ps in self._passive_map(player)["proc"].get("counter", []):
            self.p_buffs["revenge_atk"] = max(self.p_buffs.get("revenge_atk", 0), 1)
            break
        # 阶段八：受击词条（减伤/格挡/反击/反伤/腐蚀/坚韧）
        dmg = self._affix_on_taken(player, dmg, logs)
        dmg = self._food_on_taken(player, dmg, logs)
        # v142 数据驱动：套装受击特效（taken_* 型，读 params.type 调通用执行器）
        dmg = self._set_taken_proc(player, dmg, logs)
        # v140 波3.1：特效装备受击（哨兵壁垒/铁壁回响/寒霜凝视/荆棘/卫士/深岩/龙脊/复仇环/烬火/石像/泰坦/巡林）
        # 亡舞战铠常驻 -8% 减伤一并在此消费（passive taken 分发）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wetaken = {"dmg": dmg, "taken": dmg}
            _we_proc(self, player, "taken", _wetaken, logs)
            _we_proc(self, player, "passive", {"taken": _wetaken.get("taken", dmg)}, logs)
            dmg = max(1, int(_wetaken.get("taken", dmg)))
        except Exception:
            pass
        # v140 波4：新手特效 守御（novice_first_turn_guard）——每场战斗首刻受击伤害 -10%
        if (self.p_eff or {}).get("novice_guard_active") and self._tick_no() <= 1:
            dmg = max(1, int(dmg * 0.90))
            logs.append("🛡️ 守御：首刻受击伤害 -10%！")
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
                        # v130.2f2（T7 P2-1）：受击被动 res_gain（磐石体/墓穴护甲/守护姿态）改走
                        # _res_gain_class——与 on_hit 基础受击渠道同口径：上限含词条/套装加成，
                        # 满资源溢出转盾（不再直调 E.core_resource_gain 平顶蒸发）；满值时
                        # 真实增量判定防误报（转盾由 _res_gain_class 日志单独反馈）。
                        _rg_before = int(self.resources.get(_rk, 0) or 0)
                        self.resources[_rk] = self._res_gain_class(_rcls, _rk, _rg)
                        if int(self.resources.get(_rk, 0) or 0) > _rg_before:
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
        # v142 数据驱动：磐石不动（pan_shi_steady）——常驻 5% 减伤并入汇总（数值读 params）
        _ps_eff = self._set_eff(player, "pan_shi_steady", 4)
        if _ps_eff:
            _ps_params = (_ps_eff or {}).get("params") or {}
            reduce_total += int(dmg * float(_ps_params.get("reduce_pct", 0.05)))
            logs.append("⛰️ 磐石不动：巍然不动，减伤 5%！")
        # 圣堂壁垒（holy_bastion_def）——常驻 5% 减伤（数值读 params）
        _hb_eff = self._set_eff(player, "holy_bastion_def", 4)
        if _hb_eff:
            _hb_params = (_hb_eff or {}).get("params") or {}
            reduce_total += int(dmg * float(_hb_params.get("reduce_pct", 0.05)))
            logs.append("⛪ 圣堂壁垒：受击减伤 5%！")
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
        # v142 数据驱动：石拳反打（shi_quan_retort）——受击 15% 概率以 30% 攻击反击（数值读 params）
        _sq_eff = self._set_eff(player, "shi_quan_retort", 4)
        if _sq_eff and self.enemy.get("hp", 0) > 0:
            _sq_params = (_sq_eff or {}).get("params") or {}
            if random.random() < float(_sq_params.get("chance", 0.15)):
                _sq_st = self._player_stats(player)
                _sq_est = self._enemy_stats()
                _sq_dmg = E.calc_damage(int(_sq_st["atk"] * float(_sq_params.get("atk_pct", 0.30))), _sq_est.get("def", 0), dmg_type="phys")
                _sq_dmg = self._boss_dmg_filter(_sq_dmg, player, logs)
                self._damage_enemy(_sq_dmg, logs)
                logs.append(f"🥊 石拳反打！铁拳回敬 {_sq_dmg} 点伤害！")
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
                    # v130.2f 反击回气承诺落地（monk.md §3.1「受击换气/反震回气」）：
                    # 以守为攻/反击之王 反击命中后 气 +2（走 _res_gain_class 类资源上限管线）
                    _cr_cls = player.get("class_name", "")
                    _cr_rd = E.core_resource_def(_cr_cls)
                    if _cr_rd and _cr_rd.get("key") == "chi":
                        _chi_now = self._res_gain_class(_cr_cls, "chi", 2)
                        logs.append(f"🥊 反击回气 +2（气 {_chi_now}）")
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
        # v140 波3.2：次元门扉符无敌——本刻免疫一切伤害（p_eff invuln，用后清 + 记录僵直）
        _inv = (self.p_eff or {}).get("invuln")
        if _inv and int(_inv.get("turns", 1) or 1) > 0:
            _inv["turns"] = int(_inv.get("turns", 1) or 1) - 1
            if int(_inv.get("turns", 0) or 0) <= 0:
                self.p_eff.pop("invuln", None)
                _sa = int(_inv.get("stun_after", 1) or 1)
                if _sa > 0:
                    self.p_buffs["stun"] = max(int(self.p_buffs.get("stun", 0) or 0), _sa)
                    logs.append("🌀 次元门扉关闭，你陷入短暂僵直！")
            logs.append("🌀 次元门扉：免疫了这次伤害！")
            return
        # v140 波3.2：龙血变身药剂——受击伤害 +15%（morph_dmg_taken）
        _morph = float((self.p_eff or {}).get("morph_dmg_taken", 0) or 0)
        if _morph > 0:
            dmg = max(1, int(dmg * (1 + _morph)))
            logs.append(f"🐉 龙人形态：额外承受 {int(dmg * _morph)} 点伤害！")
        # v142 数据驱动：圣徽守护（bless_ward_shield）——受击 25% 概率获得 8% 最大生命护盾（3 刻，数值读 params）
        _bws_eff = self._set_eff(player, "bless_ward_shield", 4)
        if _bws_eff:
            _bws_params = (_bws_eff or {}).get("params") or {}
            if random.random() < float(_bws_params.get("chance", 0.25)):
                _bw_sh = int(player.get("max_hp", player.get("hp", 1)) * float(_bws_params.get("shield_pct", 0.08)))
                self._add_shield("bless_ward", _bw_sh, int(_bws_params.get("shield_turns", 3)))
                logs.append(f"✨ 圣徽守护！获得 {_bw_sh} 点护盾！")
        # v142 数据驱动：圣辉圣环（holy_halo_shield）——受击后 10% 伤害转护盾（每刻最多 1 次，数值读 params）
        _hh_eff = self._set_eff(player, "holy_halo_shield", 4)
        if _hh_eff and int(dmg) > 0:
            _hh_params = (_hh_eff or {}).get("params") or {}
            _hh_turn = self._tick_no()
            if (self.p_eff or {}).get("holy_halo_used") != _hh_turn:
                _hh_sh = int(dmg * float(_hh_params.get("shield_pct", 0.10)))
                if _hh_sh > 0:
                    self._add_shield("holy_halo", _hh_sh, 2)
                    self.p_eff["holy_halo_used"] = _hh_turn
                    logs.append(f"✨ 圣辉圣环：{_hh_sh} 点伤害化为护盾！")
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
        # v142 数据驱动：S1 受击直连已迁至 _set_taken_proc（ferry_repel/tie_pi_bulwark/tie_pi_harden/shou_wang_ward/tie_shou_blood）
        player["hp"] = max(0, player.get("hp", 0) - dmg)
        # v140 波3.1：特效装备生命阈值（时光凝滞/磐石守护/苍穹庇护/石像鬼之心/不灭意志）
        # + 不灭意志免疫致死（本刻免疫致死伤害，扣血后回拉）
        try:
            from .core.weapon_effects import proc as _we_proc
            _we_proc(self, player, "threshold", {"dmg": dmg}, logs)
            if battle_p_eff_undying := getattr(self, "p_eff", {}).get("we_undying_immune"):
                if player.get("hp", 0) <= 0:
                    player["hp"] = max(1, int(player.get("max_hp", player.get("hp", 1)) * 0.10))
                    logs.append("✨ 不灭意志：你撑住了致命一击！")
                self.p_eff.pop("we_undying_immune", None)
            # 死亡之舞：受击伤害 35% 转为缓伤池（刻开始结算 10%）
            if getattr(self, "p_eff", {}).get("we_death_pool") is not None:
                self.p_eff["we_death_pool"] = float(self.p_eff.get("we_death_pool", 0) or 0) + dmg * 0.35
        except Exception:
            pass
        # v140 波3.2：不死鸟之羽复活——致死时以 revive_hp% 生命复活 1 次（+ 减伤 buff）
        if player["hp"] <= 0 and (self.p_eff or {}).get("phoenix_revive") and not (self.p_eff or {}).get("phoenix_consumed"):
            _pr = self.p_eff.get("phoenix_revive") or {}
            self.p_eff["phoenix_consumed"] = True
            player["hp"] = max(1, int(player.get("max_hp", player.get("hp", 1)) * float(_pr.get("hp", 0.30) or 0.30)))
            _prt = max(1, int(_pr.get("turns", 3) or 3))
            self.p_buffs["reduce_all"] = max(float(self.p_buffs.get("reduce_all", 0) or 0),
                                             float(_pr.get("dmg_reduce", 0.20) or 0.20))
            self._reduce_all_left = max(int(getattr(self, "_reduce_all_left", 0) or 0), _prt)
            logs.append(f"🪶 不死鸟之羽燃尽！你以 {player['hp']} HP 复活，获得减伤！")
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
        # v151 隐藏职业删除：星语猎印 on_hit 双语义解耦白名单已移除（受击按 on_hit 正常读）
        if rd and rd.get("on_hit"):
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
        # v130.2 资源增幅：受击触发（沸腾战血 3 刻内受击额外 +2 怒，P0-1 消费端；持续时长制 turns 衰减）
        _amp_th = self._amp_resource(player, "on_hit_taken")
        if _amp_th:
            logs.append(f"⚡ 沸腾战血：受击额外资源 +{_amp_th}！")
        # v130.2c 资源词条：受击（浴血 怒气/虔诚护符 信仰/磐息 气 +1；残血灼薪 血量条件判定）
        self._affix_res_proc(player, "on_taken", logs)
        # v151 隐藏职业删除：暮影影步受击清空（原 cls_shadow_blade 专属）已移除
        # v130.2 刺客攻线·影舞者：受击回退 -1 连击点 + 连段归零（高风险高回报，assassin_转职 §1.0）
        if cls == "cls_ci_ke" and self._is_path(player, 1):
            _pen = int(ASSASSIN_ON_TAKE_HIT_PENALTY or 0)
            cur_cp = int(self.resources.get("cp", 0) or 0)
            if cur_cp > 0 and _pen < 0:
                penalty = min(cur_cp, -_pen)
                self.resources["cp"] = cur_cp - penalty
                logs.append(f"🗡️ 受击！连击点 -{penalty}({self.resources['cp']}/{rd['max'] if rd else 5})")
            self._combo_break(player, self._combo_keep_chance(player))
        # v140 S1 直连消费：拳心回流（tie_shou_blood）——受击 30% 概率回复 3% 最大生命
        if self._set_eff(player, "tie_shou_blood", 4) and player.get("hp", 0) > 0:
            if random.random() < 0.30:
                _ts_heal = int(player.get("max_hp", player.get("hp", 1)) * 0.03)
                player["hp"] = min(player.get("max_hp", player.get("hp", 1)), player.get("hp", 0) + _ts_heal)
                logs.append(f"🩸 拳心回流：气血奔涌，回复 {_ts_heal} 点生命！")
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
