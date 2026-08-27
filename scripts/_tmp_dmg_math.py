# -*- coding: utf-8 -*-
"""《奥兰迪亚》伤害公式 dmg = atk²/(atk+def) —— 跨级失衡放大机制 数学分析（只读，不改源码）

真实引擎口径：
  game.engine.calc_damage(atk, def_, is_crit, variance=0.15, pene_pct, ...)
    dmg = atk*atk/(atk+def)；暴击 ×1.5（引擎内部）；波动 ±15%（均匀）；下限 1。
  玩家面板：engine.player_final_stats(class, level, equipment={}, ...) —— 裸装。
  怪物构建：core.drops.build_monster((mid,name,role,lv,skills,drops), map_obj)。

分析内容：
  ① 11 级战士/刺客 裸装普攻 → 11/13/16 级 DPS 型普通怪：单发期望伤害、怪物血量、击杀回合数；
  ② 同场景怪物 → 玩家：单发伤害期望、玩家血量、承伤回合数；
  ③ atk/def 比值 1/2/3/4/6（附 0.5/10 上下文）下公式伤害与等效缩减率表（含数学推导）；
  ④ 暴击（基础 5%~10%，战士实值 5%、刺客实值 20%，爆伤 ×1.5）对期望伤害的提升；
  ⑤ 结论：攻防差多大时公式开始"崩坏"，并用 11v16 实例佐证。
"""
import sys
import math
import random

sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")

from game import engine as E
from game.core.drops import build_monster

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MAP = {"id": "ana", "name": "评测平原", "area": "ana"}
MON_ID = "m_ana_dps"  # 不在 MONSTER_MODS 表内 → 无个体修正，纯粹普通怪模板
MON_ROLE = "dps"      # 野外最常见普通怪模板（攻高血薄）
# DPS 模板自带 5% 物穿（stat_templates.py MONSTER_ROLE_BASE["dps"]["pene_phys"]=0.05）。
# 注意：build_monster 返回体不含 pene_phys 键（战斗侧另有通道取模板值），这里直接取模板权威值。
MON_PENE = 0.05

# ---------------- 真实引擎蒙特卡洛：单发伤害期望（含波动/暴击/穿透） ----------------
def mc_expect(atk, def_, crit_rate=0.0, pene_pct=0.0, n=150000, seed=7):
    """用真实 E.calc_damage 求【含暴击+波动的单发期望】。calc_damage 内部消费模块级 random，
    先固化模块种子保证可复现；暴击判定用独立 rng 防耦合。"""
    random.seed(seed)
    rng = random.Random(seed + 1)
    tot = 0
    for _ in range(n):
        crit = rng.random() < crit_rate
        tot += E.calc_damage(atk, def_, is_crit=crit, pene_pct=pene_pct)
    return tot / n


def exact_bounds(atk, def_, crit_rate=0.0, pene_pct=0.0):
    """按引擎结算链解析求单发最小/最大：
       base=int(atk²/(atk+def_eff)) → int(base*(1±0.15)) → (暴击 int(·*1.5)) → max(1,·)"""
    eff_def = max(0, int(def_ * (1 - pene_pct))) if pene_pct > 0 else def_
    base = int(atk * atk / (atk + eff_def)) if atk + eff_def > 0 else 1
    lo = max(1, int(base * 0.85))
    hi = max(1, int(base * 1.15))
    if crit_rate > 0:
        lo_c = max(1, int(int(base * 0.85) * 1.5))
        hi_c = max(1, int(int(base * 1.15) * 1.5))
        # 混合暴击后的区间 = 普通段 ∪ 暴击段
        lo, hi = min(lo, lo_c), max(hi, hi_c)
    return lo, hi


def build_mon(lv):
    """构建 lv 级 DPS 普通怪（build_monster 真实路径）"""
    return build_monster((MON_ID, "普通怪·试", MON_ROLE, lv, (), ()), MAP)


PROFILES = [
    {"name": "战士", "cls": "战士"},
    {"name": "刺客", "cls": "刺客"},
]

LVS = [11, 13, 16]

# ==================== 玩家面板（裸装 11 级） ====================
players = {}
for p in PROFILES:
    st = E.player_final_stats(p["cls"], 11, {})
    players[p["name"]] = st

