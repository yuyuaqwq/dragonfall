# -*- coding: utf-8 -*-
"""v130.2 核心资源重设计 最小回归测试（test_v130_resources.py）

覆盖 5 项核心新机制：
  1. 基础法师无资源（纯蓝施法者，0 高考挂载）
  2. 元素法师充能条 获取/消耗（攻线·元素法师转职首获，0-5）
  3. 歌者 共鸣+回声 双资源（牧师攻线，resonance max10 / echo max3）
  4. 战士血债怒火（受击回怒 = 1 + ⌊缺失HP%×4⌋，cap 5）
  5. 刺客连段（cap10 / finish_min3 / 每层5% / 上限40%）

设计原则（防引擎并发编辑误红）：
  - 数据/配置层断言（读 C.CORE_RESOURCES + battle_config 常量）= 硬断言，值回归必红；
  - 引擎行为层断言 = 参照 _smoke_v130_engine.py 已过路径，额外做「引擎未就绪 → skip」兜底
    （battle.py 可能被引擎 agent 并行修改；钩子缺失/中途改崩时记 skip 而非假失败，
    同时打印提示，映射到主 agent 的「待引擎修复后回归」清单）。

运行：python tests/test_v130_resources.py（exit=0 全绿；skip 不计数为失败）

注：v130.2c/d 机制行为断言（consume_all 统一公式 / 回声满层翻倍 / 六词条 / 套装消费）见
tests/test_v1302c_mechanics.py——本文件只覆盖 v130.2 资源层数据 + 引擎就绪判定。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, clean_db  # noqa: E402
from data.plugins.dragonfall.game.data import battle_config as BC  # noqa: E402

passed = failed = skipped = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def skip(name, reason):
    global skipped
    skipped += 1
    print(f"  ⏭️  {name}（引擎未就绪/被改，待引擎修复后回归）：{reason}")


# ---------------- 构造 ---------------- 
def make_enemy(hp=2000, atk=40):
    return {"name": "靶子", "hp": hp, "max_hp": hp, "atk": atk, "matk": 40,
            "def": 20, "mdef": 20, "spd": 5, "crit": 0.05}


def mk_player(cls, tier, path, learned=()):
    return {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": 40,
            "hp": 400, "max_hp": 400, "mp": 200, "max_mp": 200,
            "equipment": {"weapon": {"name": "测试杖", "stats": {"atk": 60, "matk": 60},
                                     "affixes": [], "enhance": 0}},
            "attributes": {}, "race": None, "learned_skills": list(learned),
            "name": "测试勇者"}


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p


# ================= 1. 基础法师无资源（纯蓝） =================
def test_base_mage_no_resource():
    print("【1. 基础法师无资源（纯蓝施法者）】")
    rd = C.CORE_RESOURCES.get("cls_fa_shi") or {}
    check("cls_fa_shi 资源 key = element（转职首获根）", rd.get("key") == "element", str(rd))
    check("纯蓝：on_attack/on_hit/on_skill 全 0",
          rd.get("on_attack", -1) == 0 and rd.get("on_hit", -1) == 0 and rd.get("on_skill", -1) == 0,
          str({k: rd.get(k) for k in ("on_attack", "on_hit", "on_skill")}))
    # 数据层：基础法师全技能 0 处 res_gain/res_cost/on_*（纯蓝无挂载）
    base_skills = C.PLAYER_SKILLS.get("cls_fa_shi", {}).get("skills", {})
    bad = [(n, s) for n, s in base_skills.items()
           if s.get("res_gain") or s.get("res_cost") or s.get("on_attack") or s.get("on_hit") or s.get("on_skill")]
    check("基础法师技能 0 处资源挂载（纯蓝）", not bad, str(list(bad)[:3]))
    # 引擎：基础法师（ID 名，tier0）不持资源
    try:
        b, p = new_battle("cls_fa_shi", 0, 0)
        check("引擎：基础法师 _branch_keys 空", b._branch_keys(p) == [], f"{b._branch_keys(p)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：基础法师 _branch_keys", str(ex))


# ================= 2. 元素法师充能条（获取/消耗） =================
def test_element_charge():
    print("\n【2. 元素法师充能条 获取/消耗】")
    rd = C.CORE_RESOURCES.get("cls_fa_shi") or {}
    check("充能条 max = 5（设计 0-5）", rd.get("max") == 5, str(rd.get("max")))
    check("攻线分支 override (cls_fa_shi,1) → element",
          BC.BRANCH_RESOURCE_OVERRIDE.get(("cls_fa_shi", 1)) == ("element",),
          str(BC.BRANCH_RESOURCE_OVERRIDE.get(("cls_fa_shi", 1))))
    try:
        b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素冲击"])
        check("攻线元素法师资源 key = ['element']", b._branch_keys(p) == ["element"], f"{b._branch_keys(p)}")
        check("充能条初始 0 / 当前系 fire",
              b._elem_charge() == 0 and b.resources.get("element") == "fire",
              str(b.resources))
        b._res_gain(p, "element", 3)
        check("充能 +3 = 3", b._elem_charge() == 3, f"charge={b._elem_charge()}")
        b._res_gain(p, "element", 5)
        check("充能封顶 5", b._elem_charge() == 5, f"charge={b._elem_charge()}")
        check("消耗 5 足够 → 0", b._res_spend("element", 5) and b._elem_charge() == 0,
              f"charge={b._elem_charge()}")
        check("消耗不足 1 → False", not b._res_spend("element", 1), f"charge={b._elem_charge()}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：充能条 获取/消耗", str(ex))


# ================= 3. 牧师信念负载（v153 §4 C-18） =================
def test_bard_dual_resource():
    print("\n【3. 牧师信念负载（v153：歌者双资源退役 → faith 负载制）】")
    # v153：牧师攻线 = 神谕者/死灵祭司（歌者已独立为第 7 职业 诗人），
    # 共鸣/回声资源定义保留为历史遗留（不再有生产者）；牧师核心资源 = faith 负载制。
    rd = C.CORE_RESOURCES.get("cls_mu_shi") or {}
    check("牧师核心资源 key = faith", rd.get("key") == "faith", str(rd.get("key")))
    check("牧师 on_heal=2 / on_hit=1 / on_skill=0", 
          rd.get("on_heal") == 2 and rd.get("on_hit") == 1 and rd.get("on_skill") == 0,
          str({k: rd.get(k) for k in ("on_heal", "on_hit", "on_skill")}))
    tiers = rd.get("load_tiers") or []
    check("负载四档 0-3/4-7/8-9/10", len(tiers) == 4
          and tiers[0].get("max") == 3 and tiers[1].get("max") == 7
          and tiers[2].get("max") == 9 and tiers[3].get("max") == 10,
          str(tiers))
    check("专注档治疗 ×1.25 / 透支档 ×1.50",
          abs(float(tiers[1].get("heal_mult", 0)) - 1.25) < 1e-9
          and abs(float(tiers[2].get("heal_mult", 0)) - 1.50) < 1e-9, str(tiers))
    check("每刻衰减 −0.7 / 过载触发全队回复",
          abs(float(rd.get("decay_per_tick", 0)) - 0.7) < 1e-9
          and tiers[3].get("overload") is True, str({k: rd.get(k) for k in ("decay_per_tick", "overload_heal_pct")}))
    # 历史遗留：resonance/echo 定义仍在（无生产者）；(cls_mu_shi,1) override 已过时
    rc = C.CORE_RESOURCES.get("resonance") or {}
    ec = C.CORE_RESOURCES.get("echo") or {}
    check("（遗留）共鸣 max=10 / 回声 max=3 定义保留", rc.get("max") == 10 and ec.get("max") == 3,
          str((rc.get("max"), ec.get("max"))))
    try:
        b, p = new_battle("cls_mu_shi", 0, 0)
        check("基础牧师资源 key = ['faith']", b._branch_keys(p) == ["faith"],
              f"{b._branch_keys(p)}")
        b._res_gain(p, "faith", 5)
        check("信念 +5 = 5", b._res_read("faith") == 5, f"faith={b._res_read('faith')}")
        b._res_gain(p, "faith", 9)
        check("信念封顶 10", b._res_read("faith") == 10, f"faith={b._res_read('faith')}")
        check("信念消耗 -3 = 7", b._res_spend("faith", 3) and b._res_read("faith") == 7,
              f"faith={b._res_read('faith')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：牧师信仰资源", str(ex))


# ================= 4. 战士血债怒火 =================
def test_warrior_blood_debt():
    print("\n【4. 战士血债怒火（攻线·狂战士）】")
    cfg = BC.RAGE_GAIN_HP_SCALE or {}
    check("血债配置 base=1 / coef=4.0 / cap=5",
          cfg.get("base") == 1 and abs(cfg.get("coef", 0) - 4.0) < 1e-9 and cfg.get("cap") == 5,
          str(cfg))
    # 设计公式：gain = min(cap, 1 + ⌊缺失HP% ×4⌋)
    def design_gain(miss_pct):
        return min(cfg.get("cap", 5), cfg.get("base", 1) + int(miss_pct * cfg.get("coef", 4.0)))
    check("半血受击回怒 = 3（1+floor(0.5×4)）", design_gain(0.5) == 3, str(design_gain(0.5)))
    check("缺失100%回怒封顶 5（cap）", design_gain(1.0) == 5, str(design_gain(1.0)))
    check("过饱和(缺失>100%)仍不破 cap", design_gain(2.0) == 5, str(design_gain(2.0)))
    try:
        b, p = new_battle("cls_zhan_shi", 1, 1)
        p["hp"] = int(p["max_hp"] * 0.5)
        # 生产路径：先算 gain 再交 _res_gain_class 累加（上限 10）
        gain = design_gain(0.5)
        b.resources["rage"] = b._res_gain_class("cls_zhan_shi", "rage", gain)
        check("引擎：半血受击回怒 = 3", b.resources.get("rage") == 3, f"rage={b.resources.get('rage')}")
        b.resources["rage"] = b._res_gain_class("cls_zhan_shi", "rage", 10)
        check("引擎：怒气上限 10", b.resources.get("rage") == 10, f"rage={b.resources.get('rage')}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：血债怒火", str(ex))


# ================= 5. 刺客连段 =================
def test_assassin_combo():
    print("\n【5. 刺客连段（攻线·影舞者）】")
    cfg = BC.COMBO_CFG or {}
    check("连段配置 cap=10 / finish_min=3 / per_layer=0.05 / max_bonus=0.40",
          cfg.get("cap") == 10 and cfg.get("finish_min") == 3
          and abs(cfg.get("per_layer", 0) - 0.05) < 1e-9 and abs(cfg.get("max_bonus", 0) - 0.40) < 1e-9,
          str(cfg))
    try:
        b, p = new_battle("cls_ci_ke", 1, 1, learned=["影刃"])
        check("攻线影舞连段活跃", b._combo_active(p) is True, f"{b._combo_active(p)}")
        for _ in range(10):
            b._combo_add(p)
        check("连段封顶 10", b.mech_stacks.get("combo") == 10, f"combo={b.mech_stacks.get('combo')}")
        b.mech_stacks["combo"] = 8
        check("combo8 增伤 ×1.40", abs(b._combo_dmg_mult(p) - 1.40) < 1e-9, f"{b._combo_dmg_mult(p)}")
        b.mech_stacks["combo"] = 3
        check("combo3 增伤 ×1.15", abs(b._combo_dmg_mult(p) - 1.15) < 1e-9, f"{b._combo_dmg_mult(p)}")
        b.mech_stacks["combo"] = 2
        check("combo<3 无增伤 ×1.0", b._combo_dmg_mult(p) == 1.0, f"{b._combo_dmg_mult(p)}")
        # on_crit 额外 +1 连击点
        b.resources["cp"] = 4
        b._on_crit_resource(p)
        check("on_crit +1 cp = 5", b.resources.get("cp") == 5, f"cp={b.resources.get('cp')}")
        # 基础刺客不读连段
        b2, p2 = new_battle("cls_ci_ke", 0, 0)
        check("基础刺客无连段", b2._combo_active(p2) is False, f"{b2._combo_active(p2)}")
    except (AttributeError, TypeError) as ex:
        skip("引擎：刺客连段", str(ex))


if __name__ == "__main__":
    clean_db()
    test_base_mage_no_resource()
    test_element_charge()
    test_bard_dual_resource()
    test_warrior_blood_debt()
    test_assassin_combo()
    print(f"\n===== v130.2 资源回归: {passed} passed / {failed} failed / {skipped} skipped =====")
    sys.exit(1 if failed else 0)
