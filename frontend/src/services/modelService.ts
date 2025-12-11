import { apiService } from './api';

export interface Model {
  id: string;
  name: string;
  provider: string;
  type: 'text' | 'vision' | 'audio' | 'multimodal';
  description?: string;
  isActive: boolean;
  capabilities: string[];
  config?: Record<string, any>;
}

export interface ModelStats {
  modelId: string;
  totalRequests: number;
  successRate: number;
  avgResponseTime: number;
  lastUsed: string;
}

export interface UpdateModelRequest {
  isActive?: boolean;
  config?: Record<string, any>;
}

class ModelService {
  async getModels(): Promise<Model[]> {
    return apiService.get<Model[]>('/models');
  }

  async getModel(modelId: string): Promise<Model> {
    return apiService.get<Model>(`/models/${modelId}`);
  }

  async getActiveModel(): Promise<Model> {
    return apiService.get<Model>('/models/active');
  }

  async setActiveModel(modelId: string): Promise<Model> {
    return apiService.post<Model>(`/models/${modelId}/activate`, {});
  }

  async updateModel(modelId: string, data: UpdateModelRequest): Promise<Model> {
    return apiService.put<Model>(`/models/${modelId}`, data);
  }

  async getModelStats(modelId: string): Promise<ModelStats> {
    return apiService.get<ModelStats>(`/models/${modelId}/stats`);
  }

  async testModel(modelId: string, prompt: string): Promise<{ response: string; responseTime: number }> {
    return apiService.post(`/models/${modelId}/test`, { prompt });
  }
}

export const modelService = new ModelService();
export default modelService;
