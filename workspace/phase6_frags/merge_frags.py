# -*- coding: utf-8 -*-
"""Phase 6 片段合并脚本（主 agent 专用）——把 workspace/phase6_frags/*.py 的 MERGE dict 合并进源数据文件。

用法: python workspace/phase6_frags/merge_frags.py
只做数据合并，不跑测试。合并前备份源文件到 workspace/phase6_frags/backup/
"""
import os, sys, importlib.util, shutil, re

ROOT = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall"
FRAGS = os.path.join(ROOT, "workspace", "phase6_frags")
BACKUP = os.path.join(FRAGS, "backup")

# 目标文件映射：MERGE 键 → (文件路径, dict 名, 是否在 dict 闭合前插入)
TARGETS = {
    "EQUIP_ROSTER": (os.path.join(ROOT, "game/data/equip_roster.py"), "EQUIP_ROSTER"),
    "SERIES_FIXED_AFFIX": (os.path.join(ROOT, "game/data/affixes.py"), "SERIES_FIXED_AFFIX"),
    "SERIES_SETS": (os.path.join(ROOT, "game/data/equip_roster.py"), "SERIES_SETS"),
    "EQ_SERIES_THEME": (os.path.join(ROOT, "game/data/equip_roster.py"), "_EQ_SERIES_THEME"),
    "MATERIALS": (os.path.join(ROOT, "game/data/items.py"), "MATERIALS"),
    "CRAFT_RECIPES": (os.path.join(ROOT, "game/data/craft.py"), "CRAFT_RECIPES"),
    "CLASS_SET_BONUS": (os.path.join(ROOT, "game/core/class_sets.py"), "_SERIES_SET_BONUS"),
}

def load_frags():
    """加载所有 frag_*.py 的 MERGE dict，返回合并后的 {键: {子键: 值}}。"""
    merged = {k: {} for k in TARGETS}
    frag_files = sorted(f for f in os.listdir(FRAGS) if f.startswith("frag_") and f.endswith(".py"))
    for fn in frag_files:
        path = os.path.join(FRAGS, fn)
        mod_name = fn[:-3]
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "MERGE"):
            print(f"⚠️ {fn}: 无 MERGE dict，跳过")
            continue
        for key, entries in mod.MERGE.items():
            if key not in merged:
                print(f"⚠️ {fn}: 未知键 {key}，跳过")
                continue
            if not isinstance(entries, dict):
                print(f"⚠️ {fn}: {key} 不是 dict，跳过")
                continue
            # 检查与已有内容的重名（含其他片段已合并的）
            dup = set(entries) & set(merged[key])
            if dup:
                print(f"⚠️ {fn}: {key} 重复键: {list(dup)[:5]}... 跳过重复")
                for d in dup:
                    entries.pop(d)
            merged[key].update(entries)
        print(f"✅ {fn}: 已加载")
    return merged

def _insert_into_dict(src: str, dict_name: str, entries: dict, header: str) -> str:
    """把 entries 插入 src 中 dict_name 的 dict 内部（最后一个条目后）。"""
    # 找到 dict_name = { 的位置
    pat = re.compile(rf"({dict_name}\s*=\s*\{{)")
    m = pat.search(src)
    if not m:
        raise RuntimeError(f"找不到 {dict_name}")
    start = m.end()
    # 从 start 开始找配对的大括号（跳过嵌套 dict）
    depth = 1
    i = start
    in_str = None
    while i < len(src) and depth > 0:
        ch = src[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
        else:
            if ch in "\"'":
                in_str = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        i += 1
    # i-1 是闭合 }
    close_pos = i - 1
    # 在闭合前插入
    indent = "    "
    lines = []
    for k, v in entries.items():
        # 简单 repr 序列化（键是字符串，值是 dict/list/str/int）
        lines.append(f"{indent}{k!r}: {v!r},")
    body = "\n".join(lines)
    insert = f"\n{header}\n{body}\n"
    return src[:close_pos] + insert + src[close_pos:]

def main():
    merged = load_frags()
    os.makedirs(BACKUP, exist_ok=True)
    for key, entries in merged.items():
        if not entries:
            continue
        path, dict_name = TARGETS[key]
        # 备份
        bak = os.path.join(BACKUP, os.path.basename(path) + f".{key}.bak")
        shutil.copy(path, bak)
        src = open(path, encoding="utf-8").read()
        header = f"    # ===== v136 Phase6 合并: {key} ({len(entries)} 条) ====="
        src = _insert_into_dict(src, dict_name, entries, header)
        open(path, "w", encoding="utf-8").write(src)
        print(f"✅ {os.path.basename(path)}: {dict_name} +{len(entries)} 条")

if __name__ == "__main__":
    main()
