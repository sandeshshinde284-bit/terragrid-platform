"""
Structured prompt schemas for Gemini AI responses.
Ensures consistent JSON output with numeric constraints and enums.
"""

import json

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
    "facility_name": "string (facility name from the input data only; 'Not in input data' if absent)",
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
    "name": "string (site name from the input data only; 'Not in input data' if absent)",
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

# ---------------------------------------------------------------------------
# Incident output schemas (Gemini structured output).
#
# The same dict is (a) sent to Gemini as response_schema, so the service
# enforces the shape, and (b) rendered into the prompt text, so the prompt and
# the enforced schema cannot drift apart. A field marked nullable is returned as
# null when the input does not support it. The model is never asked to invent a
# name, number or time just to fill a slot.
# ---------------------------------------------------------------------------

def _str(desc, nullable=False):
    return {"type": "STRING", "description": desc, **({"nullable": True} if nullable else {})}


def _int(desc, nullable=False):
    return {"type": "INTEGER", "description": desc, **({"nullable": True} if nullable else {})}


def _num(desc, nullable=False):
    return {"type": "NUMBER", "description": desc, **({"nullable": True} if nullable else {})}


def _arr(items, desc, nullable=False):
    return {"type": "ARRAY", "items": items, "description": desc, **({"nullable": True} if nullable else {})}


def _obj(props, desc, required=None):
    node = {"type": "OBJECT", "description": desc, "properties": props}
    if required:
        node["required"] = required
    return node


_NULL_IF_NOT_IN_INPUT = "null if the input does not contain it."

RESPONSE_PLAN_GEMINI_SCHEMA = _obj({
    "country_context": _str("Jurisdiction, taken only from the input. " + _NULL_IF_NOT_IN_INPUT, True),
    "severity_assessment": _str("Two sentences, sentence case, based only on the input. null if the input is insufficient.", True),
    "trigger_event": _str("One sentence on the cause, from the input telemetry only. " + _NULL_IF_NOT_IN_INPUT, True),
    "infrastructure_factors": _arr(_str("A fact from the input."), "Systems or capacities under pressure, from the input only. Empty list if none."),
    "predicted_outcome": _str("What follows if the input trend continues. null if the input does not support a prediction.", True),
    "historical_reference": _str("A past event, only if an input history record matches it. Otherwise null.", True),
    "immediate_actions": _arr(_str("One concrete action for this incident."), "Up to five actions. Each must rest on an input fact."),
    "immediate_action_evidence": _arr(_str("The input fact behind the matching action, or 'no supporting input'."), "One entry per action, in the same order."),
    "resource_allocation": _arr(_obj({
        "resource": _str("Resource type."),
        "quantity": _int("Number of units. null if the input does not justify a number.", True),
        "unit_measure": _str("Units, Personnel, Vehicles or Teams."),
        "assigned_agency": _str("Agency name from the input only. " + _NULL_IF_NOT_IN_INPUT, True),
        "estimated_arrival_minutes": _int("Only if the input gives a distance or route to base it on. Otherwise null.", True),
        "priority": _int("1 = IMMEDIATE, 2 = HIGH, 3 = STAGED."),
    }, "One resource need.", ["resource", "priority"]), "Resource needs. Empty list if none is supported."),
    "evacuation_guidance": _str("Corridors and shelters named in the input only. " + _NULL_IF_NOT_IN_INPUT, True),
}, "Crisis response plan for one incident.", ["immediate_actions", "immediate_action_evidence"])

