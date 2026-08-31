# 隐藏职业迁移任务卡（等引擎侦察确认后派）

## 背景
v150 框架 §7.1 已拍板：隐藏职业（龙裔/时咒法师/星语者/暗影神谕/暮影行者/淬势者）class id 保留不删，
标记 deprecated/legacy；机制精华拆解进六职业战术线（v151 技能表已含）。

## 任务
在 `C:/Users/yuyu/qqbot/data/plugins/dragonfall` 里执行隐藏职业迁移：

1. **classes.py**：6 个隐藏职业（cls_dragon_oath/chronomancer/wild_hunter/hymn/shadow_blade/wu_sheng）
   加 `"deprecated": True, "legacy": True` 标记，desc 更新为"旧隐藏职业，已并入 <对应线>"
2. **转职/任务链门禁**：找隐藏职业解锁逻辑（40 级任务链/种族锁 src_race），确认新角色无法通过任务链解锁
   （保留为叙事内容），老角色继续可玩
3. **技能冻结**：_ADD_HIDDEN_SKILLS 不再新增（数据冻结在 v142）

## 输出
报告：改了哪些文件哪些行、隐藏职业迁移状态表

## 铁律
- 只改 classes.py / 解锁逻辑 / _ADD_HIDDEN_SKILLS 注释，禁改其他
- 禁 git commit，禁跑全量回归
- 用 grep 定位，不要整读大文件
