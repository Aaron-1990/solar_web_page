// ========================================
// CONFIGURACIÓN GLOBAL
// ========================================
const API_BASE_URL = window.location.origin;
const VEHICLE_SPECS = {
    'byd-king-dm-i-8.3': { battery: 8.3, efficiency: 11.4, name: 'BYD King DM-i (8.3 kWh)' },
    'mitsubishi-outlander': { battery: 20, efficiency: 45.4, name: 'Mitsubishi Outlander PHEV' },
    'mg-ehs': { battery: 16.6, efficiency: 6.06, name: 'MG eHS PHEV' },
    'tesla-model-3': { battery: 57.5, efficiency: 15, name: 'Tesla Model 3' },
    'nissan-leaf': { battery: 40, efficiency: 18, name: 'Nissan LEAF' }
};

// ========================================
// CALCULADORA SOLAR
// ========================================
function initCalculator() {
    const vehicleModelSelect = document.getElementById('vehicleModel');
    const customSpecsDiv = document.getElementById('customSpecs');
    const dailyKmGroupDiv = document.getElementById('dailyKmGroup');
    
    if (vehicleModelSelect) {
        vehicleModelSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customSpecsDiv.style.display = 'block';
                dailyKmGroupDiv.style.display = 'block';
            } else if (this.value === '') {
                customSpecsDiv.style.display = 'none';
                dailyKmGroupDiv.style.display = 'none';
            } else {
                customSpecsDiv.style.display = 'none';
                dailyKmGroupDiv.style.display = 'block';
            }
        });
    }
}

