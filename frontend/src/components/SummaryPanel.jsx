export default function SummaryPanel({ title, rows, total }) {
  return (
    <div className="summary-card">
      <h3>{title}</h3>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Category</th>
            <th style={{ textAlign: "right" }}>Points</th>
            <th style={{ textAlign: "right" }}>Share</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.cat}>
              <td>
                <span className="dot" style={{ background: row.color }} />
                {row.label}
              </td>
              <td style={{ textAlign: "right", fontWeight: 600 }}>{row.count}</td>
              <td style={{ textAlign: "right" }}>{row.share.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td>Total</td>
            <td style={{ textAlign: "right" }}>{total}</td>
            <td style={{ textAlign: "right" }}>100%</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
