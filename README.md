# Coimbatore (CBE) Burning Compliance Heat Map

Interactive heat map of street-light burning compliance for Coimbatore officials. Reads Excel data, plots each CCMS/light point on a Folium map, and serves it locally or on [Render](https://render.com) via Flask + Gunicorn.

**For higher officials:** see [IMPLEMENTATION_STEPS.md](IMPLEMENTATION_STEPS.md) — step-by-step briefing on what was built and how to use it in review meetings.

## Features

- Color-coded markers by burning percentage (red / yellow / green)
- Ward number shown inside each marker bubble
- Live filters: Region, Zone, Ward, and status checkboxes
- Summary table updates with active filters
- Click popup with per-point CCMS details (load, lights, burning %)
- Fullscreen, minimap, and layer controls

## Color rules

| Burning % | Status   | Color  |
|-----------|----------|--------|
| &lt; 50%  | Critical | Red    |
| 50–90%    | Moderate | Yellow |
| ≥ 91%     | Good     | Green  |

## Project structure

```
HEAT_MAP(CBE)/
├── data/
│   └── cbe_burning_data.xlsx   # Source data (Sheet2)
├── output/
│   └── cbe_burning_heatmap.html
├── app.py                      # Flask web app (Render / local server)
├── generate_heatmap.py         # Map generator
├── requirements.txt
├── render.yaml                   # Render deployment blueprint
├── run.bat                       # Generate map + open in browser
├── run_server.bat                # Start local web server (Windows)
└── open_map.bat                  # Open existing HTML only
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

### Run web server (preview deployment)

Double-click **`run_server.bat`**, or:

```powershell
.\venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000** in your browser.

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
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Deploy. The map is served at your Render URL.

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
