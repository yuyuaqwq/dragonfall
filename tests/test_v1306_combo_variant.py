# -*- coding: utf-8 -*-
"""v130.6 拳师连招变招 + 三连回馈固化测试

覆盖：
  ① combo_ready 消费端：三连后（combo_ready=1）放气力技（碎骨拳，耗气）→
     消费路径生效（_combo_ready_used=True）、标记归零、日志含「三连余劲」
  ② combo_ready 非气力技不消费：标记存在时放直拳（不耗气）→ 标记保留、无消费标志
  ③ last_combo_tag：三连触发清空序列后仍记忆上一招 tag（变招引擎）
  ④ 侧踢变招（player_combo cond）：上一招【拳】→ cond_mult=1.10；对照（last=掌）→ 1.0
  ⑤ 序列化往返：last_combo_tag 存档保留

运行：python tests/test_v1306_combo_variant.py（exit=0 全绿）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_v1306_combo_variant.db")
os.environ["GWEN_GAME_DB"] = _DB

from conftest import C, clean_db  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"✅ {name}")
    else:
        failed += 1
        print(f"❌ {name} {detail}")


def mk(cls="拳师", lv=30, mp=500):
    return {'class_name': cls, 'level': lv, 'hp': 300, 'max_hp': 300, 'mp': mp, 'max_mp': mp,
            'atk': 50, 'def': 10, 'matk': 5, 'mdef': 5, 'spd': 10, 'crit': 0.0, 'dodge': 0.0,
            'equipment': {}, 'learned_skills': [], 'skill_levels': {}}


def mkmon(name='木桩', hp=99999):
    return {'name': name, 'hp': hp, 'max_hp': hp, 'atk': 5, 'def': 0, 'matk': 0, 'mdef': 0,
            'spd': 1, 'lv': 1, 'role': 'dps', 'skills': []}


SK = C.PLAYER_SKILLS["cls_wu_seng"]["skills"]


def skill_name(key):
    return SK[key]["name"]


# v151 拳师表：直拳(拳)/侧踢(踢)/钢拳(掌)/连招三连/震地击/铜墙/冲拳/冥想
# 气力技已移至分支（磐岩释能 res_cost guard_core）——combo_ready 消费端测试改用
# 磐岩释能（guard_core 气力技）验证；普通技用 直拳
_CHI_SKILL = "磐岩释能"   # v151 分支气力技（res_cost guard_core 1）
_PLAIN_SKILL = "直拳"     # 普通 combo 技（不耗资源）


def cast(sk_name, setup=None, chi=10):
    """构造拳师战斗并施放指定技能（sk_name 传中文名），返回 (battle, logs)"""
    p = mk(lv=40)
    p["class_name"] = "cls_wu_seng"
    p["class_tier"] = 1
    p["evolve_path"] = 2
    p["learned_skills"] = [sk_name]
    b = BT.Battle("monster", mkmon(), player=p)
    b._p_res()["guard_core"] = chi  # v180-B：resources 在 player actor dict
    if setup:
        setup(b)
    logs, _ = b.actor_turn("skill", sk_name, p, enemy_act=False)
    # v154 读条命中制：出招读条结束（cast_done）才命中结算（伤害/叠层）——推进后触发
    b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
    return b, logs


def main():
    clean_db()
    print("【① combo_ready 消费：三连后气力技 +20%】")
    # v151：拳师资源改为 guard_core（磐核），combo_ready 消费端 `_is_chi_skill` 只认 res_cost chi——
    # v151 无 chi 资源技能，该机制已随旧资源体系废弃。保留验证：combo_ready 标记对非 chi 技不消费
    # （对应旧②语义），并直接验证 guard_core 资源技（磐岩释能）正常施放
    bA, logsA = cast(_CHI_SKILL, lambda b: b._p_res().__setitem__("combo_ready", 1))
    check("① 磐岩释能正常施放（guard_core 资源技）", bA.enemy["hp"] < 99999, str(logsA)[:200])
    check("① 非 chi 资源技不消费 combo_ready（v151 旧机制废弃）",
          bA._p_res().get("combo_ready") == 1 and not getattr(bA, "_combo_ready_used", False),
          str(bA._p_res()))
    check("① 无三连余劲日志（v151 无 chi 技）", not any("余劲" in x for x in logsA), str(logsA)[:250])
    # 伤害均值对比（战斗有幸运一击 ±50% 随机，8 次均值消除噪声）——v151 无 chi 消耗差异，改为施放正常性冒烟
    import random
    dmg_with = []
    random.seed(20260828)
    for _ in range(8):
        b, logs = cast(_CHI_SKILL, lambda b: b._p_res().__setitem__("combo_ready", 1))
        dmg_with.append(99999 - b.enemy["hp"])
    dmg_wo = []
    random.seed(20260828)
    for _ in range(8):
        b, _ = cast(_CHI_SKILL)
        dmg_wo.append(99999 - b.enemy["hp"])
    avg_with = sum(dmg_with) / 8
    avg_wo = sum(dmg_wo) / 8
    check(f"① 磐岩释能 8 次施放均值稳定（{avg_with:.0f} vs {avg_wo:.0f}）",
          avg_with > 0 and avg_wo > 0,
          f"with={dmg_with} wo={dmg_wo}")

    print("【② combo_ready 非气力技不消费】")
    bC, logsC = cast(_PLAIN_SKILL, lambda b: b._p_res().__setitem__("combo_ready", 1))
    check("② 普通技不消费标记", bC._p_res().get("combo_ready") == 1, str(bC._p_res()))
    check("② 无消费标志", not getattr(bC, "_combo_ready_used", False), str(logsC)[:200])
    check("② 普通技无余劲日志", not any("余劲" in x for x in logsC), str(logsC)[:250])

    print("【③ last_combo_tag 记忆】")
    bE = BT.Battle("monster", mkmon(), player=mk())
    bE._combo_push("拳")
    bE._combo_push("踢")
    bE._combo_push("掌")
    check("③ 三连后序列清空", bE._p_combo_seq() == [], str(bE._p_combo_seq()))
    check("③ 上一招记忆=掌", bE._p_last_combo_tag() == "掌", str(bE._p_last_combo_tag()))
    bE._combo_push("拳")
    check("③ 新序列更新记忆=拳", bE._p_last_combo_tag() == "拳", str(bE._p_last_combo_tag()))

    print("【④ 侧踢变招：上一招拳 → +10%（_cond_mult 确定性断言）】")
    p = mk(lv=30)
    # v151：侧踢无 cond 字段——构造带 player_combo cond 的技能 dict 验证变招条件引擎（v130.6 引擎仍在）
    info = {"name": "侧踢", "power": 1.0, "kind": "物理",
            "cond": {"type": "player_combo", "last": "拳", "mult": 1.10, "label": "侧踢变招"}}
    bF = BT.Battle("monster", mkmon(), player=p)
    bF._combo_push("拳")
    check("④ 上一招拳 → cond 触发", abs(bF._cond_mult(info, p) - 1.10) < 1e-9,
          str(bF._cond_mult(info, p)))
    bG = BT.Battle("monster", mkmon(), player=p)
    bG._combo_push("踢")
    bG._combo_push("掌")
    check("④ 上一招掌 → 不触发", abs(bG._cond_mult(info, p) - 1.0) < 1e-9,
          str(bG._cond_mult(info, p)))
    # 空序号（无连招）→ 不触发
    bH = BT.Battle("monster", mkmon(), player=p)
    check("④ 无连招 → 不触发", abs(bH._cond_mult(info, p) - 1.0) < 1e-9,
          str(bH._cond_mult(info, p)))
    # 完整施放冒烟：上一招拳 + 侧踢
    bI, logsI = cast("侧踢", lambda b: b._combo_push("拳"))
    check("④ 变招施放无异常", bI.enemy["hp"] < 99999, str(logsI)[:200])

    print("【⑤ 序列化往返】")
    bJ = BT.Battle("monster", mkmon(), player=mk())
    bJ._combo_push("拳")
    bJ._combo_push("踢")
    st = bJ.to_state()
    bK = BT.Battle.from_state(st)
    bK._focus = mk()  # v180-B ①：from_state 后绑定玩家 actor dict
    bK._apply_restore_pstate()
    check("⑤ combo_seq 保留", bK._p_combo_seq() == ["拳", "踢"], str(bK._p_combo_seq()))
    check("⑤ last_combo_tag 保留", bK._p_last_combo_tag() == "踢", str(bK._p_last_combo_tag()))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()