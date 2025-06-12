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

# ACTUALIZACIÓN DEL MÓDULO DE ANALYTICS
class Analytics:
    """Módulo de analytics actualizado con información de paneles"""
    
    def track_calculation(self, result, panel_type=None):  # AGREGADO panel_type=None
        # Tracking mejorado con información de paneles
        print(f"✅ Calculation tracked:")
        print(f"  • Panels: {result.get('numberOfPanels')} x {panel_type or 'unknown'}")
        print(f"  • System: {result.get('systemPowerKw')} kW")
        print(f"  • Investment: ${result.get('netCost'):,.2f}")
        print(f"  • Annual savings: ${result.get('totalAnnualSavings'):,.2f}")
        
        # Aquí puedes integrar con servicios reales
        # Ejemplo para enviar a webhook o servicio externo:
        """
        tracking_data = {
            'event': 'solar_calculation_completed',
            'panel_type': panel_type,
            'panels_needed': result.get('numberOfPanels'),
            'system_power_kw': result.get('systemPowerKw'),
            'investment_amount': result.get('netCost'),
            'annual_savings': result.get('totalAnnualSavings'),
            'timestamp': datetime.utcnow().isoformat()
        }
        """
    
    def track_subscription(self, email, source):
        print(f"📧 Subscription tracked: {email} from {source}")
    
    def track_partner_click(self, partner, product):
        print(f"🔗 Partner click tracked: {partner} - {product}")

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