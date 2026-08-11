# 《剑与魔法》对话引擎审计 + NPC 台词陈旧修复（v101.23 系列）

> 日期：2026-08-11
> 触发：鱼鱼发现镇长做完史莱姆任务后，开场白/选项仍念旧任务（v101.23 修复台词变体 → v101.23c 修复选项残留）→ 顺藤摸瓜全量审计 22 个对话树 NPC + 审查引擎可扩展性。
> 审计脚本：`scripts/audit_dialogue_stale.py`（关键词扫描：台词绑定任务剧情但无变体/无入口条件 = 陈旧风险）。**本报告所有"仍存在/已修复"结论均基于重跑脚本验证**，非初报记忆。

---

## 一、NPC 陈旧台词问题清单（重跑 audit_dialogue_stale.py 实测）

### 🔴 真问题（任务 NPC 台词不随主线切换，已修复 ✅）

| # | NPC | 节点 | 问题 | 修复版本 |
|---|---|---|---|---|
| S1 | 镇长 npc_mayor | welcome | 开场白写死"史莱姆拱麦田"（q1_1 做完还念） | **v101.23** texts 变体：q1_1 done → "麦田的事多亏了你" |
| S2 | 镇长 npc_mayor | quest_talk | 接取台词写死史莱姆（镇长有 q1_1/q1_3/q1_4/q1_6 四个主线） | **v101.23** texts 变体：q1_3 野猪 / q1_4 哥布林 / q1_6 喝酒 |
| S3 | 镇长 npc_mayor | welcome/town 选项 | 选项 1 还显示"史莱姆是怎么回事？" | **v101.23c** 新增 `not_quest_done` 条件（注册表 ~6 行）+ need 隐藏 |
| S4 | 镇长 npc_mayor | dogs 节点 | 会话残留时 dogs 还念史莱姆；"解决它们/麦田损失"选项指向旧分支 | **v101.23c/c2** dogs 台词变体 + 选项 need 隐藏 |
| S5 | 矮人长老 npc_dwarf_elder | welcome | 写死"地精霸占矿洞，帮我夺回"（q8_3 完成后还喊） | **v101.23c2** texts 变体：q8_3 done → "矿洞的事你功不可没" |
| S6 | 矮人长老 npc_dwarf_elder | quest_talk | 写死"矿洞的事交给你了"（长老有 q8_3/q8_5 两个主线，q8_5 是找酒桶） | **v101.23c2** texts 变体：q8_5 pending → 酒桶台词 |
| S7 | 吟游诗人 npc_bard | welcome | 传闻"矿洞被地精占了"（q8_3 后过时） | **v101.23c2** texts 变体：q8_3 done → "矿洞总算消停了，隧洞之王传说还在流传" |

### 🟡 判定为"可接受"（不是陈旧，审计脚本误报，已人工确认）

| NPC | 节点 | 关键词 | 判定理由 |
|---|---|---|---|
| 酒馆老板娘 npc_innkeeper | gossip | 隧洞/矿洞 | 世界观传闻闲聊（隧洞之王彩蛋），非任务台词；welcome 是住宿招呼，无任务绑定 |
| 生活职业导师 ×7（草药/矿/渔/厨/炼金/锻造/强化） | practice_*/master_* | 草药/矿石/鱼 | **职业学徒流程**台词绑定职业内容（本来就是"采草药/挖矿/钓鱼"考验），入口有 `not_apprentice` 条件保护，学徒完成后入口自动关闭，不会出现"主线推进后还念旧台词" |
| 职业导师 ×6 | chat | 白鹿城 | 世界观介绍（主城名），非任务台词 |
| 镇长 npc_mayor | town | 隧洞 | 介绍吟游诗人莉莉的传闻，世界观引入 |
| 武僧导师 npc_monk_tutor | welcome | 海 | 待复核（未读到全文，海=海外武学源流，世界观类概率高） |

> 审计脚本 46 个"风险节点"中：7 个真问题（已修）、~10 个职业流程伪报（apprentice 保护）、其余为世界观闲聊/传闻。

---

## 二、对话引擎设计审查（可扩展性）

### 分层架构（现状）

```
data/dialogues.py        纯数据：22 个 NPC 对话树（1138 行）
core/dialogue.py         引擎纯逻辑（67 行）：get_dialogue/dialogue_node/check_need/visible_options/node_text
core/dialogue_conds.py   条件注册表（204 行，~30 条件）：register 装饰器 + CONDITIONS dict
commands/world.py        命令层：find_npc(入口)/talk_choice(推进)/_apply_talk_action(动作落地)/
                         _render_talk_node(渲染)/_talk_ctx(上下文)/_talk_quest_progress(talk 型任务)
store 层                 db.get/set/clear_talk_state、talk flags（会话状态）
```

