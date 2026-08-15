# -*- coding: utf-8 -*-
"""v114/v2 多对多站位战斗引擎测试（test_v114_formation.py）

覆盖 27d 审计验收清单 A3-A8 / 27b §11：
  - A3 目标选择：近战 reach1 只打前排；远程 reach2 可指定打后排；指定目标超出射程被拒
  - A3 阵型压缩：formation.compact 纯函数 rank 重编号；战斗内前排死亡即时压缩后排前移
  - A4 多怪回合：敌人按 CTB ct 时间轴行动（v121 起非"每轮固定各行动一次"，见 test_multi_enemy_turns）；全灭=胜利
  - A5 AOE：scope=front 只打前排 / scope=all 打全阵 / falloff 衰减（rank>1 减伤）
  - A6 蓄力：施放扣MP → 蓄力中禁普攻 → 回合开始自动释放；受击打断返还50% MP；控制打断；DOT 不打断
  - A7 召唤/援军：_summon_entity 召唤物带 rank/reach 进前排；_summon_minions 援军入 enemies
  - A8 兼容：单怪 Battle("monster", enemy_dict) + enemy/e_buffs 读写行为不变

环境铁律：私有库 test_v114_formation.db（绝不碰生产库）；确定性用固定 seed / 确定性构造；
不改 conftest.py / game/ 实现代码。

== 审计期间发现的引擎规格缺口 ==
本测试开发过程中曾通过用例暴露并记录了以下引擎缺口；审计（T6）修复已落地到 game/battle.py
（"审计 P1 修复"等），对应用例现按修复后正确行为断言并通过：
  - G1〔A3〕指定目标超出射程未拒绝（_resolve_player_target 已加射程校验，battle.py:477）
  - G2〔A3/A5〕战斗内敌方死亡未即时压缩（_damage_enemy 死亡即 _remove_unit+compact，battle.py:3054）
  - G3〔A5〕AOE 逐目标不消费各自防御（_aoe_damage 已并入逐目标减伤）
  - G4〔A6〕蓄力释放被自身冷却阻塞（释放路径已绕过 CD 重复校验）
  - G5〔A6〕蓄力释放重复扣 MP（释放路径已不重复扣）
保留这些用例 = 回归护栏，防止上述缺陷回退。TEST_BUG 列表在引擎已修复时为空的即属此情形。
"""
import os
import sys
import random

os.environ["GWEN_GAME_DB"] = os.path.abspath("test_v114_formation.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import formation as FM  # noqa: E402

passed = failed = 0
KNOWN_BUGS = []


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail)[:250]}")


def mk_unit(name, hp=1000, atk=10, matk=0, rank=1, reach=1, spd=10, def_=0, mdef=0,
            buffs=None, stacks=None, charging=None, skills=None, uid=None):
    return {"uid": uid or "e_%s" % name, "name": name, "hp": hp, "max_hp": hp,
            "atk": atk, "def": def_, "matk": matk, "mdef": mdef, "spd": spd, "crit": 0,
            "dodge": 0, "rank": rank, "reach": reach, "side": "enemy",
            "buffs": buffs if buffs is not None else {}, "stacks": stacks if stacks is not None else {},
            "defending": False, "charging": charging, "skills": skills if skills is not None else []}


def mk_player(cls="cls_zhan_shi", learned=None, hp=5000, mp=100, reach=2, spd=0, atk=500, **extra):
    p = {"class_name": cls, "level": 30, "hp": hp, "max_hp": hp,
         "mp": mp, "max_mp": mp, "reach": reach, "crit": 0.0, "dodge": 0.0,
         "equipment": {"weapon": {"name": "测试剑",
                                  "stats": {"atk": atk, "matk": 500, "spd": spd},
                                  "affixes": [], "enhance": 0}},
         "attributes": {"str": 10, "int": 10},
         "learned_skills": learned or [], "race": "human"}
    p.update(extra)
    return p


def hp_of(b, name):
    for u in b.enemies:
        if u["name"] == name:
            return u["hp"]
    return None  # 单位已被移除（死亡即压缩）


