/**
 * ========================================
 * MARKETPLACE JAVASCRIPT FUNCTIONS
 * marketplace.js - Funcionalidad para tracking y gestión de productos
 * ========================================
 */

// Configuración del marketplace
const MarketplaceConfig = {
    // URLs base para cada plataforma
    platforms: {
        amazon: {
            name: 'Amazon México',
            baseUrl: 'https://amazon.com.mx',
            affiliateTag: 'sundepot-20',
            trackingParams: '?tag=sundepot-20&linkCode=ur2&linkId=',
            commission: '3-8%'
        },
        mercadolibre: {
            name: 'MercadoLibre',
            baseUrl: 'https://mercadolibre.com.mx',
            affiliateProgram: 'ml_affiliates',
            trackingParams: '?pdp_filters=category:',
            commission: '4-12%'
        },
        temu: {
            name: 'Temu',
            baseUrl: 'https://temu.com',
            affiliateProgram: 'temu_affiliate',
            trackingParams: '?_bg_fs=1&_p_jump=1&_x_sessn_id=',
            commission: '5-15%'
        },
        aliexpress: {
            name: 'AliExpress',
            baseUrl: 'https://aliexpress.com',
            affiliateProgram: 'portals_ali',
            trackingParams: '?aff_fcid=',
            commission: '5-20%'
        }
    },
    
    // Productos estáticos para Fase 1
    products: {
        amazon: {
            'panel-400w': {
                url: '/dp/B08XYZ123',
                name: 'Panel Solar 400W Monocristalino',
                price: 4500
            },
            'inversor-3000w': {
                url: '/dp/B08ABC456',
                name: 'Inversor Solar 3000W Onda Pura',
                price: 8950
            },
            'bateria-litio-100ah': {
                url: '/dp/B08DEF789',
                name: 'Batería Litio 100Ah Solar',
                price: 12500
            }
        },
        mercadolibre: {
            'kit-solar-5kw': {
                url: '/MLM-123456789-kit-solar-completo-5kw',
                name: 'Kit Solar Completo 5kW Residencial',
                price: 85000
            },
            'regulador-mppt-60a': {
                url: '/MLM-987654321-regulador-mppt-60a',
                name: 'Regulador MPPT 60A Solar',
                price: 2850
            },
            'estructura-4-paneles': {
                url: '/MLM-456789123-estructura-aluminio',
                name: 'Estructura Aluminio 4 Paneles',
                price: 3200
            }
        },
        temu: {
            'monitor-solar-wifi': {
                url: '/goods.html?_bg_fs=1&goods_id=601099512',
                name: 'Monitor Solar WiFi Inteligente',
                price: 850
            },
            'medidor-consumo-wifi': {
                url: '/goods.html?_bg_fs=1&goods_id=601099513',
                name: 'Medidor de Consumo Eléctrico WiFi',
                price: 450
            }
        },
        aliexpress: {
            'kit-herramientas-25pz': {
                url: '/item/4000123456789.html',
                name: 'Kit Herramientas Instalación Solar',
                price: 1250
            }
        }
    }
};

/**
 * Función principal para tracking de clicks en marketplace
 * @param {string} platform - Plataforma (amazon, mercadolibre, temu, aliexpress)
 * @param {string} productId - ID del producto
 */
async function trackMarketplaceClick(platform, productId) {
    console.log(`🛒 Tracking click: ${platform} - ${productId}`);
    
    try {
        // 1. Validar parámetros
        if (!MarketplaceConfig.platforms[platform]) {
            console.error(`❌ Plataforma no válida: ${platform}`);
            return;
        }
        
        if (!MarketplaceConfig.products[platform] || !MarketplaceConfig.products[platform][productId]) {
            console.error(`❌ Producto no encontrado: ${platform}/${productId}`);
            return;
        }
        
        // 2. Mostrar loading en el botón
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Redirigiendo...';
        button.classList.add('loading');
        button.disabled = true;
        
        // 3. Construir URL de destino
        const product = MarketplaceConfig.products[platform][productId];
        const platformConfig = MarketplaceConfig.platforms[platform];
        const destinationUrl = buildAffiliateUrl(platform, product.url, productId);
        
        // 4. Enviar tracking al backend
        const trackingData = {
            platform: platform,
            product_id: productId,
            product_name: product.name,
            product_price: product.price,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent,
            referrer: window.location.href
        };
        
        // Enviar tracking (no bloquear si falla)
        try {
            await sendTrackingData(trackingData);
        } catch (trackingError) {
            console.warn('⚠️ Tracking falló, pero continuando con redirección:', trackingError);
        }
        
        // 5. Analytics externos
        trackExternalAnalytics(platform, productId, product);
        
        // 6. Pequeño delay para UX y luego redirigir
        setTimeout(() => {
            console.log(`🔗 Redirigiendo a: ${destinationUrl}`);
            window.open(destinationUrl, '_blank', 'noopener,noreferrer');
            
            // Restaurar botón
            button.textContent = originalText;
            button.classList.remove('loading');
            button.disabled = false;
        }, 800);
        
    } catch (error) {
        console.error('❌ Error en trackMarketplaceClick:', error);
        
        // Fallback: redirigir de cualquier manera
        const fallbackUrl = `https://${platform}.com`;
        window.open(fallbackUrl, '_blank');
        
        // Restaurar botón en caso de error
        if (event.target) {
            event.target.textContent = event.target.dataset.originalText || 'Ver Producto';
            event.target.classList.remove('loading');
            event.target.disabled = false;
        }
    }
}

/**
 * Construir URL de afiliado con parámetros de tracking
 * @param {string} platform - Plataforma
 * @param {string} productPath - Path del producto
 * @param {string} productId - ID del producto para tracking
 * @returns {string} URL completa con afiliación
 */
