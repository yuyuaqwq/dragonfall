# v151 隐藏职业删除任务卡（鱼鱼拍板：直接删）

## 背景
鱼鱼拍板：隐藏职业直接删，别留。装备保留改效果（另一任务卡）。

## 任务
在 `C:/Users/yuyu/qqbot/data/plugins/dragonfall` 里删除 6 个隐藏职业的**数据定义**（禁动引擎逻辑）：

1. **game/data/classes.py**：删除 6 个隐藏职业段（cls_dragon_oath L417-464 / cls_chronomancer L465-512 / cls_wild_hunter L513-564 / cls_hymn L565-621 / cls_shadow_blade L622-674 / cls_wu_sheng L675-734），以及文件头注释里隐藏职业相关说明
2. **game/data/skills.py**：删除 `_ADD_HIDDEN_SKILLS`（12 个隐藏职业技能 dict）整个定义；PLAYER_SKILLS 里隐藏职业专属技能（归属 cls_dragon_oath 等的 sk_ 技能）删除
3. **game/data/core_resources.py**：删除隐藏职业资源条（cls_dragon_oath dragon_might / cls_chronomancer time_sand / cls_wild_hunter hunt_mark / cls_hymn canticle / cls_shadow_blade shadow_step / cls_wu_sheng zen）
4. **game/data/battle_config.py**：删除隐藏职业专属配置（龙焰 dual_form 等，保留基础职业的）
5. **game/data/quests.py**：删除隐藏职业任务链（unlock_class=cls_xxx 的任务）
6. **game/data/achievements.py**：删除隐藏职业成就（hidden_class 类型）
7. **game/data/dialogues.py**：删除隐藏职业解锁/专属对话（need hidden_unlocked=cls_xxx）
8. **game/data/builds.py / job_guide.py / items.py**：删除隐藏职业流派预设/简介/技能书（require_class=cls_xxx）

## 输出
写报告 `workspace/hidden_delete_report.md`：每个文件删了什么（行号范围）、残留引用检查结果

## 铁律
- **只改数据文件（game/data/ 下）**，禁动 game/battle.py、game/commands/、game/core/ 等引擎/命令层
- 禁 git commit，禁跑全量回归
- 每删完一个文件跑 `python -c "from game.data import <模块>; print('ok')"` 验证 import 不崩
- 删完后 grep 确认无残留引用（允许注释里的历史说明残留）
- 注意：sk_ 开头的字符串会被 Hermes 显示层脱敏（***），用 Python 原生 open().read() 核实
