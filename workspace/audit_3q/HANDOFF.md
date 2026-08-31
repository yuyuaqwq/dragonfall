# 交接文档：dragonfall 装备/套装/副本改造（2026-08-30/31）

> 给新会话的实现 agent。所有设计文档已在 `workspace/audit_3q/` 落盘，本文件是速览 + 实现顺序。

## 一、背景（鱼鱼需求）
1. 副本入口要"设施化"：不能虚空进入，要走到入口才能开本
2. 装备要有特色：不要换皮——**一部分**装备有独特特殊效果（金字塔：大部分普通、一部分独特），分阶段分布（前期少、中期开始、后期丰富、终局最华丽）
3. 套装去模板化：不要 6 个 effect 模板轮播（dodge_set 11 套/regen 10 套/pierce 10 套/execute 10 套/thunder 9 套/lifesteal 9 套），每套要有专属效果

## 二、已完成（已落地验证）
- **F1/F2 副本入口设施化**：22 副本 entry 字段 + 21 处入口子区域 funcs=instance + 开本位置校验 + 列表显示入口 + 子区域面板
  - ⚠️ **未提交 git**！工作区有 7 个文件改动（instance.py/world.py/instances.py/subareas.py + 3 测试文件）
  - 已验证：185 断言全绿、py_compile 通过、运行时确认
  - **新会话第一件事：先提交这一版！**

## 三、设计文档（全部落盘 workspace/audit_3q/）
| 文档 | 内容 |
|---|---|
| D1_design.md | 装备特色模板 12 种（数值定位+取舍，守恒验证） |
| D2_design.md | 独特装备子集 44 件 + 24 效果库 |
| D3_A_report.md ~ D3_E_report.md | 独特装备加量版 128 件 + 33 新效果（5 阶段） |
| S1_A_report.md ~ S1_E_report.md | 套装去模板化 ~87 套专属效果 |
| R1-R6_report.md | 三问题审查原始报告 |

## 四、实现顺序建议
1. **先提交 F1/F2**（已验证 185 绿，先存一版）
2. **落地 D3 装备**（数据层为主：LEGENDARY_EFFECTS 补 33 新效果 + 名册挂载字段，风险低）
3. **落地 S1 套装**（需改引擎 handler：SET_PROC_EFFECTS 注册 ~30 个 + battle.py 硬编码分支扩展，风险高）

## 五、落地要点（从设计稿提炼）
### D3 装备落地
- 数据层：`game/data/affixes.py` LEGENDARY_EFFECTS 补新效果（格式：{key:{name,kind,trigger,chance?,effect,desc}}）
- 名册：`game/data/equip_roster.py` 给选中装备挂 `legendary` 字段（stat 型直接并入 stats）
- 引擎：on_hit/on_taken 型需在 `game/core/affix_effects.py` 注册 handler（~5 行/个）；battle_start 型挂 battle.py 战斗开始区；passive 条件型走 _affix_dmg_mult（battle.py:3033）
- 蓝装轻量用既有词条 ID 复用为专属（element_ice/swift/dmg_reduce）

### S1 套装落地
- 数据层：`game/data/sets.py`（SETS 字面量）+ `game/data/class_sets.py`（_SERIES_SET_BONUS，live 名册套）改 effect 名 + desc
- 引擎：`game/core/affix_effects.py` SET_PROC_EFFECTS 注册新 handler（~30 个）；battle.py:4989 regen 分支、5762 reflect 分支扩展；区域套 bonus_5_cond 走既有消费（battle.py:3016-3027）零改动
- ⚠️ 数据双写：sets.py SETS 字面量 + class_sets.py _SERIES_SET_BONUS（_build_class_sets 运行时注册覆盖）——两处都要改

## 六、受影响测试（落地后跑）
- test_v1252_audit_closure.py（SET_PROC 注册反向断言：注册的新 handler 必须出现在某套装 effect 中）
- test_v98_05_registry.py、test_v136_phase6_equip.py、test_v106_1_attributes.py
- 套装改后：test_v136_phase6_equip / test_v1252_audit_closure / test_v98_05_registry / test_v106_1_attributes 四件套全绿
- 铁律：单测用 `python tests/test_xxx.py`（无 pytest），禁全量回归并行

## 七、铁律提醒
- 只改数据先提交，引擎改动单独提交
- 改前 git status 确认工作区干净（先提交 F1/F2）
- CRLF 大文件（economy.py/instance.py 等）多行改动用 Python 行级脚本，禁 patch 多行替换
- 落地后跑对应单测 + 双仓库提交（代码仓 + design 仓）
- 测试用独立私有临时库（GWEN_GAME_DB 指向 tempfile），禁共享 test_game_data.db 并行
