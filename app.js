/**
 * APP.JS - ORCHESTRATORE FRONTEND
 * Collega gli eventi della UI alle funzioni dei vari moduli.
 */
document.addEventListener("DOMContentLoaded", () => {
    // 1. Recupero degli elementi dal DOM
    const fileInput = document.getElementById("fasta-upload");
    const fileNameDisplay = document.getElementById("file-name-display"); 
    const startBtn = document.getElementById("start-analysis-btn");
    const aiModelSelect = document.getElementById("ai-model");
    const viennaToolSelect = document.getElementById("vienna-tool");

    let fileCaricato = null;

    // 2. Evento: Selezione del file
    fileInput.addEventListener("change", (e) => {
        fileCaricato = e.target.files[0];
        nascondiErrore(); // Funzione importata da ui_components.js
        if (fileCaricato) {
            fileNameDisplay.innerHTML = `<span class="font-semibold text-green-600">File caricato:</span> ${fileCaricato.name}`;
        } else {
            fileNameDisplay.innerHTML = `<span class="font-semibold">Clicca per caricare</span> o trascina qui`;
        }
    });

    // 3. Evento: Click sul bottone "Avvia Analisi"
    startBtn.addEventListener("click", async () => {
        if (!fileCaricato) {
            mostraErrore("Carica un file FASTA prima di avviare."); // Funzione importata da ui_components.js
            return;
        }

        try {
            // A. Lettura e validazione (Funzioni da fasta_parser.js)
            const testoFasta = await leggiFileTesto(fileCaricato);
            const sequenzeValidato = analizzaEValidaFasta(testoFasta);
            
            const configurazioneAnalisi = {
                modelloAI: aiModelSelect.value,
                strumentoVienna: viennaToolSelect.value,
                sequenze: sequenzeValidato
            };

            // B. Blocco dell'interfaccia durante il caricamento
            startBtn.disabled = true;
            startBtn.textContent = "Elaborazione in corso...";
            
            // C. Chiamata al Server Python
            await inviaAlBackend(configurazioneAnalisi);

        } catch (errore) {
            mostraErrore(errore.message);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = "Avvia Analisi";
        }
    });

    // 4. Funzione di comunicazione con le API FastAPI
    async function inviaAlBackend(dati) {
        const urlAPI = "/api/analizza";
        try {
            const risposta = await fetch(urlAPI, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dati)
            });

            if (!risposta.ok) {
                let msg = "Errore server.";
                try { const info = await risposta.json(); msg = info.detail || msg; } catch (e) {}
                throw new Error(msg);
            }

            const risultati = await risposta.json();
            
            // D. Avvio del motore di rendering grafico (Funzione da results_renderer.js)
            mostraRisultati(risultati, dati.strumentoVienna);
            
        } catch (errore) {
            throw new Error("Comunicazione fallita: " + errore.message);
        }
    }
});