import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DecisionSupportService:
    """
    AI-Powered Decision Support Service (Feature 6).
    Leverages Google Cloud Vertex AI to generate localized, country-specific 
    tactical emergency response plans based on disaster metrics.
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_REGION", "us-central1")
        self.model = None

        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            
            if self.project_id:
                # Initialize Vertex AI with GCP credentials
                vertexai.init(project=self.project_id, location=self.location)
                
                self.model = GenerativeModel(
                    model_name=model_name,
                    # Vertex uses generation_config but sometimes dict format differs, keeping it standard
                    generation_config={"response_mime_type": "application/json"}
                )
                logger.info(f"DecisionSupportService: Vertex AI {model_name} initialized successfully.")
            else:
                logger.warning("DecisionSupportService: GCP_PROJECT_ID is not configured in .env. Will use fallback plans.")
                
        except ImportError:
            logger.warning("DecisionSupportService: google-cloud-aiplatform SDK not installed. Will use fallback plans.")
        except Exception as e:
            logger.warning(f"DecisionSupportService: Could not initialize Vertex AI SDK ({type(e).__name__}: {e}). Will use fallback plans.")

    def generate_response_plan(self, incident: Dict[str, Any], zone_data: Optional[Dict[str, Any]] = None, use_mock: bool = False) -> Dict[str, Any]:
        """
        Generates a tailored, country-specific disaster response plan.
        
        Args:
            incident: Dictionary containing disaster metrics (location_name, threat_score, event_type).
            zone_data: Optional evacuation zone statistics.
            use_mock: If True, bypasses API and returns a rich fabricated demonstration plan.
            
        Returns:
            Structured JSON response containing immediate actions, evacuation advice, and resource allocations.
        """
        from .mock_data_loader import MockDataLoader
        
        location = incident.get("location_name", "Unknown Region")
        event_type = incident.get("event_type", "disaster").upper()
        threat_score = incident.get("threatScore") or incident.get("impact", {}).get("risk_score", 50)
        pop_at_risk = zone_data.get("total_population_affected") if zone_data else (incident.get("affectedPopulation") or 10000)

        # Transparent AI Offline Fallback (Addresses Copilot's "Fallback-Heavy" critique)
        fallback_plan = MockDataLoader.load_fallback_ai_plan()

        # Rich demonstration plan
        if use_mock:
            mock_plan = MockDataLoader.load_mock_plan()
            logger.info(f"Returning rich mock demonstration plan for {location}")
            return mock_plan

        if not self.model:
            return fallback_plan

        try:
            prompt = f"""
            You are a Senior Disaster Response Incident Commander (military-grade) operating the TerraGrid Emergency Intelligence System.
            Analyze the following live incident and provide an operational, hyper-realistic, country-specific emergency response plan.

            INCIDENT PARAMETERS:
            - Disaster Type: {event_type}
            - Location / Jurisdiction: {location}
            - Calculated Threat Score: {threat_score} / 100
            - Estimated Population at Risk: {pop_at_risk:,} civilians

            STRICT OPERATIONAL DIRECTIVES:
            1. DO NOT give generic advice. Use highly specific, tactical, and military/FEMA-style terminology (e.g., 'Triage', 'Perimeter Containment', 'Forward Operating Base').
            2. FORMATTING MANDATE: Output MUST be written in crisp, professional Sentence Case (e.g., 'Initiate Joint Field Office activation...', NOT 'INITIATE JOINT...'). Do NOT use monolithic all-caps.
            3. Keep action bullets punchy and actionable (maximum 2 lines per bullet).
            4. Tailor the agencies specifically to the location (e.g. if India, deploy NDRF; if USA, deploy FEMA/National Guard; if Japan, JDF).
            5. Resource allocation must sound like real military/emergency logistics (e.g., 'CH-47 Chinook Helicopters', 'Water Purification Units').
            6. Return a clean JSON object matching this EXACT schema:
            {{
              "country_context": "string (e.g. 'FEMA Region 6 Jurisdiction: Port Fourchon Sector, Louisiana')",
              "severity_assessment": "string (Concise 2-sentence tactical overview in clean sentence case)",
              "immediate_actions": ["string (Action 1 in sentence case)", "string (Action 2 in sentence case)", "string (Action 3 in sentence case)"],
              "resource_allocation": [
                {{"resource": "string", "quantity": "string", "status": "string"}},
                {{"resource": "string", "quantity": "string", "status": "string"}},
                {{"resource": "string", "quantity": "string", "status": "string"}}
              ],
              "evacuation_guidance": "string (Specific highway corridors, choke-point warnings, and designated municipal shelters in clean sentence case)"
            }}
            """

            response = self.model.generate_content(prompt)
            if response and response.text:
                plan = json.loads(response.text.strip())
                logger.info(f"Generated AI Decision Support Plan for {location} via Vertex AI.")
                return plan

        except Exception as e:
            logger.error(f"❌ CRITICAL VERTEX AI FAILURE: {type(e).__name__} - {str(e)}")
            logger.warning("Vertex AI decision support generation failed. Returning tactical fallback.")

        return fallback_plan

    def generate_deep_tactical_dossier(self, event_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """
        Tier 2 Deep Intelligence Dossier: Fuses multi-source telemetry from NASA, USGS,
        OpenWeather, and GDACS, sending a multi-variable military prompt to Google Cloud Vertex AI
        (gemini-1.5-flash) to generate 2000% detailed crisis forecasting across the 8 tabs.
        
        Args:
            event_data: Incident data.
            use_mock: If True, bypasses API and returns a rich fabricated demonstration dossier.
        """
        event_type = event_data.get("event_type", "Hazard")
        location = event_data.get("location_name", "Target Sector")
        lat = event_data.get("latitude", 0.0)
        lon = event_data.get("longitude", 0.0)
        source = event_data.get("source", "TerraGrid Global Ingestion Network")

        impact = event_data.get("impact") or {}
        threat_score = impact.get("risk_score", 50.0)
        area_km2 = impact.get("affected_area_km2", 50.0)
        pop_at_risk = impact.get("affected_population", 10000)

        # Extract atmospheric telemetry if present (OpenWeather)
        raw_data = event_data.get("data") or {}
        weather_data = raw_data.get("data") or raw_data
        wind_speed = weather_data.get("wind_speed_ms", 5.2)
        wind_gust = weather_data.get("wind_gust_ms", 8.4)
        humidity = weather_data.get("humidity_percent", 65)
        temperature = weather_data.get("temperature_c", 22.0)
        pressure = weather_data.get("pressure_hpa", 1013)
        weather_desc = weather_data.get("description", "Active weather conditions")

        from .mock_data_loader import MockDataLoader

        # Transparent AI Offline Fallback (Addresses Copilot's "Fallback-Heavy" critique)
        fallback_dossier = MockDataLoader.load_fallback_dossier()
        
        # Rich demonstration dossier
        if use_mock:
            mock_dossier = MockDataLoader.load_mock_dossier()
            logger.info(f"Returning rich mock demonstration dossier for {location}")
            return mock_dossier

        if not self.model:
            logger.warning("Vertex AI model unconfigured. Returning transparent offline state.")
            return fallback_dossier

        try:
            prompt = f"""
            You are the Chief Geospatial Intelligence Officer and Senior Military Incident Commander for the TerraGrid Crisis Command Center.
            Analyze this live multi-source disaster event and generate an exhaustive, hyper-realistic, 2000% detailed Tactical Intelligence Dossier.

            GROUND TRUTH SENSOR TELEMETRY:
            - Incident Type: {event_type}
            - Location / Jurisdiction: {location}
            - Coordinates: Lat {lat}, Lon {lon}
            - Calculated Threat Score: {threat_score} / 100
            - Impacted Area: {area_km2} km²
            - Population at Immediate Risk: {pop_at_risk:,} citizens
            - Atmospheric Telemetry (OpenWeather):
              • Surface Wind Speed: {wind_speed} m/s | Wind Gusts: {wind_gust} m/s
              • Relative Humidity: {humidity}% | Ambient Temp: {temperature}°C
              • Barometric Pressure: {pressure} hPa | Weather: {weather_desc}
            - Source Telemetry: {source}

            STRICT OPERATIONAL DIRECTIVES:
            1. NO generic advice. Use authentic military, FEMA, and UN OCHA crisis terminology.
            2. Calculate the PREDICTIVE CASCADE (Feature 9) for 6 Hours, 12 Hours, and 24 Hours based on the physical wind vectors and terrain:
               - Fire spreads downwind; storm surge moves inland; flood perimeters expand into low-lying basins; seismic aftershocks follow active fault branches.
            3. Identify SPECIFIC CRITICAL INFRASTRUCTURE at risk: local municipal hospitals, power substations, bridges, water treatment facilities within danger radii.
            4. Detail EVACUATION CORRIDORS (Feature 3A): specific highway routes, dangerous choke-points (bridges/bottlenecks), and safe assembly staging areas.
            5. Build a RESOURCE MOBILIZATION MATRIX (Feature 6): concrete units, helicopter sorties, field hospital beds, emergency generators, and potable water rations.
            6. Detail VULNERABLE DEMOGRAPHICS: senior care facilities, schools, and special-needs medical requirements.

            Return a single clean JSON object matching this EXACT schema:
            {{
              "situational_assessment": "string (Concise, high-impact 3-sentence military briefing evaluating the crisis vector)",
              "threat_level": "string ('CRITICAL' | 'HIGH' | 'MEDIUM')",
              "predictive_cascade": [
                {{
                  "timeframe": "6 Hours",
                  "perimeter_delta_km2": 15.2,
                  "spread_direction": "string (Specific vector along wind/topography)",
                  "primary_risk": "string",
                  "secondary_threat": "string"
                }},
                {{
                  "timeframe": "12 Hours",
                  "perimeter_delta_km2": 32.5,
                  "spread_direction": "string",
                  "primary_risk": "string",
                  "secondary_threat": "string"
                }},
                {{
                  "timeframe": "24 Hours",
                  "perimeter_delta_km2": 65.0,
                  "spread_direction": "string",
                  "primary_risk": "string",
                  "secondary_threat": "string"
                }}
              ],
              "critical_infrastructure": [
                {{
                  "facility_name": "string (e.g. 'St. Jude Regional Hospital')",
                  "facility_type": "string ('Hospital' | 'Power Grid' | 'Water Treatment' | 'Bridge/Transit')",
                  "distance_km": 3.2,
                  "risk_level": "string ('CRITICAL' | 'HIGH' | 'MODERATE')",
                  "action_required": "string"
                }}
              ],
              "evacuation_corridors": {{
                "primary_corridor": "string (Specific highway or transit route)",
                "alternative_route": "string",
                "choke_points": ["string (Specific bottleneck warning)"],
                "safe_assembly_zones": ["string (Specific stadium or park rally point)"],
                "estimated_clearance_time_hours": 3.5
              }},
              "resource_matrix": [
                {{
                  "resource": "string",
                  "quantity": "string",
                  "assigned_agency": "string",
                  "priority": "string ('IMMEDIATE' | 'HIGH' | 'STAGED')"
                }}
              ],
              "vulnerable_demographics": {{
                "facilities_at_risk": ["string"],
                "estimated_displaced_citizens": 1200,
                "special_needs_assistance_required": "string"
              }}
            }}
            """

            response = self.model.generate_content(prompt)
            if response and response.text:
                # Clean response text in case of markdown formatting
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                dossier = json.loads(cleaned_text)
                logger.info(f"Generated Tier 2 Deep Tactical AI Dossier for {location} via Vertex AI.")
                return dossier

        except Exception as e:
            logger.error(f"❌ VERTEX AI DEEP DOSSIER FAILURE: {type(e).__name__} - {str(e)}")
            logger.warning("Returning operational contingency dossier.")

        return fallback_dossier


# Lazy-load singleton to avoid blocking startup during Gemini SDK initialization
_decision_support_service = None

def get_decision_support_service() -> DecisionSupportService:
    """Lazy-load the decision support service on first use."""
    global _decision_support_service
    if _decision_support_service is None:
        _decision_support_service = DecisionSupportService()
    return _decision_support_service
