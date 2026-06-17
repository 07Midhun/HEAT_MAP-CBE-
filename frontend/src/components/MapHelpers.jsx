import { useEffect } from "react";
import { useMap } from "react-leaflet";

export function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => map.invalidateSize(), 120);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}

export function MapFocus({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom ?? map.getZoom(), { duration: 0.8 });
    }
  }, [center, zoom, map]);
  return null;
}
