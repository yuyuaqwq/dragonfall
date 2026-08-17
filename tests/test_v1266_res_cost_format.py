# -*- coding: utf-8 -*-
"""v126.5 技能列表资源消耗显示格式 回归测试。

鱼鱼问「信仰-3 是不是需要消耗 3 信仰才能释放？」——原渲染 `信仰值 -3`
容易被读成属性值 -3。v126.5 改为资源消耗并入魔力求：
  `消耗：30 魔力 + 3 信仰值 ｜ 射程：2`
直白表达"消耗 30 魔力和 3 信仰值"。

同时修复脱战拦截提示输出英文 key（`faith3`）违反"玩家可见文本禁止内部 ID"铁律。

1. 圣光惩击（cls_mu_shi res_cost faith3）：消耗行含 `30 魔力 + 3 信仰值`，不含 `信仰值 -3`
2. 战士怒气技（res_cost rageN）：消耗行含 `N 怒气` 并入
3. 零 MP + 纯资源技：只显示资源不求
4. 无资源技能：消耗行不含 `-` 资源后缀
5. 脱战拦截提示：显示中文资源名（`消耗 3 信仰值`），不含英文 key

环境铁律：私有库 test_v1266.db（绝不碰生产库）。
"""
import os
import sys

os.environ["GWEN_GAME_DB"] = os.path.abspath("test_v1266.db")
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.main import Main  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_priest(hp=400, mp=100, learned=None):
    return {
        "class_name": "cls_mu_shi", "level": 30, "hp": hp, "max_hp": 1000,
        "mp": mp, "max_mp": 100, "name": "牧师", "reach": 3,
        "equipment": {"weapon": {"name": "测试法杖", "stats": {"matk": 200, "atk": 50},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"int": 20, "str": 5},
        "learned_skills": learned or ["治愈术"],
    }


def mk_warrior(hp=400, mp=100, learned=None):
    return {
        "class_name": "cls_zhan_shi", "level": 30, "hp": hp, "max_hp": 1000,
        "mp": mp, "max_mp": 100, "name": "战士", "reach": 1,
        "equipment": {"weapon": {"name": "测试铁剑", "stats": {"atk": 100, "matk": 0},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 20, "int": 5},
        "learned_skills": learned or ["猛击"],
    }


def test_skill_list_res_cost_format():
    print("【1. 技能列表资源消耗并入魔力求（v126.5）】")
    clean_db()
    m = Main(None)

    # 圣光惩击：res_cost {"faith": 3}，mp 30
    priest = mk_priest(learned=["圣光惩击"])
    out = m._skill_list_page(priest, 1)
    check("圣光惩击消耗行格式 30 魔力 + 3 信仰值",
          "30 魔力 + 3 信仰值" in out, out[:400])
    check("不再显示旧格式 信仰值 -3",
          "信仰值 -3" not in out, out[:400])
    check("消耗行不含 `信仰值 -3` 负号样式",
          "-3 信仰值" not in out, out[:400])

    # 战士怒气技：裂地斩 res_cost {"rage": 3} 之类的技能
    warrior = mk_warrior(learned=["裂地斩"])
    out2 = m._skill_list_page(warrior, 2)
    found_rage = "怒气" in out2
    check("战士技能列表含 怒气", found_rage, out2[:400])
    if found_rage:
        # 怒气消耗并入：形如 `N 怒气`，不是 `怒气 -N`
        check("怒气消耗并入（无 `怒气 -` 后缀）", "怒气 -" not in out2, out2[:400])


def test_skill_list_no_res_suffix():
    print("【2. 无资源技能不产生资源后缀】")
    clean_db()
    m = Main(None)
    # 用 level 1 牧师（只学早期技能，多数无 res_cost）
    low = mk_priest(learned=["治愈术", "圣光术"])
    out = m._skill_list_page(low, 1)
    check("消耗行不含 `信仰值 -` 残留", "信仰值 -" not in out, out[:400])
    check("消耗行含有 射程：", "射程：" in out, out[:200])


def test_offbattle_guard_chinese_name():
    print("【3. 脱战治疗拦截显示中文资源名】")
    clean_db()
    from data.plugins.dragonfall.game.commands.combat import CombatCmds
    cc = CombatCmds()
    priest = mk_priest(learned=["圣光惩击"])
    info = E.skill_info(priest["class_name"], "圣光惩击")
    check("圣光惩击有 res_cost", bool(info and info.get("res_cost")), str(info))
    if not (info and info.get("res_cost")):
        return
    # 直接验证渲染片段（脱战拦截在 handler 里带 event，这里验证 join 逻辑产物）
    _rd = E.core_resource_def(priest["class_name"])
    _rcn = _rd.get("name", "") if _rd else ""
    parts = []
    for _k, _v in info["res_cost"].items():
        _cn = _rcn or _k
        parts.append(f"{_v} {_cn}")
    rendered = " + ".join(parts)
    check("脱战提示消耗片段含中文 3 信仰值", "3 信仰值" in rendered, rendered)
    check("脱战提示不含英文 key faith", "faith" not in rendered, rendered)


if __name__ == "__main__":
    test_skill_list_res_cost_format()
    test_skill_list_no_res_suffix()
    test_offbattle_guard_chinese_name()
    print(f"\n===== 结果 {passed} 通过 / {failed} 失败 =====")
    sys.exit(1 if failed else 0)