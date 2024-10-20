# importa da altre librerie
import sys
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from whoosh.qparser import MultifieldParser, FuzzyTermPlugin, PhrasePlugin, QueryParser
from whoosh.scoring import TF_IDF, BM25F
import tkinter as tk
from tkinter import messagebox
import time
import os

# importa da altri moduli
import indexing
import scraping
import ricerche
import benchmark
from EmotionButton import EmotionButton
from show_results import mostra_risultati_GUI, mostra_risultati_w2v_GUI
from utils import correggi_query, center_window, rimuovi_righe_vuote_iniziali, \
    estrai_primi_200_token, format_emotions, mostra_messaggio_temporaneo, reset_schermate, get_selected_emotions, \
    ordina_risultati, make_link_callback, mostra_testo_completo, btn_ricerca_libera, ordina_risultati_alfabetico, \
    calcola_media_emozioni_artista

# contiene l'artista in analisi
query_artist = None

# Variabile globale per l'indice
titleBoost = 2.0
global elapsed_time

# Stringa contenente la query aggiornata
query_str = None

# servono per muoversi fra le pagine nelle ricerche non word2vec
results = None
current_offset = 0
page_size = 20

# servono per muoversi fra le pagine nella ricerca word2vec
results_w2v = []
current_offset_w2v = 0
page_size_w2v = 20  # limite brani per pagina


# rende il nome degli artisti clickable nell'area di risultati, così permette l'accesso alla loro pagina dedicata
def make_artist_callback(artist_name, output_widget):
    def callback(event):
        global query_artist
        query_artist = artist_name
        mostra_risultati_artista_GUI(query_artist, output_widget)

    return callback


############################ RICERCA GENERICA (NO W2V) #################################################################

# la query processata nelle funzioni di ricerca ora è pronta per creare results che contiene tutti i risultati di ricerca che saranno poi impaginati e ordinati nel momdulo show_results. Calcola il tempo si ricerca
def ricerca_query_GUI(parser, searcher, corrector, query_str=None, corrected=False, output_widget=None):
    global results, current_offset
    current_offset = 0  # azzerato per una nuova impaginazione

    if query_str is None:
        return

    # Inizio del tempo di misurazione
    start_time = time.time()

    # parsing query
    query = parser.parse(query_str)
    # file coinvolti nella ricerca da cui estrarre i dati effettivi da mostrare nel pannello
    results = searcher.search(query, limit=None)  # Limita i risultati a None per ottenere tutti i risultati

    # Fine del tempo di misurazione
    end_time = time.time()
    global elapsed_time
    elapsed_time = end_time - start_time  # Tempo impiegato in secondi

    # se la ricerca ha fallito potrebbero esserci errori grammaticali che la funzione correggi_query cerca di risolvere al meglio
    if len(results) == 0 and not corrected:
        corrected_query_str = correggi_query(query_str, corrector)
        if corrected_query_str != query_str:  # se c'è correzione effettiva
            query_str = corrected_query_str
            corrected = True
            query = parser.parse(query_str)
            start_time = time.time()  # Misura di nuovo il tempo per la query corretta
            results = searcher.search(query, limit=None)
            end_time = time.time()
            elapsed_time = end_time - start_time  # Tempo impiegato in secondi

    # ora results è pronto per dare i suoi file trovati in pasto a mostra_risultati per l'impaginazione
    reset_last_search_position()
    mostra_risultati_GUI(results_text, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing,
                         make_link_callback, make_artist_callback)


# avvia la ricerca di tipo TF-IDF, richiamata dal bottone GUI

