import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

class PartnerManager:
    """
    Gestión centralizada de partners, afiliados y productos
    """
    
    def __init__(self):
        self.partners_data = self._load_partners_config()
        self.tracking_urls = {}
        self._build_tracking_urls()
    
    def _load_partners_config(self) -> Dict:
        """Cargar configuración de partners desde JSON"""
        partners_path = os.path.join('config', 'partners.json')
        try:
            with open(partners_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Retornar estructura vacía si no existe
            return {
                "equipamiento": {},
                "electrodomesticos": {},
                "capacitacion": {}
            }
    
    def _build_tracking_urls(self):
        """Construir URLs de tracking para todos los productos"""
        for section, categories in self.partners_data.items():
            for category, partners in categories.items():
                for partner in partners:
                    partner_id = partner.get('id')
                    base_url = partner.get('base_url', '')
                    
                    for product in partner.get('products', []):
                        product_id = product.get('id')
                        key = f"{partner_id}-{product_id}"
                        
                        # Construir URL según el tipo de partner
                        if partner_id == 'amazon':
                            # URLs de Amazon con tag de afiliado
                            affiliate_tag = partner.get('affiliate_tag', 'energiasol-20')
                            search_terms = product.get('search_terms', '')
                            self.tracking_urls[key] = f"{base_url}s?k={search_terms}&tag={affiliate_tag}"
                        
                        elif partner_id == 'hotmart':
                            # URLs de Hotmart con ID de producto
                            hotmart_id = product.get('hotmart_id', '')
                            self.tracking_urls[key] = f"https://pay.hotmart.com//{hotmart_id}?checkoutMode=10"
                        
                        else:
                            # URLs genéricas con parámetros de tracking
                            url_suffix = product.get('url_suffix', '')
                            tracking_params = partner.get('tracking_params', '')
                            self.tracking_urls[key] = f"{base_url}{url_suffix}{tracking_params}"
    
    def get_all_partners(self) -> Dict:
        """Obtener todos los partners organizados por sección"""
        return self.partners_data
    
    def get_partners_by_section(self, section: str) -> Dict:
        """Obtener partners de una sección específica"""
        return self.partners_data.get(section, {})
    
    def get_partner_products(self, section: str, category: str, partner_id: str) -> List[Dict]:
        """Obtener productos de un partner específico"""
        try:
            partners = self.partners_data.get(section, {}).get(category, [])
            for partner in partners:
                if partner.get('id') == partner_id:
                    return partner.get('products', [])
            return []
        except:
            return []
    
    def get_redirect_url(self, partner_id: str, product_id: str) -> str:
        """Obtener URL de redirección con tracking"""
        key = f"{partner_id}-{product_id}"
        return self.tracking_urls.get(key, '#')
    
    def get_products_for_comparison(self, category: str) -> List[Dict]:
        """
        Obtener productos para herramienta de comparación
        
        Args:
            category: Categoría a comparar (paneles, inversores, baterias, vehiculos)
            
        Returns:
            Lista de productos con especificaciones para comparar
        """
        products = []
        
        if category == 'paneles':
            # Agregar paneles de diferentes partners
            equipment_partners = self.partners_data.get('equipamiento', {})
            for cat_partners in equipment_partners.values():
                for partner in cat_partners:
                    for product in partner.get('products', []):
                        if 'panel' in product.get('name', '').lower():
                            products.append({
                                'name': product['name'],
                                'partner': partner['name'],
                                'price': product.get('price', 0),
                                'power': self._extract_panel_power(product['name']),
                                'warranty': self._extract_warranty(product.get('features', [])),
                                'efficiency': self._estimate_efficiency(product),
                                'url': self.get_redirect_url(partner['id'], product['id'])
                            })
        
        elif category == 'vehiculos':
            # Agregar vehículos de la configuración
            from modules.calculator import SolarCalculator
            calc = SolarCalculator()
            for vehicle_id, vehicle_data in calc.vehicles.items():
                products.append({
                    'name': vehicle_data['name'],
                    'type': vehicle_data['type'],
                    'battery': vehicle_data['battery'],
                    'efficiency': vehicle_data['efficiency'],
                    'electric_range': vehicle_data.get('electric_range', 0),
                    'price_estimate': self._estimate_vehicle_price(vehicle_data)
                })
        
        return products
    
    def _extract_panel_power(self, name: str) -> int:
        """Extraer potencia del panel del nombre"""
        import re
        match = re.search(r'(\d+)[Ww]', name)
        return int(match.group(1)) if match else 0
    
    def _extract_warranty(self, features: List[str]) -> int:
        """Extraer años de garantía de las características"""
        for feature in features:
            if 'garantía' in feature.lower():
                import re
                match = re.search(r'(\d+)\s*año', feature)
                if match:
                    return int(match.group(1))
        return 10  # Valor por defecto
    
    def _estimate_efficiency(self, product: Dict) -> float:
        """Estimar eficiencia del panel"""
        # Estimación basada en tecnología actual
        power = self._extract_panel_power(product.get('name', ''))
        if power >= 450:
            return 21.5
        elif power >= 400:
            return 20.5
        else:
            return 19.5
    
    def _estimate_vehicle_price(self, vehicle_data: Dict) -> int:
        """Estimar precio del vehículo"""
        # Estimaciones basadas en el mercado mexicano
        if vehicle_data['type'] == 'ev':
            if vehicle_data['battery'] > 50:
                return 1200000  # Tesla Model 3
            else:
                return 800000   # Nissan Leaf
        else:  # PHEV
            if vehicle_data['battery'] > 15:
                return 1000000  # Outlander PHEV
            else:
                return 650000   # BYD King
    
    def get_guide_content(self, slug: str) -> Optional[Dict]:
        """
        Obtener contenido de guías educativas
        
        Args:
            slug: Identificador de la guía
            
        Returns:
            Contenido de la guía o None si no existe
        """
        guides = {
            'como-calcular-paneles-solares': {
                'title': 'Cómo Calcular Cuántos Paneles Solares Necesitas',
                'description': 'Guía completa para dimensionar tu sistema solar',
                'content': """
                    <h2>Paso 1: Analiza tu consumo eléctrico</h2>
                    <p>Revisa tus recibos de CFE de los últimos 12 meses...</p>
                    
                    <h2>Paso 2: Considera tu ubicación</h2>
                    <p>Las horas de sol pico (HSP) varían según tu estado...</p>
                    
                    <h2>Paso 3: Calcula la potencia necesaria</h2>
                    <p>Usa nuestra calculadora o la fórmula: Potencia = Consumo diario / (HSP × 0.8)</p>
                """,
                'related_category': 'equipamiento'
            },
            'beneficios-vehiculo-electrico': {
                'title': 'Beneficios de Combinar Paneles Solares con Vehículo Eléctrico',
                'description': 'Maximiza tu ahorro con la sinergia perfecta',
                'content': """
                    <h2>Ahorro doble</h2>
                    <p>Al cargar tu vehículo con energía solar, eliminas gastos de gasolina...</p>
                    
                    <h2>Independencia energética</h2>
                    <p>No dependes de gasolineras ni de aumentos en tarifas eléctricas...</p>
                """,
                'related_category': 'electrodomesticos'
            }
        }
        
        return guides.get(slug)
    
    def get_related_products(self, guide_slug: str) -> List[Dict]:
        """Obtener productos relacionados con una guía"""
        guide = self.get_guide_content(guide_slug)
        if not guide:
            return []
        
        related_category = guide.get('related_category', 'equipamiento')
        products = []
        
        # Obtener productos de la categoría relacionada
        category_data = self.partners_data.get(related_category, {})
        for partners in category_data.values():
            for partner in partners[:2]:  # Limitar a 2 partners
                for product in partner.get('products', [])[:1]:  # 1 producto por partner
                    products.append({
                        'name': product['name'],
                        'partner': partner['name'],
                        'price': product.get('price', product.get('price_from', 0)),
                        'url': self.get_redirect_url(partner['id'], product['id'])
                    })
        
        return products
    
    def seed_initial_partners(self):
        """Cargar datos iniciales de partners en la base de datos si es necesario"""
        # Esta función puede ser expandida para cargar datos en la BD
        # Por ahora solo valida que el archivo JSON existe
        if not os.path.exists(os.path.join('config', 'partners.json')):
            # Crear archivo con datos iniciales
            initial_data = {
                "equipamiento": {
                    "premium": [
                        {
                            "id": "labodegasolar",
                            "name": "La Bodega Solar",
                            "commission": 0.08,
                            "base_url": "https://www.labodegasolar.com/",
                            "tracking_params": "?ref=energiasolar360",
                            "products": []
                        }
                    ]
                },
                "electrodomesticos": {},
                "capacitacion": {}
            }
            
            os.makedirs('config', exist_ok=True)
            with open(os.path.join('config', 'partners.json'), 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            
            print("Archivo de partners creado con datos iniciales")
    
    def update_partner_products(self, section: str, category: str, 
                               partner_id: str, products: List[Dict]):
        """
        Actualizar productos de un partner
        
        Args:
            section: Sección (equipamiento, electrodomesticos, capacitacion)
            category: Categoría dentro de la sección
            partner_id: ID del partner
            products: Lista de productos actualizados
        """
        if section not in self.partners_data:
            self.partners_data[section] = {}
        
        if category not in self.partners_data[section]:
            self.partners_data[section][category] = []
        
        # Buscar y actualizar partner
        partners = self.partners_data[section][category]
        partner_found = False
        
        for i, partner in enumerate(partners):
            if partner.get('id') == partner_id:
                partners[i]['products'] = products
                partner_found = True
                break
        
        if not partner_found:
            raise ValueError(f"Partner {partner_id} no encontrado en {section}/{category}")
        
        # Guardar cambios
        self._save_partners_config()
        
        # Reconstruir URLs de tracking
        self._build_tracking_urls()
    
    def _save_partners_config(self):
        """Guardar configuración de partners en JSON"""
        partners_path = os.path.join('config', 'partners.json')
        with open(partners_path, 'w', encoding='utf-8') as f:
            json.dump(self.partners_data, f, indent=2, ensure_ascii=False)
    
    def get_commission_rate(self, partner_id: str) -> float:
        """Obtener tasa de comisión de un partner"""
        for section in self.partners_data.values():
            for category in section.values():
                for partner in category:
                    if partner.get('id') == partner_id:
                        return partner.get('commission', 0.0)
        return 0.0
    
    def generate_affiliate_link(self, partner_id: str, product_id: str, 
                               source: str = 'web') -> str:
        """
        Generar link de afiliado con tracking adicional
        
        Args:
            partner_id: ID del partner
            product_id: ID del producto
            source: Fuente del click (web, email, social)
        """
        base_url = self.get_redirect_url(partner_id, product_id)
        
        # Agregar parámetros adicionales de tracking
        separator = '&' if '?' in base_url else '?'
        tracking_params = f"{separator}utm_source=energiasolar360&utm_medium={source}"
        
        # Generar ID único para tracking
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = hashlib.md5(f"{partner_id}{product_id}{timestamp}".encode()).hexdigest()[:8]
        tracking_params += f"&click_id={unique_id}"
        
        return base_url + tracking_params

