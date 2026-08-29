# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - boss_phases.py（v138.1 阶段状态机模板表）

借鉴《云海猎团》03 章 M3.2「阶段状态机」：常态→激怒→疲态→狂澜四阶段，
每阶段配「数值变化 / 行为变化 / 退出条件 / 反制窗口」四件套。
核心设计原则：阶段是内容单位不是血量单位——强度靠「要解的题」，不靠「要磨的量」。

用法：
  1. 模板表 BOSS_PHASE_TEMPLATES：四阶段通用模板，数值可逐 Boss 覆盖
  2. Boss 数据（MONSTER_MODS / INSTANCES）phases[] 条目可加 phase_id 引用模板，
     或直接内联四件套字段覆盖模板值
  3. 引擎侧（battle.py _phase_apply + battle_mech._b_phase）按模板应用数值/行为/退出/反制

字段说明（四件套）：
  - 数值变化：atk_mult / def_add / spd_add / dmg_taken_mult（承伤倍率，>1=更脆）
  - 行为变化：add_skills（换招表）/ freq_mult（行动频率倍率，<1=降频）/ ult_every（每 N 回合全场大招）
  - 退出条件：exit_turns（回合数，None=不限）/ exit_dmg（累计承伤阈值，None=不限）
  - 反制窗口：counter（反制文案，写入战报引导玩家解题）
  - 演出：icon / enter_line（进场文案）/ warn_line（预告文案）
  - 进度遗产：preserve_debuffs（阶段转换时是否保留一半异常层数，默认 True=v138.2 律三）

兼容：旧 phases[] 条目（只有 min / add_skills / script）不引用模板，引擎自动按旧行为处理。
"""

# 四阶段通用模板（数值为基准，逐 Boss 可在 phases[] 内联覆盖）
BOSS_PHASE_TEMPLATES = {
    "normal": {
        "id": "normal",
        "name": "常态",
        "icon": "⚖️",
        "atk_mult": 1.00, "def_add": 0, "spd_add": 0,
        "dmg_taken_mult": 1.00,
        "add_skills": [],
        "freq_mult": 1.00, "ult_every": None,
        "exit_turns": None, "exit_dmg": None,
        "counter": "试探招式，攒资源，别贪刀",
        "enter_line": "气息平稳，蓄势待发",
        "warn_line": None,
        "preserve_debuffs": True,
    },
    "enrage": {
        "id": "enrage",
        "name": "激怒",
        "icon": "🔥",
        "atk_mult": 1.25, "def_add": 80, "spd_add": 20,
        "dmg_taken_mult": 1.00,
        "add_skills": [],           # 逐 Boss 配 +1~2 新招
        "freq_mult": 1.00, "ult_every": None,
        "exit_turns": 8, "exit_dmg": None,
        "counter": "读招期：看清新招前摇，别贪输出",
        "enter_line": "暴怒了！攻击↑ 防御↑——",
        "warn_line": "气息开始紊乱……似乎要进入更凶猛的阶段了！",
        "preserve_debuffs": True,
    },
    "exhaust": {
        "id": "exhaust",
        "name": "疲态",
        "icon": "💧",
        "atk_mult": 0.80, "def_add": -120, "spd_add": -10,
        "dmg_taken_mult": 1.40,     # 核心件外露：等效易伤 +0.40（对应云海「疲态 H+0.40」）
        "add_skills": [],
        "freq_mult": 0.50, "ult_every": None,   # 降频：每 2 回合一动
        "exit_turns": 5, "exit_dmg": None,
        "counter": "爆发期！集中火力，把绝技砸进这个窗口！",
        "enter_line": "攻势衰竭，核心破绽外露——",
        "warn_line": "它的动作慢下来了……破绽出现了！",
        "preserve_debuffs": True,
    },
    "rampage": {
        "id": "rampage",
        "name": "狂澜",
        "icon": "🌊",
        "atk_mult": 1.50, "def_add": 150, "spd_add": 30,
        "dmg_taken_mult": 1.00,
        "add_skills": [],           # 逐 Boss 配全场大招
        "freq_mult": 1.00, "ult_every": 3,      # 每 3 回合一次全场大招
        "exit_turns": None, "exit_dmg": None,
        "counter": "破核是唯一出路！集火核心件打断大招！",
        "enter_line": "陷入狂澜！每 3 回合将释放全场大招——",
        "warn_line": "⚠️ 下回合可能释放全场大招——优先破核打断！",
        "preserve_debuffs": True,
    },
}

# 阶段顺序（默认推进顺序；逐 Boss 可在 phases[] 里按需跳过/自定义）
DEFAULT_PHASE_ORDER = ["normal", "enrage", "exhaust", "rampage"]

# 阶段四件套字段白名单（引擎 _phase_apply 只读这些键，防未知字段误入）
PHASE_NUMERIC_KEYS = ("atk_mult", "def_add", "spd_add", "dmg_taken_mult", "freq_mult")
PHASE_BEHAVIOR_KEYS = ("add_skills", "ult_every")
PHASE_EXIT_KEYS = ("exit_turns", "exit_dmg")
PHASE_SCRIPT_KEYS = ("icon", "enter_line", "warn_line", "counter", "name")


def phase_template(phase_id: str) -> dict:
    """取阶段模板（带缺省兜底，未知 id 返回常态模板）。"""
    return BOSS_PHASE_TEMPLATES.get(phase_id) or BOSS_PHASE_TEMPLATES["normal"]


def merge_phase_config(phase_id: str, overrides: dict | None = None) -> dict:
    """模板 + Boss 内联覆盖合并：模板为底，overrides 逐键覆盖。

    兼容旧数据：overrides 为空或只有旧字段（min/add_skills/script）时，
    返回模板值 + 旧字段透传，不破坏存量。
    """
    base = dict(phase_template(phase_id))
    if overrides:
        for k, v in overrides.items():
            base[k] = v
    return base
