# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - hidden_monsters.py（v87 04 章十六节：隐藏怪物）

低概率彩蛋怪——不在地图常规怪物列表，探索时独立判定出现（≤1%）。
格式同 maps.py 怪物 6 元组：["m_id", "名字", role, lv, [技能], [掉落]]
lv 用相对值（如 +2 = 地图等级+2），combat 展开时换算。
"""

# 隐藏怪物表：key = id，value = dict
# cond 出现条件（combat 判定）：
#   forest  森林类地图（type 或 id 含 forest/wood/glade）
#   water   水域类地图（river/lake/sea/reef/dock）
#   ruin    遗迹/地底（ruin/mine/abyss/battlefield/altar/underground）
#   night   仅夜间（时间系统时段为夜晚）
#   any     任意野外
HIDDEN_MONSTERS = {
    "e_gold_slime": {
        "id": "e_gold_slime", "name": "黄金史莱姆", "role": "elite",
        "lv_off": 2, "skills": ["ms_du_ya"],
        "drops": ["琥珀精华"], "gold_mult": 80,
        "cond": "any", "chance": 0.004, "tag": "✨ 隐藏",
        "flavor": "一只通体金黄的史莱姆，在阳光下闪闪发光！",
    },
    "e_white_stag": {
        "id": "e_white_stag", "name": "白鹿王", "role": "elite",
        "lv_off": 3, "skills": ["ms_chong_zhuang"],
        "drops": ["白鹿角"], "gold_mult": 40,
        "cond": "forest_night", "chance": 0.005, "tag": "✨ 隐藏",
        "flavor": "月光下，一匹通体雪白的巨鹿正低头饮水，鹿角泛着圣洁的光。",
    },
    "e_glimmer_fish": {
        "id": "e_glimmer_fish", "name": "荧光鱼群", "role": "elite",
        "lv_off": 1, "skills": ["ms_shui_dan"],
        "drops": ["荧光鳞"], "gold_mult": 20,
        "cond": "water", "chance": 0.005, "tag": "✨ 隐藏",
        "flavor": "水面下闪过一片荧光，一群发光的鱼正逆流而上！",
    },
    "e_rune_golem": {
        "id": "e_rune_golem", "name": "符文魔像", "role": "elite",
        "lv_off": 5, "skills": ["ms_fu_wen_chong_ji"],
        "drops": ["符文碎片"], "gold_mult": 30,
        "cond": "ruin", "chance": 0.003, "tag": "✨ 隐藏",
        "flavor": "一尊刻满符文的石像缓缓转动头颅，符文亮起猩红的光。",
    },
    "e_shadow_stalker": {
        "id": "e_shadow_stalker", "name": "暗影猎手", "role": "elite",
        "lv_off": 6, "skills": ["ms_an_ying_dan"],
        "drops": ["暗影精华"], "gold_mult": 50,
        "cond": "night_any", "chance": 0.003, "tag": "✨ 隐藏",
        "flavor": "黑暗中一双眼睛盯着你——下一秒，利刃已到面前！",
    },
    "e_fortune_fox": {
        "id": "e_fortune_fox", "name": "幸运灵狐", "role": "elite",
        "lv_off": 1, "skills": ["ms_du_ya"],
        "drops": ["幸运符"], "gold_mult": 60,
        "cond": "any", "chance": 0.002, "tag": "✨ 隐藏",
        "flavor": "一只通体赤红的小狐狸好奇地绕着你转圈，尾巴尖上闪着金光。",
    },
}
