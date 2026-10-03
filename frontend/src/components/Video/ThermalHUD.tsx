import { useState, useEffect } from 'react';
import Map from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';

const HUDCorners = ({ color = 'border-amber-500/50' }) => (
    <>
        <div className={`absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 ${color} rounded-tl z-10 m-3`}></div>
        <div className={`absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 ${color} rounded-tr z-10 m-3`}></div>
        <div className={`absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 ${color} rounded-bl z-10 m-3`}></div>
        <div className={`absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 ${color} rounded-br z-10 m-3`}></div>
    </>
);

interface ThermalHUDProps {
    hoverLocation?: { longitude: number; latitude: number };
}

export function ThermalHUD({ hoverLocation = { longitude: 7.76, latitude: 36.90 } }: ThermalHUDProps) {
    const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN;
    const [realTemp, setRealTemp] = useState<string>('--.-');

    useEffect(() => {
        let isMounted = true;
        
        const fetchTemp = async () => {
            try {
                // Fetch real current temperature using Open-Meteo API (Free, no auth required)
                const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${hoverLocation.latitude}&longitude=${hoverLocation.longitude}&current=temperature_2m`);
                const data = await res.json();
                if (isMounted && data.current && data.current.temperature_2m !== undefined) {
                    setRealTemp(data.current.temperature_2m.toFixed(1));
                }
            } catch (e) {
                console.error("Failed to fetch real temperature", e);
            }
        };

        // Debounce API calls by 1 second to avoid rate-limiting while the mouse is moving
        const timeoutId = setTimeout(() => {
            fetchTemp();
        }, 1000);

        return () => {
            isMounted = false;
            clearTimeout(timeoutId);
        };
    }, [hoverLocation.latitude, hoverLocation.longitude]);

    return (
        <div className="w-full h-full bg-gray-900/60 backdrop-blur-md border border-gray-700/50 rounded-xl flex flex-col overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.5)] relative">
            <div className="bg-gradient-to-r from-gray-800/80 to-transparent p-2 px-4 text-xs font-mono font-semibold border-b border-gray-700/50 flex justify-between items-center z-20 text-amber-400 tracking-wider">
                <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                    Thermal HUD
                </span>
                <span className="text-amber-500/70 text-[10px]">FLIR MODE</span>
            </div>
            
            <div className="flex-1 relative bg-black/90 overflow-hidden group">
                <div className="absolute inset-0 opacity-85 group-hover:opacity-100 transition-all duration-700 pointer-events-none group-hover:scale-105 grayscale invert contrast-150 brightness-125 sepia-[.3] hue-rotate-15">
                    <Map
                        longitude={hoverLocation.longitude}
                        latitude={hoverLocation.latitude}
                        zoom={17}
                        pitch={60}
                        bearing={45}
                        mapStyle="mapbox://styles/mapbox/satellite-v9"
                        mapboxAccessToken={mapboxToken}
                        interactive={false}
                    />
                </div>

                {/* Scanline effect (slower for thermal) */}
                <div className="absolute inset-0 w-full h-[15%] bg-gradient-to-b from-transparent via-amber-500/10 to-transparent opacity-60 z-10 pointer-events-none animate-scanline mix-blend-screen" style={{ animationDuration: '5s' }}></div>
                
                {/* HUD Overlay Grid */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:30px_30px] pointer-events-none z-10"></div>
                
                {/* Temperature scale indicator */}
                <div className="absolute right-2 top-1/2 -translate-y-1/2 w-2 h-32 bg-gradient-to-b from-white via-red-500 to-blue-500 rounded-full border border-gray-800 z-10 opacity-70"></div>
                
                {/* Target Crosshairs */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 pointer-events-none z-10 opacity-30 group-hover:opacity-70 transition-opacity duration-500">
                    <div className="absolute top-1/2 left-0 w-full h-[1px] bg-amber-500"></div>
                    <div className="absolute top-0 left-1/2 w-[1px] h-full bg-amber-500"></div>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 border border-amber-500 rounded-sm"></div>
                </div>

                {/* Digital Temp Readout */}
                <div className="absolute bottom-4 left-4 z-20 flex flex-col items-start bg-black/50 p-2 rounded backdrop-blur-sm border border-amber-500/20">
                    <div className="text-2xl font-mono font-bold text-amber-500 drop-shadow-[0_0_8px_rgba(245,158,11,0.8)]">
                        {realTemp}°C
                    </div>
                    <div className="text-[10px] text-amber-500/80 font-mono tracking-widest mt-1">
                        ACTUAL SURFACE
                    </div>
                </div>

                <HUDCorners />
            </div>
        </div>
    );
}
