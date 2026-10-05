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

    def generate_response_plan(self, incident: Dict[str, Any], zone_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generates a tailored, country-specific disaster response plan.
        
        Args:
            incident: Dictionary containing disaster metrics (location_name, threat_score, event_type).
            zone_data: Optional evacuation zone statistics.
            
        Returns:
            Structured JSON response containing immediate actions, evacuation advice, and resource allocations.
        """
        location = incident.get("location_name", "Unknown Region")
        event_type = incident.get("event_type", "disaster").upper()
        threat_score = incident.get("threatScore") or incident.get("impact", {}).get("risk_score", 50)
        pop_at_risk = zone_data.get("total_population_affected") if zone_data else (incident.get("affectedPopulation") or 10000)

        # Fallback plan in case the LLM is unconfigured, times out, or hits rate limits
        fallback_plan = {
            "country_context": "AI DECISION SUPPORT OFFLINE",
            "severity_assessment": f"Automated tactical response generation is currently unavailable for {location}. Please rely on established emergency management protocols.",
            "immediate_actions": [
                "Initiate standard multi-agency manual response protocols.",
                "Refer to local municipal guidelines for the affected jurisdiction.",
                "Establish forward incident command post and monitor situation manually."
            ],
            "resource_allocation": [
                {"resource": "Automated Intelligence", "quantity": "-", "status": "Unavailable"}
            ],
            "evacuation_guidance": "Automated routing disabled. Consult local emergency broadcasting networks for evacuation orders."
        }

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
            2. Tailor the agencies specifically to the location (e.g. if India, deploy NDRF; if USA, deploy FEMA/National Guard; if Japan, JDF).
            3. Resource allocation must sound like real military/emergency logistics (e.g., 'CH-47 Chinook Helicopters', 'Water Purification Units').
            4. Return a clean JSON object matching this EXACT schema:
            {{
              "country_context": "string (e.g. 'NDRF JURISDICTION ACTIVE: VARANASI SECTOR')",
              "severity_assessment": "string (Tactical appraisal of the threat vector)",
              "immediate_actions": ["string (Action 1)", "string (Action 2)", "string (Action 3)"],
              "resource_allocation": [
                {{"resource": "string", "quantity": "string", "status": "string"}},
                {{"resource": "string", "quantity": "string", "status": "string"}},
                {{"resource": "string", "quantity": "string", "status": "string"}}
              ],
              "evacuation_guidance": "string (Specific highway/route closure or shelter deployment instructions)"
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


# Lazy-load singleton to avoid blocking startup during Gemini SDK initialization
_decision_support_service = None

def get_decision_support_service() -> DecisionSupportService:
    """Lazy-load the decision support service on first use."""
    global _decision_support_service
    if _decision_support_service is None:
        _decision_support_service = DecisionSupportService()
    return _decision_support_service