function buildAffiliateUrl(platform, productPath, productId) {
    const config = MarketplaceConfig.platforms[platform];
    const baseUrl = config.baseUrl;
    
    // Generar ID único para tracking
    const clickId = generateClickId(platform, productId);
    
    switch (platform) {
        case 'amazon':
            return `${baseUrl}${productPath}${config.trackingParams}${clickId}&utm_source=sundepot&utm_medium=affiliate&utm_campaign=solar_calc`;
            
        case 'mercadolibre':
            return `${baseUrl}${productPath}${config.trackingParams}&utm_source=sundepot&click_id=${clickId}`;
            
        case 'temu':
            return `${baseUrl}${productPath}${config.trackingParams}${clickId}&utm_source=sundepot`;
            
        case 'aliexpress':
            return `${baseUrl}${productPath}${config.trackingParams}${clickId}&utm_source=sundepot&utm_medium=affiliate`;
            
        default:
            return `${baseUrl}${productPath}`;
    }
}

/**
 * Generar ID único para tracking de clicks
 * @param {string} platform - Plataforma
 * @param {string} productId - ID del producto
 * @returns {string} ID único
 */
function generateClickId(platform, productId) {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `${platform}_${productId}_${timestamp}_${random}`;
}

/**
 * Enviar datos de tracking al backend
 * @param {Object} trackingData - Datos del tracking
 */
async function sendTrackingData(trackingData) {
    const response = await fetch('/api/track/marketplace-click', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(trackingData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('✅ Tracking enviado:', result);
    return result;
}

/**
 * Tracking en analytics externos
 * @param {string} platform - Plataforma
 * @param {string} productId - ID del producto
 * @param {Object} product - Datos del producto
 */
function trackExternalAnalytics(platform, productId, product) {
    // Google Analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'marketplace_click', {
            'event_category': 'affiliate',
            'event_label': `${platform}_${productId}`,
            'value': product.price,
            'custom_parameters': {
                'platform': platform,
                'product_name': product.name,
                'product_price': product.price
            }
        });
        
        // Evento de conversión de afiliado
        gtag('event', 'affiliate_click', {
            'event_category': 'monetization',
            'event_label': platform,
            'value': product.price
        });
    }
    
    // Facebook Pixel
    if (typeof fbq !== 'undefined') {
        fbq('track', 'ViewContent', {
            content_name: product.name,
            content_category: platform,
            content_type: 'product',
            value: product.price,
            currency: 'MXN'
        });
        
        // Evento personalizado para afiliados
        fbq('trackCustom', 'AffiliateClick', {
            platform: platform,
            product_id: productId,
            value: product.price
        });
    }
    
    console.log(`📊 Analytics tracked: ${platform} - ${product.name}`);
}

/**
 * Inicializar marketplace
 */
function initMarketplace() {
    console.log('🛒 Inicializando marketplace...');
    
    // Guardar texto original de botones para restaurar en caso de error
    document.querySelectorAll('.cta-button').forEach(button => {
        button.dataset.originalText = button.textContent;
    });
    
    // Lazy loading de imágenes de productos
    initProductImageLazyLoading();
    
    // Event listeners para interacciones adicionales
    initMarketplaceEventListeners();
    
    console.log('✅ Marketplace inicializado');
}

/**
 * Lazy loading para imágenes de productos
 */
function initProductImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.1
        });
        
        document.querySelectorAll('.product-img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

/**
 * Event listeners adicionales para marketplace
 */
function initMarketplaceEventListeners() {
    // Hover effects en tarjetas de productos
    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            if (!this.classList.contains('loading')) {
                this.style.transform = 'translateY(0)';
            }
        });
    });
    
    // Tracking de vistas de productos (viewport)
    initProductViewTracking();
}

/**
 * Tracking de vistas de productos
 */
function initProductViewTracking() {
    if ('IntersectionObserver' in window) {
        const viewObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const card = entry.target;
                    const platform = card.dataset.platform;
                    const productId = card.dataset.productId;
                    
                    if (platform && productId) {
                        // Track view
                        if (typeof gtag !== 'undefined') {
                            gtag('event', 'product_view', {
                                'event_category': 'marketplace',
                                'event_label': `${platform}_${productId}`
                            });
                        }
                        
                        // Solo trackear una vez
                        viewObserver.unobserve(card);
                    }
                }
            });
        }, {
            threshold: 0.5,
            rootMargin: '0px'
        });
        
        document.querySelectorAll('.product-card').forEach(card => {
            viewObserver.observe(card);
        });
    }
}

/**
 * Función para mostrar/ocultar productos por categoría (para futuras fases)
 * @param {string} category - Categoría a filtrar
 */
function filterProductsByCategory(category) {
    const allProducts = document.querySelectorAll('.product-card');
    
    allProducts.forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'filter_products', {
            'event_category': 'marketplace',
            'event_label': category
        });
    }
}

/**
 * Función para mostrar estadísticas de marketplace (para dashboard)
 */
function getMarketplaceStats() {
    return {
        totalProducts: Object.keys(MarketplaceConfig.products).reduce((total, platform) => {
            return total + Object.keys(MarketplaceConfig.products[platform]).length;
        }, 0),
        platforms: Object.keys(MarketplaceConfig.platforms).length,
        avgCommission: '8%', // Calculado basado en rangos
        topPlatform: 'amazon' // Placeholder
    };
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMarketplace);
} else {
    initMarketplace();
}

// Exportar funciones para uso global
window.trackMarketplaceClick = trackMarketplaceClick;
window.filterProductsByCategory = filterProductsByCategory;
window.MarketplaceConfig = MarketplaceConfig;