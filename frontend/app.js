// API Configuration
const API_URL = window.location.pathname.startsWith('/app')
    ? ''  // Same origin when served from /app
    : window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://metodo-api-production.up.railway.app';

// State
let currentStep = 1;
let currentAnalysis = {
    joke: { text: '', comic: '', show: '', year: '' },
    premisa: { concepto: '', diseccion: [], elementoMecanico: '', estructura: '', tags: [] },
    ruptura: { tecnica: '', caracteristica: '', tags: [] },
    remate: { tecnica: '', situaciones: [], tags: [] }
};

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initTechniqueSelectors();
    initDynamicLists();
    initSteps();
    initSaveButton();
    loadEntries();
});

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-view]');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const viewId = item.dataset.view;

            // Update nav
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            // Update view
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            const view = document.getElementById(`view-${viewId}`);
            if (view) view.classList.add('active');

            // Update header
            const titles = {
                'analyze': 'Nuevo Análisis',
                'entries': 'Mis Análisis',
                'write': 'Escribir Chiste',
                'tags': 'Catálogo de Etiquetas',
                'techniques': 'Técnicas',
                'comics': 'Cómicos'
            };
            document.querySelector('.header-title').textContent = titles[viewId] || viewId;

            // Toggle catalog panel
            const catalog = document.getElementById('catalogPanel');
            catalog.style.display = viewId === 'analyze' ? 'block' : 'none';
        });
    });
}

// Technique Selectors
function initTechniqueSelectors() {
    document.querySelectorAll('.technique-selector').forEach(selector => {
        const options = selector.querySelectorAll('.technique-option');
        const hiddenInput = selector.nextElementSibling;

        options.forEach(option => {
            option.addEventListener('click', () => {
                options.forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                if (hiddenInput && hiddenInput.type === 'hidden') {
                    hiddenInput.value = option.dataset.value;
                }
            });
        });
    });
}

// Dynamic Lists (Disección & Situaciones)
function initDynamicLists() {
    // Add disección
    document.getElementById('addDiseccion')?.addEventListener('click', () => {
        const container = document.getElementById('diseccionItems');
        const newItem = document.createElement('div');
        newItem.className = 'diseccion-item';
        newItem.innerHTML = `
            <input type="text" class="input input-sm" placeholder="Característica">
            <input type="text" class="input" placeholder="Valor">
            <button class="btn-icon btn-remove">×</button>
        `;
        container.appendChild(newItem);
        initRemoveButtons(newItem);
    });

    // Add situation
    document.getElementById('addSituation')?.addEventListener('click', () => {
        const container = document.getElementById('situationsList');
        const count = container.querySelectorAll('.situation-item').length + 1;
        const newItem = document.createElement('div');
        newItem.className = 'situation-item';
        newItem.innerHTML = `
            <span class="situation-num">${count}</span>
            <input type="text" class="input" placeholder="Situación ${count}...">
            <button class="btn-icon btn-remove">×</button>
        `;
        container.appendChild(newItem);
        initRemoveButtons(newItem);
    });

    // Init existing remove buttons
    document.querySelectorAll('.btn-remove').forEach(btn => {
        initRemoveButtons(btn.parentElement);
    });
}

function initRemoveButtons(container) {
    container.querySelector('.btn-remove')?.addEventListener('click', () => {
        container.remove();
        // Renumber situations
        document.querySelectorAll('.situation-item').forEach((item, index) => {
            const num = item.querySelector('.situation-num');
            if (num) num.textContent = index + 1;
        });
    });
}

// Steps Navigation
function initSteps() {
    document.getElementById('btnNext')?.addEventListener('click', () => {
        if (currentStep < 4) {
            updateStep(currentStep + 1);
        }
    });

    document.getElementById('btnPrev')?.addEventListener('click', () => {
        if (currentStep > 1) {
            updateStep(currentStep - 1);
        }
    });
}

