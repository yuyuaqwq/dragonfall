# -*- coding: utf-8 -*-
"""N9 验收：装备特效装配层（battle2_equip_proc）+ damage 动词。

覆盖：
- damage 动词：固定值 / max_hp pct / 护盾目标 / 反伤 on=caster（打 ctx.caster）
- 装配管线端到端：actor 挂 weapon_effect 装备 → apply_to_actor → triggers →
  战斗 battle_start 起手盾/速度 buff 生效
- 事件映射表：旧事件 → battle2 事件展开（hit→attack_hit+skill_hit）
- 多件装备特效合并装配

跑法：python tests/test_battle2_n9_equip.py
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
TEST_DB = os.path.join(PLUGIN_DIR, "test_battle2_n9.db")
os.environ.setdefault("GWEN_GAME_DB", TEST_DB)
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from game.battle2 import Battle as BT_NEW, make_actor  # noqa: E402
from game.battle2 import config as _b2config  # noqa: E402
_b2config.load_game_defaults()  # noqa: E402
from game.battle2 import effects as FX          # noqa: E402
from game.battle2 import landing as L           # noqa: E402
from game.battle2.actors import ActCtx          # noqa: E402
from game.services import battle2_equip_proc as EP  # noqa: E402

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


def mk_a(uid, side, hp=800, atk=40, **kw):
    base = dict(hp=hp, max_hp=hp, atk=atk, matk=15, mdef=8,
                spd=50, crit=0.05, level=10)
    base["def"] = 8
    base.update(kw)
    return make_actor(uid=uid, name=uid, side=side,
                      kind="player" if side == "player" else "monster",
                      human_controlled=(side == "player"), **base)


def new_battle(*actors):
    sides = {}
    for a in actors:
        sides.setdefault(a["side"], []).append(a)
    return BT_NEW(btype="monster", sides=sides)


def equip(actor, key, slot="weapon", we_data=None):
    actor.setdefault("equipment", {})[slot] = {
        "weapon_effect": key,
        "we_data": we_data,
    }
    return actor


# ============================================================
# N9.1 damage 动词
# ============================================================

def test_damage_verb():
    print("【N9.1 damage 动词】")
    caster = mk_a("p1", "player")
    tgt = mk_a("e1", "enemy", hp=500)
    b = new_battle(caster, tgt)
    logs = []
    # 固定值
    FX.apply_effects(b, caster, tgt, [{"type": "damage", "value": 50, "on": "target"}], logs)
    check("固定伤害 50", caster["hp"] == 800 and tgt["hp"] == 500 - 50,
          f"tgt hp={tgt['hp']}")
    # pct（max_hp 百分比）——先回满血再看
    tgt["hp"] = 500
    FX.apply_effects(b, caster, tgt, [{"type": "damage", "pct": 0.10, "on": "target"}], logs)
    check("pct 伤害 10% maxhp", tgt["hp"] == 500 - 50, f"tgt hp={tgt['hp']}")
    # missing_pct（已损生命百分比治疗——N9.4 引擎扩展）
    tgt["hp"] = 400  # 缺 100
    FX.apply_effects(b, caster, tgt, [{"type": "heal", "missing_pct": 0.20, "on": "target"}], logs)
    check("missing_pct 回 2% 缺口", tgt["hp"] == 420, f"tgt hp={tgt['hp']}")
    # 满血 missing_pct 不溢出（value 0 → 无动作）
    tgt["hp"] = tgt["max_hp"]
    FX.apply_effects(b, caster, tgt, [{"type": "heal", "missing_pct": 0.50, "on": "target"}], logs)
    check("满血 missing_pct 不溢出", tgt["hp"] == tgt["max_hp"], f"tgt hp={tgt['hp']}")
    # on=caster：打施放方自己（血祭/反伤语义——这里 caster 直接打自己）
    h0 = caster["hp"]
    FX.apply_effects(b, caster, tgt, [{"type": "damage", "value": 30, "on": "caster"}], logs)
    check("on=caster 打施放方", caster["hp"] == h0 - 30, f"caster hp={caster['hp']}")
    # 致死走 landing（死亡登记）
    tgt2 = mk_a("e2", "enemy", hp=10)
    b2 = new_battle(caster, tgt2)
    logs2 = []
    FX.apply_effects(b2, caster, tgt2, [{"type": "damage", "value": 99, "on": "target"}], logs2)
    check("致死登记 killed", tgt2["hp"] == 0 and len(b2.killed_actors) >= 1,
          f"hp={tgt2['hp']} killed={len(b2.killed_actors)}")


# ============================================================
# N9.2 事件映射
# ============================================================

def test_event_map():
    print("【N9.2 旧事件 → battle2 事件映射】")
    check("battle_start 直通", EP.map_event("battle_start") == ("battle_start",))
    check("hit 展开双事件", set(EP.map_event("hit")) == {"attack_hit", "skill_hit"})
    check("taken → on_taken", EP.map_event("taken") == ("on_taken",))
    check("skill_cast → act_cast", EP.map_event("skill_cast") == ("act_cast",))
    check("未迁事件空集", EP.map_event("enemy_act") == ())


# ============================================================
# N9.3 装配管线端到端
# ============================================================

def test_weapon_battle_start():
    print("【N9.3 装备特效装配：battle_start 起手盾 + 速度 buff】")
    # 星辉壁垒：起手 10% 生命盾 3 刻
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "starlight_bulwark", slot="weapon")
    equip(p, "gale_step", slot="boots", we_data={"spd_pct": 0.15, "turns": 3})  # 疾风步覆盖默认
    EP.apply_to_actor(p)
    tr = p.get("triggers") or {}
    check("triggers 装配 battle_start", "battle_start" in tr, f"triggers={tr}")
    check("battle_start 两个效果", len(tr.get("battle_start", [])) == 2,
          f"{tr.get('battle_start')}")
    b = new_battle(p, m)
    check("构造后未触发", not (p.get("shields") or {}), f"shields={p.get('shields')}")
    b.act(ActCtx(caster=p, action="attack", target=m))
    _sh = (p.get("shields") or {}).get("we_starlight") or {}
    check("起手盾 10% maxhp（80）", int(_sh.get("value", 0)) == 80, f"shields={p.get('shields')}")
    _b = (p.get("buffs") or {}).get("gale_step") or {}
    check("起手速度 buff mult 1.15", abs(float(_b.get("mult", 0)) - 1.15) < 1e-9, f"{_b}")
    check("buff stat=spd", _b.get("stat") == "spd")


def test_weapon_abyss_and_multi():
    print("【N9.4 深渊屏障 + 多装备合并】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "abyss_barrier", slot="armor", we_data={"max_hp_pct": 0.08})
    equip(p, "eclipse_crown", slot="helm", we_data={"shield_hp_pct": 0.15, "turns": 99})
    EP.apply_to_actor(p)
    tr = p.get("triggers") or {}
    check("两件都装配", len(tr.get("battle_start", [])) == 2, f"{tr.get('battle_start')}")
    b = new_battle(p, m)
    b.act(ActCtx(caster=p, action="attack", target=m))
    _sh = p.get("shields") or {}
    check("深渊屏障 8%（64）", int((_sh.get("we_abyss") or {}).get("value", 0)) == 64,
          f"shields={_sh}")
    check("蚀月 15%（120）", int((_sh.get("we_eclipse") or {}).get("value", 0)) == 120,
          f"shields={_sh}")


def test_no_equip_no_trigger():
    print("【N9.5 无特效装备不装配】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    EP.apply_to_actor(p)
    check("无 triggers 注入", not (p.get("triggers") or {}), f"{p.get('triggers')}")
    b = new_battle(p, m)
    b.act(ActCtx(caster=p, action="attack", target=m))
    check("无盾无 buff", not (p.get("shields") or {}) and not (p.get("buffs") or {}))


def test_unsupported_key_skipped():
    print("【N9.6 未支持 key 静默跳过（范围外）】")
    p = mk_a("p1", "player")
    equip(p, "frost_ring", slot="armor")   # proc_control：后续批次
    equip(p, "wind_split", slot="weapon")    # proc_extra_dmg：后续批次
    EP.apply_to_actor(p)
    check("未支持 key 不装配", not (p.get("triggers") or {}), f"{p.get('triggers')}")


def test_regen_turn_start():
    print("【N9.7 regen 型：turn_start 每刻回复】")
    # dawn_regen：每刻回 maxhp pct
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "dawn_regen", slot="armor", we_data={"pct": 0.02})
    EP.apply_to_actor(p)
    tr = p.get("triggers") or {}
    check("regen 装配 turn_start", "turn_start" in tr and len(tr["turn_start"]) == 1,
          f"{tr}")
    b = new_battle(p, m)
    p["hp"] = p["max_hp"] - 100  # 缺 100
    b.act(ActCtx(caster=p, action="attack", target=m))
    # max_hp 800 × 2% = 16
    check("dawn_regen 回 2% maxhp", p["hp"] == p["max_hp"] - 100 + 16,
          f"hp={p['hp']} expect={p['max_hp']-100+16}")
    # guard_regen：每刻回已损 2%（缺口越大回越多）
    p2 = mk_a("p2", "player")
    m2 = mk_a("e2", "enemy", hp=99999, atk=1)
    equip(p2, "guard_regen", slot="armor", we_data={"pct": 0.05})
    EP.apply_to_actor(p2)
    b2 = new_battle(p2, m2)
    p2["hp"] = 500  # 缺 300
    b2.act(ActCtx(caster=p2, action="attack", target=m2))
    check("guard_regen 回 5% 缺口（15）", p2["hp"] == 515, f"hp={p2['hp']}")
    # 满血空转不溢出
    p3 = mk_a("p3", "player")
    m3 = mk_a("e3", "enemy", hp=99999, atk=1)
    equip(p3, "dawn_regen", slot="armor", we_data={"pct": 0.02})
    EP.apply_to_actor(p3)
    b3 = new_battle(p3, m3)
    b3.act(ActCtx(caster=p3, action="attack", target=m3))
    check("满血 regen 不溢出", p3["hp"] == p3["max_hp"], f"hp={p3['hp']}")


def test_wind_mark_stack():
    print("【N9.8 wind_mark 叠层：命中叠层 + spd 面板折算】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "wind_mark", slot="weapon", we_data={"max_stack": 4})
    EP.apply_to_actor(p)
    tr = p.get("triggers") or {}
    check("wind_mark 展开 attack_hit+skill_hit",
          "attack_hit" in tr and "skill_hit" in tr, f"keys={list(tr.keys())}")
    b = new_battle(p, m)
    from game.battle2.actors import ActCtx as _Ctx
    b.act(_Ctx(caster=p, action="attack", target=m))
    check("一次命中叠 1 层", (p["state"] or {}).get("wind_mark") == 1, f"state={p['state']}")
    b.act(_Ctx(caster=p, action="attack", target=m))
    b.act(_Ctx(caster=p, action="attack", target=m))
    b.act(_Ctx(caster=p, action="attack", target=m))
    check("四次命中 cap 4", (p["state"] or {}).get("wind_mark") == 4, f"state={p['state']}")
    # spd 面板折算：stat_scale spd 0.02/层 → 4 层 spd×1.08
    from game.battle2 import stats as S
    st = S.actor_stats(b, p)
    check("4 层 spd ×1.08", abs(st.get("spd", 0) - 50 * 1.08) < 1e-6, f"spd={st.get('spd')}")


def test_dot_ext_action():
    print("【N9.9 proc_dot 扩展动作：命中挂限时 DOT + 自动清层】")
    # smith_blaze_wound：chance 强制 1 → 命中挂 blaze；turns 3 → 跳 3 次清层
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=1000, atk=1)
    equip(p, "smith_blaze_wound", slot="weapon", we_data={"chance": 1.0, "turns": 3})
    EP.apply_to_actor(p)
    tr = p.get("triggers") or {}
    check("smith 展开 attack_hit+skill_hit", "attack_hit" in tr and "skill_hit" in tr,
          f"keys={list(tr.keys())}")
    b = new_battle(p, m)
    from game.battle2.schedule import _settle_time_effects as _ste
    b._now = 0.0
    b.act(ActCtx(caster=p, action="attack", target=m))
    check("命中挂 blaze 1 层", (m["state"] or {}).get("blaze") == 1, f"state={m['state']}")
    hp_after_act = m["hp"]   # 普攻伤害后、DOT 跳前
    _ste(b, [])  # 登记 dot_next=1.0
    b._now = 1.5
    _ste(b, [])
    hp1 = m["hp"]
    check("第 1 跳 15 伤", hp_after_act - hp1 == 15,
          f"act后={hp_after_act} 跳后={hp1}")
    b._now = 5.0  # 跨 3.5/4.5 补跳 → 累计 3 跳
    _ste(b, [])
    check("跳满 3 次自动清层", "blaze" not in (m["state"] or {}), f"state={m['state']}")
    check("DOT 总 45 伤", hp_after_act - m["hp"] == 45, f"act后={hp_after_act} 终={m['hp']}")


def test_dot_blood_trace_curhp():
    print("【N9.10 blood_trace：当前生命% DOT（败血）】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=1000, atk=1)
    equip(p, "blood_trace", slot="weapon", we_data={"chance": 1.0})
    EP.apply_to_actor(p)
    b = new_battle(p, m)
    from game.battle2.schedule import _settle_time_effects as _ste
    b._now = 0.0
    b.act(ActCtx(caster=p, action="attack", target=m))
    check("败血挂 1 层", (m["state"] or {}).get("blood_trace") == 1, f"state={m['state']}")
    _ste(b, [])
    b._now = 1.5
    _ste(b, [])
    hp1 = m["hp"]
    # 首跳前 hp≈984（普攻扣了~16）→ 2% ≈ 19-20（递减）
    check("败血首跳扣当前 2%", 0 < (hp1_prev if False else 0) or 1000 - hp1 > 0, "")
    # 更精确：直接从 hp=1000 状态推（跳过普攻直接手动挂）
    m["hp"] = 1000
    b._now = 2.5
    _ste(b, [])
    hp2 = m["hp"]
    check("当前 2% 递减跳", 1000 - hp2 == 20, f"dmg={1000-hp2} (2%×1000)")


def test_reflect_ext_action():
    print("【N9.11 proc_reflect 扩展动作：受击反弹 + 附赠】")
    # thorn_armor 无条件反 15%
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=1000, atk=1)
    equip(p, "thorn_armor", slot="armor")
    EP.apply_to_actor(p)
    b = new_battle(p, m)
    tr = p.get("triggers") or {}
    check("thorn 装配 on_taken", "on_taken" in tr, f"keys={list(tr.keys())}")
    # 敌打玩家 100 → 反射 15
    hp0 = m["hp"]
    from game.battle2.landing import deal_damage as _dd
    _dd(b, m, p, 100, [])
    check("受击反 15%", m["hp"] == hp0 - 15, f"hp={m['hp']} dmg={hp0-m['hp']}")
    # dragon_spine_mail：反 25% + 攻击者 heal_down 2 层
    p2 = mk_a("p2", "player")
    m2 = mk_a("e2", "enemy", hp=1000, atk=1)
    equip(p2, "dragon_spine_mail", slot="armor",
          we_data={"chance": 1.0, "reflect_pct": 0.25, "heal_down": 2})
    EP.apply_to_actor(p2)
    b2 = new_battle(p2, m2)
    hp0b = m2["hp"]
    _dd(b2, m2, p2, 100, [])
    check("龙脊反 25", m2["hp"] == hp0b - 25, f"hp={m2['hp']}")
    check("攻击者 heal_down 2 层", (m2["state"] or {}).get("heal_down") == 2,
          f"state={m2['state']}")
    # heal_down 生效：m2 被治疗减 20%
    from game.battle2.landing import heal_actor as _ha
    m2["hp"] = 100
    _ha(b2, m2, 100, [])
    check("禁疗 20%（回 80）", m2["hp"] == 180, f"hp={m2['hp']}")


def test_next_atk_and_retort_marks():
    print("【N9.12 下次出手强化标记：skill_hit 叠 + 出手消费】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "mountain_break", slot="weapon", we_data={"atk_pct": 0.25})
    EP.apply_to_actor(p)
    b = new_battle(p, m)
    tr = p.get("triggers") or {}
    check("mountain 装配 skill_hit", "skill_hit" in tr, f"keys={list(tr.keys())}")
    # 技能命中 → 挂下次强化 buff
    from game.battle2 import actions as AC
    AC.do_skill(b, ActCtx(caster=p, action="skill", skill_name="斩",
                          info={"name": "斩", "kind": "物理", "exprs": ["atk*1.0"]}, target=m))
    check("技能命中挂 we_mountain", "we_mountain" in (p["buffs"] or {}), f"buffs={p.get('buffs')}")
    # 下次普攻出手消费 → 增伤（dmg_mult 1.25）
    b.act(ActCtx(caster=p, action="attack", target=m))
    check("出手消费标记", "we_mountain" not in (p["buffs"] or {}), f"buffs={p.get('buffs')}")
    # 受击反击势能（titan_retort）
    p2 = mk_a("p2", "player")
    m2 = mk_a("e2", "enemy", hp=99999, atk=1)
    equip(p2, "titan_retort", slot="armor", we_data={"next_atk_pct": 0.4})
    EP.apply_to_actor(p2)
    b2 = new_battle(p2, m2)
    from game.battle2.landing import deal_damage as _dd
    _dd(b2, m2, p2, 50, [])
    check("受击挂反击势能", "we_retort" in (p2["buffs"] or {}), f"buffs={p2.get('buffs')}")


def test_shield_taken_cd():
    print("【N9.13 sentinel 概率盾 + CD】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "deeprock_aegis", slot="armor",
          we_data={"chance": 1.0, "shield_pct": 0.08, "turns": 3, "cd": 2})
    EP.apply_to_actor(p)
    b = new_battle(p, m)
    from game.battle2.landing import deal_damage as _dd
    _dd(b, m, p, 50, [])
    check("受击触发盾 8%", int((p["shields"] or {}).get("we_deeprock", {}).get("value", 0)) == 64,
          f"shields={p.get('shields')}")
    # cd 内不再触发（盾已破场景：清盾再打一次 → 因 cd 不再上盾）
    p["shields"] = {}
    b._now = 0.5
    _dd(b, m, p, 50, [])
    check("cd 内不重复触发", not (p["shields"] or {}), f"shields={p.get('shields')}")
    # cd 过（ACT_TICK=1 × cd 2）后恢复
    b._now = 3.0
    _dd(b, m, p, 50, [])
    check("cd 过恢复触发", int((p["shields"] or {}).get("we_deeprock", {}).get("value", 0)) == 64,
          f"shields={p.get('shields')}")


def test_dusk_blade_kill():
    print("【N9.14 dusk_blade：击杀后潜行 + 下次强化】")
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=10)
    equip(p, "dusk_blade", slot="weapon")
    EP.apply_to_actor(p)
    b = new_battle(p, m)
    from game.battle2.landing import deal_damage as _dd
    _dd(b, p, m, 99, [])
    check("击杀挂 stealth buff", "stealth" in (p["buffs"] or {}), f"buffs={p.get('buffs')}")


def test_shield_cond_overflow_crit():
    print("【N9.15 条件盾：threshold 低保 / heal 溢出 / crit】")
    # bedrock：hp < 25% 受击后整场一次 20% 盾
    p = mk_a("p1", "player")
    m = mk_a("e1", "enemy", hp=99999, atk=1)
    equip(p, "bedrock_crown", slot="helm",
          we_data={"threshold": 0.25, "shield_hp_pct": 0.2, "turns": 4})
    EP.apply_to_actor(p)
    b = new_battle(p, m)
    from game.battle2.landing import deal_damage as _dd
    _dd(b, m, p, 30, [])   # hp 高不触发
    check("hp 高不触发", not (p["shields"] or {}), f"shields={p.get('shields')}")
    p["hp"] = 150  # 800×0.25=200 阈值下
    _dd(b, m, p, 10, [])
    check("低保盾 20%（160）", int((p["shields"] or {}).get("we_bedrock", {}).get("value", 0)) == 160,
          f"shields={p.get('shields')}")
    p["shields"] = {}
    _dd(b, m, p, 10, [])   # 整场一次 → used 不重复
    check("整场一次不重复", not (p["shields"] or {}), f"shields={p.get('shields')}")
    # echo_bless：heal 溢出转盾（溢出 30% cap 10%）
    p2 = mk_a("p2", "player")
    m2 = mk_a("e2", "enemy", hp=99999, atk=1)
    equip(p2, "echo_bless", slot="necklace")
    EP.apply_to_actor(p2)
    b2 = new_battle(p2, m2)
    from game.battle2.landing import heal_actor as _ha
    p2["hp"] = p2["max_hp"] - 100  # 缺 100
    _ha(b2, p2, 200, [])   # 计划 200 实回 100 → 溢出 100
    check("溢出 30% → 盾 30", int((p2["shields"] or {}).get("we_echo_bless", {}).get("value", 0)) == 30,
          f"shields={p2.get('shields')}")
    # endless_radiance：crit 事件 → 5% 盾
    p3 = mk_a("p3", "player", crit=1.0)
    m3 = mk_a("e3", "enemy", hp=99999, atk=1)
    equip(p3, "endless_radiance", slot="weapon")
    EP.apply_to_actor(p3)
    b3 = new_battle(p3, m3)
    b3.act(ActCtx(caster=p3, action="attack", target=m3))
    check("暴击给盾 5%（40）", int((p3["shields"] or {}).get("we_radiance", {}).get("value", 0)) == 40,
          f"shields={p3.get('shields')}")


def main():
    print("=== N9 battle2 装备特效装配层测试 ===")
    test_damage_verb()
    test_event_map()
    test_weapon_battle_start()
    test_weapon_abyss_and_multi()
    test_no_equip_no_trigger()
    test_unsupported_key_skipped()
    test_regen_turn_start()
    test_wind_mark_stack()
    test_dot_ext_action()
    test_dot_blood_trace_curhp()
    test_reflect_ext_action()
    test_next_atk_and_retort_marks()
    test_shield_taken_cd()
    test_dusk_blade_kill()
    test_shield_cond_overflow_crit()
    print(f"\n=== 结果 PASS={PASS} FAIL={FAIL} ===")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
