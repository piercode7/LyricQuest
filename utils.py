import webbrowser
import nltk
from bs4 import BeautifulSoup
from tkinter import Toplevel, Label
import numpy as np
import tkinter as tk
from tkinter import messagebox
from whoosh.qparser import QueryParser

# qui ci sono funzioni utili e più generiche per il programma (GUI e non)

# corregge la query prima di darla in pasto alla ricerca
def correggi_query(query_str, corrector):
    corrected_terms = []
    for term in query_str.split():
        corrected_term = corrector.suggest(term, limit=1)
        if corrected_term:
            corrected_terms.append(corrected_term[0])
        else:
            corrected_terms.append(term)
    return " ".join(corrected_terms)


# Funzione per ottenere un estratto che contiene la query, sarà usato per evidenziare il/i match/s delle query nei testi mostrati
def get_highlight_with_query(highlight_text):
    soup = BeautifulSoup(highlight_text, "html.parser")
    text = soup.get_text()
    sentences = text.split('. ')
    if sentences and sentences[0]:
        first_sentence = sentences[0] + '.' if sentences[0][-1] != '.' else sentences[0]
        if len(sentences) > 1:
            return first_sentence + " ..."
        return first_sentence
    return text


# Accentra l'apertura di un frame
def center_window(window, parent):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


# corregge la stringa del nome dell'artista per una ricerca più mirata
def correggi_query_artista(query_str, corrector):
    suggestions = corrector.suggest(query_str, limit=1)
    if suggestions:
        return suggestions[0]
    return query_str


# rimuove le prime righe vuote e spazi vuoti se ci sono all'inizio, serve per abbellire i testi mostrati per intero nelle pagine degli artisti
def rimuovi_righe_vuote_iniziali(testo):
    # Divide il testo in righe
    righe = testo.split('\n')
    # Rimuove spazi vuoti all'inizio di ogni riga e filtra le righe vuote
    righe_pulite = [riga.strip() for riga in righe if riga.strip()]
    # Unisce le righe in un unico testo
    testo_pulito = '\n'.join(righe_pulite)
    return testo_pulito




# estrae i primi 200 tokens dal testo, verrà usato nella pagina degli artisti per mostrare l'anteprima
import nltk


def estrai_primi_200_token(testo):
    # Estrae i primi 200 token dal testo
    tokens = nltk.word_tokenize(testo)
    primi_200_token = tokens[:200]

    # Riassembla i token in una stringa, trattando correttamente la punteggiatura
    testo_assemblato = ''
    for i, token in enumerate(primi_200_token):
        if i > 0 and token not in ['.', ',', ';', ':', '!', '?', '(', ')', '[', ']', '{', '}', "'", '"', '-', '...']:
            testo_assemblato += ' '
        testo_assemblato += token

    return testo_assemblato


# riduce i valori delle emozioni a meno cifre dopo la virgola per ragioni estetiche
def format_emotions(emotions_str):
    emozioni = eval(emotions_str)
    formatted_emotions = {k: round(v, 3) for k, v in emozioni.items()}
    return str(formatted_emotions)


# mostra un messaggio modificabile di pochi secondi per un avviso veloce (come fine operazione)
def mostra_messaggio_temporaneo(parent, titolo, messaggio, durata=2000):
    completion_message = Toplevel(parent)
    completion_message.title(titolo)
    Label(completion_message, text=messaggio).pack(padx=20, pady=20)
    center_window(completion_message, parent)
    completion_message.after(durata, completion_message.destroy)


# Funzione per resettare results_text prima di caricare un nuovo indice ed aprire quindi una nuova scheda di ricerca
def reset_schermate(results_text):
    global results, current_offset, results_word2vec, current_offset_word2vec
    results = None
    current_offset = 0
    results_word2vec = []
    current_offset_word2vec = 0
    results_text.config(state=tk.NORMAL)
    results_text.delete("1.0", tk.END)
    results_text.config(state=tk.DISABLED)


# estrae dai pulsanti in basso i sentimenti che si desidera utilizzare per il riordino nella funzione successiva
def get_selected_emotions(emotion_buttons):
    selected_emotions = [btn.emotion for btn in emotion_buttons if btn.pressed]
    return selected_emotions


# riordina i risultati (in results) prima di mostrarli su results_text in base a quelli che sono i sentimenti selezionati sui bottoni in basso
import ast


