document.addEventListener("DOMContentLoaded", () => {
    // --- ELEMENTI DEL DOM ---
    const fileInput = document.getElementById("fasta-upload");
    const fileNameDisplay = document.getElementById("file-name-display"); 
    const startBtn = document.getElementById("start-analysis-btn");
    const errorMsg = document.getElementById("input-error");
    const resultsSection = document.getElementById("results-section");
    const tableBody = document.getElementById("results-table-body");
    const aiModelSelect = document.getElementById("ai-model");
    const viennaToolSelect = document.getElementById("vienna-tool");

    let fileCaricato = null;

    // --- EVENT LISTENERS ---
    fileInput.addEventListener("change", (e) => {
        fileCaricato = e.target.files[0];
        nascondiErrore();
        
        // Aggiornamento grafico per dare feedback immediato all'utente
        if (fileCaricato) {
            fileNameDisplay.innerHTML = `
                <span class="font-semibold text-green-600">File caricato con successo:</span> 
                <br> <span class="text-gray-700">${fileCaricato.name}</span>
            `;
        } else {
            // Se l'utente clicca su "Annulla" nel menu a tendina del file picker, resettiamo il messaggio
            fileNameDisplay.innerHTML = `
                <span class="font-semibold">Clicca per caricare</span> o trascina il file qui
            `;
        }
    });

    startBtn.addEventListener("click", async () => {
        if (!fileCaricato) {
            mostraErrore("Per favore, carica un file FASTA prima di avviare l'analisi.");
            return;
        }

        try {
            // 1. Legge il file e ne estrae il testo
            const testoFasta = await leggiFileTesto(fileCaricato);
            
            // 2. Esegue il parsing e tutti i controlli (regex, univocità, uppercase, split a 7 nt)
            const sequenzeValidato = analizzaEValidaFasta(testoFasta);
            
            // 3. Prepara il payload da inviare al backend
            const configurazioneAnalisi = {
                modelloAI: aiModelSelect.value,
                strumentoVienna: viennaToolSelect.value,
                sequenze: sequenzeValidato
            };

            console.log("Dati in invio al backend:", configurazioneAnalisi);
            
            // 4. Invia i dati al backend reale tramite fetch()
            startBtn.disabled = true;
            startBtn.textContent = "Elaborazione in corso sul server...";
            
            await inviaAlBackend(configurazioneAnalisi);

        } catch (errore) {
            mostraErrore(errore.message);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = "Avvia Analisi";
        }
    });

    // --- FUNZIONI DI SUPPORTO ---
    function leggiFileTesto(file) {
        return new Promise((resolve, reject) => {
            const lettore = new FileReader();
            lettore.onload = (e) => resolve(e.target.result);
            lettore.onerror = () => reject(new Error("Errore durante la lettura del file."));
            lettore.readAsText(file);
        });
    }

    function analizzaEValidaFasta(testo) {
        const righe = testo.split(/\r?\n/);
        let sequenzeFinali = [];
        let idsRilevati = new Set();
        
        let idCorrente = null;
        let sequenzaCorrente = "";
        
        // Regex per bloccare caratteri estranei (solo A, U, C, G)
        const regexRNA = /^[AUCG]+$/;

        const processaSequenza = (id, seq) => {
            if (!id) return;

            // Controllo che ogni sequenza abbia un ID diverso tra loro
            if (idsRilevati.has(id)) {
                throw new Error(`Errore: L'ID "${id}" è duplicato. Ogni sequenza deve avere un ID univoco.`);
            }
            idsRilevati.add(id);

            // Trasforma tutto in maiuscolo e rimuove spazi 
            let seqPulita = seq.toUpperCase().trim();
            
            // Converte eventuali 'T' del DNA in 'U' per l'RNA
            seqPulita = seqPulita.replace(/T/g, "U");

            if (!seqPulita) {
                throw new Error(`Errore: La sequenza per l'ID "${id}" è vuota.`);
            }

            // Validazione con Espressione Regolare (solo 4 nucleotidi standard)
            if (!regexRNA.test(seqPulita)) {
                throw new Error(`Errore nell'ID "${id}": Trovati caratteri non validi. Sono permessi solo A, U, C, G.`);
            }

            // TRADE-OFF: Input di 7 nucleotidi max. Taglio e associo nuovo ID.
            const MAX_NUCLEOTIDI = 7;
            if (seqPulita.length > MAX_NUCLEOTIDI) {
                let indiceParte = 1;
                for (let i = 0; i < seqPulita.length; i += MAX_NUCLEOTIDI) {
                    const blocco = seqPulita.substring(i, i + MAX_NUCLEOTIDI);
                    sequenzeFinali.push({
                        id: `${id}_part${indiceParte}`,
                        sequenza: blocco
                    });
                    indiceParte++;
                }
            } else {
                sequenzeFinali.push({ id: id, sequenza: seqPulita });
            }
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
        
        // Processa l'ultima sequenza rimasta nel buffer
        processaSequenza(idCorrente, sequenzaCorrente);

        if (sequenzeFinali.length === 0) {
            throw new Error("Nessuna sequenza FASTA valida trovata nel file.");
        }

        return sequenzeFinali;
    }

    async function inviaAlBackend(dati) {
        // L'URL del tuo endpoint FastAPI 
        const urlAPI = "http://127.0.0.1:8000/api/analizza";
        
        try {
            // Chiamata reale al server backend
            const risposta = await fetch(urlAPI, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dati)
            });

            if (!risposta.ok) {
                let messaggioErrore = "Errore di elaborazione sul server.";
                try {
                    const infoErrore = await risposta.json();
                    messaggioErrore = infoErrore.detail || messaggioErrore;
                } catch (e) {
                    messaggioErrore = `Errore HTTP: ${risposta.status}`;
                }
                throw new Error(messaggioErrore);
            }

            const risultati = await risposta.json();
            
            // Popolamento della tabella e inizializzazione grafica
            mostraRisultati(risultati);

        } catch (errore) {
            if (errore.message === "Failed to fetch") {
                throw new Error("Impossibile connettersi al server. Assicurati che FastAPI sia in esecuzione su " + urlAPI);
            }
            throw new Error("Comunicazione col server fallita: " + errore.message);
        }
    }

    function mostraRisultati(risultati) {
        tableBody.innerHTML = "";
        
        // 1. Prepara il div container svuotando i testi precedenti
        const containerDiv = document.getElementById("forna-container");
        containerDiv.innerHTML = ""; 

        // Crea il div target dove forna disegnerà la struttura
        const rnaRenderDiv = document.createElement("div");
        rnaRenderDiv.id = "rna-structure-plot";
        rnaRenderDiv.style.width = "100%";
        rnaRenderDiv.style.height = "100%";
        containerDiv.appendChild(rnaRenderDiv);

        // Definiamo la variabile e le opzioni prima del controllo
        let fornaContainer;
        const opzioniForna = {
            animation: true,
            zoomable: true,
            initialSize: [containerDiv.clientWidth || 700, containerDiv.clientHeight || 350]
        };

        // 2. Inizializza l'oggetto FornaContainer
        // Controlliamo in che modo la libreria è stata esposta a livello globale
        if (typeof fornac !== "undefined" && typeof fornac.FornaContainer !== "undefined") {
            fornaContainer = new fornac.FornaContainer("#rna-structure-plot", opzioniForna);
        } else if (typeof FornaContainer !== "undefined") {
            fornaContainer = new FornaContainer("#rna-structure-plot", opzioniForna);
        } else {
            throw new Error("Impossibile avviare Fornac: la libreria grafica non è stata caricata. Controlla i link CDN.");
        }

        // 3. Itera sui risultati e popola la tabella
        risultati.forEach((risultato, index) => {
            const tr = document.createElement("tr");
            tr.className = "bg-white border-b hover:bg-gray-50 transition-colors"; // Tolto cursor-pointer dalla riga                         
            tr.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${risultato.id1}</td>
                <td class="px-6 py-4">${risultato.id2 || "-"}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 bg-green-100 text-green-800 rounded-full font-semibold">
                        ${(risultato.probabilita * 100).toFixed(1)}%
                    </span>
                </td>
                <td class="px-6 py-4 font-mono">${risultato.mfe} kcal/mol</td>
                <td class="px-6 py-4 text-right">
                    <!-- NUOVO BOTTONE -->
                    <button type="button" class="view-2d-btn px-4 py-2 bg-blue-100 text-blue-700 font-semibold rounded-lg hover:bg-blue-200 hover:scale-105 transition-all shadow-sm">
                        Visualizza in 2D
                    </button>
                </td>
            `;

            // Rende interattivo SOLO il bottone, non l'intera riga
            const btnVisualizza = tr.querySelector('.view-2d-btn');
            
            btnVisualizza.addEventListener("click", () => {
                // Rimuove l'evidenziazione dalle altre righe
                Array.from(tableBody.children).forEach(row => row.classList.remove("bg-blue-50"));
                tr.classList.add("bg-blue-50");                                 
                renderizzaStrutturaRNA(fornaContainer, risultato);
            });

            tableBody.appendChild(tr);

            // Renderizza automaticamente il primo risultato della lista all'avvio
            if (index === 0) {
                tr.classList.add("bg-blue-50");
                renderizzaStrutturaRNA(fornaContainer, risultato);
            }
        });

        resultsSection.classList.remove("hidden");
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // 4. Funzione helper per l'aggiornamento di forna
    function renderizzaStrutturaRNA(container, risultato) {
        // Svuota il grafico precedente
        container.clearNodes();
        
        // Verifichiamo se la struttura generata dal backend contiene la "&" (segno di output cofolded/unito)
        const isCofold = risultato.struttura.includes("&");

        if (isCofold) {
            // Controlliamo in quale modalità siamo basandoci sull'input dell'utente
            const strumentoSelezionato = viennaToolSelect.value;
            
            if (strumentoSelezionato === "RNAcofold") {
                // Caso 1: È una vera interazione cofold.
                // Usiamo il separatore per sequenza e struttura
                const sequenzaCombinata = `${risultato.seq1_seq}&${risultato.seq2_seq}`;
                container.addRNA(risultato.struttura, { sequence: sequenzaCombinata });
                
            } else {
                // Caso 2: È il nostro output finto di RNAfold (struct1 & struct2).
                // Dividiamo le strutture e le sequenze e le disegniamo come molecole INDIPENDENTI
                const struttureSeparate = risultato.struttura.split("&");
                
                // Disegna la prima sequenza da sola
                if (struttureSeparate[0] && risultato.seq1_seq) {
                    container.addRNA(struttureSeparate[0].trim(), { sequence: risultato.seq1_seq });
                }
                // Disegna la seconda sequenza da sola (apparirà accanto alla prima)
                if (struttureSeparate[1] && risultato.seq2_seq) {
                    container.addRNA(struttureSeparate[1].trim(), { sequence: risultato.seq2_seq });
                }
            }
        } else {
            // Fallback generico per sicurezza: disegna solo la prima sequenza
            container.addRNA(risultato.struttura, { sequence: risultato.seq1_seq });
        }
    }

    function mostraErrore(messaggio) {
        errorMsg.textContent = messaggio;
        errorMsg.classList.remove("hidden");
    }

    function nascondiErrore() {
        errorMsg.textContent = "";
        errorMsg.classList.add("hidden");
    }
});