import requests, os
from bs4 import BeautifulSoup
from whoosh.scoring import TF_IDF, BM25F
from whoosh import qparser, index
from whoosh.analysis import  StemmingAnalyzer
from whoosh.qparser import MultifieldParser, FuzzyTermPlugin, PhrasePlugin
from whoosh.qparser import QueryParser
from matplotlib.backends.backend_pdf import PdfPages
from gensim.models import Word2Vec

import math
import outputBench
import ricerche
import webbrowser

key_google = "AIzaSyDceo7ZM0YJGf3CEHCKgGi6BxE9B3CReXU"
id_motore = "2421bf90cf758400b"

key_scaleserp = "D29179D71904405484DE46CF83739BE2"
titleBoost = 2.0

descrizione_benchmark="Descrizione Benchmark:\nViene valutata l'efficacia del motore di ricerca confrontandolo con i risultati ottenuti da Google.\n\
Viene definito un insieme di query di prova che rappresentano le possibili richieste di ricerca degli utenti.\n\
Per ogni query, viene eseguita una ricerca su Google, limitando i risultati al sito 'genius.com' su cui abbiamo effettuato lo scraping:\n\
I primi 150 risultati di ricerca vengono estratti utilizzando l'API di ScaleSERP e salvati in file di testo separati per ciascuna query. Questi risultati rappresentano i documenti rilevanti per ciascuna query.\n\
Le stesse query vengono eseguite sul nostro motore di ricerca e vengono valutate due metriche di valutazione:\n\
-Precision@k: rapporto tra il numero di documenti rilevanti tra i primi k risultati restituiti dal nostro motore di ricerca e il numero di risultati restituiti. La precisione a k viene calcolata per k = 1, 2, ..., 10.\n\
-DCG: tiene conto della posizione dei documenti rilevanti nei risultati restituiti, applicando una penalizzazione logaritmica ai documenti rilevanti che compaiono più in basso nella lista dei risultati.\n"




# funzione per salvare le query in un file di testo
def save_queries(queries, filename):
    with open(filename, 'w') as file:
        for query in queries:
            file.write(query + '\n')


# funzione per caricare le query del file di testo in una lista
# se ricerca_google = True sostituisco gli spazi con un + per comporre l'url di  una ricerca google
def load_queries(filename, ricerca_google=False):
    queries = []
    with open(filename, 'r') as file:
        for line in file:
            # Rimuovi eventuali spazi bianchi e newline dalla riga e aggiungi la query alla lista
            query = line.strip()
            if ricerca_google:
                query = query.replace(' ', '+')
            queries.append(query)
    return queries


