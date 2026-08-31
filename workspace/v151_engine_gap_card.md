# v151 引擎差距侦察任务卡

## 背景
v151 设计文档（`docs/CLASS_MECHANICS_REDESIGN_v151_FULL.md`）要落地六职业六形式：
- 战士=战意（自身叠层 0-10，持有即生效，不消耗）
- 法师=元素印记（铺敌身，火/冰/雷各 0-3 层，反应表引爆）
- 游侠=精力（预算）+标记（挂敌身）
- 牧师=行为（无资源条，CD+目标抉择）
- 刺客=连段（命中计数 0-10）
- 拳师=破绽（挂敌身 0-50，推满跳回合）

设计文档 §10 说：旧 `core_resources.py` 的 12 个资源条废弃，换成 `mech_stacks`（自身叠层）+ `enemy_buffs`（敌身挂账）。

## 任务
侦察 `C:/Users/yuyu/qqbot/data/plugins/dragonfall` 现有引擎对这套机制的支撑度：

1. **mech_stacks**：battle.py 里有没有现成的 `mech_stacks` 机制？（grep "mech_stacks"）它是怎么存的、怎么增减的？
2. **enemy_buffs / 敌身挂账**：敌方 debuffs 怎么存？（grep "debuffs"）现有的 mark/破绽/shaken 机制在哪、怎么工作？
3. **core_resources.py 消费点**：battle.py / battle_mech.py 里所有读 CORE_RESOURCES 的地方（grep "core_resource" / "res_gain" / "res_cost" / "_resource_label"），列出来——要废弃资源条，这些消费点都要改
4. **cond 条件系统**：battle_conds.py 里现有 cond 类型清单（grep "register"），v151 需要的"战意≥N""印记层数""连段≥N"条件有没有现成的？
5. **reaction 反应表**：法师元素反应（蒸发/超载/冻结/感电）在现有引擎有没有影子？（grep "reaction" / "蒸发" / "超载"）
6. **召唤物**：summons.py 现有召唤物系统怎么工作？v151 §7 的骷髅/藤蔓守卫/古树守卫要属性表

## 输出格式
写报告到 `C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/v151_engine_gap_report.md`：

```markdown
# v151 引擎差距侦察报告
## 1. mech_stacks 现状
## 2. enemy_buffs / 敌身挂账现状
## 3. core_resources 消费点清单（要废弃需改哪些）
## 4. cond 条件清单（v151 需要的有没有）
## 5. 元素反应现状
## 6. 召唤物现状
## 7. 结论：v151 落地需要的引擎改动清单（按文件分组）
```

## 铁律
- 只查不改，禁 git commit
- 每条带 `文件:行号` 证据
- 用 grep 定位，不要整读大文件
- 不跑全量回归
