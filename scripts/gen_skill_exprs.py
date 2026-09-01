# -*- coding: utf-8 -*-
"""v161 技能 exprs 表达式自动生成脚本（样板：战士 + 法师伤害技能）

用法:
    python scripts/gen_skill_exprs.py [--apply]

原理:
    读取 skills_v153.py 中指定职业的伤害技能（kind ∈ 物理/魔法/真伤），
    按"数值等价"规则生成 exprs 表达式（单条 expr + skill_lv 变量，自动表达成长曲线）：

      表达式 = 主攻属性×(power×(1+p/100×(skill_lv-1))) + player_lv + 12 + skill_lv×2

    其中 p = SKILL_UP[技能名].p（每级成长%），与旧公式
      base = atk/matk×power×skill_power_mult(lv) + skill_flat_value(player_lv, lv)
    完全等价（verify_v161_expr_equiv.py 验证）。

    --apply 才写回文件；不加 --apply 只打印计划 + 校验。

    ⚠️ 样板阶段：只给指定职业的伤害技能加 exprs，不删 power/formula（单轨删除在
    样板验证后铺开——涉及 battle.py 非 formula 路径改造，属后续批次）。
"""
import json
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SKILLS_FILE = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/skills.py"

# 样板职业（鱼鱼拍板：战士 + 法师）
SAMPLE_CLASSES = {"cls_zhan_shi", "cls_fa_shi"}

# 主攻属性
STAT_BY_KIND = {
    "物理": "atk", "真伤": "atk",
    "魔法": "matk",
}


def kind_stat(kind: str) -> str | None:
    """按 kind 解析主攻属性（支持元素后缀：魔法·火/冰/雷 → matk）。"""
    if kind in STAT_BY_KIND:
        return STAT_BY_KIND[kind]
    if kind and kind.startswith("魔法"):
        return "matk"
    if kind and kind.startswith("物理"):
        return "atk"
    return None


def build_expr(stat: str, power: float, p: float) -> str:
    """构造等价表达式（单条 expr + skill_lv 变量）。"""
    def _fmt(x):
        return str(int(x)) if float(x).is_integer() else repr(round(float(x), 4))
    return (f"{stat}*({_fmt(power)}*(1+{_fmt(p)}/100*(skill_lv-1)))"
            f" + player_lv + 12 + skill_lv*2")


# v161 LOL 式设计表 → scripts/v161_design_table.py（每技能独立 base/ratio，按特色设计）
#   每技能: (base_flat, per_player_lv, per_skill_lv, ratio, 定位, 特色)
#   expr = 属性×ratio + base_flat + player_lv×per_player_lv + skill_lv×per_skill_lv


def build_expr_lol(stat: str, skill_name: str) -> str:
    """v161 LOL 式表达式：属性×ratio + base + player_lv×per_plv + skill_lv×per_slv。

    V161_DESIGN 从 scripts/v161_design_table.py 导入（每技能独立 base/ratio 设计）。
    """
    from scripts.v161_design_table import V161_DESIGN  # noqa
    d = V161_DESIGN.get(skill_name)
    if not d:
        return None
    base_flat, per_plv, per_slv, ratio, _pos, *_ = d
    def _fmt(x):
        return str(int(x)) if float(x).is_integer() else repr(round(float(x), 4))
    return (f"{stat}*{_fmt(ratio)} + {_fmt(base_flat)}"
            f" + player_lv*{_fmt(per_plv)} + skill_lv*{_fmt(per_slv)}")


def find_skill_block(src: str, key: str) -> tuple | None:
    """按 key（"sk_xxx" 或 中文名）定位技能块，返回 (start, end, block_text)。"""
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