async function calculateIntegral() {
    // Verificar si estamos usando el nuevo diseño
    const newDesign = document.getElementById('includeVehicle');
    
    if (newDesign) {
        // Usar la lógica nueva
        return calculateIntegralNew();
    }
    // Obtener valores del formulario
    const formData = {
        homeConsumption: parseFloat(document.getElementById('homeConsumption').value) || 0,
        location: document.getElementById('location').value,
        coverage: parseFloat(document.getElementById('coverage').value),
        vehicleModel: document.getElementById('vehicleModel').value,
        dailyEvKm: parseFloat(document.getElementById('dailyEvKm').value) || 0,
        panelType: document.getElementById('panelType')?.value || '500w' // NUEVO
    };
    
    // Validaciones
    if (!formData.location) {
        showError('Por favor selecciona tu ubicación');
        return;
    }
    
    // Si es vehículo custom, agregar capacidad de batería
    if (formData.vehicleModel === 'custom') {
        formData.batteryCapacity = parseFloat(document.getElementById('batteryCapacity').value);
        if (!formData.batteryCapacity) {
            showError('Por favor especifica la capacidad de la batería');
            return;
        }
    }
    
    // Mostrar loading
    const calculateBtn = document.querySelector('.calculate-btn');
    const originalText = calculateBtn.innerHTML;
    calculateBtn.innerHTML = '<span class="loading"></span> Calculando...';
    calculateBtn.disabled = true;
    
    try {
        // Llamar a la API
        const response = await fetch(`${API_BASE_URL}/api/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result.data);
            
            // Track evento en analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'calculation_completed', {
                    'event_category': 'engagement',
                    'event_label': formData.vehicleModel || 'no_vehicle',
                    'custom_parameters': {
                        'panel_type': formData.panelType,
                        'panel_power': result.data.panelPowerW
                    }
                });
            }
            
            // Facebook Pixel
            if (typeof fbq !== 'undefined') {
                fbq('track', 'CompleteRegistration', {
                    value: result.data.netCost,
                    currency: 'MXN',
                    content_name: result.data.panelType
                });
            }
        } else {
            showError(result.error || 'Error al calcular');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Error al conectar con el servidor');
    } finally {
        // Restaurar botón
        calculateBtn.innerHTML = originalText;
        calculateBtn.disabled = false;
    }
}

// Nueva función para manejar la calculadora mejorada con paneles modulares
async function calculateIntegralNew() {
    try {
        // Obtener configuración de paneles del módulo si está disponible
        const panelConfig = window.PanelModule ? window.PanelModule.getCalculationConfig() : null;
        
        // Preparar datos del formulario
        const formData = {
            homeConsumption: parseFloat(document.getElementById('homeConsumption').value) || 0,
            location: document.getElementById('location').value,
            coverage: parseFloat(document.getElementById('coverage').value),
            panelType: panelConfig ? panelConfig.panelType : (document.getElementById('panelType')?.value || '500w')
        };
        
        // Validaciones básicas
        if (!formData.location) {
            showError('Por favor selecciona tu ubicación');
            return;
        }
        
        // Verificar si se incluye vehículo
        const includeVehicle = document.getElementById('includeVehicle')?.checked || false;
        
        if (includeVehicle) {
            // Determinar el modo activo (simple o avanzado)
            const activeTab = document.querySelector('.mode-tab.active');
            const isSimpleMode = activeTab && activeTab.textContent.includes('Simple');
            
            if (isSimpleMode) {
                // MODO SIMPLE
                const vehicleModelSelect = document.getElementById('vehicleModel');
                formData.vehicleModel = vehicleModelSelect?.value || '';
                
                if (!formData.vehicleModel) {
                    showError('Por favor selecciona un vehículo');
                    return;
                }
            } else {
                // MODO AVANZADO
                formData.vehicleModel = 'custom';
                
                // Obtener datos del modo avanzado
                const vehicleEfficiency = parseFloat(document.getElementById('consumptionInput')?.value);
                const customVehicleName = document.getElementById('customVehicleName')?.value;
                
                if (!vehicleEfficiency) {
                    showError('Por favor ingresa el consumo del vehículo');
                    return;
                }
                
                formData.vehicleEfficiency = vehicleEfficiency;
                formData.customVehicleName = customVehicleName || 'Vehículo personalizado';
            }
            
            // Kilómetros diarios (común para ambos modos)
            formData.dailyEvKm = parseFloat(document.getElementById('dailyEvKm')?.value) || 40;
        } else {
            // No incluir vehículo
            formData.vehicleModel = '';
            formData.dailyEvKm = 0;
        }
        
        // Mostrar loading
        const calculateBtn = document.querySelector('.calculate-btn');
        const originalContent = calculateBtn.innerHTML;
        calculateBtn.innerHTML = '<span class="loading"></span> Calculando...';
        calculateBtn.disabled = true;
        
        // Llamar a la API
        const response = await fetch(`${API_BASE_URL}/api/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Usar la función mejorada de display que incluye información de paneles
            displayResults(result.data);
            
            // Disparar evento para el módulo de paneles
            if (window.PanelModule) {
                const event = new CustomEvent('calculationUpdated', {
                    detail: result.data
                });
                document.dispatchEvent(event);
            }
            
            // Analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'calculation_completed', {
                    'event_category': 'engagement',
                    'event_label': includeVehicle ? 'with_vehicle' : 'home_only',
                    'event_value': result.data.numberOfPanels,
                    'custom_parameters': {
                        'panel_type': formData.panelType,
                        'panel_power': result.data.panelPowerW,
                        'system_power_kw': result.data.systemPowerKw
                    }
                });
            }
            
            // Facebook Pixel
            if (typeof fbq !== 'undefined') {
                fbq('track', 'CompleteRegistration', {
                    value: result.data.netCost,
                    currency: 'MXN',
                    content_type: includeVehicle ? 'home_plus_vehicle' : 'home_only',
                    content_name: result.data.panelType
                });
            }
        } else {
            showError(result.error || 'Error al calcular');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Error al conectar con el servidor');
    } finally {
        // Restaurar botón
        const calculateBtn = document.querySelector('.calculate-btn');
        if (calculateBtn) {
            calculateBtn.innerHTML = calculateBtn.dataset.originalContent || 
                '<span class="btn-icon">⚡</span><span class="btn-text">Calcular Mi Sistema Solar</span>';
            calculateBtn.disabled = false;
        }
    }
}

// ========================================
// FUNCIÓN DISPLAYRESULTS MEJORADA - CON DESGLOSE SEPARADO
// Reemplazar en static/js/main.js
// ========================================

