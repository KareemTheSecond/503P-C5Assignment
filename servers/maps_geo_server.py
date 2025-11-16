import json
from typing import Any, Dict, List

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("maps_geo")

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSRM_ROUTE_BASE_URL = "https://router.project-osrm.org/route/v1"

USER_AGENT = "maps-geo-server/1.1_KH"


async def http_get_json(url,  params):
    """
    Helper: perform an HTTP GET request and return JSON-decoded response.
    """
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    
async def http_post_form_json(url, data):
    """
    Helper: perform an HTTP POST (form-encoded) request and return JSON-decoded response.
    Used for Overpass API queries.
    """
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()
    

@mcp.tool()
async def geocodeAddress(query, limit: int = 3):
    """
    Inputs:
        query: A place name or address (like Bliss street or shi).
        limit: Maximum number of results to return.

    Returns:
        JSON string containing a list of candidate locations with their coordinates.
    """
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
    }

    raw_results = await http_get_json(f"{NOMINATIM_BASE_URL}/search", params=params)

    results: List[Dict[str, Any]] = []
    for item in raw_results:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, ValueError):
            continue

        results.append(
            {
                "displayName": item.get("display_name"),
                "lat": lat,
                "lon": lon,
                "type": item.get("type"),
                "class": item.get("class"),
            }
        )

    payload = {
        "query": query,
        "results": results,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

@mcp.tool()
async def reverseGeocode(lat, lon) :
    """
    Input:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.

    Returns:
        JSON string describing the best-matching place/address at that location.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
    }

    data = await http_get_json(f"{NOMINATIM_BASE_URL}/reverse", params=params)

    address = data.get("address", {}) if isinstance(data, dict) else {}

    result = {
        "lat": lat,
        "lon": lon,
        "displayName": data.get("display_name"),
        "address": {
            "road": address.get("road"),
            "neighbourhood": address.get("neighbourhood"),
            "suburb": address.get("suburb"),
            "city": address.get("city") or address.get("town") or address.get("village"),
            "state": address.get("state"),
            "postcode": address.get("postcode"),
            "country": address.get("country"),
        },
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
@mcp.tool()
async def searchPois(keyword, lat, lon, radiusM: int = 2000, maxResults: int = 10) -> str:
    """
    Inputs:
        keyword: Type of the amenity/place to search for (e.g., "cafe").
        lat: Center latitude in decimal degrees.
        lon: Center longitude in decimal degrees.
        radiusM: Search radius in meters.
        maxResults: Maximum number of POIs to include in the response.

    Returns:
        JSON string containing a list of POIs with basic information,
        or an error field if the external service fails.
    """

    overpass_query = f"""
    [out:json][timeout:25];
    node(around:{radiusM},{lat},{lon})["amenity"="{keyword}"];
    out body {maxResults};
    """

    try:
        raw = await http_post_form_json(
            OVERPASS_URL,
            data={"data": overpass_query},
        )
    except Exception as e:
        # Graceful degradation on Overpass failure (e.g., 504)
        payload = {
            "center": {"lat": lat, "lon": lon},
            "search": {"keyword": keyword, "radiusM": radiusM},
            "results": [],
            "error": f"Overpass request failed: {e}",
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    elements = raw.get("elements", []) if isinstance(raw, dict) else []

    pois: List[Dict[str, Any]] = []
    for el in elements[:maxResults]:
        if el.get("type") != "node":
            continue

        tags = el.get("tags", {})
        pois.append(
            {
                "name": tags.get("name"),
                "amenity": tags.get("amenity"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
            }
        )

    payload = {
        "center": {"lat": lat, "lon": lon},
        "search": {"keyword": keyword, "radiusM": radiusM},
        "results": pois,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)

@mcp.tool()
async def basicRoute(startLat,startLon ,endLat ,endLon ,profile = "driving") :
    """
    Inputs:
        startLat: Start latitude.
        startLon: Start longitude.
        endLat: End latitude.
        endLon: End longitude.
        profile: Travel mode (e.g., "driving", "foot", "cycling").

    Returns:
        JSON string with distance (km), duration (minutes), and a list of step summaries.
    """

    path = f"{startLon},{startLat};{endLon},{endLat}"
    url = f"{OSRM_ROUTE_BASE_URL}/{profile}/{path}"

    params = {
        "overview": "false",
        "steps": "true",
    }

    data = await http_get_json(url, params=params)

    routes = data.get("routes", []) if isinstance(data, dict) else []
    if not routes:
        return json.dumps(
            {
                "error": "No route found",
                "start": {"lat": startLat, "lon": startLon},
                "end": {"lat": endLat, "lon": endLon},
            },
            ensure_ascii=False,
            indent=2,
        )

    route = routes[0]
    distance_km = route.get("distance", 0) / 1000.0
    duration_min = route.get("duration", 0) / 60.0

    steps: List[str] = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            instruction = step.get("name") or ""
            modifier = maneuver.get("modifier")
            step_type = maneuver.get("type")
            pieces = [p for p in [step_type, modifier, instruction] if p]
            steps.append(" - ".join(pieces))

    payload = {
        "start": {"lat": startLat, "lon": startLon},
        "end": {"lat": endLat, "lon": endLon},
        "profile": profile,
        "distanceKm": distance_km,
        "durationMin": duration_min,
        "steps": steps,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)

def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
