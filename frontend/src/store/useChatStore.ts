import { create } from 'zustand';
import { ChatMessage } from '@/types/api';

interface ChatState {
  messages: ChatMessage[];
  isTyping: boolean;
  retryContent: string | null;
  addMessage: (msg: ChatMessage) => void;
  updateMessage: (id: string, content: string) => void;
  setError: (id: string, errorType: string, content: string) => void;
  removeMessages: (ids: string[]) => void;
  setTyping: (typing: boolean) => void;
  setRetryContent: (content: string | null) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isTyping: false,
  retryContent: null,
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateMessage: (id, content) => set((state) => ({
    messages: state.messages.map(m => m.id === id ? { ...m, content } : m)
  })),
  setError: (id, errorType, content) => set((state) => ({
    messages: state.messages.map(m => m.id === id ? { ...m, isError: true, errorType, content } : m)
  })),
  removeMessages: (ids) => set((state) => ({
    messages: state.messages.filter(m => !ids.includes(m.id))
  })),
  setTyping: (typing) => set({ isTyping: typing }),
  setRetryContent: (content) => set({ retryContent: content }),
  clearChat: () => set({ messages: [] })
}));
