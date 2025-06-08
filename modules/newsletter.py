# modules/newsletter.py
from flask_mail import Message

class NewsletterManager:
    """Gestor simplificado de newsletter"""
    
    def __init__(self, db, mail):
        self.db = db
        self.mail = mail
    
    def send_welcome_email(self, email):
        """Enviar email de bienvenida"""
        try:
            msg = Message(
                subject="¡Bienvenido a EnergiaSolar360!",
                recipients=[email],
                body="""
                ¡Gracias por suscribirte a nuestro newsletter!
                
                Recibirás:
                - Guías exclusivas sobre energía solar
                - Ofertas especiales de nuestros partners
                - Calculadoras avanzadas
                - Tips de ahorro energético
                
                ¡Bienvenido a la revolución solar!
                
                Equipo EnergiaSolar360
                """
            )
            # Comentado para evitar errores si no hay servidor de email configurado
            # self.mail.send(msg)
            print(f"Welcome email would be sent to: {email}")
        except Exception as e:
            print(f"Error sending email: {e}")
