# 数值测试机制（v130.9 建立）——公共框架

## 目标
以后任何改动（技能/怪物/装备/属性加点/CTB/掉落/成长公式/伤害公式/数据表数值）都必须跑 `scripts/run_numeric_tests.py` 全绿才能提交。数值测试 = 平衡快照 + 区间约束，防止"动了数值不知道动了"。

## 环境（同 FRAMEWORK.md）
- 插件根 `C:\Users\yuyu\qqbot\data\plugins\dragonfall`（真实工作区，禁临时副本）
- Python: `C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 禁 git / 禁生产库 / 最小区块

## 模拟战斗基础（所有胜率类测试共用）
- 直接构造 `BT.Battle`（game/battle.py:209 `Battle(btype="monster", enemy=怪dict, player=玩家dict)`）循环 `player_turn("attack"/"skill", ...)` 直到 `b.result`
- 固定种子序列（seed 0..N-1）保证可复现
- 玩家 dict 构造：
  ```python
  st = E.player_final_stats(cls, lv, equip, 0, attr)
  player = {"class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": equip, "attributes": attr, "learned_skills": [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None}
  ```
- 怪构造：`C.build_monster((id, 名, role, lv, [掉落], []), {"id": id, "name": 名, "area": "field", "lv": lv})`
- 参考已实装模拟模式：workspace/v1307 的 sim 脚本思路（battle.py 直接构造）

## 你的任务卡规定的测试文件写法
- 每个测试文件独立可跑：`python tests/test_numeric_xxx.py`
- 全部用真实 handler/引擎（E.player_final_stats / C.build_monster / BT.Battle），不 mock 核心公式
- 断言失败信息带实际值（方便基线更新）
- **当前基线 = 当前代码锁定**（含已知失衡点，如 CTB 行动频率 15 倍——CTB 修复后由主 agent 统一更新断言，你不需要修代码）

## 铁律
1. 只新建自己卡里的文件；禁改 game/ 源码；禁改既有测试
2. 禁 git / 禁生产库 / 测试走 conftest 机制（不设 GWEN_GAME_DB 残留）
3. 报告：文件清单 + 断言数 + 通过数 + 遗留