def avvia_ricerca_tf_idf_GUI(output_widget=None):
    if index_type_var.get() == 0:
        messagebox.showerror("Errore", "Seleziona un indice prima di effettuare la ricerca.")
        return

    ix = indexing.get_index()
    if ix is None:
        messagebox.showerror("Errore",
                             "Nessun indice disponibile. Creare o caricare un indice prima di effettuare la ricerca.")
        return

    query_str = query_entry.get() if output_widget else None
    if query_str == "":
        messagebox.showerror("Errore", "Inserisci una query prima!")
        return
    try:
        parser = MultifieldParser(["title", "content"], schema=ix.schema, fieldboosts={"title": titleBoost})
        parser.add_plugin(FuzzyTermPlugin())
        parser.add_plugin(PhrasePlugin())
        searcher = ix.searcher(weighting=TF_IDF())
        corrector = ix.reader().corrector("content")
        ricerca_query_GUI(parser, searcher, corrector, query_str=query_str, output_widget=output_widget)
    except Exception as e:
        messagebox.showerror("Errore", "Indice assente o corrotto, eseguire una nuova scansione.")
        return


# avvia la ricerca di tipo BM25
def avvia_ricerca_bm25_GUI(output_widget=None):
    if index_type_var.get() == 0:
        messagebox.showerror("Errore", "Seleziona un indice prima di effettuare la ricerca.")
        return

    ix = indexing.get_index()
    if ix is None:
        messagebox.showerror("Errore",
                             "Nessun indice disponibile. Creare o caricare un indice prima di effettuare la ricerca.")
        return

    query_str = query_entry.get() if output_widget else None
    if query_str == "":
        messagebox.showerror("Errore", "Inserisci una query prima!")
        return
    try:
        parser = MultifieldParser(["title", "content"], schema=ix.schema, fieldboosts={"title": titleBoost})
        parser.add_plugin(FuzzyTermPlugin())
        parser.add_plugin(PhrasePlugin())
        searcher = ix.searcher(weighting=BM25F())
        corrector = ix.reader().corrector("content")
        ricerca_query_GUI(parser, searcher, corrector, query_str=query_str, output_widget=output_widget)
    except Exception as e:
        messagebox.showerror("Errore", "Indice assente o corrotto, eseguire una nuova scansione.")
        return

# avvia la ricerca per titolo
def avvia_ricerca_titolo_GUI(output_widget=None):
    if index_type_var.get() == 0:
        messagebox.showerror("Errore", "Seleziona un indice prima di effettuare la ricerca.")
        return

    ix = indexing.get_index()
    if ix is None:
        messagebox.showerror("Errore",
                             "Nessun indice disponibile. Creare o caricare un indice prima di effettuare la ricerca.")
        return

    query_str = query_entry.get() if output_widget else None  # prende query da casella di testo
    if query_str == "":
        messagebox.showerror("Errore", "Inserisci una query prima!")
        return
    try:
        parser = QueryParser("title", schema=ix.schema)  # Parser per il campo del titolo
        parser.add_plugin(FuzzyTermPlugin())
        parser.add_plugin(PhrasePlugin())
        searcher = ix.searcher(weighting=TF_IDF())  # Utilizza TF_IDF per la ricerca
        corrector = ix.reader().corrector("title")  # Correttore per il campo del titolo
        ricerca_query_GUI(parser, searcher, corrector, query_str=query_str, output_widget=output_widget)
    except Exception as e:
        messagebox.showerror("Errore", "Indice assente o corrotto, eseguire una nuova scansione.")
        return

