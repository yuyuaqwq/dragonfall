# -*- coding: utf-8 -*-
"""v125.1/v125.2 收口审计·注册表完整性固化测试（纯数据断言，不建号）。

把收口审计 A3 结论「数据使用键 ⊆ 注册表 handler」固化成断言：
  1. 技能 mech 词   → MECH_EFFECTS（core/battle_mech.py）
  2. 技能 cond 类型 → COND_CHECKS（core/battle_conds.py）
  3. 被动 cond      → PASSIVE_COND_CHECKS（core/battle_conds.py）
  4. 怪物增益 effect→ MON_BUFF_EFFECTS（core/battle_mech.py）
  5. 怪物控制 mech  → MON_CTRL_EFFECTS（core/battle_mech.py）
  6. Boss mech token→ BOSS_MECHS（reflect 被动白名单豁免）
  7. 词条 trigger   → affix_effects HIT/TAKEN/TURN_START/SET_PROC（handler 自查 aid 方向 + 数据方向）
  8. 药水 effect_data→ POTION_EFFECTS（含 3 个别名）
  9. 宠物 skill_type→ PET_SKILL_EFFECTS（block 由 _pet_block_check 独立消费）
 10. POI effect/副本 type → POI_EFFECTS（世界 9 + 副本 7）
 11. 采集条件词     → economy._GATHER_COND_CHECKERS
 12. battle_config 各表 → battle.py 模块级接线消费（identity 断言 + 功能抽查）
"""
import os
import re
import sys

# ---- 私有临时库（基于 __file__；铁律：绝不触碰生产 game_data.db）----
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1252_audit_closure.db")
os.environ["GWEN_GAME_DB"] = _DB
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, BT  # noqa: E402
from data.plugins.dragonfall.game.core import battle_mech as BM  # noqa: E402
from data.plugins.dragonfall.game.core import battle_conds as BC  # noqa: E402
from data.plugins.dragonfall.game.core import potion_effects as PE  # noqa: E402
from data.plugins.dragonfall.game.data import affixes as DA  # noqa: E402
from data.plugins.dragonfall.game.core import poi_effects as POIE  # noqa: E402
from data.plugins.dragonfall.game.core import affix_effects as AF  # noqa: E402
from data.plugins.dragonfall.game.commands.economy import _GATHER_COND_CHECKERS  # noqa: E402
from data.plugins.dragonfall.game.data.sets import SETS  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
# v141.3 S1 套装去模板化：名册套（class_sets）运行时注册进 SETS，审计需先 build
from data.plugins.dragonfall.game.core.class_sets import _build_class_sets  # noqa: E402
_build_class_sets()  # noqa: E402

# R3 audit 加固：battle.py 源码（反查 SET_EFFECT_CONSUMED / stat-trigger 词条消费点用；大文件只做包含检查）
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BATTLE_SRC = open(os.path.join(_PLUGIN_DIR, "game", "battle.py"), encoding="utf-8").read()

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def _eff_params(eff_name: str) -> dict:
    """v142：从套装数据查 effect 的 params（数据驱动）"""
    for _s in SETS.values():
        for _tk in ("bonus_2", "bonus_3", "bonus_4", "bonus_5"):
            _b = _s.get(_tk) or {}
            if _b.get("effect") == eff_name and _b.get("params"):
                return _b["params"]
    return {}


def _has_params(eff_name: str) -> bool:
    return bool(_eff_params(eff_name))


def all_skills():
    """聚合 PLAYER_SKILLS + TUTOR_SKILLS 全部技能定义（按 id 合并）。"""
    out = {}
    for _src in (getattr(C, "PLAYER_SKILLS", {}) or {}, getattr(C, "TUTOR_SKILLS", {}) or {}):
        for _cd in _src.values():
            for _k, _v in (_cd.get("skills") or {}).items():
                out.setdefault(_k, {}).update(_v)
    for _cd in (getattr(C, "BRANCH_SKILLS", {}) or {}).values():
        for _b in (_cd.get("branches") or {}).values():
            for _k, _v in (_b.get("skills") or {}).items():
                out.setdefault(_k, {}).update(_v)
    return out


SKILLS = all_skills()