# ============ A3 目标选择 ============
def test_formation_select_target():
    clean_db()
    front1 = mk_unit("甲", rank=1, reach=1)
    front2 = mk_unit("乙", rank=1, reach=1)
    back = mk_unit("丙", rank=2, reach=2)
    units = [front1, front2, back]
    t = FM.select_target({"reach": 1, "uid": "p"}, units)
    check("近战只在前排选", t and t["rank"] == 1, str(t))
    t2 = FM.select_target({"reach": 2, "uid": "p"}, units)
    check("远程前排优先", t2 and t2["rank"] == 1, str(t2))
    front1["hp"] = 0
    front2["hp"] = 0
    t3 = FM.select_target({"reach": 1, "uid": "p"}, units)
    check("前排死光近战兜底可打后排", t3 and t3["name"] == "丙", str(t3))
    units2 = [mk_unit("甲", rank=1, uid="a"), mk_unit("乙", rank=1, uid="b")]
    t4 = FM.select_target({"reach": 1, "uid": "p"}, units2, threat={"a": 10, "b": 99})
    check("同层按仇恨最高", t4 and t4["uid"] == "b", str(t4))


def test_battle_target_behaviour():
    """远程指定后排可命中；近战自动目标只选前排。"""
    clean_db()
    front = mk_unit("狼头领", hp=3000, atk=0, rank=1, reach=1)
    back = mk_unit("狼巫", hp=3000, atk=0, rank=2, reach=2)
    pr = mk_player(cls="cls_fa_shi", reach=2, spd=0)
    br = BT.Battle("monster", None, {}, player=pr, enemies=[dict(front), dict(back)])
    br.player_turn("attack", None, pr, target="狼巫", enemy_act=False)
    check("远程 reach2 可指定打后排", hp_of(br, "狼巫") < 3000, f"狼巫 hp={hp_of(br, '狼巫')}")
    pm = mk_player(reach=1, spd=0)
    bm = BT.Battle("monster", None, {}, player=pm, enemies=[dict(front), dict(back)])
    bm.player_turn("attack", None, pm, enemy_act=False)
    check("近战自动目标打前排（后排不掉）", hp_of(bm, "狼巫") == 3000, f"狼巫 hp={hp_of(bm, '狼巫')}")


def test_melee_target_out_of_range():
    """[引擎 P1 修复已落地] 近战 reach1 指定 rank2 后排 → 被拒（提示够不着 + 不结算回合/敌方不行动）。"""
    clean_db()
    front = mk_unit("狼头领", hp=3000, atk=30, rank=1, reach=1)
    back = mk_unit("狼巫", hp=3000, atk=0, rank=2, reach=2)
    pm = mk_player(reach=1, spd=0, hp=1000)
    bm = BT.Battle("monster", None, {}, player=pm, enemies=[front, back])
    hp_b = hp_of(bm, "狼巫")
    player_hp0 = pm["hp"]
    cd0 = dict(bm.cooldown)
    random.seed(2)
    logs, ended = bm.player_turn("attack", None, pm, target="狼巫", enemy_act=True)
    check("近战指定后排被拒（后端未掉血）", hp_of(bm, "狼巫") == hp_b, f"{hp_b}->{hp_of(bm, '狼巫')}")
    check("返回『够不着/攻击范围外』提示",
          any(("够不着" in x or "攻击范围之外" in x or "射程" in x) for x in logs), str(logs[:3]))
    check("被拒回合未结算敌方行动（玩家不掉血）", pm["hp"] == player_hp0, f"hp {player_hp0}->{pm['hp']}")
    check("被拒回合未进入敌方阶段（冷却未递减）", dict(bm.cooldown) == cd0, str(bm.cooldown))
    check("未进入结束/胜利", ended is False, str(ended))


# ============ A3 阵型压缩 ============
def test_formation_compact():
    clean_db()
    front = mk_unit("甲", rank=1, reach=1)
    mid = mk_unit("乙", rank=2, reach=1)
    back = mk_unit("丙", rank=3, reach=2)
    units = [front, mid, back]
    front["hp"] = 0
    removed = FM.compact(units)
    check("compact 移除死亡单位", removed == [front], str([u["name"] for u in removed]))
    check("compact 后排前移 rank 重编号", [u["name"] for u in units] == ["乙", "丙"]
          and [u["rank"] for u in units] == [1, 2], str([(u["name"], u["rank"]) for u in units]))
    check("front_rank 无存活返回 MAX_RANKS+1",
          FM.front_rank([{"rank": 1, "hp": 0}]) == FM.MAX_RANKS + 1)


