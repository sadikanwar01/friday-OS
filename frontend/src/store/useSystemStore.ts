import { create } from 'zustand';
import { SystemStatusResponse } from '@/types/api';

interface SystemState {
  status: SystemStatusResponse | null;
  lastUpdated: string | null;
  updateStatus: (status: SystemStatusResponse) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
  status: null,
  lastUpdated: null,
  updateStatus: (status) => set({ status, lastUpdated: new Date().toISOString() })
}));
