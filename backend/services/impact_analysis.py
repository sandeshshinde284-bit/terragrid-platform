"""
Feature 2: Impact Analysis Service
Calculates and analyzes impact of disasters:
- Affected population
- Affected area
- Population density
- Risk scores
- Vulnerability assessment
"""
import logging
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)

class ImpactAnalysisService:
    """Service to analyze disaster impact"""
    
    # Global population density grid (simplified estimates by region)
    POPULATION_DENSITY = {
        # (lat_range, lon_range): density per km²
        # High density urban areas
        (28, 30, 76, 78): 11000,    # Delhi region
        (19, 21, 72, 74): 20000,    # Mumbai region
        (34, 36, -118, -116): 1500, # Los Angeles
        (37, 39, -122, -120): 800,  # San Francisco Bay
        (40, 42, -74, -72): 2000,   # New York
        # Low density rural areas
        (35, 40, -120, -115): 50,   # Sierra Nevada
        (-35, -30, 140, 155): 20,   # Australia outback
    }
    
    @classmethod
    def calculate_impact(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive impact analysis for an event
        
        Args:
            event: Event data from API
            
        Returns:
            Impact analysis with affected population, area, risk score, etc.
        """
        try:
            lat = event.get("latitude", 0)
            lon = event.get("longitude", 0)
            event_type = event.get("event_type", "unknown")
            severity = event.get("severity", "low")
            
            # Calculate affected area (km²) based on event type and severity
            affected_area = cls._calculate_affected_area(event_type, severity)
            
            # Get population density for location
            pop_density = cls._get_population_density(lat, lon)
            
            # Calculate affected population
            affected_population = cls._calculate_affected_population(
                affected_area, pop_density
            )
            
            # Calculate vulnerability score (0-100)
            vulnerability = cls._calculate_vulnerability(lat, lon, event_type)
            
            # Calculate risk score (0-100) combining severity + vulnerability
            risk_score = cls._calculate_risk_score(severity, vulnerability)
            
            # Get trend/forecast (6-hour expansion)
            trend_area = cls._calculate_trend(event_type, affected_area)
            forecast_6h = affected_area + trend_area
            
            # Get impact zones
            impact_zones = cls._get_impact_zones(lat, lon, affected_area)
            
            return {
                "affected_area_km2": round(affected_area, 2),
                "affected_population": int(affected_population),
                "population_density_km2": int(pop_density),
                "vulnerability_score": round(vulnerability, 1),
                "risk_score": round(risk_score, 1),
                "trend_km2_per_hour": round(trend_area / 6, 2),  # Per hour rate
                "forecast_6h_km2": round(forecast_6h, 2),
                "impact_zones": impact_zones,
                "severity_level": cls._interpret_severity(risk_score),
                "humanitarian_impact": cls._calculate_humanitarian_impact(
                    affected_population, event_type, severity
                ),
                "recommended_actions": cls._get_recommended_actions(
                    event_type, affected_population, risk_score
                )
            }
        except Exception as e:
            logger.error(f"Error calculating impact: {str(e)}")
            return cls._get_default_impact()
    
    @classmethod
    def _calculate_affected_area(cls, event_type: str, severity: str) -> float:
        """Calculate affected area in km² based on event type and severity"""
        base_areas = {
            "fire": 50,      # fires start small, expand
            "earthquake": 200,  # broader impact zone
            "flood": 150,    # area dependent on terrain
            "storm": 300,    # storms cover large areas
            "volcano": 400,  # large exclusion zones
            "landslide": 20, # localized
            "aerosol": 500,  # dust storms very large
            "snow_ice": 100,
        }
        
        base = base_areas.get(event_type, 100)
        
        # Severity multipliers
        multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
        
        return base * multipliers.get(severity, 1.0)
    
    @classmethod
    def _get_population_density(cls, lat: float, lon: float) -> float:
        """Get population density for coordinates"""
        for (lat_min, lat_max, lon_min, lon_max), density in cls.POPULATION_DENSITY.items():
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return density
        
        # Default: estimate based on latitude
        # Higher density in developed regions
        if abs(lat) < 30:
            return 200  # Tropical regions
        elif abs(lat) < 50:
            return 150  # Mid-latitude
        else:
            return 20   # Polar regions
    
    @classmethod
    def _calculate_affected_population(cls, area: float, density: float) -> float:
        """Calculate affected population from area and density"""
        # Not all area has same density - use 60% coefficient
        return area * density * 0.6
    
    @classmethod
    def _calculate_vulnerability(cls, lat: float, lon: float, event_type: str) -> float:
        """Calculate vulnerability score (0-100) based on location and event type"""
        # Base vulnerability by region
        vulnerability = 50.0
        
        # Geography-based vulnerability
        if 10 <= lat <= 40:
            vulnerability += 15  # Tropical/subtropical - high disaster risk
        
        if lon < -100 or (lon > 60 and lon < 140):
            vulnerability += 10  # Pacific Ring of Fire
        
        # Event-specific vulnerability
        event_vulnerabilities = {
            "earthquake": 30,  # Earthquakes unpredictable
            "volcano": 25,
            "flood": 15,      # Some warning possible
            "fire": 20,
            "storm": 15,
        }
        
        vulnerability += event_vulnerabilities.get(event_type, 0)
        
        return min(100.0, vulnerability)
    
    @classmethod
    def _calculate_risk_score(cls, severity: str, vulnerability: float) -> float:
        """Calculate overall risk score (0-100)"""
        severity_scores = {
            "low": 25,
            "medium": 50,
            "high": 75,
            "critical": 95
        }
        
        severity_score = severity_scores.get(severity, 50)
        
        # Risk = weighted combination of severity and vulnerability
        risk = (severity_score * 0.6) + (vulnerability * 0.4)
        
        return min(100.0, risk)
    
    @classmethod
    def _calculate_trend(cls, event_type: str, base_area: float) -> float:
        """Calculate area expansion over 6 hours"""
        # Expansion rates by event type
        expansion_rates = {
            "fire": 0.25,      # Fires expand 25% in 6h
            "earthquake": 0.0, # Earthquakes don't expand
            "flood": 0.15,     # Floods spread gradually
            "storm": 0.05,     # Storms move slowly
            "volcano": 0.0,
            "landslide": 0.0,
        }
        
        rate = expansion_rates.get(event_type, 0.1)
        return base_area * rate
    
    @classmethod
    def _get_impact_zones(cls, lat: float, lon: float, area: float) -> List[Dict]:
        """Get affected cities/zones"""
        # Simplified: return center and distance-based zones
        radius_km = math.sqrt(area / math.pi)
        
        return [
            {
                "zone_type": "primary",
                "radius_km": round(radius_km * 0.5, 1),
                "description": "Most severe impact zone"
            },
            {
                "zone_type": "secondary",
                "radius_km": round(radius_km * 0.8, 1),
                "description": "Moderate impact zone"
            },
            {
                "zone_type": "tertiary",
                "radius_km": round(radius_km, 1),
                "description": "Peripheral impact zone"
            }
        ]
    
    @classmethod
    def _interpret_severity(cls, risk_score: float) -> str:
        """Interpret risk score as severity level"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    @classmethod
    def _calculate_humanitarian_impact(cls, population: int, event_type: str, severity: str) -> Dict:
        """Calculate humanitarian impact metrics"""
        # Casualty estimates based on population and event type
        casualty_rates = {
            "earthquake": 0.02,   # ~2% in earthquakes
            "volcano": 0.01,
            "flood": 0.005,
            "fire": 0.003,
            "storm": 0.001,
        }
        
        rate = casualty_rates.get(event_type, 0.001)
        severity_multipliers = {"low": 0.5, "medium": 1.0, "high": 2.0, "critical": 3.0}
        multiplier = severity_multipliers.get(severity, 1.0)
        
        estimated_deaths = int(population * rate * multiplier)
        estimated_injured = estimated_deaths * 3
        estimated_homeless = int(population * 0.1 * multiplier)
        
        return {
            "estimated_deaths": estimated_deaths,
            "estimated_injured": estimated_injured,
            "estimated_homeless": estimated_homeless,
            "need_level": "critical" if estimated_deaths > 100 else "high" if estimated_deaths > 10 else "moderate"
        }
    
    @classmethod
    def _get_recommended_actions(cls, event_type: str, population: int, risk_score: float) -> List[str]:
        """Get recommended humanitarian response actions"""
        actions = []
        
        # Severity-based actions
        if risk_score >= 80:
            actions.append("🚨 Immediate evacuation recommended")
            actions.append("🏥 Deploy emergency medical teams")
            actions.append("📡 Activate emergency broadcasting")
        elif risk_score >= 60:
            actions.append("⚠️ Alert residents and prepare evacuation routes")
            actions.append("🏥 Pre-position medical supplies")
            actions.append("🛡️ Deploy rescue teams to staging areas")
        
        # Event-specific actions
        if event_type == "earthquake":
            actions.append("🏢 Conduct structural damage assessments")
            actions.append("🚚 Stage heavy equipment for debris removal")
        elif event_type == "flood":
            actions.append("💧 Deploy water purification systems")
            actions.append("🏠 Activate temporary shelters")
        elif event_type == "fire":
            actions.append("🔥 Create firebreaks and evacuation corridors")
            actions.append("💨 Monitor air quality")
        elif event_type == "storm":
            actions.append("📶 Protect critical infrastructure")
            actions.append("⚡ Prepare generators and backup power")
        
        # Population-based actions
        if population > 1000000:
            actions.append("🛂 Coordinate international humanitarian aid")
            actions.append("📊 Establish incident command center")
        
        return actions[:4]  # Return top 4 actions
    
    @classmethod
    def _get_default_impact(cls) -> Dict[str, Any]:
        """Return default impact when calculation fails"""
        return {
            "affected_area_km2": 0,
            "affected_population": 0,
            "population_density_km2": 0,
            "vulnerability_score": 50.0,
            "risk_score": 50.0,
            "trend_km2_per_hour": 0,
            "forecast_6h_km2": 0,
            "impact_zones": [],
            "severity_level": "UNKNOWN",
            "humanitarian_impact": {
                "estimated_deaths": 0,
                "estimated_injured": 0,
                "estimated_homeless": 0,
                "need_level": "unknown"
            },
            "recommended_actions": []
        }
