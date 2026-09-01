# -*- coding: utf-8 -*-
"""v157 技能 formula 自动生成脚本（一次生成，全量补齐 129 个伤害技能）

用法:
    python scripts/gen_skill_formulas.py [--apply]

原理:
    读取 skills_v153.py 当前生效的伤害技能（kind ∈ 物理/魔法/真伤），
    按"数值等价"规则自动生成 formula 字段：
      物理非穿透: [{"stat": "atk",  "mult": power, "type": "phys", "skill_flat": true}]
      物理穿透:   [{"stat": "atk",  "mult": power, "type": "phys", "pierce": true, "skill_flat": true}]
      魔法:       [{"stat": "matk", "mult": power, "type": "magi", "skill_flat": true}]
      真伤:       [{"stat": "atk",  "mult": power, "type": "true", "skill_flat": true}]
    skill_flat: true = 引擎注入 v156 基础值（×pmult，与非 formula 路径等价）
    pierce: true = 引擎绕过防御公式（resolve_formula 段级 pierce 支持，v157 新增）

    多段技能（hits≥2）：当前战斗 multi=1（hits 不读，已知 bug 单独修），
    formula 按当前行为写单段，不动数值。

    --apply 才写回文件；不加 --apply 只打印计划 + 校验。
"""
import json
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SKILLS_FILE = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills_v153.py"

# kind → (stat, type) 映射
# v158 修复：支持元素后缀 kind（魔法·火/冰/雷/暗…）——此前只认纯"魔法"，
# 漏了法师核心输出（火球术/陨石术/万象天雷等 13 个），补全。
# 召唤 kind（唤火/唤雷/召唤守卫…）本体无直接伤害但带 power，同样补 formula。
KIND_MAP = {
    "物理": ("atk", "phys"),
    "魔法": ("matk", "magi"),
    "真伤": ("atk", "true"),
    "召唤": ("atk", "phys"),
}


def kind_stat_type(kind: str) -> tuple | None:
    """按 kind 解析 (stat, type)。支持元素后缀：魔法·火/冰/雷/暗… → magi。"""
    if kind in KIND_MAP:
        return KIND_MAP[kind]
    if kind and kind.startswith("魔法"):
        return ("matk", "magi")
    if kind and kind.startswith("物理"):
        return ("atk", "phys")
    return None


def gen_formula(skill: dict) -> list:
    """按技能 dict 生成 formula 段（数值等价）。"""
    kind = skill.get("kind")
    st = kind_stat_type(kind)
    if st is None:
        return None
    stat, ftype = st
    power = float(skill.get("power", 1.0) or 1.0)
    seg = {"stat": stat, "mult": round(power, 4), "type": ftype}
    if skill.get("pierce") and kind != "真伤":
        seg["pierce"] = True
    seg["skill_flat"] = True
    return [seg]


def find_skill_block(src: str, key: str) -> tuple | None:
    """按 key（"sk_xxx" 或 中文名）定位技能块，返回 (start, end, block_text)。"""
    # 匹配 "key": { 或 'key': {（key 后直接 {）
    pat = re.compile(r'(["\']' + re.escape(key) + r'["\']\s*:\s*\{)')
    for m in pat.finditer(src):
        start = m.start(1)
        depth = 0
        i = src.index("{", start)
        j = i
        while j < len(src):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = src[i:j + 1]
        if "'lv':" in block and "'kind':" in block:
            return (start, j + 1, block)
    return None


def inject_formula(block_text: str, formula: list) -> str:
    """在技能块内插入 formula 字段（放在 'kind' 行之后）。"""
    # 手动构造 Python 单引号字面量（不用 json.dumps，避免 true/false 与字符串值混淆）
    parts = []
    for _seg in formula:
        _p = "{"
        for _k, _v in _seg.items():
            if isinstance(_v, bool):
                _vs = "True" if _v else "False"
            elif isinstance(_v, str):
                _vs = f"'{_v}'"
            else:
                _vs = repr(_v)
            _p += f"'{_k}': {_vs}, "
        _p = _p.rstrip(", ") + "}"
        parts.append(_p)
    fmt = "[" + ", ".join(parts) + "]"
    m = re.search(r"('kind':\s*'[^']*',)", block_text)
    if not m:
        return block_text
    insert_at = m.end(1)
    indent = "             "
    formula_line = f"\n{indent}'formula': {fmt},"
    return block_text[:insert_at] + formula_line + block_text[insert_at:]


def main():
    apply = "--apply" in sys.argv
    src = open(SKILLS_FILE, encoding="utf-8").read()

    # 用 import 拿当前生效技能（含 v153 覆盖），但只处理 v153 表里的 key
    import sys as _sys
    _sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins/dragonfall")
    from game.data.skills import PLAYER_SKILLS, BRANCH_SKILLS

    # 收集所有伤害技能（key + 技能 dict）——v158：kind_stat_type 支持元素后缀/召唤
    targets = {}  # key -> skill dict
    for cid, cinfo in PLAYER_SKILLS.items():
        sk = cinfo.get("skills") if isinstance(cinfo, dict) else cinfo
        for sid, s in (sk or {}).items():
            if kind_stat_type(s.get("kind")) is not None:
                targets[sid] = s
    for cid, cinfo in (BRANCH_SKILLS or {}).items():
        branches = cinfo.get("branches") if isinstance(cinfo, dict) else cinfo
        for bidx, (bkey, bsk) in enumerate(branches.items(), 1):
            if not isinstance(bsk, dict):
                continue
            for bname, bskills in bsk.items():
                if not isinstance(bskills, dict):
                    continue
                for sid, s in bskills.items():
                    if kind_stat_type(s.get("kind")) is not None:
                        targets[sid] = s

    print(f"目标伤害技能: {len(targets)}")
    plan = []
    missing = []
    for key, skill in targets.items():
        fml = gen_formula(skill)
        if fml is None:
            continue
        found = find_skill_block(src, key)
        if not found:
            missing.append(key)
            continue
        start, end, block = found
        plan.append((start, end, block, key, skill, fml))

    print(f"找到可 patch 的: {len(plan)}，未找到块: {len(missing)}")
    if missing:
        print("缺失 key:", missing[:20])

    for start, end, block, key, skill, fml in plan[:5]:
        print(f"  示例 {key}: {json.dumps(fml, ensure_ascii=False)}")

    if not apply:
        print("\n(未写回。加 --apply 写回文件)")
        return

    # 从后往前替换
    new_src = src
    done = 0
    for start, end, block, key, skill, fml in sorted(plan, key=lambda x: -x[0]):
        new_block = inject_formula(block, fml)
        if new_block != block:
            # 重新定位（前面替换可能改变位置，但 key 块文本不变，用 find 兜底）
            cur = new_src.find(block, 0)
            if cur >= 0:
                new_src = new_src[:cur] + new_block + new_src[cur + len(block):]
                done += 1

    open(SKILLS_FILE, "w", encoding="utf-8").write(new_src)
    print(f"\n已写回 {done} 个技能 formula")


if __name__ == "__main__":
    main()
