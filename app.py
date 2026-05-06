from __future__ import annotations

import html
from numbers import Number
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Flight Route Optimizer",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from streamlit_folium import st_folium
except ImportError:  # pragma: no cover - used only when optional renderer is absent.
    st_folium = None

try:
    from flight_optimizer.algorithms import (
        astar_smart,
        bellman_ford_cheapest,
        bfs_connectivity,
        booking_rows,
        city_suggestions,
        dfs_components,
        dijkstra_fastest,
        kruskal_forest,
        next_flights,
        route_rows,
        routes_to_dot,
        sort_flights,
        tarjan_bridges,
    )
    from flight_optimizer.geocoding import ensure_city_coord, geocode_missing_cities
    from flight_optimizer.map_viz import build_flight_map
    from flight_optimizer.models import Booking, FlightRoute
    from flight_optimizer.storage import (
        load_bookings,
        load_custom_coords,
        load_routes,
        make_seat,
        next_booking_id,
        save_bookings,
        save_custom_coords,
        save_routes,
    )
except ModuleNotFoundError as exc:
    st.error(f"Missing Python package: {exc.name}")
    st.write("Start the app with the project virtual environment, or install dependencies into the Python environment currently running Streamlit.")
    st.code(
        ".\\.venv\\Scripts\\python.exe -m streamlit run app.py\n"
        "# or\n"
        "pip install -r requirements.txt",
        language="powershell",
    )
    st.stop()