def test_compact_on_death():
    """[引擎 P1 修复已落地] 战斗内前排死亡 → 即时压缩、存活后排 rank 重编号为 1。"""
    clean_db()
    front = mk_unit("狼头领", hp=3000, atk=0, rank=1, reach=1)
    back = mk_unit("狼巫", hp=3000, atk=0, rank=2, reach=2)
    p = mk_player(reach=1, spd=0, atk=10 ** 6)
    b = BT.Battle("monster", None, {}, player=p, enemies=[front, back])
    b._damage_enemy(10 ** 9, [], target=b.enemies[0])  # 打死前排
    check("前排死亡被移除（enemies 仅剩存活）", [u["name"] for u in b.enemies] == ["狼巫"],
          str([(u["name"], u["hp"]) for u in b.enemies]))
    check("存活后排 rank 重编号为 1", all(u["rank"] == 1 for u in b.enemies),
          str([(u["name"], u["rank"]) for u in b.enemies]))
    check("enemy property 指向新前排", b.enemy["name"] == "狼巫", f"enemy={b.enemy['name']}")
    # 近战 reach1 现在可打已前移的后排（压缩后近战有目标）
    picked = b._resolve_player_target(p)
    check("近战可选中压缩后前排", picked is not None and picked["name"] == "狼巫",
          str(picked and picked["name"]))


# ============ A4 多怪回合 + 全灭 ============
def test_multi_enemy_turns():
    clean_db()
    p = mk_player(reach=2, hp=500000, spd=0)
    b = BT.Battle("monster", None, {}, player=p,
                  enemies=[mk_unit("怪甲", hp=10 ** 9, atk=30, spd=10),
                           mk_unit("怪乙", hp=10 ** 9, atk=30, spd=15),
                           mk_unit("怪丙", hp=10 ** 9, atk=30, spd=10)])
    hp0 = p["hp"]
    random.seed(4)
    # v121 CTB：敌方行动段按 ct 调度（不再"每怪每轮固定行动一次"）。把玩家 ct 置高
    # （玩家行动后处于时间轴后方），使三个敌方单位均在当段轮到行动，验证多怪可各自命中玩家。
    b.p_ct = 5.0
    logs, _ = b._enemy_phase(p, [], True)
    check("多怪每怪各行动一次（玩家受击）", p["hp"] < hp0, f"loss={hp0 - p['hp']}")
    hit = set()
    for x in logs:
        for nm in ("怪甲", "怪乙", "怪丙"):
            if nm in x and "攻击" in x:
                hit.add(nm)
    check("三只怪都出手", hit == {"怪甲", "怪乙", "怪丙"}, str(sorted(hit)))


def test_all_dead_victory():
    clean_db()
    b = BT.Battle("monster", None, {}, player=mk_player(reach=3, spd=0),
                  enemies=[mk_unit("怪1", hp=1, rank=1), mk_unit("怪2", hp=1, rank=1),
                           mk_unit("怪3", hp=1, rank=1)])
    b._aoe_damage(10 ** 6, [], "all")
    check("AOE 打遍三只怪全部死亡", not FM.alive_units(b.enemies),
          str([(u["name"], u["hp"]) for u in b.enemies]))
    check("敌方无存活 → _enemy_dead True", b._enemy_dead(), "")


# ============ A5 AOE ============
def test_aoe_scope_fallback():
    clean_db()
    b = BT.Battle("monster", None, {}, player=mk_player(reach=3, spd=0),
                  enemies=[mk_unit("甲", hp=1000, rank=1), mk_unit("乙", hp=1000, rank=1),
                           mk_unit("丙", hp=1000, rank=2)])
    b._aoe_reach = 3
    b._aoe_falloff = 1.0
    b._aoe_damage(100, [], "front")
    check("front AOE 只伤前排", hp_of(b, "甲") == 900 and hp_of(b, "乙") == 900
          and hp_of(b, "丙") == 1000,
          str([(u["name"], u["hp"]) for u in b.enemies]))
    b._aoe_damage(100, [], "all")
    check("all AOE 伤全阵", hp_of(b, "丙") == 900, f"丙 hp={hp_of(b, '丙')}")
    b2 = BT.Battle("monster", None, {}, player=mk_player(reach=3, spd=0),
                   enemies=[mk_unit("甲", hp=1000, rank=1), mk_unit("丙", hp=1000, rank=2)])
    b2._aoe_reach = 3
    b2._aoe_falloff = 0.5
    b2._aoe_damage(100, [], "all")
    check("falloff 后排减半", hp_of(b2, "丙") == 950, f"丙 hp={hp_of(b2, '丙')}")


