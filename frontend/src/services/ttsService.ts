import { apiService } from './api';

interface TTSStatus {
  available: boolean;
  enabled?: boolean;
  volume?: number;
  language?: string;
}

class TTSService {
  private audioQueue: HTMLAudioElement[] = [];
  private isPlaying = false;
  private cachedStatus: TTSStatus | null = null;

  /**
   * Play TTS audio for given text
   * @param text Text to synthesize and play
   */
  async speak(text: string): Promise<void> {
    try {
      // Check if TTS is enabled
      const status = await this.getStatus();
      if (!status.available) {
        console.log('TTS not available');
        return;
      }

      // Request TTS from backend
      const response = await fetch('http://localhost:5050/api/tts/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          language: status.language || 'de',
        }),
      });

      if (!response.ok) {
        console.error('TTS synthesis failed:', response.statusText);
        return;
      }

      // Get audio blob
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create audio element
      const audio = new Audio(audioUrl);
      
      // Apply volume from settings (default 100%)
      audio.volume = (status.volume ?? 100) / 100;

      // Add to queue
      this.audioQueue.push(audio);

      // Play if not already playing
      if (!this.isPlaying) {
        this.playNext();
      }
    } catch (error) {
      console.error('TTS error:', error);
    }
  }

  /**
   * Play next audio in queue
   */
  private playNext(): void {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      return;
    }

    this.isPlaying = true;
    const audio = this.audioQueue.shift()!;

    audio.onended = () => {
      URL.revokeObjectURL(audio.src);
      this.playNext();
    };

    audio.onerror = () => {
      console.error('Audio playback error');
      URL.revokeObjectURL(audio.src);
      this.playNext();
    };

    audio.play().catch(err => {
      console.error('Failed to play audio:', err);
      this.playNext();
    });
  }

  /**
   * Stop all audio playback
   */
  stop(): void {
    // Clear queue
    this.audioQueue.forEach(audio => {
      audio.pause();
      URL.revokeObjectURL(audio.src);
    });
    this.audioQueue = [];
    this.isPlaying = false;
  }

  /**
   * Get TTS status
   */
  async getStatus(): Promise<TTSStatus> {
    try {
      // Use cached status for 5 seconds to avoid excessive API calls
      if (this.cachedStatus && Date.now() - (this.cachedStatus as any)._timestamp < 5000) {
        return this.cachedStatus;
      }

      const status = await apiService.get<TTSStatus>('/api/tts/status');
      this.cachedStatus = { ...status, _timestamp: Date.now() } as any;
      return status;
    } catch (error) {
      console.error('Failed to get TTS status:', error);
      return { available: false };
    }
  }

  /**
   * Check if TTS is available
   */
  async isAvailable(): Promise<boolean> {
    const status = await this.getStatus();
    return status.available;
  }
}

export const ttsService = new TTSService();
export default ttsService;
