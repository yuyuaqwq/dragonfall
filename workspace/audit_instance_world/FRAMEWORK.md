# 副本与野外合并审计 — 公共框架

> 任务：审计 dragonfall 插件「副本 vs 野外」是否已真正合并、逻辑是否通用。
> 角色：**只读审计 agent**。禁改任何代码/数据/文档，禁 git commit/stash/reset，禁重启服务，禁动生产库 game/game_data.db。
> 真实工作区 = git 根目录 `C:/Users/yuyu/qqbot/data/plugins/dragonfall`。禁止在临时副本/junction/symlink 上操作。
> Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`（唯一带 pypinyin 的解释器）。系统 python 缺依赖。
> 测试纪律：禁跑全量 `scripts/run_all_tests.py`（并行 agent 会污染共享 test_game_data.db）——只许跑你自己的**独立私有库单测**（`GWEN_GAME_DB=<临时文件>` 前缀），或只读脚本。
> 报告每条发现必须带 `文件:行号` 证据；先给"我摸了哪些文件/统计数"证明覆盖，再列发现。
> 收尾：确认自己没留下任何临时文件（`git status` 只能有审计前就存在的未跟踪文件）。

## 背景（2026-08-30 快照，来自主 agent 侦察）

- v137 副本地图化已落地：副本 = MAPS(type=副本) + SUBAREAS + SUBAREA_LINKS_INDEX 封闭地图，dungeon 修饰符（no_exit/discovery_agro=0.85/boss_room/on_clear）在 `game/data/maps.py`。
- 地图模式：world.py 的 `_instance_dungeon_move`（1655 行）+ `_travel_ambush` 遇怪 + instance.py 薄壳（开本/结算/奖励）。
- v137 Phase2 已把 `BT.Battle` btype="instance" 收编进 battle.py（225/254/1423/1757 行，`_inst_*` 方法群）。
- v141 大陆隔离：`game/core/worlds.py`（instance_worlds 动态大陆）+ `game/core/position.py`（Position 结构体），玩家 world_id 字段，开本创建大陆实例、撤退保留、离开/失败销毁、退队回滚、孤儿自愈。
- 全量 225/225 绿（v141 已提交，git log c0ac0fc）。
- **主 agent 侦察到的疑点**：instance.py 仍 3375 行（v137 前 2518 行），仍保留 `_instance_*` CTB/仇恨/人数缩放方法群（_instance_next_actor/_instance_apply_enemy_act_ct/_instance_enemy_one_act 等）+ `_stage_virtual_map` 老层全景——疑似**双轨并存**（老战斗模式 vs 新地图模式），需要你确认：哪些老路径还在被玩家触达，哪些是死代码。

## 铁律（针对副本/野外）

1. **以玩家触达为准**：判断一段代码是不是死代码，要 grep 谁调用它（命令 handler → 方法链），不要只看"有没有 def"。命令入口看 `game/commands/_registry.py` 和 `main.py` 的指令路由。
2. 副本 id 两套：`inst_xxx`（INSTANCES key）与 `xxx`（MAP_BY_ID key），`_inst_map_id` 做转换——注意它是否被一致使用。
3. 报告格式：
   - P0 = 玩家可触达的真 bug（会崩/会卡/会丢进度/明显逻辑错）
   - P1 = 双轨并存但暂时不崩（老代码还能走到，但和新逻辑冲突/冗余维护成本）
   - P2 = 死代码/已无引用/纯维护负担
   - P3 = 文档与实现不一致
4. 每条结论给出：路径证据（谁调用谁，文件:行号）+ 判定理由。
