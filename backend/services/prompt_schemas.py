"""
Structured prompt schemas for Gemini AI responses.
Ensures consistent JSON output with numeric constraints and enums.
"""

RESOURCE_ITEM = {
    "resource": "string (enum: Helicopter, Ambulance, Fire Engine, Water Truck, Search Dog, Rescue Team, Mobile Hospital, Water Purification Unit)",
    "quantity": "integer (exact number, not range)",
    "unit_measure": "string (enum: Units, Personnel, Vehicles, Teams)",
    "assigned_agency": "string (full agency name with jurisdiction)",
    "deployment_location": "string (street address or landmark)",
    "estimated_arrival_minutes": "integer (0-480)",
    "priority": "integer (1=IMMEDIATE, 2=HIGH, 3=STAGED)",
    "confidence": "integer (0-100, how confident is this estimate?)"
}

CASCADE_PREDICTION_ITEM = {
    "timeframe_hours": "integer (1, 3, 6, 12, 24, or 48 only)",
    "perimeter_delta_km2": "float (area expansion)",
    "spread_polygon": "array of [lat, lon] pairs forming a closed shape (minimum 4 points)",
    "wind_influence_percent": "integer (0-100, how much does wind push the spread?)",
    "color_code": "string (RED, ORANGE, YELLOW, or GREEN only)",
    "primary_risks": [
        {
            "facility_type": "string (Hospital, School, Power Grid, Water Treatment, Bridge, Fire Station)",
            "count_affected": "integer (how many facilities of this type)",
            "names": "array of facility names entering danger zone in this timeframe"
        }
    ]
}

INFRASTRUCTURE_ITEM = {
    "facility_name": "string (real name, e.g. 'St. Jude Regional Hospital')",
    "facility_type": "string (Hospital, Power Grid, Water Treatment, Bridge, Fire Station, School, Shelter)",
    "distance_km": "float",
    "risk_level": "string (CRITICAL, HIGH, or MODERATE)",
    "action_required": "string (specific tactical action)",
    "entry_time_hours": "integer (when does it enter danger zone? 0, 3, 6, 12, 24, 48)",
    "confidence": "integer (0-100, how confident is this risk assessment?)"
}

CHOKE_POINT = {
    "location": "string (specific street/highway name)",
    "impact": "string (CRITICAL, HIGH, or MODERATE)",
    "width_meters": "integer"
}

SAFE_ASSEMBLY_ZONE = {
    "name": "string (e.g. 'Lincoln High School Football Stadium')",
    "latitude": "float",
    "longitude": "float",
    "capacity_people": "integer"
}

EVACUATION_CORRIDORS = {
    "primary_corridor": "string (specific highway or transit route name)",
    "capacity_vehicles_per_hour": "integer",
    "estimated_clearance_hours": "float",
    "choke_points": [CHOKE_POINT],
    "safe_assembly_zones": [SAFE_ASSEMBLY_ZONE]
}

DEEP_DOSSIER_SCHEMA_TEXT = """
{
  "country_context": "string (e.g. 'FEMA Region 6 Jurisdiction: Port Fourchon Sector, Louisiana')",
  "severity_assessment": "string (2-3 sentence tactical overview in sentence case)",
  "immediate_actions": ["string (Action 1)", "string (Action 2)", "string (Action 3)"],
  "resource_matrix": [
    {
      "resource": "string (enum: Helicopter, Ambulance, Fire Engine, Water Truck, Search Dog, Rescue Team, Mobile Hospital, Water Purification Unit)",
      "quantity": "integer",
      "unit_measure": "string (enum: Units, Personnel, Vehicles, Teams)",
      "assigned_agency": "string (full agency name with jurisdiction)",
      "deployment_location": "string (real street/location)",
      "estimated_arrival_minutes": "integer (0-480)",
      "priority": "integer (1=IMMEDIATE, 2=HIGH, 3=STAGED)",
      "confidence": "integer (0-100)"
    }
  ],
  "cascade_predictions": [
    {
      "timeframe_hours": "integer (1, 3, 6, 12, 24, or 48 only)",
      "perimeter_delta_km2": "float",
      "spread_polygon": "[[lat, lon], [lat, lon], [lat, lon], [lat, lon], ...]",
      "wind_influence_percent": "integer (0-100)",
      "color_code": "string (RED, ORANGE, YELLOW, or GREEN only)",
      "primary_risks": [
        {
          "facility_type": "string",
          "count_affected": "integer",
          "names": ["string", "string"]
        }
      ]
    }
  ],
  "critical_infrastructure": [
    {
      "facility_name": "string (real name)",
      "facility_type": "string",
      "distance_km": "float",
      "risk_level": "string (CRITICAL, HIGH, or MODERATE)",
      "action_required": "string",
      "entry_time_hours": "integer (0, 3, 6, 12, 24, or 48)",
      "confidence": "integer (0-100)"
    }
  ],
  "evacuation_corridors": {
    "primary_corridor": "string (highway name)",
    "capacity_vehicles_per_hour": "integer",
    "estimated_clearance_hours": "float",
    "choke_points": [
      {
        "location": "string",
        "impact": "string (CRITICAL, HIGH, or MODERATE)",
        "width_meters": "integer"
      }
    ],
    "safe_assembly_zones": [
      {
        "name": "string",
        "latitude": "float",
        "longitude": "float",
        "capacity_people": "integer"
      }
    ]
  },
  "vulnerable_demographics": {
    "facilities_at_risk": ["string"],
    "estimated_displaced_citizens": "integer",
    "special_needs_assistance_required": "string"
  }
}
"""

RESPONSE_PLAN_SCHEMA_TEXT = """
{
  "country_context": "string (e.g. 'FEMA Region 6 Jurisdiction: Port Fourchon Sector, Louisiana')",
  "severity_assessment": "string (2-sentence tactical overview in sentence case)",
  "immediate_actions": ["string (Action 1)", "string (Action 2)", "string (Action 3)"],
  "resource_allocation": [
    {
      "resource": "string (enum: Helicopter, Ambulance, Fire Engine, Water Truck, Search Dog, Rescue Team, Mobile Hospital, Water Purification Unit)",
      "quantity": "integer",
      "unit_measure": "string (enum: Units, Personnel, Vehicles, Teams)",
      "assigned_agency": "string (full agency name)",
      "estimated_arrival_minutes": "integer",
      "priority": "integer (1=IMMEDIATE, 2=HIGH, 3=STAGED)",
      "confidence": "integer (0-100)"
    }
  ],
  "evacuation_guidance": "string (Specific highway corridors, choke-point warnings, designated shelters)"
}
"""
