import { ShieldAlert, ShieldCheck, AlertCircle } from 'lucide-react';

export default function AnomaliesList({ items }) {
  const list = items || [];

  return (
    <section className="glass panel">
      <div className="panel-head">
        <div>
          <h2>Operational alerts</h2>
          <p className="hint">Queue spikes · dead zones · conversion drops</p>
        </div>
        {list.length === 0 ? (
          <ShieldCheck size={22} className="icon-ok" />
        ) : (
          <ShieldAlert size={22} className="icon-warn" />
        )}
      </div>
      {!list.length ? (
        <div className="empty-state success">
          <ShieldCheck size={40} strokeWidth={1.5} />
          <p>All clear</p>
          <span>No queue or conversion anomalies in this window</span>
        </div>
      ) : (
        <ul className="anomaly-list">
          {list.map((a, i) => {
            const sev = (a.severity || 'info').toLowerCase();
            return (
              <li key={i} className={`anomaly-card severity-${sev}`}>
                <AlertCircle size={18} />
                <div>
                  <strong>{a.type || a.anomaly_type}</strong>
                  <p>{a.message || a.description}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
