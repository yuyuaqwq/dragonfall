# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import C
v = C.subarea_links("oak_plain", "oak_plain_6")
print("subarea_links oak_plain_6 =", repr(v), "| type", type(v).__name__)
print("list() =", list(v))
# also check the raw mesh
from data.plugins.dragonfall.game.data import SUBAREA_LINKS_INDEX as I
print("raw mesh[oak_plain_6] =", repr(I["oak_plain"].get("oak_plain_6")), type(I["oak_plain"].get("oak_plain_6")).__name__)
print("id(subarea_links idx) == id(raw idx)?", )
