import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const COLORS = ['#6c5ce7', '#a8a5e6', '#f59e0b', '#10b981'];

export default function FunnelChart({ data, loading }) {
  const stages = data?.funnel || [];
  const chartData = stages.map((s) => ({
    name: s.stage,
    count: s.count,
    drop: s.drop_off_pct,
  }));

  return (
    <section className="glass panel">
      <h2>Conversion funnel</h2>
      <p className="hint">Entry → Zone → Billing → Purchase (staff excluded)</p>
      {loading && !stages.length ? (
        <div className="placeholder">Loading funnel…</div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="name" tick={{ fill: '#8a99ad', fontSize: 12 }} />
            <YAxis tick={{ fill: '#8a99ad' }} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: '#101423', border: '1px solid #333' }}
              formatter={(v, _n, p) => [`${v} (${p.payload.drop}% drop-off)`, 'Count']}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
