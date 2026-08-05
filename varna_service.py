"""
VARNA RENDERING SERVICE
Gestisce l'esecuzione di VARNAcmd per il rendering 2D e la sanificazione dell'XML SVG.
"""
import os
import re
import tempfile
import subprocess

def genera_svg_struttura(sequenza: str, struttura: str, is_cofold: bool = False, len_seq1: int = 0, color_mode: str = "blue") -> str:
    """
    Genera l'immagine SVG vettoriale usando l'eseguibile Java VARNA.
    Applica gli stili categorici per evitare la comparsa di legende o glitch cromatici.
    """
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp_path = tmp.name

        varna_jar = os.path.abspath("VARNA.jar")
        
        if not os.path.exists(varna_jar):
            raise Exception("File VARNA.jar non trovato nella directory principale.")

        cmd = [
            "java",
            "-cp", varna_jar,
            "fr.orsay.lri.varna.applications.VARNAcmd",
            "-sequenceDBN", sequenza,
            "-structureDBN", struttura,
            "-algorithm", "naview", 
            "-o", tmp_path
        ]

        if is_cofold:
            len_stringa_totale = len(sequenza)
            cmd.extend([
                "-basesStyle1", "fill=#2563eb",                 # Stile 1: Blu
                "-applyBasesStyle1on", f"1-{len_seq1}",         # Assegnalo alla Seq1
                "-basesStyle2", "fill=#dc2626",                 # Stile 2: Rosso
                "-applyBasesStyle2on", f"{len_seq1 + 2}-{len_stringa_totale}" # Assegnalo alla Seq2
            ])
        else:
            len_stringa_totale = len(sequenza)
            fill_color = "#dc2626" if color_mode == "red" else "#2563eb"
            cmd.extend([
                "-basesStyle1", f"fill={fill_color}",
                "-applyBasesStyle1on", f"1-{len_stringa_totale}"
            ])

        processo = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if processo.returncode != 0:
            raise Exception(f"Errore interno VARNA: {processo.stderr}")

        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            with open(tmp_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content)
            svg_content = re.sub(r'<!DOCTYPE[^>]*>', '', svg_content)
            
            return svg_content.strip()
        else:
            raise Exception("Immagine SVG non generata (file vuoto).")

    except Exception as e:
        print(f"Errore generazione SVG: {e}")
        return f'<svg viewBox="0 0 500 100" class="w-full"><text x="50" y="50" fill="red">Errore generazione grafico: {str(e)}</text></svg>'
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass