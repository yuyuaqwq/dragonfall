# -*- coding: utf-8 -*-
"""5c P1：Boss 剧本导演（mech DSL 执行器 battle2 化）——阶段/演出/换招。

设计 docs/REFACTOR_v181P4_N5B5c_boss_script_design.md：
- 导演在命令层：读 MONSTER_MODS/INSTANCES 配置（v178 E1/E2 合并语义），
  在怪行动帧（script_hook，battle2/battle.py actor_auto 前置）检查血量阈值 →
  触发剧本动作（转阶段演出/换招/演出刻 skip/阈值预告）。
- 引擎零游戏知识：只提供 script_hook 注入钩子；本文件不 import 旧 game.battle。
- 导演状态 st["boss_script"] 随副本持久化；actors 只留引擎效果（V 系列铁律）。

P1 范围：phases 转阶段。P2+（opening/player_low/summon/chains...）后续批扩展。
"""
from __future__ import annotations


def boss_script_cfg(st: dict, actor: dict):
    """解析 Boss 剧本配置（MONSTER_MODS 基准 + INSTANCES 副本覆盖，v178 E1/E2）。

    输入 actor（battle2 enemy side actor，monster_to_actor 透传 id/_inst_id）。
    返回 None（无 phases 剧本）或 cfg dict（含缺省 key，opening/triggers/chains
    供 P2+ 批读取；P1 只消费 phases）。
    """
    bid = actor.get("id") or actor.get("uid") or ""
    if not bid:
        return None
    try:
        from .. import content as C
        mods = (C.MONSTER_MODS or {}).get(bid) or {}
        cfg = {
            "opening": mods.get("opening"),
            "triggers": mods.get("triggers") or {},
            "phases": list(mods.get("phases") or []),
            "chains": mods.get("chains"),
            "on_interrupt": mods.get("on_interrupt"),
            "on_minion_died": mods.get("on_minion_died"),
        }
        _mech = [x.strip() for x in str(mods.get("mech") or "").split(",") if x.strip()]
        # v178 E1：副本 Boss 带 _inst_id → 副本条目 phases/opening/triggers/chains 覆盖
        # （battle.py _boss_cfg 同款：副本优先，整体覆盖——v178 后 inst 内联是权威）
        iid = actor.get("_inst_id") or st.get("inst_id") or ""
        if iid and (C.INSTANCES or {}).get(iid):
            inst2 = C.INSTANCES[iid]
            for k in ("opening", "triggers", "phases", "chains"):
                if inst2.get(k) is not None:
                    cfg[k] = inst2[k]
            # v178 E2：mech token 并集去重（MONSTER_MODS + inst 内联，非覆盖）
            _inst_mech = [x.strip() for x in str(inst2.get("mech") or "").split(",")
                          if x.strip()]
            _mech = list(dict.fromkeys(_mech + _inst_mech))
        cfg["mech"] = _mech
        if not cfg["phases"]:
            return None
        return cfg
    except Exception:
        return None


def _phase_threshold(phases: list, pc: int) -> float:
    """第 pc 阶段进下一阶段阈值（ratio 0-1）：有 phases[pc].min 用 min/100
    （设计 60%/30%），否则回退 0.5**(pc+1)（50%/25%）——旧 _phase_threshold 同款。"""
    if pc < len(phases):
        mn = (phases[pc] or {}).get("min")
        if mn is not None:
            try:
                return float(mn) / 100.0
            except Exception:
                pass
    return 0.5 ** (pc + 1)


def _phase_cleanse_negatives(actor: dict, logs: list) -> None:
    """转阶段净化：移除 effects 容器负面条目（preserve_debuffs=False 时）。
    P1 简化：只清明确标记的负面（无 cleanse 语义反向推断——不动控制/周期，
    防误清 Boss 自身状态）。全清变体等 P2 盘点 EFFECT_RULES 时细化。"""
    # P1 占位：V 系列负面键反向推断风险高，默认保留（preserve_debuffs=True 语义），
    # 模板显式 False 时清 adapt/减速等明确负面由 P2 盘点后实现
    return


def make_script_hook(st: dict):
    """导演帧闭包工厂：callable(battle, actor, logs) -> bool（True=拦截本刻行动）。

    只处理"当前行动 actor 是剧本 Boss"的情况（一次一帧只查当前行动者，
    天然避免多怪重复触发）。导演状态 st["boss_script"] 首次调用初始化。
    """
    def hook(battle, actor, logs):
        try:
            if int(actor.get("hp", 0) or 0) <= 0:
                return False
            if not _looks_like_boss(actor):
                return False
            cfg = boss_script_cfg(st, actor)
            if not cfg:
                return False
            bs = st.get("boss_script")
            if not isinstance(bs, dict):
                bs = st["boss_script"] = _new_script_state()
            bs["round_no"] = int(bs.get("round_no", 0) or 0) + 1
            return _check_phases(st, battle, actor, cfg, bs, logs)
        except Exception:
            return False
    return hook


def _looks_like_boss(actor: dict) -> bool:
    """剧本 Boss 快速判定：role=boss/is_boss 或带 _inst_id（副本 Boss 上下文）。"""
    if actor.get("role") == "boss" or actor.get("is_boss"):
        return True
    if actor.get("_inst_id"):
        return True
    return False


def _new_script_state() -> dict:
    return {
        "phase_count": 0,
        "round_no": 0,
        "summon_cd": 0,
        "summoned": [],
        "flags": {},
        "chain_i": 0,
        "chain_cd": 0,
    }


