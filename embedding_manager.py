import torch  # PyTorch: usata per la gestione dei sensori/tensori e la modalità di inferenza
import fm     # RNA-FM Foundation Model: libreria dedicata al modello pre-addestrato per RNA

# ==============================================================================
# TASK 3: IMPLEMENTAZIONE MECCANISMO DI CACHING IN MEMORIA
# ==============================================================================
# Dizionario globale in RAM per memorizzare le sequenze già calcolate.
# Struttura -> CHIAVE: sequenza RNA pulita (str) | VALORE: tupla (avg_pooling, max_pooling)
# La tupla viene creata in questo punto: coppia_embeddings = (avg_pooling, max_pooling)
EMBEDDING_CACHE = {}

# ==============================================================================
# VARIABILI GLOBALI E LAZY LOADING
# ==============================================================================
# Inizializziamo le variabili del modello a None. Verranno caricate in memoria 
# solo al primo utilizzo effettivo (pattern Lazy Loading) per velocizzare l'avvio del server.
_MODEL = None
_ALPHABET = None
_BATCH_CONVERTER = None

def _carica_modello_rna_fm():
    """
    Carica il modello RNA-FM in memoria RAM solo quando viene invocato per la prima volta.
    Fornisce il supporto all'esecuzione su CPU.
    """
    # Dichiarazione per accedere e modificare le variabili globali
    global _MODEL, _ALPHABET, _BATCH_CONVERTER
    
    # Se il modello non è ancora stato caricato in RAM...
    if _MODEL is None:
        # TASK 4: Stampa messaggio di log per il tracciamento del caricamento
        print("⏳ Caricamento del modello RNA-FM in memoria CPU...")
        
        # ----------------------------------------------------------------------
        # TASK 1: ESTRAZIONE EMBEDDINGS DI SEQUENZE SINGLE (Caricamento Modello CPU)
        # ----------------------------------------------------------------------
        # Carica la versione pre-addestrata t12 di RNA-FM e l'alfabeto dei nucleotidi
        _MODEL, _ALPHABET = fm.pretrained.rna_fm_t12()
        
        # Estrae il convertitore che trasforma le stringhe di testo in token numerici
        _BATCH_CONVERTER = _ALPHABET.get_batch_converter()
        
        # Imposta il modello in modalità valutazione (disattiva dropout/batchnorm)
        _MODEL.eval()
        
        # TASK 4: Stampa di conferma caricamento completato
        print("✅ Modello RNA-FM caricato e pronto all'uso su CPU!")


def calcola_o_recupera_embedding(sequenza: str):
    """
    Gestisce il flusso completo:
    1. Sanitizza la sequenza di input.
    2. Controlla la presenza in Cache (Task 3).
    3. Esegue l'estrazione con RNA-FM su CPU (Task 1).
    4. Calcola Average e Max Pooling (Task 2).
    5. Stampa i messaggi di stato nel terminale (Task 4).
    """
    
    # Normalizzazione difensiva: rimuove spazi, converte in maiuscolo e sostituisce le Timine (T) con Uracili (U)
    seq_pulita = sequenza.strip().upper().replace("T", "U")

    # --------------------------------------------------------------------------
    # TASK 3: CONTROLLO DELLA CACHE IN MEMORIA
    # --------------------------------------------------------------------------
    # Se la sequenza è già stata analizzata in precedenza...
    if seq_pulita in EMBEDDING_CACHE:
        # TASK 4: Stampa del messaggio di notifica (CACHE HIT)
        print(f"⚡ [CACHE HIT] Embedding già presente in memoria per la sequenza ({len(seq_pulita)} nt): {seq_pulita[:10]}...")
        
        # Restituisce immediatamente il risultato salvato senza richiamare il modello PyTorch
        return EMBEDDING_CACHE[seq_pulita]
    
    # --------------------------------------------------------------------------
    # TASK 1: ESTRAZIONE EMBEDDINGS CON RNA-FM SU CPU
    # --------------------------------------------------------------------------
    # Invocazione della funzione di Lazy Loading (carica il modello se _MODEL è None)
    _carica_modello_rna_fm()

    # Formattazione del dato per il batch converter di RNA-FM: lista di tuple (id_etichetta, sequenza)
    # Il modello accoglie la seueuenza di basi nello specifico formato [(id, sequenza)] e restituisce i token numerici corrispondenti
    data = [("rna_seq", seq_pulita)] 
    
    # ESECUZIONE MODELLO: converte la sequenza di basi nei corrispettivi token numerici leggibili dal modello Transformer
    _, _, batch_tokens = _BATCH_CONVERTER(data)

    # Disabilita il calcolo dei gradienti PyTorch per risparmiare RAM e velocizzare l'inferenza su CPU
    with torch.no_grad():
        # Esegue il passaggio forward nel modello chiedendo di estrarre le rappresentazioni del layer 12
        results = _MODEL(batch_tokens, repr_layers=[12])

    # Estrae la matrice delle rappresentazioni dei token dal dodicesimo layer (layer 12)
    token_representations = results["representations"][12]
    
    # Rimuove i token speciali di inizio sequenza (<cls>) e fine sequenza (<eos>) prendendo solo gli elementi 1:-1
    seq_rep = token_representations[0, 1:-1]

    # --------------------------------------------------------------------------
    # TASK 2: ESTRAZIONE AVERAGE E MAX POOLING
    # --------------------------------------------------------------------------
    # Calcola l'Average Pooling (media dei vettori lungo la dimensione dei nucleotidi) e converte in array NumPy
    avg_pooling = seq_rep.mean(dim=0).numpy()
    
    # Calcola il Max Pooling (valore massimo dei vettori lungo la dimensione dei nucleotidi) e converte in array NumPy
    max_pooling = seq_rep.max(dim=0).values.numpy()

    # Raggruppa i due vettori compressi in una tupla
    coppia_embeddings = (avg_pooling, max_pooling)

    # --------------------------------------------------------------------------
    # TASK 3: SALVATAGGIO DEL RISULTATO IN CACHE
    # --------------------------------------------------------------------------
    # Memorizza la tupla appena calcolata usando la sequenza pulita come chiave
    EMBEDDING_CACHE[seq_pulita] = coppia_embeddings

    # --------------------------------------------------------------------------
    # TASK 4: STAMPA DEL MESSAGGIO DI NOTIFICA
    # --------------------------------------------------------------------------
    # Notifica sul terminale del server che il calcolo degli embedding è avvenuto con successo
    print(f"🧠 [EMBEDDING CALCOLATO] Average e Max pooling calcolati con successo per la sequenza: {seq_pulita[:10]}...")
    
    # Restituisce la tupla contenente (array_average_pooling, array_max_pooling)
    return coppia_embeddings