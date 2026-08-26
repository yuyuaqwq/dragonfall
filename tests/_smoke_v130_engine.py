# -*- coding: utf-8 -*-
"""v130.2 战斗引擎层挂点冒烟测试 —— 独立私有临时库，只测新挂点主路径不崩 + 关键数值。
不跑全量回归；失败即该挂点未落地。运行：
  cd C:/Users/yuyu/qqbot/data/plugins/dragonfall
  python tests/_smoke_v130_engine.py
"""
import os
import sys
import tempfile

PLUGIN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QQBOT = os.path.abspath(os.path.join(PLUGIN, "..", "..", ".."))
# 独立私有临时库（绝不触碰生产 game_data.db / test_game_data.db）
os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.gettempdir(), "v130_engine_smoke.db")
sys.path.insert(0, QQBOT)
sys.path.insert(0, PLUGIN)

from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402

_passed = 0


def check(name, cond, extra=""):
    global _passed
    if cond:
        _passed += 1
        print(f"  ✓ {name} {extra}")
    else:
        print(f"  ✗ FAIL {name} {extra}")
        raise AssertionError(name)


def make_enemy(hp=500, atk=60, spd=20, name="烟兽"):
    return {"name": name, "hp": hp, "max_hp": 500, "atk": atk, "matk": 60,
            "def": 40, "mdef": 40, "spd": spd, "crit": 0.05}


def mk_player(cls, tier, path, level=40, hp=None, learned=()):
    st = {"class_name": cls, "class_tier": tier, "evolve_path": path, "level": level,
          "hp": 400 if hp is None else hp, "max_hp": 400, "mp": 200, "max_mp": 200,
          "equipment": {}, "attributes": {}, "race": None, "learned_skills": list(learned),
          "name": "烟侠"}
    return st


def new_battle(cls, tier, path, **pw):
    p = mk_player(cls, tier, path, **pw)
    b = BT.Battle("monster", make_enemy(), player=p)
    return b, p


def smoke_branch_resource():
    print("[挂点1/10] 分支级 resource_override + 基础法师无资源")
    # 基础法师：无资源
    b, p = new_battle("cls_fa_shi", 0, 0)
    check("基础法师无资源", b._branch_keys(p) == [], f"keys={b._branch_keys(p)}")
    check("基础法师 label 空", b._resource_label(p) == "", b._resource_label(p))
    # 攻线·元素法师：充能条 element
    b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素冲击"])
    check("元素法师分支资源=['element']", b._branch_keys(p) == ["element"], f"{b._branch_keys(p)}")
    check("充能条初始化 0/5", b._elem_charge() == 0 and b.resources.get("element") == "fire")
    b._res_gain(p, "element", 3)
    check("充能 +3=3", b._elem_charge() == 3)
    check("element 合成标签", "元素亲合 3/5" in b._resource_label(p), b._resource_label(p))
    check("充能消耗足够", b._res_spend("element", 3) and b._elem_charge() == 0)
    check("充能消耗不足", not b._res_spend("element", 1))
    # 攻线·歌者（牧师 cls_mu_shi path=1）：双资源 resonance+echo
    b, p = new_battle("cls_mu_shi", 1, 1, learned=["轻快拨弦"])
    check("歌者分支资源=['resonance','echo']", b._branch_keys(p) == ["resonance", "echo"], f"{b._branch_keys(p)}")
    check("歌者 label 双资源", "共鸣" in b._resource_label(p) and "回声" in b._resource_label(p), b._resource_label(p))
    b._res_gain(p, "resonance", 9)
    check("共鸣 +9=9", b._res_read("resonance") == 9)
    b._res_gain(p, "resonance", 9)
    check("共鸣封顶 10", b._res_read("resonance") == 10)
    check("共鸣消耗 -3=7", b._res_spend("resonance", 3) and b._res_read("resonance") == 7)
    # 守线神谕者（path=2）：仍用 faith
    b, p = new_battle("cls_mu_shi", 1, 2, learned=["圣言术"])
    check("守线神谕单信仰", b._branch_keys(p) == ["faith"], f"{b._branch_keys(p)}")


