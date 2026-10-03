import { useEffect, useState } from 'react';
import { PipelineMap } from './components/Map/PipelineMap';
import { VideoHUD } from './components/Video/VideoHUD';
import { ThermalHUD } from './components/Video/ThermalHUD';
import { AlertTimeline } from './components/Alerts/AlertTimeline';
import { fetchPipelines, fetchPipelineSegments, fetchAlerts } from './services/api';
import { useMonitoringSocket } from './services/ws';

function App() {
  const [pipelines, setPipelines] = useState<any>(null);
  const [segments, setSegments] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [hoverLocation, setHoverLocation] = useState({ longitude: 7.76, latitude: 36.90 });
  
  const { lastEvent } = useMonitoringSocket();

  useEffect(() => {
    // Basic init load
    const loadData = async () => {
      try {
        const p = await fetchPipelines();
        setPipelines(p);
        
        // If we have a pipeline, fetch its segments
        if (p?.features?.length > 0) {
          const firstPipelineId = p.features[0].properties.id;
          const s = await fetchPipelineSegments(firstPipelineId);
          setSegments(s);
        }

        const a = await fetchAlerts();
        setAlerts(a);
      } catch (e) {
        console.error("Failed to fetch initial data", e);
      }
    };
    
    loadData();
  }, []);

  return (
    <div className="w-screen h-screen bg-black text-gray-200 overflow-hidden flex flex-col font-sans">
      <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center px-6 shrink-0 shadow-md z-10">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          Intelligence Platform
        </h1>
        <div className="ml-auto text-xs text-gray-500 font-mono tracking-widest">
          SYS: OPERATIONAL
        </div>
      </header>
      
      <main className="flex-1 p-4 grid grid-cols-12 grid-rows-6 gap-4 min-h-0">
        
        {/* Map View (Left/Center) */}
        <div className="col-span-12 lg:col-span-8 row-span-4 lg:row-span-6 rounded-lg overflow-hidden shadow-2xl relative">
            <PipelineMap pipelines={pipelines} segments={segments} alerts={alerts} setHoverLocation={setHoverLocation} />
        </div>

        {/* HUD Views (Right) */}
        <div className="col-span-12 lg:col-span-4 row-span-2 lg:row-span-2">
            <VideoHUD hoverLocation={hoverLocation} />
        </div>
        
        <div className="col-span-12 lg:col-span-4 row-span-2 lg:row-span-2">
            <ThermalHUD hoverLocation={hoverLocation} />
        </div>

        {/* Alert Timeline (Right Bottom) */}
        <div className="col-span-12 lg:col-span-4 row-span-2 lg:row-span-2">
            <AlertTimeline alerts={alerts} wsEvent={lastEvent} />
        </div>
        
      </main>
    </div>
  );
}

export default App;