function displayResults(results) {
    const resultsSection = document.getElementById('results');
    const resultsSummary = document.getElementById('resultsSummary');
    const resultsGrid = document.getElementById('resultsGrid');
    
    if (!resultsSection || !resultsGrid) {
        console.error('❌ Elementos de resultados no encontrados');
        return;
    }
    
    // Detectar si tenemos información detallada de paneles
    const hasPanelDetails = results.hasOwnProperty('panelType') && 
                           results.hasOwnProperty('panelPowerW') && 
                           results.hasOwnProperty('kwh_per_panel_bimestral');
    
    console.log(`📊 Mostrando resultados ${hasPanelDetails ? 'con' : 'sin'} detalles de paneles`);
    
    // ================================
    // SECCIÓN DE RESUMEN
    // ================================
    if (resultsSummary) {
        let summaryText;
        
        if (hasPanelDetails) {
            summaryText = results.hasVehicle 
                ? `${results.numberOfPanels} paneles de ${results.panelPowerW}W • Ahorro anual de $${results.totalAnnualSavings.toLocaleString()}`
                : `${results.numberOfPanels} paneles de ${results.panelPowerW}W para tu hogar • Ahorro anual de $${results.totalAnnualSavings.toLocaleString()}`;
                
            resultsSummary.innerHTML = `
                <h4>¡Tu sistema solar ideal está listo!</h4>
                <p class="main-result">${results.systemPowerKw} kW (${results.panelType})</p>
                <p class="sub-result">${summaryText}</p>
                <div class="panel-summary">
                    <span class="panel-detail">Cada panel genera ~${results.kwh_per_panel_bimestral} kWh bimestral</span>
                    <span class="panel-detail">Área total requerida: ${results.totalRoofArea} m²</span>
                </div>
            `;
        } else {
            summaryText = results.hasVehicle 
                ? `Sistema de ${results.systemPowerKw} kW • Ahorro anual de $${results.totalAnnualSavings.toLocaleString()}`
                : `Sistema de ${results.systemPowerKw} kW para tu hogar • Ahorro anual de $${results.totalAnnualSavings.toLocaleString()}`;
                
            resultsSummary.innerHTML = `
                <h4>¡Tu sistema solar ideal está listo!</h4>
                <p class="main-result">${results.numberOfPanels} paneles solares</p>
                <p class="sub-result">${summaryText}</p>
            `;
        }
    }
    
    // ================================
    // GRID DE RESULTADOS (SIN DESGLOSE)
    // ================================
    
    // Resultados de vehículo (si aplica)
    let vehicleResults = '';
    if (results.hasVehicle) {
        vehicleResults = `
            <div class="result-card">
                <div class="result-icon">⛽</div>
                <div class="result-value">$${results.annualGasSavings.toLocaleString()}</div>
                <div class="result-label">Ahorro Anual en Gasolina</div>
            </div>
            <div class="result-card">
                <div class="result-icon">🚗</div>
                <div class="result-value">${results.vehicleInfo}</div>
                <div class="result-label">Vehículo Incluido</div>
            </div>
        `;
    }
    
    // Tarjeta de paneles (adaptativa)
    let panelCard;
    if (hasPanelDetails) {
        panelCard = `
            <div class="result-card highlight panel-info">
                <div class="result-icon">⚡</div>
                <div class="result-value">${results.numberOfPanels}</div>
                <div class="result-label">Paneles ${results.panelPowerW}W</div>
                <div class="result-sublabel">${results.panelType}</div>
            </div>
        `;
    } else {
        panelCard = `
            <div class="result-card highlight">
                <div class="result-icon">⚡</div>
                <div class="result-value">${results.numberOfPanels}</div>
                <div class="result-label">Paneles Solares</div>
            </div>
        `;
    }
    
    // Construir grid SIN el desglose
    resultsGrid.innerHTML = `
        ${panelCard}
        <div class="result-card highlight">
            <div class="result-icon">💰</div>
            <div class="result-value">$${results.netCost.toLocaleString()}</div>
            <div class="result-label">Inversión Total (con incentivos)</div>
        </div>
        <div class="result-card">
            <div class="result-icon">🏠</div>
            <div class="result-value">$${results.annualElectricitySavings.toLocaleString()}</div>
            <div class="result-label">Ahorro Anual en Electricidad</div>
        </div>
        ${vehicleResults}
        <div class="result-card">
            <div class="result-icon">📅</div>
            <div class="result-value">${results.paybackYears} años</div>
            <div class="result-label">Recuperación de Inversión</div>
        </div>
        <div class="result-card">
            <div class="result-icon">🌱</div>
            <div class="result-value">${results.totalCo2Avoided} ton</div>
            <div class="result-label">CO₂ Evitado Anualmente</div>
        </div>
        <div class="result-card">
            <div class="result-icon">📐</div>
            <div class="result-value">${results.totalRoofArea} m²</div>
            <div class="result-label">Área de Techo Requerida</div>
        </div>
        <div class="result-card">
            <div class="result-icon">💵</div>
            <div class="result-value">${results.monthlySavings.toLocaleString()}</div>
            <div class="result-label">Ahorro Mensual Promedio</div>
        </div>
        <div class="result-card">
            <div class="result-icon">📈</div>
            <div class="result-value">${results.roi25Years}%</div>
            <div class="result-label">ROI a 25 años</div>
        </div>
        <div class="result-card">
            <div class="result-icon">🌳</div>
            <div class="result-value">${Math.round(results.treesEquivalent)}</div>
            <div class="result-label">Árboles Equivalentes</div>
        </div>
    `;
    
    // ================================
    // NUEVA SECCIÓN: DESGLOSE SEPARADO E INDEPENDIENTE
    // ================================
    if (hasPanelDetails) {
        // Buscar o crear contenedor para el desglose
        let breakdownContainer = document.getElementById('calculationBreakdownSection');
        
        if (!breakdownContainer) {
            // Crear nueva sección después de resultsSection
            breakdownContainer = document.createElement('div');
            breakdownContainer.id = 'calculationBreakdownSection';
            breakdownContainer.className = 'calculation-breakdown-section full-rounded';
            
            // Insertar después de la sección de resultados
            resultsSection.parentNode.insertBefore(breakdownContainer, resultsSection.nextSibling);
        }
        
        // Contenido del desglose independiente
        breakdownContainer.innerHTML = `
            <div class="container">
                <div class="calculation-breakdown">
                    <h5>📊 Desglose Detallado del Cálculo</h5>
                    
                    <div class="breakdown-grid">
                        <div class="breakdown-item">
                            <span class="breakdown-label">Panel seleccionado:</span>
                            <span class="breakdown-value">${results.panelType}</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Generación teórica por panel (bimestral):</span>
                            <span class="breakdown-value">${(results.kwh_per_panel_bimestral / 0.8).toFixed(1)} kWh</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Generación real por panel (bimestral):</span>
                            <span class="breakdown-value">${results.kwh_per_panel_bimestral} kWh</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Generación total diaria:</span>
                            <span class="breakdown-value">${results.dailyGeneration} kWh</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Generación anual:</span>
                            <span class="breakdown-value">${results.annualSolarGeneration.toLocaleString()} kWh</span>
                        </div>
                        <div class="breakdown-item hsp-item">
                            <span class="breakdown-label">HSP de tu ubicación:</span>
                            <span class="breakdown-value">${results.hsp} horas</span>
                            <div class="hsp-source-info">
                                <small class="source-reference">
                                    📊 <strong>Fuente:</strong> NASA POWER Database | 
                                    <span class="source-detail">Datos satelitales validados (±3-5% precisión)</span>
                                </small>
                            </div>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Cobertura seleccionada:</span>
                            <span class="breakdown-value">${results.coverage}%</span>
                        </div>
                    </div>
                    
                    <!-- Explicación de pérdidas del sistema -->
                    <div class="system-losses-explanation">
                        <div class="explanation-header">
                            <h6>🔧 Explicación de Pérdidas del Sistema (20%)</h6>
                            <span class="info-toggle" onclick="toggleSystemLossesInfo()">ℹ️ Ver detalles</span>
                        </div>
                        <div class="calculation-note">
                            <p class="note-main">
                                <strong>¿Por qué 20% de pérdidas?</strong> Los sistemas solares tienen pérdidas operativas normales 
                                que reducen la generación teórica. Esto es estándar en la industria y está incluido en nuestros cálculos.
                            </p>
                            <div class="losses-breakdown" id="lossesBreakdown" style="display: none;">
                                <h6>Desglose de pérdidas típicas:</h6>
                                <ul class="losses-list">
                                    <li>🔌 <strong>Inversor:</strong> 4-6% (conversión DC a AC)</li>
                                    <li>⚡ <strong>Cables:</strong> 1-3% (resistencia eléctrica)</li>
                                    <li>🌡️ <strong>Temperatura:</strong> 5-10% (paneles se calientan)</li>
                                    <li>☁️ <strong>Sombreado parcial:</strong> 0-5% (nubes, objetos)</li>
                                    <li>🧹 <strong>Suciedad/polvo:</strong> 2-5% (mantenimiento)</li>
                                    <li>⚖️ <strong>Desajuste de paneles:</strong> 1-3% (tolerancias de fabricación)</li>
                                </ul>
                                <div class="losses-total">
                                    <strong>Total promedio: 15-25% (usamos 20% conservador)</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Si no hay detalles de paneles, ocultar/remover la sección de desglose
        const existingBreakdown = document.getElementById('calculationBreakdownSection');
        if (existingBreakdown) {
            existingBreakdown.style.display = 'none';
        }
    }
    
    // ================================
    // MOSTRAR Y ANIMAR RESULTADOS
    // ================================
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Funciones auxiliares
    if (typeof showCostDisclaimer === 'function') {
        showCostDisclaimer();
    }
    
    if (typeof animateNumbers === 'function') {
        animateNumbers();
    }
    
    console.log('✅ Resultados mostrados correctamente');
}


// NUEVA FUNCIÓN: Toggle para mostrar/ocultar detalles de pérdidas
function toggleSystemLossesInfo() {
    const lossesBreakdown = document.getElementById('lossesBreakdown');
    const toggleBtn = document.querySelector('.info-toggle');
    
    if (!lossesBreakdown || !toggleBtn) {
        console.warn('⚠️ Elementos de toggle no encontrados');
        return;
    }
    
    if (lossesBreakdown.style.display === 'none') {
        lossesBreakdown.style.display = 'block';
        toggleBtn.textContent = '❌ Ocultar detalles';
        lossesBreakdown.style.animation = 'fadeIn 0.3s ease';
    } else {
        lossesBreakdown.style.display = 'none';
        toggleBtn.textContent = 'ℹ️ Ver detalles';
    }
}

// Hacer funciones globales
window.toggleSystemLossesInfo = toggleSystemLossesInfo;

// ========================================
// NUEVAS FUNCIONES PARA CALCULADORA MEJORADA
// ========================================

//VERSIÓN CORREGIDA:
function toggleVehicleSection() {
    // Prevenir propagación del evento
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    console.log('🚗 Toggle vehículo activado');
    
    const checkbox = document.getElementById('includeVehicle');
    const vehicleContent = document.getElementById('vehicleContent');
    const toggleText = document.getElementById('vehicleToggleText');
    const calculationMode = document.getElementById('calculationMode');
    
    // Verificar que todos los elementos existen
    if (!checkbox || !vehicleContent || !toggleText || !calculationMode) {
        console.error('❌ Elementos del toggle no encontrados');
        return;
    }
    
    const isChecked = checkbox.checked;
    console.log(`📋 Estado checkbox: ${isChecked ? 'ACTIVADO' : 'DESACTIVADO'}`);
    
    if (isChecked) {
        // MOSTRAR sección de vehículo
        vehicleContent.style.display = 'block';
        toggleText.textContent = 'Incluir';
        calculationMode.textContent = 'Calculando para hogar + vehículo eléctrico';
        
        // Animación de apertura
        vehicleContent.style.opacity = '0';
        vehicleContent.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            vehicleContent.style.opacity = '1';
            vehicleContent.style.transform = 'translateY(0)';
            vehicleContent.style.transition = 'all 0.3s ease';
        }, 10);
        
        console.log('✅ Sección vehículo MOSTRADA');
        
    } else {
        // OCULTAR sección de vehículo
        vehicleContent.style.opacity = '0';
        vehicleContent.style.transform = 'translateY(-10px)';
        toggleText.textContent = 'No incluir';
        calculationMode.textContent = 'Calculando solo para tu hogar';
        
        setTimeout(() => {
            vehicleContent.style.display = 'none';
        }, 300);
        
        console.log('✅ Sección vehículo OCULTADA');
    }
}

// Cambiar entre modo simple y avanzado
function selectVehicleMode(mode) {
    const tabs = document.querySelectorAll('.mode-tab');
    const simpleMode = document.getElementById('simpleVehicleMode');
    const advancedMode = document.getElementById('advancedVehicleMode');
    
    // Actualizar tabs
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.closest('.mode-tab').classList.add('active');
    
    // Mostrar panel correspondiente
    if (mode === 'simple') {
        simpleMode.style.display = 'block';
        advancedMode.style.display = 'none';
    } else {
        simpleMode.style.display = 'none';
        advancedMode.style.display = 'block';
        document.getElementById('dailyKmSection').style.display = 'block';
    }
}

// Manejar selección de vehículo
function handleVehicleSelection() {
    const vehicleModel = document.getElementById('vehicleModel').value;
    const dailyKmSection = document.getElementById('dailyKmSection');
    dailyKmSection.style.display = vehicleModel ? 'block' : 'none';
}

// OPCIONAL: Función para resetear el toggle si hay problemas
function resetVehicleToggle() {
    const checkbox = document.getElementById('includeVehicle');
    const vehicleContent = document.getElementById('vehicleContent');
    const toggleText = document.getElementById('vehicleToggleText');
    
    if (checkbox && vehicleContent && toggleText) {
        checkbox.checked = false;
        vehicleContent.style.display = 'none';
        toggleText.textContent = 'No incluir';
        console.log('🔄 Toggle vehículo reseteado');
    }
}

// Calcular eficiencia desde batería y autonomía
function calculateEfficiency() {
    const battery = parseFloat(document.getElementById('batteryHelper').value);
    const range = parseFloat(document.getElementById('rangeHelper').value);
    
    if (battery && range) {
        const efficiency = (battery / range) * 100;
        document.getElementById('consumptionInput').value = efficiency.toFixed(1);
        
        // Animación de éxito
        const input = document.getElementById('consumptionInput');
        input.style.backgroundColor = '#d4edda';
        setTimeout(() => {
            input.style.backgroundColor = '';
            input.style.transition = 'background-color 0.5s ease';
        }, 1000);
    } else {
        alert('Por favor ingresa tanto la capacidad de batería como la autonomía');
    }
}

// Actualizar valor del slider
function updateKmValue() {
    const slider = document.getElementById('kmSlider');
    const input = document.getElementById('dailyEvKm');
    input.value = slider.value;
}

// Actualizar slider desde input
function updateKmSlider() {
    const slider = document.getElementById('kmSlider');
    const input = document.getElementById('dailyEvKm');
    slider.value = input.value;
}

// Establecer km predefinidos
function setKm(value) {
    document.getElementById('dailyEvKm').value = value;
    document.getElementById('kmSlider').value = value;
    
    // Resaltar botón seleccionado
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.style.backgroundColor = '';
    });
    event.target.style.backgroundColor = '#e8f5e8';
}


// ========================================
// GESTIÓN DE PARTNERS
// ========================================
function switchPartner(section, partner) {
    const contents = document.querySelectorAll(`#${section} .partner-content`);
    const buttons = document.querySelectorAll(`#${section} .partner-tab`);
    
    // Ocultar todos los contenidos
    contents.forEach(content => content.classList.remove('active'));
    
    // Desactivar todos los botones
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Activar el contenido y botón seleccionado
    const contentToShow = document.getElementById(`${section}-${partner}`);
    if (contentToShow) {
        contentToShow.classList.add('active');
    }
    
    // Activar el botón clickeado
    event.target.classList.add('active');
}

async function trackClick(partner, product) {
    try {
        // Enviar tracking al servidor
        const response = await fetch(`${API_BASE_URL}/api/track/click`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ partner, product })
        });
        
        const result = await response.json();
        
        if (result.success && result.redirect_url) {
            // Analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'partner_click', {
                    'event_category': 'affiliate',
                    'event_label': `${partner}-${product}`
                });
            }
            
            // Facebook Pixel
            if (typeof fbq !== 'undefined') {
                fbq('track', 'ViewContent', {
                    content_name: product,
                    content_category: partner
                });
            }
            
            // Abrir en nueva ventana
            window.open(result.redirect_url, '_blank');
        }
    } catch (error) {
        console.error('Error tracking click:', error);
        // Fallback: abrir URL directamente
        window.open('#', '_blank');
    }
}

