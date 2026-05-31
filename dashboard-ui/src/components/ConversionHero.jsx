import { Users, Receipt } from 'lucide-react';
import JourneyRail from './JourneyRail';

export default function ConversionHero({ metrics, funnel, loading, storeId }) {
  const conversionNum = metrics ? metrics.conversion_rate * 100 : null;
  const conversion = conversionNum != null ? conversionNum.toFixed(1) : '—';
  const ringPct = conversionNum != null ? Math.min(conversionNum, 100) : 0;
  const visitors = metrics?.unique_visitors ?? '—';
  const purchases = funnel?.funnel?.find((s) => s.stage === 'Purchase')?.count ?? '—';
  const entries = funnel?.funnel?.find((s) => s.stage === 'Entry')?.count ?? '—';

  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (ringPct / 100) * circumference;

  return (
    <section className={`hero apex-hero glass ${loading ? 'loading-pulse' : ''}`}>
      <div className="hero-grid">
        <div className="hero-copy">
          <span className="eyebrow">Apex Lens · {storeId.replace('STORE_', '').replace('_', ' ')}</span>
          <h2 className="display-title">Conversion command</h2>
          <p className="hero-tagline">
            One number that ties CCTV footfall to checkout — staff excluded, zones included.
          </p>
          <div className="hero-mini-stats">
            <span><Users size={14} /> {visitors} visitors</span>
            <span><Receipt size={14} /> {purchases} / {entries} to purchase</span>
          </div>
        </div>

        <div className="conversion-ring-wrap">
          <svg className="conversion-ring" viewBox="0 0 120 120" role="img" aria-label={`Conversion ${conversion}%`}>
            <circle className="ring-track" cx="60" cy="60" r="54" />
            <circle
              className="ring-fill"
              cx="60"
              cy="60"
              r="54"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="ring-center">
            <span className="ring-value">{conversion}</span>
            <span className="ring-unit">%</span>
            <span className="ring-label">conversion</span>
          </div>
        </div>
      </div>

      <JourneyRail funnel={funnel} loading={loading} />
    </section>
  );
}
