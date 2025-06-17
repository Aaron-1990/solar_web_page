# modules/newsletter.py
from flask_mail import Message

class NewsletterManager:
    """Gestor de newsletter Nova Solar MX"""
    
    def __init__(self, db, mail):
        self.db = db
        self.mail = mail
    
    def send_welcome_email(self, email):
        """Enviar email de bienvenida Nova Solar MX"""
        try:
            msg = Message(
                subject="¡Bienvenido a Nova Solar MX! 🌞",
                recipients=[email],
                body="""
                ¡Gracias por unirte a la revolución solar con Nova Solar MX!
                
                Como miembro de nuestra comunidad, tendrás acceso a:
                
                🔧 HERRAMIENTAS EXCLUSIVAS:
                • Calculadora solar avanzada con selección de paneles
                • Comparador de equipos premium
                • Simulador de ahorros con vehículos eléctricos
                
                💰 BENEFICIOS ESPECIALES:
                • 10% de descuento en tu primera compra
                • Acceso anticipado a ofertas flash
                • Precios preferenciales con nuestros partners
                
                📚 CONTENIDO PREMIUM:
                • Guías técnicas de instalación
                • Webinars con expertos en energía solar
                • Análisis de mercado y tendencias
                
                🎯 SOPORTE ESPECIALIZADO:
                • Consultoría técnica gratuita
                • Asesoría en trámites gubernamentales
                • Conexión con instaladores certificados
                
                ¿Listo para comenzar tu transición energética?
                Visita: https://novasolarmx.com
                
                ¡Bienvenido al futuro de la energía!
                
                Equipo Nova Solar MX
                📧 mxnovasun@outlook.com
                🌐 novasolarmx.com
                
                ---
                Este email fue enviado porque te suscribiste a nuestro newsletter.
                Si no deseas recibir más emails, puedes darte de baja aquí.
                """
            )
            # Comentado para evitar errores si no hay servidor de email configurado
            # self.mail.send(msg)
            print(f"✅ Welcome email would be sent to: {email}")
            print(f"📧 From: Nova Solar MX <mxnovasun@outlook.com>")
        except Exception as e:
            print(f"❌ Error sending welcome email: {e}")
    
    def send_calculation_follow_up(self, email, calculation_data):
        """Enviar seguimiento después de usar la calculadora"""
        try:
            panels_needed = calculation_data.get('numberOfPanels', 'N/A')
            system_power = calculation_data.get('systemPowerKw', 'N/A')
            annual_savings = calculation_data.get('totalAnnualSavings', 'N/A')
            
            msg = Message(
                subject=f"Tu Sistema Solar de {system_power}kW está listo - Nova Solar MX",
                recipients=[email],
                body=f"""
                ¡Hola! Acabas de usar nuestra calculadora solar.
                
                📊 RESUMEN DE TU CÁLCULO:
                • Paneles necesarios: {panels_needed}
                • Potencia del sistema: {system_power} kW
                • Ahorro anual estimado: ${annual_savings:,.2f} MXN
                
                🚀 PRÓXIMOS PASOS:
                1. Solicita una cotización gratuita
                2. Conecta con instaladores certificados
                3. Aprovecha los incentivos gubernamentales
                
                💡 ¿NECESITAS AYUDA?
                Responde a este email o contáctanos:
                📧 mxnovasun@outlook.com
                🌐 novasolarmx.com
                
                ¡Hagamos realidad tu sistema solar!
                
                Equipo Nova Solar MX
                """
            )
            # self.mail.send(msg)
            print(f"✅ Follow-up email would be sent to: {email}")
        except Exception as e:
            print(f"❌ Error sending follow-up email: {e}")
    
    def send_partner_notification(self, partner_email, lead_data):
        """Notificar a partners sobre nuevos leads"""
        try:
            msg = Message(
                subject="Nuevo Lead Cualificado - Nova Solar MX",
                recipients=[partner_email],
                body=f"""
                Nuevo cliente potencial desde Nova Solar MX:
                
                INFORMACIÓN DEL LEAD:
                • Email: {lead_data.get('email')}
                • Sistema calculado: {lead_data.get('systemPowerKw')} kW
                • Paneles: {lead_data.get('numberOfPanels')}
                • Ubicación: {lead_data.get('location')}
                • Ahorro estimado: ${lead_data.get('totalAnnualSavings'):,.2f}/año
                
                SIGUIENTE ACCIÓN:
                Contactar al cliente en las próximas 24 horas.
                
                Nova Solar MX Partner Network
                """
            )
            # self.mail.send(msg)
            print(f"✅ Partner notification sent for lead: {lead_data.get('email')}")
        except Exception as e:
            print(f"❌ Error sending partner notification: {e}")