def test_aoe_per_target_falloff():
    """AOE 逐目标独立：rank1 全额、rank2/rank3 各自按 falloff（同构造全阵）。"""
    clean_db()
    b = BT.Battle("monster", None, {}, player=mk_player(reach=3, spd=0),
                  enemies=[mk_unit("前排", hp=10 ** 6, rank=1),
                           mk_unit("中排", hp=10 ** 6, rank=2),
                           mk_unit("后排", hp=10 ** 6, rank=3)])
    b._aoe_reach = 3
    b._aoe_falloff = 0.7
    b._aoe_damage(1000, [], "all")
    check("rank1 全额 1000", (10 ** 6) - hp_of(b, "前排") == 1000, f"前排={hp_of(b, '前排')}")
    check("rank2=rank3=700（各自 falloff）",
          (10 ** 6) - hp_of(b, "中排") == 700 and (10 ** 6) - hp_of(b, "后排") == 700,
          f"中排={hp_of(b, '中排')} 后排={hp_of(b, '后排')}")


def test_aoe_target_def_gap():
    """[规格 G3] _aoe_damage 未消费目标各自防御（高防/低防同伤）。
    规格 §5 要求逐目标独立走完整伤害链（各自 def/mdef/减免）。当前高防未显著减伤 → FAIL。"""
    clean_db()
    b = BT.Battle("monster", None, {}, player=mk_player(reach=3, spd=0),
                  enemies=[mk_unit("高防", hp=10 ** 6, rank=1, def_=500000),
                           mk_unit("低防", hp=10 ** 6, rank=2, def_=0)])
    b._aoe_reach = 3
    b._aoe_falloff = 1.0
    b._aoe_damage(500, [], "all")
    hi = (10 ** 6) - hp_of(b, "高防")
    lo = (10 ** 6) - hp_of(b, "低防")
    check("高防目标扣血显著更少（逐目标消费防御）", hi < lo, f"高防={hi} 低防={lo}")
    if hi == lo:
        KNOWN_BUGS.append("G3：_aoe_damage 未逐目标消费各自 def/mdef/减免（battle.py:2987）")


# ============ A6 蓄力 ============
def test_charge_cast():
    clean_db()
    p = mk_player(learned=["蓄力斩"], mp=100, spd=0)
    e = mk_unit("靶子", hp=99999, atk=0)
    b = BT.Battle("monster", e, {}, player=p)
    mp0 = p["mp"]
    logs, _ = b.player_turn("skill", "蓄力斩", p, enemy_act=False)
    check("施放进入蓄力(剩1)", b.charging and b.charging["left"] == 1, str(b.charging))
    check("蓄力施放扣MP(16)", p["mp"] == mp0 - 16, f"{mp0}->{p['mp']}")
    check("施放回合不结算（靶子不掉血）", e["hp"] == 99999, f"hp={e['hp']}")


def test_charge_blocks_attack():
    """蓄力中(charge>=2, 下一回合仍蓄力)禁普攻 → 提示。"""
    clean_db()
    p = mk_player(learned=["蓄力斩"], mp=100, spd=0)
    e = mk_unit("靶子", hp=99999, atk=0)
    b = BT.Battle("monster", e, {}, player=p)
    b.charging = {"skill": "蓄力斩", "left": 2, "name": "蓄力斩", "mp_spent": 16}
    logs, _ = b.player_turn("attack", None, p, enemy_act=False)
    check("蓄力中普攻被拦截（提示正在蓄力）", any("正在蓄力" in x for x in logs), str(logs[:3]))
    check("蓄力中普攻未泄力（charging 仍在）", b.charging is not None, str(b.charging))


