"""
Coimbatore (CBE) Burning% Heat Map
Generates a presentation-ready interactive HTML map for officials.
"""

from __future__ import annotations

import argparse
import json
import math
import webbrowser
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
from folium import plugins

# Presentation palette (clear on projector / print)
COLORS = {
    "red": "#D32F2F",
    "yellow": "#F9A825",
    "green": "#2E7D32",
}

CATEGORY_LABELS = {
    "red": "Critical (<= 50%)",
    "green": "Moderate (51% – 99%)",
    "yellow": "Good (100%)",
}

DEFAULT_MAP_TITLE = "COIMBATORE CORPORATION CORE AREA - HEAT MAP"
DEFAULT_MAP_SUBTITLE = "Street-light burning, non burning status"


def classify_burning(pct: float) -> str:
    """Map Burning% to red / yellow / green per official thresholds."""
    if pd.isna(pct):
        return "red"
    if pct >= 100:
        return "yellow"
    if pct >= 51:
        return "green"
    return "red"


def _column_key(col) -> str:
    return str(col).strip().lower().replace(" ", "").replace("_", "")


def _detect_date_column(df: pd.DataFrame) -> str | None:
    """Find a likely date column from common naming variants."""
    for col in df.columns:
        key = _column_key(col)
        if key in (
            "date",
            "readingdate",
            "recordeddate",
            "surveydate",
            "reportdate",
            "entrydate",
            "datestamp",
            "timestamp",
        ):
            return col
    return None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Accept common column name variants from Excel exports."""
    rename = {}
    for col in df.columns:
        key = _column_key(col)
        if key in ("zone", "zonename", "zoneno"):
            rename[col] = "Zone"
        elif key in ("ward", "wardname", "wardno"):
            rename[col] = "Ward"
        elif key in ("burning%", "burning", "burningpct", "burningpercent"):
            rename[col] = "Burning%"
        elif key in ("latitude", "lat", "luminatorlatitude"):
            rename[col] = "Latitude"
        elif key in ("longitude", "long", "lng", "lon", "luminatorlongitude"):
            rename[col] = "Longitude"
        elif key in ("gpscoordinates", "gps", "coordinates"):
            rename[col] = "GPS"
        elif key in ("ccmsid", "ccms"):
            rename[col] = "CCMS ID"
        elif key in ("region",):
            rename[col] = "Region"
        elif key in ("connectedload",):
            rename[col] = "Connected Load"
        elif key in ("recordedload",):
            rename[col] = "Recorded Load"
        elif key in ("nonburningload",):
            rename[col] = "Non Burning Load"
        elif key in ("no.ofnonburninglights", "nonburninglights", "noofnonburninglights"):
            rename[col] = "No. of Non Burning Lights"
        elif key in ("no.oflightsconnected", "lightsconnected", "nooflightsconnected"):
            rename[col] = "No. of Lights Connected"
    out = df.rename(columns=rename)

    date_col = _detect_date_column(out)
    if date_col and date_col != "Date":
        out = out.rename(columns={date_col: "Date"})

    if "GPS" in out.columns and "Latitude" not in out.columns:
        parts = out["GPS"].astype(str).str.split(",", n=1, expand=True)
        out["Latitude"] = pd.to_numeric(parts[0].str.strip(), errors="coerce")
        out["Longitude"] = pd.to_numeric(parts[1].str.strip(), errors="coerce")

    required = ["Zone", "Ward", "Burning%"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    out["Burning%"] = pd.to_numeric(out["Burning%"], errors="coerce")
    if out["Burning%"].max(skipna=True) <= 1:
        out["Burning%"] = out["Burning%"] * 100

    if "Latitude" in out.columns:
        out["Latitude"] = pd.to_numeric(out["Latitude"], errors="coerce")
    if "Longitude" in out.columns:
        out["Longitude"] = pd.to_numeric(out["Longitude"], errors="coerce")
    if "Date" in out.columns:
        parsed = pd.to_datetime(out["Date"], errors="coerce", dayfirst=True)
        out["Date"] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), "")

    for col in (
        "Connected Load",
        "Recorded Load",
        "Non Burning Load",
        "No. of Non Burning Lights",
        "No. of Lights Connected",
    ):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    out = out.dropna(subset=["Burning%", "Latitude", "Longitude"]).copy()
    out["category"] = out["Burning%"].map(classify_burning)
    out["color"] = out["category"].map(COLORS)
    return out


def load_dataset(path: Path) -> pd.DataFrame:
    """Load Sheet2 when present; otherwise pick the best matching worksheet."""
    if path.suffix.lower() in (".xlsx", ".xls"):
        workbook = pd.ExcelFile(path)
        if "Sheet2" in workbook.sheet_names:
            return pd.read_excel(path, sheet_name="Sheet2")

        best_sheet = None
        best_score = -1
        for sheet in workbook.sheet_names:
            preview = pd.read_excel(path, sheet_name=sheet, nrows=5)
            keys = {_column_key(c) for c in preview.columns}
            score = 0
            if any(k in keys for k in ("burning%", "burning", "burningpct")):
                score += 3
            if any(k in keys for k in ("gpscoordinates", "gps", "coordinates")):
                score += 2
            if "zone" in keys:
                score += 1
            if "ward" in keys:
                score += 1
            if score > best_score:
                best_score = score
                best_sheet = sheet
        if best_sheet is None:
            best_sheet = workbook.sheet_names[0]
        return pd.read_excel(path, sheet_name=best_sheet)

    return pd.read_csv(path)


def summary_rows(df: pd.DataFrame) -> str:
    counts = df["category"].value_counts()
    total = len(df)
    rows = []
    for cat in ("red", "yellow", "green"):
        n = int(counts.get(cat, 0))
        pct = (n / total * 100) if total else 0
        rows.append(
            f'<tr data-summary-cat="{cat}">'
            f'<td><span style="display:inline-block;width:12px;height:12px;'
            f'background:{COLORS[cat]};border-radius:2px;margin-right:6px;"></span>'
            f'{CATEGORY_LABELS[cat]}</td>'
            f'<td class="summary-count" style="text-align:right;font-weight:600;">{n}</td>'
            f'<td class="summary-share" style="text-align:right;">{pct:.1f}%</td></tr>'
        )
    return "".join(rows)


def summary_html(df: pd.DataFrame, panel_id: str = "to", title: str = "Burning status overview") -> str:
    total = len(df)
    return f"""
  <div style="font-family:Segoe UI,Arial,sans-serif;min-width:260px;">
    <div style="font-size:15px;font-weight:700;margin-bottom:8px;color:#1a237e;" id="summary-title-{panel_id}">
      {title}
    </div>
    <table style="width:100%;font-size:13px;border-collapse:collapse;">
      <thead>
        <tr style="color:#555;border-bottom:1px solid #ddd;">
          <th style="text-align:left;padding:4px 0;">Category</th>
          <th style="text-align:right;">Points</th>
          <th style="text-align:right;">Share</th>
        </tr>
      </thead>
      <tbody id="summary-body-{panel_id}">{summary_rows(df)}</tbody>
      <tfoot>
        <tr style="border-top:1px solid #ddd;font-weight:700;">
          <td style="padding-top:6px;">Total</td>
          <td id="summary-total-{panel_id}" style="text-align:right;padding-top:6px;">{total}</td>
          <td style="text-align:right;padding-top:6px;">100%</td>
        </tr>
      </tfoot>
    </table>
  </div>
  """


def ward_number(ward: str) -> str:
    """Extract display number from values like CJB-S-76 -> 76."""
    ward = str(ward).strip()
    if "-" in ward:
        return ward.rsplit("-", 1)[-1]
    return ward


def ward_summary_payload(df: pd.DataFrame) -> dict[str, dict]:
    """Aggregate load and light stats per ward for detail popups."""
    summaries: dict[str, dict] = {}
    for (zone, ward), group in df.groupby(["Zone", "Ward"]):
        ward_str = str(ward)
        zone_str = str(zone)
        burning = float(group["Burning%"].mean())
        category = classify_burning(burning)
        entry: dict = {
            "zone": zone_str,
            "ward": ward_str,
            "wardNum": ward_number(ward_str),
            "region": (
                str(group["Region"].iloc[0])
                if "Region" in group.columns and group["Region"].notna().any()
                else ""
            ),
            "burning": round(burning, 1),
            "category": category,
            "color": COLORS[category],
            "label": CATEGORY_LABELS[category],
            "points": int(len(group)),
        }
        if "Connected Load" in group.columns:
            entry["connectedLoad"] = int(group["Connected Load"].sum())
        if "Recorded Load" in group.columns:
            entry["recordedLoad"] = int(group["Recorded Load"].sum())
        if "No. of Non Burning Lights" in group.columns:
            entry["nonBurningLights"] = int(group["No. of Non Burning Lights"].sum())
        if "No. of Lights Connected" in group.columns:
            lights = int(group["No. of Lights Connected"].sum())
            entry["lightsConnected"] = lights
            entry["glowingLights"] = lights - entry.get("nonBurningLights", 0)
        summaries[f"{zone_str}|{ward_str}"] = entry
    return summaries


def points_payload(df: pd.DataFrame) -> list[dict]:
    records = []
    for _, row in df.iterrows():
        ward = str(row["Ward"])
        zone = str(row["Zone"])

        def _int_val(col: str):
            if col not in row.index or pd.isna(row[col]):
                return None
            return int(row[col])

        records.append(
            {
                "zone": zone,
                "ward": ward,
                "wardKey": f"{zone}|{ward}",
                "wardNum": ward_number(ward),
                "pointKey": (
                    str(row["CCMS ID"])
                    if "CCMS ID" in row and pd.notna(row["CCMS ID"]) and str(row["CCMS ID"]).strip()
                    else f"{zone}|{ward}|{float(row['Latitude']):.6f}|{float(row['Longitude']):.6f}"
                ),
                "region": str(row["Region"]) if "Region" in row and pd.notna(row["Region"]) else "",
                "category": row["category"],
                "burning": round(float(row["Burning%"]), 1),
                "color": row["color"],
                "lat": float(row["Latitude"]),
                "lng": float(row["Longitude"]),
                "ccms": str(row["CCMS ID"]) if "CCMS ID" in row and pd.notna(row["CCMS ID"]) else "",
                "date": str(row["Date"]) if "Date" in row and pd.notna(row["Date"]) else "",
                "label": CATEGORY_LABELS[row["category"]],
                "connectedLoad": _int_val("Connected Load"),
                "recordedLoad": _int_val("Recorded Load"),
                "nonBurningLights": _int_val("No. of Non Burning Lights"),
                "lightsConnected": _int_val("No. of Lights Connected"),
            }
        )
    return records


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def region_circles_payload(df: pd.DataFrame) -> dict[str, dict]:
    """Bounding circle per region for map highlight when filtered."""
    if "Region" not in df.columns:
        return {}
    return _circles_for_column(df, "Region")


def zone_circles_payload(df: pd.DataFrame) -> dict[str, dict]:
    """Bounding circle per zone (e.g. CJB-N) for map highlight when filtered."""
    return _circles_for_column(df, "Zone")


def _circles_for_column(df: pd.DataFrame, column: str) -> dict[str, dict]:
    circles: dict[str, dict] = {}
    for name, group in df.groupby(column):
        label = str(name).strip()
        if not label:
            continue
        lats = group["Latitude"].astype(float)
        lngs = group["Longitude"].astype(float)
        center_lat = float(lats.mean())
        center_lng = float(lngs.mean())
        max_dist = 0.0
        for lat, lng in zip(lats, lngs):
            max_dist = max(max_dist, _haversine_meters(center_lat, center_lng, float(lat), float(lng)))
        circles[label] = {
            "center": [center_lat, center_lng],
            "radiusMeters": max(max_dist * 1.1 + 400, 800),
        }
    return circles


ZONE_REGION_NAMES = {
    "CJB-N": "North",
    "CJB-S": "South",
    "CJB-C": "Central",
    "CJB-E": "East",
    "CJB-W": "West",
}


def region_areas_payload(df: pd.DataFrame) -> list[dict]:
    """Map zones to named regions with bounding circles for the React map."""
    zones = zone_circles_payload(df)
    areas: list[dict] = []
    for zone_id in sorted(zones):
        circle = zones[zone_id]
        label = ZONE_REGION_NAMES.get(zone_id, zone_id.rsplit("-", 1)[-1])
        areas.append(
            {
                "id": zone_id,
                "label": label,
                "fullLabel": f"{label} ({zone_id})",
                "center": circle["center"],
                "radiusMeters": circle["radiusMeters"],
            }
        )
    return areas


def build_api_payload(
    df: pd.DataFrame,
    title: str = DEFAULT_MAP_TITLE,
    subtitle: str = DEFAULT_MAP_SUBTITLE,
) -> dict:
    """JSON payload for the React frontend."""
    dates = sorted(d for d in df["Date"].dropna().astype(str).unique() if d.strip()) if "Date" in df.columns else []
    zones = sorted(df["Zone"].dropna().astype(str).unique())
    return {
        "title": title,
        "subtitle": subtitle,
        "points": points_payload(df),
        "dates": dates,
        "zones": zones,
        "regionAreas": region_areas_payload(df),
        "colors": COLORS,
        "categoryLabels": CATEGORY_LABELS,
        "center": [float(df["Latitude"].mean()), float(df["Longitude"].mean())],
    }


def filter_panel_html(df: pd.DataFrame) -> str:
    zones = sorted(df["Zone"].dropna().astype(str).unique())
    wards = sorted(df["Ward"].dropna().astype(str).unique())
    regions = (
        sorted(df["Region"].dropna().astype(str).unique())
        if "Region" in df.columns
        else []
    )
    dates = sorted(d for d in df["Date"].dropna().astype(str).unique() if d.strip()) if "Date" in df.columns else []

    zone_opts = '<option value="ALL">All zones</option>' + "".join(
        f'<option value="{z}">{z}</option>' for z in zones
    )
    ward_opts = '<option value="ALL">All wards</option>' + "".join(
        f'<option value="{w}">{w}</option>' for w in wards
    )
    region_block = ""
    if regions:
        region_opts = '<option value="ALL">All regions</option>' + "".join(
            f'<option value="{r}">{r}</option>' for r in regions
        )
        region_block = f"""
        <label style="font-size:12px;color:#444;">Region</label>
        <select id="filter-region" style="width:100%;margin:4px 0 10px;padding:6px;border:1px solid #ccc;border-radius:4px;">
          {region_opts}
        </select>
        """

    date_block = ""
    if dates:
        date_opts = "".join(
            f'<option value="{d}">{d}</option>' for d in dates
        )
        date_block = f"""
        <label style="font-size:12px;color:#444;">From date</label>
        <select id="filter-date-from" style="width:100%;margin:4px 0 10px;padding:6px;border:1px solid #ccc;border-radius:4px;">
          {date_opts}
        </select>
        <label style="font-size:12px;color:#444;">To date</label>
        <select id="filter-date-to" style="width:100%;margin:4px 0 10px;padding:6px;border:1px solid #ccc;border-radius:4px;">
          {date_opts}
        </select>
        """

    return f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;min-width:220px;">
      <div style="font-size:15px;font-weight:700;margin-bottom:10px;color:#1a237e;">Filters</div>
      {date_block}
      {region_block}
      <label style="font-size:12px;color:#444;">Zone</label>
      <select id="filter-zone" style="width:100%;margin:4px 0 10px;padding:6px;border:1px solid #ccc;border-radius:4px;">
        {zone_opts}
      </select>
      <label style="font-size:12px;color:#444;">Ward</label>
      <select id="filter-ward" style="width:100%;margin:4px 0 10px;padding:6px;border:1px solid #ccc;border-radius:4px;">
        {ward_opts}
      </select>
      <label style="font-size:12px;color:#444;display:block;margin-bottom:6px;">Status</label>
      <label style="display:block;font-size:12px;margin:4px 0;">
        <input type="checkbox" id="filter-red" checked> Critical (<= 50%)
      </label>
      <label style="display:block;font-size:12px;margin:4px 0;">
        <input type="checkbox" id="filter-green" checked> Moderate (51% – 99%)
      </label>
      <label style="display:block;font-size:12px;margin:4px 0;">
        <input type="checkbox" id="filter-yellow" checked> Good (100%)
      </label>
      <button id="filter-reset" type="button"
        style="margin-top:10px;width:100%;padding:7px;border:none;border-radius:4px;
        background:#1a237e;color:white;font-weight:600;cursor:pointer;">
        Reset filters
      </button>
      <div id="filter-count" style="margin-top:8px;font-size:11px;color:#666;"></div>
    </div>
    """


