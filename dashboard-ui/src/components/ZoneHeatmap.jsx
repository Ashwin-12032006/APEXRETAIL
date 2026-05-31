const ZONE_STYLE = {
  SKINCARE: { color: '#a78bfa', label: 'Skincare', emoji: '✨' },
  HAIRCARE: { color: '#c4b5fd', label: 'Haircare', emoji: '💇' },
  BILLING: { color: '#34d399', label: 'Billing', emoji: '💳' },
  MAKEUP: { color: '#f472b6', label: 'Makeup', emoji: '💄' },
  FRAGRANCE: { color: '#fbbf24', label: 'Fragrance', emoji: '🌸' },
  COSMETICS: { color: '#fb7185', label: 'Cosmetics', emoji: '💋' },
  WELLNESS: { color: '#2dd4bf', label: 'Wellness', emoji: '🌿' },
};

export default function ZoneHeatmap({ zones, loading, confidence }) {
  const sorted = [...(zones || [])].sort((a, b) => b.visit_frequency - a.visit_frequency);
  const max = Math.max(...sorted.map((z) => z.visit_frequency), 1);

  return (
    <section className="glass panel">
      <div className="panel-head">
        <div>
          <h2>Zone dwell heatmap</h2>
          <p className="hint">Beauty category traffic — SKINCARE · HAIRCARE · BILLING</p>
        </div>
        {confidence != null && (
          <span className={`badge ${confidence ? 'badge-ok' : 'badge-warn'}`}>
            {confidence ? 'High confidence' : 'Low sample'}
          </span>
        )}
      </div>
      {loading && !sorted.length ? (
        <div className="chart-placeholder shimmer" />
      ) : !sorted.length ? (
        <div className="empty-state">
          <p>No zone events yet</p>
          <span>Run pipeline or open Live CCTV tab</span>
        </div>
      ) : (
        <div className="zone-list">
          {sorted.map((z) => {
            const style = ZONE_STYLE[z.zone_id] || { color: '#8b5cf6', label: z.zone_id, emoji: '📍' };
            const pct = (z.visit_frequency / max) * 100;
            const score = Math.round(z.avg_dwell_score || 0);
            return (
              <div key={z.zone_id} className="zone-card">
                <div className="zone-head">
                  <span className="zone-emoji">{style.emoji}</span>
                  <span className="zone-name">{style.label}</span>
                  <span className="zone-vis">{z.visit_frequency} visits</span>
                </div>
                <div className="zone-bar-bg">
                  <div
                    className="zone-bar-fill"
                    style={{
                      width: `${pct}%`,
                      background: `linear-gradient(90deg, ${style.color}, ${style.color}88)`,
                      boxShadow: `0 0 20px ${style.color}44`,
                    }}
                  />
                </div>
                <div className="zone-foot">
                  <span>Dwell score</span>
                  <strong>{score}/100</strong>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
