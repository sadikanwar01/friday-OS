"use client";

import { useSystemStore } from "@/store/useSystemStore";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SystemStatusResponse } from "@/types/api";
import { useEffect } from "react";
import { Activity, Cpu, Database, Network } from "lucide-react";
import { HolographicPanel } from "@/components/ui/HolographicPanel";
import { motion, Variants } from "framer-motion";

export function DashboardFeature() {
  const { status, updateStatus } = useSystemStore();

  const { data, isError } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.get<SystemStatusResponse>('/api/system'),
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (data) {
      updateStatus(data);
    }
  }, [data, updateStatus]);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="w-full h-full flex flex-col justify-center items-center pointer-events-none p-8">
      {/* HUD Title */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mb-12 text-center pointer-events-auto"
      >
        <h1 className="text-4xl font-light tracking-[0.2em] text-blue-100 uppercase drop-shadow-[0_0_10px_rgba(0,150,255,0.8)]">
          System Telemetry
        </h1>
        <div className="h-[1px] w-48 bg-gradient-to-r from-transparent via-blue-400 to-transparent mx-auto mt-4 opacity-50" />
      </motion.div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-7xl pointer-events-auto"
      >
        <motion.div variants={itemVariants}>
          <HolographicPanel intensity="high" className="h-40 flex flex-col justify-between group">
            <div className="flex items-center justify-between text-blue-200">
              <span className="text-sm font-medium tracking-widest uppercase">OS State</span>
              <Activity className="w-5 h-5 text-blue-400 drop-shadow-[0_0_5px_rgba(0,150,255,0.8)]" />
            </div>
            <div>
              <div className="text-3xl font-light text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">Online</div>
              <p className="text-xs text-blue-300/60 mt-1 uppercase tracking-wider">Sync Active</p>
            </div>
            {/* Glowing line connector simulation */}
            <div className="absolute -bottom-px left-1/4 right-1/4 h-[2px] bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </HolographicPanel>
        </motion.div>

        <motion.div variants={itemVariants}>
          <HolographicPanel intensity="medium" className="h-40 flex flex-col justify-between group">
            <div className="flex items-center justify-between text-blue-200">
              <span className="text-sm font-medium tracking-widest uppercase">CPU Core</span>
              <Cpu className="w-5 h-5 text-blue-400 drop-shadow-[0_0_5px_rgba(0,150,255,0.8)]" />
            </div>
            <div>
              <div className="text-3xl font-light text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
                {status?.cpu_percent != null ? Number(status.cpu_percent).toFixed(1) : "--"}%
              </div>
              <div className="h-1.5 w-full bg-blue-950/50 rounded-full mt-3 overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${status?.cpu_percent || 0}%` }}
                  transition={{ type: "spring" }}
                  className="h-full bg-blue-400 shadow-[0_0_10px_rgba(0,150,255,0.8)]" 
                />
              </div>
            </div>
          </HolographicPanel>
        </motion.div>

        <motion.div variants={itemVariants}>
          <HolographicPanel intensity="medium" className="h-40 flex flex-col justify-between group">
            <div className="flex items-center justify-between text-blue-200">
              <span className="text-sm font-medium tracking-widest uppercase">Memory Allocation</span>
              <Database className="w-5 h-5 text-blue-400 drop-shadow-[0_0_5px_rgba(0,150,255,0.8)]" />
            </div>
            <div>
              <div className="text-3xl font-light text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
                {status?.ram_percent != null ? Number(status.ram_percent).toFixed(1) : "--"}%
              </div>
              <div className="h-1.5 w-full bg-blue-950/50 rounded-full mt-3 overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${status?.ram_percent || 0}%` }}
                  transition={{ type: "spring" }}
                  className="h-full bg-blue-400 shadow-[0_0_10px_rgba(0,150,255,0.8)]" 
                />
              </div>
            </div>
          </HolographicPanel>
        </motion.div>

        <motion.div variants={itemVariants}>
          <HolographicPanel intensity="low" className="h-40 flex flex-col justify-between group">
            <div className="flex items-center justify-between text-blue-200">
              <span className="text-sm font-medium tracking-widest uppercase">Subsystems</span>
              <Network className="w-5 h-5 text-blue-400 drop-shadow-[0_0_5px_rgba(0,150,255,0.8)]" />
            </div>
            <div>
              <div className="text-3xl font-light text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
                {[status?.gemini_status, status?.memory_status, status?.automation_status, status?.voice_status].filter(s => s === 'online').length}
                <span className="text-blue-400/50 text-xl font-normal ml-1">/ 4</span>
              </div>
              <p className="text-xs text-blue-300/60 mt-1 uppercase tracking-wider">Engines Online</p>
            </div>
          </HolographicPanel>
        </motion.div>
      </motion.div>

      {/* Engine Detailed Telemetry */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 lg:grid-cols-4 gap-4 w-full max-w-7xl mt-8 pointer-events-auto"
      >
        {[
          { name: 'Gemini Engine', status: status?.gemini_status },
          { name: 'Memory DB', status: status?.memory_status },
          { name: 'Automation', status: status?.automation_status },
          { name: 'Voice Pipeline', status: status?.voice_status },
        ].map((engine) => (
          <motion.div key={engine.name} variants={itemVariants}>
            <HolographicPanel intensity="low" className="py-3 px-4 flex items-center justify-between">
              <span className="text-sm text-blue-200/80 tracking-wider uppercase">{engine.name}</span>
              <div className="flex items-center gap-2">
                <span className={`text-xs uppercase tracking-widest ${engine.status === 'online' ? 'text-blue-300' : 'text-red-400'}`}>
                  {engine.status || "offline"}
                </span>
                <div className={`w-1.5 h-1.5 rounded-full ${engine.status === 'online' ? 'bg-blue-400 shadow-[0_0_8px_#60a5fa] animate-pulse' : 'bg-red-500'}`} />
              </div>
            </HolographicPanel>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
