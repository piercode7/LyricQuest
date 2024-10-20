import searchLyrics as srcLyr
import pickle
import itertools
import tkinter as tk
from tkinter import messagebox
import os
import threading

dest_dir = "DestScraping"

def avvia_scraping():
    artist_songs = {}
    artisti = srcLyr.cercaArtisti()
    artist_songs, titles = srcLyr.cercaCanzoni(artisti)
    with open("artist_urls.pkl", "rb") as file:
        artist_songs = pickle.load(file)
        titles = pickle.load(file)

    listaDiListe = artist_songs.values()
    merged = list(itertools.chain(*listaDiListe))

    # print(merged.index("https://genius.com/young-miko-trending-lyrics"))

    # print(titles.index("Trending"))

    srcLyr.salvaDocumenti(merged, titles, dest_dir)




# aziona la fase di scraping
def avvia_scraping_GUI(root):
    # Messaggio informativo che indica dove saranno salvati i file ottenuti dallo scraping
    messagebox.showinfo("Informazione",
                        "I file ottenuti dallo scraping saranno presenti in DestScraping. Potrai selezionarla per lo scanner in seguito. "
                        "Per interrompere lo scraping è sufficiente chiudere il browser su cui è in corso.")

    # Finestra di progresso
    progress_win = tk.Toplevel(root)
    progress_win.title("Scraping in corso...")
    progress_win.geometry("300x100")
    tk.Label(progress_win, text="Scraping in corso...").pack(pady=20)

    # se non esiste viene creata per contenere i file al termine dello scraping


    # Crea la cartella se non esiste
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    def start_scraping():
        try:
            avvia_scraping()
            if progress_win.winfo_exists():
                messagebox.showinfo("Completato", "Scraping completato! I file sono stati salvati in: DestScraping")
            progress_win.destroy()
        except Exception as e:
            if progress_win.winfo_exists():
                messagebox.showerror("Errore", f"Lo scraping è stato interrotto!")
                progress_win.destroy()

    threading.Thread(target=start_scraping).start()
