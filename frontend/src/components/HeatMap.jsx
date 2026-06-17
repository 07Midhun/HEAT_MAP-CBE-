import { useMemo } from "react";
import L from "leaflet";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import RegionCircles from "./RegionCircles";
import { MapResizer } from "./MapHelpers";
import { fmtNum, statusIcon, statusText } from "../utils";

function wardIcon(point) {
  const label = point.wardNum || String(point.ward).split("-").pop();
  const wide = label.length > 2;
  const textColor = point.category === "yellow" ? "#1a237e" : "#ffffff";
  return L.divIcon({
    className: "",
    html: `<div class="ward-bubble${wide ? " wide" : ""}" style="background:${point.color};color:${textColor}">${label}</div>`,
    iconSize: [wide ? 30 : 26, wide ? 30 : 26],
    iconAnchor: [wide ? 15 : 13, wide ? 15 : 13],
  });
}

function popupHtml(point) {
  const glowing =
    point.lightsConnected != null && point.nonBurningLights != null
      ? point.lightsConnected - point.nonBurningLights
      : null;
  const coverage = point.burning.toFixed(1);
  const ccms = point.ccms ? `<div class="sub">CCMS: ${point.ccms}</div>` : "";
  const textOnBadge = point.category === "yellow" ? "#1a237e" : "#fff";

  return `
    <div class="ward-popup">
      <div class="label">Ward Details</div>
      <div class="ward-title">Ward ${point.wardNum}</div>
      <div class="sub">${point.ward}</div>
      ${ccms}
      <div class="row"><span>Zone</span><strong>${point.zone}</strong></div>
      <div class="row">
        <span>Status</span>
        <span class="badge" style="background:${point.color};color:${textOnBadge}">
          ${statusIcon(point.category)} ${statusText(point.category)}
        </span>
      </div>
      <div class="section">This location</div>
      <div class="row"><span>Connected Load</span><strong style="color:#7ec8ff">${fmtNum(point.connectedLoad)} W</strong></div>
      <div class="row"><span>Recorded Load</span><strong style="color:#7ec8ff">${fmtNum(point.recordedLoad)} W</strong></div>
      <div class="row"><span>Lights Connected</span><strong>${fmtNum(point.lightsConnected)}</strong></div>
      <div class="row"><span>Glowing Lights</span><strong style="color:#66bb6a">${fmtNum(glowing)}</strong></div>
      <div class="row"><span>Non-Burning Lights</span><strong style="color:#ef5350">${fmtNum(point.nonBurningLights)}</strong></div>
      <div class="row"><span>Burning %</span><strong style="color:${point.color}">${coverage}%</strong></div>
      <div class="bar-wrap">
        <div class="row" style="border-bottom:none;padding-bottom:0">
          <span>Coverage</span><strong style="color:${point.color}">${coverage}%</strong>
        </div>
        <div class="bar"><span style="width:${Math.min(Number(coverage), 100)}%;background:${point.color}"></span></div>
      </div>
    </div>`;
}

export default function HeatMap({ data, visiblePoints, selectedArea, onSelectArea }) {
  const geoJson = useMemo(
    () => ({
      type: "FeatureCollection",
      features: visiblePoints.map((p) => ({
        type: "Feature",
        properties: p,
        geometry: { type: "Point", coordinates: [p.lng, p.lat] },
      })),
    }),
    [visiblePoints]
  );

  return (
    <MapContainer className="map-frame" center={data.center} zoom={11} scrollWheelZoom>
      <TileLayer
        attribution='&copy; OpenStreetMap &copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      <MapResizer />
      <RegionCircles
        regionAreas={data.regionAreas}
        selectedArea={selectedArea}
        onSelectArea={onSelectArea}
      />
      <GeoJSON
        key={`${visiblePoints.length}-${selectedArea}-${visiblePoints[0]?.date || ""}`}
        data={geoJson}
        pointToLayer={(feature, latlng) =>
          L.marker(latlng, { icon: wardIcon(feature.properties) })
        }
        onEachFeature={(feature, layer) => {
          layer.bindPopup(popupHtml(feature.properties), { maxWidth: 340 });
          layer.bindTooltip(
            `Ward ${feature.properties.wardNum} · ${feature.properties.burning}% · ${feature.properties.ccms || "light"}`
          );
        }}
      />
    </MapContainer>
  );
}
