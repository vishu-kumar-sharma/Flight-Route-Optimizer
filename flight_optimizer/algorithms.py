from __future__ import annotations

import heapq
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import count
from typing import Iterable

import networkx as nx
import pandas as pd

from .locations import resolve_city_coords
from .models import Booking, FlightRoute, RouteResult


def all_cities(routes: Iterable[FlightRoute]) -> list[str]:
    cities: set[str] = set()
    for route in routes:
        cities.add(route.src)
        cities.add(route.dest)
    return sorted(cities, key=lambda city: city.lower())


def route_rows(routes: list[FlightRoute]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "From": route.src,
                "To": route.dest,
                "Flight": route.flight_num,
                "Distance (km)": route.distance,
                "Time (min)": route.time,
                "Fare (Rs)": route.fare,
            }
            for route in routes
        ]
    )


def booking_rows(bookings: list[Booking]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Booking ID": booking.booking_id,
                "Passenger": booking.passenger,
                "Route": booking.route,
                "Fare (Rs)": booking.fare,
                "Seat": booking.seat,
            }
            for booking in bookings
        ]
    )


def build_multidigraph(routes: list[FlightRoute]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for route in routes:
        graph.add_node(route.src)
        graph.add_node(route.dest)
        graph.add_edge(
            route.src,
            route.dest,
            key=route.flight_num,
            distance=route.distance,
            time=route.time,
            fare=route.fare,
            flight_num=route.flight_num,
            route_key=route.route_key,
        )
    return graph


def routes_from_source(routes: list[FlightRoute]) -> dict[str, list[FlightRoute]]:
    grouped: dict[str, list[FlightRoute]] = defaultdict(list)
    for route in routes:
        grouped[route.src].append(route)
    return grouped


def _adjacency(routes: list[FlightRoute]) -> dict[str, list[FlightRoute]]:
    return routes_from_source(routes)


def _restore_path(
    src: str,
    dest: str,
    parent: dict[str, tuple[str, FlightRoute]],
) -> tuple[list[str], list[tuple[str, str, str]]]:
    path = [dest]
    route_keys: list[tuple[str, str, str]] = []
    current = dest
    while current != src:
        previous, route = parent[current]
        route_keys.append(route.route_key)
        current = previous
        path.append(current)
    path.reverse()
    route_keys.reverse()
    return path, route_keys


def dijkstra_fastest(routes: list[FlightRoute], src: str, dest: str) -> RouteResult:
    cities = set(all_cities(routes))
    if src not in cities or dest not in cities:
        return RouteResult("Dijkstra Fastest Route", "Time", None, [], [], "City not found.")

    adjacency = _adjacency(routes)
    distances = {city: math.inf for city in cities}
    parent: dict[str, tuple[str, FlightRoute]] = {}
    tie = count()
    distances[src] = 0
    heap: list[tuple[float, int, str]] = [(0, next(tie), src)]

    while heap:
        current_distance, _, city = heapq.heappop(heap)
        if current_distance > distances[city]:
            continue
        for route in adjacency.get(city, []):
            candidate = current_distance + route.time
            if candidate < distances[route.dest]:
                distances[route.dest] = candidate
                parent[route.dest] = (city, route)
                heapq.heappush(heap, (candidate, next(tie), route.dest))

    if math.isinf(distances[dest]):
        return RouteResult("Dijkstra Fastest Route", "Time", None, [], [], "No route found.")

    path, route_keys = _restore_path(src, dest, parent)
    return RouteResult(
        "Dijkstra Fastest Route",
        "Time",
        int(distances[dest]),
        path,
        route_keys,
        "Fastest route by total flight time.",
    )


def bellman_ford_cheapest(routes: list[FlightRoute], src: str, dest: str) -> RouteResult:
    cities = set(all_cities(routes))
    if src not in cities or dest not in cities:
        return RouteResult("Bellman-Ford Cheapest Route", "Fare", None, [], [], "City not found.")

    costs = {city: math.inf for city in cities}
    parent: dict[str, tuple[str, FlightRoute]] = {}
    costs[src] = 0

    for _ in range(max(len(cities) - 1, 0)):
        changed = False
        for route in routes:
            if math.isinf(costs[route.src]):
                continue
            candidate = costs[route.src] + route.fare
            if candidate < costs[route.dest]:
                costs[route.dest] = candidate
                parent[route.dest] = (route.src, route)
                changed = True
        if not changed:
            break

    if math.isinf(costs[dest]):
        return RouteResult(
            "Bellman-Ford Cheapest Route",
            "Fare",
            None,
            [],
            [],
            "No route found.",
        )

    path, route_keys = _restore_path(src, dest, parent)
    return RouteResult(
        "Bellman-Ford Cheapest Route",
        "Fare",
        int(costs[dest]),
        path,
        route_keys,
        "Cheapest route by total fare.",
    )


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 6371.0 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _astar_heuristic(
    city: str,
    dest: str,
    custom_coords: dict[str, tuple[float, float]],
) -> float:
    city_coords = resolve_city_coords(city, custom_coords)
    dest_coords = resolve_city_coords(dest, custom_coords)
    if city_coords and dest_coords:
        return _haversine_km(city_coords, dest_coords) / 9.0

    value = sum(ord(char) for char in city) - sum(ord(char) for char in dest)
    return abs(value) * 10


def astar_smart(
    routes: list[FlightRoute],
    src: str,
    dest: str,
    custom_coords: dict[str, tuple[float, float]] | None = None,
) -> RouteResult:
    cities = set(all_cities(routes))
    if src not in cities or dest not in cities:
        return RouteResult("A* Smart Route", "Score", None, [], [], "City not found.")

    custom_coords = custom_coords or {}
    adjacency = _adjacency(routes)
    g_score = {city: math.inf for city in cities}
    parent: dict[str, tuple[str, FlightRoute]] = {}
    tie = count()
    g_score[src] = 0
    first_f = _astar_heuristic(src, dest, custom_coords)
    heap: list[tuple[float, int, str]] = [(first_f, next(tie), src)]

    while heap:
        current_f, _, city = heapq.heappop(heap)
        if city == dest:
            break
        if current_f > g_score[city] + _astar_heuristic(city, dest, custom_coords):
            continue
        for route in adjacency.get(city, []):
            candidate = g_score[city] + route.time + (route.distance / 10)
            if candidate < g_score[route.dest]:
                parent[route.dest] = (city, route)
                g_score[route.dest] = candidate
                priority = candidate + _astar_heuristic(route.dest, dest, custom_coords)
                heapq.heappush(heap, (priority, next(tie), route.dest))

    if math.isinf(g_score[dest]):
        return RouteResult("A* Smart Route", "Score", None, [], [], "No route found.")

    path, route_keys = _restore_path(src, dest, parent)
    return RouteResult(
        "A* Smart Route",
        "Score",
        round(g_score[dest], 2),
        path,
        route_keys,
        "Smart score combines flight time, distance, and a map-based heuristic.",
    )


@dataclass(frozen=True)
class TraversalResult:
    title: str
    route_keys: list[tuple[str, str, str]]
    cities: list[str]
    message: str = ""


def bfs_connectivity(routes: list[FlightRoute], src: str) -> TraversalResult:
    if src not in set(all_cities(routes)):
        return TraversalResult("BFS Connectivity", [], [], "City not found.")

    adjacency = _adjacency(routes)
    visited = {src}
    order = [src]
    route_keys: list[tuple[str, str, str]] = []
    queue: deque[str] = deque([src])

    while queue:
        city = queue.popleft()
        for route in adjacency.get(city, []):
            if route.dest not in visited:
                visited.add(route.dest)
                order.append(route.dest)
                queue.append(route.dest)
                route_keys.append(route.route_key)

    return TraversalResult(
        "BFS Connectivity",
        route_keys,
        order,
        f"{len(order)} city/cities reachable from {src}.",
    )


def undirected_adjacency(routes: list[FlightRoute]) -> dict[str, list[tuple[str, FlightRoute]]]:
    adjacency: dict[str, list[tuple[str, FlightRoute]]] = defaultdict(list)
    for route in routes:
        adjacency[route.src].append((route.dest, route))
        adjacency[route.dest].append((route.src, route))
    return adjacency


def dfs_components(routes: list[FlightRoute]) -> list[list[str]]:
    cities = all_cities(routes)
    adjacency = undirected_adjacency(routes)
    visited: set[str] = set()
    components: list[list[str]] = []

    for city in cities:
        if city in visited:
            continue
        stack = [city]
        component: list[str] = []
        visited.add(city)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor, _ in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component, key=lambda item: item.lower()))

    return components


