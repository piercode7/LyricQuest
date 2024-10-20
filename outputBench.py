import matplotlib.pyplot as plt

def plot_precision(ax, precision, label):
    line, = ax.plot(range(1, len(precision) + 1), precision, marker='o', label=label)
    return line

def stampa_prec(precision_list):
    return [round(prec, 2) for prec in precision_list]

def add_page_to_pdf(pdf_pages, query, precision_tfidf, precision_bm25, precision_tfidf_Stop, precision_bm25_Stop,
                    precision_word2vec, dcg_tfidf, dcg_bm25, dcg_tfidf_Stop, dcg_bm25_Stop, dcg_word2vec):
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    # Grafico della ricerca senza stopwords
    lines = []
    lines.append(plot_precision(axs[0, 0], precision_tfidf, 'TF-IDF'))
    lines.append(plot_precision(axs[0, 0], precision_bm25, 'BM25'))
    axs[0, 0].set_title(f'Precision at k for query: "{query}" (without stopwords)')
    axs[0, 0].legend(handles=lines, loc='best')

    # Grafico della ricerca con stopwords
    lines = []
    lines.append(plot_precision(axs[0, 1], precision_tfidf_Stop, 'TF-IDF'))
    lines.append(plot_precision(axs[0, 1], precision_bm25_Stop, 'BM25 '))
    axs[0, 1].set_title(f'Precision at k for query: "{query}" (with stopwords)')
    axs[0, 1].legend(handles=lines, loc='best')

    # Grafico Word2Vec in basso a sinistra
    lines = []
    lines.append(plot_precision(axs[1, 0], precision_word2vec, 'Word2Vec'))
    axs[1, 0].set_title(f'Precision at k for query: "{query}" (Word2Vec)')
    axs[1, 0].legend(handles=lines, loc='best')

    # Testo dei valori DCG in basso a destra
    dcg_text = (
        f'DCG Values:\n\n'
        f'TF-IDF (without stopwords): {dcg_tfidf:.2f}\n'
        f'BM25 (without stopwords): {dcg_bm25:.2f}\n'
        f'-------------------------------------\n'
        f'TF-IDF (with stopwords): {dcg_tfidf_Stop:.2f}\n'
        f'BM25 (with stopwords): {dcg_bm25_Stop:.2f}\n'
        f'-------------------------------------\n'
        f'Word2Vec: {dcg_word2vec:.2f}'
    )
    axs[1, 1].text(0.5, 0.5, dcg_text, ha='center', va='center', fontsize=12, transform=axs[1, 1].transAxes)
    axs[1, 1].axis('off')

    # Salva la pagina nel PDF
    pdf_pages.savefig(fig)
    plt.close(fig)


def add_page_titolo_artista(pdf_pages, query, precision, dcg,tipologia):
    fig, (ax_plot, ax_text) = plt.subplots(1, 2, figsize=(15, 7))

    # Grafico della precisione
    plot_precision(ax_plot, precision, 'Precision')
    ax_plot.set_title(f'Precision at k for {tipologia} query: "{query}"')
    ax_plot.legend(loc='best')

    # Testo della precisione e DCG
    precision_dcg_text = (
        f'Precision at k:\n{stampa_prec(precision)}\n\n'
        f'DCG: {dcg:.2f}'
    )
    ax_text.text(0.5, 0.5, precision_dcg_text, ha='center', va='center', fontsize=12)
    ax_text.axis('off')

    # Salva la pagina nel PDF
    pdf_pages.savefig(fig)
    plt.close(fig)