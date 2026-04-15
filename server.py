#!/usr/bin/env python3
"""Geolocation AI MCP — MEOK AI Labs. IP geolocation, distance calculation, timezone lookup."""

import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

import json, os, re, hashlib, math
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "geolocation-ai",
    instructions="MEOK AI Labs — IP geolocation, distance calculation, timezone lookup, coordinate parsing.",
)

FREE_DAILY_LIMIT = 30
_usage = defaultdict(list)


def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now - t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT:
        return json.dumps(
            {"error": "Limit {0}/day. Upgrade: meok.ai".format(FREE_DAILY_LIMIT)}
        )
    _usage[c].append(now)
    return None


# IP geolocation database (simplified)
_ip_cache = {
    "8.8.8.8": {
        "city": "Mountain View",
        "country": "US",
        "lat": 37.4223,
        "lon": -122.0848,
        "org": "Google",
    },
    "1.1.1.1": {
        "city": "San Francisco",
        "country": "US",
        "lat": 37.7749,
        "lon": -122.4194,
        "org": "Cloudflare",
    },
}

_timezone_offsets = {
    (-12, 0): "Etc/GMT+12",
    (-11, 0): "Pacific/Pago_Pago",
    (-10, 0): "Pacific/Honolulu",
    (-9, 0): "America/Anchorage",
    (-8, 0): "America/Los_Angeles",
    (-7, 0): "America/Denver",
    (-6, 0): "America/Chicago",
    (-5, 0): "America/New_York",
    (-4, 0): "America/Halifax",
    (-3, -3): "America/Sao_Paulo",
    (-3, 0): "America/Buenos_Aires",
    (0, 0): "Europe/London",
    (1, 0): "Europe/Paris",
    (2, 0): "Europe/Berlin",
    (3, 0): "Europe/Moscow",
    (5, 30): "Asia/Kolkata",
    (8, 0): "Asia/Shanghai",
    (9, 0): "Asia/Tokyo",
    (10, 0): "Australia/Sydney",
}


@mcp.tool()
def geolocate_ip(ip_address: str, api_key: str = "") -> str:
    """Get approximate location from IP address."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if err := _rl():
        return err

    ip = ip_address.strip()
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return {"error": "Invalid IP address format"}

    result = _ip_cache.get(
        ip,
        {"city": "Unknown", "country": "XX", "lat": 0.0, "lon": 0.0, "org": "Unknown"},
    )
    result["ip_address"] = ip_address
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return result


@mcp.tool()
def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    units: str = "km",
    api_key: str = "",
) -> str:
    """Calculate distance between two coordinates using Haversine formula."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if err := _rl():
        return err

    R = 6371 if units == "km" else 3959
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c_val = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c_val
    bearing = 0.0

    return {
        "from": {"lat": lat1, "lon": lon1},
        "to": {"lat": lat2, "lon": lon2},
        "distance": round(distance, 2),
        "units": units,
        "bearing_degrees": round(bearing, 1),
    }


@mcp.tool()
def parse_coordinates(location: str, api_key: str = "") -> str:
    """Parse location string into lat/lon coordinates."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if err := _rl():
        return err

    coord_pattern = r"(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)"
    match = re.search(coord_pattern, location)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {
                "location": location,
                "lat": lat,
                "lon": lon,
                "format": "decimal_degrees",
            }

    known_locations = {
        "london": (51.5074, -0.1278),
        "new york": (40.7128, -74.0060),
        "san francisco": (37.7749, -122.4194),
        "tokyo": (35.6762, 139.6503),
        "paris": (48.8566, 2.3522),
        "sydney": (-33.8688, 151.2093),
    }
    location_lower = location.lower().strip()
    if location_lower in known_locations:
        lat, lon = known_locations[location_lower]
        return {
            "location": location,
            "lat": lat,
            "lon": lon,
            "format": "named_location",
        }

    return {"error": "Could not parse coordinates from location", "input": location}


@mcp.tool()
def timezone_from_coords(latitude: float, longitude: float, api_key: str = "") -> str:
    """Determine timezone from coordinates using brute-force offset matching."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if err := _rl():
        return err

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return {"error": "Coordinates out of range"}

    rough_offset = int(longitude / 15)
    candidates = [
        (abs(longitude - tz[0] * 15) + abs(0 - tz[1] * 60) / 60, tz)
        for tz in _timezone_offsets.items()
    ]
    candidates.sort(key=lambda x: x[0])
    best_tz = candidates[0][1]
    tz_name = best_tz[2]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": tz_name,
        "utc_offset_hours": best_tz[0],
        "dst_offset": best_tz[1],
    }


@mcp.tool()
def ip_to_coordinates(ip_address: str, api_key: str = "") -> str:
    """Convert IP address to approximate coordinates without full geolocation."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if err := _rl():
        return err

    ip = ip_address.strip()
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return {"error": "Invalid IP address format"}

    geo = _ip_cache.get(ip, {})
    if geo:
        return {"ip": ip, "lat": geo.get("lat", 0), "lon": geo.get("lon", 0)}
    return {"ip": ip, "lat": None, "lon": None, "note": "IP not in cache"}


if __name__ == "__main__":
    mcp.run()
