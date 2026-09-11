# -*- coding: utf-8 -*-
"""A2 真引擎多技能循环模拟器 battle2 —— v175 平衡矩阵门禁：职业×流派×副本 Boss

背景：tests/numeric_sim.py 只能单技能/纯普攻模拟（class_battle_matrix），本模块扩展为
“多技能循环”真实引擎模拟器：按流派 rotation 顺序逐技能尝试施放（被 CD/蓝/资源拦截
→ 试下一个；全部拦截 → 普攻），跑真实 BT.Battle 直到分出胜负。

用法（见 battle_rotation docstring）：
    from numeric_lib import battle2
    boss = C.INSTANCES['inst_goblin_camp']['boss']   # 或取 C.INSTANCES[iid]['boss']
    battle2.battle_rotation('cls_zhan_shi', 20, 'solo_low', {'str': 66},
                            ['挥砍', '猛击', '破甲斩'], boss, seeds=8)

口径（与 numeric_sim.class_battle_matrix 对齐）：
  - 直接构造 BT.Battle(btype="monster", enemy=怪, player=玩家)，循环 actor_turn
  - 固定种子序列 seed 0..N-1：每场先 random.seed(seed) 再建人开打（可复现）
  - 玩家 dict 完全对齐 numeric_sim：class_name/level/class_tier/evolve_path/
    equipment/attributes/learned_skills/hp/mp/max_hp/max_mp/race/title_bonus
  - class_tier/evolve_path 按 lv 算：lv>=90→tier3, >=60→tier2, >=30→tier1, else 0；
    evolve_path=1（攻线）
  - 技能拦截判定：actor_turn 返回后 b._p_acts 不变 且 b.result is None
    （O118 前置校验拦截：技能不存在/未学习/冷却中/蓝不足/核心资源不足 →
    玩家刻不开始、敌方不行动；numeric_sim 121-124 行同款逻辑）
  - 击杀轮口径：b._tick_no()（numeric_sim 129 行同款）
  - 护栏 max_turns=500（numeric_sim._MAX_TURNS 同款）
"""
import os
import random
import sys
import copy  # noqa: E402  (v175b：boss 每场 deepcopy 防嵌套 buffs/stacks 串场)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # scripts/numeric_lib/
_SCRIPTS_DIR = os.path.dirname(_SCRIPT_DIR)                       # scripts/
_PLUGIN_DIR = os.path.dirname(_SCRIPTS_DIR)                       # dragonfall/
_TESTS_DIR = os.path.join(_PLUGIN_DIR, "tests")
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))  # qqbot/
for _p in (_QQBOT_DIR, _PLUGIN_DIR, _TESTS_DIR, _SCRIPTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS_DIR, "test_game_data.db"))

from data.plugins.dragonfall.game import content as C  # noqa: E402
from game.content_rules.panel import player_final_stats
from game.content_rules.skills import skill_info
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
try:  # noqa: E402
    from .gear import gear_loadout  # noqa: E402
except ImportError:  # 直接 python 跑本文件（无父包）→ scripts/ 已在 sys.path，按包名导入
    from numeric_lib.gear import gear_loadout  # noqa: E402

_MAX_TURNS = 500  # 单场回合护栏（numeric_sim._MAX_TURNS 同款；正常对局远低于此）

# v175e 全职业被动技能表（battle2 补被动进 learned_skills 用）：
# 从 skills 数据收集 kind=被动 的技能（基础 + 分支全表），按职业聚合。
try:  # noqa: E402
    from data.plugins.dragonfall.game.data import skills as _SK  # noqa: E402

    _SK_ALL_PASSIVES_BY_CLASS = {}
    for _cid, _cdata in _SK.PLAYER_SKILLS.items():
        _acc = {}
        for _sid, _sk in (_cdata.get("skills") or {}).items():
            if (_sk or {}).get("kind") == "被动":
                _acc[_sid] = _sk
        _SK_ALL_PASSIVES_BY_CLASS[_cid] = _acc
    for _cid, _cdata in _SK.BRANCH_SKILLS.items():
        _acc = _SK_ALL_PASSIVES_BY_CLASS.setdefault(_cid, {})
        for _lb, _branches in (_cdata.get("branches") or {}).items():
            for _bname, _sks in (_branches or {}).items():
                for _sid, _sk in (_sks or {}).items():
                    if (_sk or {}).get("kind") == "被动":
                        _acc[_sid] = _sk
    SK_ALL_PASSIVES_BY_CLASS = _SK_ALL_PASSIVES_BY_CLASS
