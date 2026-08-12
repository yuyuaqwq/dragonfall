# -*- coding: utf-8 -*-
"""gm_alt4 自动练级辅助：银风驿站刷森林狼 → Lv.12。仅驱动回环客户端，不改游戏代码。"""
import subprocess
import sys
import time
import re

IDENT = "gm_alt4"
SCRIPT_DIR = __import__("os").path.dirname(__import__("os").path.abspath(__file__))

def send(cmd):
    r = subprocess.run(
        [sys.executable, "loopback_client.py", IDENT, cmd],
        cwd=SCRIPT_DIR, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    return r.stdout or r.stderr

def main():
    max_battles = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    battles = 0
    hp_low = 200
    while battles < max_battles:
        out = send("探索")
        print(out)
        if "遭遇战斗" in out:
            battles += 1
            # 战斗循环
            for i in range(12):
                # 血线检查：如果自己血量低于阈值且有逃跑选项，回城
                m = re.search(r"你：❤️ (\d+)/(\d+)", out)
                if m:
                    hp = int(m.group(1))
                    if hp < hp_low and "逃跑" in out:
                        print(f"⚠️ 血线过低({hp})，尝试逃跑回城")
                        out = send("逃跑")
                        print(out)
                        break
                # 技能起手（圣光术），然后普攻
                if i == 0:
                    out = send("技能 圣光术")
                else:
                    out = send("攻击")
                print(out)
                if "击败" in out or "你击败了" in out:
                    break
                if "升级" in out or "Lv.12" in out:
                    pass
            # 升级加点：检查自由属性点
            if "升级" in out:
                out2 = send("加点 智力 2")
                print(out2)
        else:
            time.sleep(1)
    print(f"=== 练级结束，共 {battles} 场战斗 ===")

if __name__ == "__main__":
    main()
