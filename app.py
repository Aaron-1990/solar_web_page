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

# Modelos de base de datos
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

# Rutas principales
@app.route('/')
def index():
    """Página principal con calculadora y todas las secciones"""
    partners_data = partner_manager.get_all_partners()
    locations = calculator.get_locations()
    vehicles = calculator.get_vehicles()
    
    return render_template('index.html',
                         partners=partners_data,
                         locations=locations,
                         vehicles=vehicles)

@app.route('/api/calculate', methods=['POST'])
def calculate_solar():
    """API endpoint para cálculos solares"""
    try:
        data = request.json
        
        # Extraer datos del request
        home_consumption = float(data.get('homeConsumption', 400))
        location = data.get('location')
        coverage = float(data.get('coverage', 100)) / 100
        vehicle_model = data.get('vehicleModel', '')
        daily_ev_km = float(data.get('dailyEvKm', 0))
        custom_battery = data.get('batteryCapacity')
        
        # Realizar cálculo
        result = calculator.calculate_integral(
            home_consumption=home_consumption,
            location=location,
            coverage=coverage,
            vehicle_model=vehicle_model,
            daily_ev_km=daily_ev_km,
            custom_battery=custom_battery
        )
        
        # Guardar cálculo en base de datos
        calculation = Calculation(
            home_consumption=home_consumption,
            location=location,
            vehicle_model=vehicle_model or 'none',
            panels_needed=result['numberOfPanels'],
            system_cost=result['totalSystemCost'],
            annual_savings=result['totalAnnualSavings'],
            user_ip=request.remote_addr
        )
        db.session.add(calculation)
        db.session.commit()
        
        # Track analytics
        analytics.track_calculation(result)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        app.logger.error(f"Error en cálculo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

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
    # Aquí podrías agregar autenticación
    stats = {
        'total_calculations': Calculation.query.count(),
        'total_subscribers': Subscriber.query.filter_by(active=True).count(),
        'total_clicks': ClickTracking.query.count(),
        'recent_calculations': Calculation.query.order_by(
            Calculation.created_at.desc()
        ).limit(10).all(),
        'popular_partners': db.session.query(
            ClickTracking.partner,
            db.func.count(ClickTracking.id).label('clicks')
        ).group_by(ClickTracking.partner).order_by(
            db.func.count(ClickTracking.id).desc()
        ).limit(5).all()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

# Páginas informativas adicionales
@app.route('/guias/<slug>')
def guide_page(slug):
    """Páginas de guías y contenido educativo"""
    # Cargar contenido de guías desde archivos o base de datos
    guide_content = partner_manager.get_guide_content(slug)
    if not guide_content:
        return render_template('errors/404.html'), 404
    
    return render_template('guides/guide.html', 
                         content=guide_content,
                         related_products=partner_manager.get_related_products(slug))

@app.route('/comparador/<category>')
def comparison_tool(category):
    """Herramientas de comparación por categoría"""
    if category not in ['paneles', 'inversores', 'baterias', 'vehiculos']:
        return render_template('404.html'), 404
    
    products = partner_manager.get_products_for_comparison(category)
    return render_template('tools/comparison.html',
                         category=category,
                         products=products)

# Manejo de errores
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

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

with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

