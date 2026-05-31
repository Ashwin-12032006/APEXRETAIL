import { RefreshCw, ChevronDown } from 'lucide-react';

export default function Header({ stores, storeId, onStoreChange, health, onRefresh, lastUpdate }) {
  const online = health?.database === 'connected';
  const timeStr = lastUpdate
    ? lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';

  return (
    <header className="topbar glass">
      <div className="topbar-left">
        <h1>Store command center</h1>
        <p>Real-time CCTV intelligence for beauty retail</p>
      </div>
      <div className="topbar-actions">
        <span className="update-chip">Updated {timeStr}</span>
        <div className="select-wrap">
          <select value={storeId} onChange={(e) => onStoreChange(e.target.value)} aria-label="Store">
            {stores.map((s) => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
          <ChevronDown size={16} className="select-chevron" />
        </div>
        <span className={`live-pill ${online ? 'on' : 'off'}`}>
          <span className="live-dot" />
          {online ? 'Live ingest' : 'Degraded'}
        </span>
        <button type="button" className="btn-icon" onClick={onRefresh} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </div>
    </header>
  );
}
