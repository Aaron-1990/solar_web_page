# modules/analytics.py
class Analytics:
    """Módulo simplificado de analytics"""
    
    def track_calculation(self, result):
        # Por ahora solo imprime, después puedes integrar con servicios reales
        print(f"Calculation tracked: {result.get('numberOfPanels')} panels needed")
    
    def track_subscription(self, email, source):
        print(f"Subscription tracked: {email} from {source}")
    
    def track_partner_click(self, partner, product):
        print(f"Partner click tracked: {partner} - {product}")
        