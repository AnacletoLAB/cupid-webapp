"""
PREDICTION SERVICE MODULE
Gestisce l'inferenza della rete neurale (Feed-Forward) per classificare
l'interazione tra coppie di RNA utilizzando gli embedding estratti da RNA-FM.
"""
import os
import torch
import torch.nn as nn
import numpy as np
from fastapi import HTTPException

# ==============================================================================
# ARCHITETTURA DELLA RETE NEURALE
# ==============================================================================
class InteractionNN(nn.Module):
    """
    Rete Neurale Feed-Forward allineata esattamente alla struttura dei pesi 
    salvati nei file .pth forniti dal laboratorio.
    """
    def __init__(self, input_dim=2560):
        super(InteractionNN, self).__init__()
        
        # Struttura nascosta esatta richiesta dal dizionario dei pesi
        self.hidden_layers = nn.Sequential(
            nn.Linear(input_dim, 1024),  # index 0
            nn.ReLU(),                   # index 1
            nn.Dropout(0.2),             # index 2
            
            nn.Linear(1024, 1024),       # index 3
            nn.ReLU(),                   # index 4
            nn.Dropout(0.2),             # index 5
            
            nn.Linear(1024, 1024),       # index 6
            nn.ReLU(),                   # index 7
            nn.Dropout(0.2),             # index 8
            
            nn.Linear(1024, 1024),       # index 9
            nn.ReLU(),                   # index 10
            nn.Dropout(0.2)              # index 11
        )
        
        # Livello finale isolato come richiesto dai pesi
        self.output_layer = nn.Linear(1024, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.hidden_layers(x)
        x = self.output_layer(x)
        return self.sigmoid(x)


# ==============================================================================
# GESTIONE DEI PESI E LAZY LOADING
# ==============================================================================
_PREDICTION_MODELS_CACHE = {}

def _carica_modello(model_path: str, input_dim: int = 2560) -> nn.Module:
    """
    Carica i pesi .pth in memoria RAM (Lazy Loading) e imposta la rete in sola valutazione.
    """
    if model_path not in _PREDICTION_MODELS_CACHE:
        print(f"⏳ Caricamento dei pesi predittivi da {model_path}...")
        
        model = InteractionNN(input_dim=input_dim)
        
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            print("✅ Pesi neurali caricati con successo!")
        else:
            print(f"⚠️ ATTENZIONE: File pesi {model_path} non trovato. Verrà usata l'inizializzazione casuale per test.")
        
        model.eval()
        _PREDICTION_MODELS_CACHE[model_path] = model
        
    return _PREDICTION_MODELS_CACHE[model_path]


# ==============================================================================
# FUNZIONE PRINCIPALE
# ==============================================================================
def predici_interazione(emb_seq1: tuple, emb_seq2: tuple, modello_richiesto: str, id1: str, id2: str) -> dict:
    
    # 1. Fusione delle Features (Concatenazione Matematica)
    vettore_coppia = np.concatenate([emb_seq1[0], emb_seq1[1], emb_seq2[0], emb_seq2[1]]) 
    
    # 2. Conversione per PyTorch
    tensor_input = torch.tensor(vettore_coppia, dtype=torch.float32).unsqueeze(0)
    
    path_pesi = "pesi/default.pth"
    
    # RICONOSCIMENTO AUTOMATICO SE mirInter-Trans
    if modello_richiesto == "mirInter-Trans":
        str_coppia = f"{id1.lower()} {id2.lower()}"
        
        if "mirna" in str_coppia and "lncrna" in str_coppia:
            path_pesi = "pesi/mirnalncrna.pth"
        elif "mirna" in str_coppia and "snorna" in str_coppia:
            path_pesi = "pesi/mirnasnorna.pth"
        elif str_coppia.count("mirna") >= 2:
            path_pesi = "pesi/mirnamirna.pth"
        else:
            messaggio = (
                f"Combinazione non supportata da mirInter-Trans per le sequenze '{id1}' e '{id2}'. "
                f"Assicurati di includere nell'ID il tipo di ncRNA supportato (mirna, lncrna o snorna)."
            )
            print(f"⚠️ {messaggio}")
            raise HTTPException(status_code=400, detail=messaggio)
            
    elif modello_richiesto == "CUPID":
        messaggio_cupid = "Il modello predittivo CUPID non è ancora disponibile per l'inferenza (pesi non integrati)."
        print(f"⚠️ {messaggio_cupid}")
        raise HTTPException(status_code=400, detail=messaggio_cupid)

    else:
        raise HTTPException(status_code=400, detail=f"Modello '{modello_richiesto}' non riconosciuto.")

    # 3. Caricamento rapido (Lazy/Cache)
    rete_neurale = _carica_modello(path_pesi, input_dim=2560)
    
    # 4. Inferenza Veloce CPU (Autograd Disattivato)
    with torch.no_grad():
        prob_tensor = rete_neurale(tensor_input) #💎CORE OUTPUT💎
        prob_grezza = prob_tensor.item()
        
    # 5. Valutazione e Soglia Ottimale
    soglia_ottimale = 0.5 
    esito = "Interagisce" if prob_grezza >= soglia_ottimale else "Non Interagisce"
    
    return {
        "probabilita_percentuale": round(prob_grezza * 100, 2),
        "esito": esito,
        "soglia_applicata": soglia_ottimale
    }