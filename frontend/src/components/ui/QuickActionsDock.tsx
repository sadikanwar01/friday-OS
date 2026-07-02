"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Camera, 
  Globe, 
  Calculator, 
  FileText, 
  Terminal, 
  Play, 
  Search,
  Loader2,
  AlertCircle
} from "lucide-react";
import { audioManager } from "@/lib/AudioManager";
import { API_BASE_URL } from "@/lib/api";

const actions = [
  { id: "screenshot", label: "Screenshot", icon: Camera, color: "text-blue-400" },
  { id: "browser", label: "Browser", icon: Globe, color: "text-cyan-400" },
  { id: "calculator", label: "Calculator", icon: Calculator, color: "text-emerald-400" },
  { id: "notepad", label: "Notepad", icon: FileText, color: "text-amber-400" },
  { id: "terminal", label: "Terminal", icon: Terminal, color: "text-neutral-400" },
  { id: "google", label: "Google", icon: Search, color: "text-red-400" },
  { id: "youtube", label: "YouTube", icon: Play, color: "text-rose-500" },
];

export function QuickActionsDock() {
  const [overlay, setOverlay] = useState<{ visible: boolean; label: string; status: 'executing' | 'error' | 'success'; message?: string } | null>(null);

  const handleHover = () => {
    audioManager.play("hover");
  };

  const handleClick = async (action: { id: string; label: string }) => {
    audioManager.play("notification");
    setOverlay({ visible: true, label: action.label, status: 'executing', message: `Executing ${action.label}...` });
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/quick-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action.id })
      });
      if (!res.ok) {
        if (res.status === 404) {
          throw new Error("Feature not yet available in backend");
        }
        throw new Error("Failed to execute action");
      }
      setOverlay({ visible: true, label: action.label, status: 'success', message: `${action.label} executed successfully.` });
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "Unknown error";
      setOverlay({ visible: true, label: action.label, status: 'error', message: errorMsg });
    } finally {
      setTimeout(() => setOverlay(null), 3000);
    }
  };

  return (
    <div className="p-4 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md relative overflow-hidden">
      
      <AnimatePresence>
        {overlay?.visible && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/90 backdrop-blur-md rounded-2xl p-4 text-center"
          >
            {overlay.status === 'executing' && <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-2 shadow-[0_0_15px_currentColor]" />}
            {overlay.status === 'error' && <AlertCircle className="w-8 h-8 text-red-400 mb-2 drop-shadow-[0_0_10px_currentColor]" />}
            {overlay.status === 'success' && <Globe className="w-8 h-8 text-emerald-400 mb-2 drop-shadow-[0_0_10px_currentColor]" />}
            
            <span className="text-sm font-semibold tracking-wide text-white/90">
              {overlay.message}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <h2 className="text-sm font-semibold tracking-wide text-white/80 uppercase mb-3">Quick Actions</h2>
      <div className="grid grid-cols-4 gap-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <motion.button
              key={action.id}
              whileHover={{ 
                scale: 1.1,
                y: -2,
                transition: { type: "spring", stiffness: 400, damping: 10 }
              }}
              whileTap={{ scale: 0.95 }}
              onHoverStart={handleHover}
              onClick={() => handleClick(action)}
              className="relative group flex items-center justify-center p-3 rounded-xl bg-black/40 hover:bg-white/10 transition-colors border border-white/5"
            >
              <Icon className={`w-5 h-5 ${action.color} drop-shadow-[0_0_8px_currentColor]`} />
              
              {/* Tooltip */}
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 backdrop-blur-md text-white text-xs rounded border border-white/20 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                {action.label}
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
