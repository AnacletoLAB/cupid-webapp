import itertools
import RNA  # La libreria C/C++ di ViennaRNA, importata in modo nativo!
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="ncRNA Interaction Analyzer API")

# --- 1. CONFIGURAZIONE CORS ---
# Permette al file index.html locale di fare richieste a questo server senza essere bloccato
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. MODELLI PYDANTIC ---
# Mappano esattamente la struttura del JSON che abbiamo preparato in app.js
class SequenzaInput(BaseModel):
    id: str
    sequenza: str

class RichiestaAnalisi(BaseModel):
    modelloAI: str
    strumentoVienna: str
    sequenze: List[SequenzaInput]

# --- 3. ENDPOINT PRINCIPALE ---
@app.post("/api/analizza")
async def analizza_sequenze(dati: RichiestaAnalisi):
    try:
        sequenze = dati.sequenze
        
        # Validazione di base
        if len(sequenze) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Sono necessarie almeno 2 sequenze per calcolare le interazioni."
            )
        
        # Generazione del Prodotto Cartesiano: crea tutte le combinazioni possibili a coppie (es. A-B, A-C, B-C)
        coppie = list(itertools.combinations(sequenze, 2))
        
        risultati = []
        
        # --- 4. CICLO DI ELABORAZIONE ---
        for seq1, seq2 in coppie:
            struttura_secondaria = ""
            mfe = 0.0
            
            # --- INTEGRAZIONE VIENNARNA ---
            if dati.strumentoVienna == "RNAcofold":
                # RNAcofold calcola come due molecole si legano tra loro. 
                # Richiede la concatenazione delle sequenze con il carattere "&"
                seq_interazione = f"{seq1.sequenza}&{seq2.sequenza}"
                struttura_secondaria, mfe = RNA.cofold(seq_interazione)
                
            elif dati.strumentoVienna == "RNAfold":
                # RNAfold calcola il ripiegamento di una singola molecola.
                # Essendo un prodotto cartesiano tra due molecole, calcoliamo la stabilità di entrambe
                struct1, mfe1 = RNA.fold(seq1.sequenza)
                struct2, mfe2 = RNA.fold(seq2.sequenza)
                
                # Uniamo i risultati per la visualizzazione
                struttura_secondaria = f"{struct1} & {struct2}"
                mfe = round((mfe1 + mfe2), 2)

            # --- MOCKUP MODELLI AI (mirInter-Trans / CUPID) ---
            # Per ora assegniamo una probabilità di interazione fittizia (99.9%).
            # Qui in futuro chiameremo i veri modelli AI che caricherai sulla GPU.
            probabilita_interazione = 0.999 

            # Aggiungiamo il risultato elaborato alla lista da rispedire al frontend
            risultati.append({
                "id1": seq1.id,
                "id2": seq2.id,
                "seq1_seq": seq1.sequenza,  # AGGIUNTO: Necessario a Fornac per le etichette
                "seq2_seq": seq2.sequenza,  # AGGIUNTO: Necessario a Fornac per le etichette
                "probabilita": probabilita_interazione,
                "mfe": mfe,
                "struttura": struttura_secondaria  # Fondamentale per la libreria JS "forna"
            })
            
        return risultati

    except Exception as e:
        # Cattura qualsiasi errore imprevisto ed evita che il server crashi
        raise HTTPException(status_code=500, detail=f"Errore di elaborazione backend: {str(e)}")

# Endpoint di test rapido per verificare se il server è acceso
@app.get("/")
def read_root():
    return {"status": "successo", "messaggio": "Server FastAPI per Bioinformatica Operativo!"}