def ref_aids(registry):
    """从 handler 源码提取其自查的词条 aid（\"xxx\" in ids / _equip_affix_ids）。"""
    out = set()
    for fn in registry.values():
        try:
            src = inspect_getsource(fn)
        except Exception:
            continue
        out |= set(re.findall(r"\"([a-z_0-9]+)\" in (?:ids|battle\._equip_affix_ids\(player\))", src))
        out |= set(re.findall(r"@\w+\((?:\w+\.)*\w+, \"([a-z_0-9]+)\"\)", src))  # v130.2c @register 装饰器模式
    return out


import inspect as _inspect  # noqa: E402
inspect_getsource = _inspect.getsource


# ================= 1. 技能 mech 词 → MECH_EFFECTS =================
def section_mech():
    print("【1. 技能 mech 词 → MECH_EFFECTS】")
    used = set()
    for sk in SKILLS.values():
        for t in str(sk.get("mech") or "").split(","):
            t = t.strip()
            if t:
                used.add(t)
    check("技能 mech 词非空（有数据被消费）", len(used) >= 5, f"used={sorted(used)}")
    missing = used - set(BM.MECH_EFFECTS)
    check("全部技能 mech 词已注册 handler", not missing, f"missing={sorted(missing)}")
    # 反向：注册表键都有数据或为爆发/被动后缀（burst 由技能数据 mech 字段引用）
    check("MECH_EFFECTS 注册表非空且 ≥25 键", len(BM.MECH_EFFECTS) >= 25, str(len(BM.MECH_EFFECTS)))


# ================= 2. 技能 cond 类型 → COND_CHECKS =================
def section_cond():
    print("【2. 技能 cond 类型 → COND_CHECKS】")
    used = set()
    for sk in SKILLS.values():
        cd = sk.get("cond")
        if isinstance(cd, dict) and cd.get("type"):
            used.add(cd["type"])
    check("技能 cond 类型非空", len(used) >= 5, f"used={sorted(used)}")
    missing = used - set(BC.COND_CHECKS)
    check("全部技能 cond 类型已注册 handler", not missing, f"missing={sorted(missing)}")


# ================= 3. 被动 cond → PASSIVE_COND_CHECKS =================
def section_passive_cond():
    print("【3. 被动 cond → PASSIVE_COND_CHECKS】")
    used = set()
    for sk in SKILLS.values():
        for p in sk.get("passives") or []:
            if isinstance(p, dict) and p.get("cond"):
                used.add(p["cond"])
    missing = used - set(BC.PASSIVE_COND_CHECKS)
    check("全部被动 cond 已注册 handler", not missing, f"missing={sorted(missing)}")
    check("PASSIVE_COND_CHECKS 6 键注册完整",
          set(BC.PASSIVE_COND_CHECKS) == {"rage>=5", "hp_low_50", "hp_high_70",
                                          "battle_start", "hp_low_30", "dual_stat"},
          f"reg={sorted(BC.PASSIVE_COND_CHECKS)} used={sorted(used)}")
    check("passive_cond_ok 未知 cond 安全降级 default",
          BC.passive_cond_ok(None, None, {"cond": "no_such_cond"}, default=True) is True)
    check("passive_cond_ok 无 cond 直接 default",
          BC.passive_cond_ok(None, None, {}, default=False) is False)


# ================= 4/5. 怪物增益 effect / 控制 mech =================
def section_monster():
    print("【4/5. 怪物增益 effect / 控制 mech】")
    mb_used, mc_used = set(), set()
    for sk in C.MONSTER_SKILLS.values():
        if sk.get("kind") == "增益":
            if sk.get("effect"):
                mb_used.add(sk["effect"])
        else:
            if sk.get("mech"):
                mc_used.add(sk["mech"])
    missing = mb_used - set(BM.MON_BUFF_EFFECTS)
    check("怪物增益 effect 全部注册（含 shield/spd_up 补注册）", not missing,
          f"missing={sorted(missing)} used={sorted(mb_used)}")
    check("shield/spd_up 增益确实被数据使用",
          {"shield", "spd_up"} <= mb_used, f"used={sorted(mb_used)}")
    missing = mc_used - set(BM.MON_CTRL_EFFECTS)
    check("怪物控制 mech 全部注册（含 interrupt）", not missing,
          f"missing={sorted(missing)} used={sorted(mc_used)}")
    check("interrupt 确实被数据使用（暗影弹）", "interrupt" in mc_used)
    check("暗影弹数据经 mech 接线（非死字段 interrupt:True）",
          C.MONSTER_SKILLS.get("ms_an_ying_dan", {}).get("mech") == "interrupt",
          str(C.MONSTER_SKILLS.get("ms_an_ying_dan", {})))


