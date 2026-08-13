#!/bin/bash
# v101.30 副业优化全量回归（等 playtest 结束后跑，防 test_game_data.db 污染）
cd /c/Users/yuyu/qqbot/data/plugins/dragonfall || exit 1
for i in $(seq 1 120); do
  if [ ! -f scripts/playtest.lock ]; then
    echo "[$(date +%H:%M:%S)] playtest.lock 消失，等待 60s 确认稳定后开始全量"
    sleep 60
    if [ ! -f scripts/playtest.lock ]; then
      break
    fi
  fi
  echo "[$(date +%H:%M:%S)] playtest 仍在跑，等待... ($i/120)"
  sleep 60
done
if [ -f scripts/playtest.lock ]; then
  echo "❌ 等 2 小时 playtest 仍未结束，放弃自动全量"
  exit 1
fi
echo "[$(date +%H:%M:%S)] 开始全量回归"
"C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe" scripts/run_all_tests.py 2>&1 | tail -15
echo "[$(date +%H:%M:%S)] 全量回归结束 exit=$?"