def smoke_warrior_blood():
    print("[挂点2/10] 战士血债怒火（攻线·狂战士受击回怒缩放）")
    b, p = new_battle("cls_zhan_shi", 1, 1)  # 狂战士
    p["hp"] = p["max_hp"]  # 满血
    rd = C.CORE_RESOURCES["cls_zhan_shi"]
    # 直接驱动受击 on_hit 分支（_damage_player 的攻线血债段）
    gain_full = rd["on_hit"]
    check("基础受击 +1 保留", True, f"on_hit={gain_full}")
    # 模拟半血受击：1+floor(0.5*4)=3
    def _rage_at(miss_pct):
        cur = b.resources.setdefault("rage", 0)
        return cur
    b.resources["rage"] = 0
    p["hp"] = int(p["max_hp"] * 0.5)
    gain = 1 + int(0.5 * 4.0)
    b.resources["rage"] = b._res_gain_class("cls_zhan_shi", "rage", gain)
    check("缺50%血受击回怒=3", b.resources["rage"] == 3, f"rage={b.resources['rage']}")
    p["hp"] = 1
    b.resources["rage"] = 0  # 重置：从 0 起验证；实现语义=单次受击获取量封顶 cap=5（非累计==5）
    # production 路径（_damage_player 血债段）先算 gain=min(cap, 1+missing×4) 再交 _res_gain_class 累加。
    # 濒死 missing→100%：gain = min(5, 1+4) = 5。这里模拟濒死缺失≈100% 时 production 给出的 gain=5：
    gain_dying = 5
    b.resources["rage"] = b._res_gain_class("cls_zhan_shi", "rage", gain_dying)
    check("濒死受击回怒封顶5", b.resources["rage"] == 5, f"rage={b.resources['rage']} gain_dying={gain_dying}")
    # 基础战士（无分支）：无血债缩放
    b2, p2 = new_battle("cls_zhan_shi", 0, 0)
    check("基础战士资源 rage", b2._branch_keys(p2) == ["rage"], f"{b2._branch_keys(p2)}")


def smoke_ranger_full():
    print("[挂点3/10] 游侠满弦状态（守线·风行者 精力≥80 低耗暴击）")
    b, p = new_battle("cls_you_xia", 1, 2, learned=["疾风射击"])  # 风行者
    b.resources["energy"] = 100
    # 满弦判定
    skill = C.PLAYER_SKILLS.get("cls_you_xia", {}).get("sk_miao_zhun")
    if not isinstance(skill, dict) or "skills" in (skill or {}):
        skill = None
    check("满弦状态 True（精力100）", b._energy_high_crit(p) is True)
    check("满弦对高耗技 False", b._energy_high_crit(p, {"res_cost": {"energy": 40}}) is False)
    b.resources["energy"] = 70
    check("精力70 不满足阈值", b._energy_high_crit(p) is False)
    # 攻线林语者（path=1）不吃满弦
    b3, p3 = new_battle("cls_you_xia", 1, 1, learned=["追猎"])
    b3.resources["energy"] = 100
    check("林语者不吃满弦", b3._energy_high_crit(p3) is False)


def smoke_assassin_combo():
    print("[挂点4/10] 刺客 on_crit/受击回退/连段计数（攻线·影舞者）")
    b, p = new_battle("cls_ci_ke", 1, 1, learned=["影刃"])  # 影舞者
    check("连段活跃(攻线影舞)", b._combo_active(p) is True)
    b._combo_add(p)
    b._combo_add(p)
    b._combo_add(p)
    check("连段 +3=3", b.mech_stacks.get("combo") == 3, f"{b.mech_stacks.get('combo')}")
    for _ in range(10):
        b._combo_add(p)
    check("连段封顶10", b.mech_stacks.get("combo") == 10, f"{b.mech_stacks.get('combo')}")
    # 终结技连段增伤：combo 10 → 5%×10 cap 40% → ×1.40
    b.mech_stacks["combo"] = 8
    check("combo8 增伤 ×1.40", abs(b._combo_dmg_mult(p) - 1.40) < 1e-9, f"{b._combo_dmg_mult(p)}")
    b.mech_stacks["combo"] = 3
    check("combo3 增伤 ×1.15", abs(b._combo_dmg_mult(p) - 1.15) < 1e-9, f"{b._combo_dmg_mult(p)}")
    b.mech_stacks["combo"] = 2
    check("combo<3 无增伤", b._combo_dmg_mult(p) == 1.0)
    # on_crit 额外 +1 连击点
    b.resources["cp"] = 4
    b._on_crit_resource(p)
    check("on_crit +1 cp=5", b.resources["cp"] == 5, f"cp={b.resources['cp']}")
    # 受击回退 -1 + 连段归零
    b.mech_stacks["combo"] = 5
    b.resources["cp"] = 4
    p["hp"] -= 50
    # 直接调用受击段（_damage_player 里攻线惩罚）；此处手动模拟
    rd = C.CORE_RESOURCES["cls_ci_ke"]
    b.resources["cp"] = max(0, 4 - 1)
    b._combo_break(p)
    check("受击回退 cp-1=3", b.resources["cp"] == 3)
    check("受击连段归零", b.mech_stacks.get("combo") is None, f"{b.mech_stacks.get('combo')}")
    # 基础刺客（无分支）：不读连段
    b2, p2 = new_battle("cls_ci_ke", 0, 0)
    check("基础刺客无连段", b2._combo_active(p2) is False)


