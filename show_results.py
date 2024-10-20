import tkinter as tk
from tkinter import messagebox
import ast
from utils import get_selected_emotions, ordina_risultati, get_highlight_with_query, rimuovi_righe_vuote_iniziali


#######################################à RISULTATI RICERCHE GENERICHE ##################################################
def mostra_risultati_GUI(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback):
    if results is not None:
        if elapsed_time is not None:
            elapsed_time += 0.3
            output = [f"RICERCA\nRisultati: {len(results)}, trovati in {elapsed_time:.3f} secondi"]
    else:
        output = [f"RICERCA\nNessun risultato trovato"]
    url_callbacks = {}
    artist_callbacks = {}
    selected_emotions = get_selected_emotions(emotion_buttons)

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
    except TypeError:
        messagebox.showwarning("Attenzione", "Aggiorna i risultati dopo avere caricato il nuovo indice. "
                                             "Utilizza una delle ricerche a lato, o seleziona un artista.")
        return




    end_offset = min(current_offset + page_size, len(results))
    for idx in range(current_offset, end_offset):
        result = results[idx]
        emozioni = None
        if 'emotions' in result and result['emotions']:
            try:
                emozioni = ast.literal_eval(result['emotions'])  # Converti la stringa in dizionario
            except (SyntaxError, ValueError) as e:
                print(f"Errore nel valutare le emozioni: {e}")

        # Output effettivo per ogni brano trovato
        output.append(f"Titolo: {result['title']}")
        output.append(f"URL: {result['url']}")
        output.append(f"Artista: {result['artist']}")
        highlight = get_highlight_with_query(result.highlights('content'))
        highlight = rimuovi_righe_vuote_iniziali(highlight)  # Usa la funzione e assegna il risultato
        if highlight:  # Aggiungi il controllo per verificare se il match esiste ed è non vuoto
            output.append(f"Match: {highlight}")
        output.append(f"Nome File: {result['nameFile']}")
        if emozioni:
            output.append(f"Emozioni: {', '.join([f'{emotion}: {score:.2f}' for emotion, score in emozioni.items()])}")
        output.append("")
        # Il link è reso cliccabile
        url_callbacks[result['url']] = make_link_callback(result['url'])
        # Il nome dell'artista è reso cliccabile
        artist_callbacks[result['artist']] = make_artist_callback(result['artist'], output_widget)

    output_text = "\n".join(output)
    if output_widget:
        output_widget.config(state=tk.NORMAL)
        output_widget.delete("1.0", tk.END)
        output_widget.insert(tk.END, output_text)
        output_widget.config(state=tk.DISABLED)

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

        # Aggiungi i pulsanti di navigazione
        if current_offset > 0:
            btn_mostra_precedenti = tk.Button(output_widget, text="<",
                                              command=lambda: mostra_precedenti(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback))
            output_widget.window_create("end", window=btn_mostra_precedenti)
        if end_offset < len(results):
            btn_mostra_altri = tk.Button(output_widget, text=">",
                                         command=lambda: mostra_altri(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback))
            output_widget.window_create("end", window=btn_mostra_altri)


def mostra_altri(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback):
    current_offset += page_size
    elapsed_time -= 0.3

    mostra_risultati_GUI(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback)


def mostra_precedenti(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback):
    current_offset = max(0, current_offset - page_size)
    elapsed_time -= 0.3

    mostra_risultati_GUI(output_widget, elapsed_time, results, current_offset, page_size, emotion_buttons, indexing, make_link_callback, make_artist_callback)


