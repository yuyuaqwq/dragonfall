# v130.2f/f.1 上线前审计 · 公共框架（2026-08-26）

## 环境事实
- 项目根：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`
- Python（唯一）：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- AstrBot 在线（PID 32472，端口 6185/6199），回环通道：`scripts/loopback_client.py`（用法见文件头注释）
- 测试权威运行方式：`python tests/test_xxx.py` 直跑模式（非 pytest）；全量 = `scripts/run_all_tests.py`
- 当前生产库 game/game_data.db（只读查询可以，不写）

## 铁律
1. **只查不改**：禁止修改任何源码/测试/文档/数据文件；禁止 git commit；禁止跑全量回归（并行污染）
2. 验证手段：read_file / search_files / python -c 只读脚本 / 独立临时 SQLite 连接（只读模式）+ 回环指令（gm_t 身份，见任务卡）
3. skills.py 中文技能 key 在工具输出层会被脱敏显示（`***`/截断）——**脱敏是显示假象，磁盘文件完好**；证据用 Python open+正则 取
4. 报告格式：模块统计 + P0/P1/P2/P3 清单（级别 | 现象 | 文件:行号证据 | 影响）+ 体验/风险总结；不确定标 ⚠️
5. 全部中文

## 上下文：v130.2f/f.1 刚落地的改动（审计重点面）
- v130.2f（提交 39eeb11）：时停领域满沙cond×1.3 / 流星陨落满印cond×1.15 / 龙焰吐息龙力≥8×1.2；被动节拍器改版（鹰眼 mark_extra 0.15、战争咆哮 res_gain_bonus、磐石体 dmg_taken res_gain、墓穴护甲、神圣坚韧、魔力贯穿 attack_res time_sand）；引擎挂点（亡灵祭仪、反击回气+2、致命预谋首次终结返还 1CP、歌者伴奏 20% 回声）；overflow_shield 战士/拳师；desc 收敛 5 处；cond 施放前快照 `_pre_cost_res`（battle_conds.py:150 读快照，HC-12）
- v130.2f.1（提交 62ca50b）：暮影潜行乘区 `SHADOW_STEALTH_DMG_MULT={"终结·破影一击":1.5,"幽影刃":1.25}`（battle_config.py:174，battle.py 消费+🌙标签）；苦修禅意持有加伤 `ZEN_HOLD_CFG={"per_zen":0.04,"cap_zen":10}`（battle_config.py:159，battle.py:1096-1108 `_zen_hold_mult`，技能/普攻双通道+🧘标签）；苦修档位改名 苦修士→淬势者、大地武僧→锻势行者（classes.py 展示层，key 不动，旧名留别名）；龙脉每层 0.18→0.10（battle_config.py:21 MECH_STACK_BONUS，终曲 8.96→6.4）
- 关键交互点：消费技的 `_pre_cost_res` 快照 / consume_all 套装减免留残点（元素使徒 4 件 -1、余烬军团 4 件）/ 受击清空影步 / 回声 max3 驻留 / overflow_shield 冷却 1 回合

## 报告落盘
- 报告写入 `workspace/qa_v1302f/audit_<你的编号>.md`（workspace 目录允许新建文件，别处不许）