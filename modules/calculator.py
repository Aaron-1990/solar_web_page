import json
import os
from typing import Dict, Optional, List, Tuple

class SolarCalculator:
    """
    Módulo para realizar todos los cálculos relacionados con sistemas solares
    incluyendo consumo del hogar y vehículos eléctricos/híbridos
    """
    
    def __init__(self):
        # Cargar datos de configuración
        self.locations = self._load_locations()
        self.vehicles = self._load_vehicles()
        
        # Constantes del sistema
        self.SYSTEM_LOSSES = 0.20  # 20% pérdidas del sistema
        self.PANEL_POWER_W = 450  # Watts por panel estándar
        self.PANEL_AREA_M2 = 2.3  # Área por panel en m²
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
    
    def calculate_integral(self,
                    home_consumption: float,
                    location: str,
                    coverage: float = 1.0,
                    vehicle_model: str = "",
                    daily_ev_km: float = 0,
                    custom_battery: Optional[float] = None,
                    vehicle_efficiency: Optional[float] = None,  # Nuevo
                    custom_vehicle_name: Optional[str] = None) -> Dict:  # Nuevo
        """
        Realizar cálculo integral del sistema solar
        
        Args:
            home_consumption: Consumo bimestral del hogar en kWh
            location: Código de ubicación
            coverage: Porcentaje de cobertura deseado (0-1)
            vehicle_model: Modelo de vehículo eléctrico/híbrido
            daily_ev_km: Kilómetros diarios en modo eléctrico
            custom_battery: Capacidad de batería personalizada (si aplica)
            vehicle_efficiency: Eficiencia del vehículo en kWh/100km (para modo avanzado)
            custom_vehicle_name: Nombre personalizado del vehículo
            
        Returns:
            Dict con todos los resultados del cálculo
        """
        
        # Validar ubicación
        if location not in self.locations:
            raise ValueError(f"Ubicación inválida: {location}")
        
        # Obtener HSP de la ubicación
        hsp = self.locations[location]["hsp"]
        
        # Calcular consumo del hogar
        monthly_home_consumption = home_consumption / 2
        annual_home_consumption = monthly_home_consumption * 12
        daily_home_consumption = annual_home_consumption / 365
        solar_energy_needed_home = daily_home_consumption * coverage
        
        # Inicializar variables del vehículo
        solar_energy_needed_vehicle = 0
        vehicle_info = ""
        annual_gas_liters_saved = 0
        efficiency = 0  # Inicializar para evitar errores
        
        if vehicle_model and vehicle_model != "":
            if vehicle_model == "custom":
                # Vehículo personalizado - usar eficiencia proporcionada o calcular
                if vehicle_efficiency:
                    efficiency = vehicle_efficiency
                elif custom_battery:
                    # Si solo tenemos batería, asumir eficiencia default
                    efficiency = 20  # 20 kWh/100km es un promedio razonable
                else:
                    raise ValueError("Datos insuficientes para vehículo personalizado. Proporcione eficiencia o capacidad de batería.")
                
                vehicle_info = custom_vehicle_name or "Vehículo personalizado"
                
            else:
                # Vehículo predefinido
                if vehicle_model not in self.vehicles:
                    raise ValueError(f"Modelo de vehículo inválido: {vehicle_model}")
                
                vehicle_data = self.vehicles[vehicle_model]
                battery_capacity = vehicle_data["battery"]
                efficiency = vehicle_data["efficiency"]
                vehicle_info = vehicle_data["name"]
            
            # Calcular consumo del vehículo (común para ambos casos)
            if daily_ev_km > 0:
                daily_energy_consumption_vehicle = (daily_ev_km * efficiency) / 100
                solar_energy_needed_vehicle = daily_energy_consumption_vehicle
                
                # Calcular gasolina ahorrada
                vehicle_efficiency_km_per_liter = 15  # Asumir 15 km/L promedio
                annual_gas_liters_saved = (daily_ev_km * 365) / vehicle_efficiency_km_per_liter
            else:
                # Si no hay km diarios, no hay consumo
                solar_energy_needed_vehicle = 0
                annual_gas_liters_saved = 0
        
        # Si no hay vehículo, todas las variables ya están en 0
        
        # Calcular sistema solar total necesario
        total_daily_energy_needed = solar_energy_needed_home + solar_energy_needed_vehicle
        
        # Calcular potencia del sistema considerando pérdidas
        system_power_kw = total_daily_energy_needed / (hsp * (1 - self.SYSTEM_LOSSES))
        
        # Calcular número de paneles
        number_of_panels = int((system_power_kw * 1000) / self.PANEL_POWER_W)
        if (system_power_kw * 1000) % self.PANEL_POWER_W > 0:
            number_of_panels += 1
        
        # Asegurar mínimo 1 panel si hay consumo
        if total_daily_energy_needed > 0 and number_of_panels == 0:
            number_of_panels = 1
        
        # Recalcular potencia real del sistema basada en paneles
        actual_system_power_kw = (number_of_panels * self.PANEL_POWER_W) / 1000
        
        # Calcular costos
        total_system_cost = actual_system_power_kw * self.COST_PER_KW_INSTALLED
        sener_incentive = total_system_cost * self.SENER_INCENTIVE_RATE
        net_cost = total_system_cost - sener_incentive
        
        # Calcular generación anual del sistema
        annual_solar_generation = actual_system_power_kw * hsp * 365 * (1 - self.SYSTEM_LOSSES)
        
        # Calcular ahorros
        annual_electricity_savings = min(annual_solar_generation, annual_home_consumption) * self.CFE_RATE_PER_KWH
        annual_gas_savings = annual_gas_liters_saved * self.GAS_PRICE_PER_LITER
        total_annual_savings = annual_electricity_savings + annual_gas_savings
        
        # Calcular periodo de recuperación
        payback_years = net_cost / total_annual_savings if total_annual_savings > 0 else 999
        
        # Calcular impacto ambiental
        annual_co2_avoided_electric = (annual_solar_generation * self.CO2_PER_KWH) / 1000  # Toneladas
        annual_co2_avoided_gas = (annual_gas_liters_saved * self.CO2_PER_LITER_GAS) / 1000  # Toneladas
        total_co2_avoided = annual_co2_avoided_electric + annual_co2_avoided_gas
        
        # Calcular área de techo requerida
        total_roof_area = number_of_panels * self.PANEL_AREA_M2
        
        # Calcular ROI a 25 años
        total_savings_25_years = total_annual_savings * 25
        roi_25_years = ((total_savings_25_years - net_cost) / net_cost) * 100 if net_cost > 0 else 0
        
        return {
            # Sistema
            "systemPowerKw": round(actual_system_power_kw, 2),
            "numberOfPanels": number_of_panels,
            "totalRoofArea": round(total_roof_area, 1),
            
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
            "treesEquivalent": round(total_co2_avoided * 16.5, 0),  # 1 árbol absorbe ~60kg CO2/año
            
            # Información del vehículo
            "vehicleInfo": vehicle_info,
            "hasVehicle": bool(vehicle_model and vehicle_model != ""),
            "annualGasLitersSaved": round(annual_gas_liters_saved, 0),
            
            # Generación
            "annualSolarGeneration": round(annual_solar_generation, 0),
            "dailyGeneration": round(annual_solar_generation / 365, 1),
            
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


