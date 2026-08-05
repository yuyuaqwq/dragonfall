# -*- coding: utf-8 -*-

from ..data import PET_POOL


"""《剑与魔法》数据层 - pets.py"""
def make_pet_egg(pet_key):
    p = next((x for x in PET_POOL if x["key"] == pet_key), PET_POOL[0])
    return {"name": f"{p['name']}蛋", "type": "宠物蛋", "pet_key": pet_key, "stackable": True,
            "price": 200, "desc": f"使用后可孵化出『{p['name']}』"}

def pet_exp_need(level):
    return level * 50

