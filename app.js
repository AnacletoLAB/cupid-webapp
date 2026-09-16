/**
 * APP.JS - ORCHESTRATORE FRONTEND
 * Collega gli eventi della UI alle funzioni dei vari moduli.
 */
document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fasta-upload");
    const fileNameDisplay = document.getElementById("file-name-display");
    const startBtn = document.getElementById("start-analysis-btn");
    const aiModelSelect = document.getElementById("ai-model");
    const viennaToolSelect = document.getElementById("vienna-tool");
    let fileCaricato = null;

    fileInput.addEventListener("change", (e) => {
        fileCaricato = e.target.files[0];
        nascondiErrore(); 
        if (fileCaricato) {
            fileNameDisplay.innerHTML = `<span class="font-semibold text-green-600">File caricato:</span> ${fileCaricato.name}`;
        } else {
            fileNameDisplay.innerHTML = `<span class="font-semibold">Clicca per caricare</span> o trascina qui`;
        }
    });

    startBtn.addEventListener("click", async () => {
        if (!fileCaricato) {
            mostraErrore("Carica un file FASTA prima di avviare."); 
            return;
        }
        
        try {
            const testoFasta = await leggiFileTesto(fileCaricato);
            // Ora analizzaEValidaFasta restituisce un oggetto complesso
            const parsing = analizzaEValidaFasta(testoFasta);
            
            const errorMsg = document.getElementById("input-error");
            
            // Se trova delle T, mostra l'avviso a schermo (Arancione)
            if (parsing.warningTimine) {
                errorMsg.innerHTML = "⚠️ <b>Nota:</b> Hai inserito delle T nella sequenza, sono state convertite in U.";
                errorMsg.classList.remove("hidden", "text-red-500");
                errorMsg.classList.add("text-amber-600", "block");
            } else {
                errorMsg.classList.add("hidden");
            }
            
            const configurazioneAnalisi = {
                modelloAI: aiModelSelect.value,
                strumentoVienna: viennaToolSelect.value,
                sequenze: parsing.sequenze // Estraiamo l'array di sequenze pulite
            };

            startBtn.disabled = true;
            startBtn.textContent = "Elaborazione in corso...";
            
            await inviaAlBackend(configurazioneAnalisi);

        } catch (errore) {
            const errorMsg = document.getElementById("input-error");
            // Ripristina il colore rosso per i veri errori critici
            errorMsg.classList.remove("text-amber-600");
            errorMsg.classList.add("text-red-500");
            mostraErrore(errore.message);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = "Avvia Analisi";
        }
    });

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
            mostraRisultati(risultati, dati.strumentoVienna);
        } catch (errore) {
            throw new Error("Comunicazione fallita: " + errore.message);
        }
    }
});