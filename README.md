
## Installazione

Istruzioni passo-passo su come installare il progetto e le dipendenze.

1. unzippare la cartella del progetto

2. Accedi alla directory del progetto:

    ```bash
    cd Engine-Main
    ```

3. Installa le dipendenze dal file `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```
4. Esegui il modulo main di Python:
	
	```bash
    python main.py
    ```

## Uso dell'applicazione

Per poter utilizzare il Search Engine è necessario avere una directory contenente i documenti di testo con le canzoni: avviare quindi lo scraping col relativo pulsante
o unzippare all'interno della cartella del progetto il file zip fornito (all'interno della cartella drive) con i documenti da noi scaricati.
Successivamente, se non è già stato fatto, bisogna andare a creare almeno un inverted index tra i 3 proposti: con o stenza stopwords, oppure sentiment (la creazione con la sentiment impiega circa 40 minuti, per comodità alleghiamo il link ad una cartella drive con l'indice con sentiment da inserire nella directory del progetto).
Fatto ciò sarà possibile ogni volta che si sceglie l'indice desiderato effettuare le proprie query di ricerca e sarà possibile scegliere quale metodo di ranking utilizzare tra i 3 proposti.

LINK AL DRIVE: https://drive.google.com/drive/folders/16FZe3lJFzlpmqEcx1_UX28CsK9Udv4hB?usp=drive_link
nel drive è presente anche il file zip che contiene i documenti già scaricati, inserire la cartella unzippata nella directory del progetto.

## Esecuzione del benchmark e lettura dei dati

Per eseguire il benchmark premere il relativo pulsante in basso a sinistra.
IMPORTANTE: per il corretto funzionamento del benchmark è necessario aver già creato almeno una volta entrambi gli inverted index con e senza stopwords.

Una volta avviato il benchmark verrà aperto in automatico sul browser predefinito il pdf con i relativi dati. Viene inoltre creato il file di testo "risultati_benchmark.txt" con qualche informazione aggiuntiva.


#Aggiornamento per novembre 2024
# Nuovo progetto Python da avviare da zero con una versione precisa di python
1. sudo apt install python3.10-venv python3.10-distutils
2. python3.10 -m venv myenv
3. source myenv/bin/activate
4. python3.10 -m ensurepip --upgrade
5. pip install -r requirements.txt

