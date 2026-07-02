import { create } from 'zustand';

export type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface VoiceStore {
  state: VoiceState;
  setState: (state: VoiceState) => void;
  audioLevel: number;
  setAudioLevel: (level: number) => void;
}

export const useVoiceStore = create<VoiceStore>((set) => ({
  state: 'idle',
  setState: (state) => set({ state }),
  audioLevel: 0,
  setAudioLevel: (level) => set({ audioLevel: level }),
}));
