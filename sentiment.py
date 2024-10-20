from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import nltk
import re
import torch
import os

max_workers = os.cpu_count()  # Utilizza il numero di core della CPU

# Assicurati di aver scaricato le risorse necessarie di nltk
nltk.download('punkt')

# Configurazione del dispositivo per utilizzare la GPU se disponibile
# Configurazione del dispositivo per utilizzare la GPU se disponibile, altrimenti la CPU
if torch.cuda.is_available():
    device = 0
else:
    device = "cpu"

# Carica il modello per l'analisi delle emozioni e il tokenizer
model_name = "j-hartmann/emotion-english-distilroberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)

# Definisci la pipeline con il parametro aggiornato
classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, top_k=None, device=device)


def normalize_text(text):
    # Rimuovi spazi duplicati
    text = re.sub(r'\s+', ' ', text)
    return text


def calcola_emozioni(segmento):
    # Normalizza il testo
    segmento = normalize_text(segmento)
    # Esegue l'analisi delle emozioni sul segmento normalizzato
    risultati = classifier(segmento)
    return risultati


def batch_calcola_emozioni(segmenti):
    batch_risultati = classifier(segmenti)
    return batch_risultati


def stampa_segmenti_e_emozioni(testo, max_workers=20):
    emozioni_totali = {
        'anger': 0.0,
        'disgust': 0.0,
        'fear': 0.0,
        'joy': 0.0,
        'neutral': 0.0,
        'sadness': 0.0,
        'surprise': 0.0
    }

    # Dividi il testo in segmenti di 150 tokens
    tokens = nltk.word_tokenize(testo)
    segmenti = [' '.join(tokens[i:i + 180]) for i in range(0, len(tokens), 180)]

    # Configurazione per batch processing e multithreading
    batch_size = 60  # Numero di segmenti per batch

    # Utilizza ThreadPoolExecutor per parallelizzare le invocazioni di calcola_emozioni su ciascun segmento
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_segment = {executor.submit(batch_calcola_emozioni, segmenti[i:i + batch_size]): i for i in
                             range(0, len(segmenti), batch_size)}

        for future in as_completed(future_to_segment):
            batch_result = future.result()
            for segment_result in batch_result:
                for emozione in segment_result:
                    if emozione['label'] in emozioni_totali:
                        emozioni_totali[emozione['label']] += emozione['score']

    # Normalizza le emozioni cumulative
    totale_score = sum(emozioni_totali.values())
    if totale_score > 0:
        for emozione in emozioni_totali:
            emozioni_totali[emozione] /= totale_score

    return emozioni_totali
