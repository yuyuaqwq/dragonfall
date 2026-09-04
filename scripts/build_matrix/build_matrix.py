# -*- coding: utf-8 -*-
"""v175 A1 期望引擎核心 build_matrix —— 全职业×流派×加点×装备 期望矩阵。

主 agent 亲写（铁律：引擎主 agent 写）。依赖：
  - scripts/balance_data/cls_<职业>.json（职业 agent 产出，schema 校验过）
  - scripts/build_matrix/schema.py（技能名集/常量）
  - numeric_lib（build_player / gear_loadout / monster 等既有底座）
  - game engine（skill_expr_preview / calc_damage / skill_info）

口径（与 numeric_lib.player 同源，真实引擎实算）：
  1. 面板：E.player_final_stats（build_player 封装，attr 显式点）
  2. 流派循环：rotation（JSON 里 cond/prio 声明）→ 按 tick 模拟
  3. 伤害：E.skill_expr_preview 代入面板 + calc_damage 过防（variance=0）
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

from data.plugins.dragonfall.game import engine as E          # noqa: E402
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


def skill_lv_at(info: dict, player_lv: int) -> int:
    """技能等级：未解锁 0；学得时 1；此后每 4 级 +1，封顶 SKILL_UP.max。"""
    learn_lv = int(info.get("lv", 1) or 1)
    if player_lv < learn_lv:
        return 0
    max_lv = E.skill_max_level(info)
    grow = 1 + max(0, (player_lv - learn_lv) // 4)
    return min(grow, max_lv)


def build_panel(cls_id: str, lv: int, loadout: str, attr: dict) -> dict:
    """真实面板（build_player 封装）。attr 已是最终点数 dict。"""
    gear = gear_loadout(lv, loadout) if loadout and loadout != "naked" else {}
    return build_player(cls_id, lv, gear, PlayerOptions(), attr=attr)


def _interval(cast: float, spd: float) -> float:
    return float(cast or 0) * math.sqrt(SPD_REF / max(float(spd or 0), 1.0))


def _dmg_of(info: dict, st: dict, skill_lv: int, target: dict) -> float:
    """单发期望伤害（skill_expr_preview + calc_damage 过防）。目标 dict 含 def/mdef。

    ⚠️ 只对 kind=物理/魔法 的输出技算伤害；治疗/增益/召唤/被动 = 0
    （治疗技 heal_formula 的 skill_expr_preview 返回治疗量，误当伤害会让
    牧师神谕治疗流"13轮击杀"假象——v175 修复）。"""
    kind = str(info.get("kind", ""))
    if not (kind.startswith("物理") or kind.startswith("魔法")):
        return 0.0
    phys = kind.startswith("物理")
    _st = dict(st)
    _st["_player_lv"] = int(st.get("level", st.get("_player_lv", 1)) or 1)
    _st["_skill_lv"] = max(1, skill_lv)
    raw = float(E.skill_expr_preview(info, skill_lv, _st) or 0.0)
    if raw <= 0:
        return 0.0
    dmg_type = "phys" if phys else "magi"
    if info.get("pierce"):
        base = E.calc_damage(int(raw), 0, pierce=True, dmg_type=dmg_type, variance=0.0)
    else:
        defv = int(target.get("def", 0)) if phys else int(target.get("mdef", 0))
        base = E.calc_damage(int(raw), defv, dmg_type=dmg_type, variance=0.0)
    return base * int(info.get("hits", 1) or 1)


def _cond_ok(cond: str, state: dict) -> bool:
    """cond 语法判定。state: {resource_key: 当前值, cd_left: {skill: tick}, ...}"""
    if not cond or cond == "always":
        return True
    if cond == "cd_ready":
        return True  # cd_ready 表示"轮到自己且CD好"，由循环层保证
    if cond.startswith("rage>=") or cond.startswith("cp>=") or cond.startswith("chi>=") \
       or cond.startswith("faith>=") or cond.startswith("energy>=") or cond.startswith("resonance>="):
        res = cond.split(">=")[0]
        need = float(cond.split(">=")[1])
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


def _res_cost_of(info: dict, res_key: str) -> float:
    """技能资源消耗：res_cost dict → 对应键值；否则 0。"""
    rc = info.get("res_cost") or {}
    if isinstance(rc, dict):
        for k, v in rc.items():
            if k == res_key and isinstance(v, (int, float)):
                return float(v)
        return 0.0
    return 0.0


def rotation_dps(cls_id: str, lv: int, loadout: str, attr: dict,
                 rotation: list, fight_len: float = 60.0,
                 target: dict | None = None) -> dict:
    """期望循环模拟核心。

    rotation: [{"skill": 名, "cond": "...", "prio": n}, ...]（prio 0=最高优先级）
    target: {role, lv, max_hp, def, mdef, hp}（build_monster 展开）；None = 自动同级 dps 怪
    返回 {dps, kill_rounds, total_dmg, empty_mp_rounds, skill_hits: {技能名: 次数}}
    """
    from numeric_lib.monster import build as _mb
    st = build_panel(cls_id, lv, loadout, attr)
    pool = class_skill_pool(cls_id, lv)
    res_key = None
    res_max = 0
    regen = 0.0
    # 读 balance_data JSON 拿资源（若无则从 core_resources 推）
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
        # fallback core_resources
        from data.plugins.dragonfall.game.data import core_resources as CR
        cr = CR.CORE_RESOURCES.get(cls_id, {})
        res_key = cr.get("key")
        res_max = int(cr.get("max", 0))
        regen = float(cr.get("regen", 0))

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
    basic_dmg = E.calc_damage(int(st.get("atk", 0)),
                              int(target.get("def", 0)), variance=0.0, dmg_type="phys")

    # 模拟状态（事件驱动：按行动跳步，不逐 tick 扫——几千格矩阵性能关键）
    state = {res_key: 0.0} if res_key else {}
    state["_resource_key"] = res_key
    state["_resource_max"] = res_max
    state["enemy_hp_pct"] = 100.0
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
        acted = False
        for sk in sorted(rot_skills, key=lambda x: x["prio"]):
            if next_avail.get(sk["name"], 0) > t + 1e-9:
                continue
            if not _cond_ok(sk["cond"], state):
                continue
            if mp < sk["mp"] - 1e-9:
                continue
            cost = _res_cost_of(sk["info"], res_key)
            if res_key and cost > state.get(res_key, 0) + 1e-9:
                continue
            # 施放
            mp -= sk["mp"]
            if res_key:
                state[res_key] = max(0.0, state.get(res_key, 0) - cost)
            dmg = _dmg_of(sk["info"], st, sk["skill_lv"], target)
            total_dmg += dmg
            skill_hits[sk["name"]] = skill_hits.get(sk["name"], 0) + 1
            # 资源获取
            gain = _res_gain_of(sk["info"])
            if res_key and gain:
                state[res_key] = min(res_max, state.get(res_key, 0) + gain)
            # CD（绝对时刻制）
            if sk["cd"] > 0:
                next_avail[sk["name"]] = t + sk["cd"]
            # 行动耗时
            act_t = _interval(sk["cast"], spd)
            t += act_t
            acted = True
            break
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


def build_vs_boss(cls_id: str, lv: int, loadout: str, attr: dict,
                  rotation: list, boss: dict, boss_lv: int) -> dict:
    """流派 vs Boss：期望击杀轮 + 生存轮。

    boss: boss_def（instances.py 6元组）或已展开 dict（含 max_hp/def/mdef/atk/matk/spd）
    boss_lv: 覆盖 boss_def[3]（玩家跨级打高本时用）
    返回 {kill_rounds, survive_rounds, verdict}
    """
    # 展开 Boss 面板
    if isinstance(boss, (tuple, list)):
        # (id, 名, role, lv, [技能], [掉落])
        from numeric_lib.monster import build as _mb
        boss_panel = _mb("boss", boss_lv or int(boss[3]))
    elif isinstance(boss, dict) and "max_hp" in boss:
        boss_panel = boss
    else:
        from numeric_lib.monster import build as _mb
        boss_panel = _mb("boss", boss_lv or 20)
    hp = float(boss_panel.get("max_hp", boss_panel.get("hp", 1000)))
    edef = int(boss_panel.get("def", 0))
    mdef = int(boss_panel.get("mdef", 0))
    target = {"role": "boss", "lv": boss_lv or 20, "max_hp": hp,
              "def": edef, "mdef": mdef, "hp": hp}
    r = rotation_dps(cls_id, lv, loadout, attr, rotation, fight_len=60.0, target=target)
    kill = r["kill_rounds"]
    # 承伤侧：Boss 单发期望 × enraged 1.35（team.py BOSS_ATK_MULT 同款保守）
    st = build_panel(cls_id, lv, loadout, attr)
    boss_atk = float(boss_panel.get("atk", 0)) * 1.35
    boss_matk = float(boss_panel.get("matk", 0)) * 1.35
    d_phys = E.calc_damage(int(boss_atk), int(st.get("def", 0)), variance=0.0, dmg_type="phys")
    d_magi = E.calc_damage(int(boss_matk), int(st.get("mdef", 0)), variance=0.0, dmg_type="magi")
    boss_hit = max(d_phys, d_magi)
    player_hp = float(st.get("max_hp", 1000))
    # 自愈近似：heal 类技能从 dps 里扣减承伤（暂简化：只有 rotation 里治疗技才减）
    survive = player_hp / max(boss_hit, 1.0) if boss_hit > 0 else 999.0
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
                    d_phys = E.calc_damage(int(boss_atk), int(st.get("def", 0)), variance=0.0, dmg_type="phys")
                    d_magi = E.calc_damage(int(boss_matk), int(st.get("mdef", 0)), variance=0.0, dmg_type="magi")
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
