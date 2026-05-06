import json
from collections import Counter
import sys

# 读取整个 JSON 文件
with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)

counts = Counter()

for domain, info in data.items():
    ca = info.get("issuer_organization")
    if ca and ca != "unknown":
        counts[ca] += 1

total = sum(counts.values())

if total == 0:
    print("HHI = 0 (no valid certificates)")
else:
    hhi = sum((c / total) ** 2 for c in counts.values())
    print("HHI =", hhi)
