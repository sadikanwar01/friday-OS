"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { VoiceResponse } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

export function VoiceFeature() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState<string | null>(null);

  const handlePushToTalk = async () => {
    if (isRecording) {
      // Stopping (In a real implementation, we'd stop MediaRecorder and send blob)
      // Here we just trigger the backend endpoint
      setIsRecording(false);
      setIsProcessing(true);
      
      try {
        const res = await api.post<VoiceResponse>('/api/voice');
        setResponse(res.message || "Voice command processed successfully.");
      } catch (err: unknown) {
        setResponse((err as Error).message || 'Failed to process voice command');
      } finally {
        setIsProcessing(false);
      }
    } else {
      setIsRecording(true);
      setResponse(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
          <Mic className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Voice Pipeline</h1>
          <p className="text-sm text-muted-foreground">Push to Talk Interface</p>
        </div>
      </div>

      <Card className="bg-card/40 backdrop-blur-md border-border/50 text-center py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
        <CardContent className="flex flex-col items-center justify-center relative z-10 space-y-12">
          
          <div className="relative flex items-center justify-center w-48 h-48">
            <AnimatePresence>
              {isRecording && (
                <>
                  <motion.div
                    initial={{ scale: 1, opacity: 0.5 }}
                    animate={{ scale: 2, opacity: 0 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeOut" }}
                    className="absolute inset-0 bg-red-500/30 rounded-full"
                  />
                  <motion.div
                    initial={{ scale: 1, opacity: 0.5 }}
                    animate={{ scale: 1.5, opacity: 0 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeOut", delay: 1 }}
                    className="absolute inset-0 bg-red-500/30 rounded-full"
                  />
                </>
              )}
            </AnimatePresence>

            <Button
              size="icon"
              variant={isRecording ? "destructive" : "secondary"}
              className={`w-32 h-32 rounded-full transition-all duration-300 shadow-xl ${isRecording ? 'shadow-red-500/20' : ''}`}
              onClick={handlePushToTalk}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <Loader2 className="w-12 h-12 animate-spin text-muted-foreground" />
              ) : (
                <Mic className={`w-12 h-12 ${isRecording ? 'text-white animate-pulse' : 'text-primary'}`} />
              )}
            </Button>
          </div>

          <div className="space-y-2 h-16">
            {isRecording ? (
              <p className="text-lg font-medium text-red-500 animate-pulse">Listening...</p>
            ) : isProcessing ? (
              <p className="text-lg font-medium text-primary animate-pulse">Processing voice...</p>
            ) : (
              <p className="text-lg font-medium text-muted-foreground">Press the microphone to speak</p>
            )}
            
            {response && (
              <motion.p 
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-foreground/80"
              >
                {response}
              </motion.p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
