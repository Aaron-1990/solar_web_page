from flask import Flask, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import json
import os
from config.settings import Config
from modules.calculator import SolarCalculator
from modules.partners import PartnerManager
from modules.analytics import Analytics
from modules.newsletter import NewsletterManager

# Inicialización de la aplicación
app = Flask(__name__)
app.config.from_object(Config)

# Inicialización de extensiones
db = SQLAlchemy(app)
mail = Mail(app)

# Inicialización de módulos personalizados
calculator = SolarCalculator()
partner_manager = PartnerManager()
analytics = Analytics()
newsletter_manager = NewsletterManager(db, mail)

# Modelos de base de datos actualizados
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), default='homepage')
    active = db.Column(db.Boolean, default=True)

class ClickTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    partner = db.Column(db.String(50), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    user_ip = db.Column(db.String(45))
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    referrer = db.Column(db.String(500))

class Calculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_consumption = db.Column(db.Float)
    location = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(100))
    panels_needed = db.Column(db.Integer)
    system_cost = db.Column(db.Float)
    annual_savings = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_ip = db.Column(db.String(45))
    
    # NUEVOS CAMPOS PARA PANELES
    panel_type = db.Column(db.String(20), default='500w')
    panel_power_w = db.Column(db.Integer, default=500)
    system_power_kw = db.Column(db.Float)
    roof_area_m2 = db.Column(db.Float)

class MarketplaceClick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(200))
    product_price = db.Column(db.Float)
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    referrer = db.Column(db.String(500))
    click_id = db.Column(db.String(100))
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_price': self.product_price,
            'clicked_at': self.clicked_at.isoformat()
        }


# RUTA PRINCIPAL ACTUALIZADA
@app.route('/')
def index():
    """Página principal con calculadora y todas las secciones - ACTUALIZADA"""
    try:
        partners_data = partner_manager.get_all_partners()
        locations = calculator.get_locations()
        vehicles = calculator.get_vehicles()
        panels = calculator.get_panel_options()  # NUEVO
        
        return render_template('index.html',
                             partners=partners_data,
                             locations=locations,
                             vehicles=vehicles,
                             panels=panels)  # NUEVO
    except Exception as e:
        app.logger.error(f"Error loading index page: {str(e)}")
        # Fallback sin paneles si hay error
        return render_template('index.html',
                             partners={},
                             locations=calculator.get_locations(),
                             vehicles=calculator.get_vehicles(),
                             panels=[])

@app.route('/api/calculate', methods=['POST'])
def calculate_solar():
    """API endpoint para cálculos solares - ACTUALIZADO con selección de paneles"""
    try:
        data = request.json
        
        # Extraer datos del request
        home_consumption = float(data.get('homeConsumption', 400))
        location = data.get('location')
        coverage = float(data.get('coverage', 100)) / 100
        vehicle_model = data.get('vehicleModel', '')
        daily_ev_km = float(data.get('dailyEvKm', 0))
        custom_battery = data.get('batteryCapacity')
        vehicle_efficiency = data.get('vehicleEfficiency')
        custom_vehicle_name = data.get('customVehicleName')
        panel_type = data.get('panelType', '500w')  # NUEVO PARÁMETRO
        
        # Validaciones básicas
        if not location:
            return jsonify({
                'success': False,
                'error': 'La ubicación es requerida'
            }), 400
        
        # Realizar cálculo con el nuevo parámetro
        result = calculator.calculate_integral(
            home_consumption=home_consumption,
            location=location,
            coverage=coverage,
            vehicle_model=vehicle_model,
            daily_ev_km=daily_ev_km,
            custom_battery=custom_battery,
            vehicle_efficiency=vehicle_efficiency,
            custom_vehicle_name=custom_vehicle_name,
            panel_type=panel_type  # NUEVO
        )
        
        # Guardar cálculo en base de datos con información de paneles
        calculation = Calculation(
            home_consumption=home_consumption,
            location=location,
            vehicle_model=vehicle_model or 'none',
            panels_needed=result['numberOfPanels'],
            system_cost=result['totalSystemCost'],
            annual_savings=result['totalAnnualSavings'],
            user_ip=request.remote_addr,
            # NUEVOS CAMPOS
            panel_type=panel_type,
            panel_power_w=result.get('panelPowerW'),
            system_power_kw=result.get('systemPowerKw'),
            roof_area_m2=result.get('totalRoofArea')
        )
        
        try:
            db.session.add(calculation)
            db.session.commit()
        except Exception as db_error:
            # Si falla el guardado en DB, continuar con el resultado
            app.logger.warning(f"Database save failed: {str(db_error)}")
            db.session.rollback()
        
        # Track analytics con información de paneles
        analytics.track_calculation(result)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ValueError as ve:
        app.logger.error(f"Validation error in calculation: {str(ve)}")
        return jsonify({
            'success': False,
            'error': str(ve)
        }), 400
    except Exception as e:
        app.logger.error(f"Error en cálculo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor. Por favor intenta de nuevo.'
        }), 500

