"use client";

import { useChatStore } from "@/store/useChatStore";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { HolographicPanel } from "@/components/ui/HolographicPanel";
import { Bot } from "lucide-react";

export function ChatFeature() {
  const { messages } = useChatStore();

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto space-y-4">
      <div className="flex items-center gap-3 px-2">
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
          <Bot className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight">FRIDAY Chat</h1>
          <p className="text-xs text-muted-foreground">Connected to Conversation Engine</p>
        </div>
      </div>

      <HolographicPanel intensity="high" className="flex-1 flex flex-col min-h-0 overflow-hidden !p-0">
        <MessageList />
        <MessageInput />
      </HolographicPanel>
    </div>
  );
}