except Exception:  # 导入失败 → 空表（补被动功能降级为无）
    SK_ALL_PASSIVES_BY_CLASS = {}


def tier_path_of(lv: int) -> tuple[int, int]:
    """玩家转职档位（照任务卡）：lv>=90→tier3, >=60→tier2, >=30→tier1, else 0；evolve_path=1（攻线）。"""
    return (3 if lv >= 90 else 2 if lv >= 60 else 1 if lv >= 30 else 0), 1


def attr_pts_total(lv: int) -> int:
    """自由属性点总量 = DEFAULT_ATTR_PTS(9) + (lv-1)×3（numeric_sim ATTR_PTS_TOTAL 同口径）。"""
    return C.DEFAULT_ATTR_PTS + (lv - 1) * 3


def boss_of(boss_def: tuple, warn: bool = True, iid: str | None = None,
            n_players: int = 1) -> dict:
    """boss 6 元组 (id, 名, role, lv, [技能ID], [掉落]) → C.build_monster 展开成怪 dict。

    地图 obj 带 area='instance'（副本口径：instance Boss atk 段乘区生效）。
    展开失败（个别 Boss 需特殊 map 对象）→ fallback numeric_sim.monster_of('boss', lv)。

    v175 口径对齐（鱼鱼拍板）：iid 给定且实例有 hp_mult 时，Boss 血量叠
    team.boss_hp 人数缩放（与 team_matrix / 期望引擎 build_vs_boss 同口径）。
    默认 n_players=1（单人流派矩阵）；多人本传对应人数。
    """
    try:
        bd = tuple(boss_def)
        if len(bd) < 6:
            raise ValueError("boss_def 需要 6 元组 (id, 名, role, lv, [技能], [掉落])，实际长度 %d" % len(bd))
        m = C.build_monster(bd, {"id": bd[0], "name": bd[1], "area": "instance", "lv": bd[3]})
        # v175：叠实例 hp_mult（team.boss_hp 公式）——若调用方给 iid
        if iid:
            from .team import boss_hp as _bh
            inst = C.INSTANCES.get(iid)
            if inst:
                mn = inst.get("min_players", 1)
                n_eff = max(int(n_players or 1), mn)
                hp_tot = _bh(m.get("max_hp", 0), n_eff, mn, inst.get("hp_mult"))
                m = dict(m)
                m["max_hp"] = hp_tot
                m["hp"] = hp_tot
        return m
    except Exception as exc:  # noqa: BLE001 —— 展开失败 fallback，保持与 numeric_sim 同源可跑
        if warn:
            print("[battle2][警告] boss_def 展开失败(%s)，fallback numeric_sim.monster_of('boss', lv=%s)"
                  % (exc, boss_def[3] if len(boss_def) > 3 else "?"))
        from data.plugins.dragonfall.tests import numeric_sim as NS  # noqa: PLC0415
        return NS.monster_of("boss", boss_def[3] if len(boss_def) > 3 else 1)