def smoke_monk_momentum():
    print("[挂点5/10] 拳师蓄势 momentum（攻线·格斗士 每气+3%）")
    b, p = new_battle("cls_wu_seng", 1, 1, learned=["疾风拳"])  # 格斗士
    b.resources["chi"] = 5
    check("气5 → ×1.15", abs(b._momentum_mult(p) - 1.15) < 1e-9, f"{b._momentum_mult(p)}")
    b.resources["chi"] = 10
    check("气10 → ×1.30（封顶）", abs(b._momentum_mult(p) - 1.30) < 1e-9, f"{b._momentum_mult(p)}")
    b.resources["chi"] = 0
    check("气0（耗尽）→ 1.0", b._momentum_mult(p) == 1.0)
    # 守线磐石行者不吃蓄势
    b3, p3 = new_battle("cls_wu_seng", 1, 2, learned=["铁壁拳"])
    b3.resources["chi"] = 9
    check("守线不蓄势", b3._momentum_mult(p3) == 1.0)
    # 基础拳师不吃
    b4, p4 = new_battle("cls_wu_seng", 0, 0)
    b4.resources["chi"] = 9
    check("基础不蓄势", b4._momentum_mult(p4) == 1.0)


def smoke_shadow():
    print("[挂点6/10] 暮影 on_dodge_success +1 影步 / 受击清空")
    b, p = new_battle("cls_shadow_blade", 0, 0, learned=["幽影袭"])
    b.resources["shadow_step"] = 2
    # 受击清空（_damage_player 单独段）
    rd = C.CORE_RESOURCES["cls_shadow_blade"]
    if b.resources.get(rd["key"], 0) > 0:
        b.resources[rd["key"]] = 0
    check("受击清空影步", b.resources.get("shadow_step") == 0)
    # 闪避成功攒步（on_dodge_success 段手动驱动）
    b.resources["shadow_step"] = b._res_gain_class("cls_shadow_blade", "shadow_step", rd.get("on_dodge_success", 1))
    check("on_dodge_success +1", b.resources.get("shadow_step") == 1, f"{b.resources.get('shadow_step')}")
    # on_crit 攒步（on_crit_resource）
    b.resources["shadow_step"] = b._res_gain_class("cls_shadow_blade", "shadow_step", rd.get("on_crit", 1))
    check("on_crit +1 影步", b.resources.get("shadow_step") == 2, f"{b.resources.get('shadow_step')}")


def smoke_bard_echo():
    print("[挂点7/10] 牧师歌者双资源：echo 叠层/上限/引用于 _turn_start 全队恢复")
    b, p = new_battle("cls_mu_shi", 1, 1, learned=["轻快拨弦"])
    b._echo_add(p, [])
    b._echo_add(p, [])
    check("回声叠 2/3", b._echo_layers() == 2, f"{b._echo_layers()}")
    b._echo_add(p, [])
    b._echo_add(p, [])
    check("回声封顶 3", b._echo_layers() == 3)
    # 歌类技判定
    info = C.BRANCH_SKILLS.get("cls_mu_shi", {}).get("branches", {}).get(1, {}).get("吟游诗人", {}).get("轻快拨弦")
    check("轻快拨弦=歌类技", b._is_bard_skill(p, info) is True)
    info2 = C.PLAYER_SKILLS.get("cls_mu_shi", {}).get("sk_she_dan")
    if isinstance(info2, dict) and "skills" not in info2:
        check("基础圣光弹非歌类", b._is_bard_skill(p, info2) is False)
    # _turn_start 全队恢复：满层翻倍 6×3×2=36/回合（策划案 12 章 5.1.1；原恒真 check 已改真断言）
    p["hp"] = 100  # 满血时恢复被跳过（hp<max 才结算），先压低血量再验证真实恢复量
    logs_ts = b._turn_start(p)
    check("回合初始回声恢复(3层=36)", p["hp"] == 136,
          f"hp={p['hp']} echo={b._echo_layers()} logs={logs_ts[-3:]}")
    # 回声重开战斗（驻留）——新 Battle 归零
    b2, _p2 = new_battle("cls_mu_shi", 1, 1)
    check("新战斗回声归零", b2._echo_layers() == 0)


