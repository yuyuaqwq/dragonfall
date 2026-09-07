# -*- coding: utf-8 -*-
"""v181.P2D-D3b 挂点14 _deal_damage 对敌标记/破绽/挽歌 5 段族等价探针（test_p2dd3b_dmg_marks.py）

验证 battle.py _deal_damage（挂点14，行 9635-9711 区域）的 5 个对敌标记/破绽/挽歌
乘区 proc 从内联 for 迁移到 passive_procs 注册表族 dmg_mult_cond（ctx mult_kind 分派
hunt_mark/soul_mark/shaken_bar/broken_break/dirge_debuffs）后行为零变化
（OLD vs NEW 双实现差分）。

语义快照（迁移前原 5 段循环体）：
1. hunt_mark_up（自然之眼）：目标 debuffs.hunt_mark>0 → 每层 (0.08 基础 + _ps.per_layer)%
   乘区；标签 🎯猎印x{round(1+pct*layer,2)}；首条 break（只加首条 per_layer）
2. soul_mark_cap（灵魂锁链）：目标 debuffs.soul_mark>0 → 每层 (0.06 基础 + _ps.per_layer)%
   乘区；标签 💀魂标x…；首条 break。挂点14 只消费乘区段（cap 段在挂点16 _apply_mech_effect）
3. shaken_awareness（气力之心）：目标 buffs.shaken dict 且 val≥_ps.bar_at(15) →
   ×(1+_ps.mult 0.20)；标签固定 🧠破绽x1.2；首条 break（即使不满足也 break——只判首条）
4. broken_extend（破绽·极）乘区段：目标 buffs.shaken dict 且 trigger_count>0 且
   immune_turns>0 → ×(1+_ps.broken_mult 0.50)；标签 💢破防x…；首条 break
5. dirge_debuff_dmg（挽歌·极）：读 battle._enemy_debuff_kind_count()（self.enemy 口径）
   → pct=min(_ps.per_debuff*敌负面种数, _ps.cap)；pct>0 → ×(1+pct)；标签 🎵挽歌x…；首条 break
连乘语义：_mult_pas 逐段 *=；命中任何段后 dmg = max(1, int(dmg*mult))；标签 "·".join 进 logs。

OLD = 迁移前 _deal_damage 原 5 段循环体逐字副本（87e219f）。
NEW = 现引擎 _deal_damage 5 段（→ run_proc_family dmg_mult_cond ×5）。
差分矩阵覆盖：学/不学 × 目标状态（标记 0/1/3 层、shaken dict 形态、负面种数 0/1/4/10）+
attacker 归属（None=玩家 / 宠物 actor 无被动 / 宠物 actor 带被动）+ 零默认值（缺字段）+ 双条目防御。

运行（与门禁同款 python）：
  python tests/test_p2dd3b_dmg_marks.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player  # noqa: E402
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
    """构造战斗玩家 dict（学指定被动中文名；class_name=cls_id 读 skills 被动 dict）。"""
    pl = make_player(cls=cls_id, level=60)
    pl = db.get_player(pl.get("group_id", "g1"), pl.get("qq_id", "q1")) if pl.get("qq_id") else pl
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": 100},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {}, "buffs": {}, "eff": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10, lv=None):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd,
            "buffs": {}, "debuffs": {}, "lv": lv}


def mk_battle(player, enemy=None):
    b = BT.Battle("monster", enemy or mk_enemy(), {}, player)
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    b.player.setdefault("buffs", {})
    b.player.setdefault("eff", {})
    b.enemy.setdefault("element_marks", {})
    b.enemy.setdefault("buffs", {})
    b.enemy.setdefault("debuffs", {})
    # 等级压制守卫：探针只测 5 段乘区 → 不给 enemy lv（_deal_damage 压制段自然跳过）
    return b


def set_target_state(b, hunt=0, soul=0, shaken=None, debuff_kinds=0, debuff_dict=None):
    """设置 target（b.enemy 或探针传 target 同 dict 引用）debuffs/buffs + self.enemy 负面种数。"""
    eb = b.enemy
    eb.setdefault("debuffs", {})
    eb.setdefault("buffs", {})
    if hunt > 0:
        eb["debuffs"]["hunt_mark"] = hunt
    elif "hunt_mark" in eb["debuffs"]:
        del eb["debuffs"]["hunt_mark"]
    if soul > 0:
        eb["debuffs"]["soul_mark"] = soul
    elif "soul_mark" in eb["debuffs"]:
        del eb["debuffs"]["soul_mark"]
    if shaken is not None:
        if shaken == {}:
            eb["buffs"]["shaken"] = {}
        elif shaken is False:
            eb["buffs"].pop("shaken", None)
        else:
            eb["buffs"]["shaken"] = dict(shaken)
    # 负面种数（_enemy_debuff_kind_count 读 self.enemy.debuffs 的 dict 型条目 n>0）
    eb["debuffs"] = {k: v for k, v in eb["debuffs"].items() if v not in ("", None, False)}
    if debuff_dict is not None:
        # 显式覆盖（放 N 个 n>0 的 debuff 条目）
        eb["debuffs"] = dict(debuff_dict)
    # self.enemy 口径 = b.enemy（single）；dirge 种数按显式条目或 hunt/soul 等折算由调用方断言


# ------------------------------------------------------------
# OLD：迁移前 _deal_damage 5 段循环体逐字副本（87e219f 原样）
# ------------------------------------------------------------
def OLD_5(b, dmg, logs, target=None, attacker=None):
    """OLD 挂点14 5 段（乘区部分）——读 _pm_d proc 聚合。返回 (dmg, tags)。"""
    if target is None:
        target = getattr(b, "_active_target", None) or b.enemy
    if dmg <= 0:
        return dmg, []
    _atk_actor = attacker if attacker is not None else (b.player or {})
    _mult_pas = 1.0
    _tags_pas = []
    _pl_d = _atk_actor
    _pm_d = b._proc_pm(_pl_d) if _pl_d else {"proc": {}}
    _db_t = target.get("debuffs") or {}
    _hm = int(_db_t.get("hunt_mark", 0) or 0)
    if _hm > 0:
        _hm_pct = 0.08
        for _pn, _ps in _pm_d["proc"].get("hunt_mark_up", []):
            _hm_pct += float(_ps.get("per_layer", 0.06) or 0.06)
            break
        _mult_pas *= 1.0 + _hm_pct * _hm
        _tags_pas.append(f"🎯猎印x{round(1 + _hm_pct * _hm, 2)}")
    _sm = int(_db_t.get("soul_mark", 0) or 0)
    if _sm > 0:
        _sm_pct = 0.06
        for _pn, _ps in _pm_d["proc"].get("soul_mark_cap", []):
            _sm_pct += float(_ps.get("per_layer", 0.08) or 0.08)
            break
        _mult_pas *= 1.0 + _sm_pct * _sm
        _tags_pas.append(f"💀魂标x{round(1 + _sm_pct * _sm, 2)}")
    _sb_sh = (target.get("buffs") or {}).get("shaken")
    if isinstance(_sb_sh, dict):
        for _pn, _ps in _pm_d["proc"].get("shaken_awareness", []):
            if int(_sb_sh.get("val", 0) or 0) >= int(_ps.get("bar_at", 15) or 15):
                _mult_pas *= 1.0 + float(_ps.get("mult", 0.20) or 0.20)
                _tags_pas.append("🧠破绽x1.2")
            break
    if isinstance(_sb_sh, dict) and int(_sb_sh.get("trigger_count", 0) or 0) > 0 \
            and int(_sb_sh.get("immune_turns", 0) or 0) > 0:
        for _pn_be2, _ps_be2 in _pm_d["proc"].get("broken_extend", []):
            _mult_pas *= 1.0 + float(_ps_be2.get("broken_mult", 0.50) or 0.50)
            _tags_pas.append(f"💢破防x{round(1 + float(_ps_be2.get('broken_mult', 0.50) or 0.50), 2)}")
            break
    for _pn, _ps in _pm_d["proc"].get("dirge_debuff_dmg", []):
        _kinds = b._enemy_debuff_kind_count()
        _pct_e = min(float(_ps.get("per_debuff", 0.04) or 0.04) * _kinds,
                     float(_ps.get("cap", 0.40) or 0.40))
        if _pct_e > 0:
            _mult_pas *= 1.0 + _pct_e
            _tags_pas.append(f"🎵挽歌x{round(1 + _pct_e, 2)}")
        break
    if _mult_pas != 1.0:
        dmg = max(1, int(dmg * _mult_pas))
        if _tags_pas:
            logs.append("·".join(_tags_pas))
    return dmg, _tags_pas


# ------------------------------------------------------------
# 通用差分跑批
# ------------------------------------------------------------
def _proc_entries(cls_id, names):
    """从 skills.py 拉取被动条目（确定性注入——battle._passive_map 需按 skills 数据
    判定，依赖 class 分支表 + db learned 不可靠）。返回 {proc: [(中文名, passive dict)]}。
    ⚠️ 跨职业注入：被动归属类 ≠ 玩家 class（如玩家 cls_mu_shi 也可被注入 cls_you_xia 的
    自然之眼做差分）——skill_info 必须按技能"归属职业"查，本函数对每技能用归属类解析。"""
    from data.plugins.dragonfall.game import engine as EG
    from data.plugins.dragonfall.game import content as CC
    # 归属类表（skills.py BRANCH_SKILLS 各分支 tier2 技能；主职业名=玩家 class 参数）
    OWNER = {
        "自然之眼": "cls_you_xia", "灵魂锁链": "cls_mu_shi", "气力之心": "cls_wu_seng",
        "破绽·极": "cls_wu_seng", "挽歌·极": "cls_shi_ren",
        "奥术共鸣": "cls_fa_shi", "元素起源": "cls_fa_shi", "元素同调": "cls_fa_shi",
    }
    out = {}
    for nm in names:
        owner_cls = OWNER.get(nm, cls_id)
        info = EG.skill_info(owner_cls, nm)
        ps = (info or {}).get("passive") or {}
        if ps.get("proc"):
            out.setdefault(ps["proc"], []).append((nm, ps))
    return out


def inject_proc(b, entries):
    """确定性注入：给 battle 装 _passive_map → {"proc": entries, "stat": []}。"""
    pm = {"proc": entries, "stat": []}
    b._passive_map = lambda pl, _pm=pm: _pm
    return pm


def diff_case(name, player_dict, state_setup, dmg=100, attacker=None, proc_entries=None):
    """构造 b_old/b_new 各一，跑 OLD_5 / NEW _deal_damage，返回 (out_old, out_new)。
    proc_entries：None=不注入（battle 自建 pm——探针读原数据路径）；dict=确定性注入
    {proc: [(中文名, passive)]}——学/不学由 entries 有无控制。"""
    p1 = dict(player_dict)
    p2 = dict(player_dict)
    b_old = mk_battle(p1)
    b_new = mk_battle(p2)
    if proc_entries is not None:
        inject_proc(b_old, proc_entries)
        inject_proc(b_new, proc_entries)
    state_setup(b_old)
    state_setup(b_new)
    logs_old, logs_new = [], []
    # OLD：逐字副本
    d_old, tags_old = OLD_5(b_old, dmg, logs_old, attacker=attacker)
    # NEW：现引擎 _deal_damage 完整（5 段注册表 + 等级压制/defending 等后续段——enemy 无 lv 不压制）
    d_new = b_new._deal_damage(dmg, logs_new, attacker=attacker)
    tags_new = logs_new[0].split("·") if logs_new else []
    return (d_old, tags_old, logs_old), (d_new, tags_new, logs_new)


def check_pair(name, old, new, expect_mult=None):
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    ok = (d_old == d_new) and (t_old == t_new) and (l_old == l_new)
    if expect_mult is not None:
        ok = ok and d_new == expect_mult
    check(name, ok, f"OLD dmg {d_old} tags {t_old} logs {l_old} | NEW dmg {d_new} tags {t_new} logs {l_new}")


# ============================================================
# 1. hunt_mark_up（自然之眼，森语者/游侠）——猎印 per_layer
# ============================================================
def test_hunt_mark_up():
    print("\n== 1. hunt_mark_up 猎印（per_layer 0.06 + 基础 0.08）OLD vs NEW ==")
    CLS = "cls_you_xia"
    NZY = "自然之眼"
    for learned in (False, True):
        p = mk_player(CLS, [])
        pe = _proc_entries(CLS, [NZY]) if learned else {}
        for hm in (0, 1, 3):
            def setup(b, _hm=hm):
                set_target_state(b, hunt=_hm)
            old, new = diff_case(f"学={learned} 猎印{hm}", p, setup, proc_entries=pe)
            exp = None
            if learned and hm > 0:
                exp = max(1, int(100 * (1 + (0.08 + 0.06) * hm)))
            check_pair(f"学={learned} 猎印{hm}层: OLD==NEW", old, new, exp)
    # 缺字段（_ps 无 per_layer）→ 零默认值铁律：无额外加成，只乘基础 0.08/层（NEW 语义；
    # OLD 遗留兜底 0.06 属数据重复，D0 已回填——生产数据必带 per_layer，迁移后缺字段=无此行为）
    p = mk_player("cls_you_xia", ["自然之眼"])
    def setup_missing(b):
        set_target_state(b, hunt=2)
        pm = b._passive_map(b.player)
        pm["proc"]["hunt_mark_up"] = [("自然之眼", {"proc": "hunt_mark_up"})]
        b._passive_map = lambda pl, _pm=pm: _pm
    old, new = diff_case("缺 per_layer 字段", p, setup_missing)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    exp_new = max(1, int(100 * (1 + 0.08 * 2)))
    check("缺 per_layer → NEW 只乘基础 0.08（零默认值）",
          d_new == exp_new and t_new == ["🎯猎印x1.16"], f"NEW dmg {d_new} tags {t_new}")


# ============================================================
# 2. soul_mark_cap（灵魂锁链，死灵祭司/牧师）——魂标 per_layer
# ============================================================
def test_soul_mark_cap():
    print("\n== 2. soul_mark_cap 魂标（per_layer 0.08 + 基础 0.06）OLD vs NEW ==")
    CLS = "cls_mu_shi"
    SLC = "灵魂锁链"
    for learned in (False, True):
        p = mk_player(CLS, [])
        pe = _proc_entries(CLS, [SLC]) if learned else {}
        for sm in (0, 1, 3):
            def setup(b, _sm=sm):
                set_target_state(b, soul=_sm)
            old, new = diff_case(f"学={learned} 魂标{sm}", p, setup, proc_entries=pe)
            exp = None
            if learned and sm > 0:
                exp = max(1, int(100 * (1 + (0.06 + 0.08) * sm)))
            check_pair(f"学={learned} 魂标{sm}层: OLD==NEW", old, new, exp)


# ============================================================
# 3. shaken_awareness（气力之心，格斗士/拳师）——破绽条乘区
# ============================================================
def test_shaken_awareness():
    print("\n== 3. shaken_awareness 破绽条（bar_at 15 / mult 0.20）OLD vs NEW ==")
    shaken_cases = [
        ("无shaken", False),
        ("空dict", {}),
        ("val14", {"val": 14, "threshold": 15}),
        ("val15", {"val": 15, "threshold": 15}),
        ("val30", {"val": 30, "threshold": 15}),
        ("无val键", {"threshold": 15}),
    ]
    for learned in (False, True):
        p = mk_player("cls_wu_seng", [])
        pe = _proc_entries("cls_wu_seng", ["气力之心"]) if learned else {}
        for tag, sh in shaken_cases:
            def setup(b, _sh=sh):
                set_target_state(b, shaken=_sh)
            old, new = diff_case(f"学={learned} {tag}", p, setup, proc_entries=pe)
            exp = None
            if learned and isinstance(sh, dict) and int(sh.get("val", 0) or 0) >= 15:
                exp = max(1, int(100 * 1.2))
            check_pair(f"学={learned} {tag}: OLD==NEW", old, new, exp)
    # 缺字段（_ps 无 bar_at/mult）→ 零默认值：不触发（NEW；OLD 遗留兜底 15/0.20 属数据重复）
    p = mk_player("cls_wu_seng", ["气力之心"])
    def setup_missing(b):
        set_target_state(b, shaken={"val": 20, "threshold": 15})
        pm = b._passive_map(b.player)
        pm["proc"]["shaken_awareness"] = [("气力之心", {"proc": "shaken_awareness"})]
        b._passive_map = lambda pl, _pm=pm: _pm
    old, new = diff_case("缺 bar_at/mult 字段", p, setup_missing)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    check("缺字段 → NEW 不触发（零默认值）",
          d_new == 100 and t_new == [], f"NEW dmg {d_new} tags {t_new}")


# ============================================================
# 4. broken_extend（破绽·极，格斗士/拳师）——破防免疫期乘区段
# ============================================================
def test_broken_extend():
    print("\n== 4. broken_extend 破防乘区（broken_mult 0.50）OLD vs NEW ==")
    be_cases = [
        ("无shaken", False),
        ("破防前(trig0)", {"val": 0, "trigger_count": 0, "immune_turns": 0, "threshold": 15}),
        ("免疫期(trig1+imm1)", {"val": 0, "trigger_count": 1, "immune_turns": 1, "threshold": 15}),
        ("免疫期(trig1+imm2)", {"val": 0, "trigger_count": 1, "immune_turns": 2, "threshold": 15}),
        ("免疫期但trigger0", {"val": 0, "trigger_count": 0, "immune_turns": 1, "threshold": 15}),
        ("免疫期但imm0", {"val": 0, "trigger_count": 1, "immune_turns": 0, "threshold": 15}),
    ]
    for learned in (False, True):
        p = mk_player("cls_wu_seng", [])
        pe = _proc_entries("cls_wu_seng", ["破绽·极"]) if learned else {}
        for tag, sh in be_cases:
            def setup(b, _sh=sh):
                set_target_state(b, shaken=_sh)
            old, new = diff_case(f"学={learned} {tag}", p, setup, proc_entries=pe)
            exp = None
            if learned and isinstance(sh, dict) and int(sh.get("trigger_count", 0) or 0) > 0 \
                    and int(sh.get("immune_turns", 0) or 0) > 0:
                exp = max(1, int(100 * 1.5))
            check_pair(f"学={learned} {tag}: OLD==NEW", old, new, exp)


# ============================================================
# 5. dirge_debuff_dmg（挽歌·极，挽歌者/诗人）——敌方负面种数乘区
# ============================================================
def test_dirge_debuff_dmg():
    print("\n== 5. dirge_debuff_dmg 挽歌（per_debuff 0.04 cap 0.40）OLD vs NEW ==")
    debuff_sets = [
        ("无负面", {}),
        ("1种", {"poison": {"n": 1, "turns": 2}}),
        ("4种", {"poison": {"n": 1}, "burn": {"n": 1}, "bleed": {"n": 1}, "hunt_mark": 1}),
        ("10种(过cap)", {"poison": {"n": 1}, "burn": {"n": 1}, "bleed": {"n": 1}, "corros": {"n": 1},
                         "curse": {"n": 1}, "soul_mark": 1, "hunt_mark": 1,
                         "stun_buff": None}),
    ]
    for learned in (False, True):
        p = mk_player("cls_shi_ren", [])
        pe = _proc_entries("cls_shi_ren", ["挽歌·极"]) if learned else {}
        for tag, dbd in debuff_sets:
            # 用 buffs 控制键补足种数（_enemy_debuff_kind_count 含 buffs 段 8 键）
            def setup(b, _dbd=dbd):
                # 先清干净再铺
                b.enemy["debuffs"] = {}
                b.enemy["buffs"] = {}
                for k, v in _dbd.items():
                    if k == "stun_buff":
                        b.enemy["buffs"]["stun"] = 1
                    else:
                        b.enemy["debuffs"][k] = v
            old, new = diff_case(f"学={learned} {tag}", p, setup, proc_entries=pe)
            def count_kinds(_dbd):
                return sum(1 for _ in _dbd)
            # 期望（纯 dirge 场景无标记 → 可直接算；4种/10种 含 hunt/soul 标记 → 基础乘区
            # 叠加 + 目录 entries 即种数，用 OLD 结果本身当期望（等价断言已覆盖一致性））
            exp = None
            if learned:
                has_mark = any(k in ("hunt_mark", "soul_mark") for k in dbd)
                if not has_mark:
                    n = count_kinds(dbd)
                    pct = min(0.04 * n, 0.40)
                    exp = max(1, int(100 * (1 + pct)))
            check_pair(f"学={learned} {tag}: OLD==NEW", old, new, exp)
    # 缺字段（_ps 无 per_debuff/cap）→ 零默认值：不触发（NEW；OLD 遗留兜底 0.04/0.40 属数据重复）
    p = mk_player("cls_shi_ren", ["挽歌·极"])
    def setup_missing(b):
        b.enemy["debuffs"] = {"poison": {"n": 1}, "burn": {"n": 1}}
        pm = b._passive_map(b.player)
        pm["proc"]["dirge_debuff_dmg"] = [("挽歌·极", {"proc": "dirge_debuff_dmg"})]
        b._passive_map = lambda pl, _pm=pm: _pm
    old, new = diff_case("缺 per_debuff/cap 字段", p, setup_missing)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    check("缺字段 → NEW 不触发（零默认值）",
          d_new == 100 and t_new == [], f"NEW dmg {d_new} tags {t_new}")


# ============================================================
# 6. 连乘 + attacker 归属 + 双条目防御
# ============================================================
def test_combined():
    print("\n== 6. 连乘（5 段同开）/ attacker 归属 / 双条目 ==")
    # 6a. 5 段同开（玩家带 5 被动 + 注入确定性条目）
    p = mk_player("cls_mu_shi", [])
    pe_all = _proc_entries("cls_mu_shi", ["自然之眼", "灵魂锁链", "气力之心", "破绽·极", "挽歌·极"])
    # 5 段同开 连乘（期望：猎印×魂标×破绽×破防×挽歌 + 标记基础——纯手动算）
    def setup_all(b):
        b.enemy["debuffs"] = {"hunt_mark": 2, "soul_mark": 2,
                              "poison": {"n": 1}, "burn": {"n": 1}, "bleed": {"n": 1}}
        b.enemy["buffs"]["shaken"] = {"val": 20, "trigger_count": 1, "immune_turns": 1, "threshold": 15}
    old, new = diff_case("5 段同开连乘", p, setup_all, proc_entries=pe_all)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    # dirge kinds：debuffs 全 5 条在生效（hunt_mark2/soul_mark2/poison1/burn1/bleed1）→ _kinds=5
    m = (1 + (0.08 + 0.06) * 2) * (1 + (0.06 + 0.08) * 2) * 1.2 * 1.5 * (1 + min(0.04 * 5, 0.40))
    exp = max(1, int(100 * m))
    check("5 段同开 OLD==NEW",
          d_old == d_new == exp and t_old == t_new,
          f"OLD {d_old} {t_old} | NEW {d_new} {t_new} exp {exp}")
    # 6b. attacker=宠物 actor（无被动）：不吃玩家被动 → 只吃目标标记基础
    p2 = mk_player("cls_mu_shi", [])
    pe_pet = _proc_entries("cls_mu_shi", ["自然之眼", "灵魂锁链", "挽歌·极"])
    pet_no = {"class_name": "", "level": 30, "learned_skills": [], "name": "狼崽",
              "buffs": {}, "resources": {}, "stacks": {}, "equipment": {}}
    def setup_pet(b):
        b.enemy["debuffs"] = {"hunt_mark": 3, "soul_mark": 1, "poison": {"n": 1}}
    # attacker=宠物（无 class/learned → _passive_map 走 lambda 注入只对 battle.player 生效？——
    # OLD/NEW 读 _proc_pm(_atk_actor)：monkeypatch 只影响 self._passive_map 全部 player……
    # 这里 attacker 无被动条目 → 无额外；用 OLD 结果（真实数据路径）+ 注玩家条目不适用。
    # 直接断言：OLD==NEW（双方同路径），期望 = 只标记基础
    old, new = diff_case("attacker=宠物(无被动)", p2, setup_pet, attacker=dict(pet_no),
                         proc_entries=None)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    exp_pet = max(1, int(100 * (1 + 0.08 * 3) * (1 + 0.06 * 1)))
    check("宠物无被动 → OLD==NEW 只吃基础标记",
          d_old == d_new == exp_pet and t_old == t_new,
          f"OLD {d_old} {t_old} | NEW {d_new} {t_new} exp {exp_pet}")
    # 6c. attacker=宠物 actor（带自然之眼被动本身）→ 吃自身被动（仿 v180C 对照）——
    #     宠物 actor 的 _passive_map 由自身 class/learned 解析；给它确定性注入（直接 patch 宠物）
    pet_has = dict(pet_no)
    pet_has["class_name"] = "cls_you_xia"
    pet_has["learned_skills"] = ["自然之眼"]
    pet_pe = _proc_entries("cls_you_xia", ["自然之眼"])

    def inject_proc_for(b, actor, entries):
        pm = {"proc": entries, "stat": []}
        _orig = b._passive_map
        b._passive_map = lambda pl, _pm=pm: _pm if pl is actor else _orig(pl)

    def setup_pet2(b):
        b.enemy["debuffs"] = {"hunt_mark": 3}
        # 宠物 actor 确定性注入（OLD/NEW 同 pm——解析靠 actor 自身 class）
        inject_proc_for(b, pet_has, pet_pe)
    old, new = diff_case("attacker=宠物(带自然之眼)", p2, setup_pet2, attacker=dict(pet_has),
                         proc_entries=None)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    exp_pet2 = max(1, int(100 * (1 + (0.08 + 0.06) * 3)))
    check("宠物带自然之眼 → OLD==NEW 吃自身被动",
          d_old == d_new == exp_pet2 and t_old == t_new,
          f"OLD {d_old} {t_old} | NEW {d_new} {t_new} exp {exp_pet2}")
    # 6d. 双条目防御（首条 break 语义）：hunt_mark_up 只加首条 per_layer；shaken 只判首条
    p3 = mk_player("cls_mu_shi", [])
    pe_dual = {
        "hunt_mark_up": [("自然之眼", {"proc": "hunt_mark_up", "per_layer": 0.06}),
                         ("测试第二条", {"proc": "hunt_mark_up", "per_layer": 0.50})],
        "shaken_awareness": [("气力之心", {"proc": "shaken_awareness", "bar_at": 15, "mult": 0.20}),
                             ("测试第二条", {"proc": "shaken_awareness", "bar_at": 99, "mult": 0.99})],
    }
    def setup_dual(b):
        set_target_state(b, hunt=2, shaken={"val": 30, "threshold": 15})
    old, new = diff_case("双条目（hunt 只加首条/shaken 只判首条）", p3, setup_dual,
                         proc_entries=pe_dual)
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    exp_dual = max(1, int(100 * (1 + (0.08 + 0.06) * 2) * 1.2))
    check("双条目 → OLD==NEW（只首条）",
          d_old == d_new == exp_dual and t_old == t_new,
          f"OLD {d_old} {t_old} | NEW {d_new} {t_new} exp {exp_dual}")
    # 6e. 无 proc 注册（玩家没学任何 5 proc）→ 只乘标记基础
    p4 = mk_player("cls_zhan_shi", [])
    def setup_none(b):
        set_target_state(b, hunt=5, soul=5, shaken={"val": 30, "trigger_count": 1, "immune_turns": 1})
    old, new = diff_case("未学 5 proc", p4, setup_none, proc_entries={})
    d_old, t_old, l_old = old
    d_new, t_new, l_new = new
    # 浮点连乘截断：100×(1+0.4)×(1+0.3) = 181.9999… → int 截断 181（OLD/NEW 同路径）
    check("未学 → OLD==NEW 只乘标记基础（0.08/0.06 谁打都吃）",
          d_old == d_new == 181 and t_old == t_new,
          f"OLD {d_old} {t_old} | NEW {d_new} {t_new}")


# ============================================================
# 7. 注册表静态断言
# ============================================================
def test_registry_static():
    print("\n== 7. 注册表静态（5 proc → dmg_mult_cond）+ 零默认值 ==")
    expect_map = {
        "hunt_mark_up": "dmg_mult_cond",
        "soul_mark_cap": "dmg_mult_cond",
        "shaken_awareness": "dmg_mult_cond",
        "broken_extend": "dmg_mult_cond",
        "dirge_debuff_dmg": "dmg_mult_cond",
    }
    for proc, fam in expect_map.items():
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              str(PP.PROC_FAMILIES.get(proc)))
    # P2-D4a：挂点10/11 6 proc 并入（+cc_break_cost +dr_cond 两新族）+ P2-D5b 3 proc
    # （poison_all_up→dot_mult_cond、poison_weaken→dot_weaken 新族、hunt_mark_cap→
    # dmg_mult_cond；soul_mark_cap cap 段同族）→ 声明 34 / 族 12
    check("PROC_FAMILIES 含 34 声明", len(PP.PROC_FAMILIES) == 34, str(sorted(PP.PROC_FAMILIES)))
    check("FAMILY_HANDLERS 共 12 族", len(PP.FAMILY_HANDLERS) == 12, str(list(PP.FAMILY_HANDLERS)))
    # 零默认值：_ps 空 dict → 5 段全部不触发（mult 不变）
    for mk, pname in (("hunt_mark", "hunt_mark_up"), ("soul_mark", "soul_mark_cap"),
                      ("shaken_bar", "shaken_awareness"), ("broken_break", "broken_extend"),
                      ("dirge_debuffs", "dirge_debuff_dmg")):
        ctx = {"player": {}, "ps": {}, "ps_name": "x", "mult_kind": mk, "mult": 1.0,
               "tags": [], "target": {"debuffs": {"hunt_mark": 3, "soul_mark": 3},
                                      "buffs": {"shaken": {"val": 30, "trigger_count": 1,
                                                           "immune_turns": 1, "threshold": 15}}},
               "db_t": {"hunt_mark": 3, "soul_mark": 3, "poison": {"n": 1}, "burn": {"n": 1},
                        "bleed": {"n": 1}}}
        out = PP.run_proc_family(None, [pname], ctx)
        check(f"空 _ps {mk} → 不触发 mult 不变", out == [] and ctx["mult"] == 1.0, str(out))


def main():
    clean_db()
    test_hunt_mark_up()
    test_soul_mark_cap()
    test_shaken_awareness()
    test_broken_extend()
    test_dirge_debuff_dmg()
    test_combined()
    test_registry_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
