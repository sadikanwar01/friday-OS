"use client";

import { ReactNode } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { Button } from '@/components/ui/button';
import { PanelLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import dynamic from 'next/dynamic';
import { QuickActionsDock } from '@/components/ui/QuickActionsDock';
import { ErrorBoundary } from '@/components/core/ErrorBoundary';

// Lazy load the heavy 3D scene
const AICoreScene = dynamic(() => import('@/components/core/AICoreScene').then(mod => mod.AICoreScene), { 
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-black" />
});
// Sidebar has been removed for Phase 3 Holographic HUD floating dock (to be added later)
// import { Sidebar } from './Sidebar';

import { ChatFeature } from '@/features/chat/ChatFeature';
import { NavigationPanel } from '@/components/ui/NavigationPanel';
import { TelemetryPanel } from '@/components/ui/TelemetryPanel';
import { CommandStatus } from '@/components/ui/CommandStatus';
import { DebugPanel } from '@/components/ui/DebugPanel';

export function AppLayout({ children }: { children: ReactNode }) {
  const { activeFeature } = useAppStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-black text-white relative font-sans">
      {/* 3D Background Environment */}
      <ErrorBoundary fallback={<div className="absolute inset-0 bg-black z-0" />}>
        <AICoreScene />
      </ErrorBoundary>

      {process.env.NODE_ENV === 'development' && <DebugPanel />}
      
      {/* OS OVERLAY GRID */}
      <div className="absolute inset-0 z-10 flex pointer-events-none">
        
        {/* LEFT PANE (Navigation, Telemetry, Quick Actions) */}
        <div className="w-[320px] h-full flex flex-col gap-4 p-4 pointer-events-auto border-r border-white/5 bg-black/40 backdrop-blur-md">
          <TelemetryPanel />
          <NavigationPanel />
          <QuickActionsDock />
        </div>

        {/* CENTER PANE (AI Core viewport & Command Status) */}
        <main className="flex-1 flex flex-col relative pointer-events-none">
          {/* Dynamic feature overlay (if they open memory/files it can show up here) */}
          <div className="flex-1 p-8 pointer-events-auto overflow-y-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeFeature}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.3 }}
              >
                <ErrorBoundary fallback={<div className="p-4 text-red-500 bg-red-950/20 border border-red-500/50 rounded-lg">Critical Feature Error. The module crashed.</div>}>
                  {children}
                </ErrorBoundary>
              </motion.div>
            </AnimatePresence>
          </div>
          
          {/* Bottom Command Status */}
          <CommandStatus />
        </main>

        {/* RIGHT PANE (Permanent Chat) */}
        <div className="w-[420px] h-full pointer-events-auto border-l border-white/5 bg-black/40 backdrop-blur-md p-4">
          <ChatFeature />
        </div>

      </div>
    </div>
  );
}