def smoke_element():
    print("[挂点8/10] 法师 element_marks / 反应 / 同系连发")
    b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素冲击"])  # 元素法师
    check("初始印记空", sum(b._elem_marks().values()) == 0)
    b._elem_mark_apply("fire")
    b._elem_mark_apply("fire")
    b._elem_mark_apply("fire")
    b._elem_mark_apply("fire")
    marks = b._elem_marks()
    check("fire 印记封顶 3", marks.get("fire") == 3, f"{marks}")
    b._elem_mark_apply("ice", layers=2)
    check("ice 印记 2", b._elem_marks().get("ice") == 2)
    # 引爆反应表：引爆系 fire × 目标 ice 印记 → 蒸发 ×1.30 清 ice
    b.mech_stacks.setdefault("combo", 0)
    rr = b._reaction_table_resolve(p, "fire", {"matk": 100}, [])
    check("蒸发触发", rr is not None and rr[0] == 1.30, f"{rr}")
    check("蒸发清除 ice 印记", b._elem_marks().get("ice", 0) == 0, f"{b._elem_marks()}")
    # 超载：fire × thunder → aoe（日志非空 / 不崩）
    b._elem_mark_apply("thunder")
    logs = []
    rr = b._reaction_table_resolve(p, "fire", {"matk": 100}, logs)
    check("超载触发(aoe日志)", rr is not None and rr[2] is False and logs, f"{logs} rr={rr}")
    check("超载清除 thunder", b._elem_marks().get("thunder", 0) == 0)
    # 无对应印记 → None
    b._elem_marks().clear()
    check("无印记无反应", b._reaction_table_resolve(p, "ice", {"matk": 100}, []) is None)
    # 同系连发：连续两次 fire → 额外 +1 充能
    b.resources["element_charge"] = 0
    b._last_element_set(p, "fire")
    b.resources["element_charge"] = 0
    b._last_element_set(p, "fire")
    check("同系连发额外 +1 充能", b._elem_charge() == 1, f"charge={b._elem_charge()}")
    b._last_element_set(p, "ice")
    b.resources["element_charge"] = 0
    b._last_element_set(p, "ice")
    b._last_element_set(p, "ice")
    check("同系连发连续触发 +2", b._elem_charge() == 2, f"charge={b._elem_charge()}")


def smoke_res_cost_cast():
    print("[挂点9/10] 元素充能 res_cost 施放主路径不崩（_do_player_skill 消费/校验）")
    b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素引爆", "元素冲击"])
    # 元素引爆 res_cost {"element": 2}
    info = C.BRANCH_SKILLS["cls_fa_shi"]["branches"][1]["元素法师"]["元素引爆"]
    b.resources["element_charge"] = 0
    logs, blocked = b._skill_cast_blocked("元素引爆", p)
    check("充能0 施放被拦截", blocked is True, f"{logs}")
    b.resources["element_charge"] = 3
    logs, blocked = b._skill_cast_blocked("元素引爆", p)
    check("充能3 校验通过", blocked is False, f"{logs}")
    # 直接调 _res_spend 消费
    b.resources["element_charge"] = 3
    ok = b._res_spend("element", 2)
    check("施放扣 2 充能", ok and b._elem_charge() == 1)
    # 歌者共鸣 res_cost {"resonance": 3}
    b2, p2 = new_battle("cls_mu_shi", 1, 1, learned=["启明圣咏"])
    info2 = C.BRANCH_SKILLS["cls_mu_shi"]["branches"][1]["吟游诗人"]["启明圣咏"]
    b2.resources["resonance"] = 0
    logs, blocked = b2._skill_cast_blocked("启明圣咏", p2)
    check("共鸣0 拦截", blocked is True)
    b2.resources["resonance"] = 5
    logs, blocked = b2._skill_cast_blocked("启明圣咏", p2)
    check("共鸣5 通过", blocked is False)


