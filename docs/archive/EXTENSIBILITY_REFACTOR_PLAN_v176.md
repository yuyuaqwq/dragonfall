# 引擎可扩展性重构计划（v176）

> 触发：鱼鱼"全部开始调整和重构，战斗引擎不合理设计也重构，做到可扩展性和极致优雅"
> 铁律：分阶段、每步可回退、35 门禁护航、每批 commit + 策划案同步
> 现状：battle.py 8105 行单类 Battle + 顶层宠物函数 + engine.py 1210 + core/ 已分层

## 目标（可扩展性 + 极致优雅）
1. 新职业/新技能/新机制 = 纯数据/注册表，零改引擎核心
2. 引擎核心 = 通用解释器（数据驱动），无职业/技能名硬编码
3. 代码分域清晰、单测覆盖、无 8000 行单体

## 架构分层（目标态）
```
game/
  engine.py          核心公式解释器（resolve_formula/calc_damage/skill_info）——已较纯
  battle.py          战斗编排（主循环/回合/行动）——瘦身目标
  core/
    battle_mech.py   机制注册表（63注册）——扩容目标（吸收硬编码特判）
    battle_conds.py  条件注册表（44注册）——扩容目标
    battle_modes.py  状态机（dual_form/focus/vent）
    damage.py        [新] 伤害结算域（从 battle.py 拆出）
    resources.py     [新] 资源/连段域（从 battle.py 拆出）
    passives.py      [新] 被动结算域（从 battle.py 拆出）
  data/
    skills.py        技能数据（纯数据）
    mech_effects.py  [新] 机制注册声明（或并入 core）
```

## 阶段划分

### P0 硬编码审计清单（本轮）
把 battle.py 所有"职业名/技能名/特判 if"grep 成清单：
- [ ] 每条标注：数据化 / 注册表化 / 合理保留 / 死代码
- [ ] 产出 docs/ENGINE_HARDCODE_AUDIT.md

### P1 注册表扩容（低风险，本轮可做）
- [ ] 元素法师 6 处特判 → mech/cond 数据键
- [ ] 拳师物理特判 → mech 注册
- [ ] 时停领域等技能名特判 → effect 数据
- [ ] 每改一批 → 跑 35 门禁 + 提交

### P2 引擎核心瘦身（中风险）
- [ ] damage 结算域拆 core/damage.py
- [ ] resources/连段域拆 core/resources.py
- [ ] 验证：battle.py 瘦身 + 门禁全绿

### P3 不合理设计重构（高风险，逐项）
- [ ] 列出候选：伤害公式? 读条? 资源模型? 被动结算?
- [ ] 每项出方案 → 鱼鱼确认 → 重构 → 门禁 + 真引擎矩阵验证

### P4 优雅化（收尾）
- [ ] 类型标注 / 死代码清理 / 函数瘦身 / 文档

## 红线
- 每一阶段结束必须 35 门禁全绿 + git commit（可回退）
- 真引擎矩阵（strength_matrix_report）作为行为回归基准
- 改动不破坏线上（AstrBot 运行中的实例——注意勿动运行时热载文件，改完重启前确认）
- 重构 ≠ 改数值：行为等价迁移，数值/机制调整另列
