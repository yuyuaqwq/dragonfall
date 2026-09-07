# -*- coding: utf-8 -*-
"""v181.P2D-D5a 受击反击族等价探针（test_p2dd5a_counter_cond.py）

验证挂点13 _retaliations_and_buffs 受击反击聚合段 2 proc（counter_chance 以守为攻 /
counter_up 反击之王）从 battle.py 内联双 for 聚合迁移到 passive_procs 注册表族
counter_cond（handler 逐条聚合 ctx 槽）后行为零变化（OLD vs NEW 双实现差分）。

方法（方案 §7 OLD-vs-NEW 探针）：
1. OLD = 迁移前挂点13 反击聚合段原逻辑副本（10776-10800 逐字复刻，含 roll/反击/回气）。
2. NEW = 现引擎 _retaliations_and_buffs 挂点13 段（→ run_proc_family 逐条聚合，
   cap 0.9 + roll + _phys_retort/_hit_back + 反击回气收口在骨架）。
3. 差分矩阵（固定 random seed 双路同 roll）：
   - 学/不学（无/以守为攻/反击之王单学/双学）× 目标存活/死亡 × 怪暴击 0/100%
   - cap 边界：以守为攻 mult=0.80 低伤害 vs 双学 mult=1.20（>1 高伤）→ 同一 roll 流
   - 反击回气（chi 职业）命中后 气+2；非 chi 职业不触
   - 零默认：_ps 空 dict → 无聚合（不 roll 不反击不日志）
   - 多 counter_chance 条目（跨职业合成 pm）→ max/min 全聚（OLD/NEW 一致）
4. 静态：declare_proc + counter_cond 执行器注册 + 挂点13 无旧直读残留 + 33 声明。

运行（与门禁同款 python）：
  python tests/test_p2dd5a_counter_cond.py
"""
import os
import sys
import copy
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as EG  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import passive_procs as PP  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls_id, passives, hp=500):
    """构造战斗玩家 dict（学指定被动中文名）。"""
    out = {
        "class_name": cls_id, "level": 70, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": 100},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {}, "buffs": {}, "eff": {},
        "shields": {}, "v139_modes": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10, atk=50):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": atk, "def": def_, "mdef": mdef, "spd": spd}


def mk_battle(player, enemy=None):
    """构造战斗（深拷贝防 Battle 内 setdefault 污染 OLD 参考源）。"""
    b = BT.Battle("monster", enemy or mk_enemy(), {}, copy.deepcopy(player))
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    b.player.setdefault("buffs", {})
    b.player.setdefault("shields", {})
    b.player.setdefault("eff", {})
    b.player.setdefault("v139_modes", {})
    b.player.setdefault("learned_skills", [])
    return b


def _inject_extra_cc(b, extra_entry):
    """合成 pm：在玩家真实 pm 基础上追加额外 counter_chance 条目（多条目聚合探针）。

    OLD/NEW 都走同一合成 pm 才公平——挂点13 for 遍历用 _proc_pm/_passive_map。
    """
    pm = b._proc_pm(b.player)
    base = dict(pm)
    base.setdefault("proc", {})
    lst = list(base["proc"].get("counter_chance", []))
    lst.append(extra_entry)
    base["proc"]["counter_chance"] = lst
    b._proc_pm = lambda pl: base
    b._passive_map = lambda pl: base
    return b


