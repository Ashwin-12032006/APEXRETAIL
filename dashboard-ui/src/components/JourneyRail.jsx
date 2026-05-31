const STAGES = ['Entry', 'Zone Visit', 'Billing Queue', 'Purchase'];

export default function JourneyRail({ funnel, loading }) {
  const stages = funnel?.funnel || [];
  const max = Math.max(...stages.map((s) => s.count), 1);

  return (
    <div className={`journey-rail ${loading ? 'loading-pulse' : ''}`} aria-label="Shopper journey">
      {STAGES.map((name, i) => {
        const row = stages.find((s) => s.stage === name) || { count: 0, drop_off_pct: 0 };
        const pct = Math.round((row.count / max) * 100);
        return (
          <div key={name} className="journey-step">
            <div className="journey-node">
              <span className="journey-num">{row.count}</span>
            </div>
            <div className="journey-meta">
              <span className="journey-label">{name}</span>
              <div className="journey-bar-bg">
                <div className="journey-bar-fill" style={{ width: `${pct}%` }} />
              </div>
              {i > 0 && row.drop_off_pct > 0 && (
                <span className="journey-drop">−{row.drop_off_pct}%</span>
              )}
            </div>
            {i < STAGES.length - 1 && <div className="journey-connector" aria-hidden />}
          </div>
        );
      })}
    </div>
  );
}
