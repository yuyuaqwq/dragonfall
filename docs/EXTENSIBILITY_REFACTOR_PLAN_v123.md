# v123 列表翻页快捷键 + 快捷指令后缀（功能计划）

日期：2026-08-16 · 鱼鱼需求原文：「发送 + 或 +n 向后 1/n 页；- 类似；= 直接跳转指定页；快捷指令支持附带后缀（绑定 n→前往，n1=前往 1）」

## 一、设计决策

### 1. 通用「上次列表」状态（复用背包 v104 M24 相对翻页的 event_state 模式）
- key：`last_list_{qq_id}`（players 表主键即 qq_id，无需 group_id）
- value：`{"cmd": "背包 材料", "page": 2, "pages": 5}`
  - `cmd` = 重建指令文本（**不含页码**，含分类参数），翻页时拼 `f"{cmd} {new_page}"` 走 `_run_shortcut` 转发执行 → **零侵入渲染逻辑**
- 新增 `CommandBase._record_list_state(qq_id, cmd, page, pages)`（base.py，json 封装 set_event_state，异常吞掉）

### 2. 翻页快捷键 handler（player.py 新增 `page_flip`）
- 单正则三符号：`^(?:\[At:\d+\]\s*)?[+＋\-－=][0-9０-９]*\s*$`
  - `+` / `＋` → +1 页；`+n` → +n 页
  - `-` / `－` → -1 页；`-n` → -n 页
  - `=n` / `＝n` → 直接跳 n 页（`=` 无数字 → 提示用法）
- 流程：解析 op+n → 读 `last_list_{qq_id}` → 无状态提示「先打开一个列表」→ 新 page clamp [1, pages] → 拼指令 → `_run_shortcut(event, text)` 转发 → `_stop_event_safe`
- 已 grep 确认：无任何既有指令以 `+/-/=` 开头，无冲突；符号开头不会命中对话树/物品模式/移动模式/NPC 序号（均纯数字匹配）

### 3. 快捷指令后缀（player.py `shortcut_trigger` 改造）
- 正则 `^[...][0-9０-９]\d*\s*$` → `^[...][0-9０-９]\d*[\s\S]*$`（数字开头，后任意）
- handler：数字前缀归一化查表；无后缀 → 原触发逻辑；有后缀 → `_run_shortcut(event, f"{cmd_text} {rest}")`
- 冲突安全：带后缀的数字消息不会命中对话树/物品模式/NPC 序号（均纯数字匹配），快捷指令本就是最后兜底层
- 全角数字前缀（`１３`）也要支持归一

### 4. 列表接入清单（渲染尾部调 `_record_list_state`，cmd 重建格式）
| 列表 | 文件 | cmd（拼页码后走 _run_shortcut） |
|---|---|---|
| 技能列表 | combat.py `_skill_list_page` | `技能列表` |
| 炼金 | economy.py 966-1004 | `炼金` / 提纯 → `炼金 提纯` |
| 烹饪列表 | economy.py 1107-1135 | `烹饪列表` |
| 锻造全部 | economy.py 2024 附近 | `锻造 全部` |
| 锻造分类 | economy.py 2045 附近 | `锻造 <职业名>` |
| 锻造列表 | economy.py 1996-2010 | `锻造列表` |
| 图鉴 | economy.py 2594 附近 | `图鉴` |
| 称号 | economy.py 2814 附近 | `称号` |
| 背包 | economy.py `_bag_view` | `背包` / 筛选 → `背包 <分类>` |
| 商店 | economy.py 3928 附近 | `商店` |
| 市场 | social.py 42 附近 | `市场` |
| 公会 | social.py 577 附近 | `公会` |
| 任务 | world.py 1654 附近 | `任务` |
- gm.py 玩家列表不接入（GM 专用）
- 已确认所有重建指令均支持 `cmd N` 空格页码格式；免空格粘页码（`背包材料2`）不受影响

## 二、版本号
- v123；测试命名 `test_v123_page_flip.py`（翻页 + 快捷后缀 + 全角 + 越界 clamp + 无状态提示）

## 三、同步项
- `_registry.py`：新增 `page_flip` 正则 + 修改 `shortcut_trigger` 正则（test_v87_command_matrix.py 强校验 1:1）
- 策划案 23 章：指令表补翻页快捷键 + 快捷后缀说明（主 agent 收尾同步 design 仓）

## 四、子 agent 拆分（第一轮并行 3 个，只改文件不 commit）
- A 核心：base.py 记录函数 + player.py 双改造 + _registry.py 同步
- B 经济：economy.py 8 处列表接入
- C 战斗/社交/世界：combat.py + social.py + world.py 4 处列表接入
- 第二轮：测试 agent D 写 test_v123 + 全量回归
- 收尾：主 agent 编译检查 → 全量 → 双仓提交 → 策划案同步 → 重启上线

## 五、坑位清单
- _registry.py 必须同步（test_v87_command_matrix 1:1 强校验）
- patch 后 grep 验证 + py_compile（base.py / player.py / economy.py / combat.py / social.py / world.py）
- 并行 agent 互不碰对方文件；提交由主 agent 统一做（先 git status）
- `_record_list_state` 放渲染函数尾部（能拿到 player/qq_id 就渲染函数内记，否则 handler 层记）
- `=n` 越界 clamp 到 [1, pages]；`+n`/`-n` 同理
- 全角 `＋－＝０-９` 必须支持（手机输入法）
