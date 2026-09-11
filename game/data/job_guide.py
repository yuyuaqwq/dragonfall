# -*- coding: utf-8 -*-
"""数据层 - job_guide.py（v130.2g 新增：12 职业速查数据表）

『职业』/『职业 <名称>』指令的只读数据源（玩家意见 #1 zerc「增加查看职业信息的功能」落地）。
12 职业 = 基础六职业 + 隐藏六职业（见习冒险者 cls_novice = 初始状态，不计入）。

单一数据来源（防漂移，tests/test_v1302g_job_guide.py 强校验）：
  - name/desc/role/rank_label/reach/evolve_branches/hint/src_base/src_race/aliases
    → classes.py（本表逐字段复制，desc 逐字相等）
  - 核心资源展示 → v181.M-R2c 单源化（原 data/core_resources.py 已退役删除）：
      · 职业核心资源 key + 机制 desc → 本表 CORE_RESOURCE_GUIDE（六基础职业 cid→{key, desc}，
        desc 自原表逐字迁移）；name/max → EFFECT_RULES[key].name/.cap 派生（battle_rules.py 唯一权威，不重复存）
      · 牧师攻线·歌者双资源 共鸣/回声 → 本表 EXTRA_RESOURCE_GUIDE（{name, max, desc} 全量，
        不在 EFFECT_RULES；经 EXTRA_RESOURCES 按职业合并展示）
  - 本表仅补充（全部有底层出处）：
      POSITION_BRIEF   一览定位一句话（必须为 classes desc 的子串）
      EXTRA_ALIASES    查询兼容名（歌者→牧师，v130.2 牧师攻线·歌者双资源）
      _BASE_TIER_LEVELS 与核心常量 EVOLVE_LEVELS={1:30,2:60,3:90} 同源（测试断言相等）
"""
import re

from .battle_rules import EFFECT_RULES
from .classes import CLASSES
from .races import RACES

# 分支 key → 展示名（与 commands/player.py _BRANCH_KEY_DISPLAY 同源：
# v130.2f.2 苦修线改名——武僧→淬势者、大地武僧→锻势行者；branch key 与
# skills.py BRANCH_SKILLS 强耦合不可动，展示层映射）
BRANCH_KEY_DISPLAY = {
    "武僧": "淬势者",
    "大地武僧": "锻势行者",
}

# 基础职业转职门槛（core/constants.py EVOLVE_LEVELS 同源，测试断言相等）
_BASE_TIER_LEVELS = {1: 30, 2: 60, 3: 90}
# 隐藏线档位门槛缺省（classes.py tier_levels 未配置时，按 09_职业体系.md 统一 40/60/90）
_HIDDEN_TIER_LEVELS = {1: 40, 2: 60, 3: 90}

# 一览/详情定位一句话：必须为 classes.py desc 的子串（测试强校验，改 desc 必同步）
POSITION_BRIEF = {
    "cls_zhan_shi": "身穿重甲、手持巨剑的钢铁壁垒，正面硬刚一切敌人",
    "cls_fa_shi": "掌控元素之力的施法者，输出爆炸但身板脆弱",
    "cls_you_xia": "敏捷的弓箭手，箭无虚发，暴击与闪避的艺术家",
    "cls_mu_shi": "信仰圣光的神职者，能打能奶，队伍的灵魂",
    "cls_ci_ke": "暗影中的利刃，出手必见血，暴击与闪避的极致",
    "cls_wu_seng": "以拳入道的修行者，拳拳到肉，连击与反击的行家",
    "cls_shi_ren": "怀抱诗琴的吟游诗人，旋律即力量——唱响战歌鼓舞全队，或以挽歌瓦解敌阵",
}

# classes.py aliases 之外的查询兼容名（职业名兼容层；classes aliases 自动并入 JOB_ALIASES）
EXTRA_ALIASES = {
    "歌者": "cls_mu_shi",     # 牧师攻线·歌者（吟游诗人→灵魂歌者→黎明颂者，v130.2 双资源）
    "歌者线": "cls_mu_shi",
}

# 转职分支专属核心资源：分支职业 → 资源 key 列表（副资源 key 的 name/max/desc 展示元数据
# 在本表 EXTRA_RESOURCE_GUIDE；v181.M-R2c 原 core_resources.py 表尾段已退役迁入）
EXTRA_RESOURCES = {
    "cls_mu_shi": ["resonance", "echo"],  # v130.2 牧师攻线·歌者双资源 共鸣 + 回声
}

