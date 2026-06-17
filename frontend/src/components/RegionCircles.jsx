import { Circle, Tooltip } from "react-leaflet";
import { MapFocus } from "./MapHelpers";

export default function RegionCircles({ regionAreas, selectedArea, onSelectArea }) {
  const active = regionAreas.find((a) => a.id === selectedArea);

  return (
    <>
      {active ? <MapFocus center={active.center} zoom={12} /> : null}
      {regionAreas.map((area) => {
        const isActive = selectedArea === area.id;
        return (
          <Circle
            key={area.id}
            center={area.center}
            radius={area.radiusMeters}
            pathOptions={{
              color: isActive ? "#1a237e" : "#5c6bc0",
              fillColor: isActive ? "#1a237e" : "#3949ab",
              fillOpacity: isActive ? 0.14 : 0.06,
              weight: isActive ? 3.5 : 2,
              dashArray: isActive ? undefined : "10 8",
            }}
            eventHandlers={{
              click: () => onSelectArea(isActive ? "ALL" : area.id),
            }}
          >
            <Tooltip permanent direction="center" className="region-circle-label">
              {area.label}
            </Tooltip>
          </Circle>
        );
      })}
    </>
  );
}
