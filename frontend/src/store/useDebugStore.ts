import { create } from 'zustand';

export interface ApiLog {
  id: string;
  timestamp: number;
  endpoint: string;
  requestBody?: string;
  response?: string;
  status?: number;
  errorMessage?: string;
}

export interface DiagnosticResult {
  endpoint: string;
  status: 'PASS' | 'FAIL' | 'PENDING';
  error?: string;
}

interface DebugState {
  apiLogs: ApiLog[];
  lastError: string | null;
  diagnostics: DiagnosticResult[];
  addLog: (log: Omit<ApiLog, 'id' | 'timestamp'>) => void;
  setLastError: (error: string) => void;
  setDiagnostic: (endpoint: string, status: 'PASS' | 'FAIL' | 'PENDING', error?: string) => void;
  clearLogs: () => void;
}

export const useDebugStore = create<DebugState>((set) => ({
  apiLogs: [],
  lastError: null,
  diagnostics: [],
  
  addLog: (log) => set((state) => {
    const newLog = {
      ...log,
      id: Date.now().toString() + Math.random().toString(36).substring(7),
      timestamp: Date.now()
    };
    return {
      apiLogs: [newLog, ...state.apiLogs].slice(0, 50), // keep last 50 logs
      lastError: log.errorMessage || state.lastError
    };
  }),
  
  setLastError: (error) => set({ lastError: error }),
  
  setDiagnostic: (endpoint, status, error) => set((state) => {
    const existing = state.diagnostics.find(d => d.endpoint === endpoint);
    if (existing) {
      return {
        diagnostics: state.diagnostics.map(d => 
          d.endpoint === endpoint ? { ...d, status, error } : d
        )
      };
    }
    return {
      diagnostics: [...state.diagnostics, { endpoint, status, error }]
    };
  }),

  clearLogs: () => set({ apiLogs: [], lastError: null })
}));
