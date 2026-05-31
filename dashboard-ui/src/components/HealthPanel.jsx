import { Database, Radio, Clock } from 'lucide-react';

export default function HealthPanel({ health }) {
  const stores = health?.stores ? Object.entries(health.stores) : [];

  return (
    <section className="glass panel">
      <div className="panel-head">
        <div>
          <h2>System health</h2>
          <p className="hint">Feeds · database · camera lag</p>
        </div>
      </div>
      <div className="health-cards">
        <div className="health-mini">
          <Database size={18} />
          <span>Database</span>
          <strong>{health?.database || '—'}</strong>
        </div>
        <div className="health-mini">
          <Radio size={18} />
          <span>Node</span>
          <strong>{health?.status || '—'}</strong>
        </div>
        <div className="health-mini">
          <Clock size={18} />
          <span>Sync</span>
          <strong className="mono">
            {health?.timestamp?.replace('T', ' ').replace('Z', '') || '—'}
          </strong>
        </div>
      </div>
      {stores.length > 0 && (
        <ul className="feed-list">
          {stores.map(([id, s]) => (
            <li key={id}>
              <span className="feed-id">{id.replace('STORE_', '')}</span>
              <span className={s.status === 'OK' ? 'feed-ok' : 'feed-warn'}>{s.status}</span>
              {s.lag_minutes != null && <span className="feed-lag">{s.lag_minutes}m lag</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