# avvia la ricerca per gli artisti, non utilizza ricerca_query_GUI
def avvia_ricerca_artisti_GUI(output_widget):
    if index_type_var.get() == 0:
        messagebox.showerror("Errore", "Seleziona un indice prima di effettuare la ricerca.")
        return

    # Ottieni la query dal campo di input per la ricerca degli artisti
    query_str = query_entry.get()
    try:
        ix = indexing.get_index()
        if ix is None:
            messagebox.showerror("Errore",
                                 "Nessun indice disponibile. Creare o caricare un indice prima di effettuare la ricerca.")
            return

        searcher = ix.searcher()
        artist_parser = QueryParser("artist", schema=ix.schema)

        # Esegui una ricerca per tutti gli artisti
        query = artist_parser.parse("*")
        all_artists = searcher.search(query, limit=None)
    except Exception as e:
        messagebox.showerror("Errore","Indice assente o corrotto, eseguire una nuova scansione." )
        return

    matching_artists = set()  # Usa un set per evitare duplicati
    for result in all_artists:
        artist_name = result['artist'].lower()
        if query_str.lower() in artist_name:
            matching_artists.add(result['artist'])  # Usa il nome originale per il callback

    if output_widget:
        output_widget.config(state=tk.NORMAL)
        output_widget.delete("1.0", tk.END)

    if matching_artists:
        output_widget.insert(tk.END, f"ARTISTI TROVATI PER '{query_str}':\n", ("title",))
        sorted_artists = sorted(matching_artists)  # Ordina gli artisti in ordine alfabetico
        for artist in sorted_artists:
            artist_tag = artist.lower().replace(' ', '_')  # Crea un tag unico per l'artista
            output_widget.insert(tk.END, f"{artist}\n", (artist_tag,))
            # Rendi cliccabile l'artista
            output_widget.tag_bind(artist_tag, "<Button-1>", make_artist_callback(artist, output_widget))
            output_widget.tag_config(artist_tag, foreground="blue", underline=True)
            # Cambia il cursore in una mano al passaggio del mouse
            output_widget.tag_bind(artist_tag, "<Enter>", lambda e: output_widget.config(cursor="hand2"))
            output_widget.tag_bind(artist_tag, "<Leave>", lambda e: output_widget.config(cursor=""))
    else:
        output_widget.insert(tk.END, f"Nessun artista trovato per '{query_str}'\n")

    if output_widget:
        output_widget.config(state=tk.DISABLED)




############################################## RICERCA WORD2VEC ########################################################

# alternativa alle ricerche precedenti che sfrutta la ricerca combinata w2v per ottenere un risultato di similarità migliore possibile
def avvia_ricerca_word2vec_GUI():
    if index_type_var.get() == 0:
        messagebox.showerror("Errore", "Seleziona un indice prima di effettuare la ricerca.")
        return
    query_str = query_entry.get()  # Ottieni la query dall'input dell'utente
    if query_str == "":
        messagebox.showerror("Errore", "Inserisci una query prima!")
        return

    try:
        ix = indexing.get_index()
        if ix is None:
            raise RuntimeError("Indice non caricato")

        word2vec_model = indexing.get_word2vec_model()
        if word2vec_model is None:
            raise RuntimeError("Modello Word2Vec non caricato")

        global results_w2v

        # Inizio del tempo di misurazione
        start_time = time.time()

        results_w2v = ricerca_combinata_w2v(ix.searcher(weighting=BM25F()), word2vec_model, query_str=query_str)


        # Fine del tempo di misurazione
        end_time = time.time()
        global elapsed_time
        elapsed_time = end_time - start_time  # Tempo impiegato in secondi

        global current_offset_w2v
        current_offset_w2v = 0
        reset_last_search_position()
        mostra_risultati_w2v_GUI(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing,
                                 results_text, make_link_callback, make_artist_callback, elapsed_time)
    except Exception as e:
        messagebox.showerror("Errore", f"Indice assente o corrotto, effettuare una nuova scansione.")


# perfeziona la ricerca word2vec usando anche bm25
def ricerca_combinata_w2v(searcher, word2vec_model, query_str):
    bm25_results = ricerche.ricerca_bm25(searcher, query_str)
    improved = ricerche.improve_with_word2vec(bm25_results, word2vec_model, query_str)
    return improved


