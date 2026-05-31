import { useCallback, useEffect, useState } from 'react';
import { fetchJson } from './api';
import Header from './components/Header';
import KpiGrid from './components/KpiGrid';
import FunnelChart from './components/FunnelChart';
import ZoneHeatmap from './components/ZoneHeatmap';
import AnomaliesList from './components/AnomaliesList';
import CctvMonitor from './components/CctvMonitor';
import HealthPanel from './components/HealthPanel';

const STORES = [
  { id: 'STORE_BLR_002', label: 'Bangalore Koramangala' },
  { id: 'STORE_BLR_001', label: 'Bangalore Indiranagar' },
  { id: 'STORE_MUM_001', label: 'Mumbai Bandra' },
];

export default function App() {
  const [storeId, setStoreId] = useState('STORE_BLR_002');
  const [metrics, setMetrics] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [m, f, h, a, hl] = await Promise.all([
        fetchJson(`/stores/${storeId}/metrics`),
        fetchJson(`/stores/${storeId}/funnel`),
        fetchJson(`/stores/${storeId}/heatmap`),
        fetchJson(`/stores/${storeId}/anomalies`),
        fetchJson('/health'),
      ]);
      setMetrics(m);
      setFunnel(f);
      setHeatmap(h);
      setAnomalies(Array.isArray(a) ? a : a?.anomalies || []);
      setHealth(hl);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    setLoading(true);
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <div className="app">
      <Header
        stores={STORES}
        storeId={storeId}
        onStoreChange={setStoreId}
        health={health}
        onRefresh={refresh}
      />
      {error && (
        <div className="banner error">
          API unreachable: {error}. Start API on port 8000.
        </div>
      )}
      <KpiGrid metrics={metrics} loading={loading} />
      <div className="grid-2">
        <FunnelChart data={funnel} loading={loading} />
        <ZoneHeatmap zones={heatmap?.zones || []} loading={loading} storeId={storeId} />
      </div>
      <CctvMonitor storeId={storeId} />
      <div className="grid-2">
        <AnomaliesList items={anomalies} />
        <HealthPanel health={health} />
      </div>
    </div>
  );
}
