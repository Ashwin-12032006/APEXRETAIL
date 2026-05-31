export default function Header({ stores, storeId, onStoreChange, health, onRefresh }) {
  const online = health?.database === 'connected';
  return (
    <header className="header">
      <div>
        <h1>Purplle Store Intelligence</h1>
        <p className="subtitle">CCTV → CV pipeline → conversion analytics</p>
      </div>
      <div className="header-actions">
        <select value={storeId} onChange={(e) => onStoreChange(e.target.value)}>
          {stores.map((s) => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
        <span className={`pill ${online ? 'ok' : 'bad'}`}>
          {online ? 'Live' : 'Degraded'}
        </span>
        <button type="button" onClick={onRefresh}>Refresh</button>
      </div>
    </header>
  );
}
