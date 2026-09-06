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
        LUCKY_CRIT_CHANCE, LUCKY_CRIT_MULT, LUCK_CRIT_CONV, MULTI_HIT_CRIT_FIRST_ONLY,  # v133 峰值红线
        BUFF_MULT, TEAM_BUFF_KEYS,  # v176 增益映射表下沉 data/battle_config.py
    )
from .core.battle_conds import PASSIVE_COND_CHECKS, PASSIVE_COND_STAT_KEYS, passive_cond_ok  # v1.x 被动条件注册表
from .core.skill_kinds import (  # v176 去魔法字符串：类型常量替代散落中文比较
    K_PHYS, K_MAGI, K_HEAL, K_BUFF, K_TRUE, K_TAUNT, K_SUMMON,
    is_damage_kind, seg_of,
)
from .core.constants import (  # v130.7 意见#28：逃跑成功率修正常量（core/__init__ 未导出清单，直连避免动聚合层）
    FLEE_CHANCE, FLEE_LEVEL_STEP, FLEE_SPD_STEP, FLEE_MIN, FLEE_MAX,
    # v138.2 异常体系五律：阈值递增/每场上限+饱和/跨阶段保留/饱和收敛（真伤走 DOT_DEFS true_dmg）
    DOT_THRESHOLD_MULT, DOT_THRESHOLD_CAP, DOT_MAX_TRIGGER,
    DOT_PRESERVE_PCT, DOT_PRESERVE_THRESHOLD_BONUS, DOT_SATURATE_MULT,
    # v181.P2B 引擎刻度常量收 core/constants.py 权威单源（原本文件模块级定义 →
    # core/constants import；core 模块改从 constants import，消除 core→battle 反向 import）
    BUFF_TURNS, DEBUFF_TURNS,
    BASE_DELAY, SPD_CT_CAP, SPD_REF, ACT_TICK,
    CAST_ATK, CAST_SKILL, CAST_ITEM, CAST_FOOD, CAST_DEFEND, CAST_FLEE, CAST_PET_SKILL,
)
from .core.tick_effects import TICK_HANDLERS as _TICK_HANDLERS  # v179 通用 tick 效果注册表（数据驱动）
# v181.P2D-D1 被动 proc 注册表（proc → 机制族 handler + 分发；无注册 = 不触发）
from .core.passive_procs import run_proc_family as _run_proc_family  # noqa: F401
from .data.races import (  # v181.D P1-D 种族机制数据下沉（原模块级常量/标签内联 → data 单源）
    RACE_ATTACK_MULT as _RACE_ATTACK_MULT,
    UNDEAD_KEYWORDS as _UNDEAD_KEYWORDS,
)

# v95.4 普攻文案按职业区分（玩家反馈：全职业"你挥剑攻击"违和）
# v112 数据驱动收敛（D5）：文案下沉 CLASSES[职业]["attack_text"]，逻辑层只读数据

# v181.D（P1-D）：模块级种族常量已下沉 game/data/races.py（RACE_ATTACK_MULT/UNDEAD_KEYWORDS），
# battle 顶部 import 读表（下划线别名 _RACE_ATTACK_MULT/_UNDEAD_KEYWORDS），本文件不再声明常量。
# 对外旧引用兼容：见 race_talent_display.py（已改读 data 单源，不再反向 import battle）。

# v180G B1-2 吞错留痕：结算管线 except 静默吞错计数 + 首次详情落 warning
# 只做可观测化（不改变吞错行为本身——战斗结算容错是历史设计，贸然抛错会崩整场）；
# 全量回归跑测试时 warning 可见，定位"哪条管线在静默失败"不再靠考古。
_import_logging = None


def _battle_warn(site: str, exc: BaseException | None = None, detail: str = ""):
    """结算管线 except 留痕：stdout 首次 + logging 全量（不抛错、不改行为）。"""
    global _import_logging
    try:
        if _import_logging is None:
            import logging as _lg
            _import_logging = _lg
        _logger = _import_logging.getLogger("dragonfall.battle")
        if exc is not None:
            _logger.warning("[battle-swallow] %s: %r %s", site, exc, detail)
        else:
            _logger.warning("[battle-swallow] %s %s", site, detail)
    except Exception:
        pass  # 日志设施自身失败绝不反噬战斗


def _basic_attack_verb(player: dict) -> str:
    """普攻动作文案（按职业；未知职业 fallback 挥剑攻击）"""
    return C.CLASSES.get(player.get("class_name", ""), {}).get("attack_text", "挥剑攻击")


# BUFF_MULT 已下沉 game/data/battle_config.py（v176）
# TEAM_BUFF_KEYS 已下沉 game/data/battle_config.py（v176）
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

# v181.P2B：引擎刻度常量（BUFF_TURNS/DEBUFF_TURNS/BASE_DELAY/SPD_CT_CAP/SPD_REF/ACT_TICK/
# CAST_*) 已收 game/core/constants.py 作权威单源（消除 core→battle 反向 import），
# 本文件顶部 from .core.constants import（名字不变），此处不再重复定义。

# v121 CTB 行动时间轴：全局行动消耗常量
# v152 鱼鱼拍板：总耗时 = 行动间隔（BASE_DELAY/spd）+ 固定动作耗时。
# BASE_DELAY=40 经 sim 标定：普通怪战斗 ~49s（60s 内），紧凑不拖沓。
# （旧 100 在新模型下战斗拖到 113s 太长；40 平衡节奏与速度差稀释）
# 注：BASE_DELAY/SPD_CT_CAP/SPD_REF 等常量定义见 core/constants.py（v181.P2B 权威单源）。
def _ct_cost(spd) -> float:
    """v154 CTB：一次行动的时间成本 = 基准耗时（出招+收招一拍完成）折算到时刻。
    实际耗时按 (SPD_REF / spd) 速度折算；引擎刻度常量（CAST_* 基准耗时/BASE_DELAY/
    SPD_REF 等）权威定义见 core/constants.py（v181.P2B 收 core 单源）。
    """
    return 1.0


def _ct_initial_wait(spd) -> float:
    """v154 单位初始行动等待 = 基准普攻耗时 × 速度折算系数（第一刀也按速度快慢出）。

    v161 新曲线（鱼鱼拍板：取消 cap 线性，改边际递减永续公式，与 _ct_cost 同款）：
        速度 50 → 1.0s；速度 25 → 1.41s；速度 100 → 0.71s；速度 200 → 0.50s。
    """
    import math as _m
    try:
        eff = max(float(spd or 0), 1.0)
    except Exception:
        eff = 1.0
    return CAST_ATK * _m.sqrt(SPD_REF / eff)


# ============================================================
# v179 通用 tick handler（周期效果族，数据驱动）
# 签名统一：(battle, actor, eff, logs) -> (log_list, keep)
#   keep = 本效果族通道是否仍应存在（False → 移除卡片不再续排）
#   条件语义：卡片代表"这类效果可能发生"，handler 每次判生效条件（血满跳过等）
# ============================================================
def _th_set_heal(battle, actor, eff, logs):
    """圣光/永恒套装每刻回血（regen 5% / regen_strong 8%）。条件：有该套装 4 件效果 + 掉血。

    v181-A1：回血比例数据化——按激活套装条目 bonus_4.params.heal_pct 读（晨光教会 0.08 /
    旧牧师主题 0.05 已随条目声明）；条目不可解析（遗留档无 SETS 条目）回落旧兜底 0.05/0.08，
    数值与改造前完全一致。"""
    try:
        _s4 = E.set_bonus_4(actor.get("equipment", {}))
        if not any(e in _s4 for e in ("regen", "regen_strong")):
            return [], False  # 套装换下 → 通道关闭
        eff_name = next((e for e in ("regen", "regen_strong") if e in _s4), "regen")
        pct = 0.05 if eff_name == "regen" else 0.08
        # v181-A1：读激活套装声明的 params.heal_pct（覆盖型，声明即生效——任意套装带
        # regen/regen_strong effect + params.heal_pct 都按数据值回血）
        try:
            for sname, cnt in E.active_sets(actor.get("equipment") or {}).items():
                if cnt < 4:
                    continue
                _si = E._set_info(sname)
                if not _si:
                    continue
                for _tier in ("bonus_4", "bonus_3"):
                    _tb = (_si.get(_tier) or {})
                    if _tb.get("effect") == eff_name and (_tb.get("params") or {}).get("heal_pct"):
                        pct = float(_tb["params"]["heal_pct"])
                        break
                else:
                    continue
                break
        except Exception:
            pass
        if actor.get("hp", 0) < actor.get("max_hp", 1):
            heal = int(actor.get("max_hp", actor.get("hp", 1)) * pct)
            _hlog = []
            battle._heal_actor(actor, heal, _hlog)  # v180E 统一落地（禁疗/受疗日志进 _hlog）
            return [f"✨ 套装祝福生效，你回复了 {heal} 点生命！"] + _hlog, True
        return [], True
    except Exception:
        return [], False


def _th_rune_regen(battle, actor, eff, logs):
    """符文·治愈每刻回血 x%。条件：附魔 regen 存在 + 掉血。"""
    try:
        regen_lvl = battle._enchant_lvl(battle._enchant_effects(actor), "regen")
        if not regen_lvl:
            return [], False  # 附魔消失 → 通道关闭
        if actor.get("hp", 0) < actor.get("max_hp", 1):
            heal = int(actor.get("max_hp", actor.get("hp", 1)) * C.rune_value("regen", regen_lvl))
            _hlog = []
            battle._heal_actor(actor, heal, _hlog)  # v180E 统一落地
            return [f"✨ 符文治愈生效，你回复了 {heal} 点生命！"] + _hlog, True
        return [], True
    except Exception:
        return [], False


def _th_stardust_mana(battle, actor, eff, logs):
    """5 件套夜间每刻回蓝（星尘：5%/刻，时间窗 19:00-06:00）。

    v181-A1：数据化——任意 5 件套声明 bonus_5.effect='night_mp_regen' 即触发，
    数值/时间窗读 bonus_5.params（pct=回蓝比例、night_hours=[起,止] 含跨午夜）。
    判定：该效果存在 + 夜间 + 掉蓝。"""
    try:
        _s5 = battle._set_bonus_5(actor)
        _cfg = None
        for sname in _s5:
            _b5 = (E._set_info(sname) or {}).get("bonus_5") or {}
            if _b5.get("effect") == "night_mp_regen":
                _cfg = (_b5.get("params") or {})
                break
        if _cfg is None:
            return [], False  # 套装换下 → 通道关闭
        _hours = _cfg.get("night_hours") or [19, 6]
        _h_start = int(_hours[0])
        _h_end = int(_hours[1])
        _hour = time.localtime().tm_hour
        if _h_start <= _h_end:
            _is_night = (_hour >= _h_start and _hour < _h_end)
        else:
            _is_night = (_hour >= _h_start or _hour < _h_end)  # 跨午夜窗
        if not _is_night:
            return [], True  # 白天不触发（通道仍存在，夜间恢复）
        if actor.get("mp", 0) < actor.get("max_mp", 1):
            gain = int(actor.get("max_mp", actor.get("mp", 1)) * float(_cfg.get("pct", 0.05)))
            actor["mp"] = min(actor.get("max_mp", actor.get("mp", 1)), actor.get("mp", 0) + gain)
            return [f"🌙 星尘祝福：夜风拂过，你回复了 {gain} 点魔力！({actor['mp']}/{actor.get('max_mp', '?')})"], True
        return [], True
    except Exception:
        return [], False


# v179 P1a 注册：自包含回血/回蓝族（_TICK_HANDLERS 与 core/tick_effects 同表）
for _th_kind, _th_fn in (("set_heal", _th_set_heal),
                         ("rune_regen", _th_rune_regen),
                         ("stardust_mana", _th_stardust_mana)):
    _TICK_HANDLERS[_th_kind] = _th_fn


def _th_set_holy(battle, actor, eff, logs):
    """圣堂领域/神恩爆发/壁立千仞（套装 4 件直连效果）。条件：对应套装 4 件效果存在。"""
    try:
        _s4 = E.set_bonus_4(actor.get("equipment", {}))
        if not any(k in _s4 for k in ("holy_field_heal", "divine_grace_burst", "hu_xiao_barrier")):
            return [], False  # 套装换下 → 通道关闭
        _mx = actor.get("max_hp", actor.get("hp", 1))
        out = []
        if "holy_field_heal" in _s4:
            _hfh = (battle._set_eff(actor, "holy_field_heal", 4) or {})
            _hfh_p = (_hfh or {}).get("params") or {}
            # v181-A1：数值全读 params（原本地兜底 0.50/0.06/0.03 与数据重复→删除，数值一致）
            _low = float(_hfh_p.get("cond_hp_lt", 0.50) or 0.50)
            _hl = float(_hfh_p.get("heal_low_pct", 0.06) or 0.06)
            _hh = float(_hfh_p.get("heal_high_pct", 0.03) or 0.03)
            if actor.get("hp", 0) < _mx:
                _pct = _hl if actor.get("hp", 0) / max(1, _mx) < _low else _hh
                _hf_heal = int(_mx * _pct)
                battle._heal_actor(actor, _hf_heal, out)  # v180E 统一落地
                out.append(f"⛪ 圣堂领域：圣光庇护，你回复了 {_hf_heal} 点生命！")
        if "divine_grace_burst" in _s4:
            _dgb = (battle._set_eff(actor, "divine_grace_burst", 4) or {})
            _dgb_p = (_dgb or {}).get("params") or {}
            # v181-A1：数值全读 params（原本地兜底 0.05/0.15/0.30 与数据重复→删除）
            _dg_heal = int(_mx * float(_dgb_p.get("heal_pct", 0.05)))
            if actor.get("hp", 0) < _mx:
                battle._heal_actor(actor, _dg_heal, out)  # v180E 统一落地
                out.append(f"☀️ 神恩爆发：神恩涌动，你回复了 {_dg_heal} 点生命！")
            if not (actor.setdefault('eff', {}) or {}).get("divine_burst_used") and actor.get("hp", 0) / max(1, _mx) < float(_dgb_p.get("low_hp_lt", 0.30)):
                _dg_extra = int(_mx * float(_dgb_p.get("low_extra_pct", 0.15)))
                battle._heal_actor(actor, _dg_extra, out)  # v180E 统一落地
                actor.setdefault('eff', {})["divine_burst_used"] = True
                out.append(f"☀️ 神恩爆发·濒危：圣辉倾泻，额外回复 {_dg_extra} 点生命！（每场 1 次）")
        if "hu_xiao_barrier" in _s4:
            _hxb = (battle._set_eff(actor, "hu_xiao_barrier", 4) or {})
            _hxb_p = (_hxb or {}).get("params") or {}
            # v181-A1：数值全读 params（原本地兜底 0.03/1 与数据重复→删除）
            battle._add_shield("hu_xiao_barrier", int(actor.get("max_hp", 1) * float(_hxb_p.get("shield_pct", 0.03))), int(_hxb_p.get("shield_turns", 1)))
            out.append("🧱 壁立千仞：千仞壁垒立于身前！")
        return out, True
    except Exception:
        return [], False


def _th_passive_heal(battle, actor, eff, logs):
    """被动回复族：气力调和(turn_heal)/生命之泉(team_regen)/森之共鸣(focus_regen_summon)。条件：对应被动存在。"""
    try:
        _pm = battle._passive_map(actor)["proc"]
        out = []
        _alive_ok = True
        _th = _pm.get("turn_heal") or []
        for _pn, _ps in _th:
            if actor.get("hp", 0) < actor.get("max_hp", 1):
                heal = int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("pct", 0.02)))
                battle._heal_actor(actor, heal, out)  # v180E 统一落地
                out.append(f"🍃 {_pn}生效，你回复了 {heal} 点生命！")
            break
        _tr = _pm.get("team_regen") or []
        for _pn, _ps in _tr:
            if actor.get("hp", 0) < actor.get("max_hp", 1):
                heal = int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("mult", 0.05)))
                battle._heal_actor(actor, heal, out)  # v180E 统一落地
                out.append(f"💧 {_pn}：生命之泉涌动，你回复了 {heal} 点生命！")
            break
        try:
            if battle.summons:
                for _pn, _ps in _pm.get("focus_regen_summon", []):
                    _sr_gain = int(_ps.get("gain", 5) or 5)
                    _sr_old = int(actor.setdefault('resources', {}).get("energy", 0) or 0)
                    _sr_new = battle._res_gain(actor, "energy", _sr_gain)
                    if _sr_new > _sr_old:
                        out.append(f"🌳 {_pn}：召唤物在场，专注充能 +{_sr_gain}（{_sr_new}）")
                    break
        except Exception as _sw_e:
            _battle_warn('_th_passive_heal', _sw_e)
            pass
        # 无任何被动 → 通道关闭
        if not (_th or _tr or _pm.get("focus_regen_summon")):
            return [], False
        return out, True
    except Exception:
        return [], False


def _th_mech_charge(battle, actor, eff, logs):
    """奥术/魔剑充能族：arcane_regen/arcane_intuition/spellblade_regen。条件：对应被动存在。"""
    try:
        _pm = battle._passive_map(actor)
        out = []
        _alive = False
        for _pn, _ps in _pm["proc"].get("arcane_regen", []):
            _mech = _ps.get("mech") or "arcane"
            actor.setdefault('stacks', {})[_mech] = E.mech_stack_gain(_mech, actor.setdefault('stacks', {}), 1)
            out.append(f"📖 {_pn}：充能自动+1(当前 {actor.setdefault('stacks', {})[_mech]} 层)")
            _alive = True
            break
        for _pn, _ps in _pm["proc"].get("arcane_intuition", []):
            _mech2 = _ps.get("mech") or "arcane"
            _gain2 = int(_ps.get("gain", 1) or 1)
            try:
                from .core.battle_modes import focus_active as _fa169
                if _fa169(actor):
                    _gain2 += int(_ps.get("focus_gain", 1) or 1)
            except Exception as _sw_e:
                _battle_warn('_th_mech_charge', _sw_e)
                pass
            _before2 = int(actor.setdefault('stacks', {}).get(_mech2, 0) or 0)
            actor.setdefault('stacks', {})[_mech2] = E.mech_stack_gain(_mech2, actor.setdefault('stacks', {}), _gain2)
            if int(actor.setdefault('stacks', {}).get(_mech2, 0) or 0) > _before2:
                out.append(f"📖 {_pn}：每刻充能自动+{_gain2}(当前 {actor.setdefault('stacks', {})[_mech2]} 层)")
            _alive = True
            break
        for _pn, _ps in _pm["stat"]:
            if _ps.get("stat") == "spellblade_regen":
                _mech = _ps.get("mech") or "spellblade"
                actor.setdefault('stacks', {})[_mech] = E.mech_stack_gain(_mech, actor.setdefault('stacks', {}), 1)
                out.append(f"⚔️ {_pn}：魔能自动+1(当前 {actor.setdefault('stacks', {})[_mech]} 层)")
                _alive = True
                break
        if not _alive:
            return [], False
        return out, True
    except Exception:
        return [], False


def _th_core_regen(battle, actor, eff, logs):
    """核心资源刻回复 + 疾风余韵 + 迅捷之核增幅。条件：职业带资源 regen。"""
    try:
        cls = actor.get("class_name", "")
        rd = E.core_resource_def(cls)
        if not rd or not (float(rd.get("regen", 0) or 0) > 0):
            return [], False  # 无自然回资源 → 通道关闭
        out = []
        k = rd["key"]
        old = int(actor.setdefault('resources', {}).get(k, 0) or 0)
        new = battle._res_gain(actor, k, int(rd.get("regen", 0) or 0))
        if new > old:
            out.append(f"🍃 {rd['name']}回复 {new - old} 点({new}/{battle._res_max(actor, k)})")
        if k == "energy":
            _tw_bonus = battle._tailwind_regen_bonus(actor)
            if _tw_bonus > 0:
                _old2 = int(actor.setdefault('resources', {}).get(k, 0) or 0)
                _new2 = battle._res_gain(actor, k, _tw_bonus)
                if _new2 > _old2:
                    out.append(f"🌈 疾风余韵：上刻精力满弦，本刻回复 +{_new2 - _old2} 点{rd['name']}！")
        _amp_pt = battle._amp_resource(actor, "regen")
        if _amp_pt:
            out.append(f"⚡ 迅捷之核：自然回复额外资源 +{_amp_pt}！")
        return out, True
    except Exception:
        return [], False


def _th_faith_decay(battle, actor, eff, logs):
    """牧师信念衰减/亡灵祭仪/过载状态机。条件：职业核心资源是 faith 且带 decay。"""
    try:
        _crd_f = E.core_resource_def(actor.get("class_name", ""))
        if not (_crd_f and _crd_f.get("key") == "faith"):
            return [], False  # 非信念职业 → 通道关闭
        out = []
        # 亡灵祭仪（先产后衰）
        try:
            if _crd_f.get("key") == "faith":
                for _pn, _ps in battle._passive_map(actor)["proc"].get("undead_faith", []):
                    _uf_n = battle._undead_count()
                    if _uf_n > 0 and not actor.setdefault('buffs', {}).get("faith_exhausted"):
                        _uf_gain = float(_ps.get("per_undead", 0.15) or 0.15) * _uf_n
                        _f0 = float(actor.setdefault('resources', {}).get("faith", 0) or 0)
                        actor.setdefault('resources', {})["faith"] = min(float(_crd_f.get("max", 10) or 10), _f0 + _uf_gain)
                        out.append(f"🕯️ {_pn}：{_uf_n} 只亡灵在场，信念 +{_uf_gain:.2f}（{actor.setdefault('resources', {})['faith']:.2f}）")
                    break
        except Exception as _sw_e:
            _battle_warn('_th_faith_decay', _sw_e)
            pass
        if _crd_f.get("decay_per_tick"):
            _f_before = float(actor.setdefault('resources', {}).get("faith", 0) or 0)
            if _f_before >= float(_crd_f.get("max", 10)):
                _ov_pct = float(_crd_f.get("overload_heal_pct", 0.015) or 0.015)
                _ov_heal = int(actor.get("max_hp", 1) * _ov_pct * _f_before)
                actor.setdefault('resources', {})["faith"] = 0
                _foheal = False
                try:
                    for _pn_fh, _ps_fh in battle._proc_pm(actor)["proc"].get("faith_overload_heal", []):
                        _ov_heal = int(_ov_heal * (1.0 + float(_ps_fh.get("heal_up", 0.30) or 0.30)))
                        _foheal = True
                        break
                except Exception as _sw_e:
                    _battle_warn('_th_faith_decay', _sw_e)
                    pass
                out.append(f"⚡ 信念过载！信仰之力迸发，全队回复 {_ov_heal} 点生命！")
                if not _foheal:
                    actor.setdefault('buffs', {})["faith_exhausted"] = 6
                else:
                    out.append("✨ 信念·圣化：信念过载化为圣辉，无力竭反噬！")
                if actor.get("hp", 0) < actor.get("max_hp", 1):
                    battle._heal_actor(actor, _ov_heal, out)  # v180E 统一落地
                    out.append(f"✨ 过载回响：你回复了 {_ov_heal} 点生命！")
            elif _f_before > 0:
                _f_decay = float(_crd_f.get("decay_per_tick", 0.7) or 0.7)
                actor.setdefault('resources', {})["faith"] = max(0.0, _f_before - _f_decay)
                if float(actor.setdefault('resources', {})["faith"]) < _f_before:
                    out.append(f"🕯️ 信念衰减：{_f_before:.1f} → {float(actor.setdefault('resources', {})['faith']):.1f}")
            if actor.setdefault('buffs', {}).get("faith_exhausted"):
                actor.setdefault('buffs', {})["faith_exhausted"] = int(actor.setdefault('buffs', {})["faith_exhausted"]) - 1
        return out, True
    except Exception:
        return [], False


def _th_echo_heal(battle, actor, eff, logs):
    """歌者回声驻留每层回体力。条件：回声层数 > 0。"""
    try:
        from .data.battle_config import ECHO_CFG as _ECHO_CFG
        echo_n = battle._echo_layers()
        if echo_n <= 0:
            return [], False  # 无回声层 → 通道关闭
        _heal_e = int(_ECHO_CFG.get("heal_per_layer", 6) or 6) * echo_n
        if echo_n >= int(_ECHO_CFG.get("max_layers", 3) or 3):
            _heal_e *= 2
        out = []
        if actor.get("hp", 0) < actor.get("max_hp", 1):
            battle._heal_actor(actor, _heal_e, out)  # v180E 统一落地
            out.append(f"🎵 回声余韵：全队恢复 {_heal_e} 点体力({echo_n} 层)")
        for _ally in (battle.allies or []):
            if isinstance(_ally, dict) and _ally.get("hp", 0) < _ally.get("max_hp", 1):
                battle._heal_actor(_ally, _heal_e, out)  # v180E 统一落地
        return out, True
    except Exception:
        return [], False


def _th_affix_food_we(battle, actor, eff, logs):
    """词条刻开始(_affix_turn_start) + 食物foodfx(_food_turn_start) + 武器特效 turn_start。
    条件：三者任一存在（保守常驻，内部判空转）。"""
    try:
        out = []
        try:
            if battle._affix_effs(actor, "__any__") or True:
                battle._affix_turn_start(actor, out)
        except Exception as _sw_e:
            _battle_warn('_th_affix_food_we', _sw_e)
            pass
        try:
            battle._food_turn_start(actor, out)
        except Exception as _sw_e:
            _battle_warn('_th_affix_food_we', _sw_e)
            pass
        try:
            from .core.weapon_effects import proc as _we_proc
            _we_proc(battle, actor, "turn_start", {}, out)
        except Exception as _sw_e:
            _battle_warn('_th_affix_food_we', _sw_e)
            pass
        return out, True
    except Exception:
        return [], False


# v179 P1b-e 注册：套装直连/被动/充能/核心资源/信念/回声/词条食物武器族
for _th_kind, _th_fn in (("set_holy", _th_set_holy),
                         ("passive_heal", _th_passive_heal),
                         ("mech_charge", _th_mech_charge),
                         ("core_regen", _th_core_regen),
                         ("faith_decay", _th_faith_decay),
                         ("echo_heal", _th_echo_heal),
                         ("affix_food_we", _th_affix_food_we)):
    _TICK_HANDLERS[_th_kind] = _th_fn


def _th_actor_dot(battle, actor, eff, logs):
    """v179 P2 DOT 通用 tick：结算一个 actor 身上的全部 debuffs（actor-agnostic）。

    条件：actor.debuffs 非空才结算；结算完无 debuffs → keep=False（卡自然移除）。
    与旧 dot_tick 事件等价：_tick_actor_dots 统一结算器（玩家/怪同一套）。
    """
    try:
        if not actor:
            return [], False
        _deb = actor.get("debuffs") or {}
        # 过滤出还在 DOT_DEFS 里的有效 dot 类型（debuffs 可能含非 dot 键）
        _has_dot = any(_k in DOT_DEFS for _k in _deb)
        if not _has_dot:
            return [], False  # 无有效 dot → 通道关闭（毒消失/被净化）
        out = []
        try:
            _ml = battle._tick_actor_dots(actor, logs, force=True)
            if _ml:
                out += _ml
        except Exception as _dex:
            out.append(f"(dot 结算异常: {_dex})")
        # 玩家被毒死 → defeat 置位（旧 dot_tick 事件分支语义）
        # v180F A7：死亡判定针对被结算 dot 的 actor 本身（actor 就是中毒目标），
        # 不再用 _last_player or player 猜"当前玩家"——玩家侧 actor 死 → defeat。
        try:
            if battle._is_player_side(actor) and battle._actor_dead(actor):
                battle.result = "defeat"
        except Exception as _sw_e:
            _battle_warn('_th_actor_dot', _sw_e)
            pass
        # 结算后仍有效 dot → keep=True 续排；无 → False 停
        _deb2 = actor.get("debuffs") or {}
        _still = any(_k in DOT_DEFS for _k in _deb2)
        return out, _still
    except Exception:
        return [], False


_TICK_HANDLERS["actor_dot"] = _th_actor_dot


def _th_food_hot(battle, actor, eff, logs):
    """v179 P3 食物持续恢复（p_hot → 通用 tick 卡）：每秒结算回血/回蓝 + turns 递减。

    数据存 eff.data：{heal: 比例, mana: 比例, turns: 剩余刻}。每次触发结算一次并 turns-1，
    turns<=0 → keep=False 卡自动移除（效果结束）。
    语义变化（v178.2 铁律一致）：原"每玩家行动触发"→ 改"每秒触发"，N 刻 = N 秒。
    """
    try:
        d = eff.get("data") or {}
        _turns = int(d.get("turns", 0) or 0)
        if _turns <= 0:
            return [], False  # 效果耗尽 → 卡移除
        out = []
        _hpct = float(d.get("heal", 0) or 0)
        _mpct = float(d.get("mana", 0) or 0)
        _mx_hp = actor.get("max_hp", actor.get("hp", 1))
        _mx_mp = actor.get("max_mp", actor.get("mp", 1))
        if _hpct > 0 and actor.get("hp", 0) < _mx_hp:
            gain = int(_mx_hp * _hpct)
            if gain > 0:
                before = actor.get("hp", 0)
                battle._heal_actor(actor, gain, out)  # v180E 统一落地
                out.append(f"🍲 持续恢复生效，恢复 {actor['hp'] - before} 点生命！({actor['hp']}/{_mx_hp})")
        if _mpct > 0 and actor.get("mp", 0) < _mx_mp:
            gain = int(_mx_mp * _mpct)
            if gain > 0:
                before = actor.get("mp", 0)
                actor["mp"] = min(_mx_mp, before + gain)
                out.append(f"🍲 持续恢复生效，恢复 {actor['mp'] - before} 点魔力！({actor['mp']}/{_mx_mp})")
        # turns 递减（同步 p_hot 权威状态 + 卡 data，两者一致）
        _new_turns = _turns - 1
        d["turns"] = _new_turns
        try:
            _ph = actor.setdefault('hot', {}) or {}
            if _ph:
                _ph["turns"] = _new_turns
                if _new_turns <= 0:
                    _ph.clear()
        except Exception as _sw_e:
            _battle_warn('_th_food_hot', _sw_e)
            pass
        if _new_turns > 0:
            out.append(f"（剩余 {_new_turns} 刻）")
            return out, True
        return out, False  # 耗尽 → 移除
    except Exception:
        return [], False


_TICK_HANDLERS["food_hot"] = _th_food_hot


def _th_pet_act(battle, actor, eff, logs):
    """v179 P4 宠物出手通用 tick：替换 pet_tick 专用事件。

    v179 修正（鱼鱼 2026-09-06 审计）：宠物面板 skill_interval 定死"每 N 刻一次"
    （数据 3-4 刻 = 3-4 秒），这就是唯一出手节奏——spd 只影响形象读条不影响出手
    频率。旧实现"读条周期(0.65-1.03s)排事件 + _pet_should_hit 限频压回 N 秒"是
    双周期打架的冗余（读条比面板快 3-5 倍才需要限频）——已废弃，卡 interval
    直接用 skill_interval，出手即出手（不需要限频保护，调度器保证节奏）。
    """
    try:
        if not battle.pet or battle._enemy_dead():
            return [], False  # 无宠物/敌方全灭 → 通道关闭
        # v180E 阶段2（原 _pet_skill_turn 守卫语义保留）：Lv.10 解锁 + 饱食度=0 技能失效
        if int(battle.pet.get("level", 0) or 0) < int(C.PET_SKILL_UNLOCK_LV):
            return [], True  # 未解锁 → 通道仍存在（升级后恢复），不触发
        if int(battle.pet.get("satiety", 0) or 0) <= 0:
            return [], True  # 饿肚 → 通道仍存在（喂食后恢复），不触发
        out = []
        # v180F A7：宠物出手守卫针对宠物归属的 owner（actor.owner 优先，B4 随从 owner 化），
        # 不再用 _last_player or player 猜——owner 玩家死则宠物停手。
        _powner = battle._resolve_owner(battle.pet)
        if _powner is None or not battle._actor_dead(_powner):
            # v180E 阶段2：宠物行为已数据化进 auto_act（_pet_ensure_actor 翻译）——
            # pet_act tick 只负责节奏（每 N 刻触发），执行走通用 _companion_act
            # （读宠物 actor auto_act，owner 解析见 _resolve_owner）。
            if battle.pet.get("auto_act"):
                battle._companion_act(battle.pet, out)
        # interval 固定 = 面板 skill_interval（每 N 刻一次，N×ACT_TICK 秒）——
        # 不随 spd 变、不需要限频（卡节奏由通用调度保证）
        try:
            _iv = battle._pet_interval_sec()  # = skill_interval × ACT_TICK
            eff["interval"] = max(float(_iv), 0.001)
        except Exception:
            eff["interval"] = 3.0  # 兜底默认 3 刻
        return out, True  # 宠物活着就续排
    except Exception:
        return [], False


_TICK_HANDLERS["pet_act"] = _th_pet_act


class Battle:
    def __init__(self, btype: str = "monster", enemy: dict | None = None, title_bonus: dict = None, player: dict | None = None, pet: dict | None = None, dmg_mult: float = 1.0, enemies: list | None = None, allies: list | None = None, st: dict | None = None, active_keys: list | None = None, sides: dict | None = None):
        self.btype = btype                 # monster | worldboss | pvp | instance（瞬态 Battle 结算器）
        self._st = st or {}                # v137 副本内聚状态引用（players/alive/p_defending/threat/taunt_*）
        # v158 副本合并：_inst_cb 副本回调钩子（instance 注入），敌方行动后/玩家行动后通知
        # 命令层同步血量/仇恨/贡献/房间状态。野外（不传 cb）为 None，零影响。
        self._inst_cb = (st or {}).get("_cb") if isinstance(st, dict) else None
        # v180F v2.0 通用阵营入口：sides={"阵营名": [actor, ...]}。
        # 提供时把 sides 映射到旧引擎容器（兼容中间态，最终引擎全走 sides）：
        #   - sides 含 "player" → 第一个 actor 作 player 焦点，其余进 allies
        #   - sides 其余阵营（任意名）→ 全进 enemies（各自带 side 字段保留阵营身份）
        # 无 "player" key（怪vs怪等）→ 不设 player（None → 空 dict 占位）
        if sides is not None:
            _p_side = [dict(a) for a in (sides.get("player") or [])]
            _others = []
            for _sn, _acts in sides.items():
                if _sn == "player":
                    continue
                for _a in _acts:
                    _a = dict(_a)
                    _a.setdefault("side", _sn)
                    _a.setdefault("kind", "monster")
                    _others.append(_a)
            if _p_side:
                player = player or _p_side[0]
                if len(_p_side) > 1:
                    allies = list(allies or []) + _p_side[1:]
            if _others:
                enemies = enemies or _others
        # v137 副本：btype="instance" 的 Battle 仅是命令层（instance.py）驱动的"瞬态结算器"——
        # 玩家行动 player_turn(enemy_act=False) + 序列化 type + allies ct 广播（_after_actor_ct 1393-1436）。
        # 副本战斗主循环（谁行动/敌方阶段/超时/换层）由命令层 instance.py 驱动，不在本引擎内调度。
        # active_keys 参数保留（命令层可注入在场成员 key），本引擎不使用（v137 收编方法已删）。
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
            pass  # allies 由下方 335 统一初始化（v176: 330 旧冗余赋值删除——instance 引用在 312/314 已处理）
        self._origin_enemy = dict(self.enemies[0]) if self.enemies else {}
        # v130.7 意见#17 多目标战斗击杀记录：敌方死亡单位 dict 快照列表
        # （_remove_unit 敌方死亡时记录；胜利结算按全部击杀逐个计任务进度）
        self.killed_enemies: list = []
        self.allies: list = allies or []   # v122 我方阵列（治疗指定队友：副本传存活玩家快照引用）
        self.player = player or {}         # v105 攻击方属性读取（_target_dodge_check 需要玩家精准）
        # ================= v180-B P1a/P2：玩家 actor dict 播种 =================
        # 玩家战斗可变状态权威 = 玩家 actor dict（与怪 dict 完全同构）。此处播种全部
        # 战斗可变状态键；副本 allies 快照（729-739）已播种站位键，instance._instance_
        # ensure_player_fields 会兜底老档。战斗状态不落 DB（update_player 白名单）。
        # self.player 为空（from_state 先构造后绑 player）时用 _seed 空 dict 兜底，
        # 调用方绑定真实玩家后 from_state/to_state 负责把存档状态灌入。
        _seed = player if player else {}
        _seed.setdefault("resources", {})
        _seed.setdefault("stacks", {})
        _seed.setdefault("eff", {})
        _seed.setdefault("shields", {})
        _seed.setdefault("cooldown", {})
        _seed.setdefault("combo_seq", [])
        _seed.setdefault("last_combo_tag", None)
        _seed.setdefault("hot", {})
        _seed.setdefault("food_effects", [])
        _seed.setdefault("poi_buff", None)
        _seed.setdefault("buff_hits", {})
        _seed.setdefault("reduce_all_left", 0)
        _seed.setdefault("reduce_left", 0)
        _seed.setdefault("last_element", None)
        _seed.setdefault("tailwind_prev_energy", None)
        _seed.setdefault("v139_modes", {})
        _seed.setdefault("v139_charge", {})
        _seed.setdefault("overflow_shield_cd", False)
        _seed.setdefault("stealth_atk", False)
        _seed.setdefault("buffs", {})
        _seed.setdefault("defending", False)
        _seed.setdefault("charging", None)
        # v180-B P2：玩家战斗可变状态权威 = player actor dict。
        # 引擎内读点统一走 _p_* helper（每次动态读 self.player，换绑/切焦点自动跟随），
        # Battle 实例不再持有玩家焦点字段的独立引用（原 self.p_buffs/self.resources/...
        # 实例属性已删除——避免换绑 self.player 后旧引用失联）。
        # v177 双上下文路由（保留 Battle 级——瞬时管线上下文非玩家状态）
        self._cast_ctx: dict | None = None
        self._target_ctx: dict | None = None
        self.tick_effects: list = []       # v179 通用 tick 效果条目池
        self.team_effects: list = []       # v50 团队技能效果广播
        self.e_minions: list = []          # 敌方援军实体
        # v180-C S1：我方随从 actor 阵列（召唤物/宠物统一容器）。任何"我方非玩家实体"
        # 都是 companions 一员（带 side=player + kind），引擎按字段（guard/auto_act/
        # untargetable/hidden）走通用逻辑。self.summons 是兼容视图 property（召唤物过滤）。
        self.companions: list = []
        self.killed_enemies: list = []
        self.result = None                 # None | victory | defeat | fled
        self.winner_side = None            # v180F B7：无玩家战斗（怪vs怪）胜利阵营名
        self.title_bonus = title_bonus or {}
        if player:
            # v95.19: 战斗内属性统一用实时计算值——DB max_hp/max_mp 是注册/升级快照，换装备后过时，
            # 会导致战斗内血量上限/治疗 clamp/护盾与『角色』面板不一致（装备 HP 加成战斗内不生效）
            try:
                _st = self._player_stats(player)
                player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
                player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
            except Exception as _sw_e:
                _battle_warn('__init__', _sw_e)
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
            except Exception as _sw_e:
                _battle_warn('__init__', _sw_e)
                pass
            # v97.4 回音洞穴祝福：探索事件写入 event_state bless_{qid}（玩家级，players 表全局无 group_id），本场攻击 +5%，一次性
            if player.get("qq_id") and not player.setdefault("buffs", {}).get("echo_bless"):
                try:
                    import json as _json
                    from . import db as _db
                    _key = f"bless_{player['qq_id']}"
                    _raw = _db.get_event_state(_key)
                    if _raw:
                        player.setdefault("buffs", {})["echo_bless"] = 1
                        _db.set_event_state(_key, "")
                except Exception as _sw_e:
                    _battle_warn('__init__', _sw_e)
                    pass
            # v104 M23 神龛祝福（探索 POI 写入，玩家级键 poi_buff_{qq_id}——battle 无 group_id
            # 上下文，与 echo_bless bless_{qq_id} 同款全局键）：战斗开始时读取 → 本场对应属性
            # ×1.10，left-1；用完删除 key（flee 也算消耗 1 次，按文案「持续 5 次战斗」计）
            if player.get("qq_id") and not player.get("poi_buff"):
                try:
                    import json as _json
                    from . import db as _db
                    _key = f"poi_buff_{player['qq_id']}"
                    _raw = _db.get_event_state(_key)
                    if _raw:
                        _pb = _json.loads(_raw)
                        if isinstance(_pb, dict) and _pb.get("stat") in ("atk", "def", "spd") \
                                and int(_pb.get("left", 0) or 0) > 0:
                            player["poi_buff"] = {"stat": _pb["stat"],
                                                  "mult": float(_pb.get("mult", 1.10)),
                                                  "name": _pb.get("name", _pb["stat"])}
                            _pb["left"] = int(_pb["left"]) - 1
                            if _pb["left"] <= 0:
                                _db.delete_event_state(_key)
                            else:
                                _db.set_event_state(_key, _json.dumps(_pb, ensure_ascii=False))
                except Exception as _sw_e:
                    _battle_warn('__init__', _sw_e)
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
                player.setdefault("eff", {})["wolf_howl_mult"] = 1.10
                self._startup_logs = list(getattr(self, "_startup_logs", []) or []) + ["🐺 狼嚎！本场伤害+10%"]
            if "surge_ready" in _bs_ids:
                player.setdefault("eff", {})["surge_ready"] = True
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
            except Exception as _sw_e:
                _battle_warn('__init__', _sw_e)
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
        # 由 _damage_actor 在闪避判定后决定是否输出（闪避时不再同时报伤害）
        self._pending_dmg_lines: list = []
        # v154 读条命中制：玩家出手瞬间暂存的结算参数（cast_done 事件触发时消费）
        self._pending_player_cast: dict | None = None
        # v154 读条命中制：玩家是否正在读条（出手 → 命中 之间；可被控制打断）
        self._player_casting: bool = False
        # v2 受击伤害来源（打断判定用）：最近一次对敌方造成伤害的来源名（默认玩家）
        self._last_hitter: str = "你"
        # v152：开战初始化事件队列——每个敌方排初始 enemy_act 事件；DOT/宠物/Boss 机制排初始 tick。
        # 注意：from_state 恢复的战斗不在此重排（由 from_state 末尾按存档事件恢复），
        # 仅新建战斗在此初始化。副本（instance）的 enemy_act 由 from_state 的 instance 分支
        # 按敌方 ct 补排（v158），本段只负责宠物初始 pet_tick——v167.3 起不再按 btype 排除，
        # 副本带宠物（野外/副本同一套，鱼鱼拍板）：只要 Battle 带 pet 就排初始 pet_tick。
        try:
            # v154 宠物独立速度读条（v179 P4 升级通用 tick 卡）：开战挂第一张 pet_act 卡
            # （初始等待 = 出招时间按宠物 spd 折算）。pet_act 触发 = 宠物出手，动态更新
            # interval 续排（周期 = 出招 + 收招）。v167.3：instance 的 from_state 也会经
            # __init__（带 pet 参数）——但 from_state 恢复的 _now 可能 >0，若在此挂初始
            # 卡会与真实时间轴错位，故恢复路径不依赖本段（见 from_state 末尾按 _now 补挂）；
            # 本段只服务新开战斗（_now=0 且非 from_state 恢复——v180E 阶段6：恢复路径
            # 由 tick 序列化恢复 + 末尾兜底补挂处理，__init__ 不再重复挂卡）。
            if self.pet and int(self.pet.get("level", 0) or 0) >= int(C.PET_SKILL_UNLOCK_LV) \
                    and float(getattr(self, "_now", 0.0) or 0.0) <= 0 and not self._st:
                try:
                    self._pet_ensure_actor()  # v180-C S3：宠物 actor 化（hidden+untargetable 进 companions）
                    self._pet_ensure_guard()  # v180-B ②：block 宠物转配 guard 数据化挡刀
                    # v179 修正：初始周期 = 面板 skill_interval（每 N 刻一次），非读条
                    _pt = self._pet_interval_sec()
                    self.add_tick_effect("pet_act", self.pet, max(_pt, 0.001), uid="pet_act",
                                         source="pet")
                except Exception as _sw_e:
                    _battle_warn('__init__', _sw_e)
                    pass
            # v178.2 regen_tick（v179 升级为通用 tick 卡）：玩家带 A 类每刻效果
            # （套装回血/符文治愈/食物HOT/被动充能/资源regen/状态机维护）→ _ensure_regen_effects
            # 挂通用 tick 条件卡（regen_<kind>），由 _process_until/_advance_time 通用调度处理。
            # 条件挂卡照 pet_tick 先例：无 A 类效果不挂不空转（CTB 测试玩家 equipment={} 零影响）。
            # 仅新建战斗在此挂（_now<=0）；恢复战斗由 from_state/_turn_start 保险丝兜底。
            if not self._enemy_dead() and float(getattr(self, "_now", 0.0) or 0.0) <= 0:
                try:
                    _pl0 = self.player or {}
                    if _pl0 and not self._actor_dead(_pl0):
                        self._ensure_regen_effects(_pl0)
                except Exception as _sw_e:
                    _battle_warn('__init__', _sw_e)
                    pass
            # 开战敌方初始 enemy_act：仅非副本（instance 的 enemy_act 由 from_state 分支补排，
            # 避免新建时排一次 + from_state 恢复再排一次导致敌方双重行动）
            if self.btype != "instance":
                for _u in self.enemies:
                    if _u.get("hp", 0) > 0:
                        _init_t = float(_u.get("ct", 0) or _ct_initial_wait(_u.get("spd", 0)))
                        self._schedule(_init_t, {"type": "enemy_act", "unit": _u})
            # v178.1 DOT 事件驱动：挂 dot（_apply_dot）时排 dot_tick，到点结算该 actor
            # 的 debuffs（玩家/怪同结算器 _tick_actor_dots），结算后仍有 dot 则重排。
            # Boss 定时机制由 _enemy_turn 内 _boss_mech 触发（每次敌方行动时按 r % interval 判定），
            # 不排独立 mech_tick 事件（避免双重触发）。
            # 注：词条/套装回血（regen）不排独立事件——由 player_turn 开头的 _turn_start
            # 在玩家每次行动时结算（与旧时刻制"每玩家行动结算一次"一致），避免 DOT 重复结算。
        except Exception as _sw_e:
            _battle_warn('__init__', _sw_e)
            pass
        # v180F v2.0 通用阵营：播种 self.sides（sides 数据源 + 每 actor side 字段）。
        # 现有引擎仍读 player/enemies/companions 容器（兼容中间态），sides 是权威阵营视图；
        # 后续改造逐步把读点迁到 sides/actor.side。
        self._seed_sides()

    # ---------------- v180F v2.0 通用阵营（sides） ----------------
    def _seed_sides(self) -> dict:
        """把现有玩家侧/敌方侧容器映射为通用阵营视图 self.sides。

        - player side：self.player（焦点）+ self.allies + companions（随从）
        - enemy side：self.enemies（含多 side 时各自保留 side 名）
        - 每 actor 播种 side 字段（缺失时按所属容器补默认）
        - sides 值是**同引用**（非拷贝）——引擎改动 actor 直接反映，序列化据此落档。

        返回 self.sides（dict[str, list[actor]]）。无玩家的战斗（sides 入口怪vs怪）：
        player 可能为空 dict，player side 仍建立（空列表或占位）。
        """
        _player_side = []
        _p = getattr(self, "player", None) or {}
        # 焦点玩家 actor 若无 side 字段 → 补 "player"
        if _p:
            _p.setdefault("side", "player")
            _p.setdefault("kind", "player")
            # 空 dict 占位不算成员（无玩家战斗时 self.player={}）
            if _p.get("class_name") or _p.get("name") or _p.get("qq_id"):
                _player_side.append(_p)
        for _a in (getattr(self, "allies", None) or []):
            if _a is _p:
                continue  # 焦点已在上面（allies 可能含焦点本人）
            _a.setdefault("side", "player")
            _a.setdefault("kind", "player")
            _player_side.append(_a)
        for _c in (getattr(self, "companions", None) or []):
            _c.setdefault("side", "player")
            _player_side.append(_c)
        # enemy side：enemies 各自已有 side 则保留（多敌对阵营），否则补 "enemy"
        _enemy_groups: dict[str, list] = {}
        for _e in (getattr(self, "enemies", None) or []):
            _sn = str(_e.get("side") or "enemy")
            _e.setdefault("side", _sn)
            _e.setdefault("kind", "monster")
            _enemy_groups.setdefault(_sn, []).append(_e)
        sides = {}
        if _player_side:
            sides["player"] = _player_side
        elif _p:
            # 无玩家成员但有 player 占位（sides 入口怪vs怪场景：player 空 dict 不代表真玩家）
            pass
        sides.update(_enemy_groups)
        self.sides = sides
        self._side_names = list(sides.keys())
        return sides

    def side_of(self, actor: dict | None) -> str | None:
        """v180F：返回 actor 所属阵营名（无 actor / 找不到 → None）。"""
        if not actor:
            return None
        _s = actor.get("side")
        if _s:
            return str(_s)
        # 兜底按容器归属判定（side 字段缺失的老 actor）
        if actor is getattr(self, "player", None):
            return "player"
        for _a in (getattr(self, "allies", None) or []):
            if _a is actor:
                return "player"
        for _c in (getattr(self, "companions", None) or []):
            if _c is actor:
                return "player"
        for _e in (getattr(self, "enemies", None) or []):
            if _e is actor or _e.get("uid") == actor.get("uid"):
                return str(_e.get("side") or "enemy")
        return None

    def hostile_sides(self, side: str) -> list:
        """v180F：与某阵营敌对的阵营名列表。

        通用规则：非自身阵营即敌对（混战可多敌对）。引擎不写死"player vs enemy"。
        """
        return [s for s in self._side_names if s != side]

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
        # ⚠️ 不能补 lv：lv 缺失时 _deal_damage 等级压制自然跳过（补 lv=1 会让 30 级玩家对
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
    def summons(self) -> list:
        """v180-C S1 兼容视图：我方召唤物 = companions 里 kind=='summon' 的子集。
        纯读兼容（旧代码遍历/序列化用）；召唤物增删一律直接操作 companions。
        setter 整袋替换：保留同引用（外部写回 st 场景）。"""
        return [c for c in getattr(self, "companions", []) if c.get("kind") == "summon"]

    @summons.setter
    def summons(self, val: list):
        # 整袋设置：保留非 summon 随从，追加 summon 实体
        try:
            _comp = getattr(self, "companions", None)
            if _comp is None:
                self.companions = list(val or [])
                return
            keep = [c for c in _comp if c.get("kind") != "summon"]
            self.companions = keep + [dict(c) for c in (val or [])]
            for c in self.companions:
                c.setdefault("kind", "summon")
                c.setdefault("side", "player")
                c.setdefault("buffs", {})
        except Exception:
            self.companions = list(val or [])

    def _summons_serializable(self) -> list:
        """v180F B6：summons 可序列化快照——深拷贝召唤物 actor，owner 引用 → owner_uid。

        companions 的 owner 字段是内存 actor 引用（B4），直接 json 序列化会循环引用。
        输出用 _owner_uid（qq_id/uid 字符串）替代，恢复后归属靠 _last_player/uid 匹配兜底。
        """
        import copy as _copy
        out = []
        for c in (self.summons or []):
            try:
                cc = _copy.deepcopy(c)
            except Exception:
                cc = dict(c)
            # owner actor dict → _owner_uid 字符串
            try:
                _o = c.get("owner")
                if _o is not None:
                    _ouid = str(_o.get("qq_id") or _o.get("uid") or _o.get("name") or "")
                    if _ouid:
                        cc["_owner_uid"] = _ouid
                cc.pop("owner", None)  # 去掉循环引用
            except Exception:
                cc.pop("owner", None)
            out.append(cc)
        return out

    # v180-B P2：原 mech_stacks property（落 _mech_stacks 实例槽）已删除——
    # 玩家叠层权威改存 player["stacks"]（actor dict 与怪同构），__init__ 播种为实例引用。
    # 外置 battle.mech_stacks 读点在 P4 迁移到 actor 读。

    # ---------------- 序列化 ----------------
    @staticmethod
    def _strip_actor_refs(actor: dict) -> dict:
        """v180F B6：序列化前剥离 actor 内循环引用（_cast.target / owner）。

        战斗中怪 _cast.target 指向另一 actor（B5 目标记录），双方可能互相指向 → json
        循环引用。序列化输出把 _cast.target 转 _target_uid 字符串、owner 转 _owner_uid。
        不修改原 actor（返回新 dict）。
        """
        import copy as _copy
        try:
            a = _copy.deepcopy(actor)
        except Exception:
            a = dict(actor)
        try:
            _cst = a.get("_cast")
            if isinstance(_cst, dict) and _cst.get("target") is not None:
                _t = _cst.pop("target", None)
                if isinstance(_t, dict):
                    _tu = str(_t.get("qq_id") or _t.get("uid") or _t.get("name") or "")
                    if _tu:
                        _cst["_target_uid"] = _tu
        except Exception as _sw_e:
            _battle_warn('_strip_actor_refs', _sw_e)
            pass
        try:
            _o = a.get("owner")
            if _o is not None:
                _ou = str(_o.get("qq_id") or _o.get("uid") or _o.get("name") or "")
                if _ou:
                    a["_owner_uid"] = _ou
                a.pop("owner", None)
        except Exception:
            a.pop("owner", None)
        return a

    def to_state(self) -> dict:
        _pl = self.player or {}
        _p_res = _pl.setdefault("resources", {})
        _p_stacks = _pl.setdefault("stacks", {})
        _p_eff = _pl.setdefault("eff", {})
        _p_shields = _pl.setdefault("shields", {})
        _p_hot = _pl.setdefault("hot", {})
        _p_food = _pl.setdefault("food_effects", [])
        _p_cooldown = _pl.setdefault("cooldown", {})
        _p_combo = _pl.setdefault("combo_seq", [])
        _p_buffs = _pl.setdefault("buffs", {})
        return {
            "type": self.btype,
            # v152：round 概念删除，改 _now（绝对时刻）+ _p_acts（玩家行动计数，展示用）
            "now": self._now,
            "p_acts": self._p_acts,
            # v2：敌方完整阵列（核心）；enemy 保留为兼容键（= 主目标引用）
            # v180F B6：序列化前剥离 actor 循环引用（_cast.target/owner → uid）
            "enemy": self._strip_actor_refs(self.enemy),
            "enemies": [self._strip_actor_refs(u) for u in self.enemies],
            "killed_enemies": getattr(self, "killed_enemies", []),  # v130.7 意见#17 击杀记录随战斗持久化（跨消息续战胜利不丢）
            # v180-B：玩家战斗状态已存 player actor dict——序列化输出沿用旧顶层键结构
            #（老档兼容读），值从 player dict 读
            "charging": _pl.get("charging"),
            "pet": self.pet,
            "p_buffs": _p_buffs,
            # v151 时刻制：防御型 buff 受击计数（随战斗序列化，跨消息续战不丢）
            "p_buff_hits": _pl.get("buff_hits") or {},
            # v113.1 团队减伤 reduce_all 剩余刻：percent 存 p_buffs、刻数独立计时，
            # 必须随存档持久化，否则恢复后 __init__=0 被下刻立即弹掉 reduce_all。
            "reduce_all_left": _pl.get("reduce_all_left", 0) or 0,
            # v162 单人减伤 reduce 剩余刻（铁壁/铜墙）
            "reduce_left": _pl.get("reduce_left", 0) or 0,
            "poi_buff": _pl.get("poi_buff"),
            "p_hot": _p_hot,
            "p_food_effects": _p_food,
            "p_shields": _p_shields,
            # v101.28l 旧观兼容键保留（= 敌方阵列中 summon 型援军副本，命令层写回用）
            "e_minions": self.e_minions,
            # v180F B6：序列化时 summons 清洗 owner 循环引用——owner actor dict 引用 → owner_uid
            # 字符串（uuid/qq_id），防 json 序列化循环引用；恢复后靠 _last_player 兜底归属
            "summons": self._summons_serializable(),
            "e_buffs": self.e_buffs,
            "p_defending": bool(_pl.get("defending", False)),
            "e_defending": self.e_defending,
            "title_bonus": self.title_bonus,
            "mech_stacks": _p_stacks,
            "resources": _p_res,
            # v130.2 物品效果持久数据（resource_amp/mana_cost_down/buff_phys_next/phys_up/战前预充标记）
            "eff_data": _p_eff,
            "cooldown": _p_cooldown,
            "combo_seq": _p_combo,
            "last_combo_tag": _pl.get("last_combo_tag"),
            # v180 审计：last_element 补序列化（元素法师同系连发跨行动记忆，断线续战不丢）
            "last_element": _pl.get("last_element"),
            "p_ct": self.p_ct,
            "player_hit": self._player_hit,
            "first_attack_done": self.first_attack_done,
            "death_pact_used": getattr(self, "_death_pact_used", False),
            "set_immune_used": getattr(self, "_set_immune_used", False),
            # v169.7 被动一次性/次数标记随战斗序列化（坚韧剩余次数 / 血怒·不灭 / 铁誓·不动 / 不动如山）
            "tenacity_left": getattr(self, "_tenacity_left_n", 3),
            "berserk_revive_used": getattr(self, "_berserk_revive_used", False),
            "stance_immortal_used": getattr(self, "_stance_immortal_used", False),
            "core_last_stand_used": getattr(self, "_core_last_stand_used", False),
            # v130.2f 致命预谋：首次终结返还标记（随战斗持久化，防断线恢复后重复返还）
            "assassin_refund_used": getattr(self, "_assassin_refund_used", False),
            # v104 M02 P2-9：断线恢复后 burst 机制（灼烧引爆/剑刃风暴/神恩护盾）与
            # 元素跃迁日志依赖 _last_player/_shifted_element，必须随战斗状态持久化
            "last_player": getattr(self, "_last_player", None),
            "shifted_element": getattr(self, "_shifted_element", None),
            "tailwind_prev_energy": _pl.get("tailwind_prev_energy"),  # v130.2d 疾风余韵跨刻状态
            "overflow_shield_cd": bool(_pl.get("overflow_shield_cd", False)),  # v130.2f2 满溢转盾冷却（断线恢复不重置冷却）
            # v139 职业融合：模式状态机随战斗序列化（dual_form/focus/vent + charge 电荷）
            "v139_modes": _pl.get("v139_modes") or {},
            "v139_charge": _pl.get("v139_charge") or {},
            # v154 读条命中制：玩家读条状态随战斗持久化（断线恢复不丢读条）
            "player_casting": getattr(self, "_player_casting", False),
            "pending_player_cast": getattr(self, "_pending_player_cast", None),
            # v179 通用 tick 效果：条目随战斗序列化（actor 存引用——"player" 或敌人 uid 索引，
            # from_state 恢复时重绑；data 里不能有 actor dict 引用，纯数据）
            "tick_effects": [
                {
                    "uid": e.get("uid"), "kind": e.get("kind"),
                    "interval": e.get("interval"), "next_at": e.get("next_at"),
                    "expire_at": e.get("expire_at"), "data": e.get("data") or {},
                    "source": e.get("source", ""),
                    "actor_ref": ("player" if (e.get("actor") is self.player)
                                  else ("pet" if (e.get("actor") is self.pet)
                                        else ("comp:" + str((e.get("actor") or {}).get("uid", "") or (e.get("actor") or {}).get("name", ""))
                                              if any(c is e.get("actor") for c in (getattr(self, "companions", None) or []))
                                              else next((str(u.get("uid", "")) for u in self.enemies
                                                         if u is e.get("actor")), "")))),
                }
                for e in getattr(self, "tick_effects", [])
            ],
            # v180F B6：sides 阵营完整快照（通用 actor 引擎落档——怪vs怪等无玩家战斗
            # 靠它恢复阵营结构；玩家战斗冗余但无害）。深拷贝 + owner 清洗防循环引用。
            "sides_snapshot": self._sides_snapshot(),
        }

    def _sides_snapshot(self) -> dict:
        """v180F B6：sides 可序列化快照——每阵营 actor 深拷贝，owner/_cast.target → uid。

        仅当战斗有非标准阵营（自定义 side 名 / 无玩家）时输出完整 sides；常规玩家 vs
        enemy 战斗 sides 可退化（players 侧由命令层快照承载，不重复落档）。
        """
        sides = getattr(self, "sides", None) or {}
        # 判断是否需要完整 sides 快照：存在非 player/enemy 的阵营 = 通用 actor 战斗
        _custom = [s for s in sides if s not in ("player", "enemy")]
        if not _custom:
            # 常规战斗：仅记录 player side 成员 uid 列表 + enemy side 已在 enemies 落档
            return {"_custom": False}
        out = {}
        for _sn, _acts in sides.items():
            out[_sn] = [self._strip_actor_refs(a) for a in _acts]
        out["_custom"] = True
        return out

    def _load_player_state(self, qq_id) -> dict | None:
        """v173.6 重构（v180-B ①更新）：副本敌方行动选目标后切换结算焦点。

        副本玩家状态权威 = 玩家快照 dict（actor dict，含 buffs/resources/stacks/...）。
        旧架构把状态载入 Battle 单套焦点字段；v180-B 后 Battle.player 直接指向目标玩家
        快照，并把 st 顶层 per-player 旁路键（p_buffs/resources/cooldown/...）合并进快照
        （P3 双轨折叠前的兼容读取；instance.py 后续迁移后 st 顶层键不再写）。

        返回该玩家快照 dict；找不到/已死返回 None。野外（无 _st）无操作返回 None。
        """
        if not self._st:
            return None
        try:
            st = self._st
            key = str(qq_id)
            snap = (st.get("players") or {}).get(key)
            if not snap or not (st.get("alive") or {}).get(key, True):
                return None
            # 目标玩家快照即 actor dict——切焦点 = self.player 指向它
            self.player = snap
            # 播种快照 actor 键（老档/旧开本可能缺）
            _ = snap.setdefault("buffs", {})
            snap.setdefault("resources", {})
            snap.setdefault("stacks", {})
            snap.setdefault("eff", {})
            snap.setdefault("shields", {})
            snap.setdefault("cooldown", {})
            snap.setdefault("combo_seq", [])
            snap.setdefault("hot", {})
            snap.setdefault("food_effects", [])
            snap.setdefault("buff_hits", {})
            snap.setdefault("defending", False)
            snap.setdefault("charging", None)
            snap.setdefault("last_combo_tag", None)
            snap.setdefault("poi_buff", None)
            # v180 审计：last_element 快照缺失时从 st 顶层读（老档/断线续战不丢同系连发记忆）
            if snap.get("last_element") is None and st.get("last_element") is not None:
                snap["last_element"] = st.get("last_element")
            snap.setdefault("reduce_all_left", 0)
            snap.setdefault("reduce_left", 0)
            # 从 st 顶层 per-player 旁路键合并（P3 前双轨兼容；快照自身键优先）
            snap["buffs"].clear()
            snap["buffs"].update((st.get("p_buffs") or {}).get(key, {}))
            snap["buff_hits"] = dict((st.get("p_buff_hits") or {}).get(key, {}))
            snap["reduce_all_left"] = int((st.get("reduce_all_left") or {}).get(key, snap.get("reduce_all_left", 0) or 0) or 0)
            snap["reduce_left"] = int((st.get("reduce_left") or {}).get(key, snap.get("reduce_left", 0) or 0) or 0)
            if (st.get("poi_buff") or {}).get(key) is not None:
                snap["poi_buff"] = (st.get("poi_buff") or {}).get(key)
            _h = (st.get("p_hot") or {}).get(key)
            if _h is not None:
                snap["hot"] = _h
            _fe = (st.get("p_food_effects") or {}).get(key)
            if _fe is not None:
                snap["food_effects"] = _fe
            _sh = (st.get("p_shields") or {}).get(key)
            if _sh is not None:
                snap["shields"] = _sh
            if (st.get("charging") or {}).get(key) is not None:
                snap["charging"] = (st.get("charging") or {}).get(key)
            snap["defending"] = bool((st.get("p_defending") or {}).get(key, snap.get("defending", False)))
            _ms = (st.get("mech_stacks") or {}).get(key)
            if _ms is not None:
                snap["stacks"] = dict(_ms) or {}
            _rs = (st.get("resources") or {}).get(key)
            if _rs is not None:
                snap["resources"] = dict(_rs) or {}
            _cd = (st.get("cooldown") or {}).get(key)
            if _cd is not None:
                snap["cooldown"] = dict(_cd) or {}
            _cq = (st.get("combo_seq") or {}).get(key)
            if _cq is not None:
                snap["combo_seq"] = list(_cq) or []
            self.summons = (st.get("summons") or {}).get(key, []) or []
            self._pending_player_cast = None
            self._player_casting = False
            self._last_focused_qid = key  # v173.6 当前结算目标记录（instance 读回实际目标）
            return snap
        except Exception:
            return None

    def _apply_restore_pstate(self):
        """v180-B ①：把 from_state 暂存的玩家战斗状态（_restore_pstate）灌入当前绑定的
        玩家 actor dict。仅灌一次（灌后清空 _restore_pstate）。player_turn 入口自动调用；
        测试/命令层 from_state 后直接操作前可手动调（先绑 b.player=玩家快照）。"""
        if not getattr(self, "_restore_pstate", None):
            return
        _plb = self.player
        if not _plb:
            return  # player 未绑定（空 dict）→ 保留暂存等真绑（player_turn 绑定后再灌）
        try:
            _rst = self._restore_pstate
            _plb = self.player
            for _k, _v in _rst.items():
                if _k == "stacks":
                    _plb.setdefault("stacks", {}).update(_v or {})
                elif _k == "resources":
                    _plb.setdefault("resources", {}).update(_v or {})
                elif _k == "eff":
                    _plb.setdefault("eff", {}).update(_v or {})
                elif _k == "buffs":
                    _plb.setdefault("buffs", {}).update(_v or {})
                elif _k == "hot":
                    _plb.setdefault("hot", {}).update(_v or {})
                elif _k == "food_effects":
                    _plb["food_effects"] = list(_v or [])
                elif _k == "cooldown":
                    _plb.setdefault("cooldown", {}).update(_v or {})
                elif _k == "combo_seq":
                    _plb["combo_seq"] = list(_v or [])
                else:
                    _plb[_k] = _v
        except Exception as _sw_e:
            _battle_warn('_apply_restore_pstate', _sw_e)
            pass
        self._restore_pstate = None

    def _pick_enemy_target(self, unit: dict) -> dict | None:
        """v173.6 副本敌方行动选目标（battle 侧，多目标重构）。
        从 allies（全存活玩家快照）按 monster_mods target_policy 选目标：
          hate_top（点名仇恨最高）/ random / weakest / backline（后排）/ front（前排，默认）
        并 _load_player_state 载入该玩家状态到单套字段（结算用）。
        返回目标玩家快照；无可用目标返回 None。"""
        try:
            if not self._st or not self.allies:
                return None
            from .core import formation as FM
            alive = [p for p in self.allies
                     if (self._st.get("alive") or {}).get(str(p.get("qq_id") or ""), True)]
            if not alive:
                return None
            # 嘲讽强制优先
            taunt_key = str(self._st.get("taunt_target", ""))
            if taunt_key:
                for p in alive:
                    if str(p.get("qq_id")) == taunt_key:
                        self._load_player_state(taunt_key)
                        return p
            # 仇恨表（uid → threat）
            _threat = {}
            for p in alive:
                _q = str(p.get("qq_id") or "")
                _threat[str(p.get("uid") or f"p_{_q}")] = (self._st.get("threat") or {}).get(_q, 0)
            # target_policy（monster_mods 数据）
            _tpol = ""
            try:
                _tpol = str((C.MONSTER_MODS.get(unit.get("id") or "", {}) or {}).get("target_policy", "") or "")
            except Exception:
                _tpol = ""
            # 默认：boss 全层仇恨（all）/ 其他 front
            if not _tpol:
                _tpol = "hate_top" if str(unit.get("role", "")) == "boss" else "front"
            picked = FM.pick_by_policy(_tpol, alive, threat=_threat)
            if picked is not None:
                self._load_player_state(str(picked.get("qq_id") or ""))
            return picked
        except Exception:
            return None

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
        # v180E 阶段6：__init__ 在 _now=0 时可能已挂 pet_act 初始卡（恢复路径 _now 由上方
        # 才设为存档值，__init__ 阶段判断不到）——若存档带序列化 pet_act 卡，先清掉
        # __init__ 误挂的（恢复段会按存档重绑精确节奏），避免双卡。
        if st.get("tick_effects") and any(
                _e.get("uid") == "pet_act" for _e in (st.get("tick_effects") or [])):
            b.tick_effects = [e for e in b.tick_effects if e.get("uid") != "pet_act"]
        # v158 副本合并：from_state 透传副本回调钩子（instance 注入 st["_cb"]）
        b._inst_cb = st.get("_cb") if isinstance(st, dict) else None
        b.allies = st.get("allies") or []   # v122 治疗指定队友（副本传存活玩家快照引用）
        # v180-B：玩家战斗状态权威 = player actor dict。from_state 构造时 player 可能未绑定
        #（命令层后绑 b.player = 真实玩家），恢复的玩家战斗状态先暂存 b._restore_pstate，
        # 命令层绑 player 后经 _bind_player/_restore_player_state 灌入（见 player_turn 收口）。
        b._restore_pstate = {
            "buffs": dict(st.get("p_buffs") or {}),
            "buff_hits": dict(st.get("p_buff_hits") or {}),
            "reduce_all_left": int(st.get("reduce_all_left", 0) or 0),
            "reduce_left": int(st.get("reduce_left", 0) or 0),
            "poi_buff": st.get("poi_buff"),
            "hot": st.get("p_hot", {}) or {},
            "food_effects": st.get("p_food_effects", []) or st.get("p_food_affixes", []) or [],
            "shields": st.get("p_shields", {}) or {},
            "charging": st.get("charging"),
            "defending": st.get("p_defending", False),
            "stacks": st.get("mech_stacks", {}) or {},
            "resources": st.get("resources", {}) or {},
            "eff": st.get("eff_data", {}) or {},
            "cooldown": st.get("cooldown", {}) or {},
            "combo_seq": st.get("combo_seq", []) or [],
            "last_combo_tag": st.get("last_combo_tag") or None,
            "last_element": st.get("last_element"),
            "tailwind_prev_energy": st.get("tailwind_prev_energy"),
            "v139_modes": st.get("v139_modes", {}) or {},
            "v139_charge": st.get("v139_charge", {}) or {},
            "overflow_shield_cd": bool(st.get("overflow_shield_cd", False)),
            "stealth_atk": False,
        }
        b.e_minions = st.get("e_minions", []) or []
        b.killed_enemies = [dict(u) for u in (st.get("killed_enemies") or [])]  # v130.7 意见#17 击杀记录恢复
        b.summons = st.get("summons", []) or []
        b.e_defending = st.get("e_defending", False)
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
        b._tenacity_left_n = int(st.get("tenacity_left", 3) or 3)
        b._berserk_revive_used = bool(st.get("berserk_revive_used", False))
        b._stance_immortal_used = bool(st.get("stance_immortal_used", False))
        b._core_last_stand_used = bool(st.get("core_last_stand_used", False))
        b._assassin_refund_used = bool(st.get("assassin_refund_used", False))  # v130.2f 致命预谋返还标记
        # v154 读条命中制：恢复玩家读条状态（断线恢复不丢读条）
        b._player_casting = bool(st.get("player_casting", False))
        b._pending_player_cast = st.get("pending_player_cast")
        # v104 M02 P2-9：恢复 _last_player/_shifted_element；_last_player 为空保持
        # 未设置（hasattr=False，避免 battle_mech 对 None 调 _player_stats 崩溃）
        _lp = st.get("last_player")
        if _lp:
            b._last_player = _lp
        b._shifted_element = st.get("shifted_element")
        # v139/v130.2d/v130.2f2 状态已收进 _restore_pstate（v180-B）——此处不再设实例属性
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
                    b._restore_pstate["stacks"].pop(_k, None)
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
        # v178.2 regen_tick（v179 升级通用卡）：tick_effects 已随 to_state/from_state 序列化恢复
        # （P0），此处兜底：老档无 tick_effects 字段 + player 已可用（调用方先绑定）→ 挂卡。
        # 注意 from_state 恢复的 b.player 默认空 dict（真实玩家由调用方后续绑定），
        # 恢复后首次玩家行动由 _turn_start 保险丝兜底挂卡（玩家真实可用）。
        try:
            _pl_r = b.player or {}
            if _pl_r.get("class_name") and not b._enemy_dead():
                b._ensure_regen_effects(_pl_r)
        except Exception as _sw_e:
            _battle_warn('from_state', _sw_e)
            pass
        # v163 敌方读条持久化：恢复读条中的敌方 cast_done（_enemy_turn 出手时写 e["_cast"]，
        # 随 enemies 序列化；野外/副本统一）。此前事件队列不序列化，读条伤害跨消息即丢
        # （repro_enemy_cast_loss.py 复现：野外单怪挥爪后存档恢复，伤害蒸发为 0）。
        for _u in b.enemies:
            _cst = _u.get("_cast")
            if _cst and _u.get("hp", 0) > 0:
                _hit = float(_cst.get("hit_at", 0) or 0)
                if _hit > b._now:
                    # v180F B6：恢复目标 actor（_target_uid → enemies/sides 里解析；
                    # 怪vs怪读条续战不丢目标）
                    _tgt = None
                    _tu = _cst.get("_target_uid") or ""
                    if _tu:
                        for _u2 in b.enemies:
                            if str(_u2.get("qq_id") or _u2.get("uid") or _u2.get("name") or "") == _tu:
                                _tgt = _u2
                                break
                    b._schedule(_hit, {"type": "cast_done", "side": "e", "unit": _u,
                                       "kind": _cst.get("kind", "atk"),
                                       "skill": _cst.get("skill"),
                                       "power_mult": _cst.get("power_mult", 1.0),
                                       "target": _tgt})
        # v180G B6 玩家出手挂起恢复（同敌方 _cast 样板）：扫 allies（副本玩家快照引用）
        # 的 _cast——多人 CTB 下 A 出手挂起的命中事件在 B 的 Battle 恢复补排，按 hit_at
        # 绝对时刻触发（谁先命中谁先结算）。野外/单人 allies 空/无 _cast → 无影响。
        for _pa in (b.allies or []):
            _pcs = _pa.get("_cast")
            if _pcs and _pa.get("hp", 0) > 0:
                _phit = float(_pcs.get("hit_at", 0) or 0)
                if _phit > b._now:
                    _ptu = _pcs.get("_target_uid") or ""
                    _ptgt = None
                    if _ptu:
                        for _u2 in b.enemies:
                            if str(_u2.get("qq_id") or _u2.get("uid") or _u2.get("name") or "") == _ptu:
                                _ptgt = _u2
                                break
                    b._schedule(_phit, {"type": "cast_done", "side": "p", "kind": _pcs.get("kind", "atk"),
                                        "skill": _pcs.get("skill"), "player_ref": _pa, "target": _ptgt})
        # v179 通用 tick 效果恢复：actor_ref 重绑（"player"→b.player（调用方后续绑定真实玩家，
        # 此刻可能是空 dict——效果 actor 若为玩家，恢复时 actor 先用 b.player 占位，命令层绑定
        # 真实玩家后同一引用即生效）；"pet"→b.pet（v180E 阶段6：宠物 actor 卡不再丢）；
        # 敌人 uid → enemies 里对应单位）。
        try:
            _te_st = st.get("tick_effects") or []
            for _e_st in _te_st:
                _actor = None
                _ref = _e_st.get("actor_ref", "")
                if _ref == "player":
                    _actor = b.player
                elif _ref == "pet" and b.pet:
                    _actor = b.pet
                elif _ref.startswith("comp:"):
                    # v180F 清2d：companion actor tick 卡恢复（原序列化空引用 → 恢复丢卡）
                    _cu = _ref[5:]
                    for _c in (getattr(b, "companions", None) or []):
                        if str(_c.get("uid", "") or _c.get("name", "")) == _cu:
                            _actor = _c
                            break
                else:
                    for _u in b.enemies:
                        if str(_u.get("uid", "")) == str(_ref):
                            _actor = _u
                            break
                if _actor is None:
                    continue  # 找不到 actor → 丢弃（目标已死/不存在）
                b.tick_effects.append({
                    "uid": _e_st.get("uid"), "kind": _e_st.get("kind"),
                    "actor": _actor, "interval": float(_e_st.get("interval", 1) or 1),
                    "next_at": float(_e_st.get("next_at", b._now) or b._now),
                    "expire_at": _e_st.get("expire_at"),
                    "data": _e_st.get("data") or {}, "source": _e_st.get("source", ""),
                })
        except Exception as _sw_e:
            _battle_warn('from_state', _sw_e)
            pass
        # v167.3 副本带宠物（v179 P4 升级通用卡）：pet_act 卡兜底补挂（在 tick 恢复段之后——
        # v180E 阶段6：序列化卡先恢复 actor_ref="pet" 直接重绑；无卡时此处补挂老档/旧版存档）
        if b.pet and int(b.pet.get("level", 0) or 0) >= int(C.PET_SKILL_UNLOCK_LV) and not b._enemy_dead():
            _has_pet_tick = any(e.get("uid") == "pet_act" for e in b.tick_effects)
            if not _has_pet_tick:
                try:
                    b._pet_ensure_actor()  # v180-C S3：宠物 actor 化（恢复路径也补 actor 字段）
                    b._pet_ensure_guard()  # v180-B ②：恢复路径也补 guard（老档 pet 无 guard）
                    # v179 修正：初始周期 = 面板 skill_interval（每 N 刻一次），非读条
                    _pt = b._pet_interval_sec()
                    b.add_tick_effect("pet_act", b.pet, max(_pt, 0.001),
                                      uid="pet_act", source="pet")
                except Exception as _sw_e:
                    _battle_warn('from_state', _sw_e)
                    pass
        # v180F B6：sides_snapshot 恢复——通用 actor 战斗（怪vs怪/自定义阵营）落档后重建。
        # 快照含每阵营 actor 深拷贝；enemies 在构造时已从 st["enemies"] 载入（含全部非 player
        # side actor），此处仅重播种 side 字段 + 重建 self.sides 权威视图。
        try:
            _snap = st.get("sides_snapshot") or {}
            if _snap.get("_custom"):
                _rebuilt = {}
                for _sn, _acts in _snap.items():
                    if _sn == "_custom":
                        continue
                    # 从快照恢复 actor（enemies 里已有同 uid 的 → 用现有的保持引用一致；
                    # 找不到 → 用快照 dict）
                    _arr = []
                    for _sa in _acts:
                        _uid = str(_sa.get("uid", ""))
                        _found = None
                        for _u in b.enemies:
                            if str(_u.get("uid", "")) == _uid:
                                _found = _u
                                break
                        if _found is None:
                            _found = dict(_sa)
                            _found.pop("_owner_uid", None)
                            b.enemies.append(_found)
                        _found.setdefault("side", _sn)
                        _arr.append(_found)
                    _rebuilt[_sn] = _arr
                if _rebuilt:
                    b.sides = _rebuilt
                    b._side_names = list(_rebuilt.keys())
        except Exception as _sw_e:
            _battle_warn('from_state', _sw_e)
            pass
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
            # v176: (cls, 0) 空元组 = 基础态无资源（原 842 行 cls_fa_shi 特判数据化）
            return list(ov)
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
        # v139 桥接：把 self._p_v139_modes()/_v139_charge 挂到 player dict 上，
        # 让 battle_modes/battle_bars 纯函数读写正确的状态源（状态统一存 self）
        if player is not None:
            player["v139_modes"] = self._p_v139_modes()
            player["v139_charge"] = self._p_v139_charge()
        return int(player.get("evolve_path", 0) or 0) == int(path or 0)

    def _is_element_mage(self, player: dict) -> bool:
        """元素法师（法师·攻线）判定——v181 收口：归属读分支资源表 BRANCH_RESOURCE_OVERRIDE
        （(cls_fa_shi,1)/(cls_fa_shi,2) 声明 element 充能资源）+ 攻线 path=1；
        v176 单点收口（原 7 处 cls_fa_shi+_is_path(1) 散落特判 → 数据表驱动）。"""
        cls = player.get("class_name", "")
        if not self._is_path(player, 1):
            return False
        return "element" in (BRANCH_RESOURCE_OVERRIDE.get((cls, 1)) or ())

    @staticmethod
    def _is_element_skill(info: dict) -> bool:
        """元素/奥术技能判定——技能带 element 字段或 res_gain element（v176 解耦：
        原 1145/5092 处额外判 cls_fa_shi——但 element 技能天然只有法师拥有，职业判断冗余删除）。"""
        if not info:
            return False
        return bool(info.get("element") or (info.get("res_gain") or {}).get("element"))

    def _elem_charge(self) -> int:
        """法师充能条当前值（v130.2：element 资源数值化 0-5；resources['element'] 保留当前系字符串，兼容旧消费点）
        v180-B：读焦点玩家 actor dict（与怪 actor 同构）。"""
        _pl = self.player or {}
        return int(_pl.setdefault("resources", {}).get("element_charge", 0) or 0)

    # ---------------- v177 施法者状态路由（玩家技能管线 actor 化） ----------------
    # 管线内 self._p_buffs_bag()/self._p_res()/self._p_stacks() 是"当前施法者"状态：
    # 玩家施法 → 焦点字段（原语义）；怪物施法（_cast_ctx=unit）→ unit 自身字段。
    def _tgt(self) -> dict:
        """v177 技能管线目标 actor：玩家施法=当前敌人；怪物施法玩家技能=玩家（_target_ctx 设置）。"""
        u = self._target_ctx
        if u is not None:
            return u
        return self.enemy

    def _tgt_buffs(self) -> dict:
        """v177 技能管线目标 buffs（同 _tgt，buff actor 化——目标 buffs 在目标 dict 上）。"""
        return self._tgt().setdefault("buffs", {})

    def _tgt_is_player(self) -> bool:
        """v177 管线目标是否为玩家（怪物施法玩家技能时 _target_ctx=玩家 → True）。
        v180-B：身份判定用 _is_player_side（side/引用/我方），不用 class_name——
        怪扮职业（配 class_name 的怪）不会被误判成玩家。"""
        u = self._target_ctx
        if u is None:
            return False
        return self._is_player_side(u)

    def _deal_hit(self, dmg: int, logs: list, wake_sleep: bool = True, source=None,
                  dmg_kind: str = "") -> int:
        """v177 技能管线伤害落点（双向）：玩家施法 → 打敌人（原 _deal_damage 全语义）；
        怪物施法玩家技能（_target_ctx=玩家）→ 打玩家（走 _damage_actor 玩家承伤链）。
        v180F 收编配套：dmg_kind 透传（phys/magi/混合），玩家受击减免在 _damage_actor 消费。
        返回实际扣血。"""
        if dmg <= 0:
            return 0
        try:
            if self._tgt_is_player():
                return self._damage_actor(self._tgt(), dmg, logs, source=str(source or "敌人"),
                                          dmg_kind=dmg_kind)
            return self._deal_damage(dmg, logs, wake_sleep=wake_sleep, source=source)
        except Exception:
            return dmg

    def _cast_buffs(self) -> dict:
        u = self._cast_ctx
        if u is not None:
            return u.setdefault("buffs", {})
        return self._p_buffs_bag()

    def _cast_eff(self) -> dict:
        u = self._cast_ctx
        if u is not None:
            return u.get("eff") or {}
        return self._p_eff()

    def _cast_res(self) -> dict:
        u = self._cast_ctx
        if u is not None:
            return u.setdefault("resources", {})
        return self._p_res()

    def _cast_stacks(self) -> dict:
        u = self._cast_ctx
        if u is not None:
            return u.setdefault("stacks", {})
        return self._p_stacks()

    def _cast_stats(self) -> dict:
        """v180F A3：施法者面板按 actor 身份路由（_actor_stats_of 玩家公式/怪公式通用）。
        原实现 `_cast_ctx 非空 → _enemy_stats(u)` 写死怪公式——若施法者是玩家侧
        非焦点 actor（随从/召唤物扮职业等）面板会错读。现在任意 actor 走 _actor_stats_of。"""
        u = self._cast_ctx
        if u is not None:
            return self._actor_stats_of(u)
        return self._player_stats(self.player)

    def _cast_is_player(self) -> bool:
        return self._cast_ctx is None

    # ---------------- v180-B P2：焦点玩家 actor 取袋 helper ----------------
    # 迁移后 Battle 不再持有"玩家焦点状态字段"——玩家战斗可变状态权威在
    # self.player（当前行动玩家）actor dict 上。以下 helper 是"读当前玩家 actor
    # 某状态袋"的语义口（与怪 actor dict 同构），所有原 self.xxx 读点经它们收口。
    # setdefault 惰性建袋：self.player 未绑定/测试空 dict 时安全返回空袋。
    def _p_res(self) -> dict:
        return (self.player or {}).setdefault("resources", {})

    def _p_stacks(self) -> dict:
        return (self.player or {}).setdefault("stacks", {})

    def _p_eff(self) -> dict:
        return (self.player or {}).setdefault("eff", {})

    def _p_shields_bag(self) -> dict:
        return (self.player or {}).setdefault("shields", {})

    def _p_buffs_bag(self) -> dict:
        return (self.player or {}).setdefault("buffs", {})

    # ---- v180-B P2：玩家 actor 标量/列表袋 helper（原 Battle 焦点字段迁移） ----
    def _p_charging(self):
        return (self.player or {}).get("charging")

    def _p_set_charging(self, val):
        (self.player or {})["charging"] = val

    def _p_cooldown(self) -> dict:
        return (self.player or {}).setdefault("cooldown", {})

    def _p_combo_seq(self) -> list:
        return (self.player or {}).setdefault("combo_seq", [])

    def _p_last_combo_tag(self):
        return (self.player or {}).get("last_combo_tag")

    def _p_set_last_combo_tag(self, val):
        (self.player or {})["last_combo_tag"] = val

    def _p_hot(self) -> dict:
        return (self.player or {}).setdefault("hot", {})

    def _p_food_effects(self) -> list:
        return (self.player or {}).setdefault("food_effects", [])

    def _p_defending(self) -> bool:
        return bool((self.player or {}).get("defending", False))

    def _p_set_defending(self, val: bool):
        (self.player or {})["defending"] = bool(val)

    def _p_buff_hits(self) -> dict:
        return (self.player or {}).setdefault("buff_hits", {})

    def _p_reduce_all_left(self) -> int:
        return int((self.player or {}).get("reduce_all_left", 0) or 0)

    def _p_set_reduce_all_left(self, val: int):
        (self.player or {})["reduce_all_left"] = int(val or 0)

    def _p_reduce_left(self) -> int:
        return int((self.player or {}).get("reduce_left", 0) or 0)

    def _p_set_reduce_left(self, val: int):
        (self.player or {})["reduce_left"] = int(val or 0)

    def _p_poi_buff(self):
        return (self.player or {}).get("poi_buff")

    def _p_set_poi_buff(self, val):
        (self.player or {})["poi_buff"] = val

    def _p_last_element(self):
        return (self.player or {}).get("last_element")

    def _p_set_last_element(self, val):
        (self.player or {})["last_element"] = val

    def _p_tailwind_prev_energy(self):
        return (self.player or {}).get("tailwind_prev_energy")

    def _p_set_tailwind_prev_energy(self, val):
        (self.player or {})["tailwind_prev_energy"] = val

    def _p_v139_modes(self) -> dict:
        return (self.player or {}).setdefault("v139_modes", {})

    def _p_v139_charge(self) -> dict:
        return (self.player or {}).setdefault("v139_charge", {})

    def _p_overflow_shield_cd(self) -> bool:
        return bool((self.player or {}).get("overflow_shield_cd", False))

    def _p_set_overflow_shield_cd(self, val: bool):
        (self.player or {})["overflow_shield_cd"] = bool(val)

    def _p_stealth_atk(self) -> bool:
        return bool((self.player or {}).get("stealth_atk", False))

    def _p_set_stealth_atk(self, val: bool):
        (self.player or {})["stealth_atk"] = bool(val)

    def _res_def_of(self, actor: dict) -> dict:
        """v177 actor 资源定义：actor 带 resource_def（怪物/自定义）→ 用它；
        否则回退玩家职业定义（CORE_RESOURCES by class_name）。"""
        if not actor:
            return {}
        rd = actor.get("resource_def")
        if isinstance(rd, str):
            # 引用 CORE_RESOURCES key（怪物复用玩家资源条目，如 resource_def: "rage"）
            _by_key = E.core_resource_def_by_key(rd) or {}
            if _by_key:
                return _by_key
            # 兜底：CORE_RESOURCES 条目以 key 字段注册（rage 在 cls_zhan_shi 内），按 key 值扫描匹配
            try:
                from .data.core_resources import CORE_RESOURCES
                for _cid, _crd in CORE_RESOURCES.items():
                    if _crd.get("key") == rd:
                        return dict(_crd)
            except Exception as _sw_e:
                _battle_warn('_res_def_of', _sw_e)
                pass
            return {}
        if isinstance(rd, dict):
            return rd
        return E.core_resource_def(actor.get("class_name", ""))

    def _res_read(self, key: str) -> int:
        """读取当前焦点 actor 资源值（element → 充能条 element_charge；其余直读 resources[key]）"""
        if key == "element":
            return self._elem_charge()
        return int(self._p_res().get(key, 0) or 0)

    def _res_read_actor(self, actor: dict, key: str) -> int:
        """v177 读取指定 actor 资源值（玩家/怪物同一套——只路由存储袋，不分叉逻辑）。"""
        if not actor:
            return self._res_read(key)
        if actor.get("class_name"):
            return self._res_read(key)
        bag = actor.setdefault("resources", {})
        if key == "element":
            return int(bag.get("element_charge", 0) or 0)
        return int(bag.get(key, 0) or 0)

    def _res_gain(self, actor: dict, key: str, amount: int, logs: list | None = None) -> int:
        """资源增加（带上限）。v177 actor 统一：玩家/怪物同一套逻辑，仅存储袋与定义来源路由。
        - 玩家 actor（有 class_name）→ 焦点 resources + CORE_RESOURCES 职业定义（词条/套装上限加成）
        - 怪物/自定义 actor（无 class_name，带 resource_def 或裸资源袋）→ actor["resources"] + resource_def
        element → 充能条；echo → 驻留叠层；按 key 注册副资源 → core_resource_gain_key。
        v130.2 P1-3 修复：写回不静默（调用方丢弃返回值也落库正确）。
        v130.2 R1：logs 可选透传——echo 分支经 _echo_add 产出「🎵 回声驻留 +N」反馈（歌者施放可见）。"""
        if not actor:
            return 0
        # ---- 怪物/自定义 actor（无职业定义链）：走 actor 资源袋 + resource_def 上限 ----
        if not actor.get("class_name"):
            rd = self._res_def_of(actor)
            bag = actor.setdefault("resources", {})
            if key == "element":
                bag["element_charge"] = min(int(rd.get("max", 5) or 5),
                                            int(bag.get("element_charge", 0) or 0) + int(amount or 0))
                return bag["element_charge"]
            cap = int(rd.get("max", 99) or 99) if rd else 99
            cur = int(bag.get(key, 0) or 0)
            new = min(cap, cur + int(amount or 0))
            # 满溢转盾（怪物 resource_def 也可配 overflow_shield）
            if rd.get("overflow_shield") and cur + int(amount or 0) > cap and actor.get("hp", 0) and not self._p_overflow_shield_cd():
                try:
                    self._add_shield(f"res_overflow_{key}", int((cur + int(amount or 0) - cap) * float(rd.get("overflow_ratio", 5) or 5)), 1)
                except Exception as _sw_e:
                    _battle_warn('_res_gain', _sw_e)
                    pass
            bag[key] = new
            return new
        # ---- 玩家 actor：原完整逻辑（职业/词条/套装/副资源/echo）----
        player = actor
        # v180F 清2c：资源读写入参 actor 自身袋（原 _p_res() 焦点袋——非焦点玩家/怪扮
        # 职业会读写错 actor 资源）
        _pres = actor.setdefault("resources", {})
        if key == "element":
            # v130.2c 元素使徒 2 件：充能条上限 +1（5 → 6）——走 _res_max 统一上限
            mx = self._res_max(player, key)
            _pres["element_charge"] = min(mx, int(_pres.get("element_charge", 0) or 0) + int(amount or 0))
            return _pres["element_charge"]
        if key == "echo":
            # 歌者双资源·回声驻留叠层（mech_stacks 槽）——只有带歌者定义的 actor 消费，无定义空转
            return self._echo_add(actor, logs if logs is not None else [], amount)
        # ---- 玩家 actor：完整资源链路（类主资源委托 _res_gain_class；副资源按 key 注册表；无定义不加）----
        if actor.get("class_name"):
            player = actor
            _crd_route = E.core_resource_def(player.get("class_name", ""))
            if _crd_route and key == _crd_route.get("key"):
                return self._res_gain_class(player.get("class_name", ""), key, amount, logs)
            if E.core_resource_def_by_key(key):
                # 副资源（resonance/echo 等按 key 注册）：上限 = 注册表 max（无词条/套装加成，旧语义）
                _rk_gk = E.core_resource_def_by_key(key)
                _cap_gk = int(_rk_gk.get("max", 99) or 99)
                new = min(_cap_gk, int(_pres.get(key, 0) or 0) + amount)
                _pres[key] = new
                return new
            _rd_p = E.core_resource_def(player.get("class_name", ""))
            if not _rd_p:
                # 无定义资源 key：不累加（旧语义：未配置上限/未定义的资源不限制也不写）
                return _pres.get(key, 0)
            new = min(self._res_max(player, key), int(_pres.get(key, 0) or 0) + amount)
            _pres[key] = new
            return new
        # ---- 怪物/自定义 actor（无职业链路）：统一 actor 资源袋 + resource_def 上限 ----
        cap = self._res_cap_of(actor, key)
        cur = int(bag.get(key, 0) or 0)
        new = min(cap, cur + amount)
        # 满溢转盾（rd.overflow_shield 由任意 actor 定义声明；冷却全局每刻 1 次）
        if rd.get("overflow_shield") and cur + amount > cap and actor.get("hp", 0) \
                and not self._p_overflow_shield_cd():
            try:
                _ov = int((cur + amount - cap) * float(rd.get("overflow_ratio", 5) or 5))
                if _ov > 0:
                    self._add_shield(f"res_overflow_{key}", _ov, 1)
                    self._p_set_overflow_shield_cd(True)
                    if logs is not None:
                        logs.append(f"🛡️ 满溢转化：{rd.get('name', key)}溢出 {cur + amount - cap} 点 → 护盾 +{_ov}（每刻限 1 次转盾）")
            except Exception as _sw_e:
                _battle_warn('_res_gain', _sw_e)
                pass
        bag[key] = new
        return new

    def _res_spend(self, key: str, amount: int, actor: dict | None = None) -> bool:
        """资源消耗（足够则扣除返回 True；不足不扣返回 False）。v177 actor 统一：玩家/怪物同一套。
        actor 缺省 = 当前焦点玩家（兼容旧 2 参调用）；传怪物 actor = 扣怪物资源袋。"""
        if actor is not None and not actor.get("class_name"):
            # 怪物/自定义 actor：actor["resources"] 袋
            bag = actor.setdefault("resources", {})
            if key == "element":
                cur = int(bag.get("element_charge", 0) or 0)
                if cur < int(amount or 0):
                    return False
                bag["element_charge"] = cur - int(amount or 0)
                return True
            cur = int(bag.get(key, 0) or 0)
            if cur < int(amount or 0):
                return False
            bag[key] = cur - int(amount or 0)
            return True
        # 玩家 actor：焦点 resources
        if key == "element":
            cur = self._elem_charge()
            if cur < int(amount or 0):
                return False
            self._p_res()["element_charge"] = cur - int(amount or 0)
            return True
        cur = int(self._p_res().get(key, 0) or 0)
        if cur < int(amount or 0):
            return False
        self._p_res()[key] = cur - int(amount or 0)
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
            return self._p_res().get(k, 0)
        # v130.2 R1：上限口径与 _res_max 统一（词条 max_bonus + 套装 res_max）；无 player 参数取本场玩家；
        # self.player 为 None（from_state 恢复等）时按空 dict 守卫，套装/词条加成归 0
        _pl = self.player or {}
        mx = int(rd.get("max", 99) or 99) + self._res_affix_max_bonus(_pl, k) + self._set_res_max_bonus(_pl, k)
        cur = int(self._p_res().get(k, 0) or 0)
        amount = int(amount or 0)
        overflow = 0
        if amount > 0 and cur + amount > mx:
            overflow = cur + amount - mx
        new = min(mx, cur + amount)
        if rd.get("overflow_shield") and overflow > 0:
            if not self._p_overflow_shield_cd():
                shield = int(overflow * float(rd.get("overflow_ratio", 5) or 5))  # v176: 系数读数据
                self._add_shield("overflow_shield", shield, 1)
                self._p_set_overflow_shield_cd(True)
                if logs is not None:
                    logs.append(f"🛡️ 满溢转化：{rd.get('name', k)}溢出 {overflow} 点 → 护盾 +{shield}（每刻限 1 次转盾）")
            elif logs is not None:
                logs.append(f"🛡️ 满溢转化：{rd.get('name', k)}溢出 {overflow} 点（本刻已转盾，冷却中）")
        self._p_res()[k] = new
        return new

    def _amp_resource(self, player: dict, trigger: str) -> int:
        """v130.2 资源增幅（resource_amp）消费挂点（P0-1：4 种药水写无读修复）。
        p_eff['amps'] 中 trigger 匹配且剩余计数>0 的条目，额外 _res_gain 对应资源 amount。
        trigger ∈ {on_hit_taken 受击 / on_land_hit 出手命中 / on_heal 治疗 / regen 自然回复}。
        on_hit 双语义（沸腾战血=受击/影袭=出手命中）由 hits_left 区分：>0 → 出手命中逐次递减；
        ≤0 → 持续时长制（turns 在 _end_round 递减）。返回本次额外增加总量。"""
        amps = (self._p_eff() or {}).get("amps")
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
            self._p_eff().pop("amps", None)
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
        return int(self._p_res().get("rage", 0) or 0) >= self._res_max(player, "rage")

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
        # 凝神塑能：元素/奥术技能 = 带 element 字段或 res_gain element（v176: 删 cls 特判，技能自带 element 即天然法师技）
        eff, tier = self._affix_eff_tiered(player, "arcane_focus")
        if eff and self._is_element_skill(info):
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
        if kind == K_PHYS and "chi" in self._branch_keys(player):  # 拳师（v130.2c 修正 class id；v181: 职业字面量 → chi 资源所有权，全库仅 cls_wu_seng 持有 chi）
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
                self._p_res()["element"] = "fire"
                self._p_res()["element_charge"] = 0
            elif k == "echo":
                # 回声 = mech_stacks 驻留叠层（战斗内不清零），不占 resources 数值位
                self._p_stacks().setdefault("echo", 0)
            elif k == "energy":
                # 游侠精力：唯一自然回资源，战斗开始满额 100（ranger.md 设计稿 + E1 回归修复）
                # v176: 读 core_resources start_full 字段（原 cls_you_xia 特判数据化）
                _rd_e = E.core_resource_def(player.get("class_name", ""))
                if _rd_e and _rd_e.get("start_full"):
                    self._p_res()[k] = int(_rd_e.get("max", 100) or 100)
                else:
                    self._p_res()[k] = 0
            else:
                self._p_res()[k] = 0
        # v110.3 P1-11：致命预谋被动——战斗开始 +1 连击点（数据驱动 battle_start_cp，替代名字硬匹配）
        if "cp" in keys and self._passive_map(player)["proc"].get("battle_start_cp", []):
            self._p_res()["cp"] = 1

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
                    self._p_buffs_bag()["phys_up"] = max(int(self._p_buffs_bag().get("phys_up", 0) or 0), _t)
                    self._p_eff()["phys_up"] = max(float(self._p_eff().get("phys_up", 0) or 0), _pct)
            elif _pe.get("type") == "resource_amp":
                amps = self._p_eff().setdefault("amps", {})
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
                v = int(self._p_stacks().get("echo", 0) or 0)
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
                v = int(self._p_res().get(k, 0) or 0)
                mx = self._res_max(player, k)
                parts.append(f"✦ {rd['name']} {v}/{mx}")
        return " ".join(parts)

    # ---------------- 技能冷却（v2.0 → v152 时刻制） ----------------
    def _skill_cd_left(self, skill_name: str) -> int:
        """技能剩余冷却（按时刻：ready_at - now，折算成'约 N 刻'展示用；0 = 可用）。
        v152：cooldown 存 ready_at 绝对时刻（不再存剩余刻数）。"""
        ra = self._p_cooldown().get(skill_name)
        if not ra:
            return 0
        if self._now >= float(ra):
            # 到期即清（惰性清理，避免依赖 _tick 时机）
            del self._p_cooldown()[skill_name]
            return 0
        return max(1, int((float(ra) - self._now) / ACT_TICK) + 1)

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
            # v169.7 影舞·无间 shadow_dance_cd：影舞态中所有技能冷却 −20%（乘算叠加在既有 cdr 后）
            if cd > 1 and self._p_buffs_bag().get("shadow_dance"):
                try:
                    _pl_sd = self.player or {}
                    for _pn_sd, _ps_sd in self._proc_pm(_pl_sd)["proc"].get("shadow_dance_cd", []):
                        cd = max(1, int(cd * (1.0 - float(_ps_sd.get("cdr", 0.20) or 0.20))))
                        break
                except Exception as _sw_e:
                    _battle_warn('_set_skill_cd', _sw_e)
                    pass
            self._p_cooldown()[skill_name] = self._now + cd * ACT_TICK

    def _tick_cooldowns(self):
        """v152 时刻制：冷却到期检查（惰性清除，非递减）。保留函数名兼容外部调用。"""
        _now = self._now
        for k in list(self._p_cooldown()):
            if _now >= float(self._p_cooldown()[k]):
                del self._p_cooldown()[k]
        # v151 修复（特效冷却审计 P1-1）：特效装备冷却（we_*_cd）此前只写不递减——
        # 永冻领域/无尽辉光/哨兵壁垒/深岩壁垒等"冷却 N 刻"实际永久生效。
        # v152：p_eff 中 we_*_cd 存 ready_at 绝对时刻（写入点 weapon_effects.py 已换算），到期惰性清除。
        _pe = self._p_eff()
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
                except Exception as _sw_e:
                    _battle_warn('_tick_cooldowns', _sw_e)
                    pass

    # ---------------- 连招序列（v2.0，拳师） ----------------
    # 连招顺序：拳 → 踢 → 掌 →（三连触发）→ 重新开始
    COMBO_ORDER = ["拳", "踢", "掌"]

    def _combo_push(self, tag: str) -> bool:
        """记录连招 tag（拳/踢/掌）。返回是否触发三连。
        非连招 tag 不清空序列（只有非连招技能打断不重置）。"""
        if tag not in self.COMBO_ORDER:
            return False
        seq = self._p_combo_seq()
        expect = self.COMBO_ORDER[len(seq)]
        if tag == expect:
            seq.append(tag)
        else:
            # 顺序不对：从该 tag 重新开始（如果 tag 是起手拳则开始新序列）
            seq[:] = [tag] if tag == self.COMBO_ORDER[0] else []
        self._p_set_last_combo_tag(tag)  # v130.6：无论推进/重置/触发都记忆上一招
        if len(self._p_combo_seq()) == len(self.COMBO_ORDER):
            self._p_combo_seq()[:] = []
            return True
        return False

    def _combo_label(self) -> str:
        """当前连招进度显示(如 拳→踢→_)。"""
        if not self._p_combo_seq():
            return ""
        parts = list(self._p_combo_seq())
        while len(parts) < len(self.COMBO_ORDER):
            parts.append("_")
        return "→".join(parts)

    # ---------------- v130.2 新机制挂点（资源即身份：转职分支独占，基础无） ----------------
    # —— 刺客攻线·影舞者：连段计数 combo（连了才涨、断了重来；仅攻线结算）——
    def _combo_active(self, player: dict) -> bool:
        """连段计数是否活跃（仅攻线·影舞者；基础/毒线/影步线均不读 combo）
        v176: 归属读 COMBO_CFG.class_id/path 数据（原职业特判）。"""
        return bool(player.get("class_name", "") == COMBO_CFG.get("class_id")
                    and self._is_path(player, int(COMBO_CFG.get("path", 1))))

    def _combo_add(self, player: dict) -> int:
        """命中 +1 连段（上限 cap=10）。"""
        combo = int(self._p_stacks().get("combo", 0) or 0)
        combo = min(int(COMBO_CFG.get("cap", 10) or 10), combo + 1)
        self._p_stacks()["combo"] = combo
        return combo

    def _combo_break(self, player: dict, keep_chance: float = 0.0) -> None:
        """受击或落空 → 连段归零（断了重来）。
        v130.2d 连段护持：受击时按词条概率保留连段（史诗 15%/传说 30%，tier 取档）；落空不受保护。
        v169.7 暗影之心 lian_duan_soft：断连只损失 1 段（而非归零/减半）——影舞者攻线被动；
        影舞态（p_buffs.shadow_dance）中受击不再清除连段（effect=shadow_dance 承诺）。"""
        if keep_chance > 0 and random.random() < keep_chance:
            return
        # 影舞态：受击不清连段（暗影步 effect=shadow_dance desc「受击不再清除连段」）
        if self._p_buffs_bag().get("shadow_dance"):
            return
        try:
            for _pn, _ps in self._proc_pm(player)["proc"].get("lian_duan_soft", []):
                cur = int(self._p_stacks().get("combo", 0) or 0)
                if cur > 0:
                    self._p_stacks()["combo"] = max(0, cur - 1)
                    return
                break
        except Exception as _sw_e:
            _battle_warn('_combo_break', _sw_e)
            pass
        self._p_stacks().pop("combo", None)

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
        combo = int(self._p_stacks().get("combo", 0) or 0)
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
        """蓄势持有加伤倍率。仅攻线·格斗士（monk evolve_path=1）吃到；气耗尽自然归 0。
        v176: 判据从职业名改为 chi 资源激活 + 攻线（只有拳师有 chi 资源键，等价且可扩展）。"""
        if not self._is_path(player, 1) or "chi" not in (self._p_res() or {}):
            return 1.0
        chi = int(self._p_res().get("chi", 0) or 0)
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
    # —— 游侠守线·风行者：满弦状态（精力 ≥80 时 低耗/连射技能 暴击率 +10%）——
    def _energy_high_crit(self, player: dict, info: dict | None = None) -> bool:
        """满弦状态判定：守线·风行者（you_xia evolve_path=2）且精力 ≥80 且技能处于低耗/连射档。
        v130.2：满弦烈酒 p_buffs["full_tension"] = 阈值视为已满足（立即满弦，handler 已做守线专属判定）。"""
        if self._p_buffs_bag().get("full_tension"):
            return True
        if "energy" not in (self._p_res() or {}) or not self._is_path(player, 2):  # v176: 职业名→资源键+线
            return False
        # v130.2 P1-4：读「施放前」精力（_do_player_skill 已快照）；直接调用/非技能链回落当前值。
        _pres = getattr(self, "_pre_cost_res", None)
        energy_val = int(_pres.get("energy", 0) or 0) if isinstance(_pres, dict) \
            else int(self._p_res().get("energy", 0) or 0)
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
        if element not in E.ELEMENT_MARKS:  # v176: 元素枚举读数据表 keys（原硬编码 fire/ice/thunder）
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
        if self._is_element_mage(pl):
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
        last = self._p_last_element()
        self._p_set_last_element(element)
        if not last or last != element:
            return False
        # 元素凝聚被动：同系连发第二次施放额外 +1 充能（攻线·元素法师）
        if self._is_element_mage(player) and ELEMENT_SAME_CAST_EXTRA_CHARGE:
            self._res_gain(player, "element", ELEMENT_SAME_CAST_EXTRA_CHARGE)
        return True

    # —— 牧师攻线·歌者：回声驻留叠层（echo 存 mech_stacks，战斗内不清零，上限 max_layers）——
    def _echo_layers(self) -> int:
        return int(self._p_stacks().get("echo", 0) or 0)

    def _echo_add(self, player: dict, logs: list, amount: int = 1) -> int:
        """回声叠层（上限 max_layers）。v130.2 收尾：echo 生产收敛为 res_gain 单通道，
        按技能数据 res_gain['echo'] 数值叠加（原 kind 钩子无条件 +1 已删，防双源双倍速）。"""
        if "echo" not in self._branch_keys(player):  # v176: 回声所有权查分支资源键（原 cls_mu_shi+BARD_BRANCHES 特判）
            return 0
        cur = self._echo_layers()
        cap = int(ECHO_CFG.get("max_layers", 3) or 3)
        if cur >= cap:
            return cur
        cur = min(cap, cur + int(amount or 0))
        self._p_stacks()["echo"] = cur
        logs.append(f"🎵 回声驻留 +{int(amount or 0)}：全队刻恢复随回声层数(当前 {cur}/{cap})")
        return cur

    def _is_bard_skill(self, player: dict, info: dict | None = None) -> bool:
        """技能是否歌者分支技能（歌类技 → 施放叠回声 + 增益续时）。v181 收口：
        歌者=「牧师分支资源表声明 echo 所有权」(BRANCH_RESOURCE_OVERRIDE((cls_mu_shi,1))→echo) +
        技能归属分支即资源分支（branch_skill_owner 数据查 cls 自身，不再写死职业 id）。
        数据现状：BARD_BRANCHES(吟游诗人/灵魂歌者/黎明颂者) 为 v153 前的旧分支名，现数据无任何
        牧师分支叫此名 → 本判定对现网恒 False（歌类技回声在 v153 后由 _res_gain echo 单通道 +
        _branch_keys 资源所有权驱动），此处仅保接口与旧行为等价，防误激活回声续时/伴奏。"""
        if not self._is_branch_of(player, *BARD_BRANCHES):
            return False
        if "echo" not in self._branch_keys(player):
            return False
        if info is None:
            return True
        owner = E.branch_skill_owner(player.get("class_name", ""), info.get("name", ""))
        return bool(owner and owner[1] in BARD_BRANCHES)

    # —— 法师攻线·元素：引爆技反应表结算（cond type='reaction'，读目标 element_marks）——
    def _reaction_table_resolve(self, player: dict, element: str, st: dict, logs: list) -> tuple | None:
        """引爆技按 引爆系 × 目标 element_marks 组合查 REACTION_TABLE 结算（蒸发/超载/冻结/感电）。

        返回 (reaction_mult, 反应日志, chain_flag) 或 None（目标无对应印记系）。
        aoe/freeze 在函数内结算；chain 返回 flag 由调用方 multi+1。结算后清除被反应消费的目标印记系。
        """
        if element not in E.ELEMENT_MARKS:  # v176: 元素枚举读数据表 keys
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
            self._aoe_damage(aoe_dmg, logs)
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
        if not (self._is_element_mage(player)):
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

        v161 新曲线（鱼鱼拍板：取消 cap 线性，改边际递减永续公式）：
            折算系数 = (SPD_REF / spd)^0.5，SPD_REF = 50
        - 速度 50 → 1.0（基准耗时）
        - 速度 25 → 1.41（慢 41%）；速度 100 → 0.71（快 29%）
        - 速度 200 → 0.50（快 2 倍）；速度 400 → 0.35（快 2.83 倍）
        - 永不封顶、永不归零、每点速度边际递减 → 堆速度永远有意义、不爆炸
        """
        import math as _m
        try:
            eff = max(float(spd or 0), 1.0)
        except Exception:
            eff = 1.0
        return _m.sqrt(SPD_REF / eff)

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
            # v180G B6/B7 统一 CTB：出手者 actor 自己的 next_act_at 也落快照 ct 字段
            # （allies 非焦点玩家决策表读各自 ct；焦点玩家 p_ct 与 ct 同步）
            if isinstance(_p, dict) and _p.get("class_name"):
                _p["ct"] = self.p_ct
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
        if not self._p_charging() or not self._p_charging().get("skill"):
            self._p_set_charging(None)
            return False
        left = int(self._p_charging().get("left", 1) or 1)
        cname = self._p_charging().get("name", self._p_charging().get("skill", "?"))
        if left > 0:
            self._p_charging()["left"] = max(0, left - 1)
            if self._p_charging()["left"] == 0:
                # 归零 → 自动结算技能效果（不重复扣 MP/资源）
                skill_name = self._p_charging()["skill"]
                self._p_set_charging(None)
                logs.append(f"✨ 【{cname}】蓄力完成，轰然落下！")
                self._releasing_charge = True
                try:
                    self._do_player_skill(skill_name, player)
                finally:
                    self._releasing_charge = False
                return True
            else:
                logs.append(f"⏳ 你正在蓄力【{cname}】(剩 {self._p_charging()['left']} 刻)，本刻无法普攻/技能！")
        return False

    def _player_charging_blocked(self, logs: list, action: str) -> bool:
        """蓄力期间非防御/道具行动 → 拦截（提示剩余刻），返回是否被拦截。"""
        if not (self._p_charging() and self._p_charging().get("skill")):
            return False
        if action in ("defend", "use_item", "flee"):
            return False
        cname = self._p_charging().get("name", self._p_charging().get("skill", "?"))
        left = int(self._p_charging().get("left", 1) or 1)
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
        # v178 E9：敌方被蓄力打断 → 数据驱动奖励/惩罚窗口（歌澜破音虚脱/赫尔加烛火反噬/
        # 轰鸣断过载层回3）——玩家侧（side=ally）走下方 MP 返还，不触发 Boss 反噬
        if not unit.get("side") == "ally":
            try:
                _oi = unit.get("on_interrupt") or {}
                if _oi:
                    self._on_interrupt_effect(unit, _oi, logs)
            except Exception as _sw_e:
                _battle_warn('_interrupt_charging', _sw_e)
                pass
        # 玩家侧返还 50% 已扣 MP（§6.2规则4；敌方不返还）
        if unit.get("side") == "ally":
            # 蓄力花费记录在 charging 上（施放时已扣，打断按 half 返还）
            spent = int(ch.get("mp_spent", 0) or 0)
            if spent > 0:
                unit["mp"] = min(unit.get("max_mp", unit.get("mp", 0)),
                                 unit.get("mp", 0) + (spent + 1) // 2)
                logs.append(f"✨ 返还了 {(spent + 1) // 2} 点魔力。")

    def _on_interrupt_effect(self, e: dict, cfg: dict, logs: list) -> bool:
        """v178 E9：敌方蓄力被打断后的数据驱动反噬/虚脱效果。
        单位 dict 配 "on_interrupt": {"effect": "<id>", "value": N, "turns": N}
          - "vulnerable": 承伤 ×value（写 _dmg_taken_mult）+ 虚弱 turns 刻（低攻/低防）
            对应歌澜破音虚脱（承伤×1.4 2刻）/赫尔加烛火反噬（承伤×1.3）
          - "stacks_set": 层数置 value（轰鸣断过载 → 充能层回 3，配 stacks 键）
          - "freeze_self": 自我冻结 value 刻（咕噜号令打断后 1 刻不能动）
          - "atk_down": 攻击降低 value 刻（打断惩罚）
        返回是否触发。"""
        try:
            if not e or not cfg:
                return False
            eff = cfg.get("effect")
            _val = float(cfg.get("value", 0) or 0)
            _turns = int(cfg.get("turns", 1) or 1)
            _nm = e.get("name", "Boss")
            if eff == "vulnerable":
                _mult = _val if _val > 1.0 else 1.4  # 承伤倍率（>1=更脆）
                e["_dmg_taken_mult"] = _mult
                # 虚弱：低攻降防（用 buffs 键——spd_down 减速近似行动变慢）
                eb = e.setdefault("buffs", {})
                eb["mon_atk_down"] = max(eb.get("mon_atk_down", 0), _turns)
                logs.append(f"💢 【{_nm}】被打断后露出破绽，承伤 ×{_mult}！({_turns} 刻)")
                return True
            if eff == "stacks_set":
                _skey = str(cfg.get("key", "charge") or "charge")
                _sv = max(0, int(_val))
                e.setdefault("stacks", {})[_skey] = _sv
                e["mech_stacks_n"] = _sv
                logs.append(f"⚡ 【{_nm}】能量失控散逸，{_skey} 层降至 {_sv}！")
                return True
            if eff == "freeze_self":
                eb = e.setdefault("buffs", {})
                eb["freeze"] = max(eb.get("freeze", 0), _turns)
                logs.append(f"❄️ 【{_nm}】反噬自身，陷入僵直！")
                return True
            if eff == "atk_down":
                eb = e.setdefault("buffs", {})
                eb["mon_atk_down"] = max(eb.get("mon_atk_down", 0), _turns)
                logs.append(f"📉 【{_nm}】气息紊乱，攻击降低！({_turns} 刻)")
                return True
        except Exception as _sw_e:
            _battle_warn('_on_interrupt_effect', _sw_e)
            pass
        return False

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
        # v180-B ① actor 化：行动者即焦点玩家。self.player 权威 = 构造时绑定的玩家
        # dict（含播种的战斗状态 resources/buffs/...）。player_turn 传入的 player 参数
        # 真实代码与 self.player 是同一引用（combat 先绑 b.player=player 再 player_turn）；
        # 模拟器/测试若传不同副本（battle_rotation dict(player) 模式），以 self.player 为准
        # ——只有 self.player 为空/未绑时才绑定传入 player（测试直调兜底）。
        # from_state 恢复的玩家战斗状态（_restore_pstate）在此灌入玩家 actor dict
        #（仅灌一次：首次真实 player 绑定后清空，避免切焦点/重复行动覆盖战斗内已变更状态）
        if not self.player:
            self.player = player or {}
        self._apply_restore_pstate()
        # v180F B7：player 后绑（测试/命令层 Battle 构造未传 player）→ 补 sides player 阵营，
        # 否则 _check_side_end 误判"玩家侧已灭"（sides 无 player key 时只剩 enemy）
        if self.player:
            _pl_r = self.player
            if _pl_r.get("class_name") or _pl_r.get("name") or _pl_r.get("qq_id"):
                _sides = getattr(self, "sides", None)
                if _sides is not None and "player" not in _sides:
                    _pl_r.setdefault("side", "player")
                    _pl_r.setdefault("kind", "player")
                    _sides["player"] = [_pl_r]
                    self._side_names = list(_sides.keys())
        # 若传入 player 与 self.player 不同 dict（模拟器浅拷贝模式），把传入 player 的
        # 可观察面板字段同步到 self.player（避免引擎读 self.player 得到空面板）
        if player is not None and player is not self.player:
            try:
                for _pk in ("hp", "mp", "max_hp", "max_mp"):
                    if _pk in player and player[_pk] is not None:
                        self.player[_pk] = player[_pk]
            except Exception as _sw_e:
                _battle_warn('player_turn', _sw_e)
                pass
        # v95.19: 战斗内上限统一实时值——覆盖 from_state 恢复的战斗（恢复时不传 player，
        # __init__ 刷新不到；DB max_hp/max_mp 换装备后过时，会导致战斗内上限与面板不一致）
        try:
            _st = self._player_stats(player)
            player["max_hp"] = int(_st.get("max_hp", player.get("max_hp", 100)))
            player["max_mp"] = int(_st.get("max_mp", player.get("max_mp", C.DEFAULT_MAX_MP)))
        except Exception as _sw_e:
            _battle_warn('player_turn', _sw_e)
            pass
        # v139 配置注入（player 传入时补一次）：core_resources 的 dual_form/focus/vent 定义挂到 player dict
        # （from_state 恢复的战斗 __init__ 不传 player 刷新不到，此处补注入；battle_modes/battle_bars 纯函数读这些字段）
        try:
            from . import engine as _E139b
            _crd139b = _E139b.core_resource_def(player.get("class_name", "")) or {}
            for _mk139b in ("dual_form", "focus", "vent"):
                if _crd139b.get(_mk139b) and not player.get(_mk139b):
                    player[_mk139b] = _crd139b[_mk139b]
            player["v139_modes"] = self._p_v139_modes()
            player["v139_charge"] = self._p_v139_charge()
        except Exception as _sw_e:
            _battle_warn('player_turn', _sw_e)
            pass
        # v63 玩家被沉默：技能类行动先被拦截转普攻（置于 O118 校验前，避免未学习技能
        # 在沉默下先被拦截而无法转普攻）；后续沉默状态下只能普攻/防御/道具
        if "silence" in self._p_buffs_bag() and action == "skill":
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
        # v169.7 不动如山 core_last_stand（拳师守线）：生命 <30% 触发——刻开始兜底触发一次
        # （覆盖非受击路径；受击路径 _damage_actor 内也有触发点，双保险互斥由 _used 标记保证）
        try:
            if not getattr(self, "_core_last_stand_used", False):
                _cl_pm = self._proc_pm(player)["proc"].get("core_last_stand", [])
                if _cl_pm:
                    _hp_r = player.get("hp", 0) / max(1, player.get("max_hp", 1) or 1)
                    if _hp_r < float((_cl_pm[0][1]).get("hp_lt", 0.30) or 0.30):
                        self._core_last_stand_used = True
                        self._p_res()["guard_core"] = max(self._guard_core_n(), int((_cl_pm[0][1]).get("cores", 3) or 3))
                        logs.append(f"⛰️ 不动如山：绝境不屈，获得 {int((_cl_pm[0][1]).get('cores', 3) or 3)} 枚磐核！（每场 1 次）")
        except Exception as _sw_e:
            _battle_warn('player_turn', _sw_e)
            pass
        # v2 蓄力：刻开始结算——归零自动释放技能（§6.2）
        self._player_charge_release(player, logs)
        logs += self._turn_start(player)
        # v101.28 食物持续恢复（v179 P3 升级通用 tick 卡）：每秒由 food_hot 卡结算。
        # 此处兜底：老档恢复有 p_hot 但没卡 → 挂卡（幂等）；不再每行动直接 _apply_hot
        # （防与通用调度双份结算）。
        try:
            if self._p_hot() and int(self._p_hot().get("turns", 0) or 0) > 0:
                _has_hot = any(e.get("uid") == "p_hot_card" for e in self.tick_effects)
                if not _has_hot:
                    self.add_tick_effect(
                        "food_hot", player, ACT_TICK,
                        data={"heal": self._p_hot().get("heal", 0) or 0,
                              "mana": self._p_hot().get("mana", 0) or 0,
                              "turns": int(self._p_hot().get("turns", 0) or 0)},
                        uid="p_hot_card", source="food")
        except Exception as _sw_e:
            _battle_warn('player_turn', _sw_e)
            pass
        # v154 宠物独立速度读条：宠物技能由 pet_tick 事件驱动（_process_until 内触发），
        # 不再跟随玩家行动（玩家行动时宠物可能正在读条，节奏由宠物自身 spd 决定）。
        # v63 玩家被控：眩晕/冻结 → 跳过本刻行动（CTB 下行动浪费，玩家 ct 照走，随后敌方行动段）
        # v121 审计修复：统一走 _after_actor_ct("p")——被控也是"玩家行动消耗"，
        # 敌方应同步时间流逝（与蓄力等待/防御等路径一致），避免被控方反而配速占优
        # v169.7 坚韧 tenacity：被控时消耗 2 层战意跳过（每场 3 次）——先于被控跳过判定，
        # 满足条件则本次行动不浪费（消耗战意 → 照常行动，敌方时间仍流逝）
        if ("stun" in self._p_buffs_bag() or "freeze" in self._p_buffs_bag()) and self._tenacity_try_break(player, logs):
            # 战意挡控成功：控解除、本刻照常行动（不断言走下方被控跳过分支）
            self._p_buffs_bag().pop("stun", None)
            self._p_buffs_bag().pop("freeze", None)
        # v169.7 坚城之姿 zhan_yi_full_reduce：战意满 10 免疫眩晕——被眩晕刻自动解除（无消耗）
        if "stun" in self._p_buffs_bag():
            try:
                for _pn_zy, _ps_zy in self._proc_pm(player)["proc"].get("zhan_yi_full_reduce", []):
                    if self._zhan_yi_n() >= int(_ps_zy.get("stacks", 10) or 10):
                        self._p_buffs_bag().pop("stun", None)
                        logs.append(f"🛡️ {_pn_zy}：战意圆满，眩晕不侵！")
                    break
            except Exception as _sw_e:
                _battle_warn('player_turn', _sw_e)
                pass
        # v169.7 磐石之躯 core_full：磐核满 5 免控（刻开始兜底刷新免疫窗口，等效持续免控）
        try:
            for _pn_cf, _ps_cf in self._proc_pm(player)["proc"].get("core_full", []):
                if self._guard_core_n() >= int(_ps_cf.get("stacks", 5) or 5):
                    self._p_buffs_bag()["cc_immune"] = max(int(self._p_buffs_bag().get("cc_immune", 0) or 0), 1)
                break
        except Exception as _sw_e:
            _battle_warn('player_turn', _sw_e)
            pass
        if "stun" in self._p_buffs_bag():
            logs.append("🌀 你被眩晕，无法行动！")
            self._p_buffs_bag().pop("stun", None)
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            # v180G B7 统一 CTB：出手登记后不推进，事件推进由命令层 advance_until_next_decision 统一完成
            return logs, self.result is not None
        if "freeze" in self._p_buffs_bag():
            logs.append("❄️ 你被冻结，无法行动！")
            self._p_buffs_bag().pop("freeze", None)
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            # v180G B7 统一 CTB：出手登记后不推进
            return logs, self.result is not None

        # v2 蓄力期间：普攻/技能被拦截（可防御/道具），敌方照常行动
        if self._player_charging_blocked(logs, action):
            # v121 CTB：蓄力等待也是玩家行动 → 玩家 ct 照走（PVP 不介入）
            if self.btype != "pvp":
                self._after_actor_ct("p", player=player)
            # v180G B7 统一 CTB：出手登记后不推进
            return logs, self.result is not None

        # v2 目标解析（攻击/技能指定的目标；其余行动重置为主目标）
        if action in ("attack", "skill"):
            # v122 治疗类技能：目标=队友（由 _do_player_skill 解析），不解析敌人目标
            _is_heal = False
            if action == "skill" and skill_name:
                _info0 = E.skill_info(player.get("class_name", ""), skill_name)
                _is_heal = bool(_info0 and _info0.get("kind") == K_HEAL)
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
            # v180G B7 统一 CTB：出手登记后不推进
            return logs, self.result is not None

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
                # v180G B6：出手挂起登记（同普攻）——技能命中参数写玩家 actor dict
                _pca = getattr(self, "_pending_player_cast", None) or {}
                _ht_a = _pca.get("_hit_target")
                player["_cast"] = {
                    "hit_at": self._now + _cast_t,
                    "kind": "skill",
                    "skill": skill_name,
                    "_target_uid": str(_ht_a.get("uid") or _ht_a.get("qq_id") or _ht_a.get("name") or "") if _ht_a and _ht_a.get("hp", 0) > 0 else "",
                }
            else:
                # PVP 不介入：立即结算（保持真人轮流；_do_player_skill 内部 PVP 走立即路径）
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
            _cast_mult = _cast_t + _recover_t
        else:
            # v154 读条命中制：普攻出手瞬间暂存参数（命中时刻 cast_done 才结算）
            if self.btype != "pvp":
                # v169.7 修 #132：普攻同样快照目标（指定 a2/a3 打后排时命中不丢目标）
                _atk_tgt_a = self._active_target
                self._pending_player_cast = {
                    "kind": "atk", "st": st,
                    "_hit_target": _atk_tgt_a if _atk_tgt_a is not None and _atk_tgt_a.get("hp", 0) > 0 else None,
                }
            else:
                logs += self._player_attack(st, player)
            # v154 数据驱动：出招 + 收招（速度折算）
            _cast_t, _recover_t = self._action_times("atk", player=player)
            if self.btype != "pvp":
                self._schedule_cast_done(self._now + _cast_t, {"side": "p", "kind": "atk"})
                # 玩家下次可行动 = 命中时刻 + 收招耗时（= 出手 + 总耗时），保证 cast_done 先触发
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
                self._player_casting = True
                # v180G B6：出手挂起登记——命中参数写玩家 actor dict（与怪 e["_cast"] 同构），
                # 供副本跨 Battle 恢复补排（多人 CTB：A 出手挂起，B 的 Battle 也能触发 A 命中）
                _atk_tgt_a2 = getattr(self, "_active_target", None)
                if _atk_tgt_a2 is None:
                    _atk_tgt_a2 = self.enemy if getattr(self, "enemy", None) else (self.enemies[0] if self.enemies else None)
                player["_cast"] = {
                    "hit_at": self._now + _cast_t,
                    "kind": "atk",
                    "_target_uid": str(_atk_tgt_a2.get("uid") or _atk_tgt_a2.get("qq_id") or _atk_tgt_a2.get("name") or "") if _atk_tgt_a2 and _atk_tgt_a2.get("hp", 0) > 0 else "",
                }
            else:
                self._after_actor_ct("p", player=player, cast_mult=_cast_t + _recover_t)
            _cast_mult = _cast_t + _recover_t

        if self._enemy_dead():
            self.result = "victory"
            self._end_round()
            return logs, True

        # v154：玩家下次可行动点已由 _after_actor_ct 设为命中时刻 + 收招（PVP 已即时结算）
        # 注意：非 PVP 下 cast_done 事件会在 _enemy_phase 推进时触发结算

        # v180-C S2 随从自动行为：玩家正常行动结束后触发（player_act trigger 的随从
        # ——召唤物旧语义；通用触发点，扫 companions 带 auto_act.trigger=player_act 的）
        if self.companions:
            self._companions_trigger("player_act", logs)
            if self._enemy_dead():
                self.result = "victory"
                self._end_round()
                return logs, True

        # v180G B7 统一 CTB：出手登记后不推进——事件推进由命令层
        # advance_until_next_decision 统一完成（单人=多人同一套代码）。
        return logs, self.result is not None

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
                until = self._now + ACT_TICK
            # v152：行为生效事件——玩家行动已即时结算效果，这里只推进时间处理事件
            self._process_until(until, logs, player, defend=defend)
            # v167.3 补结算（直接结算，不推进时间轴）：修复"玩家行动窗口右边界越界的敌方读条
            # 命中丢失"——玩家慢动作（逃跑/防御等）后敌方已出招（动画已播）但命中时刻 > p_ct，
            # 该伤害等下次玩家行动才结算；战斗结束则永远丢失（玩家实抓多次）。
            # 实现：直接把队首越界 cast_done 对应的伤害结算掉（复刻 _process_until cast_done(side=e)
            # 分支：_enemy_cast_done → _damage_actor），并清单位 _cast 状态。
            # ⚠️ 不调 _process_until / 不推进 now → 不抬高敌方出手频率（test_ctb_speed 基线
            # 48/60 不受影响，2026-09-03 实测对比）。
            if self.btype != "instance":
                if self._events:
                    _peek0 = self._events[0]
                    if _peek0[2].get("type") == "cast_done" and _peek0[2].get("side") == "e":
                        _hit0 = float(_peek0[0])
                        if _hit0 <= until + (ACT_TICK or 1.0) * 2 + 1e-9:
                            try:
                                _e0 = _peek0[2].get("unit") or {}
                                if _e0.get("hp", 0) > 0:
                                    _ml, _dg, _dk = self._enemy_cast_done(player, _e0, _peek0[2])
                                    logs += _ml
                                    _e0.pop("_cast", None)
                                    # v180F：管线分支已内部扣血（返回 dmg=0），非管线返回 dmg 外部扣
                                    # v180G B2-2：普攻返回 _dk（phys/magi）→ 落地传 dmg_kind 承伤链统一减免
                                    if _dg > 0:
                                        self._damage_actor(player, _dg, logs,
                                                           source=_e0.get("name", "敌人"),
                                                           dmg_kind=_dk or "")
                                    # v173.x 意见#154/#155：补结算直调 _damage_actor 缺死亡
                                    # 判定——玩家 hp 归 0 但 result 不置 defeat → 命令层看
                                    # ended=False 只存战斗状态，玩家血 0 不触发死亡/战败结算。
                                    # 与 _process_until cast_done(side=e) 分支同款判定。
                                    # 不提前 return：置 defeat 后走 _enemy_phase 正常尾部
                                    # （_advance_time 推进 + return logs, result is not None）。
                                    # v180F 修复：死亡判定移出 _dg>0 门控——管线内部扣血
                                    # （返回 0）也能致死，须同样判 defeat（flee_death 敌速5/8 回归）。
                                    if self._actor_dead(player):
                                        self.result = "defeat"
                                    self._heapq.heappop(self._events)
                            except Exception as _sw_e:
                                _battle_warn('_enemy_phase', _sw_e)
                                pass
            # v158 副本合并：instance 玩家行动后只补结算一次"读条命中"事件（cast_done）——
            # 敌方出招读条结束的伤害要在本次行动内结算（否则 from_state 不恢复事件队列，
            # 读条结算跨次丢失 → 敌方伤害永远不结算）。只处理**当前已排好的** cast_done
            # （不 while 追新：敌方新出招的读条留给下次玩家输入，避免一次行动内敌方多次
            # 结算打死玩家——2026-09-01 test_commands_feedback f4 被骷髅兵连打秒杀）。
            if self.btype == "instance":
                _peek = self._events[0] if self._events else None
                if _peek is not None and _peek[2].get("type") == "cast_done":
                    _hit_t = max(float(_peek[0]), self._now)
                    self._process_until(_hit_t + 0.001, logs, player, defend=defend)
            # v140 波3.1：特效装备敌人行动后（兰顿倦意/冰脉寒流——速度 -6%/-8% 每层）
            try:
                from .core.weapon_effects import proc as _we_proc
                _we_proc(self, player, "enemy_act", {}, logs)
            except Exception as _sw_e:
                _battle_warn('_enemy_phase', _sw_e)
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

    # ---------------- v179 通用 tick 效果框架 ----------------
    def add_tick_effect(self, kind: str, actor: dict, interval: float,
                        data: dict | None = None, expire_at: float | None = None,
                        uid: str | None = None, source: str = "", now: float | None = None):
        """挂一个周期/持续效果条目到通用 tick 池。

        参数同 core/tick_effects.make_effect（actor 可为玩家或怪，actor-agnostic）。
        重复 uid 不叠加（幂等，调用方自行保证/覆盖）。
        """
        from .core.tick_effects import make_effect
        _now = self._now if now is None else float(now)
        eff = make_effect(kind, actor, interval, _now, data=data,
                          expire_at=expire_at, uid=uid, source=source)
        # uid 幂等：同 uid 已存在 → 替换（刷新）
        if uid:
            self.tick_effects = [e for e in self.tick_effects if e.get("uid") != uid]
        self.tick_effects.append(eff)
        return eff

    def remove_tick_effect(self, uid: str | None = None, kind: str | None = None,
                           actor: dict | None = None) -> int:
        """移除 tick 效果条目。按 uid / kind / actor 过滤。返回移除数。"""
        _before = len(self.tick_effects)
        self.tick_effects = [
            e for e in self.tick_effects
            if not ((uid and e.get("uid") == uid)
                    or (kind and e.get("kind") == kind and (actor is None or e.get("actor") is actor)))
        ]
        return _before - len(self.tick_effects)

    def _tick_effects_due(self, now: float) -> list:
        """弹出所有 next_at <= now 的到期条目（按 next_at 升序）。"""
        due = [e for e in self.tick_effects if float(e.get("next_at", 0)) <= float(now)]
        if due:
            due.sort(key=lambda e: float(e.get("next_at", 0)))
            self.tick_effects = [e for e in self.tick_effects if e not in due]
        return due

    def _process_tick_effects(self, logs: list, player: dict) -> list:
        """v179 通用 tick 调度器：处理所有已到期效果条目。

        每个条目按 kind 查 _TICK_HANDLERS 分发处理。handler 返回 (logs 列表, 是否续排)。
        续排 → next_at += interval（若 actor 仍存活/未到期）；否则条目移除。
        expire_at 已过 → 不再续排（自然结束）。
        战斗结束/玩家死亡 → 全部停止。
        """
        if self.result in ("victory", "defeat") or self._actor_dead(player):
            self.tick_effects = []
            return logs
        due = self._tick_effects_due(self._now)
        for eff in due:
            kind = eff.get("kind", "")
            handler = _TICK_HANDLERS.get(kind)
            if not handler:
                # 未注册 handler → 直接丢弃（防坏条目卡池）
                continue
            try:
                _actor = eff.get("actor") or player
                if _actor.get("hp", 1) <= 0:
                    continue  # actor 已死，不结算
                h_logs, _keep = handler(self, _actor, eff, logs)
                if h_logs:
                    logs += h_logs
                # 续排判定：handler 返回 keep=True 且未到期且 actor 存活
                # 且 interval > 0（一次性条目 interval<=0 触发即移除，不续排）
                _exp = eff.get("expire_at")
                _iv = float(eff.get("interval", 0) or 0)
                if (_keep and not self.result and _iv > 0
                        and _actor.get("hp", 1) > 0
                        and (_exp is None or float(self._now) < float(_exp))):
                    eff["next_at"] = float(self._now) + max(_iv, 0.001)
                    self.tick_effects.append(eff)
            except Exception as _ex:
                logs.append(f"(tick 效果异常 {kind}: {_ex})")
        return logs

    def _process_until(self, until_t: float, logs: list, player: dict, defend: bool = False,
                       skip_enemy: bool = False):
        """处理所有 t <= until_t 的事件。这是 v152 事件队列核心调度。
        skip_enemy: True 时跳过 enemy_act 事件（副本/PVP 外部驱动敌方，v157 防双重行动）"""
        # v180G B7：允许 until == now（同刻事件未处理完时推进器会再调）——严格 < 才跳过
        if until_t < self._now:
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
            # v179 通用 tick 效果：每次时间推进后处理到期的周期/持续效果条目
            # （回血/充能/毒/宠物/召唤/食物HOT等——凡注册进 tick_effects 的统一走这里）
            if self.tick_effects:
                try:
                    self._process_tick_effects(logs, player)
                except Exception as _sw_e:
                    _battle_warn('_process_until', _sw_e)
                    pass
            evt = ev.get("type", "")
            try:
                # 早停：战斗已有结局（victory/defeat）→ 不再触发后续事件
                # （旧实现只在特定事件分支 break，战利品/宠物击杀把 result 置 victory 后
                #   同批后续事件仍可能触发——副本打怪后残留 pet_tick 下回合再出手也源于此）
                if self.result in ("victory", "defeat") and evt in ("enemy_act", "cast_done"):
                    break
                if evt == "enemy_act":
                    # v157：skip_enemy=True（副本/PVP 外部驱动敌方）→ 跳过敌方行动，
                    # 只处理玩家事件（cast_done/pet_tick），防副本双重敌方行动
                    # 注：外部驱动方负责在下一轮补排敌方行动（_instance_act 循环按 p_cts 判定
                    # 下一行动者并驱动），此处 continue 丢弃堆内事件是设计语义——事件堆仅用于
                    # 本次窗口的玩家事件结算，敌方下次行动由外部显式发起。
                    if skip_enemy:
                        continue
                    unit = ev.get("unit")
                    if not unit or unit.get("hp", 0) <= 0:
                        continue
                    if self._actor_dead(player):
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
                        except Exception as _sw_e:
                            _battle_warn('_process_until', _sw_e)
                            pass
                    # v154 敌方对称读条：_enemy_turn 已排 cast_done（出招读条结束才命中结算），
                    # dmg 恒 0（读条期间不直接打玩家）；敌方下次行动时刻已由 _enemy_turn 内部
                    # _after_actor_ct("e") 设为 命中时刻+收招。此处按新 ct 重排 enemy_act 事件。
                    if unit.get("hp", 0) > 0:
                        self._schedule(float(unit.get("ct", 0) or 0), {"type": "enemy_act", "unit": unit})
                    if self._actor_dead(player):
                        self.result = "defeat"
                        break
                elif evt == "cast_done":
                    # v154 读条命中制：出招读条结束 = 命中时刻 → 结算（用命中时刻实时状态）
                    side = ev.get("side", "p")
                    if side == "p":
                        self._player_casting = False
                        # v180G B6：跨 Battle 恢复的玩家命中（player_ref 指向 allies 快照）——
                        # 命中者可能不是当前焦点（副本 B 的 Battle 触发 A 的挂起命中）
                        _hit_player = ev.get("player_ref") or player
                        pc = self._pending_player_cast or {}
                        # 非焦点命中（player_ref 存在且不是当前玩家）：pending 属于当前焦点
                        # 玩家，不能用它结算别人命中 → 从 ev 恢复参数
                        _is_foreign = ev.get("player_ref") is not None and ev.get("player_ref") is not player
                        if not pc or _is_foreign:
                            _pkind = ev.get("kind", "atk")
                            if _pkind == "skill" and ev.get("skill"):
                                _pinf = self._lookup_skill_info(str(ev.get("skill"))) or {}
                                pc = {"skill_name": ev.get("skill"), "info": _pinf,
                                      "st": None, "target": ev.get("target")}
                            else:
                                pc = {"kind": "atk", "st": None, "target": ev.get("target")}
                        self._pending_player_cast = None
                        # v169.7 修 #132：恢复施放时快照的目标（_enemy_phase 尾部已清 _active_target）
                        # ——目标仍存活 → 设回 _active_target（伤害结算打到指定 a2/a3 而非主目标 a1）；
                        #   目标已死 → 清 None（_deal_damage 兜底主目标 = 命中落空语义）。
                        _ht = pc.get("_hit_target")
                        if _ht is not None:
                            if _ht.get("hp", 0) > 0 and _ht in self.enemies:
                                self._active_target = _ht
                            else:
                                self._active_target = None
                        # 目标已死 → 中断（命中落空）
                        if not self._enemy_dead():
                            _kind = pc.get("kind", ev.get("kind", ""))
                            if _kind == "atk":
                                logs += self._player_attack(pc.get("st") or self._player_stats(_hit_player), _hit_player)
                            elif _kind == "skill":
                                _sn = pc.get("skill_name") or ev.get("skill")
                                _inf = pc.get("info") or {}
                                if _sn and _inf:
                                    logs += self._player_skill(pc.get("st") or self._player_stats(_hit_player),
                                                               _sn, _inf, _hit_player, target=pc.get("target") or ev.get("target"))
                            elif _kind == "item":
                                # 道具无读条命中（即时生效，v152 行为保留）——这里只是兜底
                                pass
                        else:
                            logs.append("（你的攻击落空了——目标已倒下！）")
                        # v180G B6：命中结算完成 → 清玩家挂起登记（防 from_state 重复补排；同敌方 e["_cast"] 语义）
                        if ev.get("player_ref") is not None:
                            _hit_player.pop("_cast", None)
                        # 命中后玩家收招已完成（p_ct 已在出手时设为命中时刻+收招），无需再排
                    elif side == "e":
                        # v154 敌方对称读条：敌方出招读条结束 → 命中结算
                        e_unit = ev.get("unit") or {}
                        if e_unit.get("hp", 0) > 0:
                            # v180F B5：结算目标 = 排程时选定的 target（怪vs怪打敌对怪），
                            # 无 target（旧战斗/兼容路径）回落 player 参数
                            _tgt = ev.get("target") or player
                            mlogs, dmg, _dk = self._enemy_cast_done(_tgt, e_unit, ev)
                            logs += mlogs
                            # v163：敌方读条结算完成 → 清单位读条状态（防 from_state 重复补排）
                            e_unit.pop("_cast", None)
                            if defend and dmg > 0:
                                # v178 E6：方向性防御——技能数据配 defend_reduce 覆盖默认 0.5
                                # （如云怒风眼技 defend_reduce=0.8 防御挡 80%；缺省 0.5=旧行为）
                                _dr = DEFEND_REDUCE
                                try:
                                    _evk = ev.get("skill") or (pc or {}).get("skill_name")
                                    if _evk:
                                        _evi = self._lookup_skill_info(str(_evk))
                                        _evdr = _evi.get("defend_reduce")
                                        if isinstance(_evdr, (int, float)) and 0 <= float(_evdr) <= 0.95:
                                            _dr = float(_evdr)
                                except Exception as _sw_e:
                                    _battle_warn('_process_until', _sw_e)
                                    pass
                                dmg = max(1, int(round(dmg * (1.0 - _dr))))
                                self._pending_dmg_lines.append(f"(格挡后 {dmg} 点伤害)")
                            # v180F B5：目标 actor 化扣血——目标是玩家走 _damage_actor，
                            # 目标是怪/随从走 _damage_actor（怪vs怪伤害真正落目标）
                            # v180G B2-2：普攻 _dk（phys/magi）透传 dmg_kind 统一减免
                            if _tgt and _tgt is not player and self.side_of(_tgt) and self.side_of(_tgt) != "player":
                                self._damage_actor(_tgt, dmg, logs, source=e_unit.get("name", "敌人"),
                                                   dmg_kind=_dk or "")
                            else:
                                self._damage_actor(_tgt or player, dmg, logs,
                                                   source=e_unit.get("name", "敌人"),
                                                   dmg_kind=_dk or "")
                            # v154 打断：玩家读条中受到控制（眩晕/冻结/沉默）→ 打断读条
                            if self._player_casting and dmg > 0:
                                _ctrl = any(k in self._p_buffs_bag() for k in ("stun", "freeze", "silence"))
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
                    if self._actor_dead(player):
                        self.result = "defeat"
                        break
                    # v180F B7：通用 side 全灭判定（怪vs怪等无玩家战斗——某自定义
                    # 阵营全灭 → 结束）。常规战斗此判定与上方兼容（player/enemy 二选一）。
                    try:
                        if self._alive_side_names() and len(self._alive_side_names()) <= 1:
                            _chk = self._check_side_end(logs)
                            if _chk is not None:
                                break
                    except Exception as _sw_e:
                        _battle_warn('_process_until', _sw_e)
                        pass
            except Exception as _ex:
                # 单个事件异常不阻塞队列（防御性，避免一个坏事件死循环）
                logs.append(f"(事件处理异常: {_ex})")

    # ============================================================
    # v180G B6/B7 统一 CTB 推进器（一套代码：单人=副本=世界Boss=PVP）
    # 唯一"事件推进"入口——所有命令层驱动战斗都调它，不各自手写窗口推进。
    # ============================================================
    def player_act(self, action: str, skill_name: str | None, player: dict, target=None, enemy_act: bool = True) -> tuple:
        """v180G B7 统一 CTB 行动接口（命令层唯一入口）：
        1) 玩家出手登记（player_turn 纯登记：扣资源/排事件/更新行动点）
        2) 推进到下一个真人决策点（advance_until_next_decision：事件自动结算）

        返回 (logs, ended, who)：
        - logs：出手日志 + 推进期间事件日志
        - ended：战斗是否结束（result 已置）
        - who：下一个该决策的玩家 dict（多人副本可能不是出手者）；ended 时为 None

        单人：who == 出手者自己（或 None if ended）；多人：按行动点交错返回下一个真人。
        """
        logs, ended = self.player_turn(action, skill_name, player, enemy_act=enemy_act, target=target)
        if not ended:
            _act, _who = self.advance_until_next_decision(logs)
            if _act == "over" or self.result:
                ended = True
                _who = None
        else:
            _who = None
        return logs, ended, _who
    def _player_next_act_times(self) -> list:
        """所有存活真人玩家的下次可行动绝对时刻列表。焦点玩家 p_ct；副本 allies 各 ct。
        时刻 <= now 视为"已到点"（该玩家应立即决策）——返回 now 使其最先被选出。"""
        _pl0 = self.player or {}
        times = []
        if _pl0.get("class_name") and (_pl0.get("hp", 1) > 0):
            _pt = float(getattr(self, "p_ct", 0) or 0)
            times.append(_pt if _pt > self._now else self._now)
        for _a in (self.allies or []):
            if _a is _pl0:
                continue
            if _a.get("class_name") and _a.get("hp", 1) > 0:
                _at = float(_a.get("ct", 0) or 0)
                times.append(_at if _at > self._now else self._now)
        return times

    def _player_who_at(self, t: float):
        """t 时刻该行动的真人玩家。玩家行动点 <= t（已到点）时返回该玩家。"""
        _pl0 = self.player or {}
        _pt = float(getattr(self, "p_ct", 0) or 0)
        if _pl0.get("class_name") and _pl0.get("hp", 1) > 0 and _pt <= t + 1e-9:
            return _pl0
        for _a in (self.allies or []):
            if _a is _pl0:
                continue
            if _a.get("class_name") and _a.get("hp", 1) > 0 and float(_a.get("ct", 0) or 0) <= t + 1e-9:
                return _a
        # 焦点玩家行动点 > t 但 allies 都未到？找行动点最小的存活玩家兜底
        best = None
        best_t = None
        for _cand in [(_pl0, _pt)] + [(_a, float(_a.get("ct", 0) or 0)) for _a in (self.allies or []) if _a is not _pl0]:
            if _cand[0].get("class_name") and _cand[0].get("hp", 1) > 0:
                if best_t is None or _cand[1] < best_t:
                    best_t = _cand[1]
                    best = _cand[0]
        return best

    def advance_until_next_decision(self, logs, defend: bool = False):
        """v180G B6/B7 统一推进：结算所有到点事件，停在下一个真人玩家决策点。

        返回 ("player", 玩家dict) 轮到该玩家决策 | ("over", None) 战斗结束。

        语义（鱼鱼拍板标准 CTB）：
        - 事件堆按绝对时刻排（怪 enemy_act / cast_done 命中 / tick 系）
        - 循环：下一事件 vs 下一玩家行动点，谁先到处理谁
          · 事件先到 → 自动结算（怪 AI 出手、命中落定、dot 跳）→ 继续
          · 玩家行动点先到 → 推进到该时刻（期间结算 <= 它的事件）→ 返回该玩家
        - 无存活真人（怪vs怪）→ 事件跑完到结束
        命令层每次玩家出手后调本方法推进到下一个决策边界。
        """
        _guard = 0
        while self.result not in ("victory", "defeat") and _guard < 128:
            _guard += 1
            # 注：不用 _check_side_end 做提前结束判定——instance/命令层后绑玩家场景下
            # sides 可能只有 enemy（player 后绑不在 sides），存活阵营 ≤1 误判提前结束。
            # 战斗结束统一由事件处理（_enemy_dead/_actor_dead 置 result）与下方决策点判定完成。
            _ptimes = self._player_next_act_times()
            _dt = min(_ptimes) if _ptimes else None
            _et = self._events[0][0] if self._events else None
            if _dt is None and _et is None:
                return ("over", None)
            if _et is not None and (_dt is None or _et <= _dt + 1e-9):
                # 事件先到 → 结算该事件（推进到事件时刻，_process_until 处理堆顶及同刻）
                # v180G B7：事件时刻 == now（同刻恢复/浮点）也调 _process_until——它内部
                # 处理堆顶 t <= until 的事件并把 now 推到事件时刻（严格 < 才跳过）。
                self._process_until(max(_et, self._now), logs, self.player or {}, defend=defend)
                if self.result:
                    return ("over", None)
                continue
            # 玩家行动点先到 → 推进到它（期间结算 <= 它的事件），返回该玩家
            if _dt is not None:
                if _dt > self._now:
                    self._process_until(_dt, logs, self.player or {}, defend=defend)
                    # v180G B7：_process_until 只把 now 推到<=_dt 的最新事件时刻；
                    # 补推进到玩家决策点（buff/CD/DOT 用绝对时刻到期，与旧 _enemy_phase 同语义）
                    _gap = _dt - self._now
                    if _gap > 0:
                        self._advance_time(_gap)
                if self.result:
                    return ("over", None)
                # v167.3 补结算语义收编：决策点右边界越界的敌方读条命中不丢失——
                # 直接结算（复刻 _process_until cast_done(side=e) 分支伤害落地）。
                self._settle_cross_boundary_hits(logs, player=self.player or {}, until=_dt, defend=defend)
                if self.result:
                    return ("over", None)
                _who = self._player_who_at(_dt)
                return ("player", _who) if _who else ("over", None)
        return ("over", None)

    def _settle_cross_boundary_hits(self, logs, player=None, until=None, defend=False):
        """v167.3 补结算（收编自 _enemy_phase）：推进到决策点(until)后，若敌方已出招
        （动画已播）但命中时刻略超决策点右边界，直接把伤害结算掉，避免命中丢失。
        只处理队首越界 cast_done（不 while 追新：敌方新出招留给下次推进，防一次
        行动内敌方多次结算）。instance 模式由命令层补结算，此处跳过。"""
        if self.btype == "instance":
            return
        try:
            if not self._events:
                return
            _peek0 = self._events[0]
            if _peek0[2].get("type") != "cast_done" or _peek0[2].get("side") != "e":
                return
            _until = float(until) if until is not None else float(getattr(self, "p_ct", 0) or 0)
            _hit0 = float(_peek0[0])
            if _hit0 > _until + (ACT_TICK or 1.0) * 2 + 1e-9:
                return
            try:
                _e0 = _peek0[2].get("unit") or {}
                if _e0.get("hp", 0) > 0:
                    _pl = player if player is not None else (self.player or {})
                    _ml, _dg, _dk = self._enemy_cast_done(_pl, _e0, _peek0[2])
                    logs += _ml
                    _e0.pop("_cast", None)
                    if _dg > 0:
                        self._damage_actor(_pl, _dg, logs,
                                           source=_e0.get("name", "敌人"),
                                           dmg_kind=_dk or "")
                    if self._actor_dead(_pl):
                        self.result = "defeat"
                    self._heapq.heappop(self._events)
            except Exception as _sw_e:
                _battle_warn('_settle_cross_boundary_hits', _sw_e)
                pass
        except Exception as _sw_e:
            _battle_warn('_settle_cross_boundary_hits', _sw_e)
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
        except Exception as _sw_e:
            _battle_warn('_add_shield', _sw_e)
            pass
        _exp = self._now + max(1, int(turns or 1)) * ACT_TICK
        cur = self._p_shields_bag().get(key)
        if cur:
            cur["value"] += value
            # 兼容旧存档 {"value","turns"} → 转 expire_at
            if "turns" in cur and "expire_at" not in cur:
                cur["expire_at"] = self._now + max(1, int(cur.get("turns", 1))) * ACT_TICK
                cur.pop("turns", None)
            cur["expire_at"] = max(float(cur.get("expire_at", _exp)), _exp)
        else:
            self._p_shields_bag()[key] = {"value": value, "expire_at": _exp}

    def _absorb_shields(self, shields: dict, dmg: int, logs: list, label: str = "✨") -> int:
        """v177 护盾吸收核心（actor-agnostic）：多源护盾 dict 逐个扣，同源叠厚异源并存。
        玩家 p_shields / 怪物 shields（统一 dict 格式）共用。返回剩余伤害（扣完盾后的 dmg）。
        - shields: {来源: {"value": N, "expire_at": T}}（异源并存，同源在 _add_shield 已叠厚）
        - 盾吸收完删除该源；dmg 归零提前停。
        """
        if not shields or dmg <= 0:
            return dmg
        absorb_total = 0
        for key in list(shields):
            s = shields[key]
            if not isinstance(s, dict) or not s.get("value"):
                shields.pop(key, None)
                continue
            absorb = min(int(s["value"]), dmg)
            s["value"] -= absorb
            dmg -= absorb
            absorb_total += absorb
            if int(s.get("value", 0)) <= 0:
                del shields[key]
            if dmg <= 0:
                break
        if absorb_total > 0:
            left = sum(int(s.get("value", 0)) for s in shields.values())
            logs.append(f"{label} 护盾吸收 {absorb_total} 点伤害(剩余 {left})")
        return dmg

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
                if a not in self._p_food_effects():
                    self._p_food_effects().append(a)
            # v179 补挂卡：食物 foodfx 可能含 turn_start 周期效果（回春/冥想等）→ 确保
            # affix_food_we 卡已挂（_ensure_regen_effects 幂等）
            try:
                if player and not self._actor_dead(player):
                    self._ensure_regen_effects(player)
            except Exception as _sw_e:
                _battle_warn('_do_use_item', _sw_e)
                pass
            # 护盾效果：立即获得护盾（v180F 清2b：数值读数据表 food_effect_data.py，原硬编码 0.10）
            if "shield" in aids:
                from .data.food_effect_data import FOOD_EFFECT_PARAMS as _FEP
                _sh = (_FEP.get("shield") or {})
                _sh_pct = float(_sh.get("pct", 0.10) or 0.10)
                _sh_turns = int(_sh.get("turns", 3) or 3)
                self._add_shield("food_shield", int(player.get("max_hp", 100) * _sh_pct), _sh_turns)
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
            _cur_hot = self._p_hot() or {}
            _new_hot = {"heal": max(hpct, float(_cur_hot.get("heal", 0) or 0)),
                        "mana": max(mpct, float(_cur_hot.get("mana", 0) or 0)),
                        "turns": max(turns, int(_cur_hot.get("turns", 0) or 0))}
            self._p_hot().clear()
            self._p_hot().update(_new_hot)
            # v179 P3：food_hot 卡由下次行动开头兜底挂载（吃食物当回合不结算——
            # 与旧语义「吃+结算不同回合」一致；卡每秒结算并同步 p_hot turns 递减）
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
                self._heal_actor(player, hv, logs)  # v180E 统一落地
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
                except Exception as _sw_e:
                    _battle_warn('_do_use_item', _sw_e)
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
                self._p_buffs_bag()[_k] = max(self._p_buffs_bag().get(_k, 0), 3)
            # v151 时刻制（鱼鱼拍板）：防御/受击类 buff 改"受击计数"——铁壁/岩壁/影步/荆棘等
            # 防的是敌方出手，按敌方出手次数计时（3 次受击）而非玩家刻，不受速度差影响。
            # 注：food_def_up 保持持续时长制（食物是持续小加成，非爆发防御，语义不同）
            _def_keys = {"def_up", "def_up_big", "def_up_small",
                         "mdef_up", "dodge_pot", "block_pot", "thorns_pot", "magic_resist"}
            for _k in kind.split(","):
                if _k in _def_keys:
                    self._p_buff_hits()[_k] = 3
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
                self._heal_actor(player, heal, logs)  # v180E 统一落地
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
        h = self._p_hot()
        logs = []
        max_hp = player.get("max_hp", player.get("hp", 100))
        max_mp = player.get("max_mp", player.get("mp", 100))
        if h.get("heal"):
            gain = int(max_hp * h["heal"])
            if gain > 0:
                before = player.get("hp", 0)
                self._heal_actor(player, gain, logs)  # v180E 统一落地
                logs.append(f"🍲 持续恢复生效，恢复 {player['hp'] - before} 点生命！({player['hp']}/{max_hp})")
        if h.get("mana"):
            gain = int(max_mp * h["mana"])
            if gain > 0:
                before = player.get("mp", 0)
                player["mp"] = min(max_mp, before + gain)
                logs.append(f"🍲 持续恢复生效，恢复 {player['mp'] - before} 点魔力！({player['mp']}/{max_mp})")
        h["turns"] -= 1
        if h["turns"] <= 0:
            h.clear()
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
        if player["mp"] < info.get("mp", 0):
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
        if not _releasing and player["mp"] < info.get("mp", 0):
            logs.append("💙 魔力不足！")
            return logs
        # v130.2 P1-4：施放前核心资源快照（满弦判定 / 隐藏线每层加成读「施放时持有值」而非扣费后值）——
        # 满弦语义=「施放时精力≥80」，扣费后精力永低于满档导致高耗档永不触发；龙力/禅意每层加成因
        # 消耗型金技扣费后归 0 无法按层放大的同病。后续消费点读 self._pre_cost_res（未命中回落当前值）。
        self._pre_cost_res = dict(self._p_res())
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
                self._p_res()["element_charge"] = _left
            else:
                self._p_res()[ck] = _left
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
        if info.get("kind") == K_HEAL and target and self.allies:
            if self._resolve_ally_target(target) is None:
                logs.append(f"队伍里没有『{target}』～(副本中『技能 <名称> <队友名>』可指定治疗目标)")
                return logs
        # v34 符文·聚能：MP 消耗 -x%
        mana_lvl = self._enchant_lvl(self._enchant_effects(player), "mana_flow")
        mp_cost = info.get("mp", 0)
        if mana_lvl:
            mp_cost = max(1, int(mp_cost * (1 - C.rune_value("mana_flow", mana_lvl))))
        # v130.2 元素亲和药剂（mana_cost_down）：技能魔力消耗 ×(1-pct)（与符文乘算叠加）
        if self._p_buffs_bag().get("mana_cost_down"):
            _mcd = float((self._p_eff() or {}).get("mana_cost_down", 0) or 0)
            if _mcd > 0:
                mp_cost = max(1, int(mp_cost * (1 - _mcd)))
        # v130.2c 消耗减免词条：凝神塑能（元素/奥术技能蓝耗 -10%）/ 圣徽之佑（神迹技蓝耗 -5/史诗 -10）
        _mp_red = self._mp_cost_reduce(player, info)
        if _mp_red:
            mp_cost = max(1, mp_cost - _mp_red)
        # v169.7 奥术恒常 arcane_constant（奥术学者）：奥术技能耗蓝 −50%（乘算，与符文/药剂/词条叠加）
        try:
            _mech_ac = info.get("mech", "")
            _is_arcane_skill = bool(_mech_ac in MECH_PROC_GROUPS.get("arcane_dmg", ())
                                    or (info.get("res_gain") or {}).get("arcane")
                                    or _mech_ac in ("arcane", "arcane_burst"))
            if _is_arcane_skill:
                for _pn_ac, _ps_ac in self._proc_pm(player)["proc"].get("arcane_constant", []):
                    mp_cost = max(1, int(mp_cost * float(_ps_ac.get("mp_mult", 0.50) or 0.50)))
                    logs.append(f"📖 {_pn_ac}：奥术恒常，耗蓝减半！")
                    break
        except Exception as _sw_e:
            _battle_warn('_do_player_skill', _sw_e)
            pass
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
            self._p_set_charging({"skill": skill_name, "left": int(info["charge"]),
                             "name": cname, "mp_spent": mp_cost})
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
            # v169.7 修 #132：命中时刻 _active_target 会被敌方行动段清空（_enemy_phase 尾部
            # self._active_target = None），若不快照目标单位，命中结算打回主目标(a1)。
            # 快照解析好的目标 dict 引用（攻击目标，非治疗）；命中时恢复 + 死亡回退。
            # v169.9 兜底：_active_target 仅在敌方行动段赋值——直接调 _do_player_skill（测试/
            # 副本命令层某些路径）未走敌方回合时不存在该属性 → getattr 退化到主目标。
            _atk_tgt = getattr(self, "_active_target", None)
            if _atk_tgt is None:
                _atk_tgt = getattr(self, "enemy", None) or (self.enemies[0] if self.enemies else None)
            self._pending_player_cast = {
                "skill_name": skill_name,
                "info": info,
                "st": st,
                "target": target,
                "mp_cost": mp_cost,
                "mana_lvl": mana_lvl,
                "_hit_target": _atk_tgt if _atk_tgt is not None and _atk_tgt.get("hp", 0) > 0 else None,
            }
            # 出手瞬间已扣 MP/资源/进 CD（读条 = 已投入）；结算在命中时刻由 cast_done 执行
            cd = info.get("cd", 0)
            if cd:
                self._set_skill_cd(skill_name, cd)
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
        self._p_set_defending(True)
        # v152：防御也是玩家行为，有行为时长（快动作 cast_mult=CAST_DEFEND）。
        # v180G B7 统一 CTB：defending 标志已 actor 化（_damage_actor 承伤链统一减免），
        # 出手登记后不推进——事件推进由命令层 advance_until_next_decision 统一完成。
        if enemy_act and self.btype != "pvp":
            self._after_actor_ct("p", player=player, cast_mult=cast_mult)
            return logs, self.result is not None
        self._end_round()
        return logs, self.result is not None

    def _do_flee(self, player: dict, logs: list, cast_mult: float = 1.0) -> tuple:
        if self.btype in ("worldboss", "pvp"):
            logs.append("💨 这里无法逃跑！背水一战吧！")
            if self.btype == "pvp":
                # PVP：不触发 AI 反击，等对方真人行动
                return logs, False
            # v180G B7 统一 CTB：逃跑失败也被敌方追击 → 玩家 ct 照走（慢动作），
            # 事件推进由命令层 advance_until_next_decision 统一完成
            self._after_actor_ct("p", player=player, cast_mult=cast_mult)
            return logs, self.result is not None
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
        # v180G B7 统一 CTB：逃跑失败被追击 → 玩家 ct 照走（慢动作），
        # 事件推进由命令层 advance_until_next_decision 统一完成
        if self.btype != "pvp":
            self._after_actor_ct("p", player=player, cast_mult=cast_mult)
        return logs, self.result is not None

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
        # v180-B：equipment 可能缺失（怪配 class_name 但无装备字段）→ 兜底空。
        # 注意：不传 learned_skills（面板并入被动由 engine 做——战斗侧被动经 _passive_map
        # 动态处理，此处传了会双算。怪要被动走 _passive_map 同玩家路径）
        st = E.player_final_stats(player.get("class_name", "战士"), player.get("level", 1),
                                  player.get("equipment") or {},
                                  player.get("class_tier", 0),
                                  player.get("attributes"),
                                  player.get("evolve_path", 0),
                                  getattr(self, "title_bonus", None) or {},
                                  player.get("race"))
        # v180F B2 (A1)：面板聚合读**入参 player 自身** buffs（伪 actor 化修复——
        # 原读 self._p_buffs_bag() 焦点袋，非焦点 actor 算面板会拿错 buffs）
        _pbuffs = player.setdefault("buffs", {})
        st = self._apply_buffs(st, _pbuffs)
        # v104 M23 神龛祝福：持久 buff（stat ×1.10，5 次战斗），战斗开始时已消费 1 次
        _pb = player.get("poi_buff")
        if _pb and _pb.get("stat") in st:
            st[_pb["stat"]] = int(st.get(_pb["stat"], 0) * float(_pb.get("mult", 1.10)))
        # #245: 玩家减速生效（与 _enemy_stats 的 spd_down 处理对称）——此前 p_buffs["spd_down"]
        # 只被挂载从未应用，减速玩家仍按原速度先手/触发速度优势
        if "spd_down" in _pbuffs:
            st["spd"] = int(st.get("spd", 0) * SPD_DOWN_MULT)
        # v169.7 暗影步·极 shadow_dance_bonus：影舞态中自身速度 +25%
        # v181.P2D-D2b：消费迁注册表族 stat_mult_cond（stat_kind='spd' 段；影舞态守卫
        # 保留原 if 骨架——spd 消费点，与挂点2 crit_dmg 段同 proc 双消费点参数化）
        if _pbuffs.get("shadow_dance"):
            try:
                for _pn_sb, _ps_sb in self._proc_pm(player)["proc"].get("shadow_dance_bonus", []):
                    _ctx_sb = {"player": player, "ps": _ps_sb, "ps_name": _pn_sb, "stat_kind": "spd"}
                    _rv_sb = _run_proc_family(self, "shadow_dance_bonus", _ctx_sb)
                    if _rv_sb:
                        st["spd"] = int(st.get("spd", 0) * (1.0 + float(_rv_sb[0])))
                    break
            except Exception as _sw_e:
                _battle_warn('_player_stats', _sw_e)
                pass
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
        # ---- v169.7 诗人旋律被动光环（读 _melody 状态；旋律驻留光环本体由 battle_mech agent 接线，本段做被动加成）----
        # 共鸣 melody_resonance：强度层 ≥3 全队额外 +10% 全属性
        # 万籁和鸣 melody_full：强度满 5 全队额外 +15% 全属性
        # 咏叹·极 melody_master：每强度层 +5% 旋律效果（与上面两光环线性加叠）
        # ⚠️ TODO（依赖 battle_mech agent 的旋律实现）：若旋律光环本体未实现，本段只加“额外”档；
        #   已学被动玩家在有旋律时获得上述加成；无旋律（_melody.name=None）不生效
        # v181.P2D-D2b：3 段消费迁注册表族 stat_mult_cond（stat_kind='melody' 段）；
        # 挂点保留"3 段聚合 _mel_pct 再统一乘"顺序——handler 各返回贡献值，循环骨架/顺序/break 逐字保留
        try:
            _mel169 = self._melody_state()
            _pm_mel = self._proc_pm(player)["proc"]
            _mel_pct = 0.0
            _mel_n = int(_mel169.get("stack", 0) or 0)
            if _mel169.get("name") and _mel_n > 0:
                for _pn_rs, _ps_rs in _pm_mel.get("melody_resonance", []):
                    _ctx_rs = {"player": player, "ps": _ps_rs, "ps_name": _pn_rs,
                               "stat_kind": "melody", "melody_n": _mel_n}
                    _rv_rs = _run_proc_family(self, "melody_resonance", _ctx_rs)
                    if _rv_rs:
                        _mel_pct += float(_rv_rs[0])
                    break
                for _pn_mf, _ps_mf in _pm_mel.get("melody_full", []):
                    _ctx_mf = {"player": player, "ps": _ps_mf, "ps_name": _pn_mf,
                               "stat_kind": "melody", "melody_n": _mel_n}
                    _rv_mf = _run_proc_family(self, "melody_full", _ctx_mf)
                    if _rv_mf:
                        _mel_pct += float(_rv_mf[0])
                    break
                for _pn_mm, _ps_mm in _pm_mel.get("melody_master", []):
                    _ctx_mm = {"player": player, "ps": _ps_mm, "ps_name": _pn_mm,
                               "stat_kind": "melody", "melody_n": _mel_n}
                    _rv_mm = _run_proc_family(self, "melody_master", _ctx_mm)
                    if _rv_mm:
                        _mel_pct += float(_rv_mm[0])
                    break
            if _mel_pct > 0:
                for _mk_s in ("atk", "def", "matk", "mdef", "spd"):
                    st[_mk_s] = int(st.get(_mk_s, 0) * (1.0 + _mel_pct))
        except Exception as _sw_e:
            _battle_warn('_player_stats', _sw_e)
            pass
        # v140 波3.1：特效装备常驻面板属性（奥术苍穹魔攻+15%/疾风步速度+/弑星·无尽辉光暴伤+）
        # v180E 阶段4：数值全从武器特效参数表读（WEAPON_EFFECT_DATA）
        try:
            from .core.weapon_effects import weapon_effect_ids as _we_ids
            from .core.weapon_effects import effect_data as _we_edp
            _weids = set(_we_ids(self, player))
            if "arcane_firmament" in _weids:
                _af_pct = float(_we_edp(self, player, "arcane_firmament").get("matk_pct", 0.15) or 0.15)
                st["matk"] = int(st.get("matk", 0) * (1 + _af_pct))
            _gale_pct = float((self._p_eff() or {}).get("gale_step_pct", 0) or 0)
            if _gale_pct > 0 and self._p_buffs_bag().get("gale_step"):
                st["spd"] = int(st.get("spd", 0) * (1 + _gale_pct))
            if "star_slayer_edge" in _weids:
                _sse_cd = float(_we_edp(self, player, "star_slayer_edge").get("crit_dmg", 0.30) or 0.30)
                st["crit_dmg"] = float(st.get("crit_dmg", 0) or 0) + _sse_cd
            if "endless_radiance" in _weids:
                _er_cd = float(_we_edp(self, player, "endless_radiance").get("crit_dmg_pct", 0.25) or 0.25)
                st["crit_dmg"] = float(st.get("crit_dmg", 0) or 0) + _er_cd
            # 风痕（风行短弓）：每层速度 +X%
            _wm = int((self._p_stacks() or {}).get("wind_mark", 0) or 0)
            if _wm > 0:
                try:
                    from .core.weapon_effects import effect_data as _we_edw
                    _wm_pct = float(_we_edw(self, self.player, "wind_mark").get("spd_pct_per", 0.02) or 0.02)
                except Exception:
                    _wm_pct = 0.02
                st["spd"] = int(st.get("spd", 0) * (1 + _wm_pct * _wm))
            # v140 波4：新手特效 翠风（novice_wind_spd）——命中后自身速度 +5%（2 刻）
            if self._p_buffs_bag().get("novice_wind_spd"):
                try:
                    from .core.weapon_effects import effect_data as _we_ed2
                    _nws_pct = float(_we_ed2(self, self.player, "novice_wind_spd").get("spd_pct", 0.05) or 0.05)
                except Exception:
                    _nws_pct = 0.05
                st["spd"] = int(st.get("spd", 0) * (1 + _nws_pct))
            # 雷纹连打（雷纹拳甲）：每层速度 +X%、攻击 +X%
            _tw = int((self._p_stacks() or {}).get("thunder_weave", 0) or 0)
            if _tw > 0:
                try:
                    from .core.weapon_effects import effect_data as _we_edt
                    _tw_spd = float(_we_edt(self, self.player, "thunder_weave").get("spd_pct_per", 0.02) or 0.02)
                    _tw_atk = float(_we_edt(self, self.player, "thunder_weave").get("atk_pct_per", 0.01) or 0.01)
                except Exception:
                    _tw_spd, _tw_atk = 0.02, 0.01
                st["spd"] = int(st.get("spd", 0) * (1 + _tw_spd * _tw))
                st["atk"] = int(st.get("atk", 0) * (1 + _tw_atk * _tw))
        except Exception as _sw_e:
            _battle_warn('_player_stats', _sw_e)
            pass
        return st

    def _passive_map(self, player: dict) -> dict:
        """v104 R3 P1-1：已学被动按 proc/stat 聚合（数据驱动，替代名字硬匹配）。
        返回 {"proc": {proc名: [(被动名, passive字段), ...]}, "stat": [(被动名, passive字段), ...]}"""
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

    # ---------------- v169.7 被动接线辅助（只读本族状态；见下方各族消费点） ----------------
    def _proc_pm(self, player: dict) -> dict:
        """已学被动按 proc 聚合（空 _passive_map 重建的轻封装，调用侧与 _passive_map 全等）。"""
        try:
            return self._passive_map(player)
        except Exception:
            return {"proc": {}, "stat": []}

    def _zhan_yi_n(self) -> int:
        """战士战意叠层（mech_stacks.zhan_yi 0-10，battle_mech _m_zhan_yi 写入）。"""
        return int((self._p_stacks() or {}).get("zhan_yi", 0) or 0)

    def _guard_core_n(self) -> int:
        """拳师磐核数（resources.guard_core，GUARD_CORE_CFG max=5）。"""
        return int((self._p_res() or {}).get("guard_core", 0) or 0)

    def _poison_cap(self, player: dict) -> int:
        """毒层上限：基础 5（MECH_STACK_MAX poison=5 / battle_mech 叠层 min(5, ...)）+ 被动提升。
        剧毒之心（游侠 poison_cap_up +3）/ 淬毒之心（刺客 poison_cap +3，最高 8）。
        v181.P2D-D1：被动提升读注册表族 stack_cap_add（cap 基础 5 累加，封顶/下限保留原语义）。"""
        cap = 5
        pm = self._proc_pm(player)
        for _pn, _ps in pm["proc"].get("poison_cap_up", []):
            _ctx_cap = {"player": player, "ps": _ps, "ps_name": _pn, "cap": cap}
            _run_proc_family(self, "poison_cap_up", _ctx_cap)
            cap = _ctx_cap.get("cap", cap)  # handler 数值槽改写读回（cap int 不可变）
        for _pn, _ps in pm["proc"].get("poison_cap", []):
            _ctx_cap2 = {"player": player, "ps": _ps, "ps_name": _pn, "cap": cap}
            _run_proc_family(self, "poison_cap", _ctx_cap2)
            cap = _ctx_cap2.get("cap", cap)
        return max(5, min(cap, 8))

    def _shadow_dance(self, player: dict) -> bool:
        """影舞态（v169.7 battle.py 侧接线）：暗影步 effect=shadow_dance 施放时置位
        p_buffs.shadow_dance（see _skill_buff 消费点）；后续在 _combo_break / _set_skill_cd 消费。"""
        return bool(self._p_buffs_bag().get("shadow_dance"))

    def _melody_state(self) -> dict:
        """诗人旋律状态（battle_mech._melody_state 同结构：{name, stack, finale_ready}）。"""
        mel = getattr(self, "_melody", None)
        if not isinstance(mel, dict):
            return {"name": None, "stack": 0, "finale_ready": False}
        return mel

    def _enemy_debuff_kind_count(self) -> int:
        """敌方当前携带的负面种类数（挽歌·极 dirge_debuff_dmg：每 1 个负面 +4%，上限 40%）。
        统计：debuffs 各类型（poison/burn/bleed/mark/corros/curse/soul_mark/hunt_mark）+ e_buffs 控制/减益键
        （stun/freeze/silence/sleep/spd_down/def_down/mon_atk_down）——只数“正在生效”的种数。"""
        e = self.enemy or {}
        n = 0
        try:
            db = e.get("debuffs") or {}
            for k, d in db.items():
                if not isinstance(d, dict):
                    if int(d or 0) > 0:
                        n += 1
                    continue
                if int(d.get("n", 0) or 0) > 0 or int(d.get("turns", 0) or 0) > 0:
                    n += 1
        except Exception as _sw_e:
            _battle_warn('_enemy_debuff_kind_count', _sw_e)
            pass
        try:
            eb = e.get("buffs") or {}
            for k in ("stun", "freeze", "silence", "sleep", "spd_down", "def_down", "mon_atk_down", "mon_spd_down", "atk_down"):
                if eb.get(k):
                    n += 1
        except Exception as _sw_e:
            _battle_warn('_enemy_debuff_kind_count', _sw_e)
            pass
        return n

    def _passive_crit_bonus(self, player: dict, info: dict | None = None) -> float:
        """v169.7 条件暴击被动族统一消费（加法并入暴击率，随 PCT_CAPS.crit 上限截断）：
        - 狂热 zhan_yi_crit（战士）：战意 ≥8 暴击 +15%
        - 真知 arcane_wisdom（法师）：奥术充能满 5 暴击 +20%（charge 存 mech_stacks.arcane / element_charge）
        - 疾风之心 focus_surplus_crit（游侠攻线）：专注结余 ≥40 时下次技能暴击 +20%（一次性消费）
        - 元素之核 element_core（法师元素）：单系印记满 3 结算暴击 +20%（充能引爆类结算技）
        - 暗影步·极 shadow_dance_bonus：影舞态中暴击伤害 +20%（暴伤加成走 _passive_crit_dmg_mult）
        返回暴击率增量（0~1）。
        v181.P2D-D2a：4 个条件暴击 proc 消费迁注册表族 crit_cond_add（ctx res_kind 分派条件谓词：
        zhan_yi 战意 / arcane 奥术充能 / focus 精力快照 / element_mark 元素印记）；循环骨架、
        顺序、break 语义逐字保留（zy/arcane/focus 命中即 break；element_core 无条件 break——
        max=1 数据下等价，多条目防御保留原"只判首条"语义）。"""
        bonus = 0.0
        try:
            pm = self._proc_pm(player)
            # 狂热（战意层 ≥ stacks → +add）
            for _pn, _ps in pm["proc"].get("zhan_yi_crit", []):
                _ctx_zy = {"player": player, "ps": _ps, "ps_name": _pn,
                           "res_kind": "zhan_yi", "crit_add": bonus, "info": info}
                if _run_proc_family(self, "zhan_yi_crit", _ctx_zy):
                    bonus = _ctx_zy.get("crit_add", bonus)  # handler 数值槽改写读回
                    break
            # 真知（守线·奥秘法师充能条 / 攻线 arcane 叠层；满层门槛读数据 stacks）
            for _pn, _ps in pm["proc"].get("arcane_wisdom", []):
                _ctx_aw = {"player": player, "ps": _ps, "ps_name": _pn,
                           "res_kind": "arcane", "crit_add": bonus, "info": info}
                if _run_proc_family(self, "arcane_wisdom", _ctx_aw):
                    bonus = _ctx_aw.get("crit_add", bonus)
                    break
            # 疾风之心（游侠：专注结余 = 精力当前值，≥40 时本技能暴击 +20% 一次性）
            # v169.7 修 #123：读「施放前」精力快照（_pre_cost_res）——技能 res_cost 扣费后才结算暴击，
            # 读扣费后 energy 会让高耗技(30/35)施放时 energy 跌破 40 → 凝神永不触发（与满弦同坑，
            # 见 _energy_high_crit）。快照缺失（直接调用非技能链）回落当前值。
            if info is not None:
                for _pn, _ps in pm["proc"].get("focus_surplus_crit", []):
                    _ctx_fc = {"player": player, "ps": _ps, "ps_name": _pn,
                               "res_kind": "focus", "crit_add": bonus, "info": info}
                    if _run_proc_family(self, "focus_surplus_crit", _ctx_fc):
                        bonus = _ctx_fc.get("crit_add", bonus)
                        break
            # 元素之核（法师元素攻线：单系印记满 _ps.layers（默认 3）时该系结算暴击 +20%）
            if info is not None:
                for _pn, _ps in pm["proc"].get("element_core", []):
                    _ctx_ec = {"player": player, "ps": _ps, "ps_name": _pn,
                               "res_kind": "element_mark", "crit_add": bonus, "info": info}
                    if _run_proc_family(self, "element_core", _ctx_ec):
                        bonus = _ctx_ec.get("crit_add", bonus)
                    break  # 原无条件 break（印记不足也 break——多条目下只判首条）
        except Exception as _sw_e:
            _battle_warn('_passive_crit_bonus', _sw_e)
            pass
        return bonus

    def _passive_crit_dmg_mult(self, player: dict) -> float:
        """v169.7 暴伤乘区被动：
        - 暗影步·极 shadow_dance_bonus：影舞态中暴击伤害 +20%（暴伤属性加算并入 cdmg）
        返回加法增量（0~1）。
        v181.P2D-D2b：消费迁注册表族 stat_mult_cond（ctx stat_kind='crit_dmg' 段；影舞态守卫
        保留原 `if self._shadow_dance(player):` 骨架），循环骨架/顺序/break 语义逐字保留。"""
        extra = 0.0
        try:
            if self._shadow_dance(player):
                for _pn, _ps in self._proc_pm(player)["proc"].get("shadow_dance_bonus", []):
                    _ctx_cd = {"player": player, "ps": _ps, "ps_name": _pn, "stat_kind": "crit_dmg"}
                    _rv = _run_proc_family(self, "shadow_dance_bonus", _ctx_cd)
                    if _rv:
                        extra += float(_rv[0])  # 返回值 = 暴伤加法增量（读 _ps.crit_dmg）
                    break
        except Exception as _sw_e:
            _battle_warn('_passive_crit_dmg_mult', _sw_e)
            pass
        return extra

    # ---- v169.7 战士守线·坚韧 / 铁誓·不动 / 血怒·不灭 状态 ----
    def _tenacity_left(self) -> int:
        """坚韧被动剩余次数（每场 3 次，随战斗序列化）。"""
        if not hasattr(self, "_tenacity_left_n"):
            self._tenacity_left_n = 3
        return int(self._tenacity_left_n)

    def _tenacity_try_break(self, player: dict, logs: list) -> bool:
        """坚韧 tenacity：被控时消耗 2 层战意跳过控制（每场 3 次）。
        有战意（≥ps.cost 默认 2）且剩余次数 >0 → 扣战意 + 次数 -1，返回 True（本刻照常行动）。"""
        try:
            _pm = self._proc_pm(player)
            if not _pm["proc"].get("tenacity"):
                return False
            _ps = _pm["proc"]["tenacity"][0][1]
            cost = int(_ps.get("cost", 2) or 2)
            if self._zhan_yi_n() < cost:
                return False
            if self._tenacity_left() <= 0:
                return False
            # 消耗战意 + 次数
            self._p_stacks()["zhan_yi"] = max(0, self._zhan_yi_n() - cost)
            self._tenacity_left_n = self._tenacity_left() - 1
            _pn = _pm["proc"]["tenacity"][0][0]
            logs.append(f"🛡️ {_pn}：消耗 {cost} 层战意挣脱控制！（剩余 {self._tenacity_left()} 次）")
            return True
        except Exception:
            return False

    def _player_attack(self, st: dict, player: dict) -> list:
        """v174.1 普攻行动 = 释放职业 basic_skill（玩家敲"攻击"即施放该技能）。

        代码层不做任何普攻特判计算——basic_skill 是数据配置的普通技能
        （exprs 公式 / res_gain 资源 / 无 CD 无消耗），一切乘区/资源/命中
        效果均由 _player_skill 统一技能管道结算。旧版手抄 ~200 行普攻乘区
        已删除（v174.1，鱼鱼拍板：保留一套技能代码，配置做不到=设计问题）。
        """
        bs = None
        try:
            _cid = C.resolve("classes", player.get("class_name", ""))
            bs = ((C.CLASSES.get(_cid, {}) or {}).get("basic_skill")) or {}
        except Exception:
            bs = {}
        if not isinstance(bs, dict) or not bs.get("name") or not (bs.get("exprs") or bs.get("formula")):
            # 无 basic_skill 的职业回退：纯物理普攻技能（atk×1.0 物理段）
            bs = {"name": "攻击", "kind": "物理", "exprs": ["atk*1.0"]}
        info = dict(bs)
        # basic 技能无 CD/无蓝耗/无需学习等级（skill_levels 无此技能 → lv=0，
        # expr 公式内嵌全部数值、无需技能成长）；资源获取由 res_gain / on_skill 数据驱动
        return self._player_skill(st, info["name"], info, player, target=None)

    def _settle_lifesteal(self, player: dict, dmg: int, logs: list, magic: bool = False, dmg_type: str = "phys"):
        """v106.3 吸血统一结算（属性面板化）：heal = dmg × 吸血率

        来源全部汇聚到 st["lifesteal"]（通用，词条吸血/种族/被动/药水），
        v106.4 细分：物理吸血 lifesteal_phys（物理攻击段）、法术吸血 lifesteal_magi（魔法攻击段）
        与通用吸血乘算合成 1-(1-a)(1-b)；药水 buff 乘算并入，cap 30%。
        v107 真伤不吸血（纯真伤语义，鱼鱼拍板）：dmg_type == "true" 直接跳过。
        v169.7：淬血 zhan_yi_lifesteal —— 每层战意额外 +1.5% 吸血（加算并入 rate，
        突破通用 30% cap 后仍受下方 cap 30% 限制——战士常规吸血堆叠上限保持，防膨胀）。
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
        if self._p_buffs_bag().get("lifesteal_pot"):
            rate = 1 - (1 - rate) * (1 - 0.15)  # 嗜血药剂 +15% 吸血（乘算并入）
        # v169.7 淬血（战士攻线）：每层战意 +1.5% 吸血（数据驱动 proc zhan_yi_lifesteal）
        # v181.P2D-D1：proc 消费迁移注册表族 lifesteal_add（读 _ps per_layer，行为零变化）
        try:
            _zy = self._zhan_yi_n()
            if _zy > 0:
                for _pn, _ps in self._passive_map(player)["proc"].get("zhan_yi_lifesteal", []):
                    _ctx_zy = {
                        "player": player, "ps": _ps, "ps_name": _pn,
                        "zhan_yi_n": _zy, "rate": rate,
                    }
                    _run_proc_family(self, "zhan_yi_lifesteal", _ctx_zy)
                    rate = _ctx_zy.get("rate", rate)  # handler 数值槽改写读回（rate float 不可变）
                    break
        except Exception as _sw_e:
            _battle_warn('_settle_lifesteal', _sw_e)
            pass
        rate = min(rate, 0.30)
        # v1.3 重伤（mortal_wound）：目标被重创后吸血效果减半（Boss『重创』类技能施加）
        if self._p_buffs_bag().get("mortal_wound"):
            rate *= 0.5
        if rate <= 0:
            return
        heal = int(dmg * rate)
        if heal <= 0:
            return
        self._heal_actor(player, heal, logs)  # v180E 统一落地
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
            self._p_res()[k] = self._res_gain_class(cls, k, gain)
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
        if info and info.get("kind") == K_HEAL and rd.get("on_heal") and k in act_keys:
            # v153 §4（C-18）：力竭中信念不增加（过载后 6 刻）
            if not self._p_buffs_bag().get("faith_exhausted"):
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
                self._p_res()[k] = self._res_gain_class(cls, k, gain + on_skill_extra)
        # v139 双形态进入检查：技能结算后资源已更新，若满足入形态条件（狂战士满 10 怒 / 龙裔龙力≥8）自动进入
        # （auto 技能显式声明 或 资源达 enter_requirement 均可触发；免费切换不占行动）
        try:
            from .core.battle_modes import dual_form_def as _dfd139, dual_form_state as _dfs139, dual_form_can_enter as _dfce139, dual_form_enter as _dfe139
            _df_cfg = _dfd139(player)
            if _df_cfg:
                _df_key = _df_cfg.get("key", k)
                _df_val = int(self._p_res().get(_df_key, 0) or 0)
                _df_auto = (info or {}).get("auto", "")
                _df_want = _df_auto in ("rage_form_enter", "dragon_form_enter") or _dfce139(player, _df_val)
                if _df_want and not _dfs139(player).get("form") == "alt":
                    if _dfe139(player, logs):
                        logs.append(f"⚡【{_df_cfg.get('form', '形态')}】觉醒！(资源 {_df_val})")
        except Exception as _sw_e:
            _battle_warn('_resource_on_skill', _sw_e)
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
            if self._p_buffs_bag().get("stealth") or self._p_stealth_atk():
                gain += int(SHADOW_STEP_CFG.get("stealth_extra", 1) or 0)
            self._p_res()[k] = E.core_resource_gain(cls, self._p_res(), gain)
            proc_ok = True
        # 刺客攻线·影舞者：on_crit 额外 +1 连击点（叠于 on_attack/on_skill）
        elif self._combo_active(player):  # v176: combo归属已数据化COMBO_CFG
            self._p_res()[k] = E.core_resource_gain(cls, self._p_res(), ASSASSIN_ON_CRIT_GAIN)
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
        _before = int(self._p_res().get("cp", 0) or 0)
        _now = self._res_gain_class(_cls, "cp", 1)
        if _now > _before:  # 真实增量判定（连击点已满时不误报返还）
            logs.append(f"🗡️ 致命预谋：首次终结返还 1 连击点（当前 {_now}）")

    def _apply_enchant_attack(self, effs: dict, dmg: int, st: dict, player: dict, logs: list):
        """v34：攻击后符文效果结算(灼烧/冻结/吸血/连锁/虚弱/破魔)"""
        if not effs:
            return
        p_mech = self._p_stacks()
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
            self._heal_actor(player, heal, logs)  # v180E 统一落地
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
                self._deal_damage(cd, logs)
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
        """场上存活亡灵单位计数：玩家召唤骷髅（skeleton tid）或敌方名含亡灵系关键词。
        关键词与成就 亡灵使者 kills_type 同源（game/data/achievements.py ach_undead100）。"""
        n = 0
        for s in self.summons:
            if s.get("hp", 0) > 0 and s.get("tid") == "skeleton":
                n += 1
        for u in self.enemies:
            if u.get("hp", 0) > 0 and any(k in str(u.get("name", "")) for k in _UNDEAD_KEYWORDS):
                n += 1
        return n

    def _minion_count(self, boss: dict | None = None) -> int:
        """v178 E8a：场上存活爪牙（is_minion）计数——Boss 机制条件用
        （月神守卫存活机关数/歌澜和声数/奥姆骷髅龙数等）。
        boss 参数缺省时数全场 minion；传 boss 时数 boss 队伍内（同 enemies 阵列）的 minion。"""
        n = 0
        for u in self.enemies:
            if u.get("hp", 0) > 0 and u.get("is_minion"):
                n += 1
        return n

    def _on_minion_died_tick(self, e: dict, logs: list) -> bool:
        """v178 E8b：消费 Boss 配的爪牙死亡联动（数据驱动）。
        Boss dict 配 "on_minion_died": {"effect": "<effect_id>", "value": N} →
        场上任一爪牙死亡当刻触发一次。effect_id 现支持：
          - "stacks_clear": 清空 Boss 叠层（轰鸣碎晶核放能）
          - "shield": 给 Boss 套盾（月神守卫机关被击后自保）
          - "heal_pct": 回 value% 血（奥姆吸骷髅龙魂）
          - "atk_up": 加攻 value 刻（赫尔加吃怪变强）
        返回是否触发。"""
        if not e or not e.pop("_minion_died_this_act", False):
            return False
        try:
            cfg = e.get("on_minion_died") or {}
            eff = cfg.get("effect")
            if not eff:
                return False
            if eff == "stacks_clear":
                e["stacks"] = {}
                e.pop("mech_stacks_n", None)
                logs.append(f"⚡ 【{e.get('name', 'Boss')}】积蓄被击散，层数清零！")
                return True
            if eff == "shield":
                _val = int(e.get("max_hp", 1) * 0.20)
                e.setdefault("shields", {})["on_minion"] = {"value": _val, "halve": True}
                logs.append(f"🛡️ 【{e.get('name', 'Boss')}】失去爪牙后竖起护盾！")
                return True
            if eff == "heal_pct":
                _pct = float(cfg.get("value", 0.05) or 0.05)
                _heal = int(e.get("max_hp", 1) * _pct)
                self._heal_actor(e, _heal, logs)  # v180E 统一落地
                logs.append(f"💚 【{e.get('name', 'Boss')}】吸取爪牙残魂，回复 {_heal} 点生命！")
                return True
            if eff == "atk_up":
                _turns = int(cfg.get("value", 2) or 2)
                e.setdefault("buffs", {})["mon_atk_up"] = max(e.get("buffs", {}).get("mon_atk_up", 0), _turns)
                logs.append(f"🔥 【{e.get('name', 'Boss')}】吞噬爪牙之力，攻击提升！")
                return True
        except Exception as _sw_e:
            _battle_warn('_on_minion_died_tick', _sw_e)
            pass
        return False

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
            self._heal_actor(player, hp, logs)  # v180E 统一落地
        for _ally in (self.allies or []):
            if isinstance(_ally, dict) and _ally.get("hp", 0) < _ally.get("max_hp", 1):
                self._heal_actor(_ally, hp, logs)  # v180E 统一落地
        logs.append(f"🌞 圣典·日冕：神迹余晖笼罩全队，恢复 {hp} 点体力！")

    def _set_skill_dmg_mult(self, player: dict, info: dict, kind: str, skill_name: str) -> float:
        """v130.2c 套装技能伤害倍率：
        势不可挡 4 件（气力技/终结技 物理伤害 +15%）。
        v176: 暗夜圣典旧 elegy_dmg 分支删除（数据 bonus_4 已改 proc_flat_dmg，无套装配 elegy_dmg = 死分支）。"""
        mult = 1.0
        effs = self._set_eff(player, "chi_skill_phys", 4)
        if effs and kind == K_PHYS:
            # v130.2 R1：势不可挡收窄为 chi 资源相关（res_cost.chi / consume_all key==chi / 拳师），与 burst_break 口径一致
            _rc = info.get("res_cost") or {}
            _ca = info.get("consume_all") or {}
            is_chi_fin = "chi" in self._branch_keys(player) or bool(_rc.get("chi")) or _ca.get("key") == "chi"
            if is_chi_fin:
                mult *= 1.0 + float(effs.get("value", 0.15) or 0.15)
        return mult

    def _set_bonus_5(self, player: dict) -> list:
        """已激活 5 件套的套装名列表(10 章五节 5 件效果，战斗特效型)"""
        return [sname for sname, cnt in E.active_sets(player.get("equipment") or {}).items()
                if cnt >= 5]

    def _set_bonus_5_has_effect(self, player: dict, effect_name: str) -> bool:
        """v181-A1 数据驱动：已激活 5 件套中是否任一声明 bonus_5.effect == effect_name。

        替代 battle 内 \"星尘\" 等中文套装名特判——任意套装在 class_sets bonus_5 声明
        effect 即生效（_th_stardust_mana / _regen_needed / _ensure_regen_effects 共用）。"""
        try:
            for sname in self._set_bonus_5(player):
                _b5 = (E._set_info(sname) or {}).get("bonus_5") or {}
                if _b5.get("effect") == effect_name:
                    return True
        except Exception:
            pass
        return False

    def _set_bonus_5_ctrl_immune(self, player: dict) -> list:
        """v180-B ② 套装 5 件控制免疫数据化：已激活 5 件套声明 bonus_5_ctrl_immune 的
        控制类型列表（如霜狼套 ["slow"]）。数据源 class_sets.py 套装定义（经 _build_class_sets
        注册进 C.SETS），替代引擎内 '霜狼' 字符串特判——任意套装声明即生效，任意 actor 可配。

        注意：active_sets 返回装备 set 字段的系列名（"霜狼"），C.SETS 条目 name 是
        主题名（"霜狼套"）——查表需经 SERIES_SETS 系列映射或 name 匹配。"""
        try:
            out = []
            _sets = getattr(C, "SETS", {}) or {}
            for sname in self._set_bonus_5(player):
                _sd = _sets.get(sname)  # 直接命中（set 字段即 SETS key 的情况）
                if _sd is None:
                    for _info in _sets.values():
                        if _info.get("name") == sname:
                            _sd = _info
                            break
                if _sd is None:
                    # 系列名 → 主题名（SERIES_SETS: "霜狼"→"霜狼套"）
                    try:
                        from .data.equip_roster import SERIES_SETS as _SS
                        _theme = (_SS or {}).get(sname, sname)
                        for _info in _sets.values():
                            if _info.get("name") == _theme:
                                _sd = _info
                                break
                    except Exception as _sw_e:
                        _battle_warn('_set_bonus_5_ctrl_immune', _sw_e)
                        pass
                if _sd:
                    out.extend(list(_sd.get("bonus_5_ctrl_immune") or []))
            return out
        except Exception:
            return []

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
            # v181.D（P1-D）：数值/标签读 data/races.py（RACE_ATTACK_MULT + races 表展示键）
            mult *= _RACE_ATTACK_MULT["berserk"]
            tags.append(rt.get("berserk_tag") or "🔥无畏")
        tm = rt.get("timid_hp")
        if tm and ratio < tm:
            mult *= _RACE_ATTACK_MULT["timid"]
            tags.append(rt.get("timid_tag") or "😰怯战")
        fh = rt.get("first_hit")
        if fh and not self.first_attack_done:
            mult *= 1 + fh
            _fh_tag = rt.get("first_hit_tag")
            if _fh_tag:
                tags.append(_fh_tag.format(mult=round(1 + fh, 2)))
            else:
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
            if sk and any((self._lookup_skill_info(s) or {}).get("kind") == K_MAGI for s in sk):
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

    def _player_dmg_mult(self, player: dict, kind: str = K_PHYS) -> tuple:
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
        if (self._p_eff() or {}).get("wolf_howl_mult"):
            mult = mult * float(self._p_eff().get("wolf_howl_mult", 1.10))
            tags = list(tags) + ["🐺狼嚎x1.1"]
        # v130.2 拳师蓄势 Momentum（攻线·格斗士）：物理伤害吃「每 1 气 +3%」持有加伤
        _mom = self._momentum_mult(player)
        if kind == K_PHYS and _mom != 1.0:
            mult *= _mom
            tags = list(tags) + [f"🔥蓄势x{round(_mom, 2)}"]
        # v130.2f2 苦修禅意（武僧线）：物理伤害吃「每 1 禅意 +4%」持有加伤
        # v130.2 澎湃烈酒（phys_up）/ 引气精华（buff_phys_next）：物理伤害 +pct%
        if kind == K_PHYS and (self._p_buffs_bag().get("phys_up") or self._p_buffs_bag().get("buff_phys_next")):
            _pu = float((self._p_eff() or {}).get("phys_up", 0) or 0)
            _bpn = float((self._p_eff() or {}).get("buff_phys_next", 0) or 0)
            if _pu > 0:
                mult *= (1 + _pu)
            if _bpn > 0:
                mult *= (1 + _bpn)
                del self._p_buffs_bag()["buff_phys_next"]
                self._p_eff().pop("buff_phys_next", None)
            _tags_pu = ([f"🍺物理x{round(1 + _pu, 2)}"] if _pu > 0 else []) + \
                       ([f"🥊引气x{round(1 + _bpn, 2)}"] if _bpn > 0 else [])
            if _tags_pu:
                tags = list(tags) + _tags_pu
        # 阶段九：种族攻击天赋（无畏/怯战 残血、龙之吐息 首击）
        race_mult, race_tags = self._race_attack_mult(player)
        if race_tags:
            tags = list(tags) + race_tags
        # v169.7 疾风·极 speed_ratio_dmg（游侠）：速度比 ≥2.0 时所有伤害 ×1.2
        # （读实时敌方速度；敌方无速度键时按 0 防御性跳过，不误触）
        # v181.P2D-D1：proc 消费迁移注册表族 dmg_mult_cond（读 _ps ratio/dmg_add，行为零变化）
        try:
            _pst_spd = max(0.001, float((self._player_stats(player) or {}).get("spd", 0) or 0))
            _est_spd = float((self._enemy_stats() or {}).get("spd", 0) or 0)
            for _pn_sr, _ps_sr in self._proc_pm(player)["proc"].get("speed_ratio_dmg", []):
                _ctx_sr = {
                    "player": player, "ps": _ps_sr, "ps_name": _pn_sr,
                    "pst_spd": _pst_spd, "est_spd": _est_spd, "mult": mult, "tags": tags,
                }
                _run_proc_family(self, "speed_ratio_dmg", _ctx_sr)
                mult = _ctx_sr.get("mult", mult)   # handler 数值槽改写读回（mult float 不可变）
                tags = _ctx_sr.get("tags", tags)
                break
        except Exception as _sw_e:
            _battle_warn('_player_dmg_mult', _sw_e)
            pass
        return mult * race_mult, tags

    def _extra_dmg_mult(self, hp_ratio: float, mult: float, tags: list) -> tuple:
        """v101.28e/f 食物效果 + 药水特殊效果的伤害倍率（独立于装备词条）。

        食物：处决（<30% +30%）/ 精准（+10%）。
        药水：死神药剂（<30% +30%）/ 狂怒药剂（下次攻击 +50%，一次性消耗）。
        龙语印记：每层 +2% 伤害（v104 移入此处——此前 _affix_dmg_mult 在无词条时提前
        return 会漏结算该倍率，有词条路径在调用后单独结算，两路径行为不一致）。
        """
        foods = self._p_food_effects() or []
        # v110 审计修复：处决阈值 0.35 → 0.30（v109 拍板「斩杀线以 30% 为准」，
        # 与文案/设计 <30% 及 execute 被动 cond_hp=0.30 统一）
        # v180F 清2b：数值读数据表 food_effect_data.py（原硬编码 0.30/1.30/1.10）
        from .data.food_effect_data import FOOD_EFFECT_PARAMS as _FEP2
        _exe = _FEP2.get("execute") or {}
        _pre = _FEP2.get("precise") or {}
        _exe_hp = float(_exe.get("hp_ratio", 0.30) or 0.30)
        _exe_m = float(_exe.get("mult", 1.30) or 1.30)
        _pre_m = float(_pre.get("mult", 1.10) or 1.10)
        if "execute" in foods and hp_ratio < _exe_hp:
            mult *= _exe_m
            tags.append("💀处决")
        if "precise" in foods:
            mult *= _pre_m
            tags.append("🎯精准")
        if self._p_buffs_bag().get("execute_pot") and hp_ratio < 0.30:
            mult *= 1.30
            tags.append("💀处决")
        if self._p_buffs_bag().get("next_atk_up"):
            mult *= 1.50
            del self._p_buffs_bag()["next_atk_up"]
            tags.append("⚔️狂怒")
        dm = int(self._p_stacks().get("dragon_mark", 0) or 0)
        if dm:
            # v126 数值下沉：每层增伤读龙语印记数据 mark_pct（缺省 2%）
            _dt = (C.AFFIXES.get("dragon_tongue") or {}).get("effect") or {}
            mult *= 1 + float(_dt.get("mark_pct", 0.02)) * dm
        return mult, tags

    def _consume_v169_buff_dmg(self, kind: str = K_PHYS, element: str = "", skill_name: str = "") -> tuple:
        """v169.7 battle_mech §4.6/4.7 effect handler 写入的乘区键消费（普攻/技能伤害统一挂点）。

        battle_mech 写端遵循 phys_up 模式：p_buffs 存 int 时长（_advance_time 按刻到期），
        p_eff 存 float 数值。本函数在伤害结算主路径调用：
          - hunt_team_dmg  猎杀时刻：目标带猎印（debuffs.hunt_mark>0）→ ×(1+pct)
          - star_lock      星轨锁定：当前目标（单机主敌）→ ×(1+pct)
          - arcane_matrix  奥术矩阵：奥术/魔法伤害 +20%（kind=魔法，持续）
          - arcane_field   奥术力场·利刃：下次奥术技 ×1.3（一次性消费，读完即删）
        返回 (mult, tags)。
        """
        mult = 1.0
        tags = []
        if not (self._p_buffs_bag() or {}).get("hunt_team_dmg") and not (self._p_buffs_bag() or {}).get("star_lock") \
                and not (self._p_buffs_bag() or {}).get("arcane_matrix") and not (self._p_buffs_bag() or {}).get("arcane_field"):
            return mult, tags
        # 猎杀时刻：对带猎印目标增伤
        if self._p_buffs_bag().get("hunt_team_dmg"):
            _hm = int(((self.enemy or {}).get("debuffs") or {}).get("hunt_mark", 0) or 0)
            if _hm > 0:
                pct = float((self._p_eff() or {}).get("hunt_team_dmg", 0) or 0)
                if pct > 0:
                    mult *= 1.0 + pct
                    tags.append("🎯猎杀")
        # 星轨锁定：对当前主目标增伤
        if self._p_buffs_bag().get("star_lock"):
            pct = float((self._p_eff() or {}).get("star_lock", 0) or 0)
            if pct > 0:
                mult *= 1.0 + pct
                tags.append("🌟锁定")
        # 奥术矩阵：魔法/奥术伤害
        if self._p_buffs_bag().get("arcane_matrix") and kind == K_MAGI:
            pct = float((self._p_eff() or {}).get("arcane_matrix", 0) or 0)
            if pct > 0:
                mult *= 1.0 + pct
                tags.append("🔮奥术")
        # 奥术力场·利刃：下次奥术技（魔法）伤害 ×1.3 一次性
        if self._p_buffs_bag().get("arcane_field") and kind == K_MAGI:
            pct = float((self._p_eff() or {}).get("arcane_field", 0) or 0)
            if pct > 0:
                mult *= 1.0 + (pct - 1.0)  # p_eff 存 1.30 完整倍率 → 折算成增量
                tags.append("📖力场")
            del self._p_buffs_bag()["arcane_field"]
            self._p_eff().pop("arcane_field", None)
        # v180E 秘法回响（arcane_echo 词条）：下次技能伤害 +X%（一次性，任何 kind 技能消费）
        if self._p_buffs_bag().get("arcane_echo"):
            pct = float((self._p_eff() or {}).get("arcane_echo", 0) or 0)
            if pct > 0:
                mult *= 1.0 + pct
                tags.append("🔮回响")
            del self._p_buffs_bag()["arcane_echo"]
            self._p_eff().pop("arcane_echo", None)
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
        # 套装 5 件元素增伤（v181-A1 数据化：月语/海神 bonus_5.element_dmg.ice=0.10、
        # 苍穹 bonus_5.element_dmg.thunder=0.10——泛读声明，替代中文套装名特判）
        for sname in self._set_bonus_5(player):
            _ed = ((E._set_info(sname) or {}).get("bonus_5") or {}).get("element_dmg") or {}
            bonus += float(_ed.get(element, 0) or 0)
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
                self._aoe_damage(ad, logs)
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
        if not self._p_food_effects() or self.enemy.get("hp", 0) <= 0:
            return
        from .core.food_effects import FOOD_HIT_EFFECTS
        for key in self._p_food_effects():
            fn = FOOD_HIT_EFFECTS.get(key)
            if fn:
                fn(self, player, dmg, logs)

    def _food_on_taken(self, player: dict, dmg: int, logs: list) -> int:
        """受击料理效果（反击/反伤）。返回结算后伤害（当前食物效果不改减伤，透传）。"""
        if not self._p_food_effects():
            return dmg
        from .core.food_effects import FOOD_TAKEN_EFFECTS
        ctx = {"dmg": dmg, "out": dmg}
        for key in self._p_food_effects():
            fn = FOOD_TAKEN_EFFECTS.get(key)
            if fn:
                fn(self, player, ctx, logs)
        return ctx["out"]

    def _food_turn_start(self, player: dict, logs: list):
        """刻开始料理效果（回春/冥想/晨曦祝福）。"""
        if not self._p_food_effects():
            return
        from .core.food_effects import FOOD_TURN_START_EFFECTS
        for key in self._p_food_effects():
            fn = FOOD_TURN_START_EFFECTS.get(key)
            if fn:
                fn(self, player, logs)


    def _heal_actor(self, target: dict, amount: int, logs: list, *,
                    source: dict | None = None, label: str = "") -> int:
        """v180E 统一治疗落地核心（actor-agnostic）：给任意 actor 回血。

        clamp + 受疗天赋（target 自身 race heal_received）+ 禁疗/重伤（target 自身 buffs
        heal_down / _anti_heal_pct）统一收口在这里——全引擎 20+ 处 hp=min(max_hp,hp+heal)
        直写点应改调本方法，获得一致的禁疗/重伤/受疗语义。

        - target: 任意 actor dict（玩家/怪物/随从/队友快照）
        - amount: 计划治疗量（调用方已完成加成计算——玩家被动在调用方 _skill_heal 等处理，
          本核心不读施法者被动；target 是怪则不吃玩家 heal_power/圣光套/神恩）
        - source: 施法者 actor（可选，用于日志）
        - label: 日志前缀（可选）
        返回实际回血量（clamp 后）。需要\"禁疗修正后、clamp 前\"量做溢出计算的主路径
        （_skill_heal）请用 _apply_heal_mods + _heal_land 两层组合。
        """
        if target is None or amount is None:
            return 0
        if target.get("hp") is None:
            return 0  # 无 hp 容器（宠物 actor hidden/untargetable）不可被治疗落地
        heal2 = self._apply_heal_mods(target, amount, logs)
        return self._heal_land(target, heal2, logs)

    def _apply_heal_mods(self, target: dict, amount: int, logs: list) -> int:
        """受疗/禁疗修正层（供 _heal_actor 与需溢出计算的主路径共用）：
        受疗天赋按 target 自身 race heal_received；禁疗/重伤按 target 自身 buffs
        heal_down（层×10% cap50%）/_anti_heal_pct（cap80%）。返回修正后治疗量（未 clamp）。"""
        if target is None or amount is None:
            return 0
        heal = max(0, int(amount))
        if heal <= 0:
            return 0
        try:
            _hr = self._race_bonus(target).get("heal_received", 0) or 0
            if _hr:
                heal = max(1, int(heal * (1 + _hr)))
                logs.append(f"🐉 孤傲之血：治疗效果 -{int(-_hr * 100)}%！")
        except Exception as _sw_e:
            _battle_warn('_apply_heal_mods', _sw_e)
            pass
        try:
            tb = target.setdefault("buffs", {})
            _ehd = int(tb.get("heal_down", 0) or 0)
            if _ehd > 0:
                _cut = min(_ehd * 0.10, 0.50)
                heal = max(0, int(heal * (1 - _cut)))
                logs.append(f"🩸 禁疗：治疗量 -{int(_cut * 100)}%！")
            _aheal = float(tb.get("_anti_heal_pct", 0) or 0)
            if _aheal > 0:
                _cut2 = min(_aheal, 0.80)
                heal = max(0, int(heal * (1 - _cut2)))
                logs.append(f"🩸 重伤：治疗量 -{int(_cut2 * 100)}%！")
        except Exception as _sw_e:
            _battle_warn('_apply_heal_mods', _sw_e)
            pass
        return max(0, heal)

    def _heal_land(self, target: dict, heal2: int, logs: list) -> int:
        """落地层：clamp 写 hp，返回实际回血量。heal2 = 已受疗/禁疗修正的治疗量。"""
        if target is None or heal2 is None:
            return 0
        if target.get("hp") is None:
            return 0
        heal2 = max(0, int(heal2))
        if heal2 <= 0:
            return 0
        _mx = target.get("max_hp", target.get("hp", 1)) or 1
        _before = target.get("hp", 0) or 0
        target["hp"] = min(_mx, _before + heal2)
        return int(target["hp"]) - _before

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
            _faith_now = float(self._cast_res().get("faith", 0) or 0)
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
        elif info.get("hp_pct"):
            # v174（鱼鱼拍板）：HP% 治疗改为显式字段 hp_pct（如拳师气息调息 15% HP）。
            # 旧逻辑 power<1 隐式按 HP% 结算已废弃——power 现统一为 LOL 式倍率（伤害/治疗共用），
            # 不再承载"<1 就是 HP%"的语义炸弹（v161 曾致治愈术被误按 87% 生命结算）。
            heal = int(player.get("max_hp", 0) * float(info.get("hp_pct", 0)) * E.skill_power_mult(lv, info) * cond_mult)
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
        # v181-A1：×1.08 读 params.heal_mult（数据声明），替代本地 1.08 兜底（数值一致）
        _cho_eff = self._set_eff(player, "cloth_heal_overflow", 4)
        if _cho_eff:
            _cho_p = (_cho_eff or {}).get("params") or {}
            heal = int(heal * float(_cho_p.get("heal_mult", 1.08) or 1.08))
        # 阶段八：圣光套效果——治疗 +10%（v181-A1 数据化：任意件数持有即生效——遍历装备
        # set 解析到声明 piece_heal_power 的套装 → ×(1+piece_heal_power)。
        # 原 E.has_set(…\"圣光套\") 语义 = 任意 ≥1 件 圣光套 → 数值 0.10 完全一致；
        # 该字段只声明在圣光套，其余套装（布衣/祝福等 bonus_2.heal_power）不受影响 = 现状保持）
        _piece_heal = 0.0
        for _it in (player.get("equipment") or {}).values():
            if not _it or not _it.get("set"):
                continue
            _si = E._set_info(_it["set"])
            if _si and _si.get("piece_heal_power"):
                _piece_heal = max(_piece_heal, float(_si["piece_heal_power"]))
        if _piece_heal > 0:
            heal = int(heal * (1 + _piece_heal))
        # v101.28f 圣光药剂：治疗技能效果 +20%（3 刻）
        if self._cast_buffs().get("heal_up"):
            heal = int(heal * 1.20)
        # v106.2 治疗强度：heal_power 属性 ×(1+heal_power)（cap 50%，职业/词条/套装多来源）
        try:
            _hpv = min(float(self._player_stats(player).get("heal_power", 0) or 0), 0.5)
            if _hpv > 0:
                heal = int(heal * (1 + _hpv))
        except Exception as _sw_e:
            _battle_warn('_skill_heal', _sw_e)
            pass
        # 阶段九：种族受疗天赋（目前仅龙裔孤傲之血 -10%；人类 v106.2 已移除圣光亲和改 exp_bonus）
        # v122：受疗天赋按被治疗者结算（奶队友时队友是龙裔同样 -10%）
        hr = self._race_bonus(target_unit).get("heal_received", 0) or 0
        if hr:
            heal = max(1, int(heal * (1 + hr)))
            logs.append(f"🐉 孤傲之血：治疗效果 -{int(-hr*100)}%！")
        # v130.2 信仰结晶副效果（next_heal_up，P0-3 消费端）：下一次治疗技能效果 +pct%（一次性，随即清 p_eff）
        _nhu = float((self._cast_eff() or {}).get("next_heal_up", 0) or 0)
        if _nhu > 0:
            heal = int(heal * (1 + _nhu))
            del self._cast_eff()["next_heal_up"]
            logs.append(f"✨ 信仰结晶：治疗技能效果 +{int(_nhu * 100)}%！")
        hp_before = target_unit.get("hp", 0)
        # v180E：禁疗/重伤/受疗消费统一收口到 _apply_heal_mods（target 自身 buffs/race）——
        # 与全引擎其他治疗落地同语义。heal 保持"修正后未 clamp"的量，供后续溢出转盾
        # （圣愈不浪费/庇护之光/圣光回响）算真实溢出——落地单独 _heal_land 做，不覆盖 heal。
        heal = self._apply_heal_mods(target_unit, heal, logs)
        # v140 波3.1：特效装备治疗加成（坚毅祝福+15%/圣辉涌动+20%/回响祝福+25%）+ 溢出转盾（圣木/赎罪）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wectx = {"heal": heal, "overflow": 0, "target": target_unit}
            _we_proc(self, player, "heal", _wectx, logs)
            heal = max(1, int(_wectx.get("heal", heal)))
            _we_proc(self, player, "passive", {"heal": heal}, logs)
        except Exception as _sw_e:
            _battle_warn('_skill_heal', _sw_e)
            pass
        self._heal_land(target_unit, heal, logs)
        # v140 S1 直连消费：圣愈不浪费（cloth_heal_overflow）——治疗溢出量 50% 转护盾
        # v181-A1：0.50/2刻 读 params（overflow_pct/shield_turns，数据声明），替代本地兜底
        if _cho_eff:
            _cho_ov = hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0))
            if _cho_ov > 0:
                _cho_sh = int(_cho_ov * float(_cho_p.get("overflow_pct", 0.50) or 0.50))
                _cho_tt = int(_cho_p.get("shield_turns", 2) or 2)
                if target_ally is not None:
                    _sh_t = target_unit.setdefault("p_shields", {})
                    _cur_t = _sh_t.get("cloth_overflow")
                    if _cur_t:
                        _cur_t["value"] = _cur_t.get("value", 0) + _cho_sh
                        _cur_t["turns"] = max(_cur_t.get("turns", 0), _cho_tt)
                    else:
                        _sh_t["cloth_overflow"] = {"value": _cho_sh, "turns": _cho_tt}
                    logs.append(f"☀️ 圣愈不浪费：治疗溢出转化 {_cho_sh} 点护盾！")
                else:
                    self._add_shield("cloth_overflow", _cho_sh, _cho_tt)
                    logs.append(f"☀️ 圣愈不浪费：治疗溢出转化 {_cho_sh} 点护盾！")
        # v140 波3.1：特效装备治疗溢出转盾（回响祝福/赎罪之盾）——clamp 后计算真实溢出
        try:
            _real_overflow = max(0, hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0)))
            if _real_overflow > 0:
                from .core.weapon_effects import proc as _we_proc2
                _we_proc2(self, player, "heal", {"heal": heal, "overflow": _real_overflow}, logs)
        except Exception as _sw_e:
            _battle_warn('_skill_heal', _sw_e)
            pass
        # v110.3 P2-4：庇护之光按“真实治疗溢出量”结算（数据驱动 proc="heal_shield"，替代名字硬匹配）
        # 此前 clamp 后按 hp-(max_hp-hp) 计算，任意治疗补满都误给 ≈20% max_hp 护盾
        # v122：治疗队友时溢出护盾加给被治疗者（队友快照 p_shields；自己场景保持 self._add_shield）
        # v169.7 圣光回响 heal_overflow_shield：与庇护之光同族同语义（proc 不同名，数值 50% 转盾）
        # ——复用同一溢出计算；两 proc 全学则各自独立结算（50%+20% = 70% 溢出转盾，属同族叠加）
        _heal_overflow_procs = [("heal_shield", 0.2), ("heal_overflow_shield", 0.5)]
        for _hpn, _hpdef in _heal_overflow_procs:
            for _pn, _ps in self._passive_map(player)["proc"].get(_hpn, []):
                overflow = hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0))
                if overflow > 0:
                    shield_gain = int(overflow * float(_ps.get("pct", _hpdef)))
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
        # v169.7 圣光回响（heal_overflow_shield）——治疗自身无溢出（血量未满）时无效果，此分支仅日志占位
        # v169.7 信念·流转 faith_share：治疗时承担目标 10% 伤害（分担）——单人战斗无分担目标，
        # 副本（allies 多目标）场景由命令层 instance 广播；本引擎单人场景无副作用（记录占位）
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
            except Exception as _sw_e:
                _battle_warn('_skill_buff', _sw_e)
                pass
            # v169.7 二重唱 melody_duet：吟唱时旋律强度额外 +1（_m_melody_chant 叠完后补一层）
            if mech == "melody_chant":
                try:
                    for _pn_md, _ps_md in self._proc_pm(player)["proc"].get("melody_duet", []):
                        _mel_md = self._melody_state()
                        if _mel_md.get("name") and int(_mel_md.get("stack", 0) or 0) > 0:
                            from .core.battle_mech import MELODY_CFG as _MEL_CFG
                            _mel_md["stack"] = min(int(_MEL_CFG.get("max_stack", 5) or 5),
                                                   int(_mel_md.get("stack", 0) or 0) + 1)
                            logs.append(f"🎶 {_pn_md}：二重唱，旋律强度额外 +1！（{_mel_md['stack']}/5）")
                        break
                except Exception as _sw_e:
                    _battle_warn('_skill_buff', _sw_e)
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
                # v180：怪物施法（_cast_ctx 非玩家 actor）buff 刻数固定读 info.buff_turns（缺省 3）
                # ——怪 buff 无"技能等级养成"，对齐旧 MON_BUFF BUFF_TURNS=3（不叠加折算等级成长）
                if not self._cast_is_player():
                    base_turns = int(info.get("buff_turns", 3) or 3)
                else:
                    base_turns = E.skill_buff_turns(lv)
                # v130.2 歌者回声：增益技持续 + 回声层数 刻（priest_转职.md §3.0）
                if self._is_bard_skill(player, info):
                    base_turns += int(ECHO_CFG.get("buff_extend_per_layer", 1) or 1) * self._echo_layers()
                self._cast_buffs()[key] = max(self._cast_buffs().get(key, 0), base_turns)
        # v1.x：原 burn_burst/rage_burst/bless_shield 三分支（v29 effect 型引爆/转化）
        # 全库无数据 producer（skills.py 无 effect=burn_burst/rage_burst/bless_shield 条目）
        # → 死代码删除；其专属 cond_mult/cond_label 计算一并移除。
        self._apply_mech_gain(mech, mval, p_mech, logs, skill_name)
        # v169.7 守护姿态（战士守线 增益技带 stance 字段）——置位 stance_guard 守护态标记
        # （守护姿态数据无 effect，仅 info.stance='counter'；铁誓·不动 stance_immortal 消费该标记）
        if info.get("stance"):
            self._cast_buffs()["stance_guard"] = max(int(self._cast_buffs().get("stance_guard", 0) or 0), 999)
            logs.append("🛡️ 进入守护姿态！（铁誓·不动守护被动就绪）")
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
    def _skill_hit_settle(self, st: dict, player: dict, info: dict, mech: str,
                           mval: int, p_mech: dict, effs: dict,
                           is_crit: bool, total: int, lv: int,
                           skill_name: str, kind: str, _procs: dict, logs: list) -> None:
        """v176 拆分：攻击命中后结算（原 _player_skill 172 行内联）。

        连招/符文/词条/料理/武器hit → mech效果/mech2/cc/控制延长/shaken →
        技能吸血/破防 → 资源/词条/连段/暴击 → 套装特效。
        副作用全在 self + logs。返回 None。
        """
        combo_tag = info.get("combo", "")
        if combo_tag:
            combo_full = self._combo_push(combo_tag)
            if combo_full:
                combo_bonus = int(total * 0.30)
                # v109.2 P1-2：连招精通——三连击破追加伤害提升至 50%（0.30 → 0.50，武圣连击强化设计落地）
                for _pn, _ps in _procs.get("combo_boost", []):
                    combo_bonus = int(total * 0.50)
                    break
                self._deal_damage(combo_bonus, logs)
                logs.append(f"🥊 三连击破！拳-踢-掌完美连招，追加 {combo_bonus} 点伤害！(下次气力技+20%)")
                self._cast_res()["combo_ready"] = 1
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
        except Exception as _sw_e:
            _battle_warn('_skill_hit_settle', _sw_e)
            pass
        # v140 波3.2：连携增幅墨——技能命中使目标毒/灼烧/流血层数 +1（dot_amp 标记）
        _dam = (self._cast_eff() or {}).get("dot_amp")
        if _dam and int(_dam.get("turns_left", 0) or 0) > 0 and total > 0:
            _per = max(1, int(_dam.get("layer_per_hit", 1) or 1))
            _deb = self._tgt().setdefault("debuffs", {})
            for _dk in ("poison", "burn", "bleed"):
                if _deb.get(_dk, {}).get("n", 0):
                    _d = _deb.setdefault(_dk, {"n": 0, "mult": 1.0})
                    _d["n"] = int(_d.get("n", 0) or 0) + _per
            logs.append(f"🎨 连携增幅墨：异常层数 +{_per}！")

        # ---- 分支机制结算（v29） ----
        self._last_player = player
        self._apply_mech_effect(mech, mval, p_mech, total, logs, skill_name, is_crit, info, caster=player)
        # v169.7 元素亲和 element_affinity：元素引爆（mech=element_burst* 清印记结算）后置位
        # 下次挂印 +1 标记（命中挂印分支消费）；已学被动才置位
        if mech and mech.startswith("element_burst"):
            try:
                for _pn_ea, _ps_ea in self._proc_pm(player)["proc"].get("element_affinity", []):
                    self._elem_affinity_next = True
                    break
            except Exception as _sw_e:
                _battle_warn('_skill_hit_settle', _sw_e)
                pass
        # v169.7 蚀骨 poison_burst_up / 毒刃·共鸣 poison_spread TODO（依赖 battle_mech agent 的
        # _m_poison_burst 乘区与击杀扩散接线——毒爆结算在 battle_mech.py handler 内，battle.py
        # 无法在不改 battle_mech 的前提下插入其内部伤害/扩散；待 battle_mech agent 在 handler
        # 内补读 battle._proc_pm(battle._last_player)["proc"]["poison_burst_up"]/["poison_spread"]）
        # v169.7 链舞 finisher_up TODO（数据缺陷，见 技能引擎缺口全量清单 §四.4）：finisher_up proc
        # 挂在 kind=物理 主动技「链舞」上而非被动技能 → E.passive_skills_learned 按 kind=被动 过滤，
        # _passive_map 聚合不到该 proc，终结技 mech=finisher 的 per_stack（10%→16%）无法按被动接线；
        # 待 skills agent 修数据（链舞改 kind=被动 或移除 passive 字段并另立被动条目）。
        # 若数据修正后仍需引擎支持：在 _apply_mech_effect mech=="finisher" 分支读
        # _proc_pm(battle._last_player)["proc"]["finisher_up"] 提升 per（battle.py 侧可接）。
        # v153：mech2 第二机制（如冰锥 mech=ice_mark + mech2=spd_down 减速）——独立结算
        _mech2 = info.get("mech2")
        if _mech2:
            _m2val = int(info.get("mech2_val", 0) or 0) or 1
            self._apply_mech_effect(_mech2, _m2val, p_mech, total, logs, skill_name, is_crit, info, caster=player)
        # v63 额外控制效果（cc 字段，独立于 mech 叠层）：眩晕/沉默/净化
        # v125.2 B1：cc 白名单查表 SKILL_CC_WHITELIST
        cc = info.get("cc")
        if cc and cc in SKILL_CC_WHITELIST:
            self._apply_mech_effect(cc, 1, p_mech, total, logs, skill_name, is_crit, info, caster=player)
        # v169.7 镇魂安魂 dirge_ctrl_up（诗人挽歌线）：挽歌系控制时长 +1.5 刻——
        # 本技能对敌施加的控制（mech/cc 走 MECH_EFFECTS 写入 e_buffs 后）延长 1 刻（1.5 向下取整；
        # 小数半刻引擎不支持，见 技能引擎缺口全量清单 §四.5）
        try:
            _ctrl_keys_dg = ("stun", "freeze", "silence", "sleep", "spd_down")
            _apply_any_ctrl = False
            if mech in _ctrl_keys_dg or cc in _ctrl_keys_dg or _mech2 in _ctrl_keys_dg:
                _apply_any_ctrl = True
            if _apply_any_ctrl:
                for _pn_dg, _ps_dg in self._proc_pm(player)["proc"].get("dirge_ctrl_up", []):
                    _eb_dg = self._tgt_buffs()
                    for _ck_dg in _ctrl_keys_dg:
                        if _eb_dg.get(_ck_dg):
                            _eb_dg[_ck_dg] = int(_eb_dg[_ck_dg]) + int(_ps_dg.get("add", 1) or 1)
                            logs.append(f"🎵 {_pn_dg}：挽歌延长【{_ck_dg}】控制 +1 刻！")
                            break
                    break
        except Exception as _sw_e:
            _battle_warn('_skill_hit_settle', _sw_e)
            pass
        # ---- v139 enemy_bar 挂敌身条：技能命中注入 shaken（拳师破绽/淬势撼岳）----
        # 数据源：技能 info.shaken_gain（三连击破+15/碎颅势+15/旋风踢+5每目标/无影连打每段+3）
        # 触发：阈值满 → 敌方跳过刻（skip_turn）；触发后免疫窗口 + 阈值递增（防无限控）
        _shaken_gain = info.get("shaken_gain")
        if _shaken_gain:
            try:
                from .core.battle_bars import bar_gain, bar_should_trigger, bar_trigger
                _tgt = getattr(self, "_active_target", None) or self._tgt()
                _sg = int(_shaken_gain)
                bar_gain(_tgt, "shaken", _sg, logs)
                if bar_should_trigger(_tgt, "shaken"):
                    if bar_trigger(_tgt, "shaken", logs):
                        _tgt_buffs = _tgt.get("buffs", {})
                        _bs = _tgt_buffs.get("shaken", {})
                        # v169.7 破绽·极 broken_extend（拳师攻线）：破防持续 +1.5 刻（免疫窗口 +1，半刻不支持向下取整）
                        try:
                            for _pn_be, _ps_be in self._proc_pm(player)["proc"].get("broken_extend", []):
                                _bs["immune_turns"] = int(_bs.get("immune_turns", 0) or 0) + int(_ps_be.get("extend", 1) or 1)
                                break
                        except Exception as _sw_e:
                            _battle_warn('_skill_hit_settle', _sw_e)
                            pass
                        logs.append(f"💢 破绽值满！敌人被震慑，下刻无法行动！(阈值提升至 {_bs.get('threshold', '?')})")
            except Exception as _sw_e:
                _battle_warn('_skill_hit_settle', _sw_e)
                pass

        # ---- 技能特效（v9 落地）----
        # v2.0：技能名硬编码特效已废弃（12 章技能全数据驱动，mech/effect/cond 在 _apply_mech_effect 覆盖）
        # v104 R3 P2-10 修复：吸血改按 lifesteal 数据字段触发（原只认 effect=="lifesteal"，
        # 全表无技能带此 effect → 嗜血斩 lifesteal:0.25 实机 0 吸血）；数值由 skill_lifesteal_pct 读字段
        if info.get("lifesteal"):
            heal = int(total * E.skill_lifesteal_pct(info, lv))
            if self._cast_buffs().get("mortal_wound"):  # v1.3 重伤：技能吸血减半
                heal = int(heal * 0.5)
            self._heal_actor(player, heal, logs)  # v180E 统一落地
            logs.append(f"💉 『{skill_name}』汲取了 {heal} 点生命！")
        # v2.0 破防（pierce 数据字段）：直接给敌方降防
        if info.get("pierce") and self._tgt().get("hp", 0) > 0:
            self._tgt_buffs()["def_down"] = E.skill_buff_turns(lv)
        # v180 pdot 管线化：技能带 pdot（持续伤害：毒/灼烧/流血/腐蚀）→ 命中挂目标
        # （v178 E4 怪技能 pdot 原在 _enemy_cast_done 简化段处理；收编管线后在命中结算统一挂——
        #  玩家/怪技能同入口 _apply_dot(target=被打目标, source=施法者)。cc_immune 免疫不挂）
        try:
            _pdot_p = info.get("pdot") or (info.get("effect") or {}).get("pdot")
            if _pdot_p and isinstance(_pdot_p, dict) and not self._tgt_buffs().get("cc_immune"):
                self._apply_dot(self._tgt(), self._cast_ctx or player, _pdot_p, logs)
        except Exception as _sw_e:
            _battle_warn('_skill_hit_settle', _sw_e)
            pass
        # v2.0 核心资源：攻击命中获取（战士怒气/刺客连击点/拳师气，res_gain 覆盖默认）
        # v174.1 普攻技能化语义：basic 技（basic_skill，普攻）命中走"攻击"事件（on_attack），
        # 非 basic 技能走 on_skill——保证"释放技能才触发"的被动/词条不会因普攻被误触。
        _is_basic = bool(info.get("basic") or info.get("is_basic"))
        self._resource_on_skill(player, info, logs)
        # v130.2c 资源词条：攻击命中（basic）走 on_attack；技能命中走 on_skill/on_cast/combo_skill
        if _is_basic:
            self._affix_res_proc(player, "on_attack", logs)
        else:
            self._affix_res_proc(player, "on_skill", logs)
            if self._is_element_skill(info):  # v176: 元素技能命中触发 on_cast 资源词条（原 5092 额外判 cls_fa_shi）
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
        # v174.1 武器效果 hit 事件：技能 info 配 trigger_hit（如 basic_skill 普攻技）→
        # 命中时额外发 "hit" 事件（风痕/猎影等注册在 hit 的武器特效本为普攻命中触发，
        # 普攻技能化后靠此字段兼容；普通技能不触发，不会误触普攻专属武器效果）。
        if total > 0 and info.get("trigger_hit"):
            try:
                from .core.weapon_effects import proc as _we_proc
                _we_proc(self, player, "hit", {"dmg": total, "is_crit": is_crit}, logs)
            except Exception as _sw_e:
                _battle_warn('_skill_hit_settle', _sw_e)
                pass


    def _skill_apply_tags_marks(self, st: dict, player: dict, info: dict, mech: str,
                                is_crit: bool, total: int, element: str,
                                frozen_bonus: float, stealth_mult: float, stack_bonus: float,
                                cond_mult: float, cond_label: str, magic_bonus: float, mb_lvl: int,
                                _execute_tag: str, affix_tags: list, elem_mult: float,
                                reaction_log: str,
                                _procs: dict, logs: list, _v169_tags: list) -> None:
        """v176 拆分：攻击技能标签组装 + 元素印记命中（原 _player_skill 74 行内联）。

        把暴击/碎冰/潜行/增幅/条件/破魔/斩杀/词条/元素 标签拼到伤害日志；
        带 element 技能命中给目标挂印记 + 法师切系 + 元素被动消费。
        副作用：改 logs[-1]、e_buffs 印记、_last_element_set。返回 None。
        """
        tags = []
        if is_crit:
            tags.append("💥暴击")
        if mech in MECH_FULL_HP_CRIT and self._tgt().get("hp", 0) >= self._tgt().get("max_hp", 1):
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
        # v169.7 effect 乘区键标签（猎杀时刻/星轨锁定/奥术矩阵/奥术力场）
        if locals().get("_v169_tags"):
            tags.extend(_v169_tags)
        if elem_mult > 1.0:
            tags.append(f"✨元素x{round(elem_mult, 2)}")
        if tags:
            logs[-1] += " " + "·".join(tags)
        # v169.7 修 #123：疾风之心凝神触发提示（_passive_crit_bonus 置位，技能结算后消费一行）
        if (self._cast_eff() or {}).pop("focus_surplus_proc", None):
            logs.append("🎯 凝神屏息！结余 ≥40，本次技能暴击 +20%")
        if reaction_log:
            logs.append(reaction_log)
        # v2.0 元素印记：施放带 element 的技能后给目标挂印记 + 法师切换当前系
        if element and E.ELEMENT_MARKS.get(element):
            extra_layers = 1
            # v104 R3 P1-1：追踪印记——30% 概率额外叠 1 印记（游侠基础被动）
            for _pn, _ps in _procs.get("mark_extra", []):
                if random.random() < float(_ps.get("chance", 0.3)):
                    extra_layers += 1
            # v169.7 元素亲和 element_affinity：引爆后下次挂印 +1 层（_elem_affinity_next 由引爆结算置位）
            if getattr(self, "_elem_affinity_next", False):
                self._elem_affinity_next = False
                extra_layers += 1
                logs.append("✨ 元素亲和：引爆余韵，挂印 +1 层！")
            # v169.7 元素同调 element_sync：连续两次同系施法第二次挂印 +1 层（_player_skill 前置判定置位）
            if getattr(self, "_elem_sync_bonus", False):
                self._elem_sync_bonus = False
                extra_layers += 1
                logs.append("✨ 元素同调：同系连发，挂印 +1 层！")
            E.element_mark_apply(self._tgt_buffs(), element, extra_layers)
            # v130.2 目标侧 element_marks 登记（每系上限 3；仅命中叠加——mage_转职.md §1.0①）
            if total > 0:
                new_marks = self._elem_mark_apply(element, layers=extra_layers, player=player)
                if self._is_element_mage(player):
                    logs.append(f"✦ 元素印记：目标{ {'fire': '火', 'ice': '冰', 'thunder': '雷'} [element]}印 {new_marks}/{self._elem_mark_max(player)}")
                # v130.2 last_element 同系连发：记录上次元素，同系第二次施放额外 +1 充能（元素凝聚）
                # v176: 解耦——玩家激活元素体系（resources 含 element 键）即记录，不再判职业名
                if "element" in (self._cast_res() or {}):
                    self._last_element_set(player, element)
            # v104 R3 P1-1：寒霜亲和——冰系技能命中附带减速 2 刻
            if element == "ice":
                for _pn, _ps in _procs.get("ice_slow", []):
                    self._tgt_buffs()["spd_down"] = max(self._tgt_buffs().get("spd_down", 0), 2)
                    logs.append("❄️ 寒霜亲和：敌人被减速！")
            if self._cast_res().get("element") is not None:
                self._cast_res()["element"] = element


    def _skill_finalize_damage(self, st: dict, player: dict, info: dict, kind: str,
                               element: str, skill_name: str, multi: int,
                               is_crit: bool, total: int, _magi_part: int,
                               logs: list) -> tuple:
        """v176 拆分：攻击总伤后处理（原 _player_skill 113 行内联）。

        boss filter → 武器被动增伤 → v153 乘区 → v169 乘区 → 感电 → 敌方抗性 → 闪避/AOE →
        伤害落地(_deal_damage) → 吸血/吸魔。返回 (total, magi_part, info)。
        副作用：改 self._cast_buffs()/e_buffs、打伤害、回血回蓝（经 self + logs 传出）。
        """
        # v180F 收编配套：伤害类型透传承伤链（玩家受击 phys/magi 免伤消费）
        _dmg_kind = seg_of(kind) or ""
        total = self._boss_dmg_filter(total, player, logs, dmg_type=seg_of(kind))
        # v140 波3.1：特效装备技能被动增伤（奥术苍穹/岁月流转/永恒契约/铭文/秘典/雷纹/三相/破岳/咒誓/暮裂）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wectx = {"mult": 1.0, "tags": [], "is_crit": is_crit, "kind": kind, "skill": skill_name}
            _we_proc(self, player, "passive", _wectx, logs)
            # v140 波3.2：弱点击破石——目标负面越多增伤越高（vuln 标记）
            _vuln = (self._cast_eff() or {}).get("vuln")
            if _vuln and int(_vuln.get("turns_left", 0) or 0) > 0:
                _vb = float(_vuln.get("bonus", 0) or 0)
                if _vb > 0:
                    _wectx["mult"] = _wectx.get("mult", 1.0) * (1 + _vb)
            if _wectx.get("mult", 1.0) != 1.0:
                total = int(total * _wectx["mult"])
        except Exception as _sw_e:
            _battle_warn('_skill_finalize_damage', _sw_e)
            pass
        # v153 §2/§6：元素印记结算倍率 / 磐核爆发倍率消费（battle_mech handler 写入 p_buffs）
        _v153_mult = 1.0
        if self._cast_buffs().get("element_burst_mult"):
            _v153_mult *= float(self._cast_buffs().pop("element_burst_mult"))
            logs.append(f"🔥 元素结算增伤 ×{_v153_mult:.2f}")
        if self._cast_buffs().get("guard_core_burst_mult"):
            _v153_mult *= float(self._cast_buffs().pop("guard_core_burst_mult"))
        if self._cast_buffs().get("finisher_mult"):
            _v153_mult *= float(self._cast_buffs().pop("finisher_mult"))
        if self._cast_buffs().get("bone_rush_mult"):
            _v153_mult *= float(self._cast_buffs().pop("bone_rush_mult"))
        if self._cast_buffs().get("element_overload_aoe"):
            # 超载反应：本次技能转全体 AOE
            info = dict(info)
            info["aoe"] = "all"
            self._cast_buffs().pop("element_overload_aoe", None)
        if _v153_mult != 1.0:
            total = int(total * _v153_mult)
        # v169.7 battle_mech effect 乘区键（猎杀时刻/星轨锁定/奥术矩阵/奥术力场）——技能伤害统一挂点
        try:
            _v169m, _v169t = self._consume_v169_buff_dmg(kind=kind, element=element or "", skill_name=skill_name)
            if _v169m != 1.0:
                total = int(total * _v169m)
                _v169_tags = _v169t
            else:
                _v169_tags = []
        except Exception:
            _v169_tags = []
        # v153 §2：感电连击（雷印满 3 层结算时连击 +1/+2）——多段追加
        _ele_combo = int(self._cast_buffs().get("element_thunder_combo", 0) or 0)
        if _ele_combo:
            self._cast_buffs().pop("element_thunder_combo", None)
            _combo_dmg = int(total / max(1, int(info.get("hits", 1) or 1)))
            for _ci in range(_ele_combo):
                total += _combo_dmg
                logs.append(f"⚡ 感电连击！追加 {_combo_dmg} 点伤害！")
        # v110 P1-3：玩家攻击端消费敌方防守属性（物免/格挡/魔免/元素抗；PVP 对称，PVE 怪无键=0 无感）
        total, _magi_part = self._enemy_mitigate(total, _magi_part, element, logs, kind=kind)
        # v180 等级压制 actor 化：怪打玩家（管线 _tgt_is_player）时，伤害段 ×怪高玩家级差压制
        # （原在 _enemy_cast_done 手动乘 _lpm；管线收编后统一在落地前消费。玩家打怪仍走
        # _deal_damage 内 v136 双向曲线，不受影响；PVP btype 由 _enemy_lv_pressure 内部返回 1.0）
        if self._tgt_is_player() and self._cast_ctx is not None:
            try:
                _lpm_pipe = self._enemy_lv_pressure(self._tgt(), self._cast_ctx)
                if _lpm_pipe != 1.0:
                    total = max(1, int(total * _lpm_pipe))
            except Exception as _sw_e:
                _battle_warn('_skill_finalize_damage', _sw_e)
                pass
        # v174.1 星火（novice_spark_followup 星火法杖）：basic 普攻技命中消费星火标记（+X% 后清）。
        # 原语义"释放技能后下次普攻+10%"——basic_skill 即普攻，仅 basic 技触发，普通技能不消费。
        # v180E 阶段4：数值从武器特效参数表读（novice_spark_followup.atk_pct）
        if info.get("basic") and self._cast_stacks().get("novice_spark"):
            try:
                from .core.weapon_effects import effect_data as _we_ed
                _spark_pct = float(_we_ed(self, player, "novice_spark_followup").get("atk_pct", 0.10) or 0.10)
            except Exception:
                _spark_pct = 0.10
            total = int(total * (1 + _spark_pct))
            del self._cast_stacks()["novice_spark"]
            logs.append(f"✨ 星火x{1 + _spark_pct:.1f}：普攻伤害 +{int(_spark_pct * 100)}%！")
        # v105 怪物闪避：技能主伤害判定一次（闪避成功 total 归零，日志自然显示 0 伤害）
        # v177 双向：玩家施法=怪闪避（_target_dodge_check）；怪施法玩家技能=目标玩家闪避由 _deal_hit 内 _damage_actor 处理
        if not self._tgt_is_player() and self._target_dodge_check(logs):
            total = 0
        else:
            aoe = info.get("aoe")
            if aoe:
                # v180F 清3 设计修正：AOE = 选目标（front/all）+ 逐目标结算，方向由
                # 施法目标决定（不再写死 not _tgt_is_player——怪施法 AOE 打玩家侧也走这里）
                scope = "all" if aoe is True else str(aoe)
                self._aoe_reach = int(info.get("reach") or 3)
                self._aoe_falloff = float(info.get("aoe_falloff", 1.0) or 1.0)
                if self._tgt_is_player():
                    # 怪 AOE 打玩家侧：对玩家 side 全体存活 actor（player + allies）逐目标
                    # 走 _deal_hit（复用玩家承伤链；野外单玩家 = 单目标无差）
                    _pl_pool = self._player_side_aoe_pool()
                    if len(_pl_pool) <= 1:
                        _boss_dmg = self._deal_hit(total, logs, source=skill_name, dmg_kind=_dmg_kind)
                    else:
                        _acc = 0
                        _saved_tgt = self._target_ctx
                        for _t in _pl_pool:
                            if not _t or _t.get("hp", 0) <= 0:
                                continue
                            self._target_ctx = _t
                            try:
                                _acc += int(self._deal_hit(total, logs, source=skill_name, dmg_kind=_dmg_kind) or 0)
                            except Exception:
                                continue
                        self._target_ctx = _saved_tgt
                        _boss_dmg = _acc
                else:
                    _boss_dmg = self._aoe_damage(total, logs, scope, source=skill_name)
            else:
                # v136 等级压制：_deal_damage 内部按等级差压制实际伤害，返回值=真实扣血，
                # 回写 total 让后续日志/吸血/结算都反映压制后的值（原 total 未回写→日志虚高）
                # v177 双向：_deal_hit 按目标 actor 分发（怪施法打玩家）
                _real = self._deal_hit(total, logs, source=skill_name, dmg_kind=_dmg_kind)
                _boss_dmg = _real
                if _real != total:
                    total = _real
            # v173.3 意见#112：总伤害汇总日志提前到吸血结算前——原顺序吸血日志
            # 先输出、'你施展造成N伤害'后输出（玩家看到吸血在伤害前，观感颠倒）。
            # v174.1：技能 info 配 cast_verb（如 basic_skill "挥剑斩击"）→ 日志用动作语
            # "你挥剑斩击，造成 N 点伤害"；无 cast_verb 保持"你施展【技能】，造成 N 点伤害"。
            _verb = info.get("cast_verb")
            # v180G B7：日志主语 = 攻击者视角。攻击者(player 参数)是当前行为驱动者
            # (self.player) → "你"；攻击者是他人（副本跨玩家命中：B 的 Battle 触发 A 的
            # 挂起命中）→ 显示攻击者名；怪施法（_cast_ctx 非空）→ 显示怪名。
            _caster = self._cast_ctx
            if _caster is not None:
                _subject = str((_caster or {}).get("name", "敌人"))
            elif player is self.player or self.player is None or player is None:
                _subject = "你"
            else:
                _subject = str(player.get("name") or "队友")
            _disp_name = str(info.get("name") or skill_name)
            _subj_verb = (f"{_subject}{_verb}" if _verb else f"{_subject}施展【{_disp_name}】")
            if multi > 1:
                logs.append(_subj_verb
                            + f"，连击 {multi} 次，共造成 {total} 点伤害！")
            else:
                # v127.3 多怪时日志带目标名（a1 指定/自动选择都显示打了谁；单怪保持原文案）
                _alive_n2 = sum(1 for u in self.enemies if u.get("hp", 0) > 0)
                _tg_d2 = getattr(self, "_active_target", None) or self._tgt()
                _tgtxt2 = f"对【{_tg_d2.get('name', '敌人')}】" if _alive_n2 > 1 and _tg_d2 else ""
                logs.append(_subj_verb
                            + f"，{_tgtxt2}造成 {total} 点伤害！")
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
                self._settle_lifesteal(player, _boss_dmg, logs, magic=(kind == K_MAGI),
                                       dmg_type=seg_of(kind))
        # v107 吸MP（虚空行者）：魔法伤害的 mp_steal% 回复自身魔力（打空敌人蓝条的反向续航）
        if info.get("mp_steal") and total > 0:
            gain = int(total * float(info["mp_steal"]))
            if gain > 0:
                player["mp"] = min(player.get("max_mp", C.DEFAULT_MAX_MP),
                                   player.get("mp", 0) + gain)
                logs.append(f"🌑 虚空汲取：回复 {gain} 点魔力！")

        return total, _magi_part, info, _v169_tags

    def _skill_assemble_mults(self, st: dict, est: dict, player: dict, info: dict,
                              mech: str, kind: str, lv: int, skill_name: str,
                              p_mech: dict, logs: list, effs: dict,
                              is_crit: bool, _stealth_hit: bool,
                              lucky: bool, stealth_mult: float) -> dict:
        """v176 拆分：攻击技能乘区装配（原 _player_skill 123 行内联）。

        计算 frozen/stack/cond/passive/reaction/蓄势/终结/词条/套装 各乘区 → pmult（cap 后）。
        返回 ctx dict（段循环/标签/命中效果需要的全部中间量）。
        """
        # 机制：冰霜（冻结目标碎冰增伤）——查表 MECH_FROZEN_MULT（v125.2 B1）
        frozen_bonus = 1.0
        if mech in MECH_FROZEN_MULT and "freeze" in self._tgt_buffs():
            frozen_bonus = MECH_FROZEN_MULT[mech]
        # 机制：圣光/毒/影/气/审判/狂暴 层数加成
        stack_bonus = self._mech_stack_bonus(mech, p_mech, info)
        # v30 条件转化：按战场状态变形态（残血斩杀/背水一战）
        cond_mult = self._cond_mult(info, player, lv)
        # v104 R3 P2-18：条件满足即显示标签（含 mult=1.0 的纯条件技）
        cond_label = info.get("cond", {}).get("label", "") if self._cond_active(info, player) else ""
        # 段数：技能数据统一用 hits 键（v175e 修复——原只读 multi 导致 22 个多段技能
        # 全当单段打，疾风/血怒/奥术弹幕等多段流伤害只有设计的 1/N；multi 为旧别名兼容）
        multi = int(info.get("multi") or info.get("hits") or 1)
        # 机制：风印 → 连击次数增加（查表 MECH_COMBO_STACKS，v125.2 B1）
        if mech in MECH_COMBO_STACKS:
            multi += p_mech.get(mech, 0)
        # v34 破魔：魔法伤害 +x%
        mb_lvl = self._enchant_lvl(effs, "magic_break")
        magic_bonus = (1 + C.rune_value("magic_break", mb_lvl)) if mb_lvl and kind == K_MAGI else 1.0
        # v109.2 P2-9：半死字段数据驱动化（原按技能名硬编码，改名即失效）——
        # 破甲本能(proc pierce)/烈焰亲和(proc fire_bonus)/双修精通(stat cond=dual_stat)
        # v176: 被动伤害乘区抽 _skill_passive_dmg_bonus（原 94 行内联）
        passive_bonus, _execute_tag, element, _procs = self._skill_passive_dmg_bonus(
            st, est, player, info, mech, kind)
        # 元素反应增伤（元素共鸣：触发反应时 +15%）
        for _pn, _ps in _procs.get("reaction", []):
            self._elem_reaction_boost = float(_ps.get("mult", 1.15))
        # 元素反应：当前系 × 目标印记（技能带 element 字段时判定；"current"=当前元素亲和系）
        reaction_mult = 1.0
        reaction_log = ""
        if element and E.ELEMENT_MARKS.get(element):
            marks = {k: v for k, v in self._tgt_buffs().items() if k in E.ELEMENT_MARKS.values()}
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
                    self._aoe_damage(aoe_dmg, logs)
                    reaction_log = f"💥超载爆发！额外 {aoe_dmg} 点全体伤害！"
                # 冻结：目标冻结 1 刻
                elif r["extra"] == "freeze":
                    self._tgt_buffs()["freeze"] = 1
                    reaction_log = "❄️冻结！目标被冰封 1 刻！"
                # 感电：连击 +1（追加一次伤害）
                elif r["extra"] == "chain":
                    multi += 1
                    reaction_log = "⚡感电连锁！追加一次攻击！"
                # 清除印记（感电保留）
                if r["clear"]:
                    for mk in E.ELEMENT_MARKS.values():
                        self._tgt_buffs().pop(mk, None)
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
        if kind == K_PHYS and _mom_mult != 1.0:
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
        if self._cast_res().get("combo_ready"):
            _is_chi_skill = ("chi" in (info.get("res_cost") or {})) or \
                ((info.get("consume_all") or {}).get("key") == "chi")
            if _is_chi_skill:
                passive_bonus *= 1.20
                self._cast_res()["combo_ready"] = 0
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
        # v180 删默认成长后：怪自身技能无 SKILL_UP 配置 → skill_power_mult 恒 1.0，天然不吃成长
        # （原 _mon_own_skill 特判已删——没配 p 就是没成长，不再需要按施法者身份区分）
        pmult = (E.skill_power_mult(lv, info) * frozen_bonus * stealth_mult * stack_bonus * cond_mult
                 * magic_bonus * passive_bonus * reaction_mult * affix_mult * elem_mult
                 * self._v139_dmg_mult(player, info))
        # vF3 P1 连乘封顶：技能伤害倍率连乘（技能×冻结×潜行×叠层×条件×魔法×被动×反应×词缀×元素×种族×v139形态/专注）
        # 只 clamp 技能伤害倍率段；暴击(×1.5)/暴伤(crit_dmg)/幸运一击(×1.5) 为独立乘区，在下方另行施加不受此限。
        if pmult > C.SKILL_PMULT_CAP:
            pmult = C.SKILL_PMULT_CAP
        return {
            "multi": multi, "pmult": pmult,
            "reaction_log": reaction_log, "element": element,
            "_procs": _procs, "_execute_tag": _execute_tag,
            "frozen_bonus": frozen_bonus, "stack_bonus": stack_bonus,
            "cond_mult": cond_mult, "cond_label": cond_label,
            "magic_bonus": magic_bonus, "mb_lvl": mb_lvl,
            "stealth_mult": stealth_mult, "elem_mult": elem_mult,
            "affix_tags": affix_tags,
            "total": total, "magi_part": _magi_part,
        }

    def _skill_passive_dmg_bonus(self, st: dict, est: dict, player: dict, info: dict,
                                  mech: str, kind: str) -> tuple:
        """v176 拆分：攻击技能被动伤害乘区装配（原 _player_skill 94 行内联）。

        累乘来源：破甲/烈焰亲和/双修/元素伤害/毒/标记/奥术/元素起源/武技/速度/审判/复仇/斩杀/血魔法。
        返回 (passive_bonus, execute_tag, element, _procs)。副作用：复仇 buff 消费、_elem_reaction_boost 预置。
        """
        _pm = self._passive_map(player)
        _procs = _pm["proc"]
        passive_bonus = 1.0
        # 技能元素（"current"=当前元素亲和系）——提前解析供 proc 型被动判定
        element = info.get("element", "")
        if element == "current":
            element = self._p_res().get("element", "fire")
        # 破甲本能：破防技能伤害 +10%（proc pierce，原硬编码技能名）
        for _pn, _ps in _procs.get("pierce", []):
            if info.get("pierce"):
                passive_bonus *= float(_ps.get("mult", 1.1))
        # 烈焰亲和：火系魔法伤害 +10%（proc fire_bonus，原 stat=fire+技能名硬编码；mult 为增量语义）
        for _pn, _ps in _procs.get("fire_bonus", []):
            if element == "fire" and kind == K_MAGI:
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
        # v169.7 奥术共鸣 arcane_resonance：奥术技能伤害 +15%（与奥术之心同 mech 口径叠加）
        # v181.C: mult 读 skills.py 奥术共鸣 passive（缺字段=无此行为）
        # v181.P2D-D3a：消费迁注册表族 dmg_mult_cond（ctx mult_kind='arcane_mech' 段；循环骨架/
        # 顺序/break 语义逐字保留——原 for 无 break 逐条累乘，多条目连乘语义由逐条 run 保留）
        for _pn, _ps in _procs.get("arcane_resonance", []):
            _ctx_ar = {"player": player, "ps": _ps, "ps_name": _pn,
                       "mult_kind": "arcane_mech", "mech": mech, "mult": passive_bonus}
            _run_proc_family(self, "arcane_resonance", _ctx_ar)
            passive_bonus = _ctx_ar.get("mult", passive_bonus)  # handler 数值槽改写读回（mult float 不可变）
        # v169.7 元素起源 element_origin：三系印记同时 ≥2 层时 结算伤害 +20%（加算乘区）
        # v181.C: layers/mult 读 skills.py 元素起源 passive（缺字段=无此行为）
        # v181.P2D-D3a：消费迁注册表族 dmg_mult_cond（ctx mult_kind='element_marks' 段；循环骨架/
        # 顺序/break 语义逐字保留——原无条件 break 在循环尾，max=1 下等价，多条目防御只判首条）
        _elem_skill = bool(element and E.ELEMENT_MARKS.get(element))
        for _pn, _ps in _procs.get("element_origin", []):
            _ctx_eo = {"player": player, "ps": _ps, "ps_name": _pn,
                       "mult_kind": "element_marks", "mult": passive_bonus}
            _run_proc_family(self, "element_origin", _ctx_eo)
            passive_bonus = _ctx_eo.get("mult", passive_bonus)
            break
        # v169.7 元素同调 element_sync：连续两次同系施法，第二次挂印 +1 层（置 _elem_sync_bonus
        # 标记，命中挂印分支消费；读 _last_element 判定连续同系）
        # v181.P2D-D3a：消费迁注册表族 flag_set_cond（ctx flag_kind='elem_sync' 段；循环骨架/
        # 顺序/break 语义逐字保留——原无条件 break 在循环尾，max=1 下等价）
        for _pn, _ps in _procs.get("element_sync", []):
            _ctx_es = {"player": player, "ps": _ps, "ps_name": _pn,
                       "flag_kind": "elem_sync", "is_elem_skill": _elem_skill,
                       "element": element}
            _run_proc_family(self, "element_sync", _ctx_es)
            break
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
            elif _sstat == "stealth_crit_dmg" and (self._p_buffs_bag().get("stealth") or self._p_stealth_atk()):
                passive_bonus *= (1 + float(_ps.get("mult", 0)))
        # v104 R3 P1-1：复仇被动消费——受击后下次攻击 +30%（挨打反打，一次后清除）
        if self._p_buffs_bag().get("revenge_atk"):
            for _pn, _ps in _procs.get("counter", []):
                passive_bonus *= float(_ps.get("mult", 1.3))
            del self._p_buffs_bag()["revenge_atk"]
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
        return passive_bonus, _execute_tag, element, _procs

    def _skill_crit_roll(self, st: dict, est: dict, player: dict, info: dict,
                          mech: str, skill_name: str, logs: list) -> tuple:
        """v176 拆分：攻击技能暴击判定（原 _player_skill 42 行内联）。

        暴击来源：面板 crit + 幸运转化 + 套装 + 条件被动 + 满弦 + 标记 + 潜行必暴 + 满血必暴。
        返回 (is_crit, _stealth_hit, lucky, stealth_mult, est, effs)。
        副作用：潜行 buff 消费、_stealth_atk 标记、破甲符文改写 est 副本。
        """
        # v109.2 P1-1 运势：幸运转化为暴击补充（luck → crit，转化 0.3/cap 0.12 → LUCK_CRIT_CONV）；
        # v130.2c 套装暴击：巡林长披风（带标记 +5%）/ 夜幕合契·影纱 4 件（终结技 +15%）
        # v169.7 条件被动暴击族（狂热/真知/疾风之心/元素之核/影舞·极）：统一走 _passive_crit_bonus 消费
        is_crit = random.random() < (st["crit"] + min(float(st.get("luck", 0) or 0) * LUCK_CRIT_CONV["per_luck"],
                                                      LUCK_CRIT_CONV["cap"])
                                     + self._set_crit_bonus(player, info)
                                     + self._passive_crit_bonus(player, info=info)) * self._tenacity_mult(est)
        # v130.2 游侠满弦状态（守线·风行者）：精力 ≥80 且低耗/连射技能 暴击率 +10%
        if self._energy_high_crit(player, info):
            is_crit = is_crit or random.random() < float(ENERGY_HIGH.get("crit_bonus", 0.10) or 0.10)
        # v104 R3 P1-1：猎手本能——对标记目标暴击 +10%（e_buffs["mark"] 为目标易伤标记）
        if "mark" in self._tgt_buffs():
            for _pn, _ps in self._passive_map(player)["stat"]:
                if _ps.get("stat") == "crit_mark" and random.random() < float(_ps.get("mult", 0.1)):
                    is_crit = True
        # v104 R3 P1-10：潜行状态（stealth）——下次攻击必暴，攻击后消耗
        # v130.2f2：顺带记录本次攻击出手时处于潜行（供暮影潜行乘区 破影一击×1.5/幽影刃×1.25 消费，
        #   判定与下方必暴共享同一字段 p_buffs["stealth"]：攻击时消费即视为潜行出手）
        _stealth_hit = False
        self._p_set_stealth_atk(False)# v130.2f2（T11 P2）：潜行出手标记每次出手前复位
        if self._cast_buffs().get("stealth"):
            is_crit = True
            _stealth_hit = True
            self._p_set_stealth_atk(True)# 潜行出手标记——供 _on_crit_resource（潜行出手额外+1 影步）与暗影之舞暴伤被动读取
            del self._cast_buffs()["stealth"]
            logs.append("🌙 潜行生效！本次攻击必定暴击！")
        # v34 符文：装备效果（破甲/暴伤/破魔/攻击特效）
        effs = self._enchant_effects(player)
        ap_lvl = self._enchant_lvl(effs, "armor_pierce")
        if ap_lvl:
            est = dict(est)
            est["def"] = int(est["def"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
            est["mdef"] = int(est["mdef"] * (1 - C.rune_value("armor_pierce", ap_lvl)))
        # 机制：影袭（满血必暴）——查表 MECH_FULL_HP_CRIT（v125.2 B1）
        if mech in MECH_FULL_HP_CRIT and self._tgt().get("hp", 0) >= self._tgt().get("max_hp", 1):
            is_crit = True
        # v130.2f2 暮影潜行乘区：潜行出手时 终结·破影一击 ×1.5 / 幽影刃 ×1.25（数据驱动
        #   SHADOW_STEALTH_DMG_MULT，assassin.md §5.2；非潜行/非表内技能恒 1.0，不影响其他职业）
        stealth_mult = 1.0
        if _stealth_hit and skill_name in SHADOW_STEALTH_DMG_MULT:
            stealth_mult = float(SHADOW_STEALTH_DMG_MULT[skill_name])
        # v109.2 P1-1 运势：暴击命中后 30% 概率追加 50% 伤害（幸运一击，含必暴机制）
        lucky = is_crit and random.random() < LUCKY_CRIT_CHANCE
        return is_crit, _stealth_hit, lucky, stealth_mult, est, effs

    def _skill_seg_damage(self, st: dict, est: dict, info: dict, kind: str, lv: int,
                          pmult: float, _seg_crit: bool, _lucky_seg: bool,
                          _pp_phys: float, _pf_phys: int, _pp_magi: float, _pf_magi: int,
                          _skill_flat: int, effs: dict, player: dict) -> tuple:
        """v176 拆分：单段伤害计算（原 _player_skill 段循环内 76 行内联）。

        输入段级状态（暴击/穿透/技能基础值/乘区/符文），返回 (dmg_i, magi_add)。
        副作用：消耗 spellblade_surge buff、_apply_mark 标记。
        """
        magi_add = 0
        _skill_expr = E.skill_formula_expr(info, lv)
        if _skill_expr:
            _seg_type = "true" if kind == K_TRUE else ("phys" if kind == K_PHYS else "magi")
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
            magi_add += _mseg0
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
            magi_add += _mseg
        elif kind == K_TRUE:
            dmg_i = E.calc_damage(int((st["atk"] * info["power"] + _skill_flat) * pmult), 0, _seg_crit, dmg_type="true")
        elif kind == K_PHYS:
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
                magi_add += dmg_m
        else:
            # v109.2 P1-6：pierce 魔法分支修复——审判之剑等魔法 pierce 技能此前被结算链忽略
            if info.get("pierce"):
                dmg_i = E.calc_damage(int((st["matk"] * info["power"] + _skill_flat) * pmult), 0, _seg_crit, pierce=True,
                                      dmg_type="magi")
            else:
                dmg_i = E.calc_damage(int((st["matk"] * info["power"] + _skill_flat) * pmult), est["mdef"], _seg_crit,
                                      pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
        # v87 魔剑士·魔力涌动：消耗 buff，本次攻击追加 80% 魔法伤害
        if self._p_buffs_bag().get("spellblade_surge"):
            surge_dmg = E.calc_damage(int(st["matk"] * 0.80 * pmult), est["mdef"], _seg_crit,
                                      pene_pct=_pp_magi, pene_flat=_pf_magi, dmg_type="magi")
            dmg_i += surge_dmg
            magi_add += surge_dmg
            del self._p_buffs_bag()["spellblade_surge"]
        # v34 残忍：暴击伤害 +x%（按等级，符文特效）
        brutal_lvl = self._enchant_lvl(effs, "brutal")
        if brutal_lvl and _seg_crit:
            dmg_i = int(dmg_i * (1 + C.rune_value("brutal", brutal_lvl)))
        # v106.3 暴击伤害属性（crit_dmg 面板化：词条折算 + 种族 + 被动 + 药水）
        cdmg = float(st.get("crit_dmg", 0) or 0)
        # v169.7 暗影步·极 shadow_dance_bonus：影舞态中暴击伤害 +20%（暴伤加算）
        cdmg += self._passive_crit_dmg_mult(player)
        if self._p_buffs_bag().get("crit_dmg_pot"):
            cdmg = 1 - (1 - cdmg) * (1 - 0.25)  # 狂暴药剂 +25% 暴伤（乘算并入）
        if _seg_crit and cdmg > 0:
            dmg_i = int(dmg_i * (1 + cdmg))
        # v109.2 P1-1 运势：幸运一击——暴击后 30% 概率追加 50% 伤害
        if _lucky_seg:
            dmg_i = int(dmg_i * LUCKY_CRIT_MULT)
        dmg_i = self._apply_mark(dmg_i)
        return dmg_i, magi_add

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
        except Exception as _sw_e:
            _battle_warn('_player_skill', _sw_e)
            pass
        # v122 治疗指定队友：解析目标（allies 空=单人战斗 → None=奶自己）
        target_ally = self._resolve_ally_target(target) if kind == K_HEAL else None
        # v107 召唤：技能带 summon 字段 → 生成召唤物实体（治疗/增益/攻击技能均可带，先召唤再结算技能）
        # v177 双向：施法者是怪（_cast_ctx 无 class_name）→ 召唤敌方援军帮自己；玩家 → 原玩家侧召唤物
        if info.get("summon"):
            if not self._cast_is_player():
                try:
                    self._summon_minions(1)
                    logs.append(f"🜲 【{player.get('name', '怪物')}】召唤了援军！")
                except Exception as _sw_e:
                    _battle_warn('_player_skill', _sw_e)
                    pass
            else:
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
        p_mech = self._cast_stacks()
        if kind == K_HEAL:
            return self._skill_heal(st, skill_name, info, player, lv, mech, mval, p_mech, logs, target_ally=target_ally)
        if kind == K_BUFF:
            return self._skill_buff(st, skill_name, info, player, lv, mech, mval, p_mech, logs)
        if kind == K_TAUNT:
            # v51 挑衅怒吼：嘲讽（单人=敌方降攻+叠狂暴；副本=instance 层拉仇恨）
            self._tgt_buffs()["mon_atk_down"] = E.skill_buff_turns(lv)
            self._apply_mech_gain("rage", 1, p_mech, logs, skill_name)
            logs.append(f"📢 你大声挑衅【{self._tgt().get('name', '敌人')}】！敌人恼羞成怒，攻击力下降！")
            if info.get("team"):
                # v173.5 全层仇恨：team taunt 事件带技能配置（hate_taunt_mult/hate_lock_turns 数据驱动）
                self.team_effects.append({"kind": "taunt", "lv": lv, "cfg": info})
                logs.append(f"🌟【团队】{info.get('name', skill_name)}：Boss 的注意力被牢牢锁定！")
            return logs

        # v180 actor 化：est = 被打目标面板（原硬编码 self.enemy=主怪；怪施法打玩家时
        # 错误用怪自己 def/mdef/韧性当玩家防御 → 伤害虚高。_tgt() 玩家施法=怪、怪施法=玩家）
        if self._tgt_is_player():
            est = self._player_stats(self._tgt())
        else:
            # v180F 修复：显式传目标怪（_enemy_stats() 无参读 _active_target 多怪时漂移）
            est = self._enemy_stats(self._tgt())
        # v176: 暴击判定抽 _skill_crit_roll（原 42 行内联）
        is_crit, _stealth_hit, lucky, stealth_mult, est, effs = self._skill_crit_roll(
            st, est, player, info, mech, skill_name, logs)
        # v176: 乘区装配抽 _skill_assemble_mults（原 123 行内联）
        _mc = self._skill_assemble_mults(
            st, est, player, info, mech, kind, lv, skill_name, p_mech, logs, effs,
            is_crit, _stealth_hit, lucky, stealth_mult)
        multi = _mc["multi"]; pmult = _mc["pmult"]
        reaction_log = _mc["reaction_log"]; element = _mc["element"]
        _procs = _mc["_procs"]; _execute_tag = _mc["_execute_tag"]
        frozen_bonus = _mc["frozen_bonus"]; stack_bonus = _mc["stack_bonus"]
        cond_mult = _mc["cond_mult"]; cond_label = _mc["cond_label"]
        magic_bonus = _mc["magic_bonus"]; mb_lvl = _mc["mb_lvl"]
        stealth_mult = _mc["stealth_mult"]; elem_mult = _mc["elem_mult"]
        affix_tags = _mc["affix_tags"]
        total = _mc["total"]; _magi_part = _mc["magi_part"]
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
            # v176: 单段伤害计算抽 _skill_seg_damage（原 76 行内联）
            dmg_i, _mseg_i = self._skill_seg_damage(
                st, est, info, kind, lv, pmult, _seg_crit, _lucky_seg,
                _pp_phys, _pf_phys, _pp_magi, _pf_magi, _skill_flat, effs, player)
            _magi_part += _mseg_i
            total += dmg_i
        if lucky:
            logs.append("✨ 幸运一击！暴击伤害额外提升 50%！")
        # v176: 总伤后处理抽 _skill_finalize_damage（原 113 行内联）
        total, _magi_part, info, _v169_tags = self._skill_finalize_damage(
            st, player, info, kind, element, skill_name, multi,
            is_crit, total, _magi_part, logs)        # 特效合并成紧凑标签（避免一行堆满长后缀）
        # v176: 标签+印记抽 _skill_apply_tags_marks（原 74 行内联）
        self._skill_apply_tags_marks(
            st, player, info, mech, is_crit, total, element,
            frozen_bonus, stealth_mult, stack_bonus, cond_mult, cond_label,
            magic_bonus, mb_lvl, _execute_tag, affix_tags, elem_mult,
            reaction_log, _procs, logs, _v169_tags)        # v2.0 连招序列：拳师 combo 字段推进（拳→踢→掌 三连触发额外效果）
        # v176: 命中后结算抽 _skill_hit_settle（原 172 行内联）
        self._skill_hit_settle(
            st, player, info, mech, mval, p_mech, effs,
            is_crit, total, lv, skill_name, kind, _procs, logs)
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
                n = int(_pres.get(_k, 0) or 0) if _pres else int(self._p_res().get(_k, 0) or 0)
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
            player.setdefault("v139_modes", self._p_v139_modes())
            player.setdefault("v139_charge", self._p_v139_charge())
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

    def _apply_mech_effect(self, mech: str, mval: int, p_mech: dict, total: int, logs: list, skill_name: str, is_crit: bool = False, info: dict | None = None, caster: dict | None = None):
        """攻击技能施放后的机制结算（v98.4：数据化 → core/battle_mech.py MECH_EFFECTS）
        v113.1：info（技能 dict）下传，handler 可读技能自带 mech_chance 固定概率。"""
        from .core.battle_mech import MECH_EFFECTS
        handler = MECH_EFFECTS.get(mech)
        # v169.7 叠层被动上限（追猎者/灵魂锁链/剧毒·淬毒之心）：记录命中前层数，
        # handler 按默认 cap（3/5）叠完后再把“被 cap 吞掉”的应叠层补到被动上限
        _cap_pre = {}
        try:
            _pl_cap = caster or {}
            _tgt_cap0 = getattr(self, "_active_target", None) or self.enemy
            _deb_cap0 = (_tgt_cap0.get("debuffs") or {})
            if mech == "hunt_mark":
                _cap_pre["hunt_mark"] = int(_deb_cap0.get("hunt_mark", 0) or 0)
            if mech == "soul_mark":
                _cap_pre["soul_mark"] = int(_deb_cap0.get("soul_mark", 0) or 0)
            if mech in MECH_PROC_GROUPS.get("poison_dmg", ("poison",)):
                _cap_pre["poison"] = int((_deb_cap0.get("poison") or {}).get("n", 0) or 0)
        except Exception:
            _cap_pre = {}
        if handler:
            handler(self, mval, p_mech, total, logs, skill_name, is_crit, info)
        # ---- v169.7 被动叠层上限放宽（术后补层，只对命中当次生效；mval=叠层量）----
        try:
            _pl_cap = caster or {}
            _pm_cap = self._proc_pm(_pl_cap)
            _tgt_cap = getattr(self, "_active_target", None) or self.enemy
            _deb_cap = _tgt_cap.setdefault("debuffs", {})
            _mv = max(0, int(mval or 0))
            if mech == "hunt_mark" and _pm_cap["proc"].get("hunt_mark_cap") and _mv > 0:
                _extra_cap = 0
                for _pn, _ps in _pm_cap["proc"].get("hunt_mark_cap", []):
                    _extra_cap = int(_ps.get("add", 2) or 2)
                    break
                _old_hm = _cap_pre.get("hunt_mark", 0)
                _now_hm = int(_deb_cap.get("hunt_mark", 0) or 0)
                if _old_hm + _mv > _now_hm:
                    _deb_cap["hunt_mark"] = min(3 + _extra_cap, _old_hm + _mv)
            if mech == "soul_mark" and _pm_cap["proc"].get("soul_mark_cap") and _mv > 0:
                _extra_sm = 2
                for _pn, _ps in _pm_cap["proc"].get("soul_mark_cap", []):
                    _extra_sm = int(_ps.get("add", 2) or 2)
                    break
                _old_sm = _cap_pre.get("soul_mark", 0)
                _now_sm = int(_deb_cap.get("soul_mark", 0) or 0)
                if _old_sm + _mv > _now_sm:
                    _deb_cap["soul_mark"] = min(3 + _extra_sm, _old_sm + _mv)
            if mech in MECH_PROC_GROUPS.get("poison_dmg", ("poison",)):
                _cap_pois = self._poison_cap(_pl_cap)
                _old_p = _cap_pre.get("poison", 0)
                _now_p = int((_deb_cap.get("poison") or {}).get("n", 0) or 0)
                if _old_p + _mv > _now_p and _cap_pois > 5:
                    _deb_cap.setdefault("poison", {})["n"] = min(_cap_pois, _old_p + _mv)
        except Exception as _sw_e:
            _battle_warn('_apply_mech_effect', _sw_e)
            pass
        # v130.2f2（T7 P1-1）：鹰眼 mark_extra 在游侠标记路径（mech=mark：林语印记/猎杀标记类技能）
        # 也独立 roll——与法师元素印记路径（_player_skill 3388-3390）同语义：每个被动独立 chance，
        # 额外层经同源 handler 叠加进目标 debuffs.mark（cap 5）。此前消费点只在 element 印记分支，
        # 全库 element 技能仅法师系持有，游侠/星语猎手标记被动（追踪印记 30%/鹰眼 15%）零触发=死被动。
        if mech == "mark":
            _pl_mark = caster or {}
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
        # v178 E10：静态字段 dmg_taken_mult（build_monster 透传）作为兜底（动态 _dmg_taken_mult 优先）
        _dtm = float((self.enemy or {}).get("_dmg_taken_mult",
                     (self.enemy or {}).get("dmg_taken_mult", 1.0)) or 1.0)
        if _dtm != 1.0:
            dmg = max(1, int(dmg * _dtm))
        # v178 E3c：阶段退出 exit_dmg 累计（仅当阶段配了 exit_dmg 才记——_phase_exit 存在且 dmg 非空）
        try:
            _px = (self.enemy or {}).get("_phase_exit")
            if _px and _px.get("dmg") is not None:
                _px["_acc_dmg"] = int(_px.get("_acc_dmg", 0) or 0) + max(0, dmg)
        except Exception as _sw_e:
            _battle_warn('_boss_dmg_filter', _sw_e)
            pass
        mech = self.enemy.get("mech")
        if self.btype == "pvp":
            return dmg
        mechs = [x.strip() for x in (mech or "").split(",") if x.strip()]
        e = self.enemy
        # v180G B2-1：护盾吸收段删除——护盾（含 halve 语义）统一由 _damage_actor
        # 承伤链消费（L10853 起完整处理 halve 盾/真伤/破盾后剩余穿透）。此前此处
        # 与 _damage_actor 各有一份手写吸收 = 结构性重复；dot/附加伤害只走
        # _damage_actor、主伤害走 filter+actor，两路 halve 次数不一致的历史隐患
        # 一并消除——现在全伤害路径统一只 halve 一次（v178.1「勿双吸」目标真正落地）。
        # 全库 boss_shield 旧字段已无读写（v177 迁移 shields dict 时消费端收敛），无兜底负担。
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
        # v178 E8b：爪牙死亡联动消费（独立于 mech——配 on_minion_died 字段即生效；
        # 瞬态标记由 _on_minion_died_tick 内部 pop 消费）
        try:
            if not self.btype == "pvp" and (e or {}).get("on_minion_died"):
                self._on_minion_died_tick(e, logs)
        except Exception as _sw_e:
            _battle_warn('_boss_mech', _sw_e)
            pass
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
            return int(self._now / ACT_TICK) + 1
        except Exception:
            return 1

    def _boss_cfg(self, e: dict) -> dict:
        """v116.1：按 enemy id 从数据层解析 Boss 条件/剧本配置。
        优先取 enemy dict 自带的 scripts（数据层已直写），否则按 id 在 INSTANCES /
        MONSTER_MODS 找条目读 opening/triggers/phases/chains 字段。返回含缺省 key 的 dict。

        v178 E1：副本 Boss 的 enemy dict 带 _inst_id（instance.py _enter_stage_combat 写入），
        按它查 INSTANCES[inst_id]——旧逻辑按 e.id=b_xxx 查 INSTANCES 命中不了，
        导致副本 phases/opening/triggers 是死数据。多怪阵列（爪牙）无 _inst_id → 只查自身 id。"""
        if not e:
            return {"opening": None, "triggers": {}, "phases": [], "chains": []}
        cfg = dict(e.get("scripts") or {})
        if not cfg:
            mid = (e.get("_inst_id") or e.get("id") or "").strip()
            if mid:
                try:
                    from .data.monster_mods import MONSTER_MODS
                    from .data.instances import INSTANCES
                    # 副本 Boss：优先按 _inst_id 查副本条目（含 inst 内联 phases/opening/triggers），
                    # 再叠 monster_mods b_* 条目的剧本（两者可互补：inst 配副本专属，mods 配共用）
                    src = {}
                    if e.get("_inst_id"):
                        _ii = str(e["_inst_id"]).strip()
                        if _ii in INSTANCES:
                            src.update({k: INSTANCES[_ii].get(k) for k in
                                        ("opening", "triggers", "phases", "chains")
                                        if INSTANCES[_ii].get(k) is not None})
                        # 怪物 id（b_xxx）在 MONSTER_MODS 的剧本也合并进来
                        _bid = (e.get("id") or "").strip()
                        if _bid in MONSTER_MODS:
                            for k in ("opening", "triggers", "phases", "chains"):
                                if MONSTER_MODS[_bid].get(k) is not None:
                                    src[k] = MONSTER_MODS[_bid][k]
                    else:
                        src = INSTANCES.get(mid) or MONSTER_MODS.get(mid) or {}
                    # mech 前提：只在单位声明了机制时才读剧本（v116.1 语义保留——
                    # 副本 Boss 由 instance mech 注入保证非空；无 mech 的普通单位不读）
                    if src and (e.get("mech") or e.get("_inst_id")):
                        for k in ("opening", "triggers", "phases", "chains"):
                            if src.get(k) is not None:
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

    # v169.3 等级压制增伤（怪打玩家方向，2026-09-03 鱼鱼拍板落实审计 §六.3）：
    #   怪等级 > 玩家等级 → 玩家承伤 ×1.05^等级差（v169.4 鱼鱼拍板：原线性 +2%/级太温和，
    #   30级在45级区靠吸血站撸。改 1.05^diff 指数——与玩家打怪方向 1.02^diff 同构但更陡，
    #   越 5 级 ×1.28 / 10 级 ×1.63 / 15 级 ×2.08 / 20+ 级 ×2.65+，cap ×3.0 防一发出殡）；
    #   怪 ≤ 玩家等级不削（保持现状——低怪打高玩家不惩罚，反向无趣）。
    #   PVP 排除（敌方玩家快照无 lv 压制语义）；_damage_actor 全链路（普攻/技能/蓄力/反扑）都吃。
    def _enemy_lv_pressure(self, player: dict, e: dict) -> float:
        try:
            if self.btype == "pvp":
                return 1.0
            _elv = int((e or {}).get("lv", 0) or 0)
            _plv = int((player or {}).get("level", 0) or 0)
            _diff = _elv - _plv
            if _diff > 0:
                return min(1.05 ** min(_diff, 50), 3.0)
        except Exception as _sw_e:
            _battle_warn('_enemy_lv_pressure', _sw_e)
            pass
        return 1.0

    def _lookup_skill_info(self, skill_key: str) -> dict:
        """v177 技能查表统一入口：先查怪物技能表 MONSTER_SKILLS，查不到查玩家技能全表
        （E.skill_by_key——怪物技能可引用玩家技能 key，存储分离、解析一套）。
        返回技能 dict（可能含玩家技能字段：exprs/kind/heal_formula 等）；查不到返回 {}。"""
        if not skill_key:
            return {}
        s = C.MONSTER_SKILLS.get(skill_key)
        if s is None:
            try:
                s = E.skill_by_key(skill_key)
            except Exception:
                s = None
        return s or {}

    def _actor_skill_cast(self, caster: dict, skill_name: str, target: dict, ev: dict) -> tuple:
        """v180G B3-改名：任意 actor（caster）施放任意技能 → 统一玩家技能管线结算。
        原 _actor_skill_cast（v177 引入时只让怪放玩家技能）——现已双向 actor：
        caster=任意攻击方（怪/随从/玩家侧 actor），target=任意被击目标。
        技能全语义一次获得（exprs/cond/多段/mech/吸血/暴击/元素/标记等——不再逐项补）。
        返回 (logs, 对 target 总伤害)——管线已内部经 _deal_hit/_damage_actor 真实扣血，
        返回 dmg 恒 0（防调用处双扣，v180F 修复）。
        增益/治疗目标=施法者自身（caster），伤害目标=target。"""
        info = self._lookup_skill_info(skill_name)
        logs = []
        if not info:
            return logs, 0
        _saved_ctx = self._cast_ctx
        _saved_tgt = self._target_ctx
        self._cast_ctx = caster
        self._target_ctx = target
        # v180F：格挡 defend_reduce 需要技能名（_damage_actor 承伤链按当前施法技能查表）——
        # _cast_ctx=施法者身上没有 _cast.skill（cast_done 已清），临时挂 _cast_skill 供查
        _saved_ck = caster.get("_cast_skill")
        caster["_cast_skill"] = skill_name
        try:
            # 施法者面板 + 技能等级（玩家 exprs 里 skill_lv/player_lv 成长用施法者等级折算）
            st = self._enemy_stats(caster)
            st = dict(st)
            _slv = max(1, min(20, int(caster.get("lv", 1) or 1) // 2))
            st["_skill_lv"] = _slv
            st["_player_lv"] = int(caster.get("lv", 1) or 1)
            # 攻击方临时技能等级（管线 E.skill_level_of 读 caster.skill_levels——怪没有，管线内 lv 会=1；
            # 这里把折算等级写 caster 临时字段供管线 skill_level_of 读取）
            _had_skl = caster.get("skill_levels")
            caster["skill_levels"] = {skill_name: _slv}
            # 管线造成的 target 伤害已经 _deal_hit 落 _damage_actor(target)——从 target hp 变化反推
            _hp0 = int(target.get("hp", 0) or 0)  # 管线前快照（扣血基准）
            try:
                # target=None → 治疗/增益目标=施法者自己（管线 _resolve_ally_target(None) 单人=自己）
                plogs = self._player_skill(st, skill_name, info, caster, target=None)
            finally:
                if _had_skl is None:
                    caster.pop("skill_levels", None)
                else:
                    caster["skill_levels"] = _had_skl
            logs += plogs
            # v180F 修复 double dip：管线已通过 _deal_hit/_damage_actor 把伤害真实扣到目标
            # hp（含承伤链免伤/格挡/护盾），这里不再返回伤害值让调用处二次 _damage_actor 扣血
            # （v180 收编怪技能后调用处 3585/3320 按旧"返回 dmg 外部扣"语义双扣 = 怪技能/
            # 普攻伤害全部翻倍，本会话实测 120→240）。返回 dmg=0：调用处跳过外部扣血；
            # 防御格挡已下沉 _damage_actor 承伤链（defending 玩家统一减免），此处不需要。
            return logs, 0
        except Exception:
            return logs, 0
        finally:
            self._cast_ctx = _saved_ctx
            self._target_ctx = _saved_tgt
            if _saved_ck is None:
                caster.pop("_cast_skill", None)
            else:
                caster["_cast_skill"] = _saved_ck

    def _enemy_cast_done(self, player: dict, unit: dict, ev: dict) -> tuple:
        """v154 敌方对称读条：敌方出招读条结束（cast_done 事件触发）→ 结算伤害。
        返回 (日志列表, 对玩家伤害, 伤害段类型 or None)。
        v180G B2-2：第三返回值 dmg_kind —— 普攻 atk 分支不再手写物免/魔免减免，
        由调用处透传 _damage_actor 的 dmg_kind 统一消费（与技能管线路径同一处减免，
        消灭手写段 vs 承伤链 dmg_kind 段的双实现）。None = 技能管线已内部落地（dmg 恒 0）。
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
        # v180F B5：目标面板按 side 路由——目标是玩家走 _player_stats，怪/随从走 _enemy_stats
        try:
            _tgt_side = self.side_of(player)
        except Exception:
            _tgt_side = "player" if (player or {}).get("class_name") else "enemy"
        if _tgt_side and _tgt_side != "player":
            pst = self._enemy_stats(player)
        else:
            pst = self._player_stats(player)
        # v180F B5 修复：攻击方面板必须显式传攻击单位 e——_enemy_stats() 无参会读
        # _active_target（=被打目标），导致怪vs怪时攻击方属性错用目标面板（伤害≈0）
        est = self._enemy_stats(e)
        dmg = 0
        _kind = ev.get("kind", "atk")
        # v63 沉默：敌方技能被沉默 → 读条结束时转为普攻（与出手瞬间判定一致）
        if _kind == "skill" and "silence" in eb:
            _kind = "atk"
        if _kind == "skill":
            sinfo = self._lookup_skill_info(ev.get("skill") or "")
            if not sinfo:
                _kind = "atk"
            else:
                # v180 所有技能统一走管线（玩家技能 key + 怪自身技能 ms_*）：
                # _actor_skill_cast 已双向 actor（_cast_ctx=怪/_target_ctx=玩家），
                # _player_skill 按 kind 分流（治疗 hp_pct/heal_formula/增益/召唤/物理魔法伤害），
                # 怪自身技能数据已归一（heal_self→kind=治疗+hp_pct、无 formula 已补等效段）。
                # 原 v177 只对玩家技能 key 走管线、怪自身技能落下方 260 行简化结算（两套代码根）。
                try:
                    _ml_s, _dg_s = self._actor_skill_cast(e, ev.get("skill"), player, ev)
                    return _ml_s, _dg_s, None  # v180G B2-2：管线已内部落地，dmg_kind=None
                except Exception as _sw_e:
                    _battle_warn('_enemy_cast_done', _sw_e)
                    pass
                # v180：管线异常兜底回落普攻（简化结算死代码已删——正常全部走 _actor_skill_cast）
                _kind = "atk"
        # 敌方普攻（_kind == "atk" 或技能查表失败）
        # v169.3 等级压制增伤：怪高玩家 N 级 → 普攻 ×(1+0.02N)（cap ×3，同技能方向）
        # v174/v174.1 普攻技能化统一：怪物普攻 = 释放普攻技（默认 atk×1.0 物理；e.basic_skill
        # 可配自定义如魔法普攻怪 matk×1.0 magi 段吃 mdef），统一走 resolve_formula 管道
        _lpm = self._enemy_lv_pressure(player, e)
        is_crit = random.random() < est.get("crit", 0.05) * self._tenacity_mult(pst)
        _pp, _pf = self._pene_vals(est)
        _mbs = (e or {}).get("basic_skill")
        _mexpr = None
        _mkind = K_PHYS
        if isinstance(_mbs, dict):
            _mexpr = (_mbs.get("exprs") or [None])[0]
            _mkind = _mbs.get("kind", K_PHYS)
        if not _mexpr:
            # 默认普攻：物理 atk×1.0（与旧 calc_damage(atk) 等价，走统一公式管道）
            _mexpr = "atk*1.0"
            _mkind = K_PHYS
        _mt = seg_of(_mkind)
        _mst = dict(est)
        _d0, _mm0 = E.resolve_formula(
            [{"expr": _mexpr, "type": _mt}], _mst, pst.get("def", 0), pst.get("mdef", 0),
            is_crit=is_crit, pene_phys=_pp, pene_magi=_pf,
            mult=1.0, variance=0.0,
        )
        dmg = int(_d0)
        dmg = max(1, int(dmg * _lpm))
        # v180G B2-2：物理/魔法免伤不再手写——由调用处透传 dmg_kind 到 _damage_actor
        # 承伤链统一消费（与技能管线路径同一处减免，见 _process_until/enemy_phase 落地）。
        # 原 v180F 清2a 在此手写物免/魔免（cap 40%）→ 已收口；目标面板 pst 已在 L7440 路由。
        # v180F B5：文案用目标名（怪vs怪不再错误显示"攻击你"）
        _tgt_disp = (player or {}).get("name", "") if (player or {}).get("name") else ""
        self._pending_dmg_lines.append(
            f"【{ename}】攻击{_tgt_disp or '你'}，造成 {dmg} 点伤害！" + (" 💥暴击！" if is_crit else ""))
        dmg += self._reactive_extra_attack(e, pst, logs)
        return logs, dmg, _mt

    def _pick_hostile_target(self, unit: dict) -> dict | None:
        """v180F B5：通用敌对目标选择——从 unit 的敌对阵营选一个存活 actor。

        规则：取 unit.side 的敌对 side 列表；优先选第一个有存活 actor 的敌对 side
        的存活目标（按 rank 前排优先）。无玩家战斗（怪vs怪）时敌对 = 另一阵营。
        副本/野外（unit 在 enemy side）→ 敌对 = player side（玩家/队友）。
        返回目标 actor dict；无可用目标返回 None。
        """
        try:
            _side = self.side_of(unit) or "enemy"
            _hostile = self.hostile_sides(_side)
            if not _hostile:
                # 兜底：没有 side 体系（旧战斗）→ 玩家侧为目标
                return getattr(self, "player", None) or {}
            for _hs in _hostile:
                _pool = (self.sides or {}).get(_hs) or []
                # 前排优先：rank 小者先；存活过滤
                _alive = [a for a in _pool if a.get("hp", 0) > 0]
                if not _alive:
                    continue
                _alive.sort(key=lambda a: int(a.get("rank", 1) or 1))
                return _alive[0]
            return None
        except Exception:
            return getattr(self, "player", None) or {}

    def _enemy_turn(self, player: dict, unit=None) -> tuple:
        """敌方单个单位行动。返回 (日志列表, 对玩家伤害)。
        v2：unit 缺省 = 主目标（单怪兼容）；支持单位级蓄力。
        v154 敌方对称读条：本函数 = 敌方"出手瞬间"（决定动作类型 + 排敌方出招读条）。
        出招读条结束（cast_done）才结算伤害——见 _enemy_cast_done。
        特例：被控跳过（眩晕/冻结/睡眠）、增益/蓄力直接返回（无出招读条）。
        """
        if self.btype == "pvp":
            # v180E 低危 B3：删除僵尸 _pvp_enemy_turn——PVP 战斗 enemy_act 恒 False
            # （battle 刻由双方真人轮流操作），_enemy_phase 首行 `enemy_act and btype != "pvp"`
            # 已挡死本分支。保留 raise 防未来误直调（真实 PVP AI 需用事件系统重写）。
            raise RuntimeError("PVP 敌方 AI 未实现（不可达：PVP enemy_act 恒 False）")
        e = unit or self.enemy
        eb = e.setdefault("buffs", {})
        ename = e.get("name", "怪物")
        logs = []
        # v173.6 副本多目标重构 + v180F B5 通用敌对目标：目标 actor 决策。
        # 优先级：
        #  ① 自定义 side（怪vs怪等无玩家战斗）→ _pick_hostile_target 从敌对阵营选
        #  ② 副本（battle 带 _st + allies）→ 按 target_policy 从 allies 选（原逻辑）
        #  ③ 野外/单人 → player 原样（传入即目标）
        _e_side = self.side_of(e)
        if _e_side and _e_side != "player" and _e_side != "enemy":
            # 自定义敌对阵营（怪vs怪/多阵营混战）：从敌对 side 选目标
            _t = self._pick_hostile_target(e)
            if _t is not None and _t.get("hp", 0) > 0:
                player = _t
            else:
                # 敌对全灭 → 无目标（应由战斗流程层判胜利）
                return logs, 0
        elif self._st and self.allies and player:
            _q_src = str(player.get("qq_id") or "")
            if _q_src and not (self._st.get("alive") or {}).get(_q_src, True):
                # 原目标已死（instance 旧逻辑可能传已倒玩家）→ 重新选
                player = None
            if self._st.get("_enemy_pick_target", True):
                # 副本默认由 battle 按策略重选目标（_pick_enemy_target 内部读 target_policy；
                # 若 instance 显式指定目标（如 Boss 点名技能预选）可置 _enemy_pick_target=False）
                _picked = self._pick_enemy_target(e)
                if _picked is not None:
                    player = _picked
        elif _e_side == "enemy" and not player:
            # 敌方无玩家目标（野外构造异常/测试）→ 敌对 player side 若有成员则选
            _t = self._pick_hostile_target(e)
            if _t is not None and _t.get("hp", 0) > 0:
                player = _t
        # v2：本次敌方行动目标 = 该单位（_enemy_stats 默认按 _active_target 解析单位属性；
        # 兼容测试 monkeypatch 的 1 参 _enemy_stats）
        self._active_target = e
        # v154：est 提前定义（被控/阶段跳过分支的 ct 重排需要 spd）
        est = self._enemy_stats()
        # v116.1 反制/追击瞬态标记：每刻开头清空，仅本刻触发的刻生效
        self._clear_reactive_flags(e)
        self._boss_mech(logs, e)
        # v178 E3c：阶段退出条件轮询（exit_turns/exit_dmg 达标 → 退出当前阶段回到上一段，
        # 清 _phase_mod/_phase_ult_every/_phase_freq_mult/_phase_counter 让 Boss 恢复常态）
        _pe = e.get("_phase_exit")
        if _pe and not getattr(self, "_phase_skip_act", False):
            try:
                _entered = int(_pe.get("entered_at", 0) or 0)
                _turns = _pe.get("turns")
                _dmg = _pe.get("dmg")
                _now_r = self._tick_no()
                _do_exit = False
                if _turns is not None and _now_r - _entered >= int(_turns or 0):
                    _do_exit = True
                if not _do_exit and _dmg is not None and int(_pe.get("_acc_dmg", 0) or 0) >= int(_dmg or 0):
                    _do_exit = True
                if _do_exit:
                    e.pop("_phase_mod", None)
                    e.pop("_phase_exit", None)
                    e.pop("_phase_ult_every", None)
                    e.pop("_phase_ult_skills", None)
                    e.pop("_phase_freq_mult", None)
                    e.pop("_phase_counter", None)
                    e.pop("_dmg_taken_mult", None)
                    if e.get("phase_count", 0) > 0:
                        e["phase_count"] = max(0, int(e["phase_count"]) - 1)
                    logs.append(f"🌊 【{ename}】招式用老，气息回落，破绽收敛——")
                    self._after_actor_ct("e", e, cast_mult=CAST_ATK * self._ct_cost(est.get("spd", 0)))
                    return logs, 0
            except Exception as _sw_e:
                _battle_warn('_enemy_turn', _sw_e)
                pass
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
        # v167.3 修：蓄力释放伤害必须经 _damage_actor 落地（旧版只写 pending 日志不扣血——
        # 玩家实抓野猪王【践踏】"蓄力完成，轰然落下"后无伤害）
        if e.get("charging"):
            return self._enemy_charge_tick(e, pst, est, logs, ename, player=player)
        # v178 E3b：阶段大招 ult_every 消费（每 N 刻强制施放 ult_skills 池中技能，无视 skill_chance）
        silenced = "silence" in eb
        _ult_skill = None
        _ult_every = e.get("_phase_ult_every")
        _ult_pool = e.get("_phase_ult_skills") or []
        if _ult_every and _ult_pool and not silenced and not e.get("charging"):
            try:
                _ure = int(_ult_every or 0)
                if _ure > 0 and self._tick_no() % _ure == 0:
                    _cand = [s for s in _ult_pool if s in (e.get("skills") or [])]
                    if _cand:
                        _ult_skill = random.choice(_cand)
            except Exception:
                _ult_skill = None
        # 敌方 AI 决策（v176: 读怪数据 ai.skill_chance/weights，缺省回落全局常量——零行为变化）
        #   monsters 条目可配 {"ai": {"skill_chance": 0.5, "weights": {"ms_heal": 2, ...}, "first_move": "ms_x"}}
        _ai = (e or {}).get("ai") or {}
        _skill_chance = float(_ai.get("skill_chance", C.MON_SKILL_CHANCE) or C.MON_SKILL_CHANCE)
        # v178 E7：固定连招链 chains 消费（数据驱动——试炼骑士长固定 4 招循环等）
        #   Boss dict/scripts 配 "chains": [{"seq": ["sk1","sk2",...], "cd": N, "break": 0.1}, ...]
        #   seq=连招技能序列（按序推进，到头回绕）；cd=整链间隔（打完等 N 刻再起下轮，
        #   0=无缝循环）；break=断链概率（<1 时每步概率中断回随机池，缺省 0=必中链）
        #   引擎状态存 e._chain_cfg/_chain_pos/_chain_until（随战斗序列化）
        _chain_skill = None
        _chains_cfg = e.get("_chain_cfg")
        if _chains_cfg is None:
            try:
                _ccfg0 = self._boss_cfg(e).get("chains") or []
                if _ccfg0 and e.get("mech") or e.get("_inst_id"):
                    e["_chain_cfg"] = _ccfg0
                    _chains_cfg = _ccfg0
            except Exception:
                _chains_cfg = None
        if _ult_skill is None and _chains_cfg and not silenced and not e.get("charging"):
            try:
                _pos = int(e.get("_chain_pos", 0) or 0)
                _until = int(e.get("_chain_until", 0) or 0)
                _r_now = self._tick_no()
                # 冷却中（整链打完等 cd）→ 不推进链，回落随机
                if _r_now < _until:
                    _chain_skill = None
                else:
                    # 选当前链（可多链轮换：按 _chain_idx 取模）
                    _carr = _chains_cfg if isinstance(_chains_cfg, list) else []
                    if _carr:
                        _cidx = int(e.get("_chain_idx", 0) or 0) % len(_carr)
                        _chain = _carr[_cidx]
                        if isinstance(_chain, dict):
                            _seq = _chain.get("seq") or []
                            _brk = float(_chain.get("break", 0.0) or 0.0)
                            if _seq:
                                if _pos >= len(_seq):
                                    _pos = 0
                                    e["_chain_idx"] = _cidx + 1  # 链轮换
                                    _cidx2 = int(e.get("_chain_idx", 0) or 0) % len(_carr)
                                    _chain = _carr[_cidx2]
                                    _seq = _chain.get("seq") or []
                                    _brk = float(_chain.get("break", 0.0) or 0.0)
                                # 断链判定（break>0 时概率中断，中断=链状态清空回随机池）
                                if _brk > 0 and random.random() < _brk:
                                    e.pop("_chain_pos", None)
                                    e.pop("_chain_until", None)
                                    _chain_skill = None
                                else:
                                    _s = _seq[_pos] if _pos < len(_seq) else None
                                    if _s:
                                        _chain_skill = _s
                                        # 推进指针 + 链尾设置冷却
                                        e["_chain_pos"] = _pos + 1
                                        if _pos + 1 >= len(_seq):
                                            _cd = int(_chain.get("cd", 0) or 0)
                                            e["_chain_until"] = _r_now + _cd
            except Exception:
                _chain_skill = None
        # v178 E3b：ult_every 已强制指定 skill（_ult_skill）→ 直接进技能施放块；
        # 否则按原 AI 轮盘（skill_chance 概率）抽；E7 链命中则按链出招（无视 skill_chance）
        skill = _ult_skill or _chain_skill  # 大招 > 连招链 > 随机
        if skill is not None or (e.get("skills") and random.random() < _skill_chance and not silenced):
            # skill 已指定（ult/chain）时跳过轮盘；否则权重轮盘（缺省均匀抽）
            if skill is None:
                _weights = _ai.get("weights")
                if _weights and isinstance(_weights, dict):
                    _pool = [s for s in e["skills"] if s in _weights]
                    if _pool:
                        _wlist = [max(0, float(_weights.get(s, 1) or 1)) for s in _pool]
                        skill = random.choices(_pool, weights=_wlist, k=1)[0]
                    else:
                        skill = random.choice(e["skills"])
                else:
                    skill = random.choice(e["skills"])
            # v177 actor 资源门槛：抽中技能 res_cost 不足 → 技能不可用，回落普攻（不重抽，保持 random 序列）
            # 注意：只在技能声明 res_cost 且资源不足时拦截——旧技能无 res_cost → 零行为变化
            # （ult_every 强制大招不过资源门槛——它代表 Boss 拼死一搏，资源语义不拦；
            #  chain/随机技能正常查资源门槛）
            if skill is not None and _ult_skill is None:
                try:
                    _sfo_rc = self._lookup_skill_info(skill)
                    _rc_needed = _sfo_rc.get("res_cost")
                    if _rc_needed and isinstance(_rc_needed, dict):
                        for _rk_n, _rv_n in _rc_needed.items():
                            if self._res_read_actor(e, _rk_n) < int(_rv_n or 0):
                                skill = None  # 资源不足 → 普攻
                                break
                except Exception as _sw_e:
                    _battle_warn('_enemy_turn', _sw_e)
                    pass
            sinfo = self._lookup_skill_info(skill) if skill else None
            if sinfo:
                # v177 资源消耗：施放带 res_cost 的技能 → 出手扣资源（读条前扣——出手即付出，命中与否都消耗）
                try:
                    _rc_pay = sinfo.get("res_cost")
                    if _rc_pay and isinstance(_rc_pay, dict):
                        for _rk_p, _rv_p in _rc_pay.items():
                            self._res_spend(_rk_p, int(_rv_p or 0), actor=e)
                except Exception as _sw_e:
                    _battle_warn('_enemy_turn', _sw_e)
                    pass
                sname = sinfo.get("name", skill)  # 显示中文名
                kind = sinfo.get("kind")
                # v178 E6：记录本刻施放的技能 key（方向性防御读 defend_reduce 用）
                e["_last_skill_key"] = skill
                # v116 敌方蓄力接线：抽中带 charge 的技能且敌方未在蓄力 → 进入蓄力
                # （本刻不结算伤害，先给意图预告，之后刻由 _enemy_charge_tick 结算）
                charge_n = int(sinfo.get("charge", 0) or 0)
                if charge_n > 0 and not e.get("charging"):
                    e["charging"] = {"skill": skill, "left": charge_n, "name": sname}
                    logs.append(
                        f"⚠️ 【意图】{ename} 正在蓄力【{sname}】！下刻将造成大伤害——"
                        f"可『防御』减半或『打断技』赌它读条失败！")
                    return logs, 0
                if kind == K_BUFF or kind == K_HEAL:
                    # v180 增益/治疗即时分支统一走管线（原 MON_BUFF_EFFECTS/SKILL_BUFF_EFFECTS
                    # 双表分派为两套代码残余）：_actor_skill_cast 按 kind 分流——
                    # 增益(_skill_buff: atk_up/def_up/spd_up 兜底写怪 buffs)、治疗(_skill_heal:
                    # hp_pct/heal_formula)、召唤(summon:1 分支 _summon_minions)。即时生效语义保留
                    # （增益出手即上身，不排读条）。
                    _logs_b, _dmg_b = self._actor_skill_cast(e, skill, player,
                                                                  {"kind": "skill", "skill": skill})
                    logs += _logs_b
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
                                          "skill": skill, "power_mult": power,
                                          "target": player})
                logs.append(f"⚔️ 【{ename}】正在施展【{sname}】！(出招 {_cast_t:.1f}s)")
                # v163 敌方读条持久化：命中参数写入单位 dict（随 enemies 序列化），
                # from_state 恢复时补排 cast_done——野外/副本一套代码，读条伤害跨消息不丢。
                # v180F B5：目标 actor 一并写入（怪vs怪打敌对目标结算用）
                e["_cast"] = {"hit_at": self._now + _cast_t, "kind": "skill",
                              "skill": skill, "power_mult": power, "target": player}
                # 敌方读条后收招：ct = 命中时刻 + 收招（= 出手 + 总耗时）
                self._after_actor_ct("e", e, cast_mult=_cast_t + _rec_t)
                return logs, 0
        # v180F 敌方普攻收编管线：普攻 = 释放默认普攻技 ms_basic_attack（kind=skill 走完整
        # 管线，与 v180 敌方技能同路）。原手写普攻出招（kind=atk）已删——_enemy_cast_done
        # 不再有独立普攻结算。怪可配 e.basic_skill（技能 key）自定义普攻（缺省 ms_basic_attack）。
        _atk_key = str((e or {}).get("basic_skill") or "ms_basic_attack")
        _atk_info = self._lookup_skill_info(_atk_key) or {}
        # 普攻出招读条时长（普攻 cast 数据缺省 CAST_ATK）
        _cast_t, _rec_t = self._action_times("skill", skill=_atk_info or None, spd=est.get("spd", 0))
        if not _cast_t:
            _cast_t = CAST_ATK * self._ct_cost(est.get("spd", 0))
        # v163 敌方读条持久化（同技能分支：普攻命中参数也随单位序列化）
        # v180F B5：目标 actor 一并写入（怪vs怪打敌对目标结算用）
        e["_cast"] = {"hit_at": self._now + _cast_t, "kind": "skill",
                      "skill": _atk_key, "target": player}
        self._schedule_cast_done(self._now + _cast_t,
                                 {"side": "e", "unit": e, "kind": "skill",
                                  "skill": _atk_key, "target": player})
        _atk_name = _atk_info.get("name", "攻击") if _atk_info else "攻击"
        _tname = player.get("name", "你") if player else "你"
        logs.append(f"⚔️ 【{ename}】对{_tname}发动【{_atk_name}】！(出招 {_cast_t:.1f}s)")
        # 敌方读条后收招：ct = 命中时刻 + 收招（= 出手 + 总耗时）
        self._after_actor_ct("e", e, cast_mult=_cast_t + _rec_t)
        return logs, 0

    def _enemy_charge_tick(self, e: dict, pst: dict, est: dict, logs: list, ename: str, player: dict | None = None) -> tuple:
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
                return self._enemy_release_charge(e, ch.get("skill") or cname, pst, est, logs, ename,
                                                  player=player)
            # 蓄力持续刻：精简意图预告（剩 N）
            logs.append(f"⚠️ 【意图】{ename} 蓄力中(剩 {ch['left']})！")
            return logs, 0
        return logs, 0

    def _enemy_release_charge(self, e: dict, skill_name: str, pst: dict, est: dict, logs: list, ename: str,
                              player: dict | None = None) -> tuple:
        """敌方蓄力释放：按 MONSTER_SKILLS 里的技能结算伤害（对整个玩家方）。
        返回 (logs, 对玩家伤害)。"""
        # v180 蓄力释放统一走管线（同 _enemy_cast_done 收编）：_actor_skill_cast
        # 双向 actor（_cast_ctx=e 蓄力怪 / _target_ctx=player），_player_skill 按 kind 分流——
        # 物理/魔法伤害、治疗(hp_pct)、增益、召唤、pdot、mech 控制全语义一次获得。
        # 原简化结算（MON_BUFF_EFFECTS 增益 / calc_damage 手动伤害）为两套代码残余，已废弃。
        # ⚠️ 参数：_actor_skill_cast(unit, skill_name, target_player, ev)——第 4 参 ev 占位；
        # 返回的新 logs 要追加到本函数 logs（保留 charge_tick 已加的"蓄力完成，轰然落下"预告）
        _logs_r, _dmg_r = self._actor_skill_cast(e, skill_name, player, {"kind": "skill", "skill": skill_name})
        logs += _logs_r
        dmg = _dmg_r
        # v154：蓄力释放后敌方重排下次行动（读条 + 收招）
        self._after_actor_ct("e", e, cast_mult=CAST_SKILL * self._ct_cost(est.get("spd", 0)))
        return logs, max(0, dmg)

    # ---------------- 状态修正 ----------------
    def _apply_buffs(self, st: dict, buffs: dict) -> dict:
        st = dict(st)
        for eff, turns in buffs.items():
            if eff in BUFF_MULT:
                attr, val = BUFF_MULT[eff]
                # v104 M17 P2-5：宠物 buff（buff_atk/crit_up）实读 PET_POOL skill_value，
                # 覆盖 BUFF_MULT 常量（此前日志 25% 实际 30%，数据层承诺"加宠物=加一行"失效）
                # v180E 阶段2：强度值存 owner actor dict 的 pet_buff_vals（随 actor 序列化，
                # 替代旧 Battle 级 _pet_buff_vals 旁路——副本/断线恢复不丢）
                if attr in ("atk", "crit"):
                    _pv = (self.player or {}).get("pet_buff_vals", {}).get(attr)
                    if _pv is not None:
                        val = 1.0 + _pv if attr == "atk" else _pv
                if attr == "crit":
                    # v110 §三：暴击率上限统一 0.5（原 min(1.0) 可到 100%，与设计 50% 上限不符）
                    st["crit"] = min(C.PCT_CAPS.get("crit", 0.5), st.get("crit", 0) + val)
                elif attr == "precise":
                    # v173.3 意见#95：命中 buff 加法并入精准（PCT 百分比，cap 60% 与词条同源）
                    st["precise"] = min(C.PCT_CAPS.get("precise", 0.6), float(st.get("precise", 0) or 0) + val)
                elif attr == "magic_reduce":
                    # v180F 清2a：magic_resist 药剂魔法免伤（加法，cap 40% 与引擎 _enemy_mitigate 一致）
                    st["magic_reduce"] = min(0.4, float(st.get("magic_reduce", 0) or 0) + val)
                else:
                    st[attr] = int(st.get(attr, 0) * val)
        return st

    def _apply_equip_affix_stats(self, actor: dict, st: dict) -> dict:
        """v177 装备 stat 型词条合成（actor 通用，解析一套）：actor 带 equipment → 遍历词条，
        AFFIXES 表 effect 的 stat 键（thorns/dodge/block/phys_reduce 等面板属性）加成进 st（PCT cap）。
        玩家面板生成时已折算词条 → 传入空 equipment 无影响；怪物塞装备后此处补合成。
        无 equipment → 原样返回（零行为变化）。"""
        if not actor or not actor.get("equipment"):
            return st
        try:
            ids = self._equip_affix_ids(actor)
            if not ids:
                return st
            _caps = getattr(C, "PCT_CAPS", {})
            for aid in ids:
                info = C.AFFIXES.get(aid) or C.LEGENDARY_EFFECTS.get(aid) or {}
                eff = info.get("effect") or {}
                if not isinstance(eff, dict):
                    continue
                for k, v in eff.items():
                    if k in ("tiers", "desc", "trigger", "on"):
                        continue
                    # 只处理面板 stat 键（thorns/dodge/block/phys_reduce/magic_reduce/elem_res 等）
                    if k in ("thorns", "dodge", "block", "phys_reduce", "magic_reduce",
                             "elem_res", "abyss_res", "crit", "crit_dmg", "lifesteal",
                             "lifesteal_phys", "lifesteal_magi", "pene_phys", "pene_magi",
                             "precise", "tenacity"):
                        cap = _caps.get(k, 0.6)
                        if k in getattr(C, "PENE_PCT_STATS", ()) or ():
                            st[k] = min(1 - (1 - float(st.get(k, 0) or 0)) * (1 - float(v or 0)), cap)
                        else:
                            st[k] = min(float(st.get(k, 0) or 0) + float(v or 0), cap)
        except Exception as _sw_e:
            _battle_warn('_apply_equip_affix_stats', _sw_e)
            pass
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
            # v178 E3a：阶段行动频率倍率 freq_mult 折入速度（freq=0.5 → spd×2 慢一倍行动；
            # freq=2.0 → spd×0.5 快一倍——CTB 速度高=行动间隔短，频率语义对齐）。
            # 只对带 _phase_freq_mult 的阶段生效（旧阶段无此字段=零行为变化）
            _fq = float(e.get("_phase_freq_mult", 1.0) or 1.0)
            if _fq != 1.0 and _fq > 0:
                est["spd"] = max(1, int(est["spd"] / _fq))
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
        # v177 on_taken 受击加攻（复仇：_atk_up_val/_atk_up_until 由 _deal_damage on_taken 钩子写入；
        # _atk_up_until 为绝对 tick，过期则忽略并清理）
        _au_v = float(eb.get("_atk_up_val", 0) or 0)
        if _au_v > 0:
            if int(eb.get("_atk_up_until", 0) or 0) >= self._tick_no():
                est["atk"] = int(est["atk"] * (1 + min(_au_v, 0.5)))
                est["matk"] = int(est["matk"] * (1 + min(_au_v, 0.5)))
            else:
                eb.pop("_atk_up_val", None)
                eb.pop("_atk_up_until", None)
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
        # v177 装备 stat 型词条合成（怪物带 equipment → thorns/dodge/block 等生效；无装备零影响）
        if e.get("equipment"):
            est = self._apply_equip_affix_stats(e, est)
        return est

    def _enemy_mitigate(self, dmg: int, magi_part: int, element: str | None, logs: list, kind: str = K_PHYS,
                        dot: bool = False) -> tuple:
        """v110 P1-3：玩家攻击端消费敌方防守属性（与 _pvp_enemy_turn 玩家受击口径对称）。
        物理段吃敌方物免(≤40%)+格挡(≤40%，命中物段减半)；魔法段吃敌方魔免(≤40%)+元素抗(≤40%，按元素)。
        真伤绕过全部减伤（四层架构）；dot=True 时跳过格挡 roll（持续伤害不触发格挡事件）。
        PVE 标准怪无这些键(=0) → 伤害不变。
        v180 actor 化：目标=怪（玩家施法）读 self.enemy 防守；目标=玩家（怪物施法玩家技能/怪物技能）
        读玩家 actor 防守（phys_reduce/magic_reduce/elem_res/abyss_res 百分比免伤；格挡/闪避由
        _deal_hit 内 _damage_actor 承伤链处理）。返回 (削减后伤害, 削减后魔段)（魔段回传供吸血分账）。"""
        if kind == K_TRUE:
            return dmg, magi_part
        tgt = self._tgt()
        if self._tgt_is_player():
            tst = self._player_stats(tgt)
        else:
            tst = self._enemy_stats()
        if kind == K_MAGI:
            phys, magi = 0, dmg
        else:
            phys, magi = max(0, dmg - magi_part), magi_part
        reduced = 0
        pr = min(float(tst.get("phys_reduce", 0) or 0), 0.4)
        if pr > 0 and phys > 0:
            red = max(1, int(phys * pr))
            phys -= red
            reduced += red
        if not dot:
            bc = min(float(tst.get("block", 0) or 0), 0.4)
            if bc > 0 and phys > 0 and random.random() < bc:
                red = max(1, int(phys * 0.5))
                phys -= red
                reduced += red
                logs.append("🛡️ 敌人格挡了攻击！")
        mr_raw = float(tst.get("magic_reduce", 0) or 0)
        # 鲁莽之心（magic_reduce<0，兽人种族天赋）：魔法免伤负值 = 受伤加重
        if mr_raw < 0 and magi > 0:
            _pen_mr = max(1, int(magi * min(-mr_raw, 0.4)))
            magi += _pen_mr
            reduced -= _pen_mr
            logs.append(f"🔥 鲁莽之心，额外受到 {_pen_mr} 点伤害！")
        mr = min(mr_raw, 0.4)
        if mr > 0 and magi > 0:
            red = max(1, int(magi * mr))
            magi -= red
            reduced += red
            # v180 文案：怪打玩家走管线时输出专门"魔法免伤"（旧 _enemy_cast_done 手动段文案，
            # test_stage9_race 龙鳞/鲁莽断言依赖；玩家打怪仍合并进"敌方防守削减"）
            if self._tgt_is_player():
                logs.append(f"🛡️ 魔法免伤，减免 {red} 点伤害！")
        # v180 元素抗性词条保底（旧 _enemy_cast_done 6810-6815 语义）：装备带
        # elem_resist/abyss_resist 词条时，面板抗性不足保底值按保底算（战斗内动态读词条 id，
        # 不依赖面板折算——手工/旧装备词条可能未折算进 stats）。目标=玩家才查玩家装备。
        _pids_r = []
        if self._tgt_is_player():
            try:
                _pids_r = self._equip_affix_ids(self._tgt())
            except Exception:
                _pids_r = []
        # v180 暗影抗性（abyss_res）：dark 元素走深渊抗（旧 _enemy_cast_done melem==dark 分支）。
        # ⚠️ dark ∉ ELEMENT_MARKS（只有 fire/ice/thunder）——暗影抗必须在此独立处理，不能放块内
        if element == "dark":
            _imm_d = list((tgt or {}).get("element_immune") or [])
            if "dark" in _imm_d:
                logs.append(f"💠 免疫！【{tgt.get('name', '敌人')}】免疫暗影伤害！")
                return 0, 0
            ar_raw = float(tst.get("abyss_res", 0) or 0)
            if "abyss_resist" in _pids_r and ar_raw < 0.10:
                ar_raw = 0.10
            ar = min(ar_raw, 0.5)
            if ar > 0 and magi > 0:
                red = max(1, int(magi * ar))
                magi -= red
                reduced += red
                if self._tgt_is_player():
                    logs.append(f"🛡️ 元素抗性减免 {red} 点伤害！")
        if element and E.ELEMENT_MARKS.get(element):
            # v110 审计修复：cap 0.4 → 0.5（对齐防御端 _enemy_turn / PCT_CAPS["elem_res"]=0.5 /
            # 设计 §三「元素抗上限 50%」；此前 PVP 敌方元素抗 40%~50% 段在玩家攻击端被截断）
            # v178 E5：元素免疫/弱点表（数据驱动，蚀夜三形态/奥拉等 Boss 需要）
            #   怪物 dict: "element_immune": ["fire","ice"]（免疫元素 → 伤害归 0）
            #             "element_weak": {"ice": 1.5}（弱点元素 → 伤害 × 倍率）
            _imm = list((tgt or {}).get("element_immune") or [])
            if element in _imm:
                logs.append(f"💠 免疫！【{tgt.get('name', '敌人')}】免疫{element}伤害！")
                return 0, 0
            er = min(float(tst.get("elem_res", 0) or 0), 0.5)
            if "elem_resist" in _pids_r and er < 0.08:
                er = min(0.08, 0.5)
            if er > 0 and magi > 0:
                red = max(1, int(magi * er))
                magi -= red
                reduced += red
                # v180 文案：怪打玩家走管线时输出"元素抗性减免"（旧 _enemy_cast_done 手动段文案，
                # test_stage8_equip_affix elem_resist/abyss_resist 断言依赖）
                if self._tgt_is_player():
                    logs.append(f"🛡️ 元素抗性减免 {red} 点伤害！")
            _weak = (tgt or {}).get("element_weak") or {}
            if isinstance(_weak, dict) and element in _weak:
                try:
                    _wm = float(_weak[element] or 1.0)
                    if _wm > 1.0:
                        _add = max(1, int((phys + magi) * (_wm - 1.0)))
                        magi += _add
                        reduced -= _add  # 负的 reduced = 增伤（日志合并）
                        logs.append(f"⚡ 弱点！【{tgt.get('name', '敌人')}】弱{element}，受到额外伤害！")
                except Exception as _sw_e:
                    _battle_warn('_enemy_mitigate', _sw_e)
                    pass
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
        except Exception as _sw_e:
            _battle_warn('_pet_spd', _sw_e)
            pass
        return 50.0

    def _pet_ensure_actor(self):
        """v180-C S3：宠物参战时补 actor 字段（随从 actor 化——宠物 = companions 一员）。

        宠物作为"不在战场显示的 actor"（hidden + untargetable）进 companions：
        - side=player / kind=pet：引擎按字段走通用逻辑（治疗广播/增益等自然覆盖）
        - hidden：不进战场显示/状态面板（命令层读点按需跳过）
        - untargetable：敌人选目标跳过它（宠物不被攻击）
        - buffs 容器就位：可被增益/减益（未来扩展）
        - auto_act：v180E 阶段2 把 PET_POOL skill_type/skill_value/skill_interval 翻译成
          数据驱动行为（trigger=interval 由 pet_act tick 驱动，_companion_act 通用执行）。
        block 型宠物无 auto_act（挡刀走 guard 配置，_pet_ensure_guard 配）。
        与 self.pet 同 dict（就地补字段）→ 全部现有读点（_pet_block_check/_th_pet_act）
        零改动继续工作；伤害带 attacker=宠物 actor → 乘区读宠物自身被动。
        幂等：已在 companions 不重复加。"""
        try:
            pet = self.pet or {}
            if not pet:
                return
            if any(c is pet for c in getattr(self, "companions", [])):
                return  # 已 actor 化（同引用）
            pet.setdefault("side", "player")
            pet.setdefault("kind", "pet")
            pet.setdefault("buffs", {})
            pet["hidden"] = True
            pet["untargetable"] = True
            # v180F B4：宠物归属 owner = 焦点玩家（与召唤物同语义，挡刀/治疗归属读 owner）
            if not pet.get("owner") and self.player:
                pet["owner"] = self.player
            # v180E 阶段2：skill_type → auto_act（block 除外——挡刀走 guard）
            if not pet.get("auto_act"):
                pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
                if pdef:
                    stype = pdef.get("skill_type")
                    _TYPE_MAP = {
                        "atk_pct": "dmg_owner_atk",
                        "matk_pct": "matk_pct",
                        "heal_pct": "heal_owner",
                        "lifesteal": "lifesteal",
                        "pierce": "pierce",
                        "buff_atk": "buff_owner",
                        "crit_up": "buff_owner",
                    }
                    _act_type = _TYPE_MAP.get(stype)
                    if _act_type:
                        _act = {
                            "type": _act_type,
                            "value": float(pdef.get("skill_value", 0) or 0),
                            "skill_name": pdef.get("skill_name", "技能"),
                            "line": C.pet_line(pdef["key"]) if pdef.get("key") else "",
                        }
                        if stype in ("buff_atk", "crit_up"):
                            _act["buff"] = "atk_up" if stype == "buff_atk" else "crit_up"
                            _act["turns"] = 2
                        pet["auto_act"] = {
                            "trigger": "interval",
                            "act": _act,
                        }
            self.companions.append(pet)
        except Exception as _sw_e:
            _battle_warn('_pet_ensure_actor', _sw_e)
            pass

    def _pet_ensure_guard(self):
        """v180-B ②：block 型宠物参战时转配 guard（mode=absorb 数据化挡刀配置）。

        宠物 dict 带 guard 后 _pet_block_check 直接读配置（chance/cooldown/文案），
        不再依赖 PET_POOL skill_type=='block' 查表特判。非 block 型宠物不配 guard。
        幂等：已有 guard 不重复写。"""
        try:
            pet = self.pet or {}
            if not pet or pet.get("guard"):
                return
            pdef = next((p for p in C.PET_POOL if p["key"] == pet.get("pet_key")), None)
            if not pdef or pdef.get("skill_type") != "block":
                return
            pet["guard"] = {
                "mode": "absorb",
                "chance": float(pdef.get("skill_value", 0.25) or 0.25),
                "cooldown": float(int(pdef.get("skill_interval", 3) or 3)),
                "name": pdef.get("name", pet.get("name", "宠物")),
                "skill_name": pdef.get("skill_name", "守护"),
            }
        except Exception as _sw_e:
            _battle_warn('_pet_ensure_guard', _sw_e)
            pass

    def _reschedule_pet_tick(self):
        """v154 宠物独立读条（v179 P4 升级通用卡）：确保 pet_act 卡存在并刷新下次周期。

        周期 = 出招 + 收招，按宠物 spd 折算。旧实现排 pet_tick 事件；现在 pet_act 卡
        由 _th_pet_act handler 每次触发后动态更新 interval，通用调度按新周期续排——
        本方法仅幂等兜底（老调用点/老档补卡）。
        """
        try:
            if self.pet:
                self._pet_ensure_actor()  # v180-C S3：幂等补 actor 字段
                self._pet_ensure_guard()  # v180-B ②：幂等补 guard
                _has = any(e.get("uid") == "pet_act" for e in self.tick_effects)
                if not _has:
                    # v179 修正：周期 = 面板 skill_interval（每 N 刻一次），非读条
                    _pt = self._pet_interval_sec()
                    self.add_tick_effect("pet_act", self.pet, max(_pt, 0.001),
                                         uid="pet_act", source="pet")
        except Exception as _sw_e:
            _battle_warn('_reschedule_pet_tick', _sw_e)
            pass

    def _pet_interval_sec(self) -> float:
        """宠物技能面板节奏（skill_interval 刻 → 秒，1 刻 = ACT_TICK 秒）。

        宠物面板写明『每 N 刻一次技能』（skill_interval），v167.3 起按该节奏
        限制 pet_tick 实际出手频率（读条仍按宠物 spd 走，但两次出手间至少隔
        N × ACT_TICK 秒）。旧实现只按 CAST_PET_SKILL 读条周期触发，玩家一次
        行动窗口内跨多个到期点即连打（A2 层血蝠一次行动 5-6 次吸血撕咬实抓）。
        """
        try:
            _pdef = next((p for p in C.PET_POOL if p["key"] == (self.pet or {}).get("pet_key")), None)
            iv = int((_pdef or {}).get("skill_interval", 0) or 0)
            if iv > 0:
                return max(float(iv) * (ACT_TICK or 1.0), 0.001)
        except Exception as _sw_e:
            _battle_warn('_pet_interval_sec', _sw_e)
            pass
        return CAST_PET_SKILL * self._ct_cost(self._pet_spd())

    # ---------------- v178 E4 玩家侧持续伤害（敌方给玩家挂 dot） ----------------
    # ⚠️ v178 重构（鱼鱼指正）：dot 是 actor 能力，不是 player 特判。玩家/怪物都是
    # actor——身上有 debuffs 字段就挂/结算，没有就跳过（字段即能力，无身份 if）。
    # 挂载统一 _apply_dot(target, source)，结算统一 _tick_dots_of(actor)——
    # _tick_dots(玩家)（旧，结算"敌方身上的毒"）与 _tick_player_dots 均退化为壳。
    def _apply_dot(self, target: dict, source: dict | None, pdot: dict, logs: list) -> None:
        """给任意 actor 挂持续伤害（数据驱动 pdot 字段，玩家/怪通用）。
        容器：actor["debuffs"][type] = {"n": 层数, "mult": 全局倍率, "atk_mult": 强度倍率,
              "atk": 施法者强度快照, "matk": 施法者魔强快照, "hit_at": 挂上时刻}
        与敌方 debuffs 同构（层数/倍率语义一致）。层数叠加（n 累加，cap 10 防失控）。
        伤害强度快照 = source（施法者）面板——玩家给怪挂毒强度看玩家，怪给玩家挂毒强度看怪。"""
        try:
            if not target or not pdot:
                return
            _type = str(pdot.get("type") or "burn").strip()
            if _type not in ("poison", "burn", "bleed", "corros"):
                return
            _atk_mult = float(pdot.get("atk_mult", 1.0) or 1.0)
            _n = max(1, min(10, int(pdot.get("n", 1) or 1)))
            _mult = float(pdot.get("mult", 1.0) or 1.0)
            # 强度快照：以施法者面板为基准（_actor_stats_of 按 actor 字段路由，玩家/怪通用）
            try:
                _st = self._actor_stats_of(source) if source else {}
            except Exception:
                _st = source or {}
            _deb = target.setdefault("debuffs", {})
            _old = _deb.get(_type)
            if isinstance(_old, dict):
                _n = min(10, int(_old.get("n", 1) or 1) + _n)
            _deb[_type] = {
                "n": _n, "mult": _mult,
                "atk_mult": _atk_mult,
                "atk": int((_st or {}).get("atk", 0) or 0),
                "matk": int((_st or {}).get("matk", 0) or 0),
                "hit_at": self._now,
            }
            _is_pl = self._is_player_side(target)
            _icon_map = {"poison": "☠️", "burn": "🔥", "bleed": "🩸", "corros": "🧪"}
            _kname = {"poison": "中毒", "burn": "灼烧", "bleed": "流血", "corros": "腐蚀"}.get(_type, _type)
            _who = ("你" if _is_pl else f"【{target.get('name', '目标')}】")
            logs.append(f"{_icon_map.get(_type, '💥')} {_who}中了【{_kname}】（{_n} 层）！")
            # v178.1 事件驱动（v179 P2 升级通用 tick 卡）：目标首次带 dot → 给该 actor 挂
            # 一张 actor_dot 卡（uid = dot_<side>_<actor标识>，照 pet_tick 先例，幂等）。
            # 玩家/怪各有各的卡——同时中毒两张卡各自结算互不干扰（actor 无关）。
            # 结算后无 debuffs → handler keep=False → 卡自动移除（毒消失即停）。
            try:
                _uid = f"dot_{'p' if _is_pl else 'e'}_{id(target)}"
                _has = any(e.get("uid") == _uid for e in self.tick_effects)
                if not _has:
                    self.add_tick_effect("actor_dot", target, ACT_TICK, uid=_uid,
                                         source="dot")
            except Exception as _sw_e:
                _battle_warn('_apply_dot', _sw_e)
                pass
        except Exception as _sw_e:
            _battle_warn('_apply_dot', _sw_e)
            pass

    def _tick_actor_dots(self, actor: dict, logs: list, force: bool = False,
                         caster: dict | None = None) -> list:
        """v178.1 统一 DOT 结算：结算任意 actor（玩家/怪）身上的 debuffs——actor 无关。

        actor = 身上挂着 debuffs 的目标（玩家或怪物同一套逻辑）；
        caster = 施法者（提供强度面板/玩家被动乘区）。缺省时：
          - actor 是怪（class_name 空）→ caster 回落 self.player（玩家毒怪，现状语义）
          - actor 是玩家（有 class_name）→ 强度走 debuffs 快照（挂 dot 时存的施法者 atk/matk）
        五律按 actor 字段消费：怪/Boss 有 dot_res/adapt/immune_dots/is_boss → 抗性生效；
        玩家无这些字段 → 纯公式。落地按 actor 字段路由：玩家走 _damage_actor 承伤链，
        怪走 _enemy_mitigate + _boss_dmg_filter + _deal_damage。

        v138.2 五律（docs/COMBAT_ENRICH_v138.md §二）：
          律一 阈值递增 / 律二 每场上限+饱和 / 律三 跨阶段保留(_preserve_debuffs) /
          律四 真伤独立 / 律五 饱和阈值收敛。
        旧 debuffs 无 threshold/trigger_count/saturate_mult 字段 → 默认 0/1.0，不崩。

        - 伤害类型：毒/灼烧=magi，流血=phys；腐蚀=true（真伤）
        - force 参数兼容世界 Boss 显式结算入口（combat 层调用），无闸门语义
        """
        e = actor if actor is not None else (self.enemy or {})
        # v178.1 actor 无关：目标玩家 = actor 有 class_name（无则怪路径）
        _tgt_is_player = self._is_player_side(e)
        # v180F A7：不猜 caster——dot 强度以挂毒时存的施法者快照为准（_apply_dot 8246-8247），
        # 快照缺失（老档/直接构造）不回落 _last_player 猜当前玩家（可能是错的人——多人副本
        # 毒是 A 挂的、B 行动时结算），缺失即 0 强度只吃 max_hp 部分，随毒自然过期。
        _caster_is_player = self._is_player_side(caster) if caster is not None else False
        _tgt_name = "你" if _tgt_is_player else f"【{e.get('name', '目标')}】"
        deb = e.get("debuffs") or {}
        # v138.2 律二（控制侧）：e_buffs 里的控制效果达上限后直接失效（防 Boss 被无限控死）。
        _iname_map = {"poison": "中毒", "burn": "灼烧", "bleed": "流血", "corros": "腐蚀"}
        _eb2 = e.get("buffs") or {}
        for _ck in ("freeze", "stun", "sleep"):
            _cm = DOT_MAX_TRIGGER.get(_ck)
            if _cm is None or not _eb2.get(_ck):
                continue
            _cc = int(_eb2.get(f"{_ck}_trigger_count", 0) or 0)
            if _cc >= _cm:
                _eb2.pop(_ck, None)
                logs.append(f"🛡️ {_tgt_name}对{_iname_map.get(_ck, _ck)}产生了饱和抗性，控制不再生效！")
        if not deb:
            return logs
        max_hp = int(e.get("max_hp", 1) or 1)
        # v178.1 施法者强度：优先取目标 debuffs 里的施法者快照（挂 dot 时存的 atk/matk）——
        # 伤害跟"挂毒的人"，不跟"当前谁在结算"，玩家/怪同一语义（actor 无关核心）。
        # 快照缺失（老档/直接构造的 debuffs）→ 回落 caster 面板（玩家毒怪实时）。
        _atk = _matk = 0
        # 各类型层内快照（同类型不同层施法者不同时取最新挂的一层）
        for _dk in DOT_DEFS:
            _dd = (deb.get(_dk) or {})
            if _dd.get("atk") is not None:
                _atk = max(_atk, int(_dd.get("atk", 0) or 0))
                _matk = max(_matk, int(_dd.get("matk", 0) or 0))
        if _atk == 0 and _matk == 0 and caster is not None:
            try:
                _st = self._actor_stats_of(caster)
                _atk = max(0, int(_st.get("atk", 0) or 0))
                _matk = max(0, int(_st.get("matk", 0) or 0))
            except Exception:
                _atk = _matk = 0
        # 每层每刻混合公式：poison=atk×0.5+max_hp×1.5% / burn=matk×0.4+max_hp×1% / bleed=atk×0.6+max_hp×1.5%
        _atk_parts = {_k: _v["atk"] for _k, _v in DOT_DEFS.items()}
        _matk_parts = {_k: _v["matk"] for _k, _v in DOT_DEFS.items()}
        _hp_parts = {_k: _v["hp"] for _k, _v in DOT_DEFS.items()}
        _true_parts = {_k: bool(_v.get("true_dmg", False)) for _k, _v in DOT_DEFS.items()}
        _ctrl = ("freeze", "stun", "sleep")
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
            # 免疫：命中该类型直接移除（玩家可配 immune_dots=0 无感）
            if k in (e.get("immune_dots") or []):
                deb.pop(k, None)
                logs.append(f"🛡️ {_tgt_name}免疫{_iname}，减益消散了！")
                continue
            # v138.2 律二：饱和检查（目标有 DOT_MAX_TRIGGER 才生效——Boss 防无限控）
            _max_trig = DOT_MAX_TRIGGER.get(k)
            _saturated = bool(d.get("saturated", False)) or (
                _max_trig is not None and int(d.get("trigger_count", 0) or 0) >= _max_trig)
            if _saturated and k in _ctrl:
                if not d.get("saturated"):
                    d["saturated"] = True
                    logs.append(f"🛡️ {_tgt_name}对{_iname}产生了饱和抗性，控制不再生效！")
                continue
            if _saturated and not d.get("saturated"):
                d["saturated"] = True
                logs.append(f"⚗️ {_tgt_name}对{'腐蚀' if k == 'corros' else _iname}的异常积累已饱和，威力逐渐衰减！")
            mult = float(d.get("mult", 1.0) or 1.0)
            _sat_mult = float(d.get("saturate_mult", 1.0) or 1.0)
            if _saturated and _sat_mult < 1.0:
                mult *= _sat_mult
                _sat_tag = f"(饱和×{_sat_mult:.2f})"
            else:
                _sat_tag = ""
            # v1.2 总抗：基础抗性 + 减益适应（目标侧字段，玩家无 → 0）
            base_res = float(e.get("dot_res", 0) or 0)
            adapt_v = float((e.get("adapt") or {}).get(k, 0.0) or 0.0)
            res = min(DOT_RESIST_CAP, base_res + adapt_v)
            # 混合公式 + Boss/精英百分比打折（目标侧 is_boss/is_elite）
            atk_part = _atk * _atk_parts[k] + _matk * _matk_parts[k]
            _dot_type = (DOT_DEFS.get(k) or {}).get("type", "flat")
            # v180E：支持 per-debuff pct 覆盖——handler 显式写 d.pct 时用它替代 DOT_DEFS
            # 的 hp 系数（如词条"灼烧每刻 1.5%"真实生效）；未写则回落 DOT_DEFS 权威值。
            _dpct = d.get("pct")
            if _dpct is not None:
                _hp_part = max_hp * float(_dpct)
            else:
                _hp_part = max_hp * _hp_parts[k]
            if _hp_part > 0 and _dot_type in ("pct", "hybrid"):
                if e.get("is_boss") or e.get("role") == "boss" or e.get("is_elite"):
                    _hp_part *= DOT_BOSS_PCT_MULT
                _hp_part = min(_hp_part, max_hp * DOT_PCT_CAP)
            hp_part = _hp_part
            # v169.7 万毒归宗 poison_all_up（刺客毒线，caster 是玩家才查被动）
            _poison_all_mult = 1.0
            if k == "poison" and _caster_is_player:
                try:
                    for _pn_pa, _ps_pa in self._proc_pm(caster)["proc"].get("poison_all_up", []):
                        _poison_all_mult *= 1.0 + float(_ps_pa.get("mult", 0.35) or 0.35)
                        break
                except Exception as _sw_e:
                    _battle_warn('_tick_actor_dots', _sw_e)
                    pass
            p = int((atk_part + hp_part) * n * mult * _poison_all_mult * (1 - res))
            # v169.7 剧毒之触 poison_weaken（caster 玩家毒怪 → 怪减速降防）
            if k == "poison" and _caster_is_player and not _tgt_is_player:
                try:
                    _pw_list = self._proc_pm(caster)["proc"].get("poison_weaken", [])
                    if _pw_list and n >= int((_pw_list[0][1]).get("layers", 5) or 5):
                        for _pn_pw, _ps_pw in _pw_list:
                            _tgt_b = e.setdefault("buffs", {})
                            _tgt_b["spd_down"] = max(int(_tgt_b.get("spd_down", 0) or 0), int(_ps_pw.get("spd_down", 2) or 2))
                            _tgt_b["def_down"] = max(int(_tgt_b.get("def_down", 0) or 0), int(_ps_pw.get("def_down", 2) or 2))
                            _tgt_b["_weaken_spd_pct"] = max(float(_tgt_b.get("_weaken_spd_pct", 0) or 0), 0.30)
                            _tgt_b["_weaken_def_pct"] = max(float(_tgt_b.get("_weaken_def_pct", 0) or 0), 0.20)
                            logs.append("☠️ 剧毒之触：毒层 ≥5，敌人减速降防！")
                            break
                except Exception as _sw_e:
                    _battle_warn('_tick_actor_dots', _sw_e)
                    pass
            # v1.1 放血：目标当前生命 <30%（处决线）流血 ×2——必须在落地前翻倍
            _bleed_tag = ""
            if k == "bleed" and int(e.get("hp", 0) or 0) < max_hp * DOT_BLEED_DOUBLE_HP_PCT:
                p = int(p * 2)
                _bleed_tag = "(放血)"
            # v138.2 律四：真伤分支——绕过 _enemy_mitigate 的 def/mdef 削减，直走落地。
            # v177 actor 统一：怪物扣血/护盾吸收(halve)/死亡全由 _deal_damage→_damage_actor
            # 处理——不再先走 _boss_dmg_filter（其护盾逻辑 v177 已迁 _damage_actor，双吸）。
            if _true_parts.get(k):
                if _tgt_is_player:
                    try:
                        p = self._damage_actor(e, p, logs, source="dot", true_dmg=True)
                    except Exception as _sw_e:
                        _battle_warn('_tick_actor_dots', _sw_e)
                        pass
                else:
                    if p > 0:
                        self._deal_damage(p, logs, wake_sleep=False, target=e, true_dmg=True)
            else:
                # 伤害段：灼烧=magi 火抗 / 毒=magi / 流血=phys
                if _tgt_is_player:
                    # 玩家承伤：走 _damage_actor 完整减伤链
                    try:
                        p = self._damage_actor(e, p, logs, source="dot")
                    except Exception as _sw_e:
                        _battle_warn('_tick_actor_dots', _sw_e)
                        pass
                else:
                    if k == "burn":
                        dt = "magi"
                        p, _ = self._enemy_mitigate(p, p, "fire", logs, kind=K_MAGI, dot=True)
                    elif k == "poison":
                        dt = "magi"
                        p, _ = self._enemy_mitigate(p, p, None, logs, kind=K_MAGI, dot=True)
                    else:
                        dt = "phys"
                        p, _ = self._enemy_mitigate(p, 0, None, logs, kind=K_PHYS, dot=True)
                    if p > 0:
                        self._deal_damage(p, logs, wake_sleep=False, target=e)
            # v138.2 律一：阈值递增——每次触发后 threshold ×1.3（封顶 3.0），防无限复读
            _thr = float(d.get("threshold", 0.0) or 0.0)
            if _thr <= 0.0:
                _thr = 1.0  # 首触基准
            _thr = min(DOT_THRESHOLD_CAP, _thr * DOT_THRESHOLD_MULT)
            d["threshold"] = _thr
            # v138.2 律二：触发计数 +1，达上限置饱和标记（控制类不再结算已在上方处理）
            d["trigger_count"] = int(d.get("trigger_count", 0) or 0) + 1
            _tc = d["trigger_count"]
            if _max_trig is not None and _tc >= _max_trig:
                d["saturated"] = True
                if k not in _ctrl:
                    logs.append(f"⚗️ {_tgt_name}的{_iname}积累已达上限，进入饱和！")
            _mk_tag = ""
            _sat_tag2 = _sat_tag
            logs.append(f"{_icon_map.get(k, '💥')} {_tgt_name}{_kname_map.get(k, k)}发作！(剩余 {n - 1} 层){_mk_tag}{_bleed_tag}{_sat_tag2}")
            n -= 1
            if n <= 0:
                deb.pop(k, None)
                logs.append(f"💨 {_tgt_name}的{_kname_map.get(k, k)}消散了！")
            else:
                d["n"] = n
            # v138.2 律五：饱和收敛
            if d.get("saturated") and k not in _ctrl:
                _sm = float(d.get("saturate_mult", 1.0) or 1.0)
                d["saturate_mult"] = _sm * DOT_SATURATE_MULT
            # v1.2 适应回落（目标侧 adapt 字段）
            if k in ("poison", "burn") and not _tgt_is_player:
                _last = int(d.get("last_tick", d.get("last_round", 0)) or 0)
                if _last > 0 and self._tick_no() - _last >= 2:
                    _am = e.setdefault("adapt", {})
                    _am[k] = max(0.0, float(_am.get(k, 0.0) or 0.0) - DOT_ADAPT_DECAY_STEP)
            # 目标=怪 且被毒死 → 胜利（玩家被毒死不触发）
            if not _tgt_is_player and self._enemy_dead():
                self.result = "victory"
                death_text = ("毒发身亡" if k == "poison" else "灼烧致死" if k == "burn"
                              else "失血过多" if k == "bleed" else "腐蚀崩解")
                logs.append(f"🎉 你击败了【{e.get('name', '敌人')}】！({death_text})")
                break
        # v1.3 标记层与 dot 同生命周期（仅怪目标有 mark 语义）
        if not _tgt_is_player:
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
        # v178 E3b：阶段大招技能池（ult_every 触发时从这抽，需 ult_skills 配置才有效）
        e["_phase_ult_skills"] = list(phase_cfg.get("ult_skills") or [])
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
        _prev = self._p_tailwind_prev_energy()
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

    def _regen_needed(self, player: dict) -> bool:
        """v178.2 regen_tick 条件排入判定：玩家当前是否带"每刻效果"（A 类）。

        覆盖 _turn_start 原 A 类清单的**数据存在性**判定（不结算，只看有没有）：
        - 套装 4 件（圣光/永恒 regen、圣堂领域、神恩爆发、壁立千仞、双形态等）
        - 食物 HOT / 词条刻开始 / 特效装备 turn_start
        - 附魔 符文·治愈 / 被动 proc（turn_heal/team_regen/arcane_regen/arcane_intuition/…）
        - 核心资源 regen（游侠精力 +25/刻 等）/ 疾风余韵 / 迅捷之核增幅
        - 牧师信念衰减 / 歌者回声 / 亡灵祭仪
        无任何 A 类效果 → False → 不排 regen_tick（CTB 测试玩家 equipment={} 恒 False）。
        """
        try:
            if not player:
                return False
            # 套装 4 件/5 件效果（只认"每刻回血/充能/盾"类，攻击特效套装不需要 regen_tick）
            _s4 = E.set_bonus_4(player.get("equipment", {}))
            if _s4:
                for _eff in ("regen", "regen_strong", "holy_field_heal",
                             "divine_grace_burst", "hu_xiao_barrier"):
                    if _eff in _s4:
                        return True
            # 5 件套周期回蓝效果（night_mp_regen：星尘 5 件夜间回蓝等，数据驱动判定）
            try:
                if self._set_bonus_5_has_effect(player, "night_mp_regen"):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 词条刻开始（回春/冥想/晨曦祝福 等）
            try:
                if self._affix_effs(player, "__any_turn_start__"):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 食物持续效果
            try:
                if self._p_food_effects():
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 符文·治愈
            try:
                if self._enchant_lvl(self._enchant_effects(player), "regen"):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 被动 proc 族（turn_heal/team_regen/arcane_regen/arcane_intuition/
            # focus_regen_summon/undead_faith/faith_overload_heal/shaken_decay_half…）
            try:
                _pm = self._passive_map(player)["proc"]
                for _pk in ("turn_heal", "team_regen", "arcane_regen", "arcane_intuition",
                            "focus_regen_summon", "undead_faith", "faith_overload_heal"):
                    if _pm.get(_pk):
                        return True
                for _pn2, _ps2 in self._passive_map(player)["stat"]:
                    if _ps2.get("stat") == "spellblade_regen":
                        return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 核心资源刻回复（rd.regen > 0）
            try:
                _crd = E.core_resource_def(player.get("class_name", ""))
                if _crd and (float(_crd.get("regen", 0) or 0) > 0
                             or float(_crd.get("decay_per_tick", 0) or 0) > 0):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 疾风余韵词条（swift_tailwind，上刻精力≥80 → 本刻 +10）
            try:
                if "swift_tailwind" in self._equip_affix_ids(player):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 资源增幅（迅捷之核 natural 回额外）
            try:
                if self._amp_resource(player, "regen"):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # 歌者回声层数 / 双形态活跃（状态机维护成本）
            try:
                if self._echo_layers() > 0:
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            try:
                from .core.battle_modes import dual_form_active
                if dual_form_active(player):
                    return True
            except Exception as _sw_e:
                _battle_warn('_regen_needed', _sw_e)
                pass
            # vent/focus 状态机在行动语义（B 类）里保留，不进 regen_tick
            return False
        except Exception:
            return False

    def _ensure_regen_effects(self, player: dict):
        """v179 P1f：扫描玩家周期效果源 → 挂/收通用 tick 条件卡（幂等）。

        每个效果源 → 对应 handler kind 的常驻卡（uid 固定 "regen_<kind>"）：
          set_heal/set_holy   ← 套装 4 件回血/圣堂/神恩/壁立
          stardust_mana       ← 星尘 5 件
          rune_regen          ← 符文·治愈
          passive_heal        ← 被动 turn_heal/team_regen/focus_regen_summon
          mech_charge         ← 奥术/魔剑充能被动
          core_regen          ← 职业核心资源 regen
          faith_decay         ← 牧师信念
          echo_heal           ← 歌者回声层
          affix_food_we       ← 词条/食物foodfx/武器特效（保守常驻，内部判空转）
        效果源消失 → 卡不续（handler keep=False 自动移除）；本方法幂等，可反复调。
        """
        try:
            if not player or self.result or self._actor_dead(player):
                return
        except Exception:
            return
        _want: set = set()
        try:
            _s4 = E.set_bonus_4(player.get("equipment", {}))
            if _s4:
                for _eff in ("regen", "regen_strong"):
                    if _eff in _s4:
                        _want.add("set_heal")
                for _eff in ("holy_field_heal", "divine_grace_burst", "hu_xiao_barrier"):
                    if _eff in _s4:
                        _want.add("set_holy")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        try:
            # 5 件套周期回蓝效果（night_mp_regen：星尘 5 件夜间回蓝，数据驱动判定）
            if self._set_bonus_5_has_effect(player, "night_mp_regen"):
                _want.add("stardust_mana")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        try:
            if self._enchant_lvl(self._enchant_effects(player), "regen"):
                _want.add("rune_regen")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        try:
            _pm = self._passive_map(player)["proc"]
            if _pm.get("turn_heal") or _pm.get("team_regen") or _pm.get("focus_regen_summon"):
                _want.add("passive_heal")
            if _pm.get("arcane_regen") or _pm.get("arcane_intuition"):
                _want.add("mech_charge")
            for _pn2, _ps2 in self._passive_map(player)["stat"]:
                if _ps2.get("stat") == "spellblade_regen":
                    _want.add("mech_charge")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        try:
            _crd = E.core_resource_def(player.get("class_name", ""))
            if _crd and float(_crd.get("regen", 0) or 0) > 0:
                _want.add("core_regen")
            if _crd and _crd.get("key") == "faith":
                _want.add("faith_decay")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        try:
            if self._echo_layers() > 0:
                _want.add("echo_heal")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        # 词条/食物/武器特效：保守常驻（原 _regen_needed 对这些也是"有任一即排"）
        try:
            _has_affix = False
            try:
                _has_affix = bool(self._affix_effs(player, "__any_turn_start__"))
            except Exception:
                _has_affix = False
            if _has_affix or self._p_food_effects():
                _want.add("affix_food_we")
        except Exception as _sw_e:
            _battle_warn('_ensure_regen_effects', _sw_e)
            pass
        # 挂卡（幂等：已存在跳过）——间隔 ACT_TICK=1s，周期效果统一 1 秒一跳
        for _kind in _want:
            _uid = f"regen_{_kind}"
            _has = any(e.get("uid") == _uid for e in self.tick_effects)
            if not _has:
                self.add_tick_effect(_kind, player, ACT_TICK, uid=_uid, source="regen")
        # 收卡：已挂但玩家不再需要（保底，正常由 handler keep=False 移除）
        _keep_uids = {f"regen_{_k}" for _k in _want}
        for _e in list(self.tick_effects):
            if _e.get("source") == "regen" and _e.get("uid") not in _keep_uids:
                self.tick_effects.remove(_e)

    def _tick_regen(self, player: dict, logs: list) -> list:
        """v179 P1：每刻效果结算器（兼容壳）——依次调通用 tick handler。

        原 v178.2 A 类硬编码逻辑已全拆为 _TICK_HANDLERS 注册的效果族 handler
        （set_heal/set_holy/rune_regen/stardust_mana/passive_heal/mech_charge/
        core_regen/faith_decay/echo_heal/affix_food_we），本方法保留签名：
        直接调 _tick_regen 的旧测试（stage5_resources/v1302c/regen_tick 等）零改动。
        每个 handler 返回 (logs, keep)；此处忽略 keep（常驻调用，由 _ensure_regen_effects
        管理卡片生命周期）。
        """
        try:
            if not player:
                return logs
        except Exception:
            return logs
        _log_out = []
        # 按注册顺序跑全部周期效果族 handler（数据驱动：kind 查表，无硬编码分支）
        for _kind in ("set_heal", "set_holy", "rune_regen", "stardust_mana",
                      "passive_heal", "mech_charge", "core_regen",
                      "faith_decay", "echo_heal", "affix_food_we"):
            _fn = _TICK_HANDLERS.get(_kind)
            if not _fn:
                continue
            try:
                _h_logs, _ = _fn(self, player, {"kind": _kind, "data": {}}, _log_out)
                if _h_logs:
                    _log_out += _h_logs
            except Exception:
                continue
        return _log_out

    def _turn_start(self, player: dict) -> list:
        """刻开始：v10 套装每刻回复 + 破绽条衰减（v151）。DOT 已事件驱动（v178.1），不在此结算。"""
        logs = []
        # v178.1：_turn_start 收到实际行动玩家 → 缓存为 _last_player（dot_tick 事件结算强度用；
        # 否则事件在 player_turn 设 _last_player 之前触发，毒伤按空面板算=0）
        if player:
            try:
                self._last_player = player
            except Exception as _sw_e:
                _battle_warn('_turn_start', _sw_e)
                pass
        # v178.1 事件驱动保险丝（v179 P2 升级通用卡）：玩家行动开头扫描带 debuffs 的
        # actor（玩家/当前主敌），若已挂 dot 但没有对应 actor_dot 卡（直接写 debuffs 的
        # 旧路径/老档/新挂载漏排）→ 补挂卡。幂等：已有该 actor 的卡则跳过。
        try:
            for _dt_cand in [player] + list(self.enemies or []):
                if not _dt_cand or not (_dt_cand.get("debuffs") or {}):
                    continue
                _dt_dots = {_k for _k in _dt_cand["debuffs"] if _k in DOT_DEFS}
                if not _dt_dots:
                    continue
                _is_pl = self._is_player_side(_dt_cand)
                _uid = f"dot_{'p' if _is_pl else 'e'}_{id(_dt_cand)}"
                _has_ev = any(e.get("uid") == _uid for e in self.tick_effects)
                if not _has_ev:
                    self.add_tick_effect("actor_dot", _dt_cand, ACT_TICK, uid=_uid,
                                         source="dot")
        except Exception as _sw_e:
            _battle_warn('_turn_start', _sw_e)
            pass
        # v178.2 regen 保险丝（v179 升级为通用 tick 卡）：玩家行动开头扫描 A 类每刻效果源，
        # 挂/收通用 tick 条件卡（regen_<kind>）。断线恢复/副本 act 重建 Battle 后首次行动
        # 触发挂卡；效果源消失 → 卡由 handler keep=False 自动移除。幂等可反复调。
        try:
            if player and not self._enemy_dead() and not self._actor_dead(player):
                self._ensure_regen_effects(player)
        except Exception as _sw_e:
            _battle_warn('_turn_start', _sw_e)
            pass
        # v151 破绽断链修复（引擎差距报告 P0）：turn_start_bars 此前从未被调用——
        # 拳师破绽条（shaken）的每刻衰减 4/免疫期递减实际不跑。刻开始统一衰减+触发检查。
        try:
            from .core.battle_bars import turn_start_bars, bar_def
            _bd = None
            _trig = turn_start_bars(self.enemy, logs) or []
            for _bk in _trig:
                # 触发效果：skip_turn → 敌方跳过下刻行动（由 _enemy_turn 消费 immune_turns）
                _bd = bar_def(_bk) or {}
                if (_bd.get("trigger_effect") or "") == "skip_turn":
                    logs.append(f"💢 破绽触发！敌方即将失去行动！")
            # v169.7 破绽感知 shaken_decay_half（拳师攻线）：破绽衰减减半（−1.7/s → −0.85/s）——
            # turn_start_bars 已按配置衰减 1.7，这里把半衰量回补（净效果 −0.85）
            try:
                for _pn_dh, _ps_dh in self._proc_pm(player)["proc"].get("shaken_decay_half", []):
                    _eb_sh = self.e_buffs.get("shaken")
                    if isinstance(_eb_sh, dict):
                        _decay_full = float((_bd or {}).get("decay_per_turn", 0) or 0) or 1.7
                        _eb_sh["val"] = int(_eb_sh.get("val", 0) or 0) + int(_decay_full / 2)
                    break
            except Exception as _sw_e:
                _battle_warn('_turn_start', _sw_e)
                pass
        except Exception as _sw_e:
            _battle_warn('_turn_start', _sw_e)
            pass
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
                    _cur = float(self._p_res().get(_df_key, 0) or 0)
                    if _cur >= _mc:
                        self._p_res()[_df_key] = _cur - _mc
                        logs.append(f"⚡【{_dfd.get('form', '形态')}】维持消耗 {_mc}（{self._p_res().get(_df_key, 0)}）")
                    # 强制回基础形态
                    if dual_form_force_return(player, int(self._p_res().get(_df_key, 0) or 0)):
                        dual_form_exit(player, logs)
                        logs.append("⚠️ 力量不支，被迫回到常态！")
        # vent：满值强制排气（游侠精力 100 / 星语者猎印 5）
        _vd = vent_def(player)
        if _vd:
            _v_key = _vd.get("key", "energy")
            _v_cur = int(self._p_res().get(_v_key, 0) or 0)
            if vent_should_trigger(player, _v_cur):
                _vr = vent_apply(player, logs)
                self._p_res()[_v_key] = int(_vr.get("reset_to", 0) or 0)
                logs.append(f"💨 气息满溢，自动排气！(重置为 {_vr.get('reset_to', 0)})")
        # focus：专注计时（额外资源 + 超时退出）
        _fd = focus_def(player)
        if _fd:
            _ft = focus_tick(player, logs)
            if _ft.get("gain"):
                _f_key = _fd.get("key", "element")
                _f_gain = int(_ft["gain"])
                # 专注额外资源（走 _res_gain 带上限）
                _f_before = int(self._p_res().get(_f_key, 0) or 0)
                self._p_res()[_f_key] = self._res_gain(player, _f_key, _f_gain)
                if int(self._p_res().get(_f_key, 0) or 0) > _f_before:
                    logs.append(f"🧘 专注积累 +{_f_gain}（{self._p_res().get(_f_key, 0)}）")
        return logs

    def _end_round(self, dt: float | None = None):
        """v152 时刻制：推进战斗时刻（替代旧"刻结束递减"）。
        兼容壳：保留 _end_round 函数名（外部大量调用），内部 = _advance_time(dt)。
        dt 缺省 = ACT_TICK（一次标准行动间隔）。真正的时间流逝由 _advance_time 处理。
        v152 彻底化：不再有"每刻 -1"，一切按绝对时刻 expire_at/ready_at 到期。"""
        self._advance_time(dt if dt is not None else ACT_TICK)

    def _decay_buff_table(self, tbl: dict, is_player_bag: bool):
        """v180G B5：单 buff 表按 _now 时刻衰减（_advance_time 对全场 actor 表调用）。

        is_player_bag=True 时跳过防御型受击计数 buff（由 _damage_actor 受击递减）。
        控制类/一次性/元素印记/dict bar 各有语义不在时刻递减。
        """
        for k in list(tbl):
            v = tbl[k]
            # 控制类 buff：行动级消费，不在时刻递减（与旧语义一致）
            if k in ("stun", "freeze"):
                continue
            # 元素印记：层数标记，触发反应清除
            if k in ("fire_mark", "ice_mark", "thunder_mark"):
                continue
            # 一次性 buff：攻击消费，不在时刻递减
            if k in ("next_atk_up", "buff_phys_next", "stealth", "arcane_echo", "oath_blade_next", "we_oath"):
                continue
            # reduce_all/shield：特殊语义，不按 int 递减
            if k in ("reduce_all", "reduce", "shield"):
                continue
            # bar 状态（dict）：由 battle_bars 自行衰减
            if isinstance(v, dict):
                continue
            # 防御型 buff（受击计数）：由 _damage_actor 受击递减
            if is_player_bag and k in (self._p_buff_hits() or {}):
                continue
            # v152：buff 值兼容三种形态——expire_at(时刻)、turns(刻 int)、原始 int(视为剩余刻)
            if isinstance(v, dict) and "expire_at" in v:
                if self._now >= float(v["expire_at"]):
                    del tbl[k]
                continue
            if isinstance(v, dict) and "turns" in v:
                if self._now >= float(v["turns"]) * ACT_TICK:
                    del tbl[k]
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                # 旧 int = 剩余刻数 → 换算时刻到期
                if self._now >= float(v) * ACT_TICK:
                    del tbl[k]

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
        # ---- buff 到期检查：同时间轴全场 actor（焦点玩家 + 副本全体玩家权威 buffs + 敌方各自 dict）----
        # v180G B4 修正：原只扫 (p_buffs, e_buffs)——e_buffs 是主怪别名，副怪 buffs 不衰减；
        # v180G B5 修正（鱼鱼纠正）：副本共享同一时间轴（挂机全体等、超时自动防御），
        # 全体参战玩家的 buffs 必须一起按 _now 衰减——非焦点玩家 buff 不能"冻结"，
        # 否则敌方打他时读到过期 buff 仍生效。
        _pbag = self._p_buffs_bag()
        _tbls = [_pbag] + [u.setdefault("buffs", {}) for u in (self.enemies or [])]
        # 副本权威层 st["p_buffs"]（每玩家一份；野外无 _st 跳过）
        try:
            _pb_st = (self._st or {}).get("p_buffs")
            if isinstance(_pb_st, dict):
                _tbls += [v for v in _pb_st.values() if isinstance(v, dict)]
        except Exception:
            pass
        for tbl in _tbls:
            self._decay_buff_table(tbl, tbl is _pbag)
        # v113.1：团队减伤 buff 独立计时（reduce_all 的到期）
        if self._p_buffs_bag().get("reduce_all") is not None and self._now >= float(self._p_reduce_all_left() or 1) * ACT_TICK:
            self._p_buffs_bag().pop("reduce_all", None)
            self._p_set_reduce_all_left(0)
        # v162：单人减伤 reduce 独立计时（铁壁/铜墙等，百分比存 p_buffs["reduce"]）
        if self._p_buffs_bag().get("reduce") is not None and self._now >= float(self._p_reduce_left() or 1) * ACT_TICK:
            self._p_buffs_bag().pop("reduce", None)
            self._p_set_reduce_left(0)
        # v101.28d 护盾到期：各来源独立 expire_at
        for key in list(self._p_shields_bag()):
            sh = self._p_shields_bag()[key]
            # 兼容旧 {"turns"} → expire_at
            if "turns" in sh and "expire_at" not in sh:
                sh["expire_at"] = self._now + max(1, int(sh.get("turns", 1))) * ACT_TICK
                sh.pop("turns", None)
            if self._now >= float(sh.get("expire_at", 0) or 0):
                del self._p_shields_bag()[key]
        # v130.2 资源增幅 turns_left 衰减（hits 制由 _amp_resource 出手命中逐次扣）→ 到期清
        _amp_m = (self._p_eff() or {}).get("amps")
        if _amp_m:
            for _ak in list(_amp_m):
                _a = _amp_m[_ak]
                if not isinstance(_a, dict):
                    continue
                if int(_a.get("turns_left", 0) or 0) > 0:
                    # 换算：turns_left 刻 → 到期时刻
                    if self._now >= float(_a.get("turns_left", 0)) * ACT_TICK:
                        _a["turns_left"] = 0
                if int(_a.get("turns_left", 0) or 0) <= 0 and int(_a.get("hits_left", 0) or 0) <= 0:
                    del _amp_m[_ak]
            if not _amp_m:
                self._p_eff().pop("amps", None)
        # v140 波3.2：弱点击破/连携增幅 时刻到期
        for _pkey in ("vuln", "dot_amp"):
            _pe = (self._p_eff() or {}).get(_pkey)
            if isinstance(_pe, dict) and int(_pe.get("turns_left", 0) or 0) > 0:
                if self._now >= float(_pe.get("turns_left", 0)) * ACT_TICK:
                    self._p_eff().pop(_pkey, None)
        # CD / 特效 CD / 星辉壁垒（惰性清除）
        self._tick_cooldowns()
        # v130.2d 疾风余韵：时刻推进后记录精力（供下一次判定自然回复）
        self._p_set_tailwind_prev_energy(int(self._p_res().get("energy", 0) or 0))
        # v130.2f2 满溢转盾冷却：时刻制下按冷却时间重置（简化：每次推进后允许再次转盾，
        # 真正的"每刻限 1 次"语义由 _overflow_shield_cd 在转盾瞬间置位并靠 CD 控制频率）
        self._p_set_overflow_shield_cd(False)
        # v179 通用 tick 效果：纯时间推进（无事件）也会到期的周期/持续效果条目
        # （防御/等待/收招等 dt 推进路径——不进 _process_until 事件循环，这里补处理）
        if self.tick_effects:
            try:
                _pl_now = self.player or {}
                self._process_tick_effects([], _pl_now)
            except Exception as _sw_e:
                _battle_warn('_advance_time', _sw_e)
                pass

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
                if self._p_buffs_bag().get("pene_magi_pot"):
                    pct = min(1 - (1 - pct) * 0.85, 0.6)
                return pct, flat
            pct = min(float(st.get("pene_phys", 0) or 0), 0.6)
            flat = max(int(st.get("pene_flat", 0) or 0), 0)
            if self._p_buffs_bag().get("pene_pot"):
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

    def _target_dodge_check(self, logs: list) -> bool:
        """v105 怪物闪避判定：怪物闪避率 × (1 - 我方精准)（精准上限 60%），闪避率上限 30%。
        命中判定成功追加闪避日志并返回 True（调用方跳过本次伤害结算）。
        v169.7 修 #132：判定目标用 _active_target（指定打 a2 时判 a2 闪避），无活跃目标回退主目标。"""
        try:
            _mob = getattr(self, "_active_target", None) or self.enemy or {}
            mon_dodge = min(float(_mob.get("dodge", 0) or 0), 0.30)
            if mon_dodge <= 0:
                return False
            my_hit = 0.0
            try:
                my_hit = min(float(self._player_stats(self.player).get("precise", 0) or 0), 0.60)
            except Exception:
                my_hit = 0.0
            eff = mon_dodge * (1 - my_hit)
            if eff > 0 and random.random() < eff:
                logs.append(f"💨 {_mob.get('name', '怪物')} 闪避了攻击！")
                return True
        except Exception as _sw_e:
            _battle_warn('_target_dodge_check', _sw_e)
            pass
        return False

    def _player_side_aoe_pool(self) -> list:
        """v180F 清3：玩家侧 AOE 目标池——敌方 AOE 打玩家时选谁。

        野外 = [self.player]（单目标）；副本 = player + allies 存活（与 _pick_enemy_target
        目标池一致）。随从：hidden/untargetable（隐身宠物/纯挡刀）不进池；eats_aoe=True 的
        随从（藤蔓守卫/古树守卫等前排挡刀）进池（v151 设计意图：它们吃 AOE）。
        """
        pool = []
        _pl = getattr(self, "player", None) or {}
        if _pl.get("hp", 0) > 0 and (_pl.get("class_name") or _pl.get("qq_id") or _pl.get("name")):
            pool.append(_pl)
        for _a in (getattr(self, "allies", None) or []):
            if _a is _pl:
                continue  # 焦点已在上面
            if _a.get("hp", 0) > 0:
                pool.append(_a)
        # eats_aoe 随从（前排挡刀型召唤物吃 AOE；hidden/untargetable 宠物不吃）
        for _c in (getattr(self, "companions", None) or []):
            if _c.get("hp", 0) > 0 and _c.get("eats_aoe") and not _c.get("hidden") and not _c.get("untargetable"):
                pool.append(_c)
        return pool or ([_pl] if _pl else [])

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
                    _atk = self._infer_atk(t_dmg, _tdef)  # v180E 统一反推
                    t_dmg = max(1, int(E.calc_damage(_atk, _tdef, variance=0)))
                except Exception as _sw_e:
                    _battle_warn('_aoe_damage', _sw_e)
                    pass
            # 击杀结算当前目标（打断钩子 + 防御过滤）
            dealt = self._deal_damage(t_dmg, logs, target=t, source=source or self._last_hitter)
            logs.append(f"💥 对【{t.get('name', '敌人')}】造成 {dealt} 点伤害！")
            if dealt > 0 and t is main:
                main_hit = dealt
        return main_hit

    def _add_hate(self, player: dict, amount: int) -> None:
        """v173.5 全层仇恨：battle 内部产生的伤害（如守护姿态盾牌反击）累计进副本仇恨表。
        副本战（from_state 注入 _st 含 threat）才生效；野外/单人 _st 无 threat 空转。"""
        if not amount or not self._st:
            return
        try:
            _thr = self._st.get("threat")
            if not isinstance(_thr, dict):
                return
            _q = str(player.get("qq_id") or player.get("uid") or "")
            if _q:
                _thr[_q] = int(_thr.get(_q, 0) or 0) + int(amount)
        except Exception as _sw_e:
            _battle_warn('_add_hate', _sw_e)
            pass

    def _deal_damage(self, dmg: int, logs: list, wake_sleep: bool = True, target=None, source=None,
                      true_dmg: bool = False, attacker: dict | None = None) -> int:
        """对敌方单位造成伤害（§3.2）。返回实际对目标造成（或其 HP 被扣）的伤害。

        - target：目标单位 dict；None=当前玩家活跃目标(_active_target)或主目标(self.enemy)。
        - attacker：本次伤害的来源 actor（v180-C S3 actor 化——谁攻击吃谁的被动）。
          None = 玩家本人（兼容全部现有调用点：技能/普攻/AOE/反伤默认玩家攻击）。
          宠物 actor/随从 actor 攻击时传自己 → 乘区读宠物自身被动（无被动=无加成），
          不再白嫖玩家猎印/魂标/破绽/挽歌（v169.7 乘区）。
        - 删除旧"援军挡刀吸收"逻辑（站位天然承担）：每单位独立扣血。
        - 主动伤害>0 且目标蓄力中 → 打断（打断钩子，返还 50%MP 见 _interrupt_charging）。
        - wake_sleep：dot 传 False（持续伤害不打醒睡眠、也不打断蓄力）。
        F1 P1-4：PVP 防御生效——目标防御中(defending)时伤害减半。"""
        if target is None:
            target = getattr(self, "_active_target", None) or self.enemy
        if dmg <= 0:
            return 0
        # ---- v169.7 通用伤害乘区（读敌方标记/破绽 + 已学被动；只影响带机制/已学被动玩家）----
        # v180-C S3 actor 化：乘区读"来源 actor"（attacker）的被动——宠物/随从 actor
        # 攻击时读它们自身被动（宠物无被动 → 无乘区），不再无条件吃 self.player。
        # 缺省 attacker=None = 玩家攻击（全部旧调用点行为不变）。
        _atk_actor = attacker if attacker is not None else (self.player or {})
        try:
            _db_t = target.get("debuffs") or {}
            _mult_pas = 1.0
            _tags_pas = []
            _pl_d = _atk_actor
            _pm_d = self._proc_pm(_pl_d) if _pl_d else {"proc": {}}
            # 猎印
            _hm = int(_db_t.get("hunt_mark", 0) or 0)
            if _hm > 0:
                _hm_pct = 0.08
                for _pn, _ps in _pm_d["proc"].get("hunt_mark_up", []):
                    _hm_pct += float(_ps.get("per_layer", 0.06) or 0.06)
                    break
                _mult_pas *= 1.0 + _hm_pct * _hm
                _tags_pas.append(f"🎯猎印x{round(1 + _hm_pct * _hm, 2)}")
            # 灵魂标记
            _sm = int(_db_t.get("soul_mark", 0) or 0)
            if _sm > 0:
                _sm_pct = 0.06
                for _pn, _ps in _pm_d["proc"].get("soul_mark_cap", []):
                    _sm_pct += float(_ps.get("per_layer", 0.08) or 0.08)
                    break
                _mult_pas *= 1.0 + _sm_pct * _sm
                _tags_pas.append(f"💀魂标x{round(1 + _sm_pct * _sm, 2)}")
            # 气力之心（敌方破绽条 ≥15）
            _sb_sh = (target.get("buffs") or {}).get("shaken")
            if isinstance(_sb_sh, dict):
                for _pn, _ps in _pm_d["proc"].get("shaken_awareness", []):
                    if int(_sb_sh.get("val", 0) or 0) >= int(_ps.get("bar_at", 15) or 15):
                        _mult_pas *= 1.0 + float(_ps.get("mult", 0.20) or 0.20)
                        _tags_pas.append("🧠破绽x1.2")
                    break
            # 破绽·极 broken_extend：破防（被震慑免疫期）时 全队增伤 +50%
            if isinstance(_sb_sh, dict) and int(_sb_sh.get("trigger_count", 0) or 0) > 0 \
                    and int(_sb_sh.get("immune_turns", 0) or 0) > 0:
                for _pn_be2, _ps_be2 in _pm_d["proc"].get("broken_extend", []):
                    _mult_pas *= 1.0 + float(_ps_be2.get("broken_mult", 0.50) or 0.50)
                    _tags_pas.append(f"💢破防x{round(1 + float(_ps_be2.get('broken_mult', 0.50) or 0.50), 2)}")
                    break
            # 挽歌·极（敌方负面种数）
            for _pn, _ps in _pm_d["proc"].get("dirge_debuff_dmg", []):
                _kinds = self._enemy_debuff_kind_count()
                _pct_e = min(float(_ps.get("per_debuff", 0.04) or 0.04) * _kinds,
                             float(_ps.get("cap", 0.40) or 0.40))
                if _pct_e > 0:
                    _mult_pas *= 1.0 + _pct_e
                    _tags_pas.append(f"🎵挽歌x{round(1 + _pct_e, 2)}")
                break
            if _mult_pas != 1.0:
                dmg = max(1, int(dmg * _mult_pas))
                if _tags_pas:
                    logs.append("·".join(_tags_pas))
        except Exception as _sw_e:
            _battle_warn('_deal_damage', _sw_e)
            pass
        # v136 等级压制：玩家 vs 怪物等级差伤害修正（PVE 生效，PVP 不压；按目标自身等级实时算，
        # 多目标阵列每怪等级不同也能正确压制）。双向曲线（鱼鱼拍板：增伤不封顶，曲线自然延伸）：
        #   低打高：低 1-3 级 ×0.95/级，低 4+ 级 ×0.90/级（指数曲线，封顶 ×0.30 防归零）
        #   高打低：每高 1 级 ×1.02 连乘（指数曲线，不封顶——等级越高碾压越强）
        # v180-C S3 fix（审计）：压制基准用攻击者（attacker）自身等级——宠物 actor 有
        # level 用宠物级；无 level 的随从（召唤物按玩家属性生成）回落玩家等级（原行为）。
        # 守卫保留"有可用攻击者等级才压制"（原 self.player 条件语义：测试/DOT 无玩家不压）。
        _atk_lv = None
        if attacker is not None:
            _atk_lv = attacker.get("level")
        if _atk_lv is None:
            _atk_lv = (self.player or {}).get("level")
        if self.btype != "pvp" and _atk_lv and target.get("lv"):
            try:
                _plv = int(_atk_lv or 0)
                _diff = int(target.get("lv", 0) or 0) - _plv
                if _diff > 0:
                    _mult = 1.0
                    for _i in range(min(_diff, 10)):
                        _mult *= (0.95 if _i < 3 else 0.90)
                    dmg = max(1, int(dmg * max(0.30, _mult)))
                elif _diff < 0:
                    dmg = max(1, int(dmg * (1.02 ** min(-_diff, 50))))
            except Exception as _sw_e:
                _battle_warn('_deal_damage', _sw_e)
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
        # v177 actor 统一：怪物扣血/死亡/on_taken 全走 _damage_actor（怪物模式）
        # 前置（乘区/等级压制/defending/sleep/打断）已在此函数上方完成，此处只做落地
        _real_dmg = self._damage_actor(target, dmg, logs, source=str(source or "玩家"),
                                       true_dmg=true_dmg, wake_sleep=wake_sleep)
        return _real_dmg


    def _summon_minions(self, n: int = 1) -> list:
        """v2（§7.2）：敌方援军入 enemies 阵列（rank1/reach1，站位天然挡刀）。
        保持 e_minions 旧字段同步（命令层/instance 展示与持久化兼容）。
        每只血量=Boss 20%、攻击=Boss 40%。"""
        # v163 召唤机制定稿（策划案 04 章二.5）：援军场上上限 3 只（含开战自带爪牙）。
        # 满员时不再召唤（机制召唤/技能召唤同走本函数，统一生效）。
        # 上限 3 = 数值设计：1 Boss + 3 爪牙 = 4 前排已是队伍可处理上限；防无限堆怪拖死。
        try:
            from .core.battle_mech import SUMMON_MINION_CAP
        except Exception:
            SUMMON_MINION_CAP = 3
        if n > 0:
            _alive_min = [u for u in self.enemies if u.get("hp", 0) > 0 and u.get("is_minion")]
            _cap = int(SUMMON_MINION_CAP or 3)
            _room = max(0, _cap - len(_alive_min))
            if _room <= 0:
                return []
            n = min(n, _room)
        e = self.enemy or {}
        # v163：命名基准用 Boss 本体名（self.enemy 可能被前排爪牙顶替导致名字叠"爪牙的爪牙"）
        _boss_name = ""
        for _u in self.enemies:
            if _u.get("is_boss") and not _u.get("is_minion"):
                _boss_name = _u.get("name") or ""
                break
        if not _boss_name:
            _boss_name = e.get("name", "首领")
        created = []
        base_uid = len(self.enemies)
        # v163 召唤物=同图小怪模板（鱼鱼拍板）：优先读副本 inst.minions[].monster 模板
        # build_monster 构建（如哥布林营地=哥布林守卫 lv15 ≈ 564HP），非 Boss 比例缩放。
        # 老数据（无 inst 配置/非 instance 战斗）回落 Boss×0.2（v101.28l 旧值，仅兜底）。
        _tpl = None
        _tpl_name = "爪牙"
        # v163: 副本战斗里 Boss 单位带 map=inst_id（build_monster area=instance）。
        # 从阵列找 Boss 本体（is_boss/is_elite 或首个带 inst_ map 的单位）拿 inst 配置；
        # 野外（无 inst 配置）回落 Boss×0.2。
        _inst_id = ""
        for _u in self.enemies:
            _um = str(_u.get("map") or "")
            if _um.startswith("inst_"):
                _inst_id = _um
                break
        if _inst_id:
            try:
                from .data.instances import INSTANCES as _INSTS
                _mcfg = (_INSTS.get(_inst_id) or {}).get("minions") or []
                if _mcfg and _mcfg[0].get("monster") and isinstance(_mcfg[0]["monster"], (list, tuple)) and len(_mcfg[0]["monster"]) >= 6:
                    _tpl = _mcfg[0]["monster"]
                    _tpl_name = _mcfg[0].get("name", _mcfg[0]["monster"][1] if len(_mcfg[0]["monster"]) > 1 else "爪牙")
            except Exception as _sw_e:
                _battle_warn('_summon_minions', _sw_e)
                pass
        for i in range(n):
            m = None  # v163 修复：非模板路径下 m 未定义 → UnboundLocalError（test_v83_boss_mech 抓包）
            if _tpl is not None:
                try:
                    m = C.build_monster(_tpl, {"id": _inst_id or "x", "name": _inst_id or "x",
                                               "area": "instance"})
                except Exception:
                    m = None
                if m:
                    m = dict(m)
                    m["uid"] = f"e_min_{base_uid + i}"
                    m["side"] = "enemy"
                    m["name"] = f"{_boss_name}的{_tpl_name}"
                    m["rank"] = 1
                    m["reach"] = 1
                    m["is_minion"] = True
                    m["mech"] = ""
                    m["mod"] = ""
                    m["ct"] = -float(m.get("spd", 1) or 1)
                else:
                    m = None
            if m is None:
                # 兜底：Boss×0.2（旧值，仅非模板/老数据路径）
                m = {
                    "uid": f"e_min_{base_uid + i}",
                    "side": "enemy",
                    "rank": 1,
                    "reach": 1,
                    "name": f"{_boss_name}的爪牙",
                    "hp": int(e.get("max_hp", 1) * 0.20),
                    "max_hp": int(e.get("max_hp", 1) * 0.20),
                    "atk": int(e.get("atk", 0) * 0.40),
                    "matk": int(e.get("matk", 0) * 0.40),
                    "def": int(e.get("def", 0) * 0.40),
                    "mdef": int(e.get("mdef", 0) * 0.40),
                    "spd": int(e.get("spd", 0) or 1),
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
    def _spawn_companion(self, cfg: dict, player: dict, logs: list) -> dict | None:
        """v180-C S2 装配统一：随从 actor 单一装配函数（设计文档 §3.4）。

        技能召唤（_summon_entity）与药水召唤（potion_effects.eff_summon）共用本函数，
        消除两份手写实体装配。cfg 字段（数据驱动，全部可选带默认）：
          tid/name/icon           —— 实体标识（tid 必填）
          hp_ratio/atk_ratio/def_ratio —— 相对玩家 max_hp/atk/def 的比例（生成时算一次）
          dmg_type/rank/reach     —— 伤害类型/站位/射程
          bodyguard/absorb_once   —— 挡刀（bodyguard>0 → guard 配置；absorb_once 1 次后消失）
          aura_atk_all            —— 常驻全队攻击光环（挂 p_buffs）
          eats_aoe                —— 吃 AOE（特性字段保留）
          summon_power            —— 是否吃 summon_power 强化（技能召唤 True；药水 False，默认 False）
        """
        tid = cfg.get("tid", "")
        if not tid:
            return None
        st = self._player_stats(player)
        sp = float(cfg.get("summon_power", False) and st.get("summon_power", 0) or 0)
        mul = (1 + sp)
        hp = max(20, int(st.get("max_hp", 200) * float(cfg.get("hp_ratio", 0) or 0) * mul))
        atk = max(0, int(st.get("atk", 50) * float(cfg.get("atk_ratio", 0) or 0) * mul))
        df = max(2, int(st.get("def", 20) * float(cfg.get("def_ratio", 0) or 0) * mul))
        guard = None
        _bg = float(cfg.get("bodyguard", 0) or 0)
        if _bg > 0:
            guard = {
                "chance": _bg,
                "mode": "redirect",
                "absorb_once": bool(cfg.get("absorb_once", False)),
            }
        actor = {"tid": tid, "name": cfg.get("name", tid), "icon": cfg.get("icon", ""),
                 "hp": hp, "max_hp": hp, "atk": atk, "def": df,
                 "dmg_type": cfg.get("dmg_type", "phys"),
                 "rank": int(cfg.get("rank", 1) or 1),
                 "reach": int(cfg.get("reach", 1) or 1),
                 # v180-C S1 actor 雏形：随从统一进 companions（side/kind 标识 +
                 # buffs 容器就位——字段即能力，可被增益/减益/引擎通用逻辑处理）
                 "side": "player", "kind": "summon",
                 "buffs": {},
                 # v151 召唤物语义：纯挡刀吸收一次 / 全队攻击光环 / 吃 AOE
                 "absorb_once": bool(cfg.get("absorb_once", False)),
                 "aura_atk_all": float(cfg.get("aura_atk_all", 0) or 0),
                 "eats_aoe": bool(cfg.get("eats_aoe", False)),
                 # v180-C S2 auto_act 数据驱动：玩家行动后自动普攻（行为/触发全配置）
                 "auto_act": {
                     "trigger": "player_act",
                     "act": {"type": "basic_atk"},
                 } if atk > 0 else None,
                 # v180-B ② guard 数据化：bodyguard/absorb_once → 统一挡刀配置
                 "guard": guard,
                 # v180F B4：随从归属显式 owner（召唤者 actor 引用）——挡刀/宠物行为/
                 # 治疗归属读 owner，不再靠 _last_player 猜（多人副本歧义消除）
                 "owner": player}
        self.companions.append(actor)
        # v151 古树光环：常驻全队攻击 +30%（生成时挂 p_buffs，直到召唤物死亡）
        _aura = float(cfg.get("aura_atk_all", 0) or 0)
        if _aura > 0 and self.player:
            _cur = float(self._p_buffs_bag().get("atk_up_all", 0) or 0)
            self._p_buffs_bag()["atk_up_all"] = max(_cur, _aura)
            logs.append(f"🌳 {actor['name']}：全队攻击＋{int(_aura * 100)}%！")
        logs.append(f"{actor['icon']} {actor['name']} 加入战斗！(HP {hp} / 攻击 {atk} / 站位{actor['rank']}层)")
        return actor

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
        # v169.7 骷髅海 skeleton_cap（牧师死灵线）：骷髅上限 +2（至 5 只）——同模板召唤上限提升
        # v181.P2D-D1：proc 消费迁移注册表族 summon_cap_add（读 _ps cap/add，行为零变化）
        _summon_limit = int(tmpl.get("limit", 3))
        try:
            if tid == "skeleton":
                for _pn_sk, _ps_sk in self._proc_pm(player)["proc"].get("skeleton_cap", []):
                    _ctx_sk = {
                        "player": player, "ps": _ps_sk, "ps_name": _pn_sk,
                        "limit": _summon_limit,
                    }
                    _run_proc_family(self, "skeleton_cap", _ctx_sk)
                    _summon_limit = _ctx_sk.get("limit", _summon_limit)  # handler 数值槽改写读回
                    break
        except Exception as _sw_e:
            _battle_warn('_summon_entity', _sw_e)
            pass
        if len(cur) >= _summon_limit:
            logs.append(f"⛔ 已有 {len(cur)} 个{tmpl['name']}（上限 {_summon_limit}）！")
            return False
        # v180-C S2 装配统一：实体由 _spawn_companion 装配（技能召唤吃 summon_power）
        _actor = self._spawn_companion({
            "tid": tid, "name": tmpl["name"], "icon": tmpl.get("icon", ""),
            "hp_ratio": float(tmpl["hp_ratio"]),
            "atk_ratio": float(tmpl.get("atk_ratio", 0) or 0),
            "def_ratio": float(tmpl["def_ratio"]),
            "dmg_type": tmpl.get("dmg_type", "phys"),
            "rank": int(tmpl.get("rank", 1) or 1),
            "reach": int(tmpl.get("reach", 1) or 1),
            "bodyguard": float(tmpl.get("bodyguard", 0) or 0),
            "absorb_once": bool(tmpl.get("absorb_once", False)),
            "aura_atk_all": float(tmpl.get("aura_atk_all", 0) or 0),
            "eats_aoe": bool(tmpl.get("eats_aoe", False)),
            "summon_power": True,
        }, player, logs)
        if _actor is None:
            return False
        return True

    def _resolve_owner(self, actor: dict | None) -> dict | None:
        """v180F A7：随从/宠物归属解析——直接读 actor.owner（创建路径统一设：召唤
        _spawn_companion 9451、宠物 _pet_ensure_actor 8120），无 owner 返回 None。
        消灭 _last_player 隐式归属猜测——随从行为目标就是它自己的 owner。"""
        if not actor:
            return None
        return actor.get("owner") or None

    def _companion_act(self, actor: dict, logs: list) -> bool:
        """v180-C S2 通用随从自动行为结算：读 actor['auto_act'] 数据执行。
        返回是否出手（出手=消费本次触发）。

        数据驱动（鱼鱼 2026-09-06：语义不固定，全配置）：
        - trigger=player_act：玩家行动后触发（召唤物旧语义，player_turn 尾部扫）
        - trigger=interval：由外部 tick 卡按节奏触发（宠物 pet_act 卡每 N 刻一次）
        - act.type=basic_atk：普攻（用自身 atk/dmg_type/reach 选目标，等价旧 _summons_act 单只）
        - act.type=dmg_owner_atk/matk_pct：以 owner 面板 × value 打敌（宠物撕咬/龙息）
        - act.type=heal_owner：回复 owner max_hp×value（宠物月光祝福）
        - act.type=lifesteal：打敌 + 回 owner 伤害 50%（吸血撕咬）
        - act.type=pierce：打敌 + 破防 2 刻（碎岩冲撞）
        - act.type=buff_owner：给 owner 加 buff（雷鸣鼓舞 atk_up / 狩猎之眼 crit_up）
        扩展：加新随从行为 = 加 act.type 分支或复用玩家技能管线（act.skill），零新 hook。
        """
        try:
            if not actor or self._enemy_dead():
                return False
            # 有 hp 容器才检查存活（召唤物/实体）；无 hp 的 hidden actor（宠物）不受此限
            if "hp" in actor and int(actor.get("hp", 0) or 0) <= 0:
                return False
            aa = actor.get("auto_act") or {}
            act = aa.get("act") or {}
            atype = act.get("type", "")
            if atype == "basic_atk":
                if int(actor.get("atk", 0) or 0) <= 0:
                    return False  # 纯挡刀随从（atk=0）不普攻
                target = self._pick_summon_target(actor)
                if target is None:
                    return False
                dmg_type = actor.get("dmg_type", "phys")
                if dmg_type == "true":
                    # v180-C S3 fix（审计）：统一走 calc_damage（true=atk 直伤+统一波动/下限），
                    # 不再自写"atk×(1+U(-0.15,0.15))"（原与 calc_damage true 分支边界语义漂移）
                    dmg = max(1, E.calc_damage(actor.get("atk", 0), 0, dmg_type="true"))
                else:
                    est = self._enemy_stats(target)
                    dmg = E.calc_damage(actor.get("atk", 0), est.get("def", 0), dmg_type=dmg_type)
                dmg = max(1, dmg)
                self._deal_damage(dmg, logs, target=target, source=actor.get("name", "随从"),
                                   true_dmg=(dmg_type == "true"))
                logs.append(f"{actor.get('icon', '')} {actor.get('name', '随从')} 攻击，造成 {dmg} 点伤害！")
                return True
            # v180E 阶段2：宠物技能收编 auto_act——以下分支以 owner（主人）为目标的
            # 随从行为，数值全读 act.value（来自 PET_POOL skill_value 翻译）。
            # 伤害类宠物技能数值照旧用 owner 面板（v180-C 定论：宠物伤害=主人面板×系数，
            # 归属 attacker=宠物 actor → 被动读宠物自身），与旧 _psk_* 逐字等价。
            if atype in ("dmg_owner_atk", "matk_pct", "lifesteal", "pierce"):
                owner = self._resolve_owner(actor) or {}
                if not owner:
                    return False
                target = self._pick_summon_target(actor)
                if target is None:
                    return False
                pdef = {"skill_value": float(act.get("value", 0) or 0)}
                magic = (atype == "matk_pct")
                ost = self._player_stats(owner)
                est2 = self._enemy_stats(target)
                if magic:
                    dmg = E.calc_damage(int(ost["matk"] * pdef["skill_value"]), est2.get("mdef", 0))
                else:
                    dmg = E.calc_damage(int(ost["atk"] * pdef["skill_value"]), est2.get("def", 0))
                dmg = max(1, dmg)
                real = self._deal_damage(dmg, logs, target=target,
                                          source=actor.get("name", "宠物"), attacker=actor)
                pname = actor.get("name", "宠物")
                sname = act.get("skill_name", "技能")
                logs.append(f"🐾 {pname}的【{sname}】造成 {real} 点伤害！" + (f"「{act.get('line', '')}」" if act.get("line") else ""))
                if atype == "lifesteal":
                    heal = max(1, int(real * 0.5))
                    if owner.setdefault("buffs", {}).get("mortal_wound"):
                        heal = int(heal * 0.5)
                    self._heal_actor(owner, heal, logs)
                    logs.append(f"🩸 {pname}汲取了 {heal} 点生命归还给你！")
                elif atype == "pierce":
                    self.e_buffs["def_down"] = max(int(self.e_buffs.get("def_down", 0) or 0), 2)
                    logs.append(f"🛡️ {pname}的【{sname}】击碎了敌人的护甲！(防御减半 2 刻)")
                if self._enemy_dead():
                    self.result = "victory"
                    logs.append(f"🎉 你击败了【{self.enemy.get('name', '敌人')}】！(宠物击杀)")
                return True
            if atype == "heal_owner":
                owner = self._resolve_owner(actor) or {}
                if not owner:
                    return False
                if owner.get("hp", 0) < owner.get("max_hp", 1):
                    heal = int(owner.get("max_hp", owner.get("hp", 1)) * float(act.get("value", 0) or 0))
                    self._heal_actor(owner, heal, logs)
                    pname = actor.get("name", "宠物")
                    sname = act.get("skill_name", "技能")
                    logs.append(f"🐾 {pname}的【{sname}】为你回复了 {heal} 点生命！" + (f"「{act.get('line', '')}」" if act.get("line") else ""))
                return True
            if atype == "buff_owner":
                owner = self._resolve_owner(actor) or {}
                if not owner:
                    return False
                bkey = act.get("buff", "")
                turns = int(act.get("turns", 2) or 2)
                val = float(act.get("value", 0) or 0)
                if bkey == "atk_up":
                    owner.setdefault("buffs", {})["atk_up"] = max(int(owner.get("buffs", {}).get("atk_up", 0) or 0), turns)
                    # 强度值存 owner 的 pet_buff_vals（随 actor dict 序列化，替代旧 Battle 级旁路）
                    owner.setdefault("pet_buff_vals", {})["atk"] = max(float(owner.get("pet_buff_vals", {}).get("atk", 0) or 0), val)
                    pname = actor.get("name", "宠物")
                    sname = act.get("skill_name", "技能")
                    logs.append(f"🐾 {pname}的【{sname}】为你加持攻击强化！(攻击 +{int(val * 100)}%，{turns} 刻)" + (f"「{act.get('line', '')}」" if act.get("line") else ""))
                elif bkey == "crit_up":
                    owner.setdefault("buffs", {})["crit_up"] = max(int(owner.get("buffs", {}).get("crit_up", 0) or 0), turns)
                    owner.setdefault("pet_buff_vals", {})["crit"] = max(float(owner.get("pet_buff_vals", {}).get("crit", 0) or 0), val)
                    pname = actor.get("name", "宠物")
                    sname = act.get("skill_name", "技能")
                    logs.append(f"🐾 {pname}的【{sname}】为你加持暴击提升！(暴击 +{int(val * 100)}%，{turns} 刻)" + (f"「{act.get('line', '')}」" if act.get("line") else ""))
                return True
            # 未来 act.type 分支（引用玩家技能）在此扩展
            return False
        except Exception:
            return False

    def _companions_trigger(self, trigger: str, logs: list) -> None:
        """v180-C S2 通用随从触发点：扫我方随从阵列（companions）带 auto_act.trigger==trigger
        的 actor，逐个结算。替代旧 _summons_act（player_act 专用循环）。
        触发后清理死亡随从。"""
        if not getattr(self, "companions", None):
            return
        for c in list(self.companions):
            if c.get("hp", 0) <= 0:
                continue
            aa = c.get("auto_act") or {}
            if aa.get("trigger") != trigger:
                continue
            try:
                self._companion_act(c, logs)
            except Exception as _sw_e:
                _battle_warn('_companions_trigger', _sw_e)
                pass
        # 清理死亡随从（v180-C S3 修正：只清"有 hp 的战斗实体"——宠物 actor 无 hp
        # 字段（hidden+untargetable，非受击单位），不能被误判死亡移除）
        for c in list(self.companions):
            if c.get("kind") == "pet" or "hp" not in c:
                continue
            if c.get("hp", 0) <= 0:
                logs.append(f"💀 {c.get('name', '随从')} 倒下了！")
                self.companions.remove(c)

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
            # v178 E8b：爪牙死亡回调——死亡的是场上 minion 时，给 Boss 记一笔
            # （数据机制读 e["_minion_died_count"] 或 e["_minion_died_this_act"] 做条件——
            #  月神守卫机关击碎/雷晶轰鸣晶核击碎/歌澜和声清场等联动）
            if unit.get("is_minion"):
                try:
                    _boss_u = next((u for u in self.enemies
                                    if u.get("is_boss") and not u.get("is_minion")), None) or self.enemy
                    if _boss_u:
                        _boss_u["_minion_died_count"] = int(_boss_u.get("_minion_died_count", 0) or 0) + 1
                        _boss_u["_minion_died_this_act"] = True  # 瞬态标记（当刻消费，行动后清）
                except Exception as _sw_e:
                    _battle_warn('_remove_unit', _sw_e)
                    pass
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
                except Exception as _sw_e:
                    _battle_warn('_remove_unit', _sw_e)
                    pass
                # v169.7 追风 focus_full_on_kill（游侠）：击杀目标后 专注(精力)立即回满
                # v181.P2D-D1：proc 消费迁移注册表族 on_kill_refill（行为零变化）
                try:
                    for _pn_k, _ps_k in self._proc_pm(self.player)["proc"].get("focus_full_on_kill", []):
                        if self._p_res().get("energy") is not None:
                            _ctx_k = {
                                "player": self.player, "ps": _ps_k, "ps_name": _pn_k,
                                "res": self._p_res(), "res_key": "energy",
                                "res_max": self._res_max(self.player, "energy"),
                                "pending_dmg_lines": getattr(self, "_pending_dmg_lines", None),
                            }
                            _run_proc_family(self, "focus_full_on_kill", _ctx_k)
                        break
                except Exception as _sw_e:
                    _battle_warn('_remove_unit', _sw_e)
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

    def _guard_check(self, dmg: int, logs: list, victim: dict | None = None) -> int:
        """v180E 阶段3 统一挡刀核心（absorb + redirect 双模式合一，扫 companions）。

        任何我方随从 actor（companions 里 side=player）带 guard 配置即按字段生效——
        - mode=absorb：整伤拦截 → 0（宠物影袭/铁壁缩壳，冷却制 `_guard_last_at`）
        - mode=redirect：按随从 def 结算、随从扣血/可能死亡（召唤物，概率制 + summon_power
          强化 + absorb_once 吸收 1 次消散）
        不再区分 pet/summons 专用容器/专用函数（原 _pet_block_check + _guard_redirect_check
        双轨合一）。触发后本次伤害不再结算到玩家（拦截优先于闪避/格挡）。
        v180F B4：victim = 受击者 actor（缺省 = 焦点玩家）。挡刀池按随从 owner 归属过滤——
        只挡自己主人的刀（多人副本 A 的随从不挡 B 的刀）。
        """
        if dmg <= 0:
            return dmg
        _victim = victim or getattr(self, "player", None) or {}
        guard_actors = [s for s in (self.companions or [])
                        if isinstance(s.get("guard"), dict)
                        and s.get("guard").get("mode") in ("absorb", "redirect")
                        # v180F B4：归属过滤——随从 owner 是受击者（或未带 owner 的旧随从
                        # 兜底 = 焦点玩家场景不误挡他人）
                        and (s.get("owner") is _victim
                             or (not s.get("owner") and _victim is getattr(self, "player", None)))]
        if not guard_actors:
            return dmg
        # 召唤物 redirect 池带 hp 才可挡（死了/纯效果发生器除外）；absorb 宠物无 hp 也挡
        _absorb_pool = [s for s in guard_actors if s.get("guard", {}).get("mode") == "absorb"]
        _redirect_pool = [s for s in guard_actors
                          if s.get("guard", {}).get("mode") == "redirect" and s.get("hp", 0) > 0
                          and float(s.get("guard", {}).get("chance", 0) or 0) > 0]
        if not _absorb_pool and not _redirect_pool:
            return dmg
        # redirect 池优先于 absorb（召唤物概率挡刀先判定，命中则承担；miss 才轮到宠物冷却挡）
        if _redirect_pool:
            try:
                _owner = _victim or {}
                sp = float(self._player_stats(_owner).get("summon_power", 0) or 0) if _owner else 0
            except Exception:
                sp = 0
            s = random.choice(_redirect_pool)
            chance = min(float(s["guard"].get("chance", 0.40)) * (1 + sp), 0.85)
            if random.random() < chance:
                # 按随从 def 结算——从对玩家伤害反推攻击方等效 atk，再套随从防御公式
                try:
                    _owner2 = _victim or {}
                    _pdef = max(0, int(self._player_stats(_owner2).get("def", 0) or 0)) if _owner2 else 0
                    _atk = self._infer_atk(dmg, _pdef)  # v180E 统一反推
                    taken = max(1, int(E.calc_damage(_atk, max(0, int(s.get("def", 0) or 0)), variance=0)))
                except Exception:
                    taken = max(1, int(dmg))
                s["hp"] -= taken
                _vname = _victim.get("name", "你") if _victim else "你"
                logs.append(f"{s.get('icon', '')} {s['name']} 为{_vname}挡下 {taken} 点伤害！")
                # v151：纯挡刀随从（absorb_once）吸收 1 次单体后消失（v151 §7 藤蔓守卫）
                if s["guard"].get("absorb_once"):
                    logs.append(f"🌿 {s['name']} 完成守护，化作碎屑消散……")
                    self.companions.remove(s)
                    return 0
                if s.get("hp", 0) <= 0:
                    logs.append(f"💀 {s['name']} 在保护你时倒下了！")
                    self.companions.remove(s)
                return 0
        # absorb 池：冷却制整伤拦截（宠物影袭）——每 cooldown 秒最多一次
        if _absorb_pool:
            for s in _absorb_pool:
                gd = s.get("guard") or {}
                # 宠物挡刀需宠物解锁/饱食度 gate（原 _pet_block_check 守卫）
                if s.get("kind") == "pet":
                    if int(s.get("level", 0) or 0) < int(C.PET_SKILL_UNLOCK_LV):
                        continue
                    if int(s.get("satiety", 0) or 0) <= 0:
                        continue
                interval = float(gd.get("cooldown", 0) or 0)
                chance = float(gd.get("chance", 0.25) or 0.25)
                if interval <= 0:
                    continue
                _last = s.get("_guard_last_at")
                if _last is None:
                    _last = 0.0  # 开战时刻：前 interval 秒为冷却期
                if self._now - _last < interval:
                    continue
                if random.random() < chance:
                    s["_guard_last_at"] = self._now
                    pname = s.get("name") or gd.get("name", "宠物")
                    sname = gd.get("skill_name", "守护")
                    _vname = _victim.get("name", "你") if _victim else "你"
                    logs.append(f"🐾 {pname}的【{sname}】替{_vname}挡下了这次攻击！")
                    return 0
        return dmg

    def _drain_pending_dmg(self) -> list:
        """O116：取出并清空延迟的受击伤害日志（命中后由 _damage_actor 输出）。"""
        lines = list(getattr(self, "_pending_dmg_lines", None) or [])
        self._pending_dmg_lines = []
        return lines

    def _roll_dodge(self, actor: dict, logs: list) -> bool:
        """v177 闪避判定（actor 承伤）：dodge 乘算合成(上限40%) → roll。闪避成功返回 True（调用方中断本次承伤）。
        闪避成功副作用：丢弃延迟伤害日志 + on_dodge_success 攒资源。
        怪物 actor 的闪避由 _target_dodge_check 前置处理（避免双重 roll）——但本函数已
        actor 化（v180F B3）：一律读入参 actor 自身袋，不读焦点。"""
        if not actor or not actor.get("class_name"):
            return False
        B = actor.setdefault("buffs", {})
        EFF = actor.setdefault("eff", {})
        RES = actor.setdefault("resources", {})
        # v105 闪避体系（鱼鱼拍板"闪避改乘算"）：全部来源乘算合成 1-Π(1-dᵢ)，统一 40% 总上限
        # 攻击方精准削减：有效闪避 = 闪避 × (1 - 攻击方精准)，精准上限 60%（PVP 互殴生效，PVE 怪物无精准）
        dodge = min(float(self._actor_stats_of(actor).get("dodge", 0) or 0), 0.40)
        # 伪装帷幕（effect=dodge_up 闪避率 +40%）：乘算并入
        if B.get("dodge_up"):
            dodge = 1 - (1 - dodge) * (1 - 0.40)
        # 无声被动——闪避率＋30%：乘算并入
        for _pn, _ps in self._passive_map(actor)["proc"].get("dodge_up", []):
            dodge = 1 - (1 - dodge) * (1 - float(_ps.get("mult", 0.3)))
        # 影步药剂 15%：并入乘算（不再独立判定——旧实现独立判定绕过 40% 上限，基础 40%+药水可达 49.7%）
        if B.get("dodge_pot"):
            dodge = 1 - (1 - dodge) * (1 - 0.15)
        # v140 波4：新手特效 远行（novice_first_turn_dodge）——每场战斗首刻闪避率 +5%
        if (EFF or {}).get("novice_dodge_active") and self._tick_no() <= 1:
            try:
                from .core.weapon_effects import effect_data as _we_ed3
                _nfd_pct = float(_we_ed3(self, actor, "novice_first_turn_dodge").get("dodge_pct", 0.05) or 0.05)
            except Exception:
                _nfd_pct = 0.05
            dodge = 1 - (1 - dodge) * (1 - _nfd_pct)
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
            _rd = E.core_resource_def(actor.get("class_name", ""))
            if _rd and _rd.get("on_dodge_success"):
                _rk = _rd["key"]
                RES[_rk] = self._res_gain_class(actor.get("class_name", ""), _rk, int(_rd["on_dodge_success"]))
                logs.append(f"🫧 影步积攒 +{_rd['on_dodge_success']}({RES.get(_rk, 0)}/{_rd['max']})")
            return True

        return False
    def _mitigate_chain(self, actor: dict, dmg: int, logs: list) -> tuple:
        """v177 命中后减伤链（actor 通用）：圣典免伤/铁壁格挡(免疫中断)/reduce_all/单人减伤/格挡+反击/
        复仇/套装受击/词条料理/被动减伤族。返回 (处理后的 dmg, interrupted)；interrupted=True = 免疫本次伤害。
        怪物 actor 无这些数据源 → 空转。副作用全在 self + logs。"""
        if not actor or not (actor.get("class_name") or actor.get("equipment") or actor.get("learned_skills")
                              or actor.get("buffs") or actor.get("shields") or actor.get("resources")):
            return dmg, False
        # v180F B3：受击方状态一律读入参 actor 自身 dict（伪 actor 化修复——
        # 原按 class_name 分轨：带 class_name 走焦点袋 _p_*，非焦点玩家/带 class 怪
        # 受击会吃错被动/套装/资源）
        B = actor.setdefault("buffs", {})
        EFF = actor.setdefault("eff", {})
        RES = actor.setdefault("resources", {})
        MS = actor.setdefault("stacks", {})
        HITS = actor.setdefault("buff_hits", {})
        # v130.2c 圣典·日冕 4 件：满信仰状态下首次受击免伤（每战 1 次，随战斗序列化）
        if (not getattr(self, "_set_immune_used", False)
                and self._set_eff(actor, "first_hit_immune", 4)
                and self._res_read("faith") >= self._res_max(actor, "faith")):
            self._set_immune_used = True
            logs.append("☀️ 圣典·日冕：满信仰免伤结界抵挡了这次攻击！")
            return dmg, True
        # v142 数据驱动：铁壁格挡（anvil_parry）——受击 20% 概率免疫本次伤害（每场 3 次，数值读 params）
        _ap_eff = self._set_eff(actor, "anvil_parry", 4)
        if _ap_eff:
            _ap_params = (_ap_eff or {}).get("params") or {}
            _apl = int((EFF or {}).get("anvil_parry_left", _ap_params.get("per_battle", 3)) or 3)
            if _apl > 0 and random.random() < float(_ap_params.get("chance", 0.20)):
                EFF["anvil_parry_left"] = _apl - 1
                logs.append(f"🛡️ 铁壁格挡！千锤百炼的拳套挡下了攻击！（剩余 {_apl - 1} 次）")
                return dmg, True
        # v113.1：团队技能 reduce_all 真·百分比减伤（此前误映射 def_up 防御提升）——
        # p_buffs["reduce_all"] 存减伤百分比，刻数由 RL_ALL 单独计时。
        # 单机侧在此按比例减伤；副本广播侧（instance.py 消费 team_effects["reduce_all"]）另口径。
        _rd_pct = float(B.get("reduce_all") or 0)
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
        # v162：单人减伤（effect=reduce，铁壁/铜墙/亡魂护甲/磐岩甲）——p_buffs["reduce"] 存百分比，
        # 受击次数由 _p_buff_hits 计时（_apply_dmg_to_target 尾部递减）。百分比减伤在此消费。
        _sg_rd = float(B.get("reduce") or 0)
        if _sg_rd > 0:
            _sr = int(dmg * min(_sg_rd, 0.9))
            if _sr > 0:
                dmg = max(1, dmg - _sr)
                logs.append(f"🛡️ 减伤护体吸收 {_sr} 点伤害！")
        # v106.3 格挡属性统一结算（词条折算/种族岩壁格挡/被动/药水 → st["block"]）
        # 圣盾被动 stat=block mult=0.1 已并入被动加成（_PASSIVE_STAT_APPLY block → block_add）
        block_chance = float(self._actor_stats_of(actor).get("block", 0) or 0)
        if B.get("block_pot"):
            block_chance = 1 - (1 - block_chance) * (1 - 0.15)  # 岩壁药剂 +15% 格挡（乘算并入）
        # v169.7 battle_mech effect：铁壁·誓/铁山靠 block_up（格挡率 30%/50%，数值存 p_eff block_up_val）
        if B.get("block_up"):
            _bu = float(EFF.get("block_up_val", 0.30) or 0.30)
            block_chance = 1 - (1 - block_chance) * (1 - min(_bu, 0.5))
        block_chance = min(block_chance, 0.40)
        if block_chance > 0 and random.random() < block_chance:
            block_reduce = max(1, int(dmg * 0.5))
            dmg = max(1, dmg - block_reduce)
            logs.append(f"🛡️ 格挡！减免 {block_reduce} 点伤害！")
            # v142 数据驱动：壁槌反震（bi_chui_wall）——格挡成功必反弹 30% 原始伤害（数值读 params）
            _bw_eff = self._set_eff(actor, "bi_chui_wall", 4)
            if _bw_eff and self.enemy.get("hp", 0) > 0:
                _bw_params = (_bw_eff or {}).get("params") or {}
                _bw = max(1, int(dmg * float(_bw_params.get("reflect_pct", 0.30))))
                _bw = self._boss_dmg_filter(_bw, actor, logs)
                self._deal_damage(_bw, logs)
                logs.append(f"🧱 壁槌反震！格挡余劲反弹 {_bw} 点伤害！")
            # v107 格挡反击（圣殿骑士）：格挡成功后按 chance 反伤（物理段，mult 为反伤系数）
            # v110.3 P2-1：多个格挡反击被动逐个独立 roll，命中即停；此前 break 在 for 末尾无条件退出，只 roll 第一个被动
            for _pn, _ps in self._passive_map(actor)["proc"].get("block_counter", []):
                if self.enemy.get("hp", 0) > 0 and random.random() < float(_ps.get("chance", 0.5)):
                    rd = max(1, int(dmg * float(_ps.get("mult", 0.5))))
                    rd = self._boss_dmg_filter(rd, actor, logs)
                    self._deal_damage(rd, logs)
                    logs.append(f"🛡️ {_pn}：格挡反击！反弹 {rd} 点伤害！")
                    break  # 命中即停（一次格挡最多一次反击）
        self._player_hit = True  # v2.1 条件：记录本场受击（未受击增伤判定）
        # ---- v151 时刻制：防御型 buff 受击计数递减（鱼鱼拍板：防御药水"3 刻"应按敌方出手次数计）----
        # 铁壁药剂/岩壁药剂/影步药剂/荆棘药剂/技能铁壁 等防御/受击类 buff 不再按玩家刻递减，
        # 改为"实际受击 N 次后消失"——防的是敌方出手，就按敌方出手数计时，不受速度差影响。
        if HITS:
            for _hk in [k for k in list(HITS) if int(HITS.get(k, 0) or 0) > 0]:
                _nh = int(HITS.get(_hk, 0) or 0) - 1
                if _nh <= 0:
                    HITS.pop(_hk, None)
                    # 受击次数耗尽 → 移除对应 buff（若 p_buffs 里还有刻数残留也清掉）
                    if _hk in B:
                        B.pop(_hk, None)
                        logs.append(f"🕛 【{_hk}】效果随受击消耗殆尽！")
                else:
                    HITS[_hk] = _nh
        # ---- v139 职业融合：受击处理（dual_form 扣资源 / focus 打断 / charge 打断 -1 阶）----
        from .core.battle_modes import dual_form_def, dual_form_state, dual_form_hit, dual_form_force_return, dual_form_exit, dual_form_active, focus_def, focus_state, focus_on_hit, vent_def, vent_relief
        from .core.battle_bars import charge_state, charge_on_hit
        # dual_form：狂暴/龙焰形态受击 -N（P3 不清零、单刻封顶，由 dual_form_hit 返回应扣量）
        if dual_form_active(actor):
            _dfd = dual_form_def(actor)
            _df_hc = dual_form_hit(actor)
            if _df_hc > 0:
                _df_key = _dfd.get("key", "rage")
                _df_cur = int(RES.get(_df_key, 0) or 0)
                RES[_df_key] = max(0, _df_cur - _df_hc)
                logs.append(f"⚡【{_dfd.get('form', '形态')}】受击，形态值 -{_df_hc}（{RES.get(_df_key, 0)}）")
                # 强制回基础形态检查（资源 < force_return）
                if dual_form_force_return(actor, int(RES.get(_df_key, 0) or 0)):
                    dual_form_exit(actor, logs)
                    logs.append("⚠️ 力量不支，被迫回到常态！")
        # focus：专注中受击打断判定（interrupt_rate 概率，资源保留）
        if focus_state(actor).get("active"):
            focus_on_hit(actor, logs)
        # charge：蓄力中受击 -1 阶（不清零）
        _ch_st = charge_state(actor)
        if int(_ch_st.get("stages", 0) or 0) > 0:
            charge_on_hit(actor, {"name": _ch_st.get("skill", "蓄力")}, logs)
        # vent：闪避已在上方 return（闪避成功走 vent_relief），这里命中时不泄压
        # v104 R3 P1-1：复仇被动——受击后下次攻击 +30%（挨打反打）
        for _pn, _ps in self._passive_map(actor)["proc"].get("counter", []):
            B["revenge_atk"] = max(B.get("revenge_atk", 0), 1)
            break
        # 阶段八：受击词条（减伤/格挡/反击/反伤/腐蚀/坚韧）
        dmg = self._affix_on_taken(actor, dmg, logs)
        dmg = self._food_on_taken(actor, dmg, logs)
        # v142 数据驱动：套装受击特效（taken_* 型，读 params.type 调通用执行器）
        dmg = self._set_taken_proc(actor, dmg, logs)
        # v140 波3.1：特效装备受击（哨兵壁垒/铁壁回响/寒霜凝视/荆棘/卫士/深岩/龙脊/复仇环/烬火/石像/泰坦/巡林）
        # 亡舞战铠常驻 -8% 减伤一并在此消费（passive taken 分发）
        try:
            from .core.weapon_effects import proc as _we_proc
            _wetaken = {"dmg": dmg, "taken": dmg}
            _we_proc(self, actor, "taken", _wetaken, logs)
            _we_proc(self, actor, "passive", {"taken": _wetaken.get("taken", dmg)}, logs)
            dmg = max(1, int(_wetaken.get("taken", dmg)))
        except Exception as _sw_e:
            _battle_warn('_mitigate_chain', _sw_e)
            pass
        # v140 波4：新手特效 守御（novice_first_turn_guard）——每场战斗首刻受击伤害 -10%
        if (EFF or {}).get("novice_guard_active") and self._tick_no() <= 1:
            try:
                from .core.weapon_effects import effect_data as _we_ed4
                _nfg_pct = float(_we_ed4(self, actor, "novice_first_turn_guard").get("reduce_pct", 0.10) or 0.10)
            except Exception:
                _nfg_pct = 0.10
            dmg = max(1, int(dmg * (1 - _nfg_pct)))
            logs.append(f"🛡️ 守御：首刻受击伤害 -{int(_nfg_pct * 100)}%！")
        # v130.2c 套装受击回资源：血誓战团（受击回怒 +1）/ 圣徽·誓约（受击回信仰 +1）
        self._set_res_proc(actor, "on_taken", logs)
        # v64/v104 被动 proc 结算（按 passive 字段查 learned_skills，替换名字硬匹配）：
        #   dmg_taken → 减伤（铁壁之心/磐石体/磐石之心/磐石之躯/守护姿态）；reflect → 反伤（反震）
        ps_names = E.passive_skills_learned(actor.get("class_name", ""), actor.get("learned_skills", []))
        reduce_total = 0
        for ps_name in ps_names:
            info = E.skill_info(actor.get("class_name", ""), ps_name)
            ps = (info or {}).get("passive") or {}
            proc = ps.get("proc")
            if proc == "dmg_taken":
                rpct = float(ps.get("reduce") or 0)
                if rpct <= 0:
                    continue
                # v1.x：条件判定改查 PASSIVE_COND_CHECKS（原 hp_low_30 if 硬编码；
                # 条件不满足 → 跳过本次减伤，语义与旧 `cond==hp_low_30 and hp>=30% → continue` 一致）
                if not passive_cond_ok(self, actor, ps):
                    continue
                reduce_total += int(dmg * rpct)
                # v113.1：守护姿态 passive 带 res_gain（受击怒气+2 承诺）——此前本分支只减伤
                # 不结算 res_gain，承诺落空。消费到职业核心资源（战士怒气等）。
                _rg = int(ps.get("res_gain") or 0)
                if _rg > 0:
                    _rcls = actor.get("class_name", "")
                    _rdef = E.core_resource_def(_rcls)
                    if _rdef:
                        _rk = _rdef["key"]
                        # v130.2f2（T7 P2-1）：受击被动 res_gain（磐石体/墓穴护甲/守护姿态）改走
                        # _res_gain_class——与 on_hit 基础受击渠道同口径：上限含词条/套装加成，
                        # 满资源溢出转盾（不再直调 E.core_resource_gain 平顶蒸发）；满值时
                        # 真实增量判定防误报（转盾由 _res_gain_class 日志单独反馈）。
                        _rg_before = int(RES.get(_rk, 0) or 0)
                        RES[_rk] = self._res_gain_class(_rcls, _rk, _rg)
                        if int(RES.get(_rk, 0) or 0) > _rg_before:
                            logs.append(f"⚡ {ps_name}：受击获取 {_rg} 点资源（{_rk} {RES[_rk]}）")
            elif proc == "reflect" and self.enemy.get("hp", 0) > 0:
                # v113.1：反震——按 chance 概率反伤（缺省 100%：无条件反伤，保持旧行为）
                if "chance" in ps and random.random() >= float(ps.get("chance") or 0):
                    continue
                rd = int(dmg * float(ps.get("mult") or 0))
                if rd > 0:
                    # v104 M02 P1-5：反伤走 Boss 护盾过滤（扣盾减半/反伤），再结算援军挡刀
                    rd = self._boss_dmg_filter(rd, actor, logs)
                    self._deal_damage(rd, logs)
                    logs.append(f"🪨 {ps_name}：反弹 {rd} 点伤害！")
        # v142 数据驱动：磐石不动（pan_shi_steady）——常驻 5% 减伤并入汇总（数值读 params）
        _ps_eff = self._set_eff(actor, "pan_shi_steady", 4)
        if _ps_eff:
            _ps_params = (_ps_eff or {}).get("params") or {}
            reduce_total += int(dmg * float(_ps_params.get("reduce_pct", 0.05)))
            logs.append("⛰️ 磐石不动：巍然不动，减伤 5%！")
        # v169.7 不动如山 core_last_stand：生命 <30% 时获得 3 枚磐核并减伤 40%（每场 1 次）——
        # 触发点（磐核生产缺口见 技能引擎缺口全量清单 §3.2 磐核族：引擎无磐核生产渠道，此处
        # 首触发只补 3 磐核并置位；40% 减伤随 hp<30% 每次受击生效（用满整场仍 1 次生产））
        try:
            if not getattr(self, "_core_last_stand_used", False):
                _hp_ratio = actor.get("hp", 0) / max(1, actor.get("max_hp", 1) or 1)
                if _hp_ratio < float((self._proc_pm(actor)["proc"].get("core_last_stand", [{}])[0][1]).get("hp_lt", 0.30)) if self._proc_pm(actor)["proc"].get("core_last_stand") else False:
                    for _pn_cls, _ps_cls in self._proc_pm(actor)["proc"].get("core_last_stand", []):
                        self._core_last_stand_used = True
                        RES["guard_core"] = max(self._guard_core_n(), int(_ps_cls.get("cores", 3) or 3))
                        logs.append(f"⛰️ 不动如山：绝境不屈，获得 {int(_ps_cls.get('cores', 3) or 3)} 枚磐核！（每场 1 次）")
                        break
        except Exception as _sw_e:
            _battle_warn('_mitigate_chain', _sw_e)
            pass
        # 圣堂壁垒（holy_bastion_def）——常驻 5% 减伤（数值读 params）
        _hb_eff = self._set_eff(actor, "holy_bastion_def", 4)
        if _hb_eff:
            _hb_params = (_hb_eff or {}).get("params") or {}
            reduce_total += int(dmg * float(_hb_params.get("reduce_pct", 0.05)))
            logs.append("⛪ 圣堂壁垒：受击减伤 5%！")
        # ---- v169.7 条件减伤被动族（磐核/战意 持有档位） ----
        # 坚城之姿 zhan_yi_full_reduce（战士守线）：战意满 10 减伤 +10%
        # 磐石之躯 core_full（拳师守线）：磐核满 5 减伤 +20%（免疫控制部分在 _apply_mech_effect 消费）
        # 大地之肤 core_reduce（拳师守线）：每枚磐核额外减伤 +2%（与基础 +3% 叠加）
        # 不动如山 core_last_stand（拳师守线）：生命 <30% 减伤 40%（每场 1 次，触发时同时给 3 磐核）
        # 磐石之心 core_overflow（拳师守线）：磐核 ≥3 受击溢出伤害转护盾
        try:
            _pm_dr = self._proc_pm(actor)
            _dr_pct = 0.0
            # 坚城之姿
            for _pn2, _ps2 in _pm_dr["proc"].get("zhan_yi_full_reduce", []):
                if self._zhan_yi_n() >= int(_ps2.get("stacks", 10) or 10):
                    _dr_pct += float(_ps2.get("reduce", 0.10) or 0.10)
                break
            # 磐石之躯 / 大地之肤（磐核档）
            for _pn2, _ps2 in _pm_dr["proc"].get("core_full", []):
                if self._guard_core_n() >= int(_ps2.get("stacks", 5) or 5):
                    _dr_pct += float(_ps2.get("reduce", 0.20) or 0.20)
                break
            for _pn2, _ps2 in _pm_dr["proc"].get("core_reduce", []):
                _gn = self._guard_core_n()
                if _gn > 0:
                    _dr_pct += float(_ps2.get("per_core", 0.02) or 0.02) * _gn
                break
            # 不动如山：已触发后（hp<30%）减伤 40% 持续生效
            if getattr(self, "_core_last_stand_used", False):
                for _pn2, _ps2 in _pm_dr["proc"].get("core_last_stand", []):
                    _dr_pct += float(_ps2.get("reduce", 0.40) or 0.40)
                    break
            # 磐石之心：磐核 ≥3 → 溢出承伤转护盾（护盾 = 超过 hp 上限部分的伤害额 80%，3 刻）
            for _pn2, _ps2 in _pm_dr["proc"].get("core_overflow", []):
                if self._guard_core_n() >= int(_ps2.get("stacks", 3) or 3):
                    _ov_sh = int(dmg * float(_ps2.get("shield_pct", 0.80) or 0.80))
                    if _ov_sh > 0:
                        self._add_shield("core_overflow", _ov_sh, int(_ps2.get("turns", 3) or 3))
                        logs.append(f"🪨 磐石之心：磐核 {self._guard_core_n()} 枚，承伤转化 {_ov_sh} 点护盾！")
                break
            if _dr_pct > 0:
                reduce_total += int(dmg * min(_dr_pct, 0.9))
        except Exception as _sw_e:
            _battle_warn('_mitigate_chain', _sw_e)
            pass
        if reduce_total:
            dmg = max(1, dmg - reduce_total)
            logs.append(f"🛡️ 被动减伤 {reduce_total} 点")

        return dmg, False
    def _infer_atk(self, dmg: int, target_def: int) -> int:
        """v180E 阶段5：从\"已按某防御算好的伤害\"反推攻击方等效 atk。

        公式来源：dmg = atk²/(atk+def) → atk² - dmg·atk - dmg·def = 0
        → atk = (dmg + √(dmg² + 4·dmg·def)) / 2
        AOE 逐目标重算（_aoe_damage）与随从挡刀按 def 结算（_guard_check）共用。
        """
        try:
            _td = max(0, int(target_def or 0))
            if _td <= 0:
                return max(1, int(dmg or 0))
            return max(1, (int(dmg or 0) + int((int(dmg or 0) * int(dmg or 0) + 4 * int(dmg or 0) * _td) ** 0.5)) // 2)
        except Exception:
            return max(1, int(dmg or 0))

    def _phys_retort(self, actor: dict, atk_mult: float, logs: list,
                     is_crit: bool = False, variance: float = 0.15, roll_crit: bool = False,
                     target: dict | None = None) -> int:
        """v180E 阶段5：统一物理反击伤害结算（石拳反打/反击被动/盾牌反击/以守为攻等共用）。

        模式 = actor 面板 atk × mult 对目标 def 结算物理伤害（calc_damage 封装），
        返回 (经 _boss_dmg_filter 的实际伤害, 是否暴击)。
        roll_crit=True 时自行 roll 暴击（反击被动/以守为攻原语义）；False 保持无暴击
        （石拳反打原语义无暴击判定）。调用方可传 is_crit 精确指定。
        v180F 审查修复：target = 反击目标（=攻击者 _rtgt）。原 _enemy_stats() 无参读
        _active_target，多怪/事件队列里可能漂移成别的怪 → 反击打错目标面板。缺省 None
        回落旧行为（兼容外部直接调 _phys_retort 的点）。
        """
        try:
            _st = self._actor_stats_of(actor)
            if target is not None:
                _est = self._enemy_stats(target)
            else:
                _est = self._enemy_stats()
            if is_crit or roll_crit:
                _crit = is_crit or (random.random() < float(_st.get("crit", 0) or 0))
            else:
                _crit = False
            _d = E.calc_damage(int(_st.get("atk", 0) * float(atk_mult or 1.0)),
                               _est.get("def", 0), _crit, variance=variance, dmg_type="phys")
            _d = self._boss_dmg_filter(_d, actor, logs)
            return max(1, _d), _crit
        except Exception:
            return max(1, int(E.calc_damage(1, 0, dmg_type="phys"))), False

    def _retaliations_and_buffs(self, actor: dict, dmg: int, logs: list, attacker: dict | None = None) -> tuple:
        """v177 受击后效（任意 actor）：反伤/反击/金身/符文壁垒/次元门扉/圣辉等——回击攻击者或改自身状态。
        返回 (处理后的 dmg, interrupted)；interrupted=True = 本次承伤被免疫中断（次元门扉），调用方 return。
        回击目标 = attacker（攻击者，玩家被打=怪 / 怪被打=玩家），缺省回退 self.enemy。
        actor 无养成数据源（装备/被动/职业）→ 空转。副作用全在 self + logs。"""
        if not actor or not (actor.get("class_name") or actor.get("equipment") or actor.get("learned_skills")
                              or actor.get("buffs") or actor.get("shields") or actor.get("resources")):
            return dmg, False
        # 反击/反伤目标：攻击者优先；玩家被打场景（attacker=None）回退敌人
        _rtgt = attacker if attacker is not None else self.enemy
        # 回击落点：v177 actor 统一——玩家/怪都走 _damage_actor（状态容器按 _is_player_side 路由）。
        # 修复：旧 else 分支 _hit_back(rd_val) 无限自调（RecursionError 被吞 → 反伤静默丢失，
        # 荆棘/格挡反震等对怪回击全失效）；现统一 _damage_actor 目标即正确扣血/移除。
        def _hit_back(rd_val: int) -> None:
            if not _rtgt:
                return
            try:
                self._damage_actor(_rtgt, rd_val, logs,
                                   source=str(actor.get("name", "敌人") or "敌人") or "反伤")
            except Exception as _sw_e:
                _battle_warn('_hit_back', _sw_e)
                pass
        B = actor.setdefault("buffs", {})
        EFF = actor.setdefault("eff", {})
        RES = actor.setdefault("resources", {})
        MS = actor.setdefault("stacks", {})
        # v106.4 反伤属性统一结算（词条折算/种族/被动/药水 → st["thorns"]）
        _pst_th = self._actor_stats_of(actor)
        th = float(_pst_th.get("thorns", 0) or 0)
        if B.get("thorns_pot"):
            th = 1 - (1 - th) * (1 - 0.30)  # 荆棘药剂 +30% 反伤（乘算并入）
        th = min(th, 0.5)
        # v169.7 battle_mech effect：铁山靠/守护誓言/铁壁·誓——技能反伤数值（40%/50%，p_eff 通道）
        # block_up 存在时叠加技能反伤，cap 抬到 0.6（desc 承诺值可达 40-50%，与 thorns 并存防膨胀）
        _brv = float((EFF or {}).get("block_reflect_val", 0) or 0)
        if _brv > 0 and B.get("block_up"):
            th = min(th + _brv, 0.6)
        if th > 0 and _rtgt and _rtgt.get("hp", 0) > 0:
            rd = int(dmg * th)
            if rd > 0:
                rd = self._boss_dmg_filter(rd, actor, logs)
                _hit_back(rd)
                logs.append(f"🌵 反伤！反弹 {rd} 点伤害！")
        # v107 反击（苦修士）：受击后按 chance 概率立即普攻反击（物理段，吃暴击）
        # v109 P0-3：多个反击被动（以守为攻+反击之王）逐个独立 roll，命中即停；此前 break 在
        # for 末尾无条件退出，只 roll 第一个被动 → 反击之王(lv70)被废
        # v142 数据驱动：石拳反打（shi_quan_retort）——受击 15% 概率以 30% 攻击反击（数值读 params）
        _sq_eff = self._set_eff(actor, "shi_quan_retort", 4)
        if _sq_eff and _rtgt and _rtgt.get("hp", 0) > 0:
            _sq_params = (_sq_eff or {}).get("params") or {}
            if random.random() < float(_sq_params.get("chance", 0.15)):
                _sq_dmg, _sq_crit = self._phys_retort(actor, float(_sq_params.get("atk_pct", 0.30)), logs, target=_rtgt)  # v180E 统一反击
                _hit_back(_sq_dmg)
                logs.append(f"🥊 石拳反打！铁拳回敬 {_sq_dmg} 点伤害！")
        if _rtgt and _rtgt.get("hp", 0) > 0:
            for _pn, _ps in self._passive_map(actor)["proc"].get("counter_attack", []):
                if random.random() < float(_ps.get("chance", 0.20)):
                    ca_dmg, _ca_crit = self._phys_retort(actor, 1.0, logs, roll_crit=True, target=_rtgt)  # v180E 统一反击(原 roll 暴击)
                    _hit_back(ca_dmg)
                    logs.append(f"🥊 反击！你立刻回击造成 {ca_dmg} 点伤害！"
                                + (" 💥暴击" if _ca_crit else ""))
                    # v130.2f 反击回气承诺落地（monk.md §3.1「受击换气/反震回气」）：
                    # 以守为攻/反击之王 反击命中后 气 +2（走 _res_gain_class 类资源上限管线）
                    _cr_cls = actor.get("class_name", "")
                    _cr_rd = E.core_resource_def(_cr_cls)
                    if _cr_rd and _cr_rd.get("key") == "chi":
                        _chi_now = self._res_gain_class(_cr_cls, "chi", 2)
                        logs.append(f"🥊 反击回气 +2（气 {_chi_now}）")
                    break  # 命中即停（一次受击最多一次反击）
        # v51 盾牌反击：被攻击时 60% 概率反击 120% 伤害（原语义无 boss filter，保持）
        # v180G B2-3：收口 _phys_retort（原内联手写 calc_damage——石拳/反击/以守为攻已统一，此独漏）
        if B.get("counter", 0) > 0 and _rtgt and _rtgt.get("hp", 0) > 0:
            if random.random() < C.SHIELD_COUNTER_CHANCE:
                # v180F 审查修复：盾牌反击打 _rtgt（攻击者），显式传目标防 _active_target 漂移
                cd, _cd_crit = self._phys_retort(actor, 1.2, logs, target=_rtgt)
                _hit_back(cd)
                logs.append(f"🛡️ 盾牌反击！对【{_rtgt.get('name', '敌人')}】造成 {cd} 点伤害！")
                # v173.5 全层仇恨：守护姿态受击反击的伤害也累计仇恨（坦克被打 → 反击
                # 产生仇恨，数值模型 guard_hate 落地：反击伤害全额进仇恨）
                self._add_hate(actor, cd)
        # v169.7 以守为攻 counter_chance / 反击之王 counter_up：受击反击被动族——
        # 统一挂点（与既有 counter_attack 消费点 battle.py:6990 同段）：以守为攻给基础
        # 35% 概率×80% 普攻；反击之王在学了以守为攻时 +25% 概率 & +50% 伤害
        # （两被动皆学 = 60% 概率 ×120% 普攻——combine，见下方聚合）
        if _rtgt and _rtgt.get("hp", 0) > 0:
            _cc_list = self._proc_pm(actor)["proc"].get("counter_chance", [])
            _cu_list = self._proc_pm(actor)["proc"].get("counter_up", [])
            if _cc_list or _cu_list:
                _chance = 0.0
                _mult = 1.0
                for _pn, _ps in _cc_list:
                    _chance = max(_chance, float(_ps.get("chance", 0.35) or 0.35))
                    _mult = min(_mult, float(_ps.get("mult", 0.80) or 0.80))  # 以守为攻 80% 普攻
                if _cu_list:  # 反击之王：+25% 概率、反击伤害 +50%
                    for _pn, _ps in _cu_list:
                        _chance += float(_ps.get("chance_add", 0.25) or 0.25)
                        _mult *= 1.0 + float(_ps.get("dmg_add", 0.50) or 0.50)
                        break
                _chance = min(_chance, 0.9)
                if random.random() < _chance:
                    _c2_dmg, _c2_crit = self._phys_retort(actor, _mult, logs, roll_crit=True, target=_rtgt)  # v180E 统一反击(以守为攻)
                    _hit_back(_c2_dmg)
                    logs.append(f"🥊 反击！你立刻回击造成 {_c2_dmg} 点伤害！"
                                + (" 💥暴击" if _c2_crit else ""))
                    # 反击回气（同既有 counter_attack 消费点）：命中后 气 +2
                    _cr2_cls = actor.get("class_name", "")
                    _cr2_rd = E.core_resource_def(_cr2_cls)
                    if _cr2_rd and _cr2_rd.get("key") == "chi":
                        self._res_gain_class(_cr2_cls, "chi", 2)
        # 龙鳞套（effect reflect）：被攻击时 25% 概率反弹 25% 伤害
        # v181-A1：chance/reflect_pct 读套装 params（龙鳞 params 0.25/0.25 与旧
        # C.REFLECT_CHANCE/0.25 一致）；无 params 的 reflect 套装回落旧常量兜底（数值不变）
        for _sname_r, _cnt_r in E.active_sets(actor.get("equipment") or {}).items():
            if _cnt_r < 4:
                continue
            _si_r = E._set_info(_sname_r)
            if not _si_r:
                continue
            _b4r = (_si_r.get("bonus_4") or {})
            if _b4r.get("effect") != "reflect":
                continue
            _rp_r = (_b4r.get("params") or {})
            _r_chance = float(_rp_r.get("chance", C.REFLECT_CHANCE) or C.REFLECT_CHANCE)
            _r_pct = float(_rp_r.get("reflect_pct", 0.25) or 0.25)
            if _rtgt and _rtgt.get("hp", 0) > 0 and random.random() < _r_chance:
                rd = int(dmg * _r_pct)
                rd = self._boss_dmg_filter(rd, actor, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
                _hit_back(rd)
                logs.append(f"🐉 龙鳞反震！反弹 {rd} 点伤害！")
            break
        # v29 金身：每层减伤 4%
        mech = MS
        iron = int(mech.get("iron", 0) or 0)
        if iron > 0:
            reduce = int(dmg * 0.04 * iron)
            dmg = max(1, dmg - reduce)
            logs.append(f"🪷 金身减伤 {reduce} 点({iron} 层)")
        # v34 符文·壁垒：受击时 x% 概率获得护盾（y% 生命值）；荆棘：受击反弹 x% 伤害
        effs = self._enchant_effects(actor)
        barrier_lvl = self._enchant_lvl(effs, "barrier")
        if barrier_lvl:
            prob, pct = C.rune_value("barrier", barrier_lvl)
            # 契约断言：data/runes.py barrier lvl 返回 [prob, pct] 二元素列表，防未来改单值静默错位
            assert isinstance(prob, (int, float)) and isinstance(pct, (int, float)), \
                f"rune barrier lvl={barrier_lvl} 应返回 [prob, pct]，实得 {C.rune_value('barrier', barrier_lvl)!r}"
            if random.random() < prob:
                shield_gain = int(actor.get("max_hp", actor.get("hp", 1)) * pct)
                self._add_shield("rune_barrier", shield_gain, 2)
                logs.append(f"🛡️ 符文壁垒：获得 {shield_gain} 点护盾！")
        thorns_lvl = self._enchant_lvl(effs, "thorns")
        if thorns_lvl and _rtgt and _rtgt.get("hp", 0) > 0:
            rd = int(dmg * C.rune_value("thorns", thorns_lvl))
            rd = self._boss_dmg_filter(rd, actor, logs)  # v104 M02 P1-5：反伤走 Boss 护盾过滤
            _hit_back(rd)
            logs.append(f"🌵 符文荆棘：反弹 {rd} 点伤害！")
        # v106.4 反伤属性统一结算在 _damage_actor 段（thorns_pot 已乘算并入 thorns，
        # 此段删除 v101.28f 旧独立反弹——否则双重结算，2026-08-13 回归抓包）
        # v140 波3.2：次元门扉符无敌——本刻免疫一切伤害（p_eff invuln，用后清 + 记录僵直）
        _inv = (EFF or {}).get("invuln")
        if _inv and int(_inv.get("turns", 1) or 1) > 0:
            _inv["turns"] = int(_inv.get("turns", 1) or 1) - 1
            if int(_inv.get("turns", 0) or 0) <= 0:
                EFF.pop("invuln", None)
                _sa = int(_inv.get("stun_after", 1) or 1)
                if _sa > 0:
                    B["stun"] = max(int(B.get("stun", 0) or 0), _sa)
                    logs.append("🌀 次元门扉关闭，你陷入短暂僵直！")
            logs.append("🌀 次元门扉：免疫了这次伤害！")
            return dmg, True
        # v140 波3.2：龙血变身药剂——受击伤害 +15%（morph_dmg_taken）
        _morph = float((EFF or {}).get("morph_dmg_taken", 0) or 0)
        if _morph > 0:
            dmg = max(1, int(dmg * (1 + _morph)))
            logs.append(f"🐉 龙人形态：额外承受 {int(dmg * _morph)} 点伤害！")
        # v142 数据驱动：圣徽守护（bless_ward_shield）——受击 25% 概率获得 8% 最大生命护盾（3 刻）
        # v181-A1：兜底默认值删除——数值全读 params（祝福套 params 0.25/0.08/3 = 原兜底）
        _bws_eff = self._set_eff(actor, "bless_ward_shield", 4)
        if _bws_eff:
            _bws_params = (_bws_eff or {}).get("params") or {}
            if random.random() < float(_bws_params["chance"]):
                _bw_sh = int(actor.get("max_hp", actor.get("hp", 1)) * float(_bws_params["shield_pct"]))
                self._add_shield("bless_ward", _bw_sh, int(_bws_params["shield_turns"]))
                logs.append(f"✨ 圣徽守护！获得 {_bw_sh} 点护盾！")
        # v142 数据驱动：圣辉圣环（holy_halo_shield）——受击后 10% 伤害转护盾（每刻最多 1 次）
        # v181-A1：shield_pct/shield_turns 读 params（圣徽 params 0.10/2 = 原兜底 0.10/2 刻）
        _hh_eff = self._set_eff(actor, "holy_halo_shield", 4)
        if _hh_eff and int(dmg) > 0:
            _hh_params = (_hh_eff or {}).get("params") or {}
            _hh_turn = self._tick_no()
            if (EFF or {}).get("holy_halo_used") != _hh_turn:
                _hh_sh = int(dmg * float(_hh_params.get("shield_pct", 0.10)))
                if _hh_sh > 0:
                    self._add_shield("holy_halo", _hh_sh, int(_hh_params.get("shield_turns", 2) or 2))
                    EFF["holy_halo_used"] = _hh_turn
                    logs.append(f"✨ 圣辉圣环：{_hh_sh} 点伤害化为护盾！")

        return dmg, False
    def _post_hp_lethal(self, actor: dict, dmg: int, logs: list) -> None:
        """v177 扣血后处理（玩家 actor：特效装备阈值/复活链——不死鸟/死亡契约/血怒·不灭/铁誓·不动）。
        怪物 actor 无这些数据源 → 空转（死亡已在 _damage_actor 前置移除）。副作用全在 self + actor + logs。"""
        if not actor or not actor.get("class_name"):
            return
        B = actor.setdefault("buffs", {})
        EFF = actor.setdefault("eff", {})
        RES = actor.setdefault("resources", {})
        MS = actor.setdefault("stacks", {})
        # v140 波3.1：特效装备生命阈值（时光凝滞/磐石守护/苍穹庇护/石像鬼之心/不灭意志）
        # + 不灭意志免疫致死（本刻免疫致死伤害，扣血后回拉）
        try:
            from .core.weapon_effects import proc as _we_proc
            _we_proc(self, actor, "threshold", {"dmg": dmg}, logs)
            if EFF.get("we_undying_immune"):
                if actor.get("hp", 0) <= 0:
                    actor["hp"] = max(1, int(actor.get("max_hp", actor.get("hp", 1)) * 0.10))
                    logs.append("✨ 不灭意志：你撑住了致命一击！")
                EFF.pop("we_undying_immune", None)
            # 死亡之舞：受击伤害 35% 转为缓伤池（刻开始结算 10%）
            if EFF.get("we_death_pool") is not None:
                EFF["we_death_pool"] = float(EFF.get("we_death_pool", 0) or 0) + dmg * 0.35
        except Exception as _sw_e:
            _battle_warn('_post_hp_lethal', _sw_e)
            pass
        # v140 波3.2：不死鸟之羽复活——致死时以 revive_hp% 生命复活 1 次（+ 减伤 buff）
        if actor["hp"] <= 0 and (EFF or {}).get("phoenix_revive") and not (EFF or {}).get("phoenix_consumed"):
            _pr = EFF.get("phoenix_revive") or {}
            EFF["phoenix_consumed"] = True
            actor["hp"] = max(1, int(actor.get("max_hp", actor.get("hp", 1)) * float(_pr.get("hp", 0.30) or 0.30)))
            _prt = max(1, int(_pr.get("turns", 3) or 3))
            B["reduce_all"] = max(float(B.get("reduce_all", 0) or 0),
                                             float(_pr.get("dmg_reduce", 0.20) or 0.20))
            actor["reduce_all_left"] = max(int(actor.get("reduce_all_left", 0) or 0), _prt)
            logs.append(f"🪶 不死鸟之羽燃尽！你以 {actor['hp']} HP 复活，获得减伤！")
        # v107 死亡契约（暗影祭司）：致死时牺牲一个召唤物以 20% HP 存活（每场 1 次）
        # v180-C S3 修正：只牺牲"召唤物"（kind=summon）——宠物 actor 不是可牺牲祭品
        if actor["hp"] <= 0 and self.summons and not self._death_pact_used:
            for _pn, _ps in self._passive_map(actor)["proc"].get("death_pact", []):
                self._death_pact_used = True
                # 只从 kind=summon 里选祭品（优先尾部，等价旧 pop 语义但跳过宠物）
                _sacrifice_pool = [c for c in self.companions if c.get("kind") == "summon"]
                fallen = _sacrifice_pool.pop() if _sacrifice_pool else None
                if fallen is None:
                    self._death_pact_used = False  # 无召唤物可牺牲 → 不消耗契约
                    break
                self.companions.remove(fallen)
                actor["hp"] = max(1, int(actor.get("max_hp", actor["hp"]) * 0.20))
                logs.append(f"💀 死亡契约！{fallen.get('name', '亡灵')} 替你承受了致命一击，你以 {actor['hp']} HP 站起！")
                break
        # v169.7 死亡契约（牧师死灵线数据化：proc death_contract 信念≥5 + 骷髅在场）——
        # 与上方 v107 暗影祭司旧死亡契约（proc death_pact 无条件）并存；两条链都消费致死钩子
        if actor["hp"] <= 0 and not self._death_pact_used:
            try:
                _faith_v = float(RES.get("faith", 0) or 0)
                _skels = [s for s in self.summons if s.get("tid") == "skeleton" and s.get("hp", 0) > 0]
                for _pn, _ps in self._passive_map(actor)["proc"].get("death_contract", []):
                    if _faith_v < float(_ps.get("faith_req", 5) or 5):
                        continue
                    if not _skels:
                        logs.append("💀 死亡契约：信念已足但没有骷髅代受致命一击！")
                        continue
                    self._death_pact_used = True
                    fallen = _skels.pop()
                    self.companions.remove(fallen)
                    actor["hp"] = max(1, int(actor.get("max_hp", actor["hp"]) * float(_ps.get("hp_pct", 0.20) or 0.20)))
                    logs.append(f"💀 死亡契约：信念 {_faith_v:.0f} 引动契约，{fallen.get('name', '骷髅')} 代受致命伤，你以 {actor['hp']} HP 站起！")
                    break
            except Exception as _sw_e:
                _battle_warn('_post_hp_lethal', _sw_e)
                pass
        # v169.7 血怒·不灭（战士攻线·狂暴）：狂暴中首次致死 → 清空战意复活 30% 生命（每场 1 次）
        if actor["hp"] <= 0 and not getattr(self, "_berserk_revive_used", False):
            try:
                from .core.battle_modes import dual_form_active as _dfa169
                if _dfa169(actor):
                    for _pn, _ps in self._passive_map(actor)["proc"].get("berserk_revive", []):
                        self._berserk_revive_used = True
                        # 清空战意（血怒·不灭承诺「清空战意复活」）
                        MS["zhan_yi"] = 0
                        actor["hp"] = max(1, int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("hp_pct", 0.30) or 0.30)))
                        logs.append(f"🔥 血怒·不灭！狂暴意志撑住了致命一击，你以 {actor['hp']} HP 站起（战意已清空）！")
                        break
            except Exception as _sw_e:
                _battle_warn('_post_hp_lethal', _sw_e)
                pass
        # v169.7 铁誓·不动（战士守线·守护姿态）：守护姿态下首次致命伤害免疫，随后清空全部战意
        if actor["hp"] <= 0 and not getattr(self, "_stance_immortal_used", False) \
                and B.get("stance_guard"):
            try:
                for _pn, _ps in self._passive_map(actor)["proc"].get("stance_immortal", []):
                    self._stance_immortal_used = True
                    B.pop("stance_guard", None)
                    MS["zhan_yi"] = 0
                    actor["hp"] = max(1, int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("hp_pct", 1.0) or 1.0)))
                    logs.append(f"🛡️ 铁誓·不动！守护姿态替你挡下致命一击（战意已清空）！")
                    break
            except Exception as _sw_e:
                _battle_warn('_post_hp_lethal', _sw_e)
                pass

    def _on_taken_rewards(self, actor: dict, logs: list) -> None:
        """v177 受击后奖励结算（玩家 actor：受击资源/词条/连击惩罚/回血；怪物 actor 无 class → 空转）。
        由 _damage_actor 扣血后调用（存活才触发）。副作用全在 self + logs。"""
        if not actor or not actor.get("class_name"):
            return
        B = actor.setdefault("buffs", {})
        EFF = actor.setdefault("eff", {})
        RES = actor.setdefault("resources", {})
        MS = actor.setdefault("stacks", {})
        # v2.0 核心资源：受击获取（战士怒气/牧师信仰/拳师气）
        cls = actor.get("class_name", "")
        rd = E.core_resource_def(cls)
        # v151 隐藏职业删除：星语猎印 on_hit 双语义解耦白名单已移除（受击按 on_hit 正常读）
        if rd and rd.get("on_hit"):
            k = rd["key"]
            gain = int(rd["on_hit"])
            # v130.2 战士血债怒火（攻线·狂战士 T1）：受击回怒 = 1 + ⌊缺失HP%×4⌋，封顶 5
            #   （warrior_转职 下放签名：卖血换怒——满血+1、缺25%血+2、缺一半+3、濒死+5）
            if k == "rage" and self._is_path(actor, 1):  # v176: 资源键判（原 cls_zhan_shi 特判）
                _max = max(1, actor.get("max_hp", 1) or 1)
                _missing = max(0.0, min(1.0, 1.0 - (float(actor.get("hp", 0) or 0) / _max)))
                gain = int(RAGE_GAIN_HP_SCALE.get("base", 1) or 1)
                gain += int(_missing * float(RAGE_GAIN_HP_SCALE.get("coef", 4.0) or 4.0))
                gain = min(int(RAGE_GAIN_HP_SCALE.get("cap", 5) or 5), gain)
            RES[k] = self._res_gain_class(cls, k, gain)
        # v130.2 资源增幅：受击触发（沸腾战血 3 刻内受击额外 +2 怒，P0-1 消费端；持续时长制 turns 衰减）
        _amp_th = self._amp_resource(actor, "on_hit_taken")
        if _amp_th:
            logs.append(f"⚡ 沸腾战血：受击额外资源 +{_amp_th}！")
        # v130.2c 资源词条：受击（浴血 怒气/虔诚护符 信仰/磐息 气 +1；残血灼薪 血量条件判定）
        self._affix_res_proc(actor, "on_taken", logs)
        # v151 隐藏职业删除：暮影影步受击清空（原 cls_shadow_blade 专属）已移除
        # v130.2 刺客攻线·影舞者：受击回退 -1 连击点 + 连段归零（高风险高回报，assassin_转职 §1.0）
        if self._combo_active(actor):  # v176: combo归属已数据化COMBO_CFG
            _pen = int(ASSASSIN_ON_TAKE_HIT_PENALTY or 0)
            cur_cp = int(RES.get("cp", 0) or 0)
            if cur_cp > 0 and _pen < 0:
                penalty = min(cur_cp, -_pen)
                RES["cp"] = cur_cp - penalty
                logs.append(f"🗡️ 受击！连击点 -{penalty}({RES['cp']}/{rd['max'] if rd else 5})")
            self._combo_break(actor, self._combo_keep_chance(actor))
        # v140 S1 直连消费：拳心回流（tie_shou_blood）——受击 30% 概率回复 3% 最大生命
        if self._set_eff(actor, "tie_shou_blood", 4) and actor.get("hp", 0) > 0:
            if random.random() < 0.30:
                _ts_heal = int(actor.get("max_hp", actor.get("hp", 1)) * 0.03)
                self._heal_actor(actor, _ts_heal, logs)  # v180E 统一落地
                logs.append(f"🩸 拳心回流：气血奔涌，回复 {_ts_heal} 点生命！")
        # v110.3 P2-9：被动·神圣坚韧——受击后按 chance 概率回复 pct 生命（数据驱动 dmg_taken_heal，替代名字硬匹配）
        if actor["hp"] > 0:
            for _pn, _ps in self._passive_map(actor)["proc"].get("dmg_taken_heal", []):
                if random.random() < float(_ps.get("chance", 0.2)):
                    heal = int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("pct", 0.05)))
                    self._heal_actor(actor, heal, logs)  # v180E 统一落地
                    logs.append(f"✨ {_pn}：回复 {heal} 点生命！")

    def _actor_stats_of(self, actor: dict) -> dict:
        """v177 actor 面板聚合：玩家 → 职业/装备/被动全量公式；怪物 → 怪物 stats+buffs。
        （数据路由：面板来源不同是数据事实，结算逻辑不分身份）
        v180-B：带 class_name 的怪（actor_cfg 配置职业）也走玩家公式——面板同构。
        注意：身份判定不依赖 class_name（怪可配 class_name 扮职业仍属敌方），
        状态容器路由看 _is_player_side（见 _damage_actor）。"""
        if actor.get("class_name"):
            return self._player_stats(actor)
        return self._enemy_stats(actor)

    def _is_player_side(self, actor: dict) -> bool:
        """v180-B actor 状态容器路由判定：actor 是否当前焦点玩家（状态在 Battle 单套焦点
        字段 p_buffs/resources/...）。玩家本体/副本当前操作玩家 → True（焦点字段）；
        怪（含配 class_name 扮职业的，side=enemy）/PVP 敌方快照 → False（actor 自身 dict）。
        判定：① side 显式 player/enemy 优先（v180-B actor 化字段）；② 引用相等
        （actor is self.player / allies 内——副本切焦点换绑）；③ 兼容兜底：带 class_name
        且无 side=enemy 且非"显然敌方"（有 id 无 qq_id 的怪模板）视为玩家侧。"""
        if not actor:
            return False
        _side = actor.get("side")
        if _side is not None:
            return _side == "player"
        try:
            if actor is self.player:
                return True
            for _al in (self.allies or []):
                if _al is actor:
                    return True
            # 兜底：带 class_name 的玩家侧——无 side 老玩家 dict / 测试玩家（可能无 qq_id）。
            # 排除：在 enemies 阵列（怪/PVP 敌方快照，即使带 class_name 也是被打目标）；
            # 正规怪扮职业 build_monster 已设 side=enemy 由 ① 拦截。
            if actor.get("class_name"):
                try:
                    if any(u is actor or u.get("uid") == actor.get("uid") for u in (self.enemies or [])):
                        return False
                except Exception as _sw_e:
                    _battle_warn('_is_player_side', _sw_e)
                    pass
                if actor.get("side") in (None, "player"):
                    return True
        except Exception as _sw_e:
            _battle_warn('_is_player_side', _sw_e)
            pass
        return False

    def _actor_on_taken(self, actor: dict, logs: list) -> None:
        """受击钩子（actor.on_taken dict → 受击回血/激怒/凝甲）。字段即能力——
        v180-B：不看 class_name（怪扮职业仍保留钩子；玩家配 on_taken 也能触发），
        只按 actor 是否声明 on_taken。由 _damage_actor 扣血后调用（存活才触发）。"""
        if not actor or not actor.get("on_taken"):
            return
        try:
            # v177 actor on_taken 受击钩子（怪物 actor 配置 on_taken → 受击触发；玩家 actor 无此字段空转）
            # 主动伤害才触发（DOT wake_sleep=False 已由 _deal_damage 前置过滤——此处 _ot_wake 参数控制）
            if actor.get("hp", 0) > 0:
                try:
                    _ot = actor.get("on_taken") or {}
                    if _ot:
                        _tn = actor.get("name", "怪物")
                        # 受击回血（cd 刻内不重复）
                        _ot_h = _ot.get("heal") if isinstance(_ot.get("heal"), dict) else {}
                        _hp = float(_ot_h.get("pct", 0) or 0)
                        if _hp > 0:
                            _last_hl = actor.get("_ot_heal_tick")
                            _cd_hl = int(_ot_h.get("cd", 2) or 2)
                            if _last_hl is None or self._tick_no() - int(_last_hl or 0) >= _cd_hl:
                                _hl = max(1, int(actor.get("max_hp", 1) * _hp))
                                self._heal_actor(actor, _hl, logs)  # v180E 统一落地
                                actor["_ot_heal_tick"] = self._tick_no()
                                logs.append(f"🩹 【{_tn}】受击回血 +{_hl}！")
                        # 受击加攻（复仇：atk/matk +pct，turns 刻，绝对 tick 自管理）
                        _au = _ot.get("atk_up") if isinstance(_ot.get("atk_up"), dict) else {}
                        _aup = float(_au.get("pct", 0) or 0)
                        if _aup > 0:
                            _turns = max(1, int(_au.get("turns", 2) or 2))
                            _bd = actor.setdefault("buffs", {})
                            _until = self._tick_no() + _turns
                            if int(_bd.get("_atk_up_until", 0) or 0) < self._tick_no():
                                _bd["_atk_up_val"] = _aup
                            else:
                                _bd["_atk_up_val"] = max(float(_bd.get("_atk_up_val", 0) or 0), _aup)
                            _bd["_atk_up_until"] = max(int(_bd.get("_atk_up_until", 0) or 0), _until)
                            logs.append(f"🔥 【{_tn}】受击激怒！攻击提升 {int(_aup * 100)}%（{_turns} 刻）")
                        # 受击转盾（存 actor["shields"] dict）
                        _sh = _ot.get("shield") if isinstance(_ot.get("shield"), dict) else {}
                        _shp = float(_sh.get("pct", 0) or 0)
                        if _shp > 0 and not actor.get("shields"):
                            _sv = max(1, int(actor.get("max_hp", 1) * _shp))
                            actor.setdefault("shields", {})["on_taken"] = {"value": _sv, "halve": True}
                            logs.append(f"🛡️ 【{_tn}】受击凝甲！护盾 +{_sv}")
                except Exception as _sw_e:
                    _battle_warn('_actor_on_taken', _sw_e)
                    pass
        except Exception as _sw_e:
            _battle_warn('_actor_on_taken', _sw_e)
            pass

    def _damage_actor(self, actor: dict, dmg: int, logs: list, source: str = "伤害",
                      attacker: dict | None = None, true_dmg: bool = False,
                      wake_sleep: bool = True, dmg_kind: str = "") -> int:
        """v177 统一承伤核心（actor-agnostic）：玩家/怪物共用同一份受击结算。

        结算逻辑不再区分身份——只按 actor 声明的字段走：
          - 挡刀(召唤侧) / 闪避(dodge) / 格挡(block) / 减伤(reduce*) / 护盾(shields) / 扣血
          - 受击反应：玩家 actor 查玩家数据源(被动/套装/词条/职业模式)；怪物 actor 查 on_taken dict
        true_dmg=True（v178.1 真伤/腐蚀）：怪物 halve 盾不减半——盾层全额吸收后剩余穿透
        （v110 真伤口径：真伤不被打折，护盾层仍吸收）。
        v180F 收编敌方普攻配套：dmg_kind = 伤害类型（"phys"/"magi"/"true"/""）——玩家受击的
        phys_reduce/magic_reduce 百分比免伤统一在此消费（原只在敌方普攻手写段实现，管线/
        技能/AOE 打玩家一直没吃玩家免伤 = 隐藏 bug）。缺省 "" 不减免（兼容旧调用）。

        返回实际扣血（玩家死亡由上层处理；怪物死亡即时移除单位）。
        """
        # ---- v180-B actor 状态容器（玩家/怪/新 actor 同构，一律读 actor dict）----
        # v177 曾按 _is_player_side 分叉（玩家→Battle 焦点字段/怪→actor dict）；
        # v180-B ①后玩家战斗可变状态权威已迁入玩家 actor dict（__init__ 播种），
        # 分叉退化——B/EFF/RES/MS/CH/HITS/SH/RL 全部读 actor 自身字段。
        # 唯一保留的语义判定：玩家被打时反击/反伤目标 = 当前敌人（TARGET）。
        B = actor.setdefault("buffs", {})
        EFF = actor.get("eff") or {}
        RES = actor.setdefault("resources", {})
        MS = actor.setdefault("stacks", {})
        CH = actor.get("charging")
        HITS = actor.get("buff_hits") or {}
        SH = actor.setdefault("shields", {})
        RL_ALL = int(actor.get("reduce_all_left", 0) or 0)
        RL = int(actor.get("reduce_left", 0) or 0)
        if dmg <= 0:
            self._pending_dmg_lines = []
            return 0
        _hp_before = int(actor.get("hp", 0) or 0)  # v177 实际扣血基准（返回用）
        # v2 蓄力打断：蓄力中受到主动伤害>0 → 打断并返还 50% MP（§6.2规则4）
        # v180-B：wake_sleep=False（DOT）不打断蓄力——原 v177 后此判断丢 wake_sleep 过滤，
        # DOT 也会打断怪蓄力（test_v114 DOT 不打断蓄力回归）
        if wake_sleep and CH and CH.get("skill"):
            pname = actor.get("name", "你")
            cname = CH.get("name", CH.get("skill", "?"))
            spent = int(CH.get("mp_spent", 0) or 0)
            # v177 actor 化：局部别名赋值无效，真清状态容器（玩家 self._p_charging() / 怪物 actor["charging"]）
            actor["charging"] = None
            logs.append(f"🔨 【{pname}】的蓄力被{source}打断了！")
            if spent > 0:
                actor["mp"] = min(actor.get("max_mp", actor.get("mp", 0)),
                                   actor.get("mp", 0) + (spent + 1) // 2)
                logs.append(f"✨ 返还了 {(spent + 1) // 2} 点魔力。")
        # 24 章宠物技能·影袭：替主人挡一次攻击（主动保护优先于自身闪避，拦截后直接结束本次伤害）
        # v180-B：宠物/召唤物挡刀只服务主人（玩家受击）——怪受击也调 _damage_actor 后
        # 此段曾对怪触发（召唤技能打怪→怪受击→玩家召唤物挡刀自杀，v177 actor 化回归）
        # v180E 阶段3：absorb(宠物影袭) + redirect(召唤物) 双模式合一 _guard_check
        # v180F B4：挡刀服务**受击者本人**（任意玩家侧 actor）——随从按 owner 归属挡自己主人的刀
        dmg = self._guard_check(dmg, logs, actor)
        if dmg <= 0:
            # O116 还原原顺序：先报攻击伤害，再报挡刀
            _pl = self._drain_pending_dmg()
            if _pl:
                logs[:] = _pl + logs
            return 0
        if self._roll_dodge(actor, logs):
            return 0
        # O116 命中：此刻才输出"造成 X 点伤害"日志（此前由 _enemy_turn 延迟暂存）
        logs += self._drain_pending_dmg()
        # v180F 防御格挡下沉承伤链：玩家 defending 时敌方伤害在此减免（原只在 _process_until
        # 主调用处对"返回 dmg"生效——v180 怪技能收编管线后管线内部扣血、主调用处格挡失效，
        # 防御对怪技能/普攻全部失效（double dip 掩盖）。统一在此消费：管线/手写/AOE 全吃格挡。
        if dmg > 0 and actor.get("defending"):
            try:
                _dr = DEFEND_REDUCE
                _cc = self._cast_ctx or {}
                _ck = None
                if isinstance(_cc, dict):
                    _ck = _cc.get("_cast_skill") or (_cc.get("_cast") or {}).get("skill")
                if _ck:
                    _evi = self._lookup_skill_info(str(_ck))
                    _evdr = _evi.get("defend_reduce") if _evi else None
                    if isinstance(_evdr, (int, float)) and 0 <= float(_evdr) <= 0.95:
                        _dr = float(_evdr)
                dmg = max(1, int(round(dmg * (1.0 - _dr))))
            except Exception as _sw_e:
                _battle_warn('_damage_actor', _sw_e)
                pass
        # v180F 收编敌方普攻配套：玩家受击百分比免伤统一在此消费（phys_reduce/magic_reduce）。
        # 原只在敌方普攻手写段实现（管线/技能/AOE 打玩家不吃 = 隐藏 bug）；现按 dmg_kind
        # 减免——含 phys 段减物免、含 magi 段减魔免；true/缺省不减免。
        if dmg_kind and dmg > 0:
            try:
                _pr_st = self._actor_stats_of(actor)
                _kd = str(dmg_kind or "")
                if _kd in ("phys", "phys_magi") or "phys" in _kd:
                    _ppr = min(float(_pr_st.get("phys_reduce", 0) or 0), 0.4)
                    if _ppr > 0:
                        red = max(1, int(dmg * _ppr))
                        dmg = max(1, dmg - red)
                        logs.append(f"🪨 物理免伤，减免 {red} 点物理伤害！")
                if _kd in ("magi", "phys_magi") or "magi" in _kd:
                    _mpr = min(float(_pr_st.get("magic_reduce", 0) or 0), 0.4)
                    if _mpr > 0:
                        red = max(1, int(dmg * _mpr))
                        dmg = max(1, dmg - red)
                        logs.append(f"🛡️ 魔法抗性，减免 {red} 点魔法伤害！")
            except Exception as _sw_e:
                _battle_warn('_damage_actor', _sw_e)
                pass
        dmg, _interrupted_m = self._mitigate_chain(actor, dmg, logs)
        if _interrupted_m:
            return 0
        dmg, _interrupted = self._retaliations_and_buffs(actor, dmg, logs, attacker=attacker)
        if _interrupted:
            return 0
        # v177 actor 护盾吸收：玩家盾全额吸收；怪物盾 halve=True（受伤减半先扣盾，Boss 语义）
        # v178.1 true_dmg：真伤不减半——盾层全额吸收后剩余穿透（v110 真伤口径）
        shields = SH
        if shields:
            if any(isinstance(s, dict) and s.get("halve") for s in shields.values()) \
                    and not true_dmg:
                # 怪物 halve 盾：受伤减半后由盾吸收（与旧 _boss_dmg_filter 同款：real=dmg*0.5 先扣盾）
                _pre = sum(int(s.get("value", 0)) for s in shields.values())
                dmg = self._absorb_shields(shields, int(dmg * 0.5), logs, label="✨")
                if _pre and not shields:
                    logs.append("💥 护盾破碎！")
                if dmg <= 0:
                    return 0
            else:
                # 玩家盾（或怪物无 halve 盾 / 真伤）：全额吸收（真伤盾层全额扣，剩余穿透）
                _pre = sum(int(s.get("value", 0)) for s in shields.values()) if shields else 0
                dmg = self._absorb_shields(shields, dmg, logs, label="✨")
                if _pre and not shields:
                    pass  # 玩家盾破不额外报（_absorb_shields 已报吸收量）
                if dmg <= 0:
                    return 0
        # v142 数据驱动：S1 受击直连已迁至 _set_taken_proc（ferry_repel/tie_pi_bulwark/tie_pi_harden/shou_wang_ward/tie_shou_blood）
        actor["hp"] = max(0, actor.get("hp", 0) - dmg)
        # v177 actor 统一：怪物死亡即时移除单位（玩家死亡走下方复活链）
        _in_enemies = any(u is actor or u.get("uid") == actor.get("uid") for u in self.enemies)
        if _in_enemies and actor.get("hp", 0) <= 0:
            self._remove_unit("enemy", actor)
            return max(0, _hp_before - int(actor.get("hp", 0) or 0))
        self._actor_on_taken(actor, logs)
        self._post_hp_lethal(actor, dmg, logs)
        self._on_taken_rewards(actor, logs)

        # v177 actor 统一：返回实际扣血量（扣血基准 = 进入函数时的 hp - 最终 hp，含后续回血取扣血前）
        return max(0, _hp_before - actor.get("hp", 0))

    def _enemy_dead(self) -> bool:
        # v2：敌方阵列无存活（§3.2）——同时压缩移除死亡单位
        from .core.formation import alive_units
        return not alive_units(self.enemies)

    def _alive_side_names(self) -> list:
        """v180F B7：存活阵营名列表（通用 actor 引擎——任意 side 结构）。

        玩家侧 = sides 里 side=player 的成员（玩家/队友/随从）；敌方侧 = 各 side 组。
        无 sides（旧战斗）→ 按 player/enemies 传统判定。
        """
        sides = getattr(self, "sides", None)
        if not sides:
            # 旧战斗：玩家存活 → player；enemies 存活 → enemy
            out = []
            _pl = getattr(self, "player", None) or {}
            if _pl.get("hp", 0) > 0 or _pl.get("class_name") or _pl.get("name") or _pl.get("qq_id"):
                if _pl.get("hp", 1) > 0:
                    out.append("player")
            if any(u.get("hp", 0) > 0 for u in (self.enemies or [])):
                out.append("enemy")
            return out
        alive = []
        for _sn, _acts in sides.items():
            if not _acts:
                # 空阵营：player side 未绑成员但 self.player 已有真玩家（测试/命令层后绑）
                # → 按 self.player 存活计；其它空阵营忽略
                if _sn == "player":
                    _pl = getattr(self, "player", None) or {}
                    if _pl.get("class_name") or _pl.get("name") or _pl.get("qq_id"):
                        if _pl.get("hp", 1) > 0:
                            alive.append("player")
                continue
            if any(a.get("hp", 0) > 0 for a in _acts):
                alive.append(_sn)
        return alive

    def _check_side_end(self, logs: list) -> str | None:
        """v180F B7：通用战斗结束判定——存活阵营 ≤1 即结束。

        返回胜利阵营名（无玩家战斗怪vs怪 → 剩哪个 side 哪个赢）；
        常规战斗（player vs enemy）兼容旧 result 语义（victory/defeat）。
        未结束返回 None。
        """
        alive = self._alive_side_names()
        if len(alive) > 1:
            return None
        if len(alive) == 0:
            # 全灭（同归于尽）→ 视玩家是否存活定结果
            return "draw"
        winner = alive[0]
        if "player" in self._side_names_all() and winner == "player":
            self.result = "victory"
        elif "player" in self._side_names_all() and "player" not in alive:
            self.result = "defeat"
        else:
            # 无玩家战斗：result 记胜利阵营（命令层可读 winner_side）
            self.result = winner
            self.winner_side = winner
        return winner

    def _side_names_all(self) -> list:
        sides = getattr(self, "sides", None)
        if sides:
            return list(sides.keys())
        return ["player", "enemy"]

    def _actor_dead(self, actor: dict) -> bool:
        """v180G B3-改名：单 actor 是否死亡（hp<=0）——任意 actor 通用（玩家/怪/随从）。
        原 _player_dead 名误导（实查任意 actor），随从/宠物 owner/怪全走此判定。"""
        return actor.get("hp", 1) <= 0