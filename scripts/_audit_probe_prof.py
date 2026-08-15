# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import C, db, clean_db, make_player

clean_db()
make_player("g1", "q8", "测试辛", "战士", level=1)
make_player("g1", "q9", "测试壬", "战士", level=1)
make_player("g2", "q10", "测试癸", "战士", level=1)
print("add q8 gather 1200 ->", db.add_prof_exp("g1", "q8", "gather", 1200))
print("add q9 mining 300 ->", db.add_prof_exp("g1", "q9", "mining", 300))
print("add q10 gather 1000 ->", db.add_prof_exp("g2", "q10", "gather", 1000))
tops = db.prof_top("g1", 10)
print("prof_top:")
for r in tops:
    print("   ", r)
import inspect
print("---add_prof_exp---")
print(inspect.getsource(db.add_prof_exp))
print("---prof_top---")
print(inspect.getsource(db.prof_top))
