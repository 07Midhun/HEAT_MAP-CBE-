# Coimbatore Burning Compliance Heat Map  
## Implementation Steps — Briefing for Higher Officials

**Document purpose:** This note explains how the heat map system was built, what it shows, and how it can be used in review meetings and field follow-up.

---

## 1. Objective

To convert street-light burning data from CCMS / field records into a **single, visual, interactive map** so that officials can:

- See compliance status across **zones and wards** at a glance  
- Identify **critical areas** (low burning %) quickly  
- Drill down to **individual light points** with load and non-burning details  
- Use the same view in **presentations, reviews, and web access**

---

## 2. Implementation Overview

The project was implemented in **five connected steps**:

| Step | What was done | Outcome |
|------|----------------|---------|
| 1 | Data preparation | Standard Excel format with GPS and burning % |
| 2 | Compliance rules | Red / Yellow / Green classification applied |
| 3 | Map generation | All CCMS points plotted on Coimbatore map |
| 4 | Interactive dashboard | Filters, summary table, and detail popups |
| 5 | Web hosting | Map accessible via browser link (Render deployment) |

---

## 3. Step-by-Step Implementation

### Step 1 — Data collection and standardization

**What we did**

- Collected burning data from the existing Excel report (`cbe_burning_data.xlsx`, **Sheet2**).
- Each row represents **one CCMS / light location**, not only ward totals.
- Standardized key fields:
  - Zone, Ward, Burning %
  - GPS coordinates (latitude & longitude)
  - Connected Load, Recorded Load
  - Lights connected, Non-burning lights
  - CCMS ID (where available)

**Why it matters**

- Officials see **actual field locations**, not averaged ward numbers only.
- New zones (e.g. Central, North) can be added by updating the Excel sheet — the map updates automatically.

---

### Step 2 — Compliance classification (official thresholds)

Burning percentage is classified into three clear bands for decision-making:

| Burning % | Status | Colour | Action level |
|-----------|--------|--------|--------------|
| Below 50% | Critical | Red | Immediate attention |
| 50% – 90% | Moderate | Yellow | Monitoring / planned action |
| 91% and above | Good | Green | Satisfactory compliance |

This colour rule is applied **uniformly to every point** on the map and in all filters and summaries.

---

### Step 3 — Geographic heat map creation

**What we did**

- Built an automated script (`generate_heatmap.py`) that reads the Excel file and places each point on a **Coimbatore city map**.
- Each location is shown as a **coloured bubble** with the **ward number inside** (e.g. ward 76 appears as “76”).
- Map is centred on the average location of all plotted points for a balanced city view.
- Base map layers (street map / light background) are included for orientation during presentations.

**Current coverage**

- Zone: **CJB-S** (South) — 5 wards, **167 light points** plotted  
- Design supports adding more zones without changing the core system

---

### Step 4 — Interactive features for review meetings

The map is not a static image. It is an **interactive dashboard** suitable for projector / large-screen use.

| Feature | Location on screen | Use for officials |
|---------|-------------------|-------------------|
| Title banner | Top centre | Meeting title and context |
| Filter panel | Top right | Filter by Region, Zone, Ward, and status (Red/Yellow/Green) |
| Summary table | Bottom left | Live counts: total points, compliance breakdown |
| Colour legend | On map | Explains Red / Yellow / Green meaning |
| Marker click | On any bubble | Opens **Ward Details** popup for that CCMS point |
| Fullscreen | Top left | Presentation mode |
| Mini map | Bottom right | Navigation aid |

**Detail popup (per location)** shows:

- Ward number and CCMS ID  
- Zone and compliance status badge  
- Connected Load, Recorded Load  
- Lights connected, Glowing lights, Non-burning lights  
- Burning % with visual coverage bar  

---

### Step 5 — Web deployment for wider access

**What we did**

- Wrapped the map in a small web application (`app.py`).
- Configured cloud hosting on **Render** so officials can open the map from a **URL** (no local software install required on their device).
- Server uses **Gunicorn** (industry-standard for Python web apps on Linux servers).

**Access modes**

| Mode | How | Best for |
|------|-----|----------|
| Local file | Double-click `run.bat` | Development and offline demo on one PC |
| Local web server | `run_server.bat` | Testing before going live |
| Cloud (Render) | Shared web link | Officials, meetings, remote review |

---

## 4. Data Flow (simple view)

```
Excel data (Sheet2)
        ↓
Read & validate (Zone, Ward, Burning %, GPS)
        ↓
Apply Red / Yellow / Green rules
        ↓
Plot all points on Coimbatore map
        ↓
Add filters, summary, popups
        ↓
Save as interactive HTML  →  Serve on web (Render)
```

---

## 5. How to Use in an Official Review Meeting

**Recommended flow (5–10 minutes)**

1. **Open the map** — browser link (Render) or local `run.bat` output.  
2. **Show full city view** — explain colour meaning using the legend.  
3. **Filter to one zone or ward** — e.g. CJB-S, Ward 76.  
4. **Point out red / yellow clusters** — areas needing action.  
5. **Click a marker** — show CCMS-level load and non-burning light count.  
6. **Refer to summary table** — quote total points and compliance split for the filtered area.  
7. **Reset filters** — return to full city view for closing summary.

---

## 6. Updating Data (ongoing operations)

When new field data is available:

1. Update `data/cbe_burning_data.xlsx` (Sheet2).  
2. Regenerate the map:
   - **Local:** run `run.bat`, or  
   - **Web:** redeploy on Render, or call refresh if configured.  
3. New zones, wards, and points appear automatically in filters and on the map.

No manual re-plotting of individual markers is required.

---

## 7. Scalability and Next Phase

The system is built to scale as more areas are onboarded:

| Phase | Scope | Status |
|-------|--------|--------|
| Phase 1 | CJB-S zone (5 wards, 167 points) | Implemented |
| Phase 2 | Additional zones (Central, North, etc.) | Add rows to Excel |
| Phase 3 | Ward boundary shading (optional) | Can be added with ward GeoJSON |

---

## 8. Summary for Higher Officials

**In one sentence:**  
*We took CCMS burning data, applied official compliance colours, plotted every light point on a Coimbatore map, and made it interactive and web-accessible for monitoring and review.*

**Key benefits**

- **Visibility** — compliance visible city-wide, not only in spreadsheets  
- **Accountability** — drill-down to individual CCMS / location  
- **Speed** — filters and summary update instantly in meetings  
- **Scalability** — more zones added by updating one Excel file  
- **Accessibility** — shareable web link for officials and stakeholders  

---

## 9. Technical Reference (for IT / support staff)

| Item | Detail |
|------|--------|
| Source data | `data/cbe_burning_data.xlsx` (Sheet2) |
| Generator | `generate_heatmap.py` |
| Web app | `app.py` |
| Output | `output/cbe_burning_heatmap.html` |
| Cloud start command | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Full setup guide | See `README.md` |

---

*Coimbatore Municipal Corporation — Street-light burning compliance heat map*  
*Prepared for official briefing and presentation use*
