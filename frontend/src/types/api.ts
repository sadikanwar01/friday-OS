export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export interface EngineStatus {
  status: string;
  uptime?: string | number;
  models_loaded?: string[];
  current_goal?: string;
  error?: string;
}

export interface SystemStatusResponse {
  cpu_percent?: number;
  ram_percent?: number;
  gemini_status?: string;
  memory_status?: string;
  automation_status?: string;
  voice_status?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  isError?: boolean;
  errorType?: string;
}

export interface ChatResponse {
  response: string;
}

export interface MemoryEntry {
  id: string;
  category: string;
  key: string;
  value: unknown;
  importance: number;
  created_at: string;
}

export interface AutomationTask {
  id: string;
  goal: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

export interface VoiceResponse {
  status: string;
  message?: string;
}
