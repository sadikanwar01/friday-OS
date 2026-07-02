"use client";

import { useState, useEffect } from "react";
import { Activity, ServerCrash } from "lucide-react";
import { API_BASE_URL, api } from "@/lib/api";

interface SystemStatus {
  cpu_percent: number;
  ram_percent: number;
  gemini_status: string;
  memory_status: string;
  automation_status: string;
  voice_status: string;
}

export function TelemetryPanel() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    let mounted = true;
    
    const fetchTelemetry = async () => {
      try {
        const data = await api.get<SystemStatus>("/api/system");
        if (mounted) {
          setStatus(data);
          setIsOffline(false);
        }
      } catch (e) {
        if (mounted) {
          setIsOffline(true);
        }
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const getStatusColor = (val: string) => {
    if (isOffline) return "text-red-500";
    if (val === "online") return "text-emerald-400";
    if (val === "missing_key") return "text-amber-400";
    return "text-white/60";
  };

  const getPercentColor = (val: number) => {
    if (isOffline) return "text-red-500";
    if (val > 80) return "text-red-400";
    if (val > 60) return "text-amber-400";
    return "text-white";
  };

  return (
    <div className={`flex flex-col gap-3 p-4 border rounded-2xl backdrop-blur-md transition-colors duration-500 ${isOffline ? 'bg-red-950/20 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.1)]' : 'bg-white/5 border-white/10'}`}>
      <div className="flex items-center gap-2 mb-1">
        {isOffline ? (
          <ServerCrash className="w-4 h-4 text-red-500 animate-pulse" />
        ) : (
          <Activity className="w-4 h-4 text-blue-400" />
        )}
        <h2 className={`text-sm font-semibold tracking-wide uppercase ${isOffline ? 'text-red-400' : 'text-white/80'}`}>
          System Telemetry
        </h2>
      </div>
      
      <div className="space-y-3 font-mono text-xs uppercase tracking-wider">
        <div className="flex justify-between items-center">
          <span className="text-white/50">CPU Usage</span>
          <span className={`font-bold ${status ? getPercentColor(status.cpu_percent) : 'text-red-500'}`}>
            {status ? `${status.cpu_percent.toFixed(1)}%` : 'OFFLINE'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-white/50">RAM Usage</span>
          <span className={`font-bold ${status ? getPercentColor(status.ram_percent) : 'text-red-500'}`}>
            {status ? `${status.ram_percent.toFixed(1)}%` : 'OFFLINE'}
          </span>
        </div>
        
        <div className="h-px bg-white/5 my-2" />
        
        <div className="flex justify-between items-center">
          <span className="text-white/50">FRIDAY Engine</span>
          <span className={isOffline ? "text-red-500" : "text-emerald-400"}>
            {isOffline ? 'OFFLINE' : 'ONLINE'}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-white/50">Gemini Core</span>
          <span className={status ? getStatusColor(status.gemini_status) : 'text-red-500'}>
            {status ? status.gemini_status.replace('_', ' ') : 'OFFLINE'}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-white/50">Memory Core</span>
          <span className={status ? getStatusColor(status.memory_status) : 'text-red-500'}>
            {status ? status.memory_status : 'OFFLINE'}
          </span>
        </div>
      </div>
    </div>
  );
}
