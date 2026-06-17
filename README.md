# Coimbatore (CBE) Burning Compliance Heat Map

Interactive heat map of street-light burning compliance for Coimbatore officials. Reads Excel data, plots each CCMS/light point on a Folium map, and serves it locally or on [Render](https://render.com) via Flask + Gunicorn.

**Live map:** [https://heat-map-cbe-2.onrender.com](https://heat-map-cbe-2.onrender.com)

**For further clarification :** see [IMPLEMENTATION_STEPS.md](IMPLEMENTATION_STEPS.md) — step-by-step briefing on what was built and how to use it in review meetings.

## Features

- **React** frontend with interactive Leaflet map (`frontend/`)
- Color-coded markers by burning percentage (red / yellow / green)
- Ward number shown inside each marker bubble
- Live filters: From/To date, Region, Zone, Ward, and status checkboxes
- **Region radius circle** when a region is selected (e.g. North)
- Dual summary panels: From date (top) and To date (bottom)
- Click popup with per-point CCMS details (load, lights, burning %)

## Color rules

| Burning % | Status   | Color  |
|-----------|----------|--------|
| &lt; 50%  | Critical | Red    |
| 50–90%    | Moderate | Green  |
| ≥ 91%     | Good     | Yellow |

## Project structure

```
HEAT_MAP(CBE)/
├── data/
│   └── cbe_burning_data.xlsx   # Source data (Sheet2)
├── frontend/                   # React app (Vite + react-leaflet)
│   └── dist/                   # Built static files (after npm run build)
├── output/
│   └── cbe_burning_heatmap.html  # Legacy Folium HTML (optional)
├── app.py                      # Flask API + serves React build
├── generate_heatmap.py         # Data processing + legacy HTML generator
├── requirements.txt
├── render.yaml                   # Render deployment blueprint
├── build_frontend.bat            # Build React for production
├── run.bat                       # Generate legacy HTML map
├── run_server.bat                # Build React + start Flask server
└── open_map.bat                  # Open legacy HTML only
```

## Setup

Use the project virtual environment. **Do not use system `pip`** if it is broken on your machine — use the venv instead.

```powershell
cd "c:\MIDHUN\SCHNELL\HEAT_MAP(CBE)"

# Create venv (first time only)
python -m venv venv

# Install dependencies
.\venv\Scripts\pip.exe install -r requirements.txt
```

## Run locally

### Generate map only

Double-click **`run.bat`**, or:

```powershell
.\venv\Scripts\python.exe generate_heatmap.py
```

Optional arguments:

```powershell
.\venv\Scripts\python.exe generate_heatmap.py --input data/cbe_burning_data.xlsx --output output/cbe_burning_heatmap.html --no-open
```

### Open existing map

Double-click **`open_map.bat`**.

### Run web app (React)

Build the frontend once, then start Flask:

```powershell
.\build_frontend.bat
.\run_server.bat
```

Open **http://127.0.0.1:5000**

For frontend development with hot reload:

```powershell
# Terminal 1
.\venv\Scripts\python.exe app.py

# Terminal 2
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173** (proxies `/api` to Flask).

### Generate legacy HTML map only

| Endpoint        | Description              |
|-----------------|--------------------------|
| `/`             | Interactive heat map     |
| `/health`       | Health check (JSON)      |
| `POST /refresh` | Regenerate map from Excel |

## Data format

Place your Excel file at `data/cbe_burning_data.xlsx`. The script prefers **Sheet2** when it exists.

Required columns (name variants are auto-mapped):

- **Zone**
- **Ward**
- **Burning %** (0–1 decimal or 0–100)
- **GPS Coordinates** (`lat, lng`) or separate Latitude / Longitude

Optional columns:

- Region, CCMS ID, Connected Load, Recorded Load, No. of Lights Connected, No. of Non Burning Lights

New zones and wards appear automatically in the filter panel when added to the sheet.

## Deploy on Render

1. Push this repo to GitHub (include `data/cbe_burning_data.xlsx`).
2. On Render: **New → Web Service** → connect the repo.
3. Settings:
   - **Build command:** `pip install -r requirements.txt && cd frontend && npm install && npm run build`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Deploy. The React app is served at your Render URL.

**Production URL:** [https://heat-map-cbe-2.onrender.com](https://heat-map-cbe-2.onrender.com)

You can also use the included `render.yaml` blueprint.

### Environment variables (optional)

| Variable              | Default                                      | Purpose                          |
|-----------------------|----------------------------------------------|----------------------------------|
| `MAP_TITLE`           | Coimbatore Burning Compliance Heat Map       | Map title banner                 |
| `REGENERATE_ON_START` | (unset)                                      | Set to `1` to rebuild map on boot |
| `PORT`                | `5000`                                       | Set automatically on Render      |

## Windows notes

- **Gunicorn does not run on Windows** (`fcntl` is Linux-only). Use `run_server.bat` or `python app.py` locally. Gunicorn works on Render (Linux).
- Always use `.\venv\Scripts\python.exe` and `.\venv\Scripts\pip.exe` instead of global `python` / `pip`.
- The folder name `HEAT_MAP(CBE)` contains parentheses, which can break Python imports on Windows. `app.py` handles this automatically.

## Requirements

- Python 3.10+
- pandas, openpyxl, folium, branca, flask, gunicorn (see `requirements.txt`)
