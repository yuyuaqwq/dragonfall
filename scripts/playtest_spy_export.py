# -*- coding: utf-8 -*-
"""playtest 本轮交互记录导出（窥探功能，2026-08-12 鱼鱼要求）。

在 playtest 轮次收尾（第 5 步）运行：把 6 个角色 playthrough_out_<ident>.txt 的
本轮新增交互（指令→回复）精华导出到 scripts/playtest_spy_round{N}.md，
由 playtest_spy_forward.py（cron no_agent job）检测到后私聊转发给鱼鱼。

幂等：按文件字节偏移做增量导出，同一轮重复跑不会重复导出。

用法：
  python playtest_spy_export.py [轮次号]   # 省略时从 playtest_loop_state.json 的 next_round-1 推断
  python playtest_spy_export.py --mark [轮次号]  # 只记录当前文件偏移（本轮起点标记），不导出
"""
import json
import os
import re
import sys

# ⚠️ Windows 非 UTF-8 终端下 emoji 输出会 UnicodeEncodeError（同 forward 脚本坑），强制 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPTS, "playtest_loop_state.json")
EXPORT_STATE = os.path.join(SCRIPTS, ".spy_export_state.json")
GITIGNORE = os.path.join(os.path.dirname(SCRIPTS), ".gitignore")

OUT_TMPL = os.path.join(SCRIPTS, "playtest_spy_round{}.md")

MAX_SEG_PER_ROLE = 30      # 每角色最多保留多少段（取最新）。v101.29c：原 12 太保守，
                           # 一轮实际交互 8-30+ 段，12 会截掉大半；gm_窥探 端有 5000 字/卡兜底防 ARK
MAX_CHARS_PER_SEG = 350    # 每段回复最多保留多少字
HEADER_FOOTER = 300        # 前后文保留长度（识别指令段用）


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def role_names():
    """从 playtest_loop_state.json 的 roles 提取 ident -> 角色名（如 小蓝）"""
    st = load_json(STATE_FILE, {})
    roles = st.get("roles", {})
    names = {}
    for ident, desc in roles.items():
        m = re.match(r"^([^(（]+)", desc or "")
        names[ident] = m.group(1).strip() if m else ident
    return names


def out_path(ident):
    if ident == "main":
        return os.path.join(SCRIPTS, "playthrough_out.txt")
    return os.path.join(SCRIPTS, "playthrough_out_{}.txt".format(ident))


def split_segments(text):
    """按 ▶ 段切分（与 loopback_client 同款分隔符），返回 [(指令行, 回复体)]"""
    segs = []
    for part in re.split(r"\n={8,}\n", text):
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        cmd = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        if cmd.startswith("▶"):
            segs.append((cmd, body))
    return segs


def clip_body(body, limit):
    if len(body) <= limit:
        return body
    return body[:limit] + "\n…(已截断)"


def ensure_gitignore():
    """playtest_spy_round*.md / .spy_*_state.json 是运行产物，不提交 git"""
    try:
        with open(GITIGNORE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
    additions = []
    if "playtest_spy_round" not in content:
        additions.append("scripts/playtest_spy_round*.md")
    if ".spy_export_state" not in content and ".spy_forward_state" not in content:
        additions.append("scripts/.spy_*_state.json")
    if additions:
        with open(GITIGNORE, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(additions) + "\n")
        print("  · .gitignore 已追加: {}".format(", ".join(additions)))


def main():
    mark_only = False
    round_no = None
    args = [a for a in sys.argv[1:] if a != "--mark"]
    if "--mark" in sys.argv[1:]:
        mark_only = True
    if args:
        round_no = int(args[0])
    else:
        st = load_json(STATE_FILE, {})
        round_no = int(st.get("next_round", 1)) - 1

    st = load_json(STATE_FILE, {})
    idents = st.get("idents", ["main", "gm_alt1", "gm_alt2", "gm_alt3", "gm_alt4", "gm_alt5"])
    names = role_names()

    est = load_json(EXPORT_STATE, {"offsets": {}, "round": 0})
    offsets = est.get("offsets", {})
    prev_round = int(est.get("round", 0))

    # 轮次回退保护：导出轮次小于上次 → 视为状态错乱，重置偏移（全量当新增）
    if round_no < prev_round:
        print("⚠️ 导出轮次 {} < 上次 {}，重置偏移全量导出".format(round_no, prev_round))
        offsets = {}

    # --mark：只记录当前偏移作为本轮起点（轮初调用，轮末导出即严格本轮内容）
    if mark_only:
        for ident in idents:
            path = out_path(ident)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    offsets[ident] = len(f.read())
            except FileNotFoundError:
                offsets[ident] = 0
        save_json(EXPORT_STATE, {"offsets": offsets, "round": round_no})
        print("📌 已标记第 {} 轮起点（6 角色偏移已记录）".format(round_no))
        return

    sections = []
    total_segs = 0
    for ident in idents:
        path = out_path(ident)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            continue
        base = int(offsets.get(ident, 0))
        if len(text) < base:
            # 文件被 --clear 过：全量视为本轮新增
            base = 0
        new_text = text[base:]
        offsets[ident] = len(text)

        segs = split_segments(new_text)
        if not segs:
            continue
        segs = segs[-MAX_SEG_PER_ROLE:]
        total_segs += len(segs)

        lines = ["## 🧵 {} ({})".format(names.get(ident, ident), ident)]
        for cmd, body in segs:
            lines.append("")
            lines.append(cmd)
            if body:
                lines.append(clip_body(body, MAX_CHARS_PER_SEG))
        lines.append("")
        lines.append("> 共 {} 段 · 完整记录见 scripts/playthrough_out_{}.txt".format(len(segs), ident))
        sections.append("\n".join(lines))

    if not sections:
        print("（无新增交互，跳过导出）")
        return

    out_path_file = OUT_TMPL.format(round_no)
    header = "# Playtest 第 {} 轮 · 角色交互实录\n\n> 自动导出（playtest_spy_export.py），运行产物不提交 git\n".format(round_no)
    with open(out_path_file, "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(sections) + "\n")

    save_json(EXPORT_STATE, {"offsets": offsets, "round": round_no})
    ensure_gitignore()
    print("✅ 已导出第 {} 轮交互实录：{}（{} 个角色，{} 段）".format(round_no, out_path_file, len(sections), total_segs))


if __name__ == "__main__":
    main()
