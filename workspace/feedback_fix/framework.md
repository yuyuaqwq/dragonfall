# 玩家意见处理批（2026-08-27 早，开服第 2 天）

## 环境
- 项目根：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 测试权威运行：`python tests/test_xxx.py` 直跑；全量 `scripts/run_all_tests.py`
- AstrBot 在线（重启中，端口 6185/6199）
- DB：意见箱 `game/game_data.db` 的 feedback 表（勿改 status，主 agent 收尾统一处理）

## 铁律
1. **先核实再动手**：#2-#5 标了 done 但备注空——grep 代码确认是否真实现（done≠已实现，历史教训）
2. 只改任务卡列出的文件；禁止动其他代码/测试/文档；禁止 git commit；禁止全量回归（可单跑涉及的测试文件）
3. 实现遵循数据驱动（数值进 game/data/ 表，不进引擎硬编码）；desc/文案中文
4. 最小 diff（patch 工具对 CRLF 多行替换会加错缩进——遇到就用 V4A 行式补丁或 Python 脚本行级改）
5. skills.py 中文 key 在工具输出会被脱敏显示（`***`）——证据用 Python open+正则取
6. 报告：`workspace/feedback_fix/audit_<编号>.md`（只允许 workspace/feedback_fix/ 新建文件）

## 意见清单（7 条）
| # | 内容 | 状态 |
|---|---|---|
| 1 | 查看职业信息 | ✅已做（v130.2g『职业』指令，勿动） |
| 2 | 购买物品加 *数量（批量购买） | 标done待核实 |
| 3 | 怪物搜索功能（怪物在哪出没） | 标done待核实 |
| 4 | 副业要专门找导师学太麻烦，前期引导差 | 标done待核实 |
| 5 | 背包页数建议放底部 | 标done待核实 |
| 6 | 采集有 bug，采集后没有东西 | new 待修 |
| 7 | 技能升级之后描述不变 | new 待修 |