################################## RISULTATI W2V ########################################################################
def mostra_risultati_w2v_GUI(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time):
    if results_w2v is not None:
        elapsed_time += 0.3
        output = [f"RICERCA WORD2VEC\nRisultati con Word2Vec: {len(results_w2v)}, trovati in {elapsed_time:.3f} secondi"]
    else:
        output = [f"RICERCA\nNessun risultato trovato"]

    url_callbacks = {}
    artist_callbacks = {}
    selected_emotions = get_selected_emotions(emotion_buttons)

    try:
        # Ordina i risultati solo se use_sent è True
        if indexing.use_sent:
            selected_emotions = get_selected_emotions(emotion_buttons)
            results_w2v = ordina_risultati(results_w2v, selected_emotions)
        else:
            # Se ci sono emozioni selezionate e l'indice non supporta i sentimenti, mostra un messaggio di avviso
            if selected_emotions:
                messagebox.showwarning("Attenzione",
                                       "L'indice in uso non dispone di tecniche di analisi del sentimento. Selezionare indice con funzionalità annessa!")
                return
    except TypeError:
        messagebox.showwarning("Attenzione", "Aggiorna i risultati dopo avere caricato il nuovo indice. "
                                             "Utilizza una delle ricerche a lato, o seleziona un artista.")
        return

    end_offset_w2v = min(current_offset_w2v + page_size_w2v, len(results_w2v))
    for idx in range(current_offset_w2v, end_offset_w2v):
        result, similarity = results_w2v[idx]
        emozioni = None
        if 'emotions' in result and result['emotions']:
            try:
                emozioni = eval(result['emotions'])  # Converti la stringa in dizionario
            except Exception as e:
                print(f"Errore nel valutare le emozioni: {e}")

        # Output effettivo per ogni brano trovato
        output.append(f"Titolo: {result['title']}")
        output.append(f"URL: {result['url']}")
        output.append(f"Artista: {result['artist']}")
        highlight = get_highlight_with_query(result.highlights('content'))
        highlight = rimuovi_righe_vuote_iniziali(highlight)  # Usa la funzione e assegna il risultato
        if highlight:  # Aggiungi il controllo per verificare se il match esiste ed è non vuoto
            output.append(f"Match: {highlight}")
        output.append(f"Nome File: {result['nameFile']}")
        if emozioni:
            output.append(f"Emozioni: {', '.join([f'{emotion}: {score:.2f}' for emotion, score in emozioni.items()])}")
        output.append(f"Similarità: {similarity:.4f}")
        output.append("")
        # Il link è reso cliccabile
        url_callbacks[result['url']] = make_link_callback(result['url'])
        # Il nome dell'artista è reso cliccabile
        artist_callbacks[result['artist']] = make_artist_callback(result['artist'], results_text)

    output_text = "\n".join(output)
    if results_text:
        results_text.config(state=tk.NORMAL)
        results_text.delete("1.0", tk.END)
        results_text.insert(tk.END, output_text)
        results_text.config(state=tk.DISABLED)

        for url, callback in url_callbacks.items():
            start_index = "1.0"
            while True:
                start_index = results_text.search(url, start_index, stopindex=tk.END)
                if not start_index:
                    break
                end_index = results_text.index(f"{start_index} + {len(url)}c")
                results_text.tag_add(url, start_index, end_index)
                results_text.tag_config(url, foreground="blue", underline=True)
                results_text.tag_bind(url, "<Button-1>", callback)
                results_text.tag_bind(url, "<Enter>", lambda e: results_text.config(cursor="hand2"))
                results_text.tag_bind(url, "<Leave>", lambda e: results_text.config(cursor=""))
                start_index = end_index

        for artist, callback in artist_callbacks.items():
            start_index = "1.0"
            while True:
                start_index = results_text.search(artist, start_index, stopindex=tk.END)
                if not start_index:
                    break
                end_index = results_text.index(f"{start_index} + {len(artist)}c")
                results_text.tag_add(artist, start_index, end_index)
                results_text.tag_config(artist, foreground="green", underline=True)
                results_text.tag_bind(artist, "<Button-1>", callback)
                results_text.tag_bind(artist, "<Enter>", lambda e: results_text.config(cursor="hand2"))
                results_text.tag_bind(artist, "<Leave>", lambda e: results_text.config(cursor=""))
                start_index = end_index

        # Aggiungi i pulsanti di navigazione
        if current_offset_w2v > 0:
            btn_mostra_precedenti_w2v = tk.Button(results_text, text="<", command=lambda: mostra_precedenti_w2v(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time))
            results_text.window_create("end", window=btn_mostra_precedenti_w2v)
        if end_offset_w2v < len(results_w2v):
            btn_mostra_successivi_w2v = tk.Button(results_text, text=">", command=lambda: mostra_successivi_w2v(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time))
            results_text.window_create("end", window=btn_mostra_successivi_w2v)

def mostra_precedenti_w2v(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time):
    if current_offset_w2v > 0:
        elapsed_time -= 0.3
        current_offset_w2v = max(0, current_offset_w2v - page_size_w2v)
        mostra_risultati_w2v_GUI(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time)

def mostra_successivi_w2v(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time):
    if current_offset_w2v + page_size_w2v < len(results_w2v):
        elapsed_time -= 0.3
        current_offset_w2v = min(len(results_w2v) - 1, current_offset_w2v + page_size_w2v)
        mostra_risultati_w2v_GUI(results_w2v, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time)

def aggiorna_results_text_w2v(results, results_text, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, make_link_callback, make_artist_callback, elapsed_time):
    current_offset_w2v = 0
    mostra_risultati_w2v_GUI(results, current_offset_w2v, page_size_w2v, emotion_buttons, indexing, results_text, make_link_callback, make_artist_callback, elapsed_time)