// ========================================
// NEWSLETTER
// ========================================
async function subscribeNewsletter() {
    const emailInput = document.getElementById('emailNewsletter');
    const email = emailInput.value.trim();
    
    // Validación básica
    if (!email || !isValidEmail(email)) {
        showError('Por favor ingresa un email válido');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/newsletter/subscribe`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                email: email,
                source: 'homepage'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(result.message || '¡Gracias por suscribirte!');
            emailInput.value = '';
            
            // Analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'newsletter_subscription', {
                    'event_category': 'engagement'
                });
            }
            
            // Facebook Pixel
            if (typeof fbq !== 'undefined') {
                fbq('track', 'Lead');
            }
        } else {
            showError(result.message || 'Error al suscribirse');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Error al procesar la suscripción');
    }
}

// ========================================
// UTILIDADES
// ========================================
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showError(message) {
    // Implementar notificación de error
    const notification = createNotification(message, 'error');
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showSuccess(message) {
    // Implementar notificación de éxito
    const notification = createNotification(message, 'success');
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function createNotification(message, type) {
    const div = document.createElement('div');
    div.className = `notification ${type}-message`;
    div.textContent = message;
    div.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        ${type === 'error' ? 'background: #e74c3c;' : 'background: #2ECC71;'}
    `;
    return div;
}

// ========================================
// FUNCIONES AUXILIARES PARA PANELES
// ========================================

// Función auxiliar para preview en tiempo real (opcional)
function updateCalculationPreview(panelData) {
    // Esta función puede mostrar un preview en tiempo real
    // de cómo afecta el cambio de panel al cálculo
    const homeConsumption = parseFloat(document.getElementById('homeConsumption')?.value) || 0;
    const locationSelect = document.getElementById('location');
    const hsp = locationSelect?.options[locationSelect.selectedIndex]?.dataset.hsp || 5.5;
    
    // Cálculo rápido para preview
    const panelsNeeded = Math.ceil(homeConsumption / ((panelData.panelData.power * hsp * 60 * 0.8) / 1000));
    
    // Mostrar hint visual (opcional)
    if (document.getElementById('panelPreview')) {
        document.getElementById('panelPreview').textContent = 
            `Estimación: ~${panelsNeeded} paneles necesarios`;
    }
}

// Función global para compatibilidad con HTML onclick (para paneles)
window.updatePanelInfo = function() {
    if (window.PanelModule && window.PanelModule.state.isInitialized) {
        window.PanelModule.updatePanelInfo();
    }
};

// ========================================
// SMOOTH SCROLL
// ========================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ========================================
// LAZY LOADING DE IMÁGENES
// ========================================
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}

