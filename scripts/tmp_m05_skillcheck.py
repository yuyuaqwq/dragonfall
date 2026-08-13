# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r"C:\Users\yuyu\qqbot")
os.environ.setdefault("GWEN_GAME_DB", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_game_data.db")))
from data.plugins.dragonfall.game import content as C

ids = ["ms_kuang_bao","ms_you_ling","ms_an_ying","ms_xu_kong","ms_zhen_ji","ms_hai_yao",
       "ms_lian_zhan","ms_nu_hou","ms_zhao_huan","ms_wan_dao","ms_huo_qiang","ms_zhao_huan_shui_gui",
       "ms_jian_ji","ms_wang_wei","ms_zhao_huan_ku_lou","ms_chuan_shen","ms_ai_hao","ms_an_ying_dan",
       "ms_suo_lian","ms_shen_pan_zhi_yan","ms_hei_an_zhi_liao","ms_si_yao","ms_yue_guang_zhan",
       "ms_zhao_huan_shu_ren","ms_zhi_yu","ms_jing_ling_jian_shu","ms_an_ying_zhan","ms_zhong_ji",
       "ms_fu_wen_chong_ji","ms_ying_hua","ms_zhao_huan_e_mo","ms_hei_an_yi_shi","ms_fu_shi",
       "ms_shen_yuan_zhi_nu","ms_zhao_huan_shen_yuan","ms_an_ying_zhao","ms_long_xi","ms_long_zhao",
       "ms_gu_long_wei_ya","ms_long_wei_190","ms_wei_ya","ms_sheng_guang_dan","ms_zhao_huan",
       "ms_dun_ji","ms_sheng_guang","ms_bing_xi","ms_dong_jie","ms_lei_bao","ms_feng_bao_zhi_yan",
       "ms_zhao_huan_lei_niao","ms_xiu_jian","ms_zu_zhou","ms_mei_huo_zhi_ge","ms_ju_lang",
       "ms_zhao_huan_chu_shou","ms_mei_huo","ms_du_ci","ms_jiao_sha","ms_shui_xi","ms_hai_chao",
       "ms_zhao_huan_sha_yu","ms_jing_hua_zhi_chao","ms_shui_dan","ms_hai_chao_zhu_fu","ms_tie_bi",
       "ms_qian_ji","ms_san_cha_ji","ms_chong_zhuang","ms_zhan_chui","ms_zhao_huan_gong_cheng_shou",
       "ms_xiu_li","ms_bao_dan","ms_suan_xi","ms_tun_shi","ms_zhao_huan_you_long","ms_lei_ji",
       "ms_feng_ren","ms_lei_jian","ms_feng_bao","ms_yun_dun","ms_zhu_fu","ms_zhao_huan_yun_wei",
       "ms_gan_ran","ms_zhao_ji","ms_chan_rao","ms_du_ya"]
missing = [i for i in ids if i not in C.MONSTER_SKILLS]
print("MONSTER_SKILLS 总数:", len(C.MONSTER_SKILLS))
print("缺失:", missing)
inst_txt = open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\instances.py", encoding="utf-8").read()
sub_txt = open(r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\game\data\subareas.py", encoding="utf-8").read()
for m in missing:
    print(m, "instances 引用:", inst_txt.count(m), "| subareas 引用:", sub_txt.count(m))
# 检查 build_monster 后技能是否会被 _enemy_turn 静默吞掉
# 再看 MONSTER_MODS 里是否有这些 elite 的 mod
for k in sorted(C.MONSTER_MODS.keys()):
    if "you_ling" in k or "kuang_bao" in k:
        print("MOD:", k, C.MONSTER_MODS[k].get("desc", ""))
