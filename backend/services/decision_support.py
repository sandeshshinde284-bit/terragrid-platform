from backend.config import settings
import os
import json
import math
import logging
from typing import Dict, Any, List, Optional

from .prompt_schemas import DEEP_DOSSIER_SCHEMA_TEXT, RESPONSE_PLAN_SCHEMA_TEXT, PREPAREDNESS_ACTIONS_SCHEMA_TEXT, AGENCY_ALERT_TEMPLATES_SCHEMA_TEXT
from backend.utils.data_logger import log_raw_data

logger = logging.getLogger(__name__)

def unavailable_ai_result(kind: str, reason: str) -> Dict[str, Any]:
    """Explicit marker that live AI output is unavailable. It carries no content."""
    result: Dict[str, Any] = {"is_fallback": True, "unavailable": True, "ai_available": False, "kind": kind, "reason": reason}
    if kind == "preparedness":
        result.update(risk_context="", actions=[])
    elif kind == "agency_alerts":
        result.update(risk_context="", alerts=[])
    return result


class DecisionSupportService:
    """
    AI-Powered Decision Support Service (Feature 6).
    Leverages Google Cloud Vertex AI to generate localized, country-specific 
    tactical emergency response plans based on disaster metrics.
    """

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_REGION
        self.model = None

        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            model_name = settings.GEMINI_MODEL
            
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
        
        location = incident.get("location_name") or "Not available"
        event_type = (incident.get("event_type") or "Not available").upper()
        threat_score = incident.get("threatScore") or (incident.get("impact") or {}).get("risk_score")
        pop_at_risk = zone_data.get("total_population_affected") if zone_data else incident.get("affectedPopulation")
        threat_txt = f"{threat_score} / 100" if threat_score is not None else "Not available"
        pop_txt = f"{pop_at_risk:,} civilians" if pop_at_risk is not None else "Not available"


        # Use mock data for demonstration mode
        if use_mock:
            mock_plan = MockDataLoader.load_mock_plan()
            logger.info(f"Returning rich mock demonstration plan for {location}")
            return mock_plan

        if not self.model:
            return unavailable_ai_result("response_plan", "Gemini model is not configured")

        try:
            # The existing 6 APIs (NASA EONET, GDACS, USGS, OpenWeather, NOAA) provide complete India coverage
            # Code preserved for future use if/when IMD opens their API for public access
            
            # from .imd_weather import IMDWeatherService
            # latitude = incident.get("latitude", 0)
            # longitude = incident.get("longitude", 0)
            # has_imd_data = IMDWeatherService.is_india_location(latitude, longitude)
            
            # Build data sources list
            data_sources = [incident.get("source") or "Not available"]
            # if has_imd_data:
            #     data_sources.insert(0, "IMD (India Meteorological Department)")
            
            logger.info(f"[GEMINI ANALYSIS] Data sources for {location}: {', '.join(data_sources)}")
            
            
            
            # imd_context = ""
            # if has_imd_data:
            #     incident_data = incident.get("data", {})
            #     monsoon_status = incident_data.get("monsoon_status", "Not specified")
            #     precipitation = incident_data.get("precipitation", "Not measured")
            #     imd_alerts = incident_data.get("alert", "No specific alert")

            #     imd_context = f"""
            # CRITICAL: IMD (INDIA METEOROLOGICAL DEPARTMENT) DATA AVAILABLE
            # This incident is within India. IMD data takes priority for weather analysis:
            # - Monsoon Status: {monsoon_status}
            # - Rainfall Forecast: {precipitation}mm
            # - IMD Alert: {imd_alerts}
            # """
            
            imd_context = ""
            
            prompt = f"""
            You are analyzing a live disaster incident for the TerraGrid Emergency Response System.
            Generate a comprehensive, location-specific emergency response plan based on the following incident data.

            INCIDENT PARAMETERS ("Not available" means the value is missing; do not estimate it):
            - Disaster Type: {event_type}
            - Location / Jurisdiction: {location}
            - Calculated Threat Score: {threat_txt}
            - Estimated Population at Risk: {pop_txt}

            DATA SOURCES INTEGRATED:
            {', '.join(data_sources)}

            NO LOCATION DATABASE: Do not name agencies, facilities, staging areas or response times unless they appear in the input above.

            {imd_context}

            STRICT OPERATIONAL DIRECTIVES:

            CAUSAL CHAIN EXTRACTION:
            You MUST include these four fields in your JSON response:
            1. trigger_event: What is the root cause of this disaster? (single sentence)
            2. infrastructure_factors: What systems/capacities are being overwhelmed? (array of 2-3 bullet points)
            3. predicted_outcome: What will happen if this continues unabated? (1-2 sentences)
            4. historical_reference: What similar past event does this resemble? (specific past incident with year/location)

            1. DO NOT give generic advice. Use highly specific, tactical, and military/FEMA-style terminology (e.g., 'Triage', 'Perimeter Containment', 'Forward Operating Base').
            2. FORMATTING MANDATE: Output MUST be written in crisp, professional Sentence Case (e.g., 'Initiate Joint Field Office activation...', NOT 'INITIATE JOINT...'). Do NOT use monolithic all-caps.
            3. Keep action bullets punchy and actionable (maximum 2 lines per bullet).
            4. Tailor the agencies specifically to the location provided above.
            5. Resource allocation must sound like real military/emergency logistics (e.g., 'CH-47 Chinook Helicopters', 'Water Purification Units').
            6. "quantity" MUST be an INTEGER ONLY (e.g., 5, NOT "4-6")
            7. "priority" MUST be 1 (IMMEDIATE), 2 (HIGH), or 3 (STAGED) ONLY
            8. "estimated_arrival_minutes" MUST be INTEGER ONLY
            9. "confidence" MUST be 0-100 INTEGER ONLY
            10. Return a clean JSON object matching THIS EXACT schema:
            {RESPONSE_PLAN_SCHEMA_TEXT}
            
            Return ONLY the JSON object. Do not wrap in markdown code blocks.
            """

            #logger.info(f"[GEMINI PROMPT - Response Plan] Location: {location}, Event: {event_type}, IMD Available: {has_imd_data}")
            logger.debug(f"[GEMINI PROMPT FULL]\n{prompt}")

            response = self.model.generate_content(prompt)
            if response and response.text:
                logger.info(f"[GEMINI RESPONSE - Response Plan] Received response from Vertex AI")
                log_raw_data("gemini", response.text, label="response_plan", context={"location": location, "event_type": event_type})
                logger.debug(f"[GEMINI RESPONSE RAW]\n{response.text}")

                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                logger.debug(f"[GEMINI RESPONSE CLEANED]\n{cleaned_text}")
                
                plan = json.loads(cleaned_text)
                logger.info(f"[FEATURE_HEALTH] feature=gemini_response_plan status=success location={location} actions={len(plan.get('immediate_actions', []))}")
                return plan

        except Exception as e:
            logger.exception(f"[FEATURE_HEALTH] feature=gemini_response_plan status=error location={location} error={type(e).__name__}: {e}")
            logger.warning("Vertex AI decision support generation failed. Returning tactical fallback.")

        logger.info(f"[FEATURE_HEALTH] feature=gemini_response_plan status=fallback location={location} model_initialized={self.model is not None}")
        return unavailable_ai_result("response_plan", "Gemini request failed")

    def generate_preparedness_actions(self, city_forecast: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """
        
        Given a single city's 5-day forecast (
        generates a concrete, agency-owned preparedness checklist (clear drains,
        stock supplies, alert hospitals, position boats, etc.) tied to the specific
        escalation pattern in that forecast - not generic advice.

        Args:
            city_forecast: One city's entry from OpenWeatherService.fetch_forecast(),
                i.e. {city, country, latitude, longitude, daily: [...]}.
            use_mock: If True, bypasses Gemini and returns a rich fabricated
                demonstration checklist.

        Returns:
            {risk_context, actions: [{action, agency, category, priority,
             deadline_day, rationale}], ai_available, is_fallback, is_mock_demo}
        """
        from .mock_data_loader import MockDataLoader

        city = city_forecast.get("city", "Unknown City")
        country = city_forecast.get("country", "")
        daily = city_forecast.get("daily", [])


        if use_mock:
            # Mock mode still reflects the selected city's actual (mock) risk level,
            # so switching cities in the UI doesn't show a RED thunderstorm checklist
            # for a city whose own forecast is all GREEN.
            severity_rank = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
            is_routine = not daily or all(severity_rank.get(d.get("risk_level", "GREEN"), 0) == 0 for d in daily)
            mock_actions = MockDataLoader.load_mock_preparedness_actions(routine=is_routine)
            logger.info(f"Returning rich mock preparedness actions for {city} (routine={is_routine})")
            return mock_actions

        if not daily:
            logger.warning(f"No forecast days available for {city}, {country} - cannot generate actions.")
            return unavailable_ai_result("preparedness", "Gemini is unavailable or returned no usable output")

        if not self.model:
            return unavailable_ai_result("preparedness", "Gemini is unavailable or returned no usable output")

        try:
            severity_rank = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
            peak_day = max(daily, key=lambda d: severity_rank.get(d.get("risk_level", "GREEN"), 0))
            peak_index = daily.index(peak_day) + 1  # 1-based day number

            forecast_lines = "\n            ".join([
                f"- Day {i + 1} ({d.get('date')}): {d.get('risk_level')} - {d.get('dominant_weather')}, "
                f"{d.get('total_rain_mm', 0):.0f}mm rain, {d.get('max_wind_ms', 0):.0f}m/s wind, "
                f"{d.get('min_temp_c', 0):.0f}-{d.get('max_temp_c', 0):.0f}C"
                for i, d in enumerate(daily)
            ])

            prompt = f"""
            You are a Senior Disaster Preparedness Planner operating the TerraGrid Intelligence System.
            Given the 5-day risk escalation forecast below for {city}, {country}, generate a concrete,
            actionable preparedness checklist that named local agencies should execute BEFORE the risk
            materializes - not generic advice.

            5-DAY FORECAST:
            {forecast_lines}

            PEAK RISK: Day {peak_index} ({peak_day.get('risk_level')}, {peak_day.get('dominant_weather')},
            {peak_day.get('total_rain_mm', 0):.0f}mm rain, {peak_day.get('max_wind_ms', 0):.0f}m/s wind)

            STRICT OPERATIONAL DIRECTIVES:
            1. Generate 5-7 specific, concrete actions (e.g. "Clear storm drains in Ward 12", NOT "prepare for the storm").
            2. Each action must have a real-world owning agency type (municipal corporation, health dept,
               fire/rescue, disaster management authority, police, relief dept, etc.) - tailor to the
               country/region given.
            3. "deadline_day" is the forecast day number (1-{len(daily)}) the action must be done BEFORE,
               based on when that risk actually escalates in the data above - not a guess.
            4. "priority" MUST be 1 (IMMEDIATE), 2 (HIGH), or 3 (STAGED) ONLY.
            5. "rationale" must cite the specific forecast numbers driving that action (rain amount, wind
               speed, which day) - not a generic justification.
            6. Cover a mix of categories (drainage/infrastructure, medical, evacuation, supplies,
               communication) rather than repeating one category.
            7. If every day is GREEN (no material risk), return fewer, lower-priority routine-readiness
               actions instead of inventing a crisis.
            8. Return a clean JSON object matching THIS EXACT schema:
            {PREPAREDNESS_ACTIONS_SCHEMA_TEXT}

            Return ONLY the JSON object. Do not wrap in markdown code blocks.
            """

            logger.info(f"[GEMINI PROMPT - Preparedness Actions] City: {city}, {country}, Peak: Day {peak_index} ({peak_day.get('risk_level')})")
            logger.debug(f"[GEMINI PROMPT FULL]\n{prompt}")

            response = self.model.generate_content(prompt)
            if response and response.text:
                log_raw_data("gemini", response.text, label="preparedness_actions", context={"city": city, "country": country})
                logger.debug(f"[GEMINI RESPONSE RAW]\n{response.text}")

                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                actions_plan = json.loads(cleaned_text)
                actions_plan["ai_available"] = True
                actions_plan["is_fallback"] = False
                actions_plan["is_mock_demo"] = False
                logger.info(f"Generated AI preparedness checklist for {city}, {country} via Vertex AI. Actions: {len(actions_plan.get('actions', []))}")
                return actions_plan

        except Exception as e:
            logger.exception(f"Preparedness action generation failed for {city}: {type(e).__name__} - {str(e)}")
            logger.warning("Vertex AI preparedness action generation failed. Returning offline fallback.")

        return unavailable_ai_result("preparedness", "Gemini is unavailable or returned no usable output")

    def generate_agency_alerts(self, city_forecast: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """
        
        Given a single city's 5-day forecast, generates distinct, audience-
        appropriate alert messages for four agency types - FARMERS, HOSPITALS,
        NGOS, MUNICIPAL_CORPS - each with its own channel, length, vocabulary
        and tone, rather than one generic broadcast reused for everyone.

        Args:
            city_forecast: One city's entry from OpenWeatherService.fetch_forecast(),
                i.e. {city, country, latitude, longitude, daily: [...]}.
            use_mock: If True, bypasses Gemini and returns a rich fabricated
                demonstration alert set.

        Returns:
            {risk_context, alerts: [{audience, channel, headline, message,
             tone_rationale}], ai_available, is_fallback, is_mock_demo}
        """
        from .mock_data_loader import MockDataLoader

        city = city_forecast.get("city", "Unknown City")
        country = city_forecast.get("country", "")
        daily = city_forecast.get("daily", [])


        if use_mock:
            # Mock mode still reflects the selected city's actual (mock) risk
            # level, so switching cities doesn't show a RED thunderstorm alert
            # set for a city whose own forecast is all GREEN.
            severity_rank = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
            is_routine = not daily or all(severity_rank.get(d.get("risk_level", "GREEN"), 0) == 0 for d in daily)
            mock_alerts = MockDataLoader.load_mock_agency_alerts(routine=is_routine)
            logger.info(f"Returning rich mock agency alerts for {city} (routine={is_routine})")
            return mock_alerts

        if not daily:
            logger.warning(f"No forecast days available for {city}, {country} - cannot generate alerts.")
            return unavailable_ai_result("agency_alerts", "Gemini is unavailable or returned no usable output")

        if not self.model:
            return unavailable_ai_result("agency_alerts", "Gemini is unavailable or returned no usable output")

        try:
            severity_rank = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
            peak_day = max(daily, key=lambda d: severity_rank.get(d.get("risk_level", "GREEN"), 0))
            peak_index = daily.index(peak_day) + 1

            forecast_lines = "\n            ".join([
                f"- Day {i + 1} ({d.get('date')}): {d.get('risk_level')} - {d.get('dominant_weather')}, "
                f"{d.get('total_rain_mm', 0):.0f}mm rain, {d.get('max_wind_ms', 0):.0f}m/s wind, "
                f"{d.get('min_temp_c', 0):.0f}-{d.get('max_temp_c', 0):.0f}C"
                for i, d in enumerate(daily)
            ])

            prompt = f"""
            You are a Senior Public Communications Officer operating the TerraGrid Intelligence System.
            Given the 5-day risk escalation forecast below for {city}, {country}, draft FOUR distinct
            alert messages warning different audiences about the SAME risk - one each for FARMERS,
            HOSPITALS, NGOS, and MUNICIPAL_CORPS.

            5-DAY FORECAST:
            {forecast_lines}

            PEAK RISK: Day {peak_index} ({peak_day.get('risk_level')}, {peak_day.get('dominant_weather')},
            {peak_day.get('total_rain_mm', 0):.0f}mm rain, {peak_day.get('max_wind_ms', 0):.0f}m/s wind)

            STRICT OPERATIONAL DIRECTIVES:
            1. Each audience gets ONE alert. Do not merge audiences or skip one.
            2. FARMERS: short, plain-language SMS. Concrete deadlines (today/tomorrow/day names),
               practical field actions (harvest, livestock, avoid fields). No jargon.
            3. HOSPITALS: clinical/operational tone. Specific protocol names, stock categories,
               the clinical risk pathway driving admission surge. Written as an internal ops bulletin.
            4. NGOS: coordination-level detail. Resource categories, timing windows, which partner
               agency to align staging with. Written as a coordination brief.
            5. MUNICIPAL_CORPS: numbered, directive-style public safety advisory covering both
               internal infrastructure actions and the public-facing warning they must issue.
            6. Every message must cite the SAME underlying forecast numbers (rain, wind, which day)
               translated into that audience's own vocabulary - not generic weather language.
            7. If every day is GREEN (no material risk), all four alerts should be low-key routine
               status updates, not an invented crisis.
            8. Every message body MUST explicitly name the city "{city}" and the specific date(s)
               the peak risk hits (e.g. "{peak_day.get('date')}") in plain language - never rely on
               the headline alone to carry the location or timing. A recipient reading only the
               message body must be able to tell where and when this applies.
            9. Return a clean JSON object matching THIS EXACT schema:
            {AGENCY_ALERT_TEMPLATES_SCHEMA_TEXT}

            Return ONLY the JSON object. Do not wrap in markdown code blocks.
            """

            logger.info(f"[GEMINI PROMPT - Agency Alerts] City: {city}, {country}, Peak: Day {peak_index} ({peak_day.get('risk_level')})")
            logger.debug(f"[GEMINI PROMPT FULL]\n{prompt}")

            response = self.model.generate_content(prompt)
            if response and response.text:
                log_raw_data("gemini", response.text, label="agency_alerts", context={"city": city, "country": country})
                logger.debug(f"[GEMINI RESPONSE RAW]\n{response.text}")

                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                alerts_plan = json.loads(cleaned_text)
                alerts_plan["ai_available"] = True
                alerts_plan["is_fallback"] = False
                alerts_plan["is_mock_demo"] = False
                logger.info(f"Generated AI agency alerts for {city}, {country} via Vertex AI. Alerts: {len(alerts_plan.get('alerts', []))}")
                return alerts_plan

        except Exception as e:
            logger.exception(f"Agency alert generation failed for {city}: {type(e).__name__} - {str(e)}")
            logger.warning("Vertex AI agency alert generation failed. Returning offline fallback.")

        return unavailable_ai_result("agency_alerts", "Gemini is unavailable or returned no usable output")

    def generate_deep_tactical_dossier(self, event_data: Dict[str, Any], use_mock: bool = False, db_session=None) -> Dict[str, Any]:
        """
        Tier 2 Deep Intelligence Dossier: Fuses multi-source telemetry from NASA, USGS,
        OpenWeather, and GDACS, sending a multi-variable military prompt to Google Cloud Vertex AI
        (gemini-1.5-flash) to generate 2000% detailed crisis forecasting across the 8 tabs.
        
        Args:
            event_data: Incident data.
            use_mock: If True, bypasses API and returns a rich fabricated demonstration dossier.
            db_session: Optional DB session for historical queries.
        """
        event_type = event_data.get("event_type") or "Not available"
        location = event_data.get("location_name") or "Not available"
        lat = event_data.get("latitude")
        lon = event_data.get("longitude")
        source = event_data.get("source") or "Not available"

        impact = event_data.get("impact") or {}
        threat_score = impact.get("risk_score")
        area_km2 = impact.get("affected_area_km2")
        pop_at_risk = impact.get("affected_population")

        # Atmospheric telemetry only if the source stored it. Missing means missing.
        raw_data = event_data.get("data") or {}
        weather_data = raw_data.get("data") or raw_data
        wind_speed = weather_data.get("wind_speed_ms")
        wind_gust = weather_data.get("wind_gust_ms")
        humidity = weather_data.get("humidity_percent")
        temperature = weather_data.get("temperature_c")
        pressure = weather_data.get("pressure_hpa")
        weather_desc = weather_data.get("description") or "Not available"

        def _na(value, unit=""):
            return "Not available" if value is None else f"{value}{unit}"

        threat_txt = f"{threat_score} / 100" if threat_score is not None else "Not available"
        area_txt = _na(area_km2, " km²")
        pop_txt = f"{pop_at_risk:,} citizens" if pop_at_risk is not None else "Not available"
        coords_txt = f"Lat {lat}, Lon {lon}" if lat is not None and lon is not None else "Not available"
        wind_txt = _na(wind_speed, " m/s")
        gust_txt = _na(wind_gust, " m/s")
        humidity_txt = _na(humidity, "%")
        temp_txt = _na(temperature, " °C")
        pressure_txt = _na(pressure, " hPa")

        from .mock_data_loader import MockDataLoader
        from .infrastructure import InfrastructureService
        from .evacuation_zones import EvacuationZoneService
        from backend.models.event import Event
        from sqlalchemy import desc
        from concurrent.futures import ThreadPoolExecutor

        def _fetch_historical_context() -> str:
            """RAG vector search, falling back to a plain SQL spatial search, then to
            a transparent 'unavailable' note. Every branch returns something usable -
            this never comes back empty-handed, only less precise."""
            injection = "\n            HISTORICAL CONTEXT (RAG-RETRIEVED VIA VECTOR SIMILARITY):"
            if not db_session:
                return injection + "\n            - Historical database query bypassed."
            try:
                from .vector_rag_engine import VectorRAGEngine
                rag_engine = VectorRAGEngine()
                rag_context = rag_engine.get_historical_context(
                    current_incident=event_data,
                    db_session=db_session,
                    limit=5
                )
                return injection + rag_context
            except Exception as db_e:
                logger.warning(f"RAG retrieval failed: {db_e}, falling back to SQL search")
                try:
                    lat_deg = 100.0 / 111.0
                    lon_deg = 100.0 / (111.0 * math.cos(math.radians(lat)))
                    past_events = db_session.query(Event).filter(
                        Event.event_type == event_type,
                        Event.latitude.between(lat - lat_deg, lat + lat_deg),
                        Event.longitude.between(lon - lon_deg, lon + lon_deg),
                        Event.severity.is_not(None)
                    ).order_by(desc(Event.created_at)).limit(10).all()
                    if past_events:
                        return injection + f"\n            - {len(past_events)} similar incidents from spatial search (fallback)"
                    return injection + f"\n            - No similar incidents found"
                except Exception:
                    return injection + "\n            - Historical database query unavailable."

        # Fetch Hard GIS Data (OSM Infrastructure, OSRM Routes) and the RAG
        # historical lookup IN PARALLEL - these 3 sources are independent of
        # each other (none needs another's output), so there's no reason to
        # wait on them one at a time. This is a fan-out/fan-in: we submit all
        # 3, then block here until all 3 finish, so there's no concurrent use
        # of db_session - only one worker touches it, and nothing else reads
        # it until that worker is done. Each source already has its own
        # internal try/except + fallback (see infrastructure.py, evacuation_zones.py,
        # vector_rag_engine.py), so parallelizing them changes nothing about
        # what data comes back - only how long we wait for it.
        # Without coordinates there is nothing to look up, so the GIS calls are skipped.
        # The 10 km search radius is a query setting used only when the area is unknown.
        has_coords = lat is not None and lon is not None
        radius = math.sqrt(area_km2 / math.pi) if (area_km2 or 0) > 0 else 10.0
        with ThreadPoolExecutor(max_workers=3) as executor:
            osm_future = executor.submit(InfrastructureService.get_nearby_facilities, lat, lon, radius) if has_coords else None
            osrm_future = executor.submit(EvacuationZoneService.get_safe_routes, {"latitude": lat, "longitude": lon, "event_type": event_type}) if has_coords else None
            history_future = executor.submit(_fetch_historical_context)

            osm_facilities = osm_future.result() if osm_future else {}
            osrm_routing = osrm_future.result() if osrm_future else None
            history_injection = history_future.result()

        osm_hit = any([osm_facilities.get("hospitals"), osm_facilities.get("fire_stations"), osm_facilities.get("critical_infrastructure"), osm_facilities.get("shelters")])
        osrm_route_count = len(osrm_routing.get("routes") or [])
        rag_used = "RAG-RETRIEVED" in history_injection and "unavailable" not in history_injection and "bypassed" not in history_injection
        logger.info(
            f"[FEATURE_HEALTH] feature=deep_dossier_sources status=summary "
            f"osm={'hit' if osm_hit else 'empty'} "
            f"osrm_routes={osrm_route_count} "
            f"rag={'used' if rag_used else 'fallback'} "
            f"location={location}"
        )

        # Format GIS Data for Prompt Injection
        gis_injection = "\n            HARD GIS INFRASTRUCTURE (VERIFIED VIA OPENSTREETMAP):"
        if osm_facilities["hospitals"]:
            gis_injection += "\n            - HOSPITALS IN DANGER ZONE:"
            for h in osm_facilities["hospitals"]:
                gis_injection += f"\n              * {h['name']} ({h['distance_km']} km, est. {round(h['distance_km']/40, 1)}h by road)"
        if osm_facilities["fire_stations"]:
            gis_injection += "\n            - FIRE/EMERGENCY STATIONS:"
            for f in osm_facilities["fire_stations"]:
                gis_injection += f"\n              * {f['name']} ({f['distance_km']} km, est. {round(f['distance_km']/40, 1)}h by road)"
        if osm_facilities["critical_infrastructure"]:
            gis_injection += "\n            - CRITICAL UTILITIES & BRIDGES:"
            for c in osm_facilities["critical_infrastructure"]:
                gis_injection += f"\n              * [{c['type']}] {c['name']} ({c['distance_km']} km from epicenter)"
        if osm_facilities["shelters"]:
            gis_injection += "\n            - SCHOOLS/CIVIC SHELTERS:"
            for s in osm_facilities["shelters"]:
                gis_injection += f"\n              * {s['name']} ({s['distance_km']} km from epicenter)"
        
        if not any([osm_facilities["hospitals"], osm_facilities["fire_stations"], osm_facilities["critical_infrastructure"]]):
            gis_injection += "\n            - (No verified OSM infrastructure retrieved. Rely on regional/county assets.)"

        gis_injection += "\n\n            HARD GIS EVACUATION CORRIDORS (VERIFIED VIA OSRM ROAD NETWORKS):"
        if osrm_routing.get("routes"):
            for idx, route in enumerate(osrm_routing["routes"][:2]):
                gis_injection += f"\n            - ROUTE {idx+1}: Heading {route['direction']}, Distance: {route['distance_km']}km, Est. Clearance: {route['estimated_time_hours']} hrs."
        else:
            gis_injection += "\n            - (No OSRM road network geometries retrieved. Rely on cardinal direction egress.)"

        
        # Rich demonstration dossier
        if use_mock:
            mock_dossier = MockDataLoader.load_mock_dossier()
            logger.info(f"Returning rich mock demonstration dossier for {location}")
            return mock_dossier

        if not self.model:
            logger.warning("Vertex AI model unconfigured. No dossier generated.")
            return unavailable_ai_result("deep_dossier", "Gemini model is not configured")

        try:
            
            prompt = f"""
            Generate a detailed intelligence dossier for this live disaster incident using integrated sensor telemetry and geospatial analysis.

            GROUND TRUTH SENSOR TELEMETRY ("Not available" means the value is missing; do not estimate it):
            - Incident Type: {event_type}
            - Location / Jurisdiction: {location}
            - Coordinates: {coords_txt}
            - Calculated Threat Score: {threat_txt}
            - Impacted Area: {area_txt}
            - Population at Immediate Risk: {pop_txt}
            - Atmospheric Telemetry (OpenWeather):
              â€¢ Surface Wind Speed: {wind_txt} | Wind Gusts: {gust_txt}
              â€¢ Relative Humidity: {humidity_txt} | Ambient Temp: {temp_txt}
              â€¢ Barometric Pressure: {pressure_txt} | Weather: {weather_desc}
            - Source Telemetry: {source}

            NO LOCATION DATABASE: Do not name agencies, facilities, staging areas or response times unless they appear in the input above.

            {history_injection}
            {gis_injection}

            STRICT OUTPUT CONSTRAINTS:

            CAUSAL CHAIN EXTRACTION:
            You MUST include these four fields in your JSON response:
            1. trigger_event: What is the root cause of this disaster? (single sentence)
            2. infrastructure_factors: What systems/capacities are being overwhelmed? (array of 2-3 bullet points)
            3. predicted_outcome: What will happen if this continues unabated? (1-2 sentences)
            4. historical_reference: What similar past event does this resemble? (specific past incident with year/location)

            1. "quantity" MUST be INTEGER ONLY (e.g., 5, NOT "4-6")
            2. "priority" MUST be 1 (IMMEDIATE), 2 (HIGH), or 3 (STAGED) ONLY
            3. "estimated_arrival_minutes" MUST be INTEGER ONLY
            4. "confidence" MUST be 0-100 INTEGER ONLY
            5. "timeframe_hours" MUST be INTEGER (1, 3, 6, 12, 24, or 48 only)
            6. "spread_polygon" MUST be array of [lat, lon] pairs forming a closed shape
            7. "color_code" MUST be RED, ORANGE, YELLOW, or GREEN ONLY
            8. "risk_level" MUST be CRITICAL, HIGH, or MODERATE ONLY
            9. "entry_time_hours" MUST be INTEGER (0, 3, 6, 12, 24, or 48)
            10. Return ONLY the JSON object. Do not wrap in markdown code blocks.

            Generate response matching THIS EXACT schema:
            {DEEP_DOSSIER_SCHEMA_TEXT}
            """

            logger.info(f"[GEMINI PROMPT - Dossier] Location: {location}, Event: {event_type}, Threat: {threat_score}/100")
            logger.debug(f"[GEMINI PROMPT FULL]\n{prompt}")

            response = self.model.generate_content(prompt)
            if response and response.text:
                logger.info(f"[GEMINI RESPONSE - Dossier] Received response from Vertex AI")
                log_raw_data("gemini", response.text, label="deep_dossier", context={"location": location, "event_type": event_type, "threat_score": threat_score})
                logger.debug(f"[GEMINI RESPONSE RAW]\n{response.text}")
                
                # Clean response text in case of markdown formatting
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                logger.debug(f"[GEMINI RESPONSE CLEANED]\n{cleaned_text}")
                
                dossier = json.loads(cleaned_text)
                # Record which facilities came from OpenStreetMap, so the UI can
                # tell them apart from the model's own suggestions.
                if isinstance(dossier, dict):
                    dossier["osm_sources"] = [
                        {"name": item["name"], "category": category, "distance_km": item.get("distance_km")}
                        for category, key in (
                            ("hospital", "hospitals"),
                            ("fire_station", "fire_stations"),
                            ("critical_infrastructure", "critical_infrastructure"),
                            ("shelter", "shelters"),
                        )
                        for item in (osm_facilities.get(key) or [])
                        if item.get("name")
                    ]
                logger.info(f"[FEATURE_HEALTH] feature=gemini_deep_dossier status=success location={location} cascades={len(dossier.get('cascade_predictions', []))} resources={len(dossier.get('resource_matrix', []))} infrastructure={len(dossier.get('infrastructure_impact', []))}")
                return dossier

        except Exception as e:
            logger.exception(f"[FEATURE_HEALTH] feature=gemini_deep_dossier status=error location={location} error={type(e).__name__}: {e}")
            logger.warning("Returning operational contingency dossier.")

        logger.info(f"[FEATURE_HEALTH] feature=gemini_deep_dossier status=fallback location={location} model_initialized={self.model is not None}")
        return unavailable_ai_result("deep_dossier", "Gemini request failed")

# Lazy-load singleton to avoid blocking startup during Gemini SDK initialization
_decision_support_service = None

def get_decision_support_service() -> DecisionSupportService:
    """Lazy-load the decision support service on first use."""
    global _decision_support_service
    if _decision_support_service is None:
        _decision_support_service = DecisionSupportService()
    return _decision_support_service
