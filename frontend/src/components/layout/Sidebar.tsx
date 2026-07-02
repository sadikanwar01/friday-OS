"use client";

import { useAppStore } from '@/store/useAppStore';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  LayoutDashboard, 
  MessageSquare, 
  BrainCircuit, 
  Settings, 
  Cpu,
  Globe,
  Mic,
  FolderOpen
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'memory', label: 'Memory', icon: BrainCircuit },
  { id: 'automation', label: 'Automation', icon: Cpu },
  { id: 'browser', label: 'Browser', icon: Globe },
  { id: 'voice', label: 'Voice', icon: Mic },
  { id: 'files', label: 'Files', icon: FolderOpen },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const { sidebarOpen, activeFeature, setActiveFeature } = useAppStore();

  return (
    <motion.aside
      initial={false}
      animate={{ 
        width: sidebarOpen ? 240 : 64,
        opacity: 1
      }}
      className="h-screen bg-card/40 backdrop-blur-xl border-r border-border/40 flex flex-col z-20 shrink-0 overflow-hidden relative"
    >
      <div className="h-14 flex items-center px-4 border-b border-border/40 shrink-0">
        <div className="w-6 h-6 rounded-md bg-primary flex items-center justify-center shrink-0">
          <span className="text-primary-foreground font-bold text-xs">F</span>
        </div>
        <motion.span 
          initial={false}
          animate={{ opacity: sidebarOpen ? 1 : 0, display: sidebarOpen ? 'block' : 'none' }}
          className="ml-3 font-semibold text-sm whitespace-nowrap"
        >
          FRIDAY OS
        </motion.span>
      </div>

      <ScrollArea className="flex-1 py-4">
        <nav className="px-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeFeature === item.id;
            
            return (
              <Button
                key={item.id}
                variant={isActive ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start overflow-hidden",
                  isActive ? "bg-secondary/50 font-medium" : "text-muted-foreground hover:text-foreground",
                  !sidebarOpen && "justify-center px-0"
                )}
                onClick={() => setActiveFeature(item.id)}
              >
                <Icon className={cn("shrink-0", sidebarOpen ? "mr-3" : "mr-0", "h-4 w-4")} />
                <motion.span
                  initial={false}
                  animate={{ 
                    opacity: sidebarOpen ? 1 : 0, 
                    width: sidebarOpen ? 'auto' : 0,
                    display: sidebarOpen ? 'inline-block' : 'none'
                  }}
                  className="whitespace-nowrap overflow-hidden text-sm"
                >
                  {item.label}
                </motion.span>
              </Button>
            );
          })}
        </nav>
      </ScrollArea>
    </motion.aside>
  );
}
