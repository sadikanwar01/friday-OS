"use client";

import { ChatMessage } from "@/types/api";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Bot, User, Copy, Check, AlertTriangle, RotateCcw } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

import { useChatStore } from "@/store/useChatStore";

import React from "react";
const CodeBlock = ({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode; [key: string]: unknown }) => {
  const match = /language-(\w+)/.exec(className || "");
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!inline && match) {
    return (
      <div className="relative group rounded-md overflow-hidden my-4 border border-border/50">
        <div className="flex items-center justify-between px-4 py-1.5 bg-secondary/50 border-b border-border/50 text-xs text-muted-foreground">
          <span>{match[1]}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={handleCopy}
          >
            {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
          </Button>
        </div>
        <SyntaxHighlighter
          style={vscDarkPlus as unknown as { [key: string]: React.CSSProperties }}
          language={match[1]}
          PreTag="div"
          className="!m-0 !bg-[#0d0d0d] !p-4 text-sm"
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      </div>
    );
  }
  return (
    <code className="bg-secondary/50 px-1.5 py-0.5 rounded text-sm text-primary" {...props}>
      {children}
    </code>
  );
};

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const { messages, setRetryContent, removeMessages } = useChatStore();
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <span className="text-xs bg-secondary/50 text-muted-foreground px-3 py-1 rounded-full border border-border/50">
          {message.content}
        </span>
      </div>
    );
  }

  if (message.isError) {
    const handleRetry = () => {
      const idx = messages.findIndex(m => m.id === message.id);
      const prevMessage = messages[idx - 1];
      if (prevMessage && prevMessage.role === "user") {
        setRetryContent(prevMessage.content);
        removeMessages([prevMessage.id, message.id]);
      }
    };

    const isQuota = message.errorType === "quota_exceeded";
    const title = isQuota ? "Gemini Quota Exceeded" : "System Error";
    const desc = isQuota ? "Gemini quota exceeded. Please try again later." : message.content;

    return (
      <div className="flex w-full justify-center my-4">
        <div className="bg-red-950/40 border border-red-500/30 rounded-2xl p-5 flex flex-col items-center gap-3 text-center max-w-sm shadow-[0_0_20px_rgba(239,68,68,0.1)] backdrop-blur-xl relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-red-500/50 to-transparent" />
          <div className="w-10 h-10 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(239,68,68,0.2)]">
            <AlertTriangle className="w-5 h-5 text-red-400 drop-shadow-[0_0_5px_rgba(239,68,68,0.8)]" />
          </div>
          <div>
            <h3 className="font-semibold text-red-300 tracking-wide uppercase text-sm mb-1">{title}</h3>
            <p className="text-sm text-red-200/70 leading-relaxed font-light">
              {desc}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={handleRetry} className="mt-2 w-full bg-red-950/50 hover:bg-red-900/50 hover:text-red-200 text-red-300 border-red-500/30 transition-all rounded-xl">
            <RotateCcw className="w-4 h-4 mr-2" />
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex w-full gap-4", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className="shrink-0 flex items-start">
        <motion.div 
          whileHover={{ scale: 1.1 }}
          className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-md shadow-lg",
            isUser 
              ? "bg-white/10 text-white border border-white/20" 
              : "bg-blue-500/20 text-blue-400 border border-blue-400/30 shadow-[0_0_15px_rgba(0,150,255,0.3)]"
          )}
        >
          {isUser ? <User className="w-5 h-5 drop-shadow-md" /> : <Bot className="w-5 h-5 drop-shadow-[0_0_5px_rgba(0,150,255,0.8)]" />}
        </motion.div>
      </div>

      <div className={cn(
        "flex flex-col max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "px-6 py-4 rounded-3xl backdrop-blur-xl relative overflow-hidden transition-all duration-300",
          isUser 
            ? "bg-white/10 text-white border border-white/20 rounded-tr-sm shadow-[0_4px_30px_rgba(255,255,255,0.05)]" 
            : "bg-blue-950/30 border border-blue-400/30 shadow-[0_0_20px_rgba(0,150,255,0.1)] rounded-tl-sm text-blue-50"
        )}>
          {/* Subtle glossy highlight */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed tracking-wide font-light">{message.content}</p>
          ) : (
            <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0 font-light tracking-wide">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code: CodeBlock as React.ElementType
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
