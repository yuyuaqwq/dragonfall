# -*- coding: utf-8 -*-
"""组队 / 副本 Boss 模型（32 章三口径 + 保守下界 + v156 队伍构成）：

  Boss HP = 模板 × [hp_mult + 0.65 × (人数 - min_players)]
  组队 DPS = Σ各职业一次行动伤害 × TEAM_BUFF（队伍技能保守期望 1.10）
  轮数     = Boss HP / 组队每轮总伤害（每轮 = 每人一次行动，与旧校准工具同单位）

v156 队伍构成（阶段 4 组队副本平衡性）：
  TEAM_COMPS 定义 4 种构成（standard/all_dps/double_tank/no_heal），
  comp=None 时保持旧行为（战士单人 DPS × 人数）——向后兼容，输出逐字节一致。
  承伤侧：前排(tank)吃 Boss 单发×0.7（减伤），后排吃×0.3（溅射）；
          治疗按牧师治愈折算（heal_per_round：matk×200%×50% 轮次 ×(1+heal_power)）。

⚠️ 未计：元素反应/称号/种族/终结技/控制链/治疗仇恨（真实只会更快）—— 结论偏保守。
⚠️ 实机待复测：instance.py 全状态机（仇恨/CTB队列/阶段）未做全循环模拟（v131 记录）。
"""
from .env import setup_env  # noqa: F401
from .constants import BOSS_HP_MULT, TEAM_PER_PLAYER_ADD, TEAM_BUFF, LOADOUTS
from .player import PlayerOptions  # noqa: E402  (v156 队伍构成 _comp_survive 用)
from data.plugins.dragonfall.game import content as C  # noqa: E402


def boss_hp(base_hp: int, n_players: int, min_players: int = 1,
            hp_mult: float | None = None) -> int:
    """副本 Boss 实际血量（32 章三：模板 × [hp_mult + 0.65×(n-min_players)]）。"""
    hp_mult = hp_mult or BOSS_HP_MULT.get(n_players, 2.85)
    return int(base_hp * (hp_mult + TEAM_PER_PLAYER_ADD * (n_players - min_players)))


def team_rounds(per_player_dmg: float, n_players: int, boss_hp_total: int,
                team_buff: float = TEAM_BUFF) -> float:
    """组队击杀轮数 = BossHP / (人均行动伤害 × 人数 × 团队buff)。"""
    return boss_hp_total / max(per_player_dmg * n_players * team_buff, 1.0)


def team_net_mult(n_players: int, min_players: int, hp_mult: float | None = None,
                  team_buff: float = TEAM_BUFF) -> float:
    """组队净效率 = 人数 × 团队buff ÷ 血量涨幅（相对单刷基准 1.0；>1 = 组队更快）。"""
    hp_mult = hp_mult or BOSS_HP_MULT.get(n_players, 2.85)
    blood = hp_mult + TEAM_PER_PLAYER_ADD * (n_players - min_players)
    return n_players * team_buff / max(blood, 1.0)


def instance_details(iid: str):
    """单副本详情：Boss 模板 / lv / hp_mult / min_players。"""
    inst = C.INSTANCES.get(iid)
    if not inst:
        raise KeyError(f"未知副本: {iid}")
    boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
    return inst, boss_def


# ---------------- v156 队伍构成 ----------------
# (职业 id, 站位角色)：tank=前排承伤 / heal=治疗 / dps=输出
TEAM_COMPS = {
    "standard":   [("cls_zhan_shi", "tank"), ("cls_mu_shi", "heal"),
                   ("cls_ci_ke", "dps"), ("cls_fa_shi", "dps")],
    "all_dps":    [("cls_ci_ke", "dps"), ("cls_fa_shi", "dps"),
                   ("cls_you_xia", "dps"), ("cls_ci_ke", "dps")],
    "double_tank": [("cls_zhan_shi", "tank"), ("cls_zhan_shi", "tank"),
                    ("cls_mu_shi", "heal"), ("cls_ci_ke", "dps")],
    "no_heal":    [("cls_zhan_shi", "tank"), ("cls_ci_ke", "dps"),
                   ("cls_fa_shi", "dps"), ("cls_you_xia", "dps")],
}

