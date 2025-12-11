import { apiService } from './api';

export interface Memory {
  id: string;
  type: 'conversation' | 'fact' | 'preference' | 'context';
  content: string;
  metadata?: Record<string, any>;
  timestamp: string;
  relevance: number;
  source?: string;
}

export interface MemoryStats {
  totalMemories: number;
  byType: Record<string, number>;
  storageUsed: number;
  lastUpdated: string;
}

export interface SearchMemoryRequest {
  query: string;
  type?: string;
  limit?: number;
}

class MemoryService {
  async getMemories(type?: string): Promise<Memory[]> {
    const endpoint = type ? `/memory?type=${type}` : '/memory';
    return apiService.get<Memory[]>(endpoint);
  }

  async getMemory(memoryId: string): Promise<Memory> {
    return apiService.get<Memory>(`/memory/${memoryId}`);
  }

  async createMemory(memory: Omit<Memory, 'id' | 'timestamp' | 'relevance'>): Promise<Memory> {
    return apiService.post<Memory>('/memory', memory);
  }

  async updateMemory(memoryId: string, data: Partial<Memory>): Promise<Memory> {
    return apiService.put<Memory>(`/memory/${memoryId}`, data);
  }

  async deleteMemory(memoryId: string): Promise<void> {
    return apiService.delete(`/memory/${memoryId}`);
  }

  async searchMemories(query: SearchMemoryRequest): Promise<Memory[]> {
    return apiService.post<Memory[]>('/memory/search', query);
  }

  async getStats(): Promise<MemoryStats> {
    return apiService.get<MemoryStats>('/memory/stats');
  }

  async clearMemories(type?: string): Promise<void> {
    const endpoint = type ? `/memory/clear?type=${type}` : '/memory/clear';
    return apiService.post(endpoint, {});
  }
}

export const memoryService = new MemoryService();
export default memoryService;
