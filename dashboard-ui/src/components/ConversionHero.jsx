import { Target, Users, TrendingUp } from 'lucide-react';

export default function ConversionHero({ metrics, funnel, loading, storeId }) {
  const conversion = metrics ? (metrics.conversion_rate * 100).toFixed(1) : '—';
  const visitors = metrics?.unique_visitors ?? '—';
  const purchases = funnel?.funnel?.find((s) => s.stage === 'Purchase')?.count ?? '—';
  const entries = funnel?.funnel?.find((s) => s.stage === 'Entry')?.count ?? '—';

  return (
    <section className={`hero glass ${loading ? 'loading-pulse' : ''}`}>
      <div className="hero-copy">
        <span className="eyebrow">North star · {storeId}</span>
        <h2>Offline store conversion</h2>
        <p>Customers who purchased ÷ total visitors (staff excluded from funnel)</p>
      </div>
      <div className="hero-metrics">
        <div className="hero-stat primary-stat">
          <Target className="stat-icon" size={28} />
          <div>
            <span className="stat-value">{conversion}%</span>
            <span className="stat-label">Conversion rate</span>
          </div>
        </div>
        <div className="hero-stat">
          <Users className="stat-icon muted-icon" size={22} />
          <div>
            <span className="stat-value sm">{visitors}</span>
            <span className="stat-label">Unique visitors</span>
          </div>
        </div>
        <div className="hero-stat">
          <TrendingUp className="stat-icon muted-icon" size={22} />
          <div>
            <span className="stat-value sm">{purchases}</span>
            <span className="stat-label">Purchases / {entries} entries</span>
          </div>
        </div>
      </div>
    </section>
  );
}
