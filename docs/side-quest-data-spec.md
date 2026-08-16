# 支线剧情线数据落地规范（v124 数据驱动字段）

> 目标：21 份设计稿 → SIDE_QUESTS 纯数据条目。**零特例代码**——所有新机制都是通用字段，由通用逻辑消费。

## 1. SIDE_QUESTS 条目新字段（全部可选）

### 1.1 链式解锁 `unlock`
前置条件，满足后才可接取。支持单条或列表（列表=全部满足）。

```python
"unlock": {"side": "s5"}                 # 完成支线 s5 后解锁
"unlock": {"main": "q2_3"}               # 主线推进到 q2_3（completed_main 含它或当前主线==它）
"unlock": [{"side": "s5"}, {"main": "q2_3"}]  # 全部满足
```

### 1.2 动作计数门槛 `require_stats`
隐藏线/副业线触发用：stats 表字段达标才可接取。

```python
"require_stats": {"fish_count": 10}      # 垂钓 10 次后可接
"require_stats": {"craft_count": 20}     # 锻造 20 次后可接
```
合法字段（stats 白名单）：fish_count / gather_count / mine_count / cook_count / alchemy_count / craft_count / enhance_count / explore_count（如有）

### 1.3 use 目标 objective
使用指定物品后达成（配合 collect 或独立）。

```python
"objective": {"use": "麦酒"}             # 使用麦酒后 ready
"objective": {"use": "白桦的余烬", "collect": "月光草", "count": 3}  # 复合
```

### 1.4 分支交付 `branch`
交付时二选一/多选一。有 branch 的条目**不要**给顶层 reward_exp/reward_gold/reward_item（分支里给），顶层可留 reward_exp=0/reward_gold=0。

```python
"branch": {
    "prompt": "铁弓看着你，声音沙哑：『……你带回来的，是活着的他，还是别的什么？』",
    "options": [
        {
            "key": "1", "label": "带他回家",
            "text": "你把白桦扶上马背……（交付剧情）",
            "reward_exp": 6000, "reward_gold": 3000,
            "reward_item": "白桦护符",
            "title": "北境的恩人",       # 可选：发称号
            "flag": "s18_branch_light"   # 可选：存玩家 flag
        },
        {
            "key": "2", "label": "给他解脱",
            "text": "……你按下了那一下。",
            "reward_exp": 6000, "reward_gold": 3000,
            "reward_item": "白桦的余烬",
            "title": "长夜行者",
            "flag": "s18_branch_dark"
        }
    ]
}
```

### 1.5 剧情文本
- `story`：接取台词（现有字段，设计稿的「接取台词」）
- `progress_text`：进行中与 giver 对话的台词（设计稿的「推进台词」）
- `deliver_text`：交付时奖励前的剧情文本（设计稿的「交付台词」；有 branch 时放 options[].text）

## 2. 现有支线串链
串入剧情线的现有支线：**不动原有字段和奖励**，只加：
- `chain`: "线名"（展示用，如 "教会的阴影"）
- 若某现有支线是链中一环且需要前置，加 `unlock`
- 原支线保留独立可接性（unlock 只作用于链式接取场景，设计稿已标注）

## 3. 新 NPC 数据落地
- 城镇 NPC → `game/data/npcs.py` NPCS dict（键 npc_xxx）
- 野外 NPC → `game/data/wild_npcs.py` WILD_NPCS dict
- 隐藏 NPC → `game/data/wild_npcs.py` HIDDEN_NPCS dict
- 字段：name/title/map/icon/funcs/dialogue/lore/gender（可选）/subarea（可选，子区域定位）
- 副本内 NPC → 标注「需加 INSTANCE_STAGE_NPCS」（落地时评估）

## 4. 新物品/材料/称号
- 消耗品/装备 → `game/data/items.py`（用现名优先；新物品标注「需新增」并在该文件登记）
- 材料 → `game/data/materials.py` 或对应材料表
- 称号 → `game/data/achievements.py` titles（查重 14 章）
- 奖励引用一律用物品中文名（消费端 resolve items→materials 顺序）

## 5. 编号规则（全局重排，防并行冲突）
- 新增支线统一 s46 起顺序编号（s46-s90+），按设计稿「06 章策划案文本」登记顺序
- 隐藏线 H5-H8 内部 id 用 hq5_1/hq5_2/... 前缀（避免与 02 章隐藏区域 H5-H7 混淆）
- 分支线如 S18 改造：保持 s18 id 不变，加 branch 字段

## 6. 落地后验证
- 每条新支线：unlock 检查 → 接取 → objective 推进（kill/collect/explore/find/use）→ 交付（含分支）
- 黑名单词扫描：灭世/弑神/虚空/血怒/屠戮/金身/不动如山/百裂/气功/金刚/罗汉/内力/内息
- 奖励梯度：经验≈金币×2，金币档位参考同等级现有支线
