"use client";

import { motion } from "framer-motion";
import { useChatStore } from "@/store/useChatStore";
import { useVoiceStore } from "@/store/useVoiceStore";
import { useMemo } from "react";

export function CommandStatus() {
  const { isTyping } = useChatStore();
  const { state: voiceState } = useVoiceStore();

  const { text, color, pulseColor } = useMemo(() => {
    if (voiceState === 'listening') {
      return { text: "Listening to Audio Input...", color: "text-cyan-200", pulseColor: "bg-cyan-400 shadow-[0_0_10px_rgba(0,255,255,1)]" };
    }
    if (voiceState === 'thinking' || isTyping) {
      return { text: "Processing Command...", color: "text-purple-200", pulseColor: "bg-purple-500 shadow-[0_0_10px_rgba(150,0,255,1)]" };
    }
    if (voiceState === 'speaking') {
      return { text: "Executing • Transmitting Response...", color: "text-emerald-200", pulseColor: "bg-emerald-400 shadow-[0_0_10px_rgba(0,255,100,1)]" };
    }
    return { text: "Mission Ready • Awaiting Command", color: "text-blue-200", pulseColor: "bg-blue-500 shadow-[0_0_10px_rgba(0,100,255,1)]" };
  }, [voiceState, isTyping]);

  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 pointer-events-auto">
      <motion.div 
        key={text}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className="px-6 py-2 rounded-full bg-black/60 border border-white/10 backdrop-blur-md shadow-[0_0_20px_rgba(0,100,255,0.1)] flex items-center gap-3"
      >
        <div className={`w-2 h-2 rounded-full animate-pulse ${pulseColor}`} />
        <span className={`text-sm tracking-widest font-mono uppercase ${color}`}>
          {text}
        </span>
      </motion.div>
    </div>
  );
}
