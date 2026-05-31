export default function AnomaliesList({ items }) {
  return (
    <section className="glass panel">
      <h2>Real-time anomalies</h2>
      {!items?.length ? (
        <p className="muted">No active anomalies — queue & conversion within normal range.</p>
      ) : (
        <ul className="anomaly-list">
          {items.map((a, i) => (
            <li key={i} className={`severity-${(a.severity || 'info').toLowerCase()}`}>
              <strong>{a.type || a.anomaly_type}</strong>
              <span>{a.message || a.description}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
