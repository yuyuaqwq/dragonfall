# -*- coding: utf-8 -*-
"""组队 / 副本 Boss 模型（32 章三口径 + 保守下界）：

  Boss HP = 模板 × [hp_mult + 0.65 × (人数 - min_players)]
  组队 DPS = 人均一次行动伤害 × 人数 × TEAM_BUFF（队伍技能保守期望 1.10）
  轮数     = Boss HP / 组队每轮总伤害（每轮 = 每人一次行动，与旧校准工具同单位）

⚠️ 未计：元素反应/称号/种族/终结技/控制链/治疗仇恨（真实只会更快）—— 结论偏保守。
⚠️ 实机待复测：instance.py 全状态机（仇恨/CTB队列/阶段）未做全循环模拟（v131 记录）。
"""
from .env import setup_env  # noqa: F401
from .constants import BOSS_HP_MULT, TEAM_PER_PLAYER_ADD, TEAM_BUFF, LOADOUTS
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


def team_matrix(instances: list[str] | None = None,
                loadout: str = "team_mid",
                per_player_dmg_fn=None) -> list[dict]:
    """全副本四档矩阵（供 numeric_calibration.py / CLI 复用）。

    per_player_dmg_fn(cls, lv, gear, edef, mdef) -> float：调用方注入（默认由 player 模型算）。
    返回 [{iid, lv, boss_lv, boss_hp, boss_atk, ratio, rounds, survive, flag, ...}]。

    判定（v131 修正——只算输出不算承伤会出"48.5 轮可打"的幻觉，真实引擎 35 级打老王 5 回合即死）：
      survive  = 玩家承伤回合（HP / Boss 单发期望，按战士面板，Boss 攻强乘区取 enraged×1.35 保守）
      flag     = 🔴 survive < rounds（先死=打不过）或 >60 轮；⚠️ <15 轮过速；🟡 30-60 偏慢；✅ 15-30
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
        dmg = per_player_dmg_fn("cls_zhan_shi", lv, gear, bdef, m.get("mdef", 0))
        tb = 1.0 if loadout == "legacy" else TEAM_BUFF   # 旧模型无团队buff概念，对照必须 1.0
        rounds = team_rounds(dmg, n_eff, hp_tot, team_buff=tb)
        # v131 长盘承伤（含奶续航）：4 人队默认 1 奶（牧师治愈 200% × 50% 轮次占用 ≈ matk/轮）；
        # 净承伤 = hit - heal（下限 hit×20%，奶不足时不能完全抵消）；单刷 n=1 无奶 = 硬抗。
        st_w = build_player("cls_zhan_shi", lv, gear, PlayerOptions(), potion=0.0)
        boss_dmg = _boss_hit(boss_def, m, st_w.get("def", 0), st_w.get("mdef", 0))
        pool = st_w.get("max_hp", 1000) * n_eff
        if n_eff >= 2 and loadout != "legacy":
            # 含奶：heal = 牧师 matk×200%×50% 轮次（治愈术 200% 治疗；保守按自职业 matk 的 0.5× 折算）
            st_healer = build_player("cls_mu_shi", lv, gear, PlayerOptions(), potion=0.0)
            heal = st_healer.get("matk", 0) * 2.0 * 0.5
            net = max(boss_dmg - heal, boss_dmg * 0.2)
        else:
            net = boss_dmg
        survive = pool / max(net, 1) if n_eff >= 1 else 0
        if loadout == "legacy":
            flag = "🔴" if rounds > 80 else "🟡" if rounds > 40 else "✅"
        else:
            # v131 副本 Boss 策略长盘标准（鱼鱼 2026-08-27 拍板：保底大几十轮、拼策略；实测目标 100~150 轮）
            #   ✅ 100~150 轮（阶段/召唤/狂暴/治疗续航有演出空间）
            #   🟡 80~100（略快）或 150~180（略拖）
            #   ⚠️ <80（过速：机制没机会演出 = 秒杀）
            #   🔴 >180（拖死）或 承伤不足（先死）
            flag = "✅"
            if survive < rounds * 0.9:
                flag = "🔴"        # 先死 = 打不过
            elif rounds > 180:
                flag = "🔴"
            elif rounds < 80:
                flag = "⚠️"       # 过速（Boss 机制无演出空间）
            elif rounds < 100 or rounds > 150:
                flag = "🟡"       # 偏快或偏慢
        out.append({
            "iid": iid, "lv": lv, "boss_lv": m.get("lv", 0), "boss_hp": hp_tot,
            "boss_def": bdef, "boss_atk": m.get("atk", 0),
            "ratio": ratio, "rounds": round(rounds, 1), "survive": round(survive, 1),
            "flag": flag, "n_players": n_eff, "loadout": loadout,
        })
    return out


def _boss_hit(boss_def, m, pdef, pmdef):
    """Boss 单发期望伤害（物理/魔法取高者；攻强乘区 enraged ×1.35 保守上限）。"""
    from data.plugins.dragonfall.game import engine as E
    d_phys = E.calc_damage(int(m.get("atk", 0) * 1.35), int(pdef), variance=0.0, dmg_type="phys")
    d_magi = E.calc_damage(int(m.get("matk", 0) * 1.35), int(pmdef), variance=0.0, dmg_type="magi")
    return max(d_phys, d_magi)