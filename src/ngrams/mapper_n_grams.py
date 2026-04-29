
import sys
import re

# Config: change max_n to 2 or 3 as needed
MAX_N = 3

STOPWORDS = {
    "the","and","is","in","at","of","a","to","it","on","for","with","as","by","an"
}

def stem(word):
    if len(word) > 4:
        if word.endswith("ing"):
            return word[:-3]
        elif word.endswith("ed"):
            return word[:-2]
    return word

def preprocess(line):
    line = line.lower()
    words = re.findall(r"[a-z]+", line)
    words = [stem(w) for w in words if w not in STOPWORDS and len(w) > 1]
    return words

def generate_ngrams(words, n):
    return ["_".join(words[i:i+n]) for i in range(len(words)-n+1)]

for line in sys.stdin:
    words = preprocess(line)

    # Generate N-grams from 1 to MAX_N
    for n in range(1, MAX_N + 1):
        ngrams = generate_ngrams(words, n)
        for gram in ngrams:
            print(f"{gram}\t1")