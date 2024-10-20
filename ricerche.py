import word2vec_utils
from whoosh.qparser import MultifieldParser, FuzzyTermPlugin, PhrasePlugin
from gensim.utils import simple_preprocess
import numpy as np


# Usata per il benchmark
def ricerca_query(parser, searcher, query_str=None, corrected=False, stampa=True):
    if query_str == None:
        query_str = input("Inserisci la tua query (o 'exit' per uscire): ")

    # Se l'utente vuole uscire
    if query_str.lower() == 'exit':
        return

    # Parsing della query
    query = parser.parse(query_str)
    results = searcher.search(query, limit=10)  # Limita i risultati a 10

    # Se non vengono trovati risultati si prova a correggere la query
    if len(results) == 0:
        if corrected == False:
            # implementazione correzione automatica della query
            query_corrected = searcher.correct_query(query, query_str)
            if query_corrected:
                print(f"Query corretta\nRisultati relativi a {query_corrected.string}: ")
                ricerca_query(parser, searcher, query_corrected.string, corrected=True)

    # Stampa i risultati
    if stampa:
        print(f"\nRICERCA\nRisultati trovati: {len(results)}")
        for result in results:
            print(f"Titolo: {result['title']}")
            print(f"URL: {result['url']}")
            print(f"Nome File: {result['nameFile']}")
            print("")

    return results


def ricerca_con_word2vec(searcher, word2vec_model, query_str=None):
    if query_str is None:
        query_str = input("Inserisci la tua query (o 'exit' per uscire): ")

    # Se l'utente vuole uscire
    if query_str.lower() == 'exit':
        return
    query_words = simple_preprocess(query_str)
    query_vector = word2vec_utils.get_average_vector(word2vec_model, query_str, query_words)
    results = []
    with searcher.reader() as reader:
        for hit in reader.all_stored_fields():
            content_vector = np.array(hit['content_vector'].split(), dtype=np.float32)
            similarity = word2vec_utils.cosine_similarity(query_vector, content_vector)
            results.append((hit, similarity))

    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\nRICERCA\nRisultati trovati: {len(results)}")
    for result, similarity in results[:10]:
        print(f"Titolo: {result['title']}")
        print(f"Url: {result['url']}")
        print(f"Nome File: {result['nameFile']}")
        print(f"Similarità: {similarity}")
        print("")

    return results


def ricerca_bm25(searcher, query_str):
    parser = MultifieldParser(["title", "content"], schema=searcher.schema, fieldboosts={"title": 2.0})
    parser.add_plugin(FuzzyTermPlugin())
    parser.add_plugin(PhrasePlugin())
    query = parser.parse(query_str)
    results = searcher.search(query, limit=100)  # Limitiamo a 100 risultati
    return results


def improve_with_word2vec(bm25_results, word2vec_model, query_str):
    query_vector = word2vec_utils.get_average_vector(word2vec_model, query_str)
    improved = []
    for hit in bm25_results:
        content_vector = np.array(hit['content_vector'].split(), dtype=np.float32)
        similarity = word2vec_utils.cosine_similarity(query_vector, content_vector)
        improved.append((hit, similarity))

    improved.sort(key=lambda x: x[1], reverse=True)
    return improved


def ricerca_combinata(searcher, word_2_vec_model, query_str=None, stampa=True):
    if query_str is None:
        query_str = input("Inserisci la tua query (o 'exit' per uscire): ")
    # Se l'utente vuole uscire
    if query_str.lower() == 'exit':
        return
    bm25_results = ricerca_bm25(searcher, query_str)
    improved = improve_with_word2vec(bm25_results, word_2_vec_model, query_str)
    if stampa:
        print(f"\nRICERCA COMBINATA\nRisultati trovati: {len(improved)}")
        for result, similarity in improved[:10]:
            print(f"Titolo: {result['title']}")
            print(f"URL: {result['url']}")
            print(f"Nome File: {result['nameFile']}")
            print(f"Similarità: {similarity}\n")
    return improved[:10]