BASE_DIR = Path(__file__).resolve().parent
ROUTE_FILE = BASE_DIR / "route_data.txt"
BOOKING_FILE = BASE_DIR / "bookings.txt"
DOT_FILE = BASE_DIR / "routes.dot"
COORD_FILE = BASE_DIR / "city_coords.json"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');

        :root {
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1e40af;
            --accent: #0f766e;
            --accent-light: #14b8a6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --border: #e5e7eb;
            --border-light: #f0f1f3;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp {
            background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
            color: var(--text-primary) !important;
        }

        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
            font-family: 'Syne', sans-serif !important;
            color: var(--text-primary) !important;
            font-weight: 800 !important;
        }

        .stApp p, .stApp label, .stApp span, .stApp [data-testid="stMarkdownContainer"] {
            color: var(--text-primary) !important;
        }

        [data-testid="stSidebar"] {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-light);
            box-shadow: 8px 0 32px rgba(0, 0, 0, 0.06);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: var(--text-primary) !important;
        }

        [data-testid="stSidebar"] h1 {
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, var(--primary), var(--accent-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        [data-testid="stSidebar"] h3 {
            color: var(--text-primary) !important;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 700;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: var(--text-secondary) !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] details {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
            overflow: hidden;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] details[open] {
            box-shadow: var(--shadow-md);
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            background: var(--bg-primary);
            border-radius: 12px;
            cursor: pointer;
            padding: 0.75rem 1rem;
            transition: all 0.2s ease;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
            background: var(--bg-tertiary);
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary p,
        [data-testid="stSidebar"] [data-testid="stExpander"] summary span {
            color: var(--text-primary) !important;
            font-weight: 600;
        }

        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {
            background: var(--bg-primary) !important;
            border: 1.5px solid var(--border) !important;
            border-radius: 8px !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.2s ease !important;
        }

        [data-baseweb="select"] > div:hover,
        [data-baseweb="input"] > div:hover {
            border-color: var(--primary-light) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }

        [data-baseweb="select"] span,
        [data-baseweb="select"] div,
        [data-baseweb="select"] p,
        [data-baseweb="select"] input,
        [data-baseweb="input"] input {
            color: var(--text-primary) !important;
            -webkit-text-fill-color: var(--text-primary) !important;
        }

        [data-baseweb="select"] svg,
        [data-baseweb="select"] svg path {
            color: var(--text-secondary) !important;
            fill: var(--text-secondary) !important;
        }

        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] [role="option"],
        [data-baseweb="popover"] [role="option"] * {
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            -webkit-text-fill-color: var(--text-primary) !important;
        }

        [data-baseweb="popover"] [role="option"]:hover,
        [data-baseweb="popover"] [aria-selected="true"] {
            background: var(--bg-tertiary) !important;
            color: var(--primary) !important;
        }

        .block-container {
            max-width: 1600px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .app-hero {
            background: linear-gradient(135deg, var(--bg-primary) 0%, #f0f9ff 100%);
            border: 2px solid var(--border);
            border-radius: 16px;
            padding: 2rem 2.5rem;
            margin: 0 0 2rem 0;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }

        .app-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .app-hero > * {
            position: relative;
            z-index: 1;
        }

        .hero-kicker {
            color: var(--primary) !important;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
            display: inline-block;
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(20, 184, 166, 0.1));
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
        }

        .app-title {
            font-size: clamp(2rem, 3vw, 3rem);
            line-height: 1.2;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0.5rem 0 1rem 0;
            color: var(--text-primary) !important;
            background: linear-gradient(135deg, var(--text-primary), var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtle {
            color: var(--text-secondary) !important;
            font-size: 1rem;
            line-height: 1.5;
        }

        div[data-testid="stMetric"] {
            background: var(--bg-primary);
            border: 2px solid var(--border);
            padding: 1.5rem 1.75rem;
            border-radius: 12px;
            box-shadow: var(--shadow-md);
            min-height: 8rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        div[data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--accent-light));
        }

        div[data-testid="stMetric"]:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] p,
        div[data-testid="stMetric"] span,
        div[data-testid="stMetric"] div {
            color: var(--text-primary) !important;
        }

        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] * {
            color: var(--text-secondary) !important;
            font-size: 0.875rem;
            font-weight: 500;
        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 800 !important;
            color: var(--primary) !important;
        }

        .result-panel {
            background: linear-gradient(135deg, var(--bg-primary) 0%, #f0f9ff 50%);
            border: 2px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem 1.75rem;
            margin: 1rem 0 1.5rem 0;
            color: var(--text-primary) !important;
            box-shadow: var(--shadow-md);
            border-left: 5px solid var(--primary);
            position: relative;
        }

        .result-panel * {
            color: var(--text-primary) !important;
        }

        .result-panel h3 {
            margin: 0.5rem 0 !important;
            font-size: 1.5rem !important;
            color: var(--primary) !important;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            padding: 0.4rem 0.9rem;
            border-radius: 999px;
            border: 1.5px solid var(--primary);
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(20, 184, 166, 0.05));
            margin: 0.3rem 0.35rem 0.3rem 0;
            font-size: 0.85rem;
            color: var(--primary) !important;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .chip:hover {
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(20, 184, 166, 0.1));
            transform: scale(1.05);
        }

        div.stButton > button {
            border-radius: 10px;
            border: 1.5px solid var(--border);
            background: var(--bg-primary);
            color: var(--text-primary) !important;
            min-height: 2.8rem;
            font-weight: 600;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
            text-transform: capitalize;
            letter-spacing: 0.01em;
        }

        div.stButton > button:hover {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1), var(--shadow-md);
            transform: translateY(-1px);
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--primary), var(--accent-light));
            color: #ffffff !important;
            border-color: var(--primary);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
        }

        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, var(--primary-dark), var(--accent));
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.4);
            transform: translateY(-2px);
        }

        div.stButton > button[kind="primary"] *,
        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span {
            color: #ffffff !important;
        }

        button[data-baseweb="tab"] p,
        button[data-baseweb="tab"] span {
            color: var(--text-secondary) !important;
            font-weight: 600;
            font-size: 0.95rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] p,
        button[data-baseweb="tab"][aria-selected="true"] span {
            color: var(--primary) !important;
        }

        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 2px solid var(--border);
            padding: 0.5rem 0;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"] {
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            border-radius: 0;
            padding: 0.75rem 1.25rem;
            transition: all 0.2s ease;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"]:hover {
            color: var(--primary) !important;
        }

        div[data-testid="stTabs"] [aria-selected="true"] {
            background: transparent;
            border-bottom-color: var(--primary);
        }

        .section-title {
            font-size: 1.5rem;
            font-weight: 800;
            margin: 1.5rem 0 1rem 0;
            color: var(--text-primary) !important;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .section-title::before {
            content: '';
            display: inline-block;
            width: 4px;
            height: 1.5rem;
            background: linear-gradient(180deg, var(--primary), var(--accent-light));
            border-radius: 2px;
        }

        .data-table-wrap {
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-md);
            max-height: 500px;
            overflow-y: auto;
        }

        table.data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        table.data-table thead th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: linear-gradient(135deg, #f3f4f6, #ffffff);
            color: var(--text-primary) !important;
            text-align: left;
            font-weight: 700;
            padding: 1rem 1rem;
            border-bottom: 2px solid var(--border);
        }

        table.data-table tbody td {
            padding: 0.9rem 1rem;
            border-bottom: 1px solid var(--border-light);
            color: var(--text-primary) !important;
            background: var(--bg-primary);
        }

        table.data-table tbody tr:nth-child(even) td {
            background: var(--bg-secondary);
        }

        table.data-table tbody tr:hover td {
            background: linear-gradient(90deg, rgba(37, 99, 235, 0.05), transparent);
        }

        table.data-table td.num,
        table.data-table th.num {
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    defaults = {
        "view_title": "Base Flight Network",
        "view_message": "Showing all loaded cities and routes.",
        "highlight_keys": [],
        "path_cities": [],
        "view_type": "route",
        "components": [],
        "result_payload": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def set_view(
    title: str,
    message: str = "",
    highlight_keys: list[tuple[str, str, str]] | None = None,
    path_cities: list[str] | None = None,
    view_type: str = "route",
    components: list[list[str]] | None = None,
    payload: dict | None = None,
) -> None:
    st.session_state.view_title = title
    st.session_state.view_message = message
    st.session_state.highlight_keys = highlight_keys or []
    st.session_state.path_cities = path_cities or []
    st.session_state.view_type = view_type
    st.session_state.components = components or []
    st.session_state.result_payload = payload


def city_options(cities: list[str]) -> list[str]:
    return cities if cities else ["No cities loaded"]


def route_options(routes: list[FlightRoute]) -> dict[str, FlightRoute]:
    return {route.label: route for route in routes}


def render_light_table(dataframe, empty_message: str = "No records found.") -> None:
    if dataframe.empty:
        st.info(empty_message)
        return

    numeric_columns = {
        column
        for column in dataframe.columns
        if dataframe[column].map(lambda value: isinstance(value, Number) and not isinstance(value, bool)).all()
    }
    header_cells = []
    for column in dataframe.columns:
        class_name = "num" if column in numeric_columns else ""
        header_cells.append(f'<th class="{class_name}">{html.escape(str(column))}</th>')

    body_rows = []
    for _, row in dataframe.iterrows():
        cells = []
        for column in dataframe.columns:
            value = row[column]
            class_name = "num" if column in numeric_columns else ""
            cells.append(f'<td class="{class_name}">{html.escape(str(value))}</td>')
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    st.markdown(
        '<div class="data-table-wrap">'
        '<table class="data-table">'
        f"<thead><tr>{''.join(header_cells)}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


def render_sidebar(
    routes: list[FlightRoute],
    bookings: list[Booking],
    cities: list[str],
    custom_coords: dict[str, tuple[float, float]],
) -> None:
    st.sidebar.title("Controls")

    with st.sidebar.expander("Engine", expanded=False):
        st.caption("Data source")
        st.code(f"{ROUTE_FILE.name}\n{BOOKING_FILE.name}", language="text")
        if st.button("Show Base Map", width="stretch"):
            set_view("Base Flight Network", "Showing all loaded cities and routes.")
        country_hint = st.text_input("Geocode country hint", value="India")
        if st.button("Auto-find missing coordinates", width="stretch"):
            with st.spinner("Finding missing city coordinates..."):
                found, missing = geocode_missing_cities(cities, custom_coords, country_hint)
                save_custom_coords(COORD_FILE, custom_coords)
            if found:
                st.sidebar.success(f"Found coordinates for: {', '.join(found)}")
            if missing:
                st.sidebar.warning(f"Still missing: {', '.join(missing)}")
            if not found and not missing:
                st.sidebar.info("All loaded cities already have coordinates.")

    st.sidebar.markdown("### Graph Ops")
    with st.sidebar.expander("Add Route", expanded=False):
        with st.form("add_route_form", clear_on_submit=False):
            src = st.text_input("Source city")
            dest = st.text_input("Destination city")
            distance = st.number_input("Distance (km)", min_value=1, value=300, step=10)
            time = st.number_input("Time (minutes)", min_value=1, value=120, step=5)
            fare = st.number_input("Fare (Rs)", min_value=0, value=3000, step=100)
            flight_num = st.text_input("Flight number")
            st.caption("City coordinates are found automatically and cached.")
            submitted = st.form_submit_button("Add Flight Route", width="stretch")

        if submitted:
            if not src.strip() or not dest.strip() or not flight_num.strip():
                st.sidebar.error("Source, destination, and flight number are required.")
            else:
                new_route = FlightRoute(
                    src=src.strip(),
                    dest=dest.strip(),
                    distance=int(distance),
                    time=int(time),
                    fare=int(fare),
                    flight_num=flight_num.strip(),
                )
                updated = routes + [new_route]
                with st.spinner("Finding city coordinates..."):
                    src_ok, src_status = ensure_city_coord(src.strip(), custom_coords, country_hint)
                    dest_ok, dest_status = ensure_city_coord(dest.strip(), custom_coords, country_hint)
                save_routes(ROUTE_FILE, updated)
                save_custom_coords(COORD_FILE, custom_coords)
                coord_message = (
                    f"Coordinates: {src.strip()} {src_status}, "
                    f"{dest.strip()} {dest_status}."
                )
                if not src_ok or not dest_ok:
                    coord_message += " The route is saved, but missing cities will not appear on the map until coordinates are found."
                set_view("Base Flight Network", f"New route added and saved. {coord_message}")
                st.rerun()

    with st.sidebar.expander("Remove Route", expanded=False):
        choices = route_options(routes)
        if choices:
            label = st.selectbox("Route", list(choices.keys()), key="remove_route_select")
            if st.button("Remove Flight Route", width="stretch"):
                selected = choices[label]
                updated = [
                    route for route in routes if route.route_key != selected.route_key
                ]
                save_routes(ROUTE_FILE, updated)
                set_view("Base Flight Network", "Route removed and saved.")
                st.rerun()
        else:
            st.info("No routes loaded.")

    st.sidebar.markdown("### Routing & Analysis")
    route_algorithms = {
        "Dijkstra (Fastest)": dijkstra_fastest,
        "Bellman-Ford (Cheapest)": bellman_ford_cheapest,
        "A* (Smart Search)": astar_smart,
    }
    with st.sidebar.expander("Route Finder", expanded=True):
        if cities:
            src = st.selectbox("From", city_options(cities), key="route_src")
            dest = st.selectbox("To", city_options(cities), key="route_dest")
            algo_name = st.selectbox("Algorithm", list(route_algorithms.keys()))
            if st.button("Find Route", type="primary", width="stretch"):
                if algo_name == "A* (Smart Search)":
                    result = astar_smart(routes, src, dest, custom_coords)
                else:
                    result = route_algorithms[algo_name](routes, src, dest)
                payload = {
                    "kind": "route",
                    "metric_label": result.metric_label,
                    "metric_value": result.metric_value,
                    "path": result.path,
                }
                set_view(
                    result.title,
                    result.message,
                    result.route_keys,
                    result.path,
                    "route",
                    payload=payload,
                )
        else:
            st.info("Add routes before running route search.")

    with st.sidebar.expander("Graph Analysis", expanded=False):
        if cities:
            analysis = st.selectbox(
                "View",
                [
                    "BFS (Connectivity)",
                    "DFS (Components)",
                    "Kruskal (MST)",
                    "Tarjan (Bridges)",
                ],
            )
            if analysis == "BFS (Connectivity)":
                bfs_src = st.selectbox("Source city", cities, key="bfs_src")
                if st.button("Run BFS", width="stretch"):
                    result = bfs_connectivity(routes, bfs_src)
                    set_view(
                        result.title,
                        result.message,
                        result.route_keys,
                        result.cities,
                        "bfs",
                        payload={"kind": "bfs", "cities": result.cities},
                    )
            elif analysis == "DFS (Components)":
                if st.button("Find Components", width="stretch"):
                    components = dfs_components(routes)
                    set_view(
                        "DFS Connected Components",
                        f"{len(components)} component(s) found.",
                        [],
                        [],
                        "components",
                        components=components,
                        payload={"kind": "components", "components": components},
                    )
            elif analysis == "Kruskal (MST)":
                metric = st.selectbox(
                    "MST weight",
                    ["distance", "time", "fare"],
                    format_func=lambda value: value.title(),
                )
                if st.button("Build MST / Forest", width="stretch"):
                    result = kruskal_forest(routes, metric)
                    set_view(
                        result.title,
                        result.message,
                        result.route_keys,
                        [],
                        "mst",
                        payload={
                            "kind": "forest",
                            "metric_label": result.metric_label,
                            "total_weight": result.total_weight,
                            "components_count": result.components_count,
                        },
                    )
            else:
                if st.button("Find Critical Routes", width="stretch"):
                    result = tarjan_bridges(routes)
                    set_view(
                        result.title,
                        result.message,
                        result.route_keys,
                        [],
                        "bridges",
                        payload={"kind": "bridges", "count": len(result.route_keys)},
                    )
        else:
            st.info("No graph to analyze.")

    st.sidebar.markdown("### Flight System")
    with st.sidebar.expander("Next Flights", expanded=False):
        if cities:
            src = st.selectbox("Source", cities, key="next_src")
            count = st.number_input("Number of flights", min_value=1, value=3, step=1)
            if st.button("View Next Flights", width="stretch"):
                flights = next_flights(routes, src, int(count))
                set_view(
                    f"Next Flights from {src}",
                    f"Showing {len(flights)} flight(s), prioritized by time.",
                    [route.route_key for route in flights],
                    [src] + [route.dest for route in flights],
                    "bfs",
                    payload={"kind": "flights", "routes": flights},
                )

    with st.sidebar.expander("Sort Flights", expanded=False):
        if cities:
            src = st.selectbox("Source city", cities, key="sort_src")
            metric = st.selectbox(
                "Sort by",
                ["fare", "time", "distance"],
                format_func=lambda value: value.title(),
            )
            if st.button("Sort Flights", width="stretch"):
                flights = sort_flights(routes, src, metric)
                set_view(
                    f"Sorted Flights from {src}",
                    f"Sorted by {metric}.",
                    [route.route_key for route in flights],
                    [src] + [route.dest for route in flights],
                    "route",
                    payload={"kind": "flights", "routes": flights},
                )

    with st.sidebar.expander("Bookings", expanded=False):
        choices = route_options(routes)
        with st.form("book_ticket_form", clear_on_submit=True):
            passenger = st.text_input("Passenger name")
            selected_route_label = st.selectbox(
                "Route",
                list(choices.keys()) if choices else ["No routes available"],
            )
            fare_value = (
                choices[selected_route_label].fare
                if choices and selected_route_label in choices
                else 0
            )
            fare = st.number_input("Fare (Rs)", min_value=0, value=int(fare_value), step=100)
            booked = st.form_submit_button("Book Ticket", width="stretch")

        if booked:
            if not passenger.strip() or not choices:
                st.sidebar.error("Passenger and route are required.")
            else:
                selected_route = choices[selected_route_label]
                booking_id = next_booking_id(bookings)
                booking = Booking(
                    booking_id=booking_id,
                    passenger=passenger.strip(),
                    route=f"{selected_route.src}->{selected_route.dest}",
                    fare=int(fare),
                    seat=make_seat(booking_id),
                )
                save_bookings(BOOKING_FILE, bookings + [booking])
                st.sidebar.success(f"Booked ID {booking_id}, seat {booking.seat}.")
                st.rerun()

        if bookings:
            booking_ids = [booking.booking_id for booking in bookings]
            cancel_id = st.selectbox("Cancel booking ID", booking_ids)
            if st.button("Cancel Ticket", width="stretch"):
                updated = [booking for booking in bookings if booking.booking_id != cancel_id]
                save_bookings(BOOKING_FILE, updated)
                st.sidebar.success(f"Cancelled booking {cancel_id}.")
                st.rerun()
        else:
            st.caption("No bookings yet.")

    st.sidebar.markdown("### Search")
    prefix = st.sidebar.text_input("City Autocomplete")
    suggestions = city_suggestions(cities, prefix)
    if prefix:
        if suggestions:
            st.sidebar.write(", ".join(suggestions[:10]))
        else:
            st.sidebar.caption("No matching cities.")

    st.sidebar.markdown("### Export")
    if st.sidebar.button("Graph -> DOT format", width="stretch"):
        dot_text = routes_to_dot(routes)
        DOT_FILE.write_text(dot_text, encoding="utf-8")
        st.session_state.dot_text = dot_text
        st.sidebar.success(f"Exported {DOT_FILE.name}")


def render_result_panel() -> None:
    payload = st.session_state.result_payload
    st.markdown(
        f"""
        <div class="result-panel">
            <div class="subtle">Current view</div>
            <h3 style="margin:.15rem 0 .4rem 0;">{st.session_state.view_title}</h3>
            <div>{st.session_state.view_message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not payload:
        return

    kind = payload.get("kind")
    if kind == "route":
        metric_value = payload.get("metric_value")
        metric_label = payload.get("metric_label")
        if metric_value is None:
            st.warning("No route found for the selected cities.")
        else:
            unit = "min" if metric_label == "Time" else "Rs" if metric_label == "Fare" else ""
            st.metric(metric_label, f"{unit} {metric_value}" if unit == "Rs" else f"{metric_value} {unit}".strip())
            st.markdown(
                " ".join(f'<span class="chip">{city}</span>' for city in payload.get("path", [])),
                unsafe_allow_html=True,
            )
    elif kind == "forest":
        label = payload.get("metric_label", "Weight")
        st.metric(f"Total {label}", payload.get("total_weight", 0))
        st.caption(f"Components: {payload.get('components_count', 0)}")
    elif kind == "components":
        components = payload.get("components", [])
        for index, component in enumerate(components, start=1):
            st.markdown(
                f"**Component {index}:** "
                + " ".join(f'<span class="chip">{city}</span>' for city in component),
                unsafe_allow_html=True,
            )
    elif kind == "bridges":
        st.metric("Critical Routes", payload.get("count", 0))
    elif kind == "bfs":
        st.markdown(
            " ".join(f'<span class="chip">{city}</span>' for city in payload.get("cities", [])),
            unsafe_allow_html=True,
        )
    elif kind == "flights":
        flights = payload.get("routes", [])
        render_light_table(route_rows(flights), "No flights found.")


def render_map(
    routes: list[FlightRoute],
    cities: list[str],
    custom_coords: dict[str, tuple[float, float]],
) -> None:
    flight_map, missing = build_flight_map(
        routes,
        cities,
        custom_coords,
        highlight_keys=st.session_state.highlight_keys,
        view_type=st.session_state.view_type,
        path_cities=st.session_state.path_cities,
        components=st.session_state.components,
    )
    if missing:
        st.warning(
            "Missing coordinates for: "
            + ", ".join(missing)
            + ". Use Engine -> Auto-find missing coordinates to place them on the map."
        )

    if st_folium:
        st_folium(flight_map, height=620, use_container_width=True, returned_objects=[])
    else:
        components.html(flight_map._repr_html_(), height=620)


def main() -> None:
    inject_css()
    initialize_state()

    routes = load_routes(ROUTE_FILE)
    bookings = load_bookings(BOOKING_FILE)
    custom_coords = load_custom_coords(COORD_FILE)
    cities = sorted({city for route in routes for city in (route.src, route.dest)}, key=str.lower)

    render_sidebar(routes, bookings, cities, custom_coords)

    st.markdown(
        """
        <div class="app-hero">
            <div class="hero-kicker">Interactive Flight Intelligence</div>
            <div class="app-title">Flight Route Optimizer</div>
            <div class="subtle">Map-based routing, graph analysis, booking operations, and route exports from your live data files.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Cities", len(cities))
    metric_col2.metric("Routes", len(routes))
    metric_col3.metric("Bookings", len(bookings))

    tabs = st.tabs(["Routing & Analysis", "Visualizations"])

    with tabs[0]:
        render_result_panel()
        left, right = st.columns([1.1, 1])
        with left:
            st.markdown('<div class="section-title">Routes</div>', unsafe_allow_html=True)
            render_light_table(route_rows(routes), "No routes loaded.")
        with right:
            st.markdown('<div class="section-title">Bookings</div>', unsafe_allow_html=True)
            booking_df = booking_rows(bookings)
            render_light_table(booking_df, "No bookings found.")

    with tabs[1]:
        render_result_panel()
        render_map(routes, cities, custom_coords)


if __name__ == "__main__":
    main()
