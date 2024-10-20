import concurrent
from tkinter import Toplevel, Label, messagebox
from gensim.models import Word2Vec
from whoosh.analysis import LanguageAnalyzer, StemmingAnalyzer
from whoosh.fields import *
from whoosh import index
import os, re, shutil
from whoosh.index import create_in, open_dir
import word2vec_utils
from sentiment import stampa_segmenti_e_emozioni
from utils import center_window

# Variabili globali per l'indice e il modello Word2Vec
ix = None
use_stop = False
use_sent = False
word2vec_model = None

# Directory comune per il modello Word2Vec
COMMON_W2V_DIR = "word2vec_model"

# ordine alfabetico per i file da scansionare
def alphanumeric_sort(filename):
    parts = re.split(r'(\d+)', filename)
    return [int(part) if part.isdigit() else part for part in parts]

# imposta le variabili per decidere la tipologia di indice
def set_index_type(index_type):
    global use_stop, use_sent
    if index_type == 1:
        use_stop = True
        use_sent = False
        print(f"Stop={use_stop}, Sent={use_sent}")
    elif index_type == 2:
        use_stop = False
        use_sent = False
        print(f"Stop={use_stop}, Sent={use_sent}")
    elif index_type == 3:
        use_stop = True
        use_sent = True
        print(f"Stop={use_stop}, Sent={use_sent}")

# schema usato dall'indice
def get_schema():
    analyzer = StemmingAnalyzer(stoplist=None) if use_stop else LanguageAnalyzer("en")
    return Schema(
        title=TEXT(analyzer=analyzer, stored=True),
        url=ID(stored=True),
        artist=TEXT(stored=True),
        content=TEXT(analyzer=analyzer, stored=True),
        content_vector=TEXT(stored=True),
        nameFile=ID(stored=True),
        emotions=TEXT(stored=True)
    )

# restituisce i nomi delle directory in cui salvare i vari indici
def get_index_dir(use_stopwords, use_sentiment):
    if use_stopwords and use_sentiment:
        return "index_stopwords_sentiment"
    elif use_stopwords:
        return "index_stopwords"
    elif use_sentiment:
        return "index_nostopwords_sentiment"
    else:
        return "index_no_stopwords"

# richiama la directory in base alle variabili
def get_index_directory():
    return get_index_dir(use_stop, use_sent)

# Funzione per cambiare l'indice
def cambia_indice(documents_directory, progress_window, parent):
    global ix, word2vec_model
    index_dir = get_index_dir(use_stop, use_sent)

    # Crea la directory per l'indice se non esiste
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    os.mkdir(index_dir)

    # Crea la directory comune per il modello Word2Vec se non esiste
    if not os.path.exists(COMMON_W2V_DIR):
        os.mkdir(COMMON_W2V_DIR)

    # Addestra e salva il modello Word2Vec solo se non esiste
    word2vec_model_path = os.path.join(COMMON_W2V_DIR, "word2vec.model")
    if not os.path.exists(word2vec_model_path):
        word2vec_model = word2vec_utils.train_word2vec(documents_directory)
        word2vec_model.save(word2vec_model_path)
    else:
        word2vec_model = Word2Vec.load(word2vec_model_path)

    schema = get_schema()
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()
    file_list = sorted(os.listdir(documents_directory), key=alphanumeric_sort)

    def process_file(file_path):
        with open(file_path, "r") as file:
            fileUrl = file.readline().strip()
            fileArtist = file.readline().strip()
            fileTitle = file.readline().strip()
            fileContent = file.read()
            print(fileArtist + " " + fileTitle + " " + file_path)
            content_vector = word2vec_utils.get_average_vector(word2vec_model, fileContent).tolist()
            content_vector_str = ' '.join(map(str, content_vector))
            emozioni_str = ""
            if use_sent:
                emozioni = stampa_segmenti_e_emozioni(fileContent)
                emozioni_str = str(emozioni)
            return fileUrl, fileArtist, fileTitle, fileContent, content_vector_str, emozioni_str

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_file, os.path.join(documents_directory, i)): i for i in file_list}
        for future in concurrent.futures.as_completed(futures):
            file_path = futures[future]
            try:
                fileUrl, fileArtist, fileTitle, fileContent, content_vector_str, emozioni_str = future.result()
                writer.add_document(url=fileUrl, artist=fileArtist, title=fileTitle, content=fileContent,
                                    content_vector=content_vector_str, nameFile=file_path, emotions=emozioni_str)
            except Exception as e:
                print(f"Exception while processing {file_path}: {e}")

    writer.commit()
    print("Indice creato con successo")
    progress_window.destroy()
    completion_message = Toplevel(parent)
    completion_message.title("Completato")
    Label(completion_message, text="Indice creato con successo!").pack(padx=20, pady=20)
    center_window(completion_message, parent)
    completion_message.after(2000, completion_message.destroy)

# Funzione per caricare un indice già esistente
def carica_indice():
    global ix, word2vec_model
    index_dir = get_index_dir(use_stop, use_sent)
    word2vec_model_path = os.path.join(COMMON_W2V_DIR, "word2vec.model")

    try:
        if os.path.exists(index_dir) and os.path.exists(word2vec_model_path):
            ix = index.open_dir(index_dir)
            word2vec_model = Word2Vec.load(word2vec_model_path)
            print(f"Indice caricato da {index_dir} e modello Word2Vec caricato da {COMMON_W2V_DIR}")
            return True
        else:
            print("Nessun indice o modello Word2Vec trovato in questa directory.")
            return False
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante il caricamento: {str(e)}")
        return False

# restituisce l'indice
def get_index():
    global ix, use_stop, use_sent
    try:
        if ix is None:
            index_dir = get_index_dir(use_stop, use_sent)
            if os.path.exists(index_dir):
                ix = open_dir(index_dir)
            else:
                return None
        return ix
    except Exception as e:
        messagebox.showerror("Errore",
                             f"Errore durante il caricamento dell'indice dalla directory: {index_dir}. Dettagli: {str(e)}")
        return None

# restituisce il modello w2v dell'indice
def get_word2vec_model():
    model_path = os.path.join(COMMON_W2V_DIR, "word2vec.model")
    try:
        if os.path.exists(model_path):
            return Word2Vec.load(model_path)
        else:
            return None
    except Exception as e:
        messagebox.showerror("Errore",
                             f"Errore durante il caricamento del modello Word2Vec dalla directory: {COMMON_W2V_DIR}. Dettagli: {str(e)}")
        return None
