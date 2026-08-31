# -*- coding: utf-8 -*-
"""T3 龙脉 0.18→0.10 收敛 · EQ 实算（只读验证脚本）
调真实 Battle._mech_stack_bonus / _cond_mult（stub 对象，不动库）。
"""
import sys, types
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall")
from game.battle import Battle


def stub(pre, res):
    s = types.SimpleNamespace()
    s._pre_cost_res = dict(pre) if pre is not None else None
    s.resources = dict(res)
    s.mech_stacks = {}
    return s


def stack_bonus(b, info, mech="dragon_might"):
    return Battle._mech_stack_bonus(b, mech, {}, info)


def cond_mult(b, info):
    return Battle._cond_mult(b, info, {"class_name": "cls_dragon_oath"})

print("=" * 62)
print("① 龙脉终曲 power=3.2 res_cost dragon_might=10（0.10/层）")
term = {"power": 3.2, "res_cost": {"dragon_might": 10}}
for label, pre, res in [
    ("满力10(快照10)", {"dragon_might": 10}, {"dragon_might": 10}),
    ("扣费后回落(无快照,0)", None, {"dragon_might": 0}),
]:
    b = stub(pre, res)
    m = stack_bonus(b, term)
    print(f"  {label}: 倍率={m:.4f}  EQ={3.2 * m:.4f}")

print("=" * 62)
print("② 龙焰吐息 power=2.6 res_cost=5 cond 龙力≥8×1.2（0.10/层）")
breath = {"power": 2.6, "res_cost": {"dragon_might": 5},
          "cond": {"type": "player_res_stacks", "res_key": "dragon_might",
                   "stacks": 8, "mult": 1.2, "label": "龙威"}}
for label, pre, res in [
    ("满力10施放(快照10,扣后5)", {"dragon_might": 10}, {"dragon_might": 5}),
    ("边界8力施放(快照8,扣后3)", {"dragon_might": 8}, {"dragon_might": 3}),
    ("低于阈值5力(cond不触发)", {"dragon_might": 5}, {"dragon_might": 0}),
    ("无快照回落当前5(旧语义)", None, {"dragon_might": 5}),
    ("无快照回落当前3(旧语义,8力扣后)", None, {"dragon_might": 3}),
]:
    b = stub(pre, res)
    m = stack_bonus(b, breath)
    cm = cond_mult(b, breath)
    print(f"  {label}: stack={m:.4f} cond={cm:.4f}  EQ={2.6 * m * cm:.4f}")

print("=" * 62)
print("③ 对照：战士 裂地斩 rage≥8×1.5（快照语义边界，同型先例）")
lie = {"power": 1.8, "res_cost": {"rage": 3},
       "cond": {"type": "player_res_stacks", "res_key": "rage", "stacks": 8, "mult": 1.5}}
b = stub({"rage": 8}, {"rage": 5})
m = stack_bonus(b, lie, mech="rage")
cm = Battle._cond_mult(b, lie, {"class_name": "cls_zhan_shi"})
print(f"  8怒施放(扣3剩5): stack(rage走mech)=1.0 cond={cm:.4f} EQ={1.8 * cm:.4f}")

print("=" * 62)
print("④ 排序基准（满资源单发 EQ，10 层满档）")
print(f"  龙脉终曲 3.2×{1 + 10 * 0.10:.2f} = {3.2 * (1 + 10 * 0.10):.4f}")
print(f"  龙焰吐息 2.6×{1 + 10 * 0.10:.2f}×1.2 = {2.6 * (1 + 10 * 0.10) * 1.2:.4f}")
print(f"  撼岳·终焉(苦修) 2.5×{1 + 10 * 0.12:.2f} = {2.5 * (1 + 10 * 0.12):.4f}，破势×1.1 = {2.5 * (1 + 10 * 0.12) * 1.1:.4f}")
print(f"  无畏冲击(战士) 2.2×(1+0.12×10) = {2.2 * (1 + 0.12 * 10):.4f}")
print(f"  旧 0.18 终曲 3.2×{1 + 10 * 0.18:.2f} = {3.2 * (1 + 10 * 0.18):.4f}（收敛前）")