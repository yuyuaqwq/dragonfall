# 职业体系重构 v151 执行计划（2026-08-31 夜）

> 鱼鱼拍板：完全抛弃隐藏职业，重构职业体系；职业装备及套装也要改造；
> 严格遵循数据驱动（看 v151 文档，前面一些职业是废案）；
> 审计"基于回合的效果"问题（如防御药水 3 回合防御，全是自己回合时防御无意义 → 时刻制）；
> 提前规划任务分派子 agent，禁子 agent 全量读项目。

## 蓝图文档（权威）
- `docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md` —— 六职业六形式十二分支完整技能表（落地蓝图）
- `docs/CLASS_REDESIGN_FRAMEWORK_v150.md` —— 框架（隐藏职业拆解映射、命名、迁移）
- `docs/CLASS_REDESIGN_PROPOSAL.md` / `docs/SKILLS_FULL_DESIGN_v150.md` —— 前序废案（参考机制，不直接落地）

## 现状基线（主 agent 侦察，2026-08-31）
- classes.py: 13 职业 = 新手 + 6 基础（cls_zhan_shi/fa_shi/you_xia/mu_shi/ci_ke/wu_seng）+ 6 隐藏（cls_dragon_oath/chronomancer/wild_hunter/hymn/shadow_blade/wu_sheng）
- skills.py: PLAYER_SKILLS(135) / BRANCH_SKILLS(24=12职业×2线) / _ADD_HIDDEN_SKILLS(12) / TUTOR_SKILLS(6)
- core_resources.py: 12 个资源条（rage/element/energy/faith/cp/chi + 隐藏线资源），v151 要废 → mech_stacks + enemy_buffs
- 装备: equip_roster.py(208件, 183KB) 按 weapon_type 关联，req 用属性；套装 sets.py(60个) 通用效果
- 战斗 CTB: BASE_DELAY/spd 速度条，self.round 回合推进，p_buffs {effect: 剩余回合} 每回合递减（L5261 _end_round）
- 战斗药水: buff_atk/buff_def → p_buffs 3 回合（items.py:2053），→ 回合制失真待审计

## 落地策略（数据驱动，禁子 agent 全量读项目）
1. **P1 数据层**（派子 agent，每 agent 一个职业，任务卡写死字段格式）
   - 6 基础职业技能表按 v151 重写（PLAYER_SKILLS 基础层 + BRANCH_SKILLS 两线）
   - 隐藏职业技能 → 拆解并入对应线（龙裔→血怒、时咒→时律、星语→疾风、暗影神谕→幽祷、暮影→影舞、淬势→破绽）
   - 新机制字段：mech_stacks（自身叠层 战意/连段/气）、enemy_buffs（敌身挂账 印记/破绽/标记）
2. **P2 引擎层**（主 agent 亲写，不派并行）
   - core_resources.py 12 资源条 → 废弃，换 mech_stacks/enemy_buffs 读取
   - battle.py 挂点：_apply_buffs、_end_round、技能结算、资源读改
   - 回合制效果 → 时刻制改造（见 P4）
3. **P3 装备/套装**（派子 agent，独立文件模式）
   - 装备按新六职业对齐（weapon_type 归属、req 调整）
   - 套装效果适配新体系（资源条相关效果改造）
4. **P4 回合制效果审计**（派子 agent 先审计，主 agent 收尾设计）
   - 防御药水 buff_def 3 回合在 CTB 下的失真
   - 全量 grep "N 回合" 效果，判定哪些该改时刻制、哪些保留回合制
5. **P5 测试**（主 agent 收尾）
   - 回归全绿 + 双仓库提交 + 重启验证

## 子 agent 纪律（memory 已存）
- 任务卡写死怎么做（数值/字段/挂点/样例），禁全量读项目
- 纯数据任务 = 主 agent 预计算值，子 agent 只照抄 + import 验证
- 禁 commit，主 agent 收尾统一提交
- 引擎接线主 agent 亲写；同文件并行 = 独立新文件 + 主 agent 合并

## 受影响测试
- test_v87_hidden（隐藏职业断言 631→632 名册）→ 隐藏职业 deprecated 后要更新
- run_numeric_tests.py（数值红线）
- 各职业技能测试
