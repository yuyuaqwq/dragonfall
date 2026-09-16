# design/ 已被清空 —— 策划案仓已移出本仓（2026-09-13）

本目录（原 `design/new_world/`，849 文件 / 10.0 MB）在 **2026-09-13 的 B1 清场**中**整体移出游戏仓**（移出 ≠ 删除）。

## 为什么移

`design/new_world/` 是一个**独立的 git 仓库**（内含自己的 `.git`，独占 7.2 MB）。
外挂仓混进插件目录会让代码仓状态混乱（`docs/archive/ENGINE_CONTENT_SPLIT_PLAN.md` 的 R10 记的就是这个隐患，`.gitignore` 里也只能靠 `design/` 整目录排除）。
鱼鱼拍板 **A 案：保持移出**，并把「策划案同步铁律」改为已退役 —— 见 `DEVELOPMENT.md` §6。

## 现在在哪 / 怎么找回

- **新家（2026-09-13 定案）**：`C:\Users\yuyu\dragonfall-designer\`
  —— 与 `framework-engine` **同级的外挂兄弟仓**，保留它自己的 git 历史与远端
  `git@github.com:yuyuaqwq/dragonfall-designer.git`（设计稿在那里维护、独立提交）。
- **中转站**：B1 清场先把它移到 `...\workspace\_retired\20260913\design\new_world\`，
  同日迁到上面的新家；`_retired\20260913\design\` 只留 `MOVED_TO.txt` 指针，
  `_retired\20260913\MANIFEST.json` 存着这次移出的 1,978 条 `path / dst / bytes / sha256`（可逐字节核对）。

## 源码里的 `design/new_world/...` 引用怎么理解

仓内约 10 处**注释**把 `design/new_world/32_数值设计.md` 等当「数值/设计权威」引用
（如 `game/data/battle_rules.py`、`game/data/classes.py`、`game/store/professions.py`、
`game/commands/combat.py`、`tests/test_v181_batch_d_dot_formula.py`）。
这些注释**沿用旧写法未逐条改** —— 按本文件跳转即可：路径前缀 `design/new_world/` 一律替换为
`C:\Users\yuyu\dragonfall-designer\`（例如 `design/new_world/32_数值设计.md`
→ `C:\Users\yuyu\dragonfall-designer\32_数值设计.md`）。

## 定案（2026-09-13）

设计/数值改动的同步对象 = **外挂仓 `dragonfall-designer`**（见上）。规则：
**不再强制"先策划案再提交代码"**；改数值·新内容·机制时可选更新设计稿，但**必须在代码提交说明里写清设计依据并知会鱼鱼**。
完整口径见 `DEVELOPMENT.md` §6。

> 宿主旧编辑器 `editor/`（技能/词条 2 域 MVP）也在同批退役 → `_retired\20260913\editor\`；
> 现行编辑器 = `framework-engine/editor`（24 域、端口 8766，本仓不再自带编辑器）。

> 本文件是仓内**唯一**被跟踪的 `design/` 文件（`.gitignore` 用 `design/*` + `!design/README.md` 实现），
> 作用是让所有指向 `design/` 的旧路径不再悬空。
