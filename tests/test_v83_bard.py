# -*- coding: utf-8 -*-
"""v83 隐藏职业·吟游诗人（22 章）：注册拦截 / 传承转职 / 成就 / 数据完整性"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, E, BT, Main, FakeEvent, run, clean_db, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


async def main():
    clean_db()
    m = Main(None)

    # ---- 1. 数据完整性 ----
    bard = C.CLASSES.get("cls_bard")
    check("cls_bard 存在", bool(bard), "")
    check("cls_bard 标记隐藏", bard and bard.get("hidden") is True, str(bard and bard.get("hidden")))
    check("cls_bard 辅助定位", bard and bard.get("role") == "辅助", str(bard and bard.get("role")))
    sk = C.PLAYER_SKILLS.get("cls_bard", {}).get("skills", {})
    check("吟游诗人 12 技能", len(sk) == 12, str(len(sk)))  # v95 补 Lv.2 轻快拨弦 + v106.1 快板节奏
    names = [v.get("name") for v in sk.values()]
    check("技能名齐全", "即兴弹唱" in names and "战歌" in names and "终章·黎明颂歌" in names, str(names))
    team_cnt = sum(1 for v in sk.values() if v.get("team"))
    check("团队技能>=5", team_cnt >= 5, str(team_cnt))
    # SKILL_UP 覆盖（v102.4 下沉 data/skill_up.py，经 C 访问）
    for n in names:
        check(f"SKILL_UP 有 {n}", n in E.C.SKILL_UP, "")

    # ---- 2. 注册拦截 ----
    out = await cmd(m, "register", "g2", "w2", "注册 吟游诗人 小诗人 男")
    check("隐藏职业不可注册", "隐藏职业" in out or "传说" in out, out[:150])
    check("未创建玩家", db.get_player("g2", "w2") is None, "")

    # ---- 3. 传承转职流程 ----
    await cmd(m, "register", "g1", "w1", "注册 牧师 旅人 男")
    db.update_player("g1", "w1", level=30, gold=5000)
    # 未解锁时被拦
    out = await cmd(m, "evolve", "g1", "w1", "转职 吟游诗人")
    check("未解锁被拦", "传承" in out and "还未" in out, out[:200])
    # 手动解锁（模拟试炼完成）
    db.update_player("g1", "w1", hidden_class_unlock=["cls_bard"])
    out = await cmd(m, "evolve", "g1", "w1", "转职 吟游诗人")
    check("传承成功", "吟游诗人" in out and "传承完成" in out, out[:250])
    p = db.get_player("g1", "w1")
    check("职业已切换", p["class_name"] == "cls_bard", str(p["class_name"]))
    check("转职清零", p.get("class_tier") == 1 and p.get("evolve_path") == 1, str((p.get("class_tier"), p.get("evolve_path"))))
    check("学到初始技能", "即兴弹唱" in p["learned_skills"], str(p["learned_skills"]))
    check("HP 按诗人重算", p["max_hp"] == p["hp"] and p["max_hp"] > 0, str(p["max_hp"]))
    # 再转提示已是诗人
    out = await cmd(m, "evolve", "g1", "w1", "转职 吟游诗人")
    check("已是诗人提示", "已是吟游诗人" in out, out[:150])
    # 等级不足
    db.update_player("g1", "w1", class_name="cls_mu_shi", hidden_class_unlock=["cls_bard"], level=10)
    out = await cmd(m, "evolve", "g1", "w1", "转职 吟游诗人")
    check("等级不足拦截", "Lv.30" in out, out[:150])

    # ---- 4. 成就 cond ----
    from data.plugins.dragonfall.game.core.achievements import cond_met
    p = db.get_player("g1", "w1")
    check("hidden_class cond 命中", cond_met(p, {}, {}, {}, {"type": "hidden_class", "key": "cls_bard"}), "")
    p2 = dict(p); p2["hidden_class_unlock"] = []
    check("hidden_class cond 不命中", not cond_met(p2, {}, {}, {}, {"type": "hidden_class", "key": "cls_bard"}), "")
    p3 = dict(p); p3["class_name"] = "cls_bard"; p3["level"] = 90
    check("hidden_class_lv cond 命中", cond_met(p3, {}, {}, {}, {"type": "hidden_class_lv", "key": "cls_bard", "value": 90}), "")
    p4 = dict(p3); p4["level"] = 89
    check("hidden_class_lv cond 不命中", not cond_met(p4, {}, {}, {}, {"type": "hidden_class_lv", "key": "cls_bard", "value": 90}), "")
    # 成就总数 110（v87 隐藏线 +6）
    check("成就总数 110", len(C.ACHIEVEMENTS) == 110, str(len(C.ACHIEVEMENTS)))
    ach_names = [a["name"] for a in C.ACHIEVEMENTS]
    for n in ("虹彩邂逅", "夜钓月华", "星海遗民", "流星祈愿者", "诗人传承", "黎明颂者"):
        check(f"成就含 {n}", n in ach_names, "")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
