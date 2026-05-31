import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts';

const STAGE_COLORS = ['#8b5cf6', '#a78bfa', '#f59e0b', '#34d399'];

export default function FunnelChart({ data, loading }) {
  const stages = data?.funnel || [];
  const chartData = stages.map((s, i) => ({
    name: s.stage.replace(' ', '\n'),
    short: s.stage,
    count: s.count,
    drop: s.drop_off_pct,
    fill: STAGE_COLORS[i % STAGE_COLORS.length],
  }));

  return (
    <section className="glass panel funnel-panel">
      <div className="panel-head">
        <div>
          <h2>Conversion funnel</h2>
          <p className="hint">Where shoppers drop off — CV tracking to POS</p>
        </div>
        <span className="badge">4 stages</span>
      </div>
      {loading && !stages.length ? (
        <div className="chart-placeholder shimmer" />
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 24, right: 12, left: 0, bottom: 8 }}>
            <XAxis
              dataKey="short"
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'Outfit' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              cursor={{ fill: 'rgba(139, 92, 246, 0.08)' }}
              content={({ active, payload }) => {
                if (!active || !payload?.[0]) return null;
                const p = payload[0].payload;
                return (
                  <div className="chart-tooltip">
                    <strong>{p.short}</strong>
                    <span>{p.count} customers</span>
                    {p.drop > 0 && <span className="drop">{p.drop}% drop-off</span>}
                  </div>
                );
              }}
            />
            <Bar dataKey="count" radius={[10, 10, 4, 4]} maxBarSize={72}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} fillOpacity={0.9} />
              ))}
              <LabelList
                dataKey="count"
                position="top"
                fill="#e2e8f0"
                fontSize={12}
                fontWeight={600}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
      {stages.length > 0 && (
        <div className="funnel-drops">
          {stages.slice(1).map((s) => (
            <span key={s.stage} className="drop-chip">
              {s.stage}: −{s.drop_off_pct}%
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
