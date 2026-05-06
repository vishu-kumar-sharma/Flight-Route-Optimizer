from __future__ import annotations


DEFAULT_CITY_COORDS: dict[str, tuple[float, float]] = {
    "agra": (27.1767, 78.0081),
    "ahmedabad": (23.0225, 72.5714),
    "amritsar": (31.6340, 74.8723),
    "bengaluru": (12.9716, 77.5946),
    "bhopal": (23.2599, 77.4126),
    "chamba": (32.5534, 76.1258),
    "chandigarh": (30.7333, 76.7794),
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "dehradun": (30.3165, 78.0322),
    "delhi": (28.6139, 77.2090),
    "etawah": (26.7769, 79.0217),
    "goa": (15.2993, 74.1240),
    "gurugram": (28.4595, 77.0266),
    "guwahati": (26.1445, 91.7362),
    "hyderabad": (17.3850, 78.4867),
    "hyderadabad": (17.3850, 78.4867),
    "indore": (22.7196, 75.8577),
    "jaipur": (26.9124, 75.7873),
    "jodhpur": (26.2389, 73.0243),
    "kanpur": (26.4499, 80.3319),
    "kochi": (9.9312, 76.2673),
    "kolkata": (22.5726, 88.3639),
    "lucknow": (26.8467, 80.9462),
    "mumbai": (19.0760, 72.8777),
    "noida": (28.5355, 77.3910),
    "patna": (25.5941, 85.1376),
    "prayagraj": (25.4358, 81.8463),
    "pune": (18.5204, 73.8567),
    "shamli": (29.4493, 77.3128),
    "shyamli": (29.4493, 77.3128),
    "sirsa": (29.5336, 75.0177),
    "surat": (21.1702, 72.8311),
    "udaipur": (24.5854, 73.7125),
    "varanasi": (25.3176, 82.9739),
}


def normalized_city(city: str) -> str:
    return " ".join(city.strip().lower().split())


def resolve_city_coords(
    city: str,
    custom_coords: dict[str, tuple[float, float]] | None = None,
) -> tuple[float, float] | None:
    key = normalized_city(city)
    custom_coords = custom_coords or {}
    return custom_coords.get(key) or DEFAULT_CITY_COORDS.get(key)

