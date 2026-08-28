# -*- coding: utf-8 -*-
"""v133 全职业爆发峰值批量扫描（修正学习等级口径 v2）"""
import subprocess, sys, os, time

BASE = r"C:/Users/yuyu/qqbot/data/plugins/dragonfall"
CLS = ['cls_ci_ke', 'cls_zhan_shi', 'cls_you_xia', 'cls_fa_shi', 'cls_mu_shi', 'cls_wu_seng']
LVS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
LOADOUTS = ['naked', 'blue5']
DIFFS = [0, 3, 5]
OUT = os.path.join(BASE, 'workspace', 'burst_scan', 'scan_v2')

os.makedirs(OUT, exist_ok=True)
t0 = time.time()
for cls in CLS:
    fpath = os.path.join(OUT, f'scan_{cls}.csv')
    with open(fpath, 'w', encoding='utf-8', newline='') as f:
        f.write('cls,lv,loadout,diff,skill,peak_dmg,target_hp,peak_pct,target_lv\n')
    for lv in LVS:
        for lo in LOADOUTS:
            for df in DIFFS:
                r = subprocess.run(
                    [sys.executable, os.path.join(BASE, 'scripts', 'burst_scan.py'),
                     '--cls', cls, '--lv', str(lv), '--loadout', lo, '--diff', str(df)],
                    capture_output=True, text=True, encoding='utf-8', cwd=BASE)
                if r.returncode != 0:
                    print(f'FAIL {cls} {lv} {lo} {df}: {r.stderr[-200:]}', flush=True)
                    continue
                lines = r.stdout.strip().split('\n')[1:]
                with open(fpath, 'a', encoding='utf-8', newline='') as f:
                    for ln in lines:
                        if ln.strip():
                            f.write(ln.strip() + '\n')
                print(f'OK {cls} {lv} {lo} d{df} rows={len(lines)}', flush=True)
    print(f'--- {cls} done in {time.time()-t0:.0f}s', flush=True)
print(f'ALL DONE in {time.time()-t0:.0f}s', flush=True)