################################## ARTISTA #############################################################################
# mostra un calcolo delle polarità del singolo artista basato su tutti i suoi testi
def mostra_info_artista(artist_name):
    try:
        emozioni_medie = calcola_media_emozioni_artista(artist_name, indexing)
    except Exception as e:
        emozioni_medie = None

    window = tk.Toplevel()
    window.title(f"Informazioni su {artist_name}")

    if emozioni_medie is None:
        window.geometry("500x200")
        label = tk.Label(window,
                         text="Nessun dato disponibile.\nUtilizza l'indice che dispone di analisi del\n sentimento per ottenere questa informazione.")
        label.pack(expand=True, fill=tk.BOTH)
    else:
        window.geometry("800x600")

        # Creare il grafico
        fig, ax = plt.subplots()
        emozioni = list(emozioni_medie.keys())
        valori = list(emozioni_medie.values())

        ax.bar(emozioni, valori, color=['red', 'green', 'purple', 'yellow', 'gray', 'blue', 'orange'])
        ax.set_xlabel('Emozioni')
        ax.set_ylabel('Media')
        ax.set_title(f"Media delle emozioni per {artist_name}")

        # Posizionare il grafico nel frame
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)


# mostra la pagine intera dell'artista, i contenuti sono in ordine alfabetico se i sentimenti non sono premuto, altrimenti si possono filtrare i brani per sentimento
def mostra_risultati_artista_GUI(query_str, output_widget):

    global results
    ix = indexing.get_index()
    if ix is None:
        messagebox.showerror("Errore",
                             "Nessun indice disponibile. Creare o caricare un indice prima di effettuare la ricerca.")
        return

    reset_last_search_position()

    searcher = ix.searcher()
    artist_parser = QueryParser("artist", schema=ix.schema)
    corrector = searcher.reader().corrector("artist")

    query = artist_parser.parse(query_str)
    results = searcher.search(query, limit=None)

    url_callbacks = {}
    artist_callbacks = {}

    selected_emotions = get_selected_emotions(emotion_buttons)
    results = ordina_risultati_alfabetico(results)

    try:
        # Ordina i risultati solo se use_sent è True
        if indexing.use_sent:
            selected_emotions = get_selected_emotions(emotion_buttons)
            results = ordina_risultati(results, selected_emotions)
        else:
            # Se ci sono emozioni selezionate e l'indice non supporta i sentimenti, mostra un messaggio di avviso
            if selected_emotions:
                messagebox.showwarning("Attenzione",
                                       "L'indice in uso non dispone di tecniche di analisi del sentimento. Selezionare indice con funzionalità annessa!")
                return
            else:
                results = ordina_risultati_alfabetico(results)
    except TypeError:
        messagebox.showwarning("Attenzione", "Aggiorna i risultati dopo avere caricato il nuovo indice. "
                                             "Utilizza una delle ricerche a lato, o seleziona un artista.")
        return

    if output_widget:
        output_widget.config(state=tk.NORMAL)
        output_widget.delete("1.0", tk.END)

    if results:
        artist_name = results[0]['artist'].upper()
        output_widget.insert(tk.END, f"{artist_name}\n", ("title",))

        btn_artista_info = tk.Button(output_widget, text="Che artista è?",
                                     command=lambda: mostra_info_artista(artist_name))
        output_widget.window_create(tk.END, window=btn_artista_info)
        output_widget.insert(tk.END, "\n\n")

    for idx in range(len(results)):
        result = results[idx]
        content = rimuovi_righe_vuote_iniziali(result['content'])
        first_part = estrai_primi_200_token(content)
        rimuovi_righe_vuote_iniziali(first_part)

        output_widget.insert(tk.END, f"Titolo: {result['title']}\n")
        output_widget.insert(tk.END, f"URL: {result['url']}\n", (result['url'],))
        output_widget.insert(tk.END, f"Artista: {result['artist']}\n", (result['artist'],))
        output_widget.insert(tk.END, f"Nome File: {result['nameFile']}\n")
        output_widget.insert(tk.END, f"Testo: {first_part}...\n")

        # Controllo se emotions è presente e valido
        emotions_str = result.get('emotions', None)
        if emotions_str and emotions_str != 'None':
            try:
                formatted_emotions = format_emotions(emotions_str)
                output_widget.insert(tk.END, f"Emozioni: {formatted_emotions}\n")
            except SyntaxError:
                output_widget.insert(tk.END, f"Emozioni: Dati non validi\n")

        btn_mostra_testo = tk.Button(output_widget, text=f"Mostra testo completo",
                                     command=lambda t=result['title'], c=content: mostra_testo_completo(t, c, root))
        output_widget.window_create(tk.END, window=btn_mostra_testo)
        output_widget.insert(tk.END, "\n\n")

        url_callbacks[result['url']] = make_link_callback(result['url'])
        artist_callbacks[result['artist']] = make_artist_callback(result['artist'], output_widget)

    if output_widget:
        output_widget.config(state=tk.DISABLED)

        output_widget.tag_config("content", foreground="darkblue")

        for url, callback in url_callbacks.items():
            start_index = "1.0"
            while True:
                start_index = output_widget.search(url, start_index, stopindex=tk.END)
                if not start_index:
                    break
                end_index = output_widget.index(f"{start_index} + {len(url)}c")
                output_widget.tag_add(url, start_index, end_index)
                output_widget.tag_config(url, foreground="blue", underline=True)
                output_widget.tag_bind(url, "<Button-1>", callback)
                output_widget.tag_bind(url, "<Enter>", lambda e: output_widget.config(cursor="hand2"))
                output_widget.tag_bind(url, "<Leave>", lambda e: output_widget.config(cursor=""))

                start_index = end_index

        for artist, callback in artist_callbacks.items():
            start_index = "1.0"
            while True:
                start_index = output_widget.search(artist, start_index, stopindex=tk.END)
                if not start_index:
                    break
                end_index = output_widget.index(f"{start_index} + {len(artist)}c")
                output_widget.tag_add(artist, start_index, end_index)
                output_widget.tag_config(artist, foreground="green", underline=True)
                output_widget.tag_bind(artist, "<Button-1>", callback)
                output_widget.tag_bind(artist, "<Enter>", lambda e: output_widget.config(cursor="hand2"))
                output_widget.tag_bind(artist, "<Leave>", lambda e: output_widget.config(cursor=""))

                start_index = end_index


