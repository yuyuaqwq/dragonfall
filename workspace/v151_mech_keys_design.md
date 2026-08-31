# v151 mech_stacks / enemy_buffs 新 key 设计（主 agent 引擎层）

> 引擎现状：mech_stacks 已有（self.mech_stacks dict，随战斗序列化），mech_stack_gain 引擎函数现成。
> MECH_STACK_MAX 白名单（engine.py）现有 14 个 key，v151 需要新增。
> 敌身挂账：enemy.buffs 已有，battle_bars.py 的 enemy_bar 机制（shaken/curse）现成。

## 自身叠层（mech_stacks）—— v151 六形式

| 职业 | 形式 | key | 上限 | 获取 | 收益 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 战士 | 战意 | `zhan_yi` | 10 | 普攻/技能命中+1，击杀+2 | 每层攻击+4%（血怒+6%）、受伤+2%（血怒+3%）| 满10入狂暴（dual_form 已有 fury 机制） |
| 刺客 | 连段 | `lian_duan` | 10 | 命中+1，miss/闪避归零 | 每段暴击+3%，终结技每段+10% | 计数非货币 |
| 拳师 | 气 | `qi` | 10 | 技能命中+1 | 每点持有物理+3%（Momentum）| 已有 chi 可复用或新 key |

## 敌身挂账（enemy.buffs / enemy_bar）—— v151 三形式

| 职业 | 形式 | key | 上限 | 机制 | 引擎载体 |
| --- | --- | --- | --- | --- | --- |
| 法师 | 元素印记 | `fire_mark`/`ice_mark`/`thunder_mark` | 各 3 | 反应表：蒸发×1.3/超载AOE/冻结/感电 | 已有 fire_mark 等 + REACTION_TABLE |
| 游侠 | 标记 | `mark` | 3 | 全队对标记目标增伤，叠满+30% | 已有 mark |
| 拳师 | 破绽 | `shaken` | 50 | 推满跳回合，阈值×1.35递增 | 已有 enemy_bar shaken |

## MECH_STACK_MAX 新增项（engine.py）
```python
"zhan_yi": 10,    # 战意（战士）
"lian_duan": 10,  # 连段（刺客）
# qi 可复用现有 chi（气力）或新增 qi
```

## MECH_STACK_WHITELIST 新增项（battle.py 或 engine.py）
- zhan_yi / lian_duan（qi 若新 key）

## 引擎改动清单（主 agent 亲写，不派子 agent）
1. engine.py: MECH_STACK_MAX 加 zhan_yi/lian_duan
2. battle.py: MECH_STACK_WHITELIST 加 zhan_yi/lian_duan
3. 技能 mech 字段消费：技能里 `mech: "zhan_yi", mech_val: 1` → mech_stacks 增减（_player_skill 已有 mech 处理，L4122 白名单查表）
4. 持有收益：每层战意攻击+4% → 在 _player_stats 或被动结算处查 mech_stacks["zhan_yi"] 加成（新引擎挂点）
5. 受伤+2%/层 → 在 _damage_player 查战意层数加承伤（新引擎挂点）
6. 满10入狂暴 → 已有 dual_form fury 机制可复用
