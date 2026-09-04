# -*- coding: utf-8 -*-
"""v175 职业平衡矩阵 schema 落地：常量 + JSON 校验器。

职业 agent 产出 balance_data/cls_<职业>.json 后，用 validate() 校验：
  python -c "from build_matrix.schema import validate; print(validate('scripts/balance_data/cls_zhan_shi.json'))"
"""
from __future__ import annotations
import os, sys, json

_BM_DIR = os.path.dirname(os.path.abspath(__file__))                          # scripts/build_matrix/
_SCRIPTS = os.path.dirname(_BM_DIR)                                            # scripts/
_PLUGIN = os.path.dirname(_SCRIPTS)                                            # dragonfall/
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))            # qqbot/
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 职业/流派/资源（勿改，已核实）
KNOWN_CLASSES = {
    "cls_zhan_shi": "战士", "cls_fa_shi": "法师", "cls_you_xia": "游侠",
    "cls_mu_shi": "牧师", "cls_ci_ke": "刺客", "cls_wu_seng": "拳师",
    "cls_shi_ren": "吟游诗人",
}
RESOURCE_KEYS = {"rage": 10, "element": 5, "energy": 100, "faith": 10,
                 "cp": 5, "chi": 10, "resonance": 10, "echo": 3}
# 流派 role 取值
ROLES = ("dps", "tank", "heal", "support", "control")
# cond 支持语法（前缀匹配即可；期望引擎解释）
COND_PREFIXES = ("always", "cd_ready", "rage>=", "rage==", "cp>=", "cp==", "chi>=", "faith>=",
                 "energy>=", "resource_full", "resource_low", "enemy_hp_pct<", "buff_active:",
                 "combo_ready", "always_after:")
# 转职线名（tier1 分支，BUILDS 内技能同线）
BRANCH_LINES = {
    "cls_zhan_shi": ["狂战士", "盾卫士"],
    "cls_fa_shi": ["元素使", "奥术学者"],
    "cls_you_xia": ["森语者", "风行者"],
    "cls_mu_shi": ["神谕者", "死灵祭司"],
    "cls_ci_ke": ["影舞者", "毒刃者"],
    "cls_wu_seng": ["格斗士", "磐石行者"],
    "cls_shi_ren": ["咏叹者", "挽歌者"],
}


def skill_name_set(cls_id: str) -> set[str]:
    """该职业全部可引用技能名（base + branch，真实数据源）。"""
    from data.plugins.dragonfall.game.data import skills as SK
    names = set()
    cdef = SK.PLAYER_SKILLS.get(cls_id, {})
    for info in cdef.get("skills", {}).values():
        names.add(info.get("name", ""))
    br = SK.BRANCH_SKILLS.get(cls_id, {}).get("branches", {})
    for tier, tdef in br.items():
        if not isinstance(tdef, dict):
            continue
        for line, skills in tdef.items():
            if not isinstance(skills, dict):
                continue
            for info in skills.values():
                if isinstance(info, dict):
                    names.add(info.get("name", ""))
    names.discard("")
    return names


def validate(path: str) -> list[str]:
    """校验职业 JSON，返回错误清单（空 = 通过）。"""
    errs = []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    cid = data.get("class_id", "")
    if cid not in KNOWN_CLASSES:
        errs.append(f"class_id 未知: {cid}")
        return errs
    if data.get("class_name") != KNOWN_CLASSES[cid]:
        errs.append(f"class_name 应为 {KNOWN_CLASSES[cid]}")
    # 资源
    res = data.get("resource", "")
    if res not in RESOURCE_KEYS:
        errs.append(f"resource 未知: {res}（可用 {list(RESOURCE_KEYS)}）")
    else:
        if int(data.get("resource_max", 0)) != RESOURCE_KEYS[res]:
            errs.append(f"resource_max 应为 {RESOURCE_KEYS[res]}")
    # 流派
    names = skill_name_set(cid)
    builds = data.get("builds", {})
    if not isinstance(builds, dict) or len(builds) != 3:
        errs.append(f"builds 必须 3 个流派（当前 {len(builds) if isinstance(builds, dict) else 0}）")
    # 与 BUILDS 键对齐
    from data.plugins.dragonfall.game.data import builds as BD
    expected_builds = set(BD.BUILDS.get(cid, {}).keys())
    got_builds = set(builds.keys())
    if got_builds != expected_builds:
        errs.append(f"builds 键应={expected_builds} 实={got_builds}")
    for bname, bdef in builds.items():
        if not isinstance(bdef, dict):
            errs.append(f"builds.{bname} 非 dict")
            continue
        if bdef.get("role") not in ROLES:
            errs.append(f"builds.{bname}.role 应为 {ROLES} 之一，实={bdef.get('role')}")
        # 检查同技能重复定义（会导致期望引擎规则冲突）
        seen_skills = {}
        for i, step in enumerate(bdef.get("rotation", [])):
            if not isinstance(step, dict) or "skill" not in step:
                errs.append(f"builds.{bname}.rotation[{i}] 需含 skill")
                continue
            sk = step["skill"]
            if sk not in names:
                errs.append(f"builds.{bname}.rotation[{i}] 技能名不存在: {sk}")
            cond = step.get("cond", "always")
            if not any(cond.startswith(p) for p in COND_PREFIXES):
                errs.append(f"builds.{bname}.rotation[{i}] cond 语法不支持: {cond}")
            if "prio" not in step:
                errs.append(f"builds.{bname}.rotation[{i}] 缺 prio")
            if sk in seen_skills:
                errs.append(f"builds.{bname}.rotation[{i}] 技能 '{sk}' 重复定义"
                            f"（首次在 rotation[{seen_skills[sk]}]）——同一技能多规则请合并为一条 cond 用 or 语义")
            seen_skills[sk] = i
    # 加点预设
    attr_presets = data.get("attr_presets", {})
    if not isinstance(attr_presets, dict) or len(attr_presets) < 2:
        errs.append(f"attr_presets 至少 2 套（当前 {len(attr_presets) if isinstance(attr_presets, dict) else 0}）")
    return errs


if __name__ == "__main__":
    import glob
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          "..", "balance_data", "cls_*.json")))
    if not paths:
        print("未找到任何 balance_data/cls_*.json（职业 agent 尚未产出）")
        sys.exit(0)
    bad = 0
    for p in paths:
        errs = validate(p)
        if errs:
            bad += 1
            print(f"❌ {p}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"✅ {p}")
    sys.exit(1 if bad else 0)