##################################### FILTRAGGIO #######################################################################
# in base al contesto in cui ci si trova effettua un filtro in base ai sentimenti premuti nei bottoni, i risultati su schermo verranno ordinati
def decidi_update(query_str, output_widget):
    # Leggi la prima riga del testo nel widget di output
    first_line = output_widget.get("1.0", "1.0 lineend").strip()
    # Se il testo nel widget di output è vuoto, mostra un messaggio di errore
    if first_line == "":
        messagebox.showerror("Errore",
                             "Effettua una ricerca o seleziona un artista prima di fare un'analisi del sentimento!")
        return

    # Controlla se la prima parola è "RICERCA"
    elif first_line.split()[0] == "RICERCA":
        # Verifica se le prime due parole sono "RICERCA WORD2VEC"
        if len(first_line.split()) > 1 and first_line.split()[1] == "WORD2VEC":
            global current_offset_w2v
            current_offset_w2v = 0
            mostra_risultati_w2v_GUI(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing,
                                     results_text, make_link_callback, make_artist_callback, elapsed_time)
        else:
            global current_offset
            current_offset = 0
            mostra_risultati_GUI(results_text, elapsed_time, results, current_offset, page_size, emotion_buttons,
                                 indexing, make_link_callback, make_artist_callback)

    elif first_line.split()[0] == "ARTISTI":
        if indexing.use_sent:
            messagebox.showinfo("Errore",
                            "Visualizza la pagina di uno degli artisti elencati per analizzare i sentimenti che trasmette!")
            return

        else :
            messagebox.showerror("Errore",
                            "L'indice in uso non dispone di tecniche di analisi del sentimento. Selezionare indice con funzionalità annessa!")
            return


    elif first_line.split()[0] == "Nessun":
        messagebox.showinfo("Errore",
                            "Non c'è alcun elenco da filtrare.")

    else:
        mostra_risultati_artista_GUI(query_str, output_widget)


