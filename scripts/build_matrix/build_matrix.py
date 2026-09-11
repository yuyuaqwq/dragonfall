# -*- coding: utf-8 -*-
"""v175 A1 期望引擎核心 build_matrix —— 全职业×流派×加点×装备 期望矩阵。

主 agent 亲写（铁律：引擎主 agent 写）。依赖：
  - scripts/balance_data/cls_<职业>.json（职业 agent 产出，schema 校验过）
  - scripts/build_matrix/schema.py（技能名集/常量）
  - numeric_lib（build_player / gear_loadout / monster 等既有底座）
  - game engine（skill_expr_preview / calc_damage / skill_info）

口径（与 numeric_lib.player 同源，真实引擎实算）：
  1. 面板：player_final_stats（build_player 封装，attr 显式点）
  2. 流派循环：rotation（JSON 里 cond/prio 声明）→ 按 tick 模拟
  3. 伤害：skill_expr_preview 代入面板 + calc_damage 过防（variance=0）
  4. CD/MP/资源：cond 拦截 → 普攻填充（引擎 _skill_cast_blocked 同语义近似）
  5. 目标：build_monster(role, lv) 真实面板

设计决策（冻结，勿改）：
  - 资源模型：资源键 rage/energy/cp/chi/faith/resonance 各自简化累积/消耗。
    循环模拟按 JSON cond 判定；没有引擎级全机制复刻（那是 A2 真引擎的活）。
    期望模型允许近似，误差由 A2 门禁仲裁。
  - 技能等级：skill_lv = min(SKILL_UP.max, 1 + (玩家lv-技能lv)//4)，0=未解锁
  - 速度折算：interval = cast × sqrt(SPD_REF/spd)（numeric_lib._interval 同款）
  - 目标 def：build_monster(role, lv) 真实 def/mdef/max_hp

对外接口（门禁测试 import 用）：
  build_panel / class_skill_pool / rotation_dps / build_vs_boss / full_matrix
"""
from __future__ import annotations
import os, sys, json, math

_BM_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_BM_DIR)
_PLUGIN = os.path.dirname(_SCRIPTS)
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from saintess_engine.formulas import calc_damage, skill_expr_preview, skill_max_level
from game.content_rules.panel import player_final_stats
from data.plugins.dragonfall.game.data import skills as SK     # noqa: E402
from data.plugins.dragonfall.game.data import skill_up as SU   # noqa: E402

try:
    from numeric_lib.player import build_player, PlayerOptions  # noqa: E402
    from numeric_lib.gear import gear_loadout                   # noqa: E402
    from numeric_lib.constants import STAGES, LOADOUTS, TIER_GROWTH  # noqa: E402
    _HAS_NUMLIB = True
except Exception:
    _HAS_NUMLIB = False

SPD_REF = 50.0
# 资源键 → 属性键（engine 属性换算：str→atk/int→matk/agi→spd+crit/vit→hp）
ATTR_KEYS = ("str", "int", "agi", "vit")
# 职业主属性（与 numeric_lib.constants CLASSES 对齐）
CLASS_MAIN_ATTR = {
    "cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
    "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
    "cls_shi_ren": "int",
}
# 属性点来源：DEFAULT_ATTR_PTS=9 + 每级 3 点（engine/core/constants.py）
DEFAULT_ATTR_PTS = 9
ATTR_PER_LV = 3
# 阶段装备档（与 numeric_lib STAGES 对齐，P3/P4 用紫+9 是既有口径）
STAGE_CFG = [
    ("P1", 10, "solo_low"),
    ("P2", 24, "solo_mid"),
    ("P3", 45, "team_purple9"),
    ("P4", 75, "team_purple9"),
    ("P5", 95, "team_orange9"),
]


def attr_pts_of(lv: int) -> int:
    return DEFAULT_ATTR_PTS + ATTR_PER_LV * (lv - 1)


def resolve_attr(attr_preset: dict, lv: int) -> dict:
    """加点 preset → 实际点数 dict。
    - 'all'/'full' → 全投该属性
    - 数字=比例 → 按总点按比例分配（四舍五入，保证总和=总点）
    例：{"str": "all"} → {"str": 39}（lv11）
        {"str": 0.4, "agi": 0.3, "vit": 0.3} → 按 39 点分配
    """
    total = attr_pts_of(lv)
    out = {}
    if not attr_preset:
        return {}
    # 先看是否有 "all" 单投
    all_keys = [k for k, v in attr_preset.items() if str(v).lower() in ("all", "full")]
    if all_keys:
        out[all_keys[0]] = total
        return out
    # 比例分配
    fracs = {k: float(v) for k, v in attr_preset.items() if float(v) > 0}
    s = sum(fracs.values())
    if s <= 0:
        return {}
    # 最大余数法保证整数和 = total
    raw = {k: total * v / s for k, v in fracs.items()}
    assigned = {k: int(math.floor(v)) for k, v in raw.items()}
    rem = total - sum(assigned.values())
    # 按小数部分从大到小补
    order = sorted(fracs.keys(), key=lambda k: raw[k] - assigned[k], reverse=True)
    for i in range(rem):
        assigned[order[i % len(order)]] += 1
    return {k: v for k, v in assigned.items() if v > 0}


def tier_of(lv: int) -> int:
    return 3 if lv >= 90 else 2 if lv >= 60 else 1 if lv >= 30 else 0


