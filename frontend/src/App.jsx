import { useEffect, useMemo, useState } from "react";
import AppView from "./AppView";
import { defaultDates, matchesPoint, summarize } from "./utils";

async function fetchMapData() {
  const res = await fetch("/api/map-data");
  if (!res.ok) throw new Error("Failed to load map data");
  return res.json();
}

const defaultStatus = { red: true, green: true, yellow: true };

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState(null);

  useEffect(() => {
    fetchMapData()
      .then((payload) => {
        const dates = defaultDates(payload.dates);
        setData(payload);
        setFilters({
          fromDate: dates.fromDate,
          toDate: dates.toDate,
          area: "ALL",
          ward: "ALL",
          ...defaultStatus,
        });
      })
      .catch((err) => setError(err.message));
  }, []);

  const wardsForFilter = useMemo(() => {
    if (!data || !filters) return [];
    const wards = new Set();
    data.points.forEach((p) => {
      if (p.date !== filters.toDate) return;
      if (filters.area !== "ALL" && p.zone !== filters.area) return;
      wards.add(p.ward);
    });
    return [...wards].sort();
  }, [data, filters]);

  const visibleToPoints = useMemo(() => {
    if (!data || !filters) return { points: [], summary: [], total: 0 };
    const points = data.points.filter((p) => matchesPoint(p, filters, filters.toDate));
    return {
      points,
      summary: summarize(points, data.categoryLabels, data.colors),
      total: points.length,
    };
  }, [data, filters]);

  const visibleFromPoints = useMemo(() => {
    if (!data || !filters) return { points: [], summary: [], total: 0 };
    const points = data.points.filter((p) => matchesPoint(p, filters, filters.fromDate));
    return {
      points,
      summary: summarize(points, data.categoryLabels, data.colors),
      total: points.length,
    };
  }, [data, filters]);

  const onReset = () => {
    if (!data) return;
    const dates = defaultDates(data.dates);
    setFilters({
      fromDate: dates.fromDate,
      toDate: dates.toDate,
      area: "ALL",
      ward: "ALL",
      ...defaultStatus,
    });
  };

  if (error) return <div className="error-box">{error}</div>;
  if (!data || !filters) return <div className="loading">Loading map data…</div>;

  return (
    <AppView
      data={data}
      filters={filters}
      setFilters={setFilters}
      showFilters={showFilters}
      setShowFilters={setShowFilters}
      visibleToPoints={visibleToPoints}
      visibleFromPoints={visibleFromPoints}
      wardsForFilter={wardsForFilter}
      onReset={onReset}
    />
  );
}