# ============================================================
# OLD：迁移前挂点13 反击聚合段原逻辑副本（15f0ef7^ 逐字复刻）
# ============================================================
def OLD_counter_segment(b, actor, logs, seed, enemy_hp=None):
    """迁移前 _retaliations_and_buffs 挂点13 反击聚合段（含 roll/反击/回气 + 前置守卫）。

    返回 (target_hp_after, logs)——攻击者 _rtgt 由挂点解析：attacker 缺省 → self.enemy。
    前置段（石拳/盾牌反击/龙鳞等）在 OLD/NEW 差分场景下全部惰性（无对应数据源）。
    random.seed(seed) 使模块流（roll/crit/variance 全程同一流）与 NEW 侧完全同序。
    """
    random.seed(seed)
    _rtgt = b.enemy
    if enemy_hp is not None:
        _rtgt = dict(_rtgt)
        _rtgt["hp"] = enemy_hp
    if _rtgt and _rtgt.get("hp", 0) > 0:
        _cc_list = b._proc_pm(actor)["proc"].get("counter_chance", [])
        _cu_list = b._proc_pm(actor)["proc"].get("counter_up", [])
        if _cc_list or _cu_list:
            _chance = 0.0
            _mult = 1.0
            for _pn, _ps in _cc_list:
                _chance = max(_chance, float(_ps.get("chance", 0.35) or 0.35))
                _mult = min(_mult, float(_ps.get("mult", 0.80) or 0.80))  # 以守为攻 80% 普攻
            if _cu_list:  # 反击之王：+25% 概率、反击伤害 +50%
                for _pn, _ps in _cu_list:
                    _chance += float(_ps.get("chance_add", 0.25) or 0.25)
                    _mult *= 1.0 + float(_ps.get("dmg_add", 0.50) or 0.50)
                    break
            _chance = min(_chance, 0.9)
            if random.random() < _chance:
                # 原 _phys_retort（actor atk×mult vs 目标 def, roll_crit=True）复刻——
                # roll/crit/variance 都走模块 random（seed 后与 NEW 引擎同序同值）
                _st = b._actor_stats_of(actor)
                _est = b._enemy_stats(_rtgt)
                _crit = random.random() < float(_st.get("crit", 0) or 0)
                _d = EG.calc_damage(int(_st.get("atk", 0) * float(_mult or 1.0)),
                                    _est.get("def", 0), _crit, variance=0.15, dmg_type="phys")
                _d = b._boss_dmg_filter(_d, actor, logs)
                _c2_dmg = max(1, _d)
                # _hit_back（_damage_actor 扣目标血——复刻副作用）
                if _rtgt.get("hp", 0) > 0:
                    try:
                        b._damage_actor(_rtgt, _c2_dmg, logs,
                                        source=str(actor.get("name", "敌人") or "敌人") or "反伤")
                    except Exception:
                        pass
                logs.append(f"🥊 反击！你立刻回击造成 {_c2_dmg} 点伤害！"
                            + (" 💥暴击" if _crit else ""))
                # 反击回气（同既有 counter_attack 消费点）：命中后 气 +2
                _cr2_cls = actor.get("class_name", "")
                _cr2_rd = EG.core_resource_def(_cr2_cls)
                if _cr2_rd and _cr2_rd.get("key") == "chi":
                    b._res_gain_class(_cr2_cls, "chi", 2)
    return (_rtgt.get("hp", 0), list(logs))


def NEW_counter_segment(b, actor, logs, seed, enemy_hp=None):
    """NEW：现引擎挂点13 段等价抽取（复刻 _retaliations_and_buffs 段顺序——调用前
    前置段惰性，调用后只取反击段作用后的目标 hp/日志/资源）。

    直接跑 b._retaliations_and_buffs(actor, dmg, logs, attacker=None) 全链，段内
    只触发反击族（前置反伤/石拳/盾反/龙鳞等数据源全空惰性）。random.seed(seed) 使
    引擎模块流（roll/crit/variance）与 OLD 侧同序同值。
    """
    random.seed(seed)
    _rtgt = b.enemy
    if enemy_hp is not None:
        b.enemy["hp"] = enemy_hp
    dmg_out, _interrupted = b._retaliations_and_buffs(actor, 100, logs, attacker=None)
    # _retaliations_and_buffs 前置段（石拳/龙鳞等）空转惰性——但末尾还有「敌方防御者
    # 死亡移除」等整链副作用会改写目标；挂点13 反击族作用后目标 hp 从这里读回：
    return (_rtgt.get("hp", 0), list(logs))


# ============================================================
# 1. 学/不学 × 目标存活/死亡 × 暴击 0/100% 差分（固定 seed）
# ============================================================
def test_learn_matrix():
    print("\n== 1. 学/不学 × 目标态 × 暴击 差分（OLD vs NEW，固定 seed）==")
    combos = [
        ("cls_wu_seng", [], "无被动"),
        ("cls_wu_seng", ["以守为攻"], "以守为攻"),
        ("cls_wu_seng", ["反击之王"], "反击之王(单学=无 chance 底)"),
        ("cls_wu_seng", ["以守为攻", "反击之王"], "双学 60%×120%"),
    ]
    for cls, sk, label in combos:
        for seed in (1, 7, 42, 999):
            for tgt_hp in (100000, 0):
                for crit in (0.0, 1.0):
                    p = mk_player(cls, sk)
                    p["attributes"] = {"str": 10, "int": 10}
                    b_old = mk_battle(dict(p), mk_enemy())
                    b_new = mk_battle(dict(p), mk_enemy())
                    # 暴击：NEW 走 _actor_stats_of——affix 无 crit 键 → 0；用 buffs.crit 顶
                    if crit:
                        b_old.player["buffs"]["crit"] = 1.0
                        b_new.player["buffs"]["crit"] = 1.0
                    logs_o, logs_n = [], []
                    ro = OLD_counter_segment(b_old, b_old.player, logs_o, seed, tgt_hp)
                    rn = NEW_counter_segment(b_new, b_new.player, logs_n, seed, tgt_hp)
                    same = (ro == rn)
                    # 特写：学以守为攻 且 seed 落 35% 内 → 反击伤害复刻一致
                    tag = f"[{label}] seed{seed} 敌hp{tgt_hp} 暴击{crit}"
                    check(f"{tag}: OLD==NEW {ro} vs {rn}", same,
                          f"OLD{ro} NEW{rn}\nOLDlogs{logs_o}\nNEWlogs{logs_n}")


