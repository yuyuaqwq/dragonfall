# -*- coding: utf-8 -*-
"""v157 怪物技能 formula 自动生成脚本（143 个伤害技能）

用法:
    python scripts/gen_monster_formulas.py [--apply]

原理:
    读取 game/data/monsters.py MONSTER_SKILLS 中 kind ∈ 物理/魔法 的伤害技能，
    按数值等价规则生成 formula：
      物理: [{"stat": "atk",  "mult": power, "type": "phys"}]
      魔法: [{"stat": "matk", "mult": power, "type": "magi"}]
    敌方无 skill_flat 概念（_hostile_cast_done 不注入基础值），故不带 skill_flat。
    有 mech 控制/元素字段的技能照常保留原字段，formula 只描述伤害段。

    --apply 才写回；不加 --apply 只打印计划。
"""
import json
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MONSTERS_FILE = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/monsters.py"

KIND_MAP = {
    "物理": ("atk", "phys"),
    "魔法": ("matk", "magi"),
}


def gen_formula(skill: dict) -> list:
    kind = skill.get("kind")
    if kind not in KIND_MAP:
        return None
    stat, ftype = KIND_MAP[kind]
    power = float(skill.get("power", 1.0) or 1.0)
    return [{"stat": stat, "mult": round(power, 4), "type": ftype}]


def find_skill_block(src: str, key: str) -> tuple | None:
    """按 key（ms_xxx）定位技能块。"""
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
        if '"kind"' in block or "'kind'" in block:
            return (start, j + 1, block)
    return None


def inject_formula(block_text: str, formula: list) -> str:
    """在技能块内插入 formula 字段（放在 'kind' 行之后）。"""
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
    # monsters.py 用双引号风格（"kind": "魔法"）
    m = re.search(r'("kind":\s*"[^"]*",)', block_text)
    if not m:
        return block_text
    insert_at = m.end(1)
    indent = "        "
    formula_line = f"\n{indent}\"formula\": {fmt},"
    return block_text[:insert_at] + formula_line + block_text[insert_at:]


def main():
    apply = "--apply" in sys.argv
    src = open(MONSTERS_FILE, encoding="utf-8").read()

    import sys as _sys
    _sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins/dragonfall")
    from game.data.monsters import MONSTER_SKILLS

    plan = []
    missing = []
    for key, skill in MONSTER_SKILLS.items():
        fml = gen_formula(skill)
        if fml is None:
            continue
        found = find_skill_block(src, key)
        if not found:
            missing.append(key)
            continue
        start, end, block = found
        plan.append((start, end, block, key, skill, fml))

    print(f"怪物伤害技能: {len(plan)}，未找到块: {len(missing)}")
    if missing:
        print("缺失:", missing[:20])

    for start, end, block, key, skill, fml in plan[:3]:
        print(f"  示例 {key}: {json.dumps(fml, ensure_ascii=False)}")

    if not apply:
        print("\n(未写回。加 --apply 写回文件)")
        return

    new_src = src
    done = 0
    for start, end, block, key, skill, fml in sorted(plan, key=lambda x: -x[0]):
        new_block = inject_formula(block, fml)
        if new_block != block:
            cur = new_src.find(block, 0)
            if cur >= 0:
                new_src = new_src[:cur] + new_block + new_src[cur + len(block):]
                done += 1

    open(MONSTERS_FILE, "w", encoding="utf-8").write(new_src)
    print(f"\n已写回 {done} 个怪物技能 formula")


if __name__ == "__main__":
    main()
