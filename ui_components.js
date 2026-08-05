/**
 * UI COMPONENTS & TEMPLATES MODULE
 * Gestisce la generazione del markup HTML per le plance, le card e i messaggi di errore.
 */

function mostraErrore(messaggio) {
    const errorMsg = document.getElementById("input-error");
    if (errorMsg) {
        errorMsg.textContent = messaggio;
        errorMsg.classList.remove("hidden");
    }
}

function nascondiErrore() {
    const errorMsg = document.getElementById("input-error");
    if (errorMsg) {
        errorMsg.textContent = "";
        errorMsg.classList.add("hidden");
    }
}

function generaPlanciaHTML(prefisso, titolo = "🎮 Controlli Inquadratura") {
    return `
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 shadow-sm space-y-2 mb-3">
            <div class="flex justify-between items-center border-b pb-1.5">
                <span class="font-bold text-gray-700 text-xs flex items-center gap-1.5">${titolo}</span>
                <div class="flex gap-2">
                    <button type="button" id="btn-download-${prefisso}" class="px-2.5 py-1 bg-green-100 hover:bg-green-200 text-green-800 font-semibold rounded text-[11px] transition-colors shadow-sm border border-green-200">
                        ⬇️ Scarica SVG
                    </button>
                    <button type="button" id="btn-reset-${prefisso}" class="px-2.5 py-1 bg-red-100 hover:bg-red-200 text-red-700 font-semibold rounded text-[11px] transition-colors">
                        🔄 Resetta Vista
                    </button>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-semibold text-gray-600">
                <div class="space-y-1">
                    <div class="flex justify-between text-[11px]">
                        <span>🔍 Zoom:</span>
                        <span id="zoom-val-${prefisso}" class="font-mono text-blue-600">100%</span>
                    </div>
                    <input type="range" id="slider-zoom-${prefisso}" min="20" max="1500" value="100" class="w-full accent-blue-600 cursor-pointer">
                </div>
                <div class="space-y-1">
                    <div class="flex justify-between text-[11px]">
                        <span>↔️ Spostamento X:</span>
                        <span id="x-val-${prefisso}" class="font-mono text-blue-600">0 px</span>
                    </div>
                    <input type="range" id="slider-x-${prefisso}" min="-5000" max="5000" value="0" class="w-full accent-blue-600 cursor-pointer">
                </div>
                <div class="space-y-1">
                    <div class="flex justify-between text-[11px]">
                        <span>↕️ Spostamento Y:</span>
                        <span id="y-val-${prefisso}" class="font-mono text-blue-600">0 px</span>
                    </div>
                    <input type="range" id="slider-y-${prefisso}" min="-15000" max="15000" value="0" class="w-full accent-blue-600 cursor-pointer">
                </div>
            </div>
        </div>
    `;
}

function generaCardStruttura(prefisso, titoloNavigazione, titoloCard) {
    return `
        <div class="border border-gray-200 rounded-lg p-4 bg-white shadow-sm">
            <h4 class="font-semibold text-gray-700 border-b pb-2 mb-2 flex justify-between items-center">
                <span id="label-${prefisso}">${titoloCard}</span>
                <span id="mfe-${prefisso}-label" class="text-sm font-mono text-gray-500"></span>
            </h4>
            ${generaPlanciaHTML(prefisso, titoloNavigazione)}
            <div id="rna-${prefisso}-svg-box" class="w-full h-[550px] overflow-hidden bg-gray-50 rounded-lg relative flex justify-center items-center border border-gray-200 p-4"></div>
        </div>
    `;
}