"use client";

import { useState, useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useAppStore } from "@/store/useAppStore";
import { DashboardFeature } from "@/features/dashboard/DashboardFeature";
import { ChatFeature } from "@/features/chat/ChatFeature";
import { MemoryFeature } from "@/features/memory/MemoryFeature";
import { AutomationFeature } from "@/features/automation/AutomationFeature";
import { BrowserFeature } from "@/features/browser/BrowserFeature";
import { VoiceFeature } from "@/features/voice/VoiceFeature";
import { FilesFeature } from "@/features/files/FilesFeature";
import { SettingsFeature } from "@/features/settings/SettingsFeature";
import { BootSequence } from "@/components/ui/BootSequence";

export default function Home() {
  const { activeFeature } = useAppStore();
  const [bootComplete, setBootComplete] = useState(false);

  useEffect(() => {
    // Failsafe: force boot completion after 15 seconds maximum if stuck
    const timer = setTimeout(() => {
      if (!bootComplete) setBootComplete(true);
    }, 15000);
    return () => clearTimeout(timer);
  }, [bootComplete]);

  const renderFeature = () => {
    switch (activeFeature) {
      case 'dashboard':
        return <DashboardFeature />;
      case 'memory':
        return <MemoryFeature />;
      case 'automation':
        return <AutomationFeature />;
      case 'browser':
        return <BrowserFeature />;
      case 'voice':
        return <VoiceFeature />;
      case 'files':
        return <FilesFeature />;
      case 'settings':
        return <SettingsFeature />;
      case 'chat':
        return null; // Chat is rendered permanently in AppLayout
      default:
        return <DashboardFeature />;
    }
  };

  return (
    <>
      {!bootComplete && <BootSequence onComplete={() => setBootComplete(true)} />}
      
      {/* Hide the OS until boot is essentially transitioning out */}
      <div 
        className="w-full h-full transition-opacity duration-1000 ease-in-out"
        style={{ opacity: bootComplete ? 1 : 0 }}
      >
        <AppLayout>
          {renderFeature()}
        </AppLayout>
      </div>
    </>
  );
}