def test_charge_release_damage():
    """蓄力回合开始自动释放 → 技能效果生效（伤害）。用 CD 已清确保释放路径本身能结算。
    [G5 注] 释放不应重复扣 MP（§6.2「不重复扣 MP/资源」）；当前 _do_player_skill 释放路径仍
    再次扣 MP → 本用例"释放不重复扣MP"当前 FAIL，一并记录 G5。"""
    clean_db()
    p = mk_player(learned=["蓄力斩"], mp=100, spd=0)
    e = mk_unit("靶子", hp=99999, atk=0)
    b = BT.Battle("monster", e, {}, player=p)
    p["mp"] = 84  # 模拟施放已扣 16
    b.charging = {"skill": "蓄力斩", "left": 1, "name": "蓄力斩", "mp_spent": 16}
    b.cooldown.pop("蓄力斩", None)  # 清 CD：隔离"释放路径能结算"（G4 是 CD 阻塞问题）
    mp1 = p["mp"]
    logs = []
    released = b._player_charge_release(p, logs)
    check("蓄力回合开始触发释放", released, f"released={released}")
    check("释放技能效果造成伤害（清CD后生效）", e["hp"] < 99999, f"靶子 hp={e['hp']}")
    check("释放清空蓄力", not b.charging, str(b.charging))
    check("释放不重复扣MP", p["mp"] == mp1, f"{mp1}->{p['mp']}")
    if p["mp"] != mp1:
        KNOWN_BUGS.append("G5：蓄力释放 _do_player_skill 再次扣MP（§6.2 应不重复扣）")


def test_charge_release_cd_gap():
    """[规格 G4] 真实 蓄力斩(cd=4) 释放回合被自身 CD 阻塞 → 伤害不生效。规格应自动结算。"""
    clean_db()
    p = mk_player(learned=["蓄力斩"], mp=100, spd=0)
    e = mk_unit("靶子", hp=99999, atk=0)
    b = BT.Battle("monster", e, {}, player=p)
    b.player_turn("skill", "蓄力斩", p, enemy_act=False)  # 施放设 CD=4
    hp0 = e["hp"]
    released = b._player_charge_release(p, [])  # 下回合开始：蓄力释放（隔离，不含玩家普攻）
    check("真实蓄力斩释放造成伤害（不被自身CD阻塞）", e["hp"] < hp0, f"hp={hp0}->{e['hp']}")
    if released and e["hp"] == hp0:
        KNOWN_BUGS.append("G4：蓄力技能释放被自身CD阻塞（_do_player_skill 释放路径仍查 _skill_on_cd）")


def test_charge_interrupt():
    clean_db()
    p = mk_player(learned=["蓄力斩"], mp=100, spd=0)
    e = mk_unit("怪", hp=10 ** 9, atk=0)
    b = BT.Battle("monster", e, {}, player=p)
    b.charging = {"skill": "蓄力斩", "left": 2, "name": "蓄力斩", "mp_spent": 16}
    mp_before = p["mp"]
    # 屏蔽随机闪避，保证受击断言确定性（蓄力打断精确断言）
    _orig_ps = b._player_stats
    def _ps_nododge(p_):
        s = _orig_ps(p_)
        s["dodge"] = 0.0
        return s
    b._player_stats = _ps_nododge
    logs = []
    b._damage_player(p, 50, logs, source="怪")  # 玩家受击 → 打断 + 返还 50%MP
    check("玩家受击打断蓄力", not b.charging, str(b.charging))
    check("打断返还50%已扣MP(16→8)", p["mp"] == mp_before + 8, f"{mp_before}->{p['mp']}")
    check("打断日志", any("打断" in x for x in logs), str(logs))
    e2 = mk_unit("蓄力怪", hp=1000, charging={"skill": "ms_charge", "left": 2, "name": "蓄力猛击"})
    p2 = mk_player(reach=1, spd=0, atk=500)
    b2 = BT.Battle("monster", e2, {}, player=p2)
    random.seed(2)
    logs2, _ = b2.player_turn("attack", None, p2, enemy_act=False)
    check("攻击打断敌方蓄力", not e2["charging"], str(e2.get("charging")))
    e3 = mk_unit("蓄力怪3", hp=1000, charging={"skill": "x", "left": 2, "name": "聚气"})
    b._interrupt_charging(e3, [], source="你的控制")
    check("控制打断敌方蓄力", not e3["charging"], str(e3.get("charging")))
    b4 = BT.Battle("monster", None, {}, player=mk_player(reach=1, spd=0),
                   enemies=[mk_unit("毒怪", hp=1000, rank=1, charging={"skill": "x", "left": 2, "name": "聚气"})])
    b4._damage_enemy(10, [], wake_sleep=False, target=b4.enemies[0])
    check("DOT(wake_sleep=False) 不打断敌方蓄力", b4.enemies[0]["charging"] is not None,
          str(b4.enemies[0].get("charging")))


