const CATEGORIES = ["red", "green", "yellow"];

export function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function defaultDates(dates) {
  if (!dates.length) return { fromDate: "", toDate: "" };
  const today = todayIso();
  const toDate = dates.includes(today) ? today : dates[dates.length - 1];
  return { fromDate: dates[0], toDate };
}

export function matchesPoint(point, filters, dateValue) {
  if (dateValue && point.date !== dateValue) return false;
  if (filters.area !== "ALL" && point.zone !== filters.area) return false;
  if (filters.ward !== "ALL" && point.ward !== filters.ward) return false;
  if (point.category === "red" && !filters.red) return false;
  if (point.category === "green" && !filters.green) return false;
  if (point.category === "yellow" && !filters.yellow) return false;
  return true;
}

export function summarize(points, categoryLabels, colors) {
  const total = points.length;
  const counts = { red: 0, green: 0, yellow: 0 };
  points.forEach((p) => {
    counts[p.category] += 1;
  });
  return CATEGORIES.map((cat) => ({
    cat,
    label: categoryLabels[cat],
    color: colors[cat],
    count: counts[cat],
    share: total ? (counts[cat] / total) * 100 : 0,
  }));
}

export function fmtNum(value) {
  return value != null ? Number(value).toLocaleString() : "—";
}

export function statusText(category) {
  return { red: "Critical", green: "Moderate", yellow: "Good" }[category] || category;
}

export function statusIcon(category) {
  return { red: "✕", green: "!", yellow: "✓" }[category] || "•";
}
