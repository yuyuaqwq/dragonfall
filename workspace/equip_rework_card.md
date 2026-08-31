# 装备/套装改造任务卡（第二批，等 equip_audit_report 确认后派）

## 背景（鱼鱼拍板）
- 隐藏职业直接删（classes.py 等）
- **隐藏职业装备保留**，改效果对齐新六职业
- 职业装备及套装也要改造

## 主 agent 已侦察的系列结构
- SERIES_SETS（equip_roster.py）把系列映射套装：龙脊→龙脊套、星尘→星尘套、暮影→暮影套、龙裔→龙裔套、灰烬守卫→灰烬守卫套
- 隐藏职业相关装备系列：龙脊（Lv.80-92）、星尘（Lv.55）、暮影（Lv.88-96）、龙裔、灰烬守卫、星语（Lv.52）
- 装备字段：name/slot/weapon_type/quality/lv/series/req/source/weapon_effect/legendary
- 套装效果（sets.py + class_sets.py）：绑定旧资源（mark/faith/rage/element/cp/combo）

## 任务
等 equip_audit_report.md 的完整清单，然后：
1. **隐藏职业专属装备**：保留，改效果对齐新六职业（龙脊→战士、星尘→法师、暮影→刺客、星语→游侠）
   - weapon_effect / legendary 绑定旧资源（dragon 等）→ 改新机制效果
   - desc 去掉"隐藏职业专属"字样（如有）
2. **套装效果改造**：绑定旧资源的套装效果 → 改新机制（mech_stacks/enemy_buffs）
3. **职业武器类型映射**：确认新六职业各用哪些 weapon_type，隐藏职业专属武器类型并入

## 输出
报告：改了什么、新效果是什么、验证结果

## 铁律
- 禁改 classes.py（另一个 agent 负责删隐藏职业）
- 禁 git commit，禁跑全量回归
- 改完 py_compile 验证
- 最小 diff，禁整文件重写
