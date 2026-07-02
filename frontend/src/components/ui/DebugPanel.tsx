"use client";

import { useState, useEffect } from "react";
import { useDebugStore } from "@/store/useDebugStore";
import { useAppStore } from "@/store/useAppStore";
import { useVoiceStore } from "@/store/useVoiceStore";
import { usePathname } from "next/navigation";
import { API_BASE_URL } from "@/lib/api";
import { Bug, X, Copy, RefreshCw, Terminal, Activity, FileText } from "lucide-react";
import { Button } from "./button";
import { ScrollArea } from "./scroll-area";

export function DebugPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  
  const { apiLogs, lastError, diagnostics, setDiagnostic } = useDebugStore();
  const { activeFeature } = useAppStore();
  const { state: voiceState } = useVoiceStore();

  const [connectionStatus, setConnectionStatus] = useState<'Checking...' | 'Online' | 'Offline'>('Checking...');

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;
    
    const checkConn = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`);
        setConnectionStatus(res.ok ? 'Online' : 'Offline');
      } catch {
        setConnectionStatus('Offline');
      }
    };
    checkConn();
    const int = setInterval(checkConn, 5000);
    return () => clearInterval(int);
  }, []);

  if (process.env.NODE_ENV !== 'development') return null;

  const runDiagnostics = async () => {
    const endpoints = [
      '/health', 
      '/api/system', 
      '/api/chat', 
      '/api/chat/stream', 
      '/api/memory', 
      '/api/history', 
      '/api/automation', 
      '/api/browser', 
      '/api/voice'
    ];
    
    for (const ep of endpoints) {
      setDiagnostic(ep, 'PENDING');
      try {
        const isPost = ep.includes('chat') || ep.includes('voice') || ep.includes('browser') || ep.includes('automation');
        const res = await fetch(`${API_BASE_URL}${ep}`, {
          method: isPost ? 'POST' : 'GET',
          headers: isPost ? { 'Content-Type': 'application/json' } : undefined,
          body: isPost ? JSON.stringify(ep === '/api/chat' || ep === '/api/chat/stream' ? { message: "ping" } : {}) : undefined
        });
        
        if (res.ok) {
          setDiagnostic(ep, 'PASS');
        } else {
          // If we hit a 404 or 501 or 405, it might be expected if the endpoint isn't fully implemented, but we still mark it FAIL as per spec
          setDiagnostic(ep, 'FAIL', `${res.status} ${res.statusText}`);
        }
      } catch (e) {
        setDiagnostic(ep, 'FAIL', (e as Error).message);
      }
    }
  };

  const copyReport = () => {
    const report = `
# FRIDAY OS Debug Report
Date: ${new Date().toISOString()}
Route: ${pathname}
Connection: ${connectionStatus}

## States
- Active Feature: ${activeFeature}
- Voice State: ${voiceState}
- AI State: ${voiceState === 'thinking' ? 'Processing' : 'Idle'}

## Diagnostics
${diagnostics.map(d => `- ${d.endpoint}: ${d.status} ${d.error ? `(${d.error})` : ''}`).join('\n')}

## Last Error
${lastError || 'None'}

## API Logs (Last 5)
${apiLogs.slice(0, 5).map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.status} ${l.endpoint}\nError: ${l.errorMessage}`).join('\n\n')}
    `.trim();

    navigator.clipboard.writeText(report);
    alert('Debug report copied to clipboard');
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50 p-3 bg-black/80 border border-white/20 rounded-full text-white/50 hover:text-white hover:bg-black transition-all"
        title="Open Debug Panel"
      >
        <Bug className="w-5 h-5" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 max-h-[80vh] flex flex-col bg-black/95 border border-white/20 rounded-xl shadow-2xl backdrop-blur-xl overflow-hidden font-mono text-xs text-white/80">
      
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/10 bg-white/5">
        <div className="flex items-center gap-2 font-bold text-amber-500">
          <Bug className="w-4 h-4" />
          <span>DEVELOPER PANEL</span>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-white/50 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          
          {/* Status Section */}
          <section>
            <h3 className="text-white/40 uppercase tracking-widest mb-2 flex items-center gap-2"><Activity className="w-3 h-3" /> System Status</h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white/5 p-2 rounded">
                <div className="text-white/40 mb-1">Backend</div>
                <div className={connectionStatus === 'Online' ? 'text-emerald-400' : 'text-red-400'}>{connectionStatus}</div>
              </div>
              <div className="bg-white/5 p-2 rounded">
                <div className="text-white/40 mb-1">Route</div>
                <div className="truncate" title={pathname}>{pathname}</div>
              </div>
              <div className="bg-white/5 p-2 rounded">
                <div className="text-white/40 mb-1">Active Feature</div>
                <div className="text-blue-300">{activeFeature}</div>
              </div>
              <div className="bg-white/5 p-2 rounded">
                <div className="text-white/40 mb-1">Voice State</div>
                <div className="text-purple-300">{voiceState}</div>
              </div>
            </div>
          </section>

          {/* Diagnostics Section */}
          <section>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-white/40 uppercase tracking-widest flex items-center gap-2"><Terminal className="w-3 h-3" /> Diagnostics</h3>
              <Button size="sm" variant="outline" className="h-6 text-[10px]" onClick={runDiagnostics}>
                <RefreshCw className="w-3 h-3 mr-1" /> Run
              </Button>
            </div>
            <div className="bg-white/5 rounded p-2 space-y-1">
              {diagnostics.length === 0 ? (
                <div className="text-white/30 text-center py-2">Click Run to test endpoints</div>
              ) : (
                diagnostics.map((d, i) => (
                  <div key={i} className="flex justify-between items-center py-1 border-b border-white/5 last:border-0">
                    <span className="truncate pr-2">{d.endpoint}</span>
                    <span className={`font-bold ${d.status === 'PASS' ? 'text-emerald-400' : d.status === 'FAIL' ? 'text-red-400' : 'text-amber-400'}`}>
                      {d.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Last Error */}
          {lastError && (
            <section>
              <h3 className="text-red-400/80 uppercase tracking-widest mb-2 flex items-center gap-2"><X className="w-3 h-3" /> Last Error</h3>
              <div className="bg-red-950/30 text-red-200 p-2 rounded border border-red-900/50 break-words">
                {lastError}
              </div>
            </section>
          )}

          {/* API Logs */}
          <section>
            <h3 className="text-white/40 uppercase tracking-widest mb-2 flex items-center gap-2"><FileText className="w-3 h-3" /> Failed API Requests</h3>
            {apiLogs.length === 0 ? (
              <div className="text-white/30 text-center py-2 bg-white/5 rounded">No failed requests</div>
            ) : (
              <div className="space-y-2">
                {apiLogs.slice(0, 3).map((log) => (
                  <div key={log.id} className="bg-white/5 p-2 rounded border border-white/10 flex flex-col gap-1">
                    <div className="flex justify-between text-white/50">
                      <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                      <span className="text-red-400 font-bold">{log.status}</span>
                    </div>
                    <div className="font-semibold">{log.endpoint}</div>
                    <div className="text-red-300 truncate">{log.errorMessage}</div>
                  </div>
                ))}
              </div>
            )}
          </section>

        </div>
      </ScrollArea>

      <div className="p-3 border-t border-white/10 bg-white/5 flex gap-2">
        <Button onClick={copyReport} className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded">
          <Copy className="w-4 h-4 mr-2" /> Copy Debug Report
        </Button>
      </div>
    </div>
  );
}