def _check_phases(st: dict, battle, actor: dict, cfg: dict, bs: dict,
                  logs: list) -> bool:
    """phase 转阶段检查：血量 < 阈值 → 触发（演出/换招/atk 乘区/演出刻 skip）。

    对齐旧 _b_phase（battle_mech.py:698）：
    - 阈值：phases[pc].min（缺省 0.5^n）；pc<3
    - 阈值预告：pc>0 且血量在下一阈值 +3% 内 → 提前 warn（once）
    - 演出：phases[npc-1].script name/icon
    - 换招：add_skills 幂等 append 进 actor.skills + auto_act 切阶段主技能
    - atk 乘区：phases 条目/模板 atk_mult（覆盖式），无 → 旧行为 1+0.2×npc
    - 阶段模板：phase_id → boss_phases.merge_phase_config（preserve_debuffs 等）
    - 演出刻：返回 True（引擎 actor_auto 拦截本刻行动，照推 ct）
    """
    phases = cfg["phases"] or []
    pc = int(bs.get("phase_count", 0) or 0)
    if pc >= len(phases):
        return False
    hp = int(actor.get("hp", 0) or 0)
    mh = int(actor.get("max_hp", 1) or 1)
    if mh <= 0:
        return False
    ratio = hp / mh
    target = _phase_threshold(phases, pc)
    name = actor.get("name", "")
    # ---- 阈值预告（阶段 2/3 起）：接近下一阈值 +3% 提前 2 刻口径输出 ----
    if pc > 0:
        nxt = _phase_threshold(phases, pc)
        within = 0.03
        warned = (bs.setdefault("flags", {})).get("_phase_warned") or []
        if nxt <= ratio <= nxt + within and (pc + 1) not in warned:
            warned = list(warned) + [pc + 1]
            bs["flags"]["_phase_warned"] = warned
            logs.append(f"⚠️ 【{name}】的气息开始紊乱……似乎要进入更凶猛的阶段了！")
    if ratio >= target or pc >= 3:
        return False
    npc = pc + 1
    bs["phase_count"] = npc
    flags = bs.setdefault("flags", {})
    flags["_phase_warned"] = list(flags.get("_phase_warned") or []) + [npc]
    _ph = phases[npc - 1] if npc - 1 < len(phases) else {}
    # ---- 阶段模板合并（phase_id → boss_phases 模板 + 内联覆盖）----
    _merged = None
    try:
        _pid = (_ph or {}).get("phase_id")
        if _pid:
            from ..data.boss_phases import merge_phase_config
            _merged = merge_phase_config(_pid, _ph)
    except Exception:
        _merged = None
    # ---- 演出文案 ----
    script = (_ph or {}).get("script") or (_merged or {}).get("script") or {}
    sname = script.get("name")
    icon = script.get("icon", "🔥")
    if sname:
        logs.append(f"{icon}【{name}】{sname}！")
    logs.append(f"🔥【{name}】进入第 {npc + 1} 阶段！力量再度攀升！")
    # ---- atk 乘区（覆盖式：entry/模板 atk_mult；无 → 旧行为 1+0.2×npc）----
    am = None
    if _merged is not None and (_merged.get("atk_mult") or 1.0) != 1.0:
        am = float(_merged.get("atk_mult"))
    if am is None and (_ph or {}).get("atk_mult") is not None:
        am = float(_ph["atk_mult"])
    if am is None:
        am = 1.0 + 0.2 * npc
    if abs(am - 1.0) > 0.001:
        _apply_atk_phase(actor, am, npc)
        logs.append(f"⚔️【{name}】攻击力提升至 {am:.2f} 倍！")
    # ---- 换招：add_skills 幂等 append + auto_act 切阶段主技能 ----
    adds = list((_merged or {}).get("add_skills") or (_ph or {}).get("add_skills") or [])
    for s in adds:
        if s and s not in (actor.get("skills") or []):
            actor["skills"] = list(actor.get("skills") or []) + [s]
    if adds:
        actor["auto_act"] = {"act": {"type": "skill", "skill": adds[0]}}
        logs.append(f"🎯【{name}】使出了新招【{adds[0]}】！")
    # ---- 异常净化（模板 preserve_debuffs=False 才清；默认保留 50% 语义 P1 简化为全保留）----
    if _merged is not None and _merged.get("preserve_debuffs") is False:
        _phase_cleanse_negatives(actor, logs)
    # ---- 演出刻：本刻不行动（引擎 actor_auto 收到 True 拦截）----
    return True


def _apply_atk_phase(actor: dict, am: float, npc: int) -> None:
    """阶段 atk 乘区 → actor effects（面板快照型：stat/op/mult 内嵌，无需规则注册）。

    stats._apply_effects 折算：entry {stat:"atk", op:"mul", mult:am} → atk ×am；
    matk 同乘（旧行为 atk/matk +20%/阶段双乘）。key=boss_phase_atk 覆盖式
    （后阶段覆盖前阶段，非叠乘——模板 atk_mult 是相对常态的最终乘区）。
    """
    ef = actor.setdefault("effects", {})
    ef["boss_phase_atk"] = {"stat": "atk", "op": "mul", "mult": am, "stacks": 1,
                            "phase": npc}
    ef["boss_phase_matk"] = {"stat": "matk", "op": "mul", "mult": am, "stacks": 1,
                             "phase": npc}
