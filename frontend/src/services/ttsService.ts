import { apiService } from './api';
import { settingsService } from './settingsService';

class TTSService {
  private audioQueue: HTMLAudioElement[] = [];
  private isPlaying = false;

  /**
   * Play TTS audio for given text
   * @param text Text to synthesize and play
   */
  async speak(text: string): Promise<void> {
    try {
      // Check if TTS is enabled
      const settings = await settingsService.getSettings();
      if (!settings.tts?.enabled) {
        return; // TTS disabled, skip
      }

      // Request TTS from backend
      const response = await fetch('http://localhost:8000/api/tts/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          language: settings.tts?.language || 'de',
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
      
      // Apply volume from settings
      audio.volume = (settings.tts?.volume ?? 100) / 100;

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
   * Check if TTS is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const response = await apiService.get<{ available: boolean }>('/api/tts/status');
      return response.available;
    } catch {
      return false;
    }
  }
}

export const ttsService = new TTSService();
export default ttsService;
