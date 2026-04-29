#!/usr/bin/env python3
import sys
import math
from collections import defaultdict
# word -> {doc: count}
word_doc_counts = defaultdict(lambda: defaultdict(int))
doc_lengths = defaultdict(int)
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    word, doc, count = line.split("\t")
    count = int(count)
    word_doc_counts[word][doc] += count
    doc_lengths[doc] += count
N = len(doc_lengths)
for word, doc_counts in word_doc_counts.items():
    df = len(doc_counts)
    idf = math.log(N / (1 + df))
    for doc, tf_count in doc_counts.items():
        tf = tf_count / doc_lengths[doc]
        tfidf = tf * idf
        print(f"{doc}\t{word}\t{round(tfidf, 6)}")