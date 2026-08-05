"""
VIENNARNA COMPUTATION SERVICE
Esegue le analisi di folding termodinamico (RNAfold & RNAcofold) e coordina la creazione delle mappe 2D.
"""
import RNA
from varna_service import genera_svg_struttura

def analizza_struttura_vienna(seq1_str: str, seq2_str: str, strumento: str) -> dict:
    """
    Calcola le strutture secondarie e l'energia MFE, invocando VARNA per la resa grafica.
    """
    svg_fold_1 = None
    svg_fold_2 = None
    mfe_1 = None
    mfe_2 = None
    svg_cofold = None
    mfe_cofold = None
    svg_main = None
    struttura_secondaria = ""
    mfe = 0.0

    if strumento == "RNAcofold":
        len1 = len(seq1_str)
        seq_interazione = f"{seq1_str}&{seq2_str}"
        struttura_secondaria, mfe = RNA.cofold(seq_interazione)
        mfe = round(mfe, 2)
        
        svg_main = genera_svg_struttura(seq_interazione, struttura_secondaria, is_cofold=True, len_seq1=len1)
        svg_cofold = svg_main
        mfe_cofold = mfe
        
    elif strumento == "RNAfold":
        struct1, mfe1 = RNA.fold(seq1_str)
        struct2, mfe2 = RNA.fold(seq2_str)
        struttura_secondaria = f"{struct1} & {struct2}"
        mfe = round((mfe1 + mfe2), 2)
        
        mfe_1 = round(mfe1, 2)
        mfe_2 = round(mfe2, 2)
        
        svg_fold_1 = genera_svg_struttura(seq1_str, struct1, is_cofold=False, color_mode="blue")
        svg_fold_2 = genera_svg_struttura(seq2_str, struct2, is_cofold=False, color_mode="red")
        svg_main = svg_fold_1
        
    elif strumento == "entrambi":
        len1 = len(seq1_str)
        struct1, mfe1 = RNA.fold(seq1_str)
        struct2, mfe2 = RNA.fold(seq2_str)
        
        mfe_1 = round(mfe1, 2)
        mfe_2 = round(mfe2, 2)
        
        svg_fold_1 = genera_svg_struttura(seq1_str, struct1, is_cofold=False, color_mode="blue")
        svg_fold_2 = genera_svg_struttura(seq2_str, struct2, is_cofold=False, color_mode="red")
        
        seq_interazione = f"{seq1_str}&{seq2_str}"
        struttura_cofold, mfe_cofold = RNA.cofold(seq_interazione)
        mfe_cofold = round(mfe_cofold, 2)
        
        svg_cofold = genera_svg_struttura(seq_interazione, struttura_cofold, is_cofold=True, len_seq1=len1)
        svg_main = svg_cofold
        
        struttura_secondaria = struttura_cofold
        mfe = mfe_cofold

    return {
        "struttura": struttura_secondaria,
        "mfe": mfe,
        "svg_main": svg_main,
        "svg_fold_1": svg_fold_1,
        "svg_fold_2": svg_fold_2,
        "mfe_1": mfe_1,
        "mfe_2": mfe_2,
        "mfe_cofold": mfe_cofold,
        "svg_cofold": svg_cofold
    }
    