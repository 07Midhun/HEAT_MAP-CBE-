export default function FilterPanel({
  data,
  filters,
  setFilters,
  wardsForFilter,
  visibleCount,
  totalCount,
  onReset,
}) {
  const set = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));

  const onFromDate = (value) => {
    setFilters((prev) => {
      const next = { ...prev, fromDate: value };
      if (value > prev.toDate) next.toDate = value;
      return next;
    });
  };

  const onToDate = (value) => {
    setFilters((prev) => {
      const next = { ...prev, toDate: value };
      if (value < prev.fromDate) next.fromDate = value;
      return next;
    });
  };

  const onAreaChange = (value) => {
    setFilters((prev) => ({ ...prev, area: value, ward: "ALL" }));
  };

  return (
    <div className="filter-panel">
      <h2>Filters</h2>

      <label htmlFor="filter-date-from">From date</label>
      <select
        id="filter-date-from"
        value={filters.fromDate}
        onChange={(e) => onFromDate(e.target.value)}
      >
        {data.dates.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>

      <label htmlFor="filter-date-to">To date</label>
      <select
        id="filter-date-to"
        value={filters.toDate}
        onChange={(e) => onToDate(e.target.value)}
      >
        {data.dates.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>

      <label htmlFor="filter-area">Region</label>
      <select
        id="filter-area"
        value={filters.area}
        onChange={(e) => onAreaChange(e.target.value)}
      >
        <option value="ALL">All regions</option>
        {data.regionAreas.map((area) => (
          <option key={area.id} value={area.id}>
            {area.fullLabel}
          </option>
        ))}
      </select>
      <div className="filter-hint">Click a labelled circle on the map to filter a region.</div>

      <label htmlFor="filter-ward">Ward</label>
      <select
        id="filter-ward"
        value={filters.ward}
        onChange={(e) => set("ward", e.target.value)}
      >
        <option value="ALL">All wards</option>
        {wardsForFilter.map((w) => (
          <option key={w} value={w}>
            {w}
          </option>
        ))}
      </select>

      <label>Status</label>
      <label className="status-row">
        <input
          type="checkbox"
          checked={filters.red}
          onChange={(e) => set("red", e.target.checked)}
        />{" "}
        Critical (&lt; 50%)
      </label>
      <label className="status-row">
        <input
          type="checkbox"
          checked={filters.green}
          onChange={(e) => set("green", e.target.checked)}
        />{" "}
        Moderate (51% – 90%)
      </label>
      <label className="status-row">
        <input
          type="checkbox"
          checked={filters.yellow}
          onChange={(e) => set("yellow", e.target.checked)}
        />{" "}
        Good (≥ 91%)
      </label>

      <button type="button" className="reset" onClick={onReset}>
        Reset filters
      </button>
      <div className="filter-count">
        Showing {visibleCount} of {totalCount} points
      </div>
    </div>
  );
}
