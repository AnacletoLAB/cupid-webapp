/**
 * SVG INTERACTIVE & GRAPHICS UTILS MODULE
 * Gestisce la pulizia degli SVG, le trasformazioni 2D, il download del file e l'Auto-Framing.
 */

function formaggiaSVG(svgString) {
    if (!svgString) return "<p class='text-gray-400 font-semibold'>Nessuna immagine generata</p>";
    let pulito = svgString;

    pulito = pulito.replace(/width="[^"]*"/g, '');
    pulito = pulito.replace(/height="[^"]*"/g, '');
    pulito = pulito.replace(/viewBox="[^"]*"/g, ''); 
    
    pulito = pulito.replace(/<svg /, '<svg style="width: 100%; height: 100%; display: block; margin: auto;" ');
    return pulito;
}

function applicaAutoFraming() {
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            const contenitori = ["rna-fold1-svg-box", "rna-fold2-svg-box", "rna-cofold-svg-box", "rna-single-svg-box"];
            
            contenitori.forEach(boxId => {
                const box = document.getElementById(boxId);
                if (box) {
                    const svg = box.querySelector("svg");
                    if (svg) {
                        try {
                            const bbox = svg.getBBox();
                            const padding = 50; 
                            svg.setAttribute(
                                "viewBox", 
                                `${bbox.x - padding} ${bbox.y - padding} ${bbox.width + padding * 2} ${bbox.height + padding * 2}`
                            );
                        } catch (e) {
                            console.warn("Impossibile calcolare BBox per", boxId);
                        }
                    }
                }
            });
        });
    });
}

function inizializzaControlliVista(prefisso, boxId) {
    const sliderZoom = document.getElementById(`slider-zoom-${prefisso}`);
    const sliderX = document.getElementById(`slider-x-${prefisso}`);
    const sliderY = document.getElementById(`slider-y-${prefisso}`);
    const btnReset = document.getElementById(`btn-reset-${prefisso}`);
    const btnDownload = document.getElementById(`btn-download-${prefisso}`); 
    const labelZoom = document.getElementById(`zoom-val-${prefisso}`);
    const labelX = document.getElementById(`x-val-${prefisso}`);
    const labelY = document.getElementById(`y-val-${prefisso}`);

    const boxElem = document.getElementById(boxId);
    if (!boxElem || !sliderZoom || !sliderX || !sliderY) return;

    const applicaTrasformazione = () => {
        const z = sliderZoom.value;
        const x = sliderX.value;
        const y = sliderY.value;

        if (labelZoom) labelZoom.textContent = `${z}%`;
        if (labelX) labelX.textContent = `${x} px`;
        if (labelY) labelY.textContent = `${y} px`;

        const scale = z / 100;
        const svgs = boxElem.querySelectorAll("svg");
        svgs.forEach(svg => {
            svg.style.transform = `translate(${-x}px, ${y}px) scale(${scale})`;
            svg.style.transformOrigin = "center center";
            svg.style.transition = "transform 0.05s ease-out";
        });
    };

    sliderZoom.addEventListener("input", applicaTrasformazione);
    sliderX.addEventListener("input", applicaTrasformazione);
    sliderY.addEventListener("input", applicaTrasformazione);

    if (btnReset) {
        btnReset.addEventListener("click", () => {
            sliderZoom.value = 100;
            sliderX.value = 0;
            sliderY.value = 0;
            applicaTrasformazione();
        });
    }

    if (btnDownload) {
        btnDownload.addEventListener("click", () => {
            const svg = boxElem.querySelector("svg");
            if (!svg) {
                alert("Nessun grafico da scaricare in questo riquadro.");
                return;
            }

            const serializer = new XMLSerializer();
            let source = serializer.serializeToString(svg);

            if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            }
            if (!source.match(/^<svg[^>]+xmlns:xlink="http\:\/\/www\.w3\.org\/1999\/xlink"/)) {
                source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }

            const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `struttura_rna_${prefisso}.svg`;
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        });
    }
}