DEEP_DOSSIER_GEMINI_SCHEMA = _obj({
    "country_context": _str("Jurisdiction, taken only from the input. " + _NULL_IF_NOT_IN_INPUT, True),
    "severity_assessment": _str("Two to three sentences, sentence case, based only on the input.", True),
    "trigger_event": _str("One sentence on the cause, from the input telemetry only. " + _NULL_IF_NOT_IN_INPUT, True),
    "infrastructure_factors": _arr(_str("A fact from the input."), "Systems or capacities under pressure, from the input only. Empty list if none."),
    "predicted_outcome": _str("What follows if the input trend continues. null if the input does not support a prediction.", True),
    "historical_reference": _str("A past event, only if an input history record matches it. Otherwise null.", True),
    "immediate_actions": _arr(_str("One concrete action for this incident."), "Up to five actions. Each must rest on an input fact."),
    "resource_matrix": _arr(_obj({
        "resource": _str("Resource type."),
        "quantity": _int("Number of units. null if the input does not justify a number.", True),
        "unit_measure": _str("Units, Personnel, Vehicles or Teams."),
        "assigned_agency": _str("Agency name from the input only. " + _NULL_IF_NOT_IN_INPUT, True),
        "deployment_location": _str("Location from the input only. " + _NULL_IF_NOT_IN_INPUT, True),
        "estimated_arrival_minutes": _int("Only if the input gives a distance or route to base it on. Otherwise null.", True),
        "priority": _int("1 = IMMEDIATE, 2 = HIGH, 3 = STAGED."),
        "purpose": _str("One short line on what the resource does in this incident.", True),
    }, "One resource need.", ["resource", "priority"]), "Resource needs. Empty list if none is supported."),
    "cascade_predictions": _arr(_obj({
        "timeframe_hours": _int("One of 1, 3, 6, 12, 24, 48."),
        "perimeter_delta_km2": _num("Expansion area. null unless the input supports it.", True),
        "spread_polygon": _arr(_arr(_num("Latitude or longitude."), "[lat, lon] pair."), "Closed outline. null unless the input supports a spread model.", True),
        "wind_influence_percent": _int("0-100. null unless the input wind data supports it.", True),
        "color_code": _str("RED, ORANGE, YELLOW or GREEN."),
        "primary_risks": _arr(_obj({
            "facility_type": _str("Facility category."),
            "count_affected": _int("Number of facilities of this type in the input. null if none.", True),
            "names": _arr(_str("A facility name from the input."), "Facility names from the input only."),
        }, "One risk group."), "Risks by facility type. Empty list if none."),
    }, "One time-step projection."), "Projections. Empty list if the input does not support any."),
    "critical_infrastructure": _arr(_obj({
        "facility_name": _str("Exact facility name from the input. Never invent a name."),
        "facility_type": _str("Facility category."),
        "distance_km": _num("Distance from the input. " + _NULL_IF_NOT_IN_INPUT, True),
        "risk_level": _str("CRITICAL, HIGH or MODERATE."),
        "action_required": _str("Specific tactical action."),
        "entry_time_hours": _int("0, 3, 6, 12, 24 or 48. null if not supported.", True),
    }, "One facility from the input.", ["facility_name", "risk_level"]), "Facilities named in the input. Empty list if none."),
    "evacuation_corridors": _obj({
        "primary_corridor": _str("Route name from the input only. " + _NULL_IF_NOT_IN_INPUT, True),
        "capacity_vehicles_per_hour": _int("null unless the input gives a capacity.", True),
        "estimated_clearance_hours": _num("null unless the input gives a basis for it.", True),
        "choke_points": _arr(_obj({
            "location": _str("Location from the input."),
            "impact": _str("CRITICAL, HIGH or MODERATE."),
            "width_meters": _int("null unless the input gives a width.", True),
        }, "One choke point."), "Choke points from the input. Empty list if none."),
        "safe_assembly_zones": _arr(_obj({
            "name": _str("Site name from the input."),
            "latitude": _num("From the input. null if absent.", True),
            "longitude": _num("From the input. null if absent.", True),
            "capacity_people": _int("null unless the input gives a capacity.", True),
        }, "One assembly zone."), "Assembly zones from the input. Empty list if none."),
    }, "Evacuation corridors from the input."),
    "vulnerable_demographics": _obj({
        "facilities_at_risk": _arr(_str("Facility name from the input."), "Facilities from the input only."),
        "estimated_displaced_citizens": _int("null unless the input gives a basis for it.", True),
        "special_needs_assistance_required": _str("Specific need from the input. " + _NULL_IF_NOT_IN_INPUT, True),
    }, "Vulnerable population from the input."),
}, "Crisis intelligence dossier for one incident.", ["immediate_actions"])


def _for_prompt(node):
    """Render a schema node as readable text for the prompt body."""
    kind = node["type"]
    if kind == "OBJECT":
        return {k: _for_prompt(v) for k, v in node["properties"].items()}
    if kind == "ARRAY":
        return [_for_prompt(node["items"])]
    base = {"STRING": "string", "INTEGER": "integer", "NUMBER": "number"}[kind]
    suffix = " or null" if node.get("nullable") else ""
    return f"{base}{suffix}: {node.get('description', '')}"


RESPONSE_PLAN_SCHEMA_TEXT = json.dumps(_for_prompt(RESPONSE_PLAN_GEMINI_SCHEMA), indent=2)
DEEP_DOSSIER_SCHEMA_TEXT = json.dumps(_for_prompt(DEEP_DOSSIER_GEMINI_SCHEMA), indent=2)

PREPAREDNESS_ACTIONS_SCHEMA_TEXT = """
{
  "risk_context": "string (1-2 sentence summary of the escalation window driving these actions, e.g. 'Thunderstorm risk escalates to RED by Day 3 with 46mm rainfall and 20m/s winds.')",
  "actions": [
    {
      "action": "string (specific, concrete task for this incident)",
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
