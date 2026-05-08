# Flight Route Optimizer Web App

Streamlit conversion of the C++ console-based flight route optimizer into an interactive map dashboard.

## Features

- Add and remove flight routes from `route_data.txt`
- Dijkstra fastest route, Bellman-Ford cheapest route, and A* smart search
- BFS connectivity, DFS components, Kruskal minimum spanning forest, and Tarjan bridge detection
- Priority-queue style next flights, sortable flights, ticket booking/canceling, and booking list
- City autocomplete
- Folium interactive map with city markers, route edges, highlighted algorithm results, and automatic city-name geocoding
- DOT export to `routes.dot`

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Or use the launcher:

```powershell
.\run_app.ps1
```

If you see `ModuleNotFoundError: No module named 'networkx'`, Streamlit is using a different Python environment. Activate the virtual environment from this folder, then install dependencies with `pip install -r requirements.txt`.

If Python is not on PATH on another machine, install Python 3.11+ first, then run the install command above from this folder.

## Deploy

This app is ready for Streamlit Community Cloud:

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app from the GitHub repository.
3. Select the `main` branch and set the entrypoint file to `app.py`.
4. Keep `requirements.txt`, `.streamlit/config.toml`, and the data files in the repository root.

GitHub Pages cannot host this app because Streamlit runs as a Python server application.

## Data Files

- `route_data.txt`: `source destination distance_km time_minutes fare flight_number`
- `bookings.txt`: `booking_id | passenger | source->destination | fare | seat`
- `city_coords.json`: app-generated coordinate cache for custom cities

The app reloads these files on every interaction and saves route and booking updates immediately.

When you add a route with a new city name, the app first checks its built-in coordinate list. If the city is unknown, it searches online once with a no-key geocoder and stores the result in `city_coords.json`.
