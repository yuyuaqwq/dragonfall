# -*- coding: utf-8 -*-
"""多身份文件回环客户端：子 agent 走真实 AstrBot 链路的入口。

用法：
  python loopback_client.py <ident> <游戏指令>       # 发一条指令，等待结果并打印（自动处理单行长度）
  python loopback_client.py <ident> --tail <n>       # 只读该身份输出文件的最近 n 段，不发指令
  python loopback_client.py <ident> --clear          # 清空该身份输出文件

ident 示例：gm_alt1 / gm_alt2 / gm_alt3（仅 [A-Za-z0-9_-]）
主通道（gm_playtest）用 ident=main。
"""
import os
import re
import sys
import time

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
CMD_TMPL = os.path.join(SCRIPTS, "playthrough_cmd_{}.txt")
OUT_TMPL = os.path.join(SCRIPTS, "playthrough_out_{}.txt")
MAIN_CMD = os.path.join(SCRIPTS, "playthrough_cmd.txt")
MAIN_OUT = os.path.join(SCRIPTS, "playthrough_out.txt")


def _paths(ident):
    if ident == "main":
        return MAIN_CMD, MAIN_OUT
    if not re.fullmatch(r"[A-Za-z0-9_-]+", ident):
        sys.exit(f"❌ 非法 ident: {ident!r}（仅 [A-Za-z0-9_-]）")
    return CMD_TMPL.format(ident), OUT_TMPL.format(ident)


def _read_tail(path, n):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return ""
    parts = [p for p in text.split("\n=") if p.strip()]
    return "\n".join("=" + p for p in parts[-n:]) if n else text


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    ident = sys.argv[1]
    cmd_file, out_file = _paths(ident)

    if sys.argv[2] == "--tail":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        print(_read_tail(out_file, n) or f"（{ident} 暂无输出）")
        return
    if sys.argv[2] == "--clear":
        open(out_file, "w", encoding="utf-8").close()
        print(f"✅ {out_file} 已清空")
        return

    # 发指令：记录当前输出长度 → 写 cmd 文件 → 轮询等新输出
    try:
        with open(out_file, "r", encoding="utf-8") as f:
            base = len(f.read())
    except FileNotFoundError:
        base = 0
    cmd = " ".join(sys.argv[2:])
    with open(cmd_file, "w", encoding="utf-8") as f:
        f.write(cmd)
    deadline = time.time() + 40  # worker 1s 轮询，40s 兜底
    while time.time() < deadline:
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                text = f.read()
            if len(text) > base:
                print(text[base:].strip())
                return
        except FileNotFoundError:
            pass
        time.sleep(1.0)
    print(f"⏰ 超时未收到响应（指令：{cmd}）——检查 AstrBot 是否运行")


if __name__ == "__main__":
    main()
