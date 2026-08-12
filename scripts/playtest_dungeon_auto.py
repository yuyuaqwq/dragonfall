#!/usr/bin/env python3
"""海蚀洞窟组队副本自动推进脚本（格温视角，配合小红自动防御超时机制）"""
import subprocess, sys, time, re, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(SCRIPT_DIR, "dungeon_auto.log")

def run(args):
    r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "loopback_client.py"), "main"] + args,
                       capture_output=True, text=True, timeout=60, cwd=SCRIPT_DIR)
    return r.stdout

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def act(cmd):
    out = run([cmd])
    log(f"指令[{cmd}] -> {out[-200:].strip()}")
    return out

def tail(n=3):
    return run(["--tail", str(n)])

def main():
    log("=== 自动推进开始 ===")
    idle_since = time.time()
    in_battle = False
    last_tail = ""
    for cycle in range(120):
        t = tail(3)
        # 提取最新战斗状态行
        key = ""
        for line in t.splitlines():
            if "轮到" in line or "肃清" in line or "深入" in line or "🎉" in line or "通关" in line or "传出" in line or "自由出手" in line or "你挥剑" in line or "经验 +" in line or "Boss" in line or "海盗王" in line:
                key = line.strip()
        if key != last_tail:
            log(f"状态: {key}")
            last_tail = key
        if "轮到 格温" in t or "自由出手" in t:
            # 我的回合：血量低先用药，否则攻击
            if "血量" in t:
                pass
            out = act("攻击")
            idle_since = time.time()
            # 若击杀出现肃清
            if "肃清" in out or "可以『深入』" in out:
                time.sleep(2)
                act("深入")
                idle_since = time.time()
            continue
        if "轮到 小红" in t or "现在是 小红" in t:
            # 小红不活跃，超时后发攻击触发
            if time.time() - idle_since > 125:
                out = act("攻击")
                idle_since = time.time()
                if "肃清" in out or "可以『深入』" in out:
                    time.sleep(2)
                    act("深入")
                    idle_since = time.time()
                continue
            time.sleep(20)
            continue
        if "🎉" in t:
            log("=== 检测到 🎉 击杀播报！===")
            act("副本")
            return
        if "通关" in t or "传出" in t:
            log("=== 检测到通关/传出 ===")
            act("副本")
            return
        # 其他情况（战斗结算/无状态）
        time.sleep(15)
    log("=== 循环结束（120轮）===")

if __name__ == "__main__":
    main()