# ==================== ① 玩家 → 怪物 ====================
print("## ① 11级玩家裸装普攻 → 11/13/16级普通怪（DPS型）：击杀回合数\n")
print("| 职业 | 怪等级 | 玩家atk | 怪def | 攻防比 | 单发期望 | 单发区间 | 怪物HP | 击杀回合(期望) | 击杀回合(区间) |")
print("|------|-------:|-------:|------:|-------:|--------:|---------|-------:|---------------:|----------------|")

sec1 = []
for p in PROFILES:
    pn, st = p["name"], players[p["name"]]
    for lv in LVS:
        m = build_mon(lv)
        atk, df, hp = st["atk"], m["def"], m["hp"]
        cr = st.get("crit", 0.0)
        ex = mc_expect(atk, df, crit_rate=cr)
        lo, hi = exact_bounds(atk, df, crit_rate=cr)
        k_exp = math.ceil(hp / ex)
        k_lo = math.ceil(hp / hi)
        k_hi = math.ceil(hp / lo)
        print(f"| {pn} | {lv} | {atk} | {df} | {atk/df:.2f} | {ex:.2f} | {lo}~{hi} | {hp} | **{k_exp}** | {k_lo}~{k_hi} |")
        sec1.append((pn, lv, ex, hp, k_exp, atk / df))

# 注：刺客自带 10% 物穿（职业天生，classes.py），若按真实战斗路径计入，单发期望约 +5%
# （11v16 约 30.9），击杀回合不变，不影响结论。表内统一用纯公式口径以便横向对比。

# ==================== ② 怪物 → 玩家 ====================
print("\n## ② 同场景怪物 → 11级玩家：承伤回合数（玩家被普攻能扛几回合）\n")
print("| 职业 | 怪等级 | 怪atk | 玩家def | 攻防比 | 单发期望(无穿) | 含怪5%物穿 | 玩家HP | 承伤回合(无穿) | 含穿透承伤回合 |")
print("|------|-------:|------:|--------:|-------:|---------------:|-----------:|-------:|---------------:|---------------:|")

sec2 = []
for p in PROFILES:
    pn, st = p["name"], players[p["name"]]
    for lv in LVS:
        m = build_mon(lv)
        matk, pdef, php = m["atk"], st["def"], st["max_hp"]
        pp = MON_PENE
        ex0 = mc_expect(matk, pdef)                      # 纯公式口径（无穿透）
        ex1 = mc_expect(matk, pdef, pene_pct=pp)         # 真实引擎口径（DPS怪模板自带5%物穿）
        lo0, hi0 = exact_bounds(matk, pdef)
        s0 = math.ceil(php / ex0)
        s1 = math.ceil(php / ex1)
        print(f"| {pn} | {lv} | {matk} | {pdef} | {matk/pdef:.2f} | {ex0:.2f} ({lo0}~{hi0}) | {ex1:.2f} | {php} | **{s0}** | {s1} |")
        sec2.append((pn, lv, matk, pdef, ex0, ex1, php, s0, s1))

# ==================== ③ atk/def 比值表（纯公式，variance=0） ====================
print("\n## ③ 公式性质：atk/def 比值 → 伤害与等效缩减率（def=100 基准，E.calc_damage variance=0 精确值）\n")
print("| r=atk/def | atk | def | dmg=atk²/(atk+def) | dmg/atk | 等效缩减率 def/(atk+def) | 一阶近似 atk−def+def²/atk | 线性公式 atk−def 对照 |")
print("|----------:|----:|----:|-------------------:|--------:|------------------------:|------------------------:|--------------------:|")

ratios = [0.5, 1, 2, 3, 4, 6, 10]
for r in ratios:
    atk, df = int(r * 100), 100
    dmg = E.calc_damage(atk, df, variance=0.0)
    red = 1 - dmg / atk
    approx = atk - df + df * df / atk
    lin = max(0, atk - df)
    print(f"| {r:.1f} | {atk} | {df} | {dmg} | {dmg/atk:.3f} | {red*100:.1f}% | {approx:.1f} | {lin} |")

