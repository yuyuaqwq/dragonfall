# v125.2 数据驱动收尾修复计划（2026-08-16）

## 目标
鱼鱼拍板"还有就继续一次性做完"——清完 v125.1 审计剩余的 P2 级数据驱动欠账。

## 批次划分（按文件隔离，battle.py 由 2 个 agent 分区域并行——v125.1 已验证 2 agent 同改 battle.py 可行）

| 批次 | 文件 | 内容 |
|------|------|------|
| B1 战斗主路径 | battle.py 伤害段 + 新建 data/battle_config.py | mech 特判 8 处收敛 + 控制白名单 + MECH_STACK_BONUS 叠层倍率 + DOT_DEFS + ELEMENT_REACTIONS 迁数据 + Boss 攻乘区 |
| B2 战斗效果类 | battle.py 效果段 + items.py 药水 + pets.py + combat.py 显示段 | 药水 15 分支注册表 + 宠物技能 5 分支注册表 + 被动 proc 映射数据化 + buff 显示映射补全 + atk_down 死键清理 |
| B3 副业数值 | economy.py 副业段 + prof_config.py | 附魔槽位规则单点 + 符文等级门数据化 + 每日奖励 50 + 价格带公式 + 稀有阈值 150 |
| B4 怪物清理 | monsters.py + monster_mods.py + battle_mech.py + 数据 | aoe:all/interrupt 死字段处理 + m_giant_rat 死数据 + boss/elite 补 mod + mech 去重校验 |
| B5 命令层数值 | misc.py + social.py + economy.py 市场段 + world.py 传送段 + 新建 data/econ_config.py | 住宿/传送/许愿/PVP/市场 20+ 魔法数字下沉 |
| B6 任务收敛 | world.py 任务段 + combat.py 每日段 | 每日发奖双副本收敛 + need 99 兜底 + 面板渲染统一 |
| B7 成就文案 | titles.py + achievements.py | desc 语义 4 处 + 文案遗留 2 处 |

## 冲突控制
- battle.py：B1 管伤害计算段（约 1900-3100），B2 管效果段（约 897-951 药水/2827-2874 宠物）——区域锚定最小 diff
- economy.py：B3 管副业段（约 380-2600），B5 管市场/传送段（约 3000-4324）
- world.py：B5 只动传送费用 1-2 处，B6 管任务段
- combat.py：B2 管显示映射段，B6 管每日任务段

## 铁律
- 最小 diff、不碰 git、不跑全量回归、私有库验证、py_compile、输出变更清单
- 行为等价验证：改前后基线 diff（v125.1 验证过的模式）
- 只修断链/下沉数值，不补被有意删除的数据（v125.1 教训）
- 完成后主 agent：全量回归 → 双仓提交 → 重启 → refs 实录
