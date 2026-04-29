"""
generate_sample_corpus.py
Author: Maximilian Malz

Generates a realistic sample corpus for pipeline testing when Project Gutenberg
is not reachable (e.g. sandboxed environments, CI). Produces text files that
match the structure and approximate size of the real novels, with varied
vocabulary, sentence length, and stylistic patterns per popularity tier.

In production, this is REPLACED by collect_novels.py + real Gutenberg downloads.
"""

import os
import json
import random
import string
from datetime import datetime

RAW_DIR   = "raw_novels"
META_FILE = "dataset_metadata.json"
LOG_DIR   = "logs"

random.seed(42)

# ── Vocabulary pools ───────────────────────────────────────────────────────────
# Simulates distinct linguistic register per tier

HIGH_VOCAB = (
    "the and was it to of in that her she he had not with as at but all "
    "from they were there one when who would could said about been then "
    "into its than him more very what if upon which so their much how "
    "little do me no time great love heart mind world man woman life day "
    "house eyes hand long young old before again after every through "
    "dear away never still felt looked seemed mr mrs miss quite indeed "
    "own soon thought perhaps however rather yet always without well "
    "certainly room voice first night nothing good last place came going "
    "come back under many another must here such between both those know "
    "called say told made knew though might open think only few found "
    "far along set given feel left thing head while during themselves "
    "manner together until either should over family too being country "
    "small large taken name seen heard moment true half letter friend "
    "nothing everything nothing beauty charm delightful pleasant charming "
    "society agreeable admiration affection attachment feelings spirits "
    "temper character fortune situation conduct behaviour understanding "
    "sensibility resolution prudence civility elegance accomplishments"
).split()

MEDIUM_VOCAB = (
    "darkness shadow creature ancient blood night terror secret forbidden "
    "mysterious haunted pale cold ancient cursed monster soul doom ruin "
    "despair anguish torment suffering pale dread horror skull bones "
    "castle dungeon forest mist spectral apparition phantom wraith shade "
    "evil sinister malevolent corrupt decay death dying dead grave tomb "
    "asylum madness insanity obsession curse whisper scream horror evil "
    "betrayal revenge guilt remorse confession punishment exile sorrow "
    "burden consciousness psychological internal tormented driven guilty "
    "crime punishment reason moral human society poverty suffering "
    "redemption confession salvation damnation fate tragedy inevitable "
    "struggle identity transformation metamorphosis isolation alienation "
    "the and was not but all from were with said had been there then "
    "he she it they their into upon which could would think felt found "
    "knew came went saw took gave long dark night cold black empty "
    "alone door window street light fire blood hand face eyes old "
    "voice again moment time never still life death man woman before "
    "pale strange quiet silent deep heavy slow great dim suddenly"
).split()

LOW_VOCAB = (
    "notwithstanding thereof hitherto aforementioned heretofore wherein "
    "inasmuch henceforward forthwith wheresoever therefrom thereupon "
    "hereinafter whereof subsistence subsistence beseech bespoke prithee "
    "methinks perchance whence hitherto verily forsooth henceforth "
    "mayhaps perchance betwixt entwined enthralled bespoke implore "
    "implored entreated beseeched supplication petition declaration "
    "proclamation remonstrance deliberation consideration contemplation "
    "philosophical metaphysical hermeneutical epistemological ontological "
    "providence dispensation adjudication manifestation corroboration "
    "ecclesiastical venerable distinguished magnanimous perspicacious "
    "circumspect meticulous fastidious scrupulous punctilious assiduous "
    "indefatigable inveterate inimitable ineffable inscrutable intractable "
    "the and was not but all from were with said had been there then "
    "he she it they their into upon which could would think felt found "
    "knew came went saw took gave long great world man woman life time "
    "never still before great vast wide eternal ancient noble honourable "
    "worthy faithful steadfast resolute determined courageous honourable "
    "gentleman lady fortune estate consequence propriety decorum "
    "understanding arrangement settlement establishment respectability"
).split()

TIER_VOCAB = {
    "HIGH":   HIGH_VOCAB,
    "MEDIUM": MEDIUM_VOCAB,
    "LOW":    LOW_VOCAB,
}

# Sentence length distribution (in words) per tier
TIER_SENT_LEN = {
    "HIGH":   (8, 22),   # Austen-like: moderate, balanced
    "MEDIUM": (5, 18),   # Gothic/psychological: punchy to flowing
    "LOW":    (12, 40),  # Victorian/archaic: long, complex
}

# Target word count per novel
TIER_WORD_COUNT = {
    "HIGH":   80_000,
    "MEDIUM": 55_000,
    "LOW":    100_000,
}


def make_sentence(vocab: list[str], min_len: int, max_len: int) -> str:
    length = random.randint(min_len, max_len)
    words  = [random.choice(vocab) for _ in range(length)]
    words[0] = words[0].capitalize()
    return " ".join(words) + random.choice([".", ".", ".", "!", "?"])