########################################### GUI ELEMENTS ###############################################################
root = tk.Tk()
root.title("Search Engine")
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)
# Frame per il pannello dei risultati (destra)
results_frame = tk.Frame(main_frame)
results_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
# Area di testo per visualizzare i risultati non editabile (TestArea nel pannello destro)
results_text = ScrolledText(results_frame, wrap="word", height=20, width=100, state=tk.DISABLED, padx=10, pady=10)
results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
# Nuovo frame per il campo di ricerca sotto il results_text
search_frame = tk.Frame(results_frame)
search_frame.pack(fill=tk.X, padx=10, pady=10)
# Configurazione del layout a griglia per il search_frame
search_frame.columnconfigure(0, weight=1)
search_frame.columnconfigure(1, weight=0)
# Frame per i pulsanti delle emozioni accanto al campo di ricerca
emotion_frame = tk.Frame(search_frame)
emotion_frame.grid(row=0, column=0, padx=5, pady=5, sticky="w")
emotions = ['anger', 'disgust', 'fear', 'joy', 'neutral', 'sadness', 'surprise']
selected_emotions = []
emotion_buttons = []
for emotion in emotions:
    btn = EmotionButton(emotion_frame, text=emotion.capitalize(), emotion=emotion)
    btn.pack(side=tk.LEFT, padx=2)
    emotion_buttons.append(btn)
# Aggiungi un frame vuoto per separare i pulsanti delle emozioni dal pulsante di update
separator_frame = tk.Frame(emotion_frame, width=60)
separator_frame.pack(side=tk.LEFT)
# Aggiungi il nuovo pulsante "Aggiorna Risultati" accanto agli altri pulsanti delle emozioni
btn_aggiorna_risultati = tk.Button(emotion_frame, text="Filtra",
                                   command=lambda: decidi_update(query_str=query_artist, output_widget=results_text))
btn_aggiorna_risultati.pack(side=tk.LEFT, padx=2)

# Campo di input per la ricerca all'interno dei risultati
search_entry = tk.Entry(search_frame, width=50)
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="e")

last_search_position = None


# permette di muoversi tra i risultati evidenziati in giallo della ricerca libera (ricerca libera è in utils)
def set_last_search_position():
    global last_search_position
    last_search_position = btn_ricerca_libera(search_entry, results_text, last_search_position)

# resetta il contatore delle posizioni usato nella ricerca libera
def reset_last_search_position():
    global last_search_position
    last_search_position = None


def chiudi_programma(root):
    root.quit()  # Termina il ciclo principale di Tkinter
    root.destroy()  # Distrugge la finestra principale di Tkinter
    sys.exit(0)  # Termina il programma completamente


btn_ricerca_libera_btn = tk.Button(search_frame, text="Cerca", command=lambda: set_last_search_position())
btn_ricerca_libera_btn.grid(row=0, column=2, padx=5, pady=5, sticky="e")

# Frame per la query e i pulsanti (sinistro)
control_frame = tk.Frame(main_frame, width=80)
control_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
# Frame per i pulsanti di navigazione
nav_frame = tk.Frame(main_frame)
nav_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
# Campo di input per la query
tk.Label(control_frame, text="Inserisci la tua query").pack(pady=5)
query_entry = tk.Entry(control_frame, width=30)
query_entry.pack(pady=5)
# pulsante per la ricerca con TF-IDF (avvia_ricerca_tf_idf)
btn_ricerca_tf_idf = tk.Button(control_frame, text="Ricerca con TF-IDF", width=30,
                               command=lambda: avvia_ricerca_tf_idf_GUI(output_widget=results_text))