# ================= 6. Boss mech token → BOSS_MECHS =================
def section_boss_mech():
    print("【6. Boss mech token → BOSS_MECHS】")
    used = set()
    for _src in (C.INSTANCES, C.MONSTER_MODS):
        for _v in _src.values():
            for t in str(_v.get("mech") or "").split(","):
                t = t.strip()
                if t:
                    used.add(t)
    missing = used - set(BM.BOSS_MECHS) - set(BM._PASSIVE_MECH_TOKENS)
    check("Boss mech token 全部注册（reflect 被动白名单豁免）", not missing,
          f"missing={sorted(missing)} used={sorted(used)}")
    check("启动校验可重复调用且当前无重复注册", BM.validate_boss_mechs() is None)


# ================= 7. 词条 trigger → affix_effects =================
def section_affix():
    print("【7. 词条 trigger → affix_effects】")
    data = dict(getattr(C, "AFFIXES", {}) or {})
    data.update(getattr(C, "LEGENDARY_EFFECTS", {}) or {})
    # 数据方向：on_hit/on_taken/turn_start 触发型词条必须被 handler 引用（starfall 由 battle.py 直连）
    ref = ref_aids(AF.HIT_EFFECTS) | ref_aids(AF.TAKEN_EFFECTS) | ref_aids(AF.TURN_START_EFFECTS)
    ref |= set(getattr(BT.Battle, "RES_AFFIX_GAIN", ()) or ())  # v130.2c battle.py 统一读取器接线
    ref |= set(getattr(BT.Battle, "RES_AFFIX_TURN_START", ()) or ())  # v130.2d battle.py 回合开始接线（疾风余韵）
    ref |= set(getattr(BT.Battle, "RES_AFFIX_ON_TAKEN", ()) or ())  # v130.2d battle.py 受击接线（连段护持）
    # v130.2d 六词条全部接线后下架集合已删除（affixes.py 注释确认）——死参数兜底空集删掉，
    # 改为断言「集合不存在」，防止未来误复活死字段（若重挂 AFFIX_DELISTED_V130_2C 此处即红）
    check("AFFIX_DELISTED_V130_2C 集合已删除（六词条重回掉落池）",
          not hasattr(DA, "AFFIX_DELISTED_V130_2C"))
    trigger_ids = {aid for aid, d in data.items() if d.get("trigger") in ("on_hit", "on_taken", "turn_start")}
    uncovered = trigger_ids - ref - {"starfall"}
    check("触发型词条（on_hit/on_taken/turn_start）全部有 handler", not uncovered,
          f"uncovered={sorted(uncovered)}")
    # handler 方向：handler 自查的 aid 必须存在于数据
    not_in_data = ref - set(data)
    # reduce = TAKEN_EFFECTS 的 effect-key 注册（_t_reduce 按 effect dict 分发 dmg_reduce/earth_heart 等），非词条 aid
    not_in_data = not_in_data - {"reduce"}
    check("handler 引用的词条 aid 全部存在（AFFIXES/LEGENDARY_EFFECTS）", not not_in_data,
          f"not_in_data={sorted(not_in_data)}")
    # 套装 4 件攻击特效：无 stats 字段的 bonus_4.effect 必须 ∈ SET_PROC_EFFECTS 或 battle.py 直连消费
    # v141.3 S1：区域 3 槽位套（护林/渡口/巡林/霜猎/龙裔）用 bonus_3，一并纳入
    no_stats_eff = set()
    for _s in SETS.values():
        for _tk in ("bonus_4", "bonus_3"):
            _b4 = _s.get(_tk) or {}
            if _b4.get("effect") and not _b4.get("stats"):
                no_stats_eff.add(_b4["effect"])
    set_consumed = set(getattr(BT.Battle, "SET_EFFECT_CONSUMED", ()) or ())  # v130.2c 套装 effect 战斗侧直连消费
    # v142 数据驱动：有 params 的 effect 由 SET_PROC_TYPES/TAKEN_TYPES 通用执行器消费
    _dd_effs = {_eff for _eff in no_stats_eff if _has_params(_eff)}
    missing = no_stats_eff - _dd_effs - set(AF.SET_PROC_EFFECTS) - {"reflect", "regen", "regen_strong"} - set_consumed
    check("套装 4 件无 stats 特效全部有消费（数据驱动/直连）", not missing,
          f"missing={sorted(missing)} effects={sorted(no_stats_eff)}")
    check("SET_PROC_EFFECTS 键 ⊆ 套装数据 effect 键（旧注册表仅兼容）",
          set(AF.SET_PROC_EFFECTS) <= no_stats_eff | {"reflect", "regen", "regen_strong"}
          | {"execute", "lifesteal_set", "pierce", "thunder"},
          f"reg={sorted(AF.SET_PROC_EFFECTS)} data={sorted(no_stats_eff)}")
    # v142：数据驱动注册表（SET_PROC_TYPES + TAKEN_TYPES）覆盖全部有 params 的 effect type
    _all_params_types = {(_eff, _p.get("type")) for _eff in no_stats_eff if (_p := _eff_params(_eff))}
    _known_types = set(AF.SET_PROC_TYPES) | set(AF.TAKEN_TYPES)
    _unknown = {(e, t) for e, t in _all_params_types if t not in _known_types}
    check("数据驱动：全部 params.type ∈ SET_PROC_TYPES/TAKEN_TYPES", not _unknown,
          f"unknown={sorted(_unknown)}")
    # v130.2c 全档位（2/4/5 件）effect 型套装效果覆盖审计：全部 ∈ 战斗侧直连消费注册表
    # （stats 型 effect——mdef_up_set/crit_up_set/dodge_set——由 compute_stats 属性面板消费，不在此列）
    all_effs = set()
    for _s in SETS.values():
        for _tk in ("bonus_2", "bonus_3", "bonus_4", "bonus_5"):
            _b = _s.get(_tk) or {}
            if isinstance(_b, dict) and _b.get("effect") and not _b.get("stats"):
                all_effs.add(_b["effect"])
    # v142 数据驱动：有 params 的 effect 由通用执行器消费（SET_PROC_TYPES/TAKEN_TYPES）；SET_EFFECT_CONSUMED 仅覆盖直连型
    _dd_all = {_eff for _eff in all_effs if _has_params(_eff)}
    missing_effs = all_effs - _dd_all - set_consumed - set(AF.SET_PROC_EFFECTS) - {"reflect", "regen", "regen_strong"}
    check("12 套资源联动 effect 全部有战斗侧消费（数据驱动/直连）", not missing_effs,
          f"missing={sorted(missing_effs)} all={sorted(all_effs)}")
    check("SET_EFFECT_CONSUMED 键全部在套装数据中存在", set_consumed <= all_effs,
          f"ghost={sorted(set_consumed - all_effs)}")
    # R3 audit 加固：SET_EFFECT_CONSUMED 自证式漏洞——不能只信「注册表自身声明」，
    # 反查 battle.py 源码：每个 effect 名出现 ≥1 次（真实消费点）；找不到消费点 → 红
    for _eff in sorted(set_consumed):
        _cnt = _BATTLE_SRC.count(f'"{_eff}"')
        check(f"SET_EFFECT_CONSUMED『{_eff}』battle.py 源码含消费点(≥1)", _cnt >= 1, f"count={_cnt}")
    # R3 audit 加固：六词条 4 个 stat-trigger 词条零保护补丁——battle.py 源码反查消费点
    # （sigil_engrave/reaction_catalyst/combo_edge/momentum_mastery 是 trigger=stat，
    #  不在上方触发型词条集合内；swift_tailwind/combo_ward 已由 RES_AFFIX_TURN_START/ON_TAKEN 覆盖）
    for _aid in ("sigil_engrave", "reaction_catalyst", "combo_edge", "momentum_mastery"):
        _cnt = _BATTLE_SRC.count(f'"{_aid}"')
        check(f"stat-trigger 词条『{_aid}』battle.py 源码含消费点(≥1)", _cnt >= 1, f"count={_cnt}")


