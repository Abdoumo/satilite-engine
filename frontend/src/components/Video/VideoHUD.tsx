import Map from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';

const HUDCorners = ({ color = 'border-cyan-500/50' }) => (
    <>
        <div className={`absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 ${color} rounded-tl z-10 m-3`}></div>
        <div className={`absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 ${color} rounded-tr z-10 m-3`}></div>
        <div className={`absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 ${color} rounded-bl z-10 m-3`}></div>
        <div className={`absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 ${color} rounded-br z-10 m-3`}></div>
    </>
);

interface VideoHUDProps {
    hoverLocation?: { longitude: number; latitude: number };
}

export function VideoHUD({ hoverLocation = { longitude: 7.76, latitude: 36.90 } }: VideoHUDProps) {
    const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN;

    return (
        <div className="w-full h-full bg-gray-900/60 backdrop-blur-md border border-gray-700/50 rounded-xl flex flex-col overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.5)] relative">
            <div className="bg-gradient-to-r from-gray-800/80 to-transparent p-2 px-4 text-xs font-mono font-semibold border-b border-gray-700/50 flex justify-between items-center z-20 text-cyan-400 tracking-wider">
                <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                    RGB HUD (YOLOv8)
                </span>
                <span className="text-red-500 flex items-center gap-1.5 font-bold">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse-soft shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
                    REC
                </span>
            </div>
            
            <div className="flex-1 relative bg-black/90 overflow-hidden group">
                <div className="absolute inset-0 opacity-85 group-hover:opacity-100 transition-all duration-700 pointer-events-none group-hover:scale-105">
                    <Map
                        longitude={hoverLocation.longitude}
                        latitude={hoverLocation.latitude}
                        zoom={17}
                        pitch={45}
                        bearing={0}
                        mapStyle="mapbox://styles/mapbox/satellite-v9"
                        mapboxAccessToken={mapboxToken}
                        interactive={false}
                    />
                </div>

                {/* Scanline effect */}
                <div className="absolute inset-0 w-full h-[15%] bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent opacity-60 z-10 pointer-events-none animate-scanline mix-blend-screen"></div>
                
                {/* HUD Overlay Grid */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:30px_30px] pointer-events-none z-10"></div>
                
                {/* Target Crosshairs */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 pointer-events-none z-10 opacity-30 group-hover:opacity-70 transition-opacity duration-500">
                    <div className="absolute top-1/2 left-0 w-full h-[1px] bg-cyan-500"></div>
                    <div className="absolute top-0 left-1/2 w-[1px] h-full bg-cyan-500"></div>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 border border-cyan-500 rounded-full"></div>
                </div>

                <HUDCorners />
            </div>
        </div>
    );
}
