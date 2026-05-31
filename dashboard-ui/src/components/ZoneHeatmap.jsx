export default function ZoneHeatmap({ zones, loading, storeId }) {
  const sorted = [...(zones || [])].sort((a, b) => b.visit_frequency - a.visit_frequency);
  const max = Math.max(...sorted.map((z) => z.visit_frequency), 1);

  return (
    <section className="glass panel">
      <h2>Zone dwell & heatmap</h2>
      <p className="hint">{storeId} · SKINCARE / HAIRCARE / BILLING</p>
      {loading && !sorted.length ? (
        <div className="placeholder">Loading zones…</div>
      ) : !sorted.length ? (
        <div className="placeholder">No zone data — run pipeline or CCTV ingest.</div>
      ) : (
        <div className="zone-list">
          {sorted.map((z) => (
            <div key={z.zone_id} className="zone-row">
              <span className="zone-id">{z.zone_id}</span>
              <div className="zone-bar-bg">
                <div
                  className="zone-bar-fill"
                  style={{ width: `${(z.visit_frequency / max) * 100}%` }}
                />
              </div>
              <span className="zone-meta">{z.visit_frequency} vis · score {Math.round(z.avg_dwell_score || 0)}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
