# 回合制效果审计任务卡（鱼鱼点名专项）

## 背景
游戏战斗是 CTB（计时回合制）：`BASE_DELAY/spd` 速度条决定行动频率，`self.round` 是"全队行动一轮"的回合计数。
当前 buff/效果用"剩余回合"计时：`p_buffs = {effect: 剩余回合}`，在 `_end_round`（battle.py:5261）每回合递减。

**鱼鱼质疑**：防御药水"3 回合防御 +45%"，但 CTB 下每个角色行动频率不同——如果都是自己人的回合，防御 buff 覆盖的"敌方出手次数"极少，防御没意义。效果应该基于"时刻"（行动点/出手次数）而不是"回合"（全队轮数）。

## 任务
审计 `C:/Users/yuyu/qqbot/data/plugins/dragonfall` 里所有"基于回合"的效果，产出完整清单：

1. **玩家 buff（p_buffs）**：battle.py 里 `p_buffs[key] = N` 的所有位置，哪些是"回合制递减"的
2. **敌方 buff（e_buffs）**：同上
3. **道具/药水效果**：items.py / alchemy.py 里所有 "N 回合" 的 buff 药水（buff_atk/buff_def/buff_spd/buff_crit/buff_matk 等）
4. **技能效果**：skills.py 里带回合的 effect/cond（减速/灼烧/毒/眩晕/冰冻等）
5. **套装效果**：sets.py 里 bonus 带回合的（frost/slow/burn 等）
6. **护盾（p_shields）**：battle.py 里 turns 字段

## 输出格式
写报告到 `C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/turn_audit_report.md`：

```markdown
# 回合制效果审计报告
## 1. 玩家 buff（p_buffs）回合递减清单
| 效果 key | 设置位置 | 持续回合 | 消费位置 | 问题 | 建议 |
## 2. 敌方 buff（e_buffs）
## 3. 道具/药水
## 4. 技能效果
## 5. 套装效果
## 6. 护盾
## 7. 结论：哪些必须改时刻制，哪些保留回合制合理
```

## 铁律
- 只查不改，禁 git commit，禁改任何文件
- 每条带 `文件:行号` 证据
- 用 grep 定位，不要整读大文件（battle.py 6128 行、items.py 3000+ 行）
- 不跑全量回归，只许跑单个测试文件（如需要）
- 报告重点：**判断哪些"回合"效果在 CTB 下真的失真**（防御/减伤类 buff 最可疑），哪些合理（DOT 每回合掉血本来就该按回合）