def inject_expr(block_text: str, expr: str) -> str:
    """在技能块内插入/替换 exprs 字段（放在 'formula' 行之前）。

    v161：块内已有任意 exprs 字段时全部替换为一条新值（源文件有重复 formula
    导致旧生成可能产生多行 exprs，后写的覆盖先写的 → 必须清掉所有旧 exprs）；
    没有则插入一条。
    """
    fmt = f"'{expr}'"
    # 已有 exprs 字段 → 全部替换为一条新值
    if "'exprs':" in block_text:
        # 用行级处理：删掉所有 exprs 行，再在 formula 前插一条
        lines = block_text.split("\n")
        kept = [ln for ln in lines if "'exprs':" not in ln]
        block_text = "\n".join(kept)
        # 重新定位 formula/kind 插入点
        m = re.search(r"('formula':\s*\[)", block_text)
        if not m:
            m = re.search(r"('kind':\s*'[^']*',)", block_text)
            if not m:
                return block_text
            insert_at = m.end(1)
        else:
            insert_at = m.start(1)
        indent = "             "
        expr_line = f"\n{indent}'exprs': [{fmt}],"
        return block_text[:insert_at] + expr_line + block_text[insert_at:]
    m = re.search(r"('formula':\s*\[)", block_text)
    if not m:
        m = re.search(r"('kind':\s*'[^']*',)", block_text)
        if not m:
            return block_text
        insert_at = m.end(1)
    else:
        insert_at = m.start(1)
    indent = "             "
    expr_line = f"\n{indent}'exprs': [{fmt}],"
    return block_text[:insert_at] + expr_line + block_text[insert_at:]


def main():
    apply = "--apply" in sys.argv
    src = open(SKILLS_FILE, encoding="utf-8").read()

    import sys as _sys
    _sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins/dragonfall")
    from game.data.skills import PLAYER_SKILLS
    from game import content as C
    # v161 全量设计表（每技能独立 base/ratio）
    from scripts.v161_design_table import V161_DESIGN  # noqa

    targets = {}  # key -> (skill dict, expr)
    for cid, cinfo in PLAYER_SKILLS.items():
        sk = cinfo.get("skills") if isinstance(cinfo, dict) else cinfo
        for sid, s in (sk or {}).items():
            stat = kind_stat(s.get("kind"))
            if stat is None:
                continue
            sname = s.get("name", "")
            # v161 LOL 式：技能名在设计表 → 用 LOL 模板；否则回退旧公式展开
            expr = build_expr_lol(stat, sname)
            if expr is None:
                power = float(s.get("power", 1.0) or 1.0)
                up = C.SKILL_UP.get(sname, {})
                p = float(up.get("p", 10) or 10)  # 默认每级+10%（SKILL_POWER_PER_LV）
                expr = build_expr(stat, round(power, 4), p)
            targets[sid] = (s, expr)

    # v161 分支技能（BRANCH_SKILLS，branches = {tier: {分支名: {技能表}}}）
    for cid, cinfo in (C.BRANCH_SKILLS or {}).items():
        branches = cinfo.get("branches") if isinstance(cinfo, dict) else cinfo
        for bidx, branches_of_tier in (branches or {}).items():
            if not isinstance(branches_of_tier, dict):
                continue
            for bname, bskills in branches_of_tier.items():
                if not isinstance(bskills, dict):
                    continue
                for sid, s in bskills.items():
                    stat = kind_stat(s.get("kind"))
                    if stat is None:
                        continue
                    sname = s.get("name", sid)
                    expr = build_expr_lol(stat, sname)
                    if expr is None:
                        power = float(s.get("power", 1.0) or 1.0)
                        up = C.SKILL_UP.get(sname, {})
                        p = float(up.get("p", 10) or 10)
                        expr = build_expr(stat, round(power, 4), p)
                    targets[sid] = (s, expr)

    print(f"伤害技能: {len(targets)}")
    plan = []
    missing = []
    for key, (skill, expr) in targets.items():
        found = find_skill_block(src, key)
        if not found:
            missing.append(key)
            continue
        start, end, block = found
        plan.append((start, end, block, key, expr))

    print(f"找到可 patch 的: {len(plan)}，未找到块: {len(missing)}")
    if missing:
        print("缺失 key:", missing[:20])

    for start, end, block, key, expr in plan[:5]:
        print(f"  示例 {key}: {expr}")

    if not apply:
        print("\n(未写回。加 --apply 写回文件)")
        return

    new_src = src
    done = 0
    for start, end, block, key, expr in sorted(plan, key=lambda x: -x[0]):
        new_block = inject_expr(block, expr)
        if new_block != block:
            cur = new_src.find(block, 0)
            if cur >= 0:
                new_src = new_src[:cur] + new_block + new_src[cur + len(block):]
                done += 1

    open(SKILLS_FILE, "w", encoding="utf-8").write(new_src)
    print(f"\n已写回 {done} 个技能 exprs")


if __name__ == "__main__":
    main()