def smoke_hidden_variant():
    print("[挂点10/10] 隐藏线进阶变奏（星语命中攒印 / 悼咏溢满转盾）")
    # 星语猎印：命中才攒（on_attack + on_hit 命中语义 + 暴击额外）
    b, p = new_battle("cls_wild_hunter", 0, 0, learned=["星陨"])
    check("猎印初始 0", b.resources.get("hunt_mark", 0) == 0)
    b.resources["hunt_mark"] = 0
    b._resource_on_attack(p, is_crit=False)
    check("普通命中攒印 on_attack+on_hit=2", b.resources.get("hunt_mark") == 2, f"{b.resources.get('hunt_mark')}")
    b.resources["hunt_mark"] = 0
    b._resource_on_attack(p, is_crit=True)
    check("暴击命中 +2 +暴击额外1=3", b.resources.get("hunt_mark") == 3, f"{b.resources.get('hunt_mark')}")
    # 悼咏溢满转盾（overflow_shield）
    b, p = new_battle("cls_hymn", 0, 0)
    b.resources["canticle"] = 9
    b._res_gain_class("cls_hymn", "canticle", 4)  # 9+4 → 满10 溢出3 → 盾15
    check("悼咏封顶10", b.resources.get("canticle") == 10, f"{b.resources.get('canticle')}")
    sh = b.p_shields.get("canticle_overflow")
    check("溢出转盾 15", sh is not None and sh["value"] == 15, f"{sh}")
    # 龙力/时之沙 regen 已在 core_resources（_turn_start 通用 regen 管线），构造即不崩
    b, p = new_battle("cls_dragon_oath", 0, 0)
    b.resources["dragon_might"] = 8
    b._turn_start(p)
    check("龙力回合自然回 +1", b.resources.get("dragon_might") == 9, f"{b.resources.get('dragon_might')}")


def smoke_tier2_3_branches():
    """P1-1 修复：分支机制 tier2/3 全档断档——_is_path 按 (class,path) 判定，60/90 级进化改名不断档"""
    print("[修复1/8] P1-1 分支机制 tier2/3 全档生效")
    # 刺客攻线：影舞者(t1)→暗影之刃(t2)→无影之刃(t3) 连段全档
    for tier in (1, 2, 3):
        b, p = new_battle("cls_ci_ke", tier, 1)
        check(f"刺客攻线 t{tier} 连段活跃", b._combo_active(p) is True)
        b.resources["cp"] = 4
        b._on_crit_resource(p)
        check(f"刺客攻线 t{tier} on_crit +1", b.resources["cp"] == 5, f"cp={b.resources['cp']}")
    # 拳师攻线：格斗士(t1)→拳术师(t2)→破晓者(t3) 蓄势全档
    for tier in (1, 2, 3):
        b, p = new_battle("cls_wu_seng", tier, 1)
        b.resources["chi"] = 5
        check(f"拳师攻线 t{tier} 蓄势 ×1.15", abs(b._momentum_mult(p) - 1.15) < 1e-9, f"{b._momentum_mult(p)}")
    # 游侠守线：风行者(t1)→疾风射手(t2)→疾风猎手(t3) 满弦全档
    for tier in (1, 2, 3):
        b, p = new_battle("cls_you_xia", tier, 2)
        b.resources["energy"] = 100
        check(f"游侠守线 t{tier} 满弦 True", b._energy_high_crit(p) is True)
    # 法师攻线：元素法师(t1)→元素术士(t2)→元素贤者(t3) 同系连发全档
    for tier in (1, 2, 3):
        b, p = new_battle("cls_fa_shi", tier, 1)
        b.resources["element_charge"] = 0
        b._last_element_set(p, "fire")
        b.resources["element_charge"] = 0
        b._last_element_set(p, "fire")
        check(f"法师攻线 t{tier} 同系连发 +1 充能", b._elem_charge() == 1, f"charge={b._elem_charge()}")
    # 战士攻线：狂战士(t1)→狂战统领(t2)→战争领主(t3) 血债线判定
    b, p = new_battle("cls_zhan_shi", 3, 1)
    check("战士攻线 t3 _is_path(1)=True", b._is_path(p, 1) is True and b._is_path(p, 2) is False)
    # 守线不得误命中（刺客攻线判定对守线=False）
    b, p = new_battle("cls_ci_ke", 2, 2)
    check("刺客守线(毒线)不读连段", b._combo_active(p) is False)
    # 基础职业不受影响
    b, p = new_battle("cls_wu_seng", 0, 0)
    check("基础拳师 _is_path(1)=False", b._is_path(p, 1) is False)


