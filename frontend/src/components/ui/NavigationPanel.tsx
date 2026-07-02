"use client";

import { useAppStore } from "@/store/useAppStore";
import { Button } from "@/components/ui/button";
import { audioManager } from "@/lib/AudioManager";
import { 
  LayoutDashboard, 
  BrainCircuit, 
  Settings, 
  FolderOpen,
  LucideIcon
} from "lucide-react";

const navItems: { id: string, label: string, icon: LucideIcon }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "memory", label: "Memory Core", icon: BrainCircuit },
  { id: "files", label: "File System", icon: FolderOpen },
  { id: "settings", label: "Settings", icon: Settings },
];

export function NavigationPanel() {
  const { activeFeature, setActiveFeature } = useAppStore();

  const handleNav = (id: string) => {
    audioManager.play("hover");
    setActiveFeature(id);
  };

  return (
    <div className="flex-1 flex flex-col gap-2 p-4 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md overflow-y-auto">
      <h2 className="text-sm font-semibold tracking-wide text-white/80 uppercase mb-2">Navigation</h2>
      
      <div className="flex flex-col gap-2">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activeFeature === item.id;
          return (
            <Button
              key={item.id}
              variant="ghost"
              className={`justify-start h-12 transition-all ${
                isActive 
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30 shadow-[0_0_15px_rgba(0,100,255,0.2)] hover:bg-blue-500/30 hover:text-blue-300" 
                  : "text-white/60 hover:text-white hover:bg-white/10 border border-transparent"
              }`}
              onClick={() => handleNav(item.id)}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
