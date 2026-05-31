function fmtDwell(ms) {
  if (!ms) return '—';
  const s = ms / 1000;
  return s >= 60 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.round(s)}s`;
}

export default function KpiGrid({ metrics, loading }) {
  const cards = [
    { label: 'Unique visitors', value: metrics?.unique_visitors ?? '—' },
    { label: 'Conversion rate', value: metrics ? `${(metrics.conversion_rate * 100).toFixed(1)}%` : '—' },
    { label: 'Avg dwell', value: metrics ? fmtDwell(
      Object.values(metrics.avg_dwell_by_zone || {}).reduce((a, b, _, arr) => a + b / arr.length, 0)
    ) : '—' },
    { label: 'Queue depth', value: metrics?.queue_depth ?? '—' },
    { label: 'Queue abandonment', value: metrics ? `${((metrics.abandonment_rate ?? metrics.queue_abandonment_rate ?? 0) * 100).toFixed(1)}%` : '—' },
  ];

  return (
    <section className="kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className={`glass ${loading ? 'skeleton' : ''}`}>
          <div className="kpi-label">{c.label}</div>
          <div className="kpi-value">{c.value}</div>
        </div>
      ))}
    </section>
  );
}
