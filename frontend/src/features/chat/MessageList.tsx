"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/useChatStore";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatBubble } from "./ChatBubble";
import { motion, AnimatePresence } from "framer-motion";

export function MessageList() {
  const { messages, isTyping } = useChatStore();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-secondary/50 flex items-center justify-center mb-4">
          <span className="text-2xl font-bold text-primary">F</span>
        </div>
        <h2 className="text-xl font-medium mb-2">How can I help you today?</h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          FRIDAY OS is ready. You can ask me to run automations, manage files, or just chat.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 p-4 md:p-6">
      <div className="space-y-6 pb-4 max-w-4xl mx-auto">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
            >
              <ChatBubble message={message} />
            </motion.div>
          ))}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex items-center space-x-2 text-white p-4 bg-blue-900/30 border border-blue-400/30 rounded-3xl backdrop-blur-xl shadow-[0_0_15px_rgba(0,150,255,0.1)] w-fit"
            >
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s] shadow-[0_0_5px_#60a5fa]" />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s] shadow-[0_0_5px_#60a5fa]" />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce shadow-[0_0_5px_#60a5fa]" />
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endRef} />
      </div>
    </ScrollArea>
  );
}
