#!/bin/bash
INPUT_DIR="cleaned_novels"
INTERMEDIATE="tfidf_intermediate.txt"
OUTPUT="tfidf_output.txt"
if [ ! -d "$INPUT_DIR" ]; then
    echo "ERROR: cleaned_novels folder not found."
    echo "This script expects Max's preprocessed output folder: cleaned_novels/"
    exit 1
fi
rm -f "$INTERMEDIATE" "$OUTPUT"
for file in "$INPUT_DIR"/*.txt; do
    doc=$(basename "$file")
    while IFS= read -r line; do
        echo -e "$doc\t$line"
    done < "$file"
done | python3 tfidf_mapper.py | sort | python3 tfidf_reducer.py > "$OUTPUT"
echo "TF-IDF complete."
echo "Output written to $OUTPUT"