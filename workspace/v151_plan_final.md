# v151 落地执行方案（鱼鱼两次拍板更新版，2026-08-31 夜）

## 鱼鱼拍板记录
1. **隐藏职业直接删，别留，没人转职**（classes.py 删除，不是 deprecated）
2. **隐藏职业的装备不一定要删，可以考虑保留然后更改效果**（装备保留，改效果对齐新体系）

## 执行方向

### A. 职业层（删）
- classes.py：6 隐藏职业段（cls_dragon_oath/chronomancer/wild_hunter/hymn/shadow_blade/wu_sheng）删除
- skills.py：_ADD_HIDDEN_SKILLS 删除，隐藏职业专属技能删除
- core_resources.py：隐藏职业资源条删除
- 转职/任务链/种族锁：隐藏职业解锁逻辑删除
- 测试：20+ 测试文件的隐藏职业断言删除/改新六职业

### B. 装备层（保留 + 改造）
- 隐藏职业专属装备（龙鳞/星尘/暮影/龙裔系列 40+ 件）**保留**，改名/改效果对齐新六职业
- 绑定旧资源的效果（rage/element/energy/faith/chi/combo）改新机制
- 套装效果对齐新体系

### C. 技能层（v151 落地）
- 六职业技能表按 v151 翻译落地（PLAYER_SKILLS + BRANCH_SKILLS）
- 隐藏职业机制精华并入对应线（龙裔→血怒/时咒→时律/星语→疾风/暗影神谕→幽祷/暮影→影舞/淬势→破绽）
- 新机制字段 mech_stacks/enemy_buffs

### D. 时刻制改造（鱼鱼点名）
- 防御/减伤类 buff 按敌方出手次数计（_enemy_phase 递减）
- 攻击类 buff 保持按轮数；DOT 保持按轮数；控制保持行动级

## 任务批次
1. 侦察（进行中）：回合制审计 / v151 引擎差距 / 装备改造范围
2. 数据层落地（等侦察）：6 职业技能 agent + 装备改造 agent + 隐藏删除 agent
3. 引擎层（主 agent 亲写）：mech_stacks 新 key + 时刻制改造
4. 测试收尾：回归全绿 + 双仓库提交 + 重启
