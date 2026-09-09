# N10-B6：战斗属性承伤消费批（dodge/block/物免/魔免）——设计文档

> 状态：待鱼鱼审查（2026-09-09）
> 触发：鱼鱼拍板"顺手核实后开小批补"——已核实 battle2 对 phys_reduce/magic_reduce/
> block/dodge **零消费**（stats.py 有聚合定义但引擎无读点），玩家被怪打不吃闪避/格挡/物免。
> 铁律：引擎零游戏知识；行为对齐旧 _damage_actor 承伤链；范围 = 最小可玩闭环。

---

## 1. 问题（已核实）

battle2 landing.deal_damage 当前承伤链：
`等级压制 → taken_calc → vulnerable → defending(固定0.5/B2可覆盖) → 睡眠 → 蓄力打断 → _apply_damage(护盾→扣血→死亡)`

**缺失段**（旧引擎 _damage_actor 有，battle2 无）：
| 属性 | 旧引擎语义 | battle2 现状 | 影响 |
|---|---|---|---|
| dodge 闪避 | 承伤 roll，乘算合成 cap40%，成功免伤 | 零消费 | 游侠/刺客被怪打不闪避（实测面板 12% 无效） |
| block 格挡 | 承伤 roll，cap40%，成功减免一半 | 零消费（除 defending 固定减伤） | 战士/词条格挡无效 |
| phys_reduce 物免 | 物理伤害 %减免 cap40% | 零消费 | 词条/技能物免无效 |
| magic_reduce 魔免 | 魔法伤害 %减免 cap40% | 零消费 | 词条魔免无效 |
| tenacity 坚韧 | 被控消耗资源跳过控制（职业 proc C 类） | 零消费 | **不迁**（职业机制，非通用承伤） |

## 2. 旧引擎顺序（语义参考，battle.py _damage_actor:11190）

```
蓄力打断 → 挡刀(_guard_check) → 闪避(_roll_dodge) → defending(格挡) →
物免/魔免(按 dmg_kind) → _mitigate_chain(block格挡/减伤/套装免疫/反击) →
护盾 → 扣血
```

## 3. battle2 落点（全在 landing.deal_damage / _apply_damage，引擎层通用）

### 3.1 dodge 闪避（承伤最前，defending 前）

```python
# deal_damage 内（睡眠/蓄力打断前，对齐旧"挡刀→闪避"最早消费）
def _roll_dodge(battle, target, logs) -> bool:
    """actor 承伤闪避：读 S.actor_stats(target).dodge，乘算合成上限 40%。
    引擎零知识：dodge 是面板数值字段。闪避成功 → 本次承伤中断（deal_damage 返回 0）。"""
    if not target: return False
    st = S.actor_stats(battle, target)
    dodge = min(float(st.get("dodge", 0) or 0), 0.40)
    if dodge <= 0: return False
    if random.random() < dodge:
        logs.append("💨 闪避了攻击！")
        return True
    return False
```

位置：deal_damage 中 `if target.get("defending")` 之前（在 taken_calc/vulnerable 之后？——
旧引擎闪避在等级压制之后、防守减免之前 → battle2 放 taken_calc 后 defending 前）。

### 3.2 物免/魔免（按 dmg_kind，defending 后）

```python
# deal_damage 内 defending 段后（对齐旧按 dmg_kind 减免）
if dmg_kind and dmg > 0:
    st = S.actor_stats(battle, target)
    if "phys" in dmg_kind:
        pr = min(float(st.get("phys_reduce", 0) or 0), 0.4)
        if pr > 0:
            red = max(1, int(dmg * pr)); dmg = max(1, dmg - red)
            logs.append(f"🪨 物理免伤，减免 {red} 点物理伤害！")
    if "magi" in dmg_kind:
        mr = min(float(st.get("magic_reduce", 0) or 0), 0.4)
        if mr > 0:
            red = max(1, int(dmg * mr)); dmg = max(1, dmg - red)
            logs.append(f"🛡️ 魔法抗性，减免 {red} 点魔法伤害！")
```

### 3.3 block 格挡（减免一半，物免后）

```python
# 同段（物免/魔免后；旧 _mitigate_chain 内 block 消费）
bc = min(float(st.get("block", 0) or 0), 0.40)
if bc > 0 and random.random() < bc:
    red = max(1, int(dmg * 0.5))
    dmg = max(1, dmg - red)
    logs.append(f"🛡️ 格挡！减免 {red} 点伤害！")
```

**RNG 消耗顺序对齐**：dodge roll → (block roll 仅命中后)。与旧引擎同序。

### 3.4 不做（边界）

- **tenacity**：职业 proc（战士 cc_break_cost 消耗战意跳控）→ 上层职业批
- **挡刀 _guard_check**：宠物影袭/召唤物 redirect——battle2 随从体系独立批
- **套装免伤/反击族**（first_hit_immune/anvil_parry/bi_chui_wall/retaliations）：
  battle2 事件总线已可表达（on_taken 声明），独立装配批
- **dodge_up/block_pot 等 buff 乘算**：这些是效果条目（effects 声明），B6 只消费面板基础
  dodge/block；buff 加值由 effects 面板折算（_apply_effects 已有 add/mul 支持）自然叠加

## 4. 引擎改动清单

| 文件 | 改动 | 行量 |
|---|---|---|
| game/battle2/landing.py | deal_damage 加 dodge roll + 物免/魔免 + block 段 | ~35 行 |
| game/battle2/landing.py | import random / S（检查现有） | 0-2 行 |

零配置改动（属性已在 actor_stats 聚合）。RNG 顺序需测试锁定。

## 5. 测试计划（tests/test_battle2_n10_b6_taken_attrs.py 新建）

| # | 场景 | 断言 |
|---|---|---|
| 1 | 玩家 dodge=1.0（cap 压 0.4）被打 → 命中时闪避（seed 固定后概率性/或 dodge=1 必闪） | 0 伤害 + 💨 文案 |
| 2 | dodge=0 → 正常承伤 | 扣血正常 |
| 3 | phys_reduce=0.3 吃物理 → 减免 ~30% | 对照无免伤 |
| 4 | magic_reduce=0.3 吃魔法 → 减免；吃物理不减免 | 对照 |
| 5 | block=1.0（cap 0.4）命中后 → 减免一半 | dmg 减半 |
| 6 | 真伤绕过全减免（dmg_kind=true） | 不减免 |
| 7 | 攻击方（玩家打怪）→ 怪有 dodge/block 也吃（actor-agnostic） | 怪闪避/格挡 |
| 8 | battle2 全套回归基线零新增 | 对照 |

## 6. 验证顺序

1. 设计文档 commit → git status 干净 → 改 landing.py → py_compile
2. 新测试全绿 → battle2 全套对照 → 汇报鱼鱼 → commit（v181.N10-B6）