// ========================================
// SERVICE WORKER (PWA)
// ========================================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered'))
            .catch(err => console.log('SW registration failed'));
    });
}

// ========================================
// INICIALIZACIÓN UNIFICADA MEJORADA
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando aplicación...');
    
    // 1. NAVEGACIÓN MÓVIL
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Cerrar menú al hacer click en un enlace
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
        });
    });
    
    // 2. DETECTAR Y INICIALIZAR CALCULADORA CORRECTA
    const oldCalculator = document.getElementById('vehicleModel');
    const newCalculator = document.getElementById('includeVehicle');
    const panelSelector = document.getElementById('panelType');
    
    if (newCalculator) {
        // Inicializar calculadora nueva
        initNewCalculator();
        console.log('✅ Calculadora nueva inicializada');
    } else if (oldCalculator) {
        // Usar calculadora antigua
        initCalculator();
        console.log('✅ Calculadora antigua inicializada');
    }
    
    // 3. VERIFICAR MÓDULO DE PANELES
    if (window.PanelModule) {
        console.log('✅ Módulo de paneles detectado y listo');
        
        // Escuchar eventos del módulo de paneles
        document.addEventListener('panelChanged', function(e) {
            console.log('📋 Panel changed:', e.detail.panelType);
            
            // Actualizar preview en tiempo real si es necesario
            updateCalculationPreview(e.detail);
        });
    } else {
        console.warn('⚠️ Módulo de paneles no detectado');
    }
    
    // 4. ANIMACIONES AL SCROLL
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observar elementos para animación
    document.querySelectorAll('.stat-card, .benefit-card, .product-card').forEach(el => {
        observer.observe(el);
    });
    
    // 5. GUARDAR CONTENIDO ORIGINAL DEL BOTÓN CALCULAR
    const calculateBtn = document.querySelector('.calculate-btn');
    if (calculateBtn) {
        calculateBtn.dataset.originalContent = calculateBtn.innerHTML;
    }
    
    console.log('✅ Inicialización completa');
    // AGREGAR el event listener del toggle vehículo
    const vehicleToggle = document.getElementById('includeVehicle');
    if (vehicleToggle) {
        vehicleToggle.addEventListener('change', function(event) {
            toggleVehicleSection(event);
        });
        console.log('✅ Event listener del toggle vehículo configurado');
    }
});

