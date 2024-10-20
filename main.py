import gui

def main():
    try:
        gui.avvia_gui()
        # Creazione dell'indice o altre operazioni di inizializzazione
    except KeyboardInterrupt:
        print("Programma interrotto dall'utente.")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    main()
