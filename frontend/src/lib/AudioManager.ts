/**
 * AudioManager handles dynamic loading and graceful playback of UI sounds.
 * If a sound file is missing, it will fail silently and gracefully.
 */

type SoundType = 
  | 'startup' 
  | 'hover' 
  | 'notification' 
  | 'thinking' 
  | 'listening' 
  | 'speaking' 
  | 'shutdown';

class AudioManager {
  private static instance: AudioManager;
  private audioContext: AudioContext | null = null;
  private buffers: Map<SoundType, AudioBuffer> = new Map();
  private activeSources: Map<SoundType, AudioBufferSourceNode> = new Map();
  private isInitialized = false;

  private constructor() {}

  public static getInstance(): AudioManager {
    if (!AudioManager.instance) {
      AudioManager.instance = new AudioManager();
    }
    return AudioManager.instance;
  }

  /**
   * Must be called after user interaction to unlock the AudioContext in browsers.
   */
  public async initialize() {
    if (this.isInitialized) return;
    
    try {
      this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }
      this.isInitialized = true;
      this.preloadSounds();
    } catch (_e) {
      console.warn("Failed to initialize AudioContext", _e);
    }
  }

  private async preloadSounds() {
    const sounds: SoundType[] = [
      'startup', 'hover', 'notification', 'thinking', 'listening', 'speaking', 'shutdown'
    ];
    
    for (const sound of sounds) {
      this.loadSound(sound);
    }
  }

  private async loadSound(sound: SoundType) {
    if (!this.audioContext) return;
    
    try {
      const response = await fetch(`/audio/${sound}.mp3`);
      if (!response.ok) {
        // File doesn't exist, fail gracefully
        return;
      }
      
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      this.buffers.set(sound, audioBuffer);
    } catch (_e) {
      // Graceful failure
      console.warn(`Could not load audio file for ${sound}`);
    }
  }

  public play(sound: SoundType, loop: boolean = false): void {
    if (!this.audioContext || !this.buffers.has(sound)) return;

    try {
      // If it's a looping sound (like thinking/listening), stop the previous one if it exists
      if (loop && this.activeSources.has(sound)) {
        this.stop(sound);
      }

      const source = this.audioContext.createBufferSource();
      source.buffer = this.buffers.get(sound)!;
      source.loop = loop;
      
      // Basic gain node for volume control
      const gainNode = this.audioContext.createGain();
      gainNode.gain.value = 0.5; // Default 50% volume for UI sounds
      
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      source.start(0);
      
      if (loop) {
        this.activeSources.set(sound, source);
      }
    } catch (_e) {
      console.warn(`Failed to play sound: ${sound}`);
    }
  }

  public stop(sound: SoundType): void {
    const source = this.activeSources.get(sound);
    if (source) {
      try {
        source.stop();
        source.disconnect();
      } catch (_e) {
        // Ignore errors on stop
      }
      this.activeSources.delete(sound);
    }
  }
  
  public stopAll(): void {
    for (const sound of this.activeSources.keys()) {
      this.stop(sound);
    }
  }
}

export const audioManager = AudioManager.getInstance();
