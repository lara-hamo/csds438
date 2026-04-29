### **Distributed Text Mining Pipeline Using Hadoop MapReduce**



##### **Overview**

This project implements a distributed text mining pipeline for analyzing large collections of literary works using Hadoop MapReduce. The system processes a corpus of novels to identify linguistic and stylistic patterns associated with different levels of popularity.



The pipeline includes:

* Text preprocessing (cleaning, tokenization, normalization)
* N-gram extraction (unigrams, bigrams, trigrams)
* TF-IDF computation
* Distributed execution using Hadoop Streaming
* HDFS-based data storage
* Containerization using Singularity for reproducibility



##### Project Structure

group3repo/

│

├── config/

│   └── Hadoop\_container\_singularity.def

│

├── reports/

│   ├── CSD438 - Group 3 Project Presentation

│   ├── Group 3 Abstract 438.docx

│   ├── Group 3 Project Status.docx

│   ├── Group 3 Report - CSDS438.docx

│   └── preparation\_report.txt

│

├── results/

│   └── (output files from MapReduce jobs)

│

├── scripts/

│   ├── hadoopconfig.sh

│   ├── run\_experiments.sh

│   ├── run\_tfidf.sh

│   └── testhadoopconfig.slurm

│

├── src/

│   ├── ngrams/

│   │   ├── mapper.py

│   │   ├── mapper\_n\_grams.py

│   │   └── reducer.py

│   │

│   ├── preprocessing/

│   │   ├── collect\_novels.py

│   │   ├── dataset\_metadata.json

│   │   ├── generate\_sample\_corpus.py

│   │   ├── organize\_hdfs.py

│   │   └── prepare\_novels.py

│   │

│   └── tfidf/

│       ├── tfidf\_mapper.py

│       └── tfidf\_reducer.py

│

└── .gitignore.txt



##### Features

###### Distributed Processing

Uses Hadoop MapReduce to parallelize text processing tasks

Scales across multiple nodes in an HPC environment

###### Text Preprocessing Pipeline

* Lowercasing and normalization
* Tokenization
* Common word removal
* Stemming

###### N-gram Analysis

* Extracts:
* Unigrams
* Bigrams
* Trigrams
* Enables contextual and thematic analysis

###### TF-IDF Computation

* Identifies important words within each document
* Reduces weight of common words across corpus

###### HDFS Integration

Structured storage of:

* Corpus (by popularity tiers)
* Metadata
* Output results

###### Containerization

Uses Singularity for:

* Reproducibility
* Portability across compute environments

###### Dataset

Source: Project Gutenberg

Size: \~24 novels (\~1.9 million words)

Organized into:

* HIGH popularity
* MEDIUM popularity
* LOW popularity



##### How to Run

1\. Prepare Dataset

python src/preprocessing/collect\_novels.py

python src/preprocessing/prepare\_novels.py

2\. Organize Data in HDFS

python src/preprocessing/organize\_hdfs.py

3\. Run TF-IDF Pipeline

bash scripts/run\_tfidf.sh

4\. Run Full Experiments

bash scripts/run\_experiments.sh

5\. (Optional) Run via SLURM

sbatch scripts/testhadoopconfig.slurm



##### Outputs

Results are stored in the results/ directory and HDFS output paths, including:

* TF-IDF scores (word, document, score)
* N-gram frequency counts
* Processed corpus files



##### Technologies Used

Python

Hadoop MapReduce (Streaming)

HDFS

SLURM (for job scheduling)

Singularity (containerization)



##### Team

Lara Hamo

Hy Nguyen

Maximilian Malz

Kadijah Taylor



##### Potential Future Work

Scale to larger datasets

Increase number of compute nodes

Improve performance benchmarking

Expand analysis to additional corpora

Enhance popularity classification metrics



##### Notes

Designed for HPC environments

Optimized for distributed execution

Modular pipeline for easy extension