# ============ A7 召唤/援军 ============
def test_summon_minions():
    clean_db()
    e = mk_unit("首领", hp=10000, atk=10)
    p = mk_player(reach=1, spd=0)
    b = BT.Battle("monster", e, {}, player=p)
    created = b._summon_minions(2)
    check("援军入 enemies 阵列", len(b.enemies) == 3, str(len(b.enemies)))
    check("援军 rank1/reach1", all(u["rank"] == 1 and u["reach"] == 1 for u in created))
    check("援军字段齐全", all(u.get("buffs") is not None and u.get("stacks") is not None
                             and u.get("charging") is None and u.get("defending") is False
                             for u in created), str(created))


def test_summon_entity():
    clean_db()
    p = mk_player(reach=1, spd=0, hp=1000, atk=1000)
    e = mk_unit("靶子", hp=10 ** 9, atk=0)
    b = BT.Battle("monster", e, {}, player=p)
    logs = []
    ok = b._summon_entity("skeleton", p, logs)
    check("召唤成功", ok, str(logs))
    check("召唤物带 rank/reach", b.summons and b.summons[0].get("rank") is not None
                               and b.summons[0].get("reach") is not None, str(b.summons))
    check("骷髅 rank=1（前排肉盾）", b.summons and b.summons[0]["rank"] == 1,
          str(b.summons and b.summons[0].get("rank")))
    hit = False
    for seed in range(40):
        random.seed(seed)
        logs_ = []
        b._damage_player(p, 100, logs_)
        if any("挡下" in x or "倒下了" in x for x in logs_):
            hit = True
            break
    check("召唤物经受敌方攻击（挡刀）", hit, "")


# ============ A8 兼容 ============
def test_single_enemy_compat():
    clean_db()
    e = mk_unit("单怪", hp=500, atk=5)
    p = mk_player(reach=1, spd=0)
    b = BT.Battle("monster", e, {}, player=p)
    check("单怪构造兼容 enemy 主目标", b.enemy["name"] == "单怪", "")
    check("单怪包装成 enemies[1]", len(b.enemies) == 1, str(len(b.enemies)))
    b.e_buffs["def_down"] = 2
    check("e_buffs 写入代理主目标 buffs", b.enemy["buffs"].get("def_down") == 2, str(b.e_buffs))
    b.e_buffs = {"poison": 3}
    check("e_buffs 整体赋值 setter", b.enemy["buffs"].get("poison") == 3, str(b.enemy["buffs"]))
    b.e_defending = True
    check("e_defending 读写代理", b.e_defending is True and b.enemies[0]["defending"] is True,
          str(b.e_defending))
    st = b.to_state()
    check("to_state 含 enemies 阵列", isinstance(st.get("enemies"), list) and len(st["enemies"]) == 1,
          str(st.keys()))
    check("to_state 保留 enemy 兼容键", st.get("enemy") is not None, "")
    b2 = BT.Battle.from_state(st)
    check("from_state 恢复单怪", b2.enemy["name"] == "单怪" and b2.e_buffs.get("poison") == 3,
          str(b2.enemy.get("name")))


def main():
    print("===== v114 多对多站位战斗引擎（formation/多怪/AOE/蓄力/召唤/兼容）=====")
    test_formation_select_target()
    test_battle_target_behaviour()
    test_melee_target_out_of_range()
    test_formation_compact()
    test_compact_on_death()
    test_multi_enemy_turns()
    test_all_dead_victory()
    test_aoe_scope_fallback()
    test_aoe_per_target_falloff()
    test_aoe_target_def_gap()
    test_charge_cast()
    test_charge_blocks_attack()
    test_charge_release_damage()
    test_charge_release_cd_gap()
    test_charge_interrupt()
    test_summon_minions()
    test_summon_entity()
    test_single_enemy_compat()
    print(f"\n结果: {passed} passed, {failed} failed")
    if KNOWN_BUGS:
        print("已记录引擎规格缺口（供审计修复）：")
        for s in dict.fromkeys(KNOWN_BUGS):
            print("  •", s)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
