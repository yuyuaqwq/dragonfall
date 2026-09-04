# 乘区全量盘点（v175e 系统扫描 2026-09-05）

> 触发：鱼鱼"扫描全项目看看还有什么乘区被遗漏"
> 方法：扫 面板全键 / 词条池 AFFIXES / 引擎战斗结算链（_damage_player 承伤链 + 伤害结算链）

## 一、输出乘区（已建模 vs 遗漏）

| 乘区 | 面板键 | 引擎挂点 | 建模状态 |
|---|---|---|---|
| 攻击% | atk/matk | calc_damage | ✅ affix_type=atk |
| 暴击率+爆伤 | crit/crit_dmg | calc_damage ×1.5 ×(1+cdmg) | ✅ crit |
| 急速 | spd | cast 速度折算 | ✅ spd |
| 穿透 | pene_phys/magi | 有效防御削减 | ✅ pene |
| 全伤/元素增伤 | dmg_mult | resolve_formula 外层 | ✅ elem |
| 冷却缩减 | cdr | _set_skill_cd ×(1-cdr) cap40% | ✅ cdr |
| **吸血** | lifesteal | 伤害回血结算 | ⚠️ 只标生存向没进输出对比 |
| **幸运** | luck | 暴击后 30% ×1.3 | ⚠️ 暴击子项已含，独立 luck 词条未建 |
| **处决/斩杀** | execute_threshold | 目标血量<30% ×1.3 | ❌ 未建（词条有 dmg_mult execute_threshold） |
| **精准** | precise | 削减敌方闪避 | ❌ 未建（PVP/高闪怪相关） |
| **属性联动被动** | passive dmg_mult | 常驻条件增伤 | ❌ 未建（词条被动型） |

## 二、生存/承伤乘区（全未建模！）

| 乘区 | 面板键 | 引擎挂点 | 说明 |
|---|---|---|---|
| **闪避** | dodge | _damage_player 全额免伤 cap40%（PVE 怪物无精准） | 🔴 鱼鱼点名"闪避战士"核心 |
| **格挡** | block | 减半伤害 cap40% | 🔴 盾坦核心 |
| **减伤** | reduce/reduce_all | 百分比减伤 cap90% | ⚠️ 技能 buff 为主，词条 dmg_reduce |
| **减伤词条** | dmg_reduce | — | ❌ 词条有但没建模 |
| **反伤** | thorns | — | ❌ 词条有（thorns 反伤） |
| **生命%** | max_hp | 承伤池 | ⚠️ 坦克向没建词条 |
| **回复** | regen | turn_start.regen | ❌ 词条有 |

## 三、资源/经济乘区

| 乘区 | 说明 | 建模状态 |
|---|---|---|
| **资源词条 res** | 装备给怒气/连击点/信仰等（31 资源词条） | ❌ 未建 |
| mp 减耗 | mp_cost_reduce | ❌ 未建（长盘续航） |
| 回复药水/食物 | 战斗外 | economy_lib 已覆盖 |

## 四、结论：优先级建议

1. **闪避（dodge）**：鱼鱼点名玩法 + PVE 真实强力 → 优先建
2. **吸血（lifesteal）**：生存+输出双属性，词条已定义 → 补进对比
3. **格挡（block）**：盾坦向，坦克流验证用 → 中优先
4. **资源词条 res**：影响技能循环频率（怒气/连击点更多 → 终结更快）→ 中优先
5. 处决/反伤/减伤/回复：锦上添花 → 低优先

## 落地记录（v175e 生存乘区全加）
- **gear AFFIX_BY_TYPE 新增 6 生存词条**：dodge+20%（cap40）、block+25%（cap40 减半）、
  reduce+20%（减伤）、thorns+30%（反伤）、luck+15%（幸运/暴击联动）、execute（斩杀线30%）
- **build_vs_boss 支持 affix_type**，生存段乘 (1-dodge)×(1-block/2) 期望减免因子
- **N09 生存乘区门禁**（真引擎 battle_rotation 打不过档强 Boss 验证）：
  - lifesteal 吸血：存活 3-4 倍（战士 14.2→50.3、游侠 12→55.5、法师 9.8→41.8）续航王
  - dodge 闪避：+32-45% 存活（全职业稳定）
  - block 格挡：+20-46% 存活（弱于闪避/吸血但有效）
- **balance_data 15 流派全标注 affix_preset**（含生存向：盾卫→block、磐核→dodge、
  神谕→lifesteal、咏叹→reduce、挽歌→thorns）
- 期望模型不模拟 Boss 行动 → 吸血精确结算走真引擎（N09 已覆盖）；期望 survive 保留 dodge/block 粗判
