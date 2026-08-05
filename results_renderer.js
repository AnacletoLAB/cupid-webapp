/**
 * RESULTS RENDERER MODULE
 * Gestisce la tabella delle probabilità e l'iniezione dei grafici 2D nelle rispettive card.
 */

function renderizzaSVG(risultato, strumentoSelezionato) {
    if (strumentoSelezionato === "entrambi") {
        const label1 = document.getElementById("label-fold1");
        const label2 = document.getElementById("label-fold2");
        if (label1) label1.textContent = `1A. RNAfold (${risultato.id1})`;
        if (label2) label2.textContent = `1B. RNAfold (${risultato.id2})`;

        const mfeFold1Label = document.getElementById("mfe-fold1-label");
        const mfeFold2Label = document.getElementById("mfe-fold2-label");
        const mfeCofoldLabel = document.getElementById("mfe-cofold-label");
        
        if (mfeFold1Label) mfeFold1Label.textContent = `MFE: ${risultato.mfe_1} kcal/mol`;
        if (mfeFold2Label) mfeFold2Label.textContent = `MFE: ${risultato.mfe_2} kcal/mol`;
        if (mfeCofoldLabel) mfeCofoldLabel.textContent = `MFE: ${risultato.mfe_cofold} kcal/mol`;
        
        const boxFold1 = document.getElementById("rna-fold1-svg-box");
        const boxFold2 = document.getElementById("rna-fold2-svg-box");
        const boxCofold = document.getElementById("rna-cofold-svg-box");
        
        if (boxFold1) boxFold1.innerHTML = formaggiaSVG(risultato.svg_fold_1);
        if (boxFold2) boxFold2.innerHTML = formaggiaSVG(risultato.svg_fold_2);
        if (boxCofold) boxCofold.innerHTML = formaggiaSVG(risultato.svg_cofold);

    } else if (strumentoSelezionato === "RNAfold") {
        const label1 = document.getElementById("label-fold1");
        const label2 = document.getElementById("label-fold2");
        if (label1) label1.textContent = `RNAfold (${risultato.id1})`;
        if (label2) label2.textContent = `RNAfold (${risultato.id2})`;

        const mfeFold1Label = document.getElementById("mfe-fold1-label");
        const mfeFold2Label = document.getElementById("mfe-fold2-label");
        if (mfeFold1Label) mfeFold1Label.textContent = `MFE: ${risultato.mfe_1} kcal/mol`;
        if (mfeFold2Label) mfeFold2Label.textContent = `MFE: ${risultato.mfe_2} kcal/mol`;

        const boxFold1 = document.getElementById("rna-fold1-svg-box");
        const boxFold2 = document.getElementById("rna-fold2-svg-box");
        if (boxFold1) boxFold1.innerHTML = formaggiaSVG(risultato.svg_fold_1);
        if (boxFold2) boxFold2.innerHTML = formaggiaSVG(risultato.svg_fold_2);

    } else {
        const mfeSingleLabel = document.getElementById("mfe-single-label");
        if (mfeSingleLabel) mfeSingleLabel.textContent = `MFE: ${risultato.mfe} kcal/mol`;
        
        const boxSingle = document.getElementById("rna-single-svg-box");
        if (boxSingle) boxSingle.innerHTML = formaggiaSVG(risultato.svg_main);
    }

    ["fold1", "fold2", "cofold", "single"].forEach(prefisso => {
        const btnReset = document.getElementById(`btn-reset-${prefisso}`);
        if (btnReset) btnReset.click();
    });

    // Richiama l'Auto-Framing da svg_interactive.js
    applicaAutoFraming();
}

function mostraRisultati(risultati, strumentoSelezionato) {
    const tableBody = document.getElementById("results-table-body");
    const containerDiv = document.getElementById("visualization-container");
    const resultsSection = document.getElementById("results-section");

    tableBody.innerHTML = "";
    containerDiv.innerHTML = ""; 

    if (strumentoSelezionato === "entrambi") {
        containerDiv.className = "w-full space-y-8";
        containerDiv.innerHTML = 
            generaCardStruttura("fold1", "🎮 Navigazione Molecola 1", "1A. RNAfold (Molecola 1)") +
            generaCardStruttura("fold2", "🎮 Navigazione Molecola 2", "1B. RNAfold (Molecola 2)") +
            generaCardStruttura("cofold", "🎮 Navigazione RNAcofold", "2. RNAcofold (Interazione di Coppia)");

        inizializzaControlliVista("fold1", "rna-fold1-svg-box");
        inizializzaControlliVista("fold2", "rna-fold2-svg-box");
        inizializzaControlliVista("cofold", "rna-cofold-svg-box");

    } else if (strumentoSelezionato === "RNAfold") {
        containerDiv.className = "w-full space-y-8";
        containerDiv.innerHTML = 
            generaCardStruttura("fold1", "🎮 Navigazione Molecola 1", "RNAfold (Molecola 1)") +
            generaCardStruttura("fold2", "🎮 Navigazione Molecola 2", "RNAfold (Molecola 2)");

        inizializzaControlliVista("fold1", "rna-fold1-svg-box");
        inizializzaControlliVista("fold2", "rna-fold2-svg-box");

    } else {
        containerDiv.className = "w-full space-y-6";
        containerDiv.innerHTML = generaCardStruttura("single", "🎮 Navigazione 2D", "Struttura Secondaria Vettoriale");
        inizializzaControlliVista("single", "rna-single-svg-box");
    }

    risultati.forEach((risultato, index) => {
        const tr = document.createElement("tr");
        tr.className = "bg-white border-b hover:bg-gray-50 transition-colors";                      
        tr.innerHTML = `
            <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${risultato.id1}</td>
            <td class="px-6 py-4">${risultato.id2 || "-"}</td>
            <td class="px-6 py-4"><span class="px-2 py-1 bg-green-100 text-green-800 rounded-full font-semibold">${(risultato.probabilita * 100).toFixed(1)}%</span></td>
            <td class="px-6 py-4 font-mono">${risultato.mfe} kcal/mol</td>
            <td class="px-6 py-4 text-right">
                <button type="button" class="view-2d-btn px-4 py-2 bg-blue-100 text-blue-700 font-semibold rounded-lg hover:bg-blue-200 shadow-sm">Visualizza in 2D</button>
            </td>
        `;

        const btnVisualizza = tr.querySelector('.view-2d-btn');
        btnVisualizza.addEventListener("click", () => {
            Array.from(tableBody.children).forEach(row => row.classList.remove("bg-blue-50"));
            tr.classList.add("bg-blue-50");                                 
            renderizzaSVG(risultato, strumentoSelezionato);
        });

        tableBody.appendChild(tr);
        if (index === 0) {
            tr.classList.add("bg-blue-50");
            renderizzaSVG(risultato, strumentoSelezionato);
        }
    });

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}