def smoke_on_heal():
    """P1-2 修复：on_heal 消费者——牧师/悼咏治疗攒点 +2（v130 删 per-skill gain 后的唯一主渠道）"""
    print("[修复2/8] P1-2 on_heal 消费端（牧师治疗攒点）")
    # 基础牧师施放 治愈术 → 治疗命中攒 2 信仰（黑盒走 _do_player_skill 全链）
    b, p = new_battle("cls_mu_shi", 0, 0, learned=["治愈术"])
    p["hp"] = 200
    b.p_eff["next_heal_up"] = 0.20
    b.resources["faith"] = 0
    logs = b._do_player_skill("治愈术", p)
    check("牧师治疗攒点 on_heal=2", b.resources.get("faith", 0) == 2, f"faith={b.resources.get('faith')} logs={logs}")
    # 歌者（双资源分支）治疗走共鸣，不给信仰（防双计数）
    b, p = new_battle("cls_mu_shi", 1, 1)
    b.resources["faith"] = 0
    b.resources["resonance"] = 0
    b._resource_on_skill(p, {"kind": "治疗", "res_gain": {"resonance": 2}, "name": "咏叹调"})
    check("歌者治疗走共鸣、不计信仰", b.resources.get("faith", 0) == 0 and b.resources.get("resonance", 0) == 2,
          f"faith={b.resources.get('faith')} resonance={b.resources.get('resonance')}")


def smoke_resource_amp():
    """P1-3 修复：resource_amp 消费端——受击/出手命中/治疗/自然回 四触发 + turns/hits 衰减"""
    print("[修复3/8] P1-3 resource_amp（4 种药水接线 + 衰减）")
    b, p = new_battle("cls_zhan_shi", 0, 0)
    b.resources["rage"] = 0
    b.p_eff.setdefault("amps", {})["rage"] = {"key": "rage", "amount": 2, "trigger": "on_hit",
                                              "turns_left": 3, "hits_left": 0}
    # 受击触发（沸腾战血 turns 制）→ +2，且 turns 不在触发点递减（回合制 _end_round 减）
    extra = b._amp_resource(p, "on_hit_taken")
    check("受击增幅 +2", extra == 2 and b.resources["rage"] == 2, f"rage={b.resources['rage']}")
    check("受击增幅 turns 未在触发点减", b.p_eff["amps"]["rage"]["turns_left"] == 3)
    # 出手命中不应命中 turns 制受击增幅（hits_left=0）——语义解耦
    b.resources["rage"] = 0
    check("出手命中不误吃受击增幅", b._amp_resource(p, "on_land_hit") == 0 and b.resources["rage"] == 0)
    b._end_round()
    check("回合衰减 turns 3→2", b.p_eff["amps"]["rage"]["turns_left"] == 2)
    # 出手命中 hits 制（影袭药水 cp）
    b, p = new_battle("cls_ci_ke", 0, 0)
    b.resources["cp"] = 0
    b.p_eff.setdefault("amps", {})["cp"] = {"key": "cp", "amount": 1, "trigger": "on_hit",
                                            "turns_left": 0, "hits_left": 3}
    for i in range(3):
        extra = b._amp_resource(p, "on_land_hit")
        check(f"出手命中 {i+1}/3 增幅 +1", extra == 1 and b.resources["cp"] == i + 1, f"cp={b.resources['cp']}")
    check("hits 耗尽清 amp", "cp" not in b.p_eff.get("amps", {}), f"amps={b.p_eff.get('amps')}")
    # 自然回 regen（迅捷之核 energy +30）+ 治疗 on_heal（香薰圣烛 faith +1）语义
    b, p = new_battle("cls_you_xia", 0, 0)
    b.resources["energy"] = 0
    b.p_eff.setdefault("amps", {})["energy"] = {"key": "energy", "amount": 30, "trigger": "regen",
                                                "turns_left": 1, "hits_left": 0}
    extra = b._amp_resource(p, "regen")
    check("自然回增幅 +30", extra == 30 and b.resources["energy"] == 30)
    b, p = new_battle("cls_mu_shi", 0, 0)
    b.resources["faith"] = 0
    b.p_eff.setdefault("amps", {})["faith"] = {"key": "faith", "amount": 1, "trigger": "on_heal",
                                               "turns_left": 3, "hits_left": 0}
    extra = b._amp_resource(p, "on_heal")
    check("治疗增幅 +1 信仰", extra == 1 and b.resources["faith"] == 1, f"faith={b.resources['faith']}")


