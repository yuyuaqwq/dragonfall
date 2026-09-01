# v153 测试适配规则（给子 agent 的唯一依据）

> 背景：v153 职业重做后，34 个测试文件失败（162 处断言）。失败原因分 5 类，按本规则适配。
> 测试运行：`"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" tests/test_xxx.py`
> 全量回归：`python scripts/run_all_tests.py --serial`（慢，适配完再跑）

## 类别 1：技能数值快照（test_numeric_skill_power / test_numeric_panel_snapshot）
- 锁定表 LOCK 断言旧 power/lv/mp/SKILL_UP.p
- 适配：**从实际数据生成新 LOCK 表**（写个小脚本 import game.data 打印各职业 lv1 技能 + lv[10,15] 档位的 name/lv/power/mp/SKILL_UP.p，把输出写回 LOCK）
- 6 职业 → 7 职业（新增 cls_shi_ren 诗人）

## 类别 2：旧技能名/等级断言（test_commands_skills / test_stage6 / test_v83_bard 等）
- 测试里"学会旋风斩(14级)" → v153 旋风斩是 Lv.20
- 测试里"疾风连射" → v153 改名"连射"（lv1）；"冰霜新星" → 不存在
- 适配：用 v153 技能表（见下方技能名对照）更新测试用技能名/等级

## 类别 3：资源数值（test_stage5_resources）
- 游侠 energy regen 30→18（v153 专注流量制）
- 测试断言"精力 +30/刻" → 改 +18；"消耗 20 精力" → 按 v153 技能 focus_cost 改

## 类别 4：职业数/职业表（test_data_characters / test_v1302g_job_guide）
- 6 职业 → 7 职业（新增 cls_shi_ren 诗人）
- 转职名：法师 元素法师→元素使、奥秘法师→奥术学者/奥术大师/奥秘主宰；游侠 林语者→森语者、自然行者→自然守望者、疾风猎手→狂风之猎；牧师 B 线→死灵祭司/亡魂引渡者/黯灵君主；拳师 磐岩壁垒→不破之壁；诗人 咏叹者/晨曦歌者/天籁颂者 + 挽歌者/安魂歌者/镇魂挽者

## 类别 5：技能机制断言（test_aoe_multi_target / test_commands_battle / test_v109_2 等）
- 断言技能字段（multi/aoe/power/mech）按 v153 新表更新
- 机制 handler 名变化：毒层/灼烧/连段等

## v153 技能名速查（旧 → 新）
- 战士：盾击→盾击·誓、旋风斩 lv14→lv20、铁壁 lv14→lv12、蓄力斩→删除、冲锋 lv26→lv24
- 法师：元素弹幕→骤雨弹幕(lv20)、冰霜新星→删除、元素冲击→织焰、时滞术/时间裂隙/凝时锁/时停领域→删除（时律线删）、元素爆发→元素迸发
- 游侠：疾风连射→连射(lv1)、风之疾走→风之疾走(lv16)、林语印记→猎印射击、淬毒箭矢→淬毒箭、毒爆术→荆棘爆、蓄力狙击→蓄力射击、召唤藤蔓守卫/古树守卫 保留、致命狙击 lv20
- 牧师：圣光弹/圣光惩击→删除、即兴弹唱→删除（诗人独立）、战歌→删除（诗人独立）、鼓舞→删除、圣诗合唱→删除、安魂曲→(诗人) 保留名、召唤骷髅 保留
- 刺客：暗杀→删除、淬毒→毒刃、毒雾→毒雾·淬、疾风连射→无
- 拳师：气力天地→气力通天、碎骨拳→无
- 诗人（新职业 cls_shi_ren）：战歌/守歌/疾歌/拨弦/音刃/安神曲/疾走音/和声 + 咏叹线/挽歌线

## 关键数据文件（只读，别改）
- game/data/skills_v153.py（v153 技能表）
- game/data/classes.py（7 职业定义）
- game/data/core_resources.py（资源配置：energy regen 18 / faith 负载）

## 红线
- **禁止改 game/ 下任何数据文件**（只改 tests/）
- 测试断言失败 = 改测试断言（用实际数据），不是改数据迁就测试
- 真 bug（引擎行为错误）→ 记下来报告主 agent，别自己改引擎
- 每个文件改完跑一遍确认单测绿