// Función para inicializar la calculadora nueva
function initNewCalculator() {
    console.log('🔧 Inicializando calculadora nueva...');
    
    // Verificar que los elementos existen
    const vehicleToggle = document.getElementById('includeVehicle');
    const vehicleContent = document.getElementById('vehicleContent');
    
    if (vehicleToggle && vehicleContent) {
        console.log('✅ Toggle de vehículo encontrado y listo');
    }
    
    // Inicializar el slider si existe
    const kmSlider = document.getElementById('kmSlider');
    if (kmSlider) {
        kmSlider.addEventListener('input', updateKmValue);
    }
    
    const dailyEvKm = document.getElementById('dailyEvKm');
    if (dailyEvKm) {
        dailyEvKm.addEventListener('change', updateKmSlider);
    }
    
    // Verificar selector de paneles
    const panelSelector = document.getElementById('panelType');
    if (panelSelector) {
        console.log('✅ Selector de paneles encontrado');
    } else {
        console.warn('⚠️ Selector de paneles no encontrado');
    }
}

// ========================================
// FUNCIONES PARA DISCLAIMER DE COSTOS
// ========================================

function showQuoteOptions() {
    document.getElementById('quoteModal').style.display = 'flex';
    
    // Analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'quote_request_opened', {
            'event_category': 'engagement'
        });
    }
}

