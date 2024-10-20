from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
import requests
import re
import random
import time
from selenium import webdriver
import pickle

from selenium.common import NoSuchWindowException

# USER AGENT da usare per le richieste GET
# Ne uso più di uno per non rischiare di venire bannato
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
]

titles = []

NUMERO_ARTISTI = 200
NUMERO_CANZONI = 100


# Funzione per modificare stringa degli ARTISTI per l'url
def modificaStringaUrl(stringa):
    special_chars = ["'", '£', "%", '/', '.', '(', ')', '=', '?', '[', ']', '#', '@', '|', ',', '¥', '\u200b']
    removeSpecialChars = stringa.replace('&', 'and')
    removeSpecialChars = removeSpecialChars.replace('$', ' ')
    removeSpecialChars = removeSpecialChars.replace('!', ' ')
    removeSpecialChars = removeSpecialChars.replace('é', 'e')
    removeSpecialChars = removeSpecialChars.replace('è', 'e')
    removeSpecialChars = removeSpecialChars.replace('ë', 'e')
    removeSpecialChars = removeSpecialChars.replace('í', 'i')
    removeSpecialChars = removeSpecialChars.replace('ì', 'i')

    removeSpecialChars = removeSpecialChars.replace(' ', '-')

    # removeSpecialChars=removeSpecialChars.replace(' ','')

    for symbol in special_chars:
        if symbol in removeSpecialChars:
            removeSpecialChars = removeSpecialChars.replace(symbol, "")

    return removeSpecialChars.lower()


# Funzione per modificare stringa dei TITOLI per l'url
# potevo fare in un'unica funzione

def modificaStringaTitolo(stringa):
    special_chars = ["'", '£', "%", '/', '.', '(', ')', '=', '?', '[', ']', '#', '@', '|', ',', '¥', '\u200b', "’",
                     "”", ]
    removeSpecialChars = stringa.replace('$', 's')
    removeSpecialChars = removeSpecialChars.replace('!', 'i')
    removeSpecialChars = removeSpecialChars.replace('é', 'e')
    removeSpecialChars = removeSpecialChars.replace('è', 'e')
    removeSpecialChars = removeSpecialChars.replace('í', 'i')
    removeSpecialChars = removeSpecialChars.replace('ë', 'e')

    removeSpecialChars = removeSpecialChars.replace(' ', '-')

    for symbol in special_chars:
        if symbol in removeSpecialChars:
            removeSpecialChars = removeSpecialChars.replace(symbol, "")

    return removeSpecialChars.lower()


# Funzione per cercare i top X artisti dal sito Kworb, che ci serviranno per ricercare le varie canzoni
def cercaArtisti():
    URL = "https://kworb.net/spotify/listeners.html"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    td_artisti = soup.findAll("td", class_="text")
    elencoArtisti = []
    for i, td in enumerate(td_artisti):
        if td.text == '¥$':
            continue
        elencoArtisti.append(td.text)
        if i >= NUMERO_ARTISTI:
            break

    return elencoArtisti


# Funzione per cercare i titoli e creare gli url
def cercaCanzoni(artisti):
    driver = webdriver.Chrome()  # You should replace this with the appropriate web driver you're using (Chrome, Firefox, etc.)
    driver.set_window_size(1920, 1080)
    BASE_URL = "https://genius.com/artists/"
    urls = []
    artist_songs = {}
    try:
        for artista in artisti:
            delay = random.uniform(0.3, 2)
            time.sleep((delay))
            artistaMod = modificaStringaUrl(artista)
            url = BASE_URL + artistaMod + '/songs'
            driver.get(url)  # Do l'url per driver di Selenium
            scroll_pause_time = 1.5  # Pause between each scroll
            screen_height = driver.execute_script("return window.screen.height;")
            i = 0
            while i < 10:  # eseguo 10 scroll della pagina con selenium
                driver.execute_script(f"window.scrollTo(0, {1500 * i});")  # avvio dello script
                i += 1
                time.sleep(scroll_pause_time)
                scroll_height = driver.execute_script(
                    "return document.body.scrollHeight;")  # setto altezza dello scroll
                if screen_height * i > scroll_height:
                    print("Limite")
                    break
            soup = BeautifulSoup(driver.page_source, "html.parser")
            h3_canzoni = soup.findAll("h3", class_="ListItem__Title-sc-122yj9e-4")
            songs = []
            for i, canzone in enumerate(h3_canzoni):
                if i > NUMERO_CANZONI:
                    break
                song = canzone.text
                titles.append(song)
                song = modificaStringaTitolo(song)
                urlCanzone = f"https://genius.com/{artistaMod}-{song}-lyrics"  # Creazione url titolo canzone
                songs.append(urlCanzone)  # Lista di canzoni per ogni artista
                print(str(i) + ")creato: " + urlCanzone)
            artist_songs[artista] = songs  # per ogni artista aggiungo la lista di canzoni
    except NoSuchWindowException:
        print("Finestra chiusa, interruzione dello scraping.")
    finally:
        driver.quit()

    with open('artist_urls.pkl', 'wb') as file:
        pickle.dump(artist_songs, file)
        pickle.dump(titles, file)
    return artist_songs, titles


# Funzione per salvare i documenti
def salvaDocumenti(artist_songs, titles, dest_dir):
    id = 0
    iterator_titles = iter(titles)
    for url in artist_songs:
        headers = {'User-Agent': random.choice(user_agents)}
        print(url)
        try:
            titolo = next(iterator_titles)
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.content, "html.parser")
            a_artista = soup.select('a.HeaderArtistAndTracklistdesktop__Artist-sc-4vdeb8-1')
            artist = [tag.string for tag in a_artista]
            if a_artista:
                artist = a_artista[0].string
                print(artist)
            else:
                artist = "Artista non trovato"
            for br in soup('br'):
                br.replace_with(' ')
            div_testo = soup.select('div[class*="Lyrics__Container-sc-"]')
            testoCanzone = ""
            for div in div_testo:
                testoCanzone += div.text
                testoCanzone = re.sub('\[[^\]]*\]', '', testoCanzone)
                testoCanzone = testoCanzone.replace("  ", "\n")
            try:
                if detect(testoCanzone) == 'en':
                    with open(f"{dest_dir}/{id}.txt", "w") as file:
                        file.write(url + "\n")
                        file.write(artist + "\n")
                        file.write(titolo + "\n")
                        file.write(testoCanzone)
                        id += 1
            except LangDetectException:
                pass
        except requests.exceptions.ConnectionError:
            time.sleep(5)