def filter_script(map_id: str, points: list[dict], ward_summaries: dict[str, dict]) -> str:
    points_json = json.dumps(points)
    ward_json = json.dumps(ward_summaries)
    return f"""
    (function() {{
      function initBurningMapFilters() {{
        const map = {map_id};
        if (!map || typeof L === "undefined") return;
        const allPoints = {points_json};
        const wardSummaries = {ward_json};
        const markersLayer = L.layerGroup().addTo(map);

      function detailRow(label, value, valueColor) {{
        return `<div style="display:flex;justify-content:space-between;align-items:center;
          padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
          <span style="opacity:0.88;font-size:13px;">${{label}}</span>
          <span style="font-weight:700;font-size:13px;color:${{valueColor || "#fff"}};">${{value}}</span>
        </div>`;
      }}

      function fmtNum(value) {{
        return value != null ? Number(value).toLocaleString() : "—";
      }}

      function statusBadgeFrom(category, color, label) {{
        const icons = {{red: "✕", green: "!", yellow: "✓"}};
        const text = {{
          red: "Critical",
          green: "Moderate",
          yellow: "Good"
        }}[category] || label;
        return `<span style="display:inline-flex;align-items:center;gap:5px;
          background:${{color}};color:#fff;padding:3px 10px;border-radius:999px;
          font-size:11px;font-weight:700;">${{icons[category] || "•"}} ${{text}}</span>`;
      }}

      function sectionTitle(text) {{
        return `<div style="font-size:10px;letter-spacing:1px;text-transform:uppercase;
          opacity:0.55;margin:12px 0 6px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.12);">
          ${{text}}</div>`;
      }}

      function buildDetailPopup(point) {{
        const coverage = point.burning.toFixed(1);
        const glowingPoint = point.lightsConnected != null && point.nonBurningLights != null
          ? point.lightsConnected - point.nonBurningLights
          : null;

        const ccmsLine = point.ccms
          ? `<div style="font-size:11px;color:#90caf9;margin-bottom:8px;">CCMS: ${{point.ccms}}</div>`
          : "";

        return `
          <div style="font-family:Segoe UI,Arial,sans-serif;min-width:280px;max-width:320px;
            background:linear-gradient(145deg,#1a2744 0%,#121c33 100%);
            color:#fff;padding:14px 16px;border-radius:12px;
            box-shadow:0 8px 24px rgba(0,0,0,0.35);">
            <div style="font-size:10px;letter-spacing:1.2px;opacity:0.65;text-transform:uppercase;">
              Ward Details
            </div>
            <div style="font-size:20px;font-weight:800;color:#F9A825;margin:6px 0 2px;">
              Ward ${{point.wardNum}}
            </div>
            <div style="font-size:12px;opacity:0.75;margin-bottom:10px;">${{point.ward}}</div>
            ${{ccmsLine}}
            ${{detailRow("Zone", point.zone)}}
            <div style="display:flex;justify-content:space-between;align-items:center;
              padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
              <span style="opacity:0.88;font-size:13px;">Status</span>
              ${{statusBadgeFrom(point.category, point.color, point.label)}}
            </div>
            ${{sectionTitle("This location")}}
            ${{detailRow("Connected Load", fmtNum(point.connectedLoad) + " W", "#7ec8ff")}}
            ${{detailRow("Recorded Load", fmtNum(point.recordedLoad) + " W", "#7ec8ff")}}
            ${{detailRow("Lights Connected", fmtNum(point.lightsConnected))}}
            ${{detailRow("Glowing Lights", fmtNum(glowingPoint), "#66bb6a")}}
            ${{detailRow("Non-Burning Lights", fmtNum(point.nonBurningLights), "#ef5350")}}
            ${{detailRow("Burning %", coverage + "%", point.color)}}
            <div style="margin-top:10px;">
              <div style="display:flex;justify-content:space-between;font-size:12px;opacity:0.85;">
                <span>Coverage</span>
                <span style="font-weight:700;color:${{point.color}};">${{coverage}}%</span>
              </div>
              <div style="height:6px;background:rgba(255,255,255,0.15);border-radius:4px;margin-top:6px;overflow:hidden;">
                <div style="width:${{Math.min(Number(coverage), 100)}}%;height:100%;background:${{point.color}};border-radius:4px;"></div>
              </div>
            </div>
          </div>`;
      }}

      function popupHtml(point) {{
        const ccms = point.ccms
          ? `<div style="font-size:11px;color:#888;">CCMS: ${{point.ccms}}</div>`
          : "";
        return `
          <div style="font-family:Segoe UI,Arial,sans-serif;min-width:180px;">
            <div style="font-weight:700;font-size:14px;color:#1a237e;">Zone ${{point.zone}}</div>
            <div style="margin:4px 0;">Ward <b>${{point.ward}}</b></div>
            ${{ccms}}
            <div style="font-size:22px;font-weight:700;color:${{point.color}};">${{point.burning}}%</div>
            <div style="font-size:11px;color:#666;margin-top:4px;">${{point.label}}</div>
          </div>`;
      }}

      function selectedValue(id) {{
        const el = document.getElementById(id);
        return el ? el.value : "ALL";
      }}

      function isChecked(id) {{
        const el = document.getElementById(id);
        return el ? el.checked : true;
      }}

      function matchesFilters(point, dateValue) {{
        const zone = selectedValue("filter-zone");
        const ward = selectedValue("filter-ward");
        const region = selectedValue("filter-region");
        const date = dateValue || selectedValue("filter-date-to");
        if (date && point.date !== date) return false;
        if (region !== "ALL" && point.region !== region) return false;
        if (zone !== "ALL" && point.zone !== zone) return false;
        if (ward !== "ALL" && point.ward !== ward) return false;
        if (point.category === "red" && !isChecked("filter-red")) return false;
        if (point.category === "yellow" && !isChecked("filter-yellow")) return false;
        if (point.category === "green" && !isChecked("filter-green")) return false;
        return true;
      }}

      function updateWardOptions() {{
        const wardSelect = document.getElementById("filter-ward");
        if (!wardSelect) return;
        const zone = selectedValue("filter-zone");
        const region = selectedValue("filter-region");
        const toDate = selectedValue("filter-date-to");
        const current = wardSelect.value;
        const wards = [...new Set(
          allPoints
            .filter(p => (!toDate || p.date === toDate))
            .filter(p => (zone === "ALL" || p.zone === zone))
            .filter(p => (region === "ALL" || !p.region || p.region === region))
            .map(p => p.ward)
        )].sort();
        wardSelect.innerHTML = '<option value="ALL">All wards</option>' +
          wards.map(w => `<option value="${{w}}">${{w}}</option>`).join("");
        if (wards.includes(current)) wardSelect.value = current;
      }}

      function updateSummaryPanel(visible, panelId, dateLabel) {{
        const total = visible.length;
        const counts = {{red: 0, yellow: 0, green: 0}};
        visible.forEach(p => counts[p.category] += 1);
        ["red", "yellow", "green"].forEach(cat => {{
          const row = document.querySelector(`#summary-body-${{panelId}} tr[data-summary-cat="${{cat}}"]`);
          if (!row) return;
          const n = counts[cat];
          const pct = total ? (n / total * 100) : 0;
          row.querySelector(".summary-count").textContent = n;
          row.querySelector(".summary-share").textContent = pct.toFixed(1) + "%";
        }});
        const totalEl = document.getElementById(`summary-total-${{panelId}}`);
        if (totalEl) totalEl.textContent = total;
        const titleEl = document.getElementById(`summary-title-${{panelId}}`);
        if (titleEl && dateLabel) {{
          titleEl.textContent = `Burning status overview — ${{dateLabel}}`;
        }}
      }}

      function updateSummaries(visibleTo) {{
        const fromDate = selectedValue("filter-date-from");
        const toDate = selectedValue("filter-date-to");
        const fromVisible = allPoints.filter(p => matchesFilters(p, fromDate));
        updateSummaryPanel(fromVisible, "from", fromDate);
        updateSummaryPanel(visibleTo, "to", toDate);
        const countEl = document.getElementById("filter-count");
        if (countEl) countEl.textContent = `Showing ${{visibleTo.length}} of ${{allPoints.length}} points`;
      }}

      function markerIcon(point) {{
        const label = point.wardNum || point.ward.split("-").pop();
        const size = label.length > 2 ? 30 : 26;
        const fontSize = label.length > 2 ? 8 : 10;
        const textColor = point.category === "yellow" ? "#1a237e" : "#ffffff";
        return L.divIcon({{
          className: "ward-bubble-icon",
          html: `<div style="
            width:${{size}}px;height:${{size}}px;border-radius:50%;
            background:${{point.color}};border:2px solid #ffffff;
            display:flex;align-items:center;justify-content:center;
            font-size:${{fontSize}}px;font-weight:700;color:${{textColor}};
            box-shadow:0 1px 5px rgba(0,0,0,0.28);
            font-family:Segoe UI,Arial,sans-serif;">${{label}}</div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        }});
      }}

      function renderMarkers() {{
        markersLayer.clearLayers();
        const visible = allPoints.filter(p => matchesFilters(p, selectedValue("filter-date-to")));
        visible.forEach(pt => {{
          const marker = L.marker([pt.lat, pt.lng], {{ icon: markerIcon(pt) }});
          marker.bindPopup(() => buildDetailPopup(pt), {{ maxWidth: 340 }});
          marker.bindTooltip(`Ward ${{pt.wardNum}} · ${{pt.burning}}% · ${{pt.ccms || "light"}}`);
          marker.addTo(markersLayer);
        }});
        updateSummaries(visible);
      }}

      function resetFilters() {{
        ["filter-zone", "filter-ward", "filter-region"].forEach(id => {{
          const el = document.getElementById(id);
          if (el) el.value = "ALL";
        }});
        ["filter-red", "filter-yellow", "filter-green"].forEach(id => {{
          const el = document.getElementById(id);
          if (el) el.checked = true;
        }});
        defaultDateValue();
        updateWardOptions();
        renderMarkers();
      }}

      function defaultDateValue() {{
        const fromEl = document.getElementById("filter-date-from");
        const toEl = document.getElementById("filter-date-to");
        if (!fromEl || !toEl) return;
        const available = Array.from(toEl.options)
          .map(opt => opt.value)
          .filter(v => v);
        if (!available.length) return;
        const today = new Date().toISOString().slice(0, 10);
        const preferred = available.includes(today) ? today : available[available.length - 1];
        toEl.value = preferred;
        fromEl.value = available[0];
      }}

      function setupFilterPanelToggle() {{
        const panel = document.getElementById("filter-panel");
        const toggle = document.getElementById("filter-toggle");
        if (!panel || !toggle) return;
        toggle.addEventListener("click", () => {{
          const hidden = panel.style.display === "none";
          panel.style.display = hidden ? "block" : "none";
          toggle.textContent = hidden ? "Hide filters" : "Filters";
        }});
      }}

      ["filter-date-from", "filter-date-to", "filter-zone", "filter-ward", "filter-region",
       "filter-red", "filter-yellow", "filter-green"].forEach(id => {{
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("change", () => {{
          const fromEl = document.getElementById("filter-date-from");
          const toEl = document.getElementById("filter-date-to");
          if (fromEl && toEl && fromEl.value > toEl.value) {{
            if (id === "filter-date-from") toEl.value = fromEl.value;
            else fromEl.value = toEl.value;
          }}
          if (id === "filter-date-to" || id === "filter-zone" || id === "filter-region") updateWardOptions();
          renderMarkers();
        }});
      }});

      const resetBtn = document.getElementById("filter-reset");
      if (resetBtn) resetBtn.addEventListener("click", resetFilters);

        setupFilterPanelToggle();
        defaultDateValue();
        updateWardOptions();
        renderMarkers();
      }}

      window.addEventListener("load", initBurningMapFilters);
    }})();
    """


