# 玩家意见修复批次 v130.7 公共框架（只读这份 + 自己的任务卡）

## 环境
- 项目根（真实工作区，git 根目录）：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`
- ⚠️ 禁止在临时副本/junction/symlink 上改代码——改了等于没改（历史教训）
- Python 解释器：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 测试权威运行：`python tests/test_xxx.py` 直跑（单文件）

## 铁律（违反 = 白干）
1. **只改自己任务卡列出的文件**；禁改卡外任何文件（代码/数据/文档/测试/策划案）
2. 禁 git commit / stash / reset / checkout；禁动生产库 `game/game_data.db`
3. **最小 diff**：CRLF 大文件（economy.py/combat.py/battle.py/social.py/player.py 等）多行改动必须用 Python 行级脚本（readlines → 按唯一内容锚点定位 → 替换/插入 → `open(w, newline="")` 写回 → `py_compile` 验证）；禁 write_file 整文件重写（会覆盖并行者改动）
4. 数值进数据表/常量，不进引擎硬编码（本项目铁律：数据驱动）
5. 文案中文、风格与既有代码一致（面板块风格、提示用 💡/📄 等 emoji 惯例）
6. 新测试文件：`tests/test_v1307_<主题>.py`。**不碰 scripts/run_all_tests.py**（主 agent 收尾统一登记）
7. 验证用**独立私有临时库**（并行 agent 互清共享测试库会假失败）。模板：
   ```python
   import os, tempfile
   os.environ["GWEN_GAME_DB"] = os.path.join(tempfile.gettempdir(), f"v1307_{你的主题}.db")
   os.environ["GWEN_TEST_MODE"] = "1"
   sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests")
   from conftest import C, E, db, clean_db, Main, FakeEvent, run
   ```
   注意：测试文件本身（tests/test_v1307_*.py）**不能**设置 GWEN_GAME_DB 残留环境（会污染主会话），测试文件的库走 conftest 机制；私有库只用于你的临时验证脚本（放 workspace/ 下，验收完删）。
8. 战斗类测试用 FakeEvent(group_id, qq_id, msg)——**msg 是第三参**（传错前两个参数会把消息当群号）
9. 报告：结论 + 改动 diff 摘要（文件:行号）+ 单测结果 + 遗留问题

## 新测试文件写法（照 test_v1304_use_batch.py 模式）
- 在 tests/ 下新建独立文件（名字 test_v1307_<主题>.py），import conftest 的组件
- 断言真实 handler 输出关键串（运行时实测，不是静态检查）
- 不需要自己设置 GWEN_GAME_DB（conftest 管）
- 跑法：`python tests/test_v1307_<主题>.py` 全绿即可