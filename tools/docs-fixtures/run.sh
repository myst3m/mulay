set -e
cd "$(dirname "$0")"
python3 extract.py
rm -f stage/runtime/run-1.dwt hang.txt
rm -rf stage2; cp -r stage stage2
python3 fillall.py stage
python3 fillall.py stage2
rm -f /tmp/dw-buffer-output-*.tmp
python3 post.py
