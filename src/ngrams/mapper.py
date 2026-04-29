#!/usr/bin/env python3
import sys
import re

# Basic stopword list (expand as needed)
STOPWORDS = {
    "the","and","is","in","at","of","a","to","it","on","for","with","as","by","an"
}

# Simple stemming function
def stem(word):
    if len(word) > 4:
        if word.endswith("ing"):
            return word[:-3]
        elif word.endswith("ed"):
            return word[:-2]
    return word

for line in sys.stdin:
    # Normalize text: lowercase and remove non-letters
    line = line.strip().lower()
    words = re.findall(r"[a-z]+", line)

    for word in words:
        if word not in STOPWORDS and len(word) > 1:
            word = stem(word)
            print(f"{word}\t1")