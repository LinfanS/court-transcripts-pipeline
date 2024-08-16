"""Python script to initialise download of wordnet model for NLTK"""

import nltk

if __name__ == "__main__":
    nltk.download("wordnet", download_dir="./tmp")
