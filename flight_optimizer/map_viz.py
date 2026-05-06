from __future__ import annotations

from collections import defaultdict

import folium
from folium import plugins

from .locations import resolve_city_coords
from .models import FlightRoute


BASE_EDGE = "#52657a"
ROUTE_HIGHLIGHT = "#0f9f7f"
BRIDGE_HIGHLIGHT = "#dc2626"
BFS_HIGHLIGHT = "#2563eb"
MST_HIGHLIGHT = "#16a34a"
COMPONENT_COLORS = [
    "#0f766e",
    "#7c3aed",
    "#d97706",
    "#0284c7",
    "#be123c",
    "#4d7c0f",
    "#9333ea",
]


def _route_lookup(routes: list[FlightRoute]) -> dict[tuple[str, str, str], FlightRoute]:
    return {route.route_key: route for route in routes}


def _city_coords(
    cities: list[str],
    custom_coords: dict[str, tuple[float, float]],
) -> tuple[dict[str, tuple[float, float]], list[str]]:
    coords: dict[str, tuple[float, float]] = {}
    missing: list[str] = []
    for city in cities:
        resolved = resolve_city_coords(city, custom_coords)
        if resolved:
            coords[city] = resolved
        else:
            missing.append(city)
    return coords, missing


def _map_center(coords: dict[str, tuple[float, float]]) -> tuple[float, float]:
    if not coords:
        return (22.9734, 78.6569)
    lat = sum(value[0] for value in coords.values()) / len(coords)
    lon = sum(value[1] for value in coords.values()) / len(coords)
    return (lat, lon)


def _line_color(view_type: str, is_highlighted: bool) -> str:
    if not is_highlighted:
        return BASE_EDGE
    if view_type == "bridges":
        return BRIDGE_HIGHLIGHT
    if view_type == "bfs":
        return BFS_HIGHLIGHT
    if view_type == "mst":
        return MST_HIGHLIGHT
    return ROUTE_HIGHLIGHT


def build_flight_map(
    routes: list[FlightRoute],
    cities: list[str],
    custom_coords: dict[str, tuple[float, float]] | None = None,
    highlight_keys: list[tuple[str, str, str]] | None = None,
    view_type: str = "route",
    path_cities: list[str] | None = None,
    components: list[list[str]] | None = None,
) -> tuple[folium.Map, list[str]]:
    custom_coords = custom_coords or {}
    highlight_set = set(highlight_keys or [])
    coords, missing = _city_coords(cities, custom_coords)
    center = _map_center(coords)
    flight_map = folium.Map(location=center, zoom_start=5, tiles="CartoDB positron")
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(flight_map)

    component_lookup: dict[str, int] = {}
    for index, component in enumerate(components or []):
        for city in component:
            component_lookup[city] = index

    grouped_edges: dict[tuple[str, str], list[FlightRoute]] = defaultdict(list)
    for route in routes:
        grouped_edges[(route.src, route.dest)].append(route)

    for edge_routes in grouped_edges.values():
        for offset_index, route in enumerate(edge_routes):
            if route.src not in coords or route.dest not in coords:
                continue
            is_highlighted = route.route_key in highlight_set
            src_lat, src_lon = coords[route.src]
            dest_lat, dest_lon = coords[route.dest]
            line = [(src_lat, src_lon), (dest_lat, dest_lon)]
            tooltip = (
                f"{route.src} -> {route.dest}<br>"
                f"Flight {route.flight_num}<br>"
                f"Time {route.time} min | Fare Rs {route.fare} | {route.distance} km"
            )
            opacity = 0.92 if is_highlighted else 0.62
            weight = 6 if is_highlighted else 3
            color = _line_color(view_type, is_highlighted)
            polyline = folium.PolyLine(
                line,
                color=color,
                weight=weight,
                opacity=opacity,
                tooltip=tooltip,
            )
            polyline.add_to(flight_map)
            if offset_index == 0:
                plugins.PolyLineTextPath(
                    polyline,
                    "  >  ",
                    repeat=True,
                    offset=7,
                    attributes={"fill": color, "font-weight": "bold", "font-size": "12"},
                ).add_to(flight_map)

    route_lookup = _route_lookup(routes)
    for key in highlight_set:
        route = route_lookup.get(key)
        if not route or route.src not in coords or route.dest not in coords:
            continue
        folium.PolyLine(
            [coords[route.src], coords[route.dest]],
            color=_line_color(view_type, True),
            weight=9,
            opacity=0.45,
        ).add_to(flight_map)

    path_set = set(path_cities or [])
    for city in cities:
        if city not in coords:
            continue
        component_index = component_lookup.get(city)
        marker_color = (
            COMPONENT_COLORS[component_index % len(COMPONENT_COLORS)]
            if component_index is not None
            else "#0f172a"
        )
        if city in path_set:
            marker_color = "#f59e0b"
        folium.CircleMarker(
            location=coords[city],
            radius=8 if city in path_set else 6,
            color="#ffffff",
            weight=2,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.95,
            tooltip=city,
            popup=folium.Popup(f"<strong>{city}</strong>", max_width=220),
        ).add_to(flight_map)

    if coords:
        sw = [min(lat for lat, _ in coords.values()), min(lon for _, lon in coords.values())]
        ne = [max(lat for lat, _ in coords.values()), max(lon for _, lon in coords.values())]
        flight_map.fit_bounds([sw, ne], padding=(30, 30))

    folium.LayerControl(collapsed=True).add_to(flight_map)
    return flight_map, missing