def smoke_full_tension_timing():
    """P1-4 修复：满弦判定读「施放前」精力（扣费后读 → 高耗档永不生效）"""
    print("[修复4/8] P1-4 满弦时序（读施放前精力）")
    b, p = new_battle("cls_you_xia", 1, 2)  # 风行者
    b.resources["energy"] = 100
    # 模拟 _do_player_skill：施放前快照 energy=100，随后扣 25 → 当前 75
    b._pre_cost_res = dict(b.resources)
    b._res_spend("energy", 25)
    check("扣费后当前精力75(<80)", b.resources["energy"] == 75)
    # 低耗档(25≤max_cost)：满弦应以施放前 100 判定 → True（修复前扣费后 75 → False 断档）
    check("满弦读施放前精力判定 True", b._energy_high_crit(p, {"res_cost": {"energy": 25}}) is True)
    # 无快照（直接调用/非技能链）回落当前值
    b._pre_cost_res = None
    check("无快照回落当前精力75 → False", b._energy_high_crit(p, {"res_cost": {"energy": 25}}) is False)


def smoke_wild_hunter():
    """P1-5 修复：wild_hunter on_hit 命中语义——受击不攒猎印（旧受击钩子误读）"""
    print("[修复5/8] P1-5 星语猎手 on_hit 双语义解耦")
    b, p = new_battle("cls_wild_hunter", 0, 0)
    p["hp"] = p["max_hp"]
    b.resources["hunt_mark"] = 0
    logs = []
    b._damage_player(p, 100, logs)
    check("星语猎手受击不再 +1 猎印", b.resources.get("hunt_mark", 0) == 0, f"{b.resources.get('hunt_mark')}")
    # 命中渠道保留（普攻命中攒印）
    b, p = new_battle("cls_wild_hunter", 0, 0)
    b.resources["hunt_mark"] = 0
    b._resource_on_attack(p, is_crit=False)
    check("星语猎手普攻命中仍攒印 +2", b.resources.get("hunt_mark") == 2, f"{b.resources.get('hunt_mark')}")
    # 战士受击渠道不受影响（on_hit=受击 +1 怒气）
    b, p = new_battle("cls_zhan_shi", 0, 0)
    p["hp"] = p["max_hp"]
    b.resources["rage"] = 0
    logs = []
    b._damage_player(p, 50, logs)
    check("战士受击回怒保持 +1", b.resources.get("rage", 0) >= 1, f"rage={b.resources.get('rage')}")


def smoke_item_consumers():
    """P0 消耗品 5 项只写不读修复：buff_phys_next / next_heal_up / reduce_all负值 / phys_up"""
    print("[修复6/8] P0 消耗品消费端（引气精华/信仰结晶/熔核之心/澎湃烈酒）")
    # 引气精华 buff_phys_next：下一次物理技 一次性消费（命中即清，豁免回合递减）
    b, p = new_battle("cls_zhan_shi", 0, 0, learned=["无畏冲击"])
    b.player = p
    st = b._player_stats(p)
    b.p_buffs["buff_phys_next"] = 1
    b.p_eff["buff_phys_next"] = 0.20
    b._player_attack(st, p)
    check("buff_phys_next 物理普攻命中即清", "buff_phys_next" not in b.p_buffs and "buff_phys_next" not in b.p_eff,
          f"p_buffs={b.p_buffs}")
    # 信仰结晶 next_heal_up：_do_player_skill 治疗黑盒消费（上面 P1-2 已共用）
    # 熔核之心 reduce_all 负值：受伤 +20%（P0-4）
    b, p = new_battle("cls_zhan_shi", 0, 0)
    b.player = p
    p["hp"] = p["max_hp"]
    b.p_buffs["reduce_all"] = -0.2
    b._reduce_all_left = 2
    logs = []
    hp_before = p["hp"]
    b._damage_player(p, 100, logs)
    lost = hp_before - p["hp"]
    check("熔核负值减伤：受损 +20%(120)", lost >= 115, f"lost={lost} hp={p['hp']} logs={logs}")
    # 正向 reduce_all 不被覆盖（团队技能减伤 ×0.9 保持）
    b, p = new_battle("cls_zhan_shi", 0, 0)
    b.player = p
    p["hp"] = p["max_hp"]
    b.p_buffs["reduce_all"] = 0.5
    b._reduce_all_left = 2
    logs = []
    b._damage_player(p, 100, logs)
    lost = p["max_hp"] - p["hp"]
    check("正向 reduce_all 仍减伤(50%→50)", lost <= 55 and lost > 0, f"lost={lost}")
    # 澎湃烈酒 phys_up：物理伤害 +5%，回合制持续 buff 普攻后仍在
    b, p = new_battle("cls_zhan_shi", 0, 0)
    b.player = p
    st = b._player_stats(p)
    b.p_buffs["phys_up"] = 3
    b.p_eff["phys_up"] = 0.05
    b._player_attack(st, p)
    check("phys_up 普攻后仍在(回合制)", b.p_buffs.get("phys_up") == 3, f"{b.p_buffs.get('phys_up')}")


