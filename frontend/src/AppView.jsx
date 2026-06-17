import SummaryPanel from "./components/SummaryPanel";
import FilterPanel from "./components/FilterPanel";
import Legend from "./components/Legend";
import HeatMap from "./components/HeatMap";

export default function App({
  data,
  filters,
  setFilters,
  showFilters,
  setShowFilters,
  visibleToPoints,
  visibleFromPoints,
  wardsForFilter,
  onReset,
}) {
  return (
    <div className="app-shell">
      <div className="title-banner">
        <h1>{data.title}</h1>
        <p>{data.subtitle}</p>
      </div>

      <button
        type="button"
        className="filter-toggle"
        onClick={() => setShowFilters((v) => !v)}
      >
        {showFilters ? "Hide filters" : "Filters"}
      </button>

      {showFilters ? (
        <FilterPanel
          data={data}
          filters={filters}
          setFilters={setFilters}
          wardsForFilter={wardsForFilter}
          visibleCount={visibleToPoints.total}
          totalCount={data.points.length}
          onReset={onReset}
        />
      ) : null}

      <div className="summary-stack">
        <SummaryPanel
          title={`Burning status overview — ${filters.fromDate}`}
          rows={visibleFromPoints.summary}
          total={visibleFromPoints.total}
        />
        <SummaryPanel
          title={`Burning status overview — ${filters.toDate}`}
          rows={visibleToPoints.summary}
          total={visibleToPoints.total}
        />
      </div>

      <Legend colors={data.colors} categoryLabels={data.categoryLabels} />

      <HeatMap
        data={data}
        visiblePoints={visibleToPoints.points}
        selectedArea={filters.area}
        onSelectArea={(area) => setFilters((prev) => ({ ...prev, area, ward: "ALL" }))}
      />
    </div>
  );
}