# ============================================================
# 2. cap 边界 + 高/低 mult（0.80 vs 1.20）
# ============================================================
def test_cap_and_mult():
    print("\n== 2. cap 边界与 mult 高/低档（OLD vs NEW 同 roll 流）==")
    # mult=1.20 双学 → 反击伤害高于普攻 → 伤害复刻验证 mult 传递正确
    for seed in (3, 5, 11):
        p = mk_player("cls_wu_seng", ["以守为攻", "反击之王"])
        b_old = mk_battle(dict(p), mk_enemy())
        b_new = mk_battle(dict(p), mk_enemy())
        logs_o, logs_n = [], []
        ro = OLD_counter_segment(b_old, b_old.player, logs_o, seed)
        rn = NEW_counter_segment(b_new, b_new.player, logs_n, seed)
        check(f"双学 seed{seed}: OLD==NEW", ro == rn, f"OLD{ro} NEW{rn} logs{logs_o}/{logs_n}")
    # cap 0.9：chance_add 堆叠超 0.9 → min 截断——合成 counter_chance 0.85 + counter_up 0.25
    p = mk_player("cls_wu_seng", [])
    b_old = mk_battle(dict(p), mk_enemy())
    b_new = mk_battle(dict(p), mk_enemy())
    extra = ("高概率", {"proc": "counter_chance", "chance": 0.85, "mult": 0.80})
    _inject_extra_cc(b_old, extra)
    _inject_extra_cc(b_new, extra)
    # 单 counter_up 条目：0.85+0.25=1.10 → cap 0.9
    up = [("反击之王", {"proc": "counter_up", "chance_add": 0.25, "dmg_add": 0.50})]
    for b in (b_old, b_new):
        pm = b._proc_pm(b.player)
        base = dict(pm)
        base.setdefault("proc", {})
        base["proc"]["counter_up"] = up
        b._proc_pm = lambda pl: base
        b._passive_map = lambda pl: base
    logs_o, logs_n = [], []
    ro = OLD_counter_segment(b_old, b_old.player, logs_o, 2)
    rn = NEW_counter_segment(b_new, b_new.player, logs_n, 2)
    check("cap0.9: 1.10→0.9 截断 OLD==NEW", ro == rn, f"OLD{ro} NEW{rn}")
    # mult min：两条 counter_chance mult 0.80 / 0.60 → min 0.60（低伤档）
    p2 = mk_player("cls_wu_seng", [])
    b_o2 = mk_battle(dict(p2), mk_enemy())
    b_n2 = mk_battle(dict(p2), mk_enemy())
    for b in (b_o2, b_n2):
        pm = b._proc_pm(b.player)
        base = dict(pm)
        base.setdefault("proc", {})
        base["proc"]["counter_chance"] = [
            ("低伤", {"proc": "counter_chance", "chance": 0.35, "mult": 0.60}),
            ("高伤", {"proc": "counter_chance", "chance": 0.35, "mult": 0.80}),
        ]
        b._proc_pm = lambda pl: base
        b._passive_map = lambda pl: base
    logs_o2, logs_n2 = [], []
    ro2 = OLD_counter_segment(b_o2, b_o2.player, logs_o2, 9)
    rn2 = NEW_counter_segment(b_n2, b_n2.player, logs_n2, 9)
    check("多 cc 条目 mult min: OLD==NEW", ro2 == rn2, f"OLD{ro2} NEW{rn2}")


# ============================================================
# 3. 反击回气（chi 职业命中 → 气+2）与非 chi 职业
# ============================================================
def test_chi_regen():
    print("\n== 3. 反击回气（chi 职业）与非 chi 职业 ==")
    # 拳师守线磐石行者 cls_wu_seng → core resource chi（真实路径）
    p = mk_player("cls_wu_seng", ["以守为攻"])
    b_old = mk_battle(dict(p), mk_enemy())
    b_new = mk_battle(dict(p), mk_enemy())
    # 强制命中（chance→1.0 合成）+ 高伤区 使反击必触发 → 看 气
    for b in (b_old, b_new):
        pm = b._proc_pm(b.player)
        base = dict(pm)
        base.setdefault("proc", {})
        base["proc"]["counter_chance"] = [("以守为攻", {"proc": "counter_chance", "chance": 1.0, "mult": 0.80})]
        b._proc_pm = lambda pl: base
        b._passive_map = lambda pl: base
        b.player["resources"]["chi"] = 3
    logs_o, logs_n = [], []
    ro = OLD_counter_segment(b_old, b_old.player, logs_o, 1)
    rn = NEW_counter_segment(b_new, b_new.player, logs_n, 1)
    chi_o = b_old.player["resources"].get("chi", 0)
    chi_n = b_new.player["resources"].get("chi", 0)
    # 挂点13 反击段回气是静默副作用（无日志串——只有 v107 counter_attack 段有回气日志），
    # OLD/NEW 都不输出 回气+2 日志；断言状态一致 + 气 3→5
    check("chi 职业反击命中 气+2（3→5）OLD==NEW 且无回气日志（段内静默）",
          ro == rn and chi_o == chi_n == 5 and not any("回气" in s for s in logs_n),
          f"OLD chi={chi_o} logs{logs_o} | NEW chi={chi_n} logs{logs_n}")


