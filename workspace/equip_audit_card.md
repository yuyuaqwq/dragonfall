# 装备/套装改造侦察任务卡

## 背景
v151 职业体系重构：完全抛弃隐藏职业（龙裔/时咒法师/星语者/暗影神谕/暮影行者/淬势者），收束到六基础职业十二战术线。
职业装备及套装也要改造对齐新体系。

主 agent 已侦察：
- equip_roster.py: 208 件（名册 632 件总），武器按 weapon_type（sword/bow/staff/mace/shield/fist/dagger/spear）
- affixes.py: 效果库里 rage×5/element×9/energy×5/faith×4/chi×4/combo×37 绑定旧资源条
- 装备名含隐藏职业词：龙裔×17/暮影×11/龙鳞×12/亡者×7/武僧×2
- sets.py: mark×18/faith×4/rage×3/element×3 绑定旧资源
- class_sets.py: 职业套装（铁皮/精铁/百炼=战士，学徒/符文/秘法=法师等）

## 任务
侦察 `C:/Users/yuyu/qqbot/data/plugins/dragonfall` 装备/套装与职业体系的耦合点：

1. **隐藏职业专属装备**：名册里所有含"龙裔/龙血/龙鳞/时咒/星语/暗影/暮影/亡者/武僧/淬势"等词的装备，列出完整清单（eq_id + 名称 + 归属隐藏职业）
2. **装备效果绑定旧资源**：affixes.py 里 LEGENDARY_EFFECTS / 效果字典中引用 rage/element/energy/faith/cp/chi/combo/zen/dragon 的效果，列出（效果key + 消费的资源 + 现状是否仍有效）
3. **套装绑定旧资源**：sets.py / class_sets.py 里 bonus 引用旧资源条的效果（mark/faith/rage/element/cp/combo），列出
4. **职业武器类型映射**：现有 6 基础职业各用哪些 weapon_type（战士=剑/锤/盾？法师=法杖？游侠=弓？牧师=权杖？刺客=匕首？拳师=拳套？）→ 隐藏职业的武器类型（龙裔=？时咒=？）要并入哪
5. **装备 req 属性**：装备 req 用 str/vit/agi/int，新六职业的主属性映射（战士=str？法师=int？游侠=agi？）

## 输出格式
写报告到 `C:/Users/yuyu/qqbot/data/plugins/dragonfall/workspace/equip_audit_report.md`：

```markdown
# 装备/套装改造侦察报告
## 1. 隐藏职业专属装备清单（eq_id / 名称 / 归属）
## 2. 装备效果绑定旧资源清单（效果key / 资源 / 现状）
## 3. 套装绑定旧资源清单
## 4. 职业武器类型映射表
## 5. 装备 req 属性映射
## 6. 结论：装备/套装改造的改动清单（按文件分组）
```

## 铁律
- 只查不改，禁 git commit
- 每条带 `文件:行号` 证据
- 用 grep 定位，不要整读大文件（equip_roster.py 183KB）
- 不跑全量回归
- 注意：sk_ 开头的字符串会被 Hermes 显示层脱敏（***），用 Python 原生读文件核实
