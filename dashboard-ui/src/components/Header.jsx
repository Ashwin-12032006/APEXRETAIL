import { RefreshCw, ChevronDown, MapPin } from 'lucide-react';

export default function Header({ stores, storeId, onStoreChange, health, onRefresh, lastUpdate }) {
  const online = health?.database === 'connected';
  const timeStr = lastUpdate
    ? lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';
  const store = stores.find((s) => s.id === storeId);

  return (
    <header className="topbar glass apex-panel">
      <div className="topbar-left">
        <span className="topbar-kicker">Offline beauty retail</span>
        <h1 className="display-title sm">{store?.label || 'Store'}</h1>
        <p className="topbar-sub">
          <MapPin size={13} /> {store?.city || '—'} · 5-camera intelligence mesh
        </p>
      </div>
      <div className="topbar-actions">
        <span className="update-chip">Synced {timeStr}</span>
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
          {online ? 'Ingest live' : 'API degraded'}
        </span>
        <button type="button" className="btn-icon" onClick={onRefresh} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </div>
    </header>
  );
}
