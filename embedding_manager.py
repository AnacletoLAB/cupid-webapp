import numpy as np
import torch  # PyTorch: usata per la gestione dei sensori/tensori e la modalità di inferenza
import fm     # RNA-FM Foundation Model: libreria dedicata al modello pre-addestrato per RNA

# ==============================================================================
# TASK 3: IMPLEMENTAZIONE MECCANISMO DI CACHING IN MEMORIA
# ==============================================================================
# Dizionario globale in RAM per memorizzare le sequenze già calcolate.
# Struttura -> CHIAVE: sequenza RNA pulita (str) | VALORE: tupla (avg_pooling, max_pooling)
# La tupla viene creata e memorizzata dopo il calcolo o la ricomposizione dei chunk.
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
    Carica il modello RNA-FM in memoria RAM solo quando viene invocato per la prima volta (Lazy Loading).
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
        
        # Imposta il modello in modalità valutazione (disattiva dropout e batch normalization)
        _MODEL.eval()
        
        # TASK 4: Stampa di conferma caricamento completato
        print("✅ Modello RNA-FM caricato e pronto all'uso su CPU!")


def _estrai_chunk_singolo(sub_sequenza: str):
    """
    Esegue l'inferenza PyTorch ed estrae i vettori di pooling per un singolo blocco/chunk (<= 1022 nt).
    
    TASK 1: Estrazione embeddings con RNA-FM su CPU.
    TASK 2: Calcolo Average e Max Pooling per il chunk.
    """
    # Formattazione del dato per il batch converter di RNA-FM: lista di tuple (id_etichetta, sequenza)
    data = [("rna_seq", sub_sequenza)]
    
    # Converte la sequenza di basi nei corrispettivi token numerici leggibili dal modello Transformer
    _, _, batch_tokens = _BATCH_CONVERTER(data)
    
    # Disabilita il calcolo dei gradienti PyTorch per risparmiare RAM e velocizzare l'inferenza su CPU
    with torch.no_grad():
        # Esegue il passaggio forward nel modello chiedendo di estrarre le rappresentazioni del layer 12
        results = _MODEL(batch_tokens, repr_layers=[12])
    
    # Estrae la matrice delle rappresentazioni dei token dal dodicesimo layer (layer 12)
    token_representations = results["representations"][12]
    
    # Rimuove i token speciali di inizio sequenza (<cls>) e fine sequenza (<eos>) prendendo solo gli elementi 1:-1
    seq_rep = token_representations[0, 1:-1]
    
    # TASK 2: Calcolo Average e Max Pooling del chunk
    avg_p = seq_rep.mean(dim=0).numpy()
    max_p = seq_rep.max(dim=0).values.numpy()
    
    return avg_p, max_p


# ==============================================================================
# FUNZIONE PRINCIPALE CON GESTIONE CHUNKING
# ==============================================================================
def calcola_o_recupera_embedding(sequenza: str, max_chunk_len: int = 800, overlap: int = 200):
    """
    Gestisce il flusso completo:
    1. Normalizza e sanitizza la sequenza di input.
    2. Controlla la presenza in Cache in RAM (Task 3).
    3. Gestisce le sequenze brevi (<= 1022 nt) con elaborazione diretta su CPU (Task 1 & 2).
    4. Gestisce le sequenze lunghe (> 1022 nt) applicando il Chunking (Sliding Window) e ricomponendo i vettori.
    5. Memorizza il risultato finale in Cache e stampa le notifiche di stato (Task 3 & 4).
    """
    # Normalizzazione difensiva: rimuove spazi, converte in maiuscolo e sostituisce le Timine (T) con Uracili (U)
    seq_pulita = sequenza.strip().upper().replace("T", "U")
    
    # --------------------------------------------------------------------------
    # TASK 3: CONTROLLO DELLA CACHE IN MEMORIA
    # --------------------------------------------------------------------------
    if seq_pulita in EMBEDDING_CACHE:
        # TASK 4: Stampa del messaggio di notifica (CACHE HIT)
        print(f"⚡ [CACHE HIT] Embedding già presente in memoria per la sequenza ({len(seq_pulita)} nt): {seq_pulita[:10]}...")
        # Restituisce immediatamente il risultato salvato senza richiamare il modello PyTorch
        return EMBEDDING_CACHE[seq_pulita]
    
    # Invocazione della funzione di Lazy Loading (carica il modello se _MODEL è None)
    _carica_modello_rna_fm()
    
    # --------------------------------------------------------------------------
    # SEQUENZE BREVI (<= 1022 nt): ELABORAZIONE DIRETTA
    # --------------------------------------------------------------------------
    if len(seq_pulita) <= 1022:
        avg_pooling, max_pooling = _estrai_chunk_singolo(seq_pulita)
    
    # --------------------------------------------------------------------------
    # SEQUENZE LUNGHE (> 1022 nt): STRATEGIA CHUNKING (SLIDING WINDOW)
    # --------------------------------------------------------------------------
    else:
        print(f"🔄 Sequenza lunga ({len(seq_pulita)} nt): applicazione Chunking (Sliding Window)...")
        avg_chunks = []
        max_chunks = []
        step = max_chunk_len - overlap
        
        # Generazione delle sotto-sequenze (chunk) sovrapposte
        for i in range(0, len(seq_pulita), step):
            chunk = seq_pulita[i : i + max_chunk_len]
            # Ignora residui troppo brevi alla fine della sequenza
            if len(chunk) < 10:
                continue
            
            # Estrazione dei vettori di pooling per il singolo chunk
            avg_p, max_p = _estrai_chunk_singolo(chunk)
            avg_chunks.append(avg_p)
            max_chunks.append(max_p)
        
        # TASK 2: Ricomposizione matematica dei vettori di tutti i chunk
        # Calcola la media globale dei vettori media e il massimo globale dei vettori max
        avg_pooling = np.mean(avg_chunks, axis=0)
        max_pooling = np.maximum.reduce(max_chunks)
    
    # --------------------------------------------------------------------------
    # TASK 3: SALVATAGGIO DEL RISULTATO IN CACHE
    # --------------------------------------------------------------------------
    coppia_embeddings = (avg_pooling, max_pooling)
    EMBEDDING_CACHE[seq_pulita] = coppia_embeddings
    
    # --------------------------------------------------------------------------
    # TASK 4: STAMPA DEL MESSAGGIO DI NOTIFICA
    # --------------------------------------------------------------------------
    print(f"🧠 [EMBEDDING CALCOLATO] Pooling completato per sequenza di {len(seq_pulita)} nt: {seq_pulita[:10]}...")
    
    # Restituisce la tupla contenente (array_average_pooling, array_max_pooling)
    return coppia_embeddings