# funzione per ritornare i risultati delle ricerche google
def scaleserp_search(query, api_key, page, num_results=10):
    search_url = f"https://api.scaleserp.com/search"
    query += " site:genius.com"
    params = {
        'q': query,
        'api_key': api_key,
        'num': num_results,
        'page': page,
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        results = response.json()
        return results.get('organic_results', [])
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []


# funzione per salvare i primi total_results risultati delle ricerche google su un file di testo nella cartella nomeCartella
def save_google_links(queries, total_results=150):
    nomeCartella = "googleResults"
    if not os.path.exists(nomeCartella):
        os.mkdir(nomeCartella)
    for i, query in enumerate(queries):
        filename = f"{nomeCartella}/results_{i}.txt"

        with open(filename, 'w') as file:
            links = []
            for page in range(1, (total_results // 10) + 1):
                # print(page)
                results = scaleserp_search(query, key_scaleserp, page, num_results=10)
                print(results)
                links.extend(results)

            for link in links:
                url = link['link']
                if 'lyrics' in url:
                    file.write(url + '\n')


# funzione per avviare il salvataggio dei file di testo con query e risultati google
def salva_file_benchmark():
    queries = ["love", "imagine", "this is a beautiful day","man in the mirror","birds fly in different directions","it's my life","speak","cash","birds","coldplay"]
    save_queries(queries, "queries.txt")
    queries = load_queries("queries.txt", True)
    save_google_links(queries)


# funzione per calcolare la precisione alla posizione k
def precision_at_k(risultati_query, num_file_google, ris_word2vec=False):
    precision = []
    link_google = []
    with open(f"googleResults/results_{num_file_google}.txt", 'r') as file:
        for line in file:
            link = line.strip().strip('"').lower()
            link_google.append(link)
    num_rilevanti = 0

    for i, result in enumerate(risultati_query, start=1):
        if ris_word2vec == False:
            url = result['url'].strip().lower()
        else:
            url = result[0]['url'].strip().lower()
        print(i)
        if url in link_google:
            num_rilevanti += 1
        precision.append(num_rilevanti / i)

    print(precision)
    return precision


# funzione per calcolare il dcg
def calculate_dcg(risultati_query, num_file_google, ris_word2vec=False):
    link_google = []
    with open(f"googleResults/results_{num_file_google}.txt", 'r') as file:
        for line in file:
            link = line.strip().strip('"').lower()
            link_google.append(link)

    relevance_scores = {}
    for i, link in enumerate(link_google):
        if i < 15:
            relevance_scores[link] = 3
        elif i < 45:
            relevance_scores[link] = 2
        elif i < 90:
            relevance_scores[link] = 1
        else:
            relevance_scores[link] = 0

    # Calcola il DCG per i risultati della query
    dcg = 0
    for i, result in enumerate(risultati_query, start=1):
        if ris_word2vec == False:
            url = result['url'].strip().lower()
        else:
            url = result[0]['url'].strip().lower()
        if url in relevance_scores:
            print(f"punteggio rilevanza {relevance_scores[url]}")
            relevance = relevance_scores[url]
        else:
            relevance = 0

        if i == 1:
            dcg += relevance
        else:
            dcg += relevance / math.log2(i)

    return dcg

def preprocess_query(query):
    analyzer = StemmingAnalyzer()
    tokens = [token.text for token in analyzer(query)]
    return ' '.join(tokens)

def stampa_prec(precision_list):
    return [round(prec, 2) for prec in precision_list]

def avvia_bench():
    #salva_file_benchmark()
    queries=load_queries("queries.txt")
    #per ora parsing della query di benchmark solo su titolo e contenuto
    ix=index.open_dir("index_no_stopwords") 
    parser = MultifieldParser(["title", "content"], schema=ix.schema,fieldboosts={"title":titleBoost}) #Do un boost al titolo per la ricerca (il titolo ha un peso più importante rispetto alla norma)
    parser.add_plugin(FuzzyTermPlugin())
    parser.add_plugin(PhrasePlugin())
    searcher_tfidf=ix.searcher(weighting=TF_IDF())
    searcher_bm25 = ix.searcher(weighting=BM25F())

    ixStop=index.open_dir("index_stopwords")
    parserStop = MultifieldParser(["title", "content"], schema=ixStop.schema,fieldboosts={"title":titleBoost}) #Do un boost al titolo per la ricerca (il titolo ha un peso più importante rispetto alla norma)
    parserStop.add_plugin(PhrasePlugin())
    searcher_tfidf_Stop=ixStop.searcher(weighting=TF_IDF())
    searcher_bm25_Stop=ixStop.searcher(weighting=BM25F())

    word2vec_model = Word2Vec.load("word2vec_model/word2vec.model")

    with PdfPages('benchmark_results.pdf') as pdf_pages,open("risultati_benchmark.txt","w") as result_file:
        result_file.write(f"{descrizione_benchmark}")
        result_file.write(f"____________________________________________________________________________________________\n\n")
        for i,query in enumerate(queries):
            if i<8:   
                print(f"Risultati relativi a {query}")
                risultati_query_tfidf=ricerche.ricerca_query(parser,searcher_tfidf,query_str=query,stampa=False)
                risultati_query_bm25=ricerche.ricerca_query(parser,searcher_bm25,query_str=query,stampa=False)
                risultati_query_word2vec=ricerche.ricerca_combinata(searcher_bm25,word2vec_model,query_str=query,stampa=False)
                risultati_query_tfidf_Stop=ricerche.ricerca_query(parserStop,searcher_tfidf_Stop,query_str=query,stampa=False)
                risultati_query_bm25_Stop=ricerche.ricerca_query(parserStop,searcher_bm25_Stop,query_str=query,stampa=False)

                precision_tfidf=precision_at_k(risultati_query_tfidf,i)
                precision_bm25=precision_at_k(risultati_query_bm25,i)
                precision_tfidf_Stop=precision_at_k(risultati_query_tfidf_Stop,i)
                precision_bm25_Stop=precision_at_k(risultati_query_bm25_Stop,i)
                precision_word2vec=precision_at_k(risultati_query_word2vec,i,ris_word2vec=True)

                dcg_tfidf=calculate_dcg(risultati_query_tfidf,i)
                dcg_bm25=calculate_dcg(risultati_query_bm25,i)
                dcg_tfidf_Stop=calculate_dcg(risultati_query_tfidf_Stop,i)
                dcg_bm25_Stop=calculate_dcg(risultati_query_bm25_Stop,i)
                dcg_word2vec = calculate_dcg(risultati_query_word2vec, i,ris_word2vec=True)



                #print(dcg_tfidf,dcg_bm25)

                outputBench.add_page_to_pdf(pdf_pages, query, precision_tfidf, precision_bm25, precision_tfidf_Stop, precision_bm25_Stop, precision_word2vec, dcg_tfidf, dcg_bm25, dcg_tfidf_Stop, dcg_bm25_Stop, dcg_word2vec)
                
                query_senza_stopwords = preprocess_query(query)
                result_file.write(f"UIN: {query}\n")
                result_file.write(f"Query senza stopwords: {query_senza_stopwords}\n")
                result_file.write(f"RISULTATI\n")
                result_file.write(f"Precision@k TF-IDF senza stopwords: {stampa_prec(precision_tfidf)}\n")
                result_file.write(f"Precision@k BM25 senza stopwords: {stampa_prec(precision_bm25)}\n")
                result_file.write(f"DCG TF-IDF senza stopwords: {dcg_tfidf:.2f}\n")
                result_file.write(f"DCG BM25 senza stopwords: {dcg_bm25:.2f}\n")
                result_file.write(f"Precision@k TF-IDF con stopwords: {stampa_prec(precision_tfidf_Stop)}\n")
                result_file.write(f"Precision@k BM25 con stopwords: {stampa_prec(precision_bm25_Stop)}\n")
                result_file.write(f"DCG TF-IDF con stopwords: {dcg_tfidf_Stop:.2f}\n")
                result_file.write(f"DCG BM25 con stopwords: {dcg_bm25_Stop:.2f}\n")
                result_file.write(f"Word2Vec\n")
                result_file.write(f"Precision@k Word2Vec: {stampa_prec(precision_word2vec)}\n")
                result_file.write(f"DCG Word2Vec: {dcg_word2vec:.2f}\n")
                result_file.write("\n")
            elif i==8:
                parserTitolo=QueryParser("title", schema=ixStop.schema)  
                searcherTitolo=ixStop.searcher(weighting=TF_IDF())
                risultati_titolo=ricerche.ricerca_query(parserTitolo,searcherTitolo,query_str=query)
                precision_titolo=precision_at_k(risultati_titolo,i)
                dcg_titolo=calculate_dcg(risultati_titolo,i)
                outputBench.add_page_titolo_artista(pdf_pages,query,precision_titolo,dcg_titolo,"TITLE")
                
                result_file.write(f"UIN ricerca per titolo: {query}\n")
                result_file.write(f"Precision@k ricerca per titolo: {stampa_prec(precision_titolo)}\n")
                result_file.write(f"DCG ricerca per titolo: {dcg_titolo:.2f}\n")
            else:
                parserArtista=QueryParser("artist", schema=ixStop.schema)  
                searcherArtista=ixStop.searcher(weighting=TF_IDF())
                risultati_artista=ricerche.ricerca_query(parserArtista,searcherArtista,query_str=query)
                precision_artista=precision_at_k(risultati_artista,i)
                dcg_artista=calculate_dcg(risultati_artista,i)
                outputBench.add_page_titolo_artista(pdf_pages,query,precision_artista,dcg_artista,"ARTIST")
                
                result_file.write(f"UIN ricerca per artista: {query}\n")
                result_file.write(f"Precision@k ricerca per artista: {stampa_prec(precision_artista)}\n")
                result_file.write(f"DCG ricerca per artista: {dcg_artista:.2f}\n")

    webbrowser.open('benchmark_results.pdf')