def make_paragraph(vocab, sent_range, num_sentences=None) -> str:
    n = num_sentences or random.randint(3, 8)
    return " ".join(make_sentence(vocab, *sent_range) for _ in range(n))


def make_chapter(vocab, sent_range, target_words: int) -> str:
    lines = []
    words_so_far = 0
    chapter_num  = random.randint(1, 40)
    lines.append(f"CHAPTER {chapter_num}.\n")
    while words_so_far < target_words:
        para = make_paragraph(vocab, sent_range)
        lines.append(para)
        words_so_far += len(para.split())
    return "\n\n".join(lines)


def generate_novel_text(tier: str) -> str:
    vocab      = TIER_VOCAB[tier]
    sent_range = TIER_SENT_LEN[tier]
    target     = TIER_WORD_COUNT[tier]

    parts = [
        f"The Project Gutenberg EBook\n",
        f"*** START OF THE PROJECT GUTENBERG EBOOK ***\n",
    ]

    words_written = 0
    chapter_target = target // 20  # ~20 chapters
    while words_written < target:
        chapter_text = make_chapter(vocab, sent_range, chapter_target)
        parts.append(chapter_text)
        words_written += len(chapter_text.split())

    parts.append("\n*** END OF THE PROJECT GUTENBERG EBOOK ***\n")
    return "\n\n".join(parts)


# ── Novel catalog (mirrors collect_novels.py) ──────────────────────────────────
NOVELS = [
    (1342,  "Pride and Prejudice",               "Jane Austen",           "HIGH"),
    (11,    "Alice's Adventures in Wonderland",  "Lewis Carroll",         "HIGH"),
    (84,    "Frankenstein",                      "Mary Shelley",          "HIGH"),
    (1661,  "The Adventures of Sherlock Holmes", "Arthur Conan Doyle",    "HIGH"),
    (98,    "A Tale of Two Cities",              "Charles Dickens",       "HIGH"),
    (2701,  "Moby Dick",                         "Herman Melville",       "HIGH"),
    (74,    "The Adventures of Tom Sawyer",      "Mark Twain",            "HIGH"),
    (1080,  "A Modest Proposal",                 "Jonathan Swift",        "HIGH"),
    (345,   "Dracula",                           "Bram Stoker",           "MEDIUM"),
    (1260,  "Jane Eyre",                         "Charlotte Bronte",      "MEDIUM"),
    (2542,  "A Doll's House",                    "Henrik Ibsen",          "MEDIUM"),
    (768,   "Wuthering Heights",                 "Emily Bronte",          "MEDIUM"),
    (5200,  "Metamorphosis",                     "Franz Kafka",           "MEDIUM"),
    (2554,  "Crime and Punishment",              "Fyodor Dostoevsky",     "MEDIUM"),
    (161,   "Sense and Sensibility",             "Jane Austen",           "MEDIUM"),
    (174,   "The Picture of Dorian Gray",        "Oscar Wilde",           "MEDIUM"),
    (1400,  "Great Expectations",                "Charles Dickens",       "LOW"),
    (786,   "The Mayor of Casterbridge",         "Thomas Hardy",          "LOW"),
    (158,   "Emma",                              "Jane Austen",           "LOW"),
    (1184,  "The Count of Monte Cristo",         "Alexandre Dumas",       "LOW"),
    (2097,  "Leviathan",                         "Thomas Hobbes",         "LOW"),
    (209,   "The Turn of the Screw",             "Henry James",           "LOW"),
    (244,   "A Study in Scarlet",                "Arthur Conan Doyle",    "LOW"),
    (996,   "Don Quixote",                       "Miguel de Cervantes",   "LOW"),
]


def generate():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(LOG_DIR,  exist_ok=True)

    metadata = []
    print(f"Generating sample corpus — {len(NOVELS)} novels\n")

    for gid, title, author, tier in NOVELS:
        print(f"  [{tier}] {title} ...", end=" ", flush=True)

        text       = generate_novel_text(tier)
        word_count = len(text.split())

        safe_title = title.replace(" ", "_").replace("'", "").replace("/", "-")
        filename   = f"{gid}_{safe_title}.txt"
        filepath   = os.path.join(RAW_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"OK  ({word_count:,} words)")

        metadata.append({
            "gutenberg_id":    gid,
            "title":           title,
            "author":          author,
            "popularity_tier": tier,
            "word_count":      word_count,
            "char_count":      len(text),
            "filename":        filename,
            "filepath":        filepath,
            "collected_at":    datetime.utcnow().isoformat(),
            "source":          "GENERATED_SAMPLE",
        })

    with open(META_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    total_words = sum(e["word_count"] for e in metadata)
    print(f"\nCorpus generated: {len(metadata)} novels, {total_words:,} total words")
    print(f"Metadata: {META_FILE}")


if __name__ == "__main__":
    generate()