# ================= 8. 药水 effect_data → POTION_EFFECTS =================
def section_potion():
    print("【8. 药水 effect_data → POTION_EFFECTS】")
    item_eff = set()
    for _d in C.ITEMS.values():
        ed = _d.get("effect_data")
        if isinstance(ed, dict) and ed:
            item_eff.add(_d.get("effect"))
    # v140 口径修正：item effect_data 含 19 种功能性道具（灯笼/罗盘/改名/背包等，
    # 走 item_templates.py 模板 handler），非药水 → 药水类 = POTION_EFFECTS 覆盖的 effect
    alias = PE._EFFECT_KIND
    potion_eff = {alias.get(e, e) for e in item_eff} & set(PE.POTION_EFFECTS)
    check("药水特殊效果数据齐备（POTION_EFFECTS 覆盖 36 种）", len(potion_eff) == len(PE.POTION_EFFECTS),
          f"potion={sorted(potion_eff)}")
    missing = {alias.get(e, e) for e in item_eff} - set(PE.POTION_EFFECTS)
    # 功能道具类 effect 由 item_templates.py 处理，检查它们是否注册了模板 handler
    from data.plugins.dragonfall.game.core import item_templates as IT
    tpl_missing = [e for e in missing if e not in IT.TEMPLATES
                   and not hasattr(IT, f"tpl_{e}")]
    check("功能道具 effect 全部有模板 handler（非药水）", not tpl_missing, f"tpl_missing={sorted(tpl_missing)}")
    check("POTION_EFFECTS 注册 36 键", len(PE.POTION_EFFECTS) == 36, str(len(PE.POTION_EFFECTS)))
    check("DEFAULTS 由 items.py effect_data 扫描覆盖全部注册键",
          set(PE.POTION_EFFECTS) <= set(PE.DEFAULTS),
          f"缺默认值={sorted(set(PE.POTION_EFFECTS) - set(PE.DEFAULTS))}")
    check("狂怒药剂 effect_data 数值 {pct:0.5}",
          C.ITEMS["i_fury_potion"].get("effect_data") == {"pct": 0.5},
          str(C.ITEMS["i_fury_potion"].get("effect_data")))