### ✅ 设计优点（已具备的高扩展性）

1. **加新 NPC = 纯数据**：DIALOGUES 加一条，引擎零改动；测试自动校验"对话树引用全部合法 / NPC 全部存在"
2. **条件注册表化**（v98.3）：加条件 = `@register("xxx")` 函数 ~5 行，check_need 零 if-elif；本次 `not_quest_done` 就是现挂的
3. **动作声明式**：action dict（set_flag/give_gold/quest_take/...）由命令层统一落地，数据不写副作用代码
4. **节点台词条件变体**（v101.23）：`texts=[{need, text}]` 取第一个满足 need 的，NPC 台词随主线/状态自动切换——镇长/长老问题的基础设施
5. **giver 校验**（v101.23）：`quest_pending/ready` 动态判断时校验"当前主线发布者 == 对话 NPC"，从机制上杜绝"镇长替小艾发任务"
6. **引擎可单测**：core 不碰 DB/QQ，56 个对话测试独立进程可跑
7. **会话惰性失效**：NPC 不在当前地图 → 会话作废，无残留状态

### ⚠️ 可改进点（分级，供后续迭代）

| 级别 | 问题 | 位置 | 说明 |
|---|---|---|---|
| **A 级（建议做）** | 多任务 NPC 台词切换靠**人工维护 texts 变体** | dialogues.py 各 quest_talk | 镇长/长老都是手动写变体。理想：quest_talk/quest_done_talk 支持**任务数据回退**——无匹配变体时用当前主线任务的 `story`/`ending` 字段自动生成接取/交付台词（quests.py 里本来就有每任务的台词）。人工维护漏一个 = 又出 S5/S6 类问题 |
| **B 级（值得做）** | 动作落地是 if-elif 链（~90 行） | commands/world.py `_apply_talk_action` | 与条件注册表不对称。加新动作 = 改引擎代码。建议 ACTIONS 注册表与 CONDITIONS 对称（动作函数签名 `fn(ctx, action, ...) -> [通知行]`），纯内容扩展零引擎改动 |
| **B 级（设计缺口）** | 选项文本不支持变体 | core/dialogue.py `visible_options` | texts 只覆盖节点台词。选项文字只能"隐藏"不能"换文案"。目前隐藏方案够用（话题消失=不该有入口），但如要"同一选项位置换文案"需扩展 |
| **C 级（顺手）** | 陈旧台词无自动化防线 | scripts/audit_dialogue_stale.py | 审计脚本已就位（本次顺手写的），可挂进 run_all_tests 作为静态检查：台词含任务关键词且无变体 → 警告。防止以后加任务/NPC 再犯 |

### 🟢 合理不动

- 会话状态存 event_state（`db.get_talk_state`）：轻量、按 (group, qq) 维度，无冗余
- `quest_status` 通用节点：与任务系统解耦，任务提示动态生成
- 未知条件放行（`CONDITIONS.get(k) is None → continue`）：向后兼容，旧数据不崩

---

## 三、踩坑记录（本次）

1. **导入循环**：脚本直接 `from game.core.dialogue import ...` 报 circular import——必须走 conftest 的完整包路径 `data.plugins.dragonfall.game`（先导入 game 顶层包初始化 data/_assembly，再导 core）
2. **运算符优先级**：`return v not in (...) or []` 语义错乱（`or` 优先级低于 `not in`），写成先取变量再判断
3. **playtest 子 agent 并发改 world.py**：v95r65 支线修复与本次对话改动同文件，git add -A 时被一起带入提交（功能无冲突，但提醒：并发改同一 repo 时提交前 git log 确认谁带了什么）

---

## 四、遗留项

- [ ] A 级建议：quest_talk 任务数据回退（story/ending 自动生成台词）——需要设计数据格式，单独立项
- [ ] B 级建议：动作注册表化 ACTIONS（与 CONDITIONS 对称）
- [ ] C 级建议：audit_dialogue_stale.py 挂进测试作为静态检查
- [x] ~~复核 npc_monk_tutor.welcome"海"台词~~（2026-08-11 已确认：武僧背景意象"码头搬货的汉子，一拳能打碎海浪"，纯世界观，无风险）
- [ ] q8_5 完成后（主线离开长老线）welcome 变体是否需要第三态（目前 q8_3 done 变体一直生效，q8_5 做完也显示"矿洞的事你功不可没"——可接受）