# NUEVO ENDPOINT para obtener opciones de paneles
@app.route('/api/panels')
def get_panel_options():
    """Obtener opciones de paneles disponibles"""
    try:
        panels = calculator.get_panel_options()
        return jsonify({
            'success': True,
            'data': panels
        })
    except Exception as e:
        app.logger.error(f"Error getting panel options: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener opciones de paneles'
        }), 500

@app.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Suscripción al newsletter"""
    try:
        data = request.json
        email = data.get('email')
        source = data.get('source', 'homepage')
        
        # Validar email
        if not email or '@' not in email:
            return jsonify({
                'success': False,
                'message': 'Email inválido'
            }), 400
        
        # Verificar si ya existe
        existing = Subscriber.query.filter_by(email=email).first()
        if existing:
            if not existing.active:
                existing.active = True
                db.session.commit()
                newsletter_manager.send_welcome_email(email)
                return jsonify({
                    'success': True,
                    'message': 'Suscripción reactivada exitosamente'
                })
            return jsonify({
                'success': False,
                'message': 'Este email ya está suscrito'
            }), 400
        
        # Crear nueva suscripción
        subscriber = Subscriber(email=email, source=source)
        db.session.add(subscriber)
        db.session.commit()
        
        # Enviar email de bienvenida
        newsletter_manager.send_welcome_email(email)
        
        # Track analytics
        analytics.track_subscription(email, source)
        
        return jsonify({
            'success': True,
            'message': '¡Gracias por suscribirte! Revisa tu email.'
        })
        
    except Exception as e:
        app.logger.error(f"Error en suscripción: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al procesar la suscripción'
        }), 500

@app.route('/api/track/click', methods=['POST'])
def track_click():
    """Tracking de clicks en partners/productos"""
    try:
        data = request.json
        partner = data.get('partner')
        product = data.get('product')
        
        # Guardar click en base de datos
        click = ClickTracking(
            partner=partner,
            product=product,
            user_ip=request.remote_addr,
            referrer=request.referrer
        )
        db.session.add(click)
        db.session.commit()
        
        # Track analytics
        analytics.track_partner_click(partner, product)
        
        # Obtener URL de redirección
        redirect_url = partner_manager.get_redirect_url(partner, product)
        
        return jsonify({
            'success': True,
            'redirect_url': redirect_url
        })
        
    except Exception as e:
        app.logger.error(f"Error en tracking: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/partners/<section>')
def get_partners_by_section(section):
    """Obtener partners por sección"""
    try:
        partners = partner_manager.get_partners_by_section(section)
        return jsonify({
            'success': True,
            'data': partners
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/track/marketplace-click', methods=['POST'])
def track_marketplace_click():
    """Endpoint para tracking de clicks en marketplace"""
    try:
        data = request.json
        
        # Validaciones básicas
        required_fields = ['platform', 'product_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo requerido: {field}'
                }), 400
        
        # Crear registro de click
        marketplace_click = MarketplaceClick(
            platform=data.get('platform'),
            product_id=data.get('product_id'),
            product_name=data.get('product_name'),
            product_price=data.get('product_price'),
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            referrer=data.get('referrer', ''),
            click_id=data.get('click_id')
        )
        
        # Guardar en base de datos
        try:
            db.session.add(marketplace_click)
            db.session.commit()
            
            # Analytics
            analytics.track_marketplace_click(
                data.get('platform'),
                data.get('product_id'),
                data.get('product_name')
            )
            
            return jsonify({
                'success': True,
                'message': 'Click tracked successfully',
                'click_id': marketplace_click.id
            })
            
        except Exception as db_error:
            db.session.rollback()
            app.logger.error(f"Database error in marketplace tracking: {str(db_error)}")
            return jsonify({
                'success': False,
                'error': 'Error saving tracking data'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error en tracking marketplace: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/marketplace/stats')
def get_marketplace_stats():
    """Estadísticas del marketplace para dashboard"""
    try:
        # Stats básicas
        total_clicks = MarketplaceClick.query.count()
        
        # Clicks por plataforma
        platform_stats = db.session.query(
            MarketplaceClick.platform,
            db.func.count(MarketplaceClick.id).label('clicks')
        ).group_by(MarketplaceClick.platform).all()
        
        # Productos más clickeados
        popular_products = db.session.query(
            MarketplaceClick.platform,
            MarketplaceClick.product_id,
            MarketplaceClick.product_name,
            db.func.count(MarketplaceClick.id).label('clicks')
        ).group_by(
            MarketplaceClick.platform,
            MarketplaceClick.product_id,
            MarketplaceClick.product_name
        ).order_by(db.func.count(MarketplaceClick.id).desc()).limit(10).all()
        
        # Clicks por día (últimos 30 días)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        daily_clicks = db.session.query(
            db.func.date(MarketplaceClick.clicked_at).label('date'),
            db.func.count(MarketplaceClick.id).label('clicks')
        ).filter(
            MarketplaceClick.clicked_at >= thirty_days_ago
        ).group_by(
            db.func.date(MarketplaceClick.clicked_at)
        ).order_by('date').all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_clicks': total_clicks,
                'platform_stats': [
                    {'platform': stat.platform, 'clicks': stat.clicks}
                    for stat in platform_stats
                ],
                'popular_products': [
                    {
                        'platform': prod.platform,
                        'product_id': prod.product_id,
                        'product_name': prod.product_name,
                        'clicks': prod.clicks
                    }
                    for prod in popular_products
                ],
                'daily_clicks': [
                    {'date': str(day.date), 'clicks': day.clicks}
                    for day in daily_clicks
                ]
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting marketplace stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al obtener estadísticas'
        }), 500

# Panel de administración (básico)
@app.route('/admin')
def admin_dashboard():
    """Dashboard administrativo básico"""
    try:
        # Estadísticas básicas
        stats = {
            'total_calculations': Calculation.query.count(),
            'total_subscribers': Subscriber.query.filter_by(active=True).count(),
            'total_clicks': ClickTracking.query.count(),
        }
        
        # Cálculos recientes
        try:
            stats['recent_calculations'] = Calculation.query.order_by(
                Calculation.created_at.desc()
            ).limit(10).all()
        except:
            stats['recent_calculations'] = []
        
        # Partners populares
        try:
            stats['popular_partners'] = db.session.query(
                ClickTracking.partner,
                db.func.count(ClickTracking.id).label('clicks')
            ).group_by(ClickTracking.partner).order_by(
                db.func.count(ClickTracking.id).desc()
            ).limit(5).all()
        except:
            stats['popular_partners'] = []
        
        # Estadísticas de paneles
        try:
            stats['panel_stats'] = db.session.query(
                Calculation.panel_type,
                db.func.count(Calculation.id).label('count'),
                db.func.avg(Calculation.panels_needed).label('avg_panels')
            ).filter(Calculation.panel_type.isnot(None)).group_by(
                Calculation.panel_type
            ).all()
        except:
            stats['panel_stats'] = []
        
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {str(e)}")
        return jsonify({'error': 'Error loading dashboard'}), 500

# Agregar a app.py para comprobar a google propiedad del dominio.
# Agregar ANTES de if __name__ == '__main__':
@app.route('/google0ef2424a6acb9a1b.html')
def google_verification():
    """Verificación de Google Search Console"""
    return app.send_static_file('google0ef2424a6acb9a1b.html')

@app.route('/sitemap.xml')
def sitemap():
    """Servir sitemap.xml para SEO con headers correctos"""
    try:
        response = app.send_static_file('sitemap.xml')
        # ✅ CORRECCIÓN: Content-Type correcto para XML
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache por 1 hora
        response.headers['X-Robots-Tag'] = 'noindex'  # Evitar indexación del sitemap mismo
        return response
    except Exception as e:
        app.logger.error(f"Error serving sitemap: {e}")
        return "Sitemap not found", 404

# También verificar que la ruta de robots.txt tenga headers correctos:
@app.route('/robots.txt')
def robots_txt():
    """Servir robots.txt para SEO con headers correctos"""
    try:
        response = app.send_static_file('robots.txt')
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache por 24 horas
        return response
    except Exception as e:
        app.logger.error(f"Error serving robots.txt: {e}")
        return "robots.txt not found", 404

# Agregar en app.py después de la ruta del sitemap
@app.route('/robots.txt')
def robots_txt():
    """Servir robots.txt para SEO"""
    return app.send_static_file('robots.txt'), 200, {'Content-Type': 'text/plain'}

@app.route('/admin/marketplace')
def admin_marketplace_simple():
    """Vista simple de estadísticas de marketplace"""
    try:
        # Estadísticas básicas
        total_clicks = MarketplaceClick.query.count()
        
        # Top 3 productos
        top_products = db.session.query(
            MarketplaceClick.platform,
            MarketplaceClick.product_name,
            db.func.count(MarketplaceClick.id).label('clicks')
        ).group_by(
            MarketplaceClick.platform,
            MarketplaceClick.product_name
        ).order_by(
            db.func.count(MarketplaceClick.id).desc()
        ).limit(3).all()
        
        # JSON response simple para empezar
        return jsonify({
            'marketplace_stats': {
                'total_clicks': total_clicks,
                'top_products': [
                    {
                        'platform': p.platform,
                        'name': p.product_name,
                        'clicks': p.clicks
                    } for p in top_products
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Páginas informativas adicionales
@app.route('/guias/<slug>')
def guide_page(slug):
    """Páginas de guías y contenido educativo"""
    try:
        guide_content = partner_manager.get_guide_content(slug)
        if not guide_content:
            return render_template('errors/404.html'), 404
        
        return render_template('guides/guide.html', 
                             content=guide_content,
                             related_products=partner_manager.get_related_products(slug))
    except Exception as e:
        app.logger.error(f"Error loading guide {slug}: {str(e)}")
        return render_template('errors/404.html'), 404

@app.route('/comparador/<category>')
def comparison_tool(category):
    """Herramientas de comparación por categoría"""
    if category not in ['paneles', 'inversores', 'baterias', 'vehiculos']:
        return render_template('errors/404.html'), 404
    
    try:
        products = partner_manager.get_products_for_comparison(category)
        return render_template('tools/comparison.html',
                             category=category,
                             products=products)
    except Exception as e:
        app.logger.error(f"Error in comparison tool for {category}: {str(e)}")
        return render_template('tools/comparison.html',
                             category=category,
                             products=[])

# Manejo de errores
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# CLI Commands para inicialización
@app.cli.command()
def init_db():
    """Inicializar base de datos"""
    db.create_all()
    print("Base de datos inicializada exitosamente")

@app.cli.command()
def seed_partners():
    """Cargar datos iniciales de partners"""
    partner_manager.seed_initial_partners()
    print("Partners cargados exitosamente")

@app.cli.command()
def migrate_panels_db():
    """Migrar base de datos para agregar campos de paneles"""
    try:
        # Usar inspección más robusta
        inspector = db.inspect(db.engine)
        
        # Verificar si la tabla existe
        if not inspector.has_table('calculation'):
            print("⚠️ Tabla 'calculation' no existe. Ejecuta init_db primero.")
            return
            
        columns = [col['name'] for col in inspector.get_columns('calculation')]
        
        migrations = []
        
        if 'panel_type' not in columns:
            migrations.append("ALTER TABLE calculation ADD COLUMN panel_type VARCHAR(20) DEFAULT '500w'")
        
        if 'panel_power_w' not in columns:
            migrations.append('ALTER TABLE calculation ADD COLUMN panel_power_w INTEGER DEFAULT 500')
        
        if 'system_power_kw' not in columns:
            migrations.append('ALTER TABLE calculation ADD COLUMN system_power_kw FLOAT')
        
        if 'roof_area_m2' not in columns:
            migrations.append('ALTER TABLE calculation ADD COLUMN roof_area_m2 FLOAT')
        
        # Ejecutar migraciones
        for migration in migrations:
            try:
                db.engine.execute(migration)
                print(f"✅ Executed: {migration}")
            except Exception as e:
                print(f"⚠️ Migration already applied or error: {e}")
        
        if migrations:
            print(f"✅ Panel database migration completed ({len(migrations)} changes)")
        else:
            print("✅ Database already up to date")
            
    except Exception as e:
        print(f"❌ Error in migration: {e}")

@app.cli.command()
def migrate_marketplace_db():
    """Migrar base de datos para agregar tabla de marketplace"""
    try:
        # Crear tabla marketplace_click si no existe
        db.create_all()
        
        # Verificar que la tabla se creó correctamente
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        if 'marketplace_click' in inspector.get_table_names():
            print("✅ Tabla marketplace_click creada exitosamente")
        else:
            print("❌ Error: Tabla marketplace_click no se pudo crear")
            
        print("✅ Migración de marketplace completada")
        
    except Exception as e:
        print(f"❌ Error en migración de marketplace: {e}")

# Función auxiliar para generar productos de prueba
def seed_marketplace_products():
    """Generar productos de prueba para desarrollo"""
    test_products = [
        {
            'platform': 'amazon',
            'product_id': 'panel-400w',
            'product_name': 'Panel Solar 400W Monocristalino',
            'product_price': 4500.0
        },
        {
            'platform': 'mercadolibre',
            'product_id': 'kit-solar-5kw',
            'product_name': 'Kit Solar Completo 5kW Residencial',
            'product_price': 85000.0
        },
        {
            'platform': 'temu',
            'product_id': 'monitor-solar-wifi',
            'product_name': 'Monitor Solar WiFi Inteligente',
            'product_price': 850.0
        }
    ]
    
    for product in test_products:
        # Simular click para prueba
        test_click = MarketplaceClick(
            platform=product['platform'],
            product_id=product['product_id'],
            product_name=product['product_name'],
            product_price=product['product_price'],
            user_ip='127.0.0.1',
            user_agent='Test Agent',
            referrer='test',
            click_id=f"test_{product['product_id']}"
        )
        
        db.session.add(test_click)
    
    try:
        db.session.commit()
        print("✅ Productos de prueba agregados al marketplace")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error agregando productos de prueba: {e}")

# Comando CLI para sembrar datos de prueba
@app.cli.command()
def seed_marketplace():
    """Sembrar datos de prueba para marketplace"""
    seed_marketplace_products()



# VALIDACIÓN DE CONFIGURACIÓN AL INICIO
def validate_panel_configuration():
    """Validar que la configuración de paneles esté correcta"""
    try:
        panels = calculator.get_panel_options()
        
        if len(panels) == 0:
            print("⚠️ Warning: No panel options loaded")
            return False
        
        required_fields = ['value', 'name', 'power', 'area_m2', 'efficiency']
        for panel in panels:
            missing_fields = [field for field in required_fields if field not in panel]
            if missing_fields:
                print(f"❌ Panel {panel.get('value', 'unknown')} missing fields: {missing_fields}")
                return False
        
        print(f"✅ Panel configuration validated: {len(panels)} panels loaded")
        return True
        
    except Exception as e:
        print(f"❌ Panel configuration validation failed: {e}")
        return False

# Actualizar la clase Analytics para incluir marketplace
class Analytics:
    """Módulo de analytics actualizado con marketplace"""
    
    def track_calculation(self, result, panel_type=None):
        print(f"✅ Calculation tracked:")
        print(f"  • Panels: {result.get('numberOfPanels')} x {panel_type or 'unknown'}")
        print(f"  • System: {result.get('systemPowerKw')} kW")
        print(f"  • Investment: ${result.get('netCost'):,.2f}")
        print(f"  • Annual savings: ${result.get('totalAnnualSavings'):,.2f}")
    
    def track_subscription(self, email, source):
        print(f"📧 Subscription tracked: {email} from {source}")
    
    def track_partner_click(self, partner, product):
        print(f"🔗 Partner click tracked: {partner} - {product}")
    
    def track_marketplace_click(self, platform, product_id, product_name):
        """Nuevo: Tracking específico para marketplace"""
        print(f"🛒 Marketplace click tracked:")
        print(f"  • Platform: {platform}")
        print(f"  • Product: {product_name} ({product_id})")
        print(f"  • Timestamp: {datetime.utcnow().isoformat()}")


# INICIALIZACIÓN CON VALIDACIÓN
def initialize_app():
    """Inicializar la aplicación con validaciones"""
    with app.app_context():
        try:
            # Crear tablas
            db.create_all()
            print("✅ Base de datos inicializada")
            
            # Validar configuración de paneles
            if validate_panel_configuration():
                print("✅ Configuración de paneles válida")
            else:
                print("⚠️ Revisar configuración de paneles")
                
        except Exception as e:
            print(f"❌ Error durante la inicialización: {e}")

# Llamar inicialización
initialize_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)