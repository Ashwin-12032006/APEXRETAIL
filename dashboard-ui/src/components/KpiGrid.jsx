import { Clock, UsersRound, ShoppingBag, AlertTriangle } from 'lucide-react';

function fmtDwell(metrics) {
  const dwells = Object.values(metrics?.avg_dwell_by_zone || {});
  if (!dwells.length) return '—';
  const ms = dwells.reduce((a, b) => a + b, 0) / dwells.length;
  const s = ms / 1000;
  return s >= 60 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.round(s)}s`;
}

const CARDS = [
  { key: 'visitors', label: 'Footfall', icon: UsersRound, accent: 'violet' },
  { key: 'dwell', label: 'Avg dwell', icon: Clock, accent: 'cyan' },
  { key: 'queue', label: 'Billing queue', icon: ShoppingBag, accent: 'amber' },
  { key: 'abandon', label: 'Queue abandon', icon: AlertTriangle, accent: 'rose' },
];

export default function KpiGrid({ metrics, loading }) {
  const values = {
    visitors: metrics?.unique_visitors ?? '—',
    dwell: metrics ? fmtDwell(metrics) : '—',
    queue: metrics?.queue_depth ?? '—',
    abandon: metrics
      ? `${((metrics.abandonment_rate ?? metrics.queue_abandonment_rate ?? 0) * 100).toFixed(1)}%`
      : '—',
  };

  return (
    <section className="kpi-grid">
      {CARDS.map(({ key, label, icon: Icon, accent }) => (
        <article key={key} className={`kpi-card glass accent-${accent} ${loading ? 'shimmer' : ''}`}>
          <div className="kpi-icon-wrap">
            <Icon size={20} strokeWidth={2} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">{label}</span>
            <span className="kpi-value">{values[key]}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