def build_map(
    df: pd.DataFrame,
    title: str,
    subtitle: str = DEFAULT_MAP_SUBTITLE,
) -> folium.Map:
    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # Subtle base context
    folium.TileLayer("OpenStreetMap", name="Street map").add_to(m)

    title_html = f"""
    <div style="
      position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:9999;
      background:rgba(255,255,255,0.95);padding:10px 22px 12px;border-radius:8px;
      box-shadow:0 2px 12px rgba(0,0,0,0.18);font-family:Segoe UI,Arial,sans-serif;
      border-top:4px solid #1a237e;text-align:center;">
      <div style="font-size:18px;font-weight:700;color:#1a237e;">{title}</div>
      <div style="font-size:12px;color:#555;margin-top:4px;text-align:center;">
        {subtitle}
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    bubble_style = """
    <style>
      .ward-bubble-icon {
        background: transparent !important;
        border: none !important;
      }
      .leaflet-popup-content-wrapper {
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        border-radius: 12px !important;
      }
      .leaflet-popup-content {
        margin: 0 !important;
        width: auto !important;
      }
      .leaflet-popup-tip {
        background: #1a2744 !important;
      }
    </style>
    """
    m.get_root().html.add_child(folium.Element(bubble_style))

    points = points_payload(df)
    ward_summaries = ward_summary_payload(df)
    map_id = m.get_name()

    filter_box = f"""
    <button id="filter-toggle" type="button" style="
      position:fixed;top:80px;right:12px;z-index:10000;
      background:#1a237e;color:#fff;border:none;border-radius:6px;
      padding:8px 12px;font-size:12px;font-weight:700;cursor:pointer;
      box-shadow:0 2px 10px rgba(0,0,0,0.25);">
      Filters
    </button>
    <div id="filter-panel" style="
      display:none;position:fixed;top:118px;right:12px;z-index:9999;
      background:rgba(255,255,255,0.97);padding:12px 14px;border-radius:8px;
      box-shadow:0 2px 12px rgba(0,0,0,0.18);max-height:68vh;max-width:290px;overflow:auto;">
      {filter_panel_html(df)}
    </div>
    """
    m.get_root().html.add_child(folium.Element(filter_box))
    m.get_root().script.add_child(folium.Element(filter_script(map_id, points, ward_summaries)))

    legend = cm.StepColormap(
        colors=[COLORS["red"], COLORS["green"], COLORS["yellow"]],
        index=[0, 51, 100],
        vmin=0,
        vmax=100,
        caption="Burning % compliance",
        tick_labels=["0", "51", "100"],
    )
    legend.add_to(m)

    summary_from_panel = f"""
    <div style="
      position:fixed;bottom:280px;left:12px;z-index:9999;
      background:rgba(255,255,255,0.96);padding:12px 14px;border-radius:8px;
      box-shadow:0 2px 12px rgba(0,0,0,0.18);">
      {summary_html(df, panel_id="from", title="Burning status overview — From date")}
    </div>
    """
    m.get_root().html.add_child(folium.Element(summary_from_panel))

    summary_panel = f"""
    <div style="
      position:fixed;bottom:24px;left:12px;z-index:9999;
      background:rgba(255,255,255,0.96);padding:12px 14px;border-radius:8px;
      box-shadow:0 2px 12px rgba(0,0,0,0.18);">
      {summary_html(df, panel_id="to", title="Burning status overview — To date")}
    </div>
    """
    m.get_root().html.add_child(folium.Element(summary_panel))

    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MiniMap(toggle_display=True, position="bottomright").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def render_map_html(
    df: pd.DataFrame,
    title: str = DEFAULT_MAP_TITLE,
    subtitle: str = DEFAULT_MAP_SUBTITLE,
) -> str:
    """Return a complete standalone HTML document for the heat map."""
    m = build_map(df, title, subtitle)
    return m.get_root().render()


def generate_map(
    input_path: Path | str,
    output_path: Path | str,
    title: str = DEFAULT_MAP_TITLE,
    subtitle: str = DEFAULT_MAP_SUBTITLE,
) -> Path:
    """Build the heat map HTML file and return the output path."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if input_path.suffix.lower() in (".xlsx", ".xls", ".csv"):
        raw = load_dataset(input_path)
    else:
        raise ValueError("Input must be .xlsx, .xls, or .csv")

    df = normalize_columns(raw)
    html = render_map_html(df, title, subtitle)
    output_path.write_text(html, encoding="utf-8")
    return output_path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CBE Burning% heat map")
    parser.add_argument(
        "--input",
        "-i",
        default="data/cbe_burning_data.xlsx",
        help="Excel/CSV path (default: data/cbe_burning_data.xlsx)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output/cbe_burning_heatmap.html",
        help="Output HTML path",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_MAP_TITLE,
        help="Map title for presentation",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Save HTML only; do not open the map in a browser",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    generate_map(input_path, output_path, args.title)
    output_file = output_path.resolve()

    if not args.no_open:
        webbrowser.open(output_file.as_uri())

    df = normalize_columns(load_dataset(input_path))

    print(f"Opening map in your browser: {output_file}")
    print(f"Data points on map: {len(df)}")
    print(f"Zones: {', '.join(sorted(df['Zone'].astype(str).unique()))}")
    print(df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()