# ================= 9. 宠物 skill_type → PET_SKILL_EFFECTS =================
def section_pet():
    print("【9. 宠物 skill_type → PET_SKILL_EFFECTS】")
    types = {p.get("skill_type") for p in C.PET_POOL}
    missing = types - set(BT.PET_SKILL_EFFECTS) - {"block"}
    check("宠物 skill_type 全部有 handler（block 走 _pet_block_check）", not missing,
          f"missing={sorted(missing)} types={sorted(types)}")
    check("PET_SKILL_EFFECTS 注册 7 类型", len(BT.PET_SKILL_EFFECTS) == 7,
          f"reg={sorted(BT.PET_SKILL_EFFECTS)}")
    check("heal_pct 类型确实被数据使用（月光兔等）", "heal_pct" in types)
    check("block 类型确实在数据中（影袭/铁壳龟）", "block" in types)


# ================= 10. POI effect/副本 type → POI_EFFECTS =================
def section_poi():
    print("【10. POI effect/副本 type → POI_EFFECTS】")
    world_eff = {p["effect"] for p in C.POIS.values() if isinstance(p, dict) and isinstance(p.get("effect"), str)}
    check("世界 POI 9 效果全注册", world_eff <= set(POIE.POI_EFFECTS),
          f"missing={sorted(world_eff - set(POIE.POI_EFFECTS))} used={sorted(world_eff)}")
    check("世界 POI 效果数 = 9（recover/buff/merchant/herb/loot/rune/fish/note/sight）",
          len(world_eff) == 9, f"used={sorted(world_eff)}")
    # v137 副本 POI 注册进 POIS：dict effect 的副本 POI 走 inst:<type>（POI_EFFECTS），
    # 不计入世界 effect；此处从 POIS 收集副本 POI 的 inst: 键做注册校验。
    inst_types = set()
    from data.plugins.dragonfall.game.data.instance_stage_maps import INSTANCE_STAGE_MAPS  # noqa: E402

    def walk(pois):
        for p in pois or []:
            if p.get("type"):
                inst_types.add(f"inst:{p['type']}")
            if isinstance(p.get("secret"), dict):
                walk(p["secret"].get("pois"))
    for _stages in INSTANCE_STAGE_MAPS.values():
        for _st in _stages.values():
            walk(_st.get("pois"))
    check("副本内联 POI 7 类型全注册", inst_types <= set(POIE.POI_EFFECTS),
          f"missing={sorted(inst_types - set(POIE.POI_EFFECTS))} used={sorted(inst_types)}")
    check("副本 POI 类型数 = 7（chest/campfire/rune_stone/mechanism/trap/supply/corpse）",
          len(inst_types) == 7, f"used={sorted(inst_types)}")