@dataclass(frozen=True)
class ForestResult:
    title: str
    metric_label: str
    total_weight: int
    route_keys: list[tuple[str, str, str]]
    components_count: int
    message: str


class _DisjointSet:
    def __init__(self, nodes: Iterable[str]) -> None:
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}

    def find(self, node: str) -> str:
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, left: str, right: str) -> bool:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return False
        if self.rank[left_root] < self.rank[right_root]:
            self.parent[left_root] = right_root
        elif self.rank[left_root] > self.rank[right_root]:
            self.parent[right_root] = left_root
        else:
            self.parent[right_root] = left_root
            self.rank[left_root] += 1
        return True


def kruskal_forest(routes: list[FlightRoute], metric: str = "distance") -> ForestResult:
    cities = all_cities(routes)
    components_count = nx.number_connected_components(build_multidigraph(routes).to_undirected()) if cities else 0
    metric = metric if metric in {"distance", "time", "fare"} else "distance"
    metric_label = {"distance": "Distance", "time": "Time", "fare": "Fare"}[metric]

    dsu = _DisjointSet(cities)
    selected: list[FlightRoute] = []
    sorted_routes = sorted(
        routes,
        key=lambda route: (getattr(route, metric), route.src.lower(), route.dest.lower(), route.flight_num),
    )

    for route in sorted_routes:
        if dsu.union(route.src, route.dest):
            selected.append(route)

    total = int(sum(getattr(route, metric) for route in selected))
    message = (
        "The network is disconnected, so the highlighted result is a spanning forest."
        if components_count > 1
        else "The highlighted result is the minimum spanning tree."
    )
    return ForestResult(
        "Kruskal Minimum Spanning Forest",
        metric_label,
        total,
        [route.route_key for route in selected],
        components_count,
        message,
    )