def class_skill_pool(cls_id: str, lv: int) -> dict:
    """该等级可学全部技能名 → info dict（base 全量 + branch 按 tier 解锁）。
    tier 解锁：lv>=30 开 tier1 两线、lv>=60 开 tier2、lv>=90 开 tier3（玩家可学该线技能）。
    技能自身 lv<=玩家 lv 才可用（由调用方再筛）。
    """
    pool = {}
    cdef = SK.PLAYER_SKILLS.get(cls_id, {})
    for info in cdef.get("skills", {}).values():
        pool[info["name"]] = info
    tid = tier_of(lv)
    br = SK.BRANCH_SKILLS.get(cls_id, {}).get("branches", {})
    for tier_i, tdef in br.items():
        if tier_i > tid:
            continue
        if not isinstance(tdef, dict):
            continue
        for line, skills in tdef.items():
            if not isinstance(skills, dict):
                continue
            for info in skills.values():
                if isinstance(info, dict) and info.get("name") not in pool:
                    pool[info["name"]] = info
    return pool


def skill_lv_at(info: dict | None, player_lv: int) -> int:
    """技能等级：未解锁 0；学得时 1；此后每 4 级 +1，封顶 SKILL_UP.max。
    info=None/空（技能不在当前池/未配置）→ 返回 0（不可学）。"""
    if not info:
        return 0
    learn_lv = int(info.get("lv", 1) or 1)
    if player_lv < learn_lv:
        return 0
    max_lv = skill_max_level(info)
    grow = 1 + max(0, (player_lv - learn_lv) // 4)
    return min(grow, max_lv)


def _gear_of(lv: int, loadout: str, affix_type: str = "atk") -> dict:
    """取装备（支持 v175e 词条乘区 affix_type；naked 返回 {}）。"""
    if not loadout or loadout == "naked":
        return {}
    from numeric_lib.gear import gear_loadout as _gl
    if affix_type and affix_type != "atk":
        # 词条乘区流：手动 make_gear（gear_loadout 不带 affix_type）
        from numeric_lib.gear import make_gear
        from numeric_lib.constants import LOADOUTS
        cfg = LOADOUTS.get(loadout, {})
        return make_gear(lv, cfg.get("quality", "blue"), cfg.get("enhance", 0),
                         cfg.get("upgrade", 0), cfg.get("gem_tier", 0),
                         cfg.get("set_bonus", False), affix_type=affix_type)
    return _gl(lv, loadout)


def build_panel(cls_id: str, lv: int, loadout: str, attr: dict,
                affix_type: str = "atk") -> dict:
    """真实面板（build_player 封装）。attr 已是最终点数 dict。
    affix_type: v175e 词条乘区（atk/crit/spd/pene/lifesteal/elem）。"""
    gear = _gear_of(lv, loadout, affix_type)
    st = build_player(cls_id, lv, gear, PlayerOptions(), attr=attr)
    # v175e：词条乘区里不进引擎面板的键（dmg_mult 全伤）由期望引擎手动读入
    _dm = 0.0
    for slot, entry in gear.items():
        if isinstance(entry, dict):
            _dm += float((entry.get("stats") or {}).get("dmg_mult", 0.0) or 0.0)
    if _dm > 0:
        st["_affix_dmg_mult"] = _dm
    return st


def _interval(cast: float, spd: float) -> float:
    return float(cast or 0) * math.sqrt(SPD_REF / max(float(spd or 0), 1.0))


def _crit_mult_of(st: dict, multi: int = 1) -> float:
    """暴击期望倍率（v175e 对齐引擎 battle.py:1043+4822）：
    - calc_damage：暴击基础 ×1.5
    - crit_dmg：暴击那次再 ×(1+crit_dmg)（乘算，v106.3）
    - 幸运一击：暴击后 30% ×LUCKY_CRIT_MULT(1.5? 查常量)——对齐 numeric_lib 取 0.3
    # 单段暴击总倍率 = 1.5 × (1+crit_dmg)；幸运额外 ≈ +crit×0.3×0.5
    # 期望 = 1 + crit × [(1.5×(1+crit_dmg)) - 1] + crit × 0.3 × 0.5（幸运）
    # 多段仅首段暴击（multi≥2 按 1/multi）。"""
    crit = min(float(st.get("crit", 0) or 0), 0.5)
    if crit <= 0:
        return 1.0
    crit_dmg = float(st.get("crit_dmg", 0) or 0)
    # 单次暴击总倍率（引擎 1.5 × (1+cdmg) 乘算）
    crit_mult = 1.5 * (1 + crit_dmg)
    first = 1.0 / max(1, int(multi or 1))
    # 幸运期望：暴击后 LUCKY_CRIT_CHANCE(0.3) 概率 ×LUCKY_CRIT_MULT(1.3) → 额外 0.3×(1.3-1)
    lucky_extra = 0.3 * (1.3 - 1.0)  # = 0.09（v133 收敛：LUCKY_CRIT_MULT=1.3）
    return 1.0 + (crit * (crit_mult - 1.0) + crit * lucky_extra) * first


def _pene_mult_of(st: dict, phys: bool, target: dict) -> float:
    """穿透期望（v175e）：pene_phys/pene_magi 按百分比无视防御。
    简化：穿透率 p 等效伤害倍率 = 1/(1 - p×def_mit_ratio) 过重——
    直接近似：伤害加成 ≈ p×0.5（50% 防御无视约等于 30-50% 增伤，取中）。
    ⚠️ 精确口径靠真引擎；期望引擎只做排序粗筛。"""
    pene = float(st.get("pene_phys", 0) if phys else st.get("pene_magi", 0) or 0)
    return 1.0 + pene * 0.5 if pene > 0 else 1.0


def _dmg_of(info: dict, st: dict, skill_lv: int, target: dict) -> float:
    """单发期望伤害（skill_expr_preview + calc_damage 过防）。目标 dict 含 def/mdef。

    ⚠️ 只对 kind=物理/魔法/真伤 的输出技算伤害；治疗/增益/召唤/被动 = 0
    （治疗技 heal_formula 的 skill_expr_preview 返回治疗量，误当伤害会让
    牧师神谕治疗流"13轮击杀"假象——v175 修复）。
    v175b：真伤（kind=真伤，穿防 0 防御 calc_damage(pierce=True)）纳入——
    战争化身/龙息之怒/腐蚀之刃/万毒噬心 是真伤高价值技，此前算 0 严重低估。
    v175d：召唤技折算召唤物期望 DPS 当量（对齐 SUMMONS 模板：atk_ratio×玩家atk×频率）。
    v175e：全乘区期望——暴击(crit×crit_dmg×幸运) / 穿透(pene) 折入单发期望。
    """
    kind = str(info.get("kind", ""))
    # 召唤技：折算召唤物持续伤害（atk_ratio × 玩家 atk，按 attack_interval 频率）
    if kind == "召唤":
        return _summon_dmg_of(info, st, target)
    if not (kind.startswith("物理") or kind.startswith("魔法") or kind == "真伤"):
        return 0.0
    phys = kind.startswith("物理")
    _st = dict(st)
    _st["_player_lv"] = int(st.get("level", st.get("_player_lv", 1)) or 1)
    _st["_skill_lv"] = max(1, skill_lv)
    raw = float(skill_expr_preview(info, skill_lv, _st) or 0.0)
    if raw <= 0:
        return 0.0
    dmg_type = "phys" if phys else "magi"
    if info.get("pierce") or kind == "真伤":
        # 真伤/穿防：无视防御（calc_damage pierce=True）
        base = calc_damage(int(raw), 0, pierce=True, dmg_type=dmg_type, variance=0.0)
    else:
        defv = int(target.get("def", 0)) if phys else int(target.get("mdef", 0))
        # 穿透：扣防前先按 pene 打折防御（等效防御降低）
        pene = float(st.get("pene_phys", 0) if phys else st.get("pene_magi", 0) or 0)
        if pene > 0:
            defv = int(defv * (1 - min(pene, 0.6)))
        base = calc_damage(int(raw), defv, dmg_type=dmg_type, variance=0.0)
    multi = int(info.get("hits", 1) or 1)
    dmg = base * multi
    # 暴击期望（非真伤——真伤不暴击，引擎语义）
    if kind != "真伤":
        dmg *= _crit_mult_of(st, multi=multi)
    # v175e 全伤乘区（elem 词条 dmg_mult，不进引擎面板由期望引擎手动读）
    _adm = float(st.get("_affix_dmg_mult", 0.0) or 0.0)
    if _adm > 0:
        dmg *= (1 + _adm)
    return dmg


def _summon_dmg_of(info: dict, st: dict, target: dict) -> float:
    """召唤技单发期望 = 召唤物在其存活/召唤 CD 周期内的总伤害贡献。

    对齐 SUMMONS 模板（game/data/summons.py）：
      - atk_ratio：召唤物攻击 = 玩家 atk × ratio（法师/牧师用 matk 若 dmg_type=magi）
      - attack_interval：攻击频率（刻/次，默认 1.0）
      - dmg_type：phys/magi（过对应防御）
    贡献周期 ≈ 召唤 CD（cd 秒内召唤物持续攻击）——放一次召唤 = 获得 cd 秒的召唤物火力。
    挡刀/光环（treant aura 等）为生存向，期望引擎不折算（A2 真引擎覆盖）。
    """
    from data.plugins.dragonfall.game.data.summons import SUMMONS
    tid = str(info.get("summon", "") or "")
    tmpl = SUMMONS.get(tid)
    if not tmpl:
        return 0.0
    atk_ratio = float(tmpl.get("atk_ratio", 0.0) or 0.0)
    if atk_ratio <= 0:
        # 纯挡刀召唤（藤蔓守卫 atk=0）无伤害贡献
        return 0.0
    dmg_type = tmpl.get("dmg_type", "phys")
    interval = float(tmpl.get("attack_interval", 1.0) or 1.0)
    # 召唤物攻击力 = 玩家主攻 × ratio
    if dmg_type == "magi":
        atk = float(st.get("matk", 0) or 0)
        defv = int(target.get("mdef", 0))
    else:
        atk = float(st.get("atk", 0) or 0)
        defv = int(target.get("def", 0))

    per_hit = calc_damage(int(atk * atk_ratio), defv, variance=0.0, dmg_type=dmg_type)
    # 贡献周期 = 召唤 CD（cd 秒内召唤物持续攻击）；期望引擎"一次施放"折算为 CD 周期总伤
    cd = float(info.get("cd", 16) or 16)
    hits = max(1.0, cd / max(interval, 0.5))
    # 多只（亡魂大军 3 骷髅）按 summon_count 或 limit 折算（骷髅海可叠 3）
    n = 1
    # 粗略：desc 带"3 只"之类 → 模板 limit 上限（骷髅 limit=3）
    if tid == "skeleton":
        n = 3  # 亡魂大军/骷髅海叠 3
    return per_hit * hits * n * 0.5  # 保守 0.5：召唤物不是全程满编（会死/挡刀消耗）


def _cond_ok(cond: str, state: dict) -> bool:
    """cond 语法判定。state: {resource_key: 当前值, cd_left: {skill: tick}, ...}"""
    if not cond or cond == "always":
        return True
    if cond == "cd_ready":
        return True  # cd_ready 表示"轮到自己且CD好"，由循环层保证
    if cond.startswith("rage>=") or cond.startswith("cp>=") or cond.startswith("chi>=") \
       or cond.startswith("faith>=") or cond.startswith("energy>=") or cond.startswith("resonance>=") \
       or cond.startswith("arcane>=") or cond.startswith("zhan_yi>=") or cond.startswith("hunt_mark>=") \
       or cond.startswith("poison>="):
        res = cond.split(">=")[0]
        need = float(cond.split(">=")[1])
        # v175e mech 层数（arcane 等）走 state.mech_stacks 子表
        if res in ("arcane", "zhan_yi", "hunt_mark", "poison"):
            return float((state.get("mech_stacks") or {}).get(res, 0) or 0) >= need
        return state.get(res, 0) >= need
    if cond.startswith("rage==") or cond.startswith("cp==") or cond.startswith("chi=="):
        res = cond.split("==")[0]
        need = float(cond.split("==")[1])
        return state.get(res, 0) == need
    if cond == "resource_full":
        res = state.get("_resource_key", "")
        return state.get(res, 0) >= state.get("_resource_max", 1)
    if cond == "resource_low":
        res = state.get("_resource_key", "")
        return state.get(res, 0) < state.get("_resource_max", 1) * 0.5
    if cond.startswith("enemy_hp_pct<"):
        need = float(cond.split("<")[1])
        hp_pct = state.get("enemy_hp_pct", 100)
        return hp_pct < need
    if cond.startswith("buff_active:"):
        return state.get("buff_" + cond.split(":")[1], False)
    if cond == "combo_ready":
        return state.get("cp", 0) >= 3
    return True  # 未知 cond 保守放行（宁用不卡循环）


def _res_gain_of(info: dict) -> float:
    """技能资源获取近似：mech 字段 / res_gain 字段 → 每放一次加多少资源。
    简化映射（期望模型近似；真机制以 A2 为准）：
      - res_gain dict {res_key: n} → n
      - mech: zhan_yi(战士怒)/lian_duan(连击) 等命中攒点 → mech_val
      - 普攻：战士怒+1 / 刺客cp+1 / 拳师chi+1（on_attack）
    """
    rg = info.get("res_gain") or {}
    if isinstance(rg, dict) and rg:
        return float(sum(v for v in rg.values() if isinstance(v, (int, float))))
    # 常见 mech 攒点
    mech = str(info.get("mech", ""))
    if mech in ("zhan_yi", "zhan_yi_cash", "lian_duan", "melody", "melody_chant"):
        return float(info.get("mech_val", 1) or 1)
    return 0.0


def _is_finisher(info: dict) -> bool:
    """终结技判定（v175b）：mech=finisher/poison_burst_finisher 或带 consume_all =
    引擎 _m_finisher 结算后资源归零（对齐真引擎：终结读层数增伤后清零）。
    """
    mech = str(info.get("mech", ""))
    if "finisher" in mech:
        return True
    if info.get("consume_all"):
        return True
    return False


def _res_cost_of(info: dict, res_key: str) -> float:
    """技能资源消耗：res_cost dict → 对应键值；否则 0。
    v175b：终结技（mech 含 finisher / consume_all）→ 视为耗光当前资源（期望模型近似，
    对齐真引擎 _m_finisher 结算后归零）。"""
    rc = info.get("res_cost") or {}
    if isinstance(rc, dict):
        for k, v in rc.items():
            if k == res_key and isinstance(v, (int, float)):
                return float(v)
    if _is_finisher(info):
        return -1.0  # 哨兵：调用方按"清零"处理
    return 0.0


def rotation_dps(cls_id: str, lv: int, loadout: str, attr: dict,
                 rotation: list, fight_len: float = 60.0,
                 target: dict | None = None,
                 affix_type: str = "atk") -> dict:
    """期望循环模拟核心。

    rotation: [{"skill": 名, "cond": "...", "prio": n}, ...]（prio 0=最高优先级）
    target: {role, lv, max_hp, def, mdef, hp}（build_monster 展开）；None = 自动同级 dps 怪
    affix_type: v175e 词条乘区流派（atk/crit/spd/pene/lifesteal/elem）
    返回 {dps, kill_rounds, total_dmg, empty_mp_rounds, skill_hits: {技能名: 次数}}
    """
    from numeric_lib.monster import build as _mb
    st = build_panel(cls_id, lv, loadout, attr, affix_type=affix_type)
    pool = class_skill_pool(cls_id, lv)
    res_key = None
    res_max = 0
    regen = 0.0
    # 读 balance_data JSON 拿资源（若无则从 job_guide 展示表 + EFFECT_RULES 推）
    json_path = os.path.join(_BM_DIR, "..", "balance_data", f"{cls_id}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as f:
                jd = json.load(f)
            res_key = jd.get("resource")
            res_max = int(jd.get("resource_max", 0))
            regen = float(jd.get("resource_regen_per_tick", 0))
        except Exception:
            pass
    if not res_key:
        # fallback：job_guide CORE_RESOURCE_GUIDE（cid→key）+ EFFECT_RULES（cap / period.amount 折算 regen）
        # （原 data/core_resources.py 表随 v181.M-R2c 退役——六职业 key/desc 迁 CORE_RESOURCE_GUIDE，
        #   name/cap 单源 EFFECT_RULES；regen 18 对应 energy period dir=gain amount=18）
        from data.plugins.dragonfall.game.data.job_guide import CORE_RESOURCE_GUIDE
        from data.plugins.dragonfall.game.data.battle2_rules import EFFECT_RULES
        _cfg = CORE_RESOURCE_GUIDE.get(cls_id, {})
        res_key = _cfg.get("key")
        _er = EFFECT_RULES.get(res_key, {}) if res_key else {}
        res_max = int(_er.get("cap", 0) or 0)
        _period = _er.get("period") if isinstance(_er.get("period"), dict) else {}
        regen = float(_period.get("amount", 0) or 0)

    # 目标
    if target is None:
        m = _mb("dps", lv)
        target = {"role": "dps", "lv": lv, "max_hp": m.get("max_hp", m.get("hp", 100)),
                  "def": m.get("def", 0), "mdef": m.get("mdef", 0),
                  "hp": m.get("max_hp", m.get("hp", 100))}
    target_hp = float(target.get("max_hp", target.get("hp", 100)) or 100)

    # 预取技能 info + skill_lv
    rot_skills = []
    for step in rotation:
        nm = step["skill"]
        info = pool.get(nm)
        if info is None:
            continue
        slv = skill_lv_at(info, lv)
        if slv <= 0:
            continue  # 未解锁
        rot_skills.append({"name": nm, "info": info, "skill_lv": slv,
                           "cond": step.get("cond", "always"),
                           "prio": int(step.get("prio", 9)),
                           "cast": float(info.get("cast", 1.0) or 1.0),
                           "cd": float(info.get("cd", 0) or 0),
                           "mp": float(info.get("mp", 0) or 0)})
    # 普攻数据（物理职业 atk / 法系 atk 低但普攻走 atk 引擎口径）
    basic_cast = 1.0
    for _cid, _cdef in SK.PLAYER_SKILLS.items():
        if _cid == cls_id:
            basic_cast = 1.0
            break
    spd = float(st.get("spd", 50) or 50)
    basic_interval = _interval(1.0, spd)
    basic_dmg = calc_damage(int(st.get("atk", 0)),
                              int(target.get("def", 0)), variance=0.0, dmg_type="phys")

    # 模拟状态（事件驱动：按行动跳步，不逐 tick 扫——几千格矩阵性能关键）
    state = {res_key: 0.0} if res_key else {}
    state["_resource_key"] = res_key
    state["_resource_max"] = res_max
    state["enemy_hp_pct"] = 100.0
    state["mech_stacks"] = {}   # v175e mech 层数（arcane/zhan_yi/hunt_mark/poison 等攒层流派）
    cd_left = {}   # skill name -> tick left（绝对时刻制：存"下次可用时刻"）
    skill_hits = {}
    mp = float(st.get("max_mp", 0) or 0)
    max_mp = mp
    mp_regen = max_mp * 0.05  # numeric_lib MP_REGEN_PCT（每"轮"回 5% ≈ 简化每行动回）
    t = 0.0
    total_dmg = 0.0
    empty_mp_rounds = 0
    rounds_elapsed = 0
    next_avail = {}   # skill name -> 绝对时刻（CD 转好时刻）
    acted_last = False
    max_time = fight_len * 20.0  # 兜底（战斗长度×20 秒上限防死循环）

    while t < max_time and total_dmg < target_hp:
        rounds_elapsed += 1
        # 资源自然回：energy 18/刻 → 按行动间隔近似（每行动回 = regen × 行动耗时）
        # （真机制是每刻持续回；期望模型近似为行动时累计，误差由 A2 仲裁）
        # MP 自然回：每行动回 max_mp×5%（numeric_lib MP_REGEN_PCT 同款按轮）
        mp = min(max_mp, mp + mp_regen)
        if res_key and regen > 0:
            state[res_key] = min(res_max, state.get(res_key, 0) + regen * 1.0)
        # 找本行动可施放的技能（按 prio 排序）
        # v175 轮换修正：多个 cond=always 且 cd=0 的填充技并存时，若永远选 prio 最高的
        # （如法师 火球 always prio3 > 冰锥 always prio4 > 雷击 always prio5），
        # 低 prio 永远饿死 0 出场（"死技能"假象）。真实玩家会按循环轮换铺印。
        # 修正：cond=always 的 0CD 技视为同一"填充梯队"，在它们之间轮换；
        # CD/资源技仍严格按 prio 优先（好了就用）。
        acted = False
        available = []      # (排序键, 技能) 可施放的技能
        for sk in rot_skills:
            if next_avail.get(sk["name"], 0) > t + 1e-9:
                continue
            if not _cond_ok(sk["cond"], state):
                continue
            if mp < sk["mp"] - 1e-9:
                continue
            cost = _res_cost_of(sk["info"], res_key)
            if cost < 0:
                # 终结技：至少需 1 点资源（对齐真引擎 consume_all「至少需 1 点」）
                if res_key and state.get(res_key, 0) < 1.0:
                    continue
            elif res_key and cost > state.get(res_key, 0) + 1e-9:
                continue
            available.append(sk)
        # 梯队分离（v175b 修正）：选技策略对齐真实玩家资源循环——
        #   1. 终结技/资源消耗技（prio 0-1，cond 资源阈值满足时）最高优先
        #   2. 资源不足时：优先放「攒点技」（带 mech gain 的 always/0CD 技）让资源转起来，
        #      而不是被无资源收益的 CD 技（影袭/潜行等）饿死攒点技 → 终结永远放不出
        #   3. CD 爆发技（无资源收益但有伤害）次之
        #   4. 纯填充普攻最后
        def _gain_of_sk(sk):
            return _res_gain_of(sk["info"]) if not _is_finisher(sk["info"]) else 0.0

        finishers = [sk for sk in available if _is_finisher(sk["info"])]
        gainers = [sk for sk in available if _gain_of_sk(sk) > 0]
        cd_burst = [sk for sk in available
                    if not _is_finisher(sk["info"]) and sk["cd"] > 0 and _gain_of_sk(sk) == 0]
        fillers = [sk for sk in available if sk not in finishers and sk not in gainers
                   and sk not in cd_burst]
        chosen = None
        if finishers:
            # 终结技就绪（cond 资源阈值已满足才会在 available）→ 最高优先
            chosen = min(finishers, key=lambda x: x["prio"])
        elif gainers:
            # 攒点技：资源没满时优先放（保证资源循环），轮换避免死磕一个
            gainer_sorted = sorted(gainers, key=lambda x: x["prio"])
            idx = state.get("_filler_idx", 0) % max(len(gainer_sorted), 1)
            chosen = gainer_sorted[idx]
            state["_filler_idx"] = (idx + 1) % max(len(gainer_sorted), 1)
        elif cd_burst:
            chosen = min(cd_burst, key=lambda x: x["prio"])
        elif fillers:
            filler_sorted = sorted(fillers, key=lambda x: x["prio"])
            idx = state.get("_filler_idx", 0) % max(len(filler_sorted), 1)
            chosen = filler_sorted[idx]
            state["_filler_idx"] = (idx + 1) % max(len(filler_sorted), 1)
        if chosen:
            sk = chosen
            # 施放
            mp -= sk["mp"]
            if res_key:
                cost = _res_cost_of(sk["info"], res_key)
                if cost < 0:
                    # 终结技（哨兵 -1）：清零资源（对齐真引擎 _m_finisher 结算后归零）
                    state[res_key] = 0.0
                elif cost > 0:
                    state[res_key] = max(0.0, state.get(res_key, 0) - cost)
            dmg = _dmg_of(sk["info"], st, sk["skill_lv"], target)
            total_dmg += dmg
            skill_hits[sk["name"]] = skill_hits.get(sk["name"], 0) + 1
            # 资源获取（终结技不放获取——它是消耗端；攒点技才 +）
            gain = _res_gain_of(sk["info"])
            if res_key and gain and not _is_finisher(sk["info"]):
                state[res_key] = min(res_max, state.get(res_key, 0) + gain)
            # v175e mech 层数获取（奥术弹幕/飞弹 → arcane+1、猎印射击 → hunt_mark 等）：
            # mech 字段层数由技能数据 mech_val 决定；期望模型近似线性累加（真机制 A2 仲裁）
            _mk = str(sk["info"].get("mech", "") or "")
            _mv = float(sk["info"].get("mech_val", 0) or 0)
            if _mk and _mv and not _is_finisher(sk["info"]) \
                    and _mk in ("arcane", "zhan_yi", "hunt_mark", "poison", "thunder", "ice", "fire"):
                _ms = state["mech_stacks"]
                _ms[_mk] = min(10, _ms.get(_mk, 0) + _mv)
            # CD（绝对时刻制；v175e 冷却缩减：面板 cdr 键，cd ×(1-cdr)，cap 对齐引擎 0.4）
            if sk["cd"] > 0:
                _cd = sk["cd"]
                _cdr = min(float(st.get("cdr", 0) or 0), 0.4)
                if _cdr > 0 and _cd > 1:
                    _cd = max(1.0, _cd * (1 - _cdr))
                next_avail[sk["name"]] = t + _cd
            # 行动耗时
            act_t = _interval(sk["cast"], spd)
            t += act_t
            acted = True
        if not acted:
            # 全技能不可用 → 普攻
            total_dmg += basic_dmg
            t += basic_interval
            if res_key and res_key in ("rage", "cp", "chi"):
                state[res_key] = min(res_max, state.get(res_key, 0) + 1.0)
            if mp < 1 and max_mp > 0:
                empty_mp_rounds += 1
        # 更新敌血百分比
        state["enemy_hp_pct"] = max(0.0, (1 - total_dmg / target_hp) * 100)
        if rounds_elapsed > 5000:  # 护栏
            break
    # 输出
    kill_rounds = rounds_elapsed if total_dmg >= target_hp else None
    elapsed_t = max(t, 0.001)
    return {
        "dps": total_dmg / elapsed_t,
        "kill_rounds": kill_rounds,
        "total_dmg": round(total_dmg, 1),
        "target_hp": target_hp,
        "empty_mp_rounds": empty_mp_rounds,
        "skill_hits": skill_hits,
        "elapsed_t": round(elapsed_t, 2),
    }


def boss_instance_panel(iid: str, n_players: int = 1, boss_lv: int | None = None) -> dict:
    """实例 Boss 完整面板（与 team_matrix 同口径）：
    - 基础面板：C.build_monster（裸模板 × MONSTER_MODS 个体修正）
    - 血量：叠实例 hp_mult + 人数缩放（team.boss_hp 公式）
    - 攻击：保留 atk_mult 供承伤侧用（_boss_hit 里 ×atk_mult×1.35）
    返回 dict（含 max_hp/def/mdef/atk/matk/spd + _hp_mult/_atk_mult/_n_players）
    """
    from data.plugins.dragonfall.game import content as C
    from numeric_lib.team import boss_hp
    inst = C.INSTANCES.get(iid)
    if not inst:
        raise KeyError(f"未知副本: {iid}")
    boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
    if not boss_def:
        raise KeyError(f"副本 {iid} 无 Boss")
    mn = inst.get("min_players", 1)
    n_eff = max(int(n_players or 1), mn)  # 进不去按最少可进人数
    lv = boss_lv or int(boss_def[3])
    m = C.build_monster(boss_def, {"id": boss_def[0], "name": boss_def[1],
                                   "area": "instance", "lv": lv})
    hp_tot = boss_hp(m.get("max_hp", 0), n_eff, mn, inst.get("hp_mult"))
    m = dict(m)
    m["max_hp"] = hp_tot
    m["hp"] = hp_tot
    m["_hp_mult"] = inst.get("hp_mult")
    m["_atk_mult"] = inst.get("atk_mult", 1.0)
    m["_n_players"] = n_eff
    m["_min_players"] = mn
    m["_boss_def"] = boss_def
    return m


def build_vs_boss(cls_id: str, lv: int, loadout: str, attr: dict,
                  rotation: list, boss: dict, boss_lv: int = None,
                  iid: str | None = None, n_players: int = 1,
                  affix_type: str = "atk") -> dict:
    """流派 vs Boss：期望击杀轮 + 生存轮。

    boss: boss_def（instances.py 6元组）或已展开 dict（含 max_hp/def/mdef/atk/matk/spd）
    boss_lv: 覆盖 boss_def[3]（玩家跨级打高本时用）
    iid: 若给副本 id，用 team 口径叠 hp_mult/atk_mult（推荐）；否则当裸模板处理
    n_players: 打本次数（单人=1）
    affix_type: v175e 词条乘区流派（含生存向 dodge/block/lifesteal/reduce/thorns）
    返回 {kill_rounds, survive_rounds, verdict}
    """
    # 展开 Boss 面板 —— 优先实例完整口径（与 saintess_engine/team_matrix 对齐）
    if iid:
        from data.plugins.dragonfall.game import content as C
        boss_panel = boss_instance_panel(iid, n_players, boss_lv)
        atk_mult = boss_panel.get("_atk_mult", 1.0)
    elif isinstance(boss, (tuple, list)):
        # (id, 名, role, lv, [技能], [掉落]) → C.build_monster（同 saintess_engine.boss_of）
        bd = tuple(boss)
        from data.plugins.dragonfall.game import content as C
        boss_panel = C.build_monster(
            bd, {"id": bd[0], "name": bd[1], "area": "instance", "lv": bd[3]})
        atk_mult = 1.0
    elif isinstance(boss, dict) and "max_hp" in boss:
        boss_panel = boss
        atk_mult = 1.0
    else:
        from numeric_lib.monster import build as _mb
        boss_panel = _mb("boss", boss_lv or 20)
        atk_mult = 1.0
    hp = float(boss_panel.get("max_hp", boss_panel.get("hp", 1000)))
    edef = int(boss_panel.get("def", 0))
    mdef = int(boss_panel.get("mdef", 0))
    target = {"role": "boss", "lv": boss_lv or 20, "max_hp": hp,
              "def": edef, "mdef": mdef, "hp": hp}
    r = rotation_dps(cls_id, lv, loadout, attr, rotation, fight_len=60.0, target=target, affix_type=affix_type)
    kill = r["kill_rounds"]
    # 承伤侧：复用 team 口径 —— Boss 单发 = _boss_hit(boss_def, m, def, mdef, atk_mult)
    # （物理/魔法取高 × atk_mult × 1.35 enraged 保守）
    st = build_panel(cls_id, lv, loadout, attr, affix_type=affix_type)

    boss_atk = float(boss_panel.get("atk", 0)) * atk_mult * 1.35
    boss_matk = float(boss_panel.get("matk", 0)) * atk_mult * 1.35
    d_phys = calc_damage(int(boss_atk), int(st.get("def", 0)), variance=0.0, dmg_type="phys")
    d_magi = calc_damage(int(boss_matk), int(st.get("mdef", 0)), variance=0.0, dmg_type="magi")
    boss_hit = max(d_phys, d_magi)
    player_hp = float(st.get("max_hp", 1000))
    # v175e 生存乘区（闪避战士/格挡坦/吸血续航建模）：
    # 引擎口径（battle.py _damage_player）：闪避先判（全额免，cap40%，PVE 无精准削），
    # 命中后格挡判（减半，cap40%）→ 期望承伤因子 = (1-dodge) × (1-block/2)
    dodge = min(float(st.get("dodge", 0) or 0), 0.40)
    block = min(float(st.get("block", 0) or 0), 0.40)
    mit = (1.0 - dodge) * (1.0 - block / 2.0)
    ls = float(st.get("lifesteal", 0) or 0)
    # 单刷吃药水近似（team_matrix 单刷口径：防御药水 def×1.45 + 治疗药水每3轮回50%血）
    if int(boss_panel.get("_n_players", n_players)) <= 1 and loadout not in ("naked",):
        pdef_b = int(st.get("def", 0) * 1.45)
        pmdef_b = int(st.get("mdef", 0) * 1.45)
        d_phys_b = calc_damage(int(boss_atk), pdef_b, variance=0.0, dmg_type="phys")
        d_magi_b = calc_damage(int(boss_matk), pmdef_b, variance=0.0, dmg_type="magi")
        boss_hit = max(d_phys_b, d_magi_b)
        heal_per_round = player_hp * 0.50 / 3.0
        # 闪避/格挡削减 boss_hit 后，治疗药水回复才有意义（期望口径）
        net_hit = boss_hit * mit
        # 吸血续航（近似）：lifesteal × 每轮输出。每轮输出 = 击杀血量/击杀轮数
        # 注：期望模型不模拟 Boss 行动，吸血精确结算走真引擎 battle_rotation（这里粗近似）
        ls_heal = 0.0
        if ls > 0 and kill and kill > 0:
            ls_heal = (hp / kill) * ls
        net = max(net_hit - heal_per_round - ls_heal, net_hit * 0.2)
        survive = player_hp / max(net, 1.0)
    else:
        # 无药水分支：净承伤 = 单发 × 闪避/格挡减免（期望）
        net_hit = boss_hit * mit
        net = net_hit if net_hit > 0 else 1.0
        survive = player_hp / max(net, 1.0) if net > 0 else 999.0
    verdict = ""
    if kill is None:
        verdict = "🔴 杀不死"
    elif survive < kill * 0.9:
        verdict = "🔴 先死打不过"
    elif kill > 80:
        verdict = "🟡 拖太久"
    else:
        verdict = "✅ 可过"
    return {
        "kill_rounds": kill,
        "survive_rounds": round(survive, 1),
        "boss_hp": hp, "boss_hit": round(boss_hit, 1), "player_hp": player_hp,
        "verdict": verdict,
    }


def full_matrix() -> dict:
    """全职业×流派×阶段×加点×装备 → 大表（期望模型全矩阵）。

    返回 {class_id: {build_name: {stage: {attr_name: row}}}}
    row = {loadout, kill_rounds, survive_rounds, verdict, dps, empty_mp_rounds}
    """
    out = {}
    bal_dir = os.path.join(_BM_DIR, "..", "balance_data")
    for fn in sorted(os.listdir(bal_dir)):
        if not fn.startswith("cls_") or not fn.endswith(".json") or fn.startswith("_dump"):
            continue
        cid = fn.replace(".json", "")
        with open(os.path.join(bal_dir, fn), encoding="utf-8") as f:
            jd = json.load(f)
        cls_out = {}
        for bname, bdef in jd.get("builds", {}).items():
            rotation = bdef.get("rotation", [])
            build_rows = {}
            for stage_name, lv, loadout in STAGE_CFG:
                attr_presets = jd.get("attr_presets", {})
                # 该流派推荐的加点
                main_attr_name = bdef.get("attr_preset", "")
                presets = {}
                if main_attr_name and main_attr_name in attr_presets:
                    presets["_rec"] = attr_presets[main_attr_name]
                presets.update(attr_presets)
                stage_attr_rows = {}
                for aname, apreset in presets.items():
                    attr = resolve_attr(apreset, lv)
                    # 目标 = 对应阶段 Boss（粗略：用同级 boss 面板）
                    from numeric_lib.monster import build as _mb
                    m = _mb("boss", lv)
                    tgt = {"role": "boss", "lv": lv, "max_hp": m.get("max_hp", 5000),
                           "def": m.get("def", 0), "mdef": m.get("mdef", 0), "hp": m.get("max_hp", 5000)}
                    try:
                        r = rotation_dps(cid, lv, loadout, attr, rotation, fight_len=60.0, target=tgt)
                    except Exception as ex:
                        stage_attr_rows[aname] = {"error": str(ex)}
                        continue
                    # 生存
                    st = build_panel(cid, lv, loadout, attr)
                    boss_atk = float(m.get("atk", 0)) * 1.35
                    boss_matk = float(m.get("matk", 0)) * 1.35
                    d_phys = calc_damage(int(boss_atk), int(st.get("def", 0)), variance=0.0, dmg_type="phys")
                    d_magi = calc_damage(int(boss_matk), int(st.get("mdef", 0)), variance=0.0, dmg_type="magi")
                    boss_hit = max(d_phys, d_magi)
                    survive = float(st.get("max_hp", 1000)) / max(boss_hit, 1.0) if boss_hit > 0 else 999.0
                    kr = r["kill_rounds"]
                    verdict = "杀不死" if kr is None else (
                        "先死打不过" if survive < kr * 0.9 else ("拖太久" if kr > 80 else "可过"))
                    stage_attr_rows[aname] = {
                        "kill_rounds": kr, "survive_rounds": round(survive, 1),
                        "dps": round(r["dps"], 1), "empty_mp_rounds": r["empty_mp_rounds"],
                        "verdict": verdict,
                    }
                build_rows[stage_name] = stage_attr_rows
            cls_out[bname] = build_rows
        out[cid] = cls_out
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cls", nargs="?", default="cls_zhan_shi")
    ap.add_argument("--lv", type=int, default=45)
    ap.add_argument("--loadout", default="team_purple9")
    ap.add_argument("--build", default=None, help="流派名，缺省跑全部")
    ap.add_argument("--attr", default="full_str")
    args = ap.parse_args()
    json_path = os.path.join(_BM_DIR, "..", "balance_data", f"{args.cls}.json")
    if not os.path.exists(json_path):
        print(f"❌ 缺 {json_path}（职业 agent 未产出）")
        sys.exit(0)
    with open(json_path, encoding="utf-8") as f:
        jd = json.load(f)
    print(f"== {args.cls} @ Lv{args.lv} ({args.loadout}) ==")
    attr_presets = jd.get("attr_presets", {})
    builds = jd.get("builds", {})
    for bname, bdef in builds.items():
        if args.build and bname != args.build:
            continue
        rotation = bdef.get("rotation", [])
        ap_name = bdef.get("attr_preset", args.attr) or args.attr
        apreset = attr_presets.get(ap_name, {"str": "all"})
        attr = resolve_attr(apreset, args.lv)
        from numeric_lib.monster import build as _mb
        m = _mb("boss", args.lv)
        tgt = {"role": "boss", "lv": args.lv, "max_hp": m.get("max_hp", 5000),
               "def": m.get("def", 0), "mdef": m.get("mdef", 0), "hp": m.get("max_hp", 5000)}
        r = rotation_dps(args.cls, args.lv, args.loadout, attr, rotation, fight_len=60.0, target=tgt)
        st = build_panel(args.cls, args.lv, args.loadout, attr)
        print(f"\n[{bname}] role={bdef.get('role')} attr={ap_name}{apreset}")
        print(f"  rotation: {len(rotation)} 技能 -> {[s['skill'] for s in rotation]}")
        print(f"  面板: hp={st.get('max_hp')} atk={st.get('atk')} matk={st.get('matk')} "
              f"spd={st.get('spd')} mp={st.get('max_mp')}")
        print(f"  击杀轮: {r['kill_rounds']} | DPS: {r['dps']:.1f} | 空蓝轮: {r['empty_mp_rounds']}")
        if r["skill_hits"]:
            top = sorted(r["skill_hits"].items(), key=lambda x: -x[1])[:6]
            print(f"  技能占比: {dict(top)}")