# ============================================================
# 职业核心资源展示元数据（v181.M-R2c：原 game/data/core_resources.py 退役，展示表单源化）
# 六基础职业 cid → {key, desc}；name/cap 不重复存——运行时从 EFFECT_RULES[key].name/.cap
# 派生（battle_rules.py，唯一权威）。desc 为『职业』详情玩家可见的机制一句话，自旧表逐字迁移。
# cls_shi_ren（诗人 v153 起独立第 7 职业）无核心资源 → 不在表内（JOB_GUIDE resource_* 为空）。
# 注：原表 v139 形态字段（dual_form/focus/vent 等）与按 key 注册的 vow 副资源设计值随文件退役，
#   已全文留档 docs/REFACTOR_v181_CLASS_MECH_ASSEMBLY.md『v139 形态层设计留档』章（引擎批次 2 启用时自该章还原）。
# ============================================================
CORE_RESOURCE_GUIDE = {
    "cls_zhan_shi": {
        "key": "rage",
        "desc": "通用基座：普攻/技能/受击三路攒怒，满 10 掷背水一战，满溢转盾(overflow_shield)兜底；血债/沸血/壁垒等血线玩法下放转职线",
    },
    "cls_fa_shi": {
        "key": "element",
        "desc": "充能条 0-5：基础不经营(纯蓝施法)，攻线·元素/守线·奥秘转职首获；施法攒充能、-1/-2/-3/-5 消耗",
    },
    "cls_you_xia": {
        "key": "energy",
        "desc": "专注流量制：每刻 +18 持续充能，技能消耗专注；结余 ≥40 时凝神暴击；满弦/叠标/引爆下放转职线",
    },
    "cls_mu_shi": {
        "key": "faith",
        "desc": "负载制 0-10：治疗攒点(on_heal +2)/受击 +1，档位 0-3/4-7/8-9/10(过载)，每刻 −0.7；圣光/死灵两线共用",
    },
    "cls_ci_ke": {
        "key": "cp",
        "desc": "通用基底：普攻/技能命中 +1，2-4 刻攒满即爆发；连段/受击回退/暴击攒点全部下放转职线",
    },
    "cls_wu_seng": {
        "key": "chi",
        "desc": "通用基底：出招攒气(连段技额外多给)，3 气崩拳/10 气破岳拳双档，满溢转盾(overflow_shield)兜底；蓄势/受击换气下放转职线",
    },
}

# 转职分支专属副资源展示元数据（EXTRA_RESOURCES 展示用；不在 EFFECT_RULES——歌者专属，
# 引擎批次 2 才启用）：资源 key → {name, max, desc} 全量（desc 自旧表逐字迁移）
EXTRA_RESOURCE_GUIDE = {
    "resonance": {
        "name": "共鸣", "max": 10,
        "desc": "歌者短周期燃料条：歌类/咏叹技 +1(治疗赛诗 +2)，消耗放大增益/大招(启明圣咏 -3 / 终章·黎明颂歌 -5)，攒满约 4 刻",
    },
    "echo": {
        "name": "回声", "max": 3,
        "desc": "歌者长周期驻留叠层：战斗内不清零；每层刻一始全队恢复 6 点体力（v153 后回声仅由带 res_gain.echo 的技能产出）",
    },
}


def _core_resource_of(cid: str) -> dict:
    """JOB_GUIDE resource_* 字段数据源：CORE_RESOURCE_GUIDE(key/desc) + EFFECT_RULES(name/cap) 派生。

    返回 {key, name, max, desc}（无条目职业 → 全空/0，同旧表未注册口径）。
    """
    cfg = CORE_RESOURCE_GUIDE.get(cid) or {}
    key = cfg.get("key", "")
    er = EFFECT_RULES.get(key, {}) if key else {}
    return {
        "key": key,
        "name": er.get("name", ""),
        "max": int(er.get("cap", 0) or 0),
        "desc": cfg.get("desc", ""),
    }


def _task_name(desc: str) -> str:
    """从 classes desc 自动提取隐藏线任务名：『需完成<XX>任务链解锁』"""
    m = re.search(r"需完成(.+?)任务链", desc or "")
    return m.group(1) if m else ""


