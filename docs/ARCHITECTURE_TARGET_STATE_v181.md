# v181+ 通用框架目标态架构（"配置换了就是新游戏"北极星）

> 鱼鱼 2026-09-07 拍板方向：**handler 不搬进 data 目录**（那是搬家不是解耦）。
> 目标：干净的框架 = 内容(数值/声明)在 data，行为收敛为【通用执行器】，由注册表/解释器分发。
> 换配置 = 新游戏；只有出现**全新机制类别**才需要写一个通用执行器（~20 行注册）。

## 三层目标态

```
data/（纯数据，零 import 零函数）
  ├─ 数值表：倍率/概率/阈值/成长/价格（dict 随便换）
  ├─ 内容声明：技能(mech/effect/cond/passive字段) / 套装(bonus_*.params) /
  │           武器(weapon_effect key + 数值权威表) / 词条(formula/params)
  └─ 规则/表达式：formula 字符串 / rule_engine 规则 / cond 声明
        ↓ 消费
core/（通用执行器 + 注册表 + 解释器，不含具体装备/职业/套装名）
  ├─ 注册表：MECH_EFFECTS(65) / affix formula / SET_PROC_TYPES / COND_CHECKS /
  │          TICK_HANDLERS / [新] passive_procs / [新] weapon executors
  ├─ 执行器：按【机制族】分类（~40 族），读 data params 执行
  │          proc_shield / proc_buff / proc_flat_dmg / taken_def_up_stack ...
  └─ 解释器：formula_expr / rule_engine / tick_effects 框架
        ↑ 注册分发（无字段=不启用）
battle.py（纯编排，零内容名）
  ├─ 挂点调注册表：_proc_pm → passive_procs.get(proc)(...)
  ├─ 套装读 params：effect 声明 → 执行器
  └─ 不做任何 if 装备名/if 职业 id/if 套装中文名
```

## 判定标准（写代码前先问）

1. **这个值/阈值/概率** → 必须 data（dict 项，可被配置换）
2. **这个"行为类型"是否已有通用执行器？**
   - 有 → data 声明 params，引擎泛读
   - 无 → 判断它是不是"新机制族"：是则注册一个通用执行器（~20 行，参数化），
     不是则说明它是已有执行器的变体 → 加参数表达，不新写 handler
3. **代码里出现具体内容名（装备名/职业 id/套装中文名/技能名）** → 错误信号，
   必须改成数据声明驱动
4. **新增职业/技能/装备/套装，改了什么？**
   - 目标态：只改 data（或极少数新机制族注册 ~20 行）
   - 现状障碍：weapon 96 handler / 被动散点 if / battle_config 职业命名 CFG → P2 收编

## 样板（已达标，复制它们）

| 样板 | 为什么对 |
|---|---|
| battle_bars.py / battle_modes.py | 无职业特判，数值从 player 字段+CFG 读，无字段=不启用 |
| food_effects / potion_effects | 数值权威在数据表 + effect_actions 共享动作 |
| affix formula 路径 | 词条带 formula 自动零代码生效 |
| SET_PROC_TYPES 执行器 | taken_def_up_stack/proc_buff... 参数化执行器，数据声明谁用 |
| tick_effects + TICK_HANDLERS | 通用周期效果框架，卡片+handler 数据驱动 |
| formula_expr / rule_engine | 表达式/规则解释器 = 声明化终极形态 |
| v180 怪物技能管线 | 玩家/怪物同一套 skill 管线（actor 无关）|

## P2 剩余任务方向校准（2026-09-07）

- **P2C weapon_effects 96 handler → ~10 通用执行器**：handler 内数值迁 weapon_effect_data.py
  （数值权威表，已有），handler 按机制族收敛（shield/buff/dmg/control/revive...），
  装备名从 core 消失。**不做**"96 个 handler 原样搬 data"。
- **P2D 被动 proc 反射化**：仿 MECH_EFFECTS 注册表（proc 名→handler），battle 挂点查表，
  消灭 34 处散点 if。handler 按机制族参数化，被动具体数值读 skills.py passive dict
  （第一批 v181.C 已把数值补进 skills.py 数据，正好是 handler 的数据源）。
- **P2E battle_config 职业命名 CFG → 机制命名单表**：不做"40 个 CFG 搬 data 目录"，
  而是收敛成 `MECH_CFG = {机制名: {数值}}`，消费点按机制名查。
  > ✅ **P2E 已完成**（commit 095abd4 = P1a-P3a：死表清理 43 删 + 双源归一 + MECH_CFG 建表/非 battle 读点迁移；battle.py 读点迁移 P3b 与测试·docs 收尾 P3c 由 wt_p3c 跟进）。
- **P3+ 后续**（玩家状态容器/battle 拆类）同样以"内容名不进引擎"为验收线。

## 红线

- **data/ 目录不放函数定义**（纯 dict/常量；生成/校验/装配函数在 core 或 data/_assembly 明确标注）
- **core/ 里不放具体内容名**（装备/职业/套装/技能中文名；机制族名可以）
- 执行器一律参数化：数值来自 data params，代码里不写默认值兜底
  （"配置缺字段 = 无此行为"，第一批 v181.C 已立此铁律）
- 新机制族 = 注册 ~20 行 + 数据声明，禁止 if-elif 分发链

## 扩展门槛指南（鱼鱼问：以后新增东西要不要动引擎？）

> 收完 P2（weapon/被动/CFG 收编）后生效。审计证据：副本 27 本配置化、技能 305 数据驱动、
> 词条 formula 自动生效、职业纯配置（P0 已清 BRANCH_BONUS/MECH_STACK_MAX 硬编码）。

| 新增内容 | 动引擎? | 说明 |
|---|---|---|
| 装备/武器（现有特效族） | ❌ 零 | 数据一条 + weapon_effect key |
| 怪物/Boss/地图/副本 | ❌ 零 | 配置化先例已证 |
| 技能（现有 kind/mech/effect）| ❌ 零 | 数据驱动先例已证 |
| 词条 affix | ❌ 零 | formula 字段自动生效 |
| 掉落池/商店/配方 | ❌ 零 | 纯数据 dict |
| 套装（现有 bonus 结构）| ❌ 零 | params 声明 |
| 基础职业（现有资源体系）| ⚠️ 接近零 | 8~10 个 data 文件；P0-B skill_up 撞名清后=零引擎 |
| 被动（现有机制族）| ⚠️ 极小 | P2D 注册表收编后 = 数据声明 |
| **全新机制类别**（位移/换位/变形/新控制）| ✅ 动扩展点 | 注册一把通用执行器 ~20 行（架构留的口子，注册后全内容复用）|
| 新资源循环/新伤害类型 | ✅ 动引擎(小) | P3+ 收完变扩展点 |
| 底层公式骨架（calc_damage/exp 曲线）| ✅ 动引擎 | 要"配置可换"需公式表达式化（formula_expr 可推广）|

**一句话**：加内容=纯 data 零引擎；造新机制才动引擎，且动的是注册表扩展点（~20 行）不是核心结算链。