btn_ricerca_tf_idf.pack(pady=10)
# pulsante per la ricerca con BM25 (avvia_ricerca_bm25)
btn_ricerca_bm25 = tk.Button(control_frame, text="Ricerca con BM25", width=30,
                             command=lambda: avvia_ricerca_bm25_GUI(output_widget=results_text))
btn_ricerca_bm25.pack(pady=10)
# pulsante per la ricerca con Word2Vec (avvia_ricerca_word2vec)
btn_ricerca_word2vec = tk.Button(control_frame, text="Ricerca con Word2Vec", width=30,
                                 command=avvia_ricerca_word2vec_GUI)
btn_ricerca_word2vec.pack(pady=10)
# Bottoni per le ricerche
btn_ricerca_titolo = tk.Button(control_frame, text="Ricerca sul Titolo", width=30,
                               command=lambda: avvia_ricerca_titolo_GUI(output_widget=results_text))
btn_ricerca_titolo.pack(pady=10)
btn_ricerca_artisti = tk.Button(control_frame, text="Ricerca Artisti", width=30,
                                command=lambda: avvia_ricerca_artisti_GUI(output_widget=results_text))
btn_ricerca_artisti.pack(pady=10)
tk.Label(control_frame, text="").pack(pady=5)
tk.Label(control_frame, text="").pack(pady=5)
tk.Label(control_frame, text="Seleziona l'indice che vuoi utilizzare").pack(pady=5)

################################ GESTIONE PULSANTI INDICI ##############################################################

# Variabile globale per tenere traccia del pulsante selezionato
selected_index_button = None
previous_index = 0  # Variabile per memorizzare l'indice precedente


# Funzione per cambiare l'indice in base al bottone premuto
# Funzione per cambiare l'indice in base al bottone premuto
def cambia_indice_pulsante(index_type):
    global previous_index
    previous_index = index_type_var.get()  # Memorizza l'indice corrente come precedente
    index_type_var.set(index_type)
    carica_o_crea_indice(index_type)
    aggiorna_stato_bottoni()
    aggiorna_stato_bottone_directory()  # Aggiorna lo stato del bottone della directory


# richiama la creazione dell'indice con le funzioni di indexing.py
# Funzione per caricare o creare l'indice
def carica_o_crea_indice(index_type):
    global previous_index
    # Chiede all'utente se desidera aprire una nuova scheda di navigazione con il nuovo indice
    response = messagebox.askyesno("Conferma", "Vuoi aprire una nuova scheda di navigazione con l'indice selezionato?")
    if not response:
        # Ripristina il valore precedente dell'indice
        index_type_var.set(previous_index)
        aggiorna_stato_bottoni()
        return

    previous_index = index_type  # Aggiorna l'indice precedente solo se l'utente conferma
    indexing.set_index_type(index_type)
    index_dir = indexing.get_index_directory()

    if os.path.exists(index_dir):
        success = indexing.carica_indice()
        if success:
            indexing.get_index()  # Aggiorna l'indice corrente
            indexing.get_word2vec_model()  # Aggiorna il modello corrente
            mostra_messaggio_temporaneo(root, "Successo", "Indice caricato correttamente.", durata=1000)
            reset_schermate(results_text)
        else:
            messagebox.showerror("Errore", f"Indice assente o incompleto, effettuare una nuova scansione.")
    else:
        response = messagebox.askyesno("Creare Indice",
                                       "La cartella dell'indice non esiste. Vuoi creare un nuovo indice?")
        if response:
            apri_directory()
            reset_schermate(results_text)


# aggiorna lo stato dei 3 bottoni premuti per utilizzare i 3 tipi di indice, uno per volta
def aggiorna_stato_bottoni():
    btn1.config(relief=tk.SUNKEN if index_type_var.get() == 1 else tk.RAISED,
                bg='dark grey' if index_type_var.get() == 1 else 'light grey')
    btn2.config(relief=tk.SUNKEN if index_type_var.get() == 2 else tk.RAISED,
                bg='dark grey' if index_type_var.get() == 2 else 'light grey')
    btn3.config(relief=tk.SUNKEN if index_type_var.get() == 3 else tk.RAISED,
                bg='dark grey' if index_type_var.get() == 3 else 'light grey')


