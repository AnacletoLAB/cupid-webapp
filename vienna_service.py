"""
VIENNARNA COMPUTATION SERVICE
Esegue le analisi di folding termodinamico (RNAfold & RNAcofold) e coordina la creazione delle mappe 2D.
"""
# Importa la libreria RNA (ViennaRNA) per il calcolo delle strutture secondarie
import RNA
# Importa la funzione per generare la rappresentazione SVG delle strutture
from varna_service import genera_svg_struttura

def analizza_struttura_vienna(seq1_str: str, seq2_str: str, strumento: str) -> dict:
    """
    Calcola le strutture secondarie e l'energia MFE, invocando VARNA per la resa grafica.
    """
    # Inizializza la variabile per memorizzare il file SVG della prima sequenza foldata
    svg_fold_1 = None
    svg_fold_2 = None
    # Inizializza la variabile per memorizzare l'energia MFE della prima sequenza
    mfe_1 = None
    mfe_2 = None
    # Inizializza la variabile per memorizzare il file SVG del cofold
    svg_cofold = None
    mfe_cofold = None
    # Inizializza la variabile per memorizzare il file SVG principale da visualizzare
    svg_main = None
    # Inizializza la variabile per memorizzare la struttura secondaria (notazione dot-bracket)
    struttura_secondaria = ""
    mfe = 0.0

    if strumento == "RNAcofold":
        # Calcola la lunghezza della prima sequenza per identificare i confini nell'interazione
        len1 = len(seq1_str)
        # Concatena le due sequenze con il separatore "&" per l'analisi di cofold
        seq_interazione = f"{seq1_str}&{seq2_str}" #la f-string permette di inserire le variabili direttamente nella stringa altrimenti si potrebbe usare la concatenazione con il + ma sarebbe meno leggibile
        # Esegue il calcolo di cofold (interazione tra sequenze) e ottiene struttura e energia MFE
        struttura_secondaria, mfe = RNA.cofold(seq_interazione)
        # Arrotonda l'energia MFE a 2 decimali per migliorare la leggibilità
        mfe = round(mfe, 2)
        
        # Genera il file SVG della struttura di interazione utilizzando VARNA
        svg_main = genera_svg_struttura(seq_interazione, struttura_secondaria, is_cofold=True, len_seq1=len1)
        # Assegna il grafico principale anche alla variabile svg_cofold per la traccia
        svg_cofold = svg_main
        # Assegna l'energia del cofold alla variabile mfe_cofold
        mfe_cofold = mfe
        
    elif strumento == "RNAfold":
        # Calcola la struttura secondaria e l'energia MFE della prima sequenza
        struct1, mfe1 = RNA.fold(seq1_str)
        struct2, mfe2 = RNA.fold(seq2_str)
        # Concatena le due strutture secondarie con il separatore "&" per visualizzazione
        struttura_secondaria = f"{struct1} & {struct2}" #struttura_secondaria non viene passato a RNA.cofold ma solo per la visualizzazione della struttura secondaria delle due sequenze separate
        # Calcola l'energia MFE totale sommando le energie delle due sequenze e poi arrotondando a 2 decimali per migliorare la leggibilità
        mfe = round((mfe1 + mfe2), 2)

        mfe_1 = round(mfe1, 2)
        mfe_2 = round(mfe2, 2)
        
        # Genera il file SVG della struttura della prima sequenza con colore blu
        svg_fold_1 = genera_svg_struttura(seq1_str, struct1, is_cofold=False, color_mode="blue")
        svg_fold_2 = genera_svg_struttura(seq2_str, struct2, is_cofold=False, color_mode="red")
        svg_main = svg_fold_1
        
    # Controlla se l'utente ha scelto di eseguire entrambe le analisi
    elif strumento == "entrambi":
        len1 = len(seq1_str)
        struct1, mfe1 = RNA.fold(seq1_str)
        struct2, mfe2 = RNA.fold(seq2_str)
        
        # Arrotonda l'energia MFE della prima sequenza a 2 decimali
        mfe_1 = round(mfe1, 2)
        # Arrotonda l'energia MFE della seconda sequenza a 2 decimali
        mfe_2 = round(mfe2, 2)
        
        # Genera il file SVG della struttura della prima sequenza con colore blu
        svg_fold_1 = genera_svg_struttura(seq1_str, struct1, is_cofold=False, color_mode="blue")
        # Genera il file SVG della struttura della seconda sequenza con colore rosso
        svg_fold_2 = genera_svg_struttura(seq2_str, struct2, is_cofold=False, color_mode="red")
        
        # Concatena le due sequenze con il separatore "&" per l'analisi di interazione
        seq_interazione = f"{seq1_str}&{seq2_str}"
        # Esegue il calcolo di cofold (interazione tra sequenze) e ottiene struttura e energia MFE
        struttura_cofold, mfe_cofold = RNA.cofold(seq_interazione)
        # Arrotonda l'energia MFE del cofold a 2 decimali
        mfe_cofold = round(mfe_cofold, 2)
        
        # Genera il file SVG della struttura di interazione utilizzando VARNA
        svg_cofold = genera_svg_struttura(seq_interazione, struttura_cofold, is_cofold=True, len_seq1=len1)
        # Assegna il grafico del cofold come principale poiché rappresenta l'interazione
        svg_main = svg_cofold
        
        # Memorizza la struttura del cofold come struttura secondaria principale
        struttura_secondaria = struttura_cofold
        # Memorizza l'energia del cofold come energia principale
        mfe = mfe_cofold

    # Ritorna un dizionario contenente tutti i risultati dell'analisi: in base allo strumento scelto, vengono restituiti i dati pertinenti e le rimanenti variabili rimangono None
    return {
        # La struttura secondaria calcolata in notazione dot-bracket
        "struttura": struttura_secondaria,
        # L'energia libera minima totale espressa in kcal/mol
        "mfe": mfe,
        # Il file SVG principale da visualizzare nell'interfaccia
        "svg_main": svg_main,
        # Il file SVG della struttura della prima sequenza (solo RNAfold)
        "svg_fold_1": svg_fold_1,
        # Il file SVG della struttura della seconda sequenza (solo RNAfold)
        "svg_fold_2": svg_fold_2,
        # L'energia MFE della prima sequenza (solo RNAfold)
        "mfe_1": mfe_1,
        # L'energia MFE della seconda sequenza (solo RNAfold)
        "mfe_2": mfe_2,
        # L'energia MFE del cofold (interazione tra sequenze)
        "mfe_cofold": mfe_cofold,
        # Il file SVG della struttura di cofold
        "svg_cofold": svg_cofold
    }
    