# ================= 11. 采集条件词 → _GATHER_COND_CHECKERS =================
def section_gather_cond():
    print("【11. 采集条件词 → _GATHER_COND_CHECKERS】")
    words = set()
    for _entries in C.GATHER_COND_POOLS.values():
        for _e in _entries:
            for t in str(_e[2]).split("+"):
                if t:
                    words.add(t)
    check("采集条件词全部注册", words <= set(_GATHER_COND_CHECKERS),
          f"missing={sorted(words - set(_GATHER_COND_CHECKERS))} words={sorted(words)}")
    check("采集条件词非空（night/rain/winter）", len(words) >= 3, f"words={sorted(words)}")


# ================= 12. battle_config 各表被 battle.py 接线消费 =================
def section_battle_config():
    print("【12. battle_config 各表被 battle.py 消费】")
    check("MECH_STACK_BONUS 接线（battle.py 同一对象）", BT.MECH_STACK_BONUS is C.MECH_STACK_BONUS)
    check("DOT_DEFS 接线", BT.DOT_DEFS is C.DOT_DEFS)
    check("BOSS_ATTACK_MULTS 接线", BT.BOSS_ATTACK_MULTS is C.BOSS_ATTACK_MULTS)
    check("CONTROL_MECHS 接线", BT.CONTROL_MECHS is C.CONTROL_MECHS)
    check("MECH_FULL_HP_CRIT 接线", BT.MECH_FULL_HP_CRIT is C.MECH_FULL_HP_CRIT)
    check("MECH_FROZEN_MULT 接线", BT.MECH_FROZEN_MULT is C.MECH_FROZEN_MULT)
    check("MECH_COMBO_STACKS 接线", BT.MECH_COMBO_STACKS is C.MECH_COMBO_STACKS)
    check("MECH_PROC_GROUPS 接线", BT.MECH_PROC_GROUPS is C.MECH_PROC_GROUPS)
    check("MECH_STAT_PASSIVES 接线", BT.MECH_STAT_PASSIVES is C.MECH_STAT_PASSIVES)
    check("ELEMENT_REACTIONS 接线（engine.py）", E.ELEMENT_REACTIONS is C.ELEMENT_REACTIONS)
    # 功能抽查：_mech_stack_bonus 查表（rage 3 层 → 1.36）
    b = BT.Battle(enemy={"name": "t", "hp": 100, "max_hp": 100, "spd": 1})
    mult = b._mech_stack_bonus("rage", {"rage": 3}, {})
    check("_mech_stack_bonus rage×3 → 1.36（MECH_STACK_BONUS 生效）",
          abs(mult - 1.36) < 1e-9, str(mult))
    # CONTROL_MECHS 消费：Boss 控制时长减半（stun 2 → 1）
    b2 = BT.Battle(enemy={"name": "b", "hp": 100, "max_hp": 100, "is_boss": True, "spd": 1})
    check("_boss_ctrl_dur Boss 眩晕减半（CONTROL_MECHS 配套）",
          b2._boss_ctrl_dur("stun", 2) == 1, str(b2._boss_ctrl_dur("stun", 2)))


def main():
    section_mech()
    section_cond()
    section_passive_cond()
    section_monster()
    section_boss_mech()
    section_affix()
    section_potion()
    section_pet()
    section_poi()
    section_gather_cond()
    section_battle_config()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