def ordina_risultati(results, selected_emotions):
    def get_emotion_score(result, emotion):
        try:
            emozioni = ast.literal_eval(result['emotions'])
            return emozioni.get(emotion, 0)
        except (SyntaxError, ValueError) as e:
            return 0

    def sort_key(result):
        # Se il risultato è una tupla (Word2Vec), estrai il risultato vero e proprio
        if isinstance(result, tuple):
            result = result[0]

        # Calcola il prodotto dei punteggi di tutte le emozioni selezionate
        product_score = 1
        count = 0
        for emotion in selected_emotions:
            score = get_emotion_score(result, emotion)
            if score > 0:
                product_score *= score
                count += 1
        if count == 0:
            return 0
        # Calcola la media geometrica dei punteggi
        geometric_mean = product_score ** (1 / count)
        return geometric_mean

    # Ordina i risultati in base al punteggio totale, in ordine decrescente
    results = sorted(results, key=sort_key, reverse=True)
    return results


def ordina_risultati_alfabetico(results):
    def sort_key(result):
        # Se il risultato è una tupla (Word2Vec), estrai il risultato vero e proprio
        if isinstance(result, tuple):
            result = result[0]

        return result['title'].lower()  # Ordina per titolo in ordine alfabetico (case insensitive)

    # Ordina i risultati in base al titolo, in ordine alfabetico
    results = sorted(results, key=sort_key)
    return results


# permette di utilizzare i link per raggiungere la pagina originale del testo su sito da cui è stato fatto lo scraping
def make_link_callback(url):
    def callback(event):
        webbrowser.open_new_tab(url)

    return callback


# permette di mostrare il testo esteso quando sono nella pagina di un artista specifico
def mostra_testo_completo(titolo, testo_completo, root):
    window = tk.Toplevel()
    window.title(titolo)
    window.geometry("600x400")

    # Calcola la posizione centrale rispetto alla finestra principale
    root.update_idletasks()
    main_width = root.winfo_width()
    main_height = root.winfo_height()
    main_x = root.winfo_x()
    main_y = root.winfo_y()
    window_width = 600
    window_height = 700

    x_cordinate = main_x + int((main_width / 2) - (window_width / 2))
    y_cordinate = main_y + int((main_height / 2) - (window_height / 2))

    window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    text_widget = tk.Text(window, wrap=tk.WORD)
    text_widget.pack(expand=True, fill=tk.BOTH)

    text_widget.insert(tk.END, f"Titolo: {titolo}\n\n")
    text_widget.insert(tk.END, testo_completo)

    text_widget.config(state=tk.DISABLED)

# funzione per fare una ricerca libera nel results_text con la query search_entry rispettando la posizione di ogni risultato in last_search_position
# Variabile globale per memorizzare l'ultimo termine di ricerca
last_search_term = ""

# Funzione per la ricerca libera
def btn_ricerca_libera(search_entry, results_text, last_search_position):
    global last_search_term

    search_term = search_entry.get().lower()  # Converti il termine di ricerca in minuscolo

    # Controlla se il termine di ricerca è cambiato
    if search_term != last_search_term:
        last_search_term = search_term
        last_search_position = None  # Resetta la posizione di ricerca

    results_text.tag_remove('highlight', '1.0', tk.END)

    if search_term:
        if last_search_position:
            start_pos = f"{last_search_position}+1c"
        else:
            start_pos = '1.0'

        start_pos = results_text.search(search_term, start_pos, stopindex=tk.END, nocase=True)

        if not start_pos:
            last_search_position = None
        else:
            end_pos = f"{start_pos}+{len(search_term)}c"
            results_text.tag_add('highlight', start_pos, end_pos)
            results_text.tag_config('highlight', background='yellow', foreground='black')
            results_text.see(start_pos)  # Scorre per rendere visibile la parte evidenziata
            last_search_position = start_pos

    return last_search_position
# calcola le polarità di un singolo artista analizzando tutti i suoi testi
def calcola_media_emozioni_artista(artist_name, indexing):
    ix = indexing.get_index()
    if ix is None:
        messagebox.showerror("Errore",
                             "Nessun indice disponibile. Creare o caricare un indice prima di effettuare la ricerca.")
        return

    searcher = ix.searcher()
    artist_parser = QueryParser("artist", schema=ix.schema)

    query = artist_parser.parse(f'"{artist_name}"')
    results = searcher.search(query, limit=None)

    if not results:
        return

    emozioni_totali = {
        'anger': [],
        'disgust': [],
        'fear': [],
        'joy': [],
        'neutral': [],
        'sadness': [],
        'surprise': [],
    }

    for result in results:
        emozioni = eval(result['emotions'])
        for emozione, valore in emozioni.items():
            if emozione in emozioni_totali:
                emozioni_totali[emozione].append(valore)

    # Calcola la media per ogni emozione
    media_emozioni = {emozione: np.mean(valori) if valori else 0 for emozione, valori in emozioni_totali.items()}

    return media_emozioni
