export default function HealthPanel({ health }) {
  const stores = health?.stores ? Object.entries(health.stores) : [];
  return (
    <section className="glass panel">
      <h2>System health</h2>
      <div className="health-grid">
        <div><span className="muted">Status</span><strong>{health?.status || '—'}</strong></div>
        <div><span className="muted">Database</span><strong>{health?.database || '—'}</strong></div>
        <div><span className="muted">Timestamp</span><strong>{health?.timestamp?.replace('T', ' ').replace('Z', '') || '—'}</strong></div>
      </div>
      {stores.length > 0 && (
        <ul className="feed-list">
          {stores.map(([id, s]) => (
            <li key={id}>
              {id}: <span className={s.status === 'OK' ? 'ok' : 'warn'}>{s.status}</span>
              {s.lag_minutes != null && ` (${s.lag_minutes}m lag)`}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
