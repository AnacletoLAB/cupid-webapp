"""
MAIN FASTAPI APP ORCHESTRATOR
Inizializza il server web, gestisce le rotte HTTP e coordina i moduli di servizio.
"""
import itertools
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models import RichiestaAnalisi
from embedding_manager import calcola_o_recupera_embedding
from vienna_service import analizza_struttura_vienna

app = FastAPI(title="ncRNA Interaction Analyzer API")

# --- 1. CONFIGURAZIONE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. ENDPOINT PRINCIPALE ---
@app.post("/api/analizza")
async def analizza_sequenze(dati: RichiestaAnalisi):
    try:
        sequenze = dati.sequenze
        if len(sequenze) < 2:
            raise HTTPException(status_code=400, detail="Servono almeno 2 sequenze per l'analisi.")
        
        coppie = list(itertools.combinations(sequenze, 2))
        risultati = []
        
        for seq1, seq2 in coppie:
            # 🧠 1. EMBEDDINGS (RNA-FM + Cache)
            emb_seq1 = calcola_o_recupera_embedding(seq1.sequenza)
            emb_seq2 = calcola_o_recupera_embedding(seq2.sequenza)

            # 🧬 2. ANALISI STRUTTURALE & VISUALIZZAZIONE 2D (ViennaRNA + VARNA)
            dati_vienna = analizza_struttura_vienna(seq1.sequenza, seq2.sequenza, dati.strumentoVienna)

            # TODO: Inserire qui il passaggio dei vettori emb_seq1 e emb_seq2 ai modelli predittivi
            probabilita_calcolata = 0.999 

            risultati.append({
                "id1": seq1.id,
                "id2": seq2.id,
                "seq1_seq": seq1.sequenza,
                "seq2_seq": seq2.sequenza,
                "probabilita": probabilita_calcolata,
                **dati_vienna
            })

        return risultati

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore server: {str(e)}")

# --- 3. MONTA I FILE STATICI ---
app.mount("/", StaticFiles(directory=".", html=True), name="static")