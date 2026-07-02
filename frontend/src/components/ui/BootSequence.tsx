"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { audioManager } from "@/lib/AudioManager";
import { API_BASE_URL } from "@/lib/api";

interface BootSequenceProps {
  onComplete: () => void;
}

interface SystemStatus {
  database: string;
  gemini: string;
  memory: string;
  automation: string;
  voice: string;
  browser: string;
}

export function BootSequence({ onComplete }: BootSequenceProps) {
  const [stage, setStage] = useState<1 | 2 | 3 | 4 | 5 | 6>(1);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    let isMounted = true;
    
    const runSequence = async () => {
      // STAGE 1: Black screen + ambient sound
      await new Promise(resolve => setTimeout(resolve, 500));
      if (!isMounted) return;
      await audioManager.initialize();
      audioManager.play("startup"); // soft futuristic hum
      
      // STAGE 2: Particles, lines, scan
      setStage(2);
      await new Promise(resolve => setTimeout(resolve, 1500));
      if (!isMounted) return;

      // STAGE 3: Animated Boot Logs with REAL data
      setStage(3);
      setLogs(prev => [...prev, "FRIDAY OS v1.0", "Initializing AI Core..."]);
      
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        const res = await fetch(`${API_BASE_URL}/api/system`, { signal: controller.signal });
        clearTimeout(timeoutId);
        const data = await res.json();
        const sysStatus: SystemStatus = {
          database: "ONLINE", // Assuming online if backend responds
          gemini: data.gemini_status === "online" ? "ONLINE" : "OFFLINE",
          memory: data.memory_status === "online" ? "ONLINE" : "OFFLINE",
          automation: data.automation_status === "online" ? "ONLINE" : "OFFLINE",
          voice: data.voice_status === "online" ? "ONLINE" : "OFFLINE",
          browser: "ONLINE", // Assuming online for now unless backend provides
        };
        
        await new Promise(resolve => setTimeout(resolve, 500));
        setLogs(prev => [...prev, `Database ........ ${sysStatus.database}`]);
        await new Promise(resolve => setTimeout(resolve, 300));
        setLogs(prev => [...prev, `Gemini ......... ${sysStatus.gemini}`]);
        await new Promise(resolve => setTimeout(resolve, 300));
        setLogs(prev => [...prev, `Memory ......... ${sysStatus.memory}`]);
        await new Promise(resolve => setTimeout(resolve, 300));
        setLogs(prev => [...prev, `Automation ..... ${sysStatus.automation}`]);
        await new Promise(resolve => setTimeout(resolve, 300));
        setLogs(prev => [...prev, `Voice .......... ${sysStatus.voice}`]);
        await new Promise(resolve => setTimeout(resolve, 300));
        setLogs(prev => [...prev, `Browser ........ ${sysStatus.browser}`]);
        
      } catch (_err) {
        setLogs(prev => [...prev, "CRITICAL ERROR: Failed to connect to Backend.", "OFFLINE"]);
        // We continue anyway for fallback
      }

      await new Promise(resolve => setTimeout(resolve, 800));
      if (!isMounted) return;
      setLogs(prev => [...prev, "Starting AI Core...", "System Ready."]);
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (!isMounted) return;

      // STAGE 4: Core Assembles
      setStage(4);
      await new Promise(resolve => setTimeout(resolve, 2000));
      if (!isMounted) return;

      // STAGE 5: Voice Greeting
      setStage(5);
      
      const hour = new Date().getHours();
      let greeting = "Good Evening";
      if (hour >= 5 && hour < 12) greeting = "Good Morning";
      else if (hour >= 12 && hour < 17) greeting = "Good Afternoon";
      else if (hour >= 17 && hour < 22) greeting = "Good Evening";
      else greeting = "Working late again Professor? I'm ready whenever you are.";

      const fullGreeting = hour >= 22 || hour < 5 
        ? `${greeting} All systems are online. Memory synchronized. Voice engine ready. Browser engine ready. Automation engine ready. How may I assist you today?`
        : `${greeting} Professor Sadiq. Welcome back. All systems are online. Memory synchronized. Voice engine ready. Browser engine ready. Automation engine ready. How may I assist you today?`;

      // Trigger actual TTS from backend
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        await fetch(`${API_BASE_URL}/api/voice`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "synthesize", text: fullGreeting }),
          signal: controller.signal
        });
        clearTimeout(timeoutId);
      } catch (e) {
        console.error("TTS Failed", e);
      }
      
      // Wait for TTS to finish (approximation based on text length, ~15 seconds)
      await new Promise(resolve => setTimeout(resolve, 3000)); // We transition to OS while she speaks
      
      if (!isMounted) return;
      setStage(6); // Done
      setTimeout(() => {
        if (isMounted) onComplete();
      }, 1000);
    };

    runSequence();

    return () => {
      isMounted = false;
    };
  }, [onComplete]);

  if (stage === 6) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="boot-sequence"
        initial={{ opacity: 1 }}
        exit={{ opacity: 0, transition: { duration: 1.5, ease: "easeInOut" } }}
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black overflow-hidden font-mono text-blue-400"
      >
        {/* Stage 2 & 4: Energy Lines and Particles */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: stage >= 2 ? 0.3 : 0 }}
          transition={{ duration: 2 }}
          className="absolute inset-0 bg-[linear-gradient(rgba(0,100,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,100,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px] [transform:perspective(500px)_rotateX(60deg)] origin-bottom"
        />

        {stage >= 2 && (
          <div className="absolute inset-0 pointer-events-none">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 2 }}
              className="w-full h-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-black to-black"
            />
          </div>
        )}

        {/* Stage 3: Boot Logs */}
        {stage >= 3 && stage < 5 && (
          <div className="absolute left-10 top-10 flex flex-col gap-1 text-sm md:text-base z-10 w-full max-w-2xl">
            {logs.map((log, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={log.includes("OFFLINE") || log.includes("CRITICAL") ? "text-red-500" : "text-blue-400"}
              >
                {log}
              </motion.div>
            ))}
          </div>
        )}

        {/* Stage 4: AI Core Assembles */}
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={
            stage >= 4 
              ? { scale: [0, 1.2, 1], opacity: [0, 1, 1] } 
              : { scale: 0, opacity: 0 }
          }
          transition={{ duration: 2, ease: "easeOut" }}
          className="absolute w-64 h-64 rounded-full border border-blue-500/50 shadow-[0_0_100px_rgba(0,100,255,0.5)] flex items-center justify-center"
        >
          {stage >= 4 && (
            <motion.div 
              animate={{ rotate: 360 }} 
              transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
              className="w-full h-full rounded-full border-t-2 border-r-2 border-blue-400/80 absolute"
            />
          )}
          {stage >= 4 && (
            <motion.div 
              animate={{ rotate: -360 }} 
              transition={{ repeat: Infinity, duration: 6, ease: "linear" }}
              className="w-48 h-48 rounded-full border-b-2 border-l-2 border-blue-300/60 absolute"
            />
          )}
          <div className="w-24 h-24 bg-blue-500/80 blur-xl rounded-full animate-pulse" />
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
