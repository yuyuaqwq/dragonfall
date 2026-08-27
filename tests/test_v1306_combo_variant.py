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


def cast(sk_key, setup=None, chi=10):
    """构造拳师战斗并施放指定技能，返回 (battle, logs)"""
    p = mk(lv=30)
    p["learned_skills"] = [skill_name(sk_key)]
    b = BT.Battle("monster", mkmon(), player=p)
    b.resources["chi"] = chi
    if setup:
        setup(b)
    logs, _ = b.player_turn("skill", skill_name(sk_key), p, enemy_act=False)
    return b, logs


def main():
    clean_db()
    print("【① combo_ready 消费：三连后气力技 +20%】")
    bA, logsA = cast("sk_beng_quan", lambda b: b.resources.__setitem__("combo_ready", 1))
    check("① 消费路径生效（_combo_ready_used）", getattr(bA, "_combo_ready_used", False),
          str(logsA)[:200])
    check("① 日志含三连余劲", any("余劲" in x for x in logsA), str(logsA)[:250])
    check("① combo_ready 已消费归零", bA.resources.get("combo_ready") == 0, str(bA.resources))
    # 伤害均值对比（战斗有幸运一击 ±50% 随机，8 次均值消除噪声）
    dmg_with = []
    for _ in range(8):
        b, logs = cast("sk_beng_quan", lambda b: b.resources.__setitem__("combo_ready", 1))
        dmg_with.append(99999 - b.enemy["hp"])
    dmg_wo = []
    for _ in range(8):
        b, _ = cast("sk_beng_quan")
        dmg_wo.append(99999 - b.enemy["hp"])
    avg_with = sum(dmg_with) / 8
    avg_wo = sum(dmg_wo) / 8
    check(f"① 气力技伤害均值倾向 +20%（{avg_with:.0f} vs {avg_wo:.0f}）",
          avg_with > avg_wo and (avg_with - avg_wo) / avg_wo > 0.05,
          f"with={dmg_with} wo={dmg_wo}")

    print("【② combo_ready 非气力技不消费】")
    bC, logsC = cast("sk_zhi_quan", lambda b: b.resources.__setitem__("combo_ready", 1))
    check("② 普通技不消费标记", bC.resources.get("combo_ready") == 1, str(bC.resources))
    check("② 无消费标志", not getattr(bC, "_combo_ready_used", False), str(logsC)[:200])
    check("② 普通技无余劲日志", not any("余劲" in x for x in logsC), str(logsC)[:250])

    print("【③ last_combo_tag 记忆】")
    bE = BT.Battle("monster", mkmon(), player=mk())
    bE._combo_push("拳")
    bE._combo_push("踢")
    bE._combo_push("掌")
    check("③ 三连后序列清空", bE.combo_seq == [], str(bE.combo_seq))
    check("③ 上一招记忆=掌", bE.last_combo_tag == "掌", str(bE.last_combo_tag))
    bE._combo_push("拳")
    check("③ 新序列更新记忆=拳", bE.last_combo_tag == "拳", str(bE.last_combo_tag))

    print("【④ 侧踢变招：上一招拳 → +10%（_cond_mult 确定性断言）】")
    p = mk(lv=30)
    info = SK["sk_ce_ti"]
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
    bI, logsI = cast("sk_ce_ti", lambda b: b._combo_push("拳"))
    check("④ 变招施放无异常", bI.enemy["hp"] < 99999, str(logsI)[:200])

    print("【⑤ 序列化往返】")
    bJ = BT.Battle("monster", mkmon(), player=mk())
    bJ._combo_push("拳")
    bJ._combo_push("踢")
    st = bJ.to_state()
    bK = BT.Battle.from_state(st)
    check("⑤ combo_seq 保留", bK.combo_seq == ["拳", "踢"], str(bK.combo_seq))
    check("⑤ last_combo_tag 保留", bK.last_combo_tag == "踢", str(bK.last_combo_tag))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


main()