# 承伤分线口径（v156）：前排坦吃 Boss 单发 ×FRONT_MULT（站位减伤），
# 后排吃 ×BACK_MULT（溅射）；后排单位血量池按 ×BACK_HP_MULT 折算（脆皮）。
FRONT_MULT = 0.7     # 前排：重甲减伤
BACK_MULT = 0.3      # 后排：溅射
BACK_HP_MULT = 0.6   # 后排 HP 池折算（脆皮职业）
# 治疗下限：净承伤不低于 Boss 单发分线 ×HEAL_FLOOR（奶不能完全抵消）
# v173.1 治疗下限（2026-09-04 鱼鱼拍板）：全职奶（HEAL_CAST_SHARE 1.0）下
#   奶量≈Boss 单发（~13%HP/轮），若仍留 20% 净伤下限 → 承伤卡 ~26 轮，达不到
#   "每轮奶能扛 60+ 轮"的容错预期。降至 0.05：奶=伤时净承伤≈0（sv 大幅拉长），
#   但保留 5% 下限防"奶完全免伤"的极端（双奶永动机）。
HEAL_FLOOR = 0.05

HEAL_POWER_MULT = 3.0    # v174：治愈术公式首项 ratio（matk×3.0，块 A 校准版真实公式）
# v173.1 Boss 战治疗预期（2026-09-04 鱼鱼拍板：副本 Boss 战牧师全职奶）：
#   此前 0.5（半奶半输出）导致承伤模型只抵消 36% raw → 多人本 survive ~11 轮（漏 2-3 轮奶
#   就团灭）。Boss 战设计预期 = 牧师每轮治愈（专职奶），heal 翻倍 → 承伤 25-30 轮容错。
# v174：治愈术已公式化（heal_formula=matk×3.0+40+plv×1+slv×15），模型用首项 ratio 3.0 近似
#   （base/plv 成长在装备 matk 主导下占比 <5%，3.0 近似误差可接受；heal_per_round 为队伍
#   承伤校验用，精确到 5% 内足够）
HEAL_CAST_SHARE = 1.0    # 治愈术占用 100% 轮次（Boss 战专职奶，不半输出）


def heal_per_round(cls_lv_gear: tuple) -> float:
    """牧师每轮治疗量（v156/v174 奶量模型）：

    治愈术 heal_formula = matk×3.0 + 40 + player_lv×1.0 + skill_lv×15（块 A 校准）
    × HEAL_CAST_SHARE × (1 + heal_power)
    = 面板 matk × 3.0 × 1.0 × (1 + min(heal_power, 0.5))  （base/成长忽略，<5%）

    heal_power 上限 50%（27 章战斗规则；core/constants.py PCT_CAPS.heal_power=0.5），
    牧师基础 heal_power 10%（classes.py base）。cls_lv_gear = (cls, lv, gear)。
    """
    cls, lv, gear = cls_lv_gear
    from .player import build_player, PlayerOptions
    st = build_player(cls, lv, gear, PlayerOptions(), potion=0.0)
    hpv = min(float(st.get("heal_power", 0) or 0), 0.5)
    return st.get("matk", 0) * HEAL_POWER_MULT * HEAL_CAST_SHARE * (1 + hpv)


def _comp_slots(comp: str | None, loadout: str, n: int) -> list[tuple] | None:
    """构成 → 槽位列表；comp=None 保持旧行为（返回 None 走战士单人）。"""
    if comp is None:
        return None
    slots = TEAM_COMPS.get(comp)
    if slots is None:
        raise KeyError(f"未知队伍构成: {comp}（可用: {', '.join(TEAM_COMPS)}）")
    return slots


def _comp_dps_total(slots: list[tuple], lv: int, gear: dict, edef: int, mdef: int,
                    per_player_dmg_fn) -> tuple[float, list[dict]]:
    """构成总输出 = Σ各职业 per_action_dmg（坦/奶用各自实际 DPS，输出用刺客/法师/游侠）。

    v173.1（鱼鱼拍板 2026-09-04）：heal 槽位输出贡献 = 0——Boss 战牧师专职奶
    （HEAL_CAST_SHARE 1.0），不再半奶半输出。击杀轮按"1 坦 + 1 奶(纯奶) + 2 输出"标定，
    队伍 DPS 比半奶模型低 → 击杀轮相应变长（与承伤 25-30 轮口径配套）。

    返回 (总伤害, 逐职业明细 [{cls, role, dmg}])。
    """
    detail = []
    total = 0.0
    for cls, role in slots:
        if role == "heal":
            # 专职奶：无输出贡献（v173.1）
            d = 0.0
        else:
            d = per_player_dmg_fn(cls, lv, gear, edef, mdef)
        total += d
        detail.append({"cls": cls, "role": role, "dmg": round(d, 1)})
    return total, detail


