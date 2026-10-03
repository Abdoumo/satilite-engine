// @ts-ignore
import { AlertTriangle, MapPin, Activity } from 'lucide-react';

interface AlertTimelineProps {
    alerts: any;
    wsEvent: any;
}

export function AlertTimeline({ alerts, wsEvent }: AlertTimelineProps) {
    return (
        <div className="w-full h-full bg-gray-900/60 backdrop-blur-md border border-gray-700/50 rounded-xl flex flex-col shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden">
            <div className="bg-gradient-to-r from-gray-800/80 to-transparent p-3 text-sm font-mono font-bold border-b border-gray-700/50 flex justify-between items-center text-gray-200 tracking-wider z-10">
                <span className="flex items-center gap-2">
                    <Activity size={16} className="text-blue-400" />
                    ALERT TIMELINE
                </span>
                {wsEvent && (
                    <span className="text-[10px] bg-red-500/10 border border-red-500/30 text-red-400 px-2 py-1 rounded shadow-[0_0_10px_rgba(239,68,68,0.2)] animate-pulse flex items-center gap-1">
                        <Activity size={12} />
                        LIVE EVENT
                    </span>
                )}
            </div>
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-black/40 relative">
                {wsEvent && (
                    <div className="bg-gradient-to-r from-red-950/40 to-transparent border-l-4 border-red-500 p-3 rounded-r-md text-sm shadow-[0_4px_15px_rgba(239,68,68,0.15)] transition-all">
                        <div className="font-bold flex items-center gap-2 text-red-100">
                            <AlertTriangle size={16} className="text-red-500 drop-shadow-[0_0_5px_rgba(239,68,68,0.8)]" />
                            {wsEvent.event}
                        </div>
                        <div className="text-red-200/70 mt-2 text-xs font-mono bg-black/30 p-2 rounded">
                            {JSON.stringify(wsEvent.payload, null, 2)}
                        </div>
                    </div>
                )}
                
                {alerts?.features?.map((alert: any, i: number) => {
                    const isCritical = alert.properties.severity === 'CRITICAL';
                    return (
                        <div key={i} className={`bg-gradient-to-r ${isCritical ? 'from-red-950/30 border-red-500' : 'from-amber-950/30 border-amber-500'} to-transparent border-l-2 p-3 rounded-r-md text-sm shadow-md transition-all hover:translate-x-1 hover:bg-black/40 group`}>
                            <div className={`font-bold flex items-center gap-2 ${isCritical ? 'text-red-100' : 'text-amber-100'}`}>
                                <MapPin size={16} className={`${isCritical ? 'text-red-500' : 'text-amber-500'} group-hover:scale-110 transition-transform`} />
                                {alert.properties.alert_type}
                            </div>
                            <div className="text-gray-400 mt-2 flex justify-between font-mono items-center">
                                <span className="bg-gray-800/50 px-2 py-0.5 rounded text-[10px]">STATUS: {alert.properties.status}</span>
                                <span className={`${isCritical ? 'text-red-400' : 'text-amber-400'} tracking-wider text-[10px]`}>{alert.properties.severity}</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