# aggiorna lo stato della directory, se non è selezionato alcun indice (quindi nessuno dei 3 bottoni) non è accessibile
def aggiorna_stato_bottone_directory():
    if any(index_type_var.get() == i for i in [1, 2, 3]):
        btn_directory.config(state=tk.NORMAL)
    else:
        btn_directory.config(state=tk.DISABLED)


# Bottone per selezionare la directory dei documenti su cui fare la scansione per il nuovo indice
def apri_directory():
    directory = filedialog.askdirectory()
    if directory:
        index_type = index_type_var.get()
        indexing.set_index_type(index_type)
        print(f"Directory selezionata: {directory}")
        progress_window = tk.Toplevel(root)
        progress_window.title("Avanzamento")
        tk.Label(progress_window, text="Creazione dell'indice in corso...").pack(padx=20, pady=20)
        center_window(progress_window, root)
        progress_window.update()
        progress_window.transient(root)
        progress_window.grab_set()
        indexing.cambia_indice(directory, progress_window, root)
        indexing.get_index()  # Aggiorna l'indice corrente
        indexing.get_word2vec_model()  # Aggiorna il modello corrente
        root.grab_set()


# Imposta nessun bottone premuto all'inizio
def init_interface():
    index_type_var.set(0)  # Non selezionare nessun bottone all'avvio
    aggiorna_stato_bottoni()
    aggiorna_stato_bottone_directory()


index_type_var = tk.IntVar(value=0)  # 0: nessuna selezione, 1: Con stopwords, 2: Senza stopwords, 3: Con sentiment

# Bottoni di configurazione
btn1 = tk.Button(control_frame, text="Stopwords", width=30,
                 command=lambda: cambia_indice_pulsante(1))
btn1.pack(pady=10)
btn2 = tk.Button(control_frame, text="No Stopwords", width=30,
                 command=lambda: cambia_indice_pulsante(2))
btn2.pack(pady=10)
btn3 = tk.Button(control_frame, text="Stopwords & Sentiment", width=30,
                 command=lambda: cambia_indice_pulsante(3))
btn3.pack(pady=10)
# Bottone per selezionare la directory dei documenti
btn_directory = tk.Button(control_frame, text="Scansiona cartella", width=20, command=apri_directory,
                          state=tk.DISABLED)
btn_directory.pack(pady=10)
tk.Label(control_frame, text="").pack(pady=5)
tk.Label(control_frame, text="").pack(pady=5)
# Label per la sezione di "Altre opzioni"
tk.Label(control_frame, text="Altre funzionalità").pack(pady=5)
# Pulsante per avviare lo scraping
btn_avvia_scraping = tk.Button(control_frame, text="Avvia Scraping", width=30,
                               command=lambda: scraping.avvia_scraping_GUI(root))
btn_avvia_scraping.pack(pady=10)
# Pulsante per avviare il benchmark
btn_benchmark = tk.Button(control_frame, text="Benchmark", width=30, command=benchmark.avvia_bench)
btn_benchmark.pack(pady=10)
# Aggiungi il bottone per chiudere il programma
btn_chiudi = tk.Button(control_frame, text="Esci", width=8, command=lambda: chiudi_programma(root))
btn_chiudi.pack(pady=10)
# Configurazione del layout a griglia per il frame principale
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=8)

# Imposta il nessun bottone come premuto all'avvio
init_interface()
root.mainloop()

# Funzione per avviare l'interfaccia grafica, richiamata da main.py
# Avvia il ciclo principale di Tkinter
try:
    root.mainloop()
except KeyboardInterrupt:
    print("Interruzione del ciclo principale di Tkinter.")
    root.destroy()
