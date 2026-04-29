#!/usr/bin/env python3
import sys
import re
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split("\t", 1)
    if len(parts) != 2:
        continue
    doc_name, text = parts
    words = re.findall(r"[a-z]+", text.lower())
    for word in words:
        print(f"{word}\t{doc_name}\t1")