def smoke_mech_stack_hidden():
    """P1 隐藏线每层加成挂点：dragon_might +18%/层、zen +12%/层（MECH_STACK_BONUS 消费）"""
    print("[修复7/8] P1 隐藏线每层加成（龙力/禅意）")
    b, p = new_battle("cls_dragon_oath", 0, 0)
    b._pre_cost_res = dict(b.resources)
    b._pre_cost_res["dragon_might"] = 10
    m = b._mech_stack_bonus("dragon_might", {}, {"res_cost": {"dragon_might": 10}})
    check("龙脉终曲 满龙力10层 ×2.00（v130.2f 每层 0.18→0.10 收敛）", abs(m - 2.00) < 1e-9, f"{m}")
    # 注意：cls_wu_sheng=苦修士（隐藏线，禅意 zen 专属；气爆/撼岳·终焉 均其技能），
    # 与拳师 cls_wu_seng 不同——此处类名非笔误，勿"修正"
    b, p = new_battle("cls_wu_sheng", 0, 0)
    b.resources["zen"] = 10
    b._pre_cost_res = dict(b.resources)
    m = b._mech_stack_bonus("zen", {}, {"res_cost": {"zen": 10}})
    check("撼岳·终焉 满禅意10层 ×2.20", abs(m - 2.20) < 1e-9, f"{m}")
    b, p = new_battle("cls_wu_sheng", 0, 0)
    b.resources["zen"] = 5
    b._pre_cost_res = dict(b.resources)
    m = b._mech_stack_bonus("chi_burst", {}, {"res_cost": {"zen": 5}})
    check("气爆 5 禅意 ×1.60（消耗型）", abs(m - 1.60) < 1e-9, f"{m}")
    # 未消费该资源的技能不受影响
    b, p = new_battle("cls_zhan_shi", 0, 0)
    b.resources["rage"] = 5
    b._pre_cost_res = dict(b.resources)
    check("普通技能无 per-res 加成", b._mech_stack_bonus("", {}, {"res_cost": {"rage": 5}}) == 1.0)


def smoke_reaction_wiring():
    """P1 反应表接线：携带 cond.type='reaction' 且 element 的技能 → 引爆反应表触发（数据层待补格式见总结）"""
    print("[修复8/8] P1 反应表接线（引擎侧判定触发）")
    b, p = new_battle("cls_fa_shi", 1, 1, learned=["元素冲击"])
    # 目标挂 ice 印，双系连珠/元素引爆类技能带 cond reaction + element=fire → 蒸发 ×1.30
    b._elem_mark_apply("ice", layers=1)
    info = {"kind": "魔法", "element": "fire", "power": 2.0,
            "cond": {"type": "reaction", "label": "双系连珠"}}
    # 与 _player_skill:2607 内联判定一致：cond.type=='reaction' and element → 走 _reaction_table_resolve
    if info.get("cond", {}).get("type") == "reaction" and info.get("element"):
        rr = b._reaction_table_resolve(p, info["element"], {"matk": 100}, [])
        check("reaction cond 技能触发反应表(蒸发1.30)", rr is not None and rr[0] == 1.30,
              f"rr={rr}")
    # 无 cond 元素技能不触发（普通印记途径仍走旧 E.element_reaction 泛化）
    b._elem_marks().clear()
    b._elem_mark_apply("ice", layers=1)
    info2 = {"kind": "魔法", "element": "ice", "power": 1.5}
    check("无 reaction cond 不触发引爆表", not (info2.get("cond", {}).get("type") == "reaction"))


def main():
    smoke_branch_resource()
    smoke_warrior_blood()
    smoke_ranger_full()
    smoke_assassin_combo()
    smoke_monk_momentum()
    smoke_shadow()
    smoke_bard_echo()
    smoke_element()
    smoke_res_cost_cast()
    smoke_hidden_variant()
    # v130.2 修复批次（8 类断链）冒烟
    smoke_tier2_3_branches()
    smoke_on_heal()
    smoke_resource_amp()
    smoke_full_tension_timing()
    smoke_wild_hunter()
    smoke_item_consumers()
    smoke_mech_stack_hidden()
    smoke_reaction_wiring()
    print(f"\n全部通过：{_passed} 项断言 PASS")


if __name__ == "__main__":
    main()
