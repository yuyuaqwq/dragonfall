# v181 被动 proc 系统重建方案（REFACTOR_v181_PASSIVE_PROC_PLAN）

> 2026-09-10 凌晨主 agent 盘点。鱼鱼批：直接加。
> 结论：**引擎零改动**——被动 proc = 装配层声明驱动挂事件钩子（melody/class_mech 同模式）。

## 1. 现状盘点（52 个 proc 型被动全空转——N10 删旧 battle.py 后载体消失）

| 项 | 数 | 说明 |
|---|---|---|
| 技能 proc 总数 | 52 | kind=被动 + passive.proc 字段（高阶分支 60-90 级技能） |
| 有旧实现（passive_procs.py declare_proc） | 45 | 死代码保留完整 handler（family 语义权威） |
| 有旧实现无技能（死 proc） | 0 | 45 个全部有活技能对应 ✅ 无废弃 |
| 无旧实现（NO_OLD） | 7 | arcane_constant/finisher_up/poison_burst_up/lian_duan_soft/shadow_dance_cd/poison_spread/faith_share——被动载体消失后新加的，语义需从技能 passive dict + desc 推 |

### 52 proc 按旧 family 归类（旧实现被动语义权威 = passive_procs.py _h_* handler）

| 旧 family | 技能数 | 典型 | 语义（旧 handler 读 passive dict） |
|---|---|---|---|
| dmg_mult_cond | 9 | 奥术共鸣/元素起源/自然之眼/追猎者/疾风·极/灵魂锁链… | 条件伤害乘区（cond 满足 ×mult） |
| flag_set_cond | 6 | 元素亲和/元素同调/圣光回响/破绽感知/二重唱/镇魂安魂 | 条件置状态 flag（元素挂印/破绽减半/melody_duet 吟唱+1…） |
| dr_cond | 5 | 坚城之姿/磐石之心/大地之肤/磐石之躯/不动如山 | 条件减伤（cond 满足 reduce） |
| crit_cond_add | 4 | 狂热/元素之核/真知/疾风之心 | 条件暴击率 + |
| revive_cond | 3 | 血怒·不灭/铁誓·不动/死亡契约 | 死亡复活（条件/次数/回血） |
| counter_cond | 2 | 以守为攻/反击之王 | 受击概率反击 |
| stack_cap_add | 2 | 剧毒之心/淬毒之心 | 毒层 cap + |
| NO_OLD | 7 | 见上 | 待语义核查 |
| 其他单族 | 5 | tenacity(cc_break_cost)/万毒归宗(dot_mult)/剧毒之触(dot_weaken)/淬血(lifesteal)/追风(on_kill_refill)/真知… | 单族各语义 |

## 2. 新架构（声明驱动，引擎零知识——同 melody）

```
passive dict（技能数据）: {proc: "counter_chance", chance: 0.3, ...}
   ↓ 装配器 apply_class_passives（开战，扫已学 kind=被动 技能）
PASSIVE_PROC 声明表（data）: proc → {event, action, param 映射, 归属过滤}
   ↓ 参数化写 actor.triggers[event]
通用动作（class_mech_proc install 注册 ~10 个）执行
```

### 2.1 声明表形态
```python
PASSIVE_PROC = {
    # 反击族：受击后概率反击
    "counter_chance": {"event": "on_taken", "action": "passive_counter",
                       "map": {"chance": "chance"}},
    # 条件伤害乘区：dmg_calc 时 cond 满足 ×mult（cond 求值复用技能 cond 系统）
    "speed_ratio_dmg": {"event": "dmg_calc", "action": "passive_cond_mult", ...},
    # 复活：on_death 检查复活条件
    "berserk_revive": {"event": "on_death", "action": "passive_revive", ...},
    # 击杀回能：on_kill
    "focus_full_on_kill": {"event": "on_kill", "action": "passive_kill_gain", ...},
    # 减伤：taken_calc 条件乘区
    "zhan_yi_full_reduce": {"event": "taken_calc", "action": "passive_cond_reduce", ...},
    # 状态置位：act_cast/特定事件设置 flags/层
    "melody_duet": {"event": "act_cast", "action": "passive_flag", ...},
    ...
}
```

### 2.2 cond 条件求值
被动大多带 cond（rage>=5/hp_low_30/狂暴中…）——battle2 已有技能 cond 系统
（player_mech_stacks/hp 条件——cond dict 求值器），被动复用同一 cond 求值通道。

### 2.3 动作清单（~10 通用动作，从旧 _h_* handler 翻译）
passive_counter / passive_revive / passive_kill_gain / passive_cond_mult /
passive_cond_reduce / passive_crit_cond / passive_stack_cap / passive_flag /
passive_dot_mult / passive_lifesteal / passive_cc_break —— 语义逐字对照旧 handler。

## 3. 分批

| 批 | 内容 | 量级 |
|---|---|---|
| P0 | 本盘点 + 7 NO_OLD 语义核查（查 passive dict/desc/关联 mech 体系） | ✅ 完成（NO_OLD 待细核） |
| P1 | PASSIVE_PROC 声明表 + apply_class_passives 装配器 + install 注册动作框架 + 1-2 个动作样板（如 passive_cond_mult 覆盖 dmg_mult_cond 9 个） | 中 |
| P2 | 逐 family 接（flag_set/dr_cond/crit/revive/counter/…）每族测试对照旧语义 | 中 |
| P3 | 7 NO_OLD 语义定稿接入 + 全量回归 | 小中 |

## 4. 风险/约束
- 旧 handler 是 battle.py 时代 ctx 广播模型，新模型事件触发——语义对齐靠逐字对照旧 _h_* 实现 + 技能 desc
- 动引擎需求若出现（缺事件位）→ 停下给方案（预计零引擎改动）
- 引擎代码主 agent 亲写；装配/数据可拆分
