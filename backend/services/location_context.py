"""
Location-specific agency and infrastructure context for Gemini prompts.
Enables region-specific, hyper-realistic response recommendations.
"""

LOCATION_CONTEXT = {
    "louisiana": {
        "country": "USA",
        "region": "Louisiana",
        "fema_region": "FEMA Region 6",
        "primary_agency": "Louisiana Department of Wildlife and Fisheries",
        "secondary_agencies": [
            "FEMA Region 6 - Gulf Coast Response Division",
            "U.S. Coast Guard Sector New Orleans",
            "Louisiana State Police - Special Operations Division",
            "National Guard - Joint Task Force"
        ],
        "hospitals": [
            "Louisiana State University Medical Center - New Orleans",
            "Ochsner Medical Center - New Orleans",
            "Tulane Medical Center - New Orleans",
            "Charity Hospital - New Orleans",
            "Coastal Regional Medical Center - Port Fourchon"
        ],
        "emergency_services": [
            "New Orleans Fire Department",
            "Jefferson Parish Sheriff - Emergency Response",
            "St. Bernard Parish Police",
            "Louisiana State Police District 4",
            "USCG Station Galveston"
        ],
        "staging_areas": [
            "Port of South Louisiana - Multi-Purpose Terminal",
            "Louis Armstrong New Orleans International Airport",
            "Baton Rouge Port Terminal - Staging Area",
            "Lake Pontchartrain Authority Landing",
            "Belle Chasse Airfield - USCG Facility"
        ],
        "avg_response_times_minutes": {
            "helicopter": 18,
            "ambulance": 10,
            "fire_engine": 12,
            "rescue_team": 25,
            "water_purification_unit": 45
        },
        "critical_infrastructure": {
            "power_grids": ["Entergy Louisiana - Southeast Division", "SWEPCO - Port Industrial Grid"],
            "water_treatment": ["New Orleans Water Department - Main Treatment", "East Jefferson Water Authority"],
            "ports": ["Port of South Louisiana", "Baton Rouge Port"],
            "highways": ["I-10", "US-90", "LA-1", "US-61"]
        }
    },
    "india": {
        "country": "India",
        "region": "National",
        "primary_agency": "NDRF - National Disaster Response Force",
        "secondary_agencies": [
            "State Disaster Management Authority",
            "Indian Armed Forces - Rapid Response",
            "National Rapid Response System",
            "State Police - Disaster Management Wing"
        ],
        "hospitals": [
            "AIIMS Delhi - Trauma Center",
            "Safdarjung Hospital - New Delhi",
            "Institute of Medical Sciences - Delhi",
            "Rajendra Institute of Medical Sciences - Ranchi",
            "PGI Chandigarh - Emergency Response"
        ],
        "emergency_services": [
            "Delhi Fire Service",
            "Mumbai Fire Brigade",
            "NDRF - 11 Battalion (All-India)",
            "State Police Disaster Management",
            "Civil Defence Authority"
        ],
        "staging_areas": [
            "Indira Gandhi Stadium - New Delhi",
            "Jawaharlal Nehru Stadium - Delhi",
            "Bombay High Ground - Mumbai",
            "National Fire Academy - Nagpur"
        ],
        "avg_response_times_minutes": {
            "helicopter": 25,
            "ambulance": 15,
            "fire_engine": 18,
            "rescue_team": 30,
            "water_purification_unit": 50
        },
        "critical_infrastructure": {
            "power_grids": ["Power Grid Corporation of India", "National Power Distribution Grid"],
            "water_treatment": ["Municipal Water Supply - State Boards"],
            "ports": ["Mumbai Port", "Chennai Port", "Kolkata Port"],
            "highways": ["NH-1", "NH-2", "NH-4", "Golden Quadrilateral"]
        }
    },
    "japan": {
        "country": "Japan",
        "region": "National",
        "primary_agency": "Japan Disaster Relief (JDR)",
        "secondary_agencies": [
            "Self-Defense Forces - Emergency Response",
            "National Police Agency - Disaster Response",
            "Prefectural Disaster Management Headquarters",
            "Japan Maritime Self-Defense Force"
        ],
        "hospitals": [
            "National Disaster Medical Center - Tokyo",
            "Okinawa Prefectural Hospital",
            "Tohoku Medical Center - Sendai",
            "Trauma Center Network - Tokyo"
        ],
        "emergency_services": [
            "Tokyo Fire Department - Disaster Response",
            "Osaka City Fire Bureau",
            "Prefectural Police - Disaster Coordinating Unit",
            "Japan Coast Guard - Search and Rescue"
        ],
        "staging_areas": [
            "Japan Ground Self-Defense Force Base - Asaka",
            "Akasaka Palace - Emergency Command Center",
            "Tokyo Metropolitan Government Building - Disaster Center"
        ],
        "avg_response_times_minutes": {
            "helicopter": 20,
            "ambulance": 12,
            "fire_engine": 15,
            "rescue_team": 22,
            "water_purification_unit": 40
        },
        "critical_infrastructure": {
            "power_grids": ["Tokyo Electric Power", "Kansai Electric Power", "Tohoku Electric Power"],
            "water_treatment": ["Tokyo Metropolitan Waterworks Bureau"],
            "ports": ["Port of Tokyo", "Port of Osaka", "Port of Yokohama"],
            "highways": ["Tohoku Expressway", "Joban Expressway", "Shuto Expressway"]
        }
    },
    "california": {
        "country": "USA",
        "state": "California",
        "fema_region": "FEMA Region 9",
        "primary_agency": "California Governor's Office of Emergency Services (Cal OES)",
        "secondary_agencies": [
            "FEMA Region 9 - Pacific Area Response",
            "California National Guard - Joint Operations",
            "U.S. Forest Service - Region 5",
            "San Francisco Fire Department - Urban Search and Rescue"
        ],
        "hospitals": [
            "UCSF Medical Center - San Francisco",
            "Cedars-Sinai Medical Center - Los Angeles",
            "UC San Diego Medical Center",
            "Stanford Hospital - Stanford",
            "Ronald Reagan UCLA Medical Center"
        ],
        "emergency_services": [
            "Los Angeles Fire Department",
            "San Francisco Fire Department",
            "California Highway Patrol - Emergency Response",
            "San Diego Police - Disaster Services",
            "Santa Clara County Fire Department"
        ],
        "staging_areas": [
            "Oakland Coliseum",
            "Dodger Stadium - Los Angeles",
            "Petco Park - San Diego",
            "Bay Area Fairgrounds - San Mateo"
        ],
        "avg_response_times_minutes": {
            "helicopter": 22,
            "ambulance": 14,
            "fire_engine": 16,
            "rescue_team": 28,
            "water_purification_unit": 48
        },
        "critical_infrastructure": {
            "power_grids": ["PG&E - Northern California", "Southern California Edison", "SDG&E"],
            "water_treatment": ["San Francisco Public Utilities", "Los Angeles Department of Water and Power"],
            "ports": ["Port of Long Beach", "Port of Los Angeles", "Port of Oakland"],
            "highways": ["I-405", "I-5", "I-80", "US-101"]
        }
    },
    "default": {
        "country": "International",
        "region": "Unknown",
        "primary_agency": "Local Disaster Management Authority",
        "secondary_agencies": [
            "National Emergency Response Service",
            "International Red Cross / Red Crescent",
            "UN Office for Coordination of Humanitarian Affairs"
        ],
        "hospitals": ["Primary Medical Center - Regional", "Secondary Hospital - Regional"],
        "emergency_services": ["Local Emergency Services", "Regional Disaster Response"],
        "staging_areas": ["Local Government Facility", "Regional Assembly Point"],
        "avg_response_times_minutes": {
            "helicopter": 30,
            "ambulance": 20,
            "fire_engine": 25,
            "rescue_team": 35,
            "water_purification_unit": 60
        },
        "critical_infrastructure": {
            "power_grids": ["Local Power Grid Operator"],
            "water_treatment": ["Municipal Water Authority"],
            "ports": ["Regional Port Authority"],
            "highways": ["Major Highway Network"]
        }
    }
}

def get_location_context(location_name: str) -> dict:
    """
    Returns location-specific context for Gemini prompt injection.
    Falls back to default if location not found.
    """
    location_key = location_name.lower().strip()
    
    # Direct match
    if location_key in LOCATION_CONTEXT:
        return LOCATION_CONTEXT[location_key]
    
    # Partial match (e.g., "Louisiana" or "New Orleans" -> louisiana)
    for key in LOCATION_CONTEXT.keys():
        if key != "default" and key in location_key:
            return LOCATION_CONTEXT[key]
    
    # Reverse partial match
    for key in LOCATION_CONTEXT.keys():
        if key != "default" and location_key in key:
            return LOCATION_CONTEXT[key]
    
    return LOCATION_CONTEXT["default"]
