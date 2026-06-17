export default function Legend({ colors, categoryLabels }) {
  return (
    <div className="legend-box">
      <strong>Burning % compliance</strong>
      <div className="row">
        <span className="swatch" style={{ background: colors.red }} />
        <span>0 – 50% · {categoryLabels.red}</span>
      </div>
      <div className="row">
        <span className="swatch" style={{ background: colors.green }} />
        <span>51 – 90% · {categoryLabels.green}</span>
      </div>
      <div className="row">
        <span className="swatch" style={{ background: colors.yellow }} />
        <span>91 – 100% · {categoryLabels.yellow}</span>
      </div>
    </div>
  );
}