function closeQuoteModal() {
    document.getElementById('quoteModal').style.display = 'none';
}

function requestEmailQuote() {
    // Implementar lógica para solicitud por email
    alert('Funcionalidad en desarrollo: Solicitud por email\n\nPor ahora, contacta directamente con nuestros partners en la sección "Equipamiento Solar".');
    closeQuoteModal();
    
    // Scroll a sección de equipamiento
    document.getElementById('equipamiento').scrollIntoView({ behavior: 'smooth' });
}

function scheduleCall() {
    // Implementar lógica para programar llamada
    alert('Funcionalidad en desarrollo: Programar llamada\n\nPor ahora, puedes contactar directamente con los instaladores recomendados.');
    closeQuoteModal();
    
    // Scroll a sección de equipamiento
    document.getElementById('equipamiento').scrollIntoView({ behavior: 'smooth' });
}

function showInstallers() {
    // Redirigir a sección de instaladores
    closeQuoteModal();
    document.getElementById('equipamiento').scrollIntoView({ behavior: 'smooth' });
}

// Mostrar disclaimer cuando se muestren los resultados
function showCostDisclaimer() {
    const disclaimer = document.getElementById('costDisclaimer');
    if (disclaimer) {
        disclaimer.style.display = 'block';
        // Pequeño delay para que aparezca después de los resultados
        setTimeout(() => {
            disclaimer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 1000);
    }
}

// Cerrar modal al presionar Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeQuoteModal();
    }
});

// Cerrar modal al hacer click fuera
document.addEventListener('click', function(e) {
    const modal = document.getElementById('quoteModal');
    if (e.target === modal) {
        closeQuoteModal();
    }
});