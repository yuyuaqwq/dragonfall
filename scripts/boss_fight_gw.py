#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格温视角海蚀洞窟 Boss 战自动推进 v2：等小红超时 -> 血量<450喝药否则攻击 -> 录击杀播报"""
import subprocess, sys, time, os, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(SCRIPT_DIR, "boss_fight_gw.log")

def run(args):
    r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "loopback_client.py"), "main"] + args,
                       capture_output=True, text=True, timeout=80, cwd=SCRIPT_DIR)
    return r.stdout

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def act(cmd):
    out = run([cmd])
    for line in out.splitlines():
        s = line.strip()
        if any(k in s for k in ["你挥剑", "造成", "剩余", "肃清", "🎉", "战败", "传出", "经验 +", "Boss", "海盗王", "掉落", "奖励", "回复", "升级", "生命上限", "攻击 +", "血量", "生命", "药水"]):
            log(f"  | {s}")
    return out

def main():
    log("=== Boss战自动推进 v2 开始 ===")
    potions = 18
    for cycle in range(90):
        t = run(["--tail", "4"])
        # 提取当前血量
        hp = None
        m = re.search(r"格温 剩余 (\d+)/", t)
        if m:
            hp = int(m.group(1))
        if "轮到你" in t or "自由出手" in t or "轮到 格温" in t:
            out = act("攻击")
            if any(k in out for k in ["肃清", "战败", "传出", "🎉", "通关"]):
                log(">>> 战斗结束标志出现")
                break
            continue
        if "现在是 小红" in t or "轮到 小红" in t:
            time.sleep(125)
            if hp is not None and hp < 450 and potions > 0:
                out = act("使用 治疗药水")
                potions -= 1
                log(f"  [药水剩余 {potions}]")
            else:
                out = act("攻击")
            if any(k in out for k in ["肃清", "战败", "传出", "🎉", "通关"]):
                log(">>> 战斗结束标志出现")
                break
            continue
        time.sleep(20)
    log("=== 循环结束 ===")
    print(run(["--tail", "6"]))

if __name__ == "__main__":
    main()
