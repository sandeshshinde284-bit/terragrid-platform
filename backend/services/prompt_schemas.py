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
  "trigger_event": "string (e.g., 'Northeast monsoon bringing 120mm rainfall')",
  "infrastructure_factors": [
    "string (e.g., 'Dam drainage capacity only 80mm/h')",
    "string (e.g., 'Upstream gates opened at emergency flow rate')"
  ],
  "predicted_outcome": "string (e.g., 'Flash flooding at 4 PM')",
  "historical_reference": "string (e.g., 'Similar to Oct 2019 (500 displaced)')",
  "immediate_actions": ["string (Action 1)", "string (Action 2)", "string (Action 3)", "string (Action 4)", "string (Action 5)"],
  "resource_matrix": [
    {
      "resource": "string (enum: Helicopter, Ambulance, Fire Engine, Water Truck, Search Dog, Rescue Team, Mobile Hospital, Water Purification Unit)",
      "quantity": "integer",
      "unit_measure": "string (enum: Units, Personnel, Vehicles, Teams)",
      "assigned_agency": "string (full agency name with jurisdiction)",
      "deployment_location": "string (real street/location)",
      "estimated_arrival_minutes": "integer (0-480)",
      "priority": "integer (1=IMMEDIATE, 2=HIGH, 3=STAGED)",
      "confidence": "integer (0-100)",
      "purpose": "string (one short line: what this resource does in this incident, e.g. 'Aerial damage assessment of collapsed routes')"
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
  "trigger_event": "string (e.g., 'Northeast monsoon bringing 120mm rainfall')",
  "infrastructure_factors": [
    "string (e.g., 'Dam drainage capacity only 80mm/h')",
    "string (e.g., 'Upstream gates opened at emergency flow rate')"
  ],
  "predicted_outcome": "string (e.g., 'Flash flooding at 4 PM')",
  "historical_reference": "string (e.g., 'Similar to Oct 2019 (500 displaced)')",
  "immediate_actions": ["string (Action 1)", "string (Action 2)", "string (Action 3)", "string (Action 4)", "string (Action 5)"],
  "immediate_action_evidence": ["string: the input fact that supports Action 1 (source, threat score, facility name and distance, or route), or 'no supporting input'", "same for Action 2", "same for Action 3", "same for Action 4", "same for Action 5"],
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

PREPAREDNESS_ACTIONS_SCHEMA_TEXT = """
{
  "risk_context": "string (1-2 sentence summary of the escalation window driving these actions, e.g. 'Thunderstorm risk escalates to RED by Day 3 with 46mm rainfall and 20m/s winds.')",
  "actions": [
    {
      "action": "string (specific, concrete task - e.g. 'Clear and desilt monsoon drains in low-lying wards')",
      "agency": "string (specific real-world owning body - e.g. 'Municipal Corporation - Drainage Dept')",
      "category": "string (enum: DRAINAGE, MEDICAL, EVACUATION, SUPPLIES, COMMUNICATION, INFRASTRUCTURE)",
      "priority": "integer (1=IMMEDIATE, 2=HIGH, 3=STAGED)",
      "deadline_day": "integer (1-5, which forecast day this must be completed before)",
      "rationale": "string (1 sentence - why this action, tied to the specific weather/risk data given)"
    }
  ]
}
"""

AGENCY_ALERT_TEMPLATES_SCHEMA_TEXT = """
{
  "risk_context": "string (1-2 sentence summary of the escalation window these alerts are warning about)",
  "alerts": [
    {
      "audience": "string (enum: FARMERS, HOSPITALS, NGOS, MUNICIPAL_CORPS)",
      "channel": "string (the realistic delivery channel for this audience - e.g. 'SMS Broadcast', 'Radio Advisory', 'Hospital Ops Bulletin', 'NGO Coordination Brief', 'Public Safety Advisory')",
      "headline": "string (under 10 words, audience-appropriate urgency)",
      "message": "string (the actual message body - length, vocabulary, and tone MUST fit the audience: short plain-language SMS for farmers, clinical/operational for hospitals, coordination-focused for NGOs, directive/public-safety for municipal corps)",
      "tone_rationale": "string (1 sentence - why this length/tone/channel fits this specific audience)"
    }
  ]
}
"""

SATELLITE_CROSS_VALIDATION_SCHEMA_TEXT = """
{
  "visual_consistency": "string (CONSISTENT, PARTIALLY_CONSISTENT, INCONSISTENT, or INCONCLUSIVE only)",
  "visible_evidence": [
    "string (specific thing actually visible in the image, e.g. 'dense smoke plume over the northeast quadrant of the bounding box')"
  ],
  "confidence_percent": "integer (0-100, how confident is this visual read, given image resolution/cloud cover/time of day)",
  "discrepancy_notes": "string (if PARTIALLY_CONSISTENT or INCONSISTENT, what doesn't match the reported event_type/severity; empty string if CONSISTENT)",
  "reasoning": "string (2-3 sentences, what you actually see in the image and why it does or doesn't support the reported incident)"
}
"""
