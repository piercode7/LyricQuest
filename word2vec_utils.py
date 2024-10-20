from gensim.models import Word2Vec
from gensim.utils import simple_preprocess
from sklearn.metrics.pairwise import cosine_similarity as cs
import os, re
import numpy as np


def alphanumeric_sort(filename):
    parts = re.split(r'(\d+)', filename)
    return [int(part) if part.isdigit() else part for part in parts]


def read_documents(documents_directory):
    documents = []
    file_list = sorted(os.listdir(documents_directory), key=alphanumeric_sort)

    for file_name in file_list:
        with open(os.path.join(documents_directory, file_name), "r") as file:
            file.readline()
            file.readline()
            file.readline()
            content = file.read()
            documents.append(content)

    return documents


# addestramento modello word2vec
def train_word2vec(documents_directory):
    documents = read_documents(documents_directory)
    tokenized_docs = [simple_preprocess(doc) for doc in documents]
    model = Word2Vec(sentences=tokenized_docs, vector_size=100, window=5, min_count=1, workers=4)
    return model


def get_average_vector(model, text, query_words=None):
    if query_words is None:
        query_words = simple_preprocess(text)
    vectors = [model.wv[word] for word in query_words if word in model.wv]
    if vectors:
        average_vector = np.mean(vectors, axis=0)
        # print(f"Dimensione vettore medio: {average_vector.shape}")  # Debug: controlla la dimensione del vettore medio
        # print(f"Vettore medio: {average_vector[:5]}...")  # Debug: stampa i primi 5 valori del vettore medio
        return average_vector
    else:
        print("Nessun vettore trovato per le parole nella query.")  # Debug: nessun vettore trovato
        return np.zeros(model.vector_size)


def cosine_similarity(vec1, vec2):
    return cs([vec1], [vec2])[0][0]
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)