def _comp_survive(slots: list[tuple], lv: int, gear: dict, boss_dmg: float,
                  build_player) -> tuple[float, dict]:
    """构成承伤轮数（v156 分线口径 + v2.2 职业矩阵修正）：

    前排 tank：Boss 单发 ×FRONT_MULT（重甲减伤），由奶量抵消（净承伤下限 ×HEAL_FLOOR）；
    后排：每人吃 ×BACK_MULT 溅射（无奶减免）；
    **HP 池 = Σ各职业槽位真实面板 HP**（v2.2 修正：不再用"战士 HP×0.6"一刀切，
    法师/刺客等脆皮用各自面板——之前高估承伤轮，显示能扛更多轮实际早死）。
    """
    front = sum(1 for _, role in slots if role == "tank")
    back = len(slots) - front
    heal = 0.0
    # 前排总 HP（tank 槽位各算；双坦=两个战士面板）
    front_pool = 0.0
    back_pool = 0.0
    for cls, role in slots:
        st_member = build_player(cls, lv, gear, PlayerOptions(), potion=0.0)
        if role == "heal":
            heal += heal_per_round((cls, lv, gear))
        if role == "tank":
            front_pool += st_member.get("max_hp", 1000)
        else:
            back_pool += st_member.get("max_hp", 1000)
    if front == 0:
        # 无前排（all_dps）：全员按前排分线承伤（Boss 单发×FRONT_MULT×人数），
        # 血量池按各职业真实面板求和——承伤远低于有坦构成，但无奶无减伤
        raw = boss_dmg * FRONT_MULT * len(slots)
        pool = front_pool + back_pool
    else:
        raw_front = boss_dmg * FRONT_MULT            # 坦承伤（牧师单奶覆盖）
        raw_back = boss_dmg * BACK_MULT * back       # 后排溅射（自扛/群奶/药水）
        pool = front_pool + back_pool * BACK_HP_MULT
    # v173.1 分层净承伤（鱼鱼拍板 2026-09-04）：heal 只抵消坦伤（治愈术单体大奶），
    #   后排溅射由后排 HP 池自扛（不再从总 raw 里扣奶——旧口径把 3 后排溅射也当
    #   \"可被单奶覆盖\"导致承伤被低估）。坦净伤 = max(raw_front - heal, raw_front×HEAL_FLOOR)，
    #   后排净伤 = raw_back（无奶减免）。队伍净承伤 = 坦净 + 后排除，全队池分摊。
    if front == 0:
        net = max(raw - heal, raw * HEAL_FLOOR)
    else:
        net_front = max(raw_front - heal, raw_front * HEAL_FLOOR)
        net = net_front + raw_back
    survive = pool / max(net, 1.0)
    return survive, {"front": front, "back": back, "heal": round(heal, 1),
                     "raw": round(raw_front + raw_back, 1), "net": round(net, 1),
                     "front_pool": round(front_pool, 1), "back_pool": round(back_pool, 1)}


