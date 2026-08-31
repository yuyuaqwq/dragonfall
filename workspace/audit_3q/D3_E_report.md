# D3-E 终局（90+ 级）独特装备设计报告

## 挂载表

终局（90+）独特装备 28 件 = 橙装 23 件全挂 + 紫装 5 件 + 已定龙鳞庇护之坠 1 件。

【橙装 23 件全挂】20 件已有专属/特效（element_apostle_pendant 元素使徒坠饰90/star_slayer_edge 弑星巨刃90/arcane_firmament 奥术苍穹之冠90/death_dance_armor 亡舞战铠90/dragon_tongue 龙语圣剑92/time_lord_scepter 时之领主秘仪92/moon_bow 风神之环92/gargoyle_heart 石像鬼之心92/eternal_codex 永契法典92/everfrost_scepter 永霜权杖94/aura_seal 奥拉圣印95/chu_huo 灰烬圣剑·初火95/earth_heart 精制龙裔胸甲·护腿·之靴95×3/endless_blade 无终之刃95/mu_ying_blade 暮影之刃96/dawn_light 黎明之光98(深渊特攻+50%)/moro_crown 摩罗之冠98/starfall 星陨之剑100(全屏AOE 200%)）；3 件缺定义用新效果补库（★蚀夜之面 eq_shi_ye_zhi_mian 98→night_eater_mask 蚀夜 暗夜闪避+8%、★风暴之冠 eq_feng_bao_zhi_guan 98→storm_crown 雷属性伤害+20%、★云怒之核 eq_yun_nu_zhi_he 100→cloud_rage_core 雷属性伤害+20%——三件名册 leg 字段已就位仅缺 LEGENDARY_EFFECTS 数据，零改名册）。

【紫装 5 件·终局最高强度件】黑渊之眼 eq_hei_yuan_zhi_yan 92 boss→star_destruction 星陨湮灭(对深渊系+30%伤害)；深渊骑枪 eq_shen_yuan_ji_qiang 94 精英专属→dragon_annihilation 灭龙(对龙系+25%伤害)；辰光法杖 eq_chen_guang_fa_zhang 98 精英专属→divine_execution 神罚处决(对生命<30%目标+60%伤害)；雷霆护肩 eq_lei_ting_hu_jian 96 精英专属→retribution_ring(复用既有：受击20%反弹30%伤害)；骸王骨面 eq_hai_wang_gu_mian 92 精英专属→guardian_will(复用既有：受击8%使敌人下次攻击-25%)。未挂 6 件：圣辉法衣(图纸源非最高难)不挂；幻影长弓/苍穹之冠/泰坦护腿/虚空行者之靴/龙脊鳞甲已自带 weapon_effect 特效不重复挂。

【已定·鱼鱼点名】龙鳞庇护之坠→dragon_scale(D2)：全元素抗性+15%、深渊抗性+5%，代价最大生命-10%，终章剧情必得全服唯一，待主 agent 落位名册。

橙 23/23=100%，紫 5/11≈45%（任务卡 5-6 件取 5），覆盖率终局 28/34=82%，白绿蓝 0 独特。同阶段效果 key 两两唯一（earth_heart 三件为精制龙裔套件既定共享标注）。

## 新效果清单

6 个新效果（终局主题：传说/龙/神/星/毁灭），全部 stat 型或 passive 条件型，effect 键全复用引擎既有语义，零引擎改动：

E1 night_eater_mask 蚀夜｜defense｜stat｜dodge:0.08｜暗夜闪避+8%｜兑现名册 desc 既有文案，dodge<cap0.4，ΔE≈+4%
E2 storm_crown 风暴之冠｜attack｜stat｜thunder_dmg:0.20｜雷属性伤害+20%｜兑现 desc，与 aura_seal 同值同档，ΔE≈+5%
E3 cloud_rage_core 云怒雷核｜attack｜stat｜thunder_dmg:0.20｜雷属性伤害+20%｜同 E2/aura_seal，ΔE≈+5%
E4 star_destruction 星陨湮灭｜attack｜passive｜dmg_mult:1.30, enemy_contains:["深渊"], tag:"☄️星陨湮灭"｜对深渊系敌人+30%伤害｜深渊特攻(任务卡点名)；1.30<黎明之光1.50 不超车；消费链同 dawn_light(battle.py:3033)
E5 dragon_annihilation 灭龙｜attack｜passive｜dmg_mult:1.25, enemy_contains:["龙"], tag:"🐉灭龙"｜对龙系敌人+25%伤害｜龙特攻；与既有词条 dragon_aw(龙威 1.25)同值同条件不超车
E6 divine_execution 神罚处决｜attack｜passive｜dmg_mult:1.60, execute_threshold:0.30, tag:"⚡神罚处决"｜对生命<30%目标额外+60%伤害｜处决(任务卡点名)；1.60 位于 ancient_king 1.35 与 jack_hook 1.80 之间，终局最强处决仍是杰克的金钩不被动摇

铁律核验：trigger 六种白名单内(stat×3+passive×3)；强效果全有条件(深渊限定/龙限定/斩杀线限定)；总强度全部落在±15%铁律内且无一件超过既有同机制专属；与全阶段已设计 key(A5+B12+C6+D6+D2 24+既有29+weapon_effects 78)程序核对零撞车。