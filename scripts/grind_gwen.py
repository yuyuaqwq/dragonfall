# -*- coding: utf-8 -*-
"""格温(main) 渡口自动练级驱动：仅驱动回环客户端，不改游戏代码。
刷到 Lv.28 即停；记录升级横幅/掉落/血线；血少或体力不足时回晨曦城住宿再回来。
"""
import subprocess
import sys
import time
import re
import os

IDENT = "main"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(SCRIPT_DIR, "gwen_grind_log.txt")

def send(cmd):
    r = subprocess.run(
        [sys.executable, "loopback_client.py", IDENT, cmd],
        cwd=SCRIPT_DIR, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    out = r.stdout or r.stderr
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"\n>>> {cmd}\n{out}\n")
    return out

def main():
    max_battles = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    battles = 0
    levelup_logged = False
    while battles < max_battles:
        out = send("探索")
        # 体力不足判断
        if "体力不足" in out or "体力" in out and "不足" in out:
            print("⚠️ 体力不足，回城住宿")
            print(send("返回 晨曦城"))
            print(send("住宿"))
            print(send("前往 渡口"))
            continue
        if "正在战斗中" in out:
            pass  # 继续战斗
        if "遭遇战斗" in out or "正在战斗中" in out or "袭来" in out or "遭遇" in out:
            battles += 1
            for i in range(15):
                m = re.search(r"你：❤️ (\d+)/(\d+)", out)
                if m:
                    hp = int(m.group(1))
                    if hp < 300:
                        print(f"⚠️ 血线过低({hp})，尝试逃跑回城")
                        out2 = send("逃跑")
                        print(out2)
                        if "逃跑成功" in out2 or "脱离了战斗" in out2 or "回到" in out2:
                            print(send("返回 晨曦城"))
                            print(send("住宿"))
                            print(send("前往 渡口"))
                            break
                # 技能起手（战吼/旋风斩在栏位），然后普攻
                if i == 0:
                    out = send("技能 旋风斩")
                else:
                    out = send("攻击")
                print(out)
                if "击败" in out and ("你击败了" in out or "🎉" in out):
                    # 战斗结束
                    break
            # 升级检测
            if "升级" in out or "Lv.28" in out:
                print("🎉🎉🎉 检测到升级横幅（已记录日志）🎉🎉🎉")
                levelup_logged = True
                # 记录升级后的属性
                print(send("属性"))
                print("=== 升级完成，停止刷怪 ===")
                break
        else:
            time.sleep(1)
        # 每场战斗后打印进度摘要
        m = re.findall(r"经验进度 (\d+)/(\d+)", out)
        if m:
            print(f"[进度] {m[-1][0]}/{m[-1][1]}")
        if levelup_logged:
            break
    print(f"=== 练级结束，共 {battles} 场战斗 ===")

if __name__ == "__main__":
    main()