def team_matrix(instances: list[str] | None = None,
                loadout: str = "team_mid",
                per_player_dmg_fn=None,
                comp: str | None = None) -> list[dict]:
    """全副本构成矩阵（供 numeric_calibration.py / CLI / 测试复用）。

    per_player_dmg_fn(cls, lv, gear, edef, mdef) -> float：调用方注入（默认由 player 模型算）。
    comp: "standard"/"all_dps"/"double_tank"/"no_heal"（v156 构成）或 None（旧行为=战士单人）。
    返回 [{iid, lv, boss_lv, boss_hp, boss_atk, ratio, rounds, survive, flag,
           comp, slots, comp_detail, heal, ...}]。

    判定（v131 修正——只算输出不算承伤会出"48.5 轮可打"的幻觉，真实引擎 35 级打老王 5 回合即死）：
      survive  = 玩家承伤轮数（HP / Boss 单发期望，按战士面板，Boss 攻强乘区取 enraged×1.35 保守）
      flag     = 🔴 survive < rounds（先死=打不过）或 >60 轮；⚠️ <15 轮过速；🟡 30-60 偏慢；✅ 15-30
    v136 目标：✅ 60~80 轮 / 🟡 45~60 或 80~100 / ⚠️ <45 或 100~120 / 🔴 >120 或承伤不足。
    """
    from .player import per_action_dmg, PlayerOptions, build_player
    from .gear import gear_loadout

    if per_player_dmg_fn is None:
        if loadout == "legacy":
            # 旧残疾模型：全乘区关闭 + (战士+游侠)普攻均值 ×1.5（与 v131 前 numeric_calibration.py 完全一致）
            def _legacy_fn(cls, lv, gear, edef, mdef):
                opts = PlayerOptions(attr_points=False, tier=False, evolve=False,
                                     skills=False, affixes=False, enchant=False, potion=False)
                d_w = per_action_dmg("cls_zhan_shi", lv, gear, edef, mdef, opts,
                                     potion_on=False, crit=False)
                d_r = per_action_dmg("cls_you_xia", lv, gear, edef, mdef, opts,
                                     potion_on=False, crit=False)
                return (d_w + d_r) / 2 * 1.5
            per_player_dmg_fn = _legacy_fn
        else:
            per_player_dmg_fn = (
                lambda cls, lv, gear, edef, mdef:
                per_action_dmg(cls, lv, gear, edef, mdef, PlayerOptions(), potion_on=True))

    cfg = LOADOUTS.get(loadout, LOADOUTS["team_mid"])
    n = cfg["players"]
    slots = _comp_slots(comp, loadout, n)
    out = []
    for iid, inst in sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0)):
        lv = inst.get("lv", 0)
        boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
        if not boss_def:
            continue
        m = C.build_monster(boss_def, {"id": iid, "name": iid, "area": "instance"})
        mn = inst.get("min_players", 1)
        n_eff = n if n >= mn else mn   # 进不去按最少可进人数（保守）
        hp_tot = boss_hp(m.get("max_hp", 0), n_eff, mn, inst.get("hp_mult"))
        bdef = m.get("def", 0)
        norm = C.build_monster(("m_cal", "普通怪", "dps", boss_def[3], [], []),
                               {"id": "cal", "name": "cal", "area": "cal"})
        ratio = hp_tot / max(norm.get("max_hp", 1), 1)
        gear = gear_loadout(lv, loadout)
        tb = 1.0 if loadout == "legacy" else TEAM_BUFF   # 旧模型无团队buff概念，对照必须 1.0
        if slots is not None:
            # v156 构成：输出 = Σ各职业一次行动伤害（坦/奶用实际 DPS）
            dmg_total, detail = _comp_dps_total(slots, lv, gear, bdef, m.get("mdef", 0),
                                                per_player_dmg_fn)
            rounds = hp_tot / max(dmg_total * tb, 1.0)
        else:
            # 旧行为（comp=None）：战士单人 DPS × 人数 —— 与升级前逐字节一致
            dmg = per_player_dmg_fn("cls_zhan_shi", lv, gear, bdef, m.get("mdef", 0))
            dmg_total = dmg * n_eff
            detail = []
            rounds = team_rounds(dmg, n_eff, hp_tot, team_buff=tb)
        # v131 长盘承伤（含奶续航）：4 人队默认 1 奶（牧师治愈 200% × 50% 轮次占用 ≈ matk/轮）；
        # 净承伤 = hit - heal（下限 hit×20%，奶不足时不能完全抵消）；单刷 n=1 无奶 = 硬抗。
        st_w = build_player("cls_zhan_shi", lv, gear, PlayerOptions(), potion=0.0)
        # v155 单刷适配：_boss_hit 必须乘 atk_mult（此前漏乘导致承伤模型对单人失真——
        # atk_mult 从 1.3 降到 1.0 后工具仍按原始攻击算承伤，永远显示"扛不住"）
        boss_dmg = _boss_hit(boss_def, m, st_w.get("def", 0), st_w.get("mdef", 0),
                             atk_mult=inst.get("atk_mult", 1.0))
        pool = st_w.get("max_hp", 1000) * n_eff
        heal = 0.0
        if slots is not None:
            survive, sdetail = _comp_survive(slots, lv, gear, boss_dmg, build_player)
            heal = sdetail["heal"]
        elif n_eff >= 2 and loadout != "legacy":
            # 含奶：heal = 牧师 matk×200%×50% 轮次（治愈术 200% 治疗；保守按自职业 matk 的 0.5× 折算）
            st_healer = build_player("cls_mu_shi", lv, gear, PlayerOptions(), potion=0.0)
            heal = st_healer.get("matk", 0) * 2.0 * 0.5
            net = max(boss_dmg - heal, boss_dmg * 0.2)
            survive = pool / max(net, 1)
        else:
            # 单刷（n=1）：玩家会吃药水道具（鱼鱼 2026-09-01 纠正"不是无脑承伤"）——
            # 防御药水 def×1.45 + 治疗药水续航（每 3 轮回 50% 血，高级全效药水）
            # 承伤 = 单发 - 每轮治疗（下限 20%），再按玩家 HP 池折算轮数
            pdef_b = int(st_w.get("def", 0) * 1.45)
            pmdef_b = int(st_w.get("mdef", 0) * 1.45)
            dmg_buffed = _boss_hit(boss_def, m, pdef_b, pmdef_b, atk_mult=inst.get("atk_mult", 1.0))
            heal_per_round = st_w.get("max_hp", 1000) * 0.50 / 3.0
            net = max(dmg_buffed - heal_per_round, dmg_buffed * 0.2)
            survive = pool / max(net, 1) if n_eff >= 1 else 0
        if loadout == "legacy":
            flag = "🔴" if rounds > 80 else "🟡" if rounds > 40 else "✅"
        else:
            # v136 副本 Boss 目标（鱼鱼 2026-08-29 拍板：100 太长 → 60-70 轮适中，多策略但不拖沓）
            #   ✅ 60~80 轮（阶段/召唤/狂暴/治疗续航有演出空间，但不拖沓）
            #   🟡 45~60（略快）或 80~100（略拖）
            #   ⚠️ <45（过速：机制没机会演出 = 秒杀）或 100~120（偏拖）
            #   🔴 >120（拖死）或 承伤不足（先死）
            flag = "✅"
            if survive < rounds * 0.9:
                flag = "🔴"        # 先死 = 打不过
            elif rounds > 120:
                flag = "🔴"
            elif rounds < 45 or rounds > 100:
                flag = "⚠️"
            elif rounds < 60 or rounds > 80:
                flag = "🟡"
        row = {
            "iid": iid, "lv": lv, "boss_lv": m.get("lv", 0), "boss_hp": hp_tot,
            "boss_def": bdef, "boss_atk": m.get("atk", 0),
            "ratio": ratio, "rounds": round(rounds, 1), "survive": round(survive, 1),
            "flag": flag, "n_players": n_eff, "loadout": loadout,
            "comp": comp, "dps_total": round(dmg_total, 1),
        }
        if slots is not None:
            row["slots"] = slots
            row["comp_detail"] = detail
            row["heal"] = heal
        out.append(row)
    return out


def _boss_hit(boss_def, m, pdef, pmdef, atk_mult: float = 1.0):
    """Boss 单发期望伤害（物理/魔法取高者；攻强乘区 enraged ×1.35 保守上限）。
    v155：atk_mult 参数——副本实例字段（单人档 1.0-1.05 vs 多人档 1.15-1.35），
    此前漏乘导致承伤模型对单刷失真（见 team_matrix 调用处注释）。"""
    from saintess_engine.formulas import calc_damage
    d_phys = calc_damage(int(m.get("atk", 0) * atk_mult * 1.35), int(pdef), variance=0.0, dmg_type="phys")
    d_magi = calc_damage(int(m.get("matk", 0) * atk_mult * 1.35), int(pmdef), variance=0.0, dmg_type="magi")
    return max(d_phys, d_magi)
