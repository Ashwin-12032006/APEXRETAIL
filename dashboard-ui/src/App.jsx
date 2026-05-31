import { useCallback, useEffect, useState } from 'react';
import { fetchJson, apiUrl } from './api';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ConversionHero from './components/ConversionHero';
import KpiGrid from './components/KpiGrid';
import FunnelChart from './components/FunnelChart';
import ZoneHeatmap from './components/ZoneHeatmap';
import AnomaliesList from './components/AnomaliesList';
import CctvMonitor from './components/CctvMonitor';
import HealthPanel from './components/HealthPanel';

const STORES = [
  { id: 'STORE_BLR_002', label: 'Bangalore · Koramangala', city: 'BLR' },
  { id: 'STORE_BLR_001', label: 'Bangalore · Indiranagar', city: 'BLR' },
  { id: 'STORE_MUM_001', label: 'Mumbai · Bandra West', city: 'MUM' },
  { id: 'STORE_DEL_001', label: 'Delhi · Connaught Place', city: 'DEL' },
];

export default function App() {
  const [storeId, setStoreId] = useState('STORE_BLR_002');
  const [tab, setTab] = useState('analytics');
  const [metrics, setMetrics] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

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
      setLastUpdate(new Date());
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

  const legacyUrl = apiUrl('/');

  return (
    <div className="shell">
      <div className="bg-mesh" aria-hidden />
      <Sidebar tab={tab} onTab={setTab} legacyUrl={legacyUrl} />
      <div className="main">
        <Header
          stores={STORES}
          storeId={storeId}
          onStoreChange={setStoreId}
          health={health}
          onRefresh={refresh}
          lastUpdate={lastUpdate}
        />

        {error && (
          <div className="banner error">
            <span>API offline — start backend on port 8000</span>
            <code>{error}</code>
          </div>
        )}

        {tab === 'cctv' ? (
          <CctvMonitor storeId={storeId} fullPage />
        ) : (
          <>
            <ConversionHero metrics={metrics} funnel={funnel} loading={loading} storeId={storeId} />
            <KpiGrid metrics={metrics} loading={loading} />
            <div className="grid-2">
              <FunnelChart data={funnel} loading={loading} />
              <ZoneHeatmap zones={heatmap?.zones || []} loading={loading} confidence={heatmap?.data_confidence} />
            </div>
            <div className="grid-2 bottom-row">
              <AnomaliesList items={anomalies} />
              <HealthPanel health={health} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
