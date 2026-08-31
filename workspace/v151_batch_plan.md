# v151 落地批次规划（第二批：数据层）

## 依赖
- 等 v151_engine_gap_report.md 确认引擎差距（第一批 task-1）
- 等 equip_audit_report.md 确认装备改造范围（第二批 task-0）

## 批次 2A：职业技能落地（6 agent，每职业一张卡）
| agent | 职业 | 技能表原文 | 落地位置 | 隐藏职业拆解 |
| --- | --- | --- | --- | --- |
| A1 | 战士 | v151_skill_tables/zhan_shi.md | PLAYER_SKILLS + BRANCH_SKILLS | 龙裔→血怒（真伤/灼烧轴） |
| A2 | 法师 | v151_skill_tables/fa_shi.md | 同上 | 时咒→时律（控制链） |
| A3 | 游侠 | v151_skill_tables/you_xia.md | 同上 | 星语→疾风（点名权） |
| A4 | 牧师 | v151_skill_tables/mu_shi.md | 同上 | 暗影神谕→幽祷（骷髅/诅咒） |
| A5 | 刺客 | v151_skill_tables/ci_ke.md | 同上 | 暮影→影舞（影舞态） |
| A6 | 拳师 | v151_skill_tables/quan_shi.md | 同上 | 淬势→破绽（撼岳） |

每张卡内容：技能表原文 + 字段映射 + 现有格式样例 + 落地铁律（只改自己职业段，禁 commit，py_compile 验证）
→ 参考 workspace/v151_skill_task_template.md

## 批次 2B：引擎层（主 agent 亲写，不派）
- engine.py MECH_STACK_MAX 加 zhan_yi/lian_duan
- battle.py MECH_STACK_WHITELIST 加新 key
- 战意持有收益（每层攻击+4%/受伤+2%）挂点
- 时刻制改造（按敌方出手次数计防御 buff）
- core_resources 消费点收敛（数据层改完后清理）

## 批次 2C：装备/套装改造（等 equip_audit_report 后派）
- 隐藏职业专属装备改名/改归属
- 绑定旧资源的效果改新体系
- 职业武器类型映射对齐

## 批次 3：测试收尾（主 agent）
- 回归全绿（run_all_tests.py）
- test_v87_hidden 名册断言同步
- 双仓库提交（dragonfall + design/new_world）
- 重启 AstrBot 验证
