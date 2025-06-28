import json
import os
from typing import Dict, Optional, List, Tuple
import math

class SolarCalculator:
    """
    Módulo para realizar todos los cálculos relacionados con sistemas solares
    incluyendo consumo del hogar y vehículos eléctricos/híbridos
    MODIFICADO: Soporte para diferentes potencias de paneles solares
    """
    
    def __init__(self):
        # Cargar datos de configuración
        self.locations = self._load_locations()
        self.vehicles = self._load_vehicles()
        self.panel_options = self._load_panel_options()  # NUEVO
        
        # Constantes del sistema
        self.SYSTEM_LOSSES = 0.20  # 20% pérdidas del sistema
        # REMOVIDO: self.PANEL_POWER_W = 450  # Ahora es variable según selección
        self.PANEL_AREA_M2 = 2.3  # Área por panel en m² (promedio, ahora variable)
        self.COST_PER_KW_INSTALLED = 25000  # Costo por kW instalado en MXN
        self.SENER_INCENTIVE_RATE = 0.25  # 25% de incentivo SENER
        self.CFE_RATE_PER_KWH = 3.5  # Tarifa promedio CFE
        self.GAS_PRICE_PER_LITER = 24  # Precio promedio gasolina
        self.CO2_PER_KWH = 0.493  # kg CO2 por kWh
        self.CO2_PER_LITER_GAS = 2.3  # kg CO2 por litro gasolina
        
    def _load_locations(self) -> Dict:
        """Cargar ubicaciones y sus valores HSP desde archivo JSON"""
        locations_path = os.path.join('config', 'locations.json')
        try:
            with open(locations_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Valores por defecto si no existe el archivo
            return {
                "bc-norte": {"name": "Baja California Norte", "hsp": 6.0, "region": "norte"},
                "sonora": {"name": "Sonora", "hsp": 6.2, "region": "norte"},
                "nuevo-leon": {"name": "Nuevo León", "hsp": 5.2, "region": "noreste"},
                "cdmx": {"name": "Ciudad de México", "hsp": 5.1, "region": "centro"},
                "jalisco": {"name": "Jalisco", "hsp": 5.8, "region": "occidente"},
                "queretaro": {"name": "Querétaro", "hsp": 5.6, "region": "centro"},
                "puebla": {"name": "Puebla", "hsp": 5.2, "region": "centro"},
                "yucatan": {"name": "Yucatán", "hsp": 6.0, "region": "sureste"}
            }
    
    def _load_vehicles(self) -> Dict:
        """Cargar especificaciones de vehículos desde archivo JSON"""
        vehicles_path = os.path.join('config', 'vehicles.json')
        try:
            with open(vehicles_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Valores por defecto si no existe el archivo
            return {
                "byd-king-dm-i-8.3": {
                    "name": "BYD King DM-i (8.3 kWh)",
                    "battery": 8.3,
                    "efficiency": 11.4,
                    "type": "phev",
                    "electric_range": 60
                },
                "mitsubishi-outlander": {
                    "name": "Mitsubishi Outlander PHEV",
                    "battery": 20,
                    "efficiency": 45.4,
                    "type": "phev",
                    "electric_range": 54
                },
                "mg-ehs": {
                    "name": "MG eHS PHEV",
                    "battery": 16.6,
                    "efficiency": 6.06,
                    "type": "phev",
                    "electric_range": 52
                },
                "tesla-model-3": {
                    "name": "Tesla Model 3",
                    "battery": 57.5,
                    "efficiency": 15,
                    "type": "ev",
                    "electric_range": 380
                },
                "nissan-leaf": {
                    "name": "Nissan LEAF",
                    "battery": 40,
                    "efficiency": 18,
                    "type": "ev",
                    "electric_range": 270
                }
            }
    
    def _load_panel_options(self) -> Dict:
        """Cargar opciones de paneles disponibles"""
        panels_path = os.path.join('config', 'panels.json')
        try:
            with open(panels_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Valores por defecto si no existe el archivo
            return {
                "450w": {
                    "name": "Panel 450W (Estándar)",
                    "power": 450,
                    "area_m2": 2.3,
                    "efficiency": 20.5,
                    "description": "Panel solar monocristalino estándar, ideal para comenzar en energía solar",
                    "technology": "Monocristalino PERC"
                },
                "500w": {
                    "name": "Panel 500W (Alta Eficiencia)",
                    "power": 500,
                    "area_m2": 2.4,
                    "efficiency": 21.8,
                    "description": "Panel solar de alta eficiencia, mejor relación costo-beneficio",
                    "technology": "Monocristalino Half-Cell"
                },
                "550w": {
                    "name": "Panel 550W (Premium)",
                    "power": 550,
                    "area_m2": 2.5,
                    "efficiency": 22.5,
                    "description": "Panel solar premium para máxima generación en espacios limitados",
                    "technology": "Monocristalino Bifacial"
                },
                "600w": {
                    "name": "Panel 600W (Ultra Premium)",
                    "power": 600,
                    "area_m2": 2.6,
                    "efficiency": 23.2,
                    "description": "Panel solar ultra premium de última generación, máxima eficiencia",
                    "technology": "Monocristalino TOPCon"
                }
            }
    
    def get_locations(self) -> List[Dict]:
        """Obtener lista de ubicaciones para el frontend"""
        return [
            {
                "value": key,
                "name": data["name"],
                "hsp": data["hsp"],
                "region": data.get("region", "")
            }
            for key, data in self.locations.items()
        ]
    
    def get_vehicles(self) -> List[Dict]:
        """Obtener lista de vehículos para el frontend"""
        vehicles_list = [
            {
                "value": key,
                "name": data["name"],
                "battery": data["battery"],
                "type": data["type"],
                "electric_range": data.get("electric_range", 0)
            }
            for key, data in self.vehicles.items()
        ]
        
        # Agregar opción personalizada
        vehicles_list.append({
            "value": "custom",
            "name": "Otro (especificar manualmente)",
            "battery": None,
            "type": "custom"
        })
        
        return vehicles_list
    
    def get_panel_options(self) -> List[Dict]:
        """Obtener lista de opciones de paneles para el frontend"""
        return [
            {
                "value": key,
                "name": data["name"],
                "power": data["power"],
                "area_m2": data["area_m2"],
                "efficiency": data["efficiency"],
                "description": data["description"],
                "technology": data.get("technology", "Monocristalino")
            }
            for key, data in self.panel_options.items()
        ]
    
    def calculate_panels_needed_precise(self, 
                                      total_energy_kwh_bimestral: float, 
                                      hsp: float, 
                                      panel_power_w: int) -> Tuple[int, float]:
        """
        Calcular paneles necesarios usando la fórmula específica proporcionada
        
        Args:
            total_energy_kwh_bimestral: Energía total requerida en el bimestre (kWh)
            hsp: Horas Sol Pico de la ubicación
            panel_power_w: Potencia del panel en watts
            
        Returns:
            Tuple: (numero_paneles, kwh_por_panel_bimestral)
        """
        # Paso 1: Calcular kWh que genera un panel por día
        kwh_per_panel_per_day = (panel_power_w * hsp) / 1000
        
        # Paso 2: Calcular kWh que genera un panel en 60 días (bimestre)
        kwh_per_panel_bimestral = kwh_per_panel_per_day * 60
        
        # Paso 3: Calcular paneles necesarios
        # Nota: Agregamos factor de pérdidas del sistema
        kwh_per_panel_bimestral_real = kwh_per_panel_bimestral * (1 - self.SYSTEM_LOSSES)
        
        panels_needed_exact = total_energy_kwh_bimestral / kwh_per_panel_bimestral_real
        panels_needed_rounded = int(panels_needed_exact)
        
        # Siempre redondear hacia arriba para cubrir la demanda
        if panels_needed_exact > panels_needed_rounded:
            panels_needed_rounded += 1
            
        return panels_needed_rounded, kwh_per_panel_bimestral_real
    

    def calculate_integral(self,
                    home_consumption: float,
                    location: str,
                    coverage: float = 1.0,
                    vehicle_model: str = "",
                    daily_ev_km: float = 0,
                    custom_battery: Optional[float] = None,
                    vehicle_efficiency: Optional[float] = None,
                    custom_vehicle_name: Optional[str] = None,
                    panel_type: str = "500w") -> Dict:  # NUEVO PARÁMETRO
        """
        Realizar cálculo integral del sistema solar
        MODIFICADO: Incluye selección de tipo de panel
        
        Args:
            home_consumption: Consumo bimestral del hogar en kWh
            location: Código de ubicación
            coverage: Porcentaje de cobertura deseado (0-1)
            vehicle_model: Modelo de vehículo eléctrico/híbrido
            daily_ev_km: Kilómetros diarios en modo eléctrico
            custom_battery: Capacidad de batería personalizada (si aplica)
            vehicle_efficiency: Eficiencia del vehículo en kWh/100km
            custom_vehicle_name: Nombre personalizado del vehículo
            panel_type: Tipo de panel solar seleccionado (NUEVO)
            
        Returns:
            Dict con todos los resultados del cálculo
        """
        
        # Validar ubicación
        if location not in self.locations:
            raise ValueError(f"Ubicación inválida: {location}")
        
        # Validar tipo de panel
        if panel_type not in self.panel_options:
            raise ValueError(f"Tipo de panel inválido: {panel_type}")
        
        # Obtener datos del panel seleccionado
        panel_data = self.panel_options[panel_type]
        panel_power_w = panel_data["power"]
        panel_area_m2 = panel_data["area_m2"]
        
        # Obtener HSP de la ubicación
        hsp = self.locations[location]["hsp"]
        
        # === CÁLCULO DEL CONSUMO DEL HOGAR ===
        home_consumption_covered = home_consumption * coverage
        
        # === CÁLCULO DEL CONSUMO DEL VEHÍCULO ===
        solar_energy_needed_vehicle_bimestral = 0
        vehicle_info = ""
        annual_gas_liters_saved = 0
        efficiency = 0
        
        if vehicle_model and vehicle_model != "":
            if vehicle_model == "custom":
                if vehicle_efficiency:
                    efficiency = vehicle_efficiency
                elif custom_battery:
                    efficiency = 20  # Valor por defecto
                else:
                    raise ValueError("Datos insuficientes para vehículo personalizado")
                
                vehicle_info = custom_vehicle_name or "Vehículo personalizado"
            else:
                if vehicle_model not in self.vehicles:
                    raise ValueError(f"Modelo de vehículo inválido: {vehicle_model}")
                
                vehicle_data = self.vehicles[vehicle_model]
                efficiency = vehicle_data["efficiency"]
                vehicle_info = vehicle_data["name"]
            
            # Calcular consumo del vehículo
            if daily_ev_km > 0:
                daily_energy_consumption_vehicle = (daily_ev_km * efficiency) / 100
                # Convertir a consumo bimestral (60 días)
                solar_energy_needed_vehicle_bimestral = daily_energy_consumption_vehicle * 60
                
                # Calcular gasolina ahorrada anualmente
                vehicle_efficiency_km_per_liter = 15
                annual_gas_liters_saved = (daily_ev_km * 365) / vehicle_efficiency_km_per_liter
        
        # === CÁLCULO TOTAL DE ENERGÍA REQUERIDA BIMESTRAL ===
        total_energy_needed_bimestral = home_consumption_covered + solar_energy_needed_vehicle_bimestral
        
        # === NUEVO CÁLCULO DE PANELES USANDO FÓRMULA ESPECÍFICA ===
        number_of_panels, kwh_per_panel_bimestral = self.calculate_panels_needed_precise(
        total_energy_needed_bimestral, hsp, panel_power_w
        )
        
        # Asegurar mínimo 1 panel si hay consumo
        if total_energy_needed_bimestral > 0 and number_of_panels == 0:
            number_of_panels = 1
        
        # === CÁLCULOS DERIVADOS ===
        # Potencia real del sistema basada en paneles
        actual_system_power_kw = (number_of_panels * panel_power_w) / 1000
        
        # Generación anual del sistema
        daily_generation = (actual_system_power_kw * hsp * (1 - self.SYSTEM_LOSSES))
        annual_solar_generation = daily_generation * 365
        
        # Cálculo de costos - Usando método general basado en potencia del sistema
        total_system_cost = actual_system_power_kw * self.COST_PER_KW_INSTALLED
        sener_incentive = total_system_cost * self.SENER_INCENTIVE_RATE
        net_cost = total_system_cost - sener_incentive
        
        # Calcular ahorros
        monthly_home_consumption = home_consumption / 2
        annual_home_consumption = monthly_home_consumption * 12
        annual_electricity_savings = min(annual_solar_generation, annual_home_consumption) * self.CFE_RATE_PER_KWH
        annual_gas_savings = annual_gas_liters_saved * self.GAS_PRICE_PER_LITER
        total_annual_savings = annual_electricity_savings + annual_gas_savings
        
        # Métricas financieras
        payback_years = net_cost / total_annual_savings if total_annual_savings > 0 else 999
        total_savings_25_years = total_annual_savings * 25
        roi_25_years = ((total_savings_25_years - net_cost) / net_cost) * 100 if net_cost > 0 else 0
        
        # Impacto ambiental
        annual_co2_avoided_electric = (annual_solar_generation * self.CO2_PER_KWH) / 1000
        annual_co2_avoided_gas = (annual_gas_liters_saved * self.CO2_PER_LITER_GAS) / 1000
        total_co2_avoided = annual_co2_avoided_electric + annual_co2_avoided_gas
        
        # Área de techo requerida
        total_roof_area = number_of_panels * panel_area_m2

        return {
            # Sistema
            "systemPowerKw": round(actual_system_power_kw, 2),
            "numberOfPanels": number_of_panels,
            "totalRoofArea": round(total_roof_area, 1),
            "panelType": panel_data["name"],  # NUEVO
            "panelPowerW": panel_power_w,     # NUEVO
            "kwh_per_panel_bimestral": round(kwh_per_panel_bimestral, 1),  # NUEVO
            
            # Costos
            "totalSystemCost": round(total_system_cost, 2),
            "senerIncentive": round(sener_incentive, 2),
            "netCost": round(net_cost, 2),
            
            # Ahorros
            "annualElectricitySavings": round(annual_electricity_savings, 2),
            "annualGasSavings": round(annual_gas_savings, 2),
            "totalAnnualSavings": round(total_annual_savings, 2),
            "monthlySavings": round(total_annual_savings / 12, 2),
            
            # Métricas financieras
            "paybackYears": round(payback_years, 1),
            "roi25Years": round(roi_25_years, 1),
            
            # Impacto ambiental
            "totalCo2Avoided": round(total_co2_avoided, 2),
            "treesEquivalent": round(total_co2_avoided * 16.5, 0),
            
            # Información del vehículo
            "vehicleInfo": vehicle_info,
            "hasVehicle": bool(vehicle_model and vehicle_model != ""),
            "annualGasLitersSaved": round(annual_gas_liters_saved, 0),
            
            # Generación
            "annualSolarGeneration": round(annual_solar_generation, 0),
            "dailyGeneration": round(daily_generation, 1),
            
            # Metadatos
            "location": self.locations[location]["name"],
            "hsp": hsp,
            "coverage": round(coverage * 100, 0)
        }
    
    def calculate_monthly_production(self, system_power_kw: float, location: str) -> List[Dict]:
        """
        Calcular producción mensual estimada del sistema
        
        Args:
            system_power_kw: Potencia del sistema en kW
            location: Código de ubicación
            
        Returns:
            Lista con producción por mes
        """
        if location not in self.locations:
            raise ValueError(f"Ubicación inválida: {location}")
        
        hsp = self.locations[location]["hsp"]
        
        # Factores de variación mensual (basados en irradiación solar típica en México)
        monthly_factors = {
            1: 0.85,  # Enero
            2: 0.90,  # Febrero
            3: 1.00,  # Marzo
            4: 1.10,  # Abril
            5: 1.15,  # Mayo
            6: 1.12,  # Junio
            7: 1.08,  # Julio
            8: 1.05,  # Agosto
            9: 0.95,  # Septiembre
            10: 0.90, # Octubre
            11: 0.85, # Noviembre
            12: 0.80  # Diciembre
        }
        
        # Días por mes
        days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        monthly_production = []
        for month in range(1, 13):
            base_daily_production = system_power_kw * hsp * (1 - self.SYSTEM_LOSSES)
            adjusted_daily_production = base_daily_production * monthly_factors[month]
            monthly_kwh = adjusted_daily_production * days_per_month[month - 1]
            
            monthly_production.append({
                "month": month,
                "production_kwh": round(monthly_kwh, 1),
                "value_mxn": round(monthly_kwh * self.CFE_RATE_PER_KWH, 2)
            })
        
        return monthly_production
    
    def estimate_battery_size(self, daily_consumption: float, autonomy_days: float = 1.0) -> Dict:
        """
        Estimar tamaño de batería necesario para respaldo
        
        Args:
            daily_consumption: Consumo diario en kWh
            autonomy_days: Días de autonomía deseados
            
        Returns:
            Dict con especificaciones de batería
        """
        # Factores de diseño de batería
        DEPTH_OF_DISCHARGE = 0.8  # DoD recomendado para litio
        SYSTEM_EFFICIENCY = 0.95  # Eficiencia del inversor/cargador
        SAFETY_FACTOR = 1.2  # Factor de seguridad
        
        # Calcular capacidad necesaria
        energy_needed = daily_consumption * autonomy_days
        battery_capacity_kwh = (energy_needed * SAFETY_FACTOR) / (DEPTH_OF_DISCHARGE * SYSTEM_EFFICIENCY)
        
        # Estimar costo (basado en precios promedio de baterías de litio)
        cost_per_kwh = 8000  # MXN por kWh
        estimated_cost = battery_capacity_kwh * cost_per_kwh
        
        return {
            "capacityKwh": round(battery_capacity_kwh, 1),
            "estimatedCost": round(estimated_cost, 2),
            "autonomyDays": autonomy_days,
            "usableCapacityKwh": round(battery_capacity_kwh * DEPTH_OF_DISCHARGE, 1)
        }