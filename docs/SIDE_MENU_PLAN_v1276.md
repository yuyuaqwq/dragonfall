# SIDE_MENU_PLAN_v1276 · 支线接取改『多选项自选』方案

> 2026-08-18 格温(主 holder) · 鱼鱼拍板方案C:对话树『有活儿要交给我吗』改为**每个可接支线一个选项**,玩家自选,不再全接。

## 0. 为什么做

现状三处数字对不上:
- 对话外**预告**(world.py `_talk` 里 2929-2938 循环)只显示第一条(有 `break`),实际可接 2~4 条
- 对话树选项只有 1 个『📜 有活儿要交给我吗?』,`action: {side_offer: true}` 在 `_offer_side_quests` 里**全接**
- 玩家被"预告1件、实发N件"打脸(玛莎实证:提示史莱姆果冻、结果连面包贼蓬尾一起接了)

方案:选项改写 `side_menu` → 对话渲染时**动态展开成每支线一个选项**,每项只接一条。预告侧去掉 break 全量显示。

## 1. 目标行为

对话树节点含该选项时,渲染成(按可接支线动态生成,序号连续):
```
━━━━━━━━━━━━
1. 📜 接『史莱姆果冻』(收集史莱姆黏液×5)
2. 📜 接『面包贼蓬尾』(收集被偷的面包×3)
3. 告辞。
0. 结束对话
```
玩家输 1 → 只接史莱姆果冻,然后(按数据配置)回 `after` 节点可继续接别的,或 `__end__` 结束。
**无任何可接支线时该菜单不出现**(仍由 `need: {side_available: True}` 控制)。

## 2. 数据格式(新)dialogues.py

把多支线 NPC 的旧选项:
```python
{"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "action": {"side_offer": True}},
```
改为:
```python
{"text": "📜 有活儿要交给我吗？", "next": "__end__", "need": {"side_available": True}, "side_menu": {"after": "<start节点名>"}},
```
- `side_menu.after`:接完一条后跳转的节点(通常填该 NPC 对话树 `start`,实现"连串接")。
  留空/缺省 → 用选项原 `next`(通常 `__end__`,接完即散场)。
- **本轮只改 4 个多支线且有对话树的 NPC**:`npc_innkeeper`(2)、`npc_tavern_owner`(4)、`npc_guildmaster`(2)、`npc_king`(2)。
  其余单支线 NPC 的 `side_offer` 选项**不改**(单条全接=自选,无感);side_menu 展开引擎对它们同样兼容(将来可换)。
- `need: {side_available: True}` 保留——这就是"没活儿时不显示菜单"的门闩,已有条件无需新写。

## 3. 引擎改动

### 3.1 core/dialogue.py `visible_options(dlg, node, ctx)`(唯一改动点)
遍历 node.options 时,遇到 `opt.get("side_menu")`:
- 取其 `is not None`
- 调用 `ctx.get("side_menu_expand")`(world 注入的回调)→ 返回**动态子选项列表**(含 text/next/action)
- 用返回值替换该选项位置;未注入回调或不满足时直接跳过
- 其余选项逻辑(`check_need`)不动

保持 core 纯逻辑、零 DB:回调由命令层注入。

### 3.2 commands/world.py
**a) 抽公共过滤**:`_side_available_list(group_id, qq_id, npc_id, npc) -> list[dict]`
- 复制现有 `_offer_side_quests`(3651 起)的**全部过滤条件**:`giver==npc_id`、非 `board`、未接、`_sq_unlocked`、`_sq_stats_met`、`min_level`、`require_race`
- 每个返回项含:`sid, name, desc(短desc), objective_text(用 self._obj_text), reward_exp, reward_gold`
- 返回**按 SIDE_QUESTS 定义顺序**的可接支线列表(保证菜单序号稳定)

**b) `_offer_side_quests` 重构仅复用上述过滤**,保持签名与"全接+完成提示"行为不变(旧 `side_offer` action 兼容,单支线 NPC 无感)。

**c) 新增单接**:`_offer_side_quest(group_id, qq_id, npc_id, sid) -> list[str]`
- 接取单条(把现有全接循环体抽成单条函数);`_offer_side_quests` 改为遍历 `_side_available_list` 逐条调它
- 校验 `sid in _side_available_list` 才接,防越权

**d) `_talk_ctx`(3247)注入回调**:
```python
"side_menu_expand": lambda opt: self._side_menu_expand(group_id, qq_id, npc_id, opt)
```
`_side_menu_expand` 函数(新增,welcome 区附近):
- 调 `_side_available_list`;空 → 返回 []
- 每条生成:
  ```python
  {"text": f"📜 接『{name}』({objective_text})", "next": (opt.get("side_menu") or {}).get("after") or opt.get("next") or "__end__",
   "action": {"side_take_one": sid}}
  ```

**e) 预告去 break(2929-2938)**:循环不再 break,把该 NPC 所有可接支线都输出 `📜 支线『{name}』可接取……`;过滤条件与 `_side_available_list` 对齐(直接复用该函数更好——预告=菜单=实际三处同源)。

### 3.3 commands/talk_actions.py
新增注册 `side_take_one`(参照 227 行 `side_offer`):
```python
@register("side_take_one")
def action_side_take_one(world, group_id, qq_id, player, npc_id, action):
    sid = action.get("side_take_one")
    npc = C.NPCS.get(npc_id) or C.ALL_WILD.get(npc_id) or {}
    if not npc or not sid:
        return []
    return world._offer_side_quest(group_id, qq_id, npc_id, sid)
```

## 4. 测试(tests/test_v1276_side_menu.py,新文件)

按 tests/test_commands_dialogue.py 的现有套路(world = ...; 调用 handler/方法;check 断言)。至少覆盖:
1. **展开数量**:玛莎对话树 welcome 节点含 side_menu 选项时(新玩家、无任何支线 in side),渲染出 2 个子选项,文本含『史莱姆果冻』『面包贼蓬尾』
2. **单接**:点其中一项 action `side_take_one: s1` → player side 只有 s1,没有 s111
3. **隔离**:再点 s111 → 两条都在,各自独立
4. **after**:接完 next 指向配置的 after 节点(玛莎配 welcome → 返回 welcome)
5. **预告全量**:`_talk`(对话前引导)输出含两条『可接取』,不再只有 1 条
6. **单支线 NPC 不破坏**:镇长(mayor)对话树不含 side_menu 键 → 原行为不变(回归)

## 5. 不做的

- 不改 `_c_side_available` 条件(已能正确表达"有未接支线")
- 不删 `side_offer` action(兼容保留)
- 不改其余单支线 NPC 数据
- 不动限时NPC/懒计时引擎(v127.5)

## 6. 验证

- 引擎 A 自测:自己的独立测试库跑相关测试;**不要跑 run_all_tests 全量**(多 agent 并行共用库互清,主 holder 合并后统一跑)
- 各子 agent 改完**只做语法自检**(python -m py_compile / import),不并行跑全量
- 合并后主 holder 用干净测试库跑全量回归 168+
- 双仓提交:插件仓 `0271511`(当前 HEAD)基础上新增;策划案 03/19/23 章对应段落同步
- 重启 AstrBot 部署