# ============================================================
# 4. 零默认 + 多条目 max/min（handler 单测层）
# ============================================================
def test_handler_zero_default():
    print("\n== 4. 零默认值铁律 + counter_cond handler 聚合 ==")
    ctx = {"actor": {"class_name": "cls_wu_seng"}, "ps": {}, "ps_name": "以守为攻",
           "chance": 0.0, "mult": 1.0}
    out = PP.run_proc_family(None, ["counter_chance"], ctx)
    check("空 _ps counter_chance → 不聚合 chance/mult 不变",
          out == [] and ctx["chance"] == 0.0 and ctx["mult"] == 1.0, str(ctx))
    ctx2 = {"actor": {"class_name": "cls_wu_seng"},
            "ps": {"proc": "counter_up", "chance_add": 0.25, "dmg_add": 0.50},
            "ps_name": "反击之王", "chance": 0.35, "mult": 0.80}
    PP.run_proc_family(None, ["counter_up"], ctx2)
    check("counter_up 单条: chance 0.35+0.25=0.60 mult 0.80*1.5=1.20",
          abs(ctx2["chance"] - 0.60) < 1e-9 and abs(ctx2["mult"] - 1.20) < 1e-9,
          str(ctx2))
    # 两 counter_chance 条目 max/min
    ctx3 = {"actor": {"class_name": "x"}, "ps": {}, "ps_name": "", "chance": 0.0, "mult": 1.0}
    for ps in ({"proc": "counter_chance", "chance": 0.2, "mult": 0.9},
               {"proc": "counter_chance", "chance": 0.35, "mult": 0.80}):
        ctx3.update({"ps": ps, "ps_name": "cc"})
        PP.run_proc_family(None, ["counter_chance"], ctx3)
    check("多 cc 条目 chance max 0.35 mult min 0.80",
          abs(ctx3["chance"] - 0.35) < 1e-9 and abs(ctx3["mult"] - 0.80) < 1e-9, str(ctx3))


# ============================================================
# 5. 静态：声明/执行器/挂点改造痕迹 + 旧直读清零 + 计数
# ============================================================
def test_static():
    print("\n== 5. 静态：P2-D5a 2 proc 声明 + 挂点13 改造痕迹 ==")
    for proc, fam in (("counter_chance", "counter_cond"),
                      ("counter_up", "counter_cond")):
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              f"got {PP.PROC_FAMILIES.get(proc)}")
    check("族执行器 counter_cond 已注册", "counter_cond" in PP.FAMILY_HANDLERS)
    check("PROC_FAMILIES 含 33 声明", len(PP.PROC_FAMILIES) == 33, str(len(PP.PROC_FAMILIES)))
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    # 挂点13 区（_retaliations_and_buffs 方法体）走注册表聚合
    seg = battle.split("    def _retaliations_and_buffs")[1]
    seg = seg.split("    def _post_hp_lethal")[0]
    check("挂点13 调 run_proc_family counter_chance/counter_up",
          '_run_proc_family(self, "counter_chance"' in seg
          and '_run_proc_family(self, "counter_up"' in seg)
    # 旧直读残留清零（_chance = max / _mult = min / .get chance 兜底 0.35/0.80/0.25/0.50）
    old_reads = [s for s in ('_ps.get("chance", 0.35)', '_ps.get("mult", 0.80)',
                             '_ps.get("chance_add", 0.25)', '_ps.get("dmg_add", 0.50)')
                 if s in seg]
    check("挂点13 无 2 proc 旧直读残留", not old_reads, str(old_reads))
    check("挂点13 cap0.9 收口保留", "min(_chance, 0.9)" in seg)
    check("挂点13 反击回气保留", '_res_gain_class(_cr2_cls, "chi", 2)' in seg)


def main():
    clean_db()
    test_learn_matrix()
    test_cap_and_mult()
    test_chi_regen()
    test_handler_zero_default()
    test_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
