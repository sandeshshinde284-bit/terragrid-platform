import os
import json
import hashlib
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class GeocodingService:
    """
    Intelligent Reverse Geocoding Service powered by Gemini.
    Translates messy, multi-line emergency alerts or raw coordinates 
    into clean, standardized "City, Country" location names.
    Includes a permanent PostgreSQL cache to save LLM tokens.
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
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel(model_name)
                logger.info(f"GeocodingService: Initialized Vertex AI {model_name}.")
            else:
                logger.warning("GeocodingService: GCP_PROJECT_ID is not configured in .env. Will use fallback.")
                
        except ImportError:
            logger.warning("GeocodingService: google-cloud-aiplatform SDK not installed. Will use fallback.")
        except Exception as e:
            logger.warning(f"GeocodingService: Could not initialize Vertex AI SDK ({type(e).__name__}: {e}). Will use fallback.")

    @staticmethod
    def _create_signature(raw_text: str, lat: float, lon: float) -> str:
        """Create a unique MD5 signature for cache lookups."""
        content = f"{round(lat, 3)}_{round(lon, 3)}_{raw_text.strip()}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def format_location(self, raw_text: str, lat: float, lon: float, db: Optional[Session] = None) -> str:
        """
        Formats a raw location string into a clean "City, State/Country" format.
        Checks the PostgreSQL cache first. Falls back gracefully on any error.
        """
        if not raw_text or raw_text == "Unknown Location":
            return "Unknown Location"

        # Short strings that already look good (e.g. "Delhi, IN") don't need LLM processing
        if len(raw_text) < 30 and ";" not in raw_text and "waters" not in raw_text.lower():
            return raw_text.strip()

        signature = self._create_signature(raw_text, lat, lon)

        # 1. Check PostgreSQL Cache
        if db:
            try:
                from backend.models.geocoding import GeocodingCache
                cached = db.query(GeocodingCache).filter(GeocodingCache.location_signature == signature).first()
                if cached:
                    logger.debug(f"Geocoding Cache Hit for {raw_text[:20]} -> {cached.formatted_location}")
                    return cached.formatted_location
            except Exception as db_e:
                logger.warning(f"Failed to query geocoding cache: {db_e}")

        # 2. Call Gemini LLM (Anchored by Coordinates)
        formatted_result = None
        if self.model:
            try:
                # Structured prompt anchored by numerical coordinates to prevent hallucinations
                prompt = (
                    f"You are an expert GIS reverse geocoding assistant for an emergency dashboard.\n"
                    f"A disaster alert has been issued near latitude {lat}, longitude {lon}.\n"
                    f"The raw description is: \"{raw_text}\".\n"
                    f"Identify the primary municipality or city, state/province, and standard 2-letter ISO country code.\n"
                    f"Respond ONLY with a concise string in the format: 'City, State, CountryCode' (e.g. 'Apalachicola, Florida, US' or 'Kathmandu, Bagmati, NP'). "
                    f"Do not include quotes, markdown, or commentary."
                )
                
                response = self.model.generate_content(prompt)
                if response and response.text:
                    cleaned = response.text.strip().replace('"', '').replace('\n', '')
                    if len(cleaned) < 50:
                        formatted_result = cleaned
                        logger.info(f"Geocoded via Gemini: '{raw_text[:25]}...' -> '{formatted_result}'")
            except Exception as ai_e:
                logger.warning(f"Gemini geocoding failed or timed out: {ai_e}")

        # 3. Graceful Fallback Strategy (If LLM fails or is disabled)
        if not formatted_result:
            # Fall back to clean string splitting (take first location before semicolon)
            if ";" in raw_text:
                formatted_result = raw_text.split(";")[0].strip()
            else:
                formatted_result = raw_text.strip()
            
            # Ensure it never overflows 45 characters
            if len(formatted_result) > 45:
                formatted_result = formatted_result[:42] + "..."

        # 4. Save to PostgreSQL Cache
        if db and formatted_result:
            try:
                from backend.models.geocoding import GeocodingCache
                cache_entry = GeocodingCache(
                    location_signature=signature,
                    formatted_location=formatted_result
                )
                db.add(cache_entry)
                db.commit()
            except Exception as save_e:
                db.rollback()
                logger.debug(f"Failed to save geocoding cache: {save_e}")

        return formatted_result

    def batch_format_locations(self, items: List[Dict[str, Any]], db: Optional[Session] = None) -> Dict[str, str]:
        """
        Batch geocodes up to 50 raw location strings in a SINGLE Gemini request.
        Optimized with:
        - Speed Win #6: Single bulk SQL query for cache hits using .in_(signatures)
        - Speed Win #9: Pre-prompt deduplication by signature to maximize unique 50-slot capacity
        - Speed Win #8: Single bulk db.add_all() commit
        """
        results: Dict[str, str] = {}
        sig_to_items: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Pre-filter items and calculate signatures
        for item in items:
            raw_text = item.get("raw_text", "").strip()
            if not raw_text or raw_text == "Unknown Location":
                results[raw_text] = "Unknown Location"
                continue
                
            # Short strings that already look good don't need LLM
            if len(raw_text) < 30 and ";" not in raw_text and "waters" not in raw_text.lower():
                results[raw_text] = raw_text
                continue

            lat = item.get("lat", 0.0)
            lon = item.get("lon", 0.0)
            sig = self._create_signature(raw_text, lat, lon)
            
            if sig not in sig_to_items:
                sig_to_items[sig] = []
            
            item_copy = item.copy()
            item_copy["signature"] = sig
            sig_to_items[sig].append(item_copy)

        # Speed Win #6: 1 single SQL query for all cache lookups instead of N queries
        if db and sig_to_items:
            try:
                from backend.models.geocoding import GeocodingCache
                all_sigs = list(sig_to_items.keys())
                cached_records = db.query(GeocodingCache).filter(
                    GeocodingCache.location_signature.in_(all_sigs)
                ).all()
                for rec in cached_records:
                    if rec.location_signature in sig_to_items:
                        for it in sig_to_items[rec.location_signature]:
                            results[it["raw_text"]] = rec.formatted_location
                        del sig_to_items[rec.location_signature]
            except Exception as cache_e:
                logger.warning(f"Batch geocoding cache lookup error: {cache_e}")

        # Speed Win #9: Deduplicate by signature so duplicates don't waste 50-slot prompt budget
        unique_uncached = [items_list[0] for items_list in sig_to_items.values()]

        if not unique_uncached:
            return results

        if len(unique_uncached) > 50:
            logger.warning(f"Batch geocoding unique size ({len(unique_uncached)}) exceeded 50; processing first 50.")

        # 2. Call Gemini Batch if model is available (max 50 unique items in one prompt)
        batch_ai_map: Dict[str, str] = {}
        if self.model and unique_uncached:
            try:
                batch_items = unique_uncached[:50]
                prompt_items = [
                    {
                        "id": idx,
                        "raw_location": it.get("raw_text"),
                        "lat": it.get("lat"),
                        "lon": it.get("lon")
                    }
                    for idx, it in enumerate(batch_items)
                ]

                prompt = (
                    "You are an expert GIS reverse geocoding assistant for a real-time emergency disaster dashboard.\n"
                    "Analyze this JSON list of disaster locations and geographical coordinates.\n"
                    "For each item:\n"
                    "1. Identify the primary impacted City, Town, or Municipality (prioritize populated areas over offshore towers or lists of marine boundaries).\n"
                    "2. Identify the State, Province, or Region.\n"
                    "3. Identify the standard 2-letter ISO Country Code (e.g., US, IN, CN, NP, JP, PH).\n"
                    "Return a JSON object mapping the numeric string id to an exact string formatted as: 'City, State, CountryCode'.\n"
                    "Example outputs: {\"0\": \"Apalachicola, Florida, US\", \"1\": \"Kathmandu, Bagmati, NP\", \"2\": \"Mumbai, Maharashtra, IN\"}\n\n"
                    f"INPUT LOCATIONS:\n{json.dumps(prompt_items)}"
                )

                # Set 15-second timeout to prevent ingestion stalls
                try:
                    response = self.model.generate_content(prompt, request_options={"timeout": 15})
                except TypeError:
                    response = self.model.generate_content(prompt)
                    
                if response and response.text:
                    # Clean response text if wrapped in markdown
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.startswith("```"):
                        cleaned_text = cleaned_text[3:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                        
                    parsed = json.loads(cleaned_text.strip())
                    new_cache_entries = []
                    
                    for idx, it in enumerate(batch_items):
                        val = parsed.get(str(idx)) or parsed.get(idx)
                        if val and isinstance(val, str) and len(val) < 60:
                            clean_val = val.strip().replace('"', '').replace('\n', '')
                            batch_ai_map[it["signature"]] = clean_val
                            
                            # Fan out to all matching items that shared this signature
                            if it["signature"] in sig_to_items:
                                for match_it in sig_to_items[it["signature"]]:
                                    results[match_it["raw_text"]] = clean_val
                            
                            # Collect for bulk PostgreSQL cache insert (Speed Win #8)
                            if db:
                                from backend.models.geocoding import GeocodingCache
                                new_cache_entries.append(
                                    GeocodingCache(
                                        location_signature=it["signature"],
                                        formatted_location=clean_val
                                    )
                                )
                    
                    # Single bulk insert and commit (Speed Win #8)
                    if db and new_cache_entries:
                        try:
                            db.add_all(new_cache_entries)
                            db.commit()
                        except Exception as save_e:
                            db.rollback()
                            logger.debug(f"Failed to bulk-save geocoding cache: {save_e}")
                            
                    logger.info(f"Successfully geocoded {len(new_cache_entries)} unique locations in 1 Gemini batch request.")
            except Exception as e:
                logger.warning(f"Gemini batch geocoding failed or timed out ({e}). Applying graceful fallback.")

        # 3. Fallback for any remaining uncached items
        for sig, items_list in sig_to_items.items():
            for it in items_list:
                raw = it.get("raw_text", "")
                if raw not in results:
                    if ";" in raw:
                        fallback_val = raw.split(";")[0].strip()
                    else:
                        fallback_val = raw.strip()
                    if len(fallback_val) > 45:
                        fallback_val = fallback_val[:42] + "..."
                    results[raw] = fallback_val

        return results

geocoding_service = GeocodingService()
