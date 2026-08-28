# -*- coding: utf-8 -*-
"""v133 峰值红线门禁：单技能峰值 ≤ 同级怪血量 40%（L30+ 稳态截面）。

口径（与 scripts/burst_scan.py 一致）：
  玩家：主属性全投、技能 lv3、种族 human、裸装、tier 按等级自动
  目标：dps 普通怪（build_monster 真实血量），25 seeds Battle 采样取峰值
  断言：naked/diff0 下 L30/50/70 全部攻击技能 peak_pct ≤ 42
        （42 = 40 红线 + 采样波动与实现余量 2%，防止随机 flake）
  低等级段（L10-20）超限为新手期设计状态（怪血曲线 ≤15 级无 stage 放大），
  记档于 docs/BURST_REDLINE_v133.md，不在本门禁断言（防止未来失控可另立软上限）。

基线（2026-08-28 收敛后实测，L30+ 全部 ≤40%）：
  - 引擎规则：幸运一击 1.5→1.3（LUCKY_CRIT_MULT）、多段仅首段暴击（MULTI_HIT_CRIT_FIRST_ONLY）
  - 基础技能 17 个 power 收敛 / 分支技能 31 个 power 收敛
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins")

BUILD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BUILD, "scripts"))
from burst_scan import peak_of  # noqa: E402

CLS = ["cls_ci_ke", "cls_zhan_shi", "cls_you_xia", "cls_fa_shi", "cls_mu_shi", "cls_wu_seng"]
LVS = [30, 50, 70]
REDLINE = 42.0  # 40% 红线 + 2% 采样/实现余量


def test_burst_redline_all_classes():
    """全职业 L30+ 稳态截面：所有攻击技能峰值 ≤42% 同级怪血。"""
    fails = []
    for cls in CLS:
        for lv in LVS:
            rows = peak_of(cls, lv, "naked", 0)
            for name, dmg, hp, tlv in rows:
                pct = dmg * 100.0 / max(hp, 1)
                if pct > REDLINE:
                    fails.append(f"{cls} L{lv} {name}: {pct:.1f}% > {REDLINE}% (dmg={dmg}, hp={hp})")
    assert not fails, "峰值红线超限:\n" + "\n".join(fails)


def test_burst_redline_stealth_assassin():
    """刺客潜行路径（必暴窗口）红线复核：L30+ 双刃乱舞/暗杀/暗影处刑 ≤42%。"""
    fails = []
    for lv in LVS:
        rows = peak_of("cls_ci_ke", lv, "naked", 0)
        for name, dmg, hp, tlv in rows:
            if name in ("双刃乱舞", "暗杀", "暗影处刑"):
                pct = dmg * 100.0 / max(hp, 1)
                if pct > REDLINE:
                    fails.append(f"L{lv} {name}: {pct:.1f}% > {REDLINE}%")
    assert not fails, "刺客潜行路径超限:\n" + "\n".join(fails)


def test_burst_redline_branch_skills():
    """分支技能（转职线）红线复核：L40/60/80 攻击技能 ≤42%。"""
    fails = []
    for cls in CLS:
        for lv in (40, 60, 80):
            rows = peak_of(cls, lv, "naked", 0, branch=True)
            for name, dmg, hp, tlv in rows:
                pct = dmg * 100.0 / max(hp, 1)
                if pct > REDLINE:
                    fails.append(f"{cls} L{lv} {name}: {pct:.1f}% > {REDLINE}%")
    assert not fails, "分支技能超限:\n" + "\n".join(fails)


if __name__ == "__main__":
    import traceback
    for fn in (test_burst_redline_all_classes, test_burst_redline_stealth_assassin,
               test_burst_redline_branch_skills):
        try:
            fn()
            print(f"✅ {fn.__name__}")
        except AssertionError as e:
            print(f"❌ {fn.__name__}\n{e}")
            sys.exit(1)
    print("峰值红线门禁全部通过")