function updateStep(newStep) {
    const steps = document.querySelectorAll('.step');

    steps.forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.remove('active', 'completed');

        if (stepNum < newStep) {
            step.classList.add('completed');
            step.querySelector('.step-num').textContent = '✓';
        } else if (stepNum === newStep) {
            step.classList.add('active');
            step.querySelector('.step-num').textContent = stepNum;
        } else {
            step.querySelector('.step-num').textContent = stepNum;
        }
    });

    // Scroll to relevant card
    const cardIds = ['card-joke', 'card-premisa', 'card-ruptura', 'card-remate'];
    const targetCard = document.getElementById(cardIds[newStep - 1]);
    if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Update buttons
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');

    if (btnPrev) btnPrev.style.visibility = newStep === 1 ? 'hidden' : 'visible';
    if (btnNext) btnNext.textContent = newStep === 4 ? 'Finalizar' : 'Siguiente →';

    currentStep = newStep;
}

// Save Analysis
function initSaveButton() {
    document.getElementById('btnSave')?.addEventListener('click', saveAnalysis);
}

async function saveAnalysis() {
    // Collect data
    const analysis = collectAnalysisData();

    // Build content for Notion
    const content = buildAnalysisContent(analysis);

    // Create tags array
    const tags = [
        ...analysis.premisa.tags,
        ...analysis.ruptura.tags,
        ...analysis.remate.tags,
        analysis.ruptura.tecnica,
        analysis.remate.tecnica
    ].filter(t => t);

    const payload = {
        titulo: `ANÁLISIS: ${analysis.joke.text.substring(0, 50)}...`,
        tipo: 'Análisis',
        contenido: content,
        tags: [...new Set(tags)] // Remove duplicates
    };

    try {
        const response = await fetch(`${API_URL}/entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const result = await response.json();
            alert('Análisis guardado correctamente');
            // Reset form or navigate
            loadEntries();
        } else {
            throw new Error('Error al guardar');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar el análisis');
    }
}

function collectAnalysisData() {
    // Joke
    const joke = {
        text: document.getElementById('jokeText')?.value || '',
        comic: document.getElementById('jokeComic')?.value || '',
        show: document.getElementById('jokeShow')?.value || '',
        year: document.getElementById('jokeYear')?.value || ''
    };

    // Premisa
    const diseccionItems = [];
    document.querySelectorAll('#diseccionItems .diseccion-item').forEach(item => {
        const inputs = item.querySelectorAll('input');
        if (inputs[0]?.value && inputs[1]?.value) {
            diseccionItems.push({
                key: inputs[0].value,
                value: inputs[1].value
            });
        }
    });

    const premisa = {
        concepto: document.getElementById('concepto')?.value || '',
        diseccion: diseccionItems,
        elementoMecanico: document.getElementById('elementoMecanico')?.value || '',
        estructura: document.getElementById('estructuraPremisa')?.value || '',
        tags: getSelectedTags('#card-premisa')
    };

    // Ruptura
    const ruptura = {
        tecnica: document.getElementById('tecnicaRuptura')?.value || '',
        caracteristica: document.getElementById('caracteristicaAlterada')?.value || '',
        tags: getSelectedTags('#card-ruptura')
    };

    // Remate
    const situaciones = [];
    document.querySelectorAll('#situationsList .situation-item input').forEach(input => {
        if (input.value) situaciones.push(input.value);
    });

    const remate = {
        tecnica: document.getElementById('tecnicaRemate')?.value || '',
        situaciones: situaciones,
        tags: getSelectedTags('#card-remate')
    };

    return { joke, premisa, ruptura, remate };
}

function getSelectedTags(containerSelector) {
    const tags = [];
    document.querySelectorAll(`${containerSelector} .tag.selected`).forEach(tag => {
        tags.push(tag.textContent.trim());
    });
    return tags;
}

function buildAnalysisContent(analysis) {
    let content = '';

    // Joke
    content += `## CHISTE\n\n`;
    content += `"${analysis.joke.text}"\n\n`;
    if (analysis.joke.comic) content += `**Cómico:** ${analysis.joke.comic}\n`;
    if (analysis.joke.show) content += `**Especial:** ${analysis.joke.show}\n`;
    if (analysis.joke.year) content += `**Año:** ${analysis.joke.year}\n`;
    content += `\n---\n\n`;

    // Premisa
    content += `## PREMISA\n\n`;
    if (analysis.premisa.concepto) {
        content += `**Concepto:** ${analysis.premisa.concepto}\n\n`;
    }
    if (analysis.premisa.diseccion.length > 0) {
        content += `**Disección:**\n`;
        analysis.premisa.diseccion.forEach(d => {
            content += `- ${d.key}: ${d.value}\n`;
        });
        content += `\n`;
    }
    if (analysis.premisa.elementoMecanico) {
        content += `**Elemento mecánico:** "${analysis.premisa.elementoMecanico}"\n\n`;
    }
    if (analysis.premisa.estructura) {
        content += `**Estructura de premisa:** ${formatTechniqueName(analysis.premisa.estructura)}\n\n`;
    }
    content += `---\n\n`;

    // Ruptura
    content += `## RUPTURA\n\n`;
    if (analysis.ruptura.tecnica) {
        content += `**Técnica:** ${formatTechniqueName(analysis.ruptura.tecnica)}\n\n`;
    }
    if (analysis.ruptura.caracteristica) {
        content += `**Característica alterada:** ${analysis.ruptura.caracteristica}\n\n`;
    }
    content += `---\n\n`;

    // Remate
    content += `## REMATE\n\n`;
    if (analysis.remate.tecnica) {
        content += `**Técnica de justificación:** ${formatTechniqueName(analysis.remate.tecnica)}\n\n`;
    }
    if (analysis.remate.situaciones.length > 0) {
        content += `**Situaciones:**\n`;
        analysis.remate.situaciones.forEach((s, i) => {
            content += `${i + 1}. ${s}\n`;
        });
    }

    return content;
}

function formatTechniqueName(slug) {
    if (!slug) return '';
    return slug.split('-').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Load Entries
async function loadEntries() {
    const container = document.getElementById('entriesList');
    if (!container) return;

    try {
        const response = await fetch(`${API_URL}/entries?tipo=Análisis`);
        const data = await response.json();

        if (data.entries && data.entries.length > 0) {
            container.innerHTML = data.entries.map(entry => `
                <div class="entry-card" onclick="viewEntry('${entry.id}')">
                    <div class="entry-title">${entry.titulo || 'Sin título'}</div>
                    <div class="entry-meta">
                        <span>${entry.tipo || ''}</span>
                        <span>${entry.fecha || formatDate(entry.created_time)}</span>
                    </div>
                    ${entry.tags.length > 0 ? `
                        <div class="entry-tags">
                            ${entry.tags.map(t => `<span class="entry-tag">${t}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 40px;">No hay análisis guardados</div>';
        }
    } catch (error) {
        console.error('Error loading entries:', error);
        container.innerHTML = '<div style="text-align: center; color: var(--error); padding: 40px;">Error al cargar</div>';
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('es-ES');
}

// View Entry (placeholder)
function viewEntry(id) {
    console.log('View entry:', id);
    // TODO: Implement detail view
}

// Tags interaction
document.querySelectorAll('.tag:not(.add-tag)').forEach(tag => {
    tag.addEventListener('click', () => {
        tag.classList.toggle('selected');
    });
});

// Catalog item interaction
document.querySelectorAll('.catalog-item').forEach(item => {
    item.addEventListener('click', () => {
        const technique = item.dataset.technique;
        if (technique) {
            // Find and select the corresponding technique option
            const option = document.querySelector(`.technique-option[data-value="${technique}"]`);
            if (option) {
                option.click();
                option.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
});
