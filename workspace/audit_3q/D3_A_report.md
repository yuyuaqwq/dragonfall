# D3-A 前期（0-29 级）独特装备设计报告

## 挂载表

| 装备名 | rid | 品质 | 等级 | 效果 key | 效果说明 | 获得方式 |
|---|---|---|---|---|---|---|
| 王都誓约之剑 | eq_wang_du_shi_yue_zhi_jian | 橙 | 28 | oath_sword（新） | 暴击时回复 2% 最大生命（新手第一件独特装备：第一次见特殊效果+第一次见触发型） | boss |
| 咕噜的皇冠 | eq_gu_lu_de_huang_guan | 橙 | 20 | goblin_crown（既有） | 咕噜王的威仪：最大生命＋6% | 图纸→boss |
| 金钩弯刀 | eq_jin_gou_wan_dao | 橙 | 26 | gold_hook（既有） | 金钩锋锐：暴击伤害＋30% | boss |
| 杰克的金钩 | eq_jie_ke_jin_gou | 橙 | 28 | jack_hook（既有） | 处决狂潮：对生命<30% 目标＋80% 伤害 | legend |
| 珍珠项链 | eq_zhen_zhu_xiang_lian | 紫 | 18 | dawn_grace（新） | 晨光恩泽：最大生命＋4%（教学级 stat 型） | 图纸 |
| 海风长弓 | eq_hai_feng_chang_gong | 紫 | 18 | sea_breeze（新） | 海风祝福：闪避率＋3%（教学级 stat 型） | 图纸 |
| 晨露戒指 | eq_chen_lu_jie_zhi | 蓝 | 10 | morning_dew（新） | 晨露滋养：每回合回复 1% 魔力（蓝装轻量示范） | 图纸 |
| 灯塔之光 | eq_deng_ta_zhi_guang | 蓝 | 26 | lighthouse_ward（新） | 灯塔守望：受击伤害－3%（蓝装轻量示范） | 图纸 |

## 新效果清单

| key | 名 | kind | trigger | chance | effect | desc | 数值健康 |
|---|---|---|---|---|---|---|---|
| oath_sword | 誓约之刃 | attack | on_hit | 1.0（条件=暴击） | heal_pct:0.02, on_crit:True | 暴击时回复 2% 最大生命（教学锚点） | ΔE +4~8%（每场 2-4 次暴击触发）；条件=暴击，非暴击流收益趋近 0 |
| dawn_grace | 晨光恩泽 | defense | stat | — | hp_pct:0.04 | 最大生命＋4%（光明主题） | ΔE +2.4%（hp 权重 0.1）；紫装 hp_up 词条 5% 同档略低 |
| sea_breeze | 海风祝福 | defense | stat | — | dodge:0.03 | 闪避率＋3%（海风灵动主题） | ΔE +3%；dodge 词条 5% 同档略低；PCT_STATS 并入 stats 生效 |
| lighthouse_ward | 灯塔守望 | defense | stat | — | dmg_reduce:0.03 | 受击伤害－3%（守护主题） | ΔE +3%；与 dmg_reduce 词条同值；TAKEN_EFFECTS reduce 按 affix id 消费 |
| morning_dew | 晨露滋养 | defense | turn_start | — | pct:0.01 | 每回合回复 1% 魔力（温暖/成长主题） | ΔE +2~3%；与 meditate 词条同值；TURN_START_EFFECTS 按 affix id 消费 |