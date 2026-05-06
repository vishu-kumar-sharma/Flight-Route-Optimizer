from __future__ import annotations

import json
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .locations import normalized_city, resolve_city_coords


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
USER_AGENT = "flight-route-optimizer-streamlit/1.0"


def _valid_coords(lat: float, lon: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180


def _open_meteo_geocode(city: str, country_hint: str) -> tuple[float, float] | None:
    params = urlencode(
        {
            "name": city,
            "count": 5,
            "language": "en",
            "format": "json",
        }
    )
    request = Request(
        f"{OPEN_METEO_URL}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    results = data.get("results", [])
    if not isinstance(results, list):
        return None

    hint = country_hint.strip().lower()
    ranked = sorted(
        results,
        key=lambda item: (
            0 if str(item.get("country", "")).lower() == hint else 1,
            -int(item.get("population") or 0),
        ),
    )
    for item in ranked:
        try:
            lat = float(item["latitude"])
            lon = float(item["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if _valid_coords(lat, lon):
            return (lat, lon)
    return None


def _nominatim_geocode(city: str, country_hint: str) -> tuple[float, float] | None:
    city = city.strip()
    queries = [city]
    if country_hint.strip():
        queries.insert(0, f"{city}, {country_hint.strip()}")

    for query in queries:
        params = urlencode(
            {
                "q": query,
                "format": "jsonv2",
                "limit": 1,
            }
        )
        request = Request(
            f"{NOMINATIM_URL}?{params}",
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
        )
        try:
            with urlopen(request, timeout=8) as response:
                results = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
            continue

        if not results:
            continue
        try:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        if _valid_coords(lat, lon):
            return (lat, lon)

    return None


def geocode_city(city: str, country_hint: str = "India") -> tuple[float, float] | None:
    city = city.strip()
    if not city:
        return None

    return _open_meteo_geocode(city, country_hint) or _nominatim_geocode(city, country_hint)


def ensure_city_coord(
    city: str,
    custom_coords: dict[str, tuple[float, float]],
    country_hint: str = "India",
) -> tuple[bool, str]:
    if resolve_city_coords(city, custom_coords):
        return True, "already known"

    coords = geocode_city(city, country_hint)
    if coords:
        custom_coords[normalized_city(city)] = coords
        return True, "found online"

    return False, "not found"


def geocode_missing_cities(
    cities: list[str],
    custom_coords: dict[str, tuple[float, float]],
    country_hint: str = "India",
) -> tuple[list[str], list[str]]:
    found: list[str] = []
    missing: list[str] = []

    for index, city in enumerate(cities):
        if resolve_city_coords(city, custom_coords):
            continue
        ok, _ = ensure_city_coord(city, custom_coords, country_hint)
        if ok:
            found.append(city)
        else:
            missing.append(city)
        if index < len(cities) - 1:
            sleep(1.05)

    return found, missing