def tarjan_bridges(routes: list[FlightRoute]) -> TraversalResult:
    cities = all_cities(routes)
    adjacency: dict[str, list[tuple[str, FlightRoute]]] = defaultdict(list)
    pair_counts: dict[frozenset[str], int] = defaultdict(int)
    representative: dict[frozenset[str], FlightRoute] = {}

    for route in routes:
        pair = frozenset((route.src, route.dest))
        pair_counts[pair] += 1
        representative.setdefault(pair, route)
        adjacency[route.src].append((route.dest, route))
        adjacency[route.dest].append((route.src, route))

    visited: set[str] = set()
    discovery: dict[str, int] = {}
    low: dict[str, int] = {}
    timer = 0
    bridge_keys: list[tuple[str, str, str]] = []

    def dfs(city: str, parent: str | None) -> None:
        nonlocal timer
        visited.add(city)
        discovery[city] = timer
        low[city] = timer
        timer += 1

        for neighbor, route in adjacency.get(city, []):
            if neighbor == parent:
                continue
            if neighbor not in visited:
                dfs(neighbor, city)
                low[city] = min(low[city], low[neighbor])
                pair = frozenset((city, neighbor))
                if low[neighbor] > discovery[city] and pair_counts[pair] == 1:
                    bridge_keys.append(representative[pair].route_key)
            else:
                low[city] = min(low[city], discovery[neighbor])

    for city in cities:
        if city not in visited:
            dfs(city, None)

    message = (
        f"{len(bridge_keys)} critical route(s) found."
        if bridge_keys
        else "No critical routes found."
    )
    return TraversalResult("Tarjan Critical Routes", bridge_keys, cities, message)


def city_suggestions(cities: list[str], prefix: str) -> list[str]:
    prefix = prefix.strip().lower()
    if not prefix:
        return cities
    return [city for city in cities if city.lower().startswith(prefix)]


def next_flights(routes: list[FlightRoute], src: str, count_value: int) -> list[FlightRoute]:
    flights = [route for route in routes if route.src == src]
    return heapq.nsmallest(
        count_value,
        flights,
        key=lambda route: (route.time, route.fare, route.flight_num),
    )


def sort_flights(routes: list[FlightRoute], src: str, metric: str) -> list[FlightRoute]:
    metric = metric if metric in {"fare", "time", "distance"} else "distance"
    return sorted(
        [route for route in routes if route.src == src],
        key=lambda route: (getattr(route, metric), route.flight_num),
    )


def routes_to_dot(routes: list[FlightRoute]) -> str:
    lines = [
        "digraph FlightRoutes {",
        "  rankdir=LR;",
        "  node [shape=circle, style=filled, color=lightblue];",
    ]
    for route in routes:
        label = f"{route.flight_num}\\nRs{route.fare}\\n{route.time}min"
        lines.append(f'  "{route.src}" -> "{route.dest}" [label="{label}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"
