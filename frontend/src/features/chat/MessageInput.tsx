"use client";

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "@/store/useChatStore";
import { useVoiceStore } from "@/store/useVoiceStore";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2, Mic } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

export function MessageInput() {
  const [input, setInput] = useState("");
  const { addMessage, updateMessage, setError, setTyping, isTyping, retryContent, setRetryContent } = useChatStore();
  const { setState: setVoiceState, setAudioLevel } = useVoiceStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [input]);

  useEffect(() => {
    if (retryContent) {
      setTimeout(() => {
        setInput(retryContent);
        setRetryContent(null);
      }, 0);
    }
  }, [retryContent, setRetryContent]);

  const handleSubmit = async () => {
    if (!input.trim() || isTyping) return;

    const userMessageId = Date.now().toString();
    const currentInput = input.trim();
    
    addMessage({
      id: userMessageId,
      role: "user",
      content: currentInput
    });
    
    setInput("");
    setTyping(true);
    setVoiceState('thinking');

    const assistantMessageId = (Date.now() + 1).toString();
    addMessage({
      id: assistantMessageId,
      role: "assistant",
      content: ""
    });

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: currentInput })
      });

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = await response.text();
        }
        
        const errorMsg = errorData?.message || errorData?.detail || "Failed to connect to chat API";
        
        if (response.status === 429 || errorMsg.includes("RESOURCE_EXHAUSTED") || errorMsg.includes("quota")) {
          setError(assistantMessageId, "quota_exceeded", "");
          return;
        }

        throw new Error(errorMsg);
      }

      if (response.body) {
        setVoiceState('speaking');
        // Simulate audio level for visual effect during typing
        const audioInterval = setInterval(() => {
          setAudioLevel(0.3 + Math.random() * 0.7);
        }, 100);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.replace('data: ', ''));
                if (parsed.content) {
                  fullResponse += parsed.content;
                }
              } catch (e) {
                // Ignore incomplete JSON chunks
              }
            }
          }
          
          updateMessage(assistantMessageId, fullResponse);
        }
        
        clearInterval(audioInterval);
        setAudioLevel(0);
      }
    } catch (error: unknown) {
      let errorMessage = (error as Error).message || 'Failed to communicate with FRIDAY.';
      if (errorMessage.includes('Failed to fetch')) {
        errorMessage = `Failed to connect to the backend server at ${API_BASE_URL}. Please verify it is running and accessible.`;
      }
      setError(assistantMessageId, "general_error", errorMessage);
    } finally {
      setTyping(false);
      setVoiceState('idle');
      setAudioLevel(0);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 bg-black/20 backdrop-blur-md border-t border-blue-500/20 shrink-0 relative pointer-events-auto">
      <div className="max-w-4xl mx-auto relative flex items-end gap-2 bg-blue-950/40 rounded-3xl border border-blue-400/30 focus-within:border-blue-400/60 focus-within:shadow-[0_0_20px_rgba(0,150,255,0.2)] transition-all p-2">
        
        <Button variant="ghost" size="icon" className="shrink-0 h-12 w-12 text-blue-400/70 hover:text-blue-300 rounded-2xl hover:bg-blue-500/10">
          <Mic className="h-6 w-6" />
        </Button>

        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message FRIDAY..."
          className="min-h-[48px] max-h-[200px] bg-transparent border-0 focus-visible:ring-0 px-2 py-3.5 resize-none text-base text-blue-50 placeholder:text-blue-300/40"
          rows={1}
        />

        {isTyping && (
          <div className="shrink-0 h-12 w-12 flex items-center justify-center text-blue-400">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        )}
      </div>
      <div className="text-center mt-3 text-xs text-blue-300/40 uppercase tracking-widest font-light">
        FRIDAY OS Core // <kbd className="px-1.5 py-0.5 bg-blue-950/50 rounded border border-blue-500/20 text-[10px] font-mono mx-1">Enter</kbd> to execute
      </div>
    </div>
  );
}
