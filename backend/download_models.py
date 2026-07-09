import os
from transformers import pipeline
from sentence_transformers import SentenceTransformer

def download():
    print("Downloading Embedding model...")
    SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    print("Downloading QA model...")
    pipeline(
        "question-answering",
        model="deepset/tinyroberta-squad2"
    )
    print("All models downloaded and cached successfully.")

if __name__ == "__main__":
    download()