# 数学推导块
print("""
### ③推导：这是"防御形同虚设"的根源

    dmg = atk²/(atk+def) = atk·(1 + def/atk)⁻¹
         = atk·(1 − def/atk + (def/atk)² − (def/atk)³ + …)
         ≈ atk − def + def²/atk          （atk ≫ def 时）

- 防御的**绝对削减量** = atk·def/(atk+def) < def：无论攻方多弱，防御最多只挡掉"等于自身数值"的伤害，永远不能挡更多；
- 防御的**相对削减率** ε = def/(atk+def) = 1/(r+1)，随 r 增大单调趋 0 —— atk 越高，防御越没用，而不是"按比例"保持有用；
- 反方向同理：被高等级怪打时，玩家的 def 也按同一公式失效 → **失衡双向放大**。
""")

# ==================== ④ 暴击期望 ====================
print("\n## ④ 暴击期望提升（爆伤 ×1.5，引擎内实现）\n")
print("| 暴击率 p | 期望乘数 1+0.5p | 相对无暴击提升 | 战士实值(5%) | 刺客实值(20%) |")
print("|---------:|-----------------:|---------------:|-------------:|--------------:|")
for p in (0.0, 0.05, 0.10, 0.20):
    mult = 1 + 0.5 * p
    print(f"| {p*100:.0f}% | {mult:.3f} | +{ (mult-1)*100:.2f}% | {'✔ 实值' if abs(p-0.05)<1e-9 else ''} | {'✔ 实值' if abs(p-0.20)<1e-9 else ''} |")

print("\n蒙特卡洛验证（真实引擎）：")
for tag, atk, df, cr in (("战士11→怪11", 50, 24, 0.05), ("刺客11→怪16", 47, 34, 0.20), ("刺客11→怪11", 47, 24, 0.20)):
    e0 = mc_expect(atk, df, crit_rate=0.0)
    e1 = mc_expect(atk, df, crit_rate=cr)
    print(f"  {tag}: 无暴击期望 {e0:.2f} → 含{cr*100:.0f}%暴击期望 {e1:.2f}，实测提升 +{(e1/e0-1)*100:.2f}%（理论 +{0.5*cr*100:.2f}%）")

# ==================== ⑤ 结论素材：11v16 失衡放大 ====================
print("\n## ⑤ 11v16 失衡放大实证（从①②抽取）\n")
for pname, cls in (("战士", "战士"), ("刺客", "刺客")):
    st = players[pname]
    m11, m16 = build_mon(11), build_mon(16)
    # 玩家输出侧
    d16 = mc_expect(st["atk"], m16["def"], crit_rate=st.get("crit", 0))
    d11 = mc_expect(st["atk"], m11["def"], crit_rate=st.get("crit", 0))
    k16 = math.ceil(m16["hp"] / d16)
    k11 = math.ceil(m11["hp"] / d11)
    # 玩家承伤侧（真实引擎口径：DPS怪模板自带 5% 物穿）
    e16 = mc_expect(m16["atk"], st["def"], pene_pct=MON_PENE)
    e11 = mc_expect(m11["atk"], st["def"], pene_pct=MON_PENE)
    s16 = math.ceil(st["max_hp"] / e16)
    s11 = math.ceil(st["max_hp"] / e11)
    print(f"【{pname}】怪 11→16 级（def {m11['def']}→{m16['def']}，HP {m11['hp']}→{m16['hp']}，atk {m11['atk']}→{m16['atk']}）：")
    print(f"  输出侧：单发期望 {d11:.1f}→{d16:.1f}（{- (1 - d16/d11)*100:.0f}%），击杀回合 {k11}→{k16} 回合（+{k16-k11} 回合 / { (k16/k11-1)*100:.0f}%）—— 怪血量+{ (m16['hp']/m11['hp']-1)*100:.0f}% 是线性部分，攻防比塌缩是放大部分")
    print(f"  承伤侧：怪单发 {e11:.1f}→{e16:.1f}（+{ (e16/e11-1)*100:.0f}%），承伤回合 {s11}→{s16} 回合（-{s11-s16} 回合 / { (1-s16/s11)*100:.0f}%）")