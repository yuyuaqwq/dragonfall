# 宠物/坐骑系统扩容文档（v101.11 - v101.15）

2026-08-11 鱼鱼拍板「全做吧」：宠物/坐骑四个方向全上。
品质统一复用 equipment.QUALITY 5 档（⚪普通/🟢优秀/🔵稀有/🟣史诗/🟠传说），全项目一致。

## 一、现状（扩容前 → 后）

| 项目 | 前 | 后 |
|---|---|---|
| 宠物品种 | 4 | 14（白2/绿3/蓝3/紫4/橙2） |
| 坐骑品种 | 3 | 10（白2/绿2/蓝2/紫2/橙2） |
| 宠物技能类型 | 4（atk/matk/heal/block） | 8（+lifesteal吸血/pierce破防/buff_atk加攻/crit_up暴击） |
| 坐骑效果 | 2（传送折扣/精英率） | 7（+stamina_reduce/sell_bonus/collect_bonus/fish_bonus/exp_mult） |
| 战斗台词 | 无 | 全部宠物自带 3 条随机台词 |
| 蛋掉落表 | combat.py 硬编码 | data/pets.py PET_EGG_ROLL 数据化 |

## 二、新增宠物一览（data/pets.py）

| key | 名字 | 品质 | 技能 | 来源 |
|---|---|---|---|---|
| pet_wolf | 森林狼崽 | ⚪ | 撕咬 atk 40%/3T | 兽类怪掉落 |
| pet_turtle | 铁壳龟 | ⚪ | 铁壁缩壳 block 15%/4T | 垂钓blue 8% |
| pet_cat | 黑猫 | 🟢 | 影袭 block 25%/3T | 精英 6.5% |
| pet_rabbit | 月光兔 | 🟢 | 月光祝福 heal 8%/4T | 垂钓orange 15%/采集稀有10% |
| pet_dove | 圣光鸽 | 🟢 | 圣光羽翼 heal 12%/4T | 垂钓blue 5% |
| pet_fox | 冰晶狐 | 🔵 | 霜刃 matk 50%/3T | 兽类怪掉落 |
| pet_salamander | 火尾蜥 | 🔵 | 烈焰尾击 atk 55%/3T | 兽类怪掉落 |
| pet_panther | 影豹 | 🔵 | 狩猎之眼 crit+20%/3T | 精英 3.5% |
| pet_drake | 龙裔幼崽 | 🟣 | 龙息 matk 60%/4T | Boss 12% |
| pet_bat | 血蝠 | 🟣 | 吸血撕咬 lifesteal 30%/4T | 精英 3% |
| pet_armadillo | 岩甲兽 | 🟣 | 碎岩冲撞 pierce 35%/4T | 精英 3% |
| pet_thunderbird | 雷羽鸟 | 🟣 | 雷鸣鼓舞 buff_atk+30%/4T | Boss 8% |
| pet_griffin | 幼年狮鹫 | 🟠 | 狮鹫俯冲 atk 70%/3T | Boss 2% |
| pet_starbutterfly | 星灵蝶 | 🟠 | 星辉治愈 heal 15%/3T | 垂钓orange 8% |

## 三、新增坐骑一览（data/mounts.py）

| key | 名字 | 品质 | Lv | 效果 | 来源 |
|---|---|---|---|---|---|
| mount_horse | 老马 | ⚪ | 1 | 传送-10% | 商店500 |
| mount_donkey | 小毛驴 | ⚪ | 5 | 传送-5% 出售+5% | 商店300 |
| mount_steed | 骏马 | 🟢 | 15 | 传送-20% | 精英6% |
| mount_camel | 铁港驼马 | 🟢 | 20 | 传送-15% 出售+10% | 垂钓purple 5% |
| mount_wolf | 雪狼 | 🔵 | 30 | 传送-30% 精英+5% | Boss 10% |
| mount_reindeer | 北境驯鹿 | 🔵 | 35 | 传送-25% 体力15%免 采集+5% | 采集稀有5% |
| mount_ghost | 幽灵马 | 🟣 | 45 | 传送-40% 经验+5% | Boss 4% |
| mount_unicorn | 森林独角兽 | 🟣 | 45 | 传送-30% 精英+5% 体力10%免 采集+10% | 垂钓orange 8% |
| mount_warhorse | 炎蹄战马 | 🟠 | 55 | 传送-35% 精英+5% 体力10%免 钓鱼+10% 经验+5% | Boss 2% |
| mount_griffin | 狮鹫 | 🟠 | 60 | 传送-40% 精英+10% 体力20%免 出售+10% 经验+10% | 传说Boss极稀有 |

## 四、怎么扩展（数据驱动铁律）

### 加宠物 = 改 data/pets.py 一处
1. PET_POOL 加一条（key 必须 `pet_` 前缀且全局唯一，防 NPCS 式覆盖）
2. 掉落：PET_EGG_ROLL 加一行（role/is_elite/is_boss/name_kw 条件任意组合）或生活渠道（economy.py 垂钓/采集品质档分支）
3. 新技能类型 = pets.py `_PET_SKILL_DESC` 加一行描述 + battle.py `_pet_skill_turn` 加一个 elif 分支（尽量挂现有 BUFF_MULT/e_buffs 机制）

### 加坐骑 = 改 data/mounts.py 一处
1. MOUNT_POOL 加一条（key 必须 `mount_` 前缀，price>0 自动进商店可买）
2. 掉落：MOUNT_DROP_ELITE/BOSS 加一行，或生活渠道分支
3. 新效果字段 = core/mounts.py `_MOUNT_EFFECT_KEYS` 加 key + 对应消费点调用 `C.mount_effects(player)`

### 显示必须可触发
- desc/source 里写的获取渠道必须真实存在（曾把声望兑换写进 desc，实际无声望商店 → 已改生活渠道）
- 反通胀：稀缺品走生活渠道（垂钓/采集/商店），不走战斗掉落；战斗掉落只有常规宠物

## 五、提交记录
- 0661e2e 批1 数据层扩容（14+10+5品质+台词+掉落表数据化）
- e40c7e0 批2 宠物新技能 4 类 + 战斗台词
- 8e15113 批3 坐骑新效果 5 项消费点落地
- 4bb610f 批4 面板升级（品质/出处/技能/专用详情渲染器）
- a357461 批5 来源铺设（垂钓/采集/商店）
- 72dc014 测试断言更新
