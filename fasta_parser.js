/**
 * FASTA PARSER & VALIDATOR MODULE
 * Gestisce la lettura dei file e i controlli di sicurezza client-side.
 */

function leggiFileTesto(file) {
    return new Promise((resolve, reject) => {
        const lettore = new FileReader();
        lettore.onload = (e) => resolve(e.target.result);
        lettore.onerror = () => reject(new Error("Errore durante la lettura del file FASTA."));
        lettore.readAsText(file);
    });
}

function analizzaEValidaFasta(testo) {
    const righe = testo.split(/\r?\n/);
    let sequenzeFinali = [];
    let idsRilevati = new Set();
    let idCorrente = null;
    let sequenzaCorrente = "";
    
    let trovateTimine = false; // Flag per il warning

    const processaSequenza = (id, seq) => {
        if (!id) return;
        if (idsRilevati.has(id)) throw new Error(`ID duplicato rilevato: "${id}"`);
        idsRilevati.add(id);
        
        let seqUpper = seq.toUpperCase().trim();
        
        // 1. Controlla se ci sono T per attivare il warning
        if (seqUpper.includes("T")) {
            trovateTimine = true;
        }
        
        // 2. Converte subito in U per proteggere il backend
        let seqPulita = seqUpper.replace(/T/g, "U");
        
        if (!seqPulita) throw new Error(`Sequenza vuota per l'ID "${id}"`);
        
        // 3. Valida la sequenza ripulita (ora deve avere solo AUCG)
        const regexSoloRNA = /^[AUCG]+$/;
        if (!regexSoloRNA.test(seqPulita)) throw new Error(`Caratteri non validi nella sequenza ID "${id}". Usa solo A, U, C, G.`);
        
        sequenzeFinali.push({ id: id, sequenza: seqPulita });
    };

    for (let riga of righe) {
        riga = riga.trim();
        if (!riga) continue;
        if (riga.startsWith(">")) {
            processaSequenza(idCorrente, sequenzaCorrente);
            idCorrente = riga.substring(1).trim();
            sequenzaCorrente = "";
        } else {
            sequenzaCorrente += riga;
        }
    }
    
    processaSequenza(idCorrente, sequenzaCorrente);
    if (sequenzeFinali.length === 0) throw new Error("Nessuna sequenza FASTA valida trovata nel file.");
    
    // Ritorna sia i dati che il flag del warning
    return {
        sequenze: sequenzeFinali,
        warningTimine: trovateTimine
    };
}