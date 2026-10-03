import { useState, useRef } from 'react';
import Map, { Source, Layer, Marker } from 'react-map-gl/mapbox';
// @ts-ignore
import { Layers, Search, MapPin } from 'lucide-react';
import 'mapbox-gl/dist/mapbox-gl.css';

interface PipelineMapProps {
    pipelines: any;
    segments: any;
    alerts: any;
    setHoverLocation: (loc: { longitude: number, latitude: number }) => void;
}

export function PipelineMap({ pipelines, segments, alerts, setHoverLocation }: PipelineMapProps) {
    const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN;
    const [mapStyle, setMapStyle] = useState('mapbox://styles/mapbox/dark-v11');
    const [showStyleMenu, setShowStyleMenu] = useState(false);
    
    const mapRef = useRef<any>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchMarker, setSearchMarker] = useState<[number, number] | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery) return;
        
        const query = searchQuery.toLowerCase();
        
        // 0. Check custom specific POIs
        const customPlaces: Record<string, [number, number]> = {
            'cre annaba': [7.766667, 36.9],
            'centre de recherche environnement annaba': [7.766667, 36.9],
            'centre de recherche en environnement': [7.766667, 36.9]
        };
        
        for (const [key, coords] of Object.entries(customPlaces)) {
            if (query.includes(key)) {
                mapRef.current?.flyTo({ center: coords, zoom: 16, duration: 2000 });
                setSearchMarker(coords);
                return;
            }
        }
        
        // 1. Search local pipelines and segments first
        let localMatch = null;
        
        if (segments?.features) {
            localMatch = segments.features.find((f: any) => 
                f.properties?.name?.toLowerCase().includes(query)
            );
        }
        
        if (!localMatch && pipelines?.features) {
            localMatch = pipelines.features.find((f: any) => 
                f.properties?.name?.toLowerCase().includes(query) ||
                f.properties?.operator?.toLowerCase().includes(query)
            );
        }

        if (localMatch) {
            let center: [number, number] | null = null;
            if (localMatch.geometry.type === 'LineString') {
                const coords = localMatch.geometry.coordinates;
                center = coords[Math.floor(coords.length / 2)];
            } else if (localMatch.geometry.type === 'MultiLineString') {
                const coords = localMatch.geometry.coordinates[0];
                center = coords[Math.floor(coords.length / 2)];
            } else if (localMatch.geometry.type === 'Point') {
                center = localMatch.geometry.coordinates;
            }
            
            if (center) {
                mapRef.current?.flyTo({ center, zoom: 15, duration: 2000 });
                setSearchMarker(center);
                return;
            }
        }

        // 2. Fallback to Mapbox geocoding
        try {
            const res = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(searchQuery)}.json?proximity=7.76,36.90&access_token=${mapboxToken}`);
            const data = await res.json();
            if (data.features && data.features.length > 0) {
                const [lng, lat] = data.features[0].center;
                mapRef.current?.flyTo({ center: [lng, lat], zoom: 14, duration: 2000 });
                setSearchMarker([lng, lat]);
            }
        } catch (err) {
            console.error("Geocoding error", err);
        }
    };

    return (
        <div className="w-full h-full relative border border-gray-700 rounded-lg overflow-hidden bg-gray-800">
            <Map
                ref={mapRef}
                initialViewState={{
                    longitude: 7.76,
                    latitude: 36.90,
                    zoom: 12
                }}
                mapStyle={mapStyle}
                mapboxAccessToken={mapboxToken}
                onMouseMove={(e) => {
                    if (e.lngLat) {
                        setHoverLocation({ longitude: e.lngLat.lng, latitude: e.lngLat.lat });
                    }
                }}
            >
                {pipelines && pipelines.features.length > 0 && (
                    <Source id="pipelines" type="geojson" data={pipelines}>
                        <Layer 
                            id="pipelines-layer" 
                            type="line" 
                            paint={{
                                'line-color': '#00f',
                                'line-width': 4
                            }} 
                        />
                    </Source>
                )}

                {segments && segments.features.length > 0 && (
                    <Source id="segments" type="geojson" data={segments}>
                        <Layer 
                            id="segments-layer" 
                            type="line" 
                            paint={{
                                'line-color': [
                                    'match',
                                    ['get', 'risk_level'],
                                    'HIGH', '#f00',
                                    'MEDIUM', '#fa0',
                                    'LOW', '#0f0',
                                    '#0ff'
                                ],
                                'line-width': 4
                            }} 
                        />
                    </Source>
                )}

                {alerts && alerts.features.length > 0 && (
                    <Source id="alerts" type="geojson" data={alerts}>
                        <Layer 
                            id="alerts-layer" 
                            type="circle" 
                            paint={{
                                'circle-radius': 8,
                                'circle-color': '#f00',
                                'circle-stroke-width': 2,
                                'circle-stroke-color': '#fff'
                            }} 
                        />
                    </Source>
                )}
                
                {searchMarker && (
                    <Marker longitude={searchMarker[0]} latitude={searchMarker[1]} anchor="bottom">
                        <div className="animate-bounce">
                            <MapPin className="text-red-500 drop-shadow-lg" size={36} fill="#fca5a5" />
                        </div>
                    </Marker>
                )}
            </Map>
            
            {/* Search Bar */}
            <div className="absolute top-4 left-4 z-10">
                <form onSubmit={handleSearch} className="flex items-center bg-gray-900/80 backdrop-blur-md border border-gray-700/80 rounded-lg shadow-[0_4px_15px_rgba(0,0,0,0.5)] overflow-hidden focus-within:border-blue-500/70 focus-within:shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all">
                    <div className="pl-3 pr-2 text-blue-400">
                        <Search size={18} />
                    </div>
                    <input 
                        type="text" 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search coordinates or place..." 
                        className="bg-transparent border-none outline-none text-sm text-gray-200 py-2.5 w-48 lg:w-72 placeholder-gray-500 font-mono"
                    />
                    <button type="submit" className="hidden">Search</button>
                </form>
            </div>
            
            {/* Map Style Switcher */}
            <div className="absolute top-4 right-4 z-10 flex flex-col items-end">
                <button 
                    onClick={() => setShowStyleMenu(!showStyleMenu)}
                    className="bg-gray-900/80 backdrop-blur-sm border border-gray-700 p-2 rounded-md hover:bg-gray-800 transition-colors shadow-lg"
                >
                    <Layers size={20} className="text-gray-300" />
                </button>
                
                {showStyleMenu && (
                    <div className="mt-2 bg-gray-900/90 backdrop-blur-md border border-gray-700 rounded-md shadow-xl flex flex-col overflow-hidden w-40 text-sm">
                        <button 
                            className={`px-4 py-2 text-left hover:bg-blue-600/30 transition-colors ${mapStyle === 'mapbox://styles/mapbox/dark-v11' ? 'bg-blue-900/40 text-blue-400' : 'text-gray-300'}`}
                            onClick={() => { setMapStyle('mapbox://styles/mapbox/dark-v11'); setShowStyleMenu(false); }}
                        >
                            Dark Map
                        </button>
                        <button 
                            className={`px-4 py-2 text-left hover:bg-blue-600/30 transition-colors ${mapStyle === 'mapbox://styles/mapbox/satellite-v9' ? 'bg-blue-900/40 text-blue-400' : 'text-gray-300'}`}
                            onClick={() => { setMapStyle('mapbox://styles/mapbox/satellite-v9'); setShowStyleMenu(false); }}
                        >
                            Satellite
                        </button>
                        <button 
                            className={`px-4 py-2 text-left hover:bg-blue-600/30 transition-colors ${mapStyle === 'mapbox://styles/mapbox/satellite-streets-v12' ? 'bg-blue-900/40 text-blue-400' : 'text-gray-300'}`}
                            onClick={() => { setMapStyle('mapbox://styles/mapbox/satellite-streets-v12'); setShowStyleMenu(false); }}
                        >
                            Satellite Streets
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
