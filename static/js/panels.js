/**
 * ========================================
 * MÓDULO DE GESTIÓN DE PANELES SOLARES
 * panels.js - Funcionalidad específica para selección y configuración de paneles
 * ========================================
 */

// Configuración del módulo
const PanelModule = {
    // Datos de paneles (sincronizado con backend)
    PANEL_DATA: {
        '450w': {
            name: 'Panel 450W (Estándar)',
            power: 450,
            area_m2: 2.3,
            efficiency: 20.5,
            description: 'Panel solar monocristalino estándar, ideal para comenzar en energía solar',
            technology: 'Monocristalino PERC',
            warranty_years: 25,
            degradation_rate: 0.005
        },
        '500w': {
            name: 'Panel 500W (Alta Eficiencia)',
            power: 500,
            area_m2: 2.4,
            efficiency: 21.8,
            description: 'Panel solar de alta eficiencia, mejor relación costo-beneficio',
            technology: 'Monocristalino Half-Cell',
            warranty_years: 25,
            degradation_rate: 0.004
        },
        '550w': {
            name: 'Panel 550W (Premium)',
            power: 550,
            area_m2: 2.5,
            efficiency: 22.5,
            description: 'Panel solar premium para máxima generación en espacios limitados',
            technology: 'Monocristalino Bifacial',
            warranty_years: 30,
            degradation_rate: 0.003
        },
        '600w': {
            name: 'Panel 600W (Ultra Premium)',
            power: 600,
            area_m2: 2.6,
            efficiency: 23.2,
            description: 'Panel solar ultra premium de última generación, máxima eficiencia',
            technology: 'Monocristalino TOPCon',
            warranty_years: 30,
            degradation_rate: 0.003
        }
    },

    // Elementos DOM cacheados
    elements: {
        panelTypeSelect: null,
        panelInfoCard: null,
        panelPower: null,
        panelEfficiency: null,
        panelArea: null,
        panelTech: null,
        panelDescription: null,
        locationSelect: null
    },

    // Estado del módulo
    state: {
        currentPanel: '500w',
        currentHSP: 5.5,
        isInitialized: false
    },

    /**
     * Inicializar el módulo de paneles
     */
    init() {
        if (this.state.isInitialized) {
            console.warn('PanelModule ya está inicializado');
            return;
        }

        this.cacheElements();
        this.bindEvents();
        this.updatePanelInfo();
        this.state.isInitialized = true;
        
        console.log('✅ PanelModule inicializado correctamente');
    },

    /**
     * Cachear elementos DOM para mejor performance
     */
    cacheElements() {
        this.elements = {
            panelTypeSelect: document.getElementById('panelType'),
            panelInfoCard: document.getElementById('panelInfoCard'),
            panelPower: document.getElementById('panelPower'),
            panelEfficiency: document.getElementById('panelEfficiency'),
            panelArea: document.getElementById('panelArea'),
            panelTech: document.getElementById('panelTech'),
            panelDescription: document.getElementById('panelDescription'),
            locationSelect: document.getElementById('location')
        };

        // Verificar que todos los elementos existen
        const missingElements = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);

        if (missingElements.length > 0) {
            console.error('❌ Elementos DOM faltantes:', missingElements);
            throw new Error(`Elementos DOM requeridos no encontrados: ${missingElements.join(', ')}`);
        }
    },

    /**
     * Vincular eventos
     */
    bindEvents() {
        // Cambio de tipo de panel
        this.elements.panelTypeSelect.addEventListener('change', (e) => {
            this.handlePanelChange(e.target.value);
        });

        // Cambio de ubicación (afecta HSP)
        this.elements.locationSelect.addEventListener('change', () => {
            this.updateHSP();
            this.updatePanelInfo();
        });

        // Evento personalizado para cuando se actualiza el cálculo
        document.addEventListener('calculationUpdated', (e) => {
            this.handleCalculationUpdate(e.detail);
        });
    },

    /**
     * Manejar cambio de tipo de panel
     */
    handlePanelChange(panelType) {
        if (!this.PANEL_DATA[panelType]) {
            console.error('❌ Tipo de panel inválido:', panelType);
            return;
        }

        this.state.currentPanel = panelType;
        this.updatePanelInfo();
        
        // Disparar evento personalizado
        this.dispatchPanelChangeEvent(panelType);
        
        // Analytics tracking
        this.trackPanelSelection(panelType);
    },

    /**
     * Actualizar información del panel en la UI
     */
    updatePanelInfo() {
        const panelData = this.PANEL_DATA[this.state.currentPanel];
        
        if (!panelData) {
            console.error('❌ Datos de panel no encontrados:', this.state.currentPanel);
            return;
        }

        // Añadir clase de animación
        this.elements.panelInfoCard.classList.add('updating');
        
        // Actualizar contenido con pequeño delay para la animación
        setTimeout(() => {
            this.elements.panelPower.textContent = `${panelData.power}W`;
            this.elements.panelEfficiency.textContent = `${panelData.efficiency}%`;
            this.elements.panelArea.textContent = `${panelData.area_m2} m²`;
            this.elements.panelTech.textContent = panelData.technology;
            this.elements.panelDescription.textContent = panelData.description;
            
            // Actualizar tooltips si existen
            this.updateTooltips(panelData);
            
            // Remover clase de animación
            this.elements.panelInfoCard.classList.remove('updating');
        }, 100);
    },

    /**
     * Actualizar HSP basado en la ubicación seleccionada
     */
    updateHSP() {
        const selectedOption = this.elements.locationSelect.options[this.elements.locationSelect.selectedIndex];
        this.state.currentHSP = selectedOption && selectedOption.dataset.hsp 
            ? parseFloat(selectedOption.dataset.hsp) 
            : 5.5;
    },

    /**
     * Actualizar tooltips con información adicional
     */
    updateTooltips(panelData) {
        const specItems = this.elements.panelInfoCard.querySelectorAll('.spec-item');
        
        specItems.forEach(item => {
            const label = item.querySelector('.spec-label').textContent.toLowerCase();
            
            switch (label) {
                case 'potencia:':
                    item.setAttribute('data-tooltip', `Mayor potencia = menos paneles necesarios`);
                    break;
                case 'eficiencia:':
                    item.setAttribute('data-tooltip', `${panelData.efficiency}% de la luz solar se convierte en electricidad`);
                    break;
                case 'área:':
                    item.setAttribute('data-tooltip', `Espacio que ocupa cada panel en tu techo`);
                    break;
                case 'tecnología:':
                    item.setAttribute('data-tooltip', `${panelData.warranty_years} años de garantía`);
                    break;
            }
        });
    },

    /**
     * Obtener datos del panel actualmente seleccionado
     */
    getCurrentPanelData() {
        return {
            type: this.state.currentPanel,
            data: this.PANEL_DATA[this.state.currentPanel],
            hsp: this.state.currentHSP
        };
    },

    /**
     * Calcular métricas del panel actual
     */
    calculatePanelMetrics() {
        const panelData = this.PANEL_DATA[this.state.currentPanel];
        const dailyGeneration = (panelData.power * this.state.currentHSP) / 1000;
        const bimestralGeneration = dailyGeneration * 60;
        
        return {
            dailyKwh: dailyGeneration,
            bimestralKwh: bimestralGeneration,
            annualKwh: dailyGeneration * 365,
            powerDensity: panelData.power / panelData.area_m2 // W/m²
        };
    },

    /**
     * Comparar paneles
     */
    comparePanels(panelTypes = null) {
        const types = panelTypes || Object.keys(this.PANEL_DATA);
        
        return types.map(type => {
            const data = this.PANEL_DATA[type];
            const metrics = this.calculatePanelMetrics();
            
            return {
                type,
                name: data.name,
                power: data.power,
                efficiency: data.efficiency,
                area: data.area_m2,
                powerDensity: data.power / data.area_m2,
                dailyGeneration: (data.power * this.state.currentHSP) / 1000
            };
        }).sort((a, b) => b.power - a.power);
    },

    /**
     * Disparar evento personalizado cuando cambia el panel
     */
    dispatchPanelChangeEvent(panelType) {
        const event = new CustomEvent('panelChanged', {
            detail: {
                panelType,
                panelData: this.PANEL_DATA[panelType],
                metrics: this.calculatePanelMetrics()
            }
        });
        document.dispatchEvent(event);
    },

    /**
     * Manejar actualización de cálculo
     */
    handleCalculationUpdate(calculationData) {
        // Aquí puedes agregar lógica para mostrar información adicional
        // basada en los resultados del cálculo
        console.log('📊 Cálculo actualizado con panel:', this.state.currentPanel);
    },

    /**
     * Tracking de analytics
     */
    trackPanelSelection(panelType) {
        // Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'panel_selection', {
                'event_category': 'calculator',
                'event_label': panelType,
                'custom_parameters': {
                    'panel_power': this.PANEL_DATA[panelType].power,
                    'panel_efficiency': this.PANEL_DATA[panelType].efficiency
                }
            });
        }

        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', 'ViewContent', {
                content_name: this.PANEL_DATA[panelType].name,
                content_category: 'solar_panels',
                value: this.PANEL_DATA[panelType].power,
                currency: 'MXN'
            });
        }

        console.log('📈 Panel selection tracked:', panelType);
    },

    /**
     * Validar selección actual
     */
    validateCurrentSelection() {
        const errors = [];
        
        if (!this.state.currentPanel || !this.PANEL_DATA[this.state.currentPanel]) {
            errors.push('Tipo de panel inválido');
        }
        
        if (this.state.currentHSP < 3 || this.state.currentHSP > 8) {
            errors.push('HSP fuera de rango válido');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    },

    /**
     * Obtener configuración para el cálculo
     */
    getCalculationConfig() {
        const validation = this.validateCurrentSelection();
        
        if (!validation.isValid) {
            throw new Error(`Configuración de panel inválida: ${validation.errors.join(', ')}`);
        }
        
        return {
            panelType: this.state.currentPanel,
            panelData: this.PANEL_DATA[this.state.currentPanel],
            hsp: this.state.currentHSP,
            metrics: this.calculatePanelMetrics()
        };
    },

    /**
     * Destruir el módulo (cleanup)
     */
    destroy() {
        // Remover event listeners
        if (this.elements.panelTypeSelect) {
            this.elements.panelTypeSelect.removeEventListener('change', this.handlePanelChange);
        }
        
        if (this.elements.locationSelect) {
            this.elements.locationSelect.removeEventListener('change', this.updatePanelInfo);
        }
        
        // Resetear estado
        this.state.isInitialized = false;
        
        console.log('🗑️ PanelModule destruido');
    }
};

// Función global para compatibilidad con HTML onclick
window.updatePanelInfo = function() {
    if (PanelModule.state.isInitialized) {
        PanelModule.updatePanelInfo();
    }
};

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        PanelModule.init();
    });
} else {
    PanelModule.init();
}

// Exportar módulo para uso en otros scripts
window.PanelModule = PanelModule;