def _build_guide():
    """装配 12 职业速查表（classes.py + EFFECT_RULES/CORE_RESOURCE_GUIDE 派生 + 本表摘要）"""
    guide, succ = {}, {}
    for cid, cls in CLASSES.items():
        if cid == "cls_novice":  # 见习冒险者：初始状态，不计入 12 职业
            continue
        res = _core_resource_of(cid)
        hidden = bool(cls.get("hidden"))
        guide[cid] = {
            "cls_id": cid,
            "name": cls.get("name", cid),
            "icon": cls.get("icon", "✨"),
            "role": cls.get("role", ""),
            "rank_label": cls.get("rank_label", ""),
            "reach": int(cls.get("reach", 1) or 1),
            "position": POSITION_BRIEF[cid],
            "desc": cls.get("desc", ""),
            "hidden": hidden,
            "tiers": {int(t): [BRANCH_KEY_DISPLAY.get(n, n) for n in names]
                      for t, names in (cls.get("evolve_branches") or {}).items()},
            "tier_levels": (cls.get("tier_levels")
                            or (_HIDDEN_TIER_LEVELS if hidden else _BASE_TIER_LEVELS)),
            "src_base": cls.get("src_base", ""),
            "src_race": cls.get("src_race", ""),
            "race_name": (RACES.get(cls.get("src_race", ""), {}) or {}).get("name", cls.get("src_race", "") or ""),
            "hint": cls.get("hint", ""),
            "task_name": _task_name(cls.get("desc", "")),
            "resource_key": res.get("key", ""),
            "resource_name": res.get("name", ""),
            "resource_max": int(res.get("max", 0) or 0),
            "resource_desc": res.get("desc", ""),
        }
        if hidden and guide[cid]["src_base"]:
            succ.setdefault(guide[cid]["src_base"], []).append(cid)
    base_order = [cid for cid, g in guide.items() if not g["hidden"]]
    hidden_order = [cid for cid, g in guide.items() if g["hidden"]]
    return guide, base_order, hidden_order, succ


JOB_GUIDE, BASE_ORDER, HIDDEN_ORDER, HIDDEN_SUCCESSORS = _build_guide()

# 7 职业完整性 fail-fast（v153 新增诗人：6→7；与 data/_assembly.py 同款启动即报错风格）
assert len(JOB_GUIDE) == 7, f"[job_guide] 必须覆盖 7 职业，实际 {len(JOB_GUIDE)}"
assert len(BASE_ORDER) == 7 and len(HIDDEN_ORDER) == 0, \
    f"[job_guide] 基础七/隐藏分组异常：{len(BASE_ORDER)}/{len(HIDDEN_ORDER)}"

# 别名表：classes.py aliases + 分支名（含展示名映射）+ 兼容名 EXTRA_ALIASES
JOB_ALIASES = {}
for _cid, _cls in CLASSES.items():
    if _cid == "cls_novice":
        continue
    for _a in (_cls.get("aliases") or {}):
        JOB_ALIASES[_a] = _cid
    for _names in (_cls.get("evolve_branches") or {}).values():
        for _n in _names:
            JOB_ALIASES.setdefault(BRANCH_KEY_DISPLAY.get(_n, _n), _cid)
JOB_ALIASES.update(EXTRA_ALIASES)


def resolve_job(raw):
    """职业名 → 12 职业 id。

    解析顺序（对齐『转职』路由口径）：
      1) 职业 id 或显示名（classes.py name，含 v130.2 新名 淬势者）
      2) JOB_ALIASES（classes.py aliases：苦修士/武僧→淬势者…… + 分支名 + 兼容名 歌者）
      3) 模糊子串（≥2 字）：命中 1 个返回 id、多个返回 list、0 个返回 None
    """
    if not raw:
        return None
    raw = str(raw).strip()
    if raw in JOB_GUIDE:
        return raw
    if raw in {g["name"] for g in JOB_GUIDE.values()}:
        for cid, g in JOB_GUIDE.items():
            if g["name"] == raw:
                return cid
    if raw in JOB_ALIASES:
        return JOB_ALIASES[raw]
    if len(raw) >= 2:
        hit = []
        for cid, g in JOB_GUIDE.items():
            names = [g["name"]] + [a for a, c in JOB_ALIASES.items() if c == cid]
            if any(raw in n for n in names) or any(n in raw for n in names):
                hit.append(cid)
        if hit:
            return hit[0] if len(hit) == 1 else hit
    return None