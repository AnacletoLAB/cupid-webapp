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
from prediction_service import predici_interazione # 🎯 NUOVO IMPORT

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

            # 🎯 3. PREDIZIONE INTERAZIONE (Rete Neurale Feed-Forward)
            # Sfruttiamo gli ID per il riconoscimento automatico (es. miRNA-lncRNA)
            predizione = predici_interazione(emb_seq1, emb_seq2, dati.modelloAI, seq1.id, seq2.id)

            risultati.append({
                "id1": seq1.id,
                "id2": seq2.id,
                "seq1_seq": seq1.sequenza,
                "seq2_seq": seq2.sequenza,
                # Convertiamo da % (es. 95.4) a decimale (es. 0.954) per il frontend
                "probabilita": round(predizione["probabilita_percentuale"] / 100.0, 4),
                "esito": predizione["esito"],
                **dati_vienna
            })

        return risultati

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore server: {str(e)}")

# --- 3. MONTA I FILE STATICI ---
app.mount("/", StaticFiles(directory=".", html=True), name="static")