def battle_rotation(cls_id: str, lv: int, loadout: str, attr: dict,
                    rotation: list[str], boss_def: tuple, boss_lv: int | None = None,
                    seeds: int = 8, max_turns: int = 500,
                    iid: str | None = None, n_players: int = 1,
                    affix_type: str = "atk",
                    rules: list[dict] | None = None) -> dict:
    """真实引擎多技能循环 vs Boss：返回 {wins, avg_rounds, avg_survive}

    - cls_id: 'cls_zhan_shi' 等；loadout: 'solo_mid'/'team_purple9' 等（gear_loadout）；
    - attr: 加点 dict {'str': 全部分配...}（数值=该等级自由点，见下）；
    - rotation: 技能名列表（按施放优先级排序，玩家按此顺序尝试，都不可用→普攻）；
    - rules: balance_data rotation 完整定义（含 cond/prio）——v175e 策略升级：
      有 cond 门槛（rage>=6 / resource_full / cd_ready 等）时，真引擎 AI 在资源不满足时
      跳过该技能（模拟真人"攒够资源再放终结/爆发技"，防止血怒 0 怒放终焉、奥术 0 充能
      放洪流这类白放）。缺省 None = 旧行为（CD 好就放）。
    - boss_def: instances.py boss 6 元组 (id, 名, role, lv, [技能], [掉落]) 或 C.INSTANCES[iid]['boss']；
    - iid: 副本 id；给定则 Boss 血量叠实例 hp_mult（与 team_matrix 同口径，鱼鱼 v175 拍板）
    - n_players: 打本次数（单人=1）
    - affix_type: v175e 词条乘区流派（atk/crit/spd/pene/lifesteal/elem）
    - 玩家 class_tier/evolve_path 按 lv 算：lv>=90→tier3, >=60→tier2, >=30→tier1, else 0；
      evolve_path=1（攻线）
    - wins: seeds 场中胜利场数；avg_rounds: 胜利场平均击杀轮；avg_survive: 失败场平均存活轮
    """
    seeds = max(1, int(seeds or 8))
    max_turns = int(max_turns or _MAX_TURNS)
    tier, path = tier_path_of(int(lv))
    if affix_type and affix_type != "atk":
        # v175e 词条乘区装备（与 build_matrix._gear_of 同源，保证期望/真引擎同面板）
        from .constants import LOADOUTS
        from .gear import make_gear
        cfg = LOADOUTS.get(loadout, {})
        equip = make_gear(int(lv), cfg.get("quality", "blue"), cfg.get("enhance", 0),
                          cfg.get("upgrade", 0), cfg.get("gem_tier", 0),
                          cfg.get("set_bonus", False), affix_type=affix_type)
    else:
        equip = gear_loadout(int(lv), loadout)
    st = player_final_stats(cls_id, int(lv), equip, tier, dict(attr or {}), evolve_path=path)
    # v175e 被动补齐：真实玩家会把该等级可学的被动都学了（被动 stat/proc 才生效）。
    # rotation 只是主动施放循环；learned_skills = rotation 主动技 + 该职业 level≤lv 被动。
    # （施放循环仍只用 rotation——被动不施放，只挂在 learned_skills 供 _passive_map 消费）
    _passives = []
    try:
        _all = skill_info  # noqa
        # 收集该职业所有技能（基础 + 分支）kind=被动 且 lv≤玩家等级
        for _sid, _sk in SK_ALL_PASSIVES_BY_CLASS.get(cls_id, {}).items():
            _nm = _sk.get("name", "")
            _need = int(_sk.get("lv", 999) or 999)
            if _nm and _need <= int(lv):
                _passives.append(_nm)
    except Exception:
        _passives = []
    learned_skills = list(rotation) + _passives
    # v175e 技能等级门槛过滤：真实玩家 Lv.N 学不到 lv>N 的技能（技能学习等级限制），
    # battle2 模拟玩家同样受限——learned_skills 只保留 lv≤玩家等级的主动技 + 被动。
    # （此前直接放行高等级技能 → 25 级玩家拿 95 级大招打本，矩阵 P1 阶段失真）
    _filtered = []
    for _sn in learned_skills:
        _info = skill_info(cls_id, _sn) or {}
        _need = int(_info.get("lv", 0) or 0)
        if _need <= int(lv):
            _filtered.append(_sn)
    learned_skills = _filtered
    # 玩家基础信息（每场重建副本，模板不动——v175b 修复：
    # 原实现 player 在循环外建一次，循环内 actor_turn 直接改模板 player，
    # 第一场打赢后第二场从残血红蓝开始 → 多场胜率系统性偏低/0 胜假象）
    player_base = {
        "class_name": cls_id, "level": int(lv), "class_tier": tier, "evolve_path": path,
        "equipment": equip, "attributes": dict(attr or {}), "learned_skills": learned_skills,
        "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
        "race": "human", "title_bonus": None,
    }
    boss = boss_of(boss_def, iid=iid, n_players=n_players)

    wins = 0
    rounds_sum = 0.0
    survive_sum = 0.0
    loses = 0
    # 预取技能 CD 信息（决定施放优先级：CD 技 CD 好了优先用，0CD 填充技垫档）
    # v175b 修复：原实现每轮从 rotation[0] 开始试，第一个 always 成功的技能占满所有轮次，
    # 导致 CD 终结技永远轮不到（30 轮只放刺击）——真实玩家是 CD 技好了就用、填充技垫档。
    skill_cd = {}
    for skill_name in rotation:
        info = skill_info(cls_id, skill_name)
        skill_cd[skill_name] = float((info or {}).get("cd", 0) or 0)
    # v175e：只施放玩家等级已学会的技能（learned_skills 已过滤 lv≤玩家等级）
    castable = [s for s in rotation if s in learned_skills]
    cd_skills = [s for s in castable if skill_cd.get(s, 0) > 0]
    filler_skills = [s for s in castable if skill_cd.get(s, 0) <= 0]

    # v175e 策略升级：rules（balance_data rotation 完整定义）→ 技能资源门槛
    # cond 语义（与期望引擎 build_matrix._cond_ok 同源）：
    #   rage>=N / cp>=N / chi>=N / faith>=N / energy>=N / resonance>=N → 资源攒够才放
    #   resource_full / resource_low → 资源满/低判定（读职业核心资源 b._p_res()）
    #   cd_ready / always / 无 → 不设门槛（循环层已保证 CD 好才试）
    rule_map = {}
    for _r in (rules or []):
        if isinstance(_r, dict) and _r.get("skill"):
            rule_map[_r["skill"]] = _r.get("cond") or ""

    def _rule_ok(b, skill_name: str) -> bool:
        """balance_data 规则门槛：资源不满足 → False（跳过，等资源）。"""
        cond = rule_map.get(skill_name, "")
        if not cond or cond in ("always", "cd_ready"):
            return True
        # mech 层数门槛（v175e：arcane 奥术充能等——查 b._p_stacks()，非 resources）
        for _mk in ("arcane", "zhan_yi", "hunt_mark", "poison", "thunder", "ice", "fire"):
            if cond.startswith(f"{_mk}>="):
                need = float(cond.split(">=")[1])
                cur = float((b._p_stacks() or {}).get(_mk, 0) or 0)
                return cur >= need
        # 资源阈值 rage>=N / energy>=N ...
        for _res in ("rage", "cp", "chi", "faith", "energy", "resonance", "element"):
            if cond.startswith(f"{_res}>="):
                need = float(cond.split(">=")[1])
                cur = float((b._p_res() or {}).get(_res, 0) or 0)
                return cur >= need
        if cond == "resource_full":
            # v181.M-R2b：按职业主资源的 core_resource_def 已退役 → 资源信息不可得
            # → 走下方既有兜底「不拦（防卡循环）」（rd 空 → mx<=0 → return True）。
            rd = {}
            rk = rd.get("key", "")
            cur = float((b._p_res() or {}).get(rk, 0) or 0)
            mx = float((b._p_res() or {}).get(f"{rk}_max", rd.get("max", 0)) or 0)
            if mx <= 0:
                return True  # 资源信息不可得 → 不拦（防卡循环）
            return cur >= mx
        if cond == "resource_low":
            rd = {}   # 同上：core_resource_def 已退役，资源信息不可得 → 走兜底分支
            rk = rd.get("key", "")
            cur = float((b._p_res() or {}).get(rk, 0) or 0)
            mx = float((b._p_res() or {}).get(f"{rk}_max", rd.get("max", 0)) or 0)
            return cur < mx * 0.5 if mx > 0 else True
        # 未知 cond 保守放行（宁用不卡循环）
        return True

    # v175e 策略层：技能 cond 感知（player_mech_stacks 等"攒层大招"）——
    # 引擎 cond = 条件倍率非施放门槛（随时可放但低层伤害低），真人会憋到满层再打；
    # AI 模拟也要等层数够再放，否则大招全在低层白放（奥术流 DPS 假性崩盘）。
    def _cond_wait_skill(b, skill_name: str) -> bool:
        """技能有 player_mech_stacks 条件但当前不满足 → True（等层，不现在放）。"""
        info = skill_info(cls_id, skill_name)
        cond = (info or {}).get("cond")
        if not cond or cond.get("type") != "player_mech_stacks":
            return False
        return not b._cond_active(info, player)  # 层数未达标 → 等

    for seed in range(seeds):
        random.seed(seed)  # 固定种子序列 seed 0..N-1，可复现（与 numeric_sim 同款）
        # 每场重建敌方与玩家：boss 每场重新展开（build_monster 全新实例，防串场）
        b = BT.Battle(btype="monster", enemy=boss_of(boss_def, iid=iid, n_players=n_players),
                      player=dict(player_base))
        # v180G B7：循环与 Battle 共用同一 actor 对象——b._focus 是权威（出手/承伤/存活判定）
        player = b._focus
        turns = 0
        while b.result is None and turns < max_turns:
            acted = False
            # 施放顺序（v175b + v175e cond 策略）：
            #  1) CD 技：层数达标（非攒层大招）优先；攒层大招若层数够也放；
            #  2) 攒层大招层数不够 → 等（跳过，先放攒层技/填充技）
            #  3) 0CD 填充技（轮换避免死磕第一个），全拦 → 普攻
            try_order = cd_skills + filler_skills
            for skill_name in try_order:
                if not _rule_ok(b, skill_name):
                    continue   # balance 规则门槛未达（怒/能量/资源未够）→ 等资源
                if _cond_wait_skill(b, skill_name):
                    continue   # 攒层大招层数未满 → 本轮不放（等层）
                prev_acts = b._p_acts
                b.actor_turn("skill", skill_name, player)
                # v180G B7 统一 CTB：出手登记后推进到下一个决策点（命中/怪行动结算）
                b.advance_until_next_decision([])
                if b._p_acts != prev_acts:
                    acted = True     # 施放成功 → 本回合结束
                    break
                if b.result is not None:
                    break            # 技能路径中分出胜负（如处决类特技/反击）
            else:
                # 全部技能被拦截 → 普攻（numeric_sim 121-124 行同款转普攻逻辑）
                b.actor_turn("attack", None, player)
                b.advance_until_next_decision([])
                acted = True
            if b.result is not None:
                break
            turns += 1
        _ = acted
        if b.result == "victory":
            wins += 1
            rounds_sum += b._tick_no()
        else:
            # defeat / 超时护栏兜底都算未胜（存活轮口径 = _tick_no）
            loses += 1
            survive_sum += b._tick_no()
    return {
        "wins": wins,
        "avg_rounds": round(rounds_sum / max(wins, 1), 2),
        "avg_survive": round(survive_sum / max(loses, 1), 2),
        "seeds": seeds,
    }


def expect_vs_actual(cls_id: str, lv: int, loadout: str, attr: dict,
                     rotation: list[str], boss_def: tuple, seeds: int = 8) -> dict:
    """占位：主 agent 的期望模型跑完后填对比；先返回 battle_rotation 结果 + expect_kill=None。"""
    res = battle_rotation(cls_id, lv, loadout, attr, rotation, boss_def, seeds=seeds)
    res["expect_kill"] = None
    return res


if __name__ == "__main__":
    # 自检示例：战士 cls_zhan_shi vs 哥布林营地 boss（rotation 挥砍/猛击/破甲斩）
    from data.plugins.dragonfall.game.data import instances as _INST
    _boss = _INST.INSTANCES["inst_goblin_camp"]["boss"]
    _lv, _pts = 20, attr_pts_total(20)
    print("战士 lv%s loadout=solo_low 自由点=%s rotation=挥砍/猛击/破甲斩 vs 哥布林酋长·咕噜(lv%s)"
          % (_lv, _pts, _boss[3]))
    _r = battle_rotation("cls_zhan_shi", _lv, "solo_low", {"str": _pts},
                         ["挥砍", "猛击", "破甲斩"], _boss, seeds=8)